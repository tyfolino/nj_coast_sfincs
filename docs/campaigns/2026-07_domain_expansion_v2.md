<!-- Campaign record. Moved out of the Claude memory store 2026-08-05; the
     memory file was `project_domain_expansion_v2`. -->

> **Historical record — read top-down, newest first.** Blocks are appended in
> reverse chronological order and later blocks SUPERSEDE earlier ones, including
> where an earlier block calls itself current. Several conclusions in here were
> retracted; the retraction is always above the claim it retracts. For what is
> believed true *now*, see the memory store and `CLAUDE.md`, not this file.
>
> **Standing summary at the time of the move:** ⭐ NEW REPO ~/nj_coast_sfincs + shared data root ~/sfincs_data. Domain v2_barnegat extends south to Barnegat Inlet (lat 39.70), the first increment of a staged march to Cape May. Mesh 1,143,357 faces (2.09x v1, ~6.3 h/run). Brings the FIRST interior gauges that survive Sandy's peak. NO eHydro carve needed. Geography now lives in nj_sfincs/domain.py.


# Domain v2 — south to Barnegat Inlet, in a new multi-domain repo (2026-07-26)

## 🔴🔴 2026-07-30 — THE SECTION BELOW IS LIKELY AN ARTEFACT. READ THIS FIRST.

The open-ocean water level was being **clamped 2.6 km inside Barnegat Inlet**, 75 m from
the Barnegat Light gauge, in every run quoted below. A **−43 min "early" arrival is zero
lag** — it was the ocean's own phase, not a propagation measurement — and the
over-amplification is that clamp bleeding out. **The sign-flip story is built on it.**
Repaired 2026-07-30 and being re-measured; do not re-quote these as physics until the
new numbers land. See [[reference_inlet_waterlevel_clamp]] and
[[project_handoff_2026_07_30]].

## ⭐⭐ 2026-07-28 — THE BAY TIDE ARRIVES **EARLY**, AND MANTOLOKING IS OVER-AMPLIFIED 2.4×

Fell out of fixing `plots._phase_tag` (see [[project_tidal_phase_lag]]), which had been
silently printing **nothing** for every interior gauge. Measured on the premier over
`validate._prestorm_window`, model-vs-obs cross-correlation, **+ = model LATE**:

| gauge | phase | obs range | model range | r at lag 0 |
|---|---|---|---|---|
| Sandy Hook (coast) | **+17.8** | 1.586 | 1.586 | 0.984 |
| Shrewsbury / Shark (estuary) | **+35.1 / +35.2** | — | — | — |
| **Barnegat Light** (inside inlet) | **−43.0** | 0.721 | **0.719** | 0.709 |
| **Mantoloking** (mid-lagoon, 35 km up) | **−58.1** | 0.167 | **0.401** | 0.732 |

**🔑 THE SIGN FLIPS.** Everything ocean-side and estuary-side is LATE by 18–35 min;
**both bay gauges are EARLY by 43–58 min.** So this is NOT the same defect as the
Battery-imported lag, and `tide-shift` (which advances the tide further) pushes the bay
the WRONG way. Pre-registered: expect the bay phase to get ~18 min WORSE under `tide-shift`
even if the coast and estuary improve. **That is a real trade to weigh, not a surprise.**

**🔑 And the lagoon is UNDER-DAMPED.** Barnegat Light's tidal range is right to 0.002 m
(0.719 vs 0.721) — the inlet exchange is excellent — but 35 km up the lagoon the model
keeps **0.401 m where reality damps to 0.167 m (2.4×)**. Amplitude over-damping was the v1
estuary story; here it is the OPPOSITE. Together with the arriving-early phase this says
the lagoon conveys **too freely** — too little friction / too much cross-section — which is
the same direction as the closed Manahawkin wall over-filling the southern end.

**⇒ This is the mechanism the along-bay gradient defect below has been missing**, and it is
measured on 6-min records, so no part of the HWM-estimator problem touches it. ⚠️ These
gauges are still NOT in `validate.gauge_phase_lag` — the numbers above come from the figure
path only. **Fold them in when the interior gauges are added to `validate.evaluate()`.**

## ✅ 2026-07-28 — THE FIRST CAMPAIGN IS SCORED AND WRITTEN UP

Both arms finished (3:24:41 / 4:00:13) and are scored under the adopted `median` estimator.
**The verdict lives in [[project_cora_evaluation]] (three axes) and
[[reference_hwm_estimator_artifact]] (why the score changed).** Headline: ERA5 is
admissible at **1 of 7** support points and CORA at **7/7**; CORA runs a steady **+11%**
high at NDBC 44025; and the HWM score does **not** separate the arms.

### 📓 `notebooks/sfincs-nj-barnegat-viz-cora.ipynb` — 70 cells, the campaign's record
Methodology (build → forcing → wave boundary) → Results → the estimator investigation →
the CORA three-axis verdict → animations → conclusions. Executed end-to-end once
(~35 min, 57 MB with outputs); after the median change **6 cells were cleared and need
re-running** — the scores cell, the CORA cell, and the four estimator cells. The other 35
code cells still hold their figures, so it reads fine as-is.

⚠️ **An ordering bug worth not re-introducing:** `animate.WINDOWS.update({...})` for the
southern windows must live in **Setup**, not in the Animations section — the Results
flood-depth panels consume `WINDOWS["barnegat_inlet"]` long before the animations do, so a
late registration makes a top-to-bottom run die on `KeyError`. It bit a real run.

🔑 **The sharpest LIVE defect is no longer the HWMs — it is the along-bay gradient.**
Observed, Mantoloking sits **+0.518 m above** Barnegat Light; the model puts it **−0.410 m
below** (error **−0.93 m**) while getting the 5.90 h travel time right to 0.10 h. That is
scored against two agencies' 6-min records, so **none** of the estimator problem touches
it. It points at the closed Manahawkin wall over-filling the southern end. The interior
gauges are still NOT in `validate.evaluate()` — folding them in is the highest-value next
step. `wave-cora` makes the pair error slightly worse (−0.93 → −1.02 m).

## 🔴 2026-07-27 — FIRST v2 CAMPAIGN IS RUNNING. READ THIS FIRST.

**SLURM 59243636 `faber-waves-premier` (CONTROL) + 59243637 `wave-cora` (PERTURBATION)**,
both `--time=12:00:00 --mem=128G -c 48`, submitted ~21:43Z. Pre-flight CLEAR on every
axis: both sealed, **`sfincs.inp` 0-key diff**, surge forcing byte-identical
(`62a35f63a08bb1f7`, the same hash as the v1 premier), `snapwave.bnd` identical while
`.bhs/.btp/.bwd` differ, **X1 hazard 0** (coupled config: snapwave_mask ≡ sfincs mask,
817,991 both), diagnostics restored. Score with **`scripts/score_v2.py`**.

### ⭐ SEALED: v2_barnegat fingerprint = **1143357 faces / 2164 bnd edges / `9ccbab0bc7a9fc0d`**
`premier.py` is now MULTI-DOMAIN — `EXPECTED` dict keyed by domain name, `expected()`
resolves via `NJ_DOMAIN`. The "every v2 dir audits UNRECOGNISED" problem is gone.
`PREMIER_NAME` is now `faber-waves-premier` on both domains (same config, different
domain — which is exactly why the fingerprint is checked separately from the name).

### ⚠️⚠️ THE CAPE MAY TRAP — a knife-edge silent invalidation, CAUGHT AT 0.9 km
`noaa_sandy_nj.nc` has ALWAYS held **three** gauges: Battery, Atlantic City **and Cape
May (8536110)**. hydromt picks them by BUFFERING the region, so the support-point count
is a property of the DOMAIN, not the file:

| | Battery | Atlantic City | Cape May | ⇒ support pts |
|---|---|---|---|---|
| v1_monmouth | 20.0 km | 92.5 km | **150.7 km (out)** | **2** |
| v2_barnegat | 20.0 km | 39.6 km | **99.1 km (IN by 0.9 km)** | **3** ← would have been |

⇒ the "premier configuration" on v2 would have silently become a **3-node boundary** —
and an inserted node is exactly what cost `phaselag_composite_v2` **+0.18 m of HWM
bias**. Nothing else would have looked wrong. **FIXED**: `waterlevel_buffer` is now a
PER-DOMAIN field (v1 100 km, **v2 60 km** — AC 39.6 in, Cape May 99.1 out, ~40 km margin
either side) plus `n_waterlevel_support` **asserted after hydromt actually selects**
(`model.check_waterlevel_support`, called from `add_forcing` AND from the forcing-swap
branch of `prepare_experiment`). Staging log now prints `[bnd] 2 water-level support
point(s)`. **When the domain reaches Cape May, raise BOTH numbers deliberately.**

### ⚠️ THE BARNEGAT INLET SSS WAS DECLARED BUT UNFED
`_SSS_BARNEGAT_INLET` was in the registry and written into `sfincs.obs` since the domain
was built, but `sandy_storm_tide_nj.nc` only ever carried the two Monmouth Beach units
(2258/2259, BOTH at Sea Bright) — so the model wrote a series for it and there was
nothing to score against. **A declared-but-unfed gauge is worse than an absent one: it
looks like coverage.** FIXED: instrument **2260 = `SSS-NJ-OCE-001WV`** (site 7727),
added to `download_sandy_storm_tide_sensors.py`; file now has 3 stations.
⭐ **Its peak is 1.65 m @ 2012-10-30 00:00, vs Barnegat Light 01409125's 1.59 m @ 00:24
— two agencies, two instruments, ~1 km apart, agreeing to 0.06 m and 24 min.** That is a
much harder target than either alone. 🔑 STN instrument records carry **no lat/lon**;
resolve IDs by `location_description` from `Events/24/Instruments.json`.

### 🌉 THE BRIDGE RESCORE IS BUILT — and it is mandatory for any v1 comparison
`validate.hwm_metrics(..., hwm_ids=...)` restricts scoring to a mark set. **v1's 31
marks are an EXACT subset of v2's 95 by `hwm_id` (31/31)**, so the restriction is a true
bridge, not a spatial re-match. `scripts/score_v2.py` emits BOTH
`reports/v2_native95.csv` (v2 on its own terms; valid for control-vs-CORA) and
`reports/v2_bridge31.csv` (**the ONLY v1-comparable column**). Never put a native-95
number in the same column as a v1 number.

### 🔧 Repo gaps closed tonight
`run_experiments.py` **did not exist in nj_coast_sfincs at all** — ported from v1 with
the domain-registry fixes folded in, plus a new `--slurm-args` passthrough (the shared
batch script's 3 h `#SBATCH` is nowhere near enough for 1.14M faces). New
`hpc/stage_v2.sh` wraps staging, because the env-var + nohup + redirect combination is
easy to get wrong and a half-written template leaves a partial `sfincs.nc` that the next
invocation tries to fingerprint. ⚠️ **`git` is NOT on PATH on the compute nodes** —
`module load git` before committing.

## Where things live now

| | |
|---|---|
| **New repo** | `/cache/home/tpj8/nj_coast_sfincs` — git-initialised, **staged not committed** |
| **Shared data root** | `/cache/home/tpj8/sfincs_data` — the raw source bytes |
| **Old repo** | `nj_sandy_sfincs` — FROZEN as the record for the sealed premier campaign |

`~/sfincs_data/elevation/{raw, cudem/raw, ehydro/raw}` holds 29 GB of raw source (16 GB NJ
statewide LiDAR .img/.ige, 11 GB CUDEM 1/9" tiles, 2.3 GB eHydro ZIPs). **Both repos reach it by
SYMLINK at the original paths**, so no script needed changing. The move was `mv` within `/cache`
(same device, id 61 — `/home/tpj8` *is* `/cache/home/tpj8`), i.e. metadata-only, so the
hard-linked staged inputs of the then-running job were untouched. Verified after: old repo still
audits **10/13 sealed**, byte-identical file counts.

`micromamba/`, `hydromt_sfincs/` and `sfincs-desktop.sif` are symlinked from the new repo back to
the old one — **not yet consolidated into the shared root** (deferred while a job was running).

## The domain

Region v2 = v1's polygon ∪ a southern lobe at **lon −74.30…−73.45, lat 39.70…40.15**
(`data/region_v2_barnegat.geojson`, 6,133 km², ~2.04× v1's area). Brings in Manasquan Inlet,
the Point Pleasant Canal, the **Mantoloking breach**, Barnegat Bay, Island Beach and **Barnegat
Inlet** (39.7565).

- **Offshore edge stays straight at −73.45.** GMRT says the −30 m isobath is at lon −73.733 and
  −40 m at −73.502 off Barnegat, so one straight line is deep enough for the whole coast — no
  staircase, no alongshore discontinuity in the water-level boundary. ⚠️ **GEBCO's 450 m grid
  disagreed** and implied a staircase was needed; it is too coarse here. Use GMRT for isobaths.
- **West edge −74.30** so every tidal limit is enclosed ON DRY LAND (Toms R head-of-tide gauge
  −74.223, N Br Metedeconk −74.153, Manasquan at Allenwood −74.122). Workstream L rule.
- **South edge lat 39.70** = the Manahawkin narrows, the narrowest bay cross-section between
  39.55 and 39.80 (2,651 m wide, deepest −3.57 m; vs 4,533 m at 39.74 and 5,388 m at 39.62),
  6 km south of Barnegat Inlet.
- Edges verified against the DEM: west edge and the lat-40.1504 connector **entirely dry**; the
  south edge is 2.4 km of ≤3.6 m water (the intended cut), ~1 km of dry LBI, then ocean.

## ⚠️ THE SOUTH-EDGE BOUNDARY — nearly a silent invalidation

The first probe came back with **55 `mask==2` (WATER-LEVEL BC) cells at −3.87 m across the
Manahawkin cut.** A mask==2 cell has the interpolated **open-ocean level imposed on it**, so
SFINCS would have driven Barnegat Bay directly from its southern end, competing with the
exchange through Barnegat Inlet — corrupting **the exact signal the extension exists to
measure**. It passes every existing invariant (it is not an outflow-on-water leak).

**FIXED** by a `manahawkin_cut` MaskOverride (2 → 1, box 569,000–573,500 × 4,390,000–4,400,000),
the same treatment the Shrewsbury narrows get. Verified after rebuild: fires on exactly 55 cells,
south-edge waterlevel 267 → 212, and **0 waterlevel BCs remain west of x=574,000** ⇒ the bay is
driven only through its inlet.

**Known, accepted artifact:** the cut is now a closed WALL, so the real onward exchange to Little
Egg Inlet is missing ⇒ expect over-response in the last few km. The 6 km buffer to the inlet is
the margin and the Barnegat Light gauge sits inside it as the check.

## ⭐ The validation payoff — interior gauges that survive the peak

Every permanent gauge inside the v1 domain died mid-storm (Shark + Shrewsbury both end
~2012-10-29 04:00), so Sandy's peak was only ever scored against HWMs plus one open-coast wave
sensor. Barnegat Bay gives **two complete 6-min records through the crest**:

| gauge | peak NAVD88 | peak time | n |
|---|---|---|---|
| `01409125` Barnegat Light (at the inlet) | **1.59 m** | 2012-10-30 00:24 UTC | 708, max gap 18 min |
| `01408168` Mantoloking (mid-lagoon, 35 km N) | **2.11 m** | 2012-10-30 06:18 UTC | 721, max gap 6 min |

**Read them as a PAIR.** Mantoloking peaks 0.52 m higher and ~6 h later than Barnegat Light.
A model can match either alone by getting the overall level roughly right; matching the
*difference* requires bay conveyance and inlet exchange to be right. Score level AND timing.
(`01409146` Ship Bottom excluded: record ends 10-28 and it sits south of the domain edge.)

Also new: **95 usable NAVD88 HWMs** (v1's file had 31), the Barnegat Inlet SSS
(`SSS-NJ-OCE-001WV`), and **6 discharge inflows** (~46 m³/s vs v1's ~11) — Toms River,
N Br Metedeconk, Cedar Creek, Manasquan at Allenwood. Every `src_lon`/`src_lat` was chosen by
SAMPLING THE MERGED DEM for a genuinely wet cell, not from the gauge coordinate.

## ⭐ NO eHYDRO CARVE IS NEEDED — and how that was established

**Barnegat and Manasquan Inlets are already open.** The 2010 USACE lidar simply DOES NOT COVER
those channels (NoData across both throats), so CUDEM shows through and supplies them directly.
That is the opposite of Shark River Inlet, where the lidar *did* cover and returned the water
surface.

Method (reusable, and it needs **no built mesh** — the audit script does, this doesn't): sample
the merge tier-by-tier and take the **thalweg sill = max over along-channel slices of each
slice's MINIMUM**. Positive control first:

| channel | sill | |
|---|---|---|
| Shark R Inlet, carve REMOVED (control) | **+0.67 m** | DAMMED — reproduces the recorded +0.57 m |
| Shark R Inlet, carve applied | **−3.21 m** | OPEN |
| Barnegat Inlet (no carve) | **−3.71 m** | OPEN |
| Manasquan Inlet (no carve) | **−4.29 m** | OPEN |
| Point Pleasant Canal (no carve) | **−5.91 m** | OPEN |

⚠️ **Always run the positive control first.** The first attempt showed Shark "dammed both ways"
— because the eHydro rasters had not been copied into the new repo at all. Without the control
that would have read as a physics result.

## Mesh + cost

**1,143,357 faces, 2.09× the sealed v1 (547,408), ~6.3 h/run projected.** Invariants pass;
v1's footprint reproduces at 541,081 faces (vs 547,408 sealed) so the north was not disturbed.

⚠️ **A PLANNING ASSUMPTION THAT WAS WRONG:** I expected to save by coarsening the offshore shelf.
**`mask_zmin = -10` already makes deep water INACTIVE** — the entire domain has only ~9k active
cells below −10 m, so shelf coarsening saves essentially nothing. **The cost driver is LAND:
~65% of the southern lobe's active cells sit above 0 m.** Tightened the land gates against a
measured ceiling instead — southern-lobe HWMs top out at **3.66 m** (p95 3.00), domain-wide max
5.79 m — so 50 m stops at +5 m and the 100 m transition at +9 m. That saved only ~3%.
**≈1.1M faces is close to what this domain costs** at a resolution that keeps inlets, shorelines
and bays fine. Next lever if 6.3 h is too slow: bay FRINGE 25 m → 50 m (user called that terrain
the trickiest, so ask first).

Refinement recipe: `scripts/build_refinement_v2_barnegat.py` → `data/quadtree/refinement_v2_barnegat.geojson`.
v1's polygons are reused verbatim for the north. Bay vs ocean is separated by a sloped line
`x = 576,000 + 0.160*(y − 4,402,000)` (fitted to the barrier's bay-side shore), placed ~700 m
west on purpose — the same line is reused by the HWM basin rules so the two cannot disagree.
Probe with `scripts/probe_mesh_size.py` / `hpc/probe_mesh.slurm` (build_static skip_subgrid,
~8-10 min); it writes `domain_dryrun.npz`, **not** `sfincs.nc`.

## Data changes

- ⭐ **NEW TIER `cudem13_nj`** — NOAA CUDEM **1/3 arc-second (~10 m)**, ranked below `cudem_nj`
  and above `gmrt_nj`. The 1/9" product has **NO tile east of −74.00 south of 40.25, and none
  east of −73.75 anywhere on this coast** — verified against that dataset's own authoritative
  `urllist8483.txt` (942 URLs, every collection). A gap in the product, not a missed download.
  That strip is where SnapWave shoals; without this it fell straight through to 50 m GMRT.
  8 tiles, 144 MB, `scripts/download_cudem13.py` (selects tiles by domain bbox automatically).
- **`cudem_nj` now points at the TILE VRT**, not a materialised clip — avoids a ~2 GB duplicate
  and nothing to re-clip on the next push south. Values identical (`gdal_translate -projwin`
  only windowed, never resampled).
- Catalog **28 → 22 keys**: retired forcings (both composites, `gtsm_sandy*`, shblend,
  `fes_sandy_tide`) dropped rather than carried as keys pointing at deleted files. Kept:
  `noaa_sandy_nj` (premier) + `noaa_sandy_phaseshift` (the pending candidate).
- ⚠️ **`wavemaker_nj_coast` is v1 EXTENT ONLY** (lat 40.152–40.452 = the northern third).
  Unused by the premier (`wavemaker=False`) so not blocking, but **`scripts/build_wavemaker_line.py`
  DOES NOT EXIST in either repo** — the geojson outlived its builder. Any v2 wavemaker arm needs
  it written first (alongshore −5 m contour, trimmed before the Sandy Hook spit).

## Status at hand-off (2026-07-26 ~14:25)

- ✅ **MESH BUILT — SLURM 59150038 COMPLETED in 21 min** (much faster than the 8 h alloc; subgrid
  623 s over 75 blocks) → `data/frozen_mesh_v2_barnegat` (`sfincs.nc` 521 MB, `sfincs_subgrid.nc`
  373 MB, `roughness.nc` 414 MB). Self-verified at build time: **1,143,357 faces / 817,991 active
  — exactly the probe's projection**, **free-outflow cells on water = 0 (SEALED)**, Shark
  −6.19 m / Barnegat −9.99 m / Manasquan −9.94 m all OPEN. ⚠️ Those sills read DEEPER than the
  pre-build DEM audit (Barnegat −9.99 vs −3.71) because this is the SUBGRID representation, not
  the raw merge — expected, but sanity-check it before sealing the fingerprint.
  Activate with `export NJ_FROZEN_MESH=data/frozen_mesh_v2_barnegat` (or edit `BaseConfig.frozen_mesh`).
- ✅ **`wave-deep30+tide-shift` (old repo) COMPLETED + SCORED 2026-07-27** — the old campaign's
  last open arm is closed. See [[project_snapwave_decoupling]].
- ⏭️ NEXT: seal the v2_barnegat fingerprint in `premier.py` (still v1-only, see
  [[reference_premier_domain_guard]]); stage + smoke run; **X1 hazard check must run AFTER the
  wave block** (`snapwave_mask` does not exist at `build_static` time); full solve with
  `extra_args=['--time=12:00:00','--mem=128G']`; then **bridge-rescore v2 restricted to v1's HWM
  marks** — without that no v2 run is comparable to the existing campaign, since the mark count
  itself changed 31 → 95.

Related: [[project_nj_framework]] (the goal this realises), [[reference_premier_domain_guard]],
[[reference_build_traps]], [[reference_proj_double_free]], [[reference_disk_quota_dedupe]],
[[project_domain_rebuild]], [[project_tidal_phase_lag]], [[project_snapwave_decoupling]].
