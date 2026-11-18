# Structured rewrite of the LuGo step-0 HHL circuit, nelem 5

The structured rewrite of
`aux/fvm_euler_1d_nozzle/hhl-structured-rewrite-2026-11/` applied to the LuGo
qpy itself rather than to the pre-LuGo HHL. Simulation (Aer) and
transpilation only.

| piece | value |
|---|---|
| node | macos-laptop (`MH-DT9TLJQR2V`) |
| run | 2026-11-17T02:17:07Z to 2026-11-17T02:18:27Z, 80 s |
| code | aux `28850e14` plus the uncommitted `hhl-structured-rewrite-2026-11/` (`structured_rewrite.py`, `run_test.py --input lugo`); fvm repo venv, qiskit 2.6.0, qiskit-aer 0.17.2, qiskit-ibm-runtime 0.50.0 |
| experiments repo | `f3ee7755` (dirty) |
| input | `2026-02-26-LuGo/circuits/circuit_generated_nelem5_iter0.qpy`, sha256 `2c8b064d...9808bd56` |
| recorded step-0 metrics | `2026-02-26-LuGo/nelem5/statevector/exact/hhl_metrics_nelem5_statevector.csv` |

## What the rewrite takes from LuGo

LuGo builds each of its 16 blocks (8 powers and 8 inverse powers, each
synthesized separately) with qiskit's `qs_decomposition` of U^(+-2^k) and
then controls it gate by gate. The rewrite takes that QSD's intermediate
values as available and recomputes the ones it needs:

- **U**, from LuGo's first block.
- **The first-step CSD factor of U^1**, `u1` and `u2`, from the same
  `cossin` call. These values are identical to LuGo's.
- **QSD's next level for that factor**: the demultiplex and the two 4-qubit
  syntheses, on the factor with a diagonal phase folded in. These are the
  same operations, on values that differ from LuGo's by that diagonal.

The power of each LuGo block, which its name does not carry, is found by
matching the block's unitary against L Rx(m theta) L^dag: all 16 match to
below 1e-8.

## Results

| circuit | target | 2q gates | 2q depth | total depth |
|---|---|---|---|---|
| LuGo | all-to-all | 57280 | 57179 | 143699 |
| rewrite, exact | all-to-all | 7347 | 6867 | 25087 |
| rewrite, AQC | all-to-all | 5296 | 3689 | 16697 |
| LuGo | Heron | 78993 | 73567 | 287084 |
| rewrite, exact | Heron | 12257 | 10929 | 43813 |
| rewrite, AQC | Heron | 6837 | 4208 | 18758 |
| LuGo | Nighthawk | 81818 | 73670 | 271971 |
| rewrite, exact | Nighthawk | 12614 | 10975 | 41946 |
| rewrite, AQC | Nighthawk | 6415 | 4285 | 19042 |

- **Exact rewrite:**
  - each block equals LuGo's to 4.3e-12;
  - the full state equals LuGo's stored circuit to 1 - F = 5.1e-14;
  - the step-0 fidelity 0.99995714 equals the recorded one to 3e-14;
  - the used shot counts are identical for all 10 seeds.
- **AQC rewrite:**
  - both 4-qubit pieces of L at 62 CX, 1 - F 1.6e-12 and 7.3e-13;
  - block entries within 1.4e-6;
  - full state 1 - F = 3.4e-13;
  - used shot counts identical for 8 of 10 seeds;
  - fidelity spread the same: 0.99718 / 0.99843 / 0.99897 against
    0.99718 / 0.99835 / 0.99897.
- **The counts equal those from the pre-LuGo input**
  (`../2026-11-15-hhl-structured-rewrite/`) to within a few gates: both
  inputs hold the same U, so they give the same L and the same AQC pieces.

Files: `nelem5/counts.csv`, `nelem5/statevector.csv`, `nelem5/shots.csv`,
`nelem5/summary.json`, `nelem5/log.txt`, as in the pre-LuGo run.

## Per-block counts: a barrier after every block (`nelem5-barriers/`, `nelem10-barriers/`)

Run 2026-11-17T02:30Z to 02:34:41Z with `run_test.py --input lugo --barriers`
(nelem 10 with `--no-aqc`); same code, venv and node as above.

Without barriers, qiskit's level-2 transpile cancels some gates across
block seams, where one block's L meets the next block's L^dag. At nelem 5
that is 150 CX all-to-all: 7347 against 7497 with barriers.

With barriers, nothing is merged across blocks, and the whole-circuit count
equals the sum of the parts:

- exact: 16 x 444 + 256 + 138 = 7498, measured 7497;
- AQC: 16 x 312 + 394 = 5386, measured 5386.

These are the numbers for the paper's table.

| nelem | circuit | target | 2q gates | 2q depth | total depth |
|---|---|---|---|---|---|
| 5 | LuGo | all-to-all | 57280 | 57179 | 143699 |
| 5 | rewrite, exact | all-to-all | 7497 | 7096 | 26078 |
| 5 | rewrite, AQC | all-to-all | 5386 | 3842 | 17583 |
| 5 | LuGo | Heron | 78993 | 73567 | 287084 |
| 5 | rewrite, exact | Heron | 11445 | 10576 | 44551 |
| 5 | rewrite, AQC | Heron | 6949 | 4354 | 19703 |
| 5 | LuGo | Nighthawk | 81818 | 73670 | 271971 |
| 5 | rewrite, exact | Nighthawk | 12780 | 11309 | 43450 |
| 5 | rewrite, AQC | Nighthawk | 6530 | 4548 | 20111 |
| 10 | LuGo | all-to-all | 264516 | 264357 | 660908 |
| 10 | rewrite, exact | all-to-all | 33472 | 32402 | 117579 |
| 10 | LuGo | Heron | 361770 | 339395 | 1329688 |
| 10 | rewrite, exact | Heron | 53732 | 48263 | 197678 |
| 10 | LuGo | Nighthawk | 378572 | 340524 | 1256973 |
| 10 | rewrite, exact | Nighthawk | 58950 | 52155 | 195605 |

**Equivalence:**

- nelem 5: exact 1 - F = 5.8e-14 and AQC 3.4e-13 against LuGo's stored
  state; fidelity 0.999957 both.
- nelem 10: exact 1 - F = 2.6e-13; fidelity 0.999673, equal to the recorded
  value; used shot counts identical for all 10 seeds.

**nelem 10 per block:** 1820 CX exact (L is 878 CX), against 14433 to 14448
in LuGo. AQC was not run at nelem 10, where L's pieces are 5-qubit unitaries.

## Paper table inputs added 2026-11-17

**Raw HHL depth (`hhl-raw-depth/hhl_raw_depth.csv`).** The pre-LuGo HHL
qpy (`nov2025-rerun/nov_pkgs/2026-11-03/_9f0fbf67/719a35aa/circuit_generated_statevector_nelem5_iter0.qpy`)
was transpiled the same way, with `aux/.../hhl_raw_depth.py`: 199 s and
12.4 GB peak memory.

| target | 2q gates | 2q depth | depth |
|---|---|---|---|
| all-to-all | 1752696 | 1752597 | 4424714 |
| Heron | 2357018 | 2252766 | 8828386 |
| Nighthawk | 2504119 | 2258238 | 8333864 |

The depth is 30.6x to 30.8x LuGo's on all three targets.

**AQC compression sweep (`aqc-sweep/aqc_tradeoff.csv`).** Made with
`aux/.../aqc_tradeoff.py`, best of seeds 1 and 2 per piece, per-block
(barrier) circuits.

| CX per piece | 1 - F per piece | HHL fidelity | CX all-to-all |
|---|---|---|---|
| 62 | 1.6e-12 | 0.999957 | 5386 |
| 56 | 8.1e-4 | 0.99911 | 5002 |
| 48 | 1.2e-2 | 0.953 | 4490 |
| 40 | 4.8e-2 | 0.795 | 3978 |
| 32 | 0.14 | 0.52 | 3466 |
| 24 | 0.28 | 0.20 | 2954 |
| 16 | 0.53 | 0.47 | 2442 |

Below the 61-CX exact bound for a 4-qubit unitary, fidelity falls fast.
The `esp_est_chicago` column scales ibm_chicago's measured log ESP
(-11.31 over 6549 CZ) by the Nighthawk CZ count. Even at 16 CX per piece it
is only 1.7e-3.

**Tightened AQC, 56 CX per piece (`nelem5-barriers-aqc56/`).** Made with
`run_test.py --input lugo --barriers --aqc-cx 56`: best per-piece fit over
seeds 1 to 3 (1 - F 7.6e-4 and 7.4e-4), 288 CX per block.

| target | 2q gates | 2q depth | depth |
|---|---|---|---|
| all-to-all | 5002 | 3594 | 16217 |
| Heron | 6407 | 4224 | 19301 |
| Nighthawk | 6146 | 4292 | 18804 |

- **Accuracy:** full-state 1 - F = 4.0e-4 against LuGo; HHL fidelity
  0.997918; shot fidelity median 0.99650 against 0.99835.
- **The choice of fit matters.** The sweep's seed choice at 56 CX gave
  0.99911, but the fit with the lowest per-piece error gave the lower HHL
  fidelity. Fits are chosen by per-piece error, from the circuit alone,
  never by checking against the classical solution.

**AQC at 48 and 40 CX per piece (`nelem5-barriers-aqc48/`, `nelem5-barriers-aqc40/`).**
Made with `run_test.py --input lugo --barriers --no-lugo --aqc-cx 48` (and
40), best per-piece fit over seeds 1 to 3; the fidelities equal the sweep's.

| CX per piece | 1 - F per piece | block CX | fidelity | depth all-to-all | depth Heron | depth Nighthawk |
|---|---|---|---|---|---|---|
| 48 | 1.2e-2, 9.1e-3 | 256 | 0.952632 | 14400 | 17425 | 17244 |
| 40 | 4.1e-2, 4.8e-2 | 224 | 0.795492 | 12517 | 15345 | 15664 |

The paper's table now carries 62, 56, 48 and 40 CX columns.

## 150k-shot results by AQC level, and the sign step (added 2026-11-17)

Each run above has 10 Aer seeds x 150000 shots (`shots.csv`).
`aux/.../sign_check.py` rebuilds each AQC level and scores its exact
statevector two ways:

- as is;
- as the shot extraction scores it: magnitudes, with the signs of the
  classical solution x_ref (the fvm sign step).

| level | statevector fidelity | statevector, x_ref signs | wrong signs (of 15) | 150k-shot fidelity, min / median / max |
|---|---|---|---|---|
| AQC 62 | 0.999957 | 0.999957 | 0 | 0.99718 / 0.99843 / 0.99897 |
| AQC 56 | 0.997918 | 0.997900 | 0 | 0.99546 / 0.99650 / 0.99776 |
| AQC 48 | 0.952632 | 0.947114 | 1 | 0.93880 / 0.94187 / 0.95962 |
| AQC 40 | 0.795492 | 0.865799 | 5 | 0.84308 / 0.86348 / 0.87943 |

The shot medians track the x_ref-sign score at every level, less shot noise,
so the shot runs are sound.

At 40 CX, five of the fifteen solution components have the wrong sign in the
quantum state. The sign step overwrites them, which lifts the shot fidelity
above the statevector fidelity. Quote statevector fidelity, as the paper's
table does, for solution quality at 48 CX and below.

## The rewrite with real L, and AQC of L (added 2026-11-17)

Real L is from genode's analysis (mesh task 20261117T0342-0001; its modules
`real_structure.py` and `realfit.py` are now in the aux folder).

- **The method.** A is real, so the CSD factors of U are real up to column
  phases. `real_structure` checks this and raises otherwise. L = diag(P, Q),
  with P and Q in SO(16), is fitted with real gates (Ry + CX) on a
  block-diagonal 5-qubit template, `bd5(cx, every=24, lower="line",
  msb_targets=[0])`.
- **Exactness.** At 122 CX the fit is exact (1 - F = 6.3e-13 for L), since
  122 CX covers the 240 parameters of SO(16) x SO(16). Fewer CX is
  approximate, which is the AQC column.
- **Runs.** Made with
  `run_test.py --input lugo --barriers --real-l --aqc-l-cx N --no-lugo`,
  in `nelem5-barriers-realL-aqc112/`, `-aqc104/` and `-aqc96/`. Each run's
  `exact` variant is the 122-CX real L.

| L CX | per block | 1 - F of L | fidelity | shot median | depth a2a | depth Heron | depth Nighthawk | CX a2a | Nighthawk CZ |
|---|---|---|---|---|---|---|---|---|---|
| 122 (rewrite) | 276 | 6.3e-13 | 0.999957 | 0.99835 | 15455 | 15932 | 15839 | 4810 | 5767 |
| 112 | 256 | 2.7e-4 | 0.999494 | 0.99755 | 14404 | 15256 | 15499 | 4490 | 5492 |
| 104 | 240 | 2.8e-3 | 0.990536 | 0.99053 | 13635 | 14534 | 14547 | 4234 | 5270 |
| 96 | 224 | 9.8e-3 | 0.982147 | 0.98128 | 12759 | 13944 | 13691 | 3978 | 4976 |

- The rewrite's full state equals LuGo's to 1 - F = 6.3e-14. Its used shot
  counts equal the stored circuit's for 10 of 10 seeds.
- The shot medians are at or below the statevector fidelities, so the sign
  step inflates nothing here.
- This table feeds the paper's `tab:custom-transpile`.

**Lower AQC budgets for L (`nelem5-barriers-realL-aqc88/`, `-aqc80/`,
`-aqc72/`, `-aqc64/`).** Swept in steps of 8 CX until the solution fidelity
fell below 0.80.

| L CX | per block | 1 - F of L | fidelity | shot median | depth a2a | depth Heron | depth Nighthawk | CX a2a | Nighthawk CZ |
|---|---|---|---|---|---|---|---|---|---|
| 88 | 208 | 2.0e-2 | 0.921973 | 0.92134 | 11867 | 12804 | 13343 | 3722 | 4698 |
| 80 | 192 | 4.4e-2 | 0.865683 | 0.90473 | 10900 | 11725 | 12217 | 3466 | 4381 |
| 72 | 176 | 9.0e-2 | 0.906861 | 0.90793 | 10061 | 11411 | 11558 | 3210 | 4142 |
| 64 | 160 | 0.13 | 0.411890 | 0.53504 | 9237 | 10807 | 10953 | 2954 | 3912 |

- **Fidelity is not monotone below 96 CX.** 72 CX scores above 80 CX, even
  though L's own error grows steadily. Each fit is picked by its own 1 - F
  against L, never by the solution (rule 4), so the solution fidelity of an
  approximate fit is partly luck.
- **The sign step inflates the shot score at 80 and 64 CX.** The shot
  median is above the statevector fidelity there, as at the complex AQC 40.
  Quote statevector fidelity.
- **The paper's table stops at 72 CX,** the last level at or above 0.80;
  64 CX is excluded.

**AQC of L in steps of 16 CX below the exact 122 (`nelem5-barriers-realL-aqc106/`,
`-aqc90/`, `-aqc74/`, `-aqc58/`, `-aqc42/`).** These are the paper table's
AQC columns, swept until the solution fidelity fell below 0.80.

| L CX | per block | 1 - F of L | fidelity | shot median | depth a2a | depth Heron | depth Nighthawk | CX a2a | Nighthawk CZ |
|---|---|---|---|---|---|---|---|---|---|
| 106 | 244 | 1.7e-3 | 0.994373 | 0.99319 | 13797 | 14476 | 14599 | 4298 | 5280 |
| 90 | 212 | 2.1e-2 | 0.970791 | 0.98206 | 11991 | 12939 | 13193 | 3786 | 4802 |
| 74 | 180 | 7.0e-2 | 0.968983 | 0.96916 | 10287 | 11302 | 11497 | 3274 | 4259 |
| 58 | 148 | 0.17 | 0.814678 | 0.84161 | 8579 | 9747 | 10043 | 2762 | 3639 |
| 42 | 116 | 0.35 | 0.068704 | 0.35336 | 6899 | 8656 | 8582 | 2250 | 3091 |

- The table shows 106 to 58 CX. At 42 CX the fidelity is 0.069, so it is
  left out.
- As with steps of 8, fidelity is not monotone in L's error. Here 74 CX
  (0.969) nearly equals 90 CX (0.971).
- At 90 and 58 CX, the sign step lifts the shot median above the
  statevector fidelity.
