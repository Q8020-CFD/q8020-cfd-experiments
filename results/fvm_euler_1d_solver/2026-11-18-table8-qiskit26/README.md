# Paper Table 8, HHL and LuGo columns, constructed and transpiled under qiskit 2.6

Step 0, nelem 5, 14 qubits. Finished 2026-11-18T01:23:30Z on macos-laptop (MH-DT9TLJQR2V)
by `code/table8_columns.py` (sha256
`440993afc73c486e6437f83cd47a1f663865ad318bd088b0cc4f734d2d3298eb`; aux
`fcb86505`, the script then uncommitted), in the fvm solver venv: Python
3.12.10, qiskit 2.6.0, qiskit-aer 0.17.2, qiskit-ibm-runtime 0.50.0, numpy
2.5.2, scipy 1.18.0.

| column | circuit | constructed by | transpiled by |
|---|---|---|---|
| HHL | the fvm solver's own step-0 HHL circuit, built as `solve_one_step` builds it (`scale_Ab`, `convert_to_pow2`, `convert_system_to_herm`, `QuantumHHL.generate_circuit`) from `../nov2025-rerun/nov_pkgs/2026-11-03/_9f0fbf67/719a35aa/system_Ab_nelem5_iter0.pkl`; nothing simulated | qiskit 2.6.0, fvm `9f6fe461` (clean), `Q8020-CFD/quantum_linear_solvers` `99231b85` | qiskit 2.6.0 |
| LuGo | ORNL's 2026-11-03 LuGo rerun, `../nov2025-rerun/LuGo-rerun/circuits/circuit_generated_statevector_nelem5_iter0.qpy`, loaded with the 1/x parameters read from the feb26 circuit (`qpy_rewrite.load_qpy`, as `run_step0.py` does) | qiskit 2.6.1 (qpy header) | qiskit 2.6.0 |

Transpile as in Table 8: optimization level 2, seed_transpiler 1, to
all-to-all cx/rz/sx/x, FakeMarrakesh (Heron r2) and FakeNighthawk;
measurements stripped. Results in `table8_columns.csv`:

| depth | HHL | LuGo |
|---|---|---|
| all-to-all | 4,248,791 | 138,076 |
| IBM Heron | 8,660,594 | 282,422 |
| IBM Nighthawk | 8,060,986 | 264,074 |

Two-qubit gates: HHL 1,695,194 / 2,395,581 / 2,460,796, LuGo 55,580 /
79,540 / 80,518 (all-to-all / Heron / Nighthawk). The previous Table 8
columns were the qiskit 1.2.4-built HHL (4,424,714 / 8,828,386 / 8,333,864)
and the qiskit 1.4.5-built feb26 LuGo (143,699 / 287,084 / 271,971).

Same operation in every circuit (`table8_check.json`): the 16 QPE block
matrices of the qiskit 2.6.0 HHL equal those of the nov26 LuGo to 7.1e-12
and of the qiskit 1.2.4 HHL to 8.4e-12; the state preparation of b agrees
to 1.1e-16 and the 1/x reciprocal to 5.6e-16 (LuGo) and 4.2e-15 (HHL 1.2.4).
So the solution fidelity is the recorded 0.999957 for both columns; the
circuits were not simulated here.

Not kept: the qiskit 2.6.0 HHL qpy (61.6 MB). It is regenerated in about
19 s by the script, and qiskit 2.6.0 cannot load it back anyway: qiskit 2.x
writes `ExactReciprocalGate` with no parameters, the same fault as the nov26
LuGo file.
