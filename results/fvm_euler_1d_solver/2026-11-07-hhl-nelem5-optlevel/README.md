# fvm nozzle, nelem 5, HHL: transpiler optimization level 0-3, nov2025 vs nov2026

Run on macos-laptop (12 cores, 36 GB), 2026-11-07, mesh task 241f3c/20261107T0213-0001.
8 sweeper lanes at once (one per group), one thread per solver process, each
lane sequential. Wall times therefore include contention. Layout:
`<codebase>/shots<N>/opt<L>/` = one case (qpy and system_Ab pickles removed).
`logs/<lane>/` = sweeper metadata and run-time TOML copies.

- nov2026: fvm d4a531bd (feature/sqls-aiaa-4q26) + local -opt_level patch,
  python 3.12.10, `uv sync --frozen`: qiskit 2.6.0, qiskit-aer 0.17.2,
  qiskit-ibm-runtime 0.50.0, sqls 67057e4b, quantum_linear_solvers 99231b85.
- nov2025: fvm a5317f2b + local patch, python 3.12.10: qiskit 1.2.4,
  qiskit-aer 0.15.1, qiskit-algorithms 0.3.1, qiskit-ibm-runtime 0.35.0,
  qiskit-qasm3-import 0.5.1, qiskit-iqm 18.0, numpy 2.2.4, scipy 1.14.1,
  matplotlib 3.10.1, quantum_linear_solvers jw676 a94cf63.
- metautil main 2380796. Settings: BDF1, CFL 1e10, 15 steps max, 1 inner,
  restol 1e-2, tol 1e-10, local dt, HHL. transpile seed 1; nov2026 shots runs
  -seed 1; nov2025 has no -seed, its shots runs are unseeded.
- Inputs, patches, TOML, freezes and analysis:
  `aux/fvm_euler_1d_nozzle/optlevel-hhl-nelem5-2026-11/`.

`../2026-11-07-hhl-nelem5-optlevel-run1-flag-noop/` is a first full 16-case run
whose patch only reached the fake/real-ibm transpile branch. The ideal backend
calls `transpile(circ, backend)` with no level, so the flag changed nothing
there (all levels were qiskit's default level 2). Kept as a replicate set of
the level-2 behaviour and of run-to-run timing noise; not the answer.
