# Input circuit and layout: how to regenerate them

The staircase steps were cut from one input circuit, which is not kept here
because it is deterministic to rebuild (1129216 bytes, sha256
`b2f7ceb971c02915aafbd7464f0d505a3438b5a683b76464230fae85239d81e5`, the
`input_sha256` in `prep.json`). It is the LuGo step-0 circuit of nelem 5,
rewritten with the real-L structured rewrite and L fitted by AQC at 74 CX,
with barriers after every block:

- input: `results/fvm_euler_1d_solver/2026-02-26-LuGo/circuits/circuit_generated_nelem5_iter0.qpy`
  (sha256 `2c8b064d6e38442125d4d7ab599da49f3003b52d53f283dd617501e29808bd56`);
- build, with the modules in `code/` on the path:

  ```python
  import structured_rewrite as sr
  from qiskit import qpy
  circ = qpy.load(open(INPUT, "rb"))[0]
  items, nb, nl = sr.walk(circ)
  mats = sr.block_unitaries(items)
  new, rep = sr.build(circ, items, nb, mats, barriers=True,
                      real_l=sr.RealL(cx=74))
  ```

  The build picks AQC seed 3 of 1 to 3 (L infidelity 0.0703), gives 180 CX
  per block and 3274 CX all-to-all, as in
  `../2026-11-17-hhl-structured-rewrite-from-lugo/nelem5-barriers-realL-aqc74/`.
  The input was built this way on 2026-11-17 and rebuilt for the ibm_chicago
  staircase the same evening. The rebuild is the same circuit: the same
  instruction sequence, all 10112 float parameters exactly equal, and the same
  L infidelity, 0.07030746484048156. Its file's sha256 still differs from
  the first build's. Why was not pinned down: in one test a freshly built
  circuit gave different bytes on a first and a second dump, while a circuit
  loaded from qpy dumped identically. Compare a rebuild by its instructions
  and parameters, not by the file's sha256.

The physical qubits come from `layout-from-prep.json`: the `ibm_submit.py`
dry run of the full circuit on ibm_boston at 2026-11-17T18:57:43Z, best of 6
layout seeds (seed 6, 4727 two-qubit gates). The staircase steps were
transpiled onto those 14 qubits with `initial_layout` and seed 1, by
`ibm_staircase.py` in `code/`.
