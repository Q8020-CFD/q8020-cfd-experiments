# fvm nozzle, nelem 5, 150000 shots: SQLS, HHL, HHL best and QSVT (aiaa-4q26)

Harvested 2026-11-04 from runs on the linux-server mesh node, 2026-11-03T19:46Z
to 2026-11-04T16:38Z. Records, analysis and the TOMLs are in the project space
proj:aiaa-4q26 (agallojr/aiaa-4q26-space): changes
`compare-hhl-sqls-nelem5-shots` (SQLS, HHL, HHL best) and
`add-qsvt-arm-nelem5-shots` (QSVT), each with `analysis.md`; the four-arm TOML
is `changes/add-qsvt-arm-nelem5-shots/hhl_hhlbest_sqls_qsvt_nelem5_shots.toml`.

## Case

The November 2025 HHL shots case (`../2025-11-11/shots_150000`): nelem 5,
BDF1, CFL 1e10, at most 15 Newton steps, 1 inner iteration, restol 1e-2,
tol 1e-10, local time step, ideal statevector simulator, 150000 shots, seeded.

| Folder | Solver flags | Code (Q8020-CFD/fvm_euler_1d_solver) |
|---|---|---|
| `sqls_full_svd/` | `-linsolver SQLS -sqls_method full_svd -sqls_state_prep initialize -sqls_repeats 1 -pad_eps 0` | `d4a531bd` (feature/sqls-aiaa-4q26) |
| `hhl_defaults/` | `-linsolver HHL` | `d4a531bd` |
| `hhl_best/` | `-linsolver HHL -hhl_shots_sign_first on -pad_eps 0` | `d4a531bd` |
| `qsvt_best/` | `-linsolver QSVT -qsvt_shots_sign_first on -pad_eps 0` | `219907cf` (feature/sqls-aiaa-4q26-svd-deflation) |
| `qsvt_best_bigshot/` | as `qsvt_best`, seed 1, `-shots 1600000` and `-shots 7500000` (task T5, 2026-11-04T18:43Z) | `219907cf` |

Both commits lock qiskit 2.6.0, qiskit-aer 0.17.2, qiskit-ibm-runtime 0.50.0,
sqls 67057e4b and quantum_linear_solvers 99231b85; each case's
`q8020_code_*_0.json` records them.

## Layout

- `<arm>/seed<k>/` (or `shots<n>-seed<k>/` in `qsvt_best_bigshot`): one case, the solver's CSVs, metadata pickle, stdout and
  the sweeper and harvester `q8020_*` files. Removed: `*.qpy` circuits and
  `system_Ab_*.pkl` (regenerable).
- `<arm>/seed<k>-unfinished/`: no final results. `hhl_defaults` seeds 4 and 9
  were stopped by the operator after 6 Newton steps; `qsvt_best` seed 3 failed
  in step 1 (a step-0 update left a negative pressure, then a singular Newton
  system); `qsvt_best/seed3-retry/` is its one retry, which failed the same
  way.
- `logs/<run>/`: the run drivers' STATUS files and the sweeper group logs;
  `logs/<run>/sweep/<date>/_<group>/` holds each sweep's metadata
  (`q8020_expanded_cases.json`, `q8020_sweep_meta_*.json`,
  `q8020_sweep_invocation.json` and the run-time TOML copy), added
  2026-11-04 from the node's cleanup.
- `manifest.tsv`: arm, seed, sweeper case id, finished, source path.

The analysed set is seeds 1, 2, 3, 6, 7 per arm; the other finished SQLS
seeds and HHL-defaults seed 8 are kept here and not analysed.
