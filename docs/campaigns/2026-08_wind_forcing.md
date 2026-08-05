<!-- Campaign record. Moved out of the Claude memory store 2026-08-05; the
     memory file was `reference_wind_forcing_investigation`. -->

> **Historical record — read top-down, newest first.** Blocks are appended in
> reverse chronological order and later blocks SUPERSEDE earlier ones, including
> where an earlier block calls itself current. Several conclusions in here were
> retracted; the retraction is always above the claim it retracts. For what is
> believed true *now*, see the memory store and `CLAUDE.md`, not this file.
>
> **Standing summary at the time of the move:** ERA5 wind is GOOD over open water (verified vs 3 buoys). It does diagnose Barnegat Bay through land roughness — but RTMA at 2.5 km shows the SAME bay/ocean reduction, so the reduction may be PHYSICAL. Wind hypothesis weakened, not confirmed. Charnock-from-u* method is dead.


# Wind forcing over Barnegat Bay — investigated 2026-08-03

## ✅ ERA5's wind MAGNITUDE over open water is right

Verified against `data/wind/sandy_wind_obs.nc` (new). Peak ratios ERA5/observed:
**44025 1.009, 44009 0.958, 44065 1.059**; medians at U>12 m/s: 0.962 / 0.915 / 0.979.
⇒ **"ERA5 is too weak" is FALSE as a blanket claim.** Do not repeat it.

## ✅ ERA5 DOES diagnose the bay through a land surface

From `data/era5/era5_nj_sandy_sfc.nc` (new: `zust`, `fsr`, `lsm`):

| | land fraction | surface roughness (storm max) |
|---|---|---|
| cells over Barnegat Bay | 0.26–0.90 | **0.195–0.983 m** |
| genuine ocean cells | 0.000 | **0.003–0.006 m** |

50–250× the marine roughness. The mechanism is real.

## ⚠️ BUT RTMA DOES NOT CONFIRM THE WIND HYPOTHESIS — this is the correction

RTMA (2.5 km, observation-assimilating, resolves the bay far better than ERA5's 28 km)
was obtained for the exact Sandy window. **Bay/ocean wind ratio:**

| source | bay/ocean |
|---|---|
| ERA5 (28 km) | 0.77–0.81 |
| **RTMA (2.5 km)** | **0.59–0.90** |

RTMA shows the **same reduction, if anything stronger**. So the reduced over-bay wind
may be **PHYSICAL** — Barnegat Bay is a narrow lagoon with land on both sides and a
4–6 km fetch, so the internal boundary layer never equilibrates. Two products agreeing
is weak-to-moderate evidence for that (not independent: RTMA's downscaling also uses
land characteristics).

⇒ **The wind lever is weaker than the 2026-08-03 morning diagnosis claimed.** If the bay
wind is right, the 45% tilt shortfall must come from bay friction (Manning), bay depth,
or the southern connection — which makes the **Manahawkin bracket more important**.
⇒ **What would settle it: an IN-BAY wind observation.**
✅ **FOUND 2026-08-04 — and it needs no download.** The USGS COAWST/ROMS Sandy run for
this exact bay is open on OPeNDAP with `Uwind_eastward`/`Vwind_northward` half-hourly
over lat 39.44–40.14 (both interior gauges inside), and its forcing is NARR
**supplemented with the in-bay Barnegat Light anemometer**. Endpoint, caveats and the
anemometer routes that DON'T work are in [[reference_usgs_bbleh_coawst]].
⚠️ Its base is NARR at 32 km, so it is a THIRD opinion, not a tiebreaker by construction
— RTMA already reproduced ERA5's reduction.
🔎 Also confirmed: the Barnegat Light station was **operating** through Sandy (NJ State
Climatologist lists a 79 mph peak gust there, Tuckerton 88 mph) — it was never off or
destroyed; only the public NWIS API refuses to serve 2012. NJWxNet's portal is
JS-driven with no open API found; the State Climate Office is +1 (848) 932-5706.

## ❌ DEAD METHOD: Charnock re-diagnosis from ERA5's own u*

`nj_sfincs/wind.py` implements it; it **fails its own falsifier** (1.06–1.11 at the
buoys, must be 1.00). Root cause is the premise, not the code: **ERA5's `u10` is NOT the
neutral log-law wind implied by its own `zust` and `fsr`.**

| | ERA5 `u10` | log-law from its u*, z0 |
|---|---|---|
| ocean buoy | 16.19 | 18.21 |
| bay cell | 14.14 | **6.85** |

Effective roughness ERA5 actually used: **0.0028 m ocean vs 0.0298 m bay** — a 10×
difference, not the 350× that `fsr` implies. Keep the module for the record, but do not
build an arm on it without fixing the premise.

## 🧰 Access notes

- **RTMA on AWS (`noaa-rtma-pds`) starts 2013-03-19** — five months after Sandy. Useless here.
- **Google Earth Engine `NOAA/NWS/RTMA` covers 2011+** and HAS our window: 96 hourly
  images 10-28 00:00 → 10-31 23:00, **zero gaps**. Bands incl. `UGRD`/`VGRD`.
- EE project **`ee-tpj8`**; creds at `~/.config/earthengine/credentials` (on `/cache`, so
  they survive preemption). `earthengine-api` installed in the **repo** micromamba env —
  ⚠️ NOT the node-local `/tmp` python, which is rebuilt per node.
- Three separate activation steps, all required: create project + **enable the EE API** +
  **register the project** for Earth Engine. Enabling ≠ registering.
- Ruled out: CORA (no meteo in bucket), CHS/NACCS (DoD portal, no anon access),
  HWRF/HAFS/NAM/RAP buckets (none reach 2012), HRRR (2014+), NARR/CFSv2/MERRA-2 (coarser
  than the problem), ERA5-Land (land only).

## 🐛 THREE SILENT-NaN BUGS IN ONE DAY — all the same shape

Each printed correct numbers to the console while writing garbage to disk:

1. **Latitude flip** — new ERA5 file written ascending, wind file is descending. Passed a
   **size-only** assertion (21 == 21). ⇒ **checking shape is not checking alignment; compare
   coordinate VALUES.**
2. **pandas index alignment** — building a DataFrame from Series with a RangeIndex against
   a datetime index silently aligned everything to NaN. ⇒ use `.to_numpy()`.
3. **NDBC reports at :50 past the hour** — reindexing onto a 6-minute grid dropped every
   row (50 is not a multiple of 6). ⇒ use the union of the stations' OWN timestamps,
   never an invented grid.

Related: [[reference_bay_volume_deficit]], [[project_handoff_2026_08_03]].
