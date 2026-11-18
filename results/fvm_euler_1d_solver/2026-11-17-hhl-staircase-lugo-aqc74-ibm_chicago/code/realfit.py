# From genode (60ad2c), mesh task 20261117T0342-0001, 2026-11-17, Fable 5.1;
# sha256 of the original in the bus outbox result is listed there.
"""Real (Ry + CX) approximate compiling with analytic gradients.

A circuit is a gate list of ('ry', q) and ('cx', c, t); every Ry carries one
parameter. Little-endian indices as in qiskit (qubit q is bit q). The
objective is 1 - (tr(T^T C) / d)^2 for a real orthogonal target T, so a
global sign is free. Gradients come from one forward and one backward
sweep (prefix products and T^T-suffix products), each gate O(d^2).

Templates:
  spin4(k)       qiskit's make_cnot_network 'spin'/'full' on 4 qubits (the
                 layout the baseline AQC used), Ry-only parametrization;
  line4(k)       nearest-neighbour chain 0-1-2-3;
  bd5(k, every)  5-qubit block-diagonal on qubit 4 (the MSB): qubit 4 is
                 only ever a CX control and carries no rotation, so the
                 unitary is diag(U0, U1) by construction. Lower CX pairs
                 cycle over all 6 pairs (a2a) or a line; every 'every'-th
                 CX has the MSB as control.
"""
import numpy as np
from qiskit import QuantumCircuit
from qiskit.synthesis.unitary.aqc import make_cnot_network
from scipy.optimize import minimize

K2 = np.array([[0.0, -0.5], [0.5, 0.0]])  # d Ry / d theta = K Ry


def ry2(theta: float) -> np.ndarray:
    c, s = np.cos(theta / 2), np.sin(theta / 2)
    return np.array([[c, -s], [s, c]])


class RealCircuit:
    def __init__(self, n: int, gates: list):
        self.n, self.d, self.gates = n, 2 ** n, gates
        self.nparams = sum(1 for g in gates if g[0] == "ry")
        idx = np.arange(self.d)
        self.perm = {}
        for g in gates:
            if g[0] == "cx" and (g[1], g[2]) not in self.perm:
                c, t = g[1], g[2]
                self.perm[(c, t)] = idx ^ (((idx >> c) & 1) << t)

    def ncx(self) -> int:
        return sum(1 for g in self.gates if g[0] == "cx")

    def _left1(self, m: np.ndarray, q: int, g2: np.ndarray) -> np.ndarray:
        """g2 (2x2) on qubit q of the row index of m."""
        ax = self.n - 1 - q
        t = m.reshape((2,) * self.n + (m.shape[1],))
        t = np.moveaxis(np.tensordot(g2, t, axes=([1], [ax])), 0, ax)
        return t.reshape(self.d, m.shape[1])

    def unitary(self, params: np.ndarray) -> np.ndarray:
        m = np.eye(self.d)
        p = 0
        for g in self.gates:
            if g[0] == "ry":
                m = self._left1(m, g[1], ry2(params[p]))
                p += 1
            else:
                m = m[self.perm[(g[1], g[2])]]
        return m

    def value_and_grad(self, params: np.ndarray, tt: np.ndarray):
        """f = 1 - s^2, s = tr(tt C)/d with tt = T^T; and df/dtheta."""
        d = self.d
        m = np.eye(d)
        pref = []
        p = 0
        for g in self.gates:
            if g[0] == "ry":
                m = self._left1(m, g[1], ry2(params[p]))
                pref.append(m)
                p += 1
            else:
                m = m[self.perm[(g[1], g[2])]]
        s = np.trace(tt @ m) / d
        grad = np.empty(self.nparams)
        b = tt.copy()  # B_j = T^T S_j, right-multiplied by G_j going back
        p = self.nparams
        for g in reversed(self.gates):
            if g[0] == "ry":
                p -= 1
                kp = self._left1(pref[p], g[1], K2)
                grad[p] = -2 * s * np.sum(b.T * kp) / d
                # b <- b @ Ry = (Ry^T b^T)^T, Ry^T = Ry(-theta)
                b = self._left1(b.T, g[1], ry2(-params[p])).T
            else:
                b = b[:, self.perm[(g[1], g[2])]]
        return 1 - s * s, grad

    def to_qiskit(self, params: np.ndarray) -> QuantumCircuit:
        qc = QuantumCircuit(self.n)
        p = 0
        for g in self.gates:
            if g[0] == "ry":
                qc.ry(float(params[p]), g[1])
                p += 1
            else:
                qc.cx(g[1], g[2])
        return qc


def with_ry(n: int, cxs: list, rot_qubits=None) -> list:
    """Ry on every rot qubit, then each CX followed by Ry on its control
    and target (if they are rot qubits)."""
    rot = set(range(n) if rot_qubits is None else rot_qubits)
    gates = [("ry", q) for q in sorted(rot)]
    for c, t in cxs:
        gates.append(("cx", c, t))
        for q in (c, t):
            if q in rot:
                gates.append(("ry", q))
    return gates


def spin4(k: int) -> list:
    net = make_cnot_network(num_qubits=4, network_layout="spin",
                            connectivity_type="full", depth=k)
    return with_ry(4, [(int(net[0, i]), int(net[1, i])) for i in range(k)])


def line4(k: int) -> list:
    net = make_cnot_network(num_qubits=4, network_layout="spin",
                            connectivity_type="line", depth=k)
    return with_ry(4, [(int(net[0, i]), int(net[1, i])) for i in range(k)])


def cycle4(k: int, pairs: list) -> list:
    """k CX cycling over pairs, direction alternating each round."""
    cxs = []
    for i in range(k):
        a, b = pairs[i % len(pairs)]
        if (i // len(pairs)) % 2:
            a, b = b, a
        cxs.append((a, b))
    return with_ry(4, cxs)


def pair4(k: int) -> list:
    """All-to-all, two disjoint CX per layer: depth k/2."""
    return cycle4(k, [(0, 1), (2, 3), (0, 2), (1, 3), (0, 3), (1, 2)])


def ring4(k: int) -> list:
    """Square 0-1-2-3-0 (native on a square lattice), depth k/2."""
    return cycle4(k, [(0, 1), (2, 3), (1, 2), (3, 0)])


def star4(k: int) -> list:
    """Star centred on qubit 0 (serial, depth k)."""
    return cycle4(k, [(0, 1), (0, 2), (0, 3)])


TEMPLATES4 = {"spin4": spin4, "line4": line4, "pair4": pair4,
              "ring4": ring4, "star4": star4}


def bd5(k: int, every: int = 6, lower: str = "a2a", seed: int = 0,
        msb_targets=None) -> list:
    """Block-diagonal 5-qubit template: k CX, qubit 4 (MSB) control-only.
    lower: a2a (6 pairs, depth k/2), line (0-1-2-3), ring (0-1-2-3-0).
    Every 'every'-th CX is MSB -> one of msb_targets (default: all lower
    qubits for a2a, the ends 0 and 3 for line, 0 for ring)."""
    pairs = {"a2a": [(0, 1), (2, 3), (1, 2), (0, 3), (0, 2), (1, 3)],
             "line": [(0, 1), (2, 3), (1, 2)],
             "ring": [(0, 1), (2, 3), (1, 2), (3, 0)]}[lower]
    if msb_targets is None:
        msb_targets = {"a2a": [0, 1, 2, 3], "line": [0, 3], "ring": [0]}[lower]
    cxs, i, j = [], 0, 0
    while len(cxs) < k:
        if every and (len(cxs) + 1) % every == 0:
            cxs.append((4, msb_targets[j % len(msb_targets)]))
            j += 1
        else:
            a, b = pairs[i % len(pairs)]
            if (i // len(pairs)) % 2 == 1:
                a, b = b, a
            cxs.append((a, b))
            i += 1
    return with_ry(5, cxs, rot_qubits=[0, 1, 2, 3])


def fit(gates: list, n: int, target: np.ndarray, seed: int,
        maxiter: int = 20000, x0=None) -> tuple[float, np.ndarray, int]:
    """L-BFGS-B fit; returns (1 - F, params, iterations)."""
    rc = RealCircuit(n, gates)
    tt = np.ascontiguousarray(target.T)
    rng = np.random.default_rng(seed)
    if x0 is None:
        x0 = rng.uniform(-np.pi, np.pi, rc.nparams)
    res = minimize(lambda x: rc.value_and_grad(x, tt), x0, jac=True,
                   method="L-BFGS-B",
                   options={"maxiter": maxiter, "maxfun": 4 * maxiter,
                            "ftol": 1e-17, "gtol": 1e-13})
    return float(res.fun), res.x, int(res.nit)


def infidelity(circ_u: np.ndarray, target: np.ndarray) -> float:
    d = target.shape[0]
    return 1 - abs(np.trace(target.conj().T @ circ_u)) ** 2 / d ** 2


if __name__ == "__main__":
    # self-test: gradient and qiskit agreement
    from qiskit.quantum_info import Operator
    g = bd5(20, every=5)
    rc = RealCircuit(5, g)
    x = np.random.default_rng(1).uniform(-3, 3, rc.nparams)
    u = rc.unitary(x)
    assert np.allclose(u @ u.T, np.eye(32))
    assert np.max(np.abs(u[:16, 16:])) < 1e-14, "not block diagonal"
    assert np.allclose(Operator(rc.to_qiskit(x)).data, u, atol=1e-12)
    t = RealCircuit(5, g).unitary(np.random.default_rng(2).uniform(-3, 3, rc.nparams))
    f, gr = rc.value_and_grad(x, t.T)
    num = np.empty_like(gr)
    for i in range(len(x)):
        e = np.zeros_like(x)
        e[i] = 1e-6
        num[i] = (rc.value_and_grad(x + e, t.T)[0]
                  - rc.value_and_grad(x - e, t.T)[0]) / 2e-6
    print("grad max abs err", np.max(np.abs(num - gr)), "f", f)
    g4 = spin4(10)
    rc4 = RealCircuit(4, g4)
    x4 = np.random.default_rng(3).uniform(-3, 3, rc4.nparams)
    assert np.allclose(Operator(rc4.to_qiskit(x4)).data, rc4.unitary(x4),
                       atol=1e-12)
    print("ok; bd5(20) params", rc.nparams, "spin4(10) params", rc4.nparams)
