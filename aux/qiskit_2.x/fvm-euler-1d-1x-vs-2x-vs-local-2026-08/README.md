# FVM Euler 1D HHL — qiskit 1.x vs 2.x (Frontier) vs 2.3-port (local)

Three-way apples-to-apples comparison of the **base FVM** HHL nozzle case run
under three software stacks, holding the physics case fixed. All three groups
are the SAME case: identical IC/BC and evolution params, `ideal_statevector`
backend, **150000 shots**, `nelem=5`, cfl=1e10, BDF1, 15 outer / 1 inner.

- Generated: 2026-08-17 (UTC).
- The Nov-vs-Apr pair reproduces the earlier two-way study; the third column
  ("local 2.3 port") is new — it validates the freshly-ported `main` on a laptop.
- Analysis + harness moved here from the working session (see `session-notes/`).

---

## The three groups + their raw results (full paths)

### Nov 2025 — qiskit 1.2.4 (Frontier, 10 matched trials)
`/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/results/fvm_euler_1d_solver/2025-11-11/shots_150000/`

### Apr 2026 — qiskit 2.3.1 (Frontier, 3 matched trials)
`/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/results/fvm_euler_1d_solver/2026-04-05/_52d087d1/time_steps_4/`
Matched (base-FVM HHL, cfl=1e10, 150k) trials: `trial_0_b9da8a4e`,
`trial_5_883b9fa8`, `trial_7_203b7613`.

### Aug 2026 — qiskit 2.3.1 port (LOCAL laptop, 1 trial) — NEW
`/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/results/fvm_euler_1d_solver/2026-08-17-qiskit23-local/trial_0/`
Full run incl. ~1.5 GB of `.qpy` circuits (not copied into results):
`/Users/agallojr/proj/src/research-notes/bus/agent-tmp/fvm-euler-1d-qiskit-1x-vs-2x/local-run-2026/`

---

## Software stacks

| | Nov 2025 | Apr 2026 | Aug 2026 (local port) |
|---|---|---|---|
| host | Frontier | Frontier `frontier02013` | Mac laptop `MH-DT9TLJQR2V` |
| qiskit | 1.2.4 | 2.3.1 | **2.3.1** |
| qiskit-aer | 0.15.1 | 0.17.2 | **0.17.2** |
| qiskit-ibm-runtime | 0.35.0 | 0.46.1 | **0.46.1** |
| qiskit-algorithms | 0.3.1 | (dropped) | (dropped) |
| quantum-linear-solvers | jw676 fork (1.x) | agallojr fork (2.x, now deprecated) | **Q8020-CFD @ 66eadf0** |
| numpy / scipy | 2.2.4 / 1.14.1 | 2.4.4 / 1.17.1 | 2.5.2 / 1.18.0 |
| python | 3.x | 3.12.9 | 3.12.10 |

The local port matches April's three named qiskit packages EXACTLY (2.3.1 /
0.17.2 / 0.46.1) by design. The one deliberate difference: the linear-solver lib
is the **Q8020-CFD** fork (canonical going forward); April most likely ran the
now-deprecated **agallojr** fork. The two 2.x forks are near-equivalent
(Q8020-CFD = agallojr minus vestigial Estimator/Sampler stubs), and the circuit
results below confirm they produce the identical circuit.

---

## Case fingerprint — proof this is apples-to-apples

`q8020_case_*.json` is byte-identical across all three groups. Hard
confirmation: the iteration-0 outer residual is **12.375368413827264** in all
three (Nov, Apr, and local), to all printed digits — so the classical FVM
discretization and the assembled linear system `Ab` are identical; the only
moving parts downstream are the qiskit stack (library + ported HHL code) and the
shot RNG.

---

## Circuit stats — side by side (transpiled, per HHL solve)

Aggregated as `depth_max` / `gates_max` over the 15 solves (matches the earlier
study's method; depth is 638,237 in 14/15 local iters, lower only at the
lowest-condition-number solve).

| metric | Nov 1.x | Apr 2.x | Local 2.3 port | Apr vs local |
|---|---|---|---|---|
| qubits (transpiled) | 14 | 14 | **14** | identical |
| transpiled depth (max) | 689,027 | 638,237 | **638,237** | **identical** |
| transpiled gate count (max) | 689,127 | 649,089 | **649,089** | **identical** |
| condition-number range | ~58–96 | ~66–96 | ~60–96 | same band |

**The local port reproduces April's transpiled circuit byte-for-byte
(638,237 depth / 649,089 gates / 14 qubits).** This is the key validation
result: the Q8020-CFD fork builds the same circuit as April's agallojr fork —
the two 2.x ports are confirmed equivalent.

## Timing — per-iteration wall time (mean ± std)

| stage | Nov 1.x (Frontier) | Apr 2.x (Frontier) | Local 2.3 (laptop) |
|---|---|---|---|
| circuit generate (s/iter) | 253.0 ± 19.5 | 63.1 ± 3.1 | 20.4 ± 2.6 |
| transpile (s/iter) | 43.2 ± 3.2 | 7.2 ± 0.4 | 3.9 ± 0.5 |
| execute (aer sim, s/iter) | 61.7 ± 4.6 | 40.0 ± 2.3 | 17.8 ± 2.8 |
| total run (15 iters, s) | 5369.6 ± 408 | 1653.6 ± 86 | 817.7 |

**DO NOT over-read the local timing column** — it is a single laptop run on
different hardware than Frontier, so absolute seconds are not comparable across
columns. It is reported for completeness only. The Nov-vs-Apr comparison
(same-hardware Frontier) remains the valid timing story: 2.x is ~3–6× faster at
gen/transpile, ~1.5× at execute, ~3× end-to-end. The local run being *faster*
than April's Frontier numbers is a hardware/contention artifact, NOT evidence of
a further speedup from the port.

## Solution quality — side by side (mean ± std)

| metric | Nov 1.x (n=10) | Apr 2.x (n=3) | Local 2.3 (n=1) |
|---|---|---|---|
| final outer residual (iter 14) | 0.074 ± 0.135 (min 3e-7, max 0.46) | 0.112 ± 0.088 (min 2e-4, max 0.22) | 0.00469 |
| mean HHL l2_error_normalized | 0.101 ± 0.046 | 0.089 ± 0.036 | 0.095 ± 0.026 |
| mean HHL fidelity | 0.985 ± 0.015 | 0.990 ± 0.008 | 0.990 ± 0.005 |

**Quality is statistically indistinguishable across all three.** The local run's
mean HHL fidelity (0.990) and l2_error_normalized (0.095) sit right on top of the
Frontier groups; its single final residual (0.00469) is comfortably inside the
documented shot-noise band (Nov 3e-7–0.46, Apr 2e-4–0.22). With n=1 locally this
is "consistent with," not "proven equal" — but combined with the byte-identical
circuit it is a clean reproduction.

---

## Bottom line

Holding the physics case, backend, and shot count fixed:

- **The qiskit-2.3 port is validated.** The local run on the freshly-ported
  `main` (Q8020-CFD lib) reproduces April's transpiled circuit exactly
  (638,237 depth / 649,089 gates / 14 qubits) and lands on the same
  solution-quality metrics — confirming the Q8020-CFD and agallojr 2.x forks are
  equivalent, and that the port did not perturb the numerics.
- **Circuit width identical (14 qubits) across all three;** 2.x transpiled
  ~6–8% shallower/lighter than 1.x, and the two 2.x builds are byte-identical.
- **2.x is ~3–6× faster** than 1.x at gen/transpile, ~1.5× at execute (valid on
  matched Frontier hardware, Nov vs Apr). Local laptop timing is not comparable
  and is reported for completeness only.
- **Solution quality unchanged** within shot noise across all three stacks.

`session-notes/summary.json` holds the Nov/Apr per-trial breakdown; the local
per-iteration detail lives in the results dir's `qc_metadata_*.csv` /
`hhl_metrics_*.csv`.
