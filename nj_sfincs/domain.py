"""Domain registry — the geography that used to be module-level constants.

In ``nj_sandy_sfincs`` every geographic fact about the model was a literal
somewhere: ``SANDY_HOOK_TIP_Y = 4_476_000`` in ``model.py``, a sloped-easting HWM
basin classifier in ``validate.py``, a ``SHREWSBURY_WINDOW`` in ``plots.py``,
``latitude = 40.32`` in ``config.py``, and a hand-typed bbox in half the download
scripts. That was fine for exactly one domain. This repo is meant to march south
to Cape May in increments, so each increment would otherwise mean hunting the
same dozen literals through five modules — and silently getting a stale one wrong.

A ``Domain`` bundles them. ``DOMAINS`` maps a name to one, ``NJ_DOMAIN`` selects
it, and ``active()`` returns it. ``v1_monmouth`` reproduces the sealed premier's
geography verbatim so the old behaviour stays reachable and diffable.

The rule of thumb for what belongs here: if extending the model south would make
a number wrong, it is domain geography and belongs in ``Domain``. If it would
stay right (a physics constant, a solver tolerance, a datum offset), it does not.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

ROOT = Path(os.environ.get("NJ_ROOT", Path(__file__).resolve().parents[1]))
DATA = ROOT / "data"


@dataclass(frozen=True)
class ObsGauge:
    """One SFINCS observation point + how to score it.

    ``name`` is what lands in ``sfincs.obs`` and therefore in ``sfincs_his.nc``;
    every his-based metric matches it by substring, so it must stay unique.
    ``obs_file`` / ``obs_var`` / ``obs_station`` say where the OBSERVED series
    lives (relative to ``data/``); ``None`` means model-only (no scoring).
    ``kind`` is ``surge`` (compare the peak) or ``tide`` (compare range/phase).
    """

    name: str
    lon: float
    lat: float
    kind: str = "surge"
    obs_file: str | None = None
    obs_var: str | None = None
    obs_station: str | int | None = None
    note: str = ""


@dataclass(frozen=True)
class MaskOverride:
    """One rectangular mask reclass, applied after hydromt sets the boundaries.

    ``frm``/``to`` are SFINCS mask codes (1 active, 2 waterlevel BC, 3 outflow).
    Box is in the domain's projected CRS: ``(xmin, ymin, xmax, ymax)``, with
    ``None`` meaning unbounded on that side.
    """

    name: str
    frm: int
    to: int
    box: tuple[float | None, float | None, float | None, float | None]
    why: str = ""


@dataclass(frozen=True)
class BasinRule:
    """One HWM reporting basin, as coordinate thresholds in the domain CRS.

    Rules are evaluated IN ORDER and the FIRST match wins, so write them
    most-specific first. The last rule should be an unconstrained catch-all.

    Thresholds rather than hand-drawn polygons is a deliberate choice: a box and
    a slope are auditable numbers that can be checked against a chart, whereas a
    digitised polygon is opaque once written. The one concession to geometry is
    ``slope``, because the NJ barrier coast runs NNE — so the ocean/estuary
    divide is a SLOPED easting, ``x = slope_x0 + slope * (y - slope_y0)``, and
    ``side`` selects east (+1) or west (-1) of it.
    """

    name: str
    xmin: float | None = None
    ymin: float | None = None
    xmax: float | None = None
    ymax: float | None = None
    slope_x0: float | None = None
    slope_y0: float | None = None
    slope: float = 0.0
    side: int = 1
    why: str = ""

    def matches(self, x, y):
        import numpy as np

        ok = np.ones(np.shape(x), dtype=bool)
        if self.xmin is not None:
            ok &= x >= self.xmin
        if self.xmax is not None:
            ok &= x < self.xmax
        if self.ymin is not None:
            ok &= y >= self.ymin
        if self.ymax is not None:
            ok &= y < self.ymax
        if self.slope_x0 is not None:
            div = self.slope_x0 + self.slope * (y - self.slope_y0)
            ok &= (x > div) if self.side > 0 else (x <= div)
        return ok


@dataclass(frozen=True)
class Domain:
    name: str
    region: Path
    epsg: int
    latitude: float  # Coriolis reference [deg N] — domain mean
    # Quadtree refinement polygons for THIS domain. v1's recipe is not reusable
    # as-is on a larger domain: its level-3 gate (-8..+3 m) would refine all of
    # Barnegat Bay to 25 m, and its level-1 shelf polygon would refine ~1,700 km2
    # of open shelf to 100 m.
    refinement: Path = DATA / "quadtree" / "refinement_polygons_25m.geojson"
    obs_gauges: tuple[ObsGauge, ...] = ()
    mask_overrides: tuple[MaskOverride, ...] = ()
    # Force these lon/lat boxes active at any depth, so dredged channels don't
    # punch inactive holes through a bay interior.
    always_active_boxes_ll: tuple[tuple[float, float, float, float], ...] = ()
    # Northing above which the coast is no longer open ocean (a spit tip, a
    # harbour mouth). Wave-boundary support points are only taken below it.
    open_coast_max_y: float | None = None
    # Ordered HWM basin rules, first match wins. Splitting marks by hydraulic
    # basin stops the pooled RMSE from blending ocean-front marks (surge
    # delivered directly, the model gets them right) with behind-barrier estuary
    # marks (the conveyance test). Pooling them once hid a completely dammed
    # inlet behind a near-perfect basin bias.
    hwm_rules: tuple[BasinRule, ...] = ()
    # Default map window for the diagnostic panels (xmin, xmax, ymin, ymax).
    plot_window: tuple[float, float, float, float] | None = None

    def bbox_ll(self, buffer_deg: float = 0.0) -> tuple[float, float, float, float]:
        """Region bounding box in WGS-84 as ``(west, south, east, north)``.

        This is the single source of truth for every download/clip extent. The
        old repo hand-typed a bbox into ``download_3dep.py``,
        ``download_pre_sandy_topobathy.py`` and ``download_gmrt.py``, each with a
        comment reading "update this if region.geojson changes" — three separate
        chances to forget. Pass a small ``buffer_deg`` so a clipped raster covers
        the region's edge cells rather than ending exactly on them.
        """
        return _bbox_ll(self.region, buffer_deg)


@lru_cache(maxsize=8)
def _bbox_ll(region: Path, buffer_deg: float) -> tuple[float, float, float, float]:
    import geopandas as gpd

    w, s, e, n = gpd.read_file(region).to_crs(4326).total_bounds
    b = buffer_deg
    # Cast off numpy scalars: these values get formatted straight into gdal
    # command lines, and np.float64 reprs ("np.float64(-74.3)") poison them.
    return (
        round(float(w) - b, 6), round(float(s) - b, 6),
        round(float(e) + b, 6), round(float(n) + b, 6),
    )


# ── Validation gauges ────────────────────────────────────────────────────────
# v1's four, verbatim from model.py's inline `val_gauges` list.
_SANDY_HOOK = ObsGauge(
    "sandy_hook", -74.0091, 40.4669, "surge",
    "gtsm/noaa_sandy_validation.nc", "waterlevel", 8531680,
    "NOAA CO-OPS. Failed mid-storm ~2012-10-29 23:00 — score the PRE-FAILURE peak only.",
)
_SSS_SEA_BRIGHT = ObsGauge(
    "usgs_stormtide_sea_bright", -73.97304, 40.37222, "surge",
    "gtsm/sandy_storm_tide_nj.nc", "stormtide_m", 2258,
    "USGS SSS rapid-deployment wave sensor — the only open-coast record that survived the peak.",
)
_USGS_SEA_BRIGHT = ObsGauge(
    "usgs_tidal_sea_bright", -73.97494, 40.36557, "tide",
    "gtsm/usgs_sandy_tidal_nj.nc", None, 1407600,
    "Shrewsbury R. Nudged 21 m into the channel — the raw coords snap to a dry bank. "
    "Record ends ~10-29 04:00, so tidal range/phase only, not the peak.",
)
_USGS_SHARK = ObsGauge(
    "usgs_tidal_shark_river", -74.0261, 40.1856, "tide",
    "gtsm/usgs_sandy_tidal_nj.nc", None, 1407770,
    "Shark R. Record ends ~10-29 04:00 — pre-storm tide only.",
)

# ── NEW in v2_barnegat: the first interior gauges that survive Sandy's peak ─────
# Every permanent gauge inside the v1 domain died mid-storm, so the peak was only
# ever scored against HWMs plus the one open-coast wave sensor above. These two
# are complete 6-min records straight through the crest, and they disagree with
# each other in the most useful possible way: Mantoloking (mid-lagoon, 35 km from
# the inlet) peaks 0.52 m HIGHER and ~6 h LATER than Barnegat Light (at the
# inlet). That pair constrains bay conveyance and inlet exchange far harder than
# any single peak level, so score BOTH level and timing at both.
_BB_MANTOLOKING = ObsGauge(
    "usgs_tidal_bb_mantoloking", -74.0544444, 40.0405556, "surge",
    "gtsm/usgs_sandy_tidal_nj.nc", None, 1408168,
    "Barnegat Bay at Mantoloking. 721 pts, max gap 6 min, complete through the peak. "
    "Observed peak 2.11 m NAVD88 at 2012-10-30 06:18 UTC.",
)
_BB_BARNEGAT_LIGHT = ObsGauge(
    "usgs_tidal_bb_barnegat_light", -74.1105556, 39.7608333, "surge",
    "gtsm/usgs_sandy_tidal_nj.nc", None, 1409125,
    "Barnegat Bay at Barnegat Light, just inside the inlet. 708 pts, max gap 18 min. "
    "Observed peak 1.59 m NAVD88 at 2012-10-30 00:24 UTC. Sits inside the 6 km buffer "
    "to the artificial south edge, so it is also the check on that boundary.",
)
_BB_SHIP_BOTTOM = ObsGauge(
    "usgs_tidal_bb_ship_bottom", -74.1858333, 39.6541667, "tide",
    "gtsm/usgs_sandy_tidal_nj.nc", None, 1409146,
    "East Thorofare at Ship Bottom. PARTIAL — ends 2012-10-28, so pre-storm tide only. "
    "Also sits SOUTH of the 39.70 domain edge; kept for reference, not scored.",
)
_SSS_BARNEGAT_INLET = ObsGauge(
    "usgs_stormtide_barnegat_inlet", -74.104167, 39.763611, "surge",
    "gtsm/sandy_storm_tide_nj.nc", "stormtide_m", None,
    "USGS SSS-NJ-OCE-001WV/BP, deployed in Barnegat Inlet itself.",
)

# ── Mask overrides (UTM 18N) ─────────────────────────────────────────────────
# Carried over from v1 unchanged: all three are absolute northings/eastings in
# the NORTHERN part of the domain, which v2 does not move.
#
# ⚠️ ONE BOUND ADDED vs v1, and it matters. v1 wrote this as
#     west_below_bay = (fx < 582_500) & (fy < 4_474_000)
# with NO southern limit. That was harmless only because v1's domain stopped at
# lat 40.15 (y ~4,444,800), so the box could not reach past it. In v2 the domain
# runs down to y ~4,394,700 and the unbounded form catches essentially the WHOLE
# new lobe — Barnegat Inlet (577,096 / 4,401,119), the Manahawkin cut, Toms River,
# Mantoloking — converting every waterlevel boundary cell down there into a free
# outflow. Adding `ymin = 4_440_000` confines it to the territory it was written
# for (v1's west edge at x ~577,000, y 4,444,800..4,470,300).
#
# The bound is BEHAVIOUR-PRESERVING for v1_monmouth: every cell in that domain sits
# above y = 4,444,000, so nothing it used to catch falls outside the new bound.
# This is the exact failure mode the registry exists to prevent — a constant that
# is silently correct on one domain and silently wrong on the next.
_V1_MASK_OVERRIDES = (
    MaskOverride(
        "west_below_bay", 2, 3, (None, 4_440_000, 582_500, 4_474_000),
        "waterlevel -> outflow: v1's west edge is a true domain edge with no ocean "
        "beyond it, so it must not have an open-ocean level imposed.",
    ),
    MaskOverride(
        "shrewsbury", 2, 1, (586_500, 4_467_000, 587_400, 4_472_000),
        "waterlevel -> active interior: the Shrewsbury narrows are interior water, "
        "not a place to impose an open-ocean level.",
    ),
    MaskOverride(
        "arthur_kill_north", 3, 2, (None, 4_484_000, None, None),
        "outflow -> waterlevel: the north edge is harbour-driven, so it needs a level, "
        "not a free outflow.",
    ),
)

# ── v2_barnegat only ────────────────────────────────────────────────────────────
# The 39.70 south edge crosses ~2.4 km of Manahawkin Bay at up to -3.9 m. hydromt
# sees deep water on a domain edge and does the obvious thing: 55 cells came back
# as mask==2, a WATER-LEVEL boundary. That is wrong, and wrong in a way that would
# have quietly invalidated the whole reason for extending the domain.
#
# A mask==2 cell has the interpolated OPEN-OCEAN level imposed on it. Putting that
# across the bay cross-section drives Barnegat Bay directly from its southern end,
# in parallel with — and competing against — the exchange through Barnegat Inlet.
# The two new gauges exist precisely to measure that exchange (Mantoloking peaks
# 0.52 m higher and ~6 h later than Barnegat Light), so forcing the bay from the
# south would corrupt the one signal the extension was built to capture.
#
# Same treatment as the Shrewsbury narrows: demote to ordinary active interior.
# SFINCS's default for the inactive ground beyond is a closed wall, which is the
# honest choice here — the real bay does continue south to Little Egg Inlet, so a
# wall omits that exchange, but omitting it is bounded and local, whereas imposing
# an ocean level actively pumps the lagoon. The 6 km buffer to Barnegat Inlet is
# the margin, and the Barnegat Light gauge sits inside it as the check.
_MANAHAWKIN_CUT = MaskOverride(
    "manahawkin_cut", 2, 1, (569_000, 4_390_000, 573_500, 4_400_000),
    "waterlevel -> active interior: the south edge crosses INTERIOR bay water, "
    "which must not have an open-ocean level imposed on it.",
)

# ── HWM basins ───────────────────────────────────────────────────────────────
# v1's five, re-expressed as ordered rules. Same numbers, same outcome — there is
# a test that asserts this reproduces the original classifier exactly.
_BARRIER = dict(slope_x0=586_000, slope_y0=4_456_000, slope=0.075)  # NNE barrier axis

_V1_BASIN_RULES = (
    BasinRule("shark_river", xmax=584_300, ymax=4_450_800,
              why="Fed through Shark River Inlet, so these are a CONVEYANCE test, not "
                  "an open-coast one. Split out of south_coast after pooling hid the "
                  "dammed inlet: the estuary marks were dry and silently dropped, so "
                  "the basin reported a near-perfect -0.055 m bias while the river "
                  "behind it never wetted at all."),
    BasinRule("south_coast", ymax=4_458_000,
              why="Belmar/Avon ocean front — surge delivered directly."),
    BasinRule("sandy_hook_bay", ymin=4_474_000,
              why="Open Sandy Hook / Raritan Bay."),
    BasinRule("atlantic_oceanfront", ymin=4_458_000, ymax=4_474_000, side=+1, **_BARRIER,
              why="Seaward of the Sea Bright barrier axis."),
    BasinRule("shrewsbury_navesink",
              why="Catch-all: the behind-barrier estuaries — the conveyance test."),
)

# ── NEW basins for the southern lobe ─────────────────────────────────────────
# These MUST come first: v1's `south_coast` rule is `y < 4,458,000` with no lower
# bound, so on the v2 domain it would swallow every mark in the entire new lobe
# and report Barnegat Bay marks as "south_coast". Another instance of a v1
# constant that is silently correct on v1 and silently wrong on v2.
#
# The barrier divide reuses the SAME sloped line as the refinement polygons
# (x = 576,000 + 0.160*(y - 4,402,000)), fitted to the barrier's bay-side shore
# between Barnegat and Manasquan Inlets, so the two never disagree about which
# side of the barrier a point is on.
_S_BARRIER = dict(slope_x0=576_000, slope_y0=4_402_000, slope=0.160)
_V2_SOUTH_RULES = (
    BasinRule("manasquan", xmax=582_600, ymin=4_434_000, ymax=4_443_000,
              why="Manasquan River estuary, behind the inlet — a conveyance basin."),
    BasinRule("barnegat_barrier", ymax=4_444_000, side=+1, **_S_BARRIER,
              why="Ocean-front barrier: Island Beach, Bay Head/Mantoloking and the "
                  "north end of LBI. Includes the Mantoloking breach zone."),
    BasinRule("barnegat_bay", ymax=4_444_000,
              why="The lagoon and its mainland shore — behind-barrier, so the "
                  "conveyance test for Barnegat and Manasquan Inlets."),
)

V1_MONMOUTH = Domain(
    name="v1_monmouth",
    region=DATA / "region_v1_monmouth.geojson",
    epsg=32618,
    latitude=40.32,
    obs_gauges=(_SANDY_HOOK, _SSS_SEA_BRIGHT, _USGS_SEA_BRIGHT, _USGS_SHARK),
    mask_overrides=_V1_MASK_OVERRIDES,
    always_active_boxes_ll=((-74.28, 40.40, -73.95, 40.52),),
    open_coast_max_y=4_476_000,
    hwm_rules=_V1_BASIN_RULES,
    plot_window=(578_500, 592_000, 4_462_000, 4_482_000),
)

V2_BARNEGAT = Domain(
    name="v2_barnegat",
    region=DATA / "region_v2_barnegat.geojson",
    epsg=32618,
    refinement=DATA / "quadtree" / "refinement_v2_barnegat.geojson",
    # Domain-mean latitude for Coriolis: (39.70 + 40.52) / 2. v1 used 40.32 for a
    # domain spanning 40.15-40.52; keeping 40.32 here would bias f by ~0.5% at the
    # southern end. Small, but free to get right.
    latitude=40.11,
    obs_gauges=(
        _SANDY_HOOK, _SSS_SEA_BRIGHT, _USGS_SEA_BRIGHT, _USGS_SHARK,
        _BB_MANTOLOKING, _BB_BARNEGAT_LIGHT, _SSS_BARNEGAT_INLET,
    ),
    mask_overrides=(_MANAHAWKIN_CUT,) + _V1_MASK_OVERRIDES,
    always_active_boxes_ll=((-74.28, 40.40, -73.95, 40.52),),
    open_coast_max_y=4_476_000,
    hwm_rules=_V2_SOUTH_RULES + _V1_BASIN_RULES,
    plot_window=(578_500, 592_000, 4_462_000, 4_482_000),
)

DOMAINS: dict[str, Domain] = {d.name: d for d in (V1_MONMOUTH, V2_BARNEGAT)}

DEFAULT_DOMAIN = "v2_barnegat"


def classify_hwm_basin(x, y, dom: "Domain | None" = None):
    """Label each HWM (easting/northing in the domain CRS) by hydraulic basin.

    First matching rule wins; anything unmatched is ``"unassigned"`` rather than
    being silently folded into a real basin, so a mark that falls outside every
    rule shows up as a visible bucket instead of quietly biasing a neighbour.
    """
    import numpy as np

    dom = dom or active()
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    basin = np.full(x.shape, "unassigned", dtype=object)
    todo = np.ones(x.shape, dtype=bool)
    for rule in dom.hwm_rules:
        if not todo.any():
            break
        hit = todo & rule.matches(x, y)
        basin[hit] = rule.name
        todo &= ~hit
    return basin


def hwm_basin_names(dom: "Domain | None" = None) -> tuple[str, ...]:
    dom = dom or active()
    return tuple(r.name for r in dom.hwm_rules)


def active() -> Domain:
    """The domain this process is working on (``NJ_DOMAIN`` env var)."""
    name = os.environ.get("NJ_DOMAIN", DEFAULT_DOMAIN)
    if name not in DOMAINS:
        raise KeyError(
            f"NJ_DOMAIN={name!r} is not a known domain. Known: {sorted(DOMAINS)}"
        )
    return DOMAINS[name]
