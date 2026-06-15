# q4 hardware-feasibility analysis

Date: 2026-06-14. Source: `qlbm-ch-results/q4/*` symlinks → `~/q8020/2026-06-14/`.

The q4 set (N=16) is the small-grid copy of the q6 A-B bakeoff, built to probe
whether the circuits shrink into a range runnable on real IBM hardware. Each of
the 8 cases ran qlbm_circuit, cole_hopf_circuit, lbm (classical), and
ftcs_reference (accuracy anchor). relL2 = RMS(final − FTCS) / RMS(FTCS).

## 1. Accuracy vs FTCS reference

| method | mean relL2 | median relL2 |
|---|---|---|
| **cole_hopf_circuit** | **10.8%** | **9.6%** |
| lbm (classical) | 11.0% | 8.2% |
| qlbm_circuit | 73.9% | 82.5% |

The headline result: **at q4, cole_hopf matches classical LBM accuracy** (10.8%
vs 11.0% mean) — a reversal from q6, where classical LBM was clearly best and
cole_hopf trailed at 30%. On the coarse N=16 grid the classical FTCS/LBM
discretization error grows, so the spectral-exact cole_hopf transform is no
longer at a disadvantage. qlbm, by contrast, is badly degraded (74% mean) —
its scheme floor dominates at small N.

### Per-case detail

| case | qlbm | cole_hopf | lbm |
|---|---|---|---|
| mutual_q4_nu015 | 85.6% | 12.1% | 4.9% |
| mutual_q4_nu020 | 79.4% | 9.1% | 4.4% |
| mutual_q4_nu030 | 60.4% | 8.6% | 3.6% |
| mutual_q4_nu050 | 87.6% | 12.1% | 6.6% |
| shock_q4 | 87.3% | 10.0% | 21.5% |
| show_q4_ch_smooth | 17.9% | 17.6% | 19.4% |
| show_q4_ch_stress | 100.0% | 8.3% | 18.0% |
| show_q4_qlbm_margin | 72.9% | 8.8% | 9.7% |

Notable: on the harder cases (shock, ch_stress) cole_hopf *beats* classical LBM
(10.0% vs 21.5%; 8.3% vs 18.0%) — the coarse classical grid struggles with
sharp features while the transform method holds. qlbm fails almost everywhere
(only ch_smooth, its highest-nu/most-diffuse case, is competitive at 17.9%).

## 2. Hardware cost (per circuit, simulator-measured in metric basis)

| method | qubits | CX/circuit | depth | circuits/run |
|---|---|---|---|---|
| **cole_hopf** | **10** | **~1,007** | **~3,060** | 3 (6 for shock) |
| qlbm | 9 | ~119,440 | ~432,600 | 48 (96 for shock) |

- **cole_hopf CX is grid-dependent and small at q4** (~1,007 vs ~6,600 at q6).
- **qlbm CX is grid-INDEPENDENT** — 119,440 at q4, q6, and q7 alike. The grid
  is handled via measure_reprepare, not more gates. Its 9-qubit footprint is a
  red herring: the gate count is fixed and enormous at every q.

## 3. Feasibility on a 2026 IBM device (Heron-class, 2q error ε ≈ 2e-3)

Bare fidelity ≈ e^(−ε·CX):

| | CX | expected 2q errors | bare fidelity | verdict |
|---|---|---|---|---|
| cole_hopf q4 | ~1,007 | ~2.0 | ~0.13 | **runnable with error mitigation** |
| qlbm (any q) | ~119,440 | ~240 | ~0 | not a candidate at any q |

## 4. Takeaways

1. **cole_hopf at q4 is the hardware-demo candidate, and the case is stronger
   than expected**: 10 qubits, ~1,007 CX (ZNE/PEC-feasible regime), AND it is
   now as accurate as classical LBM — even better on shock/stress cases. A q4
   hardware run would be scientifically meaningful, not just a toy.
2. **qlbm is off the table on hardware at every q** (~119k CX → zero fidelity),
   and at q4 it is also the least accurate method — no reason to run it on
   hardware.
3. The accuracy crossover (cole_hopf catching classical LBM as the grid
   coarsens) means the q4 operating point is where the quantum transform method
   is genuinely competitive — the right regime for a hardware demonstration.

### Caveat
Simulator CX (~1,007) is measured at optimization_level 1 on all-to-all
connectivity. Real-device CX will be HIGHER after routing onto a fixed coupling
map (SWAP insertion); budget ~1.3–2x, i.e. plan for ~1,300–2,000 CX and
mitigation tuned accordingly.
