"""Prepare, and with --submit send, the structured HHL step-0 circuit to IBM.

Dry run by default: nothing is sent. Per backend, with its live calibration:
the circuit is transpiled with --layout-seeds seeds and the layout with the
highest estimated success probability (ESP: product of 1 - error over every
gate and measurement, from backend.target) is kept; reported are two-qubit
count and depth, scheduled duration, T1 and T2 of the chosen qubits, the
expected share of signal in the used outcomes, and QPU time and cost.

With --submit (one backend): one SamplerV2 job, three PUBs on the same
physical qubits:

  main  the circuit, all 14 qubits measured
  cal0  those qubits prepared in |0>, measured (readout calibration)
  cal1  those qubits prepared in |1>, measured
  ctrl  positive control: only the circuit's state preparation of b, on the
        same qubits, all 14 measured (expected: |b|^2 on the system, ancilla
        and clock 0), to tell a null result from a broken pipeline

Options: dynamical decoupling (--dd, ALAP); Pauli twirling of gates and
measurements, --shots-per-rand shots per randomization. Measurement
twirling makes readout errors symmetric, so cal0 and cal1 give per-qubit
flip rates for the TREX-style correction of the counts in ibm_analyze.py.
PEC, PEA and ZNE are EstimatorV2 methods for expectation values; at this
depth their overhead is out of reach (see README), so none is used.
max_execution_time caps QPU time at --cap times the estimate.
--local N runs the same PUBs on the noiseless AerSimulator with N shots
each and writes their counts for ibm_analyze.py --counts (path test only).
"""

import argparse
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import scipy.linalg as sla
from qiskit import ClassicalRegister, QuantumCircuit, qpy
from qiskit.quantum_info import Operator
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_aer import AerSimulator
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2

import structured_rewrite as sr
from run_step0 import x_part

HERE = Path(__file__).resolve().parent
EXP = HERE.parents[2]
ORIG = (EXP / "results/fvm_euler_1d_solver/nov2025-rerun/nov_pkgs/2026-11-03/"
        "_9f0fbf67/719a35aa/circuit_generated_statevector_nelem5_iter0.qpy")
P_USED_IDEAL = 0.014274  # ancilla 1, clock 0, from run_test.py


def reference(path: Path, nelem: int) -> dict:
    """x_ref, A, b from the input HHL qpy (first block and state prep)."""
    with open(path, "rb") as fh:
        circ = qpy.load(fh)[0]
    items, nb, nl = sr.walk(circ)
    blk = [p[0] for k, p, _ in items if k == "block"][0]
    u = Operator(blk).data[1::2, 1::2]
    ht = -1j * sla.logm(u)
    ht = (ht + ht.conj().T) / 2
    b = [p for k, p, _ in items if k == "sp"][0]
    nsys, n2 = 3 * nelem, 2 ** (nb - 1)
    return {"x": x_part(np.linalg.solve(ht, b).real, nsys).tolist(),
            "A": ht[:n2, n2:].real[:nsys, :nsys].tolist(),
            "b": b[:nsys].real.tolist(), "nb": nb, "nl": nl}


def esp_and_duration(isa: QuantumCircuit, target) -> tuple[float, float]:
    """log ESP (sum of log(1 - error)) and ASAP-scheduled duration in s."""
    log_esp, cursor = 0.0, {}
    for ins in isa.data:
        name = ins.operation.name
        if name in ("barrier", "delay"):
            continue
        q = tuple(isa.find_bit(x).index for x in ins.qubits)
        props = target[name].get(q) if name in target else None
        err = getattr(props, "error", None) or 0.0
        dur = getattr(props, "duration", None) or 0.0
        log_esp += math.log1p(-min(err, 0.999999))
        start = max(cursor.get(x, 0.0) for x in q)
        for x in q:
            cursor[x] = start + dur
    return log_esp, max(cursor.values())


def measured_qubits(isa: QuantumCircuit) -> list[int]:
    """Physical qubit of each clbit, in clbit order."""
    phys = {}
    for ins in isa.data:
        if ins.operation.name == "measure":
            phys[isa.find_bit(ins.clbits[0]).index] = \
                isa.find_bit(ins.qubits[0]).index
    return [phys[c] for c in sorted(phys)]


def cal_circuit(nq: int, phys: list[int], ones: bool) -> QuantumCircuit:
    qc = QuantumCircuit(nq)
    creg = ClassicalRegister(len(phys), "meas")
    qc.add_register(creg)
    for c, q in enumerate(phys):
        if ones:
            qc.x(q)
    qc.barrier([q for q in phys])
    for c, q in enumerate(phys):
        qc.measure(q, creg[c])
    return qc


def control_circuit(circ: QuantumCircuit, backend, phys: list[int],
                    opt: int) -> QuantumCircuit:
    """State preparation of b only, all qubits measured, on phys."""
    sp = circ.data[0]
    if sp.operation.name != "state_preparation":
        raise ValueError("first instruction is not the state preparation")
    qc = QuantumCircuit(circ.num_qubits)
    qc.append(sp.operation, [circ.find_bit(q).index for q in sp.qubits])
    qc.measure_all()
    pm = generate_preset_pass_manager(optimization_level=opt, backend=backend,
                                      initial_layout=phys, seed_transpiler=1)
    return pm.run(qc)


def prepare(backend, circ: QuantumCircuit, a, log) -> dict:
    target = backend.target
    best = None
    for seed in range(1, a.layout_seeds + 1):
        pm = generate_preset_pass_manager(optimization_level=a.opt,
                                          backend=backend,
                                          seed_transpiler=seed)
        isa = pm.run(circ)
        le, dur = esp_and_duration(isa, target)
        n2 = sum(1 for i in isa.data if i.operation.num_qubits == 2)
        d2 = isa.depth(lambda i: i.operation.num_qubits == 2)
        log(f"  {backend.name} seed {seed}: 2q {n2}, 2q depth {d2}, "
            f"duration {dur * 1e6:.0f} us, log ESP {le:.2f}")
        if best is None or le > best["log_esp"]:
            best = {"seed": seed, "isa": isa, "log_esp": le,
                    "duration_s": dur, "two_qubit_gates": n2,
                    "two_qubit_depth": d2, "depth": isa.depth()}
    isa = best["isa"]
    phys = measured_qubits(isa)
    qp = [target.qubit_properties[q] for q in phys]
    t1 = [p.t1 for p in qp if p.t1]
    t2 = [p.t2 for p in qp if p.t2]
    cfg = backend.configuration()
    rep = getattr(cfg, "default_rep_delay", None) or 250e-6
    rep = rep * 1e-6 if rep > 1e-2 else rep  # reported in us on some backends
    _, dcal = esp_and_duration(cal_circuit(backend.num_qubits, phys, True),
                               target)
    qpu_s = (a.shots * (best["duration_s"] + rep)
             + 3 * a.cal_shots * (dcal + rep)) * (1 + a.overhead)
    esp = math.exp(best["log_esp"])
    p_uni = 2 ** -(1 + len(phys) - 5)  # ancilla 1, clock 0, any system
    sig = esp * P_USED_IDEAL / (esp * P_USED_IDEAL + (1 - esp) * p_uni)
    return {
        "backend": backend.name, "num_qubits": backend.num_qubits,
        "processor": getattr(backend, "processor_type", None),
        "calibration_utc": str(getattr(target, "_last_update", "") or ""),
        "layout_seed": best["seed"], "optimization_level": a.opt,
        "physical_qubits": phys,
        "two_qubit_gates": best["two_qubit_gates"],
        "two_qubit_depth": best["two_qubit_depth"], "depth": best["depth"],
        "duration_us": best["duration_s"] * 1e6,
        "t1_median_us": float(np.median(t1)) * 1e6 if t1 else None,
        "t2_median_us": float(np.median(t2)) * 1e6 if t2 else None,
        "log_esp": best["log_esp"], "esp": esp,
        "signal_share_used_outcomes": sig,
        "rep_delay_us": rep * 1e6, "qpu_estimate_s": qpu_s,
        "max_execution_time_s": int(max(300, math.ceil(a.cap * qpu_s))),
        "cost_estimate_usd": qpu_s * a.usd_per_s,
        "_isa": isa,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("qpy", type=Path,
                    help="rewritten circuit (structured_rewrite.py -o)")
    ap.add_argument("--orig", type=Path, default=ORIG,
                    help="input HHL qpy, for the reference solution")
    ap.add_argument("--nelem", type=int, default=5)
    ap.add_argument("--backends", default="ibm_chicago,ibm_phoenix")
    ap.add_argument("--account", default="default-ibm-cloud")
    ap.add_argument("--shots", type=int, default=1_000_000)
    ap.add_argument("--shots-per-rand", type=int, default=10_000)
    ap.add_argument("--cal-shots", type=int, default=100_000)
    ap.add_argument("--dd", default="XY4", choices=["XX", "XpXm", "XY4"])
    ap.add_argument("--layout-seeds", type=int, default=16)
    ap.add_argument("--opt", type=int, default=2)
    ap.add_argument("--overhead", type=float, default=0.2,
                    help="QPU time overhead fraction for the estimate")
    ap.add_argument("--cap", type=float, default=1.5,
                    help="max_execution_time as a multiple of the estimate")
    ap.add_argument("--usd-per-s", type=float, default=1.60,
                    help="price for the cost estimate (pay-as-you-go list)")
    ap.add_argument("--out", type=Path,
                    default=Path.home() / "q8020/hhl-ibm-prep")
    ap.add_argument("--submit", action="store_true",
                    help="send the job (exactly one backend)")
    ap.add_argument("--local", type=int, metavar="N",
                    help="run the PUBs on noiseless Aer, N shots each")
    a = ap.parse_args()
    names = a.backends.split(",")
    if (a.submit or a.local) and len(names) != 1:
        sys.exit("--submit and --local need exactly one backend")
    if a.submit and a.local:
        sys.exit("choose --submit or --local")
    if a.shots % a.shots_per_rand or a.cal_shots % a.shots_per_rand:
        sys.exit("shots and cal-shots must be multiples of shots-per-rand")
    a.out.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    def log(msg: str) -> None:
        print(msg, flush=True)

    with open(a.qpy, "rb") as fh:
        circ = qpy.load(fh)[0]
    circ = circ.remove_final_measurements(inplace=False)
    circ.measure_all()
    ref = reference(a.orig, a.nelem)
    svc = QiskitRuntimeService(name=a.account)
    for name in names:
        backend = svc.backend(name)
        log(f"{name}: preparing ({a.layout_seeds} layout seeds)")
        prep = prepare(backend, circ, a, log)
        isa = prep.pop("_isa")
        phys = prep["physical_qubits"]
        prep.update({
            "prepared_utc": stamp, "input_qpy": str(a.qpy),
            "orig_qpy": str(a.orig), "reference": ref,
            "shots": a.shots, "cal_shots": a.cal_shots,
            "options": {"dynamical_decoupling": {
                "enable": True, "sequence_type": a.dd,
                "scheduling_method": "alap"},
                "twirling": {"enable_gates": True, "enable_measure": True,
                             "num_randomizations": "auto",
                             "shots_per_randomization": a.shots_per_rand}}})
        base = a.out / f"{name}-{stamp}"
        ctrl = control_circuit(circ, backend, phys, a.opt)
        cal0 = cal_circuit(backend.num_qubits, phys, False)
        cal1 = cal_circuit(backend.num_qubits, phys, True)
        prep["control_physical_qubits"] = measured_qubits(ctrl)
        prep["control_two_qubit_gates"] = sum(
            1 for i in ctrl.data if i.operation.num_qubits == 2)
        prep["control_b_herm"] = [abs(complex(v)) ** 2 for v in
                                  circ.data[0].operation.params]
        with open(f"{base}-isa.qpy", "wb") as fh:
            qpy.dump([isa, ctrl, cal0, cal1], fh)
        show = {k: v for k, v in prep.items() if k != "reference"}
        log(json.dumps(show, indent=1, default=str))
        if a.submit:
            sampler = SamplerV2(mode=backend)
            o = sampler.options
            o.default_shots = a.shots
            o.max_execution_time = prep["max_execution_time_s"]
            o.dynamical_decoupling.enable = True
            o.dynamical_decoupling.sequence_type = a.dd
            o.dynamical_decoupling.scheduling_method = "alap"
            o.twirling.enable_gates = True
            o.twirling.enable_measure = True
            o.twirling.num_randomizations = "auto"
            o.twirling.shots_per_randomization = a.shots_per_rand
            o.environment.job_tags = ["q8020", "fvm-hhl-structured",
                                      f"nelem{a.nelem}", "step0"]
            job = sampler.run([(isa,), (cal0, None, a.cal_shots),
                               (cal1, None, a.cal_shots),
                               (ctrl, None, a.cal_shots)])
            prep["job_id"] = job.job_id()
            prep["submitted_utc"] = datetime.now(timezone.utc).isoformat()
            log(f"SUBMITTED {name}: job {prep['job_id']}")
        if a.local:
            sampler = SamplerV2(mode=AerSimulator())
            res = sampler.run([isa, cal0, cal1, ctrl],
                              shots=a.local).result()
            data = {k: res[i].data.meas.get_counts() for i, k in
                    enumerate(("main", "cal0", "cal1", "ctrl"))}
            with open(f"{base}-local-counts.json", "w") as fh:
                json.dump(data, fh)
            log(f"local run: wrote {base}-local-counts.json")
        with open(f"{base}-prep.json", "w") as fh:
            json.dump(prep, fh, indent=1, default=str)
        log(f"wrote {base}-prep.json and {base}-isa.qpy")


if __name__ == "__main__":
    main()
