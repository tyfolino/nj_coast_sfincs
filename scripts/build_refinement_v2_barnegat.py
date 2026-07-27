"""Build the quadtree refinement polygons for domain `v2_barnegat`.

Base cell is 200 m, halved once per refinement level:
    level 0 = 200 m   level 1 = 100 m   level 2 = 50 m   level 3 = 25 m

Refinement is gated BOTH by polygon and by elevation: a cell is refined only if
its z range overlaps [zmin, zmax]. The depth gates do most of the work here —
they are what lets one box cover the bay without also refining the deep shelf.

────────────────────────────────────────────────────────────────────────────
THE COST PROBLEM THIS IS SOLVING
────────────────────────────────────────────────────────────────────────────
v1's recipe put the shelf at level 1 (100 m) and everything in z -8..+3 at
level 3 (25 m). Applied unchanged to v2 that is ruinous, for two separate
reasons:

  1. The shelf. v2 adds ~1,700 km2 of open shelf. At 100 m that is ~170k cells
     for water where wave refraction varies on kilometre scales. Dropped to the
     200 m base below -20 m — the single biggest saving available, and the one
     with the least physical cost.

  2. Barnegat Bay. The bay floor is -1 to -3.6 m, which sits squarely inside
     v1's level-3 gate of -8..+3. Applying it would refine all ~280 km2 of the
     lagoon to 25 m: ~450k cells, roughly the size of the ENTIRE v1 mesh, for
     open shallow water. The same trap the v1 script hit with Raritan Bay and
     solved the same way — bay interior at level 2, level 3 reserved for the
     shallow fringe.

So the tiering is deliberately asymmetric: fine where the physics is sharp
(inlets, surf zone, barrier crests, marsh edge), coarse where it is smooth
(shelf, open bay, high ground).

────────────────────────────────────────────────────────────────────────────
BAY / OCEAN SEPARATION
────────────────────────────────────────────────────────────────────────────
The level-3 surf-and-dune gate (-8..+3) cannot tell the surf zone from the bay
— both are in that depth band. They are separated geometrically instead, by a
sloped line following the barrier's bay-side shore. Measured from the merged
DEM, that shore runs x = 576,659 at Barnegat Inlet (y 4,402,058) to x = 582,675
at Manasquan Inlet (y 4,439,640) — a slope of 0.160 m east per m north.

The line is placed ~700 m WEST of the fitted shore on purpose. Erring west puts
a strip of back-bay into the 25 m zone rather than dropping part of the barrier
to 50 m, and the bay side of the barrier is exactly where overwash deposits and
back-bay flooding are decided.

Run:
    NJ_ROOT=$PWD PYTHONPATH=$PWD python scripts/build_refinement_v2_barnegat.py
Output:
    data/quadtree/refinement_v2_barnegat.geojson  (EPSG:32618)
"""

from __future__ import annotations

import os
from pathlib import Path

import geopandas as gpd
from shapely.geometry import Polygon, box

import nj_sfincs  # noqa: F401  (PROJ primer)

ROOT = Path(os.environ.get("NJ_ROOT", Path(__file__).resolve().parents[1]))
V1_REFINEMENT = ROOT / "data" / "quadtree" / "refinement_polygons_25m.geojson"
OUT = ROOT / "data" / "quadtree" / "refinement_v2_barnegat.geojson"
GRID_EPSG = 32618

# ── Southern lobe extent (UTM 18N) ───────────────────────────────────────────
# y: 4,394,000 (lat 39.70, the Manahawkin cut) .. 4,446,000 (lat 40.15, where v1
# takes over — overlap by ~1 km so there is no unrefined seam at the join).
S_Y0, S_Y1 = 4_394_000, 4_446_000

# Barrier bay-side shore, as x = B_X0 + B_SLOPE * (y - B_Y0). See header.
B_X0, B_Y0, B_SLOPE = 576_000, 4_402_000, 0.160

# Longitudinal limits of the southern lobe, in x.
S_X_WEST = 562_000     # west of the Toms River / Metedeconk tidal limits
S_X_L1_EAST = 586_000  # ~ the -20 m isobath: level-1 shoaling band stops here
S_X_OCEAN = 600_000    # seaward limit of any refinement at all

# ── Elevation gates (m NAVD88, positive up) ──────────────────────────────────
L1_SHELF = (-20.0, 2.0)     # 100 m: shoaling band only; below -20 m stays 200 m
L2_COASTAL = (-20.0, 5.0)   # 50 m: bay floor, marsh, barrier, low floodplain
L3_SURF = (-8.0, 3.0)       # 25 m: surf zone, foredune, barrier
L3_BAY_FRINGE = (-0.8, 2.0)  # 25 m: bay MARGIN only — interior is deeper, so it
                             # stays at 50 m and the lagoon does not explode
L1_UPLAND = (3.0, 9.0)      # 100 m: transition band only

# THE LAND CEILING, and why these two gates stop where they do. The first probe
# put 65% of the southern lobe's active cells on LAND, so the land gates are the
# only ones with real headroom left (the deep shelf costs almost nothing — the
# SFINCS mask already drops everything below -10 m, leaving just ~9k active cells
# deeper than that in the entire domain).
#
# Measured Sandy high-water marks bound it: the southern lobe's HIGHEST mark is
# 3.66 m NAVD88 (p95 = 3.00 m), and the highest anywhere in the domain is 5.79 m.
# So +5 m still covers every flooded cell in the lobe with margin, and NOTHING in
# this event reaches +9 m. Above that, 200 m base cells are meshing ground the
# water never touches.


def _barrier_x(y: float) -> float:
    return B_X0 + B_SLOPE * (y - B_Y0)


def _east_of_barrier() -> Polygon:
    """Everything seaward of the sloped barrier line, within the southern lobe."""
    return Polygon([
        (_barrier_x(S_Y0), S_Y0),
        (S_X_OCEAN, S_Y0),
        (S_X_OCEAN, S_Y1),
        (_barrier_x(S_Y1), S_Y1),
    ])


def _west_of_barrier() -> Polygon:
    """The lagoon + mainland side, within the southern lobe."""
    return Polygon([
        (S_X_WEST, S_Y0),
        (_barrier_x(S_Y0), S_Y0),
        (_barrier_x(S_Y1), S_Y1),
        (S_X_WEST, S_Y1),
    ])


def main() -> None:
    rows = []

    # ── v1's polygons, verbatim ──────────────────────────────────────────────
    # The northern part of the domain is unchanged, so its refinement should be
    # too: this keeps the mesh over v1's footprint comparable rather than
    # gratuitously different, which matters for the bridge-rescore against the
    # sealed premier.
    v1 = gpd.read_file(V1_REFINEMENT).to_crs(GRID_EPSG)
    for _, r in v1.iterrows():
        rows.append(r.to_dict())

    east, west = _east_of_barrier(), _west_of_barrier()
    lobe = box(S_X_WEST, S_Y0, S_X_OCEAN, S_Y1)

    def add(name, level, gate, geom, why):
        rows.append({
            "name": name, "refinement_level": level,
            "zmin": gate[0], "zmax": gate[1], "geometry": geom, "why": why,
        })

    # ── Southern lobe ────────────────────────────────────────────────────────
    add("s_shelf", 1, L1_SHELF,
        box(_barrier_x(S_Y0), S_Y0, S_X_L1_EAST, S_Y1).intersection(east),
        "100 m across the shoaling band; deeper than -20 m stays at the 200 m base, "
        "because shelf wave refraction varies on km scales.")

    add("s_coastal", 2, L2_COASTAL, lobe,
        "50 m over the bay floor, marsh, barrier and low floodplain — the working "
        "resolution for the lagoon interior.")

    add("s_upland", 1, L1_UPLAND, lobe,
        "100 m on higher inland ground, purely so land steps 50 -> 100 -> 200 m "
        "instead of jumping two levels at once.")

    add("s_surf_dune", 3, L3_SURF, east,
        "25 m in the surf zone, foredune and barrier — seaward of the sloped "
        "barrier line so this gate cannot reach into the bay, which shares its "
        "depth band.")

    add("s_bay_fringe", 3, L3_BAY_FRINGE, west,
        "25 m on the bay MARGIN only (-0.8..+2 m): shoreline, marsh and mudflat. "
        "The lagoon interior is deeper than -0.8 m so it stays at 50 m.")

    gdf = gpd.GeoDataFrame(rows, crs=GRID_EPSG)
    gdf = gdf[~gdf.geometry.is_empty & gdf.geometry.notna()]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_file(OUT, driver="GeoJSON")

    print(f"wrote {OUT}  ({len(gdf)} polygons)")
    for _, r in gdf.iterrows():
        a = r.geometry.area / 1e6
        print(f"  L{int(r['refinement_level'])}  {str(r.get('name')):16s} "
              f"z[{r['zmin']:>7}, {r['zmax']:>6}]  {a:8.1f} km2")


if __name__ == "__main__":
    main()
