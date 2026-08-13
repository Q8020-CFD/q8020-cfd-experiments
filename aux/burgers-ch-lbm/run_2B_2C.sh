#!/usr/bin/env bash
# =====================================================================
# Run the C6 chi ladder, then the C7 cfl ladder, back to back.
# q8020-sweep blocks until every parallel case in a sweep finishes, so
# plain sequencing gives true one-after-the-other execution.
#
# Expected wall time: C6 ~15h (bounded by chi_16) + C7 ~3.7h (bounded
# by cfl_0p1) ~= 19h total.  Run it disconnect-safe on EC2:
#
#   nohup ./q8020-cfd-experiments/aux/burgers-ch-lbm/run_c6_c7.sh \
#       > ~/q8020-runs/c6_c7.log 2>&1 &
#
# (or inside tmux/screen).  Tail progress: tail -f ~/q8020-runs/c6_c7.log
#
# If C6 fails, C7 still runs; the script exits nonzero if either did.
# To trim C6 to a same-day answer, edit its line to add:
#   --groups chi_2 chi_4 chi_8
# =====================================================================
set -u

# The sweeper's own venv (EC2: ~/.q8020).  The _env in the TOMLs only
# covers the SOLVER subprocess; q8020-sweep itself must be on PATH.
# If it already is (activated shell, conda, etc.) this is a no-op, so
# the script also works on machines where the sweeper lives elsewhere.
SWEEP_ENV="${SWEEP_ENV:-$HOME/.q8020}"
if ! command -v q8020-sweep >/dev/null 2>&1; then
    if [ -f "${SWEEP_ENV}/bin/activate" ]; then
        # shellcheck disable=SC1091
        source "${SWEEP_ENV}/bin/activate"
    fi
fi
if ! command -v q8020-sweep >/dev/null 2>&1; then
    echo "ERROR: q8020-sweep not on PATH and no venv at ${SWEEP_ENV}" >&2
    echo "       (set SWEEP_ENV=/path/to/venv or activate it first)" >&2
    exit 127
fi

# TOML paths are cwd-relative -> always run from the workspace root,
# regardless of where this script is invoked from.
cd "$(dirname "$0")/../../.." || exit 1

CASES=q8020-cfd-experiments/aux/burgers-ch-lbm/cases
rc=0

for toml in c2B_chi_ladder c2C_cfl_ladder; do
    echo "=== $(date -Is) starting ${toml} (cwd: $(pwd)) ==="
    q8020-sweep "${CASES}/${toml}.toml"
    st=$?
    echo "=== $(date -Is) ${toml} exited with status ${st} ==="
    if [ "${st}" -ne 0 ]; then
        rc=${st}
    fi
done

exit "${rc}"
