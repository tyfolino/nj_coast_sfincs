"""Per-mark v1-vs-v2 HWM sampling diagnostic on the 31 bridge marks.

Replicates validate.load_floodmap + validate.hwm_metrics' estimator (max WSE over a
50 m window, ground-capped) on BOTH domains, and additionally records the POINT-sampled
WSE and the wet-cell count in the window -- so we can separate:
   (a) the model genuinely holding more water at the mark  -> point WSE moves too
   (b) the window-max estimator finding a higher cell because v2 wets more cells
       -> point WSE flat, wet-count up, window max up
"""
import numpy as np
import geopandas as gpd
import rioxarray
import pandas as pd
import os
from pathlib import Path

# Resolve against the repo root, not whatever cwd this was launched from. Every path
# below is repo-relative: v1 and v2 now live in ONE repo, namespaced by domain
# (experiments/<domain>/<arm>), where they used to be absolute paths into two.
ROOT = Path(os.environ.get("NJ_ROOT", Path(__file__).resolve().parents[1]))
OUT = ROOT / "reports"
OUT.mkdir(parents=True, exist_ok=True)

DEPTH_MIN = 0.05
GROUND_CAP = 0.5

RUNS = {
    "v1": ROOT / "experiments" / "v1_monmouth" / "faber-waves-premier",
    "v2": ROOT / "experiments" / "v2_barnegat" / "faber-waves-premier",
    "v2cora": ROOT / "experiments" / "v2_barnegat" / "wave-cora",
}
HWM_V1 = ROOT / "data" / "validation" / "v1_monmouth" / "sandy_hwms.geojson"

hwm = gpd.read_file(HWM_V1).to_crs(32618)
ids = hwm["hwm_id"].astype(str).values
print(f"v1 mark file: {len(hwm)} marks; q<=2: {(hwm['quality'].astype(float) <= 2).sum()}")


def load(run_dir):
    """Exactly validate.load_floodmap's raster half."""
    da_hmax = rioxarray.open_rasterio(run_dir / "floodmap_hmax_lev3.tif",
                                      masked=True).squeeze(drop=True)
    da_dep = rioxarray.open_rasterio(run_dir / "subgrid" / "dep_subgrid_lev3.tif",
                                     masked=True).squeeze(drop=True)
    da_hmax = da_hmax.rio.reproject(da_hmax.rio.crs)      # de-rotate to north-up
    da_dep = da_dep.rio.reproject_match(da_hmax)
    da_hmax = da_hmax.where(da_dep.values > -0.5)         # drop deep ocean
    return da_hmax, da_dep


def sample(run_dir, tag):
    da_hmax, da_dep = load(run_dir)
    depth, dep_arr = da_hmax.values, da_dep.values
    wse = dep_arr + depth
    T = da_dep.rio.transform()
    ny, nx = wse.shape
    rad = int(round(50 / abs(T.a)))
    print(f"  [{tag}] grid {ny}x{nx}  res {T.a:.3f}  rad {rad}px")
    out = []
    for k, (X, Y) in enumerate(zip(hwm.geometry.x.values, hwm.geometry.y.values)):
        col, row = int((X - T.c) / T.a), int((Y - T.f) / T.e)
        obs = float(hwm["elev_m"].values[k])
        rec = dict(hwm_id=ids[k], obs=obs, q=float(hwm["quality"].values[k]),
                   on_grid=bool(0 <= row < ny and 0 <= col < nx))
        if rec["on_grid"]:
            sl = (slice(max(0, row - rad), row + rad + 1),
                  slice(max(0, col - rad), col + rad + 1))
            ws, hh, dd = wse[sl], depth[sl], dep_arr[sl]
            rec["n_win"] = int(hh.size)
            rec["n_wet"] = int(np.nansum(hh >= DEPTH_MIN))
            if np.isfinite(dd).any():
                rec["ground_min"] = float(np.nanmin(dd))
                rec["ground_max"] = float(np.nanmax(dd))
            flooded = (hh >= DEPTH_MIN) & (dd <= obs + GROUND_CAP)
            rec["n_flooded"] = int(np.nansum(flooded))
            if flooded.any():
                rec["wse_win"] = float(np.nanmax(np.where(flooded, ws, np.nan)))
                # where in the window did the max come from, and how deep is it?
                idx = np.unravel_index(np.nanargmax(np.where(flooded, ws, np.nan)),
                                       ws.shape)
                rec["argmax_dist_m"] = float(
                    np.hypot(idx[0] - (row - sl[0].start),
                             idx[1] - (col - sl[1].start)) * abs(T.a))
                rec["argmax_h"] = float(hh[idx])
            pr, pc = row - sl[0].start, col - sl[1].start
            rec["h_pt"] = float(hh[pr, pc])
            rec["dep_pt"] = float(dd[pr, pc])
            rec["wse_pt"] = float(ws[pr, pc]) if hh[pr, pc] >= DEPTH_MIN else np.nan
        out.append(rec)
    del depth, dep_arr, wse, da_hmax, da_dep
    return pd.DataFrame(out).set_index("hwm_id")


res = {}
for k, d in RUNS.items():
    print(f"loading {k} ...", flush=True)
    res[k] = sample(d, k)
    print(f"  on_grid {res[k].on_grid.sum()}  window-wet {res[k].wse_win.notna().sum()}"
          f"  point-wet {res[k].wse_pt.notna().sum()}")

a, b = res["v1"], res["v2"]
head = a.q <= 2
cmp = pd.DataFrame({
    "obs": a.obs,
    "v1_wse": a.wse_win, "v2_wse": b.wse_win,
    "v1_pt": a.wse_pt, "v2_pt": b.wse_pt,
    "v1_nwet": a.n_wet, "v2_nwet": b.n_wet,
    "v1_gmin": a.ground_min, "v2_gmin": b.ground_min,
    "v1_dist": a.argmax_dist_m, "v2_dist": b.argmax_dist_m,
})
cmp["d_wse"] = cmp.v2_wse - cmp.v1_wse
cmp["d_pt"] = cmp.v2_pt - cmp.v1_pt
cmp["d_nwet"] = cmp.v2_nwet - cmp.v1_nwet
cmp["d_gmin"] = cmp.v2_gmin - cmp.v1_gmin
cmp = cmp[head]

pd.set_option("display.width", 250)
pd.set_option("display.max_columns", 40)
print("\n===== per-mark, q<=2, sorted by d_wse =====")
print(cmp.sort_values("d_wse", ascending=False).round(3).to_string())

w = cmp.dropna(subset=["v1_wse", "v2_wse"])
print(f"\n--- WINDOW-MAX estimator (what the score uses), marks wet in both: {len(w)}")
print(f"    v1 bias {(w.v1_wse - w.obs).mean():+.4f}   v2 bias {(w.v2_wse - w.obs).mean():+.4f}"
      f"   delta {w.d_wse.mean():+.4f}")
p = cmp.dropna(subset=["v1_pt", "v2_pt"])
print(f"--- POINT sample (no window), marks wet in both: {len(p)}")
print(f"    v1 bias {(p.v1_pt - p.obs).mean():+.4f}   v2 bias {(p.v2_pt - p.obs).mean():+.4f}"
      f"   delta {p.d_pt.mean():+.4f}")
print(f"\nmean d_nwet: {cmp.d_nwet.mean():+.1f} wet cells of {a.n_win.iloc[0]:.0f} in window")
print(f"mean d_gmin: {cmp.d_gmin.mean():+.4f} m (lowest bed in window)")
print(f"mean argmax offset from mark:  v1 {cmp.v1_dist.mean():.1f} m   v2 {cmp.v2_dist.mean():.1f} m")
print(f"corr(d_wse, d_nwet) = {w.d_wse.corr(w.d_nwet):.3f}")
print(f"corr(d_wse, d_gmin) = {w.d_wse.corr(w.d_gmin):.3f}")
print(f"corr(d_wse, d_pt)   = {w.d_wse.corr(w.d_pt):.3f}")

cmp.to_csv(OUT / "bridge31_v1_vs_v2_marks.csv")
print("\nwrote bridge31_v1_vs_v2_marks.csv")
