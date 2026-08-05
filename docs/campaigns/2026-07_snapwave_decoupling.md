<!-- Campaign record. Moved out of the Claude memory store 2026-08-05; the
     memory file was `project_snapwave_decoupling`. -->

> **Historical record — read top-down, newest first.** Blocks are appended in
> reverse chronological order and later blocks SUPERSEDE earlier ones, including
> where an earlier block calls itself current. Several conclusions in here were
> retracted; the retraction is always above the claim it retracts. For what is
> believed true *now*, see the memory store and `CLAUDE.md`, not this file.
>
> **Standing summary at the time of the move:** SnapWave boundary decoupled from the SFINCS mask out to the 30 m contour — `wave-deep30`. ⭐ The real case is that the premier imposes Hs 8.624 m at the ~10 m contour, ABOVE the depth-limited breaking cap (~7.8 m) = physically inadmissible; deep imposes the SAME Hs at 30 m where it is valid. ✅ SCORED 2026-07-27: the UNION `wave-deep30+tide-shift` is the best level arm (bias 0.273, RMSE 0.449) and the two knobs are ~ADDITIVE (RMSE 100%, bias 91%) — the wave and tide-phase defects are independent. ⚠️ But the union is the WORST extent arm (CSI 0.684) and loses a wet HWM: level-vs-extent is a real trade the user must call. ❌ The gain is NOT 'less nearshore wave energy' — deep has MORE hm0 at 6-25 m and an UNCHANGED surf zone.


# SnapWave ⟂ SFINCS boundary decoupling — `wave-deep30` (built 2026-07-22)

## 🔴 RESUME HERE (updated 2026-07-25)

### ✅✅ SCORED — `wave-deep30` IS THE BEST ARM ON EVERY HEADLINE HWM METRIC
`reports/wave-deep30.csv`. Both runs COMPLETED (3:03:55 / 3:05:29 — **both would have been
killed by the batch script's 3 h limit**; the `--time=06:00:00` override was load-bearing).

| | premier | phase_v2 | **deep** | deep+v2 |
|---|---|---|---|---|
| **HWM bias** | 0.318 | 0.500 | **0.285** | 0.429 |
| **HWM RMSE** | 0.480 | 0.606 | **0.463** | 0.547 |
| **within 0.5 m** | 73.7% | 63.2% | **78.9%** | 68.4% |
| oceanfront / shrews / south_coast | 0.31 / 0.43 / 0.15 | 0.47 / 0.54 / 0.59 | **0.24 / 0.39 / 0.11** | 0.39 / 0.49 / 0.40 |
| sandy_hook_bay | **0.090** | 0.165 | 0.158 | 0.223 |
| MOTF CSI | 0.706 | 0.746 | 0.687 | 0.747 |
| SH Bay hm0 mean / max | 0.88 / 7.44 | 0.91 / 11.21 | 1.08 / **4.06** | 1.13 / 6.04 |

- **✅ ATTRIBUTION IS CLEAN — no boundary-reconstruction caveat applies here.** The water-level
  forcing is **byte-identical** to the premier (`62a35f63a08bb1f7` both sides). There is no
  boundary perturbation to amplify. (Contrast the phase arms, where a 2–6 cm boundary change was
  amplified ×3–9 — see [[project_tidal_phase_lag]].)

### 🧰 TWO ANALYSIS TRAPS THAT BOTH GAVE ME THE WRONG ANSWER FIRST (2026-07-26)
Hit both while auditing this arm. Either one silently inverts the conclusion.
1. **`zb` is NaN for SFINCS-INACTIVE faces in `sfincs_map.nc`.** The decoupled SnapWave domain is
   mostly SFINCS-inactive (129,188 of the 129,195 added faces), so `zb[extra]` is all-NaN and
   every `zb > x` test silently returns **0 matches** — which reads as "no dry cells, all clean"
   when it is really "no data". **Use `snapwavedepth` (a map variable) for anything about the
   decoupled domain.** That is what actually confirmed the added faces are 8.4–30.0 m deep.
2. **Comparing hm0 across arms MUST be restricted to faces SnapWave-active in BOTH runs.**
   The naive all-cells comparison counts premier-inactive faces as hm0 = 0 and manufactures a
   fake +2 m "increase". (Here the restriction did NOT change the sign — the increase is real —
   but that was luck, not method.)

### ❌❌ 2026-07-26 — "THE GAIN IS REDUCED WAVE SETUP / LESS NEARSHORE ENERGY" IS **WRONG**
Measured in the map files, restricted to the **395,567 faces SnapWave-active in BOTH runs** (the
naive all-cells comparison is invalid — it counts premier-inactive cells as hm0 = 0). Median
**peak** hm0 by bed-depth band:

| zb band | premier | deep | Δ |
|---|---|---|---|
| −25…−15 m | 0.94 | 2.99 | **+2.05** |
| −15…−11 m | 1.25 | 2.24 | +0.99 |
| −11…−9 m | 1.26 | 3.58 | **+2.32** |
| −9…−6 m | 1.24 | 2.20 | +0.96 |
| −6…−3 m | 1.18 | 1.30 | +0.12 |
| −3…−1 m | 0.61 | 0.61 | +0.01 |

**`wave-deep30` puts MORE energy in the 6–25 m band and leaves the SURF ZONE UNCHANGED.**
So the HWM gain is NOT "less wave energy nearshore." **Working hypothesis (NOT established by
this run): breaking now happens farther offshore across the shelf, so the DISSIPATION GRADIENT —
which is what drives setup — is spread out instead of concentrated at the shoreline.** Consistent
with the surf zone being flat while HWMs fall ~0.03 m. **Test it by comparing the `fwx`/`fwy`
wave-force fields, not hm0** — setup is driven by the gradient of radiation stress, not local Hs.

### ⭐⭐ THE REAL CASE FOR THIS ARM IS A PHYSICALLY INADMISSIBLE BOUNDARY CONDITION
Verified from the runs' own `snapwave.bnd` / `snapwave.bhs`: **both arms impose the SAME peak
Hs = 8.624 m** — only the location differs (premier x≈584–589 km, deep x≈605–632 km, i.e. 20–45 km
further offshore). ⇒ a genuine SINGLE-VARIABLE change.
- **Premier applies 8.624 m at the ~10 m contour. Depth-limited breaking (γ=0.78) caps Hs at
  ~7.8 m in 10 m of water ⇒ the premier's BC is ABOVE the breaking limit and must dissipate
  instantly at the boundary.** `wave-deep30` applies the same 8.624 m at ~30 m (γ = 0.29),
  which is admissible.
- Confirmed in the field: **faces past breaking (γ>0.78) 16,532 → 13,651 (−17%)**.
- **🔑 THIS, not the −0.034 m, is the argument for the arm** — it fixes a defect that is wrong
  whether or not it scores, and it survives review in a way an HWM delta would not.
- ⚠️ **Still 8,569 faces with γ>1.0 (waves TALLER than the water column) in BOTH runs, unchanged.**
  Decoupling does not touch them; likely the same shallow-cell transient family as the hm0 spike.
- ⚠️ Max hm0 anywhere rises 10.96 → 14.20 m (at 29.3 m depth, γ 0.49 — admissible, but large).

- **⚠️ 2026-07-26 — the "SH Bay hm0 max 7.44 → 4.06 (−45%)" headline is NOT evidence.** See the
  block below: `tide-shift` reproduces the same drop from a pure tide-timing change. What
  survives is the **MEAN rising 0.88 → 1.08**.
- **⚠️⚠️ 2026-07-26 — `shb_hm0_max` ALONE IS NOT A VALID DISCRIMINATOR; QUOTE THE MEAN.**
  `tide-shift` (premier wave knobs, ONLY the boundary tide advanced 24 min) scores
  **hm0 max 4.01** — as low as `wave-deep30`'s 4.06 — while its **mean is FLAT (0.884 →
  0.890)**. A pure tide-timing change cannot transform a wave field, so the max is a
  **WETTING TRANSIENT**: SnapWave running in a marginally-wet cell, and re-phasing the tide
  moves *when* those cells wet. ⇒ the max is timing-fragile. **`wave-deep30`'s result still
  stands, but it stands on the MEAN RISING (0.88 → 1.08), which is the part `tide-shift`
  does NOT reproduce.** Verified same-code-path: premier re-scored 2026-07-26 →
  `reports/faber-waves-premier_rescored.csv`, reproduces 17.6/36.9/32.8, bias 0.318, RMSE 0.480, CSI 0.706,
  hm0 max 7.44 exactly.
- **⚠️ BE REALISTIC ABOUT SIZE: −0.034 m of bias against a +0.32 m problem (~10%), and
  within-0.5 improved by exactly ONE HWM of 19.** Real, directionally right, does NOT solve the
  wet bias. Don't oversell it.
- **📊 Per-HWM breakdown (2026-07-26, full-raster path, premier vs deep, n=19):** 14/19 improve
  and the sign is CONSISTENT (17/19 ≤ 0) ⇒ a broad uniform lowering, not one outlier — that part
  is genuinely good. But only **8 marks move >0.05 m**, and the mean is −0.033 m.
  **⚠️ The within-0.5 gain 73.7% → 78.9% is ONE oceanfront mark crossing the threshold by
  0.044 m (residual 0.544 → 0.474). Do NOT quote it as a 5-point gain.**
  **The single largest per-mark move in the whole comparison is a `sandy_hook_bay` mark getting
  WORSE by +0.150 m** — the only mark that moves more than 0.11 in either direction.
- ⚠️ MOTF CSI DROPS 0.706 → 0.687 (POD 0.799 → 0.775) — expected when levels fall; per project
  rule **believe HWM over CSI**. FAR is flat (0.141 → 0.142).
- ⚠️ **`sandy_hook_bay` gets WORSE (0.090 → 0.158)** — and that basin is independently ~15%
  under-forced in tidal range ([[reference_bay_tidal_amplification]]). Lowering wave setup there
  may be compounding an existing deficit. Watch it.
- **Interaction is real but modest** (I first called it "near-additive" from 4 gauges — too
  strong): deep helps 2× more with the phase fix on (−0.071 vs −0.034), and the phase penalty
  shrinks +0.182 → +0.144. Fixing waves absorbs ~21% of the phase penalty, nowhere near all.
### ✅✅ `wave-deep30+tide-shift` SCORED 2026-07-27 — THE TWO KNOBS STACK, ~ADDITIVELY
SLURM 59148558 COMPLETED 3:12:35. `reports/wave-deep30+tide-shift.csv`. **The pre-registered
expectation "bias ~0.27 if they compose" was MET EXACTLY (0.273).**

| | premier | shift | deep | **union** |
|---|---|---|---|---|
| HWM bias | 0.318 | 0.302 | 0.285 | **0.273** |
| HWM RMSE | 0.480 | 0.466 | 0.463 | **0.449** |
| within 0.5 | 73.7% | 73.7% | 78.9% | 78.9% |
| wet/dry | 30/1 | 30/1 | 29/2 | 29/2 |
| SH / Shrews / Shark lag (min) | 17.6/36.9/32.8 | −0.1/16.8/16.9 | 17.8/37.0/32.6 | 0.1/17.1/16.7 |
| sandy_hook_bay | **0.090** | 0.064 | 0.158 | 0.142 |
| MOTF CSI | **0.706** | 0.701 | 0.687 | 0.684 |

**Additivity vs premier: RMSE 100% (deep −0.0172 + shift −0.0138 = −0.0310; union −0.0309),
bias 91%, CSI 90%.** ⇒ the wave-boundary defect and the tide-phase defect are INDEPENDENT error
sources; neither was ever a proxy for the other. **⭐ The phase fix survives the deep wave
boundary INTACT (0.1/17.1/16.7 vs shift's own −0.1/16.8/16.9)** — moving the SnapWave boundary to
30 m does not perturb tidal timing at all.

⚠️ **THE ADDITIVITY RUNS BOTH WAYS — the union is the best LEVEL model and the WORST EXTENT model
of the four.** It inherits essentially all of `wave-deep30`'s costs: **CSI 0.706 → 0.684**,
**`hwm_n_dry` 1 → 2** (a mark the premier had wet is now dry), and `sandy_hook_bay` 0.090 → 0.142
(shift's −0.026 only partly offsets deep's +0.068; the wave knob dominates that basin).
**Net trade: −0.031 m RMSE bought with −0.022 CSI + one dry mark.**
**✅ CALLED 2026-07-27 — HWM RESIDUAL IS THE HEADLINE; the CSI cost does NOT veto it, so the
union is the adopted level model and its extent cost is a stated cost. See
[[feedback_scoring_criterion]] (and its ⚠️: a NEGATIVE bias is under-forcing, not a win).**
⚠️ **`wave-deep30` is likely SUPERSEDED by `wave-cora`** (running now on v2): both fix the same
inadmissible-BC defect, but deep30 keeps ERA5's 8.62 m and MOVES the boundary to where it is
valid, while cora keeps the boundary and imposes the shelf-transformed height that belongs
there — the better route if it scores. **`tide-shift` is untouched by this and carries forward
independently** (it is orthogonal to the wave knob and was free on level). ⚠️ within-0.5 is unchanged from `wave-deep30` and is still literally
ONE mark of 19 (15 vs 14) — do not quote 78.9% as a 5-point gain.

**✅ Attribution verified byte-level at scoring time:** `sfincs_netbndbzsbzifile.nc` ≡
`tide-shift` and ≠ `wave-deep30`; `snapwave.bnd` + `sfincs.nc` ≡ `wave-deep30` and ≠
`tide-shift`. Each knob comes from exactly one parent. (Staging pre-flight was also all
green: `sfincs.inp` **0-key diff against BOTH parents**, domain **sealed** `45f4f74ca9a2347d`,
snapwave mask **524,762 active = wave-deep30 exactly**. **✅ `restore_diagnostics()` worked
end-to-end — NO manual patch needed**; first production confirmation, see [[reference_build_traps]].)
- `deep+composite_v2` is retrospective evidence only (v2 retired 2026-07-26); its config entry is
  marked ⛔ SUPERSEDED and points here.
- **No X1 runaway.** Convergence is statistically IDENTICAL to the premier: mean 9.6 iters/call,
  max 26, **0 calls hit `niter=100`**, same single error-plateau occurrence. The plateau at
  `error = 0.00256` with `%ok = 100.00` is normal SnapWave behaviour, present in the premier too.
- **⏱️ COST: 6.18 s/iteration vs the premier's 3.95 (1.56×)** — superlinear vs the +32.7% cells.
  Project full-run cost as **premier_total_iterations (1389) × s_per_iter**, NOT from mean call
  time (call time drifts with wave energy; per-iteration cost is the mesh property). ⇒ ~2.56 h,
  which does NOT fit the batch script's `#SBATCH -t 03:00:00` with any margin. **`submit_slurm`
  now takes `extra_args=[...]` so a single job can override the wall clock without editing the
  shared script** (sbatch CLI flags beat `#SBATCH`).
- **🌊 WAVE SPIN-UP IS ~6 HOURS on the enlarged domain** (`tspinup` is only 3600 s). Interior
  nearshore Hs vs premier: ratio **1.7–3.0 for the first 6 h, then 1.03→0.98**. Harmless for the
  full run (starts 10-28, peaks 10-30) but it means **any short-window wave diagnostic under ~8 h
  is measuring spin-up, not physics.**
- Converged nearshore Hs is **essentially unchanged, trending marginally LOWER (0.94–0.98)**, i.e.
  the intended direction but tiny at this energy (bnd Hs 2.8 m here vs 8.62 m at the run peak).
  **Whether the deep boundary actually reduces peak setup is UNANSWERED by the smoke** — only the
  full run reaches Sandy's peak.

### ⚠️ THREE FALSE ALARMS I RAISED ON THIS SMOKE — the lesson is always baseline against the premier
1. **"zs blew up to 70.6 m / 52% NaN"** — the premier's own map is **71.1 m / 39% NaN**. `zs`
   tracks the bed in dry cells (`zb` max 93.6 m) and NaN is the dry-cell fill. My absolute
   thresholds (15 m, zero-NaN) were invented, not derived.
2. **"nearshore Hs jumped 1.7–2.3×"** — contaminated by **premier cells that are INACTIVE in its
   own wave domain reading ~0**, which dragged its mean down. Restrict to `snapwave_mask == 1`
   AND `z > -9` before comparing.
3. **"Hs still 1.675× on interior cells"** — that was the **6 h spin-up transient** dominating a
   13-step window mean. Resolve time-varying claims per timestep before believing an aggregate.
**Rule: for any smoke metric, compute the SAME statistic on the premier over the SAME time window
and the SAME cell set before calling anything a failure.** Cf. the Shark sill, where a box `max(z)`
returned the dune on the bank; see [[project_bridge_dam]].
**✅ STAGED + ALL PRE-FLIGHT ASSERTIONS PASS.** `experiments/wave-deep30` exists, built from
`_template_sealed`. **Remaining gate = the short-window SMOKE RUN (X1-runaway); NOT yet run.**
Then full run + `collect_metrics`. Still uncommitted (user commits).
Pre-flight script: `<scratchpad>/preflight_wave-deep30.py` (worth keeping — re-run after any
mask change). Plan file: `~/.claude/plans/i-m-gonna-put-you-crystalline-adleman.md`.

| pre-flight check | result |
|---|---|
| domain seal | **OK, 1/1 sealed** |
| SFINCS `mask` / `z` / `mask==2` | **byte-unchanged** (395,574 active; 1,669 bnd cells) |
| surge forcing `sfincs_netbndbzsbzifile.nc` | **byte-identical** to premier |
| `sfincs.inp` delta vs premier | **0 keys** ⇒ perfect single-variable A/B |
| SnapWave active | 395,574 → **524,762 (+32.7%)** |
| NEW cells | 129,188, **all submerged**, z ∈ [−30, −10] exactly |
| `snapwave.bnd` support pts | 7 → 7, depth **−26.6..−30.0 m** (were −9.7..−14.1) |

### 🐛 BUG FOUND AND FIXED AT STAGING — `zmin` alone was NOT a seaward extension
`create_active(zmin=-30, copy_sfincsmask=False)` **rebuilds the mask from scratch** and admits
every cell above the threshold inside the region — so −30 also swept in **10,431 INLAND cells
(up to +106 m, lon −74.28..−74.10)** that the SFINCS mask excludes via its own include/exclude
criteria. Those were SnapWave-active + SFINCS-INACTIVE + dry = **exactly the X1 runaway geometry**
(a wave cell where SFINCS computes no `zs`). Open risk #1 was therefore *worse than assessed* —
it wasn't only the deep cells, it was 10k dry ones.
**Fix (in `add_waves`, decoupled branch):** after `create_active`, overwrite `snapwave_mask` with
the explicit union `(sfincs mask > 0) | (new & sfincs-inactive & z <= base.mask_zmin)`, written as
uniform 1s so `create_boundary` promotes only the seaward rim. Copying the SFINCS *codes* verbatim
would import `mask==2/3` (the coastal water-level/outflow boundary) as WAVE-boundary cells — the
very coupling this arm removes. **⇒ the true growth is +32.7%, not the +35% previously recorded**
(that number included the land contamination). Premier's wave domain is a strict subset (dropped 0).
- Also resolves open risk #2 (unvalidated ring size): hydromt produced **763 boundary cells in a
  tight −25..−30 m band** (median −29.7) — a clean rim, not a blob.
- Open risk #3 (GEBCO): newly-active z is smooth — only 0.7% exactly-integer, largest sorted gap
  5.88 m, no NaN. Benign.

### ⚠️ `prepare_experiment` DID NOT have the crsfile/storevel fix — NOW IT DOES
The fix existed only in `scripts/setup_sealed_premier.py` (`DIAG` dict + `flux_crosssections.crs`
copy), which stages the four SEALED arms. `run_experiments.prepare_experiment` — the path that
stages every NEW experiment — never had it, which is why both phase-lag arms needed hand-patching.
**Ported to `nj_sfincs/model.py` as `set_inp_keys()` + `restore_diagnostics()`, now called from
`prepare_experiment` after `finalize()`.** Confirmed working: staged inp delta vs premier is 0 keys
and `sfincs.crs` is present. **The manual patch step in [[project_tidal_phase_lag]] is obsolete.**

## The defect (observation-confirmed, not argued)
Premier (`faber-waves-premier`) runs SnapWave off ERA5 (`era5_waves_nj`) at a boundary
sitting at **z ≈ −10 m**, because the X1 fix forced the wave solver onto the SFINCS mesh
and support points were read from `mask == 2` (the WATER-LEVEL boundary). ERA5 is a
deep-water source ⇒ the open-ocean sea state is pasted onto the 10 m contour with **no
shelf transformation**. Arbitrated with NDBC 44025 (36 m, deep water):
at Sandy's peak (10-30 00:00) the buoy measured **7.80 m in 36 m** while ERA5 imposes
**7.82 m in 10 m** — same sea state, 26 m too shallow. CORA's SWAN (resolves the shelf)
says **5.07–6.02 m** there. Second defect: ERA5's 31 km cell > the 25 km boundary ⇒ all 7
support points carry **byte-identical Hs**. Full evidence in [[project_cora_evaluation]].
Direction is favorable: less boundary energy → less setup → lower levels, and premier HWM
bias is **+0.32 m (too wet)** — pushes the RIGHT way (unlike composite, which overshot).

## Root cause (verified)
The X2 mesh **was already built and sits unused**: `data/region.geojson` reaches lon
−73.450; the mesh reaches lon −73.449 / −69 m; **~141k offshore cells are inactive purely
because `BaseConfig.mask_zmin = -10.0`** cuts them. Not a mesh limitation — a threshold.

## Why seal-safe
`premier.py` **deliberately EXCLUDES `snapwave_mask` from the domain hash** (it's rewritten
per wave config). So extending ONLY `snapwave_mask` keeps the sealed fingerprint
(`547408 / 1635 / 45f4f74ca9a2347d`) intact, leaves the SFINCS `mask` + surge boundary +
`sfincs_netbndbzsbzifile.nc` untouched, and changes exactly one variable. Extending the
SFINCS `mask` instead would break the seal AND move the surge boundary. See
[[reference_premier_domain_guard]].

## What was changed (uncommitted)
- **`nj_sfincs/config.py`** — two new `WaveConfig` fields: `decouple_snapwave: bool = False`
  (default False ⇒ every existing arm reproduces byte-for-byte) and
  `snapwave_mask_zmin: float = -30.0`. Plus the `wave-deep30` experiment (premier wave
  knobs + `decouple_snapwave=True`; differs from the premier by **exactly one knob**, since
  −30 is already the default).
- **`nj_sfincs/model.py` `add_waves()`** — branch on `wcfg.decouple_snapwave`. Coupled path
  UNTOUCHED. Decoupled path: `create_active(zmin=-30, copy_sfincsmask=False)` (no overwrite
  with the SFINCS mask), then `create_boundary(btype="waves", zmax=-25)` for the seaward
  ring; support-point selection reads `snapwave_mask == 2` instead of `mask == 2`. The
  Sandy-Hook-tip demotion (anti-runaway) is KEPT. New const `SNAPWAVE_BND_RING = 5.0`.

## Implementation gotchas already caught (would've failed at staging)
- SnapWave `create_boundary` needs **`btype="waves"`** — `"waterlevel"` is SFINCS-only and
  raises. The subclass DOES override `create_boundary` with `model="snapwave"` (writes
  `snapwave_mask`); the parent's `model="sfincs"` default would silently rewrite the SFINCS
  `mask` and break the seal — so the override is load-bearing.

## Static verification (done)
- One-variable isolation confirmed: `wave-deep30` vs premier differs by `{decouple_snapwave}`.
- Simulated on the sealed mesh: SnapWave active **395,574 → 535,500 (+139,926, +35%)** — note
  **+35%, not the +33% I first quoted**; the offshore mesh is unexpectedly fine (82k cells at
  level-3 / 50 m over open ocean). Support points move from z ≈ −10 m to **z ≈ −26..−30 m**
  at lon −73.45..−73.77. Only the SnapWave solve (every `dtwave=1800 s`) pays the +35%.

## Open risks (NOT yet cleared)
1. **X1 runaway returning** — SnapWave needs a depth where SFINCS computes no `zs`. Lower
   risk than X1 (those cells were off-mesh, true depth 0; these carry −20..−69 m bathy, so
   even `zs=0` leaves deep water) but **inferred from physics, not read from the SnapWave
   Fortran.** The smoke run is the gate — do it before any full run.
2. **My mask-edge simulation flagged 99.98% of cells as edges** ⇒ the `mesh2d_face_faces`
   adjacency convention isn't what I assumed, so **the boundary-ring SIZE is unvalidated**
   (support-point LOCATIONS are trustworthy — they come from depth+easternmost-per-bin, not
   adjacency). hydromt does the real edge detection at staging; confirm the ring there.
3. Offshore bathy out there is **GEBCO** (integer-quantised — caused earlier nearshore hm0
   spikes). Benign at 20–70 m for propagation, but eyeball the z field before a full run.

## Deferred threads (agreed sequencing — AFTER this arm is scored)
- **Raritan Bay tide** (user is keen). North-lobe boundary (lat ≈ 40.52, 760 cells) is
  imposed at ~1.64 m range along its whole length (cells sit at s≈0.12–0.18 on the Battery→AC
  chord). TWO independent sources say the west end should be ~17% higher: **NOAA harmonics at
  Keasbey 8531262 = 1.843 m** vs Battery 1.581; **CORA lon −74.280 = 1.928 m** vs 1.685. No
  live gauge in Raritan Bay (only Battery + Sandy Hook), but Keasbey publishes harmonic
  constituents at the western corner ⇒ reuse the `phaselag_composite_v2` recipe (local
  harmonic tide + Battery→AC interpolated NTR). Adds structure on the NORTH lobe, NOT the
  open-coast chord ⇒ distinct from the composite arm that failed.
- **CORA** — NOT adopted as water-level forcing (tide lags +6..+24 min, runs 0.14–0.31 m
  low); kept as independent validator + fallback wave source. Details [[project_cora_evaluation]].

Related: [[project_cora_evaluation]], [[project_snapwave_root_cause]] (X1/X2 origin),
[[reference_premier_domain_guard]], [[project_tidal_phase_lag]], [[project_domain_rebuild]]
