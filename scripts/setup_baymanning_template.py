#!/usr/bin/env python3
"""Build `_template_baymanning` — the sealed v2 template with a rougher lagoon bed.

Identical to `_template_sealed` in every respect except the land-cover raster the roughness
and SUBGRID tables are reclassified from: `nlcd_2012_baymanning`, which re-codes the 203,075
open-water pixels inside Barnegat Bay to class 12 -> Manning n = 0.035, while class 11 stays
0.020 everywhere else. See scripts/build_bay_manning.py for why, and the catalog entry for
the measurement that motivates it.

A template rebuild is required because roughness is consumed by `quadtree_subgrid.create`;
it is NOT a `prepare_experiment` swap like `waterlevel_geodataset`.

THE INVARIANT THIS SCRIPT EXISTS TO PROVE: the domain must not move. The seal is
sha(z, mask) and excludes roughness, so a correct build produces a template that audits as
`v2_barnegat` with the SAME fingerprint as `_template_sealed`. If it does not, the mesh or
the elevation merge changed underneath us and the arm is not comparable to the premier.
That is checked here, before the solver is given three hours.

Run:  NJ_ROOT=$PWD PYTHONPATH=$PWD NJ_DOMAIN=v2_barnegat \
      python scripts/setup_baymanning_template.py
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
TEMPLATE = EXP / "_template_baymanning"

LULC = "nlcd_2012_baymanning"
TABLE = DATA / "roughness" / "NLCD_CONUS_mapping_baymanning.csv"


def main() -> int:
    if not TABLE.exists():
        raise SystemExit(f"missing {TABLE} — run scripts/build_bay_manning.py first")
    if not REF.exists():
        raise SystemExit(f"missing reference template {REF}")

    base = replace(BaseConfig(), roughness_lulc=LULC, reclass_table=TABLE)
    print(f"[template] roughness lulc = {base.roughness_lulc}")
    print(f"[template] reclass table  = {base.reclass_table.name}")
    print(f"[template] frozen mesh    = {base.frozen_mesh}")

    if TEMPLATE.exists():
        shutil.rmtree(TEMPLATE)
    model.build_static(base, TEMPLATE)

    # ⚠️ build_static COPIES the frozen mesh directory and RETURNS EARLY — including its
    # pre-built sfincs_subgrid.nc, which was baked with the ORIGINAL roughness. That is
    # correct and deliberate for the mesh (a fresh quadtree build is environment-sensitive,
    # ~18 cells of drift, which would break the seal and the A/B). But it means the
    # roughness swap never reaches the subgrid: the first build of this template came out
    # with uv_navg/uv_nrep bit-identical to the reference.
    #
    # So regenerate ONLY the subgrid on the frozen grid, the same way
    # scripts/rebuild_subgrid_h.py does for an elevation change. The grid, z and mask are
    # untouched, so the fingerprint is preserved by construction; only the roughness
    # source differs from the reference build.
    print("\n[subgrid] frozen mesh carries the OLD subgrid — regenerating with "
          f"{base.roughness_lulc}")
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
    # Stage WITH waves so snapwave.* exist, exactly as _template_sealed was staged; the
    # per-experiment wave knobs are applied later by prepare_experiment.
    wave_cfg = EXPERIMENTS["faber-waves-premier"].waves
    sw = model.add_waves(wave_cfg, base, sf)
    model.finalize(wave_cfg, base, sf, TEMPLATE, sw)
    del sf
    gc.collect()

    # ── the invariant: same domain, different bed roughness ──────────────────
    print("\n=== verification ===")
    fp_new, fp_ref = premier.domain_fingerprint(TEMPLATE), premier.domain_fingerprint(REF)
    print(f"  fingerprint  ref {fp_ref}")
    print(f"  fingerprint  new {fp_new}")
    if fp_new != fp_ref:
        raise SystemExit(
            "!! DOMAIN MOVED. Roughness is not in the seal, so an identical mesh and "
            "elevation merge MUST reproduce the reference fingerprint. Something else "
            "changed; do not run this arm."
        )
    print("  ✅ domain identical to _template_sealed (roughness is not in the seal)")

    a = xr.open_dataset(REF / "sfincs_subgrid.nc")
    b = xr.open_dataset(TEMPLATE / "sfincs_subgrid.nc")
    for v in ("z_zmin", "z_zmax", "z_volmax"):
        d = float(np.nanmax(np.abs(a[v].values - b[v].values)))
        print(f"  {v:10s} max|Δ| {d:.6g}  {'OK' if d == 0 else '!! BATHYMETRY MOVED'}")
    for v in ("uv_navg", "uv_nrep"):
        da, db = a[v].values, b[v].values
        ch = ~np.isclose(da, db, equal_nan=True)
        frac = 100 * ch.mean()
        if ch.any():
            print(f"  {v:10s} changed at {ch.sum()} / {ch.size} points ({frac:.2f}%)  "
                  f"median {np.nanmedian(da[ch]):.4f} -> {np.nanmedian(db[ch]):.4f}")
        else:
            print(f"  {v:10s} !! UNCHANGED — the roughness swap did not reach the subgrid")
    print(f"\nwrote {TEMPLATE}")
    print("Stage the arm with:\n"
          "  NJ_DOMAIN=v2_barnegat NJ_TEMPLATE=experiments/_template_baymanning \\\n"
          "    python run_experiments.py --experiments 'wave-cora+bed-baymanning' --no-run")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
