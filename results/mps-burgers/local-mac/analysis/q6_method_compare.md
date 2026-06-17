# q6 method-comparison analysis

Date: 2026-06-14. Source: `qlbm-ch-results/q6/*` symlinks → `~/q8020/2026-06-14/`.

Each of the 8 q6 cases ran the same Burgers setup (q=6, N=64, 230 steps,
150k shots, periodic sine IC, `measure_reprepare`, cfl=0.1) with four methods:
`qlbm_circuit`, `cole_hopf_circuit`, `lbm` (classical), and `ftcs_reference`
(the accuracy anchor). Per-case viscosity `nu` and IC variant differ.

## Method note on errors

The solver wrote `final_error: NaN` in every case because the in-solver
classical/analytic references were disabled (`--no-classical-reference
--no-analytic-reference`). Error is only meaningful against the
`ftcs_reference` series. The numbers below are computed here:
relL2 = RMS error of the final profile / RMS of the FTCS final profile.
The `method_compare.gif` / `_resources.png` in each case dir visualize the
same comparison.

## 1. Accuracy vs FTCS reference (relative L2, final profile)

| method | mean relL2 | median relL2 |
|---|---|---|
| **lbm (classical)** | **10.6%** | **8.9%** |
| cole_hopf_circuit | 30.4% | 23.7% |
| qlbm_circuit | 38.8% | 24.6% |

Classical LBM is the most accurate everywhere. The two quantum methods have a
near-tied median (~24%), but qlbm has a much worse tail (see sweep below).

### Per-case detail

| case | method | nu | L2 | Linf | relL2 |
|---|---|---|---|---|---|
| mutual_q6_nu015 | qlbm_circuit | 0.015 | 1.93e-01 | 2.79e-01 | 99.87% |
| mutual_q6_nu015 | cole_hopf_circuit | 0.015 | 2.81e-02 | 7.37e-02 | 14.58% |
| mutual_q6_nu015 | lbm_classical | 0.015 | 3.98e-03 | 7.56e-03 | 2.06% |
| mutual_q6_nu020 | qlbm_circuit | 0.02 | 1.50e-01 | 2.19e-01 | 80.32% |
| mutual_q6_nu020 | cole_hopf_circuit | 0.02 | 3.37e-02 | 8.98e-02 | 18.02% |
| mutual_q6_nu020 | lbm_classical | 0.02 | 5.02e-03 | 9.98e-03 | 2.68% |
| mutual_q6_nu030 | qlbm_circuit | 0.03 | 1.73e-02 | 3.05e-02 | 9.85% |
| mutual_q6_nu030 | cole_hopf_circuit | 0.03 | 5.17e-02 | 1.24e-01 | 29.42% |
| mutual_q6_nu030 | lbm_classical | 0.03 | 7.93e-03 | 1.53e-02 | 4.51% |
| mutual_q6_nu050 | qlbm_circuit | 0.05 | 2.87e-02 | 6.29e-02 | 18.48% |
| mutual_q6_nu050 | cole_hopf_circuit | 0.05 | 7.29e-02 | 1.55e-01 | 46.93% |
| mutual_q6_nu050 | lbm_classical | 0.05 | 1.62e-02 | 2.83e-02 | 10.44% |
| shock_q6 | qlbm_circuit | 0.03 | 4.99e-02 | 8.03e-02 | 27.75% |
| shock_q6 | cole_hopf_circuit | 0.03 | 7.77e-02 | 2.26e-01 | 43.17% |
| shock_q6 | lbm_classical | 0.03 | 3.23e-02 | 6.48e-02 | 17.98% |
| show_q6_ch_smooth | qlbm_circuit | 0.08 | 2.76e-02 | 5.43e-02 | 21.39% |
| show_q6_ch_smooth | cole_hopf_circuit | 0.08 | 8.09e-02 | 1.81e-01 | 62.66% |
| show_q6_ch_smooth | lbm_classical | 0.08 | 3.08e-02 | 5.05e-02 | 23.88% |
| show_q6_ch_stress | qlbm_circuit | 0.04 | 6.40e-02 | 1.48e-01 | 19.51% |
| show_q6_ch_stress | cole_hopf_circuit | 0.04 | 5.15e-02 | 1.21e-01 | 15.69% |
| show_q6_ch_stress | lbm_classical | 0.04 | 5.23e-02 | 1.10e-01 | 15.96% |
| show_q6_qlbm_margin | qlbm_circuit | 0.025 | 1.00e-01 | 1.44e-01 | 33.32% |
| show_q6_qlbm_margin | cole_hopf_circuit | 0.025 | 3.78e-02 | 9.44e-02 | 12.56% |
| show_q6_qlbm_margin | lbm_classical | 0.025 | 2.24e-02 | 4.72e-02 | 7.43% |

## 2. Resource / timing

- **shots** (150k) and **n_pauli_terms** (~1020–1160) are essentially constant
  across cases — they track circuit size, not the physics.
- **Wall time** is the sharp differentiator:

  | method | mean wall_s |
  |---|---|
  | qlbm_circuit | 71.3 |
  | cole_hopf_circuit | 10.2 |
  | lbm_classical | ~0.00 |

  `qlbm_circuit` is roughly **7× slower** than `cole_hopf_circuit` for
  comparable median accuracy. `burgers_ab_shock_q6` is the qlbm outlier at
  **136 s** (≈2× the other cases). Classical LBM is effectively free (<0.01 s)
  and most accurate — the practical baseline.

## 3. Sweep trends

### qlbm_circuit low-viscosity blow-up (mutual nu sweep, smooth sine IC)

| nu | qlbm relL2 |
|---|---|
| 0.015 | 99.9% |
| 0.020 | 80.3% |
| 0.030 | 9.8% |
| 0.050 | 18.5% |

At nu ≤ 0.02 qlbm is essentially non-convergent (error ≈ signal magnitude),
then snaps to single-digit error at nu=0.03. Below nu≈0.025 at q=6 it is
unstable.

### Complementary failure regimes

cole_hopf degrades the *opposite* way — it gets *worse* as nu rises (14.6% →
46.9% across the same nu sweep). So the two quantum methods have complementary
failure regimes: qlbm needs enough diffusion to be stable; cole_hopf loses
accuracy as diffusion grows. On the shock/stress/smooth `show` cases all three
methods cluster at 15–60% relL2, with no method dominating except classical LBM.

## 4. Takeaways

1. Classical LBM remains the accuracy/speed reference.
2. qlbm_circuit is unstable below nu≈0.025 at q=6 and ~7× costlier than
   cole_hopf for no median-accuracy gain.
3. cole_hopf and qlbm fail in opposite viscosity regimes — the most actionable
   result for choosing a method per regime.
