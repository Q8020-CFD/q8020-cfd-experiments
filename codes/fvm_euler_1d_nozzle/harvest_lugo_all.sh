#!/bin/bash
# Harvest all LuGo trial directories that don't yet have q8020 fragments.
#
# Reads raw solver output from the LuGo results tree on the remote machine
# and writes q8020 fragment JSONs into the q8020-cfd-experiments results tree.
#
# Walks nelem{5,10,20} x {exact,shots_*} x trial_{0..9}.
# Skips any trial whose destination already has q8020_results_*.json.
#
# Usage (on the remote machine, with q8020 venv active):
#   bash harvest_lugo_all.sh
#
# Requirements:
#   - q8020 venv active (has q8020_cfd_metautil installed)
#   - PYTHONPATH includes the codes dir so the harvester module resolves

set -euo pipefail

# ── paths on the remote machine ──────────────────────────────
SRC_ROOT="/ccs/home/agallojr/ard189-lustre/proj-shared/LuGo_rst/output_parallel_shots"
DST_ROOT="/ccs/home/agallojr/proj/src/q8020/q8020-cfd-experiments/results/fvm_euler_1d_solver/2026-02-26-LuGo"
HARVESTER_DIR="/ccs/home/agallojr/proj/src/q8020/q8020-cfd-experiments/codes/fvm_euler_1d_nozzle"
HARVESTER="${HARVESTER_DIR}/fvm_euler_1d_solver_harvester.py"

if [ ! -f "$HARVESTER" ]; then
    echo "ERROR: Harvester not found at $HARVESTER" >&2
    exit 1
fi

export PYTHONPATH="${HARVESTER_DIR}:${PYTHONPATH:-}"

NELEMS=(5 10 20)
SHOTS=(exact shots_1000 shots_5000 shots_10000 shots_50000 shots_100000 shots_150000)
NTRIALS=10

total=0
harvested=0
skipped=0
failed=0

for n in "${NELEMS[@]}"; do
    for s in "${SHOTS[@]}"; do
        src_shots="${SRC_ROOT}/nelem${n}/statevector/${s}"
        dst_shots="${DST_ROOT}/nelem${n}/statevector/${s}"

        if [ ! -d "$src_shots" ]; then
            echo "SKIP (missing src): nelem${n}/${s}"
            continue
        fi

        for t in $(seq 0 $((NTRIALS - 1))); do
            src_trial="${src_shots}/trial_${t}"
            dst_trial="${dst_shots}/trial_${t}"
            total=$((total + 1))

            if [ ! -d "$src_trial" ]; then
                echo "  SKIP (no src dir): nelem${n}/${s}/trial_${t}"
                skipped=$((skipped + 1))
                continue
            fi

            # Skip if already harvested at destination
            if ls "${dst_trial}"/q8020_results_*.json >/dev/null 2>&1; then
                skipped=$((skipped + 1))
                continue
            fi

            mkdir -p "$dst_trial"

            # Copy raw solver output (csv, pkl, log, png) — skip qpy files
            n_copied=0
            for f in "${src_trial}"/*; do
                [ -f "$f" ] || continue
                case "$f" in *.qpy) continue ;; esac
                base="$(basename "$f")"
                if [ ! -f "${dst_trial}/${base}" ]; then
                    cp "$f" "$dst_trial/"
                    n_copied=$((n_copied + 1))
                fi
            done
            echo "    copied ${n_copied} files from src"

            echo "  Harvesting: nelem${n}/${s}/trial_${t}"
            # generate_metadata reads from dst (which now has the raw files), writes fragments there
            if python -c "
import sys; sys.path.insert(0, '${HARVESTER_DIR}')
from fvm_euler_1d_solver_harvester import generate_metadata
from pathlib import Path
generate_metadata(Path('${dst_trial}'), write_dir=Path('${dst_trial}'))
" 2>&1; then
                harvested=$((harvested + 1))
            else
                echo "    FAILED: nelem${n}/${s}/trial_${t}" >&2
                failed=$((failed + 1))
            fi
        done
    done
done

echo ""
echo "=== Harvest complete ==="
echo "Total trial dirs:  ${total}"
echo "Newly harvested:   ${harvested}"
echo "Skipped (exists):  ${skipped}"
echo "Failed:            ${failed}"
