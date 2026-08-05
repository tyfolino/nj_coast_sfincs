<!-- Raw Claude-memory file, archived verbatim 2026-08-05 when the memory store was
     collapsed. Its standing content was merged into the new memory set and/or
     CLAUDE.md; this copy exists so the merge cannot have lost a detail.
     Superseded — do not treat as current. -->


# Sharing a flood-depth raster — the run artifact is the WRONG file

**`experiments/<arm>/floodmap_hmax_lev3.tif` is deliberately UNMASKED.**
`validate.load_floodmap` only applies `da_hmax.where(da_dep > -0.5)` *after* reading it,
and only `evaluate(gallery_tif=...)` ever writes the masked copy. Measured on v2's
premier:

| | finite cells | max | >2 m | >4 m |
|---|---|---|---|---|
| unmasked `lev3` | 18,245,134 | 71.82 m | 13,106,468 | 9,619,968 |
| masked gallery | 5,934,491 | 67.19 m | 804,729 | 8,982 |

Those 13 M cells over 2 m are **the seabed**. A damage model pointed at the raw file
computes losses across the Atlantic. ⇒ **never hand out the run-dir tif.**

## `scripts/export_share_floodmap.py` (2026-08-03)

Writes the masked raster + a README carrying the things a GeoTIFF header cannot:
sets `nodata` explicitly (the run artifacts leave NaN **untagged**), DEFLATE +
predictor=3 + tiled + overviews (**298 MB → 11.1 MB**, it is >97% NaN), and records
CRS/units/threshold/known bias.

⚠️ **The CRS is EPSG:32618 (UTM 18N), metres — NOT lat/lon.** A GeoTIFF is
georeferenced (CRS tag + affine transform) but that does not make it degrees; a
recipient expecting lat/lon sees corners like `561434, 4444626` and thinks it is
corrupt. Say the CRS up front.

⚠️ **The arm name alone is AMBIGUOUS** — `faber-waves-premier` exists on BOTH
`v1_monmouth` and `v2_barnegat` with different extents. The shared filename must carry
the domain: `sandy_hmax_v1_monmouth_faber-waves-premier_EPSG32618.tif`.

⚠️ **Wet threshold**: the raster floor is **0.05 m** (downscale `hmin`), but scoring
uses `DEPTH_MIN` **0.15**. Ship the 0.05 data, document the 0.15 recommendation — most
damage curves will assign losses to numerical damp otherwise.

For an external practice dataset prefer **v1 premier**: it is frozen, whereas every v2
arm is mid-campaign and gets superseded within days. Caveat to pass on: HWM bias about
**−0.25 m** (median estimator) — it runs LOW, so damages come out under-estimated.

Related: [[reference_floodmap_cache_traps]], [[reference_naming_convention]],
[[reference_hwm_estimator_artifact]].
