"""Interior Barnegat Bay gauge metrics across the pre- and post-repair arms.

This is the measurement the inlet-mask repair was FOR. The 07-30 campaign could
score the repair on HWM/CSI only, because Barnegat Light and Mantoloking were not in
``validate.evaluate()`` — so the repair's whole claimed benefit (bay phase + range)
went unquantified. ``validate.interior_gauge_metrics`` now supplies it.

⚠️ THIS SCRIPT DELIBERATELY CROSSES THE DOMAIN GUARD. ``wave-cora+bed-ehydro`` is on
the PRE-REPAIR domain (sha 9ccbab0bc7a9fc0d) and the two ``mask-inlet`` arms are on
the repaired one (3b1356b9590c59ff). Pooling them in a table is exactly what
``premier.assert_sealed_domain`` exists to prevent -- but here the domain IS the
treatment, and pre-flight established these arms differ ONLY by the mask (0-key
sfincs.inp diff, byte-identical forcing). So this is a single-variable comparison,
not a pooled statistic. Do not copy these rows into a table with HWM/CSI numbers.

Run:
    NJ_ROOT=$PWD NJ_DOMAIN=v2_barnegat PYTHONPATH=$PWD python scripts/score_interior_gauges.py
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

import nj_sfincs  # noqa: F401  (PROJ primer)
from nj_sfincs import validate
from nj_sfincs.config import exp_root, ROOT, DATA

ARMS = [
    "wave-cora+bed-ehydro",                        # PRE-repair control
    "wave-cora+bed-ehydro+mask-inlet",             # the repair
    "wave-cora+bed-ehydro+mask-inlet+tide-shift",  # repair + phase shift
]
OUT = ROOT / "reports" / "v2_interior_gauges.csv"


def open_model(d: Path):
    """SfincsModel + outputs, without load_floodmap's expensive raster work.

    interior_gauge_metrics needs only the his points, sfincs_map.nc and sfincs.nc --
    not the de-rotated hmax/dep rasters -- so skip the ~2 min reproject pair.
    """
    from hydromt_sfincs import SfincsModel

    mod = SfincsModel(str(d), data_libs=[str(DATA / "data_catalog.yml")], mode="r")
    validate.read_output(mod)
    return mod


def main() -> int:
    rows = {}
    for name in ARMS:
        d = exp_root() / name
        if not (d / "sfincs_map.nc").is_file():
            print(f"[{name}] missing sfincs_map.nc — skipping")
            continue
        print(f"[{name}] interior gauges ...", flush=True)
        rows[name] = validate.interior_gauge_metrics(open_model(d), d)
        # The volume/tilt split. Costs no solver time and is the GATE on the expensive
        # arms — see validate.bay_error_decomposition.
        rows[name].update(validate.bay_error_decomposition(d))

    if not rows:
        print("nothing scored")
        return 1

    df = pd.DataFrame.from_dict(rows, orient="index")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT)
    print(f"\nwrote {OUT}\n")

    def show(title, cols):
        cols = [c for c in cols if c in df.columns]
        if not cols:
            return
        print(f"=== {title} ===")
        with pd.option_context("display.width", 240, "display.max_columns", 60):
            print(df[cols].to_string())
        print()

    show("⭐ THE GATE — volume vs tilt (no solver time; decides the expensive arms)",
         ["bay_volume_err_mean_m", "bay_volume_err_final_m",
          "bay_tilt_err_mean_m", "bay_tilt_err_absmax_m",
          "bay_dominant_term", "bay_tilt_over_volume"])
    show("Matched-instant gradient — ⚠️ NOT the same quantity as ig_alongbay_*",
         ["alongbay_obs_max_m", "alongbay_matched_m", "alongbay_matched_ratio",
          "alongbay_at", "alongbay_obs_flip", "alongbay_mod_flip", "wind_reversal"])
    show("ig_alongbay_* — PEAK-minus-PEAK at UNEQUAL times. Kept for continuity only; "
         "read the matched-instant block above instead",
         ["ig_alongbay_obs_m", "ig_alongbay_mod_m", "ig_alongbay_err_m",
          "ig_peaktime_obs_h", "ig_peaktime_mod_h", "ig_peaktime_err_h"])
    show("Peak level per gauge",
         ["ig_obs_peak_barnegat_light_m", "ig_mod_peak_barnegat_light_m",
          "ig_peak_err_barnegat_light_m",
          "ig_obs_peak_mantoloking_m", "ig_mod_peak_mantoloking_m",
          "ig_peak_err_mantoloking_m",
          "ig_obs_peak_barnegat_inlet_sss_m", "ig_mod_peak_barnegat_inlet_sss_m",
          "ig_peak_err_barnegat_inlet_sss_m"])
    show("Peak TIMING per gauge (min, + = model late)",
         ["ig_peak_lag_barnegat_light_min", "ig_peak_lag_mantoloking_min",
          "ig_peak_lag_barnegat_inlet_sss_min"])
    show("Pre-storm tidal RANGE at wet channel cells",
         ["ig_n_channel_cells_barnegat_light", "ig_tide_obs_range_barnegat_light_m",
          "ig_tide_mod_range_barnegat_light_m", "ig_tide_range_err_barnegat_light_m",
          "ig_n_channel_cells_mantoloking", "ig_tide_obs_range_mantoloking_m",
          "ig_tide_mod_range_mantoloking_m", "ig_tide_range_err_mantoloking_m"])
    show("Pre-storm tidal PHASE (min, + = model late)",
         ["ig_phase_lag_barnegat_light_min", "ig_phase_lag_mantoloking_min"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
