# fvm nozzle, nelem 5: first SQLS run (full_svd), 2026-08-17, local

The first run of the fvm Euler 1D nozzle solver with ORNL's SQLS as the Newton
linear solver: `-linsolver SQLS`, method `full_svd`, `-sqls_repeats 1`,
`-v 2`, nelem 5, BDF1, ideal statevector simulator, 150000 shots setting.
It was a one-trial validation run by hand, not through the sweeper or the
harvester, so there is no TOML and no command record here.

- When: finished 2026-08-17T22:28:07Z (the solver's own `timestamp` is local
  time, 2026-08-17T18:28:07.82 -0400). `elapsed_time` 0.619 s; 0.075 s to
  0.103 s per solve. The `trial_0/` folder was created about 22:21Z, most
  likely by an earlier run without `-v 2` into the same folder.
- Node: macos-laptop.
- Code: fvm_euler_1d_solver `a885ef4719b1b3ff87f19905c06f47925eab6b8d`
  ("Bump quantum stack to latest qiskit 2.5 line") plus the uncommitted SQLS
  wiring. That wiring was committed 55 min later as
  `ef7f0a8b2247615b56e4391fa1804b59825de217` ("Add optional SQLS linear solver
  alongside HHL"); the exact tree that ran was not saved, so `ef7f0a8b` is
  the closest committed state, not a proven match.
- Libraries: sqls `9a4346a7d0255cb1b59429d3b9454358a5b5bb4d` (the local clone of
  ORNL's repo, clean), quantum_linear_solvers
  `66eadf0b4edcff100b20edf70a99e79cc69c5923` (the HHL library, present in the
  venv but not used by the SQLS path), qiskit 2.5.2, qiskit-aer 0.17.2,
  qiskit-ibm-runtime 0.49.0.
- Seed: none; the run was unseeded.
- Metadata: the `q8020_*_0.json` fragments in `trial_0/` were written by the
  SQLS-aware harvester on 2026-10-15, two months after the run, so they carry
  no experiment, exec_stats, params or environment section, and their code
  fragment has no commits. `trial_0/metapatches/20261117/` adds the commits
  above as a review patch.
- Write-up and plots: `aux/fvm_euler_1d_nozzle/sqls-vs-hhl-2026-08-17/`.

README added 2026-11-17. Sources: the August 2026 analysis (timeline rows and
findings) in the `proj:aiaa-4q26` project space, record
`note-20261117T1830Z-bd96`, file `01-august-2026-analysis.md`, and the
qiskit-upgrade analysis `03-qiskit-upgrade-and-solverfw.md` in the same
record, for the library versions.
