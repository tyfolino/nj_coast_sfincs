<!-- Campaign record. Moved out of the Claude memory store 2026-08-05; the
     memory file was `reference_bay_volume_deficit`. -->

> **Historical record — read top-down, newest first.** Blocks are appended in
> reverse chronological order and later blocks SUPERSEDE earlier ones, including
> where an earlier block calls itself current. Several conclusions in here were
> retracted; the retraction is always above the claim it retracts. For what is
> believed true *now*, see the memory store and `CLAUDE.md`, not this file.
>
> **Standing summary at the time of the move:** Barnegat Bay's defect is a cumulative volume+tilt error, not an inverted gradient. validate.bay_error_decomposition splits them and is the free GATE on expensive arms. Gate result: TILT-dominated on every arm, timing matches the wind reversal, matched-instant ratio 0.549.


# The Barnegat Bay defect — diagnosed and decomposed 2026-08-03

## ⚠️ THE CORRECTION — "the gradient is inverted" was a METRIC ARTEFACT

`ig_alongbay_*` is **peak minus peak**, and the two gauges peak ~6 h apart: it compares
Barnegat Light at 00:24 (difference ≈ −1.5 m) against Mantoloking at 06:18 (≈ +1.1 m).
It conflates GRADIENT with TIMING and reported a spurious inversion.

**At matched instants** (`ig_*` = his path; regression-tested and reproducible):

| time | obs ML−BL | mod ML−BL | ML deficit |
|---|---|---|---|
| 10-29 22:00 | −1.835 | −1.163 | **+0.429** |
| 10-30 00:00 | −1.548 | −1.316 | +0.249 |
| 10-30 02:00 | −0.335 | −0.982 | −0.525 |
| 10-30 06:00 | **+1.119** | **+0.679** | −0.860 |
| 10-30 12:00 | +0.585 | −0.217 | **−1.086** |

⇒ **always check a peak-to-peak statistic against matched instants before calling a
mechanism broken.**

## ✅ THE TOOL — `validate.bay_error_decomposition` (free, no solver time)

```
volume = mean(err_north, err_south)   -> inlet / southern connection / boundary
tilt   = err_north - err_south        -> wind stress / friction / conveyance
```
Plus `alongbay_matched_m` (matched-instant gradient — **a different quantity from
`ig_alongbay_*`, never report them under one name**) and sign-flip times.
Companion: `validate.interior_gauge_series(model_dir, gauge, source="map"|"his")`.
Wired into `scripts/score_interior_gauges.py` → `reports/v2_interior_gauges.csv`.
Constants: `BAY_WINDOW`, `WIND_REVERSAL = 2012-10-29T23:00`.

## ⭐ GATE RESULT (2026-08-03) — TILT-dominated, and the timing fits wind

| arm | volume mean | volume final | tilt mean | dominant | tilt/vol |
|---|---|---|---|---|---|
| `wave-cora+bed-ehydro` (pre-repair) | −0.053 | −0.798 | +0.379 | tilt | 1.09 |
| `+mask-inlet` | **−0.415** | −0.675 | −0.169 | **tilt** | 1.23 |
| `+mask-inlet+tide-shift` | −0.416 | −0.688 | −0.170 | tilt | 1.20 |

**Matched-instant gradient**: obs max +1.131 at 10-30 07:00; model **0.621 → ratio
0.549** post-repair. Pre-repair ratio was **1.415** — the clamp OVER-produced the tilt
because it gave Barnegat Light a 1.346 m tidal range vs 1.003 observed. 0.549 is the
honest number.

**Sign-flip timing**: obs tilt flips 10-30 03:00, model 10-30 04:00 — agree to 1 h, both
~4 h after the `WIND_REVERSAL`. ⇒ the model's tilt RESPONSE TIMING is right; only the
MAGNITUDE is short. tilt ∝ U² ⇒ 0.549 → wind ratio **0.741**, against the measured
ERA5 bay/ocean wind ratio of **0.77–0.81**. That is the land-roughness story, quantified.

⇒ **BOTH planned runs are justified**: tilt dominates (wind arm) but volume is also
−0.415 post-repair (Manahawkin bracket arm). They are independent — run in parallel.

## 🔍 The two suspects

1. **Wind — the leading one.** ERA5's *magnitude* is right (within 3–7% of NDBC
   44025/44009/44065) but the ERA5 cells over Barnegat Bay are **LAND-centred**, so its
   10 m wind is diagnosed against forest roughness while SFINCS applies a **marine** drag
   law (`cdnrb=3`). Not a tuning knob — an inconsistency in the forcing chain.
   ⚠️ A replacement product only helps if it resolves the 4–6 km bay as WATER: NAM
   (12 km), CFSv2, NARR all still put land there; HRRR did not exist in 2012.
2. **Southern wall — ⬆️ PROMOTED 2026-08-04, the demotion argument was WRONG.**
   ❌ The reasoning below was: deficit is LARGEST far from the wall (−1.09 m at
   Mantoloking, 40 km) and smallest near it (−0.3/−0.4 m at Barnegat Light, 6 km), so
   "a missing source at the wall would do the opposite." **Measured, it does exactly the
   same thing**: the Manahawkin bracket's width is +0.666 m at Mantoloking vs +0.431 m at
   Barnegat Light — larger FAR from the cut, matching the deficit's own shape. Barnegat
   Light is pinned by its inlet exchange; added supply shows up at the mid-lagoon
   constriction. ⇒ **never infer a source's location from where its effect is largest
   in a constricted basin — run the bracket.** See [[reference_bracket_pattern]].

## ❌ NOT the Mantoloking breach

The model already overtops the barrier (~9,700 land cells wet in the barrier band); the
deficit is bay-wide and grows with time; and the breach opened DURING the storm, so a
static pre-storm breach injects water hours too early.

Related: [[project_handoff_2026_08_03]], [[reference_inlet_waterlevel_clamp]],
[[reference_manahawkin_alarm]].
