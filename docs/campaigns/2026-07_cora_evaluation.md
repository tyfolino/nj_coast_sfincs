<!-- Campaign record. Moved out of the Claude memory store 2026-08-05; the
     memory file was `project_cora_evaluation`. -->

> **Historical record — read top-down, newest first.** Blocks are appended in
> reverse chronological order and later blocks SUPERSEDE earlier ones, including
> where an earlier block calls itself current. Several conclusions in here were
> retracted; the retraction is always above the claim it retracts. For what is
> believed true *now*, see the memory store and `CLAUDE.md`, not this file.
>
> **Standing summary at the time of the move:** NOAA CORA evaluated as boundary forcing 2026-07-22 — DON'T adopt for WATER LEVEL (lags, runs low). ⭐ 2026-07-27: BUILT AND RUNNING as the WAVE boundary (`wave-cora` on v2_barnegat) — scripts/build_cora_waves.py, per-support-point. ❌ CORRECTED: CORA is NOT 'low' in deep water — at NDBC 44025's own location it is +0.49 m HIGH.


# NOAA CORA as boundary forcing — evaluated 2026-07-22, **NOT ADOPTED**

## ⭐⭐ 2026-07-28 — THE VERDICT, ON THREE SEPARATE AXES (`scripts/cora_vs_era5_verdict.py`)

They disagree, so never quote one as "the" answer. Numbers are measured, not estimated.

**1. Admissibility at the support points — CORA wins decisively.** Using each point's own
CORA depth and a 0.78 breaking cap: **ERA5 is admissible at 1 of 7 points, CORA at 7 of 7.**
ERA5's γ = Hs/h runs 0.64–**1.16**; two points (7.4 and 7.5 m deep) get an imposed Hs
*larger than the depth*, which is not a sea state. CORA's γ runs 0.46–0.68 everywhere.
Alongshore spread at the peak: ERA5 **0.000 m**, CORA **1.298 m** (4.816–6.114).

**2b. ⭐ THE HIGH BIAS IS A STEADY ~+11% SCALING, NOT A STORM OVERSHOOT (2026-07-28).**
`scripts/cora_buoy_bias_structure.py` bins the buoy comparison by observed sea state. The
*additive* bias grows (+0.33 → +1.07 m) only because the waves get bigger; the **ratio is
flat**: 1.21 / 1.12 / 1.09 / 1.09 / 1.13 across Hs bins 0-2 / 2-4 / 4-6 / 6-8 / 8-12 m.
Peak (Hs≥6 m) **1.110×** vs non-peak **1.118×** — indistinguishable. ⇒ this is a
CALIBRATION property, not CORA's SWAN over-responding to the storm, so it does *not*
poison the boundary exactly when it matters. A single multiplicative correction is the
right FORM and works: dividing by 1.116 cuts RMSE 0.801 → **0.548 m**, beating an additive
−0.485 m shift (0.638 m). ERA5 is likewise a steady scaling, in the other direction —
ratio 0.79–0.86, i.e. **~20% LOW**. Correcting CORA by /1.116 would *improve*
admissibility further (γ 0.46–0.68 → ~0.41–0.61), so it costs nothing on axis 1.

**2. Against the buoy at ITS OWN location/depth — CORA is better but runs HIGH.**
NDBC 44025 (CORA node 1.3 km away, 40 m depth; ERA5 cell 30.9 km away on its 0.5° grid):

| | peak Hs | bias | RMSE |
|---|---|---|---|
| NDBC 44025 observed | 9.65 m | — | — |
| CORA @ buoy | 10.84 m | **+0.485** | **0.801** |
| ERA5 @ buoy | 7.61 m | **−0.931** | 1.059 |

🔑 **THE PARADOX WORTH UNDERSTANDING: ERA5 UNDER-states the offshore sea state (7.61 vs
9.65) yet OVER-states it at the boundary (8.624 at 7–13 m depth).** Both are the same
defect — `add_waves` takes ONE ERA5 node and hands byte-identical Hs to all 7 support
points with **no shelf transformation**. CORA's SWAN actually propagates and breaks across
the shelf: 10.84 m at the buoy in 40 m → 4.8–6.1 m at the 7–13 m contour.

**3. The HWM score — a wash, and slightly AGAINST CORA under `median`.** Native-95
(the valid v2-internal set; bridge-31 is Monmouth-only and barely sees this boundary),
50 m window, wet-only. ⭐ **These are now the PRODUCTION numbers** — `reports/v2_*.csv`
were re-scored under `median` on 2026-07-28 and carry an `hwm_estimator` column:

| | bias `max` | bias `median` | RMSE `max` | RMSE `median` | n_dry |
|---|---|---|---|---|---|
| premier (ERA5) | +0.482 | **−0.250** | 1.347 | **0.494** | 7 |
| `wave-cora` | +0.430 | −0.293 | 1.290 | 0.507 | 8 |

Under `max` CORA improves both; under the **adopted `median`** it is 0.043 m more negative,
0.013 m worse on RMSE, and turns one more mark dry. ⇒ **the HWM score does not separate
them** — see [[reference_hwm_estimator_artifact]].

**How to state it:** lead with admissibility (axis 1) — a construction fact from depths and
imposed Hs, independent of any scorer: **ERA5 admissible at 1/7 support points, CORA at
7/7**. Report axis 2 as the honest caveat, but note it is a **steady ~+11% scaling**, not a
storm-response defect (2b). Do **not** claim CORA improves the flood score; it does not,
once the estimator is fixed.

⚠️ **The paradox is the most useful single sentence here:** ERA5 *under*-states the
offshore sea state (7.61 m vs 9.65 m observed, ~20% low) yet *over*-states it at the
boundary (8.624 m imposed in 7–13 m of water). Those are one defect, not two — `add_waves`
does **no shelf transformation**, so a too-low deep-water value arrives as a far-too-high
nearshore one.

**Open, worth one run:** apply the /1.116 correction to the CORA boundary and re-run. It is
the cheapest remaining wave-boundary experiment, it is justified by an independent
observation rather than by tuning to the score, and it moves γ to 0.41–0.61.

## 🔴 2026-07-27 — THE WAVE BOUNDARY IS BUILT AND RUNNING (`wave-cora`)

**Builder: `scripts/build_cora_waves.py` (nj_coast_sfincs).** The old scratchpad
`cora_waves.py` was GONE; this is a rewrite from the access recipe below and it works.
Output `data/waves/cora_waves_nj.nc` — **unstructured (time, node), 7,824 nodes × 121
hourly steps**, nodes filtered to depth > 2 m AND all-finite (2,149 dropped: a
nearest-node lookup cannot notice it landed on a NaN).

⚠️ **The `*_map.zarr` paths are single ~400 KB kerchunk REFERENCE files, not zarr
stores.** Opening one directly raises `GroupNotFoundError`. Use the `reference`
filesystem (recipe below). Waves live at `.../native_grid/waves/zarr/swan_{HS,TPS,DIR}.63_2012_map.zarr`.

### ❌❌ CORRECTION — "CORA runs 0.14–0.31 m LOW" DOES **NOT** EXTEND TO ITS WAVES
That figure is for WATER LEVEL and still stands. For waves the old note said CORA sits
"23–45% below the buoy" — **that comparison was CORA NEARSHORE (~10 m) against the buoy
OFFSHORE (36 m), i.e. it conflated shelf transformation with bias.** Compared at the
buoy's OWN location and depth (nearest CORA node 1.7 km away, 40.0 m):

| | peak | bias | RMSE |
|---|---|---|---|
| NDBC 44025 obs | 9.65 m | — | — |
| CORA at 44025 | **10.84 m** | **+0.49 m** | 0.784 m |

⇒ **CORA is biased HIGH in deep water.** This does not weaken the arm — it strengthens
it: CORA is high offshore and *still* asks for only ~5–6 m at the 10 m contour, so the
reduction vs ERA5 is genuine SHELF TRANSFORMATION, not a low source. **Quote CORA's
direction, never its nearshore value as truth.**

### ⭐ PRE-REGISTERED at the v2 support points (measured BEFORE the run)
| | ERA5 (premier) | CORA |
|---|---|---|
| peak Hs at all 7 pts | **8.624 m, identical** | 4.98–6.11 m |
| γ = Hs/h in ~9.9 m | **0.86–0.89 ⇒ INADMISSIBLE at every point** | 0.50–0.63 ⇒ admissible |
| alongshore spread | **exactly 0.00 m** | **1.14 m** |
| peak timing | 10-29 20:00 | 10-30 01:00 (**5 h later**) |

Nearest CORA node is **0.09–0.35 km** from each support point, at CORA depths 7.4–13.4 m.
**This attacks the SAME defect as `wave-deep30` by the OPPOSITE route** — deep30 kept
ERA5's 8.624 m and moved the boundary to where it is valid; `wave-cora` keeps the
boundary and imposes the shelf-transformed height that belongs there.
⚠️ **Expect a MUCH bigger move than deep30's −0.034 m, and OVERSHOOT IS PLAUSIBLE.**
⚠️ **It changes SOURCE and ALONGSHORE STRUCTURE together** (ERA5 cannot express the
latter at all) — separating them needs a third arm: CORA at a single node.

🔧 Implementation: `WaveConfig.wave_point_dataset` → `model._point_wave_bnd()`, nearest
node per support point, and `finalize` now accepts a **2-D (ntime, npts)** wave series
(it used to `np.tile` a 1-D one — tiling a 2-D array would have emitted garbage).
🔑 **`_point_wave_bnd` references t to `base.tref`, NOT to the file's first timestamp.**
The ERA5 path uses `t - t[0]` and gets away with it only because that file happens to
start at tref; CORA is padded a day earlier, so `t - t[0]` would have shifted the entire
wave forcing 24 h with no symptom other than a bad score.

Motivation: hoped CORA would (a) remove the linear interpolation between AC and the
Battery on our 2-support-point boundary, (b) carry better tide phase than
`noaa_sandy_nj`. **It does neither. Both hopes tested and falsified.**

## Access (works, cheap — reuse this)
Anonymous kerchunk/zarr on S3, **per-year reference files ~1.6 MB**:
`s3://noaa-nos-cora-pds/cora_gec/native_grid/water_levels/zarr/fort.63_2012.zarr`
Mesh is **NOMAD v1e**, not the older HSOFS the 2024 Frontiers paper assessed.
Hourly, MSL datum, 41k nodes in the NJ box; Sandy window pulled in **35 s**.
`fsspec.filesystem("reference", fo=..., remote_protocol="s3", asynchronous=True,
remote_options={"anon":True,"asynchronous":True}, target_options={"anon":True})`
— the `asynchronous=True` on BOTH is required or zarr3 raises
"Reference-FS's target filesystem must have same value of asynchronous".
Scripts: scratchpad `cora_extract.py` / `cora_compare.py` / `cora_phase.py`.

## Why it loses (CORA vs NOAA gauge obs, hourly, 10/25–11/03, NAVD88)
| station | bias | RMSE | CORA lag | peak obs / CORA |
|---|---|---|---|---|
| Battery | −0.14 | 0.167 | **+13 min** | 3.39 / 3.35 ✅ |
| Sandy Hook | −0.18 | 0.199 | +6 min | *(gauge failed — peak invalid)* |
| Atlantic City | −0.28 | 0.295 | **+24 min** | 1.83 / **1.62** ❌ |
| Cape May | −0.31 | 0.326 | +14 min | 1.77 / 1.60 ❌ |

1. **CORA's tide is LATE by the same order we're fighting** (+6..+24 min). Our
   `noaa_sandy_composite` is 0 min by construction (NOAA harmonic predictions).
   Adopting CORA would *import* a lag, not remove one. Consistent with the paper:
   assimilation is on 4-day LOW-PASS fields, so **the tide is pure ADCIRC, never
   gauge-corrected** — CORA can't beat a harmonic prediction at a gauge site.
2. **Systematically LOW** (−0.14 → −0.31 m, growing southward) and it
   **under-predicts the AC Sandy peak by 0.21 m**. Under-forcing a surge study.

## The linear interpolation is FINE (the main hoped-for gain isn't there)
Our premier open boundary has only **2 support points** (Battery 40.701/−74.014,
AC 39.355/−74.418) and the model boundary spans only **s = 0.12–0.39** of that
line — little room to go wrong. Comparing CORA against linear interp *built from
CORA at the same two points* (so CORA's bias cancels): open-coast tidal range
differs by only **+2..+4%**, alongshore **lag 0 min**. Mean damping −1.7%.
**Linear interpolation is not a meaningful error source on the open coast.**
**⭐ 2026-07-26 — THIS BECAME LOAD-BEARING.** It is the finding that RETIRED the composite arms
([[project_tidal_phase_lag]]): the last surviving argument for a Sandy Hook support point was
"a ~150 km linear interp from a HARBOUR gauge is crude, so breaking it at Sandy Hook is
geographically right." This closes that argument independently of any HWM score — which matters
because the model is wet-biased +0.32 m, so the HWM table rewards removing forcing whether or
not the forcing was wrong. **Cite this whenever someone proposes a new open-coast support point.**

## The ONE real finding worth keeping
The **Raritan / Sandy Hook Bay boundary cells (lat ≈ 40.52)** show CORA tidal range
**11–15% LARGER** than linear interp gives them — the bay amplifies the tide and
two open-coast/harbor anchors miss it. That is a genuine localized *under*-forcing
on the western lobe. ⚠️ Temper against [[project_tidal_phase_lag]]: the composite
arm LOST on level because a 3rd support point lifted the mid-coast +0.2 m. Any
bay support point must be isolated as its own arm.
**⚠️ 2026-07-26 — AND THE BAR IS NOW HIGHER THAN "PUT IT ON THE LINE."** v2 was built to sit on
the Battery→AC surge line and STILL cost +0.18 m of HWM bias, because the on-line check was done
**at the surge peak only**: with cadence held constant the node reads +0.012 m off at its own
latitude but **+0.049 m off at Shark River**, since its re-phased tide leaves the line at other
times and the interpolated MAX between nodes rises. ⇒ **a bay support point must be verified
on-line across the WHOLE series, not at the peak, and verified at latitudes DOWNSTREAM of it,
not just at its own.** Reconstruct the imposed boundary and take max-over-time at several
latitudes before believing any "this node changes nothing" claim.

## 🔴 THE REAL WIN IS THE WAVE BOUNDARY (Stockdon is NOT in the loop — SnapWave is)
The premier runs SnapWave (`snapwave=1`) off `snapwave.bhs/btp/bwd/bds` at 7 support
points fed from **`era5_waves_nj`**. Two observation-confirmed defects there:

1. **ERA5 gives byte-IDENTICAL Hs at all 7 support points, every timestep** — a 31 km
   cell cannot resolve a 25 km boundary, so the 7 points buy nothing over 1.
2. **ERA5 is pasting the DEEP-WATER wave field onto a ~10 m contour.** The bnd points
   sit at model z ≈ −9.7..−14.1 m. Arbitrated with **NDBC 44025 (36 m, deep water)**:

| time (UTC) | NDBC 44025 @36 m | ERA5 imposed @10 m | CORA @10.5–13.4 m |
|---|---|---|---|
| 10-29 18:00 | 8.79 | **7.66** | 3.53–4.80 |
| 10-30 00:00 | 7.80 | **7.82** | 5.07–6.02 |

ERA5 @10 m ≈ the buoy @36 m ⇒ **no shelf transformation whatsoever.** ERA5 isn't
wrong, it's being applied ~26 m too shallow. CORA sits 23–45% below the buoy — what
shoaling+breaking over 36→11 m should do — and carries up to **1.38 m of alongshore
spread** (Sandy Hook / Long Island shadowing) that ERA5 has zero of. Both peak at
10-30 00:00, so it's amplitude+width, not phase; ERA5's peak is also too NARROW
(decays to 4.03 by 10-30 12:00 vs CORA holding 5.2).
⚠️ Don't overstate the breaking argument: with 2–3 m surge, depth ≈13 m and the
γ=0.78 limit is ~10 m, so ERA5's 7.8 m is *near saturation*, NOT impossible. The
buoy comparison is the real evidence; the γ argument alone is not sufficient.

**Direction of the fix is favorable:** less boundary wave energy → less setup → lower
levels, and the premier HWM bias is **+0.32 m (too wet)**. Unlike the composite arm,
this one pushes the right way. CORA nodes are 0.08–0.27 km from the bnd points.
Pull recipe + data: scratchpad `cora_waves.py` → `cora_waves_bnd.npz`
(`swan_HS.63_2012_map.zarr` etc., per-year map files exist; ~13 s for all 3 vars).
Not yet built into a forcing file or scored.

## Other still-open CORA use
- **Independent validator** free of the gauge-fitting circularity our composite has.

Related: [[project_tidal_phase_lag]], project_noaa_boundary (memory retired 2026-07-25),
[[reference_premier_domain_guard]]
