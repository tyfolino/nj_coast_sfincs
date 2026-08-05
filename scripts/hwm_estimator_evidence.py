"""Pick the HWM estimator on evidence, not on which answer it gives.

Two independent axes decide it:

1. HORIZONTAL ACCURACY -> is a search window justified at all?
   reports/hwm_metadata.csv (from fetch_hwm_metadata.py) says 94/95 marks, and
   ALL 64 q<=2 marks, were located by "Map (digital or paper)" -- the lowest-
   accuracy method in the STN vocabulary. The coordinates are NOT survey-grade,
   so a window IS justified and `nearest` (which trusts the coordinate to one
   6.25 m cell) is NOT.

   But an unknown location inside the window calls for a CENTRAL statistic over
   the plausible positions. `max` asks "the highest water anywhere it could have
   been", which is biased upward BY CONSTRUCTION and whose bias GROWS with the
   positional uncertainty. That is the opposite of what uncertainty should do.

2. MARK TYPE -> is the observation even a stillwater level?
   53 seed lines + 34 debris lines vs 8 mud lines, all "Coastal", `stillwater`
   null throughout. Debris and seed lines record the highest excursion INCLUDING
   wave runup; SFINCS zsmax is a stillwater level. If debris/seed marks sit
   systematically above mud marks, a negative model bias against them is expected
   physics, not under-forcing -- and that changes how the sign is read.

Writes reports/hwm_estimator_evidence.csv.
"""
import os
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rioxarray

ROOT = Path(os.environ.get("NJ_ROOT", Path(__file__).resolve().parents[1]))

# Import the wet threshold from validate rather than re-typing it: production is 0.15,
# and this script's first draft used 0.05, which put every number ~0.02 m off the
# scorer's. Same reason hwm_estimator_rescore_arms.py imports it.
import sys as _sys  # noqa: E402
_sys.path.insert(0, str(ROOT))
from nj_sfincs.config import exp_root  # noqa: E402
from nj_sfincs.validate import DEPTH_MIN  # noqa: E402

GROUND_CAP, RAD = 0.5, 8
RUN = exp_root() / "faber-waves-premier"


def main():
    hwm = gpd.read_file(ROOT / "data" / "validation" / "sandy_hwms.geojson").to_crs(32618)
    meta = pd.read_csv(ROOT / "reports" / "hwm_metadata.csv")
    obs = hwm["elev_m"].values

    h = rioxarray.open_rasterio(RUN / "floodmap_hmax_lev3.tif",
                                masked=True).squeeze(drop=True)
    d = rioxarray.open_rasterio(RUN / "subgrid" / "dep_subgrid_lev3.tif",
                                masked=True).squeeze(drop=True)
    h = h.rio.reproject(h.rio.crs)
    d = d.rio.reproject_match(h)
    h = h.where(d.values > -0.5)
    depth, dep = h.values, d.values
    wse = dep + depth
    T = d.rio.transform()
    ny, nx = wse.shape

    est = {k: np.full(len(obs), np.nan) for k in ("max", "median", "nearest")}
    spread = np.full(len(obs), np.nan)   # p90-p10 of WSE in the window
    for k, (X, Y) in enumerate(zip(hwm.geometry.x.values, hwm.geometry.y.values)):
        col, row = int((X - T.c) / T.a), int((Y - T.f) / T.e)
        if not (0 <= row < ny and 0 <= col < nx):
            continue
        r0, c0 = max(0, row - RAD), max(0, col - RAD)
        sl = (slice(r0, row + RAD + 1), slice(c0, col + RAD + 1))
        ws, hh, dd = wse[sl], depth[sl], dep[sl]
        fl = (hh >= DEPTH_MIN) & (dd <= obs[k] + GROUND_CAP)
        if not fl.any():
            continue
        v = ws[fl]
        est["max"][k] = np.nanmax(v)
        est["median"][k] = np.nanmedian(v)
        spread[k] = np.nanpercentile(v, 90) - np.nanpercentile(v, 10)
        rr, cc = np.nonzero(fl)
        j = int(np.argmin((rr - (row - r0)) ** 2 + (cc - (col - c0)) ** 2))
        est["nearest"][k] = ws[rr[j], cc[j]]

    df = pd.DataFrame({
        "hwm_id": hwm["hwm_id"].astype(int).values,
        "obs": obs, "quality": hwm["quality"].astype(float).values,
        "wse_spread_p90_p10": spread,
        **{f"res_{k}": v - obs for k, v in est.items()},
    }).merge(meta[["hwm_id", "hwm_type", "hcollect", "waterbody"]], on="hwm_id", how="left")
    df.to_csv(ROOT / "reports" / "hwm_estimator_evidence.csv", index=False)

    pd.set_option("display.width", 220)
    q = df[df.quality <= 2]
    print(f"=== v2 premier, {len(q)} q<=2 marks of {len(df)} ===")

    print("\n--- AXIS 1: how much does the WSE actually vary inside a 50 m window? ---")
    print("    (if the window straddles hydraulically distinct water, `max` is")
    print("     sampling a DIFFERENT feature, not positional uncertainty)")
    print(q["wse_spread_p90_p10"].describe().round(3).to_string())
    big = (q["wse_spread_p90_p10"] > 0.25).sum()
    print(f"    marks whose window spans >0.25 m of WSE: {big} of {len(q)} "
          f"({100*big/len(q):.0f}%)")

    print("\n--- AXIS 2: residual by mark type (runup contamination test) ---")
    for e in ("median", "nearest", "max"):
        g = q.groupby("hwm_type")[f"res_{e}"].agg(["count", "mean", "std"]).round(3)
        print(f"\n  estimator = {e}")
        print(g.to_string())

    print("\n--- observed ELEVATION by mark type (independent of any model) ---")
    print(q.groupby("hwm_type")["obs"].agg(["count", "mean", "std"]).round(3).to_string())


if __name__ == "__main__":
    main()
