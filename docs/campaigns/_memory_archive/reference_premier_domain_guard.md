<!-- Raw Claude-memory file, archived verbatim 2026-08-05 when the memory store was
     collapsed. Its standing content was merged into the new memory set and/or
     CLAUDE.md; this copy exists so the merge cannot have lost a detail.
     Superseded — do not treat as current. -->


# The premier and its domain — defined in code, not in memory (2026-07-21)

> ✅ **RESOLVED 2026-07-27 — `premier.py` IS MULTI-DOMAIN.** `EXPECTED` is a
> `{domain_name: DomainFingerprint}` dict and `expected()` resolves via `NJ_DOMAIN`, so the
> "every v2 dir audits UNRECOGNISED" problem is gone. `PREMIER_NAME` is `faber-waves-premier`
> on both domains — same configuration, different domain, which is exactly why the fingerprint
> is checked separately from the name.
>
> 🔴 **THE v2 FINGERPRINT MOVED 2026-07-30: `9ccbab0bc7a9fc0d` → `3b1356b9590c59ff`.** Same
> mesh, same bed — `z` is byte-identical — but the MASK was repaired (the open-ocean level had
> been imposed 2.6 km inside Barnegat Inlet) and **the mask is half the hash**. Faces and
> boundary edges are unchanged at 1,143,357 / 2,164, so ONLY the sha distinguishes them; do not
> try to tell these two apart by cell counts. The old value is registered as
> `premier.V2_BARNEGAT_PREMASK` so the whole 2026-07-26..29 campaign audits as **"PRE-REPAIR"**
> rather than "UNRECOGNISED" — those runs are not garbage, they are simply on another domain.
> ⭐ **Re-deriving a mask does NOT need a subgrid rebuild** (tables cover every face + uv point),
> so a fingerprint change of this kind costs minutes, not a rebuild.
> See [[reference_inlet_waterlevel_clamp]], [[project_domain_expansion_v2]],
> [[reference_domain_registry]].

> 🔴 **`experiments/_template_sealed` IS STALE — and rebuilding it is a TRAP (found 2026-08-04).**
> It carries **3,064** water-level BC cells; post-repair is **2,911** ⇒ it is still on
> `V2_BARNEGAT_PREMASK` (`9ccbab0bc7a9fc0d`). Cheap way to tell them apart without the hash:
> the BC cell count, since faces/edges are identical at 1,143,357 / 2,164.
> ⚠️ Because `is_sealed()` therefore returns **False**, `run_experiments.build_template()`
> does **not** refuse — it would `rmtree` the base of the premier. Its own guard comment is
> the warning: the sealed template is "NOT reproducible from BaseConfig alone" and rebuilding
> "would silently substitute a different domain under the premier's name."
> 🔑 **The staleness is a SYMPTOM, not a bug**: `faber-waves-premier` is defined on the
> pre-repair domain, `EXPECTED` moved to post-repair on 07-30, and they disagree precisely
> because the **premier promotion is on HOLD**. Fix the promotion decision, not the template.
> See [[project_handoff_2026_08_04]].

**`nj_sfincs/premier.py` is the single source of truth.** Audit anything with:
`NJ_ROOT=$PWD PYTHONPATH=$PWD micromamba/envs/sfincs/bin/python -m nj_sfincs.premier [dirs...]`
(no args = audit every experiment dir; exit 1 if any is off-domain).

| | faces | boundary edges | sha256(z,mask)[:16] |
|---|---|---|---|
| **SEALED** (premier's domain) | 547408 | **1635** | `45f4f74ca9a2347d` |
| LEGACY pre-rebuild | 547267 | **1676** | `ffc48087214bb848` |

The **41 extra boundary edges ARE the leak** — the free-outflow face hydromt cut across the
Navesink. `PREMIER_NAME = "faber-waves-premier"`, template `experiments/_template_sealed`,
built by `scripts/setup_sealed_premier.py` with `NJ_FROZEN_MESH=data/frozen_mesh_sealed`.
As of 2026-07-21 only **6 of 23** experiment dirs are on the sealed domain (the 5 `sealed_*`
runs + the template). `mask-zmin15/m20` read UNRECOGNISED — correct, they deliberately
changed the boundary depth, so they are a *third* domain.

## Why it exists
`run_experiments.py:47` hardcoded `TEMPLATE = EXP_ROOT / "_template"` (the LEGACY build),
while the premier was staged separately by `scripts/setup_sealed_premier.py`. The whole
tidal phase-lag A/B ran to a clean SLURM exit on the leaking domain and was void. See
[[project_tidal_phase_lag]].

## What was changed (uncommitted; user commits)
- **`nj_sfincs/premier.py`** (new) — `SEALED`/`LEGACY` fingerprints, `domain_fingerprint()`,
  `is_sealed()`, `assert_sealed_domain()`, `shrewsbury_obs_ok()`, `describe()`, CLI.
- **`run_experiments.py`** — `TEMPLATE` now `premier.SEALED_TEMPLATE` (override `NJ_TEMPLATE`);
  `prepare_experiment` asserts lineage right after `copytree`, **before** the solver;
  `collect_metrics` stamps a **`domain` column** on every metrics row + warns when not sealed
  (scoring legacy runs stays legal — doing it *silently* does not).
- **⚠️ `build_template()` rmtree's its target** — it now REFUSES if the target fingerprints as
  sealed. Without that, repointing `TEMPLATE` would have destroyed the premier's base.
  `_template_sealed` has **no `.window` stamp** (it wasn't built by `build_template`), so
  `template_matches()` now falls back to parsing `tstop` from its own `sfincs.inp` — otherwise
  it reads as stale and triggers that rebuild on every single invocation.

## 🔫 THE LOADED GUN BEHIND IT ALL — `frozen_mesh` default (found + FIXED 2026-07-21)
`BaseConfig.frozen_mesh` defaulted to **`data/frozen_mesh`** — the PRE-REBUILD, LEAKING mesh
(547,267 cells). `_template_sealed` was only ever sealed because
`scripts/setup_sealed_premier.py` sets `NJ_FROZEN_MESH=data/frozen_mesh_sealed` **explicitly**.
So **any** build that forgot the env var — a notebook run, a plain `build_template()` — silently
produced a leaking domain. **Default changed to `data/frozen_mesh_sealed`** (override still works).
This is the ROOT cause of the whole 2026-07-21 mess, one level below the `TEMPLATE` constant.

**`model/` explained (the "third, unrecognised domain"):** 547,285 faces / **1676** boundary edges
(leaking count) / sha `6cb93c911bd8a4e3`, dated 2026-06-29→07-03. It is **the canonical notebook's
build+run output** (`../model`), not a failed experiment — built with the then-default (leaking)
frozen mesh, and *before/around* the 07-03 freeze, hence 547,285 vs `_template`'s 547,267: the
documented **~18-cell environment sensitivity** of an unfrozen quadtree build. Stale, regenerable
by re-running the notebook, and it would now build SEALED thanks to the default change.
⚠️ **DELETED 2026-07-30** in the disk cleanup (1.8 G, user-approved) — neither viz notebook read
it. If the "third unrecognised domain" question ever comes back, this paragraph is the answer;
the directory itself is gone. See [[reference_disk_quota_dedupe]].

## The lesson worth keeping
**A coastal control cannot validate an interior experiment.** `phaselag_battery` matched the
premier's Sandy Hook phase lag to 0.3 min (16.9 vs 17.2) because the open coast is nearly
domain-independent — that looked like proof the staging was right. Meanwhile Shrewsbury was
30% down in tidal range and Shark was flat dead (0.03 m vs 1.35 m). **Check the mesh, don't
infer provenance from a gauge.** Identify lineage by fingerprint, not inode and not file size:
a per-arm forcing override rewrites `sfincs.nc` in place, giving each arm its own inode.
