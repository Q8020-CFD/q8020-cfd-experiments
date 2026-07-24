"""GHZ sampling smoke test for the Frontier qiskit-aer ROCm build.

Open-box q8020 solver: runs a GHZ circuit on AerSimulator with the
requested device (GPU = MI250X via the ROCm/Thrust backend), verifies
the sampled distribution, and writes q8020 metadata fragments inline
via meta_fragment (no separate harvester needed).

Run standalone (single process):
    ~/aer-rocm-env/bin/python aer_rocm_smoke.py --qubits 20 --device GPU \
        --shots 4096 --outdir /tmp/smoke

Run distributed (one simulation partitioned across ranks/GPUs — requires
the AER_MPI=ON build and mpi4py; each rank owns 2^blocking_qubits-amplitude
chunks and exchanges them over GPU-aware Cray MPICH):
    srun -n 16 --gpus-per-task=1 ~/aer-rocm-env/bin/python aer_rocm_smoke.py \
        --qubits 33 --device GPU --blocking-qubits 23 --outdir /tmp/smoke

Or via the sweeper (from the q8020-cfd-experiments repo root):
    q8020-sweep aux/Z-Keep/input/cases/_smoke_tests/aer_rocm_gpu.toml      # 1-GPU
    q8020-sweep aux/Z-Keep/input/cases/_smoke_tests/aer_rocm_gpu_mpi.toml  # MPI

Requires q8020-cfd-metautil installed in the same environment as
qiskit-aer (e.g. ~/aer-rocm-env/bin/pip install -e ./q8020-cfd-metautil).

Exit codes: 0 = success, 1 = ran but wrong device or bad distribution,
2 = bad arguments.
"""

import argparse
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator

from q8020_cfd_metautil import meta_fragment
from q8020_cfd_metautil.args import add_standard_quantum_args

# GHZ correctness gate: fraction of shots on |0...0> or |1...1>.
# Ideal is 1.0; anything below this indicates a broken backend.
MIN_GHZ_FRACTION = 0.99
MAX_QUBITS = 30       # single-GCD memory guard (~16 GB complex128 at 30)
MAX_QUBITS_MPI = 36   # distributed guard (1 TiB across >= 16 GCDs)


def get_mpi_context() -> tuple[int, int, "object | None"]:
    """Return (rank, world_size, comm).

    Uses mpi4py when launched under MPI (srun -n > 1). Falls back to a
    single-process context when mpi4py is missing or no MPI env is
    present, so the script still runs standalone on a laptop.
    """
    launched_under_mpi = int(
        os.environ.get("SLURM_NTASKS", os.environ.get("OMPI_COMM_WORLD_SIZE", "1"))
    ) > 1
    try:
        from mpi4py import MPI
        comm = MPI.COMM_WORLD
        return comm.Get_rank(), comm.Get_size(), comm
    except ImportError:
        if launched_under_mpi:
            # Multi-task launch but no mpi4py: every rank would run an
            # independent duplicate simulation. Fail loudly instead.
            print("ERROR: launched with multiple tasks but mpi4py is not "
                  "installed in this environment", file=sys.stderr)
            sys.exit(2)
        return 0, 1, None


def build_ghz(n_qubits: int) -> QuantumCircuit:
    """H on qubit 0, CX chain down the register, measure all."""
    qc = QuantumCircuit(n_qubits)
    qc.h(0)
    for i in range(n_qubits - 1):
        qc.cx(i, i + 1)
    qc.measure_all()
    return qc


def parse_args(world_size: int) -> argparse.Namespace:
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
    parser.add_argument("--repeats", type=int, default=1,
                        help="Timed runs of the same circuit. The first is "
                             "'cold' (includes one-time GPU/runtime init); "
                             "the min of the rest is the 'warm' time, i.e. "
                             "pure simulation cost (default: 1)")
    parser.add_argument("--blocking-qubits", type=int, default=None,
                        help="Enable Aer statevector chunking with chunks of "
                             "2^N amplitudes, distributed across MPI ranks "
                             "and GPUs. Required for multi-rank runs; ~23 is "
                             "the recommended value on Frontier (default: "
                             "off = single device)")
    args = parser.parse_args()

    max_q = MAX_QUBITS_MPI if world_size > 1 else MAX_QUBITS
    if not 2 <= args.qubits <= max_q:
        parser.error(f"--qubits must be in [2, {max_q}] "
                     f"(world_size={world_size})")
    if world_size > 1 and args.blocking_qubits is None:
        parser.error("--blocking-qubits is required for multi-rank runs "
                     "(without it each rank simulates independently)")
    return args


def main() -> int:
    rank, world_size, comm = get_mpi_context()
    args = parse_args(world_size)
    is_root = rank == 0

    def rprint(*a, **kw):
        if is_root:
            print(*a, **kw)

    outdir = Path(args.outdir or ".").expanduser()
    if is_root:
        outdir.mkdir(parents=True, exist_ok=True)
    shots = args.shots or 4096

    sim_options: dict = {"method": args.method, "device": args.device}
    if args.blocking_qubits is not None:
        sim_options.update(blocking_enable=True,
                           blocking_qubits=args.blocking_qubits)
    simulator = AerSimulator(**sim_options)

    available = simulator.available_devices()
    rprint(f"available devices: {available}")
    if args.device not in available:
        if is_root:
            print(f"ERROR: device {args.device} not in {available}",
                  file=sys.stderr)
        return 1

    circuit = transpile(build_ghz(args.qubits), simulator)
    run_times = []
    for _ in range(max(1, args.repeats)):
        if comm is not None:
            comm.Barrier()  # start all ranks together for honest timing
        t_start = time.perf_counter()
        result = simulator.run(circuit, shots=shots,
                               seed_simulator=args.seed).result()
        run_times.append(time.perf_counter() - t_start)
    cold_seconds = run_times[0]
    # min of the warm runs isolates steady-state simulation cost from
    # one-time init (HIP runtime, context, memory pools) and OS jitter
    warm_seconds = min(run_times[1:]) if len(run_times) > 1 else None
    run_seconds = cold_seconds

    # With MPI, Aer gives every rank the same aggregated result object;
    # only rank 0 validates and writes so fragments aren't duplicated.
    counts = result.get_counts()
    all_zero = "0" * args.qubits
    all_one = "1" * args.qubits
    ghz_fraction = (counts.get(all_zero, 0) + counts.get(all_one, 0)) / shots
    device_executed = result.results[0].metadata.get("device", "unknown")
    mpi_meta = {
        "mpi_world_size": world_size,
        "num_nodes": int(os.environ.get("SLURM_JOB_NUM_NODES", 1)),
        "blocking_qubits": args.blocking_qubits,
    }

    rprint(f"qubits={args.qubits} shots={shots} method={args.method} "
           f"ranks={world_size} nodes={mpi_meta['num_nodes']}")
    rprint(f"executed on: {device_executed} in {run_seconds:.3f}s (cold)")
    if warm_seconds is not None:
        rprint(f"warm time: {warm_seconds:.3f}s (min of {len(run_times) - 1} "
               f"repeats; overhead {cold_seconds - warm_seconds:.3f}s)")
    rprint(f"GHZ fraction: {ghz_fraction:.4f} "
           f"(|0..0>={counts.get(all_zero, 0)}, "
           f"|1..1>={counts.get(all_one, 0)})")

    if is_root:
        # --- q8020 metadata fragments (open-box, rank 0 only) ---
        experiment = meta_fragment.make_experiment_meta(
            "aer_rocm_smoke",
            experiment_id=args.experiment_id,
            workflow_id=args.workflow_id,
        )
        exp_id = experiment["experiment_id"]
        meta_fragment.write_experiment(outdir, experiment,
                                       experiment_id=exp_id)

        case = meta_fragment.make_case_meta(
            "ghz_sampling", n_qubits=args.qubits, shots=shots,
        )
        meta_fragment.write_case(outdir, case, experiment_id=exp_id)

        code = meta_fragment.make_code_meta(
            "ghz", "aer_rocm_smoke.py", run_args=vars(args),
        )
        meta_fragment.write_code(outdir, code, experiment_id=exp_id)

        # Hand-built dict conforming to metautil's BackendMeta contract
        # (metautil is a pure core now; extraction from live backends
        # lives in q8020_backend_utils.ibm.backend_meta.make_backend_meta,
        # which this smoke test skips to avoid the extra dependency).
        backend = {
            "name": simulator.name,
            "vendor": "ibm",
            "type": "simulator",
            "noise": False,
            "captured_at": datetime.now(timezone.utc).isoformat(),
            "requested_device": args.device,
            "requested_method": args.method,
            "executed_device": device_executed,
            **mpi_meta,
        }
        meta_fragment.write_backend(outdir, backend, experiment_id=exp_id)

        top_counts = dict(
            sorted(counts.items(), key=lambda kv: -kv[1])[:8]
        )
        results_meta = {
            "ghz_fraction": ghz_fraction,
            "run_seconds": run_seconds,
            "cold_seconds": cold_seconds,
            "warm_seconds": warm_seconds,
            "n_repeats": len(run_times),
            "device_executed": device_executed,
            "counts_top": top_counts,
            "n_outcomes": len(counts),
            **mpi_meta,
        }
        meta_fragment.write_results(outdir, results_meta,
                                    experiment_id=exp_id)

    # --- verdict (every rank returns the same code so srun exits clean) ---
    ok = device_executed == args.device and ghz_fraction >= MIN_GHZ_FRACTION
    if not ok and is_root:
        if device_executed != args.device:
            print(f"ERROR: requested {args.device} but executed on "
                  f"{device_executed}", file=sys.stderr)
        else:
            print(f"ERROR: GHZ fraction {ghz_fraction:.4f} below "
                  f"{MIN_GHZ_FRACTION} — distribution is wrong",
                  file=sys.stderr)
    rprint("OK" if ok else "FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
