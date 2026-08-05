<!-- Campaign record. Moved out of the Claude memory store 2026-08-05; the
     memory file was `reference_sandy_hook_gap`. -->

> **Historical record — read top-down, newest first.** Blocks are appended in
> reverse chronological order and later blocks SUPERSEDE earlier ones, including
> where an earlier block calls itself current. Several conclusions in here were
> retracted; the retraction is always above the claim it retracts. For what is
> believed true *now*, see the memory store and `CLAUDE.md`, not this file.
>
> **Standing summary at the time of the move:** MEASURED 2026-08-04: the Sandy Hook (8531680) record really does stop at 2012-10-29 23:36 UTC — both products, both datums. GESLA-4 is dead as a source. The non-circular way to qualify a reconstruction is to score it at Battery + AC, which survived the crest.


# The Sandy Hook gap — measured, and how to get around it honestly

## ✅ The gap is REAL (verified 2026-08-04, not inferred)

Re-queried NOAA CO-OPS `datagetter` for station **8531680**, 2012-10-28→31:

| product | datum | n | last value |
|---|---|---|---|
| `water_level` (6-min) | NAVD | 477 | **2012-10-29 23:36** |
| `water_level` | MSL | 477 | 2012-10-29 23:36 |
| `hourly_height` | NAVD | 48 | 2012-10-29 23:00 |
| `hourly_height` | MSL | 48 | 2012-10-29 23:00 |

All four hit the identical wall. Sandy made landfall near Brigantine ~23:30 UTC that
night, so **the gauge died essentially at landfall**. Not a fetch artifact, not a product
or datum choice. This confirms the 48/96-hour NaN block in
`data/gtsm/noaa_sandy_validation.nc` (10-30T00:00 → 10-31T23:00).

⚠️ Note the 6-min product reaches **23:36**, 36 minutes further than hourly. Marginal, but
it is the last real observation and worth using if a splice point is ever needed.

## ⛔ GESLA-4 is dead as a source

It is an archive of *observations* drawing on the same national networks, so for NJ its US
content **is** CO-OPS. It will carry this identical gap. It adds nothing here; its value is
global multi-decadal extreme-value statistics, not event hindcasting.

## ⛔ GSSR — and why "it's circular" was only half right

GSSR (Tadesse & Wahl) is an ML surge **reconstruction** at ~880 tide-gauge locations,
ERA5-driven, hourly. It *will* have a Sandy Hook value regardless of the gauge dying — that
is its purpose. Three standing objections: it is point data at gauges (no spatial field);
it compresses the tail because it is trained on a mostly non-extreme distribution; and it is
ERA5-driven, so it inherits the same forcing our own model already has.

⚠️ **The "you cannot validate the fill because the data you'd validate against IS the gap"
objection is WRONG, and the user caught it.** You do not have to validate at Sandy Hook.

## ⭐ THE NON-CIRCULAR SCREEN — "Test B"

**Battery (8518750) and Atlantic City (8534720) both have complete records straight through
the crest**, and they flank Sandy Hook at ~20 and ~40 km. Score any candidate reconstruction
*there*, at the peak, for this storm:

| metric | what it catches |
|---|---|
| peak level error | tail compression on **this** event |
| peak timing error | the known coastal phase defect |
| tidal amplitude ratio | what killed raw GTSM (×0.66 at 6 stations) |

Suggested gate: peak error ≤0.15 m at **both** stations and amplitude ratio 0.90–1.10.
**Pre-register before looking** — same discipline as [[reference_bracket_pattern]], and
[[feedback_ehydro_prediction_miss]] is the reminder to pick the diagnostic before you know
which side it lands on. Nothing gets a SLURM run unless a candidate passes.

Candidates: GSSR, **Parker et al. (2023) corrected GTSM** (the most promising — it corrects
exactly the tidal under-amplitude that retired `phaselag_gtsm`), CORA, any validated Sandy
ADCIRC hindcast (USACE NACCS / FEMA Region II).

## ⚠️ If something passes, do NOT rebuild the composites

Both Sandy Hook composite arms are RETIRED and marked do-not-re-run:
- `phaselag_composite` gave SH the Battery's NTR **unscaled** (funnel-amplified) — HWM bias
  +0.32 → **+0.73 m**, within-0.5 m 74% → **21%**, SSS 2258 3.65 → 4.01 vs obs 3.465.
- `phaselag_composite_v2` interpolated the NTR and *still* sat off the surge line away from
  the peak (+0.012 m at its own latitude but **+0.049 m at Shark River**).
- `tide-shift` won by inserting **no node at all**.

🔑 **That failure mode is a property of having THREE points, not of Sandy Hook.** A third
node perturbs a two-node line. Replacing the interpolant wholesale with a few hundred points
leaves no "line" for a node to sit off — so 2 → ~300 is qualitatively different from 2 → 3.
That, not a v3 composite, is the thing a passing reconstruction unlocks.
See [[reference_florence_boundary_practice]].

⚠️ Also: the retirement's "linear interpolation is not a meaningful error source" argument
was established **ON THE OPEN COAST** (CORA vs a CORA-built interpolant at the same two
points, so its own bias cancels). It does **not** extend to a semi-enclosed amplifying basin
like Raritan Bay. See [[reference_bay_tidal_amplification]].

Related: [[project_tidal_phase_lag]], [[project_handoff_2026_08_04]]
