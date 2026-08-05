<!-- Campaign record. Moved out of the Claude memory store 2026-08-05; the
     memory file was `project_bay_waves_plan`. -->

> **Historical record — read top-down, newest first.** Blocks are appended in
> reverse chronological order and later blocks SUPERSEDE earlier ones, including
> where an earlier block calls itself current. Several conclusions in here were
> retracted; the retraction is always above the claim it retracts. For what is
> believed true *now*, see the memory store and `CLAUDE.md`, not this file.
>
> **Standing summary at the time of the move:** Plan for getting waves into Sandy Hook Bay (SnapWave no-diffraction lee) — wind growth first, then IG, wavemaker-in-bay is a trap


**Problem (2026-07-01):** SnapWave does refraction+shoaling but NO diffraction, so Atlantic swell cannot wrap around the Sandy Hook spit into the bay lee. Verified from the incident-only run: Sandy Hook Bay interior Hm0 ~0.01 m (clean shadow); only the inlet gap leaks (Hm0 ~1.7–8 m); NW "fan" is 0.15–1.3 m colormap-stretched noise. Water levels fine (gauges 3.1/3.6/2.1/1.3 m).

**Sequenced plan to fill the bay (one knob at a time):**
1. **Wind growth (knob 1) — DONE 2026-07-02, SUCCESS.** `wave_wind=True` -> `snapwave_wind=1` + `snapwave_sector=360` (full circle so wind-sea travels any direction). Physically-correct source for bay waves (short-fetch local wind-chop, not swell). **RESULT: bay filled with physical fetch-limited wind-sea** — Sandy Hook Bay interior Hm0 mean 0.01->0.26 m (max 1.95); larger Raritan Bay fetch -> up to 3.67 m (correct fetch dependence). BONUS: global Hm0 max 64.8->8.9 m (depth->0 surf-zone spikes resolved by the full 360 treatment). Gauges stable 3.15/3.59/2.29/1.28 (was 3.13/3.55/2.10/1.28) — tiny +0.19 m wind-setup, NO surge over-forcing. Vindicates skipping the bay wavemaker. Cost: ~3x runtime (14->~48 min; avg timestep unchanged 0.907s so it's pure wave-solver cost, not CFL; SnapWave sweep parallelizes poorly ~12/64 cores). Speed dials for next iter: `dtwave` 1800->3600, set `snapwave_dtheta` ~10-15.
2. **IG waves (knob 2)** — `snapwave_igwaves=1`. Long-period, penetrates deep into back-bays; the compound-flooding-relevant energy. **PINNED 2026-07-03:** sweep showed IG adds nothing over tuned wind waves (igwaves_wind 0.500 vs snapwave_tuned 0.506) and pure-IG is unstable (bay Hm0→6.9e9). Parked from the headline path — see project_experiment_harness (memory retired 2026-07-25) DECISIONS. Revisit only if compound-IG physics is later needed.
3. **Wavemaker** — only at the OCEAN-side barrier/inlet injecting IG. See project_wavemaker_run (memory retired 2026-07-25). **2026-07-03:** kept as a diagnostic/upper-bound experiment (over-forces → best CSI 0.557 for the wrong reason), NOT premier.

**User idea to evaluate tomorrow: wavemaker INSIDE Sandy Hook Bay. VERDICT: likely a trap.** It would force energy in, but prescribes the answer with no defensible spectrum — forcing Atlantic swell into a sheltered basin = over-forcing, exactly the dipole the Sea Bright barrier wavemaker already caused (+0.7–1.2 m HWMs, project_wavemaker_run (memory retired 2026-07-25)). Do wind growth + IG (physically-correct in-situ generation) FIRST; only use a wavemaker ocean-side for IG, not a swell wavemaker in the bay. See project_hydromt14_quadtree_session (memory retired 2026-07-25) for the harbor-boundary fix that unblocked all this, [[feedback_no_notebook_edits_during_run]] for edit timing.
