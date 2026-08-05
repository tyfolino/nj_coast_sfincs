#!/usr/bin/env python3
"""Build `_template_manahawkin_open` — the DELIBERATELY INADMISSIBLE southern bound.

⚠️⚠️ READ THIS BEFORE RUNNING. THIS SCRIPT CREATES A KNOWN-WRONG DOMAIN ON PURPOSE.

WHAT IT IS FOR
--------------
The v2_barnegat domain stops at lat 39.70, which cuts Barnegat Bay across the Manahawkin
narrows. The real lagoon continues ~25 km south to Little Egg and Beach Haven inlets.
`_MANAHAWKIN_CUT` demotes hydromt's water-level boundary there to ordinary active
interior, and SFINCS's default beyond the domain is a CLOSED WALL. `domain.py` says so
in as many words: "a wall omits that exchange".

So the shipped configuration is a LOWER BOUND on the bay: it cannot receive the southern
inflow. This script builds the UPPER BOUND — it leaves hydromt's `mask==2` standing
across the bay cross-section, imposing the open-ocean level on interior bay water. That
over-forces the lagoon from its southern end, in parallel with (and competing against)
the inlet exchange the domain exists to measure.

Neither run is right. The point is the WIDTH between them, which is the most the
southern connection could possibly be worth:

    width < 0.25 m at Mantoloking  ->  the southward extension is retired. Do not build
                                       a new frozen mesh; the wall is good enough.
    0.25 - 0.6 m                   ->  a contributor, not the explanation.
    > 0.6 m (and the tilt does not
      degrade, and the walled run's
      deficit lies inside the bracket) -> the extension to Little Egg Inlet is justified.

That decision otherwise costs a ~1.4 M-face mesh rebuild, ~8 h solves, four re-clipped
elevation datasets, the Cape May buffer trap, and a re-baseline of every existing arm.
This script plus one 3 h run replaces it with a number.

PRE-REGISTERED PREDICTIONS (written before the run, 2026-08-03)
--------------------------------------------------------------
1. The bracket adds water at the SOUTH end, so Barnegat Light rises more than
   Mantoloking and the along-bay gradient goes FURTHER NEGATIVE. Therefore — whatever
   the width — S2 cannot explain the tilt shortfall. That conclusion is free and does
   not depend on the magnitude.
2. `ig_tide_range_barnegat_light` (0.808 m vs 1.003 observed) rises toward or past
   observed: the same clamp signature the inlet repair removed.

WHY THE SAFEGUARDS ARE HEAVY
----------------------------
This is the same defect class as the inlet clamp, which scored WELL and cost the entire
2026-07-26..29 campaign. The lesson recorded then was that labelling is not enough. So:

  * the fingerprint goes in `premier.BRACKETS`, NEVER in `premier.EXPECTED` — putting it
    there would make `assert_sealed_domain` PASS on it;
  * `assert_sealed_domain` refuses it BY NAME with an explanation;
  * the arm is named `BRACKET+...`, a machine-checkable prefix;
  * `NJ_ALLOW_BRACKET=manahawkin-open` is required to stage or score it;
  * the waived invariant prints a banner every build.

WHAT MOVES AND WHAT MUST NOT
----------------------------
Mask + boundaries only. `z` is untouched, so the eHydro carve carries through. The
subgrid tables are NOT rebuilt and do not need to be — they exist for all 1,143,357
faces and 2,307,638 uv points. The fingerprint MUST change (the mask is half of it).

Run:
  NJ_ROOT=$PWD PYTHONPATH=$PWD NJ_DOMAIN=v2_barnegat \
  NJ_ALLOW_BRACKET=manahawkin-open python scripts/setup_manahawkin_open_template.py
"""

from __future__ import annotations

import gc
import os
import shutil

import numpy as np
import xarray as xr
from hydromt_sfincs import SfincsModel

import nj_sfincs  # noqa: F401  (PROJ primer — must precede hydromt_sfincs)
from nj_sfincs import domain as _domain
from nj_sfincs import model, premier
from nj_sfincs.config import exp_root, EXPERIMENTS, ROOT, BaseConfig

EXP = exp_root()
SOURCE = EXP / "_template_ehydro_inletmask"       # the ADOPTED v2 mask
TEMPLATE = EXP / "_template_manahawkin_open"
BRACKET = "manahawkin-open"
ZONE = "manahawkin_cut"                            # both the override and the alarm


def _report(path, label: str) -> dict:
    ds = xr.open_dataset(path / "sfincs.nc")
    mask, z = ds["mask"].values, ds["z"].values
    x, y = ds.mesh2d_face_x.values, ds.mesh2d_face_y.values
    zones = {}
    for zone in _domain.active().no_waterlevel_boxes:
        xmin, ymin, xmax, ymax = zone.box
        sel = (mask == 2) & (x > xmin) & (x < xmax) & (y > ymin) & (y < ymax)
        zones[zone.name] = int(sel.sum())
    out = {"active": int((mask == 1).sum()), "waterlevel": int((mask == 2).sum()),
           "outflow": int((mask == 3).sum()), "inactive": int((mask == 0).sum()),
           "zones": zones}
    print(f"[{label}] active {out['active']:,}  waterlevel {out['waterlevel']:,}  "
          f"outflow {out['outflow']:,}  inactive {out['inactive']:,}")
    for n, c in zones.items():
        print(f"[{label}] mask==2 inside no-waterlevel zone '{n}': {c}")
    return out


def main() -> int:
    if os.environ.get("NJ_ALLOW_BRACKET") != BRACKET:
        raise SystemExit(
            f"refusing to build an inadmissible bracket without "
            f"NJ_ALLOW_BRACKET={BRACKET}.\n"
            "This script creates a KNOWN-WRONG domain on purpose; read its docstring."
        )
    if not (SOURCE / "sfincs.inp").exists():
        raise SystemExit(f"missing {SOURCE} — the adopted v2 template must exist first")

    base = BaseConfig()

    print("=== BEFORE (the adopted v2 mask) ===")
    before = _report(SOURCE, "before")
    fp_before = premier.domain_fingerprint(SOURCE)
    print(f"[before] fingerprint {fp_before}")

    if TEMPLATE.exists():
        shutil.rmtree(TEMPLATE)
    shutil.copytree(SOURCE, TEMPLATE)

    print("\n=== re-deriving mask + boundaries WITHOUT the Manahawkin override ===")
    sf = SfincsModel(str(TEMPLATE), data_libs=base.data_libs, mode="r+")
    sf.quadtree_grid.read()
    model.apply_mask_and_boundary(
        base, sf,
        skip_overrides=frozenset({ZONE}),          # let hydromt's mask==2 stand
        allow_waterlevel_zones=frozenset({ZONE}),  # and waive the alarm, loudly
    )
    sf.quadtree_grid.write()
    del sf
    gc.collect()

    print("\n=== regenerating forcing + wave boundary ===")
    sf = SfincsModel(str(TEMPLATE), data_libs=base.data_libs, mode="r+")
    model.add_forcing(base, sf)
    wave_cfg = EXPERIMENTS["faber-waves-premier"].waves
    sw = model.add_waves(wave_cfg, base, sf)
    model.finalize(wave_cfg, base, sf, TEMPLATE, sw)
    del sf
    gc.collect()
    model.restore_diagnostics(TEMPLATE)

    print("\n=== AFTER ===")
    after = _report(TEMPLATE, "after")
    fp_after = premier.domain_fingerprint(TEMPLATE)
    print(f"[after]  fingerprint {fp_after}")

    fail = []
    # The bracket is only a bracket if the boundary actually appeared.
    if after["zones"].get(ZONE, 0) == 0:
        fail.append(f"no mask==2 cells appeared in '{ZONE}' — the override skip did "
                    "NOT take effect, so this is not the bound it claims to be")
    # The OTHER zone must stay clean: we are opening one boundary, not all of them.
    for n, c in after["zones"].items():
        if n != ZONE and c:
            fail.append(f"{c} mask==2 cells appeared in unrelated zone '{n}' — "
                        "this bracket must move ONE thing")
    if fp_after == fp_before:
        fail.append("fingerprint UNCHANGED — the mask was not re-derived")

    # Single-variable guards: only the mask may move.
    a = xr.open_dataset(SOURCE / "sfincs.nc")
    b = xr.open_dataset(TEMPLATE / "sfincs.nc")
    if not np.array_equal(a["z"].values, b["z"].values, equal_nan=True):
        fail.append("`z` MOVED — this script must only touch the mask")
    sa = xr.open_dataset(SOURCE / "sfincs_subgrid.nc")
    sb = xr.open_dataset(TEMPLATE / "sfincs_subgrid.nc")
    for v in ("z_zmin", "z_volmax", "uv_zmin", "uv_navg"):
        if not np.allclose(sa[v].values, sb[v].values, equal_nan=True):
            fail.append(f"subgrid `{v}` MOVED — the eHydro carve must carry through")

    # The Manahawkin cells are z -1.0..-2.4 and fail add_waves' `z < -5.0` support-point
    # gate, so they cannot enter the wave-boundary binning. Assert it, don't trust it.
    for f in ("snapwave.bnd", "snapwave.bhs", "snapwave.btp", "snapwave.bwd"):
        if (SOURCE / f).exists() and (TEMPLATE / f).exists():
            if (SOURCE / f).read_bytes() != (TEMPLATE / f).read_bytes():
                fail.append(f"{f} CHANGED — the wave boundary must be identical to the "
                            "control or this is a two-variable experiment")

    print("\n=== summary ===")
    print(f"  mask==2 in '{ZONE}'   {before['zones'].get(ZONE,0):>6d} -> "
          f"{after['zones'].get(ZONE,0):>6d}   (0 -> N is the whole point)")
    print(f"  active cells        {before['active']:>7,} -> {after['active']:>7,} "
          f"({after['active'] - before['active']:+,})")
    print(f"  waterlevel BC       {before['waterlevel']:>7,} -> "
          f"{after['waterlevel']:>7,} ({after['waterlevel'] - before['waterlevel']:+,})")

    if fail:
        raise SystemExit("!! FAILED:\n  - " + "\n  - ".join(fail))

    print(f"\nwrote {TEMPLATE}")
    print("\nNEXT — register the fingerprint in premier.BRACKETS (NOT in EXPECTED):")
    print(f"    MANAHAWKIN_OPEN = Bracket(..., fingerprint=DomainFingerprint("
          f"{fp_after.n_faces}, {fp_after.n_boundary_edges}, "
          f"\"{fp_after.sha_z_mask}\"), ...)")
    print("\nThen stage with the bracket guard:")
    print(f"  NJ_DOMAIN=v2_barnegat NJ_ALLOW_BRACKET={BRACKET} \\\n"
          f"  NJ_TEMPLATE=experiments/{TEMPLATE.name} \\\n"
          "    python run_experiments.py --experiments "
          "'BRACKET+wave-cora+bed-ehydro+mask-inlet+mask-manahawkin-open' --no-run")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
