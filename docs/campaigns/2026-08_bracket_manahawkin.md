<!-- Campaign record. Moved out of the Claude memory store 2026-08-05; the
     memory file was `reference_bracket_pattern`. -->

> **Historical record — read top-down, newest first.** Blocks are appended in
> reverse chronological order and later blocks SUPERSEDE earlier ones, including
> where an earlier block calls itself current. Several conclusions in here were
> retracted; the retraction is always above the claim it retracts. For what is
> believed true *now*, see the memory store and `CLAUDE.md`, not this file.
>
> **Standing summary at the time of the move:** How to build a DELIBERATELY INADMISSIBLE domain that bounds a quantity without ever being mistakable for a candidate. premier.BRACKETS + BRACKET+ prefix + NJ_ALLOW_BRACKET + waived-invariant banner. First instance: manahawkin-open, sha 67378a9f00b13410.


# The BRACKET pattern — bounding a quantity with a known-wrong domain

## The idea

When a modelling choice is a bound rather than a truth, run BOTH bounds instead of
arguing. The shipped v2 domain **walls off** Barnegat Bay at lat 39.70 (Little Egg and
Beach Haven inlets are outside), so it can only UNDER-supply the bay. Leaving hydromt's
original `mask==2` standing there imposes the open-ocean level on interior bay water,
which can only OVER-supply it. **The width between them is the most the southern
connection could possibly be worth** — and it costs one ~3 h run instead of a ~1.4 M-face
southward mesh rebuild plus a re-baseline of every arm.

## ⚠️ Why the safeguards are heavy

This creates the SAME defect class as the inlet clamp, which **scored well** and cost the
entire 2026-07-26..29 campaign. The lesson recorded then was that labelling is not
enough — **the guard has to refuse.** So:

| mechanism | where |
|---|---|
| separate `premier.BRACKETS` registry, **NEVER `EXPECTED`** | putting it in `EXPECTED` would make `assert_sealed_domain` **PASS** on it — the exact property we must not have |
| `assert_sealed_domain` raises a bracket-specific error naming the bound and why | `premier.py` |
| `premier.assert_bracket()` requires `NJ_ALLOW_BRACKET=<name>` | so a copied command line cannot stage one |
| name starts `BRACKET+` (`premier.BRACKET_PREFIX`) — machine-checkable, sorts to top | deliberately redundant with `Experiment.bracket` |
| `--experiments all` filters `exp.bracket is not None` and says what it skipped | `run_experiments.py` |
| metrics row stamped `domain = "BRACKET:<name> INADMISSIBLE"`, never `metrics.csv` | `collect_metrics` |
| waived invariant prints a 78-char banner every build | `model._check_domain_invariants` |
| the "invariants OK" line reports the waiver instead of claiming OK | `model.py` |

## How to build one (mask-only variant)

`scripts/setup_manahawkin_open_template.py` is the worked example, modelled on
`setup_inlet_mask_template.py`. `model.apply_mask_and_boundary` now takes two
keyword-only args, **both defaulting to empty so every existing caller is byte-identical**:

```python
model.apply_mask_and_boundary(base, sf,
    skip_overrides=frozenset({"manahawkin_cut"}),        # let hydromt's mask==2 stand
    allow_waterlevel_zones=frozenset({"manahawkin_cut"}),# and waive the alarm, loudly
)
```

Skipping an override WITHOUT waiving the matching zone just fails the invariant — correct
behaviour: the two must be waived together and on purpose.

**Assert it is a one-variable delta** (this template does): `z` byte-identical, subgrid
`z_zmin`/`z_volmax`/`uv_zmin`/`uv_navg` allclose, `snapwave.{bnd,bhs,btp,bwd}`
byte-identical, the OTHER no-waterlevel zone still clean, and the fingerprint MOVED.

## First instance — `manahawkin-open`

Built 2026-08-03. **sha `67378a9f00b13410`** (mesh unchanged: 1143357 faces / 2164 edges).
Clean swap: active 814,938 → 814,883 (−55), waterlevel 2,911 → **2,966** (+55),
**outflow 295 → 295 unchanged**, inactive unchanged. The 55 is exactly the count
`domain.py` predicted for the cut.
✅ Outflow-on-open-water check: **0 cells** deeper than `OUTFLOW_MAX_DEPTH` (−1.0 m) in
both arms; deepest outflow cell −0.98 m. **No repeat of the Navesink/Shrewsbury leak.**

Submitted as job **60021248** (64 cores / 96 G / 8 h — prior arms peaked at 6.07 GB RSS,
so cores and wall time are the levers, not RAM).

## Pre-registered before the run

1. It adds water at the SOUTH end ⇒ Barnegat Light rises more than Mantoloking and the
   along-bay gradient goes **further negative**. Hence, whatever the width, the southern
   wall **cannot** explain the tilt shortfall — a free result, independent of magnitude.
2. `ig_tide_range_barnegat_light` (0.808 vs 1.003 observed) rises toward or past
   observed — the same clamp signature the inlet repair removed.

**Decision rule:** width at Mantoloking **<0.25 m** retires the southward extension;
0.25–0.6 m = contributor not explanation; **>0.6 m** (and tilt not degraded, and the
walled run's deficit inside the bracket) justifies the rebuild.

## ✅ RESULT (scored 2026-08-04) — REBUILD JUSTIFIED, and P1 FALSIFIED

Job 60021248 COMPLETED in **2:46**; not truncated (73 map / 433 his reaching tstop).
Scored by `scripts/score_bracket.py` (written 08-04, name pre-committed in
`assert_sealed_domain`'s error text) → `reports/bracket_manahawkin.csv`.

**Width at Mantoloking: mean +0.666 / peak +0.980 / max +0.990 m.** All three statistics
land in the same bin, so the statistic the pre-registration failed to name does not
matter here. ⚠️ It could have — compute all three and report disagreement as
disagreement; do not pick one after seeing the numbers.

Both side conditions PASS: tilt **not** degraded (|err| 0.169 → 0.066) and the deficit is
**contained** (walled −0.499 < 0 < bracket +0.167 at Mantoloking; same at Barnegat Light,
−0.330 → +0.101). The width exceeds the deficit it must explain (0.666 > 0.499).
⇒ **the southward extension is justified by the pre-registered rule.**

### ❌ P1 FALSIFIED — and it was the "free result"

Predicted: water enters at the SOUTH ⇒ Barnegat Light rises MORE than Mantoloking, tilt
goes further negative, hence *whatever the width* the southern wall cannot explain the
tilt shortfall. Every clause went the other way:

| | Barnegat Light (6 km from the cut) | Mantoloking (40 km) |
|---|---|---|
| width mean | +0.431 | **+0.666** |
| width peak | +0.610 | **+0.980** |

Tilt err **−0.169 → +0.066**; matched-instant gradient ratio **0.549 → 0.810** (obs 1.0).
The bracket IMPROVES the along-bay gradient. Coherent in hindsight — Barnegat Light is
pinned by its own inlet exchange, so extra southern supply shows up hardest at the
mid-lagoon constriction. ⇒ **the southern connection is a live candidate for the TILT
defect too**, not only the volume deficit. See [[reference_bay_volume_deficit]], whose
"southern wall demoted" reasoning this overturns.

✅ **P2 CONFIRMED**: Barnegat Light pre-storm tidal range **0.808 → 0.973** vs 1.003 obs
(err −0.195 → −0.030). Mantoloking over-amplifies (range err +0.063 → **+0.411**) and
peak err goes −0.853 → +0.142 — the upper-bound signature, exactly as intended.

⭐ **The pattern worked.** One 2:46 run replaced a ~1.4 M-face rebuild + full re-baseline
as the way to decide whether to do the rebuild, AND falsified a pre-registered mechanism
claim for free. Reuse it.

Related: [[reference_inlet_waterlevel_clamp]], [[reference_bay_volume_deficit]],
[[project_handoff_2026_08_03]].
