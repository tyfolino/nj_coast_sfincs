<!-- Raw Claude-memory file, archived verbatim 2026-08-05 when the memory store was
     collapsed. Its standing content was merged into the new memory set and/or
     CLAUDE.md; this copy exists so the merge cannot have lost a detail.
     Superseded — do not treat as current. -->


Two ways the flood-map scoring path lies to you. Found 2026-07-16 building the
Workstream E/M figures. Both produce a *plausible physics result* rather than an error,
which is the whole danger — same species as the [[project_shrewsbury_reinvestigation]] leak.

**1. Non-atomic cache write — FIXED, don't un-fix it.** `validate.load_floodmap` caches
`floodmap_hmax_lev3.tif` per run. The write takes minutes; interrupt it (Ctrl-C, kill,
quota) and it leaves a TRUNCATED raster that reads back **without error** and scores the
model bone dry: **CSI 0.00, every HWM "dry"** — a spectacular failure that is really a
broken file. `mask-zmin20` scored 0.72 from a complete raster and 0.00 from a 4 MB
stub of the same run. Now writes to `.floodmap_hmax_lev3.partial.tif` + `os.replace`
(atomic). **The temp name MUST end in `.tif`** — `downscale_floodmap` → `build_overviews`
asserts the extension and dies on `.tmp`.
**Do NOT add a size check to catch stubs:** a healthy floodmap is only **0.11–0.16×** its
dep raster (it is sparse), which overlaps what a stub looks like. Atomicity at the write is
the only reliable check. Also: don't compare a raw tif's finite-fraction to a
post-`.where(dep>-0.5)` array — they are not comparable, and I mis-diagnosed a good cache
as corrupt that way.

**2. ⚠️ OPEN: `hwm_metrics` moves with the raster EXTENT.** Same run, same call:
- FULL L3 raster (`validate.load_floodmap`) → `snapwave_tuned_25m` bias **−0.090** / RMSE **0.696**
- CLIPPED raster (`plots.load_cached_floodmap(window=...)`) → **+0.024** / **0.468**

The sealed runs agree to ~0.01 m, so it is **not** a constant offset. It is **not** the
sampling radius (both 6.2495 m/px → 8 px). Unexplained. **The full-raster path is the only
authoritative scorer** — every CSV/table/report number comes from it and they stand.
MOTF metrics are unaffected (CSI/POD/FAR match under clipping). Logged under "What is still
open" in `reports/shrewsbury_investigation.md`; the HWM figure deliberately prints no bias
because of it.

**Speed, while you're here:** `load_floodmap` re-runs `downscale_floodmap` *even when the
tif is cached*, then de-rotates the full 6596×11300 raster — minutes per run.
`plots.load_cached_floodmap` clips-before-reprojecting → ~21 s/run (8 min → 2 min for four).
But see trap 2 before trusting its HWM numbers.
