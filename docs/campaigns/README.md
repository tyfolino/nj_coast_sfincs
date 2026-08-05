# Campaign records

One dated markdown per investigation, moved out of the Claude memory store on 2026-08-05.

**These are histories, not statements of current fact.** Each is a reverse-chronological
log: blocks were appended newest-first, and later blocks supersede earlier ones — including
where an earlier block calls itself current. Several conclusions in here were retracted
outright. The retraction always sits above the claim it retracts, and every file carries a
header saying so.

They live in the repo (rather than in memory) precisely *because* they contain superseded
text. Memory is loaded into every session as if it were current; a git-tracked doc is
expected to be historical. For what is believed true now, see `CLAUDE.md`, `docs/naming.md`
and the memory store.

## Root causes found

| doc | what it establishes |
|---|---|
| `2026-06_bridge_dam.md` | The Rumson–Sea Bright causeway is baked into the 10 ft lidar as a solid earthen dam across the Shrewsbury narrows. Fixed by an eHydro channel survey, not by burning. |
| `2026-07_shrewsbury_underfill.md` | The full Shrewsbury under-fill re-investigation (Workstreams A–M). |
| `2026-07_shrewsbury_reinvestigation.md` | ⭐ The headline: the under-fill was a **mass leak** — `region.geojson` cut the Navesink mid-channel, giving it a free-outflow BC that drained 92.5% of estuary inflow. Plus a second dam at Shark River Inlet, where green lidar returned the water surface. |
| `2026-06_snapwave_root_cause.md` | SnapWave X1/X2 blow-ups: boundary points outside the mesh → depth 0 → runaway waves. |
| `2026-06_hm0_spike_rootcause.md` | Surf-zone hm0 spikes = GEBCO integer bathymetry filling nearshore NoData; offshore zs spikes = the 2dx boundary ring. |
| `2026-07_inlet_waterlevel_clamp.md` | 🔴 `mask_zmin=-10` put the open-ocean water level **2.6 km inside Barnegat Inlet**, 75 m from the gauge. Every v2 run before 07-30 is affected. |
| `2026-07_hwm_estimator_artifact.md` | 🔴 The HWM score measured the search *window*, not the model. `max(WSE)` over ±50 m is unbounded in radius; the v1→v2 "regression" was not real and the ranking inverted. |

## Levers tested

| doc | verdict |
|---|---|
| `2026-07_tidal_phase_lag.md` | `tide-shift` — advance the Battery anchor's tide +24 min. Phase fixed at no level cost. Both composites retired. |
| `2026-07_snapwave_decoupling.md` | `wave-deep30` — the premier imposes Hs above the depth-limited breaking cap, i.e. a physically inadmissible BC. Best level arm, worst extent arm: a real trade. |
| `2026-07_ehydro_carve_and_district_sign.md` | The eHydro carve was the best arm on bias, RMSE and CSI at once — and it was predicted to be a null. Also: the district sign-convention flip. |
| `2026-07_infragravity_closed.md` | ⛔ A null lever, **not** an instability. The old "IG caused blow-ups" verdict came from a pre-sealed run with a solver bug. |
| `2026-07_cora_evaluation.md` | CORA rejected for water level (tide late, levels low) but adopted as the **wave** boundary — admissible at 7/7 support points vs ERA5's 1/7. |
| `2026-06_manning_nj.md` / `2026-06_coned_upgrade.md` | NLCD→Manning reclass; the pre-Sandy 1 m topobathy elevation stack. |
| `2026-08_bracket_manahawkin.md` | The bracket pattern — bounding a quantity with a deliberately **inadmissible** domain. One 2:46 run replaced a 1.4 M-face rebuild. |

## Domain history

`2026-07_domain_rebuild.md` (leak fixed at its root, premier selected) ·
`2026-07_domain_expansion_v2.md` (the southern lobe to Barnegat Inlet) ·
`2026-07_bay_tidal_amplification.md` (why interpolating between two outside gauges cannot
produce an interior maximum).

## Open threads at the time of the move

`2026-08_bay_volume_deficit.md` — the bay defect is a **cumulative volume deficit**, not a
gradient or phase error. Corrects an earlier same-day claim that the gradient was inverted;
that was an artefact of comparing peak-to-peak across two different times.

`2026-08_wind_forcing.md` — ERA5's magnitude is good over open water but it diagnoses the
bay through land roughness. Weakened, not confirmed: RTMA at 2.5 km shows the same
reduction, so it may be physical (4–6 km fetch).

`2026-08_sandy_hook_gap.md` — the Sandy Hook gauge really does stop at landfall. But you
can score a reconstruction at Battery and Atlantic City, which flank it and survived.

`2026-08_usgs_bbleh_coawst.md` — USGS ran a COAWST model of this bay for Sandy, open on
OPeNDAP, carrying a wind field blended from the in-bay anemometer.

`2026-08_published_boundary_practice.md` — how the published SFINCS studies actually set
the water-level boundary: they **draw** it, rather than generating it from a depth rule.

`2026-06_bay_waves_plan.md` — SnapWave cannot diffract swell into the Sandy Hook Bay lee.
