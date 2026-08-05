<!-- Campaign record. Moved out of the Claude memory store 2026-08-05; the
     memory file was `project_domain_rebuild`. -->

> **Historical record — read top-down, newest first.** Blocks are appended in
> reverse chronological order and later blocks SUPERSEDE earlier ones, including
> where an earlier block calls itself current. Several conclusions in here were
> retracted; the retraction is always above the claim it retracts. For what is
> believed true *now*, see the memory store and `CLAUDE.md`, not this file.
>
> **Standing summary at the time of the move:** Workstream L (2026-07-14): region fix + Shark eHydro carve + build invariants — REBUILT and it worked. Workstream O (2026-07-15): faber-waves-premier adopted as premier, Galibier retired.


# Workstream L — the sealed, un-paved domain. ✅ REBUILT, and Workstream O chose the premier.

Fixes BOTH 07-14 defects at their root, so neither can recur. The rebuild + sealed 2×2 ran and
scored (see the ✅✅ and Workstream O blocks below). Plan: `~/.claude/plans/peaceful-moseying-blum.md`.

## 🚀 Phase 2 M+E LAUNCHED 2026-07-15 (jobs 58185237/38/39, Faber, waves, --requeue)
Off the premier `faber-waves-premier`. **M — boundary-depth sweep** `mask-zmin15` /
`mask-zmin20` + **E — infragravity** `wave-ig` (premier + `snapwave_igwaves=1`,
one-flag change). Wind (P) + N/NW boundary (C) stay RETIRED per user.
- **M needed NO subgrid rebuild** and I proved why: the sealed mesh reaches −69 m and every one
  of its 547,408 faces already carries subgrid tables, so a deeper `mask_zmin` only *activates*
  faces that already have tables. New `scripts/setup_boundary_depth.py` copies the frozen mesh and
  re-runs the mask/boundary at the new zmin (−15 +23,921 cells; −20 +80,902), then forcing+waves.
  Support points move seaward with the contour (bnd x 584–589k → 588–598k → 594–619k) ⇒ genuine,
  not a no-op. Decisively validated: re-deriving the mask at zmin=−10 reproduces the frozen mask
  **bit-for-bit (0 cells changed)**, so any −15/−20 change is purely the intended extension.
- **Refactor:** `nj_sfincs/model.py` build_static's mask/boundary block is now the reusable
  `apply_mask_and_boundary(base, sf)` (pure code motion) — the M script and the premier build share
  one source of truth. **E** staged by `scripts/setup_ig.py` (hard-links `_template_sealed`).
- **Heat-wave requeue:** added `#SBATCH --requeue` to `hpc/sfincs_run.slurm` (cluster
  PreemptMode=REQUEUE) so preempted/node-failed jobs auto-resubmit; SFINCS re-runs from scratch
  (idempotent). All uncommitted. Analyse when they land (reuse `scripts/analyze_sealed.py`
  discipline: local fix must NOT move the basins that never leaked; lead with gauge+HWM, not MOTF).

## ✅ Workstream O (2026-07-15) — premier chosen on the sealed domain
`scripts/analyze_sealed.py` scored the sealed 2×2 (Faber/Galibier × waves/nowaves).
- **`faber-waves-premier` is the ADOPTED premier.** Gauge 2.84 m vs surveyed crest 2.94 (err
  **−0.10 m**, best in campaign; broken premier was 2.22 / −0.71). Shark tide alive in all four
  sealed runs (frac_rising 0.542, range 1.30–1.35). MOTF CSI 0.51 → **0.71** (0.64 is the NO-WAVES arm), FAR 0.17 → 0.14.
- **Faber over Galibier; Galibier is UNOFFICIALLY RETIRED.** The two are bit-identical with
  waves OFF; with waves **Galibier overshoots hard** (gauge +0.57, HWM bias +0.97, RMSE 1.14)
  even with `snapwave_gammax=2.0` restored. Don't re-open the engine question.
- ⚠️ **Locality caveat (the one open thread):** the open coast that never broke drifted ~0.1 m
  on the rebuild (south_coast −0.055 → **+0.048**; atlantic_oceanfront swung further). The
  `analyze_sealed.py` guardrail flagged it — the fix is **not *purely* local**. Small vs the
  gains, not yet explained.
- Goal is **fit-for-purpose, not metric-perfect**: if we capture Sandy (the extreme), routine
  nor'easters should follow (to be tested explicitly later). User is happy with the premier.
- Viz notebook `notebooks/sfincs-nj-sandy-viz.ipynb` was slimmed (2026-07-15): Results section
  is now **side-by-side before/after** (before=`snapwave_tuned_25m`, after=`faber-waves-premier`)
  via `plots.plot_engine_panels` / `plot_gauge_verification` / `plot_hwm_residual_panels` (new) /
  `plot_motf_panels`. Note: `plot_engine_panels` API was flipped to `{label: dirname}` to match
  the others. `reports/shrewsbury_investigation.md` top block has the Workstream O resolution.

## What changed

1. **`data/region.geojson` — the leak's TRUE root cause.** The southern lobe's west edge sat at
   x≈580,650-580,915 and **chopped the Navesink in half mid-channel**; hydromt then put a
   free-outflow BC on the 5 m-deep cut face and the model drained 92.5% of the estuary's inflow.
   *The depth cut was never the problem* (those cells are only ~−5 m, well inside mask_zmin=−10)
   — **it was the region polygon.** West edge moved to **x=577,000**, west of BOTH tidal limits
   (Navesink water ends x≈577,500 at Swimming River Dam; Shark ends x≈580,000), so the domain
   edge now lands on DRY LAND. Area 2399 → 2494 km². Supersedes the post-hoc mask edit in
   `scripts/setup_leak_fix.py`, which treated the symptom.

2. **`data/elevation/ehydro_nj.tif`** (new tier, TOP of `DEFAULT_ELEVATION_LIST`, above
   `usace_nj_2010`) — carves Shark River Inlet. Built by `scripts/download_ehydro_nj.py` from
   `NJ_10_SRI_20150902_CS_4383_15`. **Clipped to WATER ONLY (z < −1 m)** — it is a *carving*
   tier, not a DEM, so it can never flatten a structure (a beach survey covering the Sea Bright
   revetment reports +2.4 m there ⇒ clipped out ⇒ seawall intact). VDatum offset −0.723 m.

3. **Build-time invariants** in `nj_sfincs/model.py` (`_check_domain_invariants`, raises):
   - **no free-outflow cell (mask==3) on water below −1 m** ⇒ *this one check would have caught
     the leak on day one*;
   - **no active cell that is land (bed ≥ −0.5 m) where eHydro sounded water (< −2 m)**.
   Both **FAIL on the old mesh** (45 and 68 cells) ⇒ they are load-bearing, not decoration.
   Wet outflow cells are auto-sealed to mask=1 (the NW/Raritan corner is on the true domain
   edge — nothing to recover, so a wall is the only correct treatment).

4. **`refinement_polygons_25m.geojson`** is now the default — see [[reference_build_traps]].

## Dry-run result (`scripts/validate_domain.py`, no subgrid) — ALL PASS

| check | old | new |
|---|---|---|
| free-outflow cells on water | **45** | **0 (SEALED)** |
| Shark inlet sill | **+0.57 m (DAM)** | **−5.10 m (OPEN)** |
| Sea Bright revetment crest | +10.99 m | +10.68 m (INTACT) |
| total faces | 547,267 | 547,408 (**+141**) |
| active cells | 392,035 | 395,574 |

## 🚀 LAUNCHED 2026-07-14 ~15:15 — jobs in flight

- **58167881 `njbuild`** (`hpc/build_mesh.slurm`, main-redhat, 16c/150G/8h) → builds
  `data/frozen_mesh_sealed`. **Passed the domain invariants at 4 min** and went into the subgrid.
- **58168000 `njstage`** (`hpc/stage_and_run_sealed.slurm`, `--dependency=afterok:58167881`) →
  builds `experiments/_template_sealed`, stages the **premier 2×2** via
  `scripts/setup_sealed_premier.py`, and submits all four:
  `sealed_{faber,galibier}_{waves,nowaves}`.
  **Faber = `sfincs-desktop.sif`; Galibier = `sfincs-cpu.sif` + `snapwave_gammax=2.0` forced back
  on** (Galibier's default of 999 removes the stability clamp ⇒ 252 m runaway wave; that finding
  is about the SOURCE, not the domain, so it survives the rebuild).
  nowaves ≈10 min, waves ≈2-4 h.

**Analyse with `scripts/analyze_sealed.py` → `reports/solver-2x2.csv`.**

## ✅✅ 2026-07-14 ~15:35 — **IT WORKED. SHARK RIVER HAS A TIDE.** (`galibier-nowaves`, 6m58s)

| | observed | ANY pre-rebuild run | **SEALED + CARVED** |
|---|---|---|---|
| Shark tidal range | 1.52 m | **none — no oscillation at all** | **1.331 m** |
| Shark frac_rising | 0.47 | **0.00** | **0.542** |
| `is_tidal` | — | **False** | **True** |
| Shrewsbury tide | 1.23 m | 0.716 (broken) / 0.977 (mask-edit) | **0.996** |

**A basin that NEVER MOVED in the entire history of this project now tracks the observed tide
cycle for cycle** (see `reports/figures/gauge_verification.png` — the broken and mask-edit runs
flatline; the sealed run oscillates with the observations, then rises to +2.8 m in the storm).
Shrewsbury holds ⇒ **the region fix reproduces the mask edit by fixing the CAUSE.**

**MOTF extent also improves HONESTLY** (`reports/figures/motf_panels.png`): broken premier
(WITH waves) CSI 0.51 / POD 0.56 / FAR 0.17 → sealed (NO waves) **CSI 0.64 / POD 0.72 / FAR
0.14**. Miss 15.3 → 9.9 km². **FAR went DOWN**, so it is not gaming MOTF's over-flooding bias —
and the sealed run beats the broken premier while running *without waves at all*.

### ⭐ THE HEADLINE TEST — no storm peak, no HWMs needed
**DOES SHARK RIVER FINALLY HAVE A TIDE?** Observed (USGS 01407770, pre-storm): **1.52 m
per-M2-cycle range, rising 47% of the time**. Old model: **frac_rising = 0.00 — the basin never
oscillated AT ALL** because its inlet was a +0.57 m dam. Both gauges (01407770 + 01407600) DIED
2012-10-29 03:54, ~20 h before Sandy's peak ⇒ **there is no storm crest at Shark and none exists
in NWIS**, so the pre-storm TIDE is the firmest validation we have there — and it happens to be
exactly the thing the dam destroys. Secondary: Shrewsbury must hold (leak-fix gave HWM +0.21,
gauge 2.691 vs obs 2.935), and **south_coast must stay at −0.0553** (the locality test).

## ❌ RETIRED 2026-07-14 (user call, and the physics agrees): **Workstream P — the wind re-test**

The case for re-running D was that a leaking basin drains away whatever wind pushes into it, so
its null was untrustworthy. But **D measured +0.002 m** — that is not "the leak ate it", that is
*no forcing response at all*. And the Shrewsbury/Navesink has only a few km of fetch and a
3.8e7 m³ prism, so wind setup there is negligible whether or not the bucket holds. Sealing the
leak gives wind **no new mechanism to act through**. **D stands: wind is a NULL LEVER. Do not
re-run it.** (Contrast with the narrows/dredge/niter nulls, which *were* void — those levers act
on CONVEYANCE, and conveyance genuinely could not show up while the basin had a hole in it.)

## Reference: how to relaunch the rebuild if needed

```
NJ_ROOT=$PWD PYTHONPATH=$PWD micromamba/envs/sfincs/bin/python scripts/freeze_mesh.py
```
(BaseConfig.frozen_mesh must be None / the script forces a real build; the subgrid is the
expensive step, ~hours.) Then re-verify with `validate_domain.py`, re-stage experiments off the
new frozen mesh, and run Phase 2: **premier Faber-vs-Galibier (sealed) → boundary-depth sweep
mask_zmin −10/−15/−20 (mask-only, NO rebuild needed — the mesh reaches −69 m and every face
already has subgrid tables) → IG.**
⚠️ **−4 m is DEFERRED**: `create_active(zmin)` is a GLOBAL cut, so −4 m would deactivate
everything deeper than 4 m — including the Shrewsbury narrows carved to −4.65 m — punching holes
through the interior. It needs an ocean-only cut + parameterising the hard-coded SnapWave
support-point filter `_z < -5.0` (`model.py`), which would otherwise yield an empty snapwave.bnd.
