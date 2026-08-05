"""Export a share-ready max-flood-depth GeoTIFF for an external collaborator.

WHY THIS EXISTS — the raw run artifact is the WRONG file to hand out
-------------------------------------------------------------------
``experiments/<arm>/floodmap_hmax_lev3.tif`` is deliberately UNMASKED: it keeps the
full water column of the bay and open ocean (see validate.load_floodmap, which only
applies ``dep > -0.5`` AFTER reading it). Measured on v2's premier: the unmasked
raster has 18.2 M finite cells, 13.1 M of them deeper than 2 m — those are the
seabed, not flooding. A damage model pointed at that file computes losses across
the Atlantic. The masked raster drops to 5.9 M finite / 0.8 M over 2 m.

So this script writes the MASKED raster, and additionally:
  * sets ``nodata`` explicitly (the run artifacts leave it untagged, so a naive
    reader can treat the NaN dry-mask as data),
  * DEFLATE-compresses + tiles it and builds overviews (the plain export is
    ~300 MB for a raster that is >95% empty),
  * drops a README next to it recording CRS, units, datum, threshold and the
    model's known bias — the things a depth raster does not carry in its header.

The CRS is left as the model's native one (UTM, metres). Reproject downstream if
the consumer needs degrees; doing it here would resample depths for no reason.

Run (v1 premier, the frozen domain — the right thing to share while v2 is mid-campaign):
    NJ_DOMAIN=v1_monmouth PYTHONPATH=$PWD python scripts/export_share_floodmap.py
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

import nj_sfincs  # noqa: F401  (PROJ primer — must precede hydromt_sfincs)
from nj_sfincs import validate
from nj_sfincs.config import ROOT

V1_PREMIER = ROOT / "experiments" / "v1_monmouth" / "faber-waves-premier"
DEFAULT_OUT = ROOT / "share"

#: The arm name alone is AMBIGUOUS — `faber-waves-premier` exists on BOTH v1_monmouth
#: and v2_barnegat, with different extents. The shared filename must carry the domain.
DEFAULT_STEM = "sandy_hmax_v1_monmouth_faber-waves-premier"


def export(model_dir: Path, out_tif: Path, stem: str) -> dict:
    _, da_hmax, _ = validate.load_floodmap(model_dir, need_model=False)

    da = da_hmax.rio.write_nodata(np.nan, encoded=False)
    da.name = "max_flood_depth_m"
    da.attrs.update(
        long_name="Maximum flood depth over the simulation",
        units="m",
        note="permanent water (subgrid bed <= -0.5 m) masked out; NaN = dry/no data",
    )

    out_tif.parent.mkdir(parents=True, exist_ok=True)
    da.rio.to_raster(
        out_tif,
        driver="GTiff",
        dtype="float32",
        compress="DEFLATE",
        predictor=3,          # float predictor — big win on smooth depth fields
        zlevel=6,
        tiled=True,
        blockxsize=512,
        blockysize=512,
        BIGTIFF="IF_SAFER",
    )

    # Overviews so it opens instantly in QGIS instead of grinding the full raster.
    import rasterio
    from rasterio.enums import Resampling

    with rasterio.open(out_tif, "r+") as ds:
        ds.build_overviews([2, 4, 8, 16, 32], Resampling.average)
        ds.update_tags(ns="rio_overview", resampling="average")

    a = da.values
    fin = a[np.isfinite(a)]
    with rasterio.open(out_tif) as ds:
        b = ds.bounds
        from rasterio.warp import transform_bounds
        ll = transform_bounds(ds.crs, "EPSG:4326", *b)
        stats = dict(
            crs=str(ds.crs), epsg=ds.crs.to_epsg(), width=ds.width, height=ds.height,
            res=ds.res[0], nodata=ds.nodata, bounds=tuple(round(v, 1) for v in b),
            lonlat=tuple(round(v, 4) for v in ll),
            mb=out_tif.stat().st_size / 1e6,
            n_finite=int(fin.size), pct_finite=100 * fin.size / a.size,
            dmin=float(fin.min()), dmax=float(fin.max()),
            n_ge_015=int((fin >= validate.DEPTH_MIN).sum()),
            p50=float(np.percentile(fin[fin >= validate.DEPTH_MIN], 50)),
            p99=float(np.percentile(fin[fin >= validate.DEPTH_MIN], 99)),
        )
    return stats


README = """# Sandy (2012) maximum flood depth — practice raster

`{fname}`

Modelled maximum water depth during Hurricane Sandy, Monmouth County / Raritan Bay,
New Jersey. SFINCS hindcast. **This is a practice dataset, not a validated hazard
layer** — see the caveats at the bottom before drawing any conclusion from it.

## Reading the file

| | |
|---|---|
| Format | GeoTIFF, single band, float32, DEFLATE-compressed, tiled, with overviews |
| **CRS** | **{crs} (EPSG:{epsg})** — UTM zone 18N, coordinates in **metres**, *not* degrees |
| Resolution | {res:.3f} m |
| Size | {width} x {height} px, {mb:.1f} MB |
| NoData | NaN (tagged in the header) — dry land and areas outside the model |
| Units | metres of water depth above the ground surface |

The CRS is the one thing most likely to trip you up. Opening this expecting
lat/lon gives corner coordinates like `561434, 4444626`; that is not corruption,
it is UTM in metres. QGIS/ArcGIS/rasterio all reproject on the fly. If you need
degrees (EPSG:4326) say so and I will ship a reprojected copy — better that than
resampling it yourself twice.

Extent: `{bounds}` in UTM, which is `{lonlat}` as (west, south, east, north) in degrees.

```python
import rioxarray
da = rioxarray.open_rasterio("{fname}", masked=True).squeeze()
da = da.where(da >= 0.15)          # see "wet threshold" below
da.rio.reproject("EPSG:4326")      # only if you actually need degrees
```

## What the values mean

- **Depth above ground**, not water-surface elevation. No datum conversion needed
  to use it as depth; it is already ground-relative.
- **Maximum over the whole simulation**, not a snapshot. Different cells peak at
  different times, so the map is not a state the system was ever in at one instant.
  That is normally what a damage model wants, but it is worth knowing.
- **Permanent water is masked out.** Bay, river and ocean cells are NaN, so the
  raster shows flooding on land rather than the full water column. Without this the
  file would report ~10 m "depths" over the Navesink and you would compute damages
  to the seabed.

Depth range in the file: {dmin:.2f} to {dmax:.2f} m. {n_finite:,} wet cells
({pct_finite:.2f}% of the grid). Median depth over the 0.15 m threshold is
{p50:.2f} m, 99th percentile {p99:.2f} m.

### Wet threshold

The raster floor is **0.05 m** (an artifact of how the downscale is built). Our own
scoring treats a cell as wet only at **>= 0.15 m**, which is {n_ge_015:,} cells.
Below that you are looking at numerical damp rather than flooding, and most damage
curves will happily assign losses to it. **Threshold at 0.15 m** unless you have a
specific reason not to. I left the 0.05 m values in the file rather than silently
deleting data, so the choice stays yours.

## Caveats — please read before trusting a number

1. **Known low bias.** Against surveyed high-water marks this model runs about
   **0.25 m low** on average (median estimator, 50 m search window). Damages
   computed from it will be *under*-estimates, and non-linearly so, because damage
   curves are steep near the low end.
2. **Hindcast, not a design event.** This is one storm reconstructed after the fact.
   It is not a return-period product and must not be read as one.
3. **Model still in development.** The domain, bathymetry and boundary conditions
   are actively being revised; this file is a snapshot from a frozen configuration
   kept for reference, not the current best model.
4. **Depth only.** No velocity, no duration, no wave action, no debris — all of
   which matter for real damage estimation.

Questions to Ty.
"""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model-dir", type=Path, default=V1_PREMIER)
    ap.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--stem", default=DEFAULT_STEM)
    a = ap.parse_args()

    out_tif = a.out_dir / f"{a.stem}_EPSG32618.tif"
    print(f"source : {a.model_dir}")
    print(f"target : {out_tif}\nexporting (masked, compressed) ...", flush=True)

    st = export(a.model_dir, out_tif, a.stem)

    readme = a.out_dir / "README.md"
    readme.write_text(README.format(fname=out_tif.name, **st))

    print("\n=== written ===")
    for k, v in st.items():
        print(f"  {k:12s} {v}")
    print(f"\n  {out_tif}\n  {readme}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
