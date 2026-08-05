<!-- Raw Claude-memory file, archived verbatim 2026-08-05 when the memory store was
     collapsed. Its standing content was merged into the new memory set and/or
     CLAUDE.md; this copy exists so the merge cannot have lost a detail.
     Superseded — do not treat as current. -->


# Handoff — 2026-08-04

**No SLURM jobs were fired today, on purpose.** Nothing scientific was staged and the one
infrastructure action turned out to be contraindicated (see the blocker below). Two files
are `git add`-ed and uncommitted: `nj_sfincs/model.py`, `nj_sfincs/domain.py`.

## 🚀 PICK UP HERE — Test B, the reconstruction screen

The gate for everything Sandy-Hook-related. Free, no SLURM. Design in
[[reference_sandy_hook_gap]]; **pre-register the pass criterion before looking.**
Score GSSR / Parker-corrected GTSM / CORA at **Battery + Atlantic City** (both complete
through the crest) on peak level, peak timing, tidal amplitude ratio. Nothing gets run
unless a candidate passes.

## 🔴 THE BLOCKER — `_template_sealed` is stale, and rebuilding it is a trap

It has **3,064** water-level BC cells; post-repair is **2,911** ⇒ it is on
`V2_BARNEGAT_PREMASK` (`9ccbab0bc7a9fc0d`), not `EXPECTED`. So `premier.is_sealed()`
returns False, which means `run_experiments.build_template()` does **not** refuse — it
would `rmtree` it. Its own guard comment says why that is bad: the sealed template is
"NOT reproducible from BaseConfig alone" and rebuilding "would silently substitute a
different domain under the premier's name."

⚠️ **The staleness is a SYMPTOM, not a bug.** `faber-waves-premier` is defined on the
pre-repair domain; `EXPECTED` moved to post-repair on 07-30; they disagree precisely
because the **premier promotion is on HOLD**. The fix is to make the promotion decision,
not to rebuild the template. The bracket has since strengthened the case for promoting
(tilt |err| 0.169 → 0.066). See [[reference_premier_domain_guard]].

## ✅ Decisions taken today

- **STAY ON v2_barnegat.** v2 geographically contains v1 (39.70–40.52 vs 40.15–40.52,
  same lon span), so every northern-boundary experiment is answerable there with the two
  interior gauges and ~19 more HWM marks. ⚠️ And the v1 repo is a **pre-domain-registry
  codebase** — see [[reference_shared_memory_symlink]].
- **The southward rebuild is DEFERRED, not retired.** The bracket's pre-registered rule
  fired (REBUILD JUSTIFIED, [[reference_bracket_pattern]]); today's deferral is a
  scheduling choice to avoid the southern eHydro DEM work, and should be recorded as such
  rather than left implicit.
- **Wind is demoted** as a suspect, consistent with [[reference_wind_forcing_investigation]].
  ⚠️ But Leijnse et al. 2025 independently report ERA5 **underestimates peak TC winds** —
  a claim about the storm peak, NOT about the bay/ocean roughness question that was tested,
  so it does not overturn the weakening. See [[reference_florence_boundary_practice]].

## ✅ Done today

- **Test A — the Sandy Hook gap is REAL.** Re-queried CO-OPS across both products and both
  datums; all four stop at **2012-10-29 23:36 UTC**, ~at landfall. Not a fetch artifact.
  ⇒ GESLA-4 is dead as a source (same underlying record). [[reference_sandy_hook_gap]]
- **`model._report_waterlevel_boundary`** — prints the whole `mask==2` set as an alongshore
  latitude profile every build, called before `_check_domain_invariants`. Validated against
  the known defect: band 39.75–39.80 reads 368 cells / W edge −74.1132 / dW −2.52 km on
  `_template_sealed` vs 223 / −74.0859 / −0.19 km on `_template_ehydro_inletmask` — the
  145-cell inlet intrusion, legible from the build log the whole time.
  ⚠️ It is a **REPORT, not an assert** — the docstring records the five predicates that do
  not work, so they are not re-attempted. Also: do **not** group BC cells with
  `connected_components` on `face_face_connectivity`; the line is one cell wide and ragged,
  so consecutive cells often touch only at a CORNER and it fragments into hundreds of
  single-cell groups.
- **The 40.52 north cut documented** in `domain.py` as a known, accepted limit — the region
  file is a RECTANGLE, so its north edge is a straight latitude cut across Raritan Bay, and
  the Battery↔AC interpolant cannot reproduce that basin's measured 1.12–1.15× interior
  maximum ⇒ ~15% under-forced by construction. A wall is wrong there (Narrows/Arthur Kill
  carry the Upper Bay + Hudson prism) and a Sandy Hook node lost twice.

## 🔭 Open finding, undecided

**70 water-level BC cells sit on dry land, up to +1.90 m**, all at lat 40.5199–40.5201.
Source is the `arthur_kill_north` MaskOverride (`3→2` for every cell `y > 4,484,000`, no x
bounds, **no depth condition**). It runs BEFORE the "(d) seal wet outflow" block, so that
block sees `mask==2` and leaves them alone — quietly reversing that block's own stated
reasoning that dry outflow cells are left alone so flood water can leave. Blast radius
looks tiny (outermost row, far north of anything scored). Fix would be a depth bound;
it is a mask change so it needs a control, and the expected effect is null.

## 📋 The three work items from the Florence paper

Full detail in [[reference_florence_boundary_practice]]. In order of cost:

1. **The boundary is generated by a RULE; theirs is DRAWN.** Migrating to a curated
   water-body polygon eliminates the intrusion class outright instead of reporting on it.
   Safe path = *capture-then-simplify*: capture today's repaired `mask==2` as an explicit
   artifact, switch the build to read it, **verify the fingerprint does not move**, only
   then delete the generating machinery. ~370–400 of ~838 mask/boundary lines are deletion
   candidates. ⚠️ `_report_waterlevel_boundary` becomes obsolete under a drawn boundary —
   its remaining use is as the verification tool for the migration.
2. **Outflow, not imposed level, is the default at a lateral terminus.** Bears on the
   40.52 cut and `arthur_kill_north`. ⚠️ Do NOT convert the 40.52 cut to outflow — Raritan's
   dredged channels run to −23 m there and an outflow BC on deep water is the Navesink drain.
3. **2 support points vs their 341.** The largest single difference and what makes
   everything else fragile. Blocked on Test B.

## 🧰 Traps confirmed today

- **There are ZERO tests in the repo.** No `tests/`, no `test_*.py`, no pytest config.
  `domain.py:440-441` claims "there is a test that asserts this reproduces the original
  classifier exactly" — **that test does not exist.** For a deletion-heavy refactor the only
  safety nets are the mesh fingerprint, `_check_domain_invariants`, the BC report, and
  `build_static(skip_subgrid=True)` dry runs (1–10 min).
- **`git` is slow on this filesystem** — `git status` and `git log` repeatedly timed out at
  60–120 s while `git add` had already succeeded. Check the result before retrying.
- **No PDF text extractor in any env** (no poppler, no pypdf/fitz). `pip install --target`
  into the scratchpad works and network is available.

Related: [[project_handoff_2026_08_03]], [[reference_bracket_pattern]],
[[reference_bay_volume_deficit]], [[reference_inlet_waterlevel_clamp]]
