"""Is CORA's +0.49 m Hs bias at NDBC 44025 a steady offset or a peak overshoot?

The two have different consequences for using CORA as a SnapWave boundary:

* A STEADY multiplicative/additive offset is a calibration property. It would inflate
  the imposed boundary Hs at all times by roughly the same factor, and could in
  principle be corrected.
* A PEAK-ONLY overshoot means CORA's SWAN is over-responding to the storm forcing
  specifically. That is the regime the model is actually run in, so the boundary would
  be worst exactly when it matters, and a single scale factor would NOT fix it.

Compares CORA and ERA5 to the buoy at the buoy's own location/depth, binned by sea
state, and reports the bias as a function of observed Hs.

Writes reports/cora_buoy_bias_structure.csv.
"""
import os
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

ROOT = Path(os.environ.get("NJ_ROOT", Path(__file__).resolve().parents[1]))
DATA = ROOT / "data"


def series():
    obs = xr.open_dataset(DATA / "waves" / "ndbc_sandy_44025.nc")
    blon = float(obs["lon"].values.ravel()[0])
    blat = float(obs["lat"].values.ravel()[0])
    o = pd.Series(obs["hs"].values.ravel(),
                  index=pd.to_datetime(obs["time"].values)).dropna()

    cds = xr.open_dataset(DATA / "waves" / "cora_waves_nj.nc")
    d = np.hypot((cds["lon"].values - blon) * np.cos(np.deg2rad(blat)),
                 cds["lat"].values - blat) * 111_000.0
    j = int(np.argmin(d))
    c = pd.Series(cds["hs"].values[:, j], index=pd.to_datetime(cds["time"].values))

    eds = xr.open_dataset(DATA / "waves" / "era5_waves_nj.nc")
    ev = eds["hs"].sel(x=blon, y=blat, method="nearest")
    e = pd.Series(ev.values, index=pd.to_datetime(eds["time"].values))

    # Put model series on the buoy clock.
    idx = o.index
    ci = c.reindex(c.index.union(idx)).interpolate("time").reindex(idx)
    ei = e.reindex(e.index.union(idx)).interpolate("time").reindex(idx)
    df = pd.DataFrame({"obs": o, "cora": ci, "era5": ei}).dropna()
    df["d_cora"] = df.cora - df.obs
    df["d_era5"] = df.era5 - df.obs
    return df, d[j] / 1000, float(abs(cds["depth"].values[j]))


def main():
    df, dist_km, depth = series()
    pd.set_option("display.width", 200)
    print(f"NDBC 44025 — CORA node {dist_km:.1f} km away, source depth {depth:.1f} m")
    print(f"{len(df)} paired hourly samples, "
          f"{df.index[0]:%Y-%m-%d %H:%M} -> {df.index[-1]:%Y-%m-%d %H:%M}\n")

    print("=== bias binned by OBSERVED sea state ===")
    bins = [0, 2, 4, 6, 8, 12]
    df["bin"] = pd.cut(df.obs, bins)
    g = df.groupby("bin", observed=True).agg(
        n=("obs", "size"), obs_mean=("obs", "mean"),
        cora_bias=("d_cora", "mean"), era5_bias=("d_era5", "mean"),
        cora_ratio=("cora", lambda s: np.nan), era5_ratio=("era5", lambda s: np.nan))
    g["cora_ratio"] = df.groupby("bin", observed=True).apply(
        lambda x: (x.cora / x.obs).mean(), include_groups=False)
    g["era5_ratio"] = df.groupby("bin", observed=True).apply(
        lambda x: (x.era5 / x.obs).mean(), include_groups=False)
    print(g.round(3).to_string())

    print("\n=== the storm peak vs the rest ===")
    pk = df.obs >= 6.0
    for lbl, m in [("peak (obs Hs >= 6 m)", pk), ("non-peak (< 6 m)", ~pk)]:
        s = df[m]
        print(f"  {lbl:24s} n={len(s):3d}  "
              f"CORA {s.d_cora.mean():+.3f} m ({(s.cora/s.obs).mean():.3f}x)   "
              f"ERA5 {s.d_era5.mean():+.3f} m ({(s.era5/s.obs).mean():.3f}x)")

    print("\n=== peak values and timing ===")
    print(f"  obs  peak {df.obs.max():5.2f} m @ {df.obs.idxmax()}")
    print(f"  CORA peak {df.cora.max():5.2f} m @ {df.cora.idxmax()}  "
          f"({df.cora.max() - df.obs.max():+.2f} m)")
    print(f"  ERA5 peak {df.era5.max():5.2f} m @ {df.era5.idxmax()}  "
          f"({df.era5.max() - df.obs.max():+.2f} m)")

    # Is a single scale factor enough? Compare additive vs multiplicative residual.
    print("\n=== would ONE correction factor fix CORA? ===")
    k = (df.cora / df.obs).mean()
    a = df.d_cora.mean()
    r_mult = df.cora / k - df.obs
    r_add = df.cora - a - df.obs
    print(f"  raw            RMSE {np.sqrt((df.d_cora**2).mean()):.3f} m")
    print(f"  after /{k:.3f} (multiplicative) RMSE {np.sqrt((r_mult**2).mean()):.3f} m")
    print(f"  after -{a:.3f} (additive)       RMSE {np.sqrt((r_add**2).mean()):.3f} m")
    print(f"  residual bias spread across sea-state bins: "
          f"{g.cora_bias.max() - g.cora_bias.min():.3f} m")

    df.drop(columns="bin").to_csv(ROOT / "reports" / "cora_buoy_bias_structure.csv")
    print("\nwrote reports/cora_buoy_bias_structure.csv")


if __name__ == "__main__":
    main()
