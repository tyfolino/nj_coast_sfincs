<!-- Campaign record. Moved out of the Claude memory store 2026-08-05; the
     memory file was `project_tidal_phase_lag`. -->

> **Historical record — read top-down, newest first.** Blocks are appended in
> reverse chronological order and later blocks SUPERSEDE earlier ones, including
> where an earlier block calls itself current. Several conclusions in here were
> retracted; the retraction is always above the claim it retracts. For what is
> believed true *now*, see the memory store and `CLAUDE.md`, not this file.
>
> **Standing summary at the time of the move:** SOLVED 2026-07-26, PORTED TO v2 2026-07-28 (SLURM 59427768 running). Modeled tide peaked LATE (Sandy Hook +17.6, Shrewsbury +36.9 min) because the Battery-anchored boundary is +21 min late. FIX = `tide-shift`: advance the EXISTING Battery anchor's tide +24 min, 2 support points, no inserted node => SH lag -0.1 min, Shrewsbury 16.8, at NO level cost (HWM bias 0.318->0.302). The phase fix is FREE. v2 reproduces the defect (17.8/35.1/35.2) and wave-cora cannot touch it. Also 2026-07-28: plots._phase_tag was quoting +35 min against a scored 17.8 — two window bugs, fixed. Both composites (v1/v2, which inserted a Sandy Hook node) RETIRED + run dirs DELETED. GTSM scrapped.


# Tidal phase lag — the modeled tide peaks LATE (advisor-noticed, 2026-07-20)

## 🚀 2026-07-28 — PORTED TO v2_barnegat. SLURM **59427768** RUNNING (hal0357, 12 h/128 G/48c).

`experiments/tide-shift` in **`~/nj_coast_sfincs`** (the v2 repo). Expect ~3.5–4 h
(the two v2 arms ran 3:24 and 4:00). Score with `scripts/score_v2.py`.

**Why re-run rather than assume it carries over:** v2's control reproduces v1's defect
almost exactly — **17.8 / 35.1 / 35.2 min** (SH/Shrews/Shark) vs v1's 17.6/36.9/32.8 —
and **`wave-cora` moves it by ≤0.6 min**, confirming (as `wave-deep30` did) that the wave
boundary and tidal phase are independent error sources. So the *diagnosis* transfers (it
is a property of the forcing: Battery +24 min interpolated to AC −18 predicts +16.7 at
Sandy Hook), but everything downstream — 95 marks vs 31, 2× the mesh, a bay lobe, two
crest-surviving interior gauges — is new and unfalsified.

Pre-flight ALL VERIFIED (not assumed):
| check | result |
|---|---|
| `sfincs.inp` vs premier | **0-key diff** |
| domain audit | **4/4 sealed on v2_barnegat** (incl. the staged arm) |
| snapwave.bnd/.bhs/.btp/.bwd vs premier | **byte-identical** ⇒ clean single-variable A/B |
| control boundary sha | `62a35f63a08bb1f7` (= the recorded premier/wave-cora forcing) |
| boundary file | differs, `6eaba7ea84a9a8c1`; **2 stations, same coords, same 73-step hourly grid** |
| **Cape May trap** | **DID NOT FIRE — `[bnd] 2 water-level support point(s)`** |
| node 0 (Battery) | **shifted −18.2 min**, peak 3.417 → 3.385 (**−0.032 m**) |
| node 1 (Atlantic City) | **max\|Δ\| = 0.000000 m** |

- **The peak moving DOWN 0.032 m re-confirms "re-phasing does not add water."**
- ⭐ `prepare_experiment` now handles the whole staging dance itself — forcing swap,
  `check_waterlevel_support`, `restore_diagnostics`. **No hand-patching; `--no-run` then
  `run.submit_slurm(dir, sif=...)` is the clean route.** The old crsfile/storevel warnings
  below are OBSOLETE.
- ⚠️ The v2 repo had NOT taken the 2026-07-27 rename — its config still said
  `phaselag_shift`. **Renamed to `tide-shift` (config.py only; no dirs/CSVs existed, so
  the rename is complete). `snapwave_deep` / `snapwave_deep_phaseshift` are still
  old-style in the v2 repo** — rename them if they are ever ported.

### 🐛🐛 THE FIGURE WAS QUOTING A NUMBER THE CSV NEVER CONTAINED — FIXED 2026-07-28
`plots._phase_tag` printed **Sandy Hook Δφ +35 min** while `phase_lag_sandy_hook_min`
scored **17.8**, in the same notebook. Two independent defects, both now fixed (it takes
`win` + `dt_s` from the caller so it CANNOT drift from `validate.gauge_phase_lag` again):
1. It anchored its own 24 h window on `ot[0]` — **no `SPINUP_SKIP_H` skip**, re-introducing
   the ~+13 min inflation fixed in `validate` on 2026-07-21.
2. **🔑 THE REUSABLE TRAP: `_uniform_series` clips its grid to EACH SERIES' OWN coverage,
   and `_xcorr_lag_minutes` then aligns the two arrays by INDEX 0 — not by wall clock.**
   Obs start a day before `tstart`, so model index 0 was matched against an obs sample
   from a different time, adding a spurious offset on top of the real lag. **Any window
   not fully covered by BOTH series silently corrupts the lag.** Deriving the window from
   the MODEL's times is what keeps that alignment honest.

Verified numerically against `reports/v2_native95.csv`: **SH 35.0 → 17.8, Shrewsbury
NaN → 35.1, Shark NaN → 35.2** — exact agreement. (The interior panels previously showed
**no Δφ at all**, silently, for the same coverage reason.)
- Sea Bright SSS now reports **`crest Δt +38 min`** instead of a bogus `Δφ +1 min`: that
  sensor was deployed FOR the storm (record 10-29 22:30 → 10-30 01:12), so the old code
  shrank its window to 3.2 h of storm crest — **there is no tide in it**. New `_peak_tag`
  reports crest timing under a name that says what it is, and **refuses when the obs peak
  is the last finite sample** (a dead gauge reports a floor, not a crest).
- Guard added: no Δφ printed unless BOTH series are `is_tidal` over the window.

## 🟢🟢 SOLVED 2026-07-26 — `tide-shift` IS THE ADOPTION CANDIDATE. THE PHASE FIX IS FREE.

`reports/tide-shift.csv` (SLURM 59138942, 2:00:48, full-length 73 map / 433 his, sealed,
19 HWMs / 0 dry). Control re-scored through the SAME code path the same day →
`reports/faber-waves-premier_rescored.csv`, and it reproduces every recorded premier number exactly
(17.6/36.9/32.8, bias 0.318, RMSE 0.480, within 73.7%, CSI 0.706, hm0 max 7.44) ⇒ the
comparison below is same-run, not cross-session.

| | premier | composite_v2 | **`tide-shift`** |
|---|---|---|---|
| phase SH / Shrews / Shark (min) | 17.6 / 36.9 / 32.8 | 6.7 / 24.6 / 34.3 | **−0.1 / 16.8 / 16.9** |
| HWM bias | 0.318 | 0.500 | **0.302** |
| HWM RMSE | 0.480 | 0.606 | **0.466** |
| within-0.5 | 73.7% | 63.2% | 73.7% |
| ocnfrt / shrews / **shb** / south | 0.31/0.43/**0.09**/0.15 | 0.47/0.54/0.17/0.59 | 0.32/0.41/**0.06**/0.14 |
| MOTF CSI / POD / FAR | 0.706/0.799/0.141 | 0.746/0.871/0.162 | 0.701/0.792/0.142 |
| SH Bay hm0 mean / max | 0.884 / 7.44 | 0.913 / 11.21 | 0.890 / 4.01 |

- **🔑 THE LEVEL PENALTY WAS 100% THE INSERTED 3rd NODE.** Remove the node (re-phase the
  EXISTING Battery anchor instead) and the entire +0.18 m vanishes *while the phase win gets
  BIGGER* (6.7 → −0.1 min). **⛔ THE "CONSTRUCTIVE ALIGNMENT" EXPLANATION BELOW IS DEAD —
  re-phasing the tide does NOT add water.** v1's original "it added a support point" diagnosis
  was RIGHT; v2's rebuttal of it was wrong. Both composites are superseded and should not be
  re-run or cited as evidence about phase.
- **Sandy Hook lands at −0.1 min — the coastal lag is GONE, not halved.** The predicted
  +16.7 min interpolation artifact was the whole of it, as the source-phase analysis said.
- **⭐ NEW PHYSICS: the interior lag was mostly IMPORTED.** Shrewsbury 36.9 → 16.8, Shark
  32.8 → 16.9 — both roughly halve, and the composites never moved Shark at all. ⇒ the
  "+20 min UP-ESTUARY EXCESS" decomposition at the bottom of this file **over-attributed to
  conveyance**; the true residual excess travel time is **~17 min, not ~20+**. (⚠️ Shark is
  sampled from the HOURLY map so it quantises ±30 min — 32.8 → 16.9 is ~one step, treat as
  directional. Shrewsbury is 10-min his and is the trustworthy interior number.)
- **The known risk did NOT materialize.** Giving the Raritan Bay lobe an open-coast phase was
  the flagged cost; `sandy_hook_bay` **improves** 0.090 → 0.064, the best of any arm.
- **No threshold blow-up.** `south_coast` — the overwash basin that went +0.44/+0.59 nonlinear
  in v1/v2 — sits at 0.144 vs the premier's 0.147. Nothing crossed a weir crest. This is what a
  forcing change that genuinely doesn't add water looks like.
- ⚠️ Shrewsbury gauge err goes −0.099 → −0.120 (slightly worse); SH peak err improves
  −0.312 → −0.224. Small, opposite signs, not decisive either way.
- ⚠️ Its `shb_hm0_max` 4.01 is a **wetting transient, not wave physics** (mean flat at 0.890) —
  see [[project_snapwave_decoupling]] for why `shb_hm0_max` alone must not rank arms.
- **✅✅ `wave-deep30+tide-shift` SCORED 2026-07-27 — THE PHASE FIX IS FREE *AND* STACKS.**
  SLURM 59148558 COMPLETED. **Union bias 0.273 / RMSE 0.449 — the best level arm of the four, and
  the pre-registered "expect ~0.27" was met exactly.** Additivity vs premier: **RMSE 100%**
  (deep −0.0172 + shift −0.0138 = −0.0310; union −0.0309), bias 91%.
  **⭐ The phase fix survives the deep wave boundary UNTOUCHED: 0.1 / 17.1 / 16.7 min vs
  `tide-shift`'s own −0.1 / 16.8 / 16.9.** Moving the SnapWave boundary 20–45 km offshore does
  not perturb tidal timing — waves and tide phase are independent error sources.
  ⚠️ The union also inherits deep's costs (CSI 0.706 → 0.684, `hwm_n_dry` 1 → 2,
  `sandy_hook_bay` 0.064 → 0.142). Full table + the level-vs-extent trade in
  [[project_snapwave_decoupling]].
- **✅ THE 2×2's INTERACTION WARNING IS NOW RESOLVED — it was about the NODE, not phase.**
  `wave-deep30`+`composite_v2` had NOT made the phase fix free (bias 0.285 → 0.429). The
  nodeless `tide-shift` composes near-perfectly instead ⇒ **that +0.14 penalty was 100% the
  inserted 3rd node, confirming the same verdict the standalone arms reached.** Additivity, once
  the node is gone, is real.

### ⛔⛔ v1 + v2 RETIRED 2026-07-26 (user's decision). RUN DIRS DELETED. DO NOT RE-OPEN.
Marked ⛔ RETIRED in **both** `nj_sfincs/config.py` (EXPERIMENTS) and `data/data_catalog.yml`
(`noaa_sandy_composite`, `noaa_sandy_composite_v2`), the same way GTSM was. **Preserved:**
`reports/phaselag_composite.csv`, `reports/phaselag_composite_v2.csv` (the evidence), the
boundary forcing files at **`archive/retired_composites/<arm>/sfincs_netbndbzsbzifile.nc`**
(verified byte-identical before deletion), plus `data/gtsm/noaa_sandy_composite*.nc` and the
build scripts. **Deleted:** `experiments/phaselag_composite`, `experiments/phaselag_composite_v2`
(5.2 GB). `experiments/snapwave_deep_composite_v2` was NOT deleted — it is a snapwave-axis
factorial cell, not a v1/v2 arm.

**⭐ THE TWO REASONS A v3 IS NOT WORTH BUILDING** (both new on 2026-07-26, both verifiable):
1. **v2's node was NOT on the line after all — and the recorded cadence caveat was wrong too.**
   Reconstructed SFINCS' own along-boundary interpolation with cadence HELD CONSTANT (built a
   2-node interpolant from **v2's OWN Battery+AC columns**, so both sides are 6-min):

   | latitude | premier (2n, hourly) | cadence | **node** | total |
   |---|---|---|---|---|
   | Sandy Hook node | 3.118 | +0.012 | **+0.012** | +0.024 |
   | Sea Bright | 3.002 | +0.011 | **+0.012** | +0.023 |
   | Shark R | 2.772 | +0.008 | **+0.049** | +0.057 |
   | mid-coast | 2.541 | +0.051 | **+0.041** | +0.092 |
   | south HWMs | 2.266 | +0.050 | **+0.025** | +0.075 |

   **The node is on the line at its OWN latitude but +0.049 m off it at Shark River.** The
   on-line check was only ever done at the surge PEAK; the node's re-phased TIDE puts it off
   the line at other times, so the **max over time of the interpolated series between nodes
   rises**. ⇒ **the off-line error is DOWNSTREAM of the node, not at it** — which is why
   verifying at the node's own latitude missed it. **Also: cadence is NOT the +0.008 m recorded
   from a single latitude — it is +0.050 m mid-coast and south**, comparable to the node itself,
   so v2-vs-premier was always a TWO-variable comparison. (`tide-shift` is hourly like the
   premier ⇒ no cadence confound at all.)
2. **The geographic argument for a Sandy Hook node is independently CLOSED by CORA.** The
   surviving pro-node argument was "interpolating an open-coast boundary linearly across ~150 km
   from a HARBOUR gauge is crude, so breaking it at Sandy Hook is geographically right." CORA
   tested exactly that — compared against a linear interpolation **built from CORA at the same
   two points**, so CORA's own bias cancels — and found **linear interpolation is not a
   meaningful error source on the open coast** ([[project_cora_evaluation]]). ⇒ the node has
   nothing left to do: phase is fixed without it, and the level it would correct is not broken.
   **The ONE place linear interp genuinely fails is the Raritan/Sandy Hook Bay cells (lat ≈40.52,
   11–15% under-forced) — that is the BAY workstream ([[reference_bay_tidal_amplification]]),
   and a node at Sandy Hook's open-coast position would not fix it.**

⇒ A v3 could only tune the node's LEVEL to chase HWM bias, with **no independent constraint on
what that level should be** (the SH gauge died before the crest ⇒ unfalsifiable). That is
calibration — the same circularity that already got `NTR_DONOR_SCALE` rejected.
**🔑 And note the scoreboard alone could NOT have justified this: the model is already wet-biased
+0.32 m, so ANY boundary lift scores better when removed. The load-bearing evidence is the Sea
Bright storm-tide sensor (obs 3.465): premier 3.650, `tide-shift` 3.626, `wave-deep30`
3.607, v2 3.837 — the coast is ALREADY over-predicted, so it does not want more water.**

## 🔴 RESUME HERE (state at end of 2026-07-25 session — SUPERSEDED BY THE BLOCK ABOVE)

### ✅ SCORED 2026-07-25: `phaselag_composite_v2` — PHASE KEPT, HALF THE LEVEL DAMAGE SURVIVES ⇒ still NOT an adoption
`reports/phaselag_composite_v2.csv`. Domain check = **sealed**. All three arms score the
SAME HWM set (n_scored 19, n_dry 1) ⇒ apples-to-apples.

| | premier (control) | v1 composite | **v2** |
|---|---|---|---|
| phase SH / Shrews / Shark (min) | 17.6 / 36.9 / 32.8 | 7.8 / 25.5 / 35.1 | **6.7 / 24.6 / 34.3** |
| Shrewsbury gauge err (obs 2.935) | −0.099 | +0.251 | **+0.037** |
| SH peak pre-fail err (obs 2.808) | −0.312 | −0.181 | −0.251 |
| HWM bias / RMSE / within-0.5 | **0.318 / 0.480 / 74%** | 0.732 / 0.813 / 21% | 0.500 / 0.606 / 63% |
| MOTF CSI / POD / FAR | 0.706 / 0.799 / 0.141 | 0.768 / 0.919 / 0.177 | 0.746 / 0.871 / 0.162 |
| HWM bias by basin (ocnfrt/shrews/shb/south) | 0.31 / 0.43 / 0.09 / 0.15 | 0.65 / 0.76 / 0.35 / 0.93 | 0.47 / 0.54 / 0.17 / 0.59 |

### ⭐ THE LIVE ARM IS `tide-shift` (SLURM **59138942**, submitted 2026-07-25) — BOTH COMPOSITES ARE SUPERSEDED
Built the way plan §5 actually specified: **re-phase the EXISTING north anchor, do not insert a
node.** `scripts/build_noaa_phaseshift.py` → `data/gtsm/noaa_sandy_phaseshift.nc`, catalog
`noaa_sandy_phaseshift`, experiment `tide-shift`.

    total_Battery(t) = tide_Battery(t + 24 min) + NTR_Battery(t)
                       ^^^ timing only            ^^^ UNTOUCHED
    Atlantic City, Cape May: UNCHANGED (verified identical to 2.2e-16)

**Why 24 min, and why NOT shift AC** — NOAA harmonic phase vs Sandy Hook (+ = late), by
cross-correlation: **Battery +24 min** (a HARBOUR gauge standing in for an open-coast anchor —
this is the contamination), **Atlantic City −18 min** (the REAL tide wave propagating up the
coast — physically correct, keep it), Cape May +54 min.
**Interpolating +24 → −18 predicts +16.7 min of lag at Sandy Hook; the premier measures +17.6.**
The phase error is ENTIRELY this interpolation artifact — nothing else needed explaining.
Residual after the shift: **−0.7 to −3.1 min coastwide.**

Verified at staging: seal 1/1, **`sfincs.inp` delta vs premier = 0 keys**, 2 stations at the
premier's exact coordinates, same 73-step hourly grid (so no 6-min cadence confound), AC
bit-identical, tidal range preserved (1.614 → 1.623 m). Boundary tide moves **−16.4 min** at
Sandy Hook (measured with `validate._xcorr_lag_minutes`) and peak level moves **DOWN** 0.02 m.
Expect interior lag ~+17.6 → ~+1 min at Sandy Hook, ~+36.9 → ~+22 at Shrewsbury.
- **🔑 Because NO node is inserted, nothing can sit off the surge line — v2's failure mode is
  STRUCTURALLY IMPOSSIBLE here, not merely avoided.**
- ⚠️ Known cost: the Battery node also anchors the **Raritan Bay lobe (~760 cells, lat 40.52)**,
  which this gives an open-coast phase — but Raritan Bay's true tide really IS late, like the
  harbour. 2 of 19 HWMs. **Check `sandy_hook_bay` when scoring**; see
  [[reference_bay_tidal_amplification]].

### ⛔ 2026-07-25 — THE "CONSTRUCTIVE ALIGNMENT" EXPLANATION BELOW IS **WRONG**. READ THIS FIRST.
User pushed back ("18 min of phase can't raise a gauge 0.5 m") and **was right**. Read the two
`sfincs_netbndbzsbzifile.nc` files instead of arguing: **premier vs v2 differ in THREE ways, and
phase is the least of them.** premier = **2 stations, HOURLY** (73 steps); v2 = **3 stations,
6-MIN** (721 steps).

Decomposed at Shark River's latitude (reconstructing SFINCS' own linear interpolation):

| | boundary peak |
|---|---|
| premier (2 nodes, hourly) | 2.758 |
| + 6-min cadence | 2.766 (**+0.008**) |
| + 3rd support node | 2.817 (**+0.051**) |
| **total** | **+0.059 m** |
| **model response at the gauge** | **+0.508 m ⇒ ×8.6** |

**The boundary barely moves (+0.02..+0.06 m); the INTERIOR amplifies it 3–9×** (sandy_hook ×3.2,
tidal_sea_bright ×5.9, stormtide_sea_bright ×8.1, shark ×8.6). The mid-coast peak arrives 36 min
earlier at ~unchanged amplitude. **The cadence caveat is NEGLIGIBLE mid-coast (+0.008 m), not the
+0.021/+0.038 measured at the source nodes.** The dominant boundary term is the **3rd node
(geometry)** — so v1's "it added a support point" diagnosis was closer to right than v2's rebuttal.
- **Mechanism = a WEIR THRESHOLD, not addition.** `usgs_tidal_shark_river` sits at **`zb` = +1.79 m
  — a DRY-LAND cell**, flat at zs≈1.80 (= zb) until 10-29 22:00, then floods. It is an
  **overwash-arrival detector**, not an estuary tide gauge. Overtopping volume goes like
  (ocean − crest)^{3/2}, so +6 cm of boundary multiplies the volume delivered inside. Same family
  as the v1 `south_coast` outlier. Cf. [[reference_hwm_metric_blindspot]].
- **⚠️ METHODOLOGICAL CONSEQUENCE: if 6 cm of boundary yields 0.5 m at threshold sites, those sites
  cannot discriminate between forcing options, and HWM bias partly measures THRESHOLD SENSITIVITY
  rather than forcing quality.** Before attributing any future HWM shift to a forcing change,
  **reconstruct the imposed boundary series and check the amplification factor first.**
- Phase may still matter — but via *when* the peak arrives relative to the barrier crest
  (modulating the threshold), NOT by adding water. Untested.

**🔑 (SUPERSEDED framing) the v1 root-cause diagnosis was only HALF right.** v2 was built so the
inserted node lies exactly ON the existing Battery→AC surge line (verified pre-flight: SH peak
3.143 vs the 3.146 the 2-node line already implied, −0.004 m), so the "3rd support point lifts
the interpolation" mechanism was *removed by construction*. Yet HWM bias still landed at **+0.50,
not back at the control's +0.32** — it recovered only ~56% of v1's damage. **⇒ roughly +0.18 m of
the lift is NOT the support-point geometry. It is the re-phased TIDE ITSELF:** moving the tidal
peak ~11 min earlier slides it into better constructive alignment with the surge peak, so total
water goes UP everywhere. The lift is broadly uniform (+0.08..+0.16 per basin) EXCEPT
**south_coast again nonlinear (+0.44)** — same overwash threshold that blew up in v1.
- **Don't re-run a v3 that only re-tunes the boundary geometry** — geometry is now exonerated for
  the residual. The open question is whether the model was previously getting the right HWM level
  for the WRONG reason (a late tide de-tuning an over-energetic surge/wave forcing). That makes
  this thread **dependent on [[project_snapwave_decoupling]]**: if `wave-deep30` removes the
  excess boundary wave energy and drops HWM bias from +0.32 toward 0, re-score v2 ON TOP of it —
  the phase fix may become free (or even required) once the level is right. **Sequence: snapwave
  first, then re-test v2.** Do NOT adopt v2 standalone.
- Caveat that still applies to both arms: composites are 6-min, control forcing is HOURLY
  (+0.021 m Battery, +0.038 m AC purely from sampling). Small vs the +0.18, doesn't explain it.

### (RAN + NOW SCORED): `phaselag_composite_v2` = SLURM **58882823** (submitted 12:45 EDT 2026-07-22, hal0360, Faber)
**THE ARM THAT ISOLATES PHASE FROM LEVEL — the user's construction, better than my scale-factor idea.**
Split the composite's two halves by their real spatial behaviour: **TIDE local** (Sandy Hook's own
NOAA harmonic — sharp phase gradients) + **NTR INTERPOLATED** along the Battery→AC chord
(spatially smooth), w=0.164. **No fitted parameter** (v1's alternative was scaling the donor NTR
~0.91 to hit a target = calibration, not a diagnostic). Because the inserted NTR *is* the
interpolant of its neighbours, **the node lies ON the existing surge line — adding a point on a
line doesn't move the line** ⇒ surge field left as the premier had it, ONLY the tide changes.
Built by **`scripts/build_noaa_composite_v2.py`** → `data/gtsm/noaa_sandy_composite_v2.nc`,
catalog key `noaa_sandy_composite_v2`, experiment `phaselag_composite_v2` in `config.py`.

Pre-flight (all verified, not assumed):
| check | result |
|---|---|
| identity at own-NTR stations (Battery/AC/CapeMay) vs premier forcing | **max\|diff\| 0.000000 m** |
| SH peak vs the 3.146 m the premier's 2-node line already implied there | **3.143 (−0.004)**; v1 was 3.389 (**+0.243**) |
| `source_phase_lag` (+ = late vs real SH obs) | premier **+21.1**, v1 −2.6, **v2 −3.3 min** ⇒ phase fix KEPT |
| interpolated NTR vs SH's OWN observed NTR (717 samples pre-failure) | **corr 0.9974**, bias +0.088 m (conservative, timing-neutral) |
| domain / inp | sealed `45f4f74ca9a2347d`; `sfincs.inp` **identical** to control |

- **⚠️ STAGING GOTCHA (bit me on both arms): `prepare_experiment` DROPS `crsfile = sfincs.crs` and
  resets `storevel 1 → 0`.** Patch both back + `cp sfincs.crs` from the control, then submit the
  staged dir directly with `run.submit_slurm(d, sif=BaseConfig().container_sif)` — do NOT use
  `--slurm`, it re-runs `prepare_experiment` and wipes the patch. Always `diff <(sort ctrl/sfincs.inp)
  <(sort new/sfincs.inp)` before submitting. (`config.BASE` doesn't exist — it's `BaseConfig()`.)
- **⚠️ CADENCE CAVEAT: the composites are 6-min, the control forcing is HOURLY**, so the flanking
  nodes read +0.021 m (Battery 3.417→3.438) and +0.038 m (AC 1.877→1.915) higher purely because
  hourly sampling misses the true peak. Present in BOTH composite arms ⇒ **v2-vs-v1 is the clean
  single-variable comparison; v2-vs-control also carries this small cadence lift.**
- **NEXT: score with `collect_metrics(['phaselag_composite_v2'])`** and compare to the table below.
  Expect HWM bias to return toward the control's +0.32 while phase stays ~−3 min at source.
  If it does: phase is free, and v2 is the adoption candidate.

### ✅ SCORED: `phaselag_composite` (58646318) — PHASE WON, LEVEL LOST. **Do NOT adopt as-is.**
Full output not truncated (73 map / 433 his to tstop). Control = `faber-waves-premier`, `sfincs.inp`
sorted-diff EMPTY ⇒ the only difference is `sfincs_netbndbzsbzifile.nc`. CSV:
`reports/phaselag_composite.csv`. Control numbers reproduce `reports/solver-2x2.csv` exactly.

| | premier | composite |
|---|---|---|
| phase SH / Shrews / Shark (min) | 17.6 / 36.9 / 32.8 | **7.8 / 25.5** / 35.1 |
| Shrewsbury gauge (obs 2.935) | 2.837 (−0.10) | 3.186 (**+0.25**) |
| HWM bias / RMSE / within-0.5 | 0.318 / 0.480 / **74%** | **0.732 / 0.813 / 21%** |
| MOTF CSI / POD / FAR | 0.706 / 0.799 / 0.141 | 0.768 / 0.919 / 0.177 |
| SH peak pre-fail (obs 2.808) | 2.496 (−0.31) | 2.627 (**−0.18**) |

- **⚠️ THE CSI "WIN" IS AN ARTIFACT.** POD 0.80→0.92 while HWMs sit +0.73 m high — it floods MORE,
  which a wet-heavy extent metric rewards. **When CSI and HWM disagree, believe HWM; CSI can't see depth.**
- **🔑 ROOT CAUSE — the composite changed TWO things.** It re-phased the tide (intended) AND
  restored Sandy Hook as a **3rd boundary support point (2 stations → 3)**. SFINCS interpolates
  LINEARLY along the boundary, so a 3.39 m node inserted between Battery (3.44) and Atlantic City
  (1.92) lifts the whole mid-coast **+0.20..+0.23 m** at the HWM latitudes — which accounts for
  most of the HWM shift in 3 of 4 basins (oceanfront +0.21 bnd/+0.34 hwm; shrewsbury +0.22/+0.32;
  sh_bay +0.23/+0.26). **south_coast is the outlier: +0.20 bnd → +0.78 hwm = NONLINEAR** (overwash
  crossing a threshold; same reason POD jumped).
- **❌ CORRECTED 2026-07-22 — I FIRST CLAIMED THE LEVEL LIFT MIGHT BE RIGHT. IT ISN'T.** I compared
  the *boundary support-point interpolation* (offshore: 3.042 control / 3.264 composite) against the
  *nearshore* SSS observation and concluded "both low ⇒ over-propagation inland". **Invalid — the
  model gains ~0.6 m between boundary and shore.** Correct comparison is model-AT-sensor
  (`usgs_stormtide_sea_bright` in `sfincs_his.nc`) vs obs-at-sensor, **obs 3.465 m**:
  **premier 3.650 (+0.19), composite 4.006 (+0.54) — BOTH HIGH, composite ~3× worse.** There is no
  contradiction and no inland-propagation mystery: HWMs, SSS and the Shrewsbury crest all say the
  same thing, **the composite over-forces the shoreline.** (SSS 2259 shares the lat but is the WAVE
  sensor — its 4.973 m is contaminated; use 2258.) **Lesson: never compare a boundary-interpolated
  value to a nearshore gauge — sample the model AT the obs point.**
- Also over-sold Sandy Hook: **obs 2.81 m is a FLOOR, not a crest** (gauge died ~1 h before peak), so
  the composite's higher full peak (3.43 vs 3.15) is unfalsifiable. Only the pre-fail rising limb
  (2.50 → 2.63) is a real comparison, and it's small.
- **🔑 GEOMETRY FINDING: the support points sit AT THE GAUGE COORDS, not on the model edge** —
  north = The Battery (−74.0142, 40.7006, *inside NY Harbor*), mid = Sandy Hook (−74.0091, 40.4669),
  south = Atlantic City (−74.4181, 39.3550). **So the premier interpolates the open-coast boundary
  linearly across ~150 km from a HARBOR gauge.** Adding Sandy Hook breaks that baseline in the
  geographically right place ⇒ **the 3-node geometry is NOT the mistake; the LEVEL it carries is.**
- **⚠️ TRAP: "keep the composite recipe but use only Battery + AC" LOSES THE PHASE FIX.** Per the
  build script's own table, Battery *harmonic tide alone* = 30 min late, Battery *total* = 24 min
  late; the recipe at the Battery returns Battery tide + Battery NTR = Battery total = **the premier
  exactly**. The phase win comes specifically from substituting **Sandy Hook's TIDE**.
- **➡️ NEXT ARM (decisive on the confound): 2 NODES, with the COMPOSITE SERIES ON THE NORTHERN NODE**
  (SH harmonic tide + Battery NTR, placed at the Battery's location). Node peak 3.389 vs premier's
  3.417 ⇒ level ~unchanged, phase corrected ⇒ isolates phase from level. If HWMs return to control,
  phase is free and the level lift was the entire cost. Then 3 nodes with a corrected SH level as
  the likely production config.
- **`NTR_DONOR_SCALE` in `scripts/build_noaa_composite.py` is the knob**, and the script explicitly
  left it for "a future independent source (nearby STN sensor)". SSS 2258 IS that source — and it
  points **opposite** to the script's fitted 1.1122× ratio: the transplanted Battery NTR is too
  **BIG** at the coast (harbor-funnel amplification), not too small.
- Also: **SH lands at +7.8 min, NOT the ~0 that `source_phase_lag` measures at the source.** That
  residual ~8 min is shelf propagation = the honest ceiling of a forcing-only fix. Shrewsbury
  improved by the SAME ~10 min ⇒ the interior lag was largely IMPORTED, not conveyance-generated.
- Housekeeping done 2026-07-22: viz notebook `notebooks/sfincs-nj-sandy-viz.ipynb` rewired to
  premier-vs-composite (it still pointed at the 3 deleted void arms) and written up in full;
  **a stale DUPLICATE `noaa_sandy_composite` key removed from `data/data_catalog.yml`** (both
  pointed at the same uri, so nothing mis-resolved — but it was a live trap).

### (historical) submit notes for 58646318
- Submitted ~15:05 EDT 2026-07-21, 3 h limit, Faber `sfincs-desktop.sif`, 64 cores. Staged from
  `_template_sealed`; `premier.assert_sealed_domain` passed at submit. COMPLETED in 1:32:09.
- **✅ NO CONTROL RUN NEEDED — the control is `faber-waves-premier` (the premier).** Its `sfincs.inp`
  is now **identical key-for-key** to the composite's, so the ONLY difference is the boundary
  forcing file. ⚠️ To get there I had to hand-patch the staged dir: **`run_experiments.py` does NOT
  add `crsfile`/`storevel`** (only `scripts/setup_sealed_premier.py` does), so a harness-staged run
  silently loses the flux/leak cross-section diagnostics. Copy `data/flux_crosssections.crs` →
  `<exp>/sfincs.crs`, set `storevel=1`, add `crsfile=sfincs.crs`, **and submit the STAGED dir via
  `run.submit_slurm(dir, sif=base.container_sif)` — NOT `--slurm`, which re-runs
  `prepare_experiment` and rmtree's the patch away.** Worth fixing in the harness properly.
- **SCORING**: do NOT use `--validate-only` (it overwrites `experiments/metrics.csv` with just these
  rows). Per arm: `SfincsModel(dir, data_libs=['data/data_catalog.yml'], mode='r')` →
  `validate.read_output(mod)` → `validate.gauge_phase_lag(mod, dir)` + `validate.gauge_peak_error(mod)`.
- **BASELINE TO BEAT (premier, corrected window): Sandy Hook 17.6 / Shrewsbury 36.9 / Shark 32.8 min.**
  **Success = `phase_lag_sandy_hook_min` → ~0.** The INTERIOR is the genuinely open question — every
  interior number we have is either from the leaking domain or from the inflated metric.
- ⚠️ **Verify not truncated before believing anything**: 433 his steps / 73 map steps, reaching
  tstop 2012-10-31. Quota exhaustion truncates maps silently while `sacct` says COMPLETED.
- **NEXT after scoring**: the ~18 min surge-phase shift (see below) as a cheap follow-up arm.

## ⭐ Boundary-source phase, measured at the SOURCE (no run needed) — still valid
`validate.source_phase_lag`, + = source late vs the REAL Sandy Hook tide: Battery `noaa_sandy_nj`
**+21 min** (the problem); blend `noaa_sandy_nj_shblend` **0**; GTSM **−2**. Superseded as a *plan*
by the composite, but the +21 min Battery diagnosis is the whole reason this workstream exists.

## 🗑️ The 3-arm A/B (58632746/747/748) — VOID, dirs DELETED 2026-07-21
Ran clean (COMPLETED 0:0, ~1h30, full-length output) but staged from `_template` = the PRE-REBUILD
LEAKING grid, so every number is void. Symptoms: Shrewsbury obs pt on a **+1.455 m dry bank** (vs
premier's −4.327 m in-channel) ⇒ `phase_lag_shrewsbury_min` = **NaN**; **Shark DEAD** (tidal range
0.03–0.05 m vs premier 1.35 m); Shrewsbury range 0.71 vs 1.03. **The open coast is nearly
domain-independent (battery 16.9 vs premier 17.2 min) — which is exactly why the Sandy Hook control
looked healthy and MASKED the problem. NEVER validate an interior experiment with a coastal gauge.**
Root cause chain now CLOSED by code: `run_experiments.py` TEMPLATE → `_template_sealed`,
`BaseConfig.frozen_mesh` default → `frozen_mesh_sealed`, and `nj_sfincs/premier.py` asserts the
domain at staging + scoring. See [[reference_premier_domain_guard]]. Directional hint only, on the
wrong domain: re-phasing cut the coastal lag ~17 → ~8 min, blend and GTSM agreeing.
- **New metrics** in `validate.py`: `gauge_phase_lag(mod, model_dir)` (model-vs-obs cross-corr,
  **+ = model late**; SH+Shrewsbury from 10-min his, Shark from hourly map wet cells; wired into
  `evaluate`) and `source_phase_lag(geodataset, ref_lonlat)` (source-vs-SH-obs, no run). Cross-corr
  helper `_xcorr_lag_minutes` (normalized per-overlap Pearson + parabolic refine) validated to
  ~1 min on synthetics. `plots.plot_source_phase` + a `Δφ +NN min` tag in `plot_gauge_verification`.
- **Harness:** `Experiment.waterlevel_geodataset` override (config.py) applied in
  `run_experiments.prepare_experiment` via `water_level.create(..., merge=False)` on the copied
  template. New experiments `phaselag_{battery,shblend,gtsm,composite}` clone the `snapwave_tuned`
  wave knobs. **⚠️ Faber is the CONTAINER (`sfincs-desktop.sif`, the default `container_sif`), NOT
  a config knob** — Galibier is a different SIF; the sealed campaign selected engines by SIF +
  file-staging `scripts/setup_*.py`, not by the EXPERIMENTS dict.
- **Sandy Hook blend** `scripts/build_sandy_hook_blend.py` → `data/gtsm/noaa_sandy_nj_shblend.nc`:
  real SH tide for t≤`2012-10-29 23:00`, then Battery+offset (`+0.185 m`) **tapered to 0 over 2 h**
  so the crest (Battery peak Oct 30 01:00) keeps its true 3.42 m. Reuses the download script's
  `build_dataset`/`write_atomic`. All-finite asserted.
- **GTSM** (`scripts/download_gtsm_sandy.py`) — CDS terms accepted; **DOWNLOADED 2026-07-20**
  (`gtsm_sandy.nc` + `gtsm_sandy_tide.nc`, 4 nodes; 403 MB zip → clipped). ⚠️ datum
  `MSL_TO_NAVD88_M=-0.12` still UNVERIFIED (affects GTSM amplitude only, not phase).
  **Hard-won request schema (verified live via CDS form.json/constraints.json):** dataset
  `sis-water-level-change-timeseries-cmip6` (needs the `-cmip6` suffix); `experiment=reanalysis`
  requires `version` (`v2`/`v3`) and exposes ONLY `total_water_level` + `storm_surge_residual`
  — **NO `tidal_elevation`** (projections-only), so GTSM **tide = total − surge** (derived).
  Datum **MSL** (1986-2005 AR5) → total shifted to NAVD88 (`MSL_TO_NAVD88_M=-0.12`, VERIFY).
  Returns a **ZIP** of per-variable ncs (`_open_gtsm` handles it). **FES**
  (`scripts/build_fes_tide_ref.py`, pyTMD) needs AVISO+ acct (tick "FES … Oceanic Tides Heights");
  **largely redundant now that GTSM tide-only is free** — keep for a 2nd independent tide model.
  pyTMD added to environment.yml. Catalog:
  `noaa_sandy_nj_shblend`, `gtsm_sandy`, `gtsm_sandy_tide`, `fes_sandy_tide`, `noaa_sandy_composite`.
- **Notebook:** old viz → `archive/notebooks/sfincs-nj-sandy-viz-estuary-leakfix.ipynb`; fresh
  canonical `notebooks/sfincs-nj-sandy-viz.ipynb` (source-phase → gauge-phase → lag table →
  regression). Plan file: `~/.claude/plans/functional-bouncing-bumblebee.md`.
- **NEXT / NOT YET DONE:** (1) read the 3 SLURM runs' modeled phase+peak per RESUME above; (2)
  **FES** still needs the AVISO+ acct (user registered FES + X-TRACK; login pending) — but redundant
  now GTSM tide-only is on-phase, so optional; (3) the **composite** (`noaa_sandy_composite`, best
  tide phase + NOAA surge residual) — gated on whether re-phasing helps the MODELED interior; (4)
  **Phase 2** seaward domain extension (X2) so GTSM is applied at depth. Everything UNCOMMITTED
  (user commits). Plan file: `~/.claude/plans/functional-bouncing-bumblebee.md`.

## ⭐ 2026-07-21 — GTSM SCRAPPED (user's call); COMPOSITE BUILT. This is the forcing route now.
`noaa_sandy_composite` **BUILT + VALIDATED + CATALOGUED** via new `scripts/build_noaa_composite.py`.
**total = NOAA harmonic tide (per station) + non-tidal residual**, 4 stations, 6-min, NAVD88.
**The unlock: harmonic predictions don't need the gauge to have survived**, so Sandy Hook is BACK as
a support point with its OWN (correct-phase) tide, borrowing the Battery's NTR (**corr 0.996, zero
lag**) across the mid-storm gap. Validated vs REAL SH 6-min obs (n=717):

| construction | RMSE | pre-storm phase err |
|---|---|---|
| Battery total, as-is (old `noaa_sandy_nj`) | 0.147–0.162 m | **24 min** |
| **composite (SH tide + Battery NTR)** | **0.103 m** | **0 min** |
| SH harmonic tide alone | 0.913 m | 6 min |
| Battery harmonic tide alone | 0.922 m | 30 min |

⇒ **the phase error is ENTIRELY in the tide**; fixing it needs no surge change at all (one variable
moved). ❌ **DO NOT scale the borrowed NTR.** Least squares gives SH_NTR = 1.1122×Battery, which
extrapolates ~33% past its fitting range through the unobserved crest and implies SH surge +3.10 m >
Battery's own +2.79 m — user rejected it, correctly, and the 0.057 m "fit" was circular (fit and
scored on the same 48 h). Unscaled costs a **known, quotable −0.08 m** conservative surge bias.
`NTR_DONOR_SCALE = 1.0` + a `MIN_DONOR_CORR = 0.95` hard guard on any borrow.
**Files:** `scripts/build_noaa_composite.py` (new), `data/gtsm/noaa_sandy_composite.nc`,
catalog entry, `phaselag_composite` preset re-described (it already existed, pointed at the right
key). GTSM marked ⛔ RETIRED in BOTH the catalog and `EXPERIMENTS`; **data files NOT deleted**.
**NOT YET RUN** — needs a SLURM submit on the sealed template. **FES = independent cross-check only**
(user has AVISO access now); NOAA constituents beat a global model at these 4 coastal stations.

## ⚠️ THE BORROWED SURGE IS ~18 min LATE AT SANDY HOOK (measured 2026-07-21, 6-min)
User's inference, and it is correct. Cross-correlation of the 6-min NTRs (n=717, corr 0.9965):
**Battery NTR lags Sandy Hook NTR by ~+18 min**; the TIDE lags by **+24 min** (corr 0.9995).
Surge and tide both propagate up the harbour, so borrowing the Battery's NTR imports an ~18 min
delay at SH — the composite fixes the TIDE phase (24 → 0 min) but does NOT fix the surge phase.
**Mitigating it is a one-line change** (`.shift(-3)` on the 6-min donor NTR, i.e. advance 18 min)
and it is MEASURED, not extrapolated. **BUT** the cross-correlation peak is BROAD — corr is 0.99623
at zero lag vs 0.99654 at 18 min — because a surge is smooth and slowly varying, so the lag is
weakly constrained and the *consequence* of getting it wrong is small. Deliberately NOT applied yet:
it would move the crest timing, and the point of the first composite run is to change ONE variable.

## 🐛 `_prestorm_window` INCLUDES SPIN-UP — inflates EVERY phase number (~+13 min) — ✅ FIXED
`validate._prestorm_window` (validate.py:93) returns the **first 24 h from tstart**, which opens
during spin-up and closes **exactly on a rising tide** (every run's window-max landed on the window
edge) ⇒ badly-conditioned cross-correlation. Sliding the window (Sandy Hook, min):

| window | battery | shblend | gtsm | PREMIER |
|---|---|---|---|---|
| +0h/24h *(as shipped)* | 30.7 | 21.7 | 27.9 | **30.0** |
| +6h/24h | 16.9 | 8.3 | 21.1 | **17.2** |
| +12h/24h | 17.4 | 8.1 | 6.4 | **17.6** |

**Skipping ≥6 h recovers the recorded +18 min baseline** (premier 17.2/17.6) — so the 07-20 ad-hoc
diagnosis was RIGHT and `gauge_phase_lag` never reproduced it; it reads ~13 min high. **Any phase
number this project produced through `gauge_phase_lag` is inflated — re-measure before citing.**
**✅ FIXED 2026-07-21**: `validate.SPINUP_SKIP_H = 12.0`, `_prestorm_window(times, hours, skip_hours)`
now opens 12 h after tstart (with a fallback to tstart on runs too short to afford the skip, so smoke
tests don't get an empty window). **The corrected metric REPRODUCES the 07-20 hand-diagnosis on the
premier: Sandy Hook 30.0 → 17.6 (recorded +18), Shrewsbury 46.0 → 36.9 (recorded +38), Shark
42.0 → 32.8 (recorded +26; Shark is sampled from the HOURLY map so it quantises ±30 min).**
Also feeds `tidal_range_metric` (validate.py:377) — its numbers shift too, for the same good reason.
**Provisional A/B signal (on the WRONG template, see above — directional only): boundary re-phasing
cuts the coastal lag ~in half, 17 → ~8 min, with blend and GTSM agreeing independently.** GTSM's
+6h/24h = 21.1 is an outlier vs its 7.9/6.4 — its low amplitude makes the correlation noisy.

## ✅ GTSM DATUM VERIFIED + a bigger problem found (2026-07-21)
The long-open `MSL_TO_NAVD88_M` TO-DO is **CLOSED**. NOAA CO-OPS published datums for 8531680
(`mdapi/prod/webapi/stations/8531680/datums.json`, epoch 1983-2001, station-datum ft): MSL 5.090,
NAVD88 5.330 ⇒ **MSL sits 0.0732 m BELOW NAVD88**, so `z_navd88 = z_msl - 0.073`. Constant changed
**-0.12 → -0.073** in `scripts/download_gtsm_sandy.py`; its old comment ("NAVD88 sits a little below
local MSL") was **backwards**, though the sign happened to be right. Residual ~1-2 cm because GTSM's
datum is the *later* 1986-2005 AR5 MSL epoch — ignored, far inside the error below.
⚠️ **`data/gtsm/gtsm_sandy.nc` on disk still has -0.12 baked in** — regenerate from the local
`gtsm_reanalysis_2012_10_raw.nc` (no re-download) when no run is reading it. A 0.047 m shift, so it
does NOT invalidate `phaselag_gtsm`.
**⭐ THE REAL GTSM PROBLEM IS THE TIDE, NOT JUST THE SURGE.** GTSM tide-only daily range at the SH
node = 1.23 / 1.15 / 1.06 / 0.95 m (mean **1.09 m**) for Oct 28-31 2012, vs published **GT = 1.594 m**
— and that week was a **SPRING tide** (full moon Oct 29) so truth should *exceed* 1.594 m ⇒ GTSM is
**≥31% under-amplitude in the TIDE ALONE**, on top of the known ~1 m surge deficit. Also seen
directly: over 10-28 obs range 1.82 m vs gtsm_total 1.17 m. **Consequence for reading the A/B: a low
`phaselag_gtsm` interior peak is an AMPLITUDE artifact, not a phase verdict — score GTSM on
`phase_lag_*_min` only.** This is the argument FOR the `noaa_sandy_composite` arm (GTSM/blend phase +
NOAA amplitude), item (3) in NEXT.
❌ Dead end, don't retry: estimating the datum empirically by differencing mean(obs NAVD88) −
mean(gtsm MSL). GTSM's own amplitude/surge bias (~0.24 m over 10-28) swamps a 0.07 m datum, and the
obs record ends 10-29 23:00 at gauge failure. The published datums are the authoritative route.

### The "GTSM just needs to be applied farther offshore" hypothesis — TESTED, REJECTED
User's challenge (good one): maybe GTSM is right *at its node* and we're wrongly comparing an
offshore point to a shoreline gauge; let SFINCS shoal it. **Ruled out by three independent lines:**
1. **The nodes are ~1 km from the gauges, not offshore.** GTSM reanalysis output points are placed
   at coastal locations by design. Battery 0.9 km, Sandy Hook 1.1, Atlantic City 1.1, Cape May 1.2.
   Green's law needs a **7.6× depth ratio** to explain a 33% deficit — impossible over 1 km here.
2. **GTSM's own field in the NY Bight is FLAT**: all 21 nodes give 0.9–1.1 m range from 35 km
   offshore to the beach. There is no offshore point whose value shoals *up* to the right coastal
   one — moving the boundary seaward starts us LOWER (0.96 vs 1.09 m).
3. **The ratio is constant across physically unrelated regimes** (vs NOAA harmonic predictions,
   `product=predictions&datum=MSL`, mean daily range): Battery 0.59, Sandy Hook 0.68, **Atlantic City
   (OPEN COAST) 0.67**, Cape May 0.72, **Bridgeport CT 0.67, New Haven CT 0.62**. Long I. Sound
   amplifies by quarter-wave *resonance*, Atlantic City by shelf *shoaling* — a sampling/shoaling
   explanation predicts wildly different errors; a near-constant ×0.66 does not. Signature of a
   deficit **inherited at the shelf/regional scale**, which is exactly why moving the boundary can't
   recover it. Robust to: calm 25-day window (Oct 1–25), raw total w/o surge subtraction, and
   hourly-vs-10-min sampling (which biases *against* the finding). **corr = 0.93–0.95 ⇒ right shape,
   right phase, scaled down ~⅓.**

### 📚 LITERATURE (2026-07-21) — what the field actually uses, and it is NOT GTSM
- **GTSM tide error is documented, but only coarsely.** CDS serves **v3.0** (our files are `_v3`):
  global tide RMSE **17.8 cm**, cut to **11.3 cm in v4.1** (−37%). Deltares wiki: "**FES2014
  outperforms the GTSM in most areas**", "larger deviations … in coastal areas", biases grow in
  high-tidal-range regions. Muis et al. 2020 (the v3.0 paper) publishes **no tide-specific
  validation** at all, and flags "relatively large" bias in the **northeastern United States**. So a
  ~25 cm amplitude deficit in the Mid-Atlantic Bight is *large but in-family* — and nothing published
  at station granularity would have warned us. ⇒ **Trust the measurement, not the absence of a paper.**
- **⭐ REGIONAL PRECEDENT IS UNANIMOUS — gauge-based, tide and surge SPLIT:**
  - **Wahl's group, Gloucester City NJ, SFINCS** (Maduwantha, Wahl, Santamaria-Aguilar, Jane,
    Dangendorf, Kim, Villarini; egusphere-2025-1557): boundary = time series **at the NOAA
    Philadelphia gauge** (8545240 + 8545530). **UTide harmonic analysis** → tide; **NTR = detrended
    obs − predicted tide**; + sampled MSL. GTSM cited only as *other people's* prior work.
  - **Orton/Stevens, Hoboken–NYC, Ida** (Kasaei, Orton, Ralston, Warner; HESS 29:2043, 2025):
    COAWST/ROMS (not SFINCS) — **subtidal water levels from NOAA Sandy Hook 8531680 + Kings Point
    8516945**, tidal constituents from the **ADCIRC database**. No GTSM.
  - GTSM-forced SFINCS is the **Eilander et al. NHESS 2023 global framework** — designed for
    *data-poor* sites. NJ is the opposite of data-poor. Using GTSM here was solving a problem we
    don't have.
- **⇒ THE COMPOSITE SHOULD BE HARMONIC-TIDE + NTR, not "GTSM phase + NOAA amplitude".**
  **The unlock: NOAA harmonic predictions for 8531680 exist for 2012 even though the gauge FAILED
  mid-storm** — predictions don't depend on the record surviving. So we can have the *real Sandy Hook
  tide, correct phase AND correct amplitude*, and add an NTR borrowed from a surviving gauge. That
  dissolves the +21 min Battery phase error and the amplitude problem in one move, and it is exactly
  what Wahl does. Fetch: `api.tidesandcurrents.noaa.gov/api/prod/datagetter?product=predictions
  &datum=MSL&station=8531680&time_zone=GMT&units=metric&interval=h` (already pulled to scratch).
- **FES is NO LONGER redundant** — the earlier note ("redundant now GTSM tide-only is free") is
  **WRONG**: FES2014 is documented to beat GTSM on tides, and we've now measured GTSM's tide 34% low.
  Still gated on the AVISO+ account, but NOAA harmonic predictions likely make it unnecessary anyway.

## Original diagnosis (unchanged)
On the `faber-waves-premier` premier, the modeled pre-storm tide peaks/troughs land **late**
vs observations. Measured by cross-correlation of detrended (surge-removed) pre-storm series
(positive = model peaks LATER than obs):

| gauge | lag | sampled from |
|---|---|---|
| Sandy Hook (coast/bay mouth) | **+18 min** | his 10-min (zb −4.88, always wet) |
| Shark R. (interior) | **+26 min** | map HOURLY (his obs-pt on a +1.79 m dry bank) |
| Shrewsbury R. (interior) | **+38 min** | his 10-min, obs-pt nudged IN-CHANNEL (zb −4.33) ✅ |

**It is REAL physics, NOT a sampling artifact.** I first suspected the hourly-map plotting
(interior gauges are drawn from hourly `sfincs_map.nc`; surge gauges from 10-min `sfincs_his.nc`
— `dtmapout=3600`, `dthisout=600`). But measuring Shrewsbury BOTH ways gave his-10min **+38** vs
map-hourly **+26** — the rigorous fine-cadence number is if anything *larger*. Hourly sampling
adds ~±10 min of eyeball noise, it does not create the offset. **Also: the magnitude is ~20–40
min, NOT the "~1 h" it looks like by eye** on the hourly interior curves.

## The gradient decomposes into two independent causes

**+18 min COASTAL baseline (every gauge inherits it) ← the FORCING is Battery-anchored.**
`waterlevel_geodataset = "noaa_sandy_nj"` (config.py) contains **only 3 gauges: Battery 8518750,
Atlantic City 8534720, Cape May 8536110 — SANDY HOOK (8531680) IS EXCLUDED** because its gauge
failed mid-storm (data_catalog.yml notes the Battery, ~5 km N, stayed up). So the whole northern
domain — including the water offshore of the Navesink — is interpolated from the **Battery**,
which sits up inside NY Harbor and carries the harbor's phase lag. Measured observed inter-gauge
phase (from the hourly NOAA records, ±10 min precision): AC→SandyHook **+14**, SandyHook→Battery
**+7**, AC→Battery **+38**. Imposing harbor-phase Battery water on an open-coast boundary imports
a late tide. **This confirms the advisor's Battery hypothesis — and it's stronger than "mainly":
Sandy Hook contributes zero to the forcing.**

**+20 min UP-ESTUARY excess (coast +18 → Shrewsbury +38) ← excess model travel time.** The
advisor's "travel time from the −10 m boundary" instinct is directionally right but needs one
correction: **pure travel time CANCELS** — the obs at Shrewsbury already contains the real
ocean→estuary delay, and so does the model, so it subtracts out in a model-vs-obs-at-same-gauge
comparison. What survives is *excess* travel time: the model propagates the tide up-estuary too
slowly. **This is the TEMPORAL TWIN of the known amplitude over-damping** (tidal range too small,
[[project_bridge_dam]] fill-timescale + Manning audits): an over-resistive / too-shallow subgrid
channel cross-section both *shrinks* and *delays* the tide — same mechanism, two faces. The
"−10 m" boundary DEPTH itself is not the cause.

## Where this leaves it

- **Coastal baseline = the improvable lever (forcing phase).** Idea to scope: add Sandy Hook back
  as the northern anchor **for the tidal window only** — its record covers the ENTIRE pre-storm
  tide and only dies before the surge crest, so it's valid for exactly the phase we care about;
  keep the Battery for the surge peak. Needs care: hydromt `water_level.create` NaN-handling for a
  gauge that goes NaN mid-record. Could shave several min off the +18.
- **Up-estuary excess = likely the same STRUCTURAL conveyance ceiling** already hit on amplitude
  (friction is at the open-water floor, L4 resolution didn't help — see [[project_bridge_dam]]).
  Phase lag and amplitude damping are one problem; don't chase them as two.
- Status: **DIAGNOSED, nothing changed.** User cleared context to start PLANNING (2026-07-20).

## Reusable facts surfaced here (verify before reuse)
- Output cadence: **map = hourly, his = 10-min** (`dtmapout=3600`, `dthisout=600` in model.py
  add_forcing). Any fine-timing analysis must prefer his.
- His obs-point beds in the premier: `sandy_hook` −4.88 (wet), `usgs_tidal_sea_bright` **−4.33 (the
  21 m channel nudge WORKED — usable 10-min tide)**, `usgs_tidal_shark_river` **+1.79 (still a dry
  bank — no usable his tide; must use map)**, `usgs_stormtide_sea_bright` +2.03 (shorefront).
- Gauge-cell sampling rule + the "no open-coast drift on the rebuild" finding are in
  [[reference_hwm_metric_blindspot]]. `plots.plot_gauge_verification` now shows **4 gauges**
  (Sandy Hook + Sea Bright SSS added; surge via his obs-point, tide via wet-channel map median).
