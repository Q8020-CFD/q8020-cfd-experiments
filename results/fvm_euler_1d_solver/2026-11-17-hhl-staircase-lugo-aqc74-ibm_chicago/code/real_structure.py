# From genode (60ad2c), mesh task 20261117T0342-0001, 2026-11-17, Fable 5.1;
# sha256 of the original in the bus outbox result is listed there.
"""Real-orthogonal structure of L from U alone.

U = exp(iHt) with H = [[0, A], [A^T, 0]] real, so the CSD factors L0, L1 of
U are real up to column phases (up to one unitary per cluster of equal
singular values, as at nelem 10 where one singular value is repeated). real_structure() returns real P, Q in
SO(16) and the Rx angles with U = diag(P, Q) . (+) Rx(theta_i) . diag(P, Q)^T
(a column of P flipped with its theta negated to fix the determinants).
real_demux() is the real Schur demultiplex diag(P, Q) =
(I x V) . diag(S, S^T) . (I x W) with V, W in SO(16) and S a direct sum of
2 x 2 rotations on index pairs (2j, 2j+1): a UCRY on qubit 0 with controls
qubits 1, 2, 3 and the MSB (angle sign flips with the MSB).
Classical work: the same CSD as the rewrite, one real Schur of a 16 x 16
product, matrix products and 2 x 2 arithmetic.
"""
import numpy as np
import scipy.linalg as sla
from qiskit import QuantumCircuit
from qiskit.circuit.library import UCRYGate


def _dephase(m: np.ndarray) -> np.ndarray:
    """Column phases making m real (distinct singular values)."""
    ph = np.empty(m.shape[1], complex)
    for j in range(m.shape[1]):
        k = np.argmax(np.abs(m[:, j]))
        ph[j] = m[k, j] / abs(m[k, j])
    r = m / ph[None, :]
    if np.max(np.abs(r.imag)) > 1e-9:
        raise ValueError("L0/L1 are not real up to column phases")
    return r.real


def _realize(l0: np.ndarray, l1: np.ndarray, cs: np.ndarray, u: np.ndarray,
             tol: float = 1e-9) -> tuple[np.ndarray, np.ndarray]:
    """Real P, Q from the CSD factors. Columns with distinct CS angles get a
    column phase each. A cluster of equal angles (a repeated singular value
    of A) is only determined up to a unitary within the cluster, so P_c is
    taken as a real orthonormal basis of the real span of [Re l0_c, Im l0_c]
    and Q_c follows from U itself: U[h:, :h] = Q (-i sin) P^T, so
    q_j = i U[h:, :h] p_j / sin(cs_j). Matrix products only."""
    h = l0.shape[0]
    order = np.argsort(cs)
    p, q = np.empty((h, h)), np.empty((h, h))
    i = 0
    while i < h:
        j = i + 1
        while j < h and abs(cs[order[j]] - cs[order[i]]) < 1e-7:
            j += 1
        cols = order[i:j]
        if len(cols) == 1:
            p[:, cols] = _dephase(l0[:, cols])
            q[:, cols] = _dephase(l1[:, cols])
        else:
            k = len(cols)
            xy = np.hstack([l0[:, cols].real, l0[:, cols].imag])
            uu, ss, _ = np.linalg.svd(xy, full_matrices=False)
            if ss[k - 1] < 1e-6 or ss[k] > 1e-6:
                raise ValueError("degenerate cluster is not real-spanned")
            pc = uu[:, :k]
            qc = 1j * u[h:, :h] @ pc / np.sin(cs[cols])[None, :]
            if np.max(np.abs(qc.imag)) > tol:
                raise ValueError("degenerate cluster: Q is not real")
            p[:, cols] = pc
            q[:, cols] = qc.real
        i = j
    for name, x in (("P", p), ("Q", q)):
        if np.max(np.abs(x @ x.T - np.eye(h))) > tol:
            raise ValueError(f"{name} is not orthogonal after realization")
    return p, q


def rx2(theta: float) -> np.ndarray:
    c, s = np.cos(theta / 2), np.sin(theta / 2)
    return np.array([[c, -1j * s], [-1j * s, c]])


def real_structure(u: np.ndarray, nb: int, tol: float = 1e-9
                   ) -> tuple[np.ndarray, np.ndarray, np.ndarray, float]:
    """P, Q in SO(h), theta (h), max off-pair error."""
    h = 2 ** (nb - 1)
    (l0, l1), cs, _ = sla.cossin(u, p=h, q=h, separate=True)
    p, q = _realize(l0, l1, cs, u)
    if np.linalg.det(p) < 0 and np.linalg.det(q) < 0:
        p[:, 0] *= -1
        q[:, 0] *= -1
    elif np.linalg.det(p) < 0:
        p[:, 0] *= -1  # flips the sign of theta_0, read off below
    elif np.linalg.det(q) < 0:
        q[:, 0] *= -1
    lr = sla.block_diag(p, q)
    t = lr.T @ u @ lr
    off = t.copy()
    theta = np.empty(h)
    err = 0.0
    for i in range(h):
        ix = [i, i + h]
        b = t[np.ix_(ix, ix)]
        off[np.ix_(ix, ix)] = 0
        theta[i] = 2 * np.arctan2(-b[0, 1].imag, b[0, 0].real)
        err = max(err, float(np.max(np.abs(rx2(theta[i]) - b))))
    offp = float(np.max(np.abs(off)))
    if err > tol or offp > tol:
        raise ValueError(f"real Rx form failed: {err:.1e} {offp:.1e}")
    return p, q, theta, max(err, offp)


def real_demux(p: np.ndarray, q: np.ndarray, tol: float = 1e-9
               ) -> tuple[np.ndarray, np.ndarray, np.ndarray, float]:
    """V, W in SO(h) and phi (h/2) with
    diag(P, Q) = (I x V) diag(S, S^T) (I x W), S = (+)_j R(phi_j) on
    (2j, 2j+1), R(phi) = [[cos, -sin], [sin, cos]] = Ry(2 phi)."""
    h = p.shape[0]
    r, v = sla.schur(p @ q.T, output="real")
    # pair up the 2 x 2 rotation blocks and 1 x 1 real eigenvalues
    i, order, angs = 0, [], []
    ones = []
    while i < h:
        if i + 1 < h and abs(r[i + 1, i]) > 1e-12:
            order += [i, i + 1]
            angs.append(np.arctan2(r[i + 1, i], r[i, i]))
            i += 2
        else:
            ones.append((i, r[i, i]))
            i += 1
    # real eigenvalues: pair equal ones as rotations by 0 or pi
    ones.sort(key=lambda x: x[1])
    if len(ones) % 2:
        raise ValueError("odd number of real eigenvalues")
    for a, b in zip(ones[::2], ones[1::2]):
        if abs(a[1] - b[1]) > 1e-9:
            raise ValueError("det(P Q^T) = -1: unpaired real eigenvalues")
        order += [a[0], b[0]]
        angs.append(0.0 if a[1] > 0 else np.pi)
    v = v[:, order]
    if np.linalg.det(v) < 0:
        # flip one column; inside a rotation pair the sign must flip the
        # sense of rotation, so flip a 1 x 1 pair member if there is one,
        # else flip both members of a pair and keep going
        if ones:
            k = order.index(ones[0][0])
            v[:, k] *= -1
        else:
            v[:, 0] *= -1
            angs[0] = -angs[0]
    phi = np.array(angs)
    s = sla.block_diag(*[np.array([[np.cos(a / 2), -np.sin(a / 2)],
                                   [np.sin(a / 2), np.cos(a / 2)]])
                         for a in phi])
    w = s.T @ v.T @ p
    err = max(float(np.max(np.abs(v @ s @ w - p))),
              float(np.max(np.abs(v @ s.T @ w - q))))
    if err > tol:
        raise ValueError(f"real demux failed: {err:.1e}")
    return v, w, phi, err


def middle_ucry(phi: np.ndarray, nb: int) -> QuantumCircuit:
    """diag(S, S^T) on nb qubits (MSB = nb - 1): UCRY on qubit 0 with
    controls [1 .. nb-2, nb-1]; angle index = lower bits + MSB on top."""
    h2 = len(phi)
    ang = np.concatenate([2 * phi, -2 * phi])  # Ry(2 phi/2 * 2)? see note
    # R(phi/2) = Ry(phi): S holds half angles phi/2 -> Ry angle = phi
    ang = np.concatenate([phi, -phi])
    qc = QuantumCircuit(nb)
    qc.append(UCRYGate(list(ang)), [0] + list(range(1, nb)))
    return qc


def assemble_l(vc: QuantumCircuit, wc: QuantumCircuit, phi: np.ndarray,
               nb: int) -> QuantumCircuit:
    """L = (I x V) . diag(S, S^T) . (I x W) as a circuit on nb qubits."""
    lower = list(range(nb - 1))
    qc = QuantumCircuit(nb)
    qc.compose(wc, lower, inplace=True)
    qc.compose(middle_ucry(phi, nb), inplace=True)
    qc.compose(vc, lower, inplace=True)
    return qc


if __name__ == "__main__":
    from pathlib import Path
    from qiskit import transpile
    from qiskit.quantum_info import Operator
    from qiskit.circuit.library import UnitaryGate
    u = np.load(Path.home() / "q8020/lugo-plus-rewrite-improvements/analysis/U.npy")
    p, q, theta, e1 = real_structure(u, 5)
    v, w, phi, e2 = real_demux(p, q)
    print("dets", np.linalg.det(p), np.linalg.det(q), np.linalg.det(v),
          np.linalg.det(w), "errs", e1, e2)
    print("phi", np.round(phi, 4))
    vc = QuantumCircuit(4); vc.append(UnitaryGate(v), range(4))
    wc = QuantumCircuit(4); wc.append(UnitaryGate(w), range(4))
    lc = assemble_l(vc, wc, phi, 5)
    got = Operator(lc).data
    print("L circuit vs diag(P,Q):", np.max(np.abs(got - sla.block_diag(p, q))))
    t = transpile(middle_ucry(phi, 5), basis_gates=["cx", "rz", "sx", "x"],
                  optimization_level=2, seed_transpiler=1)
    print("middle UCRY cx", t.count_ops().get("cx"))
    np.savez(Path.home() / "q8020/lugo-plus-rewrite-improvements/analysis/real_structure.npz",
             P=p, Q=q, theta=theta, V=v, W=w, phi=phi)
