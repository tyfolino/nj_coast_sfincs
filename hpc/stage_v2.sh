#!/bin/bash
# Stage the v2_barnegat control + perturbation (build the template once, then both
# arms) WITHOUT running the solver. Submit the solves separately so each can get its
# own wall clock — the shared batch script's 3 h default is nowhere near enough for a
# 1.14M-face domain.
#
#   bash hpc/stage_v2.sh                # -> logs/stage_v2.log
#
# Exists as a file rather than an inline command because the env-var + nohup +
# redirect combination is easy to get subtly wrong from an interactive shell, and a
# staging run that half-writes the template then dies leaves a partial sfincs.nc that
# the NEXT invocation will try to fingerprint.
set -euo pipefail

cd "$(dirname "$0")/.."
PROJ="$PWD"
ENV="$PROJ/micromamba/envs/sfincs"

export NJ_ROOT="$PROJ"
export NJ_DOMAIN="${NJ_DOMAIN:-v2_barnegat}"
export PYTHONPATH="$PROJ"
export PROJ_LIB="$ENV/share/proj" PROJ_DATA="$ENV/share/proj" GDAL_DATA="$ENV/share/gdal"
export OMP_NUM_THREADS="${OMP_NUM_THREADS:-32}"
export HDF5_USE_FILE_LOCKING=FALSE

mkdir -p logs experiments

ARMS="${ARMS:-faber-waves-premier,wave-cora}"
echo "host=$(hostname)  domain=$NJ_DOMAIN  arms=$ARMS  threads=$OMP_NUM_THREADS"
echo "started $(date -u +%Y-%m-%dT%H:%M:%SZ)"

exec "$ENV/bin/python" -u run_experiments.py --experiments "$ARMS" --no-run
