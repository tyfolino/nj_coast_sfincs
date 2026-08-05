<!-- Raw Claude-memory file, archived verbatim 2026-08-05 when the memory store was
     collapsed. Its standing content was merged into the new memory set and/or
     CLAUDE.md; this copy exists so the merge cannot have lost a detail.
     Superseded — do not treat as current. -->


# Handoff — 2026-08-03

## ✅ CLOSED 2026-08-04 — the bracket landed, was scored, and the rule was applied

Not truncated. **Width at Mantoloking +0.666 m ⇒ REBUILD JUSTIFIED**, both side
conditions pass. **P1 FALSIFIED** (the width is LARGER at Mantoloking than at Barnegat
Light and the tilt IMPROVES) ⇒ the southern connection is now a live candidate for the
along-bay gradient too, which was the 08-03 "new live thread". P2 confirmed.
Full numbers + the lesson in [[reference_bracket_pattern]]; the demotion argument it
overturns is corrected in [[reference_bay_volume_deficit]].
`scripts/score_bracket.py` written → `reports/bracket_manahawkin.csv`.

## 🚀 (was PICK UP HERE) — job 60021248

**`BRACKET+wave-cora+bed-ehydro+mask-inlet+mask-manahawkin-open`**, submitted ~16:40 on
64 cores / 96 G / **8 h** wall (the `hpc/sfincs_run.slurm` default of 3 h is too tight —
prior arms ran 2:54; and RAM is a non-issue, they peak at **6.07 GB**).

**Tomorrow, in order:**
1. Check truncation FIRST — 73 map / 433 his steps reaching tstop 2012-10-31, log closing
   cleanly. `sacct` says COMPLETED even on a quota-truncated map.
2. Score with `NJ_ALLOW_BRACKET=manahawkin-open`; `scripts/score_bracket.py` does **not
   exist yet** — write it, modelled on `scripts/score_interior_gauges.py`, writing to
   `reports/bracket_manahawkin.csv` (NEVER `metrics.csv`).
3. Apply the **pre-registered decision rule** in [[reference_bracket_pattern]] before
   looking for a story in the numbers.

## ✅ Also done 2026-08-03 (afternoon)

- **Disk: 87 G → 74 G.** `dedupe_experiment_inputs.py --apply` (11.8 GB, more than the
  5.3 GB estimate) + deleted all five `snapwave.upw` (SFINCS scratch, regenerated on the
  next solve). Nothing deleted; all 8 dirs still audit correctly.
- **`validate.bay_error_decomposition` + `interior_gauge_series`** — the free gate. See
  [[reference_bay_volume_deficit]] for the result (TILT-dominated, matched ratio 0.549).
- **`_NO_WL_MANAHAWKIN`** alarm added to `V2_BARNEGAT.no_waterlevel_boxes`; east edge
  **measured** (574,150 condemns 0 legitimate ocean BC cells, 574,300 condemns 1). Fires
  with **114 cells** on the pre-repair template — validated against a known defect.
- **Wind investigated and the hypothesis WEAKENED** — see
  [[reference_wind_forcing_investigation]]. RTMA obtained via Earth Engine but it shows
  the SAME bay/ocean reduction as ERA5.
- **Notebook slimmed**: markdown ~13,000 → **1,600 chars** (one-line captions only, per
  the user), long `print()` essays removed, duplicate cells 25/26 deleted, nbformat
  upgraded to **4.5 so cells finally have ids**. 53 → 50 cells; re-ran every logic cell.
  ⚠️ STILL 57 MB — the three inline animations are 46 MB of it. Moving them to
  `reports/figures/anim/*.mp4` is the remaining piece.
- **HWM plot speed fixed** — see [[reference_viz_performance]] (`imshow` was 10^5x
  oversampled; drawing 2.3 s now).
- ✅ **Outflow-BC check, asked for explicitly**: outflow count IDENTICAL (295) in control
  and bracket, **0 cells** on water deeper than −1.0 m in both. No Navesink repeat.

## 🔭 Lead not yet chased

The user mentioned **high-resolution radar wind/wave data**, believing it postdates Sandy.
Worth 10 minutes: Rutgers **RUCOOL** has run HF radar (CODAR) since well before 2012 — but
HF radar gives surface CURRENTS (wind direction can be inferred; speed cannot), so it may
not answer the wind question even if the coverage exists. The thing that WOULD settle it is
an **in-bay anemometer** — try the **NJ Weather & Climate Network**.


## ✅ Both 07-30 arms landed and are fully scored

`59693619` / `59693621` COMPLETED 2026-07-30 16:09, ~2:54 each. **No truncation**
(73 map / 433 his reaching tstop, logs close cleanly). They sat unscored for 4 days.

Scores in `reports/v2_postrepair_{native95,bridge31}.csv` — **deliberately separate
files** so the pre-repair baseline in `reports/v2_{native95,bridge31}.csv` survives.
`scripts/score_v2.py` cannot score them as shipped: its `ARMS` list is the old five and
the domain guard correctly refuses them. Used `scratchpad/score_postrepair.py`.

| native 95 | HWM bias | RMSE | CSI | POD |
|---|---|---|---|---|
| `wave-cora+bed-ehydro` (pre-repair) | **−0.244** | **0.493** | **0.701** | 0.878 |
| `+mask-inlet` | −0.403 | 0.582 | 0.552 | 0.682 |
| `+mask-inlet+tide-shift` | −0.429 | 0.599 | 0.549 | 0.679 |

⭐ **Bridge-31 barely moves** (−0.231 → −0.233 → −0.259) while native-95 moves a lot,
and the per-basin table is ~0.000 for shark_river / south_coast / atlantic_oceanfront.
The repair's effect is **localised to the south exactly as it should be** — that is a
strong correctness check on the repair itself, independent of whether it scores well.

## 🎯 THE PRE-REGISTERED FALSIFIER FIRED — and harder than predicted

`barnegat_bay` HWM bias **+0.005 → −0.630**; `barnegat_barrier` **+0.279 → −0.422**
(the barrier was NOT predicted). The clamp was propping up the whole southern system,
not just the bay. Per the pre-registration this is a **price, not a verdict**: an
inadmissible BC that scores well is still inadmissible.

## ⭐⭐ THE NEW LIVE THREAD: the along-bay gradient is NOT the clamp

Interior gauges are now in `validate.evaluate()` (`validate.interior_gauge_metrics`,
`reports/v2_interior_gauges.csv`, `scripts/score_interior_gauges.py`). What they say:

**Repair FIXED the inlet.** Barnegat Light peak err **+0.973 → +0.096**; SSS Barnegat
Inlet **+1.236 → +0.150**; Barnegat Light tidal range **1.346 (err +0.343) → 0.808
(err −0.195)**. Two instruments, two agencies, ~1 km apart, agreeing.

**Repair BROKE mid-lagoon.** Mantoloking peak err **−0.025 → −0.853**. Pre-repair
Mantoloking was near-perfect *because the clamp was feeding the bay* — **right for the
wrong reason.**

**Repair did NOT touch the along-bay gradient — prediction FALSIFIED.** Predicted the
clamp "is what has been holding the southern end up" so the gradient would move toward
observed. Error is **−0.998 → −0.949** (his path) / **−0.75 → −0.96** (map path):
essentially unchanged, and still INVERTED (obs +0.518, model ≈ −0.43).
⇒ **the inverted gradient is a BAY CONVEYANCE defect, not a boundary artefact.**
This is the thing to chase next.

**Bay phase: only PARTLY an artefact.** Barnegat Light −38.7 → **−26.4** min, Mantoloking
−62.2 → **−50.9**. The clamp explained ~12 min; ~26–51 min of genuine EARLY arrival
remains. So the old "bay arrives early" finding is neither confirmed nor dismissed —
it is real but roughly half the size once measured on an admissible boundary.

**Peak-time separation got WORSE**: obs 5.9 h, model 4.83 → 4.00 h. The surge runs
up-bay too fast, and the repair worsened it.

## 🔀 `tide-shift` is a genuine COAST-vs-BAY trade (as pre-registered)

Coast wins reproduced almost exactly on the repaired domain: Sandy Hook 17.8 → **−0.3**,
Shrewsbury 33.9 → **13.3**, Shark 34.6 → **18.5** min. But the bay is still EARLY, so
tide-shift makes it **~7–9 min worse** (−26.4 → −33.4; −50.9 → −59.9) — the ~8 min cost
predicted in advance. HWM/CSI cost is small (bias −0.403 → −0.429, CSI 0.552 → 0.549).

## ⭐ PREMIER PROMOTION — still open, recommend HOLD

Reasoning stands: promoting `+mask-inlet` is right on admissibility, but its central
claimed benefit (bay behaviour) is now measured and is **mixed** — inlet fixed, lagoon
broken, gradient untouched. Recommend fixing the conveyance defect first, then promote.

## 🧰 Code added 2026-08-03 (NOTHING COMMITTED — `git` is not on PATH on compute nodes)

- `nj_sfincs/validate.py` — `PEAK_FLOOR`, `INTERIOR_GAUGES`, `INTERIOR_TIDE_GAUGES`,
  `_aligned_pair`, `_peak_after_floor`, `interior_gauge_metrics`, wired into `evaluate()`.
  ⚠️ **`_aligned_pair` exists because `_uniform_series` is unsafe for a new gauge** —
  it clips the grid to each series' OWN coverage and `_xcorr_lag_minutes` then aligns by
  INDEX 0, so a non-overlapping window silently offsets the lag. Existing callers left
  alone on purpose (their numbers are in the scored campaign).
  ⚠️ Peak uses **his** (10-min; bank cell is fine AT the crest — same argument as
  `shrewsbury_gauge_peak`), range/phase uses **map at wet channel cells** (the bank cell
  is DRY pre-storm: Barnegat Light `point_zb` +0.988). Both peak paths are reported
  (`ig_*` vs `ig_modmap_*`) and agree to ~0.02 m post-repair.
  ⚠️ `ig_n_channel_cells_barnegat_light` is **21 pre-repair vs 30 post** — the repair
  changed the mask there, so that gauge's range/phase delta is measured on a slightly
  different sample. Mantoloking is 55 in both (clean).
- `scripts/score_interior_gauges.py` — deliberately crosses the domain guard; the mask
  IS the treatment and the forcing hashes prove single-variable.
- `scripts/export_share_floodmap.py` — see [[reference_share_floodmap_export]].
- `notebooks/sfincs-nj-barnegat-viz-cora.ipynb` — rewired to the 3-arm ladder (53 cells);
  cells 0,2,3,19,21,23,26,27 rewritten + new "repair verdict" section at 28–29.
  **Outputs cleared on the edited cells — needs a top-to-bottom run.**

Related: [[reference_inlet_waterlevel_clamp]], [[project_domain_expansion_v2]],
[[project_tidal_phase_lag]], [[project_handoff_2026_07_30]].
