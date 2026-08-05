<!-- Campaign record. Moved out of the Claude memory store 2026-08-05; the
     memory file was `reference_ehydro_district_sign`. -->

> **Historical record — read top-down, newest first.** Blocks are appended in
> reverse chronological order and later blocks SUPERSEDE earlier ones, including
> where an earlier block calls itself current. Several conclusions in here were
> retracted; the retraction is always above the claim it retracts. For what is
> believed true *now*, see the memory store and `CLAUDE.md`, not this file.
>
> **Standing summary at the time of the move:** eHydro XYZ sign convention FLIPS between USACE districts and v2_barnegat straddles the boundary — Shark River (NY District) ships NEGATIVE elevations, Barnegat/ICW/Oyster Creek (Philadelphia District) ship POSITIVE depths below MLLW. download_ehydro_nj.py hardcodes one sign, so a southern carve would silently produce an EMPTY raster. Also: the v2 lagoon needs no carve — model is only +0.39 m shallower than soundings, inside datum+dredging noise.


# eHydro: the sign convention flips by USACE district (found 2026-07-28)

## 🐛 THE TRAP

`scripts/download_ehydro_nj.py` and `scripts/audit_paved_channels.py` both hardcode

    z_navd88 = z_mllw_ft * FT_TO_M + offset

That is correct **only for negative-elevation surveys.** Measured on the raw `.XYZ`:

| survey | district | raw z | convention |
|---|---|---|---|
| `CENAN_DIS_NJ_10_SRI_*` (Shark River Inlet) | **NY (CENAN)** | −33.2 … −0.7 ft | **negative ELEVATION** |
| `BI_02_OCC_*` (Oyster Creek), ICW, Toms River, Barnegat Inlet | **Philadelphia (CENAP)** | **+1.5 … +64 ft** | **positive DEPTH below MLLW** |

**🔑 `v2_barnegat` STRADDLES THE DISTRICT BOUNDARY** — Shark River is NY District, all of
Barnegat Bay is Philadelphia District. So the one existing carve is on the *only* side the
hardcoded sign is right for.

**How it would fail: SILENTLY.** Run unchanged on a southern survey, the formula returns
POSITIVE "elevations"; the water-only clip `grid[grid >= WATER_MAX] = nan` (`WATER_MAX =
-1.0`) then drops **100%** of them. Output: a valid-looking raster with nothing in it, no
error, no carve. Detect the convention instead of assuming — a navigation channel is never
mostly above MLLW:

    depth_positive = np.median(z_raw) > 0
    z = (-z_raw if depth_positive else z_raw) * FT_TO_M + offset

⚠️ It bit this session's first analysis too: with the wrong sign the Oyster Creek channel
"sounded" at **+2.95 m** and the model looked 6.6 m too deep. **A positive bed elevation for
a dredged channel is the tell — stop and check the raw file.**

⚠️ `audit_paved_channels.py` also can't run on v2 as-is: `MODEL` is hardcoded to
`experiments/snapwave_tuned_25m/sfincs.nc` (a v1 dir absent from the v2 repo) and it wants
`data/elevation/cudem_nj_clip.tif`, which the v2 repo does not have (it has `cudem_nj.vrt`).
`reports/paved_channels.csv` has **never** been generated for v2.

## 🛠️ THE SOUTHERN CARVE WAS BUILT ANYWAY (2026-07-28, user's call: settle it empirically)

`scripts/build_ehydro_south.py` → `data/elevation/ehydro_south.tif`, catalog `ehydro_south`,
experiment **`wave-cora+bed-ehydro`**, staged from `_template_ehydro_south`
(`scripts/setup_ehydro_south_template.py`). **800,622 carved cells at 5 m (~20 km²), median
−2.51 m, min −18.93 m**, from the EARLIEST survey per feature (13 features: Manasquan +
Barnegat inlets, ICW ×6 segments, Point Pleasant Canal, Toms River, Oyster Creek, Wills
Hole). Sign detection fired correctly on all 13 (**all Philadelphia District,
depth-positive-down**). Water-only clip dropped just 2,031 cells (0.25%).

**🚀 RUNNING: SLURM 59430582 `wave-cora+bed-ehydro` (2026-07-28, 12 h/128 G/48c).** Staged
clean — `sfincs.inp` 0-key diff vs `wave-cora`, domain fingerprint UNCHANGED
(`9ccbab0bc7a9fc0d`), so it is directly comparable.

**⭐ THE PRE-RUN SIGNAL SAYS "NULL", AND IT IS QUANTIFIED.** What 800k carved cells actually
did to the subgrid:

| field | changed | median Δ | deepened |
|---|---|---|---|
| `z_zmin` | 9,973 / 1,143,357 (**0.87%**) | **−0.003 m** | **51%** |
| `uv_zmin` | 19,382 / 2,307,638 (0.84%) | +0.001 m | 50% |
| `z_zmax` | 8,990 (0.79%) | +0.028 m | 41% |

**A coin flip at the millimetre level over <1% of cells.** The survey bed and the existing
DEM already agree, and the per-survey VDatum correction pushes both ways. If the run comes
back null, that is not a weak test — this table says *why* in advance.
⚠️ `uv_nrep` also moves (200,954 pts, 0.87%) even though roughness is untouched: `nrep` is
per-LEVEL, so changing the bed changes which subgrid pixels are wet at each level. Expected,
not a roughness leak. The verification script's "expected ~0" wording is wrong for `nrep`.

**⭐⭐ AND IT INVALIDATES PART OF THE "+0.34 m TOO SHALLOW" NUMBER BELOW.** The scratch
comparison used a NOMINAL −0.50 m MLLW→NAVD88. The real VDatum field over this lobe runs
**−0.109 m (IW 03) to −0.731 m (Manasquan Inlet)** — a **0.62 m spread**, per-survey:

| survey | VDatum offset | vs the nominal −0.50 |
|---|---|---|
| IW 03 MKR 002–027 | −0.109 | **+0.39 m** |
| IW 05 / Toms River / Oyster Ck | −0.146 … −0.158 | +0.34 m |
| Barnegat Inlet | −0.528 | −0.03 |
| ICW 01 Manasquan R. / Wills Hole | −0.702 … −0.718 | −0.21 |
| Manasquan Inlet | −0.731 | −0.23 m |

⇒ **the datum error was the same size as the whole signal, and per-survey it has BOTH
signs.** Any future sounding-vs-model comparison must use `offset_field()`, never a
constant. The qualitative verdict (nothing paved) survives — a 7 m Shark-style error is not
hidden by 0.4 m of datum — but the "+0.34 m" itself should not be quoted.

## ❌❌ THE "NULL" PREDICTION WAS WRONG — THE CARVE IS THE BEST ARM (scored 2026-07-29)

**Everything below this heading is the argument I made for skipping the carve. The run
came back and falsified its conclusion. Keep it only as the worked example of HOW the
reasoning failed; do NOT act on its verdict.**

`wave-cora+bed-ehydro` scored (median, native 95) **best on bias, RMSE AND CSI at once**:

| arm | HWM bias | RMSE | CSI | barnegat_bay basin bias |
|---|---|---|---|---|
| `wave-cora` (control) | −0.293 | 0.507 | 0.672 | −0.215 |
| **`wave-cora+bed-ehydro`** | **−0.244** | **0.493** | **0.701** | **+0.005** |
| `wave-cora+bed-baymanning` | −0.335 | 0.543 | 0.613 | −0.452 |

⚠️ **The gain is SOUTHERN-LOBE ONLY.** On the BRIDGE 31 marks ehydro is −0.231 vs
`wave-cora`'s −0.231 — *identical*. Coherent (the carve is in the south, the new marks are
in the south), but it must never be quoted as a domain-wide or v1-comparable win.

**🔑 WHY THE PREDICTION FAILED — the wrong diagnostic.** The "coin flip at the millimetre
level" table above is arithmetically correct and still irrelevant. `z_zmin` is the DEEPEST
POINT of a cell; the hydrodynamics respond to STORAGE and RELIEF:

| field | changed | median Δ | what I did with it |
|---|---|---|---|
| `z_zmin` | 0.87% | −0.003 m | ⛔ predicted the null on this |
| **`z_volmax`** | **0.95%** | **+5.4507** | ⭐ the actual mechanism, never looked at |
| `z_zmax` | 0.79% | +0.028 m | noted, not followed up |

⇒ **A carve does not only remove bed. It adds sub-cell channel/bank RELIEF that the coarse
stack had averaged away** — which is the whole point of a subgrid. "Deepening ⇒ more
conveyance ⇒ worse" (the sign argument below) treats the edit as a uniform lowering; it
isn't. **Before calling any bed edit null, diff `z_volmax`, not just `z_zmin`.**

⚠️ And the friction lever this file recommended instead (`bed-baymanning`) is the WORST arm
in the campaign — CSI 0.672 → 0.613, barnegat_bay bias −0.215 → −0.452. Raising lagoon
Manning DAMPS and DRAINS the bay rather than redistributing along it. It does fix the
over-amplification and phase at Mantoloking (range 0.414 → 0.229, lag −62.7 → −35.8 min)
while making levels and extent clearly worse. See [[feedback_ehydro_prediction_miss]].

## ⚠️ SUPERSEDED VERDICT (kept for the reasoning, not the conclusion): NO CARVE NEEDED

89 eHydro surveys intersect the southern lobe (Barnegat Inlet, Manasquan, ICW segments,
Toms River, Oyster Creek), so data availability is not the constraint. Compared against
USACE's own soundings (correct sign, nearest model face within 25 m):

| survey | n | sounded | model | model − sounded |
|---|---|---|---|---|
| Oyster Creek ×4 | 2.5–6.6k | −3.8 … −4.6 | −3.1 … −3.6 | **+0.35 … +0.65** |
| Toms River | 1.3k | −2.67 | −2.36 | **+0.30** |
| IW 06 MKR 044–068 | 4.2k | −2.62 | −2.60 | **+0.11** |
| IW 05 MKR 040–044 | 6.7k | −3.34 | −2.99 | **+0.37** |
| | | | **median** | **+0.39 m** |

**Nothing is paved.** The failure mode eHydro exists to fix is a ~7 m error (Shark: +2 m
lidar over −5 m bed). Here the model already has every channel to within half a metre.

**And +0.39 m is inside the noise**: the surveys are **2024–2025** against a **2012** storm
(dredge/shoal cycles), and the audit-grade MLLW→NAVD88 used a nominal −0.50 m where the real
separation varies ~0.4 m over a comparable footprint. The signal is the size of its own
error bars.

**⭐ AND THE SIGN IS WRONG ANYWAY.** A carve only ever REMOVES bed ⇒ more conveyance. The
lagoon already conveys **too freely** — Mantoloking holds 0.401 m of range against 0.167 m
observed and arrives **58 min EARLY**, while Barnegat Light's range is right to 0.002 m
(see [[project_domain_expansion_v2]]). Deepening makes both worse.

**Resolution is not the problem either**, which was the original worry: bay wet faces are
**25 m (51%) / 50 m (45%)**, median 25 m, and the lagoon's mean depth **1.57 m** matches the
published ~1.5 m for Barnegat Bay. Sub-cell channel conveyance is what the subgrid tables
are for, and the subgrid DEM demonstrably has the channels.

⇒ **The lever is FRICTION / STORAGE, not bathymetry.** Depth right + tide too fast + too
little decay between inlet and mid-lagoon = too little dissipation. Candidates: bay-bottom
Manning (the open-water floor vs real eelgrass/shoal beds — see [[project_manning_nj]]),
marsh storage around the lagoon rim, and the already-flagged closed Manahawkin wall.

## 🌉 BRIDGE-DECK CHECK, southern lobe (2026-07-28) — PPC and Mantoloking Br are CLEAN

Separate failure mode from channel depth: a road deck baked into the lidar is a LOCAL SILL
(cf. Rumson–Sea Bright). Checked with the thalweg rule from [[project_bridge_dam]].

- **Point Pleasant Canal — NO dam.** Model thalweg over 2.8 km: max (the sill) **−5.73 m**,
  median −7.14 m. Continuously open; no road crossing appears as a barrier. Sounded median
  −8.60 m, so the model is ~1.3 m shallow but never blocked. ⭐ **Only ONE PPC survey has
  downloadable data (2024-01-09) — the "surveys go back a decade" expectation does not hold
  per-feature.** Southern-lobe archive spans **2015–2026** with **ZERO in 2009–2014**.
- **Rt 528 Mantoloking Bridge — NO dam.** N–S thalweg through the gauge's own longitude runs
  −2.4 … −5.3 m continuously across the bridge latitude; model −2.67/−2.46 there vs soundings
  −1.91 … −3.20 m (three surveys). The model matches the survey at the crossing.

🐛 **A FALSE POSITIVE I RAISED AND HAD TO RETRACT — the lesson is about the MASK.** A
lagoon-wide scan first reported a "controlling sill of +0.09 m at the Mantoloking Bridge."
It was an artifact of the straight barrier-island line (`lon < lon_bar − 0.004`): at 40.04
the lagoon **narrows and swings east**, so the line cut off the channel and left only
mainland marsh, whose min bed really is ~0 m. **A thalweg scan is only as good as its bay
mask — if a band returns few cells or land-like values, suspect the mask before the model.**
The straight line is still fine for the roughness recode (it only touches class-11 water).
⚠️ The data-driven replacement (split each latitude at the largest longitude GAP between wet
cells = the barrier island) is better — no band anywhere exceeds −0.03 m, so no hard dam —
but it is ALSO unstable at some latitudes (returns 3–4 cells where take-1 found 500+), so
**neither mask is trustworthy enough for a lagoon-wide verdict yet.** OPEN: the Rt 37
causeway (~39.95) reads as low as −0.10 m and deserves a proper look.

Related: [[project_domain_rebuild]] (the Shark carve that worked), [[project_bridge_dam]]
(how to measure a sill), [[reference_build_traps]].
