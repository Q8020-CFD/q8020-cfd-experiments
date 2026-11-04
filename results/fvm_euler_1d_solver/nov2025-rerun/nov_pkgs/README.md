# fvm main on the 2025-11-11 package stack, Frontier

Runs the current `fvm_euler_1d_solver` `main` on the same case and the same
reconstructed packages as the 2025-11-11 baseline
(`q8020-cfd-experiments/results/fvm_euler_1d_solver/2025-11-11`): nelem=5
nozzle, HHL on the ideal statevector simulator, 1 exact case plus 7 shot
counts x 10 trials (71 cases).

| Piece | Value |
|---|---|
| Solver | `Q8020-CFD/fvm_euler_1d_solver` `main` (`ef7f0a8b` at time of writing) |
| HHL library | `jw676/quantum_linear_solvers@a94cf63` |
| Python | 3.10 |
| Packages | [requirements.nov2025.txt](requirements.nov2025.txt) |
| Sweep | [fvm_main_novpkgs.toml](fvm_main_novpkgs.toml) |

`main` keeps the HHL path of the November commit (`a5317f2b`) unchanged; its
additions (SQLS, checkpointing, verbosity) are off by default. On a small case
(nelem=2, 3 iterations, statevector) under these packages, `main` and
`a5317f2b` gave byte-identical residuals, solutions and transpiled circuits,
so on this stack `main` reproduces the November code.

Assumptions carried from the November reconstruction: `-hhl_scale`, `-x` and
`-backend` at their defaults; shot sampling is unseeded, so shot trials can
only match statistically.

## Setup (Frontier login node; compute nodes have no internet)

Run everything from the workspace root, the directory holding the sibling
repos (`fvm_euler_1d_solver`, `q8020-cfd-metautil`,
`q8020-cfd-experiments-aux`, ...).

```bash
# 1. Update the repos
git -C q8020-cfd-experiments-aux pull
git -C fvm_euler_1d_solver fetch origin

# 2. Worktree at main, next to the main checkout
git -C fvm_euler_1d_solver worktree add ../fvm_euler_1d_solver-main origin/main

# 3. Venv: Python 3.10 + the November packages.
#    Do NOT `uv sync` in the worktree: main's uv.lock installs qiskit 2.5.
uv venv --python 3.10 fvm_euler_1d_solver-main/.venv
uv pip install --python fvm_euler_1d_solver-main/.venv \
    -r q8020-cfd-experiments-aux/fvm_euler_1d_nozzle/nov2025-rerun/nov_pkgs/requirements.nov2025.txt

# 4. Check versions (expect 3.10.x 2.2.6 1.15.3 1.2.4 0.15.1)
fvm_euler_1d_solver-main/.venv/bin/python -c "
import sys, numpy, scipy, qiskit, qiskit_aer, linear_solvers
print(sys.version.split()[0], numpy.__version__, scipy.__version__, qiskit.__version__, qiskit_aer.__version__)"
```

The same venv runs the harvester (`_postproc_venv`). `q8020-sweep` itself runs
from your usual sweeper env.

## Run

```bash
TOML=q8020-cfd-experiments-aux/fvm_euler_1d_nozzle/nov2025-rerun/nov_pkgs/fvm_main_novpkgs.toml
OUT=/lustre/orion/ard189/proj-shared/$USER/fvm-main-novpkgs

# Dry run: expect 71 cases in 2 groups, #SBATCH -N 2, only /mnt/bb/.../venv_0
q8020-sweep $TOML --dry-run --set _slurm=true --set _output_dir=$OUT

# Exact case first, to validate the stack (~70 min)
q8020-sweep $TOML exact --set _slurm=true --set _output_dir=$OUT

# Then the shots ladder (70 cases on 2 nodes, up to ~2.6 h each)
q8020-sweep $TOML shots --set _slurm=true --set _output_dir=$OUT
```

Group names are positional (there is no `--groups` flag).

Output goes to Lustre, not home: each case writes ~1.5 GB of `.qpy` circuits
(the HHL class always saves them, whatever `-savedata` says), so the full
sweep is ~100 GB. Lustre is purged, so copy the results off it, without the
circuits:

```bash
rsync -a --exclude '*.qpy' $OUT/ ~/fvm-main-novpkgs-results/
```

## Checking the result

Exact case vs `results/.../2025-11-11/exact_09899a29`:

```bash
D=$(ls -dt $OUT/*/_*/ | head -1)              # this run's directory
cat $D/*/q8020_stderr_*.txt                    # empty, or warnings only
cut -d, -f1,16,17 $D/*/qc_metadata_*.csv | head -3
tail -3 $D/*/residual_*.csv
```

- step 0: `circ_depth_transpile` = 689027, `circ_gates_transpile` = 689127
- converged in 7 iterations, final residual ~8.9e-11
- `system_Ab_*.pkl` per iteration matches the original

Shot cases: per-shot-count error spread across the 10 trials should fall
within the original trials' range.

## Pitfalls hit so far

- `_slurm_pack_venvs` must list each venv once. A duplicate makes cases
  activate a `venv_1` that was never broadcast
  (`/mnt/bb/$USER/venv_1/bin/activate: No such file or directory`).
- Walltime: the shot cases took up to ~2.6 h in November; the TOML asks for 4 h.
