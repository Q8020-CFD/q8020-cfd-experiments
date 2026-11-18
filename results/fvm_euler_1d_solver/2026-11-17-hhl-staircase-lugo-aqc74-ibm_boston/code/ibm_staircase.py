"""Prepare, and with --submit send, a staircase of mirrored HHL steps.

Step k is the state preparation of b, then the clock Hadamards and QPE blocks
1..k of the input circuit, a barrier, then the exact inverse of those blocks.
Its ideal output is known: clock and ancilla all 0, the system distributed as
|b|^2. Step 0 is the state preparation alone. The steps reuse the input
circuit's own gates, cut at its barriers (a structured_rewrite build with
barriers), and run on the physical qubits of the full circuit's best layout
(--layout-from, an ibm_submit.py prep JSON). How fast the probability that
clock and ancilla return to 0 decays with the two-qubit gate count measures
the noise the full circuit sees on those qubits.

Dry run by default: per step, the transpiled two-qubit gate count, duration,
log ESP and QPU estimate. --local N runs every PUB on noiseless Aer as a
check. --submit sends one SamplerV2 job (dynamical decoupling, gate and
measurement twirling) with readout calibration PUBs, and saves the device
calibration and the code as run. ibm_capture.py captures the finished job.
"""
import argparse
import getpass
import hashlib
import json
import math
import socket
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from qiskit import QuantumCircuit, qpy
from qiskit.transpiler import generate_preset_pass_manager
from qiskit_aer import AerSimulator
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ibm_capture as cap  # noqa: E402
from ibm_submit import cal_circuit, esp_and_duration, measured_qubits  # noqa: E402

DESCRIPTION = (
    "Staircase of mirrored HHL steps on IBM hardware: step k is the state "
    "preparation of b, the clock Hadamards and QPE blocks 1..k of the LuGo "
    "real-L AQC@74 circuit (nelem 5), then their exact inverse, so the ideal "
    "output is clock and ancilla 0 and the system as |b|^2. The decay of the "
    "return probability with two-qubit gate count measures the noise the full "
    "circuit sees on the same physical qubits.")


def segments(circ: QuantumCircuit) -> list[list]:
    """The circuit's instructions, cut at its barriers."""
    segs, cur = [], []
    for ins in circ.data:
        if ins.operation.name == "barrier":
            segs.append(cur)
            cur = []
        else:
            cur.append(ins)
    return segs + [cur]


def step_circuit(circ: QuantumCircuit, k: int) -> QuantumCircuit:
    """Prep, then the clock Hadamards and blocks 1..k, then their inverse."""
    segs = segments(circ)
    sp = segs[0][0]
    if sp.operation.name != "state_preparation":
        raise ValueError("first instruction is not the state preparation")
    if not 0 <= k < len(segs) - 1 or any(
            i.operation.name in ("QFT", "IQFT_dg", "ucry")
            for s in segs[:k] for i in s):
        raise ValueError(f"step {k} would reach past the QPE blocks")
    qc = QuantumCircuit(*circ.qregs, name=f"step{k}")
    qc.append(sp)
    if k:
        g = QuantumCircuit(*circ.qregs)
        for j, seg in enumerate(segs[:k]):
            for ins in (seg[1:] if j == 0 else seg):
                g.append(ins)
            g.barrier()
        qc.compose(g, inplace=True)
        qc.compose(g.inverse(), inplace=True)
    qc.measure_all()
    return qc


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("qpy", type=Path, help="built circuit with barriers")
    ap.add_argument("--layout-from", type=Path, required=True,
                    help="ibm_submit.py prep JSON of the full circuit")
    ap.add_argument("--backend", default="ibm_boston")
    ap.add_argument("--account", default="default-ibm-cloud")
    ap.add_argument("--steps", default="0,1,2,3,4,6,8")
    ap.add_argument("--long-from", type=int, default=4,
                    help="steps with at least this many blocks get --shots-long")
    ap.add_argument("--shots-short", type=int, default=150_000)
    ap.add_argument("--shots-long", type=int, default=1_000_000)
    ap.add_argument("--cal-shots", type=int, default=150_000)
    ap.add_argument("--shots-per-rand", type=int, default=10_000)
    ap.add_argument("--dd", default="XY4", choices=["XX", "XpXm", "XY4"])
    ap.add_argument("--opt", type=int, default=2)
    ap.add_argument("--overhead", type=float, default=0.2)
    ap.add_argument("--cap", type=float, default=1.5)
    ap.add_argument("--usd-per-s", type=float, default=1.60)
    ap.add_argument("--label", default="hhl-staircase-lugo-aqc74")
    ap.add_argument("--out", type=Path,
                    default=Path.home() / "q8020/hhl-ibm-staircase")
    ap.add_argument("--submit", action="store_true")
    ap.add_argument("--local", type=int, metavar="N",
                    help="run the PUBs on noiseless Aer, N shots each")
    a = ap.parse_args()
    steps = [int(s) for s in a.steps.split(",")]
    for n in (a.shots_short, a.shots_long, a.cal_shots):
        if n % a.shots_per_rand:
            sys.exit("shots must be multiples of --shots-per-rand")
    a.out.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    base = a.out / f"{a.backend}-{stamp}"

    with open(a.qpy, "rb") as fh:
        circ = qpy.load(fh)[0]
    full = json.loads(a.layout_from.read_text())
    if full["backend"] != a.backend:
        sys.exit(f"--layout-from is for {full['backend']}, not {a.backend}")
    phys = full["physical_qubits"]
    svc = QiskitRuntimeService(name=a.account)
    backend = svc.backend(a.backend)
    target = backend.target
    cfg = backend.configuration()
    rep = getattr(cfg, "default_rep_delay", None) or 250e-6
    rep = rep * 1e-6 if rep > 1e-2 else rep

    pm = generate_preset_pass_manager(optimization_level=a.opt, backend=backend,
                                      initial_layout=phys, seed_transpiler=1)
    isas, pubs = [], []
    for k in steps:
        isa = pm.run(step_circuit(circ, k))
        le, dur = esp_and_duration(isa, target)
        shots = a.shots_long if k >= a.long_from else a.shots_short
        pub = {"name": f"step{k}", "step": k, "blocks": k, "shots": shots,
               "two_qubit_gates": sum(1 for i in isa.data
                                      if i.operation.num_qubits == 2),
               "two_qubit_depth": isa.depth(lambda i: i.operation.num_qubits == 2),
               "depth": isa.depth(), "duration_us": dur * 1e6, "log_esp": le,
               "esp": math.exp(le), "physical_qubits": measured_qubits(isa)}
        pub["qpu_estimate_s"] = shots * (dur + rep) * (1 + a.overhead)
        print(f"step {k}: 2q {pub['two_qubit_gates']}, 2q depth "
              f"{pub['two_qubit_depth']}, {pub['duration_us']:.0f} us, ESP "
              f"{pub['esp']:.3g}, {shots} shots, QPU {pub['qpu_estimate_s']:.0f} s",
              flush=True)
        isas.append(isa)
        pubs.append(pub)
    for ones in (False, True):
        c = cal_circuit(backend.num_qubits, phys, ones)
        _, dcal = esp_and_duration(c, target)
        isas.append(c)
        pubs.append({"name": f"cal{int(ones)}", "shots": a.cal_shots,
                     "physical_qubits": phys, "duration_us": dcal * 1e6,
                     "qpu_estimate_s": a.cal_shots * (dcal + rep)
                     * (1 + a.overhead)})
    qpu_s = sum(p["qpu_estimate_s"] for p in pubs)
    options = {"dynamical_decoupling": {"enable": True, "sequence_type": a.dd,
                                        "scheduling_method": "alap"},
               "twirling": {"enable_gates": True, "enable_measure": True,
                            "num_randomizations": "auto",
                            "shots_per_randomization": a.shots_per_rand}}
    prep = {
        "kind": "staircase", "label": a.label, "description": DESCRIPTION,
        "algorithm": "hhl-staircase-mirror", "entry_point": "ibm_staircase.py",
        "interpreter": sys.executable, "argv": sys.argv,
        "backend": a.backend, "processor": getattr(backend, "processor_type", None),
        "account": a.account, "input_qpy": str(a.qpy.resolve()),
        "input_sha256": hashlib.sha256(a.qpy.read_bytes()).hexdigest(),
        "layout_from": str(a.layout_from.resolve()), "physical_qubits": phys,
        "full_circuit_two_qubit_gates": full.get("two_qubit_gates"),
        "optimization_level": a.opt, "seed_transpiler": 1, "options": options,
        "rep_delay_us": rep * 1e6, "pubs": pubs,
        "b_herm": [abs(complex(v)) ** 2 for v in circ.data[0].operation.params],
        "qpu_estimate_s": qpu_s,
        "max_execution_time_s": int(max(300, math.ceil(a.cap * qpu_s))),
        "cost_estimate_usd": qpu_s * a.usd_per_s, "prepared_utc": stamp,
        "submitted_from": {"username": getpass.getuser(),
                           "hostname": socket.gethostname(),
                           "context": "macos-laptop"},
    }
    print(f"total: {sum(p['shots'] for p in pubs)} shots, QPU estimate "
          f"{qpu_s:.0f} s ({qpu_s / 60:.1f} min), cap "
          f"{prep['max_execution_time_s']} s, list cost "
          f"${prep['cost_estimate_usd']:.0f}", flush=True)
    with open(f"{base}-isa.qpy", "wb") as fh:
        qpy.dump(isas, fh)

    if a.local:
        res = SamplerV2(mode=AerSimulator()).run(isas, shots=a.local).result()
        b2 = np.asarray(prep["b_herm"][:32]) / sum(prep["b_herm"][:32])
        n = len(phys)
        for i, pub in enumerate(pubs[: len(steps)]):
            p, shots = cap.to_prob(res[i].data.meas.get_counts(), n)
            sc = cap.score_step(p, shots, b2)
            print(f"local {pub['name']}: return P {sc['p_return']:.4f}, system "
                  f"fidelity {sc['system_fidelity']:.4f}", flush=True)

    if a.submit:
        cal = cap.calibration_snapshot(backend)
        (a.out / f"{base.name}-calibration-submit.json").write_text(
            json.dumps(cal, indent=1, default=str) + "\n")
        cap.code_snapshot(a.out / f"{base.name}-code")
        prep["calibration_submit"] = f"{base.name}-calibration-submit.json"
        prep["code_dir"] = f"{base.name}-code"
        sampler = SamplerV2(mode=backend)
        o = sampler.options
        o.max_execution_time = prep["max_execution_time_s"]
        o.dynamical_decoupling.enable = True
        o.dynamical_decoupling.sequence_type = a.dd
        o.dynamical_decoupling.scheduling_method = "alap"
        o.twirling.enable_gates = True
        o.twirling.enable_measure = True
        o.twirling.num_randomizations = "auto"
        o.twirling.shots_per_randomization = a.shots_per_rand
        o.environment.job_tags = ["q8020", "fvm-hhl-staircase", "nelem5",
                                  "lugo-realL-aqc74"]
        job = sampler.run([(isa, None, p["shots"]) for isa, p in zip(isas, pubs)])
        prep["job_id"] = job.job_id()
        prep["submitted_utc"] = datetime.now(timezone.utc).isoformat()
        print(f"SUBMITTED {a.backend}: job {prep['job_id']}", flush=True)
    with open(f"{base}-prep.json", "w") as fh:
        json.dump(prep, fh, indent=1, default=str)
    print(f"wrote {base}-prep.json and {base}-isa.qpy")


if __name__ == "__main__":
    main()
