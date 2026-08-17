# 2026-08-17 — SQLS vs HHL, FVM 1D Euler nozzle (local)

Comparison of the new **SQLS** (SVD-based quantum linear solver, ORNL) linear
solver against the existing **HHL** path in `fvm_euler_1d_solver`, on the same
case and the same qiskit-2.5.2 stack. Only the linear solver differs.

- Run host: Mac laptop `MH-DT9TLJQR2V` (NOT Frontier). Simulator only.
- Case: `-nelem 5 -time_scheme BDF1 -linsolver {SQLS|HHL} -localdt -shots
  150000 -iters 15 -initers 1 -cfl 1e10` (nondim on), ideal statevector.
- SQLS: `-sqls_method full_svd -sqls_repeats 1` (repeats=1 matches HHL's
  single 150k-shot run — see caveat below).
- Stack: qiskit 2.5.2 / aer 0.17.2 / ibm-runtime 0.49.0.
- Integration tracked in `agallojr/qtsuite` #8 → #53; `truncated_mps` follow-up
  is #54.

## Source runs

- SQLS (canonical, repeats=1):
  `results/fvm_euler_1d_solver/2026-08-17-sqls-local-v2/trial_0`
- HHL (same case, qiskit-2.5 local):
  `results/fvm_euler_1d_solver/2026-08-17-qiskit25-local/trial_0`

## Key results

| metric | SQLS (full_svd) | HHL |
|---|---|---|
| circuit qubits | 4 | 14 |
| CX / gates | ~201 CX ({u3,cx}) | 641,145 gates (Aer basis) |
| circuit depth | ~398 ({u3,cx}) | 596,688 (Aer basis) |
| mean time / solve | 0.082 s | 51.70 s |
| total solver elapsed | 0.62 s | 859.34 s |
| Newton iters to converge | 6 | 14 |
| final residual (‖Ax-b‖) | 1.26e-9 | 6.80e-3 |
| pre-tail fidelity | 0.99995–0.99998 | 0.988–0.999 |

SQLS is SVD-based, so it acts on the general non-Hermitian Euler Jacobian
directly — no Hermitian doubling (half the qubits of HHL), no spectral
pre-scale. Magnitude comes back exact from the classically-known `||final_b||`.

## Caveats (load-bearing — read before citing the numbers)

1. **CX/depth bases differ.** SQLS numbers are a `{u3,cx}` synthesis (the
   `count_cx` diagnostic, `-v 2`); HHL numbers are `transpile(circ,
   AerSimulator)` in Aer's own basis, NOT `{u3,cx}`. Depths are not
   like-for-like; the ~3-orders-of-magnitude gap is order-of-magnitude, not
   exact. A true apples-to-apples needs both circuits re-synthesized to
   `{u3,cx}`; HHL's ~1.5 GB `.qpy` circuits were not copied to the results
   tree, so that re-synthesis is not possible from these artifacts.

2. **Why HHL can't skip transpilation (verified).** The raw HHL circuit is 4
   opaque composite blocks `{state-prep, QPE, 1/x, QPE_dg}`; handed to Aer raw
   it crashes with `AerError: unknown instruction`. QPE / 1/x are Qiskit
   abstractions Aer's C++ engine cannot execute — decomposition (the
   ~597k-depth transpile) is mandatory. SQLS's `Initialize` / `UnitaryGate`
   ARE Aer-native, so it runs untranspiled. Intrinsic to the circuits, not a
   wrapper choice.

3. **Shots / repeats.** sqls `quantum_solve` defaults `repeats=10` (averages 10
   independent nshots-reconstructions), so a naive "150k shots" run silently
   does 1.5M measurements — 10× HHL. This comparison uses `-sqls_repeats 1` to
   match. At 150k shots on a 16-state system, pre-tail fidelity was identical
   at repeats 1 vs 10 (~0.99997) — sampling already saturated.

4. **Fidelity tail collapse.** SQLS per-iter fidelity is ~1.0 through the
   penultimate Newton step, then collapses (0.45–0.69, run-dependent) at the
   converged final step — a shots-sampling artifact on a near-zero solution
   update (dQ ~ 1e-11), NOT a solver error (final residual ~1e-9). Statevector
   mode (`-shots 0`) removes it.

## Contents

- `compare_sqls_hhl.py` — reads both runs' CSVs + metadata, emits the two PNGs
  and the comparison table. Uses only numpy + matplotlib (no pandas).
- `sqls_vs_hhl_compare.png` — 4-panel: circuit width, runtime/solve, gate cost,
  fidelity per iteration.
- `sqls_fidelity_collapse.png` — SQLS per-iteration fidelity, tail collapse
  annotated.

Regenerate: `python compare_sqls_hhl.py` (from the fvm venv, which has
numpy/matplotlib). Reads the two source-run dirs by absolute path.

## Related

Conceptual write-up (SQLS mechanics, why HHL must transpile, and how one might
actually quantum-time-step the solver — frozen-Jacobian first): bus research
note `note-20260817-0001-sqls-fvm-quantum-timestep-frozen-jacobian`.
