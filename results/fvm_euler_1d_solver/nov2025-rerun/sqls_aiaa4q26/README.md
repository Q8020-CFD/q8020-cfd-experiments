# SQLS on the nov2025 nozzle case, Frontier

Runs the SQLS linear solver (ORNL, via the Q8020-CFD fork) on the case used
by the HHL runs (2025-11-11 baseline and the `../nov_pkgs` rerun) and by the
HHL+LuGo runs (`../LuGo-rerun`): nelem=5 nozzle on the ideal statevector
simulator, 1 exact case plus 7 shot counts x 10 seeds (71 cases).

| Piece | Value |
|---|---|
| Solver | `Q8020-CFD/fvm_euler_1d_solver` branch `feature/sqls-aiaa-4q26` at `d4a531bd` |
| SQLS | `Q8020-CFD/sqls@67057e4` (ORNL main + shots/seed patch) |
| HHL library | `Q8020-CFD/quantum_linear_solvers@99231b8` (installed, not used by SQLS) |
| Python | 3.12 |
| Packages | [requirements.sqls-aiaa-4q26.txt](requirements.sqls-aiaa-4q26.txt), exported from the branch's `uv.lock` |
| Sweep | [fvm_sqls_aiaa4q26.toml](fvm_sqls_aiaa4q26.toml) |

SQLS settings: `-sqls_method full_svd`, `-sqls_state_prep initialize`,
`-sqls_repeats 1` (effective shots = shots, as for one HHL run),
`-pad_eps 0` (the HHL runs used the 1e-8 default). Shot trials are seeds
1..10, so they are reproducible; the HHL trials were unseeded.

What `full_svd` does: the pseudo-inverse comes from a classical dense SVD,
the solution direction is loaded with `Initialize` into 4 data qubits
(15 -> 16 padded, no Hermitian doubling) and sampled; the magnitude, and in
shots mode the component signs, are restored classically from b. Keep this
in mind when comparing it against HHL.

## Setup (Frontier login node; compute nodes have no internet)

Run everything from the workspace root, the directory holding the sibling
repos (`fvm_euler_1d_solver`, `q8020-cfd-metautil`,
`q8020-cfd-experiments-aux`, ...). You need read access to
`github.com/Q8020-CFD/sqls` (Q8020-CFD org members).

```bash
# 1. Update the repos
git -C q8020-cfd-experiments-aux pull
git -C fvm_euler_1d_solver fetch origin

# 2. Worktree pinned to the commit the requirements were exported from
git -C fvm_euler_1d_solver worktree add ../fvm_euler_1d_solver-sqls d4a531bd

# 3. Venv: Python 3.12 + the locked packages, then metautil for the harvester
REQ=q8020-cfd-experiments-aux/fvm_euler_1d_nozzle/nov2025-rerun/sqls_aiaa4q26/requirements.sqls-aiaa-4q26.txt
uv venv --python 3.12 fvm_euler_1d_solver-sqls/.venv
uv pip install --no-config --no-deps --python fvm_euler_1d_solver-sqls/.venv -r $REQ
uv pip install --no-config --no-deps --python fvm_euler_1d_solver-sqls/.venv ./q8020-cfd-metautil

# 4. Check versions (expect 3.12.x 2.5.2 1.18.0 2.6.0 0.17.2)
fvm_euler_1d_solver-sqls/.venv/bin/python -c "
import sys, numpy, scipy, qiskit, qiskit_aer, linear_solvers, sqls
import q8020_cfd_metautil.meta_fragment
print(sys.version.split()[0], numpy.__version__, scipy.__version__, qiskit.__version__, qiskit_aer.__version__)"
```

Both flags matter:

- `--no-deps`: the requirements file is the full locked closure. Resolving
  dependencies would hit sqls's own hard pins (old qiskit/numpy/scipy).
- `--no-config`: if a `pyproject.toml` with `[tool.uv]` is in the current
  directory (the branch's is), uv applies its `override-dependencies`, which
  replace the exact pins with ranges and silently install newer numpy,
  scipy and qiskit. Step 4 catches this.

`uv sync` inside the worktree also works and gives the same packages, but it
installs the dev group too and needs the network at sync time. The file plus
`--no-deps` keeps the stack identical to this README.

The same venv runs the harvester (`_postproc_venv`). `q8020-sweep` itself
runs from your usual sweeper env.

## Run

```bash
TOML=q8020-cfd-experiments-aux/fvm_euler_1d_nozzle/nov2025-rerun/sqls_aiaa4q26/fvm_sqls_aiaa4q26.toml
OUT=/lustre/orion/ard189/proj-shared/$USER/fvm-sqls-aiaa4q26

# Dry run: expect 71 cases in 2 groups, #SBATCH -N 2, only /mnt/bb/.../venv_0
q8020-sweep $TOML --dry-run --set _slurm=true --set _output_dir=$OUT

# Exact case first (seconds), then the shots ladder
q8020-sweep $TOML exact --set _slurm=true --set _output_dir=$OUT
q8020-sweep $TOML shots --set _slurm=true --set _output_dir=$OUT
```

Each case is capped at 10 min by `timeout` and took seconds in testing; the
TOML asks for 1 h on `batch`. SQLS writes no `.qpy` files, so output is
small. Writing to Lustre still keeps it off the home quota. Copy it off
Lustre before the purge.

Case directories are flat (`<case_id>/`), not `shots_N/trial_k/`. Shots
and seed are in each case's `q8020_params_<id>.json` and in the file names.

## Checking the result

```bash
D=$(ls -dt $OUT/*/_*/ | head -1)
cat $D/slurm_*.err | grep -v "can't run 1 processes"   # no tracebacks
ls $D/*/q8020_metadata_*.json | wc -l                  # 71: harvester ran
tail -2 $D/*/residual_nelem5_SQLS_statevector.csv     # exact case
```

Reference from a local test of this exact stack (2026-11-04, WSL, same
flags):

- exact: converged in 5 iterations, final residual 1.85e-13 (HHL: 7
  iterations, 8.9e-11)
- 1000 shots, seed 1: converged in 10 iterations, final residual 1.8e-9
- both under 5 s; the sweeper + harvester produced `q8020_metadata_<id>.json`
