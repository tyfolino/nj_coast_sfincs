#!/usr/bin/env python3
"""Build the BED-ROUGHNESS variant land cover for `bed-baymanning`.

WHY THIS EXISTS
---------------
Every open-water cell in the model carries NLCD class 11 -> Manning n = 0.020, which is a
bare-sand / smooth-channel value. That is a defensible number for the shelf. It is not a
defensible number for Barnegat Bay, a shallow lagoon with extensive submerged aquatic
vegetation (eelgrass, widgeon grass) over mud and sand shoals, where published estuarine
values run 0.025-0.045.

The defect that motivates it is measured, not assumed (2026-07-28). At Barnegat Light,
just inside the inlet, the model's tidal range is right to 0.002 m (0.719 vs 0.721) -- the
inlet exchange is excellent. But 35 km up the lagoon at Mantoloking the model holds
0.401 m of range where the real bay damps to 0.167 m, and its tide arrives 58 min EARLY.

  right at the inlet + too energetic and too fast up-lagoon = too little DISSIPATION
  between the two, with the bathymetry already correct (mean depth 1.57 m vs the
  published ~1.5 m, and channels within 0.4 m of USACE soundings).

Friction is the first suspect. This script makes it a knob that can be turned in the
lagoon WITHOUT touching the ocean, the Raritan/Sandy Hook lobe or the Shrewsbury -- all of
which are separately tuned and, in the north lobe's case, already UNDER-forced. A global
open-water bump would confound those.

HOW
---
NLCD class 11 pixels inside the lagoon are re-coded to class 12, a code NLCD does not use,
and a copy of the reclass table maps 12 -> BAY_N. Everything else is byte-for-byte the
original raster, so the only thing that can change is the roughness of water that is
already inside Barnegat Bay.

⚠️ Roughness feeds `quadtree_subgrid.create`, so this requires a TEMPLATE REBUILD
(scripts/setup_baymanning_template.py), not a `prepare_experiment` forcing swap. The
domain seal is sha(z, mask) and excludes roughness, so the rebuilt template still audits
as `v2_barnegat` -- comparable to the premier by construction.

THE LAGOON MASK is a latitude-dependent threshold, not a polygon (project preference):
the barrier island runs roughly (-74.055, 40.05) at Mantoloking to (-74.10, 39.76) at
Barnegat Light, so a straight line in (lon, lat) separates lagoon from ocean, and a 0.004
deg (~340 m) western offset keeps surf-zone water out. Because only class-11 pixels are
touched, a slightly generous box cannot recode land.

Run:  NJ_ROOT=$PWD PYTHONPATH=$PWD python scripts/build_bay_manning.py
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyproj
import rioxarray as rxr

from nj_sfincs.config import DATA

BAY_N = 0.035          # SAV-dominated shallow lagoon; open water elsewhere stays 0.020
BAY_CLASS = 12         # unused in NLCD -> safe spare code
OPEN_WATER = 11

SRC_TIF = DATA / "roughness" / "nlcd_2012.tif"
OUT_TIF = DATA / "roughness" / "nlcd_2012_baymanning.tif"
SRC_CSV = DATA / "roughness" / "NLCD_CONUS_mapping.csv"
OUT_CSV = DATA / "roughness" / "NLCD_CONUS_mapping_baymanning.csv"

# lagoon box (lon/lat). South to the v2 domain edge, north to the Metedeconk/Point Pleasant arm.
LAT_MIN, LAT_MAX = 39.70, 40.10
LON_WEST = -74.22                      # mainland side
BARRIER = ((-74.055, 40.05), (-74.10, 39.76))   # two points on the barrier island
BARRIER_OFFSET = 0.004                 # deg west of the barrier line


def lagoon_mask(lon: np.ndarray, lat: np.ndarray) -> np.ndarray:
    (x0, y0), (x1, y1) = BARRIER
    lon_bar = x0 + (lat - y0) * ((x1 - x0) / (y1 - y0))
    return ((lat > LAT_MIN) & (lat < LAT_MAX)
            & (lon > LON_WEST) & (lon < lon_bar - BARRIER_OFFSET))


def main() -> int:
    if not SRC_TIF.exists():
        sys.exit(f"missing {SRC_TIF}")

    r = rxr.open_rasterio(SRC_TIF, masked=False)
    band = r.isel(band=0)
    v = band.values.copy()
    print(f"source {SRC_TIF.name}: {v.shape}, crs {r.rio.crs.to_string()[:40]}...")

    # Pixel centres -> lon/lat. Only the lagoon's own window is transformed; the full
    # raster is 78M pixels and all of it outside the window is irrelevant by construction.
    xs, ys = band.x.values, band.y.values
    to_ll = pyproj.Transformer.from_crs(r.rio.crs, 4326, always_xy=True)
    to_src = pyproj.Transformer.from_crs(4326, r.rio.crs, always_xy=True)
    cx, cy = to_src.transform(
        [LON_WEST, LON_WEST, BARRIER[0][0], BARRIER[0][0]],
        [LAT_MIN, LAT_MAX, LAT_MIN, LAT_MAX])
    pad = 5000.0
    ix = np.where((xs >= min(cx) - pad) & (xs <= max(cx) + pad))[0]
    iy = np.where((ys >= min(cy) - pad) & (ys <= max(cy) + pad))[0]
    if ix.size == 0 or iy.size == 0:
        sys.exit("lagoon window does not intersect the land-cover raster")
    print(f"lagoon window: {iy.size} rows x {ix.size} cols "
          f"({100 * iy.size * ix.size / v.size:.2f}% of the raster)")

    X, Y = np.meshgrid(xs[ix], ys[iy])
    lon, lat = to_ll.transform(X, Y)
    sub = v[np.ix_(iy, ix)]
    sel = lagoon_mask(lon, lat) & (sub == OPEN_WATER)
    n_recode = int(sel.sum())
    if n_recode == 0:
        sys.exit("BUG: no open-water pixels fell inside the lagoon mask")

    sub[sel] = BAY_CLASS
    v[np.ix_(iy, ix)] = sub
    total_water = int((band.values == OPEN_WATER).sum())
    print(f"re-coded {n_recode} open-water pixels -> class {BAY_CLASS} "
          f"({100 * n_recode / total_water:.1f}% of all class-{OPEN_WATER} pixels; "
          f"{n_recode * 30 * 30 / 1e6:.1f} km2)")

    out = band.copy(data=v).expand_dims("band")
    out.rio.write_crs(r.rio.crs, inplace=True)
    # NOTE the name is `*.tmp.tif`, not `*.tif.tmp`: rasterio picks its driver from the
    # EXTENSION, so a trailing .tmp fails with "Unable to detect driver".
    tmp = OUT_TIF.with_name(OUT_TIF.stem + ".tmp.tif")
    out.rio.to_raster(tmp, compress="deflate", tiled=True)
    tmp.replace(OUT_TIF)   # atomic: a truncated raster reads back clean, cf. floodmap cache
    print(f"wrote {OUT_TIF} ({OUT_TIF.stat().st_size / 1e6:.1f} MB)")

    # reclass table: identical, plus the new class
    t = pd.read_csv(SRC_CSV)
    if BAY_CLASS in set(t["NLCD"]):
        sys.exit(f"class {BAY_CLASS} already present in {SRC_CSV.name} — pick another code")
    row = {"NLCD": BAY_CLASS, "description": "Open Water - Barnegat lagoon (SAV)",
           "landuse": BAY_CLASS, "N": BAY_N}
    pd.concat([t, pd.DataFrame([row])], ignore_index=True).to_csv(OUT_CSV, index=False)
    print(f"wrote {OUT_CSV}: class {BAY_CLASS} -> n = {BAY_N} "
          f"(class {OPEN_WATER} unchanged at {float(t.loc[t['NLCD'] == OPEN_WATER, 'N'].iloc[0])})")

    # Verify by reading back, not by trusting the write.
    chk = rxr.open_rasterio(OUT_TIF, masked=False).isel(band=0).values
    same = int((chk != band.values).sum())
    print(f"\nverify: {same} pixels differ from the source "
          f"({'OK' if same == n_recode else '!! MISMATCH'}), "
          f"class-{BAY_CLASS} count {int((chk == BAY_CLASS).sum())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
