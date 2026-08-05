# nj_coast_sfincs — read this first

SFINCS compound-flood hindcast of **Hurricane Sandy (28–31 Oct 2012)** on the New Jersey
coast, built with HydroMT-SFINCS. Compound = surge + wave setup + wind + rain + river
discharge together, validated against NOAA/USGS gauges, USGS high-water marks and the FEMA
MOTF surge extent.

The long-run goal is a config-driven template for the whole NJ coast, marching south in
domain increments toward Cape May, and eventually a compound-flooding paper.

---

## 1. The one thing that will bite you: domains

Every geographic fact lives in **`nj_sfincs/domain.py`**, keyed by the `NJ_DOMAIN` env var.
Two domains are registered:

| `NJ_DOMAIN` | extent | faces | status |
|---|---|---|---|
| `v1_monmouth` | Sandy Hook → Sea Girt (lat 40.15) | 547,408 | **FROZEN** — the sealed-premier campaign |
| `v2_barnegat` | + southern lobe to Barnegat Inlet (lat 39.70) | 1,143,357 | live (default) |

**The same experiment name exists on every domain and means a different model each time.**
`faber-waves-premier` is a *configuration*, not a run — it exists under both domains. That
is why runs live at `experiments/<domain>/<arm>` and why `nj_sfincs/premier.py` checks a
**fingerprint** (`faces`, `boundary_edges`, `sha256(z, mask)`) rather than trusting a name.

That guard exists because a full SLURM sweep once completed cleanly, with plausible
numbers, and was **scientifically void** — it had been staged from the wrong template. The
open coast is nearly domain-independent, so the coastal control *passed*, while the estuary
the experiment was about was 30% down in tidal range. Read `nj_sfincs/premier.py`'s module
docstring before you touch staging.

```bash
python -m nj_sfincs.premier                    # audit every run dir on the active domain
NJ_DOMAIN=v1_monmouth python -m nj_sfincs.premier
```

`BAD` lines are not necessarily errors — a known-but-superseded domain (e.g. the v2
pre-mask-repair campaign) and the deliberately inadmissible `BRACKET+…` arm both report by
name. `UNRECOGNISED` is the alarm.

## 2. Layout

```
nj_sfincs/          the package — config, domain registry, model build, validation, plots
  domain.py         ⭐ ALL geography. Add a domain here, not as literals elsewhere.
  config.py         BaseConfig + WaveConfig + the EXPERIMENTS registry; exp_root()
  premier.py        ⭐ the premier + domain fingerprints. The staging guard.
  model.py          build_static / add_forcing / add_waves / finalize
  validate.py       load_floodmap, hwm_metrics, motf_metrics, gauge/interior-gauge scoring
  plots.py animate.py provenance.py params.py wind.py gdaltools.py
run_experiments.py  the sweep driver (stage → run → validate → aggregate)
scripts/            data acquisition (download_*/build_*), template setup, scoring, one-offs
experiments/<domain>/<arm>/     run dirs  (gitignored)
data/               inputs; frozen_mesh_<domain>/ is the canonical mesh (NOT cheaply rebuilt)
reports/            scored CSVs;  reports/v1_monmouth/ holds the frozen campaign's results
docs/naming.md      ⭐ the naming convention + the frozen v1 scoreboard
docs/campaigns/     ⭐ campaign histories (see §5)
notebooks/          viz; v1_monmouth/ holds the frozen campaign's notebooks
hpc/                SLURM + Amarel bootstrap
```

**`~/nj_sandy_sfincs` is NOT a second project.** It was v1; since 2026-08-05 it holds only
the toolchain — `micromamba/`, `hydromt_sfincs/`, the `.sif` images and v1's git history —
which this repo symlinks to. It has its own README saying so. Never point `NJ_ROOT` or
`PYTHONPATH` at it.

## 3. Running things

```bash
export PATH=$HOME/nj_sandy_sfincs/micromamba/envs/sfincs/bin:$PATH   # git lives here too
export PYTHONPATH=$PWD

python run_experiments.py --experiments <arm> --check   # READ-ONLY: paths + domain assert
python run_experiments.py --experiments <arm> --tstop 2012-10-29   # short-window smoke
python run_experiments.py --slurm            # submit the sweep
python run_experiments.py --validate-only    # aggregate once jobs finish

NJ_DOMAIN=v2_barnegat python scripts/score_v2.py     # score the v2 ladder
python -m unittest discover -s tests         # the test suite (stdlib unittest, ~19 s)
NJ_DOMAIN=v1_monmouth python scripts/export_animations.py --list   # animation exports
```

🔴 **`--check` is the ONLY read-only mode.** `--inputs-only`, `--no-run` and the
deprecated `--dry-run` all `rmtree` each experiment directory before skipping the solver.
Reading "dry run" as "touches nothing" destroyed the v2 premier's 1.8 GB of output on
2026-08-05; `tests/test_domain_and_staging.py` now pins the ordering that prevents it.

⚠️ **Submit the STAGED dir via `run.submit_slurm(dir, sif=...)`, not `--slurm`,** when you
have already staged. Always pass `sif` explicitly — leaving it to the batch script's
fallback is how a sweep silently ran on the wrong engine.

⚠️ **`build_template()` calls `rmtree` on its target.** It refuses when the template is
already sealed for the active domain, but a template whose fingerprint has drifted does
*not* trip that guard. Do not run the sweep driver to "just rebuild" a template.

## 3a. Tests

`tests/` uses stdlib **`unittest`** — pytest is deliberately not in the pinned env.

```bash
PYTHONPATH=$PWD python -m unittest discover -s tests -v
```

20 tests, ~19 s, no SFINCS and no writes into `experiments/`. They cover the domain
registry, the fingerprint invariants (including "a bracket must never be in `EXPECTED`"),
per-domain path resolution, and — most importantly — that `prepare_experiment` refuses a
wrong domain *before* it destroys the destination. That last one fails loudly on the
pre-2026-08-05 ordering.

The repo had **zero** tests before this, and `domain.py` carried a comment claiming a test
that did not exist. If a docstring says something is covered, check.

## 4. Traps that have actually cost runs

- **A roughness or elevation change needs a SUBGRID rebuild on the frozen mesh.**
  `build_static` copies the frozen mesh and returns early, so it will silently produce a
  no-op template. A *mask* change is the opposite: no subgrid rebuild, but the fingerprint
  moves.
- **For any bed edit, diff `z_volmax`, not `z_zmin`.** A carve restores sub-cell relief; it
  is not a uniform lowering, and `z_zmin` will show ~nothing while the run changes.
- **eHydro sign convention flips by USACE district.** Shark River (NY district) ships
  negative elevations; Barnegat/ICW/Oyster Creek (Philadelphia) ship positive depths. A
  hardcoded formula produces a silently empty raster on the wrong side.
- **Import `pyproj` before `hydromt_sfincs`** — `nj_sfincs/__init__.py` does this; it
  prevents a native double-free in `downscale_floodmap`.
- **Disk quota exhaustion never says "quota".** It SIGSEGVs jobs or silently truncates
  output maps while `sacct` reports COMPLETED. Run `scripts/dedupe_experiment_inputs.py`.
- **A truncated floodmap cache reads back clean and scores bone-dry.** Writes are atomic now.
- **SnapWave is 90–95% of runtime** and scales per-iteration; the 3 h batch default is not
  enough for v2 or deep-boundary runs. Pass `extra_args=['--time=12:00:00', ...]`.
- **`zb` is NaN on SFINCS-inactive faces**, so any hm0 comparison must restrict to faces
  active in *both* runs.
- **An HWM records that water ARRIVED, not which way it came in.**

## 5. Where the history lives

`docs/campaigns/` holds one dated markdown per investigation — the bridge-as-dam root
cause, the Shrewsbury mass leak, the tidal phase lag, SnapWave decoupling, the inlet
water-level clamp, the HWM estimator artefact, the bay volume deficit, and the rest.

**Read them as history, not as fact.** They are reverse-chronological logs and several
carry conclusions that were later retracted — the retraction always sits above the claim it
retracts. Each file says so in its header. What is believed true *now* is in the Claude
memory store (short, current-only, one fact per file) and in this document.

`docs/naming.md` is authoritative for arm names and carries the frozen v1 scoreboard.

## 6. Conventions

- Domains `v1_monmouth` / `v2_barnegat`; arms are `faber-waves-premier` plus `wave-`,
  `tide-`, `solver-`, `mask-`, `bed-` deltas; unions joined by `+` in alphabetical order.
- **The user commits and pushes. Claude may `git add`, never `git commit`.**
- Don't edit notebooks while a run is in flight — it wipes outputs.
- Prefer coordinate boxes and thresholds over auto-derived polygons.
- `nbstripout` is configured per-clone; run `python scripts/setup_nbstripout.py` after a
  fresh clone or notebook outputs will be committed (that is why `.git/` is ~293 MB).
