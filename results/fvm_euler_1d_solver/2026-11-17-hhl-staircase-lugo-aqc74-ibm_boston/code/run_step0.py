"""Step-0 runs of a LuGo circuit: as stored, re-transpiled, rewritten.

Inputs are the stored qpy files of one run (step 0, per nelem), chosen by
--source: feb26 (the 2026-02-26 ORNL run, qiskit 1.4.5, the default) or nov26
(the 2026-11-03 rerun, qiskit 2.6.1). Variants, for feb26:

  feb26_stored      the stored transpiled circuit (qiskit 1.4.5 transpile, Aer
                    target), executed here as is
  feb26_qiskit26    the stored generated circuit, transpiled here
  rewrite_qiskit26  the generated circuit after qpy_rewrite, transpiled here

and for nov26 nov26_stored, nov26_qiskit26 and rewrite_nov26_qiskit26.

The nov26 generated qpy holds an ExactReciprocalGate that qiskit 2.x writes
without its size, scaling or neg_vals, so it cannot be loaded as is. It is
loaded with (nl, scaling, neg_vals) taken from the feb26 generated qpy of the
same nelem (infer_recip_angles.py derives them again from the nov26 stored
run), after
checking that the two circuits hold the same H*t and b; the load is then
checked by running it against the nov26 stored transpiled circuit
(state_fidelity_vs_<source>_stored in the statevector CSV).

Transpiles here use this venv's qiskit at optimization level 2, seed 1:
for the Aer statevector simulator (the executed circuit), and for gate
counts only, for an all-to-all cx/rz/sx/x basis and for FakeMarrakesh (IBM
Heron r2, heavy-hex, cz). Execution is on the Aer ideal simulator, as an
exact statevector and as shots with seeds 1..N.

The classical reference comes from the qpy too: H*t is the matrix log of the
first QPE block's controlled unitary, b_herm the state-prep amplitudes, and
x_ref the x part of H^-1 b_herm. Extraction and metrics mirror the fvm HHL
step (time_solvers.hhl_solve and quantum_tools at fvm a5317f2b):
amplitudes or counts with ancilla 1 and clock 0, normalized, x part of the
Hermitian solution, least-squares length fit against A and b (fvm
-hhl_scale leastsq, which the Feb 2026 run used), signs of x_ref for shots
after the fit, then fidelity, relative L2 error and normalized L2 error.
A and b are the x blocks of H*t and b_herm. All metrics are invariant to the
unknown scale t, so the qpy alone suffices. The 'true_sol' length (|x_ref|)
is also reported as l2_error_rel_truesol.
"""

import argparse
import csv
import hashlib
import json
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import qiskit
import qiskit_aer
import scipy
import scipy.linalg as sla
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator, state_fidelity
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_aer import AerSimulator
from qiskit_ibm_runtime.fake_provider import FakeMarrakesh

from qpy_rewrite import load_qpy, recip_params, rewrite

HERE = Path(__file__).resolve().parent
EXP = HERE.parents[2]
RES = EXP / "results/fvm_euler_1d_solver"
FEB_DIR = RES / "2026-02-26-LuGo/circuits"
NOV_DIR = RES / "nov2025-rerun/LuGo-rerun/circuits"
SOURCES = {
    "feb26": {"dir": FEB_DIR,
              "gen": "circuit_generated_nelem{n}_iter0.qpy",
              "stored": "circuit_transpile_nelem{n}_iter0.qpy",
              "names": ("feb26_stored", "feb26_qiskit26", "rewrite_qiskit26")},
    "nov26": {"dir": NOV_DIR,
              "gen": "circuit_generated_statevector_nelem{n}_iter0.qpy",
              "stored": "circuit_transpile_statevector_shots150000_nelem{n}"
                        "_iter0.qpy",
              "names": ("nov26_stored", "nov26_qiskit26",
                        "rewrite_nov26_qiskit26")},
}
OPT, SEED_T = 2, 1


def git_head(path: Path) -> str:
    r = subprocess.run(["git", "-C", str(path), "rev-parse", "--short=8", "HEAD"],
                       capture_output=True, text=True)
    return r.stdout.strip()


def qidx(circ: QuantumCircuit, ins) -> list[int]:
    return [circ.find_bit(q).index for q in ins.qubits]


def reference(gen: QuantumCircuit, nb: int) -> tuple[np.ndarray, np.ndarray]:
    """H*t and b_herm in the system-register basis, from the circuit."""
    sp = [i for i in gen.data if i.operation.name not in
          ("QPE", "1/x", "inv_QPE", "barrier", "measure")][0]
    if qidx(gen, sp) != list(range(nb)):
        raise ValueError("state prep is not on qubits 0..nb-1 in order")
    b = np.array(sp.operation.definition.data[0].operation.params, dtype=complex)
    qpe = [i for i in gen.data if i.operation.name == "QPE"][0]
    top = qidx(gen, qpe)
    defn = qpe.operation.definition
    blk = [i for i in defn.data if i.operation.num_qubits == nb + 1][0]
    sysq = [top[defn.find_bit(q).index] for q in blk.qubits[1:]]
    if sysq != list(range(nb)):
        raise ValueError(f"block system qubits {sysq} are not 0..nb-1")
    m = Operator(blk.operation).data
    w = m[1::2, 1::2]  # control is the block's first qubit (bit 0)
    if not np.allclose(m[0::2, 0::2], np.eye(2 ** nb), atol=1e-9):
        raise ValueError("first QPE block is not a controlled unitary")
    ph = np.angle(np.linalg.eigvals(w))
    if np.max(np.abs(ph)) > np.pi - 1e-6:
        raise ValueError("first block eigenphases reach pi: log is ambiguous")
    blk2 = [i for i in defn.data if i.operation.num_qubits == nb + 1][1]
    w2 = Operator(blk2.operation).data[1::2, 1::2]
    if not np.allclose(w2, w @ w, atol=1e-9):
        raise ValueError("second QPE block is not the square of the first")
    ht = -1j * sla.logm(w)
    ht = (ht + ht.conj().T) / 2
    return ht, b


def x_part(z: np.ndarray, nsys: int) -> np.ndarray:
    """fvm extract_true_sol_from_herm: x = z[n2:n2+nsys], n2 = next pow2."""
    n2 = 1 << (nsys - 1).bit_length()
    return z[n2:n2 + nsys]


def metrics(x_hhl: np.ndarray, x_ref: np.ndarray) -> dict:
    e = np.linalg.norm(x_ref - x_hhl)
    nr = x_ref / np.linalg.norm(x_ref)
    nh = x_hhl / np.linalg.norm(x_hhl)
    return {"fidelity": float(state_fidelity(nh, nr)),
            "l2_error_rel": float(e / np.linalg.norm(x_ref)),
            "l2_error_normalized": float(np.linalg.norm(nr - nh))}


def scaled(x: np.ndarray, ref: dict, shots: bool) -> dict:
    """fvm hhl_solve: length fit, then signs of x_ref if shots."""
    a_x = ref["A"] @ x
    ls = x * (ref["b"] @ a_x) / ((a_x @ a_x) + 1e-15)
    ts = x * np.linalg.norm(ref["x"])
    if shots:
        sg = ref["x"] / (np.abs(ref["x"]) + 1e-15)
        ls, ts = np.abs(ls) * sg, np.abs(ts) * sg
    out = metrics(ls, ref["x"])
    out["l2_error_rel_truesol"] = metrics(ts, ref["x"])["l2_error_rel"]
    return out


def extract_sv(sv: np.ndarray, nb: int, ref: dict) -> dict:
    """fvm get_sol_ideal_backend: ancilla 1, clock 0 amplitudes, real part."""
    half = len(sv) // 2
    z = sv[half:half + 2 ** nb].real
    z = z / np.linalg.norm(z)
    return scaled(x_part(z, len(ref["x"])), ref, shots=False)


def extract_counts(counts: dict, n: int, nb: int, ref: dict) -> dict:
    """fvm get_ancillaqubit + get_sol_real_backend: ancilla 1, clock 0 counts."""
    pre = "1" + "0" * (n - 1 - nb)
    c = np.array([counts.get(pre + format(s, f"0{nb}b"), 0)
                  for s in range(2 ** nb)], dtype=float)
    acc = sum(v for k, v in counts.items() if k[0] == "1")
    z = np.sqrt(c / max(acc, 1))
    z = z / (np.linalg.norm(z) + 1e-15)
    out = scaled(x_part(z, len(ref["x"])), ref, shots=True)
    out["shots_ancilla1"] = int(acc)
    out["shots_used"] = int(c.sum())
    return out


def counts_sha1(counts: dict) -> str:
    return hashlib.sha1(json.dumps(sorted(counts.items())).encode()).hexdigest()[:12]


def strip_meas(c: QuantumCircuit) -> QuantumCircuit:
    return c.remove_final_measurements(inplace=False)


def with_meas(c: QuantumCircuit) -> QuantumCircuit:
    m = strip_meas(c)
    m.measure_all()
    return m


def check_layout(t: QuantumCircuit) -> None:
    if t.layout is not None:
        perm = t.layout.final_index_layout()
        if perm != list(range(t.num_qubits)):
            raise RuntimeError(f"non-trivial output permutation {perm}")


def two_q(t: QuantumCircuit) -> tuple[int, int]:
    n2 = sum(1 for i in t.data if i.operation.num_qubits == 2)
    return n2, t.depth(lambda i: i.operation.num_qubits == 2)


def hw_counts(c: QuantumCircuit, heron: bool) -> dict:
    out = {}
    pm = generate_preset_pass_manager(optimization_level=OPT, seed_transpiler=SEED_T,
                                      basis_gates=["cx", "rz", "sx", "x"])
    t0 = time.time()
    t = pm.run(strip_meas(c))
    out["a2a_cx"], out["a2a_2q_depth"] = two_q(t)
    out["a2a_depth"] = t.depth()
    out["a2a_transpile_s"] = time.time() - t0
    if heron:
        pm = generate_preset_pass_manager(optimization_level=OPT,
                                          seed_transpiler=SEED_T,
                                          backend=FakeMarrakesh())
        t0 = time.time()
        t = pm.run(strip_meas(c))
        out["heron_cz"], out["heron_2q_depth"] = two_q(t)
        out["heron_depth"] = t.depth()
        out["heron_transpile_s"] = time.time() - t0
    return out


def write_csv(path: Path, rows: list[dict]) -> None:
    keys = list(dict.fromkeys(k for r in rows for k in r))
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)


def load_inputs(source: str, nelem: int, log) -> tuple:
    """(generated, stored, extra row fields) of one source and nelem."""
    src = SOURCES[source]
    extra: dict = {}
    if source == "feb26":
        gen = load_qpy(str(src["dir"] / src["gen"].format(n=nelem)))
    else:
        feb = load_qpy(str(FEB_DIR / SOURCES["feb26"]["gen"].format(n=nelem)))
        nl, scaling, neg = recip_params(feb)
        gen = load_qpy(str(src["dir"] / src["gen"].format(n=nelem)),
                       recip=(nl, scaling, neg))
        nbf = feb.num_qubits - nl - 1
        ht_f, b_f = reference(feb, nbf)
        ht_n, b_n = reference(gen, nbf)
        extra = {"recip_nl": nl, "recip_scaling": scaling,
                 "recip_neg_vals": neg,
                 "ht_maxdiff_vs_feb26": float(np.max(np.abs(ht_n - ht_f))),
                 "b_maxdiff_vs_feb26": float(np.max(np.abs(b_n - b_f)))}
        log(f"nelem {nelem}: {source} generated loaded with nl={nl} "
            f"scaling={scaling!r} neg_vals={neg} (from the feb26 1/x block); "
            f"H*t, b vs "
            f"feb26: {extra['ht_maxdiff_vs_feb26']:.2e}, "
            f"{extra['b_maxdiff_vs_feb26']:.2e}")
    stored = load_qpy(str(src["dir"] / src["stored"].format(n=nelem)))
    return gen, stored, extra


def run_nelem(source: str, nelem: int, seeds: list[int], shots: int,
              do_shots: bool, heron: bool, log) -> tuple[list, list, list]:
    nsys = 3 * nelem
    gen, stored, extra = load_inputs(source, nelem, log)
    rw, rep = rewrite(gen)
    log(f"nelem {nelem}: {rep}")
    nb, n = rep.nb, gen.num_qubits
    ht, b = reference(gen, nb)
    n2 = 2 ** (nb - 1)
    ref = {"x": x_part(np.linalg.solve(ht, b).real, nsys),
           "A": ht[:n2, n2:].real[:nsys, :nsys], "b": b[:nsys].real}
    kappa = np.linalg.cond(ht)
    log(f"nelem {nelem}: n={n} nb={nb} nl={rep.nl} cond(H)={kappa:.6g}")

    sim = AerSimulator(method="statevector")
    aer_pm = generate_preset_pass_manager(optimization_level=OPT, backend=sim,
                                          seed_transpiler=SEED_T)
    n_st, n_q26, n_rw = SOURCES[source]["names"]
    variants = {n_st: (stored, False), n_q26: (gen, True), n_rw: (rw, True)}
    circ_rows, sv_rows, shot_rows, svs = [], [], [], {}
    for name, (c, do_tr) in variants.items():
        row = {"nelem": nelem, "variant": name, "qubits": n,
               "rewrite_s": rep.seconds if name.startswith("rewrite") else "",
               **extra}
        t0 = time.time()
        t_sv = aer_pm.run(strip_meas(c)) if do_tr else strip_meas(c)
        t_sh = aer_pm.run(with_meas(c)) if do_tr else with_meas(c)
        row["aer_transpile_s"] = time.time() - t0 if do_tr else ""
        check_layout(t_sv)
        check_layout(t_sh)
        row["aer_depth"] = t_sh.depth()
        row["aer_gates"] = sum(t_sh.count_ops().values())
        row.update(hw_counts(c, heron))
        # exact statevector on Aer
        q = t_sv.copy()
        q.save_statevector()
        t0 = time.time()
        sv = np.asarray(sim.run(q).result().get_statevector())
        row["sv_run_s"] = time.time() - t0
        svs[name] = sv
        m = extract_sv(sv, nb, ref)
        sv_rows.append({"nelem": nelem, "variant": name, **m})
        log(f"  {name}: {row}")
        log(f"  {name} statevector: {m}")
        if do_shots:
            t0 = time.time()
            for s in seeds:
                cnt = sim.run(t_sh, shots=shots, seed_simulator=s).result().get_counts()
                ms = extract_counts(cnt, n, nb, ref)
                shot_rows.append({"nelem": nelem, "variant": name, "shots": shots,
                                  "seed": s, **ms,
                                  "counts_sha1": counts_sha1(cnt)})
            row["shots_run_s_per_seed"] = (time.time() - t0) / len(seeds)
        circ_rows.append(row)
    for name, sv in svs.items():
        f = abs(np.vdot(svs[n_st], sv)) ** 2
        for r in sv_rows:
            if r["nelem"] == nelem and r["variant"] == name:
                r[f"state_fidelity_vs_{n_st}"] = float(f)
    return circ_rows, sv_rows, shot_rows


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--source", choices=sorted(SOURCES), default="feb26",
                    help="which stored LuGo run to take the qpy from")
    ap.add_argument("--nelem", type=int, nargs="+", default=[5])
    ap.add_argument("--shots-nelem", type=int, nargs="*", default=[5])
    ap.add_argument("--shots", type=int, default=150000)
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--no-heron", action="store_true")
    ap.add_argument("--out", default=str(Path.home() / "q8020/lugo-qpy-rewrite"))
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    logf = open(out / "run.log", "a")

    def log(msg: str) -> None:
        line = f"{datetime.now(timezone.utc).isoformat(timespec='seconds')} {msg}"
        print(line, flush=True)
        logf.write(line + "\n")
        logf.flush()

    seeds = list(range(1, a.seeds + 1))
    versions = {
        "utc_start": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "python": platform.python_version(), "qiskit": qiskit.__version__,
        "qiskit_aer": qiskit_aer.__version__, "numpy": np.__version__,
        "scipy": scipy.__version__, "machine": "macos-laptop",
        "platform": platform.platform(),
        "experiments_commit": git_head(EXP), "python_exe": sys.executable,
        "args": vars(a), "opt_level": OPT, "seed_transpiler": SEED_T,
    }
    log(f"versions {versions}")
    allc, alls, allh = [], [], []
    for n in a.nelem:
        c, s, h = run_nelem(a.source, n, seeds, a.shots, n in a.shots_nelem,
                            not a.no_heron, log)
        allc += c
        alls += s
        allh += h
        sfx = "_".join(str(x) for x in a.nelem)
        write_csv(out / f"circuits_nelem{sfx}.csv", allc)
        write_csv(out / f"step0_statevector_nelem{sfx}.csv", alls)
        if allh:
            write_csv(out / f"step0_shots_nelem{sfx}.csv", allh)
    versions["utc_end"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with open(out / f"versions_nelem{sfx}.json", "w") as f:
        json.dump(versions, f, indent=1)
    log("done")


if __name__ == "__main__":
    main()
