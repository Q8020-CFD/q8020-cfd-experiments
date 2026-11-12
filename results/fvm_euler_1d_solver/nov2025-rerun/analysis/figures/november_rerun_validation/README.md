# November rerun validation: 2025 original vs 2026 rerun (qiskit 1.2.4 stack)

Is the 2026 rerun (`../../../nov_pkgs`, the 11-04 and 11-05 sweeps pooled) comparable with the original
`results/fvm_euler_1d_solver/2025-11-11`? Built by `../../make_validation_plots.py`. Both use nelem 5, HHL,
ideal statevector simulator, 1 exact case + 7 shot counts. 2025: 1 exact + 10 trials per shot count. 2026: 3 exact + 17 to 20 trials per shot count.

| check | result |
|---|---|
| exact case: Newton steps | 8 in 2025 and in all 3 runs of 2026 |
| exact case: residual history | identical (max relative difference 0.0), final 8.910e-11 |
| exact case: final Mach profile | identical (max abs difference 0.0) |
| exact case: transpiled depth per step | identical at every step (689,026 at step 0) |
| shot cases: steps used | all 15 in both years (none converge) |
| shot cases: error and residual vs shots | 2025 medians fall inside the 2026 min-max range at every shot count; medians within about 2x of each other except at 100,000 shots (2025 median is higher; 10 trials) |
| per-step times, shot cases pooled | generate 266 vs 268 s, transpile 45 vs 44 s, run 64 vs 63 s (2025 vs 2026) |

| figure | shows |
|---|---|
| `01_exact_case.png` | residual history, final Mach profile and per-step depth, 2025 vs the 2026 exact runs |
| `02_accuracy_vs_shots.png` | final Mach error (vs the 2025 exact solution) and residual vs shots |
| `03_timing_per_step.png` | generate, transpile and run time per step, all shot counts pooled |

Not compared: wall time (the 2025 results have no recorded `duration_seconds`) and crash rates (2025 shows no crashed cases among
its results, but a failed case may simply not have been kept). Shot trials are unseeded in both years, so they can only agree statistically.
