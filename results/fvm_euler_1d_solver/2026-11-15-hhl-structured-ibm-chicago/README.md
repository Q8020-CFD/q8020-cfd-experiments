# Structured HHL step 0, nelem 5, on ibm_chicago: a null result, as predicted

One IBM Quantum hardware run of the AQC structured rewrite of the fvm HHL
step-0 circuit. The method is in
`aux/fvm_euler_1d_nozzle/hhl-structured-rewrite-2026-11/README.md`, and the
simulator tests are in `../2026-11-15-hhl-structured-rewrite/`.

| piece | value |
|---|---|
| backend | `ibm_chicago`, IBM Nighthawk r2, 120 qubits |
| job | `dbt1dqreq3sc73ev92sg`, SamplerV2, tags q8020 / fvm-hhl-structured / nelem5 / step0 |
| submitted | 2026-11-15T20:32:44Z from macos-laptop (`MH-DT9TLJQR2V`), account `default-ibm-cloud` |
| finished | about 2026-11-15T20:47Z: 859 s wall, 774 s QPU charge time (12.9 min) |
| code | aux `28850e14` plus the uncommitted `hhl-structured-rewrite-2026-11/` (`structured_rewrite.py --aqc 62,64,68,72`, `ibm_submit.py`, `ibm_analyze.py`); fvm repo venv, qiskit 2.6.0, qiskit-ibm-runtime 0.50.0 |
| input | `nov2025-rerun/nov_pkgs/2026-11-03/_9f0fbf67/719a35aa/circuit_generated_statevector_nelem5_iter0.qpy` (the pre-LuGo HHL), rewritten with AQC pieces at 62 CX |

## What ran

Four PUBs on the same 14 physical qubits:
96, 97, 87, 88, 98, 107, 85, 86, 117, 99, 116, 108, 118, 106 (clbit 0 to
13; system 0 to 4, clock 5 to 12, ancilla 13). The layout is the best of 16
transpile seeds by ESP, level 2, seed 14.

| PUB | what it is | shots |
|---|---|---|
| main | the circuit: 6549 CZ, two-qubit depth 4427, 569 us scheduled | 1,000,000 |
| cal0, cal1 | all 14 qubits in 0 or 1, measured | 100,000 each |
| ctrl | positive control: the state preparation of b only, 39 CZ | 100,000 |

Options:

- dynamical decoupling, XY4, ALAP;
- Pauli twirling of gates and measurements, 10,000 shots per
  randomization;
- `max_execution_time` 1028 s.

## Result

The pre-flight ESP was 1.2e-5, so the expected share of signal among the
outcomes used for the solution was 1.8e-4.

| quantity | ideal (Aer) | maximally mixed | measured |
|---|---|---|---|
| P(ancilla 1) | 0.0144 | 0.5 | 0.500 |
| P(ancilla 1, clock 0) | 0.0143 | 0.00195 | 0.00191 |
| step-0 fidelity, raw | 0.998 (150k shots) | null 0.536 +- 0.017 | 0.541 (z +0.26) |
| step-0 fidelity, readout-corrected | | null 0.536 +- 0.019 | 0.539 (z +0.21) |
| step-0 fidelity, readout + background | | null 0.250 +- 0.145 | 0.077 (z -1.19) |

- **The main circuit's output is maximally mixed.** Every statistic sits on
  the null, which is 500 synthetic maximally mixed count sets scored the
  same way. The fidelity of about 0.54 comes from the fvm sign step, which
  takes the signs of x_ref; noise alone scores that.
- **Readout errors are small.** Flip rates from cal0 and cal1: median
  0.74 %, max 2.1 %.
- **The control confirms the pipeline but shows the device below its
  calibration.**
  - The most probable system states are the right ones and in the right
    order: state 8 at 0.37 against 0.76 expected, state 7 at 0.096 against
    0.13.
  - The clock and ancilla qubits read 0 in 99.5 % of shots, so the qubit
    mapping and bit order are correct.
  - Its classical fidelity against |b|^2 is only 0.585 raw and 0.602
    readout-corrected, against an ESP of 0.899 for its 39 CZ.
  - One system qubit that should always read 0 read 1 in 18 % of shots,
    far above any readout flip rate.

This agrees with the program's earlier hardware evidence: about 100 CZ gave
real signal and about 19.3k CZ depolarized fully (note-20260924-0006,
note-20260924-0007). About 6.5k CZ in a serial circuit is past the point
where signal survives.

## Files

| file | what it is |
|---|---|
| `prep.json` | pre-flight at submit time, options, physical qubits, reference solution, job id |
| `isa.qpy` | the four executed ISA circuits [main, ctrl, cal0, cal1] (Git LFS) |
| `counts.json` | raw counts of the four PUBs |
| `analysis.json` | `ibm_analyze.py --job dbt1dqreq3sc73ev92sg --n-null 500` output |

Re-score offline:
`ibm_analyze.py prep.json --counts counts.json`

## Note added 2026-11-17: no barriers in the executed circuit

The executed circuit was built without barriers between blocks. Qiskit's
transpile therefore cancelled some gates across block seams, where one
block's L meets the next block's L^dag. At nelem 5 all-to-all that is about
150 CX; the strictly per-block AQC circuit is 5386 CX against 5296 here.

So about 1 to 2 % of the executed CZ count comes from that cross-block
cancellation, by the generic transpiler and not by the rewrite. See
`../2026-11-17-hhl-structured-rewrite-from-lugo/` for the per-block counts.
