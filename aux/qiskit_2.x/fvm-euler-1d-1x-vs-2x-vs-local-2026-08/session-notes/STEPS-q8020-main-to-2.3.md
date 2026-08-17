# Make q8020 fvm_euler_1d_solver `main` the Qiskit 2.3 version

Repo: `/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver`
Written 2026-08-17 (UTC). **No changes made yet.** Frontier unreachable, so
local validation is a best-effort sanity check vs the stored April run, with
known version drift.

---

## Key correction from earlier discovery

**Main's Python code is ALREADY Qiskit-2.x-idiomatic.** This is not a code
port — it is mostly a **repin + a code-consistency reconciliation** against
`archive/qiskit-hhl-2`.

Evidence:
- The commit `c94889b1` "port to qiskit 2.x" touched **only packaging** (setup.py,
  pyproject.toml, requirements*, uv.lock, .python-version) — **zero `.py` files**.
- Scanned every `.py` on `main` for 1.x-only symbols (`opflow`,
  `qiskit_algorithms`, `QuantumInstance`, `execute`, `StatePreparation`,
  `primitives.Sampler`, ...): **none found**.
- Main's `quantum_tools.py` already imports `SamplerV2`, `from linear_solvers
  import HHL`, `qiskit.quantum_info.Statevector/state_fidelity` — all 2.x.
- Main's `HHL(quantum_instance=self.backend)` call is compatible with the
  Q8020-CFD lib: its `HHL.__init__` still accepts `quantum_instance=`/`expectation=`
  (ignored, kept for backward compat).

**What's actually wrong with main:** its dependency pins still say 1.x
(`requirements-quantum.txt`: `jw676` fork + `qiskit==1.2.4`, aer 0.15.1,
algorithms 0.3.1, ibm-runtime 0.35.0). So the code is 2.x but the declared
environment is 1.x — inconsistent and misleading.

---

## Branch topology (main vs archive/qiskit-hhl-2)

- Merge-base: `a5317f2b` (2025-11-11).
- `main` tip `60d973c5` (2026-08-17). Main-only work: `60d973c5` "Deliver
  feature/qiskit-hhl to main" (docs/, post_process/plot_comparison.py, ref_sol
  CSVs, helper_tools enhancements) + `4314eba4` scaling updates.
- `qiskit-hhl-2` tip `9e76e398` (2025-11-23). Branch-only work (7 commits):
  `c94889b1` 2.x pins, `bdc8e3fa` fake-backend rework (FakeBrisbane/FakeTorino),
  `8f1f816d` per-outer-iteration checkpointing, `9f243fa3` verbosity globals,
  plot args, and Mohammad's steady-mode/plotting/timing merge.

The two genuinely diverged. `git diff main archive/qiskit-hhl-2` differs in:
`.python-version, README.md, checkpoint_tools.py (+80), math_tools.py (verbosity
globals), nozzle_1d_solver.py, pyproject.toml, quantum_tools.py (fake-backend +
verbosity), requirements*.txt, setup.py, space_solvers.py, uv.lock`.

So "make main consistent with qiskit-hhl-2" = reconcile these code deltas, not
just swap pins.

---

## STEPS

### 0. Prep (safe, read-only-ish)
1. `cd /Users/agallojr/proj/src/q8020/fvm_euler_1d_solver`; confirm clean tree
   (`git status`). Do NOT branch (operator rule) — work on `main` directly, or
   ask if a working branch is wanted.
2. Fetch latest: `git fetch origin` (no push).

### 1. Reconcile main's code with qiskit-hhl-2 (consistency)
Scope is SMALL — main's code is already 2.x. Operator decisions:
- **Keep main's general fake backend (`FakeProviderForBackendV2`).** Do NOT take
  the branch's `FakeBrisbane`/`FakeTorino` rework — the general provider is
  preferred. This removes the largest `quantum_tools.py` conflict hunk.

3. Produce the authoritative per-file diff:
   `git diff main origin/archive/qiskit-hhl-2 -- '*.py'` and review each hunk.
4. Bring only the low-risk 2.x refinements onto main, KEEPING main's delivered
   features (docs, post_process, ref_sol, helper_tools) AND main's fake-backend:
   - `math_tools.py`: take the global-verbosity block
     (`_GLOBAL_VERBOSITY`, `set_verbosity`, `get_verbosity`) and the
     `verbosity=None` defaults the branch added.
   - `quantum_tools.py`: take ONLY the `verbosity=None → get_verbosity()`
     default and the `get_verbosity` import. LEAVE the fake-backend block as
     main has it (`FakeProviderForBackendV2`).
   - `checkpoint_tools.py`, `nozzle_1d_solver.py`, `space_solvers.py`: take the
     branch deltas (per-outer-iter checkpointing, arg plumbing) only where they
     don't regress main's delivery. If a hunk is entangled with the fake-backend
     change, keep main's side.
   - Given the fake-backend carve-out, hand-apply the wanted hunks rather than a
     blanket cherry-pick of `bdc8e3fa` (that commit is the fake-backend rework —
     skip it). `9f243fa3` (verbosity) and `8f1f816d` (checkpointing) are
     cherry-pick candidates if they apply cleanly. SKIP `c94889b1` (pins,
     superseded by step 2).
5. Confirm no 1.x-only symbol reappeared: re-grep all `.py` for `opflow`,
   `qiskit_algorithms`, `QuantumInstance`, `execute`, `StatePreparation`.

### 2. Repin to Qiskit 2.3 + Q8020-CFD lib — go uv-native (operator: YES to uv)
Rationale for uv: main has NO packaging today, so we're authoring it regardless;
uv is the direction the 2.x branch already took (`c94889b1` added `uv.lock`);
and a fresh lock gives DETERMINISTIC, reproducible pins going forward (uv locks
the git lib by commit SHA — better than a bare `@ git+` pin). It won't
retro-match April's exact patch versions, but it makes THIS port reproducible.

6. Author `pyproject.toml` on main as the single source of truth (uv-managed):
   - core deps in `[project].dependencies`: numpy, scipy, matplotlib (from
     current `requirements.txt`).
   - quantum deps in an optional extra `[project.optional-dependencies].quantum`:
     ```
     quantum_linear_solvers @ git+https://github.com/Q8020-CFD/quantum_linear_solvers
     qiskit>=2.3.0
     qiskit-aer>=0.17.2
     qiskit-ibm-runtime>=0.45.1
     qiskit-qasm3-import>=0.6.0
     ```
     Omit `qiskit-algorithms` — main's code does not import it (verified). Add it
     back only if a transitive resolution demands it. Drop `qiskit-iqm` (no IQM).
   - `requires-python = ">=3.12,<3.14"` and add `.python-version` (3.12).
7. `uv lock` to generate a fresh `uv.lock` (do NOT copy the branch's 1.x-era
   lock). This resolves qiskit 2.3.x + pins the Q8020-CFD lib by SHA.
8. Keep `requirements-quantum.txt` + `requirements.txt` as THIN MIRRORS of the
   pyproject extras (the Frontier venv-packing / sbatch flow reads requirements
   files, not pyproject). Set them to the same 2.3 set; keep the old 1.x combo
   as a commented "Legacy known-good set" block. Add a one-line header noting
   pyproject.toml/uv.lock is authoritative and these mirror it.
   - Reference already-authored 2.3 reqs:
     `archive/solverfw-v2-port:requirements-quantum.txt` (`2b63f6f7`).
9. Note: main's HHL call passes `quantum_instance=` — fine with Q8020-CFD (arg
   accepted, ignored for backward compat; verified in lib `hhl.py`).

### 3. Settle the dependency lib (Q8020-CFD) — DECIDED
**Q8020-CFD is the canonical quantum_linear_solvers fork going forward.** The
agallojr fork is DEPRECATED (operator, 2026-08-17). No lib tension remains:
main will pin Q8020-CFD, superseding both jw676 (old main) and agallojr
(qiskit-hhl-2 branch). qiskit-hhl-2 pinned agallojr, so main will intentionally
DIVERGE from the branch on the lib pin only — code stays consistent.
8. Confirm `github.com/Q8020-CFD/quantum_linear_solvers` is reachable/pushed at
   the intended tip (`66eadf0`). Local checkout for reference:
   `/Users/agallojr/proj/src/q8020/Z-Keep/quantum_linear_solvers`.
9. Fix the one stale live reference to the deprecated fork:
   `q8020/q8020-cfd-axequalsb/src/ax_equals_b_hhl.py:13` docstring says
   "from agallojr/quantum_linear_solvers" while its pyproject already pins
   Q8020-CFD — update the comment. (Z-Keep references are holding-area; leave.)

### 4. Local validation env (uv; base rule 6: use the local venv)
10. `cd /Users/agallojr/proj/src/q8020/fvm_euler_1d_solver`
11. `uv sync --extra quantum` (creates `.venv`, installs from pyproject +
    uv.lock: Q8020-CFD lib from git + qiskit 2.3.x).
12. Record resolved versions: `uv pip freeze | grep -iE 'qiskit|numpy|scipy'`.
    Expect drift from April's exact 2.3.1 / aer 0.17.2 (we pin `>=`) — capture
    the actual resolved set into the RESULTS note so the comparison is honest.

### 5. Run the validation case (GATED — operator runs, do not auto-launch)
The apples-to-apples case matching the stored April run
(`.../results/fvm_euler_1d_solver/2026-04-05/_52d087d1/time_steps_4/trial_0_b9da8a4e`):
```
uv run python nozzle_1d_solver.py \
  -nelem 5 -time_scheme BDF1 -linsolver HHL -localdt -noshow \
  -shots 150000 -iters 15 -initers 1 -cfl 10000000000.0 \
  -outdir /Users/agallojr/proj/src/research-notes/bus/agent-tmp/fvm-euler-1d-qiskit-1x-vs-2x/local-run-2026
```
13. **This is a long single run (~25-30 min at 15 iters on a laptop; April's
    per-trial total was ~1653 s on a Frontier node). Per overlay rule 6 it is
    gated — hand the command to the operator, do NOT launch it (nor in the
    background).** Optional fast smoke first: `-iters 3` (confirm with operator;
    if >60s it is still gated).

### 6. Compare to stored April run (first-class deliverable)
The comparison IS a goal, not a footnote. Reuse the harness already in this
folder: `gather.py` reads the q8020 result schema (`q8020_artifacts_*.json`
transpile_passes, `hhl_metrics_*.csv`, `residual_*.csv`). The local run writes
the SAME artifact files, so point a small variant of gather.py at the
`local-run-2026/` dir and at `.../time_steps_4/trial_0_b9da8a4e/`.

14. Build a side-by-side table (local 2026-08 vs April `trial_0_b9da8a4e`, and
    vs the April 3-trial aggregate in `summary.json`):
    | metric | source field | April (stored) | Local (new) |
    |---|---|---|---|
    | qubits (transpiled) | artifacts.transpile_passes[].after.num_qubits | 14 | ? |
    | transpiled depth | ...after.depth | 638,237 | ? |
    | transpiled gate count | ...after.gate_count | 649,089 | ? |
    | circuit generate (s/iter) | wall_time_generate_s | ~63 | ? (laptop) |
    | transpile (s/iter) | wall_time_transpile_s | ~7 | ? (laptop) |
    | execute (s/iter) | wall_time_execute_s | ~40 | ? |
    | final residual (iter14) | residual_*.csv last row | 0.0002-0.216 (n=3) | ? |
    | mean HHL fidelity | hhl_metrics_*.csv | ~0.99 | ? |
    | mean l2_error_normalized | hhl_metrics_*.csv | ~0.089 | ? |
15. Validity call:
    - **Numerical (must be close):** circuit width identical (14 qubits);
      transpiled depth/gates within a few % of ~638k/649k (same lib port →
      same circuit); fidelity ≈ 0.99; final residual inside the documented
      April shot-noise band (0.0002-0.216). Inside band + matching circuit
      size = VALID reproduction.
    - **Ballpark only (drift expected, DON'T over-read):** wall-clock timing
      (laptop CPU vs Frontier `nvme`/GPU node — could be much slower or faster;
      report ratios, not absolutes), and exact qiskit/aer patch versions.
    - If depth/gates differ MORE than a few %, that flags a real lib difference.
      NOTE the lib is EXPECTED to differ: local uses Q8020-CFD (`66eadf0`),
      April most likely ran the now-deprecated agallojr fork. The two 2.x ports
      are near-equivalent (diff = agallojr's inert Estimator/Sampler stubs that
      Q8020-CFD removed; same circuit-building idioms), so depth/gates SHOULD
      still match within a few %. A larger gap = investigate; a small gap =
      confirms the ports are equivalent, which is the desired outcome.
16. Write findings to a RESULTS section in this folder's README.md (full paths,
    the resolved version set, the table, and the validity verdict).

### 7. Commit — REQUIRES EXPLICIT OPERATOR GO-AHEAD
16. Do not `git add/commit/push` until asked. When asked: commit code
    reconciliation and repin as SEPARATE commits (code consistency, then pin
    bump). fvm repo is standalone — no submodule pin chain.

---

## Quick-reference SHAs
- main tip `60d973c5`; merge-base `a5317f2b`
- qiskit-hhl-2 tip `9e76e398`; 2.x-pins commit `c94889b1` (packaging only)
- reqs template: `archive/solverfw-v2-port` `2b63f6f7`
- Q8020-CFD lib tip `66eadf0`
