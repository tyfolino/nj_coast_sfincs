<!-- Raw Claude-memory file, archived verbatim 2026-08-05 when the memory store was
     collapsed. Its standing content was merged into the new memory set and/or
     CLAUDE.md; this copy exists so the merge cannot have lost a detail.
     Superseded — do not treat as current. -->


# Which metric leads — settled 2026-07-27

## ⚠️ 2026-07-28 — THE SIGN WARNING BELOW FIRED, AND HARDER THAN WRITTEN

The pre-registered "check the sign" caveat was right to exist but understated the problem:
**the sign was not a property of the model at all.** It came from the `max`-over-±50 m HWM
estimator, which is unbounded in the radius. Under the now-adopted `median` the premier is
**−0.21 m (slightly DRY)**, not +0.32 m wet — so "reduce the water level", which selected
every level arm, was pushing the wrong way. The ranking inverts exactly, and under `median`
the arms sit within ~0.05 m of each other, i.e. **inside** the spread between estimator
choices. See [[reference_hwm_estimator_artifact]].

**What this does NOT change:** HWM still leads, CSI is still a cost. What it changes is that
**a bias is not quotable without its estimator and radius** — `hwm_metrics` now stamps
`hwm_estimator` / `hwm_radius_m` into every row for exactly this reason. And the adoption of
`wave-deep30+tide-shift` as "the best level arm" rested on the `max` ordering; on HWM
evidence those arms are **not separated**.

⇒ The strongest remaining level evidence is **not** the HWMs. It is the Barnegat Bay pair
(along-bay gradient inverted by −0.93 m against 6-min records) — see
[[project_domain_expansion_v2]].

**HWM residual is the headline. CSI is reported as a cost. A CSI drop does NOT veto an
HWM win.**

The user confirmed this rather than treating it as an open call, on the grounds that the
project already had the house rule "believe HWM over CSI" — which exists because **CSI
once hid a completely dammed Shark River Inlet behind a near-perfect basin bias**. So
the rule was already earned; it just had not been applied to the level-vs-extent
question explicitly.

**Why:** this resolves the trade left open by `wave-deep30+tide-shift` on v1 — best level
arm (bias 0.273, RMSE 0.449) and worst extent arm (CSI 0.684 vs the premier's 0.706, plus
one wet HWM going dry). Under this rule the union is adopted-on-level and its extent cost
is a stated cost, not a blocker.

**How to apply:**
- Lead every results table with `hwm_bias_m_scored` / `hwm_rmse_m_scored`; report
  `motf_csi`, `motf_pod`, `hwm_n_dry` in the same table as costs, never omitted.
- ⚠️ **CHECK THE SIGN BEFORE CALLING A SMALL |bias| A WIN.** If bias goes meaningfully
  NEGATIVE the model is now UNDER-forced, and "bias improved" stops being the right
  reading — that is a different failure, not a better model. This matters most for
  `wave-cora`, which cuts boundary Hs from 8.62 m to ~5–6 m and could plausibly overshoot
  the v1 premier's +0.32 m wet bias straight through zero.
- **Fix the criterion BEFORE looking at results.** With a lever this large, whichever
  metric is read first decides the verdict. This is the same failure mode the scoring
  code already warns about twice: the wet-only HWM metric structurally REWARDS
  under-flooding (a mark the model never wets drops out of the average), and MOTF POD
  structurally rewards OVER-flooding. Never lead with either alone.
- ⚠️ Reporting rule that survives any criterion: **`hwm_within_0.5` on 19 marks moves in
  ~5-point steps because one mark is 5.3%.** Do not quote it as a 5-point gain — say
  "one mark of 19".

Related: [[project_snapwave_decoupling]] (the trade this resolves),
[[project_cora_evaluation]] (the arm that sharpens it),
[[reference_hwm_metric_blindspot]], [[project_domain_expansion_v2]].
