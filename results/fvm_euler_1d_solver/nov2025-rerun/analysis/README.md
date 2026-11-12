# nov2025-rerun analysis

Regenerate: `python3 -I load_runs.py .. cases.csv && python make_plots.py` (pandas + matplotlib).

- `cases.csv` – one row per case (465), built from raw case files so the
  file-only `LuGo-rerun` is included. Columns: shots, steps, final residual,
  converged flag, final-Mach relL2 vs exact, per-step transpile/generate/run
  times, transpiled depth, wall time (sweeper metadata only).
- `summary_by_config_shots.csv`, `summary_exact_case.csv` – medians per config.
- `figures/01..07_*.png`.

## Configs
| label | source | notes |
|---|---|---|
| HHL qiskit1.2.4 | `nov_pkgs` | the 11-04 and 11-05 sweeps pooled as replicates (up to 20 trials per shot count; 11-03 died on disk quota, no results) |
| HHL qiskit2.5.2 11-05 | `new_pkgs` | same solver commit, upgraded packages |
| HHL+LuGo nelem5 | `LuGo-rerun` | file-only, no sweeper wall time. Its nelem10 cases are in `cases.csv` but left out of the tables and plots, which are all nelem 5. |
| SQLS | `sqls_aiaa4q26` | 11-05 sweep only. The 11-04 sweep is numerically identical (seeded), so it is left out of tables and plots but kept in `cases.csv`. |

Definitions: *converged* = stopped before the 15-step cap with residual < 1e-6.
Error = relL2 of final Mach vs the exact (shots=0) HHL case of the same nelem.
SQLS "depth" is `fb_depth` (a different compile path) - not comparable with HHL depth.

Transpile settings: the HHL solver calls `transpile(circ, backend)` with no optimization level
(`quantum_tools.py` at `ef7f0a8b`, ideal-backend branch), so each stack uses qiskit's default: level 1 on
qiskit 1.2.4, level 2 on 2.5.2 and 2.6.2 (checked in each version's `transpiler.py`). No `QISKIT_SETTINGS`
override is in the sweep TOMLs, and nothing records the level in the metadata. LuGo's runs were written by
qiskit 2.6.1 (qpy header); its transpile call isn't in this repo. SQLS's `fb_depth` is a separate level-0
`{u3,cx}` count. Figures 03, 04, 05, 05b and 07 carry a footnote about this.

## Findings
1. **Convergence.** All HHL and HHL+LuGo shot cases hit the 15-step cap (0 converged).
   Final residual falls roughly as shots^-0.5 to -1 (about 1 at 1k shots to 1e-2
   at 150k) but never reaches the exact-case 9e-11. All 70 SQLS shot cases
   converge, in 12 steps at 500 shots down to 7 at 150k.
2. **Final-state error.** HHL: median relL2 about 2e-2 at 1k shots, 1e-3 at 10k+. SQLS is about 6e-12 at every shot count
   (Newton fixed point is independent of linear-solve noise once converged).
3. **Wall time.** HHL about 85-110 min per case, flat in shots, because the 15 steps of
   circuit work dominate. SQLS about 7-9 s per case, roughly 700x faster.
4. **qiskit 1.2.4 to 2.5.2** (exact case, summed over 8 steps): generate 2029 s to 365 s,
   transpile 343 s to 1980 s (about 6x slower), run 1280 s to 883 s, transpiled depth 689,026 to 598,727,
   sum of depth 5.17M to 4.48M. Wall time 67 to 55 min. Net about 18% faster; transpile is now the bottleneck.
5. **LuGo circuits are far shallower**: step-0 depth 19.5k vs 689k (35x), generate 16 s vs 2029 s, circuit
   time about 230 s vs 3300 s for the exact case. Residual and accuracy at equal shots are similar to plain HHL, so
   it still does not converge under shot noise.
6. **Reliability / completeness.** Two HHL cases crashed with `numpy.linalg.LinAlgError: Singular matrix`
   (new_pkgs `shots_4/trial_5`; nov_pkgs 11-05 `shots_0/trial_7`). Cases with a residual file: nov_pkgs 11-04 = 68 (+1 exact
   in `_b08c0b8d`), nov_pkgs 11-05 = 67, new_pkgs = 70, SQLS = 71 each. LuGo has 56 (nelem5) and 61 (nelem10, not plotted) case
   directories, against the 70+1 you would expect for 7 shot counts x 10 trials + exact; I did not check why.
