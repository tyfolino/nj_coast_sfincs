<!-- Campaign record. Moved out of the Claude memory store 2026-08-05; the
     memory file was `reference_hwm_estimator_artifact`. -->

> **Historical record — read top-down, newest first.** Blocks are appended in
> reverse chronological order and later blocks SUPERSEDE earlier ones, including
> where an earlier block calls itself current. Several conclusions in here were
> retracted; the retraction is always above the claim it retracts. For what is
> believed true *now*, see the memory store and `CLAUDE.md`, not this file.
>
> **Standing summary at the time of the move:** 🔴🔴 2026-07-28 — the HWM \"max WSE over a ±50 m window\" estimator MANUFACTURES the campaign's positive bias and is UNBOUNDED in radius. ✅ USER ADOPTED `median` 2026-07-28. The v1→v2 regression is NOT real, and the level-arm ranking INVERTS.


# The HWM score measures the window, not the model

`validate.hwm_metrics` scores a mark as **`max(WSE)` over a ±50 m window**, ground-capped
to cells with `dep <= obs + 0.5`. That estimator is **unbounded in the search radius** —
widen the window and it can only climb. Measured on the v1 premier, 19 q≤2 bridge marks:

| radius | 0 m | 12.5 m | 25 m | **50 m** | 75 m | 100 m | 150 m |
|---|---|---|---|---|---|---|---|
| bias (max) | −0.134 | +0.018 | +0.093 | **+0.322** | +0.511 | +0.690 | +1.115 |

**50 m is just where the code stops.** The argmax sits ~50 m from the mark — i.e. on the
window's outer ring — in essentially every case, which is the signature of an unbounded
max. Every *bounded* estimator is flat in radius and **negative**:

| estimator | radius swing 12.5→150 m | v1 premier bias @50 m | RMSE | within-0.5 |
|---|---|---|---|---|
| `max` (production) | **+1.10 m** | **+0.322** | 0.483 | 0.737 |
| `nearest` wet cell | +0.041 | −0.169 | 0.275 | 0.947 |
| `median` of wet cells | +0.066 | −0.213 | 0.385 | 0.947 |
| `p75` of wet cells | +0.080 | −0.172 | 0.367 | 0.947 |

## 🔑 Two settled conclusions are affected

**1. The v1→v2 "regression" is NOT real — cross-domain comparison is UNBLOCKED.**
The +0.169 m bias jump (v1 0.318 → v2 0.487) exists *only* at radius 50 m. The v2−v1 gap
is −0.031 at 12.5 m, +0.171 at 50 m, +0.080 at 100 m, −0.089 at 150 m — noise, not a
signal. Under `nearest` the gap is a stable −0.016; under `median`, +0.027. **Point-sampled
the two domains agree to −0.013 m.** The depth field was already known identical where both
are wet (mean +0.006 m); the marks confirm it. The mechanism is grid alignment: the two
domains' raster origins differ by 1433 m ≡ 0.28 px at 6.25 m, and each is independently
de-rotated (both tifs are stored with ~0.76° shear), so the 50 m windows cover different
cells and a max-estimator resamples a different extreme.

**2. The level-arm ranking INVERTS, because the SIGN of the bias flips.**
Every level arm removes water. Under `max` the bias is positive so removing water helps;
under any stable estimator it is negative so removing water hurts. The order is exactly
reversed (31-mark bridge set, q≤2, 50 m window, same marks):

| arm | bias `max` | bias `nearest` | RMSE `max` | RMSE `nearest` |
|---|---|---|---|---|
| v1 premier | +0.322 | **−0.169** ⭐ | 0.483 | **0.275** ⭐ |
| v1 `tide-shift` | +0.308 | −0.189 | 0.469 | 0.289 |
| v1 `wave-deep30` | +0.290 | −0.214 | 0.465 | 0.306 |
| v1 `wave-deep30+tide-shift` | **+0.278** ⭐ | −0.228 ✗ | **0.452** ⭐ | 0.315 ✗ |
| v2 premier | +0.492 | −0.185 | 0.636 | **0.267** ⭐ |
| v2 `wave-cora` | +0.445 ⭐ | −0.225 ✗ | 0.601 ⭐ | 0.287 ✗ |

This is precisely the sign trap [[feedback_scoring_criterion]] pre-registered ("a negative
bias is UNDER-forcing, not a win"). It fires harder than expected: the sign was never a
property of the model, it was a property of the estimator.

## ✅ DONE 2026-07-28 — `median` IS the default, code changed and reports re-scored

The user adopted `median` ("**max is too generous, especially over such a large radius**").
**Shipped the same day:**

- `validate.hwm_metrics(..., estimator="median", radius_m=50.0)` — dispatches
  `median` / `max` / `nearest`, raises on anything else, and **stamps `hwm_estimator` +
  `hwm_radius_m` into every result row** so a CSV always says which measurement it is.
  `HWM_ESTIMATORS` / `HWM_ESTIMATOR_DEFAULT` / `HWM_RADIUS_M` are module constants.
- `validate.evaluate(..., hwm_estimator=...)` threads it.
- **`plots._sample_hwm` was a SECOND, INDEPENDENT COPY of the sampler** — figures and the
  scored CSV could silently disagree about a mark's modelled level. It now imports
  `DEPTH_MIN` / `HWM_RADIUS_M` / the default from `validate` and shares the dispatch.
- `score_v2.py --estimator` (default `median`). Its hardcoded `V1_REFERENCE` (the `max`
  numbers 0.318/0.480 …) was **deleted** — it now reads v1 under the *matching* estimator
  from `reports/arm_rescore_estimators.csv`, and refuses to fall back rather than print a
  cross-estimator comparison.

### ⚠️ `DEPTH_MIN` — a real trap the first scripts fell into
Production is **`DEPTH_MIN = 0.15`**, not the 0.05 the first diagnostic scripts used. It
moves every number by ≤0.02 m and changed no conclusion, **but only at 0.15 does the
replication reproduce the frozen campaign EXACTLY** (v1 premier max@50 m = 0.3184 vs the
published 0.318; tide-shift 0.3023/0.4662; wave-deep30 0.2849/0.4628; union
0.2732/0.4490). Always import `DEPTH_MIN` from `validate`; never re-type it.

### ⚠️ A silent-staleness trap this shook out
All three `scripts/hwm_estimator_*.py` wrote their CSV to a **relative path** (a leftover
from being scratchpad scripts), so a regenerated `arm_rescore_estimators.csv` landed in the
repo ROOT while `score_v2.py` kept reading the stale copy in `reports/`. The numbers were
close enough (0.322 vs 0.318) to look right. **Any script whose output another script
consumes must write an absolute path** — all three now use
`OUT = Path(__file__).resolve().parents[1] / "reports"`. Same family as
[[reference_floodmap_cache_traps]]: a stale artifact that reads back perfectly clean.

### Re-scored numbers (median, 50 m, `hwm_bias_m` wet-only)

| | native-95 bias | RMSE | n_dry | bridge-31 bias | RMSE |
|---|---|---|---|---|---|
| v2 premier | **−0.250** | 0.494 | 7 | **−0.187** | **0.329** |
| v2 `wave-cora` | −0.293 | 0.507 | 8 | −0.231 | 0.350 |

v1 under median, 31 marks: premier **−0.213 / 0.385**, `tide-shift` −0.235 / 0.398,
`wave-deep30` −0.251 / 0.404, union −0.264 / 0.412.

🔑 **The v2 premier (−0.187 / 0.329) is BETTER than the v1 premier (−0.213 / 0.385) on the
identical 31 marks.** The domain expansion slightly *improved* the north — the exact
opposite of the "regression" that blocked this comparison for a day.

⚠️ Dry-mark interaction, kept as a SEPARATE axis: the `*_scored` family folds dry marks in
at ground elevation and pulls the pooled mean down (native-95 premier wet-only `max` 0.510
vs scored 0.482, 7 dry). Don't let an estimator change silently also change which marks
are counted.

## How to apply

- **Do NOT quote `hwm_bias_m` / `hwm_rmse_m` as a model property without naming the
  estimator and its radius.** The number has no converged value.
- ⚠️ **This does NOT by itself make `nearest` correct.** The window exists for real
  reasons — HWM coordinates carry positional error and marks sit on structures at the
  flood edge. The claim is narrower and stronger: `max` has *no converged value*, so the
  **sign** of the bias — which selected every level arm — is an artifact.
- ⚠️ **It does NOT overturn the physical case for `wave-cora`.** That case was always
  "the ERA5 boundary imposes Hs *above* the depth-limited breaking limit ⇒ inadmissible",
  which is independent of the score — see [[project_snapwave_decoupling]] and
  [[project_cora_evaluation]]. The score inverting is a reason not to *lead* with the
  score, not a reason to drop the arm.
- Under stable estimators the arms sit within ~0.06 m of each other, i.e. inside the
  spread between estimator choices. Treat the level arms as **not separated** by HWMs.
- Reproduce with the scratch scripts (rewrite if lost): sweep the radius over
  {0,1,2,4,8,12,16,24} px on `floodmap_hmax_lev3.tif` + `subgrid/dep_subgrid_lev3.tif`,
  mirroring `validate.load_floodmap` (de-rotate via `.rio.reproject`, then
  `reproject_match` the dep, then `.where(dep > -0.5)`).

Related: [[feedback_scoring_criterion]], [[reference_floodmap_cache_traps]] (the OPEN
clipped-vs-full raster discrepancy is very likely this same estimator),
[[reference_hwm_metric_blindspot]], [[project_domain_expansion_v2]].
