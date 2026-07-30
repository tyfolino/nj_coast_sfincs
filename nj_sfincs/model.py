"""Build the NJ Sandy quadtree SFINCS model, in pure functions.

Lifted verbatim (behaviour-preserving) from notebooks/sfincs-nj-sandy.ipynb:

* ``build_static``  — Phase 1, cells 9–33 (grid, elevation, mask, boundary,
  obs points, roughness, subgrid) → written once into a template dir.
* ``add_forcing``   — Phase 2, cells 38–50 (window + surge, wind/pressure, rain,
  discharge, infiltration).
* ``add_waves``     — Phase 2 cell 52 (the SnapWave block), extended with Tim's
  physics params + the optional ocean-side wavemaker.
* ``finalize``      — Phase 2 cell 54 (release handles, write, patch sfincs.inp,
  write the SnapWave ASCII forcing).

The NJ-Sandy-specific coordinate boxes (bay include, boundary corrections) are
kept as module constants with the original comments — re-derive them for a
different NJ region (see notebook Appendix A).
"""

from __future__ import annotations

import gc
import os
import shutil
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import shapely
import xarray as xr
from hydromt import log
from hydromt_sfincs import SfincsModel
from shapely.geometry import Point

from . import domain as _domain
from .config import ROOT, BaseConfig, WaveConfig

# HDF5/netCDF file locking off before any netCDF-backed write on /cache (a failed
# lock surfaces as a misleading "NetCDF: Permission denied"). Mirrors the notebook.
os.environ.setdefault("HDF5_USE_FILE_LOCKING", "FALSE")

# ── Geography now lives in the DOMAIN REGISTRY ───────────────────────────────
# `BAY_INCLUDE_BOX_LL`, `SANDY_HOOK_TIP_Y` and the three inline mask-correction
# boxes used to be module-level literals here. They are per-domain facts, so they
# moved to nj_sfincs/domain.py where extending the model south is one registry
# entry instead of a hunt through five modules. Everything left in this block is
# domain-INDEPENDENT: it stays right no matter where the domain is.

# Thickness of the seaward ring promoted to SnapWave boundary when the wave
# domain is decoupled: cells within this many metres of the deep cut become
# msk==2. Wide enough to give a contiguous ring on a 200 m quadtree edge.
SNAPWAVE_BND_RING = 5.0

# A free-outflow (Neumann) BC on water deeper than this is a DRAIN, not a boundary.
OUTFLOW_MAX_DEPTH = -1.0
# A cell the model calls (near-)land while a real survey says there is water this deep
# beneath it has been PAVED OVER by a failed lidar return.
PAVED_BED_LAND = -0.5
PAVED_SURVEY_WATER = -2.0


def _open_coast_max_y() -> float:
    """Northing above which the coast is no longer open Atlantic.

    Incident SnapWave energy must only enter along the open-ocean edge. North of
    the Sandy Hook tip the "boundary" wraps into the enclosed harbour/bay corner,
    and leaving boundary cells there let waves run away into it — the ~1e13
    blow-up. Support points are likewise taken only from below this line.

    Comes from the domain registry; ``inf`` means the whole seaward edge is open
    coast, which is the right default for a domain with no such spit.
    """
    y = _domain.active().open_coast_max_y
    return float("inf") if y is None else y


def _inactive_components(sf, mask):
    """Split the inactive cells into (ocean-connected mass, interior holes).

    "Ocean-connected" is just the LARGEST connected component of ``mask == 0``. On
    this domain that single blob is the shelf plus all the dry land, which wrap
    round each other continuously — 325,213 of 325,366 inactive cells on
    v2_barnegat. Anything else is an inactive island sitting inside the model.

    Returns ``(ocean, hole)`` boolean arrays over faces.
    """
    from scipy.sparse.csgraph import connected_components

    inactive = mask == 0
    if not inactive.any():
        z = np.zeros(len(mask), dtype=bool)
        return z, z
    adj = sf.quadtree_grid.data.grid.face_face_connectivity
    idx = np.flatnonzero(inactive)
    _, lab = connected_components(adj[inactive][:, inactive], directed=False)
    labels, counts = np.unique(lab, return_counts=True)
    main = labels[np.argmax(counts)]
    ocean = np.zeros(len(mask), dtype=bool)
    hole = np.zeros(len(mask), dtype=bool)
    ocean[idx[lab == main]] = True
    hole[idx[lab != main]] = True
    return ocean, hole


def _fill_inactive_holes(sf, mask, zb) -> np.ndarray:
    """Activate any inactive island that is not connected to the ocean/land mass.

    A depth threshold is a statement about ELEVATION, but the mask it produces is a
    statement about TOPOLOGY, and the two disagree wherever the isobath reaches
    inside the model. ``mask_zmin = -10`` left 153 such cells on v2_barnegat: 145 in
    the Barnegat Inlet throat (to -14.78 m), 3 in the Navesink, 1 at Manasquan. They
    do two things, both bad. As islands they block conveyance through the one
    cross-section that matters. As mask edges they make ``create_boundary`` impose
    the open-ocean water level around them, kilometres inside an inlet.

    So: fill them. This is deliberately topological rather than geometric — it needs
    no hand-drawn box, and it therefore keeps working when the domain moves south,
    when an eHydro carve deepens a channel, or when ``mask_zmin`` changes. It cannot
    on its own fix an intrusion that stays CONNECTED to the sea (a scoured inlet
    gorge is the case in point); that is what ``always_active_boxes_ll`` is for, and
    the two are used together at Barnegat Inlet.

    Runs BEFORE ``create_boundary`` — filling afterwards would leave the boundary
    cells the holes had already spawned.
    """
    _, hole = _inactive_components(sf, mask)
    n = int(hole.sum())
    if not n:
        print("[mask] no interior inactive holes")
        return mask
    fx, fy = sf.quadtree_grid.data.grid.face_coordinates.T
    mask = mask.copy()
    mask[hole] = 1
    print(f"[mask] filled {n} interior inactive cells (deepest {zb[hole].min():+.2f} m; "
          f"x {fx[hole].min():.0f}-{fx[hole].max():.0f}, "
          f"y {fy[hole].min():.0f}-{fy[hole].max():.0f}) — an inactive island inside "
          f"the model blocks conveyance AND spawns a water-level BC around itself")
    return mask


def _check_domain_invariants(sf, mask, zb) -> None:
    """Refuse to ship a domain carrying any of the four defects listed below.

    Both bugs were INFRASTRUCTURE, not physics — a region polygon and an elevation
    tier — which is exactly why an exhaustive elimination of every *physical* lever
    (wind, friction, mesh resolution, wave convergence, channel dredging) came back
    null for weeks. Nobody suspects a boundary condition. So we assert them instead.

    1. NO FREE-OUTFLOW BC ON OPEN WATER. The region polygon chopped the Navesink in
       half mid-channel and hydromt put a free-outflow BC on the 5 m-deep cut face.
       The model drained 92.5% of the estuary's entire inflow out of that hole,
       one-way, in 100% of timesteps, from the first hour. THIS ONE CHECK WOULD HAVE
       CAUGHT IT ON DAY ONE.

    2. NO PAVED-OVER CHANNELS. `usace_nj_2010` is green lidar: in deep or turbid
       water it fails to penetrate and returns the WATER SURFACE (~0 to +2 m), which
       looks like land. Ranked top of the elevation list, it shadowed CUDEM's correct
       bed and sealed Shark River Inlet — leaving the entire Shark estuary at exactly
       +0.00 m, never flooding, through Hurricane Sandy, while the ocean 1.8 km away
       reached +2.9 m. We check the model bed against the eHydro survey (a boat with
       an echo sounder) wherever that survey has data.

    3. NO INTERIOR INACTIVE ISLANDS. The post-condition on ``_fill_inactive_holes``.
       Cheap, and it fails loudly if the fill is ever removed or outrun.

    4. NO IMPOSED OCEAN LEVEL WHERE THE DOMAIN DECLARES THERE MUST NOT BE ONE. This
       is the third instance of one defect class in this project — the Navesink
       (free outflow on a tidal river), the Manahawkin cut (waterlevel across an
       interior bay), Barnegat Inlet (waterlevel 2.6 km inside the throat). Every one
       of them passed every check that existed at the time, ran to completion, and
       produced numbers nobody could tell were wrong. So each domain now DECLARES
       where an open-ocean level is inadmissible, and the build refuses to ship one
       there. See ``domain.NoWaterLevelBox``.
    """
    import rasterio

    from .config import DATA

    fail = []

    n_wet_out = int(((mask == 3) & (zb < OUTFLOW_MAX_DEPTH)).sum())
    if n_wet_out:
        fail.append(
            f"{n_wet_out} free-outflow cells (mask=3) sit on water below "
            f"{OUTFLOW_MAX_DEPTH} m. That is a DRAIN, not a boundary — it is the bug "
            f"that emptied the Navesink."
        )

    _, hole = _inactive_components(sf, mask)
    if hole.any():
        fx, fy = sf.quadtree_grid.data.grid.face_coordinates.T
        fail.append(
            f"{int(hole.sum())} inactive cells form islands INSIDE the model "
            f"(deepest {zb[hole].min():+.2f} m, around x {fx[hole].mean():.0f} "
            f"y {fy[hole].mean():.0f}). They block conveyance and make "
            f"create_boundary impose an open-ocean level around them."
        )

    for zone in _domain.active().no_waterlevel_boxes:
        xmin, ymin, xmax, ymax = zone.box
        fx, fy = sf.quadtree_grid.data.grid.face_coordinates.T
        sel = ((mask == 2) & (fx > xmin) & (fx < xmax)
               & (fy > ymin) & (fy < ymax))
        if sel.any():
            fail.append(
                f"{int(sel.sum())} water-level BC cells (mask=2) fall inside the "
                f"no-waterlevel zone '{zone.name}' (deepest {zb[sel].min():+.2f} m). "
                f"{zone.why}"
            )

    tif = DATA / "elevation" / "ehydro_nj.tif"
    if tif.exists():
        fx, fy = sf.quadtree_grid.data.grid.face_coordinates.T
        act = mask > 0
        with rasterio.open(tif) as d:
            v = np.array(
                [r[0] for r in d.sample(zip(fx[act].tolist(), fy[act].tolist()))],
                dtype="float64",
            )
            if d.nodata is not None:
                v[v == d.nodata] = np.nan
        v[v < -1e5] = np.nan
        paved = (zb[act] >= PAVED_BED_LAND) & (v < PAVED_SURVEY_WATER)
        if paved.any():
            fail.append(
                f"{int(paved.sum())} active cells are (near-)land in the model "
                f"(bed >= {PAVED_BED_LAND} m) where the eHydro survey sounded water "
                f"below {PAVED_SURVEY_WATER} m. A channel is still paved over."
            )

    if fail:
        raise RuntimeError(
            "[build_static] DOMAIN INVARIANTS FAILED:\n  - " + "\n  - ".join(fail)
        )
    print("[build_static] domain invariants OK (no outflow BC on water; no paved-over "
          "surveyed channel; no interior inactive islands; no imposed ocean level in a "
          "declared no-waterlevel zone)")


def apply_mask_and_boundary(base: BaseConfig, sf: SfincsModel) -> None:
    """Build the active mask + water-level/outflow boundaries and enforce the invariants.

    Extracted verbatim from ``build_static`` (sections 4-5) so it has ONE source of
    truth. ``build_static`` calls it on a freshly-built grid; the boundary-depth sweep
    (``scripts/setup_boundary_depth.py``) calls it on a COPY of the frozen mesh to
    re-derive the mask at a different ``mask_zmin`` — a pure mask/boundary change that
    reuses the frozen subgrid tables (every face already has them), so no rebuild.
    Depends only on ``sf`` and ``base`` (``base.mask_zmin`` and ``base.region``).
    """
    # 4. Active mask ----------------------------------------------------------
    # Boxes forced active at any depth, so dredged channels (-11..-27 m in
    # Raritan / Sandy Hook Bay) don't punch inactive holes through a bay interior.
    _boxes = _domain.active().always_active_boxes_ll
    bay_include = (
        gpd.GeoDataFrame(geometry=[shapely.box(*b) for b in _boxes], crs=4326)
        if _boxes else None
    )
    sf.quadtree_mask.create_active(zmin=base.mask_zmin, include_polygon=bay_include)

    # Clip the active mask to the region polygon (the rotated grid fills the L's
    # bounding box; drop the dry inland cells in the concave notch). Mask-only.
    _region = gpd.read_file(base.region).to_crs(sf.crs).geometry.iloc[0]
    fx, fy = sf.quadtree_grid.data.grid.face_coordinates.T
    _outside = ~shapely.contains_xy(_region, fx, fy)
    mask = sf.quadtree_grid.data["mask"].values.copy()
    mask[_outside] = 0

    # 4b. Fill inactive islands ----------------------------------------------
    # MUST come after the region clip (which creates its own inactive ground) and
    # BEFORE create_boundary, which is what turns an island into a ring of imposed
    # open-ocean level. See _fill_inactive_holes.
    mask = _fill_inactive_holes(sf, mask, sf.quadtree_grid.data["z"].values)
    sf.quadtree_grid.data["mask"] = sf.quadtree_grid.data["mask"].copy(data=mask)

    # 5. Boundary cells -------------------------------------------------------
    sf.quadtree_mask.create_boundary(btype="waterlevel", zmax=-1, reset_bounds=True)
    sf.quadtree_mask.create_boundary(
        btype="outflow", zmin=-1, zmax=2, reset_bounds=False
    )

    # Region-specific mask corrections, from the DOMAIN REGISTRY rather than
    # inline literals. Each is a rectangle in the domain CRS with a from-code and
    # a to-code; see nj_sfincs/domain.py for what each one is for and why.
    #
    # These used to be three hand-written boolean expressions here. The reason
    # they moved: two of them have UNBOUNDED sides, which makes them silently
    # domain-dependent — `fx < 582_500 & fy < 4_474_000` selected a small corner
    # of v1 and would have selected almost the whole southern lobe of v2.
    mask = sf.quadtree_grid.data["mask"].values.copy()
    fx, fy = sf.quadtree_grid.data.grid.face_coordinates.T
    for ov in _domain.active().mask_overrides:
        xmin, ymin, xmax, ymax = ov.box
        sel = mask == ov.frm
        if xmin is not None:
            sel &= fx > xmin
        if ymin is not None:
            sel &= fy > ymin
        if xmax is not None:
            sel &= fx < xmax
        if ymax is not None:
            sel &= fy < ymax
        n = int(sel.sum())
        if n:
            print(f"[mask] override {ov.name}: {n} cells {ov.frm} → {ov.to}  ({ov.why})")
        mask[sel] = ov.to

    # (d) SEAL ANY FREE-OUTFLOW BC THAT LANDS ON OPEN WATER  (2026-07-14) ------
    # A free-outflow (Neumann) boundary is the condition you use where water may
    # leave and never return. On a DEEP CROSS-SECTION OF A TIDAL RIVER it is not a
    # boundary, it is a DRAIN — and that is precisely the bug that wasted two
    # months of this project. The region polygon used to chop the Navesink in half
    # mid-channel; hydromt dutifully put mask=3 on the 5 m-deep cut face; the model
    # then ran that face at -0.82 m/s OUT of the domain in 100% of timesteps, never
    # once reversing, and **92.5% of everything entering the estuary vanished**.
    # The estuary was a pipe, not a bathtub, and every "null result" in the campaign
    # was really just a bucket with a hole in it.
    #
    # The region fix (west edge -> x=577,000) now lands the domain edge on dry land
    # at the Navesink and Shark, so this should catch nothing there. It still fires
    # at the NW/Raritan corner, which sits on the TRUE domain edge — there is no
    # more river to enclose, so the only correct treatment is a wall.
    #
    # A wet outflow cell becomes an ordinary active cell (mask=1); the inactive
    # ground beyond it is then SFINCS's default closed wall. Dry outflow cells are
    # left alone: they legitimately let overland flood water leave the domain
    # instead of ponding against the edge.
    zb = sf.quadtree_grid.data["z"].values
    wet_outflow = (mask == 3) & (zb < OUTFLOW_MAX_DEPTH)
    if wet_outflow.any():
        print(f"[mask] sealing {int(wet_outflow.sum())} free-outflow cells that sit on "
              f"water (deepest {zb[wet_outflow].min():+.2f} m) — an outflow BC on open water "
              f"is a drain, not a boundary")
        mask[wet_outflow] = 1
    sf.quadtree_grid.data["mask"] = sf.quadtree_grid.data["mask"].copy(data=mask)

    _check_domain_invariants(sf, mask, zb)


def build_static(base: BaseConfig, template_dir: Path, skip_subgrid: bool = False) -> None:
    """Phase 1 — build grid/elevation/mask/subgrid and write to ``template_dir``.

    Forcing-independent, so it runs once; ``add_forcing`` reopens from disk.
    """
    template_dir = Path(template_dir)
    template_dir.mkdir(parents=True, exist_ok=True)

    # Reproducibility short-circuit: the quadtree grid+subgrid build is
    # environment-sensitive — two builds of identical code/config can differ by
    # ~18 cells, which shifts CSI ~0.04 (notebook 0.54 vs harness 0.50; see
    # project memory). If a frozen static mesh is provided, copy it verbatim so
    # every run — harness AND notebook — shares ONE identical grid. Freeze once
    # with scripts/freeze_mesh.py; point BaseConfig.frozen_mesh at the result.
    if base.frozen_mesh is not None:
        frozen = Path(base.frozen_mesh)
        if not (frozen / "sfincs.inp").exists():
            raise FileNotFoundError(
                f"BaseConfig.frozen_mesh={frozen} has no sfincs.inp — "
                f"build it first with scripts/freeze_mesh.py"
            )
        print(f"[build_static] reusing frozen mesh from {frozen} (no rebuild)")
        shutil.copytree(frozen, template_dir, dirs_exist_ok=True)
        return

    log.initialize_logging()
    log.set_log_level(log_level=30)  # warnings + errors only (quiet build)
    log.to_file(template_dir / "hydromt_sfincs.log", append=False)

    sf = SfincsModel(
        data_libs=base.data_libs, root=str(template_dir), mode="w+", write_gis=True
    )

    # 2. Quadtree grid --------------------------------------------------------
    refinement_gdf = gpd.read_file(base.refinement)
    sf.quadtree_grid.create_from_region(
        region={"geom": str(base.region)},
        res=base.base_res,
        rotated=base.rotated,
        crs=base.crs,
        refinement_polygons=refinement_gdf,
        elevation_list=base.elevation(),
    )

    # 3. Elevation ------------------------------------------------------------
    sf.quadtree_elevation.create(
        elevation_list=base.elevation(), buffer_cells=0, nrmax=2000
    )

    # 4-5. Active mask + boundary cells --------------------------------------
    apply_mask_and_boundary(base, sf)

    # 6. Observation points (validation gauges only) --------------------------
    # From the domain registry. Names must stay stable: every his-based metric
    # matches its station by substring on this name.
    gauges = _domain.active().obs_gauges
    val_gauges = gpd.GeoDataFrame(
        {"name": [g.name for g in gauges]},
        geometry=[Point(g.lon, g.lat) for g in gauges],
        crs="EPSG:4326",
    )
    print(f"[obs] {len(gauges)} observation points: {', '.join(g.name for g in gauges)}")
    sf.observation_points.create(locations=val_gauges, merge=False)

    # 7. Roughness + subgrid (memory/CPU peak) --------------------------------
    if skip_subgrid:
        # Domain-geometry dry run: everything the invariants need (grid, elevation,
        # mask, boundaries) is already built, and the subgrid is by far the most
        # expensive step. Used by scripts/validate_domain.py to PROVE a region /
        # elevation change is right BEFORE paying for a full rebuild.
        print("[build_static] skip_subgrid=True — stopping after mask/boundary (no subgrid)")
        fx, fy = sf.quadtree_grid.data.grid.face_coordinates.T
        np.savez(
            template_dir / "domain_dryrun.npz",
            x=fx, y=fy,
            z=sf.quadtree_grid.data["z"].values,
            mask=sf.quadtree_grid.data["mask"].values,
        )
        del sf
        gc.collect()
        return

    for src in list(sf.data_catalog.sources):
        s = sf.data_catalog.get_source(src)
        if hasattr(s, "_data"):
            s._data = None
    gc.collect()

    roughness_list = [{"lulc": base.roughness_lulc,
                       "reclass_table": str(base.reclass_table)}]
    sf.quadtree_roughness.create(roughness_list=roughness_list, nrmax=200)
    sf.quadtree_subgrid.create(
        elevation_list=base.elevation(),
        roughness_list=roughness_list,
        nr_subgrid_pixels=base.nr_subgrid_pixels,
        nrmax=2000,  # DO NOT lower — smaller explodes the block loop
        write_dep_tif=True,  # per-level subgrid DEMs (flood-map downscale)
        write_man_tif=True,
    )

    # 8. Write ----------------------------------------------------------------
    sf.write()
    del sf
    gc.collect()


def check_waterlevel_support(sf: SfincsModel) -> int:
    """Assert hydromt selected the number of water-level support points we expect.

    Which gauges force the open boundary is decided by BUFFERING the region, so it
    is a property of the DOMAIN, not of the forcing file. `noaa_sandy_nj.nc` holds
    Battery, Atlantic City and Cape May; on v1_monmouth the 100 km buffer reaches
    the first two, and on v2_barnegat it reaches all three — Cape May crosses in by
    0.9 km. Nothing downstream notices: the run completes, the boundary is smooth,
    and the arm is simply no longer the premier's 2-node construction.

    Inserting a support point is not a cosmetic change here. It is what cost
    `phaselag_composite_v2` +0.18 m of HWM bias in v1, and the failure mode is
    silent by nature, so this is checked rather than remembered. Returns the count.
    """
    want = _domain.active().n_waterlevel_support
    data = getattr(sf.water_level, "data", None)
    if data is None or "bzs" not in data:
        raise RuntimeError(
            "water_level.create wrote no 'bzs' forcing "
            f"(water_level.data = {data!r}). Refusing to continue: the support-point "
            "count is exactly the thing that must not change silently between domains."
        )
    da = data["bzs"]
    dims = [d for d in da.dims if d != "time"]
    got = int(np.prod([da.sizes[d] for d in dims])) if dims else 1
    where = ""
    for cx, cy in (("x", "y"), ("lon", "lat")):
        if cx in data.coords and cy in data.coords:
            xs = np.atleast_1d(data[cx].values)
            ys = np.atleast_1d(data[cy].values)
            where = "  " + ", ".join(f"({a:.1f},{b:.1f})" for a, b in zip(xs, ys))
            break
    print(f"[bnd] {got} water-level support point(s){where}")
    if want is not None and got != want:
        raise RuntimeError(
            f"water-level boundary has {got} support points, expected {want} for "
            f"domain '{_domain.active().name}'.{where}\n"
            "  hydromt selects gauges by buffering the region, so extending the "
            "domain can pull an extra gauge in (or drop one) with no other symptom.\n"
            "  If this is INTENDED, change Domain.waterlevel_buffer and "
            "Domain.n_waterlevel_support together in nj_sfincs/domain.py and "
            "re-baseline — an inserted node is a forcing change, not a free one."
        )
    return got


def add_forcing(base: BaseConfig, sf: SfincsModel) -> None:
    """Phase 2 — window + physics flags and every compound forcing (no waves)."""
    sf.config.update(
        {
            "tref": base.tref,
            "tstart": base.tstart,
            "tstop": base.tstop,
            "tspinup": 3600.0,
            "coriolis": 1,
            "latitude": base.latitude,
            "advection": 1,
            "dtmapout": 3600.0,  # map output every hour
            "dtmaxout": 86400.0,  # one zsmax over the whole run
            "dthisout": 600.0,  # his output every 10 min
        }
    )

    sf.water_level.create(
        geodataset=base.waterlevel_geodataset,
        buffer=base.waterlevel_buffer,
        merge=False,
    )
    check_waterlevel_support(sf)
    sf.wind.create(wind="era5_nj")
    sf.pressure.create(press="era5_nj")
    sf.precipitation.create(
        precip="aorc_sandy_nj", cumulative_input=True, aggregate=False
    )
    sf.discharge_points.create(geodataset="usgs_sandy_discharge", merge=False)
    sf.quadtree_infiltration.create_cn(cn="cn_nj", antecedent_moisture=None, nrmax=2000)


def _point_wave_bnd(wcfg: WaveConfig, base: BaseConfig, sf: SfincsModel, pts):
    """Per-support-point wave forcing from an unstructured (time, node) point file.

    Returns ``(t, hs, tp, wd, ds)`` where every array except ``t`` is shaped
    ``(ntime, npoints)`` — one column per SnapWave support point, taken from that
    point's NEAREST source node.

    Two things here are load-bearing and neither is obvious:

    **The clock is referenced to ``base.tref``, not to the file's first timestamp.**
    The ERA5 path above computes ``t - t[0]`` and gets away with it only because
    `era5_waves_nj.nc` happens to start exactly at tref. A source padded earlier — CORA
    is built with a day of lead-in so interpolation never extrapolates at an endpoint —
    would silently shift the entire wave forcing by that pad. A 24 h offset on a storm
    whose peak is the whole point would not announce itself; it would just score badly.

    **Nearest-node lookup is checked, not trusted.** The distance to each chosen node
    and its source depth are printed and asserted, because a lookup that quietly lands
    on an estuarine or dry node produces a plausible-looking boundary file.
    """
    import pyproj

    path = Path(wcfg.wave_point_dataset)
    if not path.is_absolute():
        path = ROOT / path
    if not path.exists():
        raise FileNotFoundError(
            f"wave_point_dataset {path} not found — build it with "
            "scripts/build_cora_waves.py"
        )
    ds = xr.open_dataset(path)

    # Source nodes are lon/lat; support points are in the model's projected CRS.
    epsg = _domain.active().epsg
    tf = pyproj.Transformer.from_crs(epsg, 4326, always_xy=True)
    plon, plat = tf.transform(pts[:, 0], pts[:, 1])

    slon = np.asarray(ds["lon"].values, float)
    slat = np.asarray(ds["lat"].values, float)
    sdep = np.asarray(ds["depth"].values, float) if "depth" in ds else None

    idx, dist = [], []
    for lo, la in zip(plon, plat):
        # Local-scale planar distance is plenty at <1 km and avoids a geodesic call
        # per node; cos(lat) keeps the longitude degree honest.
        d = np.hypot((slon - lo) * np.cos(np.deg2rad(la)), slat - la) * 111_000.0
        j = int(np.argmin(d))
        idx.append(j)
        dist.append(d[j])
    idx = np.asarray(idx)
    dist = np.asarray(dist)

    print(f"[waves] point forcing from {path.name}: {ds.sizes['node']} source nodes, "
          f"{len(idx)} support points")
    for k, (lo, la, j, dk) in enumerate(zip(plon, plat, idx, dist)):
        dep = f"{sdep[j]:6.1f} m" if sdep is not None else "   n/a"
        print(f"[waves]   pt {k}: lon {lo:8.4f} lat {la:7.4f} -> node {j:6d} "
              f"({dk/1000:5.2f} km, source depth {dep})")
    if dist.max() > 5_000.0:
        raise RuntimeError(
            f"nearest source node is {dist.max()/1000:.1f} km from a support point "
            "(limit 5 km). The wave file does not cover this boundary; extend the "
            "search box in scripts/build_cora_waves.py rather than accepting it."
        )

    # Clip to the run window. Starting at tref keeps every emitted time >= 0, and the
    # pad before tref exists only so the source brackets the window.
    times = pd.to_datetime(ds["time"].values)
    keep = times >= pd.Timestamp(base.tref)
    if not keep.any():
        raise RuntimeError(f"{path.name} has no samples at/after tref {base.tref}")
    times = times[keep]
    t = (times - pd.Timestamp(base.tref)).total_seconds().to_numpy(float)

    out = []
    for var in ("hs", "tp", "wd"):
        a = np.asarray(ds[var].values, float)[np.asarray(keep)][:, idx]
        if not np.isfinite(a).all():
            raise RuntimeError(
                f"non-finite {var} in the selected {path.name} nodes — the builder is "
                "supposed to drop those; do not write NaN into a SnapWave boundary."
            )
        out.append(a)
    hs, tp, wd = out
    dspread = np.full_like(hs, 30.0)

    print(f"[waves] window {times[0]} .. {times[-1]}  (t = {t[0]:.0f} .. {t[-1]:.0f} s "
          f"from tref {base.tref})")
    print(f"[waves] peak Hs per point: "
          + ", ".join(f"{v:.2f}" for v in hs.max(axis=0))
          + f"   alongshore spread {np.ptp(hs.max(axis=0)):.2f} m")
    return t, hs, tp, wd, dspread


def add_waves(wcfg: WaveConfig, base: BaseConfig, sf: SfincsModel) -> dict:
    """Phase 2 cell 52 — the SnapWave block. Returns the ASCII boundary arrays.

    Adds Tim's physics params when ``wcfg.tune_physics`` and the ocean-side
    wavemaker when ``wcfg.wavemaker`` (both no-ops otherwise, so the default
    ``wind_waves`` preset reproduces the notebook byte-for-byte).
    """
    if wcfg.decouple_snapwave:
        # DECOUPLED: the wave solver gets its own, DEEPER domain. The SFINCS mask
        # (and with it the water-level boundary) is left untouched, so tide/surge
        # forcing stays at the coast while waves are imposed out on the shelf.
        # The X2 mesh already extends to lon -73.449 / -69 m: ~141k offshore cells
        # sit inactive purely because BaseConfig.mask_zmin cuts at -10 m.
        sf.quadtree_snapwave_mask.create_active(
            zmin=wcfg.snapwave_mask_zmin, copy_sfincsmask=False
        )
        # ...but `zmin` alone is NOT the seaward extension we want. create_active
        # rebuilds from scratch and admits EVERY cell above the threshold inside the
        # region, so -30 m also sweeps in the inland high ground (10,431 cells, up to
        # +106 m, lon -74.28..-74.10) that the SFINCS mask excludes by its own
        # include/exclude criteria. Those are SnapWave-active but SFINCS-INACTIVE and
        # dry -- precisely the X1 runaway geometry (a wave cell where SFINCS computes
        # no zs). So take the union we actually meant: everything the coupled premier
        # had, PLUS only the genuinely submerged band down to snapwave_mask_zmin.
        _sm = sf.quadtree_grid.data["mask"].values
        _zz = sf.quadtree_grid.data["z"].values
        _band = (
            (sf.quadtree_grid.data["snapwave_mask"].values > 0)
            & (_sm == 0)
            & np.isfinite(_zz)
            & (_zz <= base.mask_zmin)
        )
        # Interior is uniformly active (1); create_boundary below promotes the seaward
        # rim to 2. Copying the SFINCS codes verbatim would import mask==2/3 (the
        # water-level/outflow boundary at the COAST) as wave-boundary cells, which is
        # the coupling this arm exists to remove.
        sf.quadtree_grid.data["snapwave_mask"] = sf.quadtree_grid.data[
            "snapwave_mask"
        ].copy(data=np.where((_sm > 0) | _band, 1, 0).astype(_sm.dtype))
        # Wave boundary = the new SEAWARD edge, not the inherited SFINCS mask==2.
        # btype="waves" (snapwave's own vocabulary; "waterlevel" is SFINCS-only and
        # raises here). create_boundary picks cells on the ACTIVE-DOMAIN EDGE that
        # also satisfy zmax, so this ring is the seaward rim only — the landward
        # edge is far shallower than the cut and is filtered out.
        sf.quadtree_snapwave_mask.create_boundary(
            btype="waves", zmax=wcfg.snapwave_mask_zmin + SNAPWAVE_BND_RING
        )
    else:
        # X1 SnapWave: the wave solver shares the SFINCS mesh. Overwrite the fresh
        # snapwave_mask with the SFINCS mask so waves + hydrodynamics use one mesh.
        sf.quadtree_snapwave_mask.create_active(zmin=base.mask_zmin)
        sf.quadtree_grid.data["snapwave_mask"] = sf.quadtree_grid.data[
            "snapwave_mask"
        ].copy(data=sf.quadtree_grid.data["mask"].values.copy())

    # Incident-wave boundary = the OPEN-ATLANTIC edge only. Demote every snapwave
    # boundary cell north of the Sandy Hook tip back to active interior, so
    # incident waves don't run away into the enclosed NW corner (the ~1e13 blow-up).
    _swm = sf.quadtree_grid.data["snapwave_mask"].values.copy()
    _swfy = sf.quadtree_grid.data.grid.face_coordinates[:, 1]
    _demote = (_swm == 2) & (_swfy >= _open_coast_max_y())
    _swm[_demote] = 1
    sf.quadtree_grid.data["snapwave_mask"] = sf.quadtree_grid.data[
        "snapwave_mask"
    ].copy(data=_swm)

    # Support points = the DEEP (z<-5), open-Atlantic (y<tip) stretch of the
    # boundary, binned by northing, easternmost (seaward) cell per bin.
    # Decoupled: read the SNAPWAVE boundary (out on the shelf). Coupled: the
    # SFINCS mask==2 boundary, as X1 left it.
    N = wcfg.wave_n_support
    _fc = sf.quadtree_grid.data.grid.face_coordinates
    _z = sf.quadtree_grid.data["z"].values
    _bnd_src = "snapwave_mask" if wcfg.decouple_snapwave else "mask"
    _atl = (
        (sf.quadtree_grid.data[_bnd_src].values == 2)
        & np.isfinite(_z)
        & (_z < -5.0)
        & (_fc[:, 1] < _open_coast_max_y())
    )
    _bxy = _fc[_atl]
    _ybins = np.linspace(_bxy[:, 1].min(), _bxy[:, 1].max(), N + 1)
    snapwave_pts = np.array(
        [
            grp[np.argmax(grp[:, 0])]
            for k in range(N)
            for grp in [_bxy[(_bxy[:, 1] >= _ybins[k]) & (_bxy[:, 1] <= _ybins[k + 1])]]
            if len(grp)
        ]
    )

    if wcfg.wave_point_dataset is not None:
        snapwave_t, snapwave_hs, snapwave_tp, snapwave_wd, snapwave_ds = _point_wave_bnd(
            wcfg, base, sf, snapwave_pts
        )
    else:
        # Uniform alongshore forcing from the nearest valid ERA5 wave node.
        _ew = sf.data_catalog.get_rasterdataset(wcfg.wave_geodataset)
        _node = _ew.sel(
            x=wcfg.wave_era5_node[0], y=wcfg.wave_era5_node[1], method="nearest"
        )
        snapwave_t = (_node["time"].values - _node["time"].values[0]) / np.timedelta64(
            1, "s"
        )
        snapwave_hs = _node["hs"].values
        snapwave_tp = _node["tp"].values
        snapwave_wd = _node["wd"].values
        # ERA5 has no directional spreading; 30 deg
        snapwave_ds = np.full_like(snapwave_hs, 30.0)

    # Optional ocean-side wavemaker (native hydromt call; writes sfincs.wvm).
    if wcfg.wavemaker:
        sf.wave_makers.create(str(wcfg.wavemaker_line), merge=False)

    cfg = {
        "snapwave": 1,
        "snapwave_igwaves": int(wcfg.wave_igwaves),
        "snapwave_wind": int(wcfg.wave_wind),
        "snapwave_sector": wcfg.sector(),
        "dtwave": wcfg.dtwave,
        "storewavdir": 1,
    }
    if wcfg.tune_physics:
        cfg.update(
            {
                "snapwave_alpha": wcfg.snapwave_alpha,
                "snapwave_gamma": wcfg.snapwave_gamma,
                "snapwave_hmin": wcfg.snapwave_hmin,
                "snapwave_dtheta": wcfg.snapwave_dtheta,
                "snapwave_fw": wcfg.snapwave_fw,
                "snapwave_niter": wcfg.snapwave_niter,
                "storefw": wcfg.storefw,
            }
        )
    sf.config.update(cfg)

    return {
        "pts": snapwave_pts,
        "t": snapwave_t,
        "hs": snapwave_hs,
        "tp": snapwave_tp,
        "wd": snapwave_wd,
        "ds": snapwave_ds,
    }


def set_inp_keys(inp: Path, kv: dict) -> None:
    """Set/overwrite ``key = value`` lines in a sfincs.inp, appending any that are absent."""
    lines = Path(inp).read_text().splitlines()
    have = {ln.split("=")[0].strip() for ln in lines if "=" in ln}
    out = [
        f"{ln.split('=')[0].strip():<20} = {kv[ln.split('=')[0].strip()]}"
        if "=" in ln and ln.split("=")[0].strip() in kv
        else ln
        for ln in lines
    ]
    out += [f"{k:<20} = {v}" for k, v in kv.items() if k not in have]
    Path(inp).write_text("\n".join(out) + "\n")


def restore_diagnostics(model_dir: Path) -> None:
    """Re-enable the flux/mass-budget diagnostics that ``sf.write()`` drops.

    hydromt's writer knows nothing about ``crsfile`` (cross-sections) or ``storevel``, so a
    freshly staged experiment silently comes back with no cross-sections and ``storevel = 0``
    — i.e. no mass budget, and an inp that differs from the premier's for reasons that have
    nothing to do with the experiment. Both phase-lag arms had to be hand-patched before
    submission because of this; ``scripts/setup_sealed_premier.py`` carried the only copy of
    the fix. Call this after :func:`finalize` on every staging path.
    """
    model_dir = Path(model_dir)
    crs_src = ROOT / "data" / "flux_crosssections.crs"
    kv = {"storevel": "1"}
    if crs_src.exists():
        shutil.copy2(crs_src, model_dir / "sfincs.crs")
        kv["crsfile"] = "sfincs.crs"
    else:  # never point crsfile at a file the solver cannot open
        print(f"[warn] {crs_src} missing — staging without cross-sections")
    set_inp_keys(model_dir / "sfincs.inp", kv)


def finalize(
    wcfg: WaveConfig,
    base: BaseConfig,
    sf: SfincsModel,
    model_dir: Path,
    sw: dict | None,
) -> None:
    """Phase 2 cell 54 — release handles, write, patch sfincs.inp, write ASCII.

    Called for EVERY experiment (waves or not). When ``wcfg.wavemaker`` the
    ``wvmfile`` key + ``sfincs.wvm`` are preserved (the notebook always stripped
    them, which is why the wavemaker was disabled — do NOT strip here).
    """
    model_dir = Path(model_dir)

    # Materialize forcing in memory, drop xarray's open-file cache, so every
    # handle closes before write (avoids Errno 13 on /cache when re-writing a
    # file this kernel still holds open).
    for _c in (
        sf.water_level,
        sf.discharge_points,
        sf.wind,
        sf.pressure,
        sf.precipitation,
    ):
        try:
            if _c.data is not None:
                _c.data.load()
        except Exception:
            pass
    xr.backends.file_manager.FILE_CACHE.clear()
    gc.collect()

    sf.write()

    inp = model_dir / "sfincs.inp"
    text = inp.read_text()

    # (a) latitude — dropped on write, so Coriolis silently disables without it.
    if "\nlatitude" not in text:
        text = text.replace(
            "coriolis             = 1",
            f"coriolis             = 1\nlatitude             = {base.latitude}",
        )

    # (b) strip orphan infiltration keys (component sets key but writes no file).
    text = (
        "\n".join(
            ln
            for ln in text.splitlines()
            if not ln.strip().startswith(
                ("infiltration_file", "infiltration_type", "scsfile")
            )
        )
        + "\n"
    )

    # (c) waves: ensure SnapWave keys + write the ASCII boundary forcing.
    if wcfg.use_waves:
        if not wcfg.wavemaker:
            # Drop any stale wavemaker key (only when this run has no wavemaker).
            text = (
                "\n".join(
                    ln
                    for ln in text.splitlines()
                    if not ln.strip().startswith("wvmfile")
                )
                + "\n"
            )
        sw_keys = {
            "snapwave": "1",
            "snapwave_igwaves": str(int(wcfg.wave_igwaves)),
            "snapwave_wind": str(int(wcfg.wave_wind)),
            "snapwave_sector": str(wcfg.sector()),
            "dtwave": str(wcfg.dtwave),
            "storewavdir": "1",
            "snapwave_bndfile": "snapwave.bnd",
            "snapwave_bhsfile": "snapwave.bhs",
            "snapwave_btpfile": "snapwave.btp",
            "snapwave_bwdfile": "snapwave.bwd",
            "snapwave_bdsfile": "snapwave.bds",
        }
        if wcfg.tune_physics:
            sw_keys.update(
                {
                    "snapwave_alpha": str(wcfg.snapwave_alpha),
                    "snapwave_gamma": str(wcfg.snapwave_gamma),
                    "snapwave_hmin": str(wcfg.snapwave_hmin),
                    "snapwave_dtheta": str(wcfg.snapwave_dtheta),
                    "snapwave_fw": str(wcfg.snapwave_fw),
                    "snapwave_niter": str(wcfg.snapwave_niter),
                    "storefw": str(wcfg.storefw),
                }
            )
        present = {ln.split("=")[0].strip() for ln in text.splitlines() if "=" in ln}
        for k, v in sw_keys.items():
            if k not in present:
                text += f"{k:<20} = {v}\n"

        # Remove stale files keyed to an old config (would crash the solver).
        for stale in ("snapwave.upw", "snapwave.nc"):
            (model_dir / stale).unlink(missing_ok=True)
        if not wcfg.wavemaker:
            (model_dir / "sfincs.wvm").unlink(missing_ok=True)

        pts = sw["pts"]
        np.savetxt(model_dir / "snapwave.bnd", pts, fmt="%.3f")
        for fn, series in [
            ("snapwave.bhs", sw["hs"]),
            ("snapwave.btp", sw["tp"]),
            ("snapwave.bwd", sw["wd"]),
            ("snapwave.bds", sw["ds"]),
        ]:
            arr = np.asarray(series)
            # 1-D => one series broadcast to every support point (the ERA5 path, whose
            # 31 km cell cannot resolve the boundary anyway). 2-D => already one column
            # PER POINT (the point-source path), so it must NOT be tiled — tiling a
            # 2-D array here would silently emit a garbage-shaped boundary file.
            if arr.ndim == 1:
                block = np.tile(arr[:, None], (1, len(pts)))
            elif arr.shape == (len(sw["t"]), len(pts)):
                block = arr
            else:
                raise ValueError(
                    f"{fn}: wave series has shape {arr.shape}, expected "
                    f"({len(sw['t'])},) or ({len(sw['t'])}, {len(pts)})"
                )
            np.savetxt(
                model_dir / fn,
                np.column_stack([sw["t"], block]),
                fmt=["%11.1f"] + ["%11.3f"] * len(pts),
            )

    inp.write_text(text)
