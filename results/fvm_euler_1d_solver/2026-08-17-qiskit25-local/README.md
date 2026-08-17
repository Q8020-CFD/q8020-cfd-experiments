# 2026-08-17 — qiskit 2.5 upgrade, local validation run

Manual (non-sweep) run of the `fvm_euler_1d_solver` under the **qiskit-2.5
upgrade**. Same laptop, same case, same Q8020-CFD linear-solver fork as the
sibling `2026-08-17-qiskit23-local` run — the ONLY intended difference is the
qiskit stack (2.3.1 → 2.5.2, ibm-runtime 0.46.1 → 0.49.0). This pair is a clean
2.3-vs-2.5 isolation.

- Run host: Mac laptop `MH-DT9TLJQR2V` (NOT Frontier).
- Run time (UTC): 2026-08-17T20:56 → 21:09 (~859.3 s solver elapsed).
- Solver: `fvm_euler_1d_solver` `main` @ `3c20cff8` + uncommitted qiskit-2.5
  bump (pyproject/uv.lock; .py code unchanged from 3c20cff8).
- Linear-solver lib: `Q8020-CFD/quantum_linear_solvers` @ `66eadf0` (unchanged;
  works under 2.5 with no edits).
- Stack: qiskit 2.5.2 / aer 0.17.2 / ibm-runtime 0.49.0.

## Key result (vs the 2.3 local run)

Same case fingerprint (iter-0 residual 12.375368413827264). At iter 0 the input
is provably identical (condition number 95.9778901432456 to 13 digits), so the
circuit differences are pure transpiler:

- transpiled depth **596,688 vs 638,237** (−6.5%), gates 641,145 vs 649,089
  (−1.2%), same 14 qubits.
- transpile time **14.3 vs 3.9 s/iter** (~3.7× slower under 2.5).
- generate/execute flat; end-to-end 859.3 vs 817.7 s.
- quality unchanged within shot noise (fidelity 0.993 vs 0.990).

Full four-way analysis:
`/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/qiskit_2.x/fvm-euler-1d-1x-vs-2x-vs-local-2026-08/`

## Layout / provenance

`trial_0/` — raw solver output + metadata. Large per-iteration `.qpy` circuit
files (~1.5 GB) are NOT copied (circuit stats live in `qc_metadata_*.csv` and
`q8020_artifacts_*.json`).

- `q8020_{case,code,backend,artifacts,results,analysis}_0.json` — repo harvester.
- `q8020_{params,experiment,exec_stats}_local.json`, `q8020_env_{before,after}_local.json`,
  `q8020_code_provenance_local.json` — hand-authored provenance (command, host,
  timestamps, resolved versions, git SHAs). `_local` marks this a manual run.

## Caveat

Laptop wall-clock is comparable to the sibling 2.3 local run (same machine) but
NOT to the Frontier groups. Compare 2.3-local vs 2.5-local for the qiskit-version
timing story.
