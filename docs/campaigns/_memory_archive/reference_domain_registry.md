<!-- Raw Claude-memory file, archived verbatim 2026-08-05 when the memory store was
     collapsed. Its standing content was merged into the new memory set and/or
     CLAUDE.md; this copy exists so the merge cannot have lost a detail.
     Superseded — do not treat as current. -->


# The domain registry — `nj_sfincs/domain.py` (new repo, 2026-07-26)

Every geographic fact used to be a literal somewhere: `SANDY_HOOK_TIP_Y` in `model.py`, a
sloped-easting HWM classifier in `validate.py`, `SHREWSBURY_WINDOW` in `plots.py`,
`latitude = 40.32` in `config.py`, hand-typed bboxes in half the download scripts. Fine for one
domain; a trap the moment there are two.

A `Domain` bundles them; `DOMAINS` maps name → Domain; **`NJ_DOMAIN` env var selects**
(default `v2_barnegat`); `domain.active()` returns it. `v1_monmouth` reproduces the sealed premier's
geography so the old behaviour stays reachable and diffable.

**Rule of thumb for what belongs there:** if extending the model south would make a number
wrong, it is domain geography. If it stays right (a physics constant, a solver tolerance, a datum
offset), it does not.

Holds: `region`, `refinement`, `epsg`, `latitude` (Coriolis, domain-mean), `obs_gauges`,
`mask_overrides`, `always_active_boxes_ll`, `open_coast_max_y`, `hwm_rules`, `plot_window`,
plus `bbox_ll(buffer_deg)` — **the single source of truth for every download/clip extent**
(three download scripts each carried their own bbox under a comment reading "update this if
region.geojson changes"). `BaseConfig` now pulls `domain / region / refinement / latitude /
frozen_mesh` from it, and `frozen_mesh` is keyed as `data/frozen_mesh_<domain>` so a build cannot
land on another domain's mesh by omission.

## ⚠️ THE PAYOFF — two constants that were silently correct on v1 and wrong on v2

Both are **unbounded on one side**, which is what makes them domain-dependent without looking it:

1. **`west_below_bay` mask override** was `fx < 582_500 & fy < 4_474_000` — *no southern bound*.
   On v1 (which stops at y≈4,444,800) it caught a small corner. On v2 (down to y≈4,394,700) it
   catches **essentially the entire southern lobe** — Barnegat Inlet (577,096/4,401,119), the
   Manahawkin cut, Toms River, Mantoloking — turning every waterlevel BC down there into a free
   outflow. Fixed by adding `ymin = 4_440_000`. **Behaviour-preserving for v1**: every v1 cell
   sits above y = 4,444,000.

2. **HWM basin `south_coast`** was `y < 4_458_000`, also unbounded, so every Barnegat mark would
   have been reported as "south_coast". Fixed by ordering the v2 rules FIRST.

## HWM basins are still THRESHOLDS, not polygons

Deliberate — matches [[feedback_simple_geometry]]. A box plus a slope is an auditable number;
a digitised polygon is opaque once written. `BasinRule` = box + optional sloped divider
(`x = slope_x0 + slope*(y − slope_y0)`, `side` picks east/west), evaluated in order, **first
match wins**, unmatched → `"unassigned"` rather than silently folded into a real basin.

**Verified: `v1_monmouth`'s rules reproduce the original `classify_hwm_basin` EXACTLY — 0
disagreements over 200,000 random points across the v1 footprint.** Re-run that check if the
rules are ever touched.

v2_barnegat adds `manasquan`, `barnegat_barrier`, `barnegat_bay` (8 basins total). Its barrier
divider reuses the SAME sloped line as the refinement polygons so the two cannot disagree about
which side of the barrier a point is on.

## Also moved / added

- `model.py`: mask overrides are now data (`MaskOverride` rectangles with from/to codes), applied
  in a loop that PRINTS how many cells each one hit — which is how the Manahawkin problem became
  visible. Obs points come from `domain.obs_gauges`.
- `plots.py`: `gauges_for_domain()` selects by what the domain actually placed, so a v1 figure
  cannot try to plot a v2-only gauge.
- `validate.py`: delegates to `domain.classify_hwm_basin`; `_basin_names()` replaces the
  module-level `HWM_BASINS` tuple.
- **`data/obs.geojson` was a DEAD FILE** in the old repo (nothing read it — obs points were
  hardcoded inline in `model.py`). Not ported.

Related: [[project_domain_expansion_v2]], [[project_nj_framework]], [[feedback_simple_geometry]],
[[reference_premier_domain_guard]].
