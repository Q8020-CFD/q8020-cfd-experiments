# fvm main on the newest packages, Frontier

Runs `fvm_euler_1d_solver` `main` at `ef7f0a8b` on the newest available
packages (resolved 2026-11-10), on the same case as `../nov_pkgs` and
`../new_pkgs`: nelem=5 nozzle, HHL on the ideal statevector simulator, 1 exact
case plus 7 shot counts x 10 trials (71 cases).

| | qiskit 1.2.4 | qiskit 2.5.2 | qiskit 2.6.2 |
|---|---|---|---|
| fvm `main` `ef7f0a8b`, HHL | `../nov_pkgs` | `../new_pkgs` | **this sweep** |

| Piece | Value |
|---|---|
| Solver | `Q8020-CFD/fvm_euler_1d_solver` `main` at `ef7f0a8b` (same as the other two) |
| HHL library | `Q8020-CFD/quantum_linear_solvers@99231b8` (branch `feature/sqls-aiaa-4q26`; `new_pkgs` used `66eadf0`) |
| Python | 3.12 |
| Packages | [requirements.latestpkgs.txt](requirements.latestpkgs.txt), from [requirements.latestpkgs.in](requirements.latestpkgs.in) |
| Sweep | [fvm_main_latestpkgs.toml](fvm_main_latestpkgs.toml) |

Two things differ from `new_pkgs`: the qiskit stack and the HHL library commit.
So this does not isolate the package change on its own. To do that, build the
venv with the `66eadf0` line instead (edit the last line of the `.txt`).

All pins match the newest PyPI release, except `python-dateutil` 3.0.0
(PyPI has 4.0.0; `ibm-cloud-sdk-core` 3.28.2 needs `<3.1.0`).

Not set: transpiler optimization level. The ideal-backend transpile uses
qiskit's default, which is level 2 on qiskit 2.x and was level 1 on 1.2.4.

## Local verification (2026-11-10, WSL laptop)

Installed from the `.txt` with `--no-deps` into a Python 3.12 env and ran
`main` `ef7f0a8b` with `-nelem 2 -iters 3 -shots 0`, other flags as in the TOML:
residual after 2 steps 2.675528e-4 (2.675527e-4 on qiskit 1.2.4, 2.675534e-4 on
2.5.2), Mach [1.5641, 1.6315] as on both, transpiled depth about 69,000 per
step, 44 s. Not run: the nelem=5 case.

## Setup (Frontier login node; compute nodes have no internet)

Run from the workspace root, the directory holding the sibling repos.

```bash
git -C q8020-cfd-experiments pull
git -C q8020-cfd-experiments-aux pull
git -C fvm_euler_1d_solver fetch origin
git -C q8020-cfd-metautil pull

# Worktree pinned to ef7f0a8b, separate from the nov_pkgs and new_pkgs ones
git -C fvm_euler_1d_solver worktree add ../fvm_euler_1d_solver-main-latestpkgs ef7f0a8b

REQ=q8020-cfd-experiments/results/fvm_euler_1d_solver/nov2025-rerun/latest_pkgs/requirements.latestpkgs.txt
uv venv --python 3.12 fvm_euler_1d_solver-main-latestpkgs/.venv
uv pip install --no-config --no-deps --python fvm_euler_1d_solver-main-latestpkgs/.venv -r $REQ
uv pip install --no-config --no-deps --python fvm_euler_1d_solver-main-latestpkgs/.venv ./q8020-cfd-metautil

# Expect 3.12.x 2.5.4 1.18.1 2.6.2 0.18.2
fvm_euler_1d_solver-main-latestpkgs/.venv/bin/python -c "
import sys, numpy, scipy, qiskit, qiskit_aer, linear_solvers
import q8020_cfd_metautil.meta_fragment
print(sys.version.split()[0], numpy.__version__, scipy.__version__, qiskit.__version__, qiskit_aer.__version__)"
```

Add `--system-certs` to the `uv pip install` commands behind a TLS-intercepting
proxy; not needed on Frontier. Metautil is required: the harvester imports
`q8020_cfd_metautil.meta_fragment`.

## Run

```bash
TOML=q8020-cfd-experiments/results/fvm_euler_1d_solver/nov2025-rerun/latest_pkgs/fvm_main_latestpkgs.toml
q8020-sweep $TOML --dry-run      # expect "71 cases in 2 groups", #SBATCH -N 2
q8020-sweep $TOML exact          # validate the stack first
q8020-sweep $TOML shots          # 70 cases on 2 nodes
```

Output goes to Lustre (`/lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/latest_pkgs`);
copy results off without the circuits: `rsync -a --exclude '*.qpy' <run dir>/ <dest>/`.
`_slurm_pack_venvs` must list the venv once. Do not reuse the `nov_pkgs` or
`new_pkgs` worktrees.
