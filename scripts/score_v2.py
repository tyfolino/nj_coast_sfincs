"""Score the v2_barnegat arms — twice, on purpose.

TWO SCORINGS, AND CONFUSING THEM IS THE WHOLE HAZARD
----------------------------------------------------
**Native (95 marks).** v2 judged on its own terms. This is the number for
"how good is the model on the Barnegat domain" and for control-vs-CORA, because both
arms share the same mark set so the comparison is internally valid.

**Bridge (v1's 31 marks).** The ONLY scoring comparable to the frozen v1 campaign
(premier 0.318 / tide-shift 0.302 / wave-deep30 0.285 / union 0.273). Extending the
domain took the mark file 31 -> 95, and a pooled statistic over a different mark set is
a different measurement — validate.hwm_metrics' own docstring says a change in the
scored-mark count invalidates a comparison, and this is that change at its largest.
v1's 31 are an exact subset of v2's 95 by hwm_id, so the restriction is exact.

Never put a native v2 number in the same column as a v1 number.

Run:
    NJ_ROOT=$PWD NJ_DOMAIN=v2_barnegat PYTHONPATH=$PWD \
        micromamba/envs/sfincs/bin/python scripts/score_v2.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import geopandas as gpd
import pandas as pd

import nj_sfincs  # noqa: F401  (PROJ primer)
from nj_sfincs import premier, validate
from nj_sfincs.config import ROOT

#: Each arm is listed next to the control it is a single-variable delta against.
#: `tide-shift` moves the tidal boundary phase off `faber-waves-premier`; the two `bed-`
#: arms move the SUBGRID (roughness / elevation) off `wave-cora` on the same frozen mesh.
ARMS = ["faber-waves-premier", "wave-cora",
        "tide-shift",                        # vs faber-waves-premier
        "wave-cora+bed-baymanning",          # vs wave-cora
        "wave-cora+bed-ehydro"]              # vs wave-cora
V1_HWM = Path("/cache/home/tpj8/nj_sandy_sfincs/data/validation/sandy_hwms.geojson")
OUT = ROOT / "reports"

#: CSI is an EXTENT metric and does not depend on the HWM estimator, so the frozen v1
#: values stand as published.
V1_CSI = {
    "faber-waves-premier": 0.706, "tide-shift": 0.701,
    "wave-deep30": 0.687, "wave-deep30+tide-shift": 0.684,
}

#: ⚠️ The v1 HWM reference used to be hardcoded here as bias=0.318 / rmse=0.480 etc.
#: Those are `max` numbers. Since 2026-07-28 the default estimator is `median`, and
#: printing a `max` v1 number beside a `median` v2 number is precisely the
#: cross-estimator comparison validate.hwm_metrics' docstring forbids — the estimator
#: alone flips the SIGN of the bias and inverts the arm ranking. They are now read from
#: reports/arm_rescore_estimators.csv, which scores the v1 arms under every estimator on
#: the same 31 marks at the same radius. Regenerate with hwm_estimator_rescore_arms.py.
V1_RESCORE = ROOT / "reports" / "arm_rescore_estimators.csv"


def v1_reference(estimator: str) -> dict:
    """v1 campaign HWM numbers under the SAME estimator; {} if unavailable."""
    if not V1_RESCORE.exists():
        return {}
    d = pd.read_csv(V1_RESCORE)
    d = d[d["domain"] == "v1"]
    bcol, rcol = f"bias_{estimator}", f"rmse_{estimator}"
    if bcol not in d.columns or rcol not in d.columns:
        return {}
    return {
        r["arm"]: dict(bias=float(r[bcol]), rmse=float(r[rcol]),
                       csi=V1_CSI.get(r["arm"], float("nan")))
        for _, r in d.iterrows()
    }


def main(estimator: str = validate.HWM_ESTIMATOR_DEFAULT) -> int:
    v1_ids = sorted(gpd.read_file(V1_HWM)["hwm_id"].astype(str))
    print(f"v1 bridge mark set: {len(v1_ids)} hwm_ids")
    print(f"HWM estimator: {estimator} over a {validate.HWM_RADIUS_M:.0f} m window\n")

    OUT.mkdir(parents=True, exist_ok=True)
    rows_native, rows_bridge = {}, {}
    for name in ARMS:
        d = ROOT / "experiments" / name
        if not (d / "sfincs_map.nc").exists():
            print(f"[{name}] no sfincs_map.nc yet — skipping")
            continue
        premier.assert_sealed_domain(d, context=f"scoring {name}")
        print(f"[{name}] scoring NATIVE (95 marks) ...")
        rows_native[name] = validate.evaluate(
            d, gallery_tif=OUT / "figures" / f"{name}_hmax.tif",
            hwm_estimator=estimator,
        )
        print(f"[{name}] scoring BRIDGE ({len(v1_ids)} marks) ...")
        rows_bridge[name] = validate.evaluate(
            d, hwm_ids=v1_ids, hwm_estimator=estimator
        )
        for r in (rows_native[name], rows_bridge[name]):
            r["domain"] = "v2_barnegat"

    if not rows_native:
        print("nothing scored — have the runs finished?")
        return 1

    nat = pd.DataFrame.from_dict(rows_native, orient="index")
    brg = pd.DataFrame.from_dict(rows_bridge, orient="index")
    nat.to_csv(OUT / "v2_native95.csv")
    brg.to_csv(OUT / "v2_bridge31.csv")
    print(f"\nwrote {OUT/'v2_native95.csv'}\nwrote {OUT/'v2_bridge31.csv'}")

    key = [c for c in ("hwm_bias_m_scored", "hwm_rmse_m_scored", "hwm_bias_m",
                       "hwm_rmse_m", "hwm_n_dry", "hwm_within_0.5_m",
                       "motf_csi", "motf_pod", "motf_far") if c in nat.columns]
    with pd.option_context("display.width", 220, "display.max_columns", 60):
        print("\n=== NATIVE (95 marks) — v2 on its own terms, control vs CORA ===")
        print(nat[key].to_string())
        print(f"\n=== BRIDGE ({len(v1_ids)} marks) — the ONLY v1-comparable column ===")
        print(brg[key].to_string())

    ref = v1_reference(estimator)
    print(f"\n=== v1 campaign reference — SAME estimator ({estimator}), 31 marks ===")
    if not ref:
        print(f"  reports/{V1_RESCORE.name} missing or has no '{estimator}' column —")
        print("  run scripts/hwm_estimator_rescore_arms.py. NOT falling back to the")
        print("  old hardcoded `max` numbers: a cross-estimator comparison is invalid.")
    else:
        for k, v in ref.items():
            print(f"  {k:24s} bias {v['bias']:+.3f}  rmse {v['rmse']:.3f}  "
                  f"csi {v['csi']:.3f}")
    print("\nCompare v1 ONLY against the BRIDGE table above, and ONLY at equal estimator.")

    print("\n=== the two new interior gauges (the reason this domain exists) ===")
    print("  Barnegat Light 01409125 obs peak 1.59 m @ 2012-10-30 00:24 UTC")
    print("  Mantoloking    01408168 obs peak 2.11 m @ 2012-10-30 06:18 UTC")
    print("  SSS Barnegat Inlet 2260 obs peak 1.65 m @ 2012-10-30 00:00 UTC")
    print("  Read the PAIR: Mantoloking is 0.52 m higher and ~6 h later than")
    print("  Barnegat Light. Matching either alone is easy; matching the DIFFERENCE")
    print("  is the bay-conveyance / inlet-exchange test.")
    gcols = [c for c in nat.columns if "mantolok" in c.lower()
             or "barnegat" in c.lower() or "peak" in c.lower() or "lag" in c.lower()]
    if gcols:
        with pd.option_context("display.width", 220, "display.max_columns", 60):
            print(nat[gcols].to_string())
    return 0


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--estimator", default=validate.HWM_ESTIMATOR_DEFAULT,
                    choices=list(validate.HWM_ESTIMATORS),
                    help="how the HWM search window is reduced (default: %(default)s)")
    raise SystemExit(main(ap.parse_args().estimator))
