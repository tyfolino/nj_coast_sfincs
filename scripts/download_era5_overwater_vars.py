"""Download the ERA5 surface-layer fields needed to re-diagnose 10 m wind over WATER.

WHY (2026-08-03). ERA5's ``u10``/``v10`` are DIAGNOSTIC: they are reconstructed from the
surface-layer profile using ERA5's own LOCAL surface roughness. Barnegat Bay is 4-6 km
wide and ERA5's grid is 0.25 deg (~28 km), so the cells covering the bay are LAND cells
and their 10 m wind is slowed by Pine Barrens forest roughness. SFINCS then applies a
MARINE drag law (`cdnrb=3`) to that land-diagnosed wind. That is an internal
inconsistency in the forcing chain, not a tuning knob.

Measured consequence: the bay-cell/adjacent-ocean-cell wind ratio is 0.77-0.81, and the
model reproduces only 55% of the observed along-bay tilt. Since setup ~ U^2, 0.55 implies
a wind ratio of 0.74. Those agree.

⚠️ THIS SCRIPT WRITES A SEPARATE FILE AND MUST NEVER OVERWRITE
``era5_nj_sandy_2012_10_28_31.nc``. Every arm on disk derives its wind forcing from that
file; replacing it would silently change the forcing under already-scored runs and
destroy comparability.

Variables (all on the SAME grid/window as the original request, so they align exactly):
  zust  friction_velocity            [m s-1]  -> the profile anchor; what we re-diagnose from
  fsr   forecast_surface_roughness   [m]      -> EVIDENCE: shows the bay cells carry a
                                                 land roughness, orders of magnitude above
                                                 a Charnock sea surface
  lsm   land_sea_mask                [0-1]    -> EVIDENCE: shows ERA5 classifies the bay
                                                 cells as land in the first place

`fsr` and `lsm` are not used by the conversion; they are what turn "ERA5 is wrong over the
bay" from an assertion into a measurement. Keep them.

Prerequisites: ~/.cdsapirc with a CDS token; ERA5 single-levels terms accepted.
"""

from pathlib import Path

import cdsapi
import xarray as xr

OUTPUT_DIR = Path(__file__).resolve().parents[1] / "data" / "era5"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

#: MUST match download_era5_cds.py exactly or the fields will not align with the wind.
NJ_AREA = [42.0, -76.0, 37.0, -72.0]          # [North, West, South, East]
YEAR, MONTH, DAYS = "2012", "10", ["28", "29", "30", "31"]

RAW = OUTPUT_DIR / "era5_nj_sandy_sfc_raw.nc"
OUT = OUTPUT_DIR / "era5_nj_sandy_sfc.nc"

ORIGINAL = OUTPUT_DIR / "era5_nj_sandy_2012_10_28_31.nc"


def main() -> int:
    if OUT.exists():
        print(f"{OUT} exists — delete it to re-download.")
        return 0

    request = {
        "product_type": ["reanalysis"],
        "variable": [
            "friction_velocity",
            "forecast_surface_roughness",
            "land_sea_mask",
        ],
        "year": [YEAR],
        "month": [MONTH],
        "day": DAYS,
        "time": [f"{h:02d}:00" for h in range(24)],
        "data_format": "netcdf",
        "download_format": "unarchived",
        "area": NJ_AREA,
    }

    print(f"Requesting ERA5 surface-layer fields ->\n  {RAW}")
    cdsapi.Client().retrieve("reanalysis-era5-single-levels", request, str(RAW))

    ds = xr.open_dataset(RAW)
    print(f"  raw variables: {list(ds.data_vars)}")
    print(f"  raw coords:    {list(ds.coords)}")

    rename = {}
    for src, dst in [("valid_time", "time"), ("latitude", "y"), ("longitude", "x")]:
        if src in ds.variables or src in ds.dims:
            rename[src] = dst
    ds = ds.rename(rename)
    if "y" in ds.coords and ds["y"].values[0] > ds["y"].values[-1]:
        ds = ds.isel(y=slice(None, None, -1))       # north-up -> ascending, as the wind file

    # Alignment is the whole point — assert it rather than hope.
    if ORIGINAL.exists():
        o = xr.open_dataset(ORIGINAL)
        for c in ("y", "x"):
            assert ds.sizes[c] == o.sizes[c], (
                f"{c} size {ds.sizes[c]} != wind file {o.sizes[c]} — grids differ, "
                "the conversion would silently interpolate"
            )
        print(f"  grid matches {ORIGINAL.name}: y={ds.sizes['y']} x={ds.sizes['x']}")

    ds.to_netcdf(OUT)
    print(f"\nwrote {OUT}")
    print(f"  variables: {list(ds.data_vars)}")
    print(f"\n⚠️ {ORIGINAL.name} is UNTOUCHED — every scored arm depends on it.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
