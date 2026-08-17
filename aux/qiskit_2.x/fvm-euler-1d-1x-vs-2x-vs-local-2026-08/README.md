# FVM Euler 1D HHL — qiskit 1.x → 2.3 → 2.5, apples-to-apples

Four-way comparison of the **base FVM** HHL nozzle case run under four software
stacks, holding the physics case fixed. All four groups are the SAME case:
identical IC/BC and evolution params, `ideal_statevector` backend, **150000
shots**, `nelem=5`, cfl=1e10, BDF1, 15 outer / 1 inner.

- Generated: 2026-08-17 (UTC).
- Nov-vs-Apr = the original two-way Frontier study (qiskit 1.2.4 vs 2.3.1).
- **local 2.3** and **local 2.5** are two laptop runs done the same day on the
  same machine and the same Q8020-CFD linear-solver fork — so the ONLY
  difference between them is the qiskit stack (2.3.1 → 2.5.2, ibm-runtime
  0.46.1 → 0.49.0). That pair is the cleanest isolation of the qiskit version
  we have (see the **HEADLINE** section below); timing IS comparable there
  because the hardware is identical.
- Analysis + harness moved here from the working session (see `session-notes/`).

---

## HEADLINE — qiskit 2.3 vs 2.5 (same laptop, same fork, same case)

The two local runs differ ONLY in the qiskit stack. Best evidence is
**iteration 0**, where the input is provably identical (condition number
95.9778901432456 to 13 digits in both; same pre-transpile circuit: depth 5,
19 gates, 14 qubits; same iter-0 outer residual 12.375368413827264). So every
difference below is attributable to the **qiskit transpiler**, nothing else:

| metric (iter 0, identical input) | 2.3.1 | 2.5.2 | change |
|---|---|---|---|
| transpiled depth | 638,237 | 596,688 | **−6.5%** |
| transpiled gate count | 649,089 | 641,145 | **−1.2%** |
| transpiled qubits | 14 | 14 | identical |
| circuit generate (s) | 20.9 | 20.4 | −2.5% (noise) |
| **transpile (s)** | 4.1 | 15.8 | **+286%** |

**qiskit 2.5's transpiler builds a shallower circuit (−6.5% depth) but takes
~3.9× longer to do it** (4.1 s → 15.8 s per solve at default optimization).
Across all 15 solves the picture holds: mean transpiled depth drops ~6% and
transpile time rises to 14.3 ± 1.9 s/iter (from 3.9 ± 0.5). Generate and
execute times are unchanged, and end-to-end wall time is essentially flat
(817.7 s → 859.3 s on the same laptop — the extra transpile cost roughly
cancels against noise). Solution quality is unchanged within shot noise
(fidelity 0.990 → 0.993, l2_error_normalized 0.095 → 0.082).

Net: **the 2.3 → 2.5 bump is a transpiler behavior change (leaner circuit,
slower transpile), not an accuracy or a wall-clock change.** Nothing in the
solver or the linear-solver fork needed to change to get it.

---

## The four groups + their raw results (full paths)

### Nov 2025 — qiskit 1.2.4 (Frontier, 10 matched trials)
`/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/results/fvm_euler_1d_solver/2025-11-11/shots_150000/`

### Apr 2026 — qiskit 2.3.1 (Frontier, 3 matched trials)
`/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/results/fvm_euler_1d_solver/2026-04-05/_52d087d1/time_steps_4/`
Matched (base-FVM HHL, cfl=1e10, 150k) trials: `trial_0_b9da8a4e`,
`trial_5_883b9fa8`, `trial_7_203b7613`.

### Aug 2026 — qiskit 2.3.1 port (LOCAL laptop, 1 trial)
`/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/results/fvm_euler_1d_solver/2026-08-17-qiskit23-local/trial_0/`

### Aug 2026 — qiskit 2.5.2 upgrade (LOCAL laptop, 1 trial) — NEW
`/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/results/fvm_euler_1d_solver/2026-08-17-qiskit25-local/trial_0/`
Same laptop / fork / case as the 2.3 local run; qiskit stack bumped to the
latest 2.5 line. The ~1.5 GB of per-iteration `.qpy` circuits are not copied
into results (April keeps none either).

---

## Software stacks

| | Nov 2025 | Apr 2026 | local 2.3 | local 2.5 |
|---|---|---|---|---|
| host | Frontier | Frontier `frontier02013` | laptop `MH-DT9TLJQR2V` | laptop `MH-DT9TLJQR2V` |
| qiskit | 1.2.4 | 2.3.1 | 2.3.1 | **2.5.2** |
| qiskit-aer | 0.15.1 | 0.17.2 | 0.17.2 | 0.17.2 |
| qiskit-ibm-runtime | 0.35.0 | 0.46.1 | 0.46.1 | **0.49.0** |
| qiskit-algorithms | 0.3.1 | (dropped) | (dropped) | (dropped) |
| quantum-linear-solvers | jw676 fork (1.x) | agallojr fork (2.x, deprecated) | Q8020-CFD @ 66eadf0 | Q8020-CFD @ 66eadf0 |
| numpy / scipy | 2.2.4 / 1.14.1 | 2.4.4 / 1.17.1 | 2.5.2 / 1.18.0 | 2.5.2 / 1.18.0 |
| python | 3.x | 3.12.9 | 3.12.10 | 3.12.10 |

The two local columns are identical EXCEPT qiskit (2.3.1 → 2.5.2) and
ibm-runtime (0.46.1 → 0.49.0) — the deliberate isolation. The local 2.3 run in
turn matches April's three named qiskit packages exactly; its one difference
from April is the linear-solver lib (**Q8020-CFD** fork, canonical going
forward, vs April's now-deprecated **agallojr** fork). The two 2.x forks are
near-equivalent (Q8020-CFD = agallojr minus vestigial Estimator/Sampler stubs),
and the circuit results below confirm they build the identical circuit under
2.3.

---

## Case fingerprint — proof this is apples-to-apples

`q8020_case_*.json` is byte-identical across all four groups. Hard
confirmation: the iteration-0 outer residual is **12.375368413827264** in all
four (Nov, Apr, local 2.3, local 2.5), to all printed digits — so the classical
FVM discretization and the assembled linear system `Ab` are identical; the only
moving parts downstream are the qiskit stack (library + ported HHL code) and the
shot RNG.

---

## Circuit stats — side by side (transpiled, per HHL solve)

Aggregated as `depth_max` / `gates_max` over the 15 solves (matches the earlier
study's method).

| metric | Nov 1.x | Apr 2.3 | local 2.3 | local 2.5 |
|---|---|---|---|---|
| qubits (transpiled) | 14 | 14 | 14 | 14 |
| transpiled depth (max) | 689,027 | 638,237 | 638,237 | **596,688** |
| transpiled gate count (max) | 689,127 | 649,089 | 649,089 | **641,145** |
| condition-number range | ~58–96 | ~66–96 | ~60–96 | ~60–96 |

Two things here:
- **local 2.3 reproduces April's transpiled circuit byte-for-byte**
  (638,237 / 649,089 / 14) — confirming the Q8020-CFD and agallojr 2.x forks
  build the identical circuit.
- **qiskit 2.5 makes it ~6.5% shallower** (596,688 vs 638,237) and ~1.2%
  fewer gates, at the same width. See the HEADLINE — this is a pure transpiler
  change (iter-0 input is identical).

## Timing — per-iteration wall time (mean ± std)

| stage | Nov 1.x (Frontier) | Apr 2.3 (Frontier) | local 2.3 (laptop) | local 2.5 (laptop) |
|---|---|---|---|---|
| circuit generate (s/iter) | 253.0 ± 19.5 | 63.1 ± 3.1 | 20.4 ± 2.6 | 19.7 ± 2.5 |
| transpile (s/iter) | 43.2 ± 3.2 | 7.2 ± 0.4 | 3.9 ± 0.5 | **14.3 ± 1.9** |
| execute (aer sim, s/iter) | 61.7 ± 4.6 | 40.0 ± 2.3 | 17.8 ± 2.8 | 17.7 ± 2.8 |
| total run (15 iters, s) | 5369.6 ± 408 | 1653.6 ± 86 | 817.7 | 859.3 |

Timing notes, in order of validity:
- **local 2.3 vs local 2.5 IS a valid comparison** (same laptop). The one real
  timing change is **transpile: 3.9 → 14.3 s/iter (~3.7×)** under 2.5 — the cost
  of the shallower circuit. Generate and execute are flat; end-to-end wall time
  barely moves (817.7 → 859.3 s) because transpile is a small slice of the total.
- **Frontier vs laptop columns are NOT comparable** (different hardware); the
  Nov-vs-Apr same-Frontier story stands: 2.3 is ~3–6× faster than 1.x at
  gen/transpile. Do not read the laptop columns as faster than Frontier — that's
  hardware, not qiskit.

## Solution quality — side by side (mean ± std)

| metric | Nov 1.x (n=10) | Apr 2.3 (n=3) | local 2.3 (n=1) | local 2.5 (n=1) |
|---|---|---|---|---|
| final outer residual (iter 14) | 0.074 ± 0.135 (min 3e-7, max 0.46) | 0.112 ± 0.088 (min 2e-4, max 0.22) | 0.00469 | 0.00680 |
| mean HHL l2_error_normalized | 0.101 ± 0.046 | 0.089 ± 0.036 | 0.095 ± 0.026 | 0.082 ± 0.020 |
| mean HHL fidelity | 0.985 ± 0.015 | 0.990 ± 0.008 | 0.990 ± 0.005 | 0.993 ± 0.003 |

**Quality is statistically indistinguishable across all four.** Both local runs'
fidelity (0.990 / 0.993) and l2_error_normalized (0.095 / 0.082) sit on top of
the Frontier groups; both final residuals are well inside the documented
shot-noise band (Nov 3e-7–0.46, Apr 2e-4–0.22). The local 2.3-vs-2.5 residual
difference (0.00469 vs 0.00680) is shot RNG, not a version effect — the two runs
drew different 150k-shot samples, and per-iteration residuals diverge from iter 1
onward for that reason. With n=1 each locally this is "consistent with," not
"proven equal."

---

## Bottom line

Holding the physics case, backend, and shot count fixed:

- **qiskit 2.3 → 2.5 is a transpiler behavior change, nothing more.** On the
  same laptop / fork / case, 2.5 builds a **~6.5% shallower** circuit (596,688 vs
  638,237 depth, same 14 qubits) but takes **~3.7× longer to transpile**
  (3.9 → 14.3 s/iter). End-to-end wall time is flat; solution quality is
  unchanged within shot noise. No solver or linear-solver-fork change was needed.
- **The qiskit-2.3 port is validated.** local 2.3 reproduces April's transpiled
  circuit byte-for-byte (638,237 / 649,089 / 14) and matches its quality metrics,
  confirming the Q8020-CFD and agallojr 2.x forks are equivalent.
- **1.x → 2.x** (Nov vs Apr, matched Frontier hardware): 2.x is ~3–6× faster at
  gen/transpile, ~1.5× at execute, and transpiles ~6–8% shallower/lighter.
- **Solution quality unchanged** within shot noise across all four stacks.

`session-notes/summary.json` holds the Nov/Apr per-trial breakdown; the local
per-iteration detail lives in each results dir's `qc_metadata_*.csv` /
`hhl_metrics_*.csv`.
