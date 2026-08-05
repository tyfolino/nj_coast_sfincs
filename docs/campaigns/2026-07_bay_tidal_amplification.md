<!-- Campaign record. Moved out of the Claude memory store 2026-08-05; the
     memory file was `reference_bay_tidal_amplification`. -->

> **Historical record — read top-down, newest first.** Blocks are appended in
> reverse chronological order and later blocks SUPERSEDE earlier ones, including
> where an earlier block calls itself current. Several conclusions in here were
> retracted; the retraction is always above the claim it retracts. For what is
> believed true *now*, see the memory store and `CLAUDE.md`, not this file.
>
> **Standing summary at the time of the move:** NOAA published datums prove Raritan/Sandy Hook Bay amplifies the tide 12-15% above Battery — and the Battery↔AC boundary interpolation STRUCTURALLY cannot represent it. Tide amplification is observational (no CORA needed); SURGE amplification is unobserved.


# Bay tidal amplification — measured, not assumed (2026-07-25)

## The numbers (NOAA published datums, `mdapi/prod/webapi/stations/<id>/datums.json`, MN = mean range)

| station | id | MN | vs Battery |
|---|---|---|---|
| Atlantic City (open coast) | 8534720 | 1.225 m | 0.89× |
| Battery (NY Harbor) | 8518750 | 1.381 m | 1.00× |
| Sandy Hook (bay entrance) | 8531680 | 1.433 m | 1.04× |
| **Highlands (Sandy Hook Bay)** | 8531545 | **1.539 m** | **1.12×** |
| **Keasbey (Raritan River)** | 8531262 | **1.588 m** | **1.15×** |

Cross-check: Battery's *predicted* range in the Sandy window is 1.633 m ⇒ Keasbey implies
1.878 m, vs the 1.843 m recorded independently in [[project_cora_evaluation]]. 2% apart.

## 🔑 THE STRUCTURAL POINT
The north-lobe boundary interpolates between **Battery (1.38) and AC (1.23) — BOTH LOWER than
the bay interior.** **Linear interpolation between two points outside the bay cannot produce an
interior maximum.** This is not a tuning error; the geometry cannot express the amplification at
all. North lobe runs **~15% under-forced in tidal range** (memory's earlier "11–15%" ✅ confirmed).

## What this changes about the deferred Raritan Bay item
- **The TIDE half needs NO new dataset.** The datums give the amplification observationally
  (1.12× / 1.15×), which beats CORA — CORA runs 0.14–0.31 m LOW and 13–14 min LATE. Apply a
  local scale at the north lobe with the same "keep the NTR, change only the tide" construction
  as `noaa_sandy_phaseshift` ([[project_tidal_phase_lag]]).
- **The SURGE half is the real gap.** No NOAA/USGS gauge exists inside Raritan Bay (Sandy Hook
  8531680 is at the ENTRANCE; `sandy_storm_tide_nj` + `usgs_sandy_tidal_nj` are all south/east).
  **Do NOT apply the tidal ratio to the surge** — surge is a much longer-period wave and the
  bay's response differs. This is where a spatially complete product (bias-corrected CORA or
  ADCIRC-class) genuinely earns its keep: take **RATIOS, not values**, so the level bias cancels.

## ⚠️ Two cautions before acting
1. The premier's `sandy_hook_bay` HWM bias is only **+0.09 over 2 HWMs** — the model is not
   visibly broken there, likely because Sandy's peak was surge-dominated (NTR 2.79 m vs tidal
   range ~1.6 m).
2. Given the **×3–9 threshold amplification** ([[project_tidal_phase_lag]]), "small boundary
   error" does NOT imply "small interior consequence", in either direction. **Reconstruct the
   imposed boundary at the north lobe and measure the amplification factor before deciding
   whether this matters.**

## API notes
Subordinate stations (Keasbey 8531262, Perth Amboy 8531002, Bergen Pt 8519483) return **no
`predictions` time series** for 2012 — use the **datums** endpoint for them, not `datagetter`.
Only the primary stations (8518750 / 8531680 / 8534720 / 8536110) serve prediction series.
