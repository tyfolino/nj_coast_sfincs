<!-- Raw Claude-memory file, archived verbatim 2026-08-05 when the memory store was
     collapsed. Its standing content was merged into the new memory set and/or
     CLAUDE.md; this copy exists so the merge cannot have lost a detail.
     Superseded — do not treat as current. -->


**Node**: Intel Xeon Gold 6338, 2 sockets × 32 cores = 64 cores, 2 NUMA nodes (0: cpus 0-31 / 128 GB, 1: cpus 32-63 / 129 GB). SFINCS is **OpenMP only** (no MPI); threads = `OMP_NUM_THREADS`.

**Measured 2026-07-01 on `notebooks/sfincs-nj-sandy.ipynb` (547k cells, subgrid, SnapWave incident ON, igwaves off):**
- 48 threads across both sockets (no pinning): ETA ~885 s @ 5% (~15 min).
- 16 threads pinned to one socket (`numactl --cpunodebind=0 --membind=0`): ETA ~1442 s @ 5% (~24 min) → **~1.6× SLOWER**.

**Lesson (non-obvious):** the usual "SFINCS is memory-bandwidth-bound, plateaus at 8-16 threads, don't cross NUMA" rule is for the **bare hydro core**. **With SnapWave on**, the iterative directional-wave solver (~404k wave cells) is **compute-heavy and DOES scale with core count** — so more cores win even across sockets. Don't pin to one socket when waves are on.

**Config now in the notebook** (imports cell + `run_sfincs`): default `OMP_NUM_THREADS = len(os.sched_getaffinity(0))` — the cores ALLOCATED to the process (respects a SLURM/cgroup cap), NOT `os.cpu_count()` (physical total, ignores the cap → grabbed all 64 on a 48-core request 2026-07-01). On this node no cpuset is set so affinity = full 64; cap explicitly with `os.environ["OMP_NUM_THREADS"]="48"`. `run_sfincs` sets both `SINGULARITYENV_*` and `APPTAINERENV_*` OMP vars, `run_sfincs` wraps the singularity call with `numactl --interleave=all` (spread memory pages across both controllers so neither socket's threads starve on remote bandwidth) + `OMP_PROC_BIND=spread`, `OMP_PLACES=cores`. Env-overridable. **Waves OFF → drop to ~16.** TODO: proper 32/48/64 sweep to find the actual peak (48 was just the first number tried). See project_hydromt14_quadtree_session (memory retired 2026-07-25).
