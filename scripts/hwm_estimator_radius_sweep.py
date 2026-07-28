"""Is the v1->v2 HWM 'regression' a property of the model, or of the estimator?

validate.hwm_metrics scores a mark as `max(WSE) over a +/-50 m window, ground-capped`.
Sweep that radius from 0 (point sample) upward on both domains. If the two domains
agree at small radius and diverge as the window grows, the regression is the
estimator reacting to grid alignment, not the model holding more water.
"""
import numpy as np
import geopandas as gpd
import rioxarray
import pandas as pd
from pathlib import Path

# Write beside the other reports, not into whatever cwd this was launched from.
OUT = Path(__file__).resolve().parents[1] / "reports"
OUT.mkdir(parents=True, exist_ok=True)

DEPTH_MIN, GROUND_CAP = 0.05, 0.5
RUNS = {
    "v1": Path("/cache/home/tpj8/nj_sandy_sfincs/experiments/faber-waves-premier"),
    "v2": Path("/home/tpj8/nj_coast_sfincs/experiments/faber-waves-premier"),
    "v2cora": Path("/home/tpj8/nj_coast_sfincs/experiments/wave-cora"),
}
hwm = gpd.read_file(
    "/cache/home/tpj8/nj_sandy_sfincs/data/validation/sandy_hwms.geojson").to_crs(32618)
head = hwm["quality"].astype(float).values <= 2
obs = hwm["elev_m"].values
RADII = [0, 1, 2, 4, 8, 12, 16, 24]


def load(run_dir):
    h = rioxarray.open_rasterio(run_dir / "floodmap_hmax_lev3.tif",
                                masked=True).squeeze(drop=True)
    d = rioxarray.open_rasterio(run_dir / "subgrid" / "dep_subgrid_lev3.tif",
                                masked=True).squeeze(drop=True)
    h = h.rio.reproject(h.rio.crs)
    d = d.rio.reproject_match(h)
    h = h.where(d.values > -0.5)
    return h, d


rows = []
for tag, rd in RUNS.items():
    print(f"loading {tag} ...", flush=True)
    da_h, da_d = load(rd)
    depth, dep = da_h.values, da_d.values
    wse = dep + depth
    T = da_d.rio.transform()
    ny, nx = wse.shape
    for rad in RADII:
        mod = np.full(len(obs), np.nan)
        for k, (X, Y) in enumerate(zip(hwm.geometry.x.values, hwm.geometry.y.values)):
            col, row = int((X - T.c) / T.a), int((Y - T.f) / T.e)
            if not (0 <= row < ny and 0 <= col < nx):
                continue
            sl = (slice(max(0, row - rad), row + rad + 1),
                  slice(max(0, col - rad), col + rad + 1))
            ws, hh, dd = wse[sl], depth[sl], dep[sl]
            fl = (hh >= DEPTH_MIN) & (dd <= obs[k] + GROUND_CAP)
            if fl.any():
                mod[k] = np.nanmax(np.where(fl, ws, np.nan))
        m = head & np.isfinite(mod)
        r = mod[m] - obs[m]
        rows.append(dict(run=tag, rad_px=rad, rad_m=round(rad * abs(T.a), 1),
                         n_wet=int(m.sum()), bias=r.mean(),
                         rmse=float(np.sqrt((r ** 2).mean())),
                         within05=float(np.mean(np.abs(r) < 0.5))))
        print(f"   rad {rad:2d} ({rad*abs(T.a):5.1f} m)  n={m.sum():2d} "
              f"bias {r.mean():+.4f}  rmse {np.sqrt((r**2).mean()):.4f}", flush=True)
    del depth, dep, wse, da_h, da_d

df = pd.DataFrame(rows)
pd.set_option("display.width", 200)
piv = df.pivot(index="rad_m", columns="run", values="bias").round(4)
piv.columns = [f"bias_{c}" for c in piv.columns]
piv["d_v2_minus_v1"] = (piv["bias_v2"] - piv["bias_v1"]).round(4)
nw = df.pivot(index="rad_m", columns="run", values="n_wet")
nw.columns = [f"n_{c}" for c in nw.columns]
print("\n===== HWM bias vs estimator search radius (19 q<=2 bridge marks) =====")
print(piv.join(nw).to_string())
df.to_csv(OUT / "hwm_radius_sweep.csv", index=False)
print("\nwrote hwm_radius_sweep.csv")
