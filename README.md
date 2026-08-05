# nj_coast_sfincs — NJ coastal compound-flood hindcast

A [SFINCS](https://github.com/Deltares/SFINCS) hindcast of **Hurricane Sandy (28–31 Oct
2012)** flooding on the New Jersey coast, built with
[HydroMT-SFINCS](https://github.com/Deltares/hydromt_sfincs). Unlike a surge-only model it
represents **compound** coastal flooding — storm surge, wave setup, wind, rainfall and
river discharge together — and is validated against NOAA/USGS gauges, USGS high-water marks
and the FEMA MOTF surge extent.

The repo is built to march south in domain increments toward Cape May, so geography is a
registry rather than a set of literals. See `docs/roadmap.md`.

> **Working on this with Claude Code?** Start at [`CLAUDE.md`](CLAUDE.md) — it covers the
> domain model, the staging guard, and the traps that have actually cost runs.

## Domains

| `NJ_DOMAIN` | extent | faces | status |
|---|---|---|---|
| `v1_monmouth` | Sandy Hook → Sea Girt (lat 40.15) | 547,408 | **frozen** — the sealed-premier campaign |
| `v2_barnegat` | + southern lobe to Barnegat Inlet (lat 39.70) | 1,143,357 | live (default) |

An experiment *name* is a configuration, so the same name exists on every domain and means
a different model each time. Runs therefore live at `experiments/<domain>/<arm>`, and
`nj_sfincs/premier.py` verifies a domain **fingerprint** — `faces`, `boundary_edges`,
`sha256(z, mask)` — rather than trusting the name. See `docs/naming.md`.

## Setup

The conda env and containers live in `~/nj_sandy_sfincs` (the toolchain directory — see its
README) and are symlinked in as `micromamba/`, `hydromt_sfincs/`, `sfincs-*.sif`.

```bash
export PATH=$HOME/nj_sandy_sfincs/micromamba/envs/sfincs/bin:$PATH
export PYTHONPATH=$PWD
python scripts/setup_nbstripout.py      # once per clone, before touching notebooks
```

Building the env from scratch: `micromamba create -n sfincs -f environment.yml`
(`hpc/environment.yml` is the pinned Amarel variant). ERA5 downloads need `~/.cdsapirc`.

## Running

```bash
python run_experiments.py --experiments <arm> --dry-run        # resolve paths only
python run_experiments.py --experiments <arm> --tstop 2012-10-29   # short-window smoke
python run_experiments.py --slurm && python run_experiments.py --validate-only
NJ_DOMAIN=v2_barnegat python scripts/score_v2.py               # score the ladder
python -m nj_sfincs.premier                                     # audit run dirs
```

Data acquisition is `scripts/download_*.py` and `scripts/build_*.py`; provenance for every
layer is in `data/data_catalog.yml`.

## Layout

| path | what |
|---|---|
| `nj_sfincs/` | the package — `domain.py` (all geography), `config.py`, `premier.py` (the staging guard), `model.py`, `validate.py`, `plots.py` |
| `run_experiments.py` | sweep driver: stage → run → validate → aggregate |
| `scripts/` | data acquisition, template setup, scoring, workstream one-offs |
| `experiments/<domain>/<arm>/` | run directories (gitignored) |
| `data/` | inputs; `frozen_mesh_<domain>/` is canonical and not cheaply rebuilt |
| `reports/` | scored CSVs; `reports/v1_monmouth/` is the frozen campaign's results |
| `docs/naming.md` | naming convention + the frozen v1 scoreboard |
| `docs/campaigns/` | dated investigation histories — **read as history, not fact** |
| `docs/roadmap.md` | goals and project context |
| `notebooks/` | visualization; `v1_monmouth/` holds the frozen campaign's notebooks |
| `hpc/` | SLURM scripts + Amarel bootstrap |
| `share/` | export for external collaborators (masked, compressed, documented) |

## Status

`v1_monmouth` is closed: the mass leak was found and fixed at its root, the premier
selected, and the scoreboard frozen in `docs/naming.md`. `v2_barnegat` is mid-campaign —
the open defect is a cumulative volume deficit in Barnegat Bay. See `docs/campaigns/` for
what has been ruled in and out.

Two findings worth knowing before reading any older number: the water-level boundary was
clamped 2.6 km *inside* Barnegat Inlet until 2026-07-30, and the HWM estimator was
measuring its own search window rather than the model. Both invalidated earlier
comparisons; both are documented in `docs/campaigns/`.
