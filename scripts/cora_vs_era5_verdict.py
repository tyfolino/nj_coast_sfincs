"""CORA vs ERA5 as a SnapWave boundary — the verdict under the `median` HWM estimator.

Three questions, answered separately because they have different answers:

A. WHAT EACH PRODUCT IMPOSES at the 7 SnapWave support points, and whether it is
   physically admissible there (Hs vs the depth-limited breaking cap at that point's
   own depth).
B. HOW EACH COMPARES TO THE BUOY at NDBC 44025's OWN location and depth. This is the
   only apples-to-apples skill test; comparing a nearshore boundary value to an
   offshore buoy conflates shelf transformation with bias.
C. WHAT IT DOES TO THE SCORE on the native-95 mark set (the valid v2-internal
   comparison -- bridge-31 is Monmouth-only and barely sees the southern boundary),
   under `median` rather than the unbounded `max`.

Writes reports/cora_vs_era5_verdict.csv.
"""
import os
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import xarray as xr

ROOT = Path(os.environ.get("NJ_ROOT", Path(__file__).resolve().parents[1]))
DATA = ROOT / "data"
DEPTH_MIN, GROUND_CAP, RAD = 0.05, 0.5, 8
CONTROL, PERTURB = "faber-waves-premier", "wave-cora"
PEAK = pd.Timestamp("2012-10-30 00:00")
GAMMA = 0.78  # classic depth-limited breaking index Hs/h


# ── A. what each product imposes at the support points ────────────────────────
def imposed():
    rows = []
    for arm in (CONTROL, PERTURB):
        d = exp_root() / arm
        bnd = np.atleast_2d(np.loadtxt(d / "snapwave.bnd"))
        hs = np.loadtxt(d / "snapwave.bhs")
        k = int(np.argmax(hs[:, 1:].max(axis=1)))
        rows.append(dict(arm=arm, n_pts=bnd.shape[0],
                         hs_min=round(float(hs[k, 1:].min()), 3),
                         hs_max=round(float(hs[k, 1:].max()), 3),
                         alongshore_spread=round(
                             float(hs[k, 1:].max() - hs[k, 1:].min()), 3)))
    return pd.DataFrame(rows), None


def admissibility():
    """Hs/h at each support point, using the CORA file's own depth at that point."""
    cds = xr.open_dataset(DATA / "waves" / "cora_waves_nj.nc")
    slon, slat = cds["lon"].values, cds["lat"].values
    sdep = cds["depth"].values
    import pyproj
    from nj_sfincs import domain as _domain
    tf = pyproj.Transformer.from_crs(_domain.active().epsg, 4326, always_xy=True)

    out = []
    for arm in (CONTROL, PERTURB):
        d = exp_root() / arm
        bnd = np.atleast_2d(np.loadtxt(d / "snapwave.bnd"))
        hs = np.loadtxt(d / "snapwave.bhs")
        k = int(np.argmax(hs[:, 1:].max(axis=1)))
        plon, plat = tf.transform(bnd[:, 0], bnd[:, 1])
        for i, (lo, la) in enumerate(zip(plon, plat)):
            dd = np.hypot((slon - lo) * np.cos(np.deg2rad(la)), slat - la) * 111_000.0
            j = int(np.argmin(dd))
            h = float(abs(sdep[j]))
            H = float(hs[k, 1 + i])
            out.append(dict(arm=arm, pt=i, lon=round(lo, 4), lat=round(la, 4),
                            depth_m=round(h, 1), imposed_hs=round(H, 3),
                            breaking_cap=round(GAMMA * h, 2),
                            gamma=round(H / h, 3), admissible=bool(H <= GAMMA * h)))
    return pd.DataFrame(out)


# ── B. against the buoy, at the buoy's own location and depth ─────────────────
def buoy():
    obs = xr.open_dataset(DATA / "waves" / "ndbc_sandy_44025.nc")
    blon = float(obs["lon"].values.ravel()[0])
    blat = float(obs["lat"].values.ravel()[0])
    o = pd.Series(obs["hs"].values.ravel(), index=pd.to_datetime(obs["time"].values))

    cds = xr.open_dataset(DATA / "waves" / "cora_waves_nj.nc")
    dd = np.hypot((cds["lon"].values - blon) * np.cos(np.deg2rad(blat)),
                  cds["lat"].values - blat) * 111_000.0
    j = int(np.argmin(dd))
    c = pd.Series(cds["hs"].values[:, j], index=pd.to_datetime(cds["time"].values))
    c_dist_km, c_depth = dd[j] / 1000, float(abs(cds["depth"].values[j]))

    eds = xr.open_dataset(DATA / "waves" / "era5_waves_nj.nc")
    e = eds["hs"].sel(x=blon, y=blat, method="nearest")
    e_dist_km = np.hypot((float(e.x) - blon) * np.cos(np.deg2rad(blat)),
                         float(e.y) - blat) * 111.0
    e = pd.Series(e.values, index=pd.to_datetime(eds["time"].values))

    print(f"NDBC 44025 at lon {blon:.3f} lat {blat:.3f}")
    print(f"  CORA nearest node : {c_dist_km:.1f} km away, source depth {c_depth:.1f} m")
    print(f"  ERA5 nearest cell : {e_dist_km:.1f} km away (0.5 deg grid)")

    win = slice("2012-10-28", "2012-10-31")
    oo, cc, ee = o[win], c[win], e[win]
    ci = cc.reindex(oo.index.union(cc.index)).interpolate("time").reindex(oo.index)
    ei = ee.reindex(oo.index.union(ee.index)).interpolate("time").reindex(oo.index)
    m = np.isfinite(oo) & np.isfinite(ci) & np.isfinite(ei)

    rows = [dict(source="NDBC 44025 (obs)", peak_hs=round(float(oo.max()), 2),
                 peak_time=str(oo.idxmax()), bias=0.0, rmse=0.0, n=int(m.sum())),
            dict(source="CORA @ buoy", peak_hs=round(float(cc.max()), 2),
                 peak_time=str(cc.idxmax()),
                 bias=round(float((ci[m] - oo[m]).mean()), 3),
                 rmse=round(float(np.sqrt(((ci[m] - oo[m]) ** 2).mean())), 3),
                 n=int(m.sum())),
            dict(source="ERA5 @ buoy", peak_hs=round(float(ee.max()), 2),
                 peak_time=str(ee.idxmax()),
                 bias=round(float((ei[m] - oo[m]).mean()), 3),
                 rmse=round(float(np.sqrt(((ei[m] - oo[m]) ** 2).mean())), 3),
                 n=int(m.sum()))]
    return pd.DataFrame(rows), c_depth


# ── C. the score, native-95, under `median` ───────────────────────────────────
def rescore():
    import rioxarray
    hwm = gpd.read_file(DATA / "validation" / "sandy_hwms.geojson").to_crs(32618)
    obs = hwm["elev_m"].values
    head = hwm["quality"].astype(float).values <= 2
    rows = []
    for arm in (CONTROL, PERTURB):
        rd = exp_root() / arm
        h = rioxarray.open_rasterio(rd / "floodmap_hmax_lev3.tif",
                                    masked=True).squeeze(drop=True)
        d = rioxarray.open_rasterio(rd / "subgrid" / "dep_subgrid_lev3.tif",
                                    masked=True).squeeze(drop=True)
        h = h.rio.reproject(h.rio.crs)
        d = d.rio.reproject_match(h)
        h = h.where(d.values > -0.5)
        depth, dep = h.values, d.values
        wse = dep + depth
        T = d.rio.transform()
        ny, nx = wse.shape
        est = {k: np.full(len(obs), np.nan) for k in ("max", "median")}
        for k, (X, Y) in enumerate(zip(hwm.geometry.x.values, hwm.geometry.y.values)):
            col, row = int((X - T.c) / T.a), int((Y - T.f) / T.e)
            if not (0 <= row < ny and 0 <= col < nx):
                continue
            r0, c0 = max(0, row - RAD), max(0, col - RAD)
            sl = (slice(r0, row + RAD + 1), slice(c0, col + RAD + 1))
            ws, hh, ddp = wse[sl], depth[sl], dep[sl]
            fl = (hh >= DEPTH_MIN) & (ddp <= obs[k] + GROUND_CAP)
            if not fl.any():
                continue
            est["max"][k] = np.nanmax(ws[fl])
            est["median"][k] = np.nanmedian(ws[fl])
        rec = dict(arm=arm)
        for e, mod in est.items():
            mm = head & np.isfinite(mod)
            r = mod[mm] - obs[mm]
            rec[f"n_{e}"] = int(mm.sum())
            rec[f"bias_{e}"] = round(float(r.mean()), 4)
            rec[f"rmse_{e}"] = round(float(np.sqrt((r ** 2).mean())), 4)
        rows.append(rec)
        del depth, dep, wse, h, d
    return pd.DataFrame(rows)


if __name__ == "__main__":
    pd.set_option("display.width", 200)
    pd.set_option("display.max_columns", 30)

    print("=" * 78)
    print("A. WHAT EACH PRODUCT IMPOSES AT THE SNAPWAVE SUPPORT POINTS")
    print("=" * 78)
    imp, _ = imposed()
    print(imp.to_string(index=False))
    adm = admissibility()
    print("\nAdmissibility at each point's own depth (cap = 0.78 x h):")
    print(adm.to_string(index=False))
    print("\nadmissible points: " + ", ".join(
        f"{a} {int(g.admissible.sum())}/{len(g)}" for a, g in adm.groupby("arm")))

    print("\n" + "=" * 78)
    print("B. AGAINST THE BUOY — NDBC 44025, ITS OWN LOCATION AND DEPTH")
    print("=" * 78)
    b, cdep = buoy()
    print(b.to_string(index=False))

    print("\n" + "=" * 78)
    print("C. THE SCORE — native-95 marks, 50 m window, max vs median")
    print("=" * 78)
    rs = rescore()
    print(rs.to_string(index=False))
    print(f"\nCORA - premier   bias_max {rs.bias_max.diff().iloc[-1]:+.4f}   "
          f"bias_median {rs.bias_median.diff().iloc[-1]:+.4f}")
    print(f"                 rmse_max {rs.rmse_max.diff().iloc[-1]:+.4f}   "
          f"rmse_median {rs.rmse_median.diff().iloc[-1]:+.4f}")

    adm.to_csv(ROOT / "reports" / "cora_vs_era5_admissibility.csv", index=False)
    b.to_csv(ROOT / "reports" / "cora_vs_era5_buoy.csv", index=False)
    rs.to_csv(ROOT / "reports" / "cora_vs_era5_verdict.csv", index=False)
    print("\nwrote reports/cora_vs_era5_{admissibility,buoy,verdict}.csv")
