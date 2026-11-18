"""Exact structured rewrite of an fvm HHL circuit stored as qpy.

Input: the generated (untranspiled) HHL circuit, either the LuGo one (e.g.
2026-02-26-LuGo/circuits/circuit_generated_nelem5_iter0.qpy: flat QPE and
inv_QPE, one block per power) or the pre-LuGo one (QPE holds
controlled-(U circuit)^(2^k) per clock qubit k).

Classical work. LuGo builds every block with qiskit's quantum Shannon
decomposition (QSD) of U^(+-2^k) and controls it gate by gate (verified: its
base circuits equal qiskit 1.2.4 qs_decomposition gate for gate). The rewrite
takes those QSD intermediate values as available and recomputes the ones it
needs, since LuGo's code is not:

1. U, multiplying out the gates of LuGo's first block (U^1).
2. QSD's first step for U^1: the cosine-sine decomposition (CSD) of U split
   on the system MSB (the same scipy.linalg.cossin call qs_decomposition
   makes). L = L0 (+) L1 is block diagonal and T = L^dag U L a direct sum of
   2 x 2 blocks; each is put in the form D_i^dag Rx(theta_i) D_i with D_i
   diagonal, and D is folded into L (matrix products, no decomposition).
3. QSD's next level for L: the demultiplex (Schur of a 16 x 16 product, as
   in qs_decomposition's _demultiplex) into W, a UCRZ and V, and the
   synthesis of the 4-qubit W and V (qs_decomposition, exact). It runs on
   L with D folded in, so its values differ from LuGo's by that diagonal.

All 16 blocks then follow: controlled-U^m (m = +-2^k, read from the block
name, or for LuGo found by matching the block unitary) is
    L^dag . H(msb) . UCRZ(m theta on clock 1, 0 on clock 0) . H(msb) . L
with L^dag the circuit inverse of L. Only the middle UCRZ is controlled.
1/x becomes one UCRYGate (from the sibling lugo-qpy-rewrite-2026-11).
Totals: one CSD, one demultiplex, two 4-qubit QSDs, against LuGo's 16
QSDs. A second pass may replace the QSD of W and V by AQC (a numerical fit,
approximate in principle, with no counterpart in LuGo).

Each block can be checked against the stored block's 64 x 64 unitary,
global phase included. Blocks are not merged with each other: every block
keeps its own L and L^dag.

CLI: structured_rewrite.py <in.qpy> [-o out.qpy] [--aqc 62,64,68,72]
"""

import argparse
import re
import sys
import time
from dataclasses import dataclass, field
from functools import partial
from pathlib import Path
from typing import Callable

import numpy as np
import scipy.linalg as sla
from qiskit import QuantumCircuit, qpy, transpile
from qiskit.circuit.library import StatePreparation, UCRZGate, UnitaryGate
from qiskit.quantum_info import Operator
from qiskit.synthesis.unitary.aqc import (AQC, CNOTUnitCircuit,
                                          FastCNOTUnitObjective,
                                          make_cnot_network)
from qiskit.synthesis.unitary.qsd import qs_decomposition
from scipy.optimize import minimize

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "lugo-qpy-rewrite-2026-11"))
from qpy_rewrite import RewriteReport, _rewrite_recip  # noqa: E402

sys.path.insert(0, str(HERE))
import real_structure as rs  # noqa: E402
import realfit as rf  # noqa: E402

TOL = 1e-9
BASIS = ["cx", "rz", "sx", "x"]
Synth = Callable[[np.ndarray], QuantumCircuit]


@dataclass
class Report:
    nb: int = 0
    nl: int = 0
    blocks: int = 0
    block_max_err: float = 0.0
    l_err: float = 0.0
    t_offpair: float = 0.0
    recip_err: float = 0.0
    cx_per_block: int = 0
    cx_l: int = 0
    seconds: float = 0.0
    powers: list = field(default_factory=list)


def qidx(c: QuantumCircuit, ins) -> list[int]:
    return [c.find_bit(q).index for q in ins.qubits]


def power_of(name: str) -> int | None:
    """Exponent m of a pre-LuGo QPE block from its name, e.g.
    'ccircuit-451**8_dg' -> -8. None for LuGo blocks, whose names carry no
    power ('c_circuit-452'); build() then finds m from the block unitary."""
    hit = re.search(r"\*\*(\d+)(_dg)?$", name)
    if not hit:
        return None
    return -int(hit.group(1)) if hit.group(2) else int(hit.group(1))


QPE_NAMES = ("QPE", "QPE_dg", "inv_QPE")
SP_NAMES = ("initialize", "state_preparation")


def walk(circ: QuantumCircuit) -> tuple[list, int, int]:
    """Flatten to [(kind, payload, qubits)]: kind sp (b vector), block
    ((op, m)), recip (op) or op. Reads the pre-LuGo layout (QPE wraps one
    inner QPE gate, blocks named ...**2^k) and LuGo's (flat QPE and inv_QPE,
    blocks c_circuit-*). Returns items, nb, nl."""
    top = {i.operation.name: i for i in circ.data}
    nl = top["1/x"].operation.num_qubits - 1
    nb = top["QPE"].operation.num_qubits - nl
    items = []
    for ins in circ.data:
        op, idx = ins.operation, qidx(circ, ins)
        if op.name in ("barrier", "measure"):
            continue
        if op.name in QPE_NAMES:
            d = op.definition
            while (len(d.data) == 1
                   and d.data[0].operation.num_qubits == op.num_qubits):
                inner = d.data[0]
                idx = [idx[j] for j in qidx(d, inner)]
                d = inner.operation.definition
            for sub in d.data:
                sidx = [idx[j] for j in qidx(d, sub)]
                so = sub.operation
                if so.num_qubits == nb + 1:
                    items.append(("block", (so, power_of(so.name)), sidx))
                else:
                    items.append(("op", so, sidx))
        elif op.name == "1/x":
            items.append(("recip", op, idx))
        elif (op.definition is not None
              and op.definition.data[0].operation.name in SP_NAMES):
            b = np.array(op.definition.data[0].operation.params, complex)
            items.append(("sp", b, idx))
        else:
            items.append(("op", op, idx))
    return items, nb, nl


def match_power(lp: np.ndarray, theta: np.ndarray, u_blk: np.ndarray,
                nl: int) -> tuple[int, float]:
    """m in {+-2^k} with L' Rx(m theta) L'^dag closest to u_blk."""
    h = len(theta)
    best = (0, np.inf)
    for k in range(nl):
        for m in (2 ** k, -2 ** k):
            r = np.zeros((2 * h, 2 * h), complex)
            c, s_ = np.cos(m * theta / 2), -1j * np.sin(m * theta / 2)
            ii = np.arange(h)
            r[ii, ii], r[ii + h, ii + h] = c, c
            r[ii, ii + h], r[ii + h, ii] = s_, s_
            err = float(np.max(np.abs(lp @ r @ lp.conj().T - u_blk)))
            if err < best[1]:
                best = (m, err)
    return best


def block_unitaries(items: list) -> list[np.ndarray]:
    """64 x 64 unitary of every stored block, in circuit order (slow)."""
    return [Operator(p[0]).data for k, p, _ in items if k == "block"]


def structure(u: np.ndarray, nb: int) -> tuple[np.ndarray, np.ndarray, float]:
    """L' (block diagonal on the MSB) and Rx angles with U = L' R L'^dag."""
    h = 2 ** (nb - 1)
    (l0, l1), _, _ = sla.cossin(u, p=h, q=h, separate=True)
    lm = sla.block_diag(l0, l1)
    t = lm.conj().T @ u @ lm
    off = t.copy()
    theta, beta = np.empty(h), np.empty(h)
    for i in range(h):
        ix = [i, i + h]
        b = t[np.ix_(ix, ix)]
        off[np.ix_(ix, ix)] = 0
        if abs(np.linalg.det(b) - 1) > 1e-9 or abs(b[0, 0] - b[1, 1]) > 1e-9:
            raise ValueError(f"T block {i} is not of the form D^dag Rx D")
        half = np.arccos(np.clip(b[0, 0].real, -1, 1))
        theta[i] = 2 * half
        beta[i] = np.angle(1j * b[0, 1]) if np.sin(half) > 1e-12 else 0.0
        dd = np.diag([1, np.exp(1j * beta[i])])
        rx = np.array([[np.cos(half), -1j * np.sin(half)],
                       [-1j * np.sin(half), np.cos(half)]])
        if np.max(np.abs(dd.conj().T @ rx @ dd - b)) > 1e-9:
            raise ValueError(f"T block {i}: Rx normal form failed")
    lp = sla.block_diag(l0, l1 @ np.diag(np.exp(-1j * beta)))
    return lp, theta, float(np.max(np.abs(off)))


def qsd_synth(mat: np.ndarray) -> QuantumCircuit:
    """Exact qs_decomposition with the global phase fixed."""
    sub = qs_decomposition(mat)
    got = Operator(sub).data
    k = np.unravel_index(np.argmax(np.abs(mat)), mat.shape)
    sub.global_phase += np.angle(mat[k] / got[k])
    return sub


def aqc_factory(cx_list: list[int], seeds: list[int], tol: float,
                log=print, info: list | None = None):
    """AQC synthesis for the 4-qubit pieces of L: the first CX count in
    cx_list (any seed) with 1 - F <= tol, else the best found. Each
    piece is recorded in info as {cx, seed, infidelity}."""
    info = [] if info is None else info

    def synth(mat: np.ndarray) -> QuantumCircuit:
        n = int(np.log2(mat.shape[0]))
        dim = 2 ** n
        su = mat / np.linalg.det(mat) ** (1 / dim)
        best = None
        for cx in cx_list:
            for seed in seeds:
                t0 = time.time()
                net = make_cnot_network(num_qubits=n, network_layout="spin",
                                        connectivity_type="full", depth=cx)
                circ = CNOTUnitCircuit(n, net)
                opt = partial(minimize, args=(), method="L-BFGS-B",
                              options={"maxiter": 20000, "ftol": 1e-16,
                                       "gtol": 1e-12})
                AQC(optimizer=opt, seed=seed).compile_unitary(
                    target_matrix=su, approximate_circuit=circ,
                    approximating_objective=FastCNOTUnitObjective(n, net))
                qc = QuantumCircuit(n).compose(circ)
                got = Operator(qc).data
                inf = 1 - abs(np.trace(got.conj().T @ mat)) ** 2 / dim ** 2
                log(f"  AQC piece {len(info)}: cx {cx} seed {seed} "
                    f"1-F {inf:.2e} ({time.time() - t0:.0f} s)")
                if best is None or inf < best[0]:
                    best = (inf, cx, seed, qc)
                if inf <= tol:
                    break
            if best[0] <= tol:
                break
        inf, cx, seed, qc = best
        got = Operator(qc).data
        k = np.unravel_index(np.argmax(np.abs(mat)), mat.shape)
        qc.global_phase += np.angle(mat[k] / got[k])
        info.append({"cx": cx, "seed": seed, "infidelity": inf})
        return qc
    return synth


def demux_circuit(lp: np.ndarray, nb: int,
                  synth: Synth = qsd_synth) -> tuple[QuantumCircuit, float]:
    """Circuit for block-diagonal lp = diag(U0, U1) on the MSB: W, UCRZ, V.
    Returns the circuit (cx/rz/sx/x) and its max entry error against lp."""
    h = 2 ** (nb - 1)
    u0, u1 = lp[:h, :h], lp[h:, h:]
    tt, v = sla.schur(u0 @ u1.conj().T, output="complex")
    d = np.sqrt(np.diag(tt))
    w = np.diag(d) @ v.conj().T @ u1
    lower = list(range(nb - 1))
    qc = QuantumCircuit(nb)
    qc.compose(synth(w), lower, inplace=True)
    qc.append(UCRZGate(list(-2 * np.angle(d))), [nb - 1] + lower)
    qc.compose(synth(v), lower, inplace=True)
    qc = transpile(qc, basis_gates=BASIS, optimization_level=2,
                   seed_transpiler=1)
    got = Operator(qc).data
    k = np.unravel_index(np.argmax(np.abs(lp)), lp.shape)
    qc.global_phase += np.angle(lp[k] / got[k])
    return qc, float(np.max(np.abs(Operator(qc).data - lp)))


def block_circuit(lc: QuantumCircuit, theta: np.ndarray, m: int,
                  nb: int) -> QuantumCircuit:
    """Controlled-U^m on [clock, sys 0..nb-1]: L^dag, H, c-UCRZ, H, L."""
    sysq = list(range(1, nb + 1))
    msb = nb
    qc = QuantumCircuit(nb + 1)
    qc.compose(lc.inverse(), sysq, inplace=True)
    qc.h(msb)
    ang = np.concatenate([np.zeros(len(theta)), m * theta])
    # UCRZ controls: lower system qubits, then the clock as the top bit
    qc.append(UCRZGate(list(ang)), [msb] + sysq[:-1] + [0])
    qc.h(msb)
    qc.compose(lc, sysq, inplace=True)
    return qc


@dataclass
class RealL:
    """Real-L synthesis: L = diag(P, Q) fitted with real gates (Ry + CX) on
    genode's block-diagonal 5-qubit template (realfit.bd5). At the default
    122 CX the fit is exact (1 - F ~ 1e-13); fewer CX is approximate (AQC).
    The fit is accepted at the first seed with 1 - F <= tol against
    diag(P, Q) itself, else the best seed: never by the HHL solution."""
    cx: int = 122
    every: int = 24
    lower: str = "line"
    msb_targets: tuple = (0,)
    seeds: tuple = (1, 2, 3)
    tol: float = 1e-12
    maxiter: int = 20000
    info: dict = field(default_factory=dict)


def real_l_circuit(u: np.ndarray, nb: int, cfg: RealL
                   ) -> tuple[QuantumCircuit, np.ndarray, np.ndarray, float]:
    """L circuit, L (= diag(P, Q)), Rx angles and max entry error. U must be
    real up to column phases in its CSD factors (A real): real_structure
    raises otherwise, so the assumption is checked, not taken on trust."""
    p, q, theta, err_s = rs.real_structure(u, nb)
    lp = sla.block_diag(p, q)
    gates = rf.bd5(cfg.cx, every=cfg.every, lower=cfg.lower,
                   msb_targets=list(cfg.msb_targets))
    best = None
    for seed in cfg.seeds:
        t0 = time.time()
        inf, x, nit = rf.fit(gates, nb, lp, seed, cfg.maxiter)
        cfg.info.setdefault("tries", []).append(
            {"seed": seed, "infidelity": inf, "iterations": nit,
             "seconds": round(time.time() - t0, 1)})
        if best is None or inf < best[0]:
            best = (inf, x, seed)
        if inf <= cfg.tol:
            break
    inf, x, seed = best
    lc = rf.RealCircuit(nb, gates).to_qiskit(x)
    lc = transpile(lc, basis_gates=BASIS, optimization_level=2,
                   seed_transpiler=1)
    got = Operator(lc).data
    k = np.unravel_index(np.argmax(np.abs(lp)), lp.shape)
    lc.global_phase += np.angle(lp[k] / got[k])
    err = float(np.max(np.abs(Operator(lc).data - lp)))
    cfg.info.update({"cx": cfg.cx, "every": cfg.every, "lower": cfg.lower,
                     "msb_targets": list(cfg.msb_targets), "seed": seed,
                     "infidelity": inf, "real_structure_err": err_s})
    return lc, lp, theta, err


def build(circ: QuantumCircuit, items: list, nb: int, mats: list,
          synth: Synth = qsd_synth, check: bool = True,
          barriers: bool = False, real_l: RealL | None = None
          ) -> tuple[QuantumCircuit, Report]:
    """Rewritten circuit (no measurements) and a report. mats are the stored
    block unitaries (block_unitaries); the first must be controlled-U^1.
    With barriers, a barrier follows every block, so the transpiler cannot
    cancel one block's L against the next block's L^dag (without them,
    qiskit level 2 removes about 150 CX at the seams at nelem 5).
    With real_l, L is the real block-diagonal fit (RealL) instead of the
    complex demultiplex; synth is then unused."""
    t0 = time.time()
    rep = Report(nb=nb)
    first = mats[0]
    if not np.allclose(first[0::2, 0::2], np.eye(2 ** nb), atol=TOL):
        raise ValueError("first block is not controlled on bit 0")
    if real_l is None:
        lp, theta, rep.t_offpair = structure(first[1::2, 1::2], nb)
        lc, rep.l_err = demux_circuit(lp, nb, synth)
    else:
        lc, lp, theta, rep.l_err = real_l_circuit(first[1::2, 1::2], nb,
                                                  real_l)
    rep.cx_l = lc.count_ops().get("cx", 0)
    nl = sum(1 for k, _, _ in items if k == "block") // 2
    out = QuantumCircuit(*circ.qregs)
    bi = 0
    for kind, p, idx in items:
        if kind == "sp":
            out.append(StatePreparation(p), idx)
        elif kind == "block":
            so, m = p
            if m is None:  # LuGo: find the power from the block unitary
                m, err = match_power(lp, theta, mats[bi][1::2, 1::2], nl)
                if err > 1e-8:
                    raise ValueError(f"block {bi} is no power of U "
                                     f"(best m {m}, err {err:.1e})")
            if bi == 0 and m != 1:
                raise ValueError("first QPE block is not U^1")
            bc = block_circuit(lc, theta, m, nb)
            if check:
                err = float(np.max(np.abs(Operator(bc).data - mats[bi])))
                rep.block_max_err = max(rep.block_max_err, err)
            out.compose(bc, idx, inplace=True)
            if barriers:
                out.barrier()
            rep.powers.append(m)
            bi += 1
        elif kind == "recip":
            rr = RewriteReport()
            new = _rewrite_recip(p, rr)
            if new is None:
                raise RuntimeError("1/x is not a multiplexed RY")
            rep.nl = p.num_qubits - 1
            rep.recip_err = rr.recip_max_err
            out.compose(new, idx, inplace=True)
        else:
            out.append(p, idx)
    rep.blocks = bi
    one = transpile(block_circuit(lc, theta, 1, nb), basis_gates=BASIS,
                    optimization_level=2, seed_transpiler=1)
    rep.cx_per_block = one.count_ops().get("cx", 0)
    rep.seconds = time.time() - t0
    return out, rep


def reference(circ: QuantumCircuit, items: list, mats: list
              ) -> QuantumCircuit:
    """The stored circuit with each block as its exact 64 x 64 unitary."""
    out = QuantumCircuit(*circ.qregs)
    bi = 0
    for kind, p, idx in items:
        if kind == "sp":
            out.append(StatePreparation(p), idx)
        elif kind == "block":
            out.append(UnitaryGate(mats[bi], check_input=False), idx)
            bi += 1
        else:
            out.append(p, idx)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("qpy_in")
    ap.add_argument("-o", "--out", help="write the rewritten circuit as qpy")
    ap.add_argument("--aqc", help="AQC CX counts to try for W and V, e.g. "
                    "62,64,68,72 (default: exact qs_decomposition)")
    ap.add_argument("--aqc-tol", type=float, default=1e-11)
    ap.add_argument("--barriers", action="store_true",
                    help="barrier after every block (strictly per-block)")
    a = ap.parse_args()
    with open(a.qpy_in, "rb") as fh:
        circ = qpy.load(fh)[0]
    items, nb, _ = walk(circ)
    synth, info = qsd_synth, []
    if a.aqc:
        synth = aqc_factory([int(x) for x in a.aqc.split(",")], [1, 2, 3],
                            a.aqc_tol, print, info)
    new, rep = build(circ, items, nb, block_unitaries(items), synth=synth,
                     barriers=a.barriers)
    print(rep, info)
    if not a.aqc and (rep.block_max_err > TOL or rep.l_err > TOL):
        sys.exit(f"not exact: block {rep.block_max_err:.1e}")
    if a.out:
        with open(a.out, "wb") as fh:
            qpy.dump(new, fh)
        print(f"wrote {a.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
