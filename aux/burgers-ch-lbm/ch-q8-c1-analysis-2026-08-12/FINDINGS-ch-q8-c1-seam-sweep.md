# FINDINGS: CH q=8 C1 seam sweep — over-amplification is a late-time seam instability

*Draft findings for librarian ingest. Analysis run 2026-08-12 (UTC) over the
C1 seam-sweep results pulled into `q8020-cfd-experiments` on 2026-08-11
(campaign `_b5c8743c`). Companion to the CH q=8 investigation plan
(note-20260807-0017-plan-ch-q8-and-regime-sweeps) and the handoff docs in
`q8020-cfd-experiments/aux/burgers-ch-lbm/`. Scratch code + figure live in
`research-notes/bus/agent-tmp/ch-q8-c1-analysis-2026-08-12/`.*

## Question

The June IEEE fig-1 q=8 Cole-Hopf (CH) operating point over-amplifies: final
wave amplitude ~1.0 vs a reference ~0.25. C1 (the PRIMARY case in the plan)
asks: **is the measure/re-prepare seam count the lever, and does the
over-amplification die as the number of seams S → 1?** It sweeps
`--segment-size` k = [2, 4, 8, 16] → S = n_steps/k = [256, 128, 64, 32] at the
corrected fig-1 op point (q=8, nu=0.03, ic=sine, A=0.3, bc=periodic,
n_steps=512, evolution_mode=measure_reprepare, phi_modes=8, bond_dim=4,
shots=131072, seed=1234, max_total_qubits=26).

## Headline findings

1. **The blow-up is a late-time instability, not smooth seam-compounding.**
   Amplitude stays near the reference for most of the run, then jumps ~1000×
   in a few steps. Onset depends on k:
   - k=2 (S=256): diverges at step ~148
   - k=4 (S=128): diverges only in the final quarter, step ~368
   - k=8 (S=64) and k=16 (S=32): never diverge over all 512 steps.

   Finer seams (smaller k = more re-prepare events) trigger the instability
   **earlier**. Seam frequency sets the onset time; it is not a gradual
   per-seam bias accumulation.

2. **Fewer seams → correct answer.** Final relL2 vs a frame-aligned FTCS
   reference improves monotonically as seams decrease:

   | k  | S   | final half-amp | relL2 vs FTCS | diverged? | onset step |
   |---:|----:|---------------:|--------------:|-----------|-----------:|
   | 2  | 256 | 491.6          | 801           | yes       | ~148       |
   | 4  | 128 | 480.1          | 493           | yes       | ~368       |
   | 8  | 64  | 0.618          | 1.10          | no        | —          |
   | 16 | 32  | 0.332          | **0.446**     | no        | —          |

   k=16 is the best feasible sim point (relL2 ≈ 0.45). The trend points toward
   the S→1 limit, reachable only via C5 hardware or extrapolation (k≥32 is not
   simulable at shots>0 — see the handoff's fast/slow-path gate).

3. **The exact algorithm is sound; ALL error comes from the seams.** The C0
   SV-floor run (evolution_mode=single, shots=0, zero seams) gives final
   half-amp **0.2363**, identical to the frame-aligned FTCS reference
   (**0.2363**). With no measure/re-prepare seams the quantum method matches
   the classical reference to the digit. Every bit of the over-amplification is
   injected by the decode→re-encode round-trip at each seam.

4. **Post-selection retention is NOT the failure mode.** Mean per-seam
   `p_success` is ~0.997 for every k, including the blown-up k=2/4 runs
   (0.9980, 0.9982, 0.9980, 0.9968 for k=2/4/8/16). The ancilla post-selection
   is healthy even as the solution diverges — the instability is in the
   retained-branch dynamics, not in lost shots.

5. **Cost scales with k (depth-bound), and the stable regime is expensive.**
   Per-segment circuit depth / CX and wall time:

   | k  | avg depth | avg CX  | wall time |
   |---:|----------:|--------:|----------:|
   | 2  | 31,558    | 15,559  | 13 min    |
   | 4  | 62,580    | 30,987  | 19 min    |
   | 8  | 124,624   | 61,843  | 71 min    |
   | 16 | 248,712   | 123,555 | 25.8 hr   |

   Fewer seams = deeper per-segment circuits = more transpile/build time (the
   dominant cost per the handoff). The only stable sim configs (k=8, 16) are
   also the costly ones.

## Interpretation

The measure/re-prepare seam is the sole error source at this op point, and its
effect is not a benign accumulating bias but a **triggered instability** whose
onset time shortens with seam frequency. This reframes the failure: the fix is
not "reduce per-seam error" (retention is already ~0.997) but "reduce seam
count" or "stabilize the re-encode." At q=8 the practical stable window is
k≥8; the S→1 endpoint (k≥32, i.e. hardware C5) is where relL2 should approach
the C0/FTCS floor if the trend holds.

## Caveats / provenance

- **relL2 denominator generated in this analysis.** The C1 runs used
  `--no-classical-reference --no-analytic-reference`, so `final_error` is NaN
  in the artifacts. A frame-aligned FTCS reference was generated at the C1 op
  point (method=ftcs_reference, q=8, n_steps=512, ref-points=800,
  save-every=4, seed=1234; 129 frames, ran 34.5 s) and used as the relL2
  denominator. Its final half-amp (0.2363) matching the C0 SV floor is the
  cross-check that it is the right reference.
- **Metrics are relL2 and half-amplitude (max−min)/2** computed from the saved
  `solution_steps` / `u_final_method` fields; all field values are finite.
- **C0 shots=131072 case timed out** (cluster wall-clock timeout, status
  `timeout` in its `pipeline_result.json`; NOT a crash or a failed git pull).
  In evolution_mode=single at shots>0 the solver builds monolithic
  per-snapshot circuits (128 of them) with no seam-based ancilla recycling;
  build (2178 s) + transpile (2825 s) alone exceeded the allocation before all
  circuits ran, so no result field was written. Recoverable with a longer
  wall-clock allocation. Only the shots=0 SV floor is available, so the
  shots-only (no-seam) sampling floor is not yet measured.
- **LLM-generated analysis, unaudited.** Numbers came from the run artifacts
  via the scratch script; sanity-check before publication.

## Artifacts

- `analyze_c1.py` — regenerates the JSON + figure from the repo data.
- `c1_seam_sweep_summary.json` — aux-style manifest: op point, per-case
  metrics (relL2, amplitude, onset, retention, depth, timing), C0 floor,
  reference block, and repo-relative pointers to every source file.
- `c1_seam_sweep.png` — 4-panel figure (A: amplitude vs time; B: relL2 vs
  frame-aligned FTCS; C: retention vs k; D: depth & wall time vs k).
- `ftcs_ref_q8_nsteps512/` — the frame-aligned FTCS reference run.

## Source data

- C1: `q8020-cfd-experiments/results/burgers-ch-lbm/ch_q8_c1/2026-08-11/_b5c8743c/`
  (runs 2a3cbfeb=k2, b15a9654=k4, 39a1f5ab=k8, fe96b52e=k16).
- C0: `q8020-cfd-experiments/results/burgers-ch-lbm/ch_q8_c0/2026-08-06/_a66942a3/`.
- Plan: note-20260807-0017-plan-ch-q8-and-regime-sweeps.
- Handoff: `q8020-cfd-experiments/aux/burgers-ch-lbm/HANDOFF-ch-q8-sweeps-updated.md`.
