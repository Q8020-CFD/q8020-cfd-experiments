# Next steps: C2 → C5 (bypassing the C3 phi-modes study)

Decided 2026-08-12 (UTC), off the C1 seam-sweep finding (k=8/16 stable, k=2/4
diverge — see `FINDINGS-ch-q8-c1-seam-sweep.md` in this folder). Case defs:
`/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/burgers-ch-lbm/HANDOFF-ch-q8-sweeps-updated.md`.

## C2 — shots ladder (do next, sim)

- **Pin k\* = 8.** Stable (relL2 ≈ 1.10 over 512 steps), 71 min/run vs k=16's
  25.8 hr; k=16 depth ~2.5e5 is beyond real QC anyway. k=8 depth ~1.25e5.
- **Sweep shots DOWN** from 131072: `--shots = [16384, 32768, 65536, 131072]`
  (2^14 → 2^17). Op point else = C1 baseline: q=8, nu=0.03, A=0.3, phi-modes=8,
  bond-dim=4, measure_reprepare, n_steps=512, seed=1234;
  `--max-total-qubits 18` (= q+2+k*).
- **Deliverable:** min shots at q=8/k=8 that holds relL2 at the k=8 stable
  value — the cheap working shot count for the hardware anchor / C5.

**DEVIATION from the handoff's written C2 — chosen, not silent.** The handoff
C2 is `shots=[16384,65536,131072,524288,1048576]` (through 2^20) at
`segment-size=[4, k*]` (two k), and its PURPOSE is to *decompose* residual
error into per-seam shot-noise (∝1/√S) vs a flat truncation-floor bias. We
narrow it two ways:
- **Drop the >131072 up-rungs.** Rationale: C1 at 131072 was NOT
  shot-noise-limited (retention ~0.997, k=8 stable), so more shots are unlikely
  to help. Caveat: that is an INFERENCE — C1 held shots fixed and never swept
  them, so it cannot prove the point. If cheap, keep ONE up-rung (2^19) as a
  confirmation the floor is truncation, not noise.
- **Drop the k=4 arm.** We only run k*=8. Cost: we lose the shot-noise-vs-bias
  DECOMPOSITION the handoff C2 was built for (that needs a diverged k like 4
  contrasted against stable k* across the ladder). We are trading that
  diagnostic for speed-to-C5. Reinstate the k=4 arm only if C5 forces the
  question of whether residual error is noise or bias.

## Bypassed

- **C3 (phi-modes [0,8,32,128]) — skipped.** Phi is a second-order lever; the
  seam result stands without it. Cost accepted: we do NOT learn whether phi
  "wakes up" at good k (the plan's open question). Revisit only if C5 needs it.
- **C4 full sim dial-up (q=[4,8,16]) — not run as a sim campaign.** Its q≤16
  point is folded into the C5 hardware anchor below instead.

## Path to C5 (q=32 hardware) — with a credibility anchor

1. **Anchor first:** one q≤16 hardware run at (k*=8, phi=8) that HAS a sim/FTCS
   reference (handoff "Beyond q=16", ~line 337). Validates hardware against
   known-good before going where no reference exists. Do NOT skip straight to
   q32 — a noisy q32 curve with no reference is undefendable.
2. **C5:** q=32 on real IBM QC. No FTCS/sim ref at q32 → deliverable is
   physics-consistency + trend-vs-q, NOT relL2.

## C5 scoping — open (t.b.d.)

- **Feasible-k window may be EMPTY.** Sim wants LARGE k (stability, k≥8);
  hardware wants SMALL k (shallow, fewer ancillas, better retention). The real
  C5 question is "does any k thread both at q32?", not "port the sim run."
- **Retention.** Sim's ~0.997 is NOISELESS. On hardware it drops per seam AND
  per 2-qubit gate, compounding with seam count → small k bleeds shots, large k
  bleeds gate fidelity. Lose on two axes. Budget shots high; expect a fight.
- **"A few frames," not the full 512-step trajectory.** Pick a handful of
  snapshot steps at 1–2 k values to show noise/depth impact — otherwise it's a
  week of back-to-back batch jobs. Frame selection = t.b.d.
