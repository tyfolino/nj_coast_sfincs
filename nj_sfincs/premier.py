"""THE PREMIER and the domain it stands on — one place, asserted, not remembered.

WHY THIS FILE EXISTS (2026-07-21)
---------------------------------
The tidal phase-lag A/B (``phaselag_battery`` / ``_shblend`` / ``_gtsm``) ran to completion
on SLURM — clean exit, full-length output, no warning anywhere — and was **scientifically
void**, because ``run_experiments.py`` staged it from ``experiments/_template`` while the
adopted premier lives on ``experiments/_template_sealed``. Those are different domains: the
old one still has the Navesink mass leak and a dammed Shark River Inlet.

Nothing caught it. The staging was silent, the solver was happy, and the metrics came back
as plain numbers with no marking to say which planet they were measured on. What finally
exposed it was ``stat``-ing inodes by hand, hours later.

The trap has a sharp edge worth naming: **the open coast is nearly domain-independent.**
``phaselag_battery`` reproduced the premier's Sandy Hook phase lag to within 0.3 min
(16.9 vs 17.2), which looked like proof the harness had staged correctly. It was not. The
estuary — the entire subject of the experiment — was 30% down in tidal range at Shrewsbury
and flat dead at Shark (0.03 m vs 1.35 m). A coastal control cannot validate an interior
experiment, and a control that passes on the wrong domain is worse than no control at all.

So: the premier's identity is defined HERE, checked by fingerprint, and asserted at every
point where an experiment is staged or scored.

WHAT IDENTIFIES THE DOMAIN
--------------------------
Not file size, and not the inode. Both are real signals — every ``sealed_*`` run hard-links
one 253,750,180-byte ``sfincs.nc`` (inode 579215649) while the old template's is
253,681,934 — but a per-experiment forcing override rewrites ``sfincs.nc`` in place, giving
each arm its own inode and breaking the link. Size survives that; identity does not.

What survives everything is the **mesh and the bed**:

    sealed   547,408 faces   1,635 boundary edges   sha256(z, mask)[:16] = 45f4f74ca9a2347d
    OLD      547,267 faces   1,676 boundary edges   sha256(z, mask)[:16] = ffc48087214bb848

The 41 extra boundary edges in the old domain *are* the leak: the free-outflow face hydromt
cut across the Navesink. Verified stable across ``_template_sealed``, ``sealed_faber_waves``,
``sealed_faber_nowaves`` and ``sealed_galibier_waves`` (waves on and off, both engines), and
distinct from ``_template`` and all three ``phaselag_*`` arms.

``snapwave_mask`` is deliberately EXCLUDED from the hash — ``add_waves`` rewrites it per wave
config, so folding it in would make no-waves and waves arms of the same domain disagree.

Audit any directory::

    NJ_ROOT=$PWD PYTHONPATH=$PWD micromamba/envs/sfincs/bin/python -m nj_sfincs.premier \\
        experiments/sealed_faber_waves experiments/phaselag_battery
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import xarray as xr

from nj_sfincs import domain as _domain
from nj_sfincs.config import ROOT

# ---------------------------------------------------------------------------
# The premier
# ---------------------------------------------------------------------------

#: The adopted premier config (Workstream O, 2026-07-14). Faber engine + SnapWave +
#: wind. The NAME is the same on every domain because it is the same configuration —
#: what changes is the domain it stands on, which is why the fingerprint is checked
#: separately below rather than being inferred from the run's name.
PREMIER_NAME = "faber-waves-premier"

#: The ONLY template new experiments may be staged from.
SEALED_TEMPLATE = ROOT / "experiments" / "_template_sealed"

#: The pre-rebuild template: leaking Navesink, dammed Shark. Kept for provenance of the
#: historical runs that sit on it. Nothing new should ever be built here.
LEGACY_TEMPLATE = ROOT / "experiments" / "_template"


@dataclass(frozen=True)
class DomainFingerprint:
    """Identity of the physical domain: the mesh and the bed, nothing else."""

    n_faces: int
    n_boundary_edges: int
    sha_z_mask: str

    def __str__(self) -> str:
        return (f"faces={self.n_faces} boundary_edges={self.n_boundary_edges} "
                f"sha(z,mask)={self.sha_z_mask}")


#: v1_monmouth — region fixed at the leak's root + Shark eHydro inlet carve. This is
#: the domain the whole 2026-07 campaign (premier, tide-shift, wave-deep30 and their
#: union) was measured on, and it is now FROZEN: nothing may change it.
V1_MONMOUTH = DomainFingerprint(547408, 1635, "45f4f74ca9a2347d")

#: v2_barnegat — v1 plus the southern lobe to Barnegat Inlet, built 2026-07-26 from
#: data/frozen_mesh_v2_barnegat. 2.09x the faces of v1; v1's own footprint reproduces
#: within it at 541,081 faces, so the north was not disturbed by the extension.
#:
#: ⭐ REVISED 2026-07-30 — the Barnegat Inlet mask repair. Same mesh, same bed (`z` is
#: byte-identical); what changed is the MASK, and the mask is half of this hash.
#: `mask_zmin = -10` had left 153 inactive islands inside the model — 145 in the inlet
#: throat, scoured to -14.8 m — and `create_boundary` rimmed them, imposing the
#: open-ocean water level as far as 2.6 km inside the mouth, 75 m from the Barnegat
#: Light gauge. Measured cost: a 1.465 m pre-storm tidal range on those cells against
#: 1.461 m at the open-coast boundary and 0.707 m observed at the gauge. The bay was
#: being driven by the ocean directly instead of through its inlet.
#: After the repair: islands 153 -> 0, in-throat BC cells 114 -> 0, active +334,
#: water-level BC cells 3,064 -> 2,911. See scripts/setup_inlet_mask_template.py.
V2_BARNEGAT = DomainFingerprint(1143357, 2164, "3b1356b9590c59ff")

#: The PRE-REPAIR v2 mask. Everything in the 2026-07-26..29 campaign — the premier,
#: wave-cora, tide-shift, bed-baymanning, bed-ehydro — was measured on this domain, so
#: it is not "wrong output" to be discarded but it is NOT comparable to anything built
#: after the repair. Registered by name so an audit of those directories says which
#: domain they are on instead of "UNRECOGNISED".
V2_BARNEGAT_PREMASK = DomainFingerprint(1143357, 2164, "9ccbab0bc7a9fc0d")

#: The pre-rebuild domain. Named so the error message can say *which* wrong domain it is.
LEGACY = DomainFingerprint(547267, 1676, "ffc48087214bb848")

#: The fingerprint each registered domain MUST have. Keyed by `domain.Domain.name`, so
#: `NJ_DOMAIN` selects both the geography and the identity check in one move and the two
#: cannot drift apart.
#:
#: This registry is why the file was generalised (2026-07-27). It used to hold a single
#: SEALED constant, which meant every v2_barnegat directory audited "UNRECOGNISED" — an
#: unimplemented feature that reads exactly like a real domain error, and therefore
#: trains you to ignore the one alarm that matters.
EXPECTED: dict[str, DomainFingerprint] = {
    "v1_monmouth": V1_MONMOUTH,
    "v2_barnegat": V2_BARNEGAT,
}

#: The frozen mesh each domain is built from (see BaseConfig.frozen_mesh, which derives
#: the same path from the domain name).
FROZEN_MESH = {
    "v1_monmouth": "data/frozen_mesh_v1_monmouth",
    "v2_barnegat": "data/frozen_mesh_v2_barnegat",
}

KNOWN = {V1_MONMOUTH: "v1_monmouth SEALED (leak fixed, Shark inlet carved)",
         V2_BARNEGAT: "v2_barnegat (south to Barnegat Inlet, Manahawkin cut walled, "
                      "inlet mask repaired 2026-07-30)",
         V2_BARNEGAT_PREMASK: "v2_barnegat PRE-REPAIR (open-ocean level imposed 2.6 km "
                              "INSIDE Barnegat Inlet — the 2026-07-26..29 campaign)",
         LEGACY: "LEGACY pre-rebuild (Navesink LEAKING, Shark inlet DAMMED)"}


def expected() -> DomainFingerprint:
    """The fingerprint the ACTIVE domain (``NJ_DOMAIN``) must have."""
    name = _domain.active().name
    if name not in EXPECTED:
        raise KeyError(
            f"domain {name!r} has no sealed fingerprint in premier.EXPECTED. Build its "
            "frozen mesh, compute sha256 over (z, mask) with domain_fingerprint(), and "
            "register it here BEFORE running anything on it — an unregistered domain "
            "cannot be told apart from a corrupted one."
        )
    return EXPECTED[name]

#: Shrewsbury tidal gauge, nudged 21 m into the channel so it samples water (zb -4.33 m)
#: rather than the +1.46 m bank it started on. The old template still has the bank point,
#: which silently returns NaN from every phase/tide metric. Checked to 0.1 m.
SHREWSBURY_OBS_XY = (587031.2, 4468837.4)
SHREWSBURY_OBS_NAME = "usgs_tidal_sea_bright"


class WrongDomainError(RuntimeError):
    """Raised when a model directory is not on the sealed domain."""


def domain_fingerprint(model_dir: Path | str) -> DomainFingerprint:
    """Fingerprint the domain in ``model_dir/sfincs.nc``."""
    path = Path(model_dir) / "sfincs.nc"
    if not path.exists():
        raise FileNotFoundError(f"no sfincs.nc in {model_dir}")
    with xr.open_dataset(path) as ds:
        h = hashlib.sha256()
        for var in ("z", "mask"):  # NOT snapwave_mask — rewritten per wave config
            h.update(var.encode())
            h.update(np.ascontiguousarray(ds[var].values).tobytes())
        return DomainFingerprint(int(ds.sizes["mesh2d_nFaces"]),
                                 int(ds.sizes["mesh2d_nBoundary_edges"]),
                                 h.hexdigest()[:16])


def is_sealed(model_dir: Path | str) -> bool:
    """True iff ``model_dir`` sits on the ACTIVE domain. False if it has no sfincs.nc."""
    try:
        return domain_fingerprint(model_dir) == expected()
    except FileNotFoundError:
        return False


def shrewsbury_obs_ok(model_dir: Path | str) -> bool | None:
    """True iff the Shrewsbury gauge is the in-channel point. None if no sfincs.obs."""
    obs = Path(model_dir) / "sfincs.obs"
    if not obs.exists():
        return None
    for line in obs.read_text().splitlines():
        if SHREWSBURY_OBS_NAME in line:
            parts = line.split()
            x, y = float(parts[0]), float(parts[1])
            return (abs(x - SHREWSBURY_OBS_XY[0]) < 0.1
                    and abs(y - SHREWSBURY_OBS_XY[1]) < 0.1)
    return False


def assert_sealed_domain(model_dir: Path | str, context: str = "") -> None:
    """Raise unless ``model_dir`` is on the sealed domain with the in-channel gauge.

    Call this wherever an experiment is staged or scored. A wrong domain is not a
    degraded result — it is a different planet, and its numbers must never reach a table.
    """
    where = f"{context}: " if context else ""
    want = expected()
    dom = _domain.active().name
    got = domain_fingerprint(model_dir)
    if got != want:
        raise WrongDomainError(
            f"{where}{model_dir} is NOT on domain '{dom}'.\n"
            f"    expected {want}  <- {KNOWN[want]}\n"
            f"    got      {got}"
            + (f"  <- {KNOWN[got]}" if got in KNOWN else "  <- UNRECOGNISED domain")
            + f"\n  Stage from {SEALED_TEMPLATE.name}, not {LEGACY_TEMPLATE.name}, and\n"
              f"  check NJ_DOMAIN (currently {dom!r}) and NJ_FROZEN_MESH agree.\n"
              "  Results from the wrong domain are void: the pre-rebuild mesh leaks 92.5%\n"
              "  of estuary inflow through the Navesink and Shark River Inlet is dammed\n"
              "  shut (never floods).\n"
              "  NB the OPEN COAST barely moves between domains — a healthy Sandy Hook\n"
              "  number is NOT evidence the domain is right."
        )
    if shrewsbury_obs_ok(model_dir) is False:
        raise WrongDomainError(
            f"{where}{model_dir} has the sealed domain but a STALE Shrewsbury gauge.\n"
            f"  '{SHREWSBURY_OBS_NAME}' must sit at {SHREWSBURY_OBS_XY} (in-channel,\n"
            "  zb -4.33 m). The old point sits on a +1.46 m bank that only wets during the\n"
            "  storm, so every pre-storm tide/phase metric silently returns NaN."
        )


def describe(model_dir: Path | str) -> str:
    """One-line audit of a model directory."""
    try:
        fp = domain_fingerprint(model_dir)
    except FileNotFoundError as e:
        return f"  {str(model_dir):44s} -- {e}"
    label = KNOWN.get(fp, "UNRECOGNISED")
    obs = shrewsbury_obs_ok(model_dir)
    obs_s = {True: "gauge in-channel", False: "GAUGE STALE", None: "no sfincs.obs"}[obs]
    flag = "OK  " if (fp == expected() and obs is not False) else "BAD "
    return f"  {flag}{str(model_dir):44s} {label:60s} {obs_s}"


def _main(argv: list[str] | None = None) -> int:
    import sys
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        args = sorted(str(p) for p in (ROOT / "experiments").glob("*")
                      if (p / "sfincs.nc").exists())
    dom = _domain.active().name
    print(f"PREMIER = {PREMIER_NAME}   template = {SEALED_TEMPLATE.name}")
    print(f"NJ_DOMAIN = {dom}")
    print(f"expected domain: {expected()}\n")
    bad = 0
    for a in args:
        line = describe(a)
        bad += line.lstrip().startswith("BAD")
        print(line)
    print(f"\n{len(args) - bad}/{len(args)} on domain '{dom}'")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(_main())
