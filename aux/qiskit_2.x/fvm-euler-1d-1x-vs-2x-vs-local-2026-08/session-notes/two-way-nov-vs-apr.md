# FVM Euler 1D — qiskit 1.x vs 2.x, apples-to-apples

> ARCHIVED SESSION NOTE (moved 2026-08-17 from
> `research-notes/bus/agent-tmp/fvm-euler-1d-qiskit-1x-vs-2x/README.md`). This is
> the ORIGINAL two-way (Nov vs Apr) study plus the port RESULTS section. The
> current three-way write-up (adds the local 2.3-port run) is the `README.md` one
> level up. Paths below that point at the fvm repo are still valid; the
> `local-run-2026/` raw dir referenced in RESULTS remains at its agent-tmp
> location, and a `.qpy`-stripped copy is in the results tree under
> `results/fvm_euler_1d_solver/2026-08-17-qiskit23-local/`.

Comparison of the **base FVM** HHL nozzle case (not LuGo) run under two qiskit
stacks. Both groups are the SAME case: identical IC/BC and evolution params,
`ideal_statevector` backend, **150000 shots**, `nelem=5`, on **Frontier**.

Goal: isolate the impact of the qiskit stack (library + ported HHL code) on
circuit size, timing, and solution quality, holding the physics case fixed.

- Generated: 2026-08-17 (UTC).
- Data source: `q8020-cfd-experiments/results/fvm_euler_1d_solver/`.
- Regenerate the numbers: `python3 gather.py` (read-only; writes `summary.json`).

---

## Links to the experiment/results

### Nov 2025 — qiskit 1.2.4 (10 matched trials)
Group dir (150k-shot repeats of the identical case):
`/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/results/fvm_euler_1d_solver/2025-11-11/shots_150000/`

Representative single trial (the one used in the earlier HHL-Qrisp writeup):
`/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/results/fvm_euler_1d_solver/2025-11-11/shots_150000/trial_5_9e98b39b/`

Sibling copy of the same trials (harvested view):
`/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/results/fvm_euler_1d_solver/2025-11-11/harvest_n5_150k/`

Pinned stack for this run:
`/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/results/fvm_euler_1d_solver/2025-11-11/requirements-quantum.txt`

### Apr 2026 — qiskit 2.3.1 (3 matched trials)
Group dir (the `cfl=1e10` steady-state trials inside the CFL time-step sweep):
`/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/results/fvm_euler_1d_solver/2026-04-05/_52d087d1/time_steps_4/`

The 3 matched (base-FVM HHL, cfl=1e10, 150k) trials:
- `.../2026-04-05/_52d087d1/time_steps_4/trial_0_b9da8a4e/`
- `.../2026-04-05/_52d087d1/time_steps_4/trial_5_883b9fa8/`
- `.../2026-04-05/_52d087d1/time_steps_4/trial_7_203b7613/`

> Note: `time_steps_4/` holds 10 trial dirs, but only these 3 are base-FVM HHL
> at cfl=1e10 / 150k statevector; the rest are other CFL points or non-HHL.
> **We have more Nov trials (10) than April (3)** at this exact operating point.

---

## Case fingerprint — proof this is apples-to-apples

Every field in the case JSON is byte-identical across the two groups
(diffed `q8020_case_*.json`; zero differences):

| field | value (both groups) |
|---|---|
| name / nelem | `nozzle_1d` / 5 |
| area_equation | `A(x) = 1.398 + 0.347*tanh(0.8*x - 4)` |
| reference_values | rho_ref=1.0, u_ref=1.5, p_ref=2.25 |
| time_scheme | BDF1 |
| cfl | 1e10 (pseudo-transient driven to steady state) |
| max_iters / max_inner_iters | 15 / 1 |
| conv_tol / res_tol | 1e-10 / 0.01 |
| localdt / nondim | true / true |
| backend | ideal_statevector, noise=false, 150000 shots |
| algorithm | HHL (base FVM, not LuGo) |

**Hard confirmation:** the iteration-0 outer residual is
`12.375368413827264` in BOTH groups, to all printed digits. That means the
classical FVM discretization and the assembled linear system `Ab` are
identical — the only moving parts downstream are the qiskit stack (library +
ported HHL code) and the shot RNG. No LuGo trials exist in any of these runs
(`algorithm` is `HHL` everywhere; grep for "lugo" across the trees returns
nothing).

The one non-identical downstream input is the HHL condition-number *range*
(Nov ≈ 58–96, Apr ≈ 66–96) — expected, since the range is measured over the
15 solves and each solve's `b` vector drifts with the (stochastic) iterate.
The system size is identical: original 15 → padded 16 → hermitian 32.

---

## Library / software stack (notated)

| | Nov 2025 | Apr 2026 |
|---|---|---|
| qiskit | **1.2.4** | **2.3.1** |
| qiskit-aer | 0.15.1 | 0.17.2 |
| qiskit-ibm-runtime | 0.35.0 | 0.46.1 |
| qiskit-algorithms | 0.3.1 | (dropped in 2.x port) |
| quantum-linear-solvers | jw676 fork (1.x) | Q8020-CFD fork 0.1.0 (2.3 port) |
| numpy | 2.2.4 (known-good) | 2.4.4 |
| scipy | 1.14.1 (known-good) | 1.17.1 |
| python | 3.x | 3.12.9 |

Nov stack: pinned in `2025-11-11/requirements-quantum.txt` (qiskit==1.2.4,
aer==0.15.1, algorithms==0.3.1, ibm-runtime==0.35.0, qasm3-import==0.5.1,
iqm==18.0); numpy/scipy known-good in `requirements.txt`. The Nov result dirs
have no per-trial env snapshot JSON — the stack comes from the pinned reqs.

Apr stack: captured live per-trial in
`q8020_env_before_*.json` / `q8020_env_after_*.json`.

**Caveat — not a pure library swap.** The 2.x path also carries a *code port*:
quantum_linear_solvers moved from the jw676 fork to the Q8020-CFD fork (needs
`ExactReciprocalGate`, absent in 1.2.4) and dropped qiskit-algorithms. So this
is "same case, same shots, different (qiskit stack + ported HHL code)"; the
library and the port cannot be fully separated from these runs alone.

---

## Host (where the runs happened)

| | Nov 2025 | Apr 2026 |
|---|---|---|
| Compute host | **Frontier** (OLCF) | **Frontier** compute node `frontier02013` |
| Evidence | experiment name `frontier_nelem5`; metadata is a `harvest` onto Mac `MH-DT9TLJQR2V` on 2026-02-09 | `sweep` metadata records `hostname=frontier02013`; sbatch: `-A ard189 -N 50 -C nvme -p batch` |
| Run timestamp | run Nov 2025; harvested 2026-02-09T19:52:53Z | 2026-04-05T06:10:51Z → 06:50:06Z |

Both ran on Frontier, so the timing comparison below is on comparable hardware.
The Nov `hostname` field (`MH-DT9TLJQR2V`) is the *harvest* host (a Mac that
post-processed the Frontier output), NOT the compute host — the experiment name
`frontier_nelem5` is the tell.

---

## Circuit stats — side by side (transpiled, per HHL solve)

The linear system is identical: original 15 → padded 16 → hermitian 32,
condition number ≈ 58–96. Circuit **width is the same**; the 2.x transpile is
slightly **smaller** in depth.

| metric | Nov 1.x | Apr 2.x | ratio (1.x / 2.x) |
|---|---|---|---|
| qubits (transpiled) | 14 | 14 | 1.0 |
| transpiled depth | 689,027 | 638,237 | 1.08× deeper on 1.x |
| transpiled gate count | 689,127 | 649,089 | 1.06× more on 1.x |
| pre-transpile depth | 5 | 5 | — |

## Timing — side by side (per-iteration wall time, mean ± std over trials)

| stage | Nov 1.x (s/iter) | Apr 2.x (s/iter) | speedup 2.x |
|---|---|---|---|
| circuit **generate** | 253.0 ± 19.5 | 63.1 ± 3.1 | **~4.0×** |
| **transpile** | 43.2 ± 3.2 | 7.2 ± 0.4 | **~6.0×** |
| **execute** (aer sim) | 61.7 ± 4.6 | 40.0 ± 2.3 | **~1.5×** |
| total run (15 iters) | 5369.6 ± 408 | 1653.6 ± 86 | **~3.2×** |

The 2.x stack is dramatically faster at building and transpiling the circuit,
modestly faster at simulating it — consistent with the earlier finding that the
2.x win is **runtime, not algorithm**.

## Solution quality — side by side (mean ± std over trials)

| metric | Nov 1.x (n=10) | Apr 2.x (n=3) |
|---|---|---|
| final outer residual (iter 14) | 0.074 ± 0.135 (min 1.7e-5, max 0.46) | 0.112 ± 0.088 (min 2.1e-4, max 0.22) |
| mean HHL l2_error_normalized | 0.101 ± 0.046 | 0.089 ± 0.036 |
| mean HHL fidelity | 0.985 ± 0.015 | 0.990 ± 0.008 |

**Quality is statistically indistinguishable.** The per-trial scatter (shot RNG)
is larger than the gap between the two stacks — Nov's final residual alone
ranges over 4 orders of magnitude across its 10 repeats. On the cleaner HHL
solve-quality metrics (fidelity, l2_error_normalized) the two stacks are
essentially equal, with 2.x nominally a hair better. With only 3 April trials
this is not enough to claim any real quality difference either way.

---

## Methodology note — a trap we hit, so it isn't repeated

The first pass compared ONE Nov trial (`trial_5_9e98b39b`) against ONE April
trial (`trial_0_b9da8a4e`) and the April residual history looked ~4× worse at
every iteration — a tidy but WRONG story. Both are single stochastic draws
(150k-shot sampling of the statevector, different RNG per trial), and Nov's own
10 repeats span final residual 1.7e-5 → 0.46. Comparing single trials measures
shot noise, not the qiskit stack. The tables above therefore aggregate over all
matched trials per group; the per-trial detail lives in `summary.json`.

Two consequences to keep in mind:
- Quality conclusions rest on n=10 (Nov) vs n=3 (Apr) — the April sample is
  thin. Treat the quality verdict as "no evidence of a difference," not "proven
  equal."
- Timing/circuit-size conclusions are robust: gate count and transpiled depth
  are deterministic (std=0 across trials), and per-iteration timings are tight
  (Apr ~5% CoV), so the ~3–6× speedups are real, not noise.

---

## Related prior analysis and the migration record

- Earlier prose comparison (Nov Frontier vs a Mar 2026 local re-run at qiskit
  2.3.0 — same nozzle case, different date than the April sweep):
  `/Users/agallojr/proj/src/q8020/Z-Keep/q8020-cfd-docs/pamphlets/analysis/code-HHL-Qrisp.md`
  Its conclusion matches ours: the 2.x jump is a large *runtime* win (~14×
  gen/transpile, ~5× execute in that comparison), negligible depth change, and
  numerically consistent results; "LuGo" is where circuit depth actually drops.
- The 1.x→2.x port itself (breaking changes, dropped qiskit-algorithms, the
  missing `ExactReciprocalGate` in 1.2.4, legacy-vs-2.3 pin sets) is documented
  in the FVM repo commit messages, not a standalone doc:
  repo `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver`, commits
  `c94889b1` ("port to qiskit 2.x") and `2b63f6f7` ("Point quantum reqs at the
  Q8020-CFD fork + qiskit 2.3+"), on branches `archive/qiskit-hhl-2` and
  `archive/solverfw-v2-port`.
- Current `main` of that repo still pins the OLD stack (qiskit==1.2.4); the
  2.3+ reconciliation was never merged to main — it lives on the archive
  branches above.

---

## Bottom line

Holding the physics case, backend, and shot count fixed:

- **Circuit width identical (14 qubits); 2.x transpiled ~6–8% shallower/lighter.**
- **2.x is ~3–6× faster** at circuit generation and transpilation, ~1.5× at
  execution, ~3× faster end-to-end.
- **Solution quality unchanged** within shot noise; the qiskit jump bought
  speed, not accuracy.
- These runs conflate the qiskit **library** bump with the **HHL code port**
  (fork change + dropped qiskit-algorithms), so attribute the speedup to the
  combined 2.x stack, not qiskit alone.

`summary.json` holds the full per-trial breakdown behind these tables.

---

## RESULTS — main ported to Qiskit 2.3 (2026-08-17 UTC)

Executed the non-gated steps of `STEPS-q8020-main-to-2.3.md` on
`/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver` (branch `main`, tip was
`60d973c5`). **No git commit performed** (gated to operator). The long HHL
validation run (STEPS step 5) is also GATED and was NOT launched.

### What changed on main

- **Code reconciliation** (main was already 2.x-idiomatic; brought low-risk
  refinements from `archive/qiskit-hhl-2`, KEEPING main's `FakeProviderForBackendV2`):
  - `math_tools.py`: added global verbosity (`_GLOBAL_VERBOSITY`, `set_verbosity`,
    `get_verbosity`); `convert_to_pow2` / `convert_system_to_herm` /
    `scale_Ab_by_spectral_radius` now default `verbosity=None` → global.
  - `quantum_tools.py`: import `get_verbosity`; `QuantumHHL.__init__` honors
    `verbosity=None`. Fake-backend block left as main had it (general provider).
  - `space_solvers.py`: plot save now guarded by `self.savedata`.
  - `nozzle_1d_solver.py`: `-savedata` / `-checkpoint` / `-resume` /
    `-original_max_iters` flags; `-v/-verb/-verbosity`; sets global verbosity;
    backend quoted-string split; checkpoint save per outer iter + resume;
    converged banner; `elapsed_offset`.
  - `checkpoint_tools.py`: NEW file (checkpoint save/load/restore/find/final).
- **Packaging (uv-native, new on main):**
  - `pyproject.toml`: qiskit stack is a CORE dependency (not an optional extra —
    operator decision), pinned to April's exact stack; `qiskit-algorithms`
    omitted (Q8020-CFD ships its own AlgorithmResult). pyproject + uv.lock is the
    single source of truth.
  - `.python-version` = 3.12; `uv.lock` generated (50 pkgs; QLS pinned by SHA
    `66eadf0`). Install with `uv sync` (or `pip install .`).
  - `requirements.txt` / `requirements-quantum.txt`: **DELETED** (deprecated —
    operator decision; pyproject is authoritative). README + docs
    (`QUICKSTART_PARALLEL.md`, `FRONTIER_CONDA_SETUP.md`) updated from
    `pip install -r requirements*.txt` to the uv/pyproject workflow.

### Dependency pins (was → now, on main)

| pkg | old main (1.x) | new main | April run |
|---|---|---|---|
| quantum_linear_solvers | jw676 fork | **Q8020-CFD @ 66eadf0** | agallojr (deprecated) |
| qiskit | ==1.2.4 | **==2.3.1** | 2.3.1 |
| qiskit-aer | ==0.15.1 | **==0.17.2** | 0.17.2 |
| qiskit-ibm-runtime | ==0.35.0 | **==0.46.1** | 0.46.1 |
| qiskit-qasm3-import | ==0.5.1 | **>=0.6.0** (0.6.0) | — |
| qiskit-algorithms | ==0.3.1 | **dropped** | dropped |
| qiskit-iqm | ==18.0 | **dropped** | — |

The three named qiskit packages are pinned to April's EXACT versions
(2.3.1 / 0.17.2 / 0.46.1) for reproducibility, not `>=` ranges. All of the above
are declared as CORE `[project].dependencies` in `pyproject.toml` (not an
optional extra).

### Validation env (uv-managed `.venv`, Python 3.12.10)

Resolved set: qiskit 2.3.1, qiskit-aer 0.17.2, qiskit-ibm-runtime 0.46.1,
qiskit-qasm3-import 0.6.0, quantum-linear-solvers 0.1.0 (Q8020-CFD @ 66eadf0),
numpy 2.5.2, scipy 1.18.0, matplotlib 3.11.1. `qiskit-algorithms` confirmed
ABSENT.

### Verification done (non-gated)

- All main modules import under the 2.3.1 venv, including `from linear_solvers
  import HHL`.
- 1.x-only symbol sweep (`opflow`, `qiskit_algorithms`, `QuantumInstance`,
  `StatePreparation`, `primitives.Sampler`, `from qiskit import execute`):
  **none** in any `.py`.
- All edited modules byte-compile; project installs as `fvm-euler-1d-solver 0.1.0`.
- Classical LU smoke (nelem=5, cfl=1e10, BDF1, few iters) runs end-to-end;
  **iteration-0 residual = 12.375368413827264**, byte-identical to the documented
  case fingerprint — classical discretization untouched.

### Still GATED (operator runs, not launched here)

1. The 150k-shot HHL validation run matching April
   `.../2026-04-05/_52d087d1/time_steps_4/trial_0_b9da8a4e` — long (~25-30 min on
   a laptop; overlay rule 6). Command is in STEPS step 5.
2. `git add/commit` on main (STEPS step 7). Suggested split: (a) code
   reconciliation, (b) repin/packaging. fvm repo is standalone — no submodule
   pin chain.

Note: the `q8020-cfd-axequalsb` docstring fix (STEPS step 3) was SKIPPED — it
lives in a separate repo, out of scope for this port (operator confirmed).
