# LuGo step-0 qpy rewrite: Aer runs, 2026-11-08

Step-0 (first Newton step) HHL circuits of the 2026-02-26 ORNL LuGo run
(`../2026-02-26-LuGo/circuits/`, nelem 5 and 10), run three ways on the Aer
ideal simulator: as stored, re-transpiled with qiskit 2.6.0, and after the
exact qpy rewrite. Exact statevector and 150000 shots with Aer seeds 1 to 10.
Simulation only; the hardware gate counts are from transpiling, not running.

Method, scripts and the comparison with the recorded feb26 and nov26 runs:
`aux/fvm_euler_1d_nozzle/lugo-qpy-rewrite-2026-11/` (its `README.md` says
exactly what the post-processor does).

## Provenance

| piece | value |
|---|---|
| inputs | `../2026-02-26-LuGo/circuits/circuit_{generated,transpile}_nelem{5,10}_iter0.qpy` (written by qiskit 1.4.5, QPY format 13) |
| scripts | `aux` `lugo-qpy-rewrite-2026-11/qpy_rewrite.py`, `run_step0.py`, new and uncommitted at run time; `aux` at `369ba1e9`, this repo at `c404936c` |
| venv | the fvm repo's `.venv` (`fvm_euler_1d_solver` at `9f6fe461`): Python 3.12.10, qiskit 2.6.0, qiskit-aer 0.17.2, qiskit-ibm-runtime 0.50.0, numpy 2.5.2, scipy 1.18.0 |
| transpile | level 2, `seed_transpiler` 1; Aer statevector target for the executed circuits; `cx, rz, sx, x` all-to-all and `FakeMarrakesh` for counts only |
| node | macos-laptop, 12 cores, `OMP_NUM_THREADS` 4, one process at a time |
| runs | nelem 5: 2026-11-08T03:15:52Z to 03:16:48Z (56 s); nelem 10: 2026-11-08T03:17:07Z to 03:23:19Z (6 min 12 s, 2 min 14 s of it the rewrite) |

Commands, from the aux folder:

```
../../../../fvm_euler_1d_solver/.venv/bin/python run_step0.py --nelem 5 --shots-nelem 5 --out ~/q8020/lugo-qpy-rewrite/nelem5
../../../../fvm_euler_1d_solver/.venv/bin/python run_step0.py --nelem 10 --shots-nelem 10 --out ~/q8020/lugo-qpy-rewrite/nelem10
```

No qpy is kept: the rewritten circuits are regenerated from the inputs by
`qpy_rewrite.py` in 12 s (nelem 5) and 134 s (nelem 10).

## Files, per `nelem<N>/`

| file | what it is |
|---|---|
| `circuits_nelem<N>.csv` | per variant: qubits, Aer-target depth and gates, all-to-all CX and 2-qubit depth, Heron CZ and 2-qubit depth, transpile, rewrite and run times in s |
| `step0_statevector_nelem<N>.csv` | per variant: fidelity, relative and normalized L2 error vs the classical solve, `l2_error_rel_truesol`, state fidelity vs the stored circuit |
| `step0_shots_nelem<N>.csv` | per variant and seed: the same metrics, shots with ancilla 1, shots used (ancilla 1, clock 0), a hash of the counts |
| `versions_nelem<N>.json` | library versions, commits, arguments, UTC start and end |
| `run.log` | the run log, with the rewrite report per nelem |

Variants: `feb26_stored`, `feb26_qiskit26`, `rewrite_qiskit26`.

## Results

| nelem | qubits | variant | all-to-all CX | Heron CZ | statevector fidelity | 150000-shot fidelity, min / median / max |
|---|---|---|---|---|---|---|
| 5 | 14 | feb26_stored | 57280 | 78995 | 0.999957137763 | 0.99718 / 0.99835 / 0.99897 |
| 5 | 14 | feb26_qiskit26 | 57280 | 78993 | 0.999957137763 | same counts as stored, every seed |
| 5 | 14 | rewrite_qiskit26 | 16412 | 25915 | 0.999957137763 | same counts as stored, every seed |
| 10 | 16 | feb26_stored | 264516 | 361768 | 0.999673159489 | 0.99621 / 0.99715 / 0.99842 |
| 10 | 16 | feb26_qiskit26 | 264516 | 361770 | 0.999673150132 | 0.99624 / 0.99711 / 0.99851 |
| 10 | 16 | rewrite_qiskit26 | 75181 | 113240 | 0.999673158525 | same used counts as stored, every seed |

- The rewrite's output state matches the stored circuit's to 1 - F = 2.3e-13
  (nelem 5) and 1.6e-12 (nelem 10).
- The stored circuits run here reproduce the recorded feb26 step-0 values:
  fidelity to 3e-14 and 5e-14, relative L2 error to 1.6e-12 and 4e-13.
- Re-transpiling the stored generated circuit with qiskit 2.6 moves the
  nelem 10 state by 1 - F = 1.0e-8, enough to change which outcome some
  shots land on for a given seed. That is numerical, and the shot statistics
  are unchanged.
- At nelem 10 the rewrite's full count dictionaries differ from the stored
  circuit's for 8 of 10 seeds, but only in outcomes the extraction does not
  use; the used counts (ancilla 1, clock 0) are identical for all 10.
- Shots used (ancilla 1 and clock 0): median 2140 of 150000 (1.4 %) at
  nelem 5, 2457 (1.6 %) at nelem 10. With ancilla 1 at any clock value:
  2157 and 2531.

## Added 2026-11-08: the nov26 step-0 qpy, nelem 5 (`nov26-nelem5/`)

The same three variants for the 2026-11-03 LuGo rerun's own qpy
(`../nov2025-rerun/LuGo-rerun/circuits/`, written by qiskit 2.6.1, QPY format
18; two files, nelem 5 only): `nov26_stored`, `nov26_qiskit26`,
`rewrite_nov26_qiskit26`. Run on the macos-laptop, 2026-11-08T11:36:59Z to
11:38:05Z (66 s, 11.4 s of it the rewrite), with the same venv and the same
settings as above (qiskit 2.6.0, Aer 0.17.2, level 2, seed_transpiler 1,
`OMP_NUM_THREADS` 4, experiments commit `825a74a4`, aux scripts uncommitted at
run time). Command, from the aux folder:

```
../../../../fvm_euler_1d_solver/.venv/bin/python run_step0.py --source nov26 --nelem 5 --shots-nelem 5 --out ~/q8020/lugo-qpy-rewrite/nov26-nelem5
```

The nov26 generated qpy does not load in qiskit 2.6.0 as is (its
ExactReciprocalGate is written without parameters). `run_step0.py` loads it
with (nl 8, scaling 2^-7, neg_vals True), taken from the feb26 1/x block and
checked against the nov26 stored run; the aux README has the details.

| variant | all-to-all CX | Heron CZ | statevector fidelity | 150000-shot fidelity, min / median / max | state fidelity vs nov26_stored |
|---|---|---|---|---|---|
| nov26_stored | 55580 | 79538 | 0.999957137763 | 0.99718 / 0.99835 / 0.99897 | 1 |
| nov26_qiskit26 | 55580 | 79540 | 0.999957137763 | same counts as stored, every seed | 1 to 1e-14 |
| rewrite_nov26_qiskit26 | 16412 | 25915 | 0.999957137938 | same used counts as stored, every seed; one seed (9) differs in fidelity, 0.998584 vs 0.998616 | 1 - 8.7e-13 |

The nov26_stored run reproduces the recorded nov26 step-0 fidelity
(0.99995713776300) to 3e-14, and its Aer-target depth and gate count equal the
recorded ones plus the added measurements.
