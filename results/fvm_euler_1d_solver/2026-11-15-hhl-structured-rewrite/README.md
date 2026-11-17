# Structured rewrite of the pre-LuGo fvm HHL step-0 circuit, nelem 5

Run outputs of
`aux/fvm_euler_1d_nozzle/hhl-structured-rewrite-2026-11/run_test.py`; the
method is in that folder's `README.md`. Simulation (Aer) and transpilation
only, nothing on quantum hardware.

| piece | value |
|---|---|
| node | macos-laptop (`MH-DT9TLJQR2V`) |
| run | 2026-11-15T19:59:53Z to 2026-11-15T20:03:41Z, 228 s |
| code | aux `28850e14` plus the uncommitted folder `hhl-structured-rewrite-2026-11/` (its `structured_rewrite.py`, `run_test.py`); imports `lugo-qpy-rewrite-2026-11/qpy_rewrite.py` and `run_step0.py` at the same aux commit |
| experiments repo | `f3ee7755` (dirty: the untracked aux folder) |
| venv | fvm repo `.venv`: Python 3.12.10, qiskit 2.6.0, qiskit-aer 0.17.2, qiskit-ibm-runtime 0.50.0 |
| input | `nov2025-rerun/nov_pkgs/2026-11-03/_9f0fbf67/719a35aa/circuit_generated_statevector_nelem5_iter0.qpy`, sha256 `4573dd1f...a68402ac2` (fvm `main` `ef7f0a8b`, 2025-11 stack, Frontier) |
| LuGo comparison | `2026-02-26-LuGo/circuits/circuit_generated_nelem5_iter0.qpy`, sha256 `2c8b064d...9808bd56` |
| command | `run_test.py --out ~/q8020/hhl-structured-rewrite` (defaults: 10 seeds x 150000 shots, AQC CX 62,64,68,72, tol 1e-11) |

No qpy is kept: `structured_rewrite.py <in.qpy> -o <out.qpy>` regenerates
the exact circuit in about 75 s, most of it computing the stored blocks'
unitaries for the check.

## Files

| file | what it is |
|---|---|
| `nelem5/counts.csv` | two-qubit gates, two-qubit depth and total depth per circuit and target |
| `nelem5/statevector.csv` | 1 - F against the stored circuit, used probability, HHL metrics; the recorded run's metrics |
| `nelem5/shots.csv` | per seed: HHL metrics from 150000 shots, sha1 of the used counts, whether they equal the stored circuit's |
| `nelem5/summary.json` | versions, hashes, rewrite reports, AQC pieces, pre-LuGo CX estimate |
| `nelem5/log.txt` | the run log |

## Results

Gate counts, level 2, `seed_transpiler` 1. Heron is `FakeMarrakesh`;
`FakeNighthawk` warns that its error values are not typical, which can move
its noise-aware layout.

| circuit | target | 2q gates | 2q depth | total depth |
|---|---|---|---|---|
| LuGo (feb26) | all-to-all | 57280 | 57179 | 143699 |
| rewrite, exact | all-to-all | 7347 | 6867 | 25166 |
| rewrite, AQC | all-to-all | 5296 | 3689 | 16695 |
| LuGo (feb26) | Heron | 78993 | 73567 | 287084 |
| rewrite, exact | Heron | 12257 | 10929 | 43754 |
| rewrite, AQC | Heron | 6837 | 4208 | 18753 |
| LuGo (feb26) | Nighthawk | 81818 | 73670 | 271971 |
| rewrite, exact | Nighthawk | 12614 | 10975 | 41884 |
| rewrite, AQC | Nighthawk | 6421 | 4285 | 19043 |

The pre-LuGo circuit itself is about 1754672 CX all-to-all (estimate: one
controlled-U copy, 3436 CX, times 510 copies, plus 2312 CX for the rest).

Equivalence, against the stored circuit with its blocks as exact unitaries:

| variant | per-block max entry error | 1 - F, full state | step-0 fidelity | relative L2 error |
|---|---|---|---|---|
| stored | | 0 | 0.99995714 | 0.0068167 |
| recorded run | | | 0.99995714 | 0.0068167 |
| exact | 4.6e-12 | 1.2e-12 | 0.99995714 | 0.0068167 |
| AQC | 1.5e-6 | 2.5e-12 | 0.99995714 | 0.0068144 |

AQC pieces: both 4-qubit unitaries of L at 62 CX each, 1 - F 1.0e-12 and
1.6e-12 (exact synthesis: 95 CX each). Per block: 444 CX exact, 312 AQC.

Shots, 10 seeds x 150000: the exact rewrite's used counts (ancilla 1,
clock 0) equal the stored circuit's for all 10 seeds; the AQC rewrite's for
7 of 10. Fidelity min / median / max: stored and exact 0.99718 / 0.99835 /
0.99897; AQC 0.99718 / 0.99830 / 0.99897. About 2140 of 150000 shots are
used.
