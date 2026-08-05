#!/usr/bin/env python3
"""Build `_template_ehydro_inletmask` — the eHydro template with the inlet mask repaired.

WHAT IS BROKEN (measured 2026-07-30, and present in EVERY v2 run to date)
------------------------------------------------------------------------
`mask_zmin = -10` makes every cell deeper than -10 m inactive, so the active domain's
seaward limit is the -10 m isobath and `create_boundary` lays the imposed open-ocean
water level along it. That is the intended construction on the open coast. But the
-10 m contour also reaches THROUGH Barnegat Inlet, which is scoured to -14.8 m:

  * 153 inactive cells form 18 islands INSIDE the model — 145 of them in the inlet
    throat, 3 in the Navesink, 1 at Manasquan.
  * `create_boundary` rims them: 155 mask==2 and 28 mask==3 cells touch an island,
    and inside the inlet window there are 193 mask==2 cells spanning 2.6 km inland.
  * The Barnegat Light gauge sits **75 m** from one of them; the SSS sensor 168 m.

It is not cosmetic. In `wave-cora+bed-ehydro`, the pre-storm tidal range at those
inlet cells is **1.465 m**, against 1.461 m at the open-coast boundary off Sandy Hook
and **0.707 m observed** at Barnegat Light. The full ocean tide is clamped inside the
inlet — the same defect class as the Manahawkin cut and the Navesink drain, and the
most likely mechanism behind both recorded bay defects (a -43 min "early" arrival is
zero lag, i.e. the ocean's own phase; the 1.9x over-amplification is the clamp
bleeding out).

`z` and `mask` are byte-identical across `faber-waves-premier`, `wave-cora` and
`wave-cora+bed-ehydro`, so this is in all of them. eHydro did not cause it (that carve
is subgrid-only, `z` untouched) but would deepen it in any future mesh rebuild.

WHAT THIS SCRIPT DOES
---------------------
Re-derives ONLY the mask and the boundaries on a copy of `_template_ehydro_south`,
via `model.apply_mask_and_boundary`, which now carries two repairs:

  1. `_fill_inactive_holes` — topological, no geometry: any inactive island not
     connected to the ocean/land mass becomes active, before boundaries are laid.
  2. the `barnegat_inlet` always-active box in the domain registry — closes the part
     of the intrusion that stays CONNECTED to the sea (the gorge), which topology
     alone cannot see.

...and two new invariants that make the defect a build-time failure from now on.

The subgrid tables are NOT rebuilt and do not need to be: they exist for all
1,143,357 faces and 2,307,638 uv points, so a previously-inactive cell already has
its table. `z` is never touched, so the eHydro carve is carried through intact.

⚠️ THE DOMAIN FINGERPRINT CHANGES. It must: the mask is part of it. That is the real
cost of this fix — every existing v2 arm was measured on the pre-repair mask and is
no longer strictly comparable, so the control must be re-run alongside. This script
PRINTS the new fingerprint rather than asserting one; register it in
`nj_sfincs.premier` as the v2 fingerprint (keeping the old value as a named
historical entry) before staging anything from this template.

Run:  NJ_ROOT=$PWD PYTHONPATH=$PWD NJ_DOMAIN=v2_barnegat \
      python scripts/setup_inlet_mask_template.py
"""

from __future__ import annotations

import gc
import shutil

import numpy as np
import xarray as xr
from hydromt_sfincs import SfincsModel

import nj_sfincs  # noqa: F401  (PROJ primer — must precede hydromt_sfincs)
from nj_sfincs import domain as _domain
from nj_sfincs import model, premier
from nj_sfincs.config import exp_root, EXPERIMENTS, ROOT, BaseConfig

EXP = exp_root()
SOURCE = EXP / "_template_ehydro_south"
TEMPLATE = EXP / "_template_ehydro_inletmask"


def _mask_report(path, label: str) -> dict:
    """Count the things this fix is supposed to move, straight off disk."""
    import xugrid
    from scipy.sparse.csgraph import connected_components

    ds = xr.open_dataset(path / "sfincs.nc")
    mask = ds["mask"].values
    z = ds["z"].values
    x, y = ds.mesh2d_face_x.values, ds.mesh2d_face_y.values
    adj = xugrid.open_dataset(path / "sfincs.nc").grid.face_face_connectivity

    inactive = mask == 0
    idx = np.flatnonzero(inactive)
    _, lab = connected_components(adj[inactive][:, inactive], directed=False)
    labels, counts = np.unique(lab, return_counts=True)
    hole = np.zeros(len(mask), dtype=bool)
    hole[idx[lab != labels[np.argmax(counts)]]] = True

    zones = {}
    for zone in _domain.active().no_waterlevel_boxes:
        xmin, ymin, xmax, ymax = zone.box
        sel = (mask == 2) & (x > xmin) & (x < xmax) & (y > ymin) & (y < ymax)
        zones[zone.name] = int(sel.sum())

    out = {
        "active": int((mask == 1).sum()),
        "waterlevel": int((mask == 2).sum()),
        "outflow": int((mask == 3).sum()),
        "inactive": int(inactive.sum()),
        "holes": int(hole.sum()),
        "hole_zmin": float(z[hole].min()) if hole.any() else float("nan"),
        "zones": zones,
    }
    print(f"[{label}] active {out['active']:,}  waterlevel {out['waterlevel']:,}  "
          f"outflow {out['outflow']:,}  inactive {out['inactive']:,}")
    print(f"[{label}] interior inactive islands: {out['holes']} "
          f"(deepest {out['hole_zmin']:+.2f} m)")
    for name, n in zones.items():
        print(f"[{label}] mask==2 inside no-waterlevel zone '{name}': {n}")
    return out


def main() -> int:
    if not (SOURCE / "sfincs.inp").exists():
        raise SystemExit(
            f"missing {SOURCE} — run scripts/setup_ehydro_south_template.py first"
        )

    base = BaseConfig()

    print("=== BEFORE (the eHydro template as it stands) ===")
    before = _mask_report(SOURCE, "before")
    fp_before = premier.domain_fingerprint(SOURCE)
    print(f"[before] fingerprint {fp_before}")

    if TEMPLATE.exists():
        shutil.rmtree(TEMPLATE)
    shutil.copytree(SOURCE, TEMPLATE)

    # ── re-derive mask + boundaries on the copy ──────────────────────────────
    # No subgrid rebuild: the tables already cover every face and every uv point,
    # so a newly-activated cell arrives with its table. `z` is never touched, which
    # is what carries the eHydro carve through unchanged.
    print("\n=== re-deriving mask + boundaries ===")
    sf = SfincsModel(str(TEMPLATE), data_libs=base.data_libs, mode="r+")
    sf.quadtree_grid.read()
    model.apply_mask_and_boundary(base, sf)
    sf.quadtree_grid.write()
    del sf
    gc.collect()

    # Boundary cells moved, so the SnapWave boundary and the forcing block must be
    # regenerated. (`sfincs_netbndbzsbzifile.nc` holds the 2 NOAA stations and is
    # mask-independent — SFINCS interpolates onto mask==2 at runtime — but
    # snapwave.bnd/bhs/btp/bwd are derived from the mask and are not.)
    print("\n=== regenerating forcing + wave boundary ===")
    sf = SfincsModel(str(TEMPLATE), data_libs=base.data_libs, mode="r+")
    model.add_forcing(base, sf)
    wave_cfg = EXPERIMENTS["faber-waves-premier"].waves
    sw = model.add_waves(wave_cfg, base, sf)
    model.finalize(wave_cfg, base, sf, TEMPLATE, sw)
    del sf
    gc.collect()
    model.restore_diagnostics(TEMPLATE)

    # ── verification ─────────────────────────────────────────────────────────
    print("\n=== AFTER ===")
    after = _mask_report(TEMPLATE, "after")
    fp_after = premier.domain_fingerprint(TEMPLATE)
    print(f"[after]  fingerprint {fp_after}")

    fail = []
    if after["holes"]:
        fail.append(f"{after['holes']} interior inactive islands remain")
    for name, n in after["zones"].items():
        if n:
            fail.append(f"{n} mask==2 cells remain in no-waterlevel zone '{name}'")
    if fp_after == fp_before:
        fail.append("fingerprint UNCHANGED — the mask was not re-derived at all")

    # The carve must survive: z untouched, subgrid still the eHydro one.
    a = xr.open_dataset(SOURCE / "sfincs.nc")
    b = xr.open_dataset(TEMPLATE / "sfincs.nc")
    if not np.array_equal(a["z"].values, b["z"].values, equal_nan=True):
        fail.append("`z` MOVED — this script must only touch the mask")
    sa = xr.open_dataset(SOURCE / "sfincs_subgrid.nc")
    sb = xr.open_dataset(TEMPLATE / "sfincs_subgrid.nc")
    for v in ("z_zmin", "z_volmax", "uv_zmin", "uv_navg"):
        if not np.allclose(sa[v].values, sb[v].values, equal_nan=True):
            fail.append(f"subgrid `{v}` MOVED — the eHydro carve must carry through")

    print("\n=== summary ===")
    print(f"  interior islands   {before['holes']:>6d} -> {after['holes']:>6d}")
    for name in after["zones"]:
        print(f"  mask==2 in '{name}'  {before['zones'][name]:>6d} -> "
              f"{after['zones'][name]:>6d}")
    print(f"  active cells       {before['active']:>6,} -> {after['active']:>6,} "
          f"({after['active'] - before['active']:+,})")
    print(f"  waterlevel BC      {before['waterlevel']:>6,} -> "
          f"{after['waterlevel']:>6,} ({after['waterlevel'] - before['waterlevel']:+,})")

    if fail:
        raise SystemExit("!! FAILED:\n  - " + "\n  - ".join(fail))

    print(f"\nwrote {TEMPLATE}")
    print("\nNEXT — the fingerprint changed, so register it BEFORE staging:")
    print(f"  in nj_sfincs/premier.py set EXPECTED['v2_barnegat'] to")
    print(f"      DomainFingerprint({fp_after.n_faces}, {fp_after.n_boundary_edges}, "
          f"\"{fp_after.sha_z_mask}\")")
    print(f"  and keep {fp_before.sha_z_mask} as the historical pre-repair entry.")
    print("\nThen stage:")
    print("  NJ_DOMAIN=v2_barnegat NJ_TEMPLATE=experiments/_template_ehydro_inletmask \\\n"
          "    python run_experiments.py --experiments "
          "'wave-cora+bed-ehydro+mask-inlet,wave-cora+bed-ehydro+mask-inlet+tide-shift' "
          "--no-run")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
