"""Does the arm ranking survive a radius-stable HWM estimator?

The campaign selected level arms by reducing a POSITIVE pooled HWM bias (+0.32 m for
the premier). That bias is produced by `max WSE over a +/-50 m window`, which is
unbounded in the radius. Under every radius-stable estimator the premier is NEGATIVE.
If the sign flips, "reduce the water level" was the wrong direction and the ranking
may invert.

Scored on the 31-mark v1 set (q<=2) so v1 and v2 arms are directly comparable.
"""
import numpy as np
import geopandas as gpd
import rioxarray
import pandas as pd
from pathlib import Path

# Write beside the other reports, not into whatever cwd this was launched from.
OUT = Path(__file__).resolve().parents[1] / "reports"
OUT.mkdir(parents=True, exist_ok=True)

# Take the wet threshold FROM validate so this cannot drift from the scorer. It is
# 0.15 m, not the 0.05 this script's first draft used. The difference is <=0.02 m on
# every number here (v1 premier max@50m: 0.3217 at 0.05, 0.3184 at 0.15 — the latter
# reproducing the frozen campaign's published 0.318 exactly).
import sys as _sys  # noqa: E402
_sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from nj_sfincs.validate import DEPTH_MIN  # noqa: E402

GROUND_CAP, RAD = 0.5, 8   # RAD 8 px = 50 m, the production radius
V1 = Path("/cache/home/tpj8/nj_sandy_sfincs/experiments")
V2 = Path("/home/tpj8/nj_coast_sfincs/experiments")
ARMS = [
    ("v1", "faber-waves-premier", V1 / "faber-waves-premier"),
    ("v1", "tide-shift", V1 / "tide-shift"),
    ("v1", "wave-deep30", V1 / "wave-deep30"),
    ("v1", "wave-deep30+tide-shift", V1 / "wave-deep30+tide-shift"),
    ("v2", "faber-waves-premier", V2 / "faber-waves-premier"),
    ("v2", "wave-cora", V2 / "wave-cora"),
]
hwm = gpd.read_file(
    "/cache/home/tpj8/nj_sandy_sfincs/data/validation/sandy_hwms.geojson").to_crs(32618)
head = hwm["quality"].astype(float).values <= 2
obs = hwm["elev_m"].values
XY = list(zip(hwm.geometry.x.values, hwm.geometry.y.values))

rows = []
for dom, name, rd in ARMS:
    print(f"scoring {dom}/{name} ...", flush=True)
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
    est = {k: np.full(len(obs), np.nan) for k in ("max", "median", "nearest")}
    for k, (X, Y) in enumerate(XY):
        col, row = int((X - T.c) / T.a), int((Y - T.f) / T.e)
        if not (0 <= row < ny and 0 <= col < nx):
            continue
        r0, c0 = max(0, row - RAD), max(0, col - RAD)
        sl = (slice(r0, row + RAD + 1), slice(c0, col + RAD + 1))
        ws, hh, dd = wse[sl], depth[sl], dep[sl]
        fl = (hh >= DEPTH_MIN) & (dd <= obs[k] + GROUND_CAP)
        if not fl.any():
            continue
        est["max"][k] = np.nanmax(ws[fl])
        est["median"][k] = np.nanmedian(ws[fl])
        rr, cc = np.nonzero(fl)
        j = int(np.argmin((rr - (row - r0)) ** 2 + (cc - (col - c0)) ** 2))
        est["nearest"][k] = ws[rr[j], cc[j]]
    rec = dict(domain=dom, arm=name)
    for e, mod in est.items():
        m = head & np.isfinite(mod)
        r = mod[m] - obs[m]
        rec[f"n_{e}"] = int(m.sum())
        rec[f"bias_{e}"] = round(float(r.mean()), 4)
        rec[f"rmse_{e}"] = round(float(np.sqrt((r ** 2).mean())), 4)
        rec[f"w05_{e}"] = round(float(np.mean(np.abs(r) < 0.5)), 3)
    rows.append(rec)
    del depth, dep, wse, h, d

df = pd.DataFrame(rows)
pd.set_option("display.width", 250)
pd.set_option("display.max_columns", 40)
print("\n" + "=" * 100)
print("31-mark bridge set, q<=2, 50 m window — same marks, same window, three estimators")
print("=" * 100)
for e in ("max", "nearest", "median"):
    print(f"\n--- estimator: {e}")
    print(df[["domain", "arm", f"n_{e}", f"bias_{e}", f"rmse_{e}", f"w05_{e}"]].to_string(index=False))

print("\n--- ranking by |bias| under each estimator (best first)")
for e in ("max", "nearest", "median"):
    o = df.assign(k=df[f"bias_{e}"].abs()).sort_values("k")
    print(f"  {e:8s}: " + "  >  ".join(
        f"{r.domain}/{r.arm}({r[f'bias_{e}']:+.3f})" for _, r in o.iterrows()))
print("\n--- ranking by RMSE under each estimator (best first)")
for e in ("max", "nearest", "median"):
    o = df.sort_values(f"rmse_{e}")
    print(f"  {e:8s}: " + "  >  ".join(
        f"{r.domain}/{r.arm}({r[f'rmse_{e}']:.3f})" for _, r in o.iterrows()))
df.to_csv(OUT / "arm_rescore_estimators.csv", index=False)
print("\nwrote arm_rescore_estimators.csv")
