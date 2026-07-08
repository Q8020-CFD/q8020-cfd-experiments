
## CFL Number Sweep: 
# Effect on HHL Quantum Solver Accuracy

### Motivation

The CFL number controls the time step size in an implicit CFD solver. Larger CFL
values take bigger steps toward steady state, which is attractive for convergence
speed but changes the character of the linear system solved at each Newton
iteration. This study measures how the CFL number affects the accuracy of the HHL
quantum linear solver when used inside a nonlinear Newton iteration loop.

### Setup

The FVM Euler 1D nozzle solver was run with the HHL quantum linear solver on the
Aer statevector simulator with 150,000 shots. Five CFL values were tested, each
with 10 independent trials to capture statistical variation from quantum sampling.

| Parameter | Value |
|---|---|
| Solver | FVM Euler 1D nozzle |
| Elements | 5 |
| Time scheme | BDF1 (implicit) |
| Linear solver | HHL (statevector, 150k shots) |
| Newton iterations | 15 |
| Inner iterations | 1 |
| Local time stepping | enabled |
| CFL values | 1, 5, 10, 25, 1e10 |
| Trials per CFL | 10 |
| Platform | Frontier (ORNL), 1 node per trial |
| Libraries | Qiskit 2.3.1, qiskit-aer 0.17.2 |

CFL = 1e10 effectively removes the time derivative term, producing a steady-state
solve where the system matrix is dominated by the flux Jacobian.

### System Conditioning

The condition number of the linear system (kappa(A)) scales directly with CFL.
At CFL = 1, the time derivative term dominates the system matrix, producing a
well-conditioned system. As CFL increases, the flux Jacobian dominates and
conditioning degrades. Condition numbers are nearly identical across trials (std < 0.5) since
matrix assembly depends on the current solution state, which diverges
only slightly from quantum sampling noise.

| CFL | kappa(A) iter 0 | kappa(A) iter 14 |
|---|---|---|
| 1 | 7.1 | 7.2 |
| 5 | 30.4 | 27.1 |
| 10 | 48.1 | 39.9 |
| 25 | 69.9 | 53.6 |
| 1e10 | 96.0 | 67.2 |

### Results

Final-iteration (iter 14) L2 relative error and HHL fidelity, averaged over 10
trials:

| CFL | L2 Error (mean) | L2 Error (std) | L2 Error (range) | Fidelity (mean) | Wall Time (mean) |
|---|---|---|---|---|---|
| 1 | 2.0% | 0.2% | 1.7 – 2.4% | 0.99959 | 18.8 min |
| 5 | 5.1% | 0.5% | 4.3 – 6.2% | 0.99738 | 18.7 min |
| 10 | 3.6% | 0.5% | 2.9 – 4.7% | 0.99864 | 19.7 min |
| 25 | 6.7% | 2.1% | 3.3 – 9.2% | 0.99508 | 20.1 min |
| 1e10 | 10.0% | 5.9% | 3.6 – 24.1% | 0.98673 | 37.2 min |

### Observations

**CFL = 1 produces the most accurate and most repeatable results.** All 10 trials
converged to within 1.7–2.4% L2 relative error, with a standard deviation of
just 0.2%. This is the tightest distribution of any CFL value tested.

**Error and variance both increase with CFL.** At CFL = 5, the mean error rises
to 5.1%. At CFL = 25, trial-to-trial spread widens to a 3.3–9.2% range. At
CFL = 1e10, two outlier trials reached 18% and 24% error, and the standard
deviation is 30x larger than at CFL = 1.

**CFL = 10 is slightly better than CFL = 5.** This is likely due to the specific
conditioning of the linear system at these two step sizes rather than a general
trend. The overall pattern is still degradation with increasing CFL.

**Fidelity remains high across all CFL values.** Even at CFL = 1e10, the mean HHL
fidelity is 0.987, meaning the quantum circuit solves each individual linear
system Ax = b accurately. The solution error growth at high CFL comes from the
accumulation of small per-solve sampling errors through the nonlinear Newton
iteration, not from a breakdown of the HHL algorithm itself.

**CFL = 1e10 costs nearly twice the compute time.** Wall time jumps from ~19 min
to ~37 min at the extreme CFL, while producing the least accurate and least
reliable results. Note that these timings reflect the Qiskit 2.3.1 / aer 0.17.2
stack, which provides a 3.4x overall speedup compared to the previous Qiskit
1.2.4 / aer 0.15.1 configuration. See
`analysis/qiskit_2.x/code-Qiskit-Version-Upgrade.md` for details on the
version upgrade performance gains.

### Next Steps

**CFL < 1.** The solver accepts sub-unity CFL values with no validation. CFL < 1
would further strengthen diagonal dominance (kappa(A) < 7), potentially reducing
error and variance below the CFL = 1 baseline. The tradeoff is more pseudo-time
steps to reach steady state. Values of 0.1, 0.25, and 0.5 would map the
accuracy-vs-iteration-count curve.

**Increase shots.** The current 150k shot budget holds fidelity above 0.99 at all
CFL values. Doubling or quadrupling shots could tighten the error distribution
at moderate CFL (5-10), where fidelity is already high but sampling noise still
compounds through Newton iterations. The 3.4x Qiskit 2.x speedup
(see `analysis/qiskit_2.x/code-Qiskit-Version-Upgrade.md`) means a 300k-shot
run at CFL = 1 would still finish well under the old 1.x wall time.

**Increase Newton iterations.** The current 15-iteration cap may not be enough
for higher CFL values to converge. With CFL = 1 completing in ~19 min, there is
headroom to run 30-50 iterations and test whether the high-CFL cases eventually
converge or whether sampling noise causes them to stall or diverge.

### Reference

- Experiment: `q8020-cfd-experiments/results/fvm_euler_1d_solver/2026-04-05/_52d087d1`
- Input TOML: `q8020_fvm_1d_smoke_test.toml` (group `[time_steps]`)
- Summary plot: `analysis/fvm_euler_1d_solver/cfl_step/cfl_comparison_summary.png`
- Plot script: `analysis/fvm_euler_1d_solver/cfl_step/make_cfl_plot.py`
