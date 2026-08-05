<!-- Raw Claude-memory file, archived verbatim 2026-08-05 when the memory store was
     collapsed. Its standing content was merged into the new memory set and/or
     CLAUDE.md; this copy exists so the merge cannot have lost a detail.
     Superseded — do not treat as current. -->


**No figure from a finished run needs to cost minutes.** Measured 2026-07-21 on
`faber-waves-premier`; the two real costs were both waste, not resolution.

1. **`validate.load_floodmap` re-ran the 81 s downscale on every call** even though
   `floodmap_hmax_lev3.tif` was already cached in the run dir. Proven redundant: the fresh
   output is **byte-identical** (md5 match) to the cached file. Now reuses the cache when it
   is newer than `sfincs_map.nc` (mtime, so a re-run invalidates it); `force=True` rebuilds.
   **120 s → 30 s.**
2. **`validate.read_output` used `xu.load_dataset`** — eager, pulling all ~2.2 GB of the
   872 MB `sfincs_map.nc` when callers want a few slices. Now `xu.open_dataset` (`lazy=True`
   default). **~40 s → ~2 s cold**, and a 4-run comparison paid the old cost four times.
   Pass `lazy=False` only when reading a run about to be overwritten (a lazy handle keeps
   reading the deleted inode).

**Regression-checked, all reproduce exactly**: HWM bias 0.3184 / RMSE 0.4800 / per-basin and
Shrewsbury crest 2.8365 vs `reports/solver-2x2.csv`; MOTF CSI 0.7063 / POD 0.7991 /
FAR 0.1412 vs `reports/shrewsbury_investigation.md`. Behavior-preserving.

## ⚡ 2026-07-28 — the THIRD cost, and the biggest one left: `load_floodmap` MEMO

Skipping the downscale (item 1) left the two array ops behind, and on `v2_barnegat` they
are **~95 s a call**: `rio.reproject` to de-rotate a 14596×11684 hmax raster (**both tifs
are stored with ~0.76° of shear** — that rotation is also why naive windowed reads of the
on-disk tif mis-index), plus `reproject_match` to pull the 29192×23368 3.125 m dep raster
onto it. **The v2 viz notebook made SEVEN such calls**, because `plot_motf_panels` and
`plot_hwm_residual_panels` each re-derive *every* run independently.

`validate.load_floodmap(..., memo=True)` now memoises on **(run dir, floodmap tif mtime)** —
mtime in the key means a re-run self-invalidates. Measured: **97.0 s cold → 0.000 s warm**;
`memo=False` re-derives and returns values `array_equal` to the cached ones. FIFO-bounded to
4 entries (~2 GB each); `load_floodmap_cache_clear()` releases them.

⚠️ **The cached arrays are SHARED, not copied** (copying would double ~2 GB per entry), so
callers must treat them as READ-ONLY. Every caller in the repo does. Use `memo=False` for an
independent copy.

Effect: the notebook's estimator-sweep cell went **190 s → 43 s** (only the v1 pair loads;
v2 is already in the cache from Setup), and a full run drops by ~6 min.

**⚡ The animation trick — `nj_sfincs/animate.py`.** The quadtree is fixed for a run; only
face VALUES change with time. So rasterize the face *indices* once
(`ugrid.rasterize(arange(nface))`, ~0.6 s) and every frame is `values[idx]` (~1 ms). A full
73-frame stack builds in **<1 s**; a per-frame render of 547k `PolyCollection` quads would
be minutes. Indices come back exact (cell-tree point location, no interpolation). The
remaining cost is `to_jshtml` PNG-encoding 73 frames (~15 s, inherent) — GIF via pillow, the
env has **no ffmpeg**.

Gotchas baked into `animate.FIELDS` / `WINDOWS`: depth needs a **fixed** vmax 3.0 and
`mask_ocean` (a percentile scale reads the 15–28 m open ocean and renders the real 0.5–2 m
inundation near-white); **SnapWave runs on a sub-domain** so `hm0` is nodata east of ~590 km,
and the bright band at that edge is the ~8 m wave INFLOW boundary — real forcing, not a spike.

⚠️ **Don't repeat this misreading:** the premier's MOTF CSI is **0.71**, not 0.64 — 0.64 is
the sealed **no-waves** arm. Both sit in one table at `reports/shrewsbury_investigation.md`
~line 659, and FAR is 0.14 for both, which makes them easy to confuse. I flagged 0.71 as a
regression on 2026-07-21; the user corrected it. Check that table before calling a MOTF
number wrong. See [[project_domain_rebuild]].

## ⚡ 2026-08-03 — the FOURTH cost: `imshow` was 10^5x oversampled

The user reported the HWM panel "takes a long time". It was not the data path — it was
the DRAWING. The panel plotters handed the **whole** de-rotated raster to `imshow` and
then cropped with `set_xlim`:

* the v2 de-rotated dep raster is **171 Mpx** (14596 x 11684);
* three panels = **513 Mpx** resampled by matplotlib to fill a figure ~1600 px wide;
* the HWM window covers only ~45% of the raster, so over half was drawn and discarded.

Fix: `plots._for_display(da, window=..., max_px=1600)` crops to the window and strides to
display resolution before `imshow`. Applied in `plot_hwm_residual_panels`.

**Measured after:** drawing **2.3 s** for 3 panels (warm memo), `savefig` **0.4 s**.
⚠️ The mark SAMPLING still uses the full-resolution raster — only the grey backdrop is
decimated — so no number on the figure moves.

**What remains is inherent, not a bug:** the first `load_floodmap` of a session costs
**~70 s** (cold de-rotate + `reproject_match` of the 29192 x 23368 dep tif); later arms
cost **~16 s** because they share the subgrid and hit `_DEP_MEMO`. Caps are
`_FLOODMAP_MEMO_MAX = 8` / `_DEP_MEMO_MAX = 3`, so a 3-arm notebook does not thrash.

🔑 The same `imshow`-the-whole-raster pattern is still in `plot_motf_panels`,
`plot_engine_panels` and `plot_engine_difference` (see the `imshow` call sites in
`plots.py`). They window differently so the waste varies, but `_for_display` applies.
