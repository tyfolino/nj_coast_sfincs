"""nj_sfincs — a small toolkit for building, running, validating and visualizing
the NJ Sandy SFINCS model as a set of wave-sensitivity experiments.

Submodules are intentionally independent so cheap imports stay cheap:

    from nj_sfincs.config import EXPERIMENTS      # no heavy deps
    from nj_sfincs import plots, validate         # matplotlib / hydromt

The science (grid, elevation, subgrid, forcing, the SnapWave block, the
validation metrics) is lifted verbatim from notebooks/sfincs-nj-sandy.ipynb so
the numbers are behaviour-preserving; only the wave "knobs" vary between
experiments (see config.WaveConfig / config.EXPERIMENTS).
"""

# Prime PROJ/GEOS before hydromt_sfincs loads. In a bare (non-notebook) process,
# importing hydromt_sfincs.utils first and only later touching PROJ triggers a
# native "double free or corruption" inside utils.downscale_floodmap (a GEOS/PROJ
# load-order conflict). Importing pyproj here — before any submodule pulls in
# hydromt_sfincs — initializes PROJ first and makes the package safe from the CLI.
# The notebook never hit this because it imports the viz stack (which pulls
# pyproj) up top. Keep this import ahead of any hydromt_sfincs import.
import pyproj  # noqa: F401,E402  (PROJ primer — do not remove or reorder)

# Pin PROJ_DATA to the environment's own proj directory, and export it so GDAL
# COMMAND-LINE subprocesses inherit it.
#
# PROJ searches `~/.local/share/proj` before the env's `share/proj`. On this
# account that first path shadows the real one, so PROJ gives up and every CRS
# lookup fails. In-process that goes unnoticed — pyproj carries its own data — so
# the only symptom is a stray "proj_create_from_database: Open of ... failed" on
# stderr while results stay correct. The gdal CLI has no such fallback: it dies
# with "Invalid SRS for -t_srs" and gdalwarp exits non-zero. That silently killed
# a topobathy re-clip whose Python wrapper printed its progress lines happily
# either way, so the failure only showed up in the exit code.
#
# setdefault, so an explicit PROJ_DATA in the environment still wins.
import os as _os  # noqa: E402
from pathlib import Path as _Path  # noqa: E402

_proj_data = _Path(pyproj.datadir.get_data_dir())
if (_proj_data / "proj.db").exists():
    _os.environ.setdefault("PROJ_DATA", str(_proj_data))
    _os.environ.setdefault("PROJ_LIB", str(_proj_data))  # PROJ < 9.1 spelling
del _os, _Path, _proj_data

__all__ = ["config", "domain", "model", "run", "validate", "plots", "report"]
