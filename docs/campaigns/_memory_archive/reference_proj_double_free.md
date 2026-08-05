<!-- Raw Claude-memory file, archived verbatim 2026-08-05 when the memory store was
     collapsed. Its standing content was merged into the new memory set and/or
     CLAUDE.md; this copy exists so the merge cannot have lost a detail.
     Superseded — do not treat as current. -->


In a **bare (non-notebook) Python process**, importing `hydromt_sfincs` (and
calling `utils.downscale_floodmap`) BEFORE any PROJ-using lib triggers a native
`double free or corruption (!prev)` glibc abort inside the downscale block loop.
It is a PROJ/GEOS **load-order** conflict, not a bug in our code and not numba
(reproduces with `NUMBA_DISABLE_JIT=1`).

**Fix:** import `pyproj` (or any of matplotlib / cartopy / geopandas-that-inits-
PROJ) BEFORE `hydromt_sfincs`. Implemented as a one-line PROJ primer at the top
of `nj_sfincs/__init__.py` (`import pyproj`), and `run_experiments.py` imports
`nj_sfincs` before `hydromt_sfincs`. The notebook never hit this because its
cell-4 imports (cartopy/hvplot/matplotlib) load the viz stack first.

Env: micromamba `sfincs` (py3.14, hydromt_sfincs 2.0.0rc2). If you write a new
standalone script that touches downscale_floodmap, put a PROJ-using import first.
See project_experiment_harness (memory retired 2026-07-25).

---

# TRAP 2 — `~/.local/share/proj` SHADOWS the env's PROJ data (found 2026-07-26)

PROJ searches **`/home/tpj8/.local/share/proj` BEFORE** the environment's
`share/proj`. On this account that first path wins and PROJ then fails to open
the real database. `projinfo --searchpaths` shows the order.

**The dangerous part is the asymmetry:**
- **Python is FINE** — pyproj carries its own data dir. The only symptom is a
  stray line on stderr: `ERROR 1: PROJ: proj_create_from_database: Open of
  …/share/proj failed`. Results are correct, so it reads as harmless noise.
- **The GDAL CLI is NOT** — it has no fallback. `gdalwarp` dies with
  `ERROR 1: Invalid SRS for -t_srs`, prints a usage block and exits non-zero.

That killed a topobathy re-clip whose Python wrapper printed its progress lines
happily either way; because the wrapper's prints were buffered they landed
*after* the error in the redirected log, so the log read as success. **The exit
code was the only truthful signal.**

**FIX (shipped in `nj_coast_sfincs/nj_sfincs/__init__.py`):** after the pyproj
primer, `os.environ.setdefault("PROJ_DATA", pyproj.datadir.get_data_dir())`
(+ `PROJ_LIB` for PROJ < 9.1). `setdefault`, so an explicit value still wins.
Subprocesses inherit it, so the GDAL CLI works. Verified: `gdalsrsinfo EPSG:4326`
returns rc=0.

**Two habits worth keeping:** (a) shell out to GDAL through
`nj_sfincs/gdaltools.py::run_gdal`, which resolves the binary next to
`sys.executable` (bare `subprocess.run(["gdalwarp", …])` fails with
`FileNotFoundError` when the script is launched by absolute interpreter path,
the normal way here) and **raises on non-zero exit**; (b) `print(..., flush=True)`
in any script whose output is redirected to a log alongside a subprocess.
