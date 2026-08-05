<!-- Raw Claude-memory file, archived verbatim 2026-08-05 when the memory store was
     collapsed. Its standing content was merged into the new memory set and/or
     CLAUDE.md; this copy exists so the merge cannot have lost a detail.
     Superseded — do not treat as current. -->


## The lesson: an HWM records that water ARRIVED, not which way it came

Shark River Inlet was dammed shut in the DEM, so the **Shark River channel never floods in any
run — peak zs exactly +0.00 m.** Yet the model still floods Belmar/Avon, because **the ocean
overtops the beach and runs OVERLAND through the streets.** So the two Shark HWMs come out
**WET** (0.30 m and 2.39 m deep) while the river behind them is bone dry.

**The model got roughly the right answer in the right place by an entirely wrong pathway, and
every mark-by-mark metric was blind to it.** This is the deep lesson — not a metric bug.

Shark had **no working diagnostic at all**:
1. Its only 2 HWMs are **quality 3**, below the `qual <= 2` headline cut ⇒ never scored, wet or dry.
2. Even if scored they read **flooded** (overland), so they could never reveal a dead river.
3. Its only other metric, tidal range, was computing `max − min` of the model's monotonic
   **spin-up drawdown** (`+0.00 −0.63 −0.86 … −1.27`, no oscillation at all) ⇒ 1.27 m, which
   next to the observed 1.82 m looked like a plausible mildly-damped tide.

**FIXED 2026-07-14 in `nj_sfincs/validate.py`:** `_tidal_signal()` de-trends the spin-up and
uses **fraction-of-time-rising** as the discriminator (a tide floods and ebbs; a drain only
ebbs). Shark now returns `is_tidal=False` in every run — the alarm that was missing. Beware two
traps I hit: the drawdown is an EXPONENTIAL, so linear de-trending leaves a ~1 m bowed residual
that still looks like a range; and counting turning points is defeated by numerical wiggle.
Also added a `shark_river` HWM basin so it stops hiding inside `south_coast`.

## Separately: the HWM dry-mark flaw is REAL but was NOT the culprit

`hwm_metrics()` computed `head = wet & (qual <= 2)` ⇒ **a mark the model leaves DRY was dropped
from bias/RMSE, not scored as an error.** That structurally **rewards under-flooding**: the worse
the model under-floods, the more marks vanish and the better the average looks. (Mirror image of
the FEMA-MOTF POD flaw, which rewards OVER-flooding. Never lead with either alone.)

Fixed: dry marks are now scored against the model's ground elevation (`hwm_*_scored*` keys), and
`hwm_n_dry` is always reported.

**⚠️ BUT DO NOT REPEAT MY ERROR: I initially blamed this flaw for hiding Shark, and that was
wrong.** `n_dry = 0` for q<=2 marks in all six leak-fix runs — no dry mark was ever dropped. The
quality cut and the broken tide metric hid Shark; the dry-mark flaw never got the chance.

**How to apply:** always read `hwm_n_dry` and `hwm_n_scored` next to any bias; treat a CHANGE in
scored-mark count between two runs as invalidating the comparison. Only 19 of the 31 Sandy HWMs
pass `q<=2` at all. And when a basin looks fine, ask whether the water could be arriving by the
wrong path — check the TIDE (does it oscillate?), not just the peak.

## Gauge-cell sampling: the fix for INTERIOR gauges is WRONG for OPEN-COAST ones (2026-07-20)

`_wet_channel_cells()` (median of cells with bed < −1 m near a gauge) exists because the SFINCS
obs points snap to dry high banks. It is correct for the **interior river gauges**. But the
**open-coast** obs point `usgs_stormtide_sea_bright` (the USGS SSS storm-tide sensor 2258) sits on
a **+2.03 m shorefront/barrier cell** that only wets at the storm peak — so `_wet_channel_cells`
skips it and grabs offshore surf cells **~0.35 m lower**, reading the crest as 3.11 m (err −0.35).
Sampling the model **AT the sensor** (the his `point_zs` obs-point, blanking the dry pre-surge
steps) gives **3.65 m vs obs 3.465 (+0.19)** — the right answer, and matches the pre-K +0.18.
⇒ `plots.plot_gauge_verification` now samples **surge gauges via the his obs-point, interior tide
gauges via the wet-channel median.** Rule: at the OPEN COAST use the exact obs-point; the
wet-channel-median trick is only for dodging dry BANKS at interior gauges.

**Bonus finding (partially answers the domain-rebuild locality thread):** at that SSS sensor the
model peak is **3.62 m (pre-rebuild `snapwave_tuned`) → 3.65 m (sealed premier)** — no drift. So
the ~0.1 m open-coast wobble in [[project_domain_rebuild]]'s locality caveat lives in the
`south_coast` HWM-residual basin, NOT in the one instrument-grade open-coast surge we have.

See [[project_shrewsbury_reinvestigation]].
