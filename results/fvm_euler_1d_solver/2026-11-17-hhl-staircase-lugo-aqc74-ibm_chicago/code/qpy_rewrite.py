"""Exact, depth-reducing rewrite of an fvm HHL circuit stored as qpy.

The only input is the circuit itself: a generated (untranspiled) HHL circuit
from the fvm nozzle solver with the LuGo QPE, e.g. the 2026-02-26 run's
circuit_generated_nelem5_iter0.qpy. Its top level is: state preparation of b
on the nb system qubits, 'QPE' on system + nl clock qubits, '1/x' on clock +
ancilla, 'inv_QPE', a barrier and the measurements.

What the rewrite does:

1. QPE and inv_QPE. Every instruction inside them that acts on nb + 1 qubits
   is a controlled-U^(2^k) block (one clock qubit plus the system register).
   Its 2^(nb+1) x 2^(nb+1) unitary is computed from the stored gates and the
   block is replaced by qiskit's quantum Shannon decomposition of that
   matrix (qs_decomposition). The H gates and the QFT inside QPE are kept.
2. 1/x. Its 2^(nl+1) x 2^(nl+1) unitary is computed and checked to be a
   uniformly controlled RY on the ancilla (its last qubit), controlled by the
   nl clock qubits: block diagonal over the clock values, with a real 2 x 2
   rotation on the ancilla in each block. The 2^nl angles are read from the
   matrix and the block is replaced by one UCRYGate. If the check fails the
   block is kept unchanged.
3. Everything else (state preparation, barrier, measurements) is kept.

Every replaced block is checked against the stored one by matrix equality,
global phase included (max abs entry difference below TOL). Nothing is
learned about the matrix A beyond what each block's own unitary holds: no
eigendecomposition is used and blocks are not merged.

CLI: qpy_rewrite.py <in.qpy> [-o out.qpy]
"""

import argparse
import sys
import time
from dataclasses import dataclass, field

import numpy as np
from qiskit import QuantumCircuit, qpy
from qiskit.circuit import library as qlib
from qiskit.circuit.library import ExactReciprocalGate, UCRYGate
from qiskit.quantum_info import Operator
from qiskit.synthesis.unitary.qsd import qs_decomposition

TOL = 1e-9


@dataclass
class RewriteReport:
    nb: int = 0
    nl: int = 0
    blocks_replaced: int = 0
    block_max_err: float = 0.0
    recip_replaced: bool = False
    recip_max_err: float = 0.0
    seconds: float = 0.0
    notes: list = field(default_factory=list)


def load_qpy(path: str,
             recip: tuple[int, float, bool] | None = None) -> QuantumCircuit:
    """Load a qpy circuit.

    qiskit 2.x writes ExactReciprocalGate with no parameters, so neither
    qpy.load nor the file knows its size, scaling or neg_vals and the load
    fails with a TypeError (the nov26 LuGo generated circuit). With recip =
    (nl, scaling, neg_vals) the gate is rebuilt as ExactReciprocalGate(nl,
    scaling, neg_vals); the caller must supply values it can vouch for (see
    recip_params and the checks in run_step0.py). Without recip the plain
    loader is used, unchanged.
    """
    with open(path, "rb") as fh:
        if recip is None:
            return qpy.load(fh)[0]
        nl, scaling, neg_vals = recip

        class Stub(ExactReciprocalGate):
            def __init__(self, label: str = "1/x") -> None:
                super().__init__(nl, scaling, neg_vals, label)

        orig = qlib.ExactReciprocalGate
        qlib.ExactReciprocalGate = Stub
        try:
            return qpy.load(fh)[0]
        finally:
            qlib.ExactReciprocalGate = orig


def recip_angles(op) -> np.ndarray:
    """Rotation angle on the ancilla for each state value c of a 1/x block
    that is a uniformly controlled RY (state qubits first, ancilla last)."""
    mat = Operator(op).data
    h = 2 ** (op.num_qubits - 1)
    return np.array([2 * np.arctan2(mat[c + h, c].real, mat[c, c].real)
                     for c in range(h)])


def recip_params(circ: QuantumCircuit) -> tuple[int, float, bool]:
    """(nl, scaling, neg_vals) of a circuit's 1/x block that stores it as a
    unitary, so that ExactReciprocalGate(nl, scaling, neg_vals) is equal to it.

    Both sign conventions are tried. For neg_vals False the positive
    rotation 2 arcsin(scaling 2^nl / c) runs over c = 1 .. 2^nl - 1; for True
    it runs over c = 1 .. 2^(nl-1) - 1 and the upper half is the negative
    branch. The scaling is read from the positive angles; a candidate is
    accepted only if the rebuilt gate equals the stored block to 1e-9.
    """
    op = _top(circ, "1/x").operation
    nl = op.num_qubits - 1
    ang = recip_angles(op)
    want = Operator(op).data
    for neg in (False, True):
        half = 2 ** nl >> int(neg)
        c = np.arange(half)
        ok = (c > 0) & (ang[:half] > 1e-9) & (ang[:half] < np.pi - 1e-6)
        s = np.sin(ang[:half][ok] / 2) * c[ok] / half
        if not len(s) or np.ptp(s) > 1e-9:
            continue
        gate = ExactReciprocalGate(nl, float(s.mean()), neg)
        if np.max(np.abs(Operator(gate).data - want)) < 1e-9:
            return nl, float(s.mean()), neg
    raise ValueError("1/x is not an ExactReciprocal rotation")


def _qidx(circ: QuantumCircuit, ins) -> list[int]:
    return [circ.find_bit(q).index for q in ins.qubits]


def _top(circ: QuantumCircuit, name: str):
    hits = [i for i in circ.data if i.operation.name == name]
    if len(hits) != 1:
        raise ValueError(f"expected one top-level '{name}', found {len(hits)}")
    return hits[0]


def _exact_qsd(mat: np.ndarray) -> tuple[QuantumCircuit, float]:
    """QSD of mat, global phase fixed so the circuit equals mat exactly."""
    qc = qs_decomposition(mat)
    got = Operator(qc).data
    k = np.unravel_index(np.argmax(np.abs(mat)), mat.shape)
    qc.global_phase += np.angle(mat[k] / got[k])
    err = float(np.max(np.abs(Operator(qc).data - mat)))
    return qc, err


def _rewrite_qpe(defn: QuantumCircuit, nb: int, rep: RewriteReport):
    out = QuantumCircuit(defn.num_qubits, global_phase=defn.global_phase)
    for ins in defn.data:
        op, idx = ins.operation, _qidx(defn, ins)
        if op.num_qubits == nb + 1:
            mat = Operator(op).data
            qc, err = _exact_qsd(mat)
            if err > TOL:
                raise RuntimeError(f"block {op.name}: QSD error {err:.2e}")
            out.compose(qc, qubits=idx, inplace=True)
            rep.blocks_replaced += 1
            rep.block_max_err = max(rep.block_max_err, err)
        else:
            out.append(op, idx)
    return out


def _rewrite_recip(op, rep: RewriteReport):
    """1/x as one UCRYGate if its unitary is a multiplexed RY on the ancilla."""
    mat = Operator(op).data
    n = op.num_qubits
    h = 2 ** (n - 1)
    off = mat.copy()
    ang = np.empty(h)
    for c in range(h):
        blk = mat[np.ix_([c, c + h], [c, c + h])]
        ang[c] = 2 * np.arctan2(blk[1, 0].real, blk[0, 0].real)
        off[np.ix_([c, c + h], [c, c + h])] = 0
    qc = QuantumCircuit(n)
    qc.append(UCRYGate(list(ang)), [n - 1] + list(range(n - 1)))
    err = float(np.max(np.abs(Operator(qc).data - mat)))
    if np.max(np.abs(off)) > TOL or err > TOL:
        rep.notes.append(f"1/x kept: not a pure multiplexed RY (err {err:.1e})")
        return None
    rep.recip_replaced = True
    rep.recip_max_err = err
    return qc


def rewrite(circ: QuantumCircuit) -> tuple[QuantumCircuit, RewriteReport]:
    """Return the rewritten circuit and a report. See the module docstring."""
    t0 = time.time()
    rep = RewriteReport()
    qpe = _top(circ, "QPE")
    recip = _top(circ, "1/x")
    rep.nl = recip.operation.num_qubits - 1
    rep.nb = qpe.operation.num_qubits - rep.nl
    out = QuantumCircuit(*circ.qregs, *circ.cregs,
                         global_phase=circ.global_phase)
    for ins in circ.data:
        op, idx = ins.operation, _qidx(circ, ins)
        cl = [circ.find_bit(c).index for c in ins.clbits]
        if op.name in ("QPE", "inv_QPE"):
            new = _rewrite_qpe(op.definition, rep.nb, rep)
            out.append(new.to_instruction(label=op.name), idx)
        elif op.name == "1/x":
            new = _rewrite_recip(op, rep)
            out.append(new.to_instruction(label="1/x") if new else op, idx)
        else:
            out.append(op, idx, cl)
    rep.seconds = time.time() - t0
    return out, rep


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("qpy_in")
    ap.add_argument("-o", "--out", help="write the rewritten circuit as qpy")
    a = ap.parse_args()
    circ = load_qpy(a.qpy_in)
    new, rep = rewrite(circ)
    print(rep)
    if a.out:
        with open(a.out, "wb") as fh:
            qpy.dump(new, fh)
        print(f"wrote {a.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
