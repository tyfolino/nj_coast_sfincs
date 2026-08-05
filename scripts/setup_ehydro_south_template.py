#!/usr/bin/env python3
"""Build `_template_ehydro_south` — the sealed v2 template with the southern channels carved.

Prepends `ehydro_south` to the elevation stack and regenerates ONLY the subgrid on the
frozen mesh. Everything else — grid, coarse z, mask, boundaries, forcing, waves — is the
sealed template's.

WHY SUBGRID-ONLY (this is the important part, not a shortcut):
`model.build_static` COPIES the frozen mesh directory and returns early, so a new elevation
tier never reaches the coarse `z`. Rebuilding the quadtree from scratch instead would be
environment-sensitive (~18 cells of drift), which breaks the domain seal AND the A/B. But
the coarse `z` is not what carries conveyance — the SUBGRID tables are, and those are
rebuilt here from the carved elevation stack. So:

  * z / mask unchanged  => the domain fingerprint is preserved => this arm is directly
    comparable to `wave-cora`, which is the whole point.
  * subgrid rebuilt from the carve => the solver actually feels the deeper channels.

⚠️ CONSEQUENCE TO REMEMBER WHEN ANALYSING: `sfincs.nc`'s `z` will NOT show the carve. Any
depth check must read `sfincs_subgrid.nc` (z_zmin / uv_zmin), not `z`. Cells also cannot
newly activate, since the mask is untouched — this carve can deepen an existing channel but
cannot open one the mask never had.

Run:  NJ_ROOT=$PWD PYTHONPATH=$PWD NJ_DOMAIN=v2_barnegat \
      python scripts/setup_ehydro_south_template.py
"""

from __future__ import annotations

import gc
import shutil
from dataclasses import replace
from pathlib import Path

import numpy as np
import xarray as xr
from hydromt_sfincs import SfincsModel

import nj_sfincs  # noqa: F401  (PROJ primer — must precede hydromt_sfincs)
from nj_sfincs import model, premier
from nj_sfincs.config import exp_root, DATA, EXPERIMENTS, ROOT, BaseConfig

EXP = exp_root()
REF = EXP / "_template_sealed"
TEMPLATE = EXP / "_template_ehydro_south"
CARVE = DATA / "elevation" / "ehydro_south.tif"


def main() -> int:
    if not CARVE.exists():
        raise SystemExit(f"missing {CARVE} — run scripts/build_ehydro_south.py first")
    if not REF.exists():
        raise SystemExit(f"missing reference template {REF}")

    b0 = BaseConfig()
    # The carve goes ON TOP: it is the only source that measured the bed UNDER the water.
    elev = ({"elevation": "ehydro_south"},) + tuple(b0.elevation_list)
    base = replace(b0, elevation_list=elev)
    print("[template] elevation stack (carve prepended):")
    for e in base.elevation():
        print("   ", e)

    if TEMPLATE.exists():
        shutil.rmtree(TEMPLATE)
    model.build_static(base, TEMPLATE)

    print("\n[subgrid] frozen mesh carries the UNCARVED subgrid — regenerating")
    roughness_list = [{"lulc": base.roughness_lulc,
                       "reclass_table": str(base.reclass_table)}]
    sf = SfincsModel(str(TEMPLATE), data_libs=base.data_libs, mode="r+")
    sf.quadtree_grid.read()
    sf.quadtree_roughness.create(roughness_list=roughness_list, nrmax=200)
    sf.quadtree_subgrid.create(
        elevation_list=base.elevation(),
        roughness_list=roughness_list,
        nr_subgrid_pixels=base.nr_subgrid_pixels,
        nrmax=2000,        # DO NOT lower — smaller explodes the block loop
        write_dep_tif=True,
        write_man_tif=True,
    )
    sf.quadtree_subgrid.write()
    del sf
    gc.collect()

    sf = SfincsModel(str(TEMPLATE), data_libs=base.data_libs, mode="r+")
    model.add_forcing(base, sf)
    wave_cfg = EXPERIMENTS["faber-waves-premier"].waves
    sw = model.add_waves(wave_cfg, base, sf)
    model.finalize(wave_cfg, base, sf, TEMPLATE, sw)
    del sf
    gc.collect()

    # ── verification ─────────────────────────────────────────────────────────
    print("\n=== verification ===")
    fp_new, fp_ref = premier.domain_fingerprint(TEMPLATE), premier.domain_fingerprint(REF)
    print(f"  fingerprint ref {fp_ref}")
    print(f"  fingerprint new {fp_new}")
    if fp_new != fp_ref:
        raise SystemExit("!! DOMAIN MOVED — z/mask should be untouched by a subgrid-only "
                         "rebuild. Do not run this arm.")
    print("  ✅ domain identical to _template_sealed — comparable to wave-cora")

    a = xr.open_dataset(REF / "sfincs_subgrid.nc")
    c = xr.open_dataset(TEMPLATE / "sfincs_subgrid.nc")
    moved_any = False
    for v in ("z_zmin", "z_zmax", "z_volmax", "uv_zmin", "uv_zmax"):
        da, db = a[v].values, c[v].values
        ch = ~np.isclose(da, db, equal_nan=True)
        if ch.any():
            moved_any = True
            d = db[ch] - da[ch]
            print(f"  {v:9s} changed at {ch.sum():7d} / {ch.size} ({100 * ch.mean():.3f}%)  "
                  f"median Δ {np.median(d):+.3f} m   deepened {100 * (d < 0).mean():.0f}%")
        else:
            print(f"  {v:9s} unchanged")
    for v in ("uv_navg", "uv_nrep"):
        ch = ~np.isclose(a[v].values, c[v].values, equal_nan=True)
        print(f"  {v:9s} changed at {ch.sum()} points "
              f"({'expected ~0 — roughness untouched' if ch.sum() < c[v].size * 0.02 else '!! unexpected'})")
    if not moved_any:
        raise SystemExit("!! THE CARVE DID NOT REACH THE SUBGRID — nothing to run. "
                         "Check that ehydro_south.tif overlaps active cells.")

    print(f"\nwrote {TEMPLATE}")
    print("Stage with:\n"
          "  NJ_DOMAIN=v2_barnegat NJ_TEMPLATE=experiments/_template_ehydro_south \\\n"
          "    python run_experiments.py --experiments 'wave-cora+bed-ehydro' --no-run")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
