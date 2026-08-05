<!-- Raw Claude-memory file, archived verbatim 2026-08-05 when the memory store was
     collapsed. Its standing content was merged into the new memory set and/or
     CLAUDE.md; this copy exists so the merge cannot have lost a detail.
     Superseded — do not treat as current. -->


Two things that will silently waste a rebuild. Both bit me on 2026-07-14.

## 1. There are TWO data_catalog.yml — only one is live

- **LIVE:** `data/data_catalog.yml`  ← this is what `BaseConfig.data_libs` points at.
- **STALE:** `data/elevation/data_catalog.yml` — nothing references it, it is an OLDER copy
  (still lists `gebco_nj` instead of `gmrt_nj`, lacks `narrows_wide_h`).

I added a new elevation tier to the stale one, and hydromt silently logged
`No data in domain for ehydro_nj, skipped` and built the whole domain WITHOUT the carve. The
failure mode is a WARNING, not an error — the build "succeeds" with the tier missing. Only the
build-time invariant caught it.

**Register new datasets in `data/data_catalog.yml`.** Consider deleting the stale copy.

## 2. `refinement_polygons.geojson` is AHEAD of `data/frozen_mesh`

`data/quadtree/refinement_polygons.geojson` carries `shrewsbury_l4` + `navesink_l4` at
`refinement_level 4` (**12.5 m**), staged ~2026-07-05. But `data/frozen_mesh` was built
2026-07-03 and tops out at **25 m** (mesh levels 1-4 = 200/100/50/25 m).

⇒ **Any rebuild silently upgrades the estuary to 12.5 m**: 65,231 → 188,922 faces inside those
polygons, i.e. **+123,691 faces / +33% active cells / +33% runtime on every run thereafter** —
and it breaks comparability with every 25 m run in the campaign. L4 is a **NULL lever** anyway
(the 12.5 m rebuild, job 57864095, moved the Shrewsbury gauge +0.04 m).

**FIX SHIPPED:** `data/quadtree/refinement_polygons_25m.geojson` (same file, L4 polygons
dropped) is now the `BaseConfig.refinement` default; override with `NJ_REFINEMENT=<path>`.
With it, the 07-14 region+eHydro rebuild costs **+141 faces** instead of +124k — a genuinely
minimal, attributable change.

**How to apply:** before any rebuild, diff the mesh you are comparing against for BOTH of these.
A rebuild that quietly changes resolution is not a controlled experiment — you can no longer
attribute the result to the fix you made. See [[project_shrewsbury_reinvestigation]].

## 3. `prepare_experiment` used to DROP `crsfile`/`storevel` — ✅ FIXED AND NOW CONFIRMED

The crsfile/storevel restore lived ONLY in `scripts/setup_sealed_premier.py`, so any
harness-staged arm silently lost the flux/leak cross-section diagnostics and came out with a
non-empty `sfincs.inp` diff against the premier. **Ported 2026-07-25 as
`model.restore_diagnostics()`, called at the end of `run_experiments.prepare_experiment`.**

**✅ CONFIRMED IN PRODUCTION 2026-07-26** staging `wave-deep30+tide-shift`: `crsfile =
sfincs.crs` and `storevel = 1` both present, `sfincs.crs` copied in, and the sorted `sfincs.inp`
diff was **0 keys against BOTH parent arms** — with **no hand-patching at all**. ⇒ **the old
"patch the staged dir by hand, then submit it directly" dance is OBSOLETE.**

⚠️ **Still true and still load-bearing:** submit the **STAGED dir** via
`run.submit_slurm(exp_dir, sif=str(BaseConfig().container_sif))`. Do NOT submit via `--slurm`,
which re-runs `prepare_experiment` and rebuilds the directory you just verified. And always pass
`sif=` explicitly — leaving it to the batch script's fallback is how the 2026-07-20 phaselag runs
silently landed on Galibier instead of Faber.
⚠️ `config.BASE` does not exist — it is `BaseConfig()`.

## 5. `PROJ` is ALREADY an env var on this account — the slurm scripts collided with it

Found 2026-07-26 in `nj_coast_sfincs`. `hpc/build_mesh.slurm` (and the probe script copied from
it) opened with the idiom `PROJ="${PROJ:-$PWD}"` and then `export PYTHONPATH="$PROJ"`. But the
user's shell profile **already exports `PROJ=/home/tpj8/nj_sandy_sfincs`**, so `${PROJ:-$PWD}`
kept the inherited value and the job silently imported **the OTHER repo's `nj_sfincs` package**.
It surfaced only as `ImportError: cannot import name 'domain' from 'nj_sfincs'
(/home/tpj8/nj_sandy_sfincs/nj_sfincs/__init__.py)` — the path in the message is the tell.

**FIX:** the repo root is always the submit dir; use a name that cannot collide (`REPO="$PWD"`).
Both slurm scripts in the new repo now do. **Never `${SOMENAME:-$PWD}` for a repo root** unless
you know the name is unused — and `PROJ` in particular is doubly bad, since it also reads like a
PROJ-library variable.

## 4. Reading `sfincs_map.nc`: `zb` is NaN wherever the SFINCS mask is 0

Bit me 2026-07-26 auditing the decoupled SnapWave domain. Any `zb > x` / `zb < x` test over
SFINCS-inactive faces returns **0 matches** — which reads as "clean" when it means "no data".
**Use `snapwavedepth` for anything about the SnapWave-only domain.** See
[[project_snapwave_decoupling]] for the sibling trap (hm0 comparisons must be restricted to
faces active in BOTH runs, or premier-inactive cells count as hm0 = 0 and fake a +2 m signal).
