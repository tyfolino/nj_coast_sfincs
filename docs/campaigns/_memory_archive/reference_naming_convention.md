<!-- Raw Claude-memory file, archived verbatim 2026-08-05 when the memory store was
     collapsed. Its standing content was merged into the new memory set and/or
     CLAUDE.md; this copy exists so the merge cannot have lost a detail.
     Superseded — do not treat as current. -->


# Naming convention (adopted 2026-07-27, user-driven)

**Authoritative doc: `nj_sandy_sfincs/docs/naming.md`** — full old→new mapping, retired list,
scored table. Read it before citing any experiment by name; the old vocabulary is gone from
code and memory but survives in prose records and notebook OUTPUTS.

## Why it changed
Names encoded SIX axes inconsistently (domain, solver, wave knob, forcing knob, bed params,
composition). Three collisions: **`v2` meant both a forcing revision (`phaselag_composite_v2`)
and a domain (`coast_v2`)**; **domain was encoded by ABSENCE** (`phaselag_shift` was equally
on the sealed mesh but didn't say so); and unions didn't read as unions.

## Domains — `DOMAINS` keys in `nj_sfincs/domain.py`
`sandy_v1` → **`v1_monmouth`**, `coast_v2` → **`v2_barnegat`**. Named by **how far south they
reach**, the only thing the staged march to Cape May changes (`v1_monmouth` → lat 40.15 ⊂
`v2_barnegat` → lat 39.70 ⊂ future `v3_…`). **The storm is NOT in the name** — it is constant
across every run, and if it ever varies (Florence roadmap) it belongs on its own axis.
Data files renamed to match: `region_v1_monmouth.geojson`, `region_v2_barnegat.geojson`,
`refinement_v2_barnegat.geojson`, **`data/frozen_mesh_v2_barnegat`**,
`scripts/build_refinement_v2_barnegat.py`. `DEFAULT_DOMAIN = "v2_barnegat"`.

## Experiments
`nj_sandy_sfincs` is v1-only and frozen ⇒ **no domain prefix there**. `nj_coast_sfincs` hosts
several domains ⇒ names are `<domain>/<arm>`, first token = the `NJ_DOMAIN` value.

- Sealed 2×2 keeps factorial names: `faber-waves-premier` ⭐, `faber-nowaves`,
  `galibier-waves`, `galibier-nowaves`.
- Everything else is a **delta from the premier**: `wave-…` `tide-…` `solver-…` `mask-…`
  `bed-…`. Live: `wave-ig`, `wave-deep30`, `tide-shift`, **`wave-deep30+tide-shift`** ⭐.
- **Unions = parents joined by `+`, alphabetical** ⇒ exactly one spelling.
- `premier` is a **role suffix**, not a name — each domain gets its own.
- **Retired arms were deliberately NOT renamed** (archival value): `phaselag_gtsm`,
  `phaselag_composite`, `phaselag_composite_v2`, `snapwave_deep_composite_v2`.
- **Templates deliberately NOT renamed**: `_template_sealed` / `_template` are already guarded
  by `premier.SEALED_TEMPLATE` / `LEGACY_TEMPLATE`; renaming the guarded path buys nothing.

## ⚠️ OPEN TENSION (2026-07-30) — `mask-inlet` is a DOMAIN marker wearing an arm's name
The 07-30 arms are `wave-cora+bed-ehydro+mask-inlet` and `…+mask-inlet+tide-shift`. But the
Barnegat Inlet mask repair is a property of the **domain** (it changes `sha(z,mask)`), not a
config delta — by this convention's own logic it should have been a domain version bump
(`v2_barnegat` → `v2p1_…`) with the arm staying `wave-cora+bed-ehydro`. It was named as a delta
because the repair and its control had to be distinguishable **inside one `reports/` table**,
and because a domain bump means a second frozen mesh (~1.3 GB) on a tight quota.
⇒ **Decide this before the next domain-level repair**, and remember that renaming afterwards is
a half-rename (see below). Related: [[reference_inlet_waterlevel_clamp]].

## Traps this exercise exposed
- ⚠️ **A rename that only moves DIRECTORIES is a half-rename.** The name also lives in the
  **row index inside `reports/*.csv`** and in prose. Both were fixed; check both next time.
- ⚠️ **`experiments/` is GITIGNORED** — git cannot undo dir moves. Inverse script at
  `scripts/rename_experiment_dirs_REVERT.sh`.
- ⭐ **`bdepth_m15/m20` were MISFILED as wave arms.** `bdepth` = boundary depth of the SFINCS
  **mask**, not the wave boundary ⇒ `mask-zmin15` / `mask-zmin20`, and they are ⛔ SUPERSEDED
  and OFF the sealed domain by construction. See [[project_domain_rebuild]].
- ✅ Verification that the rename was lossless: `premier.py` still audits **10/13 sealed**, and
  re-scoring `wave-deep30+tide-shift` reproduced every metric **bit-for-bit** (bias 0.273232,
  RMSE 0.449023, CSI 0.683999). `mv` preserved mtimes ⇒ floodmap caches stayed valid.
- `Experiment.legacy_name` (config.py) and `premier.PREMIER_LEGACY_NAME` carry the old names
  in code so they stay greppable.

Related: [[reference_premier_domain_guard]], [[reference_domain_registry]],
[[project_domain_expansion_v2]], [[project_snapwave_decoupling]], [[project_domain_rebuild]].
