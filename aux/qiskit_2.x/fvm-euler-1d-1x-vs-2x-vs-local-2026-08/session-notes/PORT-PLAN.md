# Port fvm_euler_1d_solver main (1.x) → 2.x — analysis + mechanical checklist

Analysis done 2026-08-17 (UTC). **No merge performed** — this is the plan only.
Frontier is currently unreachable, so exact April provenance is a best guess
from local git + result metadata (noted where it matters).

Repo: `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver`

---

## Decisions locked with operator

- Target branch for the port = **`archive/qiskit-hhl-2`** (flat layout, matches
  the April run's entry point `./fvm_euler_1d_solver/nozzle_1d_solver.py`). NOT
  `archive/solverfw-v2-port` (that is a later `src/` refactor, out of scope).
- Preferred linear-solver lib = **Q8020-CFD/quantum_linear_solvers**.

---

## DECISION (2026-08-17): Q8020-CFD is canonical; agallojr DEPRECATED

Operator deprecated the `agallojr/quantum_linear_solvers` fork. Going forward,
**`Q8020-CFD/quantum_linear_solvers` is the one canonical fork** for all q8020
work (fvm main, axequalsb, etc.). The analysis below (lineage, drift) is why
this is safe: Q8020-CFD is a functional superset of agallojr with no unique
content lost. jw676 (old-main's 1.x pin) is also superseded.

## quantum_linear_solvers fork lineage (the question asked)

Three forks all share one object history; common upstream root is
`17fb9c0` (2022-09-21 "Initial commit" — the stock qiskit-community
anedumla/quantum_linear_solvers).

Local checkouts:
- agallojr fork: `/Users/agallojr/proj/src/Z-Keep/quantum_linear_solvers`
  (remote `github.com/agallojr/quantum_linear_solvers`, tip `a0d54ca`
  2025-11-08 "vibed port to Qiskit 2.x").
- Q8020-CFD fork: `/Users/agallojr/proj/src/q8020/Z-Keep/quantum_linear_solvers`
  (remote `github.com/Q8020-CFD/quantum_linear_solvers`, tip `66eadf0`
  2026-03-07 "re-add the init constructor").

### Does Q8020-CFD come from agallojr, or from jw676?

**Neither directly. Q8020-CFD did NOT branch off agallojr's 2.x port, and it is
not the jw676 fork.** Verified: `a0d54ca` (agallojr tip) is NOT an ancestor of
`66eadf0` (Q8020 tip). The two 2.x ports are SIBLINGS.

- **Common ancestor of the two forks = `7c57151`** (2025-04-04, "project stuff
  for uv, tried to move to qiskit 2.0 but qiskit-algorithms can't handle it").
  Everything up to and including the 2025-03 qiskit-port groundwork
  (`d4d1872` → `0f32b4e` → `7c57151`, all authored by Andy Gallo) is byte-for-byte
  shared (same SHAs in both forks).
- From that shared base the two forks each did their OWN qiskit-2.x port:
  - agallojr: one commit `a0d54ca` (2025-11-08) — "vibed port to Qiskit 2.x".
  - Q8020-CFD: `f189455` (2025-04-09) → `a94cf63` (2025-04-21) → `7a9b48f`
    (2026-03-07 "port to qiskit 2.3") → `66eadf0` (2026-03-07 "re-add the init
    constructor").
- **jw676**: not checked out locally, so not diffable here. It is the fork the
  1.x `main` pins (`git+https://github.com/jw676/quantum_linear_solvers`, still
  the 1.2.4-era code). It shares the same 2022 upstream root but predates both
  2.x ports. No evidence Q8020-CFD derives from jw676 beyond that shared root.

### How far have the two 2.x forks drifted from each other?

`git diff a0d54ca 66eadf0` — small and localized (76 insertions / 118 deletions
across 11 files; only 7 are source `.py`):

| file | Δ | nature |
|---|---|---|
| `linear_solvers/hhl.py` | +10 / −76 | **biggest**: Q8020 strips the dead Estimator/Sampler/`quantum_instance` machinery agallojr kept as no-op stubs; uses `PhaseEstimation` (class) vs agallojr `phase_estimation`; both use `qc.initialize(...)` |
| `linear_solvers/linear_solver.py` | +13 / −1 | minor API |
| `matrices/tridiagonal_toeplitz.py` | +3 / −8 | Q8020 uses `qc.initialize`, drops `StatePreparation` import |
| `observables/absolute_average.py` | +4 / −5 | import cleanup |
| `observables/matrix_functional.py` | +9 / −9 | import/name churn |
| `test/test_linear_solvers.py` | +3 / −6 | test updates |
| `setup.py`, `pyproject.toml`, `.python-version`, README | pkg metadata | Q8020 keeps a `requirements.txt-LEGACY` |

**Bottom line on drift:** the two 2.x forks are close cousins off the same
2025-03/04 base; the only substantive code difference is that Q8020-CFD is the
**cleaner** port (removed the vestigial pre-2.x Estimator/Sampler plumbing that
agallojr left as inert stubs). Both converge on the same 2.x idioms
(`qc.initialize`, `PhaseEstimation`, `ExactReciprocal`, statevector expectation).

### Provenance caveat (April run)

The April 2026 run recorded only `quantum-linear-solvers==0.1.0` (no fork URL).
The fvm `archive/qiskit-hhl-2` branch pins **agallojr/quantum_linear_solvers**,
so the April sweep most likely used the **agallojr** fork, not Q8020-CFD.
Since the operator prefers Q8020-CFD for the port, expect a lib swap from what
April actually ran — behavior should match (the ports are near-equivalent), but
this is the one spot where "reproduce April exactly" and "use preferred lib"
diverge. Cannot confirm against Frontier right now.

---

## Mechanical checklist (what has to happen — do NOT execute yet)

### A. quantum_linear_solvers (the dependency) — settle it first
1. Choose canonical fork = **Q8020-CFD** (`66eadf0`). Confirm it is pushed /
   reachable at `github.com/Q8020-CFD/quantum_linear_solvers` before pinning.
2. (Optional) Fold agallojr-only value into Q8020 if any — diff shows none of
   substance beyond the stub cleanup, so likely nothing to port over.
3. Confirm Q8020 tip installs into a clean 2.x venv and its `test/` passes.

### B. fvm_euler_1d_solver code — move 2.x onto main
4. Diff `main` (`60d973c5`) vs `archive/qiskit-hhl-2` (`9e76e398`) to catalog
   main-only commits since the branch point (main got Mohammad's steady-mode /
   plotting / timing-metadata work; qiskit-hhl-2 got the `c94889b1` "port to
   qiskit 2.x"). Decide merge direction:
   - Preferred: bring the 2.x port commits from `qiskit-hhl-2` onto `main` while
     KEEPING main's later solver features (steady mode, qc_metadata timing, etc).
     This is a real merge/rebase with conflict resolution, not a fast-forward —
     the two lines diverged.
5. Replace/author `nozzle_1d_solver.py` + supporting modules with the 2.x import
   idioms (no `qiskit-algorithms` opflow, `qc.initialize`, `PhaseEstimation`,
   `ExactReciprocal`, statevector expectation) as on `qiskit-hhl-2`.

### C. requirements / packaging on main
6. Rewrite `requirements-quantum.txt` on main:
   - FROM: `quantum_linear_solvers @ git+.../jw676/...`, `qiskit==1.2.4`,
     `qiskit-aer==0.15.1`, `qiskit-algorithms==0.3.1`,
     `qiskit-ibm-runtime==0.35.0`, `qiskit-qasm3-import==0.5.1`, `qiskit-iqm==18.0`
   - TO: `quantum_linear_solvers @ git+.../Q8020-CFD/...`, `qiskit>=2.3.0`,
     `qiskit-aer>=0.17.2`, `qiskit-ibm-runtime>=0.45.1`,
     `qiskit-qasm3-import>=0.6.0` (drop `qiskit-algorithms`; drop/relax
     `qiskit-iqm`). Keep the old combo as a commented "legacy known-good" block.
   - Reference target already exists on `archive/solverfw-v2-port`'s
     `requirements-quantum.txt` (commit `2b63f6f7`) — reuse its pin set, but
     point the lib at Q8020-CFD (it already does).
7. Reconcile `pyproject.toml` (and `setup.py` if kept) to the same pins so they
   don't contradict `requirements-quantum.txt` (that contradiction is exactly
   what `2b63f6f7` fixed on the v2 branch).

### D. verify
8. Fresh venv (`./venv` or `.venv`), install 2.x stack + Q8020-CFD lib.
9. Run the small smoke case: `nelem=5`, `-linsolver HHL`, statevector, few iters;
   confirm it solves and HHL fidelity ≈ 1 on the small system (matches the
   `2b63f6f7` verification note: "x = direction*scale reproduces the classical
   solution, fidelity 1.0").
10. (If wanted) re-run the 150k-shot nelem=5 cfl=1e10 case and sanity-check
    against the April numbers in this folder's `summary.json`.

### E. commit / pins — REQUIRES EXPLICIT OPERATOR GO-AHEAD
11. Commit on `main` (do not branch unless asked).
12. No submodule pin chain applies here (fvm repo is standalone, not under the
    bus→product nesting).

---

## Key SHAs (quick reference)

- fvm main tip: `60d973c5` (1.x)
- fvm 2.x source branch: `archive/qiskit-hhl-2` tip `9e76e398`; port commit
  `c94889b1` "port to qiskit 2.x"
- fvm v2 refactor (reference for reqs only): `archive/solverfw-v2-port`
  tip `2b63f6f7`
- QLS agallojr tip: `a0d54ca`;  QLS Q8020-CFD tip: `66eadf0`;
  QLS shared ancestor: `7c57151`;  QLS upstream root: `17fb9c0`
