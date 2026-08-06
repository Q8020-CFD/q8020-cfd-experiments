# Frontier Aer-ROCm sizing guide — statevector workloads

Reference for sizing distributed qiskit-aer statevector sweeps on OLCF
Frontier. Derived from the `aer_rocm_mpi_ladder.toml` GHZ campaigns of
2026-07-29 and 2026-07-31 (results under
`results/aer_rocm_smoke/2026-07-{29,31}/`). Consult this BEFORE authoring a
sweep TOML for any Aer-GPU case wider than ~30 qubits.

## Assumptions (the envelope this guide is valid for)

- qiskit-aer ROCm build (`AER_MPI=ON`), `method=statevector`, `device=GPU`
  (the `frontier-aer-build.sh` environment, GTL-linked mpi4py).
- Frontier node = 4 MI250X = 8 GCDs, 64 GiB HBM each → 512 GiB HBM/node.
- One MPI rank per GCD (8 ranks/node, `--gpus-per-task=1`), rank counts
  powers of two.
- Chunking enabled with `blocking_qubits = 23`.
- Statevector memory is width-only: `2^q × 16 B`. Circuit depth, gate mix,
  and shots affect runtime, never the memory ceiling.

## The rule

**The statevector must fit in ≤ 25 % of aggregate HBM.**

```
max qubits = 33 + log2(nodes)      (memory ceiling, empirical)
min qubits = 26 + log2(nodes)      (chunk floor: qubits >= blocking_qubits + log2(ranks))
```

Each doubling of nodes buys exactly one qubit. Because ranks are powers of
two and qubits are integers, occupancy only ever doubles — 25 % and 50 % are
adjacent test points, so "≤ 25 %" is the complete actionable rule; the true
ceiling lies somewhere in (25 %, 50 %) but is unreachable anyway.

## Sizing table

| Nodes | Ranks | Valid width (q) | Statevector at max | Status |
|------:|------:|:---------------:|-------------------:|--------|
| 1     | 8     | 26 – **33**     | 128 GiB            | inferred (32 pass, 34 fail) |
| 2     | 16    | 27 – **34**     | 256 GiB            | **validated** (q34 pass ×2; q35 fail) |
| 4     | 32    | 28 – **35**     | 512 GiB            | inferred (q36 fail) |
| 8     | 64    | 29 – **36**     | 1 TiB              | **validated** (q36 pass) |
| 16    | 128   | 30 – **37**     | 2 TiB              | inferred |
| 32    | 256   | 31 – **38**     | 4 TiB              | inferred |
| 64    | 512   | 32 – **39**     | 8 TiB              | inferred |

Node count for a q-qubit circuit: `N = 2^(q-33)`, rounded up to a power of
two. Below the width floor, lower `blocking_qubits` or use fewer nodes.

## Failure mode: hang, not crash

Exceeding the 25 % budget does NOT produce a clean OOM error:

- Multi-node over-budget cases (q35@2, q36@4, both 50 %) ran **silently for
  ~2 h until the walltime killed the whole job** — consistent with Aer
  falling back to host-memory chunk staging, which is functionally correct
  but orders of magnitude slower. The hung case also starved every case
  queued behind it in the same rung.
- The single-node 50 % case (q34@1) segfaulted ~43 s in (reproduced twice,
  different nodes).

Mitigations: check widths against the table before submitting, and wrap the
per-case `srun` in a timeout (every legitimate ladder case finishes in
seconds; even `timeout 15m` saves ~2 h per bad case).

## Timing anatomy (for walltime budgeting)

Per case, measured on the 2026-07-31 campaign:

- ~1.5–2 s fixed process setup (srun launch, Python start, imports off
  node-local NVMe, MPI init, transpile). Width-independent. Requires
  `_slurm_pack_venvs` — off NFS this line item is 10–25 **minutes**.
- ~0.3–0.5 s first-run init (HIP runtime, GPU context, memory pools,
  statevector allocation) — the cold−warm gap; width-independent.
- Warm run time — the only part that scales with width and nodes. GHZ
  reference points (depth ≈ q+1, 1000 shots): q32@1 node 1.10 s,
  q34@2 3.6 s, q36@8 5.7 s, q36@16 3.5 s.
- Parallel efficiency improves with width (q36: 81 % on the 8→16 doubling;
  q32: ~57 %). Deeper circuits amortize communication better than the
  shallow GHZ probe, so these are conservative floors.
- Plus one venv sbcast/untar per job (~10–25 s), shared across the rung.

## What voids the table

- `method=density_matrix` or noise models (which force it): memory is
  `2^(2q) × 16 B` → budget roughly halves: max ≈ 16 + log2(N)/2.
- Mid-circuit `save_statevector` / `save_density_matrix`: each save
  materializes another full copy of the state.
- `matrix_product_state` method: memory tracks entanglement, not width —
  no width-only formula exists.
- Materially different `blocking_qubits`, or a different rank↔GPU mapping
  (e.g. `--gpus-per-task=2`): the ceiling formula survives (it is set by
  aggregate HBM), but the 25 % headroom factor was measured at 1 rank/GCD,
  `blocking_qubits=23` — re-validate one boundary point (q34 @ 2 nodes is
  the cheap one) before trusting the table.

What does NOT void it: circuit depth, gate types, shot count, mid-circuit
measurement — these cost time, not memory.

## Provenance

- Campaigns: `results/aer_rocm_smoke/2026-07-29/` (5 rungs, transpiler cap
  blocked q35/q36 — fixed in `aer_rocm_smoke.py` by transpiling without the
  backend target) and `results/aer_rocm_smoke/2026-07-31/` (full ladder,
  q36 passing at 8 and 16 nodes).
- All passing cases: `ghz_fraction = 1.0`, exactly 2 outcomes — distributed
  sampling bit-exact up to 36 qubits / 128 GCDs.
- Warm times reproduced across campaigns to within a few percent.
