<!-- Raw Claude-memory file, archived verbatim 2026-08-05 when the memory store was
     collapsed. Its standing content was merged into the new memory set and/or
     CLAUDE.md; this copy exists so the merge cannot have lost a detail.
     Superseded — do not treat as current. -->


## ✅ STATUS 2026-07-26 — realised in CODE, not in the notebook

The generalisation happened for a concrete reason: the domain was pushed south to Barnegat Inlet
as the first of several increments toward Cape May, so "re-point it at a different NJ domain"
stopped being aspirational. It landed as **`nj_sfincs/domain.py`** in the new
`nj_coast_sfincs` repo — a `Domain` registry selected by `NJ_DOMAIN` — see
[[reference_domain_registry]] and [[project_domain_expansion_v2]].

Against the wish-list below:
- **"a single top Configuration cell gathering the per-domain knobs"** → done as a registry
  entry rather than a notebook cell (region, refinement, CRS, Coriolis latitude, mask overrides,
  obs gauges, HWM basin rules, plot window, frozen-mesh path).
- **"site-specific — swap this for another domain" notes where hardcoded** → the hardcoding is
  gone rather than annotated.
- **"OUT OF SCOPE … the download scripts also hardcode bbox"** → **also done.** Extents now come
  from `domain.active().bbox_ll(buffer)`; gauge/station lists still per-script but explicitly
  sectioned by domain.
- Still open: the **notebook itself** has not been reworked, and the light-pedagogy pass below
  has not been done. Those remain as originally described.

---

User goal (stated 2026-05-21): turn the Sandy notebook into a **reusable framework for all of New Jersey** — re-point it at a different NJ domain/event by changing a few clearly-marked knobs, not by hunting through cells. Audience is "mixed / future learners" (a grad student new to SFINCS should be able to follow), but they want it only **lightly** pedagogical — NOT a heavy teaching rework (no reframing every header as a question, no long concept paragraphs).

Implications / what makes it a framework:
- A single top **Configuration** cell gathering the per-domain/event knobs now scattered across cells: region geojson path, model_root, CRS, grid res, nr_subgrid_pixels, event window (tref/tstart/tstop), boundary buffer, beta_f, latitude, data_catalog path.
- Short **"site-specific — swap this for another domain/event"** notes where hardcoded: NOAA gauges, NDBC buoy, USGS rivers, the *pre-Sandy* DEM choice (for another event pick a contemporaneous DEM), AORC/USGS windows.
- Light concept intros (one clause) + bold **Takeaway** lines on results.
- De-clutter the config cell (39 comment lines) → move rationale to markdown.
- OUT OF SCOPE for the notebook pass but needed for true NJ generalization: the download scripts also hardcode site specifics (gauge IDs, river gauges, bbox) — parameterizing those is a separate step.

Related: [[project_compound_roadmap]], [[project_nj_sandy]], [[reference_notebook_tooling]].
