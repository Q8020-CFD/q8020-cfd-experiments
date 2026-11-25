# AIAA27 QCFD paper Figs 5-12 recreated from `latest_pkgs` (qiskit 2.6.2)

Regenerate: `python make_paper_figures.py` (numpy, pandas, scipy, matplotlib). Writes the PNGs and `fig7_l2_error.csv` here.

Data: `../../latest_pkgs/2026-11-11/_ea180c7c` (fvm `ef7f0a8b`, qiskit 2.6.2, HHL lib pinned `99231b8`; nelem 5, CFL 1e10, 15 iterations,
7 shot counts x 10 trials; exact case in `11b8064a`). Classical LU and the nelem=200 "Ref sol" come from
`fvm_euler_1d_solver/post_process/ref_sol/` (not part of this run).

| file | paper fig | what is plotted |
|---|---|---|
| fig05_density / mach_lu_vs_hhl_ideal | 5 | nelem200 LU reference, LU nelem 5, HHL exact statevector nelem 5 (only mesh with HHL data) |
| fig06_density / mach_vs_shots | 6 | final profile, mean over the 10 trials, per shot count |
| fig07_l2_error_vs_shots | 7 | L2 norm of (trial-mean (rho,u,p) minus LU nelem5); relative = / norm(LU) = 4.308 |
| fig08_fidelity_vs_shots | 8 | `hhl_metrics.fidelity`, mean per iteration with 95% t-interval |
| fig09_total_residual | 9 | `residual_total`, trial_1 of each shot count; exact SV; LU |
| fig10_circuit_timing | 10 | `circ_generate/transpile/run_time`, mean +- std per iteration |
| fig11_circuit_complexity | 11 | `circ_depth/gates/qubits_transpile`, one trial per shot count |
| fig12_condition_number | 12 | `condition_number`, one trial per shot count |
| fig04_nozzle_geometry | 4 | analytic S(x) = 1.398 + 0.347 tanh(0.8x - 4), x in [0, 10], plotted vs x/L; large fonts (reviewer comment). No run data. |
| fig11b_circuit_complexity_mean_std | (new) | same quantities as Fig 11 but mean +- population std over the 10 trials, same statistics as Fig 10; exact case drawn as a dashed line (1 run, no band) |
| fig12b_condition_number_mean_std | (new) | same as Fig 12 but mean +- std over the 10 trials, linear y axis. Std bands dip below zero (as in Fig 10's execution-time panel); the quantities are positive |

## How exact is the recipe? (all verified against the 2025-11-11 data the paper used)
Each choice was tested by recomputing the paper's plotted values from `results/fvm_euler_1d_solver/2025-11-11` and comparing.
| fig | choice | evidence |
|---|---|---|
| 6 | mean over 10 trials of (rho, Mach) | 500 shots rho at x=.7/.9: mean .566/.544, paper .565/.545; trial_1 alone gives .556/.523 |
| 7 | L2 of (trial-mean (rho,u,p) - LU nelem5) | abs error matches paper at all 7 shot counts to <1%; conservative variables give 0.196 at 500 shots (paper 0.155), so the paper text "conservative variables" is loose |
| 7 | relative = abs / ||LU (rho,u,p)|| = 4.308 | pixel-measured paper values / computed: .0359/.0361, .0255/.0255, .00226/.00225, .00393/.00395 ... all within ~1%; Mach-only norm (4.187) is 3% off |
| 8 | mean, 95% **Student-t** CI, iteration = `step` | 1000 shots, iter 14: mean .500 (paper ~.50), lower edge t=.311 (paper ~.31); normal gives .337 |
| 9 | **one trial: trial_1** (not a mean) | iter-14 residual of trial_1 vs paper read-off: .73/.7, 2.16/2.0, .55/.5, .029/.03, 6.7e-4/7e-4, 1.9e-3/2e-3; the 10-trial mean (1.17 at 1000 shots) does not match |
| 10 | mean +- **population** std (ddof=0), not min/max | 1000 shots iter 2, gen band top: pop 1109, sample 1143, paper ~1110; transpile 172/172; run 816/820. The paper's caption says "min/max" but the figure is +-std |
| 11, 12 | **trial_1** of each shot count | 500 shots dips at iter 3,4 and 10000 shots spike at iter 2 occur only in trial_1 of the 2025 run; exact case dip at iter 1 |

## Things to know before trusting these numbers
1. **Exactly 10 complete trials per shot count.** 6 of the 70 original shot cases crashed (`LinAlgError`): 5,000 shots trials 2 and 4,
   10,000 shots trials 3 and 5, 50,000 shots trials 0 and 2. The figures drop crashed cases entirely and top up those three shot counts with the first
   2 completed cases of the rerun sweep (`../../latest_pkgs_rerun/2026-11-24/_2ddbef9a`): 5,000 -> trial_0, trial_1; 10,000 -> trial_0, trial_2
   (trial_1 crashed again); 50,000 -> trial_0, trial_1. Further completed reruns (3 at 5,000, 2 at 10,000, 3 at 50,000) are unused.
   Overall: 7 crashes in 85 shot-case attempts. `fig7_l2_error.csv` has n_original / n_rerun / n_crashed_original per shot count.
   The reruns are new random draws (no `-seed`), not reproductions of the crashed cases.
2. **Fig 7 here is not the paper's curve.** Same recipe on 2026 data gives e.g. 50,000 shots 0.0176 (paper 0.0046) and 10,000 shots 0.0030 (paper 0.017):
   different random draws, and with 10 unseeded trials the non-monotonic wiggles are noise. Don't read a 2025-vs-2026 difference into it.
3. **Figs 9, 11, 12 are one trial: trial_1** of each shot count (all 7 trial_1 cases completed in the 2026 run).
4. **Depth/qubit jumps are real, not artifacts.** Over all 977 steps, transpiled qubits track the condition number: 13 qubits for kappa<=63 (depth ~297k),
   14 for kappa 63-123 (~597k), 15 for 131-164 (~1.19M), 16 for 269-476 (~2.39M), 17 for kappa 928 (4.8M). Depth doubles per qubit (QPE clock register
   sized from kappa). That explains the paper's 0.34M dips / 1.38M spike; in this run it's shots=500 (kappa spike at iter 2) and shots=50000 (kappa<63 whole run).
5. Timing differs systematically from the paper's figure by stack: here generate ~50 s, transpile ~280 s, run ~76 s per step vs the paper's ~250 / ~45 / ~60 s.
   That is the qiskit 2.x vs 1.2.4 (and optimization-level) effect already noted, not an error.

## Remaining open items
- Paper text says Fig 7 is the error of the "conservative variables"; the figure is actually (rho,u,p). Text/figure mismatch in the paper.
- Paper text says "2% relative error at 100k shots" (Fig 7 shows ~0.2%).
- Fig 10's caption says "Bands indicate min/max" but the figure is mean +- std.
