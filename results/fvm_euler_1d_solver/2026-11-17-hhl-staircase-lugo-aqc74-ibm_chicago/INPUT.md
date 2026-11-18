# Input circuit and layout: how to regenerate them

The same staircase as `../2026-11-17-hhl-staircase-lugo-aqc74-ibm_boston/`,
run on ibm_chicago (IBM Nighthawk r2). Its input circuit is not kept here
because it is deterministic to rebuild: the LuGo step-0 circuit of nelem 5,
rewritten with the real-L structured rewrite and L fitted by AQC at 74 CX,
with barriers after every block. The recipe is in the ibm_boston folder's
`INPUT.md`; the modules are in `code/`.

The input for this run was rebuilt on 2026-11-17 from that recipe. It is
the same circuit as the ibm_boston run's: the same instruction sequence, all
10112 float parameters exactly equal, and the same L infidelity,
0.07030746484048156. Its file's sha256 (`input_sha256` in `prep.json`)
differs from the ibm_boston input's, so compare a rebuild by its
instructions and parameters, not by the file's sha256.

The physical qubits come from `layout-from-prep.json`: the `ibm_submit.py`
dry run of the full circuit on ibm_chicago at 2026-11-17T23:15:10Z, best of
6 layout seeds (seed 2, 4205 two-qubit gates, log ESP -7.59). The same dry
run on ibm_phoenix, the other Nighthawk r2, gave a best log ESP of -9.82,
which is why ibm_chicago was chosen. The staircase steps were transpiled onto
those 14 qubits with `initial_layout` and seed 1, by `ibm_staircase.py` in
`code/`.
