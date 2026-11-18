# fvm nozzle, nelem 5, HHL: run 1 of the optimization-level sweep (flag had no effect)

The first full 16-case run of the nov2025 vs nov2026 transpiler
optimization-level sweep. Its `-opt_level` patch only reached the
fake/real-IBM transpile branch, and the ideal backend calls
`transpile(circ, backend)` with no level, so every case ran at qiskit's
default level: 1 on qiskit 1.2.4 (nov2025) and 2 on qiskit 2.6.0 (nov2026).
It is kept as a replicate set of each codebase's default-level behaviour and
of run-to-run timing noise, not as the answer. The answer is run 2, in
`../2026-11-07-hhl-nelem5-optlevel/`, whose README also covers this run.

- When: 2026-11-07T02:23:09Z to 04:05:47Z (UTC), 8 sweeper lanes at once, one
  per group, each lane sequential.
- Node: macos-laptop (12 cores, 36 GB).
- Code: the same two codebases as run 2, with the run-1 patches:
  - nov2026: fvm d4a531bd plus `optlevel-nov2026-d4a531bd.diff`, qiskit 2.6.0,
    qiskit-aer 0.17.2;
  - nov2025: fvm a5317f2b plus `optlevel-nov2025-a5317f2.diff`, qiskit 1.2.4,
    qiskit-aer 0.15.1.
  The run-1 diffs are in
  `aux/fvm_euler_1d_nozzle/optlevel-hhl-nelem5-2026-11/inputs/run1-flag-noop/`.
  Their sha256 matches the `diff_sha256` each case recorded.
- Metautil: main 2380796, so each lane has `q8020_code_provenance.json`.
- TOML: the run-time copies in `logs/<lane>/` are the ones that ran. The
  invocation records name `aux/.../inputs/hhl_nelem5_optlevel.toml`, which now
  holds the run-2 TOML; the run-1 TOML is
  `aux/fvm_euler_1d_nozzle/optlevel-hhl-nelem5-2026-11/inputs/run1-flag-noop/hhl_nelem5_optlevel.toml`.
- Layout: `<codebase>/shots<N>/opt<L>/` is one case (qpy and system_Ab
  pickles removed); `logs/<lane>/` holds the sweeper metadata. All 16 cases
  have an assembled `q8020_metadata_<id>.json`, and all 8 lanes a
  `q8020_sweep_meta_<wf>.json`.
- Analysis of this run:
  `aux/fvm_euler_1d_nozzle/optlevel-hhl-nelem5-2026-11/analysis/run1-flag-noop/`.

README added 2026-11-17 from the run-2 README, the invocation records and
the sweep metadata in this folder.
