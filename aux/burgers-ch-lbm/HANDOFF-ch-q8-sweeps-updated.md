# HANDOFF: CH q=8 failure sweeps

Task: write the sweep TOMLs for the q=8 Cole-Hopf (CH) investigation — find WHY
CH over-amplifies at q=8, then scale to q=16. Cases are up top; the "why" is all
below the divider. Full reasoning: `PLAN-ch-q8-and-regime-sweeps.md`. Symbols
(k, S, chi, phi, SV) and the 3 must-fix TOML gotchas are in the Background
section — skim those first.

Scoring metric is unchanged: relative L2 of u vs the FTCS reference (see
Reference & deferred). Every case is judged on relL2-vs-FTCS.

## Cases

Op point (fig-1 bad case, corrected) — every case inherits this except the
knobs it Varies: `q=8, nu=0.03, ic-amplitude=0.3, ic=sine, bc=periodic,
source=none, n-steps=512, evolution-mode=measure_reprepare, segment-size=4,
phi-modes=8, bond-dim=4, shots=131072, seed=1234, save-every=4`.

FAST-PATH GATE (avoid the machine-pinning slow case): at shots>0 in
measure_reprepare, always set `--max-total-qubits = q + 2 + (largest
--segment-size in the group)`, and keep that ≤ 33. (`--segment-size` is "k",
the steps per segment.) Each case below states the exact value. Why this works,
and why k=`--segment-size`≥32 is out of reach at shots>0, is in Background →
"Fast vs slow Aer path". Rule of thumb at q8/chi=4: fast iff `--segment-size
(k) ≤ 16`.

**C0 — idealized SV & seamless t=0 to t=end**
- Purpose: zero-seam floor — pure algorithm error, then + sampling.
- Vary: `evolution-mode=single`, `shots=[0, 131072]`.
- Args: no `--max-total-qubits` needed (single-step SV/batch; no seams).

**C1 — seam sweep (PRIMARY)**
- Purpose: is seam count the lever? does over-amp die as S→1?
- Vary: `segment-size=[2,4,8,16]` → S=[256,128,64,32]. `shots=131072`.
- Args: `--max-total-qubits 26` (= q+2+16; keeps all four k fully deferred/fast).
- Scope: k≥32 is NOT simulable at shots>0 (Background → "Fast vs slow"). Reach
  the S→1 end via C5 hardware or by extrapolating the S=256→32 trend.

**C2 — shots ladder × k**
- Purpose: split per-seam shot-noise (∝1/√S) from truncation floor (flat bias).
- Vary: `shots=[16384,65536,131072,524288,1048576]` (2^14..2^20) at
  `segment-size=[4, k*]`; one TOML per k. k* = C1 winner (≤ 16).
- Args: `--max-total-qubits = q + 2 + max(4, k*)` (e.g. k*=8 → 18; k*=16 → 26).
  Keep k ≤ 16 — a slow-path k at 2^20 shots is the exact pin-the-machine combo.

**C3 — phi re-test at best k**
- Purpose: does the filter help once seams are optimized? (phi=0 = off, never tried)
- Vary: `phi-modes=[0,8,32,128]` at `segment-size=k*`. `shots=131072`.
- Args: `--max-total-qubits = q + 2 + k*`.

**C4 — dial-up (Phase 2, after k*, phi* known)**
- Purpose: scale the tuned setting across qubit count.
- Vary: `q=[4,8,16], segment-size=[k*/2,k*,2k*], phi-modes=<per-q>`. shots:
  q4=131072, q8=131072, q16=134217728 (2^27; see Background → "Shots per q").
- Args: `--max-total-qubits = q + 2 + 2k*` per q (must be ≤ 33; at q16 this
  caps 2k* ≤ 15). q4 & q8 share one TOML (shots=131072); q16 is a SEPARATE
  shots=2^27 TOML. q4 skips C3 (N=16: phi-modes=8 already Nyquist).

**C5 — q=32 on real IBM QC (PLACEHOLDER, args TBD)**
- Purpose: go beyond classical sim (q>~20 infeasible) — hardware-only run.
- Vary: `q=32` on real IBM backend; all args TBD (backend, coupling-map, k,
  shots, error mitigation).
- Args: on hardware width is cheap and reset costly — raise `--max-total-qubits`
  freely (favor small k). No FTCS/sim ref at q32 → deliverable is
  physics-consistency + trend-vs-q, not relL2. See Background → "Beyond q=16".

## Skeleton to clone

C1, one group. `--max-total-qubits 26` = q+2+(largest k) keeps every k fast.

```toml
# CH q=8 seam sweep. segment-size is the swept lever. All else = fig-1 baseline.
[global]
_output_dir = "~/q8020"
_inject_outdir = "--outdir"
_env = "./q8020-cfd-ch-lbm/.venv"
_script = "python ./q8020-cfd-ch-lbm/src/burgers_solver.py"
"--noshow" = true
"--no-classical-reference" = true
"--no-analytic-reference" = true

"--evolution-mode" = "measure_reprepare"
"--save-every" = 4                 # keep aligned to a seam; or use --auto-cadence
"--bc" = "periodic"
"--ic" = "sine"
"--source" = "none"
"--ic-amplitude" = 0.3
"--nu" = 0.03

"--seed" = 1234
"--shots" = 131072                 # 2^17 (seams exist only at shots>0)
"--metric-transpile-timeout" = 0

"--q" = 8
"--n-steps" = 512                  # power of 2 -> every k below divides evenly

[ch_seam_sweep]
"--method" = "cole_hopf_circuit"
"--bond-dim" = 4                   # PINNED: exact for this phi (1-fid ~4e-8), scales to q16
"--phi-modes" = 8                  # baseline, held fixed here
"--max-total-qubits" = 26          # q(8)+n_bond(2)+max k(16): keeps ALL k in group fast
"--segment-size" = [2, 4, 8, 16]   # feasible seam sweep -> S=[256,128,64,32]
# k>=32 omitted: infeasible at shots>0 on Aer (fully-deferred k=32 = 42 qubits;
# capping smaller trips reset -> per-shot). Reach S->1 via C5 hardware or by
# extrapolating this trend. NOTE: no "--propagator" line — flag removed.
```

## Reference (relL2 metric)

Metric = relative L2 of u vs an FTCS reference. The ref depends on physics +
grid + cadence, NOT on any quantum knob (k, phi, chi, shots) — so it's
q-dependent (subsamples to N=2^q). C0-C3 all share ONE q=8 ref; C4 needs one
per q. `--save-every` MUST match the case (frame alignment).

One TOML emits all refs by sweeping `--q` in the group (each value = one run):

```toml
[ftcs_ref]
"--method" = "ftcs_reference"
"--q" = [4, 8, 16]            # one ref run per q (list = sweep axis)
"--n-steps" = 512
"--ref-points" = 800          # min resolved grid (see q16 note below)
"--save-every" = 4            # match the case; if C4 uses bigger k at q16, match that
# + same physics as baseline: --nu 0.03, --ic sine, --ic-amplitude 0.3,
#   --bc periodic, --source none  (put in [global])
```

Still valid at q16: the ref auto-sub-steps for CFL stability (787 sub-steps at
q16, ~seconds), so no blow-up. Caveat: ref-points=800 < N=65536, so at q16 the
ref runs ON the q-grid (no refinement) — still an independent METHOD (classical
FTCS vs quantum) but not an independent RESOLUTION. That's fine here: the q16
grid is already hugely over-resolved for nu=0.03 (FTCS truncation ~1e-10). For
a finer-grid ref at q16, set ref-points > 65536 (e.g. 131072 → 2x); rarely needed.

---

# Background (the "why")

> WARNING: unreviewed, LLM-generated. Measured numbers below (fidelity, CX
> counts, participation ratios, timings) came from probe scripts, not a human
> audit — sanity-check before relying on any figure or committing to a run.

Starting point: the June IEEE paper fig-1 q=8 CH operating point, i.e.
`q8020-cfd-experiments/aux/burgers-ch-lbm-June2026/input/ab-q8/burgers_ab_mutual_q8_nu030.toml`.

Failure signature (from priors): ~4x over-amplification (final amp ~1.0 vs ref
0.249) — a BIAS, not shot noise. That's why C0 (SV floor) comes first and why
the shots ladder is diagnostic rather than a fix.

## Symbols (some are NOT flags — read before the tables)

- **q** — data qubits; grid has N = 2^q points. Flag `--q`.
- **k** — steps per segment. NOT a flag by that name; it IS `--segment-size`.
  One circuit runs k time steps, then measures + re-prepares. "sweep k" =
  sweep `--segment-size`.
- **S** — number of segments = seams = measure/re-prepare events =
  n_steps / k. NOT a flag; it's a derived count you get by choosing k.
  Fewer seams (bigger k) = less compounding but deeper circuits.
- **chi** — MPS bond dimension. Flag `--bond-dim`. Prep uses chi/2-ish extra
  "bond" qubits. See the bond-dim decision below — we PIN it, not sweep it.
- **phi** — the Cole-Hopf transformed field; `--phi-modes` low-passes it.
- **SV** — statevector, i.e. `--shots 0` (exact readout, no sampling noise).

## READ FIRST — 3 fixes vs the June TOMLs (they will error/misrun otherwise)

1. DELETE every `"--propagator" = "qft-diagonal"` line. The flag was removed
   from the solver; qft-diagonal is now the only path. argparse hard-errors on
   an unknown flag.
2. Repoint the runner at the current repo:
   - `_script = "python ./q8020-cfd-ch-lbm/src/burgers_solver.py"`
   - `_env = "./q8020-cfd-ch-lbm/.venv"`
   (June TOMLs say `./q8020-mps-burgers/...` — retired.)
3. `--shots` is a shared/global flag (`q8020_cfd_metautil.args`), default 0 = SV.
   Keep using it; no change needed.

Mechanics to respect:
- measure_reprepare requires `n-steps % segment-size == 0`. n-steps=512 is
  chosen so every k below divides evenly.
- Set `--save-every` = `--segment-size` (frames land on seams). Or set
  `--auto-cadence` and let it pick both.
- `--t1`/`--t2` are in µs; both absent = noiseless.
- One sweep axis per TOML (a single `[...]` list). Everything else scalar.

## Knobs: which stay put, which turn over

Three knob families you asked about map like this:

| knob (flag)              | family                | Phase 1 | Phase 2 |
|--------------------------|-----------------------|---------|---------|
| `--bond-dim` (chi)       | **MPS** (prep)        | PINNED 4 (see below) | PINNED 4 |
| `--phi-modes`            | **psi-modes filter**  | LEVER (re-test at best k) | scale ~N/16 |
| `--segment-size` (k)     | **measure-reprepare** | PRIMARY LEVER | k* from Ph1 |
| `--evolution-mode`       | measure-reprepare     | single (floor) else measure_reprepare | measure_reprepare |
| `--shots`                | sampling (per seam)   | LEVER (ladder) | 131072 (+SV check) |
| `--q`                    | scale                 | FIXED 8 | [4,8,16] |
| `--nu` `--ic-amplitude`  | physics               | FIXED 0.03 / 0.3 | fixed |
| `--ic` `--bc` `--source` | physics               | sine / periodic / none | same |
| `--n-steps`              | time                  | FIXED 512 | 512 |
| `--seed`                 | rng                   | FIXED 1234 | 1234 |
| `--t1` `--t2`            | noise                 | none | none |

Why this shape: MPS is the ONLY prep path that works at q>=8 — Qiskit's
amplitude/`initialize` synthesis fails on the peaked nu=0.03 phi ("input matrix
not unitary" from near-zero tail amplitudes), so we cannot just switch to
amplitude prep. Instead we PIN chi small (see next section) so MPS contributes
negligibly and stays out of the way. That leaves the real levers: seam count k
(`--segment-size`) and the phi filter. Priors already killed both bond-dim AND
phi as levers, but only at high seam count (S=80). The one axis never varied at
q=8 is the seam count. So `--segment-size` is the prime suspect; phi gets
re-tested only AFTER we find the best k (it may wake up once seams stop
dominating).

## Fast vs slow Aer path (the --max-total-qubits gate)

The CH propagator block-encodes one non-unitary diffusion step per time step,
each needing its own post-selection ancilla. The heat-ancilla register is
capped by `--max-total-qubits` (data + MPS bond + heat). When a segment has
more steps than the cap leaves room for, the circuit RECYCLES ancillas via
mid-circuit measure+reset. That reset flips Aer's statevector backend off its
cheap sample-once path onto a PER-SHOT trajectory path — wall-clock goes
~linear in shots and a single segment can run for hours (measured q6: 512 shots
slow = 16s vs 4096 shots fast = 3s). NOT a memory wall; a time wall.

Fast (fully deferred, sample-once) iff, per segment:

    max-total-qubits >= q + n_bond + segment-size        (n_bond = 2 at chi=4)

Raising the cap grows the statevector (2^cap * 16 B), so the sim envelope is the
PAIR `q + 2 + segment-size <= max-total-qubits <= 33` (~1 Frontier node, 128 GB)
→ fast-path sim needs `segment-size <= 31 - q` (q8: ≤23, practically ≤16 on the
sweep grid; q16: ≤15). Default cap unset = original 2*q behavior (paper's runs);
set it explicitly for every shots>0 measure_reprepare case. Each run prints a
`fast path` / `SLOW PATH …` line on segment 1 — if you see SLOW PATH, kill it.

Why SV can't cover the high-k tail: seams exist ONLY at shots>0 (the seam error
is the per-re-prepare decode→re-encode round-trip). At `shots=0` the SV path
does exact per-step projection with NO decode/encode, so `segment-size` has ZERO
effect (verified: k=2/4/8 give byte-identical SV output) — shots=0 IS the
seamless floor = C0. So C1 must be shots>0, and k≥32 (fully-deferred = 42 qubits
= 70 TB) is simply unreachable on a simulator; capping smaller trips the reset
slowdown. This replaces the old "k≥32 → Frontier, ~9x/doubling" note (a stale q7
FULL-RANK carry-over): the real constraint is the reset→per-shot time wall.

## Bond-dim decision: PIN chi=4 (do NOT use full rank, do NOT sweep)

Measured on the fig-1 phi (nu=0.03, A=0.3), prep fidelity + cost, q-independent
because phi is smooth (low entanglement — same Schmidt spectrum at q=8/12/16):

| chi | 1 - fidelity | bond qubits | prep CX @q8 | prep CX @q16 |
|----:|-------------:|------------:|------------:|-------------:|
| 2   | 1.3e-3       | 1           | ~15         | ~15          |
| 4   | **3.8e-8**   | **2**       | 129         | 283          |
| 6   | 5e-14        | 3           | 540         | 1299         |
| full (16 @q8 / 256 @q16) | ~1e-16 | 4 / **8** | 1701 | **513622** |

chi=4 is effectively exact (truncation ~4e-8, seven orders below the ~4x
over-amp and far under any shot-noise floor) yet costs only 2 bond qubits and
~130-280 CX. Full rank at q16 is 513k CX / 8 bond qubits — infeasible and the
reason the original plan's "full rank" pin blocked q16. chi=4 is flat in q, so
the SAME pin holds for q4/q8/q16. It cannot confound the segment sweep.
Set `--bond-dim 4` everywhere; never sweep it in this study.

DELTA vs the June fig-1 runs: fig-1 pinned FULL rank at every q (q4 bond-dim=8
which clamps to 4; q6/q7=8; q8=16; q10=32; q16 never ran — paper stopped at
q10). Our chi=4 differs at q6+ but is numerically immaterial (~4e-8), so the
June q8 result should reproduce. At q=4 there is ZERO delta: full rank at q4 IS
4, so chi=4 reproduces the June q4 prep exactly (1-fid = 0) — q4 is a true
like-for-like anchor to the paper. If these runs feed a publication, footnote
the full-rank -> chi=4 change.

## Shots per q (C3, C4): 2^17 is NOT enough at q=16

Measurement samples |psi|^2. The phi distribution occupies a FIXED fraction of
bins (participation ratio PR ~ 0.255 * N, measured constant across q), so the
shots for a given per-bin accuracy scale LINEARLY with N=2^q. For ~1% relative
count error in a typical occupied bin, S ~ PR / (0.01)^2 ≈ **2^(q+11)** (clean
power-of-2 rule):

| q  | N     | PR (occupied bins) | shots for ~1%/bin | 2^17 gives  |
|----|-------|-------------------:|------------------:|-------------|
| 4  | 16    | 4                  | 2^15 (32768)      | ~0.5%/bin (overkill) |
| 8  | 256   | 65                 | 2^19 (524288)     | ~2%/bin (marginal) |
| 16 | 65536 | 16,700             | 2^27 (134M)       | ~36%/bin (swamped) |

Rule of thumb: **shots ~ 2^(q+11)** for ~1%/bin (q8-parity) accuracy.
- q=4: 2^17 is overkill — keep 2^17 (matches fig-1 magnitude, cheap).
- q=8: 2^17 ≈ the paper's 150k setting. The q8 failure is over-amplification,
  NOT shot noise, so 2^17 is fine for the DIAGNOSIS; C2 ladder tests this.
- q=16: 2^17 is ~1000x short. Use shots=2^27 (~1%/bin, q8-parity) — a shots>0
  q16 run is only honest at ~2^27. Don't quietly reuse 2^17.

So for C3 use shots=131072 (2^17, q8 only). For C4: shots=131072 at q4/q8, and
shots=134217728 (2^27) at q16.

## Practical top-end for q=16 (measured — it's NOT shots or memory)

At chi=4 the whole cost model shifts vs the paper's Frontier assumption:

- SHOTS are free: Aer statevector samples at 2-5 M/s, flat in both shot count
  AND qubit width (10^7 shots @19q = 3s). Shots never bind — ignore them as a
  cost axis.
- MEMORY is trivial: chi=4 makes q16 a 22-qubit circuit (16 data + 2 bond + 4
  heat anc) = 67 MB statevector. The paper's 69 GB / Frontier-node figure
  assumed FULL rank (~33 qubits, 2q+1). q16 now fits on a laptop.
- The REAL ceiling is per-segment circuit BUILD + TRANSPILE, done once per
  seam (S = n_steps/k times per run). One q16 segment's build+transpile alone
  exceeds ~2 min; x128 seams (k=4) = hours per case. This dominates, not the
  quantum sim.

So to make q16 tractable: (1) shots are cheap (2^27 ≈ 30s), so the sampling
floor is a non-issue — the ceiling is transpile, not shots; (2)
prefer FEWER, LARGER segments (bigger k -> fewer transpiles) — note this pulls
opposite to C1's fine-seam scan, so pick a modest k at q16, not k=2; (3) the
segment circuit is structurally identical every seam, so transpile ONCE and
reuse (cache) rather than re-transpiling per seam — worth a solver check before
the q16 dial-up. Budget q16 as a batch/Frontier job on wall-clock, not memory.

## Beyond q=16: real quantum hardware (q=32)

Sim is dead past q~20: Aer statevector needs 2^(total) amplitudes, and total =
q + 2 (bond) + heat ancillas, where heat = segment-size on the fast path (or
min(segment-size, cap-q-bond) once reset-tiling kicks in). At k=4 fully deferred
that is q+6 → q32 = 38 qubits = 4.4 TB. Even the classical MPS prep chokes (it
SVDs a length-2^q vector: 68 GB just to hold psi0 at q32). So q32 is a HARDWARE
run, not a sim — and that is the point: it shows CH going beyond what we can
classically verify.

WIDTH is fine on hardware: 38 physical qubits (q32, k=4) is well within current
devices. Do NOT use shots=0/SV to drive qubit count — hardware always samples;
SV is a sim-only concept and is dropped here.

What changes vs the sim cases:
- No FTCS relL2 at q32 — there is no classical reference at that size (the whole
  reason to go there). The deliverable is a self-consistency / physics-sanity
  story (mass conservation, monotonic decay, shape vs the q16 trend), NOT an
  error-vs-reference number. Anchor credibility with a q<=16 hardware run that
  DOES have a sim/FTCS ref, then extrapolate.
- The ceiling is DEPTH x error, not width or memory. Post-selection retention
  (ancilla all-|0>) drops with each seam and each 2q gate, so k and total gate
  count trade directly against how many shots survive. Expect to push shots high
  and still fight retention — the q16 shot rule (2^(q+11)) is a per-bin FLOOR,
  hardware noise sits on top.
- Fewer, larger segments (big k) cut seam count / transpiles but WIDEN the
  circuit (min(k,q) ancillas) and deepen it — opposite pull to sim. On hardware,
  depth and retention likely favor SMALL k (fewer ancillas, shallower), the
  reverse of the sim advice. Treat k at q32 as its own tuning question.

Concretely: run q32 on hardware at the Phase-1-tuned (k*, phi*), pick the k that
balances seam-retention vs depth on the target device, drive shots as high as
the queue allows, and report physics-consistency + trend-vs-q, not relL2.

## Reference & deferred

Deferred (NOT in this handoff): nu×A regime map, and the bond-dim/compression
STUDY (deliberately sweeping chi as a lever to grow problem size) — see PLAN
Phases 3-4. Here chi is just PINNED at 4 to stay out of the way; Phase 4 is
where chi becomes the subject.
