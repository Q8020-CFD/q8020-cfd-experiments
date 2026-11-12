# HHL across qiskit versions (nelem 5)

Same solver commit (`fvm_euler_1d_solver` `ef7f0a8b`), same case, three package stacks. Built by
`../../make_qiskit_version_plots.py` from `../../cases.csv`.

| | qiskit 1.2.4 | qiskit 2.5.2 | qiskit 2.6.2 |
|---|---|---|---|
| results folder | `nov_pkgs` (11-04 and 11-05 pooled) | `new_pkgs` | `latest_pkgs` |
| qiskit-aer | 0.15.1 | 0.17.2 | 0.18.2 |
| numpy / scipy | 2.2.6 / 1.15.3 | 2.5.2 / 1.18.0 | 2.5.4 / 1.18.1 |
| Python | 3.10 | 3.12 | 3.12 |
| HHL library | `jw676/quantum_linear_solvers@a94cf63` | `Q8020-CFD/...@66eadf0` | `Q8020-CFD/...@99231b8` |
| default transpile opt. level | 1 | 2 | 2 |

**These are stack comparisons, not isolated qiskit comparisons.** Python, aer, numpy/scipy and the HHL
library commit change together with qiskit, and the optimization level changes because qiskit's default did.
The solver never sets the level for the ideal-backend transpile. The HHL library change between `a94cf63`
and `66eadf0` is an API port; `66eadf0` to `99231b8` swaps some circuit-library blocks, which gave the same
depth in a random-matrix test (not the nozzle matrices).

| figure | shows |
|---|---|
| `01_depth_step0.png` | transpiled depth at Newton step 0 (identical for the exact case and every shot count) |
| `02_exact_case_per_step.png` | exact case per step: depth, generate, transpile, run time |
| `03_exact_time_breakdown.png` | exact case total time split into generate / transpile / run |
| `04_shot_cases_time.png` | per-case generate, transpile, run time per step and wall time, all shot counts pooled |
| `05_accuracy_vs_shots.png` | final error and residual vs shots (median, min-max band) |
| `06_reliability.png` | share of shot cases that crashed (`LinAlgError`) |

Not shown: SQLS and LuGo (neither is an HHL-on-qiskit-version comparison; LuGo ran on qiskit 2.6.1).
