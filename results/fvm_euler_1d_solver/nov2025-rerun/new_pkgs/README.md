# fvm main on its current package stack, Frontier

Runs `fvm_euler_1d_solver` `main` on its **own** locked packages (qiskit 2.5.2)
on the same case as the 2025-11-11 baseline and the `../nov_pkgs` rerun:
nelem=5 nozzle, HHL on the ideal statevector simulator, 1 exact case plus 7
shot counts x 10 trials (71 cases).

This fills the remaining cell of the comparison:

| | Nov-2025 packages (qiskit 1.2.4) | Current packages (qiskit 2.5.2) |
|---|---|---|
| fvm `main` `ef7f0a8b`, HHL | `../nov_pkgs` | **this sweep** |

The code commit and every solver flag match `../nov_pkgs`, so `nov_pkgs` vs
this sweep isolates the effect of the package upgrade.

| Piece | Value |
|---|---|
| Solver | `Q8020-CFD/fvm_euler_1d_solver` `main` at `ef7f0a8b` (same commit as `../nov_pkgs`) |
| HHL library | `Q8020-CFD/quantum_linear_solvers@66eadf0` |
| Python | 3.12 |
| Packages | [requirements.newpkgs.txt](requirements.newpkgs.txt), exported from `ef7f0a8b`'s `uv.lock` |
| Sweep | [fvm_main_newpkgs.toml](fvm_main_newpkgs.toml) |

As in `../nov_pkgs`: `-hhl_scale`, `-x` and `-backend` are at their defaults,
and shot sampling is unseeded (HHL on `main` has no `-seed`), so shot trials
can only match statistically.

## Setup (Frontier login node; compute nodes have no internet)

Run everything from the workspace root, the directory holding the sibling
repos (`fvm_euler_1d_solver`, `q8020-cfd-metautil`,
`q8020-cfd-experiments-aux`, ...). Copy this directory to
`q8020-cfd-experiments-aux/fvm_euler_1d_nozzle/nov2025-rerun/new_pkgs/` first,
next to `nov_pkgs/`.

```bash
# 1. Update the repos
git -C q8020-cfd-experiments-aux pull
git -C fvm_euler_1d_solver fetch origin
git -C q8020-cfd-metautil pull

# 2. New worktree pinned to ef7f0a8b. Use a separate directory: the existing
#    ./fvm_euler_1d_solver-main holds the nov_pkgs venv (qiskit 1.2.4).
git -C fvm_euler_1d_solver worktree add ../fvm_euler_1d_solver-main-newpkgs ef7f0a8b

# 3. Venv: Python 3.12 + the locked packages, then metautil for the harvester
REQ=q8020-cfd-experiments-aux/fvm_euler_1d_nozzle/nov2025-rerun/new_pkgs/requirements.newpkgs.txt
uv venv --python 3.12 fvm_euler_1d_solver-main-newpkgs/.venv
uv pip install --no-config --no-deps --python fvm_euler_1d_solver-main-newpkgs/.venv -r $REQ
uv pip install --no-config --no-deps --python fvm_euler_1d_solver-main-newpkgs/.venv ./q8020-cfd-metautil

# 4. Check versions (expect 3.12.x 2.5.2 1.18.0 2.5.2 0.17.2)
fvm_euler_1d_solver-main-newpkgs/.venv/bin/python -c "
import sys, numpy, scipy, qiskit, qiskit_aer, linear_solvers
import q8020_cfd_metautil.meta_fragment
print(sys.version.split()[0], numpy.__version__, scipy.__version__, qiskit.__version__, qiskit_aer.__version__)"
```

Notes on step 3:

- `--no-deps`: the requirements file is the full locked closure, so nothing
  is resolved and the stack is exactly `main`'s lock.
- `--no-config`: stops uv from reading a `pyproject.toml`/`uv.toml` in the
  current directory and changing what gets installed.
- metautil is required: the harvester (`_case_postproc`) imports
  `q8020_cfd_metautil.meta_fragment`. Without it every case finishes but
  postproc fails with code 1.
- `uv sync` inside the worktree gives the same solver packages, but not
  metautil, and it needs the network at sync time. The file plus `--no-deps`
  keeps the stack identical to this README.
- Behind a TLS-intercepting proxy (e.g. Zscaler on a laptop), add
  `--system-certs` to the `uv pip install` commands. Not needed on Frontier.

The same venv runs the harvester (`_postproc_venv`). `q8020-sweep` itself runs
from your usual sweeper env.

## Run

```bash
TOML=q8020-cfd-experiments-aux/fvm_euler_1d_nozzle/nov2025-rerun/new_pkgs/fvm_main_newpkgs.toml

# Dry run: expect "71 cases in 2 groups", #SBATCH -N 2, only /mnt/bb/.../venv_0
q8020-sweep $TOML --dry-run

# Exact case first, to validate the stack
q8020-sweep $TOML exact

# Then the shots ladder (70 cases on 2 nodes)
q8020-sweep $TOML shots
```

The TOML already sets `_slurm = true` and writes to
`/lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/new_pkgs`. Override
with `--set _output_dir=...` if needed, but keep it on Lustre: each case writes
~1.5 GB of `.qpy` circuits, and the 2026-11-03 nov_pkgs attempt that wrote to
`/ccs/home` died with `Disk quota exceeded`. Group names are positional (there
is no `--groups` flag).

Lustre is purged, so copy the results off it, without the circuits:

```bash
rsync -a --exclude '*.qpy' <run dir>/ <destination>/
```

## Checking the result

```bash
D=$(ls -dt /lustre/orion/ard189/proj-shared/ishangore/nov2025-rerun/new_pkgs/*/_*/ | head -1)
cat $D/*/q8020_stderr_*.txt                    # empty, or warnings only
ls $D/*/q8020_metadata_*.json | wc -l          # 1 for exact: harvester ran
cut -d, -f1,16,17 $D/*/qc_metadata_*.csv | head -3
tail -3 $D/*/residual_*.csv
```

Exact case, compared with `../nov_pkgs` (`773dd36f`):

- Same as nov_pkgs: converged in 7 iterations, final residual ~8.9e-11,
  `res/res0` ~7.2e-12, `Mach [1.5204, 2.1516]`.
- Expected to differ: `circ_depth_transpile` will NOT be 689027. qiskit 2.x
  compiles the same HHL circuit differently (a 2026-08 qiskit 2.3 check of
  this case gave 638237). Transpile and run times should be shorter.

Shot cases: per-shot-count error spread across the 10 trials should fall
within the `../nov_pkgs` and 2025-11-11 ranges.

## Local verification (2026-11-05, WSL laptop)

Before this sweep was written, the stack was installed from
`requirements.newpkgs.txt` exactly as above (Python 3.12.14, `--no-deps`)
and `main` `ef7f0a8b` was run on a small case on both stacks:
`-nelem 2 -iters 3 -shots 0`, other flags as in the TOML.

| | Nov-2025 stack (qiskit 1.2.4) | This stack (qiskit 2.5.2) |
|---|---|---|
| Residual after 2 steps | 2.675527e-4 | 2.675534e-4 |
| Solution | Mach [1.5641, 1.6315] | Mach [1.5641, 1.6315] |
| Transpiled depth per step | 79010 | ~69000 |
| Solver time | 99.8 s | 36.9 s |

Same answer to ~1e-11 relative residual on step 1 and ~3e-6 on step 2 (the
statevector HHL solution is exact up to compiler round-off), a shallower
circuit and a faster run. No import or API errors. The dry run of the TOML
expanded to 71 cases in 2 groups on 2 nodes.

## Pitfalls carried over from nov_pkgs

- `_slurm_pack_venvs` must list each venv once. A duplicate makes cases
  activate a `venv_1` that was never broadcast.
- Do not reuse `./fvm_euler_1d_solver-main`: its `.venv` is the Nov-2025
  stack, and overwriting it would break reruns of `../nov_pkgs`.
