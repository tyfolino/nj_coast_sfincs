<!-- Campaign record. Moved out of the Claude memory store 2026-08-05; the
     memory file was `reference_usgs_bbleh_coawst`. -->

> **Historical record — read top-down, newest first.** Blocks are appended in
> reverse chronological order and later blocks SUPERSEDE earlier ones, including
> where an earlier block calls itself current. Several conclusions in here were
> retracted; the retraction is always above the claim it retracts. For what is
> believed true *now*, see the memory store and `CLAUDE.md`, not this file.
>
> **Standing summary at the time of the move:** USGS ran a COAWST/ROMS model of Barnegat Bay for Sandy and it is OPEN on OPeNDAP — including Uwind/Vwind over the whole bay, blended from NARR + the in-bay Barnegat Light anemometer. This is the in-bay wind observation the wind hypothesis needed, and its grid covers the proposed v3 southern lobe.


# USGS BBLEH COAWST run — an independent Sandy model of OUR bay, openly served

Found 2026-08-04 while chasing the in-bay anemometer lead from
[[reference_wind_forcing_investigation]].

## The endpoint

```
https://geoport.usgs.esipfed.org/thredds/dodsC/sand/usgs/Projects/BBLEH/run076/roms_his.ncml
```
Opens directly with `xarray.open_dataset(url)` — no auth, no download. (`run076` = the
"Storm" child item; there is also a `noSwell` sibling.)

| | |
|---|---|
| grid | ROMS, `eta_rho` 800 × `xi_rho` 160, 7 sigma layers |
| extent | lon **−74.437 … −74.003**, lat **39.444 … 40.141** |
| time | **2012-10-27T00:30 … 2012-11-14**, 864 steps (half-hourly) |
| wind | **`Uwind_eastward`, `Vwind_northward`** (m/s), on `(ocean_time, eta_rho, xi_rho)` |

ScienceBase parent `5ca38592e4b0b8a7f6333fb3`; storm child `5d05a22ae4b0e3d3115bd27c`.
Papers: Defne, Ganju & Moriarty 2019 (JGR Oceans, doi 10.1029/2019JC015238).

## ⭐ WHY IT MATTERS — it carries the in-bay wind observation

The data release says the air-sea forcing is NARR "**supplemented with wind speed data
from the U.S. Geological Survey weather station in Barnegat Light, N.J.**" So this wind
field ASSIMILATES the very anemometer that is otherwise unreachable (see below), over
exactly the water we care about. **Both interior gauges are inside the grid** —
Mantoloking 40.041 and Barnegat Light 39.761 vs a 39.444–40.141 extent.

⇒ The test for [[reference_wind_forcing_investigation]]: compare ERA5's bay/ocean wind
ratio (0.77–0.81) against this field's at the same cells. ⚠️ **Not automatically the
better product** — the base is NARR at 32 km, which puts land over the bay just as ERA5
does, and RTMA at 2.5 km already reproduced the same reduction. The value is that this
one is anchored to a real in-bay-adjacent measurement, so it is a THIRD independent
opinion, not a tiebreaker by construction.

## 🗺️ It also covers the proposed v3 southern lobe

The grid runs to **lat 39.444**, i.e. it spans Little Egg Harbor and Great Bay — the
whole region the southward expansion would add ([[reference_bracket_pattern]]). `zeta`
gives an independent water-level field there. ⚠️ Model-to-model agreement is weak
evidence; use it to sanity-check geometry and forcing, not to validate.

## ❌ The anemometer routes that DON'T work

- **USGS 394540074062901 "Barnegat Light USGS weather station NJ"** (39.7611, −74.1081,
  `site_tp_cd=AT`, `inventory_dt=20080827`). It was on the books in 2008 and USGS used
  its Sandy wind — it was **NOT off or destroyed**. But NWIS's public instantaneous-values
  service keeps only a **rolling 120 days** for atmospheric sites: the series catalog
  returns 2026-04-06…2026-08-04 and nothing else. The 2012 record exists inside USGS, not
  on the open API. Getting it means asking the NJ Water Science Center or the paper's
  authors — or just taking it pre-blended out of the ROMS file above.
- **JCRN4 / JCNERR Nacote Creek** (39.535, −74.464, 15-min, anemometer 12.5 m). The
  station WAS recording during Sandy (CDMO metadata `jacmet01-12.10m.pdf` returns 200),
  but CDMO's open WAF exposes **metadata only** — `.../meteorological/data/Nacote Creek/`
  is an empty directory by design. Data needs CDMO's Advanced Query System (free, but a
  click-through agreement). ⚠️ Siting is poor for this question anyway: up a creek off
  the Mullica, marsh on all sides, ~40 km south of Mantoloking.

Related: [[reference_wind_forcing_investigation]], [[reference_bay_volume_deficit]],
[[reference_bracket_pattern]].
