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
