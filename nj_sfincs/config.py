"""Configuration for the NJ Sandy SFINCS build + wave-sensitivity experiments.

This replaces the single ``CONFIG`` dict in notebooks/sfincs-nj-sandy.ipynb
(cell ``f4dff70f``) with two frozen dataclasses:

* ``BaseConfig`` — everything that is INVARIANT across the wave experiments
  (paths, grid, subgrid/mask, elevation merge, simulation window, surge
  boundary). The values are the exact ones from the notebook.
* ``WaveConfig`` — the ONLY thing that varies between experiments: the SnapWave
  knobs (wind-wave growth, infragravity waves, the ocean-side wavemaker, and
  Tim Leijnse's SnapWave physics parameters).

``EXPERIMENTS`` is the preset library the runner sweeps over.

Paths resolve against the repo root, overridable with ``NJ_ROOT`` — the same
idiom the ``scripts/*.py`` use — so the CLI and the notebook work regardless of
CWD.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field, replace
from datetime import datetime
from pathlib import Path

# Repo root (…/nj_sandy_sfincs), overridable via NJ_ROOT. nj_sfincs/ lives one
# level below the root, so parents[1] is the root.
ROOT = Path(os.environ.get("NJ_ROOT", Path(__file__).resolve().parents[1]))
DATA = ROOT / "data"

from . import domain as _domain  # noqa: E402  (geography registry; see domain.py)

# Elevation merge, top → bottom; first dataset with data wins. Verbatim from the
# notebook. Kept as a tuple (dataclass forbids mutable list/dict defaults; a
# tuple of dicts is fine). See data/data_catalog.yml for per-layer provenance.
# NOTE ON ORDER (2026-07-14). The eHydro tiers MUST outrank `usace_nj_2010`, and that is the
# whole point of them. The 2010 lidar is green (bathymetric) and returns the real bed in clear
# shallow water — but in deep or turbid water it fails to penetrate and returns the WATER
# SURFACE (~0 to +2 m), which is indistinguishable from land. Ranked first, those bogus returns
# shadow CUDEM's correct bed and SEAL THE CHANNEL SHUT. That is what dammed Shark River Inlet
# (real bed −4.6 to −10.8 m; lidar +0.4 to +2.2 m) and left the whole Shark estuary at exactly
# +0.00 m — never flooding — through Hurricane Sandy. An eHydro survey is a boat with an echo
# sounder: the only source here that measures the bed UNDER the water, so it goes on top.
DEFAULT_ELEVATION_LIST: tuple[dict, ...] = (
    {"elevation": "ehydro_nj"},  # carve Shark River Inlet (lidar paved it — see scripts/audit_paved_channels.py)
    {"elevation": "shrewsbury_ehydro_2015"},  # carve Rumson–Sea Bright bridge dam
    {"elevation": "usace_nj_2010"},  # 1 m PRE-Sandy topobathy (fails in deep/turbid water)
    {"elevation": "cudem_nj"},  # 3 m fill: inlets + shelf + Raritan Bay
    {"elevation": "nj_10ft_dem", "zmin": 0.001},  # 3 m fill: inland land
    {"elevation": "cudem13_nj"},  # ~10 m fill: the nearshore OCEAN the 1/9" product never tiled
    {"elevation": "gmrt_nj"},  # ~50 m GMRT offshore tail
)


@dataclass(frozen=True)
class BaseConfig:
    """Forcing-independent build parameters (shared by every experiment)."""

    # ── Paths ────────────────────────────────────────────────────────────────
    data_catalog: Path = DATA / "data_catalog.yml"
    # Region + every other geographic fact now come from the DOMAIN REGISTRY
    # (nj_sfincs/domain.py), selected with the NJ_DOMAIN env var. In the old repo
    # this was a bare `DATA / "region.geojson"` and the domain's other facts —
    # Coriolis latitude, mask carve boxes, gauge list, HWM basin thresholds —
    # were scattered as literals across five modules. Extending the model south
    # meant finding all of them; this makes it one registry entry.
    domain: str = field(default_factory=lambda: _domain.active().name)
    region: Path = field(default_factory=lambda: _domain.active().region)
    # Quadtree refinement. Override with NJ_REFINEMENT (path relative to ROOT).
    #
    # ⚠️ `refinement_polygons.geojson` carries `shrewsbury_l4` + `navesink_l4` at
    # refinement_level 4 (12.5 m), which were STAGED AFTER data/frozen_mesh was built
    # (2026-07-03, max level 25 m). So a rebuild with it silently upgrades the estuary to
    # 12.5 m: +123,691 faces, +33% active cells, +33% runtime on every run thereafter —
    # a third change riding along with any other rebuild, and one that breaks comparability
    # with every 25 m run in the campaign. L4 was measured as a NULL lever (the 12.5 m
    # rebuild, job 57864095, moved the Shrewsbury gauge by +0.04 m).
    #
    # `refinement_polygons_25m.geojson` is the same file WITHOUT those two polygons, so the
    # 2026-07-14 region+eHydro rebuild changes only what it means to change (+1,007 faces).
    refinement: Path = field(
        default_factory=lambda: (
            (ROOT / os.environ["NJ_REFINEMENT"]) if os.environ.get("NJ_REFINEMENT")
            else _domain.active().refinement
        )
    )
    reclass_table: Path = DATA / "roughness" / "NLCD_CONUS_mapping.csv"
    # The land-cover raster the roughness + subgrid tables are reclassified from.
    # A knob (rather than a literal in model.py) so a BED-ROUGHNESS arm can swap in a
    # recoded raster — `bed-baymanning` re-codes NLCD 11 (Open Water) to a spare class
    # inside the Barnegat lagoon only, so its Manning can differ from the ocean's.
    # ⚠️ Roughness feeds `quadtree_subgrid.create`, so changing it requires a TEMPLATE
    # REBUILD — it is not a `prepare_experiment` swap like `waterlevel_geodataset`.
    # The domain seal is sha(z, mask) and does NOT include roughness, so a rebuilt
    # template still audits as the same domain. That is the point: comparable by
    # construction.
    roughness_lulc: str = "nlcd_2012"
    container_sif: Path = ROOT / "sfincs-desktop.sif"

    # Reproducibility: if set to a pre-built static-mesh dir, build_static COPIES
    # it instead of rebuilding the quadtree (which is environment-sensitive — two
    # builds can differ by ~18 cells → CSI ±0.04). Set to None to build fresh each time.
    # Override via NJ_FROZEN_MESH (relative to ROOT or absolute) to A/B an alternate
    # mesh, e.g. NJ_FROZEN_MESH=data/frozen_mesh_L4 for the narrows-L4 run.
    #
    # ⚠️ DEFAULT CHANGED 2026-07-21: `data/frozen_mesh` → `data/frozen_mesh_sealed`.
    # The old default is the PRE-REBUILD mesh (547,267 cells) — the one whose region
    # polygon chops the Navesink mid-channel, so hydromt hangs a free-outflow BC on a
    # 5 m-deep tidal cross-section and the estuary drains 92.5% of its inflow, and whose
    # Shark River Inlet is dammed shut. The sealed mesh (547,408 cells, 1,635 boundary
    # edges vs the leaking 1,676) is what the adopted premier stands on.
    #
    # This default was a loaded gun: `_template_sealed` was only sealed because
    # scripts/setup_sealed_premier.py sets NJ_FROZEN_MESH explicitly, so ANY build that
    # forgot the env var — a notebook run, a plain build_template — silently produced a
    # leaking domain. That is how `model/` (built 2026-07-03) ended up leaking, and it is
    # the same class of failure that voided the 2026-07-20 phase-lag A/B.
    # See nj_sfincs/premier.py, which now asserts the resulting domain either way.
    # Frozen mesh is PER DOMAIN — `data/frozen_mesh_<domain>`. In the old repo
    # this was a single hardcoded path, which the config comments themselves
    # called "a loaded gun": any build that forgot to set NJ_FROZEN_MESH silently
    # picked up a mesh belonging to a different domain. Keying it on the domain
    # name means the wrong mesh cannot be selected by omission — at worst the
    # path does not exist yet and build_static says so.
    frozen_mesh: Path | None = field(
        default_factory=lambda: (
            (ROOT / os.environ["NJ_FROZEN_MESH"]) if os.environ.get("NJ_FROZEN_MESH")
            else DATA / f"frozen_mesh_{_domain.active().name}"
        )
    )

    # ── Grid ─────────────────────────────────────────────────────────────────
    crs: str = "utm"  # let hydromt pick the UTM zone (→ 32618 here)
    base_res: int = 200  # level-0 cell size [m]; refined down to ~25 m
    rotated: bool = True  # rotate the grid to hug the coastline

    # ── Subgrid / mask ───────────────────────────────────────────────────────
    nr_subgrid_pixels: int = 8  # subgrid sampling per cell edge
    mask_zmin: float = -10.0  # cells with z >= this are active (NJ shelf)

    # ── Elevation merge ──────────────────────────────────────────────────────
    elevation_list: tuple[dict, ...] = DEFAULT_ELEVATION_LIST

    # ── Simulation window (Hurricane Sandy) ──────────────────────────────────
    tref: datetime = datetime(2012, 10, 28)
    tstart: datetime = datetime(2012, 10, 28)
    tstop: datetime = datetime(2012, 10, 31)
    # Coriolis reference latitude — domain-mean, so it follows the registry
    # rather than staying pinned at v1's 40.32 as the domain marches south.
    latitude: float = field(default_factory=lambda: _domain.active().latitude)

    # ── Surge boundary (observed NOAA CO-OPS gauges) ─────────────────────────
    waterlevel_geodataset: str = "noaa_sandy_nj"
    # m; reach down to the Atlantic City gauge WITHOUT reaching Cape May. This is a
    # per-domain fact rather than a shared constant: `noaa_sandy_nj.nc` carries three
    # gauges, and which of them hydromt selects depends on the region's distance to
    # each. 100 km picks Battery+AC on v1_monmouth but Battery+AC+CAPE MAY on
    # v2_barnegat (Cape May falls from 150.7 km to 99.1 km), silently converting the
    # premier's 2-node boundary into a 3-node one. See domain.py for the full note.
    waterlevel_buffer: int = field(
        default_factory=lambda: _domain.active().waterlevel_buffer
    )

    @property
    def data_libs(self) -> list[str]:
        return [str(self.data_catalog)]

    def elevation(self) -> list[dict]:
        """A fresh mutable copy of the elevation list for the hydromt API."""
        return [dict(d) for d in self.elevation_list]


@dataclass(frozen=True)
class WaveConfig:
    """The SnapWave knobs — the only thing that varies between experiments.

    Atlantic swell cannot diffract into the Sandy Hook Bay lee, so bay waves
    have to be *generated* there: via local wind-wave growth (``wave_wind``) or
    injected as infragravity energy (``wave_igwaves`` / ``wavemaker``). Those are
    the levers this project sweeps.
    """

    use_waves: bool = False
    wave_wind: bool = False  # local wind-wave growth (routes model wind; sector→360)
    wave_igwaves: bool = False  # infragravity balance (long-period back-bay runup)
    wavemaker: bool = False  # inject waves along the ocean-side wavemaker line

    # Wave boundary forcing (ERA5-coupled support points)
    wave_geodataset: str = "era5_waves_nj"
    wave_era5_node: tuple[float, float] = (-74.0, 40.0)  # nearest valid offshore node
    wave_n_support: int = 7  # alongshore support points on the boundary

    # ── Per-support-point wave forcing (2026-07-27) ──────────────────────────
    # When set, the wave boundary is read from an UNSTRUCTURED POINT file — dims
    # (time, node) with lon/lat/depth coords — and every support point gets its own
    # NEAREST node instead of one node broadcast alongshore.
    #
    # This exists because the ERA5 path cannot express alongshore structure: a 31 km
    # ERA5 cell cannot resolve a 25 km boundary, so all 7 support points receive
    # byte-identical Hs. That is a limitation of the source, not a modelling choice,
    # and it is one of the two defects the CORA arm addresses. The other is depth:
    # measured at the v2 support points, ERA5 imposes 8.624 m in ~9.9 m of water
    # (gamma 0.86-0.89, ABOVE the 0.78 depth-limited breaking cap, i.e. physically
    # inadmissible at all 7 points) while CORA's shelf-resolving SWAN imposes
    # 4.98-6.11 m there (gamma 0.50-0.63, admissible) with 1.14 m of alongshore spread.
    #
    # Path rather than a catalog key on purpose: hydromt's RasterDataset/GeoDataset
    # drivers do not describe an unstructured ADCIRC/SWAN node set, and inventing a
    # driver for it would put a debugging risk between us and a staged run. Provenance
    # is documented in data/data_catalog.yml alongside the real entries.
    wave_point_dataset: Path | None = None

    # ── SnapWave / SFINCS boundary DECOUPLING (2026-07-22) ───────────────────
    # X1 forced the wave solver onto the SFINCS mesh, which pinned the wave
    # boundary to the WATER-LEVEL boundary at BaseConfig.mask_zmin = -10 m. ERA5
    # is a deep-water source, so that pastes the open-ocean sea state onto the
    # 10 m contour with NO shelf transformation: at Sandy's peak ERA5 imposes
    # 7.66 m at 10 m depth while NDBC 44025 measured 8.79 m out in 36 m — i.e.
    # essentially the same number, 26 m of depth too shallow. CORA's SWAN, which
    # resolves the shelf, says 3.5-4.8 m there.
    #
    # Setting decouple_snapwave lets the SnapWave mask run out to
    # ``snapwave_mask_zmin`` while the SFINCS mask (and therefore the tide/surge
    # boundary) stays exactly where it is. This is seal-safe: premier.py
    # deliberately EXCLUDES snapwave_mask from the domain hash, so the sealed
    # fingerprint is unchanged and only one variable moves.
    #
    # Default False => every existing arm reproduces byte-for-byte.
    decouple_snapwave: bool = False
    snapwave_mask_zmin: float = -30.0  # SnapWave-only depth cut [m]
    wavemaker_line: Path = DATA / "wavemakers" / "wavemaker_line.geojson"
    dtwave: float = 1800.0  # SnapWave coupling interval [s]

    # Tim Leijnse's SnapWave physics parameters. Only emitted when
    # ``tune_physics`` is True — the plain wind-wave baseline deliberately SKIPS
    # them (a 2026-06-01 test showed the breaking block worsened surf-zone Hm0),
    # so leaving tune_physics=False reproduces the current notebook exactly.
    tune_physics: bool = False
    snapwave_alpha: float = 1.0  # Baldock breaking alpha
    snapwave_gamma: float = 0.78  # Baldock breaking gamma (breaking depth)
    snapwave_hmin: float = 0.01  # min water depth for SnapWave [m]
    snapwave_dtheta: int = 5  # direction bin size [deg]
    snapwave_fw: float = 0.02  # wave bottom-friction factor
    snapwave_niter: int = 100  # max iterations (÷4 internal sweeps)
    storefw: int = 1  # store extra wave output

    def sector(self) -> int:
        """Directional sector: full circle when wind can grow waves any way."""
        return 360 if self.wave_wind else 180


@dataclass(frozen=True)
class Experiment:
    """A named experiment = a label + the wave knobs to apply.

    ``waterlevel_geodataset`` optionally OVERRIDES the base water-level forcing
    source for this experiment only (default ``None`` = inherit ``BaseConfig``'s
    Battery-anchored ``noaa_sandy_nj``). The override is applied on the copied
    template in ``run_experiments.prepare_experiment`` by re-running
    ``sf.water_level.create(..., merge=False)`` — everything else (leak-fixed
    mask, subgrid, waves) is identical, so a set of experiments differing only in
    this field is a clean forcing A/B. Faber vs Galibier is NOT a knob here: it is
    the SFINCS container (``sfincs-desktop.sif`` = Faber, the default
    ``BaseConfig.container_sif``), so every run below is Faber.
    """

    name: str
    waves: WaveConfig
    description: str = ""
    waterlevel_geodataset: str | None = None

    #: BRACKET ONLY (2026-08-03). Key into ``premier.BRACKETS``. A bracket is a
    #: DELIBERATELY INADMISSIBLE domain built to BOUND a quantity — never a candidate
    #: configuration. Setting this makes the runner refuse to stage it without
    #: ``NJ_ALLOW_BRACKET``, excludes it from ``--experiments all``, and keeps its
    #: metrics out of ``reports/metrics.csv``. See
    #: ``scripts/setup_manahawkin_open_template.py``.
    bracket: str | None = None


# ── The experiment library the runner sweeps over ────────────────────────────
# Reference points first, then the wave knobs turned on one (group) at a time.
EXPERIMENTS: dict[str, Experiment] = {
    # ── v2_barnegat campaign (2026-07-27) ────────────────────────────────────
    # THE CONTROL. Identical configuration to the adopted v1 premier — Faber SIF,
    # SnapWave + wind + Tim's tuned physics, default NOAA Battery->AC forcing — run
    # on the extended domain. It is the same knobs as `snapwave_tuned` below; it
    # carries its own name because on this domain it is the reference every other
    # arm is measured against, and a run's name is what ends up in a metrics table.
    #
    # ⚠️ Nothing about "same configuration" makes it comparable to the v1 numbers.
    # The HWM mark count alone goes 31 -> 95, so any v2-vs-v1 table must be a
    # BRIDGE RESCORE restricted to v1's marks before it means anything.
    "faber-waves-premier": Experiment(
        "faber-waves-premier",
        WaveConfig(
            use_waves=True, wave_wind=True, wave_igwaves=False, tune_physics=True
        ),
        "CONTROL: the adopted premier configuration, run on v2_barnegat.",
        waterlevel_geodataset=None,
    ),
    # THE PERTURBATION. One variable vs the control: where the SnapWave boundary
    # sea state comes from. ERA5 -> CORA's shelf-resolving SWAN, applied per support
    # point instead of one node broadcast alongshore.
    #
    # Measured at the v2 support points before running (so this is a prediction, not
    # a rationalisation):
    #   ERA5  8.624 m at all 7 points, gamma 0.86-0.89  => ABOVE the 0.78 depth-limited
    #         breaking cap in ~9.9 m of water, i.e. physically inadmissible everywhere,
    #         and with EXACTLY zero alongshore variation.
    #   CORA  4.98-6.11 m, gamma 0.50-0.63 => admissible, with 1.14 m of alongshore
    #         spread. Nearest CORA node is 0.09-0.35 km away at 7.4-13.4 m depth.
    #
    # This attacks the SAME defect as v1's `wave-deep30` by the opposite route:
    # wave-deep30 kept ERA5's 8.624 m and moved the boundary out to where it is valid;
    # this keeps the boundary and imposes the shelf-transformed height that belongs
    # there. Expected direction: markedly less setup, so lower levels — the v1 premier
    # ran +0.32 m WET, so this pushes the right way, but the drop here is far larger
    # than wave-deep30's -0.034 m and OVERSHOOT IS A REAL POSSIBILITY.
    #
    # ⚠️ TWO HONEST CAVEATS, recorded before the result exists:
    #  1. This changes the SOURCE and the ALONGSHORE STRUCTURE together, because ERA5
    #     cannot express the latter at all. A null or a win cannot be attributed to one
    #     of them alone; separating them needs a third arm (CORA at a single node).
    #  2. CORA is not a gold standard. Against NDBC 44025 at the buoy's own location
    #     and depth it runs +0.49 m HIGH (peak 10.84 vs 9.65 m, RMSE 0.78 m). That
    #     cuts in this arm's favour rather than against it — CORA is biased high
    #     offshore and STILL only asks for ~5-6 m at the 10 m contour — so the
    #     reduction is shelf transformation, not a low source. Do not quote CORA's
    #     nearshore value as truth; quote the direction.
    "wave-cora": Experiment(
        "wave-cora",
        WaveConfig(
            use_waves=True, wave_wind=True, wave_igwaves=False, tune_physics=True,
            wave_point_dataset=DATA / "waves" / "cora_waves_nj.nc",
        ),
        "PERTURBATION: SnapWave boundary from CORA SWAN, per support point, instead "
        "of one ERA5 deep-water node broadcast alongshore.",
        waterlevel_geodataset=None,
    ),
    # ── bed-baymanning (2026-07-28): give the lagoon its own bed roughness ────
    # CORA waves retained, so this is one variable vs `wave-cora`: Manning n inside
    # Barnegat Bay, 0.020 -> 0.035. Class 11 stays 0.020 for the ocean, the
    # Raritan/Sandy Hook lobe and the Shrewsbury — a GLOBAL bump would confound the
    # north lobe, which is separately known to be ~15% UNDER-forced.
    #
    # THE MEASUREMENT THAT MOTIVATES IT (2026-07-28, premier, pre-storm window):
    #   Barnegat Light, just inside the inlet: model tidal range 0.719 m vs 0.721
    #     observed — the inlet exchange is already right to 2 mm.
    #   Mantoloking, 35 km up the lagoon: model 0.401 m vs 0.167 m observed (2.4x),
    #     and the tide arrives 58 min EARLY.
    # Right at the inlet but too energetic and too fast up-lagoon = too little
    # DISSIPATION in between. And it is not bathymetry: the lagoon's mean depth is
    # 1.57 m against a published ~1.5 m, and its navigation channels sit within
    # 0.4 m of USACE soundings — inside the datum uncertainty of that comparison.
    # See [[reference_ehydro_district_sign]] for why a carve was rejected: it only
    # ever removes bed, which pushes conveyance FURTHER the wrong way.
    #
    # PRE-REGISTERED PREDICTION (write it down before looking):
    #   Mantoloking range  0.401 -> DOWN toward 0.167 m; phase -58 -> toward 0 min.
    #   Barnegat Light 0.719 m and its -43 min: WATCH FOR DAMAGE. The inlet is the
    #     one thing the model already gets right, and 0.035 reaches the inlet throat.
    #   The along-bay gradient (obs +0.518 m, model -0.410 m) should NARROW.
    #   Open coast, HWMs, CSI: ~unchanged. The recode is 182.8 km2 of back-bay water.
    # A NULL here is informative: with bathymetry exonerated and friction unable to
    # move it, the defect is storage/geometry — the closed Manahawkin wall.
    #
    # ⚠️ NOT a prepare_experiment swap. Roughness feeds `quadtree_subgrid.create`, so
    # this arm must be staged from `_template_baymanning`
    # (scripts/setup_baymanning_template.py), NOT `_template_sealed`:
    #   NJ_TEMPLATE=experiments/_template_baymanning run_experiments.py \
    #     --experiments 'wave-cora+bed-baymanning' --no-run
    # The template builder asserts the domain fingerprint is UNCHANGED, because the
    # seal is sha(z, mask) and excludes roughness. Staging from the wrong template
    # silently produces a plain `wave-cora` rerun.
    # ── bed-ehydro (2026-07-28): carve the southern navigation channels ──────
    # CORA waves retained, so this is one variable vs `wave-cora`: the subgrid bed inside
    # the federal channels of the southern lobe, replaced by USACE soundings.
    #
    # ⚠️ THE HONEST FRAMING. The evidence going in says this should do little: nothing
    # down there is PAVED (the model already has every channel to within ~0.4 m of the
    # soundings, against the 7 m error that dammed Shark River), the lagoon's mean depth
    # already matches published values, and Point Pleasant Canal and the Mantoloking Bridge
    # were both checked for baked-in decks and are clean (PPC thalweg max -5.73 m over
    # 2.8 km; Mantoloking -2.67/-2.46 m vs soundings -1.91..-3.20 m). A carve also only
    # ever REMOVES bed, which pushes conveyance further the wrong way for the one defect we
    # can measure up-lagoon. This arm exists to SETTLE that empirically rather than argue
    # it, which is a legitimate reason to spend a run. Record the prediction and check it:
    # expect the Mantoloking pair to move little, and if anything to get slightly worse.
    #
    # What WOULD make it matter, and is worth looking for in the result: the VDatum offset
    # field runs -0.73 m at Manasquan to -0.53 m at Barnegat, a 0.20 m gradient across the
    # lobe. The scratch comparison that produced "+0.34 m too shallow" used a NOMINAL
    # -0.50 m constant, so part of that gap was datum, not bed. The carve applies the real
    # field, so its true depth change is smaller than +0.34 m and spatially varying.
    #
    # ⚠️ Staged from `_template_ehydro_south` (scripts/setup_ehydro_south_template.py),
    # NOT `_template_sealed`. That template regenerates only the SUBGRID on the frozen mesh,
    # so z/mask — and therefore the domain fingerprint — are untouched and this stays
    # directly comparable to `wave-cora`. Analysis consequence: `sfincs.nc`'s `z` will NOT
    # show the carve; read `sfincs_subgrid.nc`.
    "wave-cora+bed-ehydro": Experiment(
        "wave-cora+bed-ehydro",
        WaveConfig(
            use_waves=True, wave_wind=True, wave_igwaves=False, tune_physics=True,
            wave_point_dataset=DATA / "waves" / "cora_waves_nj.nc",
        ),
        "CORA wave boundary AND the southern federal navigation channels carved from "
        "USACE eHydro soundings (Barnegat/Manasquan inlets, the ICW, Point Pleasant "
        "Canal, Toms River, Oyster Creek).",
        waterlevel_geodataset=None,
    ),
    # ── mask-inlet (2026-07-30): stop imposing the ocean level inside the inlet ──
    # Not a physics knob. A repair to a boundary condition that was never admissible,
    # and the third of its kind here (Navesink drain, Manahawkin cut, this).
    #
    # THE DEFECT, measured on wave-cora+bed-ehydro's own output. `mask_zmin = -10`
    # makes deeper cells inactive, so the water-level BC follows the -10 m isobath —
    # which reaches THROUGH Barnegat Inlet (scoured to -14.8 m). 153 inactive islands
    # appeared inside the model, 145 in the throat; create_boundary rimmed them; 193
    # mask==2 cells ended up as far as 2.6 km inside the mouth, 75 m from the Barnegat
    # Light gauge. Pre-storm tidal range on those cells: 1.465 m, against 1.461 m at
    # the open-coast boundary off Sandy Hook and 0.707 m OBSERVED at Barnegat Light.
    # The bay was being handed the ocean tide directly instead of through its inlet.
    #
    # Repaired by a topological hole-fill plus one always-active box over the gorge
    # (nj_sfincs/domain.py), with both failures now asserted at build time.
    #
    # ⚠️ Staged from `_template_ehydro_inletmask` (scripts/setup_inlet_mask_template.py).
    # The mask is part of the domain fingerprint, so — unlike bed-ehydro — this arm
    # sits on a DIFFERENT domain from everything measured so far. That is the price of
    # the fix and the reason this arm is its own control: `wave-cora+bed-ehydro` on the
    # old mask is NOT a valid comparison for anything but direction.
    #
    # PRE-REGISTERED PREDICTIONS (written before the run, per the bed-ehydro lesson):
    #   Barnegat Light range 1.368 m (wet-channel cells) -> DOWN toward 0.707 observed;
    #     phase -43 min -> toward 0 or LATE.
    #   Mantoloking range 0.401 -> down; -58 min -> later. Same direction, damped.
    #   Along-bay gradient (obs +0.518 m, model -0.410 m) -> toward observed, because
    #     the clamp is what has been holding the southern end up.
    #   ⚠️ THE FALSIFIER, chosen now: `barnegat_bay` HWM bias is +0.005 on bed-ehydro
    #     and some of that may be the clamp propping the bay up. EXPECT IT TO GO
    #     NEGATIVE and bay CSI to drop. If it does, that is a real trade to weigh, not
    #     a reason to revert — an inadmissible BC that scores well is still inadmissible.
    "wave-cora+bed-ehydro+mask-inlet": Experiment(
        "wave-cora+bed-ehydro+mask-inlet",
        WaveConfig(
            use_waves=True, wave_wind=True, wave_igwaves=False, tune_physics=True,
            wave_point_dataset=DATA / "waves" / "cora_waves_nj.nc",
        ),
        "CORA waves + the eHydro southern carve + the Barnegat Inlet mask repair, so "
        "the bay is forced through its inlet instead of having the open-ocean level "
        "imposed 2.6 km inside the throat. The new v2 baseline.",
        waterlevel_geodataset=None,
    ),
    # The same, plus the +24 min Battery phase advance.
    #
    # WHY IT IS A SEPARATE ARM AND NOT FOLDED IN. `tide-shift`'s only recorded cost on
    # v2 was ~8 min of added BAY phase error, and that was scored against a bay whose
    # phase WAS the clamp (-43 min = zero lag = the ocean's own signal). With the inlet
    # unclamped, the bay phase becomes a real measurement of inlet + lagoon propagation
    # for the first time, and its sign may flip to LATE like the coast — in which case
    # tide-shift stops being a trade and becomes coherent everywhere. Folding both
    # changes into one run would destroy exactly that measurement, so the two run in
    # ── THE SOUTHERN BRACKET (2026-08-03) — NOT A CANDIDATE CONFIGURATION ──────
    # ⚠️ DELIBERATELY INADMISSIBLE. Leaves hydromt's water-level BC standing across the
    # Manahawkin bay cross-section, imposing the open-ocean level on INTERIOR bay water.
    # Same defect class as the inlet clamp that cost the 07-26..29 campaign.
    #
    # It exists to BOUND one number: the shipped domain walls off the southern lagoon at
    # lat 39.70 (Little Egg + Beach Haven inlets are outside), which can only UNDER-supply
    # the bay. This over-supplies it. The width between the two is the most the southern
    # connection could possibly be worth — and it decides, for ~3 h of compute, whether a
    # ~1.4 M-face southward mesh rebuild is justified.
    #
    # PRE-REGISTERED: it adds water at the SOUTH end, so Barnegat Light rises more than
    # Mantoloking and the along-bay gradient goes FURTHER NEGATIVE. Hence, whatever the
    # width, the southern wall cannot explain the tilt shortfall — a free result.
    # DECISION RULE: <0.25 m at Mantoloking retires the extension; >0.6 m justifies it.
    "BRACKET+wave-cora+bed-ehydro+mask-inlet+mask-manahawkin-open": Experiment(
        "BRACKET+wave-cora+bed-ehydro+mask-inlet+mask-manahawkin-open",
        WaveConfig(
            use_waves=True, wave_wind=True, wave_igwaves=False, tune_physics=True,
            wave_point_dataset=DATA / "waves" / "cora_waves_nj.nc",
        ),
        "INADMISSIBLE UPPER BOUND on the southern connection: the Manahawkin cut is "
        "left as an imposed open-ocean water-level boundary instead of a closed wall. "
        "Bounds what the walled-off Little Egg Inlet exchange could contribute. Never "
        "report beside a candidate arm.",
        waterlevel_geodataset=None,
        bracket="manahawkin-open",
    ),

    # parallel: `wave-cora+bed-ehydro+mask-inlet` is this arm's control.
    #
    # PRE-REGISTERED: coast keeps tide-shift's win (Sandy Hook ~0 min, Shrewsbury/Shark
    # ~15-19 min). The bay is the open question — if its phase error is LATE after the
    # mask repair, this arm should improve it; if still EARLY, it should worsen it by
    # ~8 min again. Either way the answer is informative and it is the reason to run it.
    "wave-cora+bed-ehydro+mask-inlet+tide-shift": Experiment(
        "wave-cora+bed-ehydro+mask-inlet+tide-shift",
        WaveConfig(
            use_waves=True, wave_wind=True, wave_igwaves=False, tune_physics=True,
            wave_point_dataset=DATA / "waves" / "cora_waves_nj.nc",
        ),
        "CORA waves + eHydro carve + Barnegat Inlet mask repair AND the Battery tide "
        "advanced +24 min. Re-asks the phase question against a bay that is finally "
        "forced through its own inlet.",
        waterlevel_geodataset="noaa_sandy_phaseshift",
    ),
    "wave-cora+bed-baymanning": Experiment(
        "wave-cora+bed-baymanning",
        WaveConfig(
            use_waves=True, wave_wind=True, wave_igwaves=False, tune_physics=True,
            wave_point_dataset=DATA / "waves" / "cora_waves_nj.nc",
        ),
        "CORA wave boundary AND Barnegat lagoon bed roughness raised 0.020 -> 0.035 "
        "(SAV-dominated lagoon). Tests whether the up-lagoon over-amplitude and "
        "early arrival are a friction deficit.",
        waterlevel_geodataset=None,
    ),
    "baseline_no_waves": Experiment(
        "baseline_no_waves",
        WaveConfig(use_waves=False),
        "Surge + meteo + fluvial only — the clean still-water spine.",
    ),
    "wind_waves": Experiment(
        "wind_waves",
        WaveConfig(use_waves=True, wave_wind=True, wave_igwaves=False),
        "Current baseline: SnapWave incident + local wind-wave growth, IG off, "
        "default physics (matches the notebook).",
    ),
    "snapwave_tuned": Experiment(
        "snapwave_tuned",
        WaveConfig(
            use_waves=True, wave_wind=True, wave_igwaves=False, tune_physics=True
        ),
        "wind_waves + Tim's SnapWave physics (gamma=0.78, alpha=1.0, fw=0.02, "
        "hmin=0.01, dtheta=5, niter=100).",
    ),
    "snapwave_tuned_wavemaker": Experiment(
        "snapwave_tuned_wavemaker",
        WaveConfig(
            use_waves=True,
            wave_wind=True,
            wave_igwaves=False,
            wavemaker=True,
            tune_physics=True,
        ),
        "snapwave_tuned + an ocean-side wavemaker, IG off — the premier config "
        "with the forcing upper-bound bracket (vs plain snapwave_tuned).",
    ),
    "igwaves": Experiment(
        "igwaves",
        WaveConfig(
            use_waves=True, wave_wind=False, wave_igwaves=True, tune_physics=True
        ),
        "Infragravity waves alone (no wind growth) — long-period energy toward "
        "the back bays.",
    ),
    "igwaves_wind": Experiment(
        "igwaves_wind",
        WaveConfig(
            use_waves=True, wave_wind=True, wave_igwaves=True, tune_physics=True
        ),
        "IG + wind-wave growth — the combined path to fill the Sandy Hook Bay lee.",
    ),
    "wavemaker": Experiment(
        "wavemaker",
        WaveConfig(
            use_waves=True,
            wave_wind=True,
            wave_igwaves=True,
            wavemaker=True,
            tune_physics=True,
        ),
        "IG + wind + an ocean-side wavemaker injecting IG energy along the "
        "open-coast line (kept ocean-side; a wavemaker inside the bay over-forces).",
    ),
    # ── Boundary re-phasing A/B (2026-07-20) ─────────────────────────────────
    # The modeled pre-storm tide peaks late (Sandy Hook +18 min) because the
    # north is interpolated from the harbor-phase Battery. These share the sealed
    # premier's wave knobs (== snapwave_tuned: Faber SIF + wind waves + Tim's
    # physics) and differ ONLY in the water-level forcing source, so gauge phase
    # lag is compared on an otherwise-identical model. See plan / project memory.
    "phaselag_battery": Experiment(
        "phaselag_battery",
        WaveConfig(use_waves=True, wave_wind=True, wave_igwaves=False, tune_physics=True),
        "Baseline arm: premier wave knobs, default NOAA Battery-anchored forcing "
        "(noaa_sandy_nj). The +18 min-late reference to beat.",
        waterlevel_geodataset=None,
    ),
    "phaselag_shblend": Experiment(
        "phaselag_shblend",
        WaveConfig(use_waves=True, wave_wind=True, wave_igwaves=False, tune_physics=True),
        "Sandy Hook tidal-window blend: real SH tide → Battery surge crest "
        "(noaa_sandy_nj_shblend). Targets the +18 min coastal baseline.",
        waterlevel_geodataset="noaa_sandy_nj_shblend",
    ),
    # ⛔ RETIRED 2026-07-21. GTSM's TIDE is ~34% under-amplitude everywhere in this region
    # (x0.66 vs NOAA harmonics at 6 stations spanning open coast, harbour and a resonant
    # sound), so its interior peaks are an amplitude artifact and say nothing about phase.
    # Kept only so the historical arm remains reproducible. Superseded by phaselag_composite.
    "phaselag_gtsm": Experiment(
        "phaselag_gtsm",
        WaveConfig(use_waves=True, wave_wind=True, wave_igwaves=False, tune_physics=True),
        "RETIRED — GTSM-ERA5 global tide+surge (gtsm_sandy). Tide is ~34% low across "
        "the whole region; do not read its crest as a result.",
        waterlevel_geodataset="gtsm_sandy",
    ),
    # ⭐ The adopted forcing route: tide/surge decomposition (Wahl/Gloucester City NJ,
    # Orton/Hoboken). Sandy Hook returns as a support point with its OWN harmonic tide —
    # predictions don't need the gauge to have survived — and borrows the Battery's NTR
    # (corr 0.996, zero lag) across the mid-storm gap. Validated vs SH 6-min obs:
    # RMSE 0.103 m and pre-storm phase error 0 min, against 0.147 m / 24 min for the
    # Battery-anchored baseline. No extrapolation anywhere.
    # ⛔ RETIRED 2026-07-26 — superseded by `tide-shift`. Run dir DELETED; the boundary
    # forcing file is preserved at archive/retired_composites/phaselag_composite/ and the
    # scored result at reports/phaselag_composite.csv. Do NOT re-run. See the v2 block below.
    "phaselag_composite": Experiment(
        "phaselag_composite",
        WaveConfig(use_waves=True, wave_wind=True, wave_igwaves=False, tune_physics=True),
        "⛔ RETIRED — NOAA harmonic tide + NTR (noaa_sandy_composite), 3 support points. "
        "Fixed the phase but over-forced the coast. Superseded by tide-shift.",
        waterlevel_geodataset="noaa_sandy_composite",
    ),
    # ⭐ v2 (2026-07-22) — the arm that actually isolates PHASE from LEVEL.
    # v1 above won on phase (SH 17.6 -> 7.8 min, Shrewsbury 36.9 -> 25.5) but lost on level
    # (HWM bias +0.32 -> +0.73 m, within-0.5 m 74% -> 21%, SSS 2258 3.65 -> 4.01 m vs an
    # observed 3.465) because it gave Sandy Hook the Battery's NTR UNSCALED — a surge peak
    # amplified by the NY Harbor funnel, inserted into the Battery->AC baseline.
    # v2 keeps the local harmonic TIDE (sharp phase gradients => must be local) but takes the
    # NTR as the Battery->AC interpolant (spatially smooth => interpolate). The node then lies
    # ON the existing surge line: 3.143 m vs the 3.146 m the premier's 2-node line already
    # implied there (-0.004 m), where v1 sat at +0.243 m. Source phase still -3.3 min vs the
    # premier's +21.1. No fitted parameter anywhere.
    #
    # ⛔ RETIRED 2026-07-26 — BOTH COMPOSITES ARE DEAD. `tide-shift` beats them on phase
    # AND level simultaneously (SH lag -0.1 vs 6.7 min; HWM bias 0.302 vs 0.500; RMSE 0.466 vs
    # 0.606; within-0.5 74% vs 63%; SSS 2258 3.626 vs 3.837 against an observed 3.465).
    # Two independent reasons not to build a v3:
    #  1. v2's node was NOT on the line after all. Reconstructing SFINCS' own interpolation with
    #     cadence held constant (2-node interpolant built from v2's OWN Battery+AC columns), the
    #     node contributes +0.012 m at its own latitude but +0.049 m at Shark River — it sits on
    #     the line at the surge PEAK, which is all that was ever verified, while its re-phased
    #     TIDE puts it off the line at other times, so the interpolated max between nodes rises.
    #     The off-line error is downstream of the node, not at it. (Cadence is also NOT the
    #     +0.008 m recorded from a single latitude: it is +0.050 m mid-coast and south.)
    #  2. The geographic argument for a Sandy Hook node is independently closed. CORA compared
    #     against a linear interpolation built from CORA at the same two points (so its own bias
    #     cancels): linear interpolation is NOT a meaningful error source on the open coast. The
    #     node has nothing left to do — phase is fixed without it, and the level is not broken.
    # A v3 could only tune the node's LEVEL to chase HWM bias, with no independent constraint on
    # what that level should be (the Sandy Hook gauge died before the crest) — i.e. calibration,
    # the same circularity that got NTR_DONOR_SCALE rejected. Run dir DELETED; boundary file at
    # archive/retired_composites/phaselag_composite_v2/, result at reports/phaselag_composite_v2.csv.
    "phaselag_composite_v2": Experiment(
        "phaselag_composite_v2",
        WaveConfig(use_waves=True, wave_wind=True, wave_igwaves=False, tune_physics=True),
        "⛔ RETIRED — local harmonic tide + interpolated NTR (noaa_sandy_composite_v2), "
        "3 support points. Superseded by tide-shift; do not re-run.",
        waterlevel_geodataset="noaa_sandy_composite_v2",
    ),
    # Phase fix done the way the plan's §5 actually specified — re-phase the EXISTING
    # north anchor rather than inserting a node. 2 support points, same coordinates and
    # same hourly grid as the premier; the Battery's TIDE is advanced +24 min to
    # open-coast phase and every NTR is left alone. Because no node is inserted, nothing
    # can sit off the Battery->AC surge line, which is exactly how v2 leaked +0.051 m
    # into a barrier-overwash threshold and lost the HWM score. One variable vs the
    # premier: tidal TIMING.
    #
    # ── PORTED TO v2_barnegat (2026-07-28) ───────────────────────────────────
    # The v2 control reproduces v1's phase defect almost exactly (17.8/35.1/35.2 min
    # vs v1's 17.6/36.9/32.8), and `wave-cora` moves it by <=0.6 min — so the
    # expansion neither created nor cured it, and the wave boundary cannot reach it.
    # The fix has to be RE-RUN here rather than assumed to carry over: v2's 95-mark
    # HWM set, its bay lobe and its two crest-surviving interior gauges are all new,
    # and none of them existed when v1 concluded "the phase fix is free".
    #
    # What transfers vs what is re-tested:
    #   TRANSFERS (a property of the forcing, not the mesh) — the Battery is a HARBOUR
    #     gauge at +24 min; interpolating +24 -> AC's -18 predicts +16.7 min of lag at
    #     Sandy Hook and the model measures +17.8. Measured at the source, no run
    #     needed, so the diagnosis holds on any domain fed from these gauges.
    #   RE-TESTED — everything downstream. v1 got -0.1/16.8/16.9 min at NO level cost
    #     (bias 0.318 -> 0.302), best basin move `sandy_hook_bay` 0.090 -> 0.064.
    #     v2 scores 3x the marks over 2x the mesh. The ~17 min that SURVIVED at
    #     Shrewsbury/Shark is excess up-estuary travel time — the temporal twin of the
    #     known amplitude over-damping — and nothing in this arm addresses it.
    #
    # ⚠️ The new risk this domain adds: the Battery anchor also sets the phase arriving
    # at Barnegat Inlet, ~110 km further from it than anything v1 contained. Barnegat
    # Light and Mantoloking survive the crest, so for the first time the interior phase
    # is FALSIFIABLE rather than inferred. Read the along-bay pair, not just the marks.
    #
    # ⚠️ The Cape May trap applies here and is CHECKED, not remembered:
    # noaa_sandy_phaseshift.nc carries the same three NOAA stations as noaa_sandy_nj.nc,
    # and support points are chosen by BUFFERING the region — so a forcing swap re-runs
    # that selection. v2's 60 km buffer keeps Cape May out; prepare_experiment asserts
    # the count via model.check_waterlevel_support.
    "tide-shift": Experiment(
        "tide-shift",
        WaveConfig(use_waves=True, wave_wind=True, wave_igwaves=False, tune_physics=True),
        "Battery tide advanced +24 min to open-coast phase, 2 support points, NTR "
        "untouched. The phase-only experiment the composites were meant to be.",
        waterlevel_geodataset="noaa_sandy_phaseshift",
    ),
    # ── SnapWave boundary decoupling (2026-07-22) ────────────────────────────
    # The premier imposes ERA5 DEEP-WATER waves at the ~10 m contour, because X1
    # pinned the wave boundary to the water-level boundary and mask_zmin cuts at
    # -10 m. Evidence it is wrong, from observations rather than argument: at
    # 10-30 00:00 NDBC 44025 measured 8.79 m in 36 m of water while ERA5 imposes
    # 7.82 m in 10 m of water — the same sea state, 26 m too shallow. CORA's SWAN
    # (which resolves the shelf) says 5.07-6.02 m there.
    #
    # This arm gives SnapWave its own domain out to the 30 m contour (+129k of the
    # 141k already-meshed but inactive offshore cells) and leaves the SFINCS mask,
    # the surge boundary and the sealed fingerprint untouched. One variable vs
    # sealed_faber_waves. Expected direction: less boundary wave energy -> less
    # setup -> HWM bias down from +0.32 (the premier is too WET, so this pushes
    # the right way, unlike phaselag_composite which overshot to +0.73).
    "snapwave_deep": Experiment(
        "snapwave_deep",
        WaveConfig(
            use_waves=True,
            wave_wind=True,
            wave_igwaves=False,
            tune_physics=True,
            decouple_snapwave=True,
            snapwave_mask_zmin=-30.0,
        ),
        "Premier wave knobs with the SnapWave domain decoupled from the SFINCS "
        "mask and pushed to the 30 m contour, so ERA5's deep-water Hs is applied "
        "where it is actually valid and SnapWave does the shelf transformation.",
        waterlevel_geodataset=None,
    ),
    # The 4th cell of the 2x2. The other three are already run: sealed_faber_waves
    # (neither), phaselag_composite_v2 (phase only), snapwave_deep (waves only).
    # The two knobs are orthogonal — `waves` touches only snapwave_mask, and
    # `waterlevel_geodataset` only sfincs_netbndbzsbzifile.nc — so this arm is
    # exactly their combination and the factorial closes.
    #
    # It exists because the phase result is NOT separable from the level. v2 kept
    # the phase win (SH 17.6 -> 6.7 min) but left HWM bias at +0.50 vs the premier's
    # +0.32, and since v2's boundary node sits ON the existing surge line by
    # construction, that residual is the re-phased tide aligning constructively with
    # the surge — not boundary geometry. The open question is whether the premier
    # was getting a defensible level for the WRONG reason: a late tide de-tuning an
    # over-energetic wave forcing. If snapwave_deep lowers the level, the phase fix
    # may come free here. Only this cell can show the interaction; the three
    # existing runs cannot.
    #
    # Carries the same 6-min-vs-hourly forcing cadence lift as the other composite
    # arms (+0.021 m at Battery, +0.038 m at AC), so the clean single-variable
    # comparison for phase is THIS vs snapwave_deep, not vs the premier.
    "snapwave_deep_composite_v2": Experiment(
        "snapwave_deep_composite_v2",
        WaveConfig(
            use_waves=True,
            wave_wind=True,
            wave_igwaves=False,
            tune_physics=True,
            decouple_snapwave=True,
            snapwave_mask_zmin=-30.0,
        ),
        "⛔ SUPERSEDED (v2 retired 2026-07-26) — SnapWave decoupled to 30 m AND the "
        "composite_v2 boundary tide. Retained as the 2x2 interaction evidence; use "
        "snapwave_deep_phaseshift instead.",
        waterlevel_geodataset="noaa_sandy_composite_v2",
    ),
    # ── The production candidate (2026-07-26) ────────────────────────────────
    # snapwave_deep's wave knobs + tide-shift's boundary forcing. Both knobs
    # are orthogonal in this config — `waves` touches only snapwave_mask, and
    # `waterlevel_geodataset` only sfincs_netbndbzsbzifile.nc — so this arm is
    # exactly their union.
    #
    # NOTE `tide-shift` already carries snapwave_mask_zmin=-30.0, but with
    # decouple_snapwave=False that value is INERT: the flag is what activates it.
    # So the two parents differ in exactly one field each and this is their union.
    #
    # Why it is worth the 3 h. Each parent beats the premier on its own axis for a
    # reason that survives independently of the HWM score:
    #   * tide-shift  — Sandy Hook lag 17.6 -> -0.1 min at NO level cost
    #     (bias 0.318 -> 0.302). The +24 min Battery phase is an interpolation
    #     artifact, measured at the source, not a fitted correction.
    #   * snapwave_deep   — the premier imposes Hs 8.624 m at the ~10 m contour,
    #     ABOVE the depth-limited breaking cap (gamma=0.78 => ~7.8 m in 10 m of
    #     water). That BC is physically inadmissible. This arm imposes the SAME
    #     8.624 m at ~30 m (gamma 0.29) where it is valid; faces past breaking
    #     drop 16,532 -> 13,651 (-17%).
    # So this run is mainly a CONFIRMATION that the two do not interfere, not a
    # search for a large gain. Expect HWM bias ~0.27 if they compose; that is
    # success. Neither knob addresses the +0.32 m wet bias and this one will not
    # either.
    #
    # Do NOT read a null result as "the phase fix costs something": the 2x2 already
    # showed deep+composite_v2 kept v2's ~+0.14 penalty, but that was a verdict on
    # v2's INSERTED NODE (off the surge line by +0.049 m at Shark River), and this
    # arm has no node. Interaction is nonetheless not guaranteed to be additive.
    #
    # Runtime: SnapWave is 90-95% of the cost and scales PER-ITERATION with the
    # decoupled domain (6.18 s/iter vs the premier's 3.95). Both deep runs took
    # 3:03-3:05 => submit with extra_args=['--time=06:00:00'], the 3 h batch
    # default would kill it.
    "snapwave_deep_phaseshift": Experiment(
        "snapwave_deep_phaseshift",
        WaveConfig(
            use_waves=True,
            wave_wind=True,
            wave_igwaves=False,
            tune_physics=True,
            decouple_snapwave=True,
            snapwave_mask_zmin=-30.0,
        ),
        "PRODUCTION CANDIDATE: SnapWave decoupled to the 30 m contour (admissible "
        "wave BC) AND the Battery tide advanced +24 min at 2 support points "
        "(no inserted node). The union of the two best arms.",
        waterlevel_geodataset="noaa_sandy_phaseshift",
    ),
}


def with_window(base: BaseConfig, tstop: datetime) -> BaseConfig:
    """Return a copy of ``base`` with a shorter run window (for smoke tests)."""
    return replace(base, tstop=tstop)
