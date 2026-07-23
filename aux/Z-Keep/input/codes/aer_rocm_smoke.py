"""GHZ sampling smoke test for the Frontier qiskit-aer ROCm build.

Open-box q8020 solver: runs a GHZ circuit on AerSimulator with the
requested device (GPU = MI250X via the ROCm/Thrust backend), verifies
the sampled distribution, and writes q8020 metadata fragments inline
via meta_fragment (no separate harvester needed).

Run standalone:
    ~/aer-rocm-env/bin/python aer_rocm_smoke.py --qubits 20 --device GPU \
        --shots 4096 --outdir /tmp/smoke

Or via the sweeper (from the q8020-cfd-experiments repo root):
    q8020-sweep aux/Z-Keep/input/cases/_smoke_tests/aer_rocm_gpu.toml

Requires q8020-cfd-metautil installed in the same environment as
qiskit-aer (e.g. ~/aer-rocm-env/bin/pip install -e ./q8020-cfd-metautil).

Exit codes: 0 = success, 1 = ran but wrong device or bad distribution,
2 = bad arguments.
"""

import argparse
import sys
import time
from pathlib import Path

from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator

from q8020_cfd_metautil import meta_fragment
from q8020_cfd_metautil.args import add_standard_quantum_args

# GHZ correctness gate: fraction of shots on |0...0> or |1...1>.
# Ideal is 1.0; anything below this indicates a broken backend.
MIN_GHZ_FRACTION = 0.99
MAX_QUBITS = 30  # statevector memory guard (~16 GB complex128 at 30)


def build_ghz(n_qubits: int) -> QuantumCircuit:
    """H on qubit 0, CX chain down the register, measure all."""
    qc = QuantumCircuit(n_qubits)
    qc.h(0)
    for i in range(n_qubits - 1):
        qc.cx(i, i + 1)
    qc.measure_all()
    return qc


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    add_standard_quantum_args(parser)
    parser.add_argument("--qubits", type=int, default=20,
                        help="GHZ register width (default: 20)")
    parser.add_argument("--device", type=str, default="GPU",
                        choices=["CPU", "GPU"],
                        help="Aer execution device (default: GPU)")
    parser.add_argument("--method", type=str, default="statevector",
                        choices=["statevector", "density_matrix"],
                        help="Aer simulation method (default: statevector)")
    args = parser.parse_args()
    if not 2 <= args.qubits <= MAX_QUBITS:
        parser.error(f"--qubits must be in [2, {MAX_QUBITS}]")
    return args


def main() -> int:
    args = parse_args()
    outdir = Path(args.outdir or ".").expanduser()
    outdir.mkdir(parents=True, exist_ok=True)
    shots = args.shots or 4096

    simulator = AerSimulator(method=args.method, device=args.device)
    available = simulator.available_devices()
    print(f"available devices: {available}")
    if args.device not in available:
        print(f"ERROR: device {args.device} not in {available}",
              file=sys.stderr)
        return 1

    circuit = transpile(build_ghz(args.qubits), simulator)
    t_start = time.perf_counter()
    result = simulator.run(circuit, shots=shots,
                           seed_simulator=args.seed).result()
    run_seconds = time.perf_counter() - t_start

    counts = result.get_counts()
    all_zero = "0" * args.qubits
    all_one = "1" * args.qubits
    ghz_fraction = (counts.get(all_zero, 0) + counts.get(all_one, 0)) / shots
    device_executed = result.results[0].metadata.get("device", "unknown")

    print(f"qubits={args.qubits} shots={shots} method={args.method}")
    print(f"executed on: {device_executed} in {run_seconds:.3f}s")
    print(f"GHZ fraction: {ghz_fraction:.4f} "
          f"(|0..0>={counts.get(all_zero, 0)}, |1..1>={counts.get(all_one, 0)})")

    # --- q8020 metadata fragments (open-box) ---
    experiment = meta_fragment.make_experiment_meta(
        "aer_rocm_smoke",
        experiment_id=args.experiment_id,
        workflow_id=args.workflow_id,
    )
    exp_id = experiment["experiment_id"]
    meta_fragment.write_experiment(outdir, experiment, experiment_id=exp_id)

    case = meta_fragment.make_case_meta(
        "ghz_sampling", n_qubits=args.qubits, shots=shots,
    )
    meta_fragment.write_case(outdir, case, experiment_id=exp_id)

    code = meta_fragment.make_code_meta(
        "ghz", "aer_rocm_smoke.py", run_args=vars(args),
    )
    meta_fragment.write_code(outdir, code, experiment_id=exp_id)

    backend = meta_fragment.make_backend_meta(
        simulator,
        requested_device=args.device,
        requested_method=args.method,
        executed_device=device_executed,
    )
    meta_fragment.write_backend(outdir, backend, experiment_id=exp_id)

    top_counts = dict(
        sorted(counts.items(), key=lambda kv: -kv[1])[:8]
    )
    results_meta = {
        "ghz_fraction": ghz_fraction,
        "run_seconds": run_seconds,
        "device_executed": device_executed,
        "counts_top": top_counts,
        "n_outcomes": len(counts),
    }
    meta_fragment.write_results(outdir, results_meta, experiment_id=exp_id)

    # --- verdict ---
    if device_executed != args.device:
        print(f"ERROR: requested {args.device} but executed on "
              f"{device_executed}", file=sys.stderr)
        return 1
    if ghz_fraction < MIN_GHZ_FRACTION:
        print(f"ERROR: GHZ fraction {ghz_fraction:.4f} below "
              f"{MIN_GHZ_FRACTION} — distribution is wrong", file=sys.stderr)
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
