<!-- Campaign record. Moved out of the Claude memory store 2026-08-05; the
     memory file was `project_bridge_dam`. -->

> **Historical record — read top-down, newest first.** Blocks are appended in
> reverse chronological order and later blocks SUPERSEDE earlier ones, including
> where an earlier block calls itself current. Several conclusions in here were
> retracted; the retraction is always above the claim it retracts. For what is
> believed true *now*, see the memory store and `CLAUDE.md`, not this file.
>
> **Standing summary at the time of the move:** NJ Sandy quadtree — ROOT CAUSE of the back-bay conveyance bottleneck FOUND 2026-06-12 (user's hypothesis): the Rumson–Sea Bright bridge causeway is baked into the NJ 10ft lidar DEM as a solid earthen dam across the Shrewsbury River at the narrows. Blocks tide + surge -> flat Shrewsbury gauge + Oceanport under-flooding. Fix: burn the channel through the causeway. Supersedes the generic 'narrows conveyance' framing.


# Bridge-as-dam — root cause of the back-bay conveyance bottleneck (2026-06-12)

**UPDATE 2026-06-23 — fix CONFIRMED to work (user, on Amarel).** Running the
no-bridge-dam bathymetry (eHydro 2015 carve + usace_nj_2010 in elevation_list)
**the Shrewsbury river floods beautifully** — the back-bay deficit chased through
the inlet-channel / wavemaker work is resolved by carving the dam, as predicted.
Knock-on: this defuses the compensation worry that blocked the waterlevel-boundary
restriction (surge now reaches the back-bay through the inlet, not via an edge
clamp) → see project_mask_boundary_cleanups (memory retired 2026-07-25), implemented 2026-06-23. Still
TODO: pull the quantitative back-bay verdict (CSI/HWMs) from the Amarel run.

**User's hypothesis, confirmed:** bridges are captured in the NJ 10 ft lidar DEM as continuous high ground that **dams the river channel**. The back-bay under-flooding + the flat Shrewsbury tide gauge are this one DEM artifact, not under-resolved bathymetry in general.

## The smoking gun
Thalweg test on the model bed (`dep_subgrid_lev3.tif`) = the DEEPEST point across the channel at each step (should stay below sea level up a tidal river):
- **Rumson–Sea Bright bridge, Shrewsbury narrows (y≈4,468,860 UTM18N, ≈40.367°N):** channel floor is −4 to −7 m everywhere EXCEPT a **~24 m-wide band where the deepest point is +1.6 m**. True-height cross-section (nearest resampling) is **100 % above sea level, embankment up to +8.6 m**. A complete dam — the entire section is dry land.
- **Rte 36 / Highlands bridge (→ Sandy Hook)** and the **Oceanic bridge (Navesink)**: channel stays −6.8 / −4.5 m under them → **NOT dams** (lidar caught open water). Only Rumson–Sea Bright fully blocks.

## Why this explains everything we'd been chasing
- **Flat Shrewsbury @ Sea Bright tidal validation:** the gauge's model cell is dry land at +1.88 m and the channel to it is dammed at +1.6 m, so the tide (obs range −0.4..+1.4 m) literally cannot reach it → flat line at the bed, one storm bump. See project_validation_roadmap (memory retired 2026-07-25) (Shrewsbury tide panel).
- **Oceanport / upper-estuary surge under-prediction:** the surge arrives at the bay mouth at the correct level but the +1.6..+8.6 m dam blocks conveyance up the Shrewsbury → the wavemaker's east overtopping can't reach the western estuary. This is the "narrows conveyance bottleneck" from project_wavemaker_run (memory retired 2026-07-25) / project_validation_roadmap (memory retired 2026-07-25) — now PINNED to a specific bridge, not generic resolution.

## Fix
**Burn the Shrewsbury channel through the Rumson–Sea Bright causeway** — cut the +1.6..+8.6 m wall down to the adjacent channel depth (~−4 m) over the channel width, so tide + surge convey. Same technique as the earlier inlet-burn experiment (`experiment_inlet_connectivity.ipynb`, burned inlets at −2 m on the regular grid — never promoted; its value on the quadtree was untested, but THIS is the spot that actually needs it). It's a bed change → Phase-1 subgrid rebuild → **batch with X2** + the project_mask_boundary_cleanups (memory retired 2026-07-25). Also worth a sweep for other dammed crossings (railroad embankments, smaller road bridges) with the same thalweg test before rebuilding.

## Source-DEM provenance (2026-06-12) — confirms structure vs solid fill
Sampled the 4-tier merge sources at the crossing cells (priority USACE>CUDEM>NJ_lidar>GEBCO; USACE=`usace_nj_2010_topobathy_clip.tif` EPSG:4326, CUDEM=`cudem_asbury.tif` EPSG:5498, NJ=`nj_10ft_dem.tif` 4326 gated z>0.001, GEBCO 4326):
- **Route 36 piers: 100% from CUDEM** (USACE is NoData across the channel there). CUDEM is a topo*bathy* product built from in-water bathymetric surveys → it captured the bridge SUBSTRUCTURE (pier caps/pile clusters/fenders/riprap) at +0.5..+2.2 m, with the channel OPEN between piers. The high deck (~20 m) is in NO tier → channel stays open → model is accidentally correct. = your "bathymetry of the pilings" hypothesis, confirmed.
- **Rumson–Sea Bright dam: solid fill in ALL fine sources.** Of the 13,121 wall cells (merged +0.5..+8.8 m), USACE median +4.35 (0% sub-sea-level), CUDEM +3.56, NJ-lidar +3.55. Wall provenance 42% USACE + 58% CUDEM. **88% of the dam footprint has NO sub-(-0.5 m) value in any fine tier — genuine solid causeway, no channel to restore.** Only ~12% have a CUDEM sub-sea-level value (down to −4.7 m) that USACE's surface capture overrode — likely the real navigation opening.
- **FIX IMPLICATION:** can't re-prioritize/restore a buried channel (88% is fill); must CARVE a synthetic opening to ~−4 m (adjacent Shrewsbury floor). Use the 12% CUDEM-deep cells to place the burn on the real navigation alignment, not arbitrarily. (Route 36 needs no fix — channel already open.)

## Fix data source RESOLVED 2026-06-12 — eHydro channel survey (better than burning)
Instead of a synthetic burn, use a real bathymetric survey of the channel. NOAA **BlueTopo** covers the Shrewsbury (−4..−5 m near the bridge) BUT its pixels there are from a **Dec-2025 survey = POST bridge-rebuild** (the bridge was destroyed + rebuilt in 2025) → REJECT. Use **USACE eHydro** instead.
- eHydro REST: `https://services7.arcgis.com/n1YM8pTrFmm7L4hs/arcgis/rest/services/eHydro_Survey_Data/FeatureServer/0/query` (query by geometry; fields surveydatestart, sdsfeaturename, surveytype CS/BD/AD, sourcedatalocation=download URL).
- The Shrewsbury is a USACE federal nav project → **annual condition surveys (CS) 2015→2024**, all PRE-rebuild. **No pre-Sandy** (earliest 2015; channel is stable + we only need the opening depth, so 2015 is a fine 2012 proxy).
- **PICK: `NJ_14_SNR_20150902_CS_4368_15`** (2015-09-02, type CS). User confirmed via the eHydro viewer its footprint covers the WHOLE Navesink+Shrewsbury system — Sandy Hook Bay → through the Rumson–Sea Bright narrows → Oceanport, + Navesink to Red Bank. (My single-point API query falsely returned 0 — the surveyed channel is a thin thalweg strip and the test point sat just off it; the visible footprint is authoritative.) Download: `https://ehydroprod.blob.core.usgovcloudapi.net/ehydro-surveys/CENAN/NJ_14_SNR_20150902_CS_4368_15.ZIP`
- **Processing:** horizontal = NJ State Plane ft (NAD83) → reproject UTM18N; vertical = **MLLW ft → NAVD88 m via NOAA VDatum** (must-do). Add as a HIGH-PRIORITY elevation tier IN THE ESTUARY CHANNELS (above CUDEM/lidar) → restores the real channel under Rumson–Sea Bright AND sharpens the Navesink + whole back-bay thalweg. Covers only the dredged channel strip (not marsh flats) — but the channel is what conveys. Burn depth cross-checks: ~−4 m (eHydro + BlueTopo + our own thalweg of the adjacent open channel).
- This is a Phase-1 (bed→subgrid) change → **batch with X2** + project_mask_boundary_cleanups (memory retired 2026-07-25).

## DOWNLOADED + PROCESSED 2026-06-17
Survey fetched + processed by `scripts/download_ehydro_shrewsbury.py` (cached/reproducible). Outputs (all under gitignored `data/`):
- `data/elevation/shrewsbury_ehydro_2015.tif` — 5 m, UTM18N, NAVD88 m, NoData OUTSIDE the dredged channel ribbon (masked to the eHydro `Bathymetry_Vector` coverage polygons). 128,605 valid channel cells; z median −3.0 m, min −12.4 m.
- `data/elevation/ehydro/shrewsbury_ehydro_2015_points.gpkg` — the 18,953 processed soundings.
- `data/elevation/ehydro/vdatum_offsets_2015.csv` — cached VDatum nodes (re-run is cheap).
Provenance details now confirmed from the ZIP: `.XYZ` = 18,953 thinned soundings, EPSG:3424 (NAD83 NJ State Plane US-ft), Z = MLLW **US survey ft, signed (negative below MLLW)**; `.DAT` is the same as +depth. Vertical conversion = **spatially-varying** NOAA VDatum REST API (geoid18): MLLW→NAVD88 offset ranges **−0.44 m (south) to −0.84 m (north/up-estuary)**, a 0.39 m gradient → applied per-point (interpolated from 400 cached in-water query nodes), NOT a single mean. `z_NAVD88_m = z_MLLW_ft*0.3048006096 + offset(x,y)`.
**Narrows validation (the whole point):** at the Rumson–Sea Bright bridge crossing latitude (y≈4,468,860 UTM18N) the eHydro tier gives CONTINUOUS channel coverage spanning x≈580,000–587,000 with z down to **−4.65 m** (median −2.9 m) — i.e. a real channel exactly where the merged DEM had the +1.6..+8.6 m dam. Carving confirmed.
**Catalog:** registered as `shrewsbury_ehydro_2015` and prepended as tier 0 (top) of the `setup_dep` list in `data/data_catalog.yml` (above usace_nj_2010 — safe because the footprint is estuary-channel-only and never touches the open-coast dune line).
**Notebook wiring:** the eHydro tier had to be added to THREE `elevation_list` blocks in `notebooks/sfincs-nj-sandy.ipynb`, not one — cell 9 (`5208270f`, `quadtree_grid.create_from_region`, gates refinement by bed → carved narrows now fall in the L3 −8..+3 gate → finer cells on the restored channel), cell 11 (`74a2cf62`, `quadtree_elevation.create`, bed onto mesh), cell 21 (`5228f7f8`, `quadtree_subgrid.create`, the load-bearing V-h conveyance tables). All three prepend `{"elevation": "shrewsbury_ehydro_2015"}`. (Gotcha: editing the .ipynb on disk while the user has it open in VSCode with a live kernel does NOT update their editor buffer — the kernel runs the buffer, not disk — so reload-from-disk or hand-paste was needed.)

## RAN 2026-06-17 — IT WORKED. The Shrewsbury floods. 🚀
Phase-1 rebuilt on the CURRENT mesh (no X2 yet) with the eHydro tier, then ran. **The Shrewsbury River floods now** — the +1.6 m bridge dam is carved out, tide + surge convey up the river into the back-bay. Root cause → fix confirmed end-to-end: real eHydro channel bathymetry restores conveyance through the Rumson–Sea Bright narrows. This is the isolated channel/conveyance fix (the east Sea Bright barrier overtopping side still wants the wavemaker, offshore ring still wants X2). User committing 2026-06-17 and done for the day. TODO next session: pull the quantitative verdict (Shrewsbury gauge tidal range restored? Oceanport/upper-estuary bone-dry HWMs come up from ~0.9 m toward obs ~2.9 m? back-bay MOTF box CSI past the 0.40 wavemaker baseline? any NEW over-flooding?) and decide whether east-barrier/wavemaker + X2 are still needed on top. See project_validation_roadmap (memory retired 2026-07-25) Phase B.

## THALWEG SWEEP 2026-06-25 — no OTHER dams; bridge-dam GEOMETRY is done
Ran the thalweg test (deepest bed per cross-channel transect) on `dep_subgrid_lev3.tif` (de-rotated, `resampling=min`, 5 m) over the back-bay channels to hunt for other dammed crossings (railroad/road embankments). **Result: NO blocking sills anywhere.** Rumson–Sea Bright narrows now −12.3..−7.2 m (eHydro carve CONFIRMED open, no longer +1.6 m); Navesink W→Red Bank −6.8..−3.1 m; Shrewsbury behind the barrier −13.1..−8.5 m. So **stop hunting bridge dams — Rumson–Sea Bright was THE dam and it's fixed.** Method caveat: min-across-corridor catches FULL dams, not channels merely too narrow/shallow to convey volume. **IMPLICATION for the back-bay deficit:** since the channels are geometrically OPEN yet the back-bay still under-floods (0.56 vs force-fed 0.77), the residual gap is NOT a blockage — it's conveyance CAPACITY (channel width/depth in the subgrid) and/or the east-barrier wave forcing magnitude project_wavemaker_run (memory retired 2026-07-25), not another dam.

## VERDICT STILL UNVERIFIED 2026-06-25 — the quantitative back-bay check is BLOCKED by a failed run
Tried to pull the Oceanport HWM (obs 2.957 m @ 582446,4465287 in `data/validation/sandy_hwms.geojson`) + Shrewsbury tidal range from the current run, but **the latest solve wrote NO output**: `sfincs_map.nc` = 0 timesteps / all-NaN zsmax (stuck at the 15:06 Phase-1 header), `sfincs_his.nc` = 0 bytes, despite the log showing "Closing off SFINCS" after 957 s. ROOT CAUSE in `sfincs_log.txt`: `NETCDF ERROR sfincs_ncoutput.F90 1635: Permission denied` then hundreds of `NetCDF: Not a valid ID` — an **HDF5 file lock**: `sfincs_map.nc` was held open by another writer (a stale SFINCS run or the live Jupyter kernel/xarray handle) when the solve launched, so the output file open failed and every record write was discarded. The notebook's `run_sfincs` Docker branch pre-removes stale `sfincs_map.nc`/`sfincs_his.nc` but the **SINGULARITY branch does NOT** (it assumed runs-as-user = no stale-file problem) → on Amarel a stale/locked map file silently kills all output. FIX: rm stale `sfincs_map.nc`+`sfincs_his.nc` before solving (mirror the Docker cleanup into the singularity branch) AND ensure a single writer (no other kernel holding the files); optionally `HDF5_USE_FILE_LOCKING=FALSE`. Re-run needed before the Oceanport/Shrewsbury verdict can be pulled. See [[reference_notebook_tooling]].

## VERDICT FINALLY PULLED 2026-07-05 — carve is IN; delivery is fine; residual = CAPACITY, ~1.3 m short
The quantitative back-bay verdict that was blocked on 06-25 (failed run) is now
pulled from `experiments/snapwave_tuned` (the sweep run; its subgrid == `data/frozen_mesh`
byte-identical at every checked point, so SAME mesh — user was right).
- **eHydro carve CONFIRMED in this subgrid, pixel-level:** sampled `dep_subgrid_lev3.tif`
  AT the eHydro deep-channel (<−1 m) pixel locations → subgrid min −11.83 / median −3.16
  vs eHydro min −11.88 / median −3.02; **100 % of channel pixels carved ≤ −1 m, 0 % above water.**
  Carve is not the problem.
- **Surge DELIVERY is fine (boundary exonerated).** Sea Bright open-coast storm-tide
  sensor (`data/gtsm/sandy_storm_tide_nj.nc`, co-located w/ obs pt `usgs_stormtide_sea_bright`
  587184,4469578): modeled peak **3.64 m vs observed 3.47 m (+0.18, RMSE 0.22, peak ~48 min late)**.
  Model is NOT uniform-Battery (Sandy Hook 3.15 → Sea Bright 3.64 gradient). Offshore BC
  delivers the surge to the coast correctly.
- **The estuary is under-filled by a WESTWARD DECAY up the channel (mapped zsmax, not a flat pool
  — an earlier "flat ~1.9 m" note here was WRONG; corrected from the estuary zsmax map w/ HWMs
  overlaid on the same colorbar).** Delivery is fine to the DOORSTEP: Sandy Hook Bay uniform ~3.4,
  **Navesink MOUTH (Highlands) modeled 2.9-3.1 vs 6 obs HWMs there median 3.34** (match). Then the
  surge DECAYS as it propagates up-estuary: lower Navesink ~2 → **cliff at the Oceanic bridge → upper
  Navesink / Red Bank ≈ 0 (essentially DRY)**. Shrewsbury south arm holds ~2 (where the eHydro carve
  helped most). Observed HWMs are 3.2-4.6 THROUGHOUT (Navesink Rumson-RedBank median 3.96). So the
  **upper Navesink (west of the Oceanic bridge) is the WORST deficit in the domain (~3 m low, near-dry
  vs obs ~3.3).** Gradual decay (not a sharp wall) = frictional/conveyance decay along an under-capacity
  channel, NOT a dam.
- Sandy Hook NOAA gauge 8531680 is NOT a clean bay-peak check: it FAILED 2012-10-29 23:00 (before the
  ~00:00-01:00 peak), obs 2.808 = a floor not the peak; modeled 3.15. Don't read the +0.35 as over-pred.
- **RECONCILES "floods beautifully" (06-17/23):** the carve lifted the estuary from bone-dry
  (~0.9 m) to ~1.9 m — real, necessary — but NOT sufficient; ~1.3 m residual remains.
- **CAUSE = conveyance CAPACITY, not a dam and not delivery** (confirms the 06-25 thalweg-sweep
  prediction). Signature = surge decays with distance UP the Navesink channel (a channel too
  small in cross-section / too frictional / too coarsely meshed to carry the tidal prism up-
  estuary), geometrically open (no dam). Worst zone = **upper Navesink WEST of the Oceanic bridge**
  (the Oceanic bridge itself is NOT a dam per 06-25 sweep — channel −4.5 m open — but the WL
  collapses just west of it). Shrewsbury south arm fills better (~2) than the upper Navesink (~0).
- **NEXT DIAGNOSTIC (not a boundary move — that would MASK this):** quantify capacity along the
  Navesink from mouth→Red Bank — quadtree cell size vs channel width, subgrid conveyance cross-
  section (deep-pixel width×depth) per station, + channel Manning. Levers if capacity-limited:
  local quadtree refinement on the upper Navesink channel, verify channel width isn't pinched to
  1 cell, check Manning. Tooling note: rasterio locally needs a libjxl.so.0.11→0.12 shim on
  LD_LIBRARY_PATH (env has 0.12 only). See project_validation_roadmap (memory retired 2026-07-25).

## CAPACITY DIAGNOSTIC 2026-07-05 — Shrewsbury body well-resolved; the Rumson–SB NARROWS is the throat
Ran width/depth/cell-size/Manning cross-sections on `experiments/snapwave_tuned` (rasterio needs the
libjxl 0.11→0.12 shim; also the subgrid tifs are on the ROTATED grid so `from_bounds` fails — sample via
`d.index(x,y)` on a regular UTM grid instead).
- **Resolution is NOT the Shrewsbury body's problem.** Channel there is 240–2048 m wide, cells 25 m (finest
  L3 present; levels = 25/50/100/200 m), so **~10–82 cells across**, deep (−2.3..−7.2 m), Manning 0.02.
  A global higher-res rebuild would be wasted on the body.
- **The Rumson–Sea Bright bridge narrows IS the flow-area minimum controlling the Shrewsbury.** Cross-
  section area drops from ~4,800 m² (body) to **~450–1,400 m² through the narrows**; tightest E-W cut
  ~**84–240 m wide = ~3–10 cells** at 25 m. At the ~3-cell pinch, resolution plausibly matters (coarse
  faces smear the narrow deep channel toward shallow banks → under-convey → throttle Shrewsbury filling).
- **Caveats:** (1) connectivity is BRAIDED — a deep continuous channel (−6..−8 m) runs behind the Sea
  Bright barrier and ALSO links Navesink↔Shrewsbury, so the narrows is *a* control not the sole gate;
  (2) the pinch may be physically real (causeway) — refinement represents it better, doesn't widen it.
- **Route 36 (Highlands) pilings:** user noticed piling artifacts in the DEM at the Navesink mouth. Per
  06-12 provenance work the Rte36 channel stays open between piers (not a dam) and the mouth already
  delivers ~3 m, so it's second-order — deprioritized.
- **DECISION PATH (not a boundary move — masks it; not a global res bump — body is fine):** before any
  rebuild, inspect the subgrid conveyance tables at the narrows u-points in `sfincs_subgrid.nc` — do the
  25 m faces capture the deep channel's flow area or flatten it to the banks? Flatten → targeted **L4
  (12.5 m) refinement localized to the Rumson–SB narrows** (+ maybe upper Navesink) is THE experiment.
  Capture → resolution isn't the lever; look at subgrid formulation / filling dynamics.

## SUBGRID CONVEYANCE CHECK 2026-07-05 — FLATTENING CONFIRMED at the narrows → refinement is the lever
Read the u/v-point conveyance tables in `sfincs_subgrid.nc` by location. **How to map npuv→coords (non-obvious):**
the subgrid `npuv` order is NOT mesh-edge order (corr 0.0). It's SFINCS's own u/v construction — replay the
loop in `hydromt_sfincs/components/quadtree/subgrid_quadtree_builder.py` (~L181): iterate cells `ic`, emit a
uv-point per `mu1/mu2/nu1/nu2>=0` (u-points then v-points, `direc` 0=x/1=y); uv coord = midpoint of
face_x/y[ic] and face_x/y[neighbor]. From `sfincs.nc`: mu/nu (flags), mu1/mu2/nu1/nu2 (1-based nbr idx, −1=none).
Verified: corr(uv_zmin, min-adjacent-cell-z)=**0.999**. (Vars: uv_zmin/uv_zmax, uv_havg(npuv,levels; lvl9=high
stage), uv_navg=Manning.)
**RESULT — the narrows faces flatten the channel out:** flow-facing (N-S) faces through the Rumson–SB narrows:
deepest crossing face only **−2.5 m**, just **3% deep (<−2 m)**, 97% sit at **+1.5 m with marsh Manning 0.041**.
Vs the deep channel behind the barrier: faces to −5.2/−7.7 m, 48% deep, n=0.020. The eHydro channel (carved
−4.65 m, dep pixels −6.6 m — confirmed IN the cells) is NOT on the conveyance faces: SFINCS routes the surge
into the Shrewsbury over a ~−2.5 m marsh sill, 2–4 m too shallow → throttles the fill. Classic 25 m-cell
thalweg-misalignment → **local L4 (12.5 m) refinement is the indicated fix.**
**CAVEAT (don't overclaim):** connectivity is BRAIDED — the barrier-side deep channel (−5.2 m faces, n=0.02) is
well-represented and offers a parallel Navesink↔Shrewsbury path, yet the Shrewsbury still under-fills → refining
the narrows is LIKELY-not-CERTAIN to close the gap; the system may be throttled at multiple points. TEST it.
**THE EXPERIMENT:** targeted L4 refinement localized to the Rumson–SB narrows (+ screen upper Navesink the same
way) → Phase-1 rebuild → rerun snapwave_tuned → check Shrewsbury fill + HWM/MOTF. Bounded (local, not global).

## STAGED 2026-07-05 (uncommitted; user does git) — L4 refinement + gauge metric, NOT yet rebuilt
- **`data/quadtree/refinement_polygons.geojson`**: added 2 polygons `shrewsbury_l4` + `navesink_l4`, both
  `refinement_level=4` (→ 12.5 m; base_res 200/2^4), bed-gate `zmin=-8, zmax=+1` (refines only channel+intertidal).
  Boxes (lon/lat): shrewsbury_l4 = (-74.025,40.315,-73.970,40.375) [S arm + Rumson-SB narrows + confluence];
  navesink_l4 = (-74.075,40.345,-73.975,40.410) [W arm → Red Bank]. L4 IS supported (quadtree.py:362-369
  `for lev in range(max(levels))`, no cap).
- **`nj_sfincs/validate.py`**: new `shrewsbury_gauge_peak(mod)` metric (wired into `evaluate()` list) — compares
  modeled peak at obs pt `usgs_tidal_sea_bright` to the 01407600 crest **2.935 m NAVD88**. Baseline (current 25 m
  snapwave_tuned) = mod 2.223 → **err −0.712 m**; refinement should push toward 0.
- **⚠️ REBUILD REQUIRED — the polygon edit is INERT until the frozen mesh is regenerated.** `BaseConfig.frozen_mesh`
  defaults to `data/frozen_mesh` (config.py:60) and `build_static` (model.py:62) COPYTREES it + skips the build. So
  the harness would reuse the OLD 25 m mesh and ignore L4. **A/B path:** `python scripts/freeze_mesh.py
  data/frozen_mesh_L4` (builds with the new polygons; freeze uses frozen_mesh=None so it actually BUILDS; ~CPU peak,
  do on Amarel) → point the refinement run's `frozen_mesh` at `data/frozen_mesh_L4` (keep old 25 m dir for the
  baseline) → rerun snapwave_tuned → compare `shrewsbury_peak_err_m` (−0.712 → ?) + Shrewsbury MOTF. Needs a small
  config/runner tweak to select the L4 mesh per-run (not yet made).

## LAUNCHED 2026-07-05 (Amarel halk0029) — L4 mesh BUILT + snapwave_tuned run SUBMITTED
- Added `NJ_FROZEN_MESH` env override to config.py (relative-to-ROOT or absolute; mirrors NJ_ROOT).
- **L4 mesh BUILT → `data/frozen_mesh_L4/`** (283 s). Cmd: `PYTHONPATH=<repo-root> python scripts/freeze_mesh.py
  data/frozen_mesh_L4` (freeze_mesh.py lives in scripts/ → NEEDS PYTHONPATH=repo-root or `import nj_sfincs` fails).
  **672,103 cells (+124,836 / +23% vs 547,267)**; new finest tier level-5 = 12.5 m (159,612 cells); narrows +
  upper Navesink confirmed at 12.5 m; no OOM (bed-gate contained growth).
- **Baseline preserved:** `experiments/snapwave_tuned_25m/` + `experiments/metrics_25m.csv` (shrewsbury_err −0.712).
- **RUN SUBMITTED = SLURM job 57864095**: `sbatch --export=ALL,NJ_FROZEN_MESH=data/frozen_mesh_L4
  hpc/run_experiments.slurm --experiments snapwave_tuned --rebuild-template` (main-redhat PREEMPTIBLE/requeue, 32c).
  ⚠️ `--rebuild-template` MANDATORY — `template_matches()` stamps only the WINDOW, not the mesh, so without it the
  run silently reuses the 25 m template. Log `logs/sweep_57864095.out`. SUCCESS TEST: modeled peak at obs pt
  `usgs_tidal_sea_bright` climbs 2.223 → toward 2.935; Shrewsbury MOTF blue shrinks. (sbatch job = harness can't
  auto-notify; poll squeue/log.)
- Uncommitted (user does git): refinement_polygons.geojson (+2 L4 polys), config.py (NJ_FROZEN_MESH env),
  validate.py (shrewsbury_gauge_peak metric).

## RESULT 2026-07-05 — L4 refinement FAILED to help (negative result; narrows resolution NOT the lever)
Job 57864095 COMPLETED (2h08m, rc=0; log confirms it used data/frozen_mesh_L4). A/B snapwave_tuned L4(12.5m) vs
25m baseline: Shrewsbury gauge peak **2.223→2.265 (+0.042 m; still −0.670 vs obs crest 2.935)**; MOTF CSI
0.506→0.509 (+0.003 = WITHIN the ±0.02 mesh-reproducibility noise floor); HWM bias −0.090→−0.051 (+0.039);
within0.5 + n_dry unchanged. **Interpretation: refining the Rumson–SB narrows + upper Navesink to 12.5 m nudged
the whole surface ~4 cm but left ~0.67 m of the in-river deficit — narrows resolution is NOT the dominant lever.**
The BRAIDED-CHANNEL caveat was decisive: the parallel barrier-side deep channel already conveyed, so sharpening
the narrows opening unlocked little. **NOW RULED OUT for the in-river deficit: forcing/boundary (delivery
confirmed on instruments), eHydro carve (in subgrid), narrows resolution (this test).** Remaining candidates:
channel Manning/friction; distributed/whole-basin filling limit; subgrid conveyance formulation; or ~0.67 m at
the gauge / CSI ~0.51 is near this config's skill ceiling. Cheap next diagnostic BEFORE more compute: re-run the
uv_havg check on data/frozen_mesh_L4 at the narrows — if 12.5 m faces NOW capture the deep channel yet WL didn't
rise → narrows was never the bottleneck (accept/redirect); if faces STILL flattened at 12.5 m → thalweg sub-12.5 m
(finer = diminishing returns). Keep `data/frozen_mesh_L4` + `experiments/snapwave_tuned` (L4) + `_25m` baseline.

## WHY L4 FAILED (uv check on L4 mesh, 2026-07-05) — narrows was NEVER the choke; earlier "flattening" read corrected
Re-ran the uv_havg/uv_zmin check on `experiments/snapwave_tuned` (L4). Narrows v-faces (N-S flow) are
RESOLUTION-INVARIANT: deepest crossing face **−2.5 m at BOTH 25 m and 12.5 m** (unchanged), 3%→5% deep, deep-face
Manning 0.020 both. So −2.5 m is REAL, not a resolution artifact. **KEY REINTERPRETATION: −2.5 m is deep ENOUGH —
with ~3 m surge at the mouth that's ~5.5 m of water over the sill = ample conveyance.** My earlier subgrid-
"flattening→under-conveyance" read (the 97% marsh faces) was INCOMPLETE: it ignored that a −2.5 m sill under a 3 m
surge isn't a choke. **The Rumson–SB narrows (and Highlands entrance, both covered by the L4 polys) was NEVER the
bottleneck** → that's why L4 did nothing. **DEFICIT IS DISTRIBUTED, not a fixable geometric feature.** Model drops
1.4 m ocean→gauge vs reality's 0.53 m — whole-estuary over-attenuation. Remaining candidates (untested): channel/
marsh Manning/friction (much of the fill path is n=0.04 marsh); filling timescale (large tidal prism vs surge
duration); subgrid conveyance formulation; OR ~0.67 m gauge deficit / CSI ~0.51 ≈ this config's skill ceiling.
NEXT (if pursued): a Manning sensitivity (lower channel/marsh n → faster fill) is the one remaining cheap-ish lever
but needs a subgrid rebuild. Otherwise: accept the level (forcing+carve+resolution all excluded) and write it up.

## FILL-TIMESCALE CHECK 2026-07-05 (#3) — estuary is OVER-DAMPED vs obs → friction IS a real lever (flips "accept")
Shrewsbury gauge (01407600) modeled-vs-observed: **peak timing SYNCHRONOUS** (interior peaks −0.2 h from ocean →
NOT a slow-fill lag), but **amplitude OVER-DAMPED: modeled pre-storm tidal range 0.91 m vs observed 1.54 m
(ratio 0.59)**. So the residual is a genuine conveyance OVER-RESTRICTION, NOT the skill ceiling — reality got
1.54 m of range at that spot, the model only 0.91 m. Mechanism = amplitude damping from too much flow resistance,
distributed (synchronous peak rules out a fill lag). **We HAVE observed calibration targets (tidal range 1.54 m,
crest 2.935 m) → a Manning sensitivity is GROUNDED, not curve-fitting. This FLIPS the earlier "accept the ceiling"
lean → friction is the motivated next lever.** Caveats: (1) model range from HOURLY map output undersamples tidal
peaks → 0.59 is a slight underestimate, true ~0.63, still over-damped; (2) over-damping may also be the subgrid
under-representing channel CROSS-SECTION (few deep uv faces) not only Manning → lowering n may only partly close it.
**BUG found: the `usgs_tidal_sea_bright` obs point lands on a +1.46 m BANK cell, not the −4.35 m channel 33 m away**
→ its tidal signal is dry-at-low-tide (range 0.000, artifact) and even the crest metric reads a bank. FIX: move the
obs point into the channel cell (model.py val_gauges) before trusting the his-based gauge metrics; the map channel-
cell sampling used here is the correct read meanwhile.

## MANNING AUDIT 2026-07-05 — friction is NOT the lever → tractable levers EXHAUSTED → accept the ceiling
Sampled subgrid Manning by depth in the estuary (496k pixels; reclass OpenWater=0.020, Barren=0.040,
EmergentWetland=0.045, WoodyWetland=0.140). **Deep channel (<−2 m): median n=0.020, 98% open-water; channel
margin: 0.020, 85%.** The conveyance channels are ALREADY at the open-water floor — can't defensibly go lower.
High n (0.045+) is confined to intertidal/low-marsh/bank (real wetlands, physically correct). **So no defensible
Manning change reduces the over-damping — friction is NOT the lever.** 
**VERDICT: tractable levers EXHAUSTED** — excluded forcing/boundary (delivery), eHydro carve (in subgrid),
resolution (L4 test), friction (this audit). The over-damping (0.91 vs 1.54 m range) is a conveyance CROSS-SECTION
under-representation (few deep uv faces / thin channel) that our knobs don't fix (resolution didn't, Manning can't).
Remaining causes are STRUCTURAL + uncertain: subgrid narrow-channel conveyance formulation, or eHydro dredged-ribbon
narrower than the real 2012 channel — both diminishing returns, not clean tunes. **RECOMMENDATION = ACCEPT THE
CEILING & WRITE UP.** It's a STRONG result now, not a shrug: delivers surge correctly, carve restored the channel,
captures ~60% of interior tidal range, within ~0.67 m of the in-river crest, with forcing/bathymetry/resolution/
friction SYSTEMATICALLY EXCLUDED as the residual's cause — the elimination IS the contribution. Loose end worth
tidying regardless: move the `usgs_tidal_sea_bright` obs point off the +1.46 m bank cell into the −4.35 m channel.

## SHREWSBURY HWM VERDICT + obs-fix DONE 2026-07-05
- **L4 run vs the 5 HWMs IN the Shrewsbury River** (box lon −74.02..−73.965, lat 40.315..40.366): **bias −0.55 m,
  RMSE 0.90 m, 0% within 0.5 m** (residuals −0.96/+0.82/−1.09/−0.99/−0.51). Model UNDER-floods the Shrewsbury by
  ~0.55 m (up to ~1 m); one over-pred outlier (obs 2.90→mod 3.72, near the barrier). Corroborates the conveyance
  deficit on INDEPENDENT physical evidence (HWMs, not MOTF) — consistent with the −0.67 m gauge-crest deficit +
  tidal over-damping. Small n=5.
- **obs-point FIX SHIPPED** (model.py val_gauges): `usgs_tidal_sea_bright` moved −73.9747,40.3656 → **−73.97494,
  40.36557** (21 m, into the −4.2 m channel cell; was a +1.46 m bank). Takes effect on the NEXT rebuild (obs pts
  written to sfincs.obs in build_static); existing runs still have the bank obs pt (worked around by map channel-cell
  sampling). Uncommitted.
- **AMAREL GPFS METADATA DEGRADED 2026-07-05 (cluster-wide, both halk0029+halk0127):** ~66 ms/file-op (vs <1 ms),
  env-python start 8.5 s, full xarray+geopandas+hydromt import → minutes → Jupyter kernel "timeout waiting for ports"
  + Bash timeouts. Bulk read fine (240 MB/s). New node did NOT fix (it's the metadata server) → report to OARC; work
  is safe on GPFS. **WORKAROUND that got analysis through: drop xarray+geopandas, use `netCDF4`+`numpy`+`pyproj` +
  parse geojson via plain `json` (lean imports ~37 s vs timeout).**
- **GAUGE CREST PROVENANCE RESOLVED 2026-07-05:** NWIS has NO through-peak data at 01407600 for EITHER param
  72279 (NAVD88) OR 00065 (gage height) — both telemetry streams died in-storm (checked all access levels 0/1/2).
  The 11.73 ft MLLW crest is a lone entry in the NWS **historic-crests table** = a POST-EVENT peak determination
  (surveyed HWM or recovered logger reading at the station — USGS's big post-Sandy HWM/storm-tide survey campaign),
  NOT a served hydrograph. → **Forcing the Shrewsbury with the gauge is DATA-BLOCKED** (no time series exists),
  independent of the prediction→prescription objection. The crest = a high-quality HWM AT the gauge (2.935 m NAVD88,
  consistent with surrounding Shrewsbury HWMs 2.9–3.5 m) → validation anchor only. A recovered hydrograph *might*
  exist in a USGS Sandy data release (OFR 2013-1043/ScienceBase) but low-probability given the crests-table form;
  not worth chasing. **THREE independent, agreeing deficit measures: crest −0.67 m, tidal range 0.91 vs 1.54
  (over-damped), Shrewsbury HWM bias −0.55 m.**

## IN-RIVER GAUGE CREST = new validation anchor (2026-07-05, user-supplied)
USGS **01407600 Shrewsbury R @ Sea Bright** recorded a historic **crest 11.73 ft MLLW** on 2012-10-29
(NWS flood-impacts page). Our downloaded series (`data/gtsm/usgs_sandy_tidal_nj.nc`, NWIS param 72279
NAVD88) DIED 10-29 03:54 at 4.54 ft/1.38 m — telemetry knocked out ~19 h BEFORE the peak, so we did NOT
have the crest. NWIS has only param 72279 for this site (no gage-height/MLLW param); the crest comes from
the NWS/recovered peak, not the IV feed. In-river STN Sandy sites (7332/7333/7345 Shrewsbury, 7326/7331
Navesink) are HWM-ONLY (0 continuous sensors — already in our HWM set); the only continuous SSS is
open-coast Monmouth Beach (=our `sandy_storm_tide_nj` 2258/2259).
**Datum: it IS MLLW (user confirmed the label; my NAVD88 guess was WRONG).** VDatum geoid18 at
(-73.9747,40.3656): MLLW is −0.640 m below NAVD88 → **crest = 2.935 m NAVD88**.
**Model deficit (instrument-grade):** model peak at that gauge (his `usgs_tidal_sea_bright`) = 2.223 m →
**under by 0.71 m.** Two-anchor reframe: obs head-loss ocean(SSS 3.465)→gauge(2.935) = 0.53 m; model
3.64→2.22 = 1.42 m → **model over-attenuates by ~0.9 m** into the river = the conveyance deficit on
INSTRUMENTS. **This MODERATES the magnitude: honest near-inlet deficit ~0.7–0.9 m, NOT the ~1.3 m HWM-median
figure** — the Navesink/Shrewsbury HWMs (median 3.23, max 4.6) run ABOVE the still-water gauge crest (wave
runup/debris bias) → trust the gauge. Deficit still GROWS inland (upper Navesink→~0). TODO: add 01407600
crest (2.935 m NAVD88) as a "Shrewsbury gauge peak" metric in validate.py; check if USGS recovered the
onboard hydrograph (continuous would add range+timing). This is THE number to judge the narrows-refinement
experiment (does modeled peak climb 2.22→~2.94?).

## Diagnostic wired into the notebook (2026-06-12)
Added a "Diagnostic: bridges baked into the bed as dams" markdown + **interactive hvplot** cell (of `dep_subgrid_lev3.tif`) just before the end-of-notebook status section, for the supervisor meeting.

## Method note (reusable)
`dep_subgrid_lev3.tif` is on the **ROTATED** model grid. De-rotate before clip/plot/transect: `da.rio.reproject(da.rio.crs, resolution=3.0, resampling=Resampling.min)` — `min` keeps the deepest sub-pixel so genuine channel openings survive (don't mask a real opening as a dam). For TRUE wall heights use `resampling=nearest`.

Related: project_validation_roadmap (memory retired 2026-07-25), project_wavemaker_run (memory retired 2026-07-25), project_mask_boundary_cleanups (memory retired 2026-07-25), [[project_nj_sandy]].

---

## SESSION SYNTHESIS / HEAD STATE 2026-07-05 (the zoom-out — read this first)
**The back-bay/Shrewsbury under-prediction investigation is COMPLETE.** Premier model = `snapwave_tuned`
(wind-wave growth + Tim's SnapWave physics); IG pinned; wavemaker = over-forcing diagnostic only.
**Systematic elimination of the ~0.5–0.7 m in-river deficit — ALL tractable levers excluded:**
1. surge forcing / boundary → NOT it (delivery to the mouth confirmed on the Sea Bright storm-tide instrument).
2. bridge-dam / eHydro carve → in place (100% of channel pixels carved in the subgrid).
3. mesh resolution at the narrows → NOT it (L4 12.5 m rebuild moved the gauge only +0.04 m; uv conveyance faces
   are resolution-invariant at −2.5 m, which is deep enough under a 3 m surge — the narrows was never the choke).
4. channel friction / Manning → NOT it (channels already at open-water 0.020; high n is real marsh, defensible).
**Residual = a DISTRIBUTED conveyance over-restriction near the model's STRUCTURAL CEILING** (estuary over-damps:
interior tidal range 0.91 vs obs 1.54 m, synchronous peak so not a fill-lag). Cause is the subgrid's representation
of the narrow channel cross-section and/or the eHydro dredged-ribbon being narrower than the real 2012 channel —
neither a clean tune; diminishing returns. **THREE independent, agreeing deficit measures: gauge crest −0.67 m,
tidal over-damping, Shrewsbury HWM bias −0.55 m.** Gauge-forcing idea = data-blocked (post-event surveyed peak,
no hydrograph) AND would be prediction→prescription.
**RECOMMENDATION: this is a STRONG, honest result — accept & write up. The systematic exclusion IS the
contribution** (model delivers a historic surge correctly, carve restored the channel, lands ~0.5 m low through a
fully-isolated conveyance limit). Lead validation with the gauge + HWM + tidal-range trio, NOT MOTF/CSI.
**Open next-step (user to steer): what's the deliverable/audience (paper / thesis chapter / Tim)?** — that decides
finalize-and-document vs. preempt-a-specific-reviewer-question. The only remaining physical probe (advised against):
is the eHydro ribbon narrower than the real 2012 channel.
**Infra caveat during this session: Amarel GPFS metadata was degraded cluster-wide (Python/Jupyter startup taking
minutes) — see the "GPFS METADATA DEGRADED" note above for the lean-import workaround.**
