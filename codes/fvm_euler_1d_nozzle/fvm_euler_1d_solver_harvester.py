"""Generate metadata JSON from FVM Euler 1D solver output directory.

Parses the output files from nozzle_1d_solver.py runs and produces a
structured metadata.json conforming to the make_meta schema.

Usage:
    fvm-euler-1d-meta --outdir /tmp/fvm
    fvm-euler-1d-meta --outdir /tmp/fvm --output metadata.json
"""

import argparse
import csv
import json
import pickle
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from q8020_cfd_metautil.meta_fragment import (
    write_analysis,
    write_artifacts,
    write_backend,
    write_case,
    write_code,
    write_results,
)


def _parse_csv_to_dicts(csv_path: Path) -> list[dict[str, Any]]:
    """Parse a CSV file with header row into list of dicts."""
    if not csv_path.exists():
        return []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, skipinitialspace=True)
        return [row for row in reader]


def _parse_csv_to_floats(csv_path: Path) -> list[dict[str, float]]:
    """Parse CSV and convert all values to floats where possible."""
    rows = _parse_csv_to_dicts(csv_path)
    result = []
    for row in rows:
        converted = {}
        for k, v in row.items():
            k = k.strip()
            try:
                converted[k] = float(v)
            except (ValueError, TypeError):
                converted[k] = v
        converted = {k: v for k, v in converted.items() if k}
        result.append(converted)
    return result


def _load_pickle(pkl_path: Path) -> dict[str, Any] | None:
    """Load a pickle file, returning None if not found."""
    if not pkl_path.exists():
        return None
    with open(pkl_path, "rb") as f:
        return pickle.load(f)


def _inventory_files(outdir: Path) -> dict[str, list[dict[str, Any]]]:
    """Categorize FVM solver-created files in output directory by type.
    
    Skips sweeper-created files (q8020_*, stdout.txt, stderr.txt, metadata.json, etc.)
    """
    inventory: dict[str, list[dict[str, Any]]] = {
        "qpy_generated": [],
        "qpy_transpiled": [],
        "csv": [],
        "pkl": [],
        "png": [],
        "other": [],
    }

    for file_path in outdir.iterdir():
        if not file_path.is_file():
            continue

        # Skip sweeper-created files (all prefixed with q8020_)
        if file_path.name.startswith("q8020_"):
            continue

        stat = file_path.stat()
        info = {
            "name": file_path.name,
            "size_bytes": stat.st_size,
            "modified": datetime.fromtimestamp(
                stat.st_mtime, tz=timezone.utc
            ).isoformat().replace("+00:00", "Z"),
        }

        if file_path.suffix == ".qpy":
            if "generated" in file_path.name:
                inventory["qpy_generated"].append(info)
            elif "transpile" in file_path.name:
                inventory["qpy_transpiled"].append(info)
            else:
                inventory["other"].append(info)
        elif file_path.suffix == ".csv":
            inventory["csv"].append(info)
        elif file_path.suffix == ".pkl":
            inventory["pkl"].append(info)
        elif file_path.suffix == ".png":
            inventory["png"].append(info)
        else:
            inventory["other"].append(info)

    return inventory


def _extract_run_params(outdir: Path) -> dict[str, Any]:
    """Extract run parameters from metadata pickle file."""
    # Find metadata pickle
    pkl_files = list(outdir.glob("metadata_*.pkl"))
    if not pkl_files:
        return {}

    metadata = _load_pickle(pkl_files[0])
    if metadata is None:
        return {}

    # Convert numpy types to Python types for JSON serialization
    result = {}
    for k, v in metadata.items():
        if hasattr(v, "item"):  # numpy scalar
            result[k] = v.item()
        elif isinstance(v, dict):
            result[k] = {
                kk: vv.item() if hasattr(vv, "item") else vv
                for kk, vv in v.items()
            }
        else:
            result[k] = v
    return result


def _extract_hhl_metrics(outdir: Path) -> list[dict[str, float]]:
    """Extract HHL metrics from CSV."""
    csv_files = list(outdir.glob("hhl_metrics_*.csv"))
    if not csv_files:
        return []
    return _parse_csv_to_floats(csv_files[0])


def _extract_qc_metadata(outdir: Path) -> list[dict[str, Any]]:
    """Extract quantum circuit metadata from CSV."""
    csv_files = list(outdir.glob("qc_metadata_*.csv"))
    if not csv_files:
        return []
    return _parse_csv_to_floats(csv_files[0])


def _extract_final_results(outdir: Path) -> list[dict[str, float]]:
    """Extract final solution results from CSV."""
    csv_files = list(outdir.glob("final_results_*.csv"))
    if not csv_files:
        return []
    return _parse_csv_to_floats(csv_files[0])


def _extract_residuals(outdir: Path) -> list[dict[str, float]]:
    """Extract residual history from CSV."""
    csv_files = list(outdir.glob("residual_*.csv"))
    if not csv_files:
        return []
    return _parse_csv_to_floats(csv_files[0])


def _read_stdout(outdir: Path) -> str:
    """Read the first q8020_stdout_*.txt file, or run.log, or return empty string."""
    stdout_files = list(outdir.glob("q8020_stdout_*.txt"))
    if stdout_files:
        return stdout_files[0].read_text(encoding="utf-8", errors="replace")
    # Fallback: Frontier runs produce run.log instead of q8020_stdout
    run_log = outdir / "run.log"
    if run_log.exists():
        return run_log.read_text(encoding="utf-8", errors="replace")
    return ""


def _parse_stdout_lu_solutions(outdir: Path) -> list[dict[str, list[float]]]:
    """Parse LU and HHL solution vectors from stdout comparison tables.

    Each iteration prints a block like:
        LU sol \t    Herm LU sol    HHL sol    L1_diff(%)
        -7.736e-02  -7.736e-02  -0.000e+00  1.000e+02
        ...
        ====...====

    Returns list of dicts (one per iteration), each with:
        {"lu": [float, ...], "hhl": [float, ...]}
    """
    text = _read_stdout(outdir)
    if not text:
        return []

    results: list[dict[str, list[float]]] = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.strip().startswith("LU sol") and "HHL sol" in line:
            i += 1
            lu_vals: list[float] = []
            hhl_vals: list[float] = []
            while i < len(lines):
                row = lines[i].strip()
                if not row or row.startswith("="):
                    break
                parts = row.split()
                if len(parts) >= 3:
                    try:
                        lu_vals.append(float(parts[0]))
                        hhl_vals.append(float(parts[2]))
                    except ValueError:
                        break
                i += 1
            if lu_vals:
                results.append({"lu": lu_vals, "hhl": hhl_vals})
        i += 1

    return results


def _parse_stdout_backend(outdir: Path) -> dict[str, Any]:
    """Parse stdout for backend and shots info as fallback.

    Looks for lines like:
        Backend: aer_simulator_statevector
        Shots: 1024
    """
    text = _read_stdout(outdir)
    if not text:
        return {}

    result: dict[str, Any] = {}

    m = re.search(r"Backend:\s*(\S+)", text)
    if m:
        result["name"] = m.group(1)

    m = re.search(r"Shots:\s*(\d+)", text)
    if m:
        result["nshots"] = int(m.group(1))

    return result


def _extract_per_iteration_results(
    outdir: Path,
) -> list[dict[str, Any]]:
    """Glob per-iteration results and dq CSVs, sorted by iter number."""
    # results_nelem*_iter*_*.csv
    result_files = sorted(
        outdir.glob("results_nelem*_iter*_*.csv"),
        key=lambda p: int(re.search(r"iter(\d+)", p.name).group(1))  # type: ignore[union-attr]
    )
    # dq_nelem*_iter*_*.csv
    dq_files = sorted(
        outdir.glob("dq_nelem*_iter*_*.csv"),
        key=lambda p: int(re.search(r"iter(\d+)", p.name).group(1))  # type: ignore[union-attr]
    )

    # Build lookup of dq by step
    dq_by_step: dict[int, list[dict[str, float]]] = {}
    for dq_path in dq_files:
        m = re.search(r"iter(\d+)", dq_path.name)
        if m:
            step = int(m.group(1))
            dq_by_step[step] = _parse_csv_to_floats(dq_path)

    per_iter: list[dict[str, Any]] = []
    for res_path in result_files:
        m = re.search(r"iter(\d+)", res_path.name)
        if not m:
            continue
        step = int(m.group(1))
        entry: dict[str, Any] = {
            "step": step,
            "solution": _parse_csv_to_floats(res_path),
        }
        if step in dq_by_step:
            entry["dq"] = dq_by_step[step]
        per_iter.append(entry)

    return per_iter


# ---------------------------------------------------------------------------
# Fragment builders
# ---------------------------------------------------------------------------

def _build_backend(
    run_params: dict[str, Any],
    qc_metadata: list[dict[str, Any]],
    outdir: Path,
) -> dict[str, Any]:
    """Build backend fragment from pickle, qc_metadata CSV, and stdout fallback."""
    # Start with pickle data
    backend_type = run_params.get("backend_type", "")
    backend_method = run_params.get("backend_method", "")
    nshots = run_params.get("nshots", 0)

    # Derive name from pickle fields
    name = ""
    if backend_type and backend_method:
        name = f"{backend_type}_{backend_method}"
    elif backend_type:
        name = backend_type

    # Fallback to stdout if pickle didn't provide backend info
    if not name:
        stdout_info = _parse_stdout_backend(outdir)
        name = stdout_info.get("name", "unknown")
        if not nshots:
            nshots = stdout_info.get("nshots", 0)

    # Determine noise from name
    noise = "fake_" in name.lower() or "fake " in str(run_params.get("backend_type", "")).lower()

    # Determine simulator type
    sim_type = "simulator"

    # num_qubits from first row of qc_metadata CSV
    num_qubits = None
    if qc_metadata:
        nq = qc_metadata[0].get("nqubits")
        if nq is not None:
            num_qubits = int(nq)

    backend: dict[str, Any] = {
        "name": name,
        "type": sim_type,
        "method": backend_method or "statevector",
        "noise": noise,
        "_source": "solver",
    }
    if num_qubits is not None:
        backend["num_qubits"] = num_qubits
    if nshots:
        backend["nshots"] = int(nshots) if not isinstance(nshots, int) else nshots

    return backend


def _build_artifacts(
    qc_metadata: list[dict[str, Any]],
    file_inventory: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    """Build artifacts fragment with transpile_passes[], circuit_timing, linear_system."""
    transpile_passes: list[dict[str, Any]] = []
    total_generate = 0.0
    total_transpile = 0.0
    total_execute = 0.0
    condition_numbers: list[float] = []

    for row in qc_metadata:
        step = int(row.get("step", 0))

        gen_time = row.get("circ_generate_time", 0.0)
        trans_time = row.get("circ_transpile_time", 0.0)
        run_time = row.get("circ_run_time", 0.0)
        total_generate += gen_time
        total_transpile += trans_time
        total_execute += run_time

        cond = row.get("condition_number")
        if cond is not None:
            condition_numbers.append(float(cond))

        pass_entry: dict[str, Any] = {
            "step": step,
            "wall_time_generate_s": round(gen_time, 6),
            "wall_time_transpile_s": round(trans_time, 6),
            "wall_time_execute_s": round(run_time, 6),
            "before": {
                "depth": int(row.get("circ_depth_orig", 0)),
                "num_qubits": int(row.get("circ_qubits_orig", 0)),
                "gate_count": int(row.get("circ_gates_orig", 0)),
            },
            "after": {
                "depth": int(row.get("circ_depth_transpile", 0)),
                "num_qubits": int(row.get("circ_qubits_transpile", 0)),
                "gate_count": int(row.get("circ_gates_transpile", 0)),
            },
        }
        transpile_passes.append(pass_entry)

    total_time = total_generate + total_transpile + total_execute

    # Linear system summary from qc_metadata
    linear_system: dict[str, Any] = {}
    if qc_metadata:
        first = qc_metadata[0]
        linear_system["matrix_size_original"] = int(first.get("matrix_size_orig", 0))
        linear_system["matrix_size_padded"] = int(first.get("matrix_size_pow2", 0))
        linear_system["matrix_size_hermitian"] = int(first.get("matrix_size_herm", 0))
    if condition_numbers:
        linear_system["condition_number_range"] = [
            round(min(condition_numbers), 4),
            round(max(condition_numbers), 4),
        ]

    artifacts: dict[str, Any] = {
        "transpile_passes": transpile_passes,
        "circuit_timing_total_s": {
            "generate": round(total_generate, 6),
            "transpile": round(total_transpile, 6),
            "execute": round(total_execute, 6),
            "total": round(total_time, 6),
        },
        "linear_system": linear_system,
        "file_inventory": file_inventory,
        "_source": "solver",
    }

    return artifacts


def _build_results(
    final_results: list[dict[str, float]],
    residuals: list[dict[str, float]],
    outdir: Path,
) -> dict[str, Any]:
    """Build results fragment with final_solution, per_iteration, residual_history."""
    per_iteration = _extract_per_iteration_results(outdir)
    lu_hhl_vectors = _parse_stdout_lu_solutions(outdir)

    # Merge LU/HHL solution vectors into per_iteration entries by index
    for idx, entry in enumerate(per_iteration):
        if idx < len(lu_hhl_vectors):
            entry["lu_reference_vector"] = lu_hhl_vectors[idx]["lu"]
            entry["hhl_solution_vector"] = lu_hhl_vectors[idx]["hhl"]

    results: dict[str, Any] = {
        "final_solution": final_results,
        "per_iteration": per_iteration,
        "residual_history": residuals,
        "_source": "solver",
    }

    # Add final iteration's LU reference at top level for parity with axb
    if lu_hhl_vectors:
        results["lu_reference_vector_final"] = lu_hhl_vectors[-1]["lu"]

    return results


def _build_analysis(
    hhl_metrics: list[dict[str, float]],
    residuals: list[dict[str, float]],
    run_params: dict[str, Any],
) -> dict[str, Any]:
    """Build analysis fragment with summary scalars and full per-iteration metrics."""
    # Top-level scalars from last iteration
    fidelity = None
    l2_error_normalized = None
    residual = None
    shots = run_params.get("nshots")
    if shots is not None:
        shots = int(shots)

    iterations_completed = len(hhl_metrics)

    # Per-iteration hhl_metrics array with step numbers
    hhl_metrics_out: list[dict[str, Any]] = []
    for row in hhl_metrics:
        entry: dict[str, Any] = {"step": int(row.get("step", 0))}
        for key in ("fidelity", "l2_error_abs", "l2_error_rel",
                    "l2_error_normalized", "linsys_residual"):
            if key in row:
                entry[key] = row[key]
        hhl_metrics_out.append(entry)

    if hhl_metrics:
        last = hhl_metrics[-1]
        fidelity = last.get("fidelity")
        l2_error_normalized = last.get("l2_error_normalized")
        residual = last.get("linsys_residual")

    # Residual reduction from CFD residual history
    residual_reduction = None
    cfd_residual = None
    if residuals and len(residuals) >= 2:
        first_res = residuals[0].get("residual_total")
        last_res = residuals[-1].get("residual_total")
        cfd_residual = last_res
        if first_res and last_res and first_res != 0:
            residual_reduction = round(last_res / first_res, 6)
    elif residuals:
        cfd_residual = residuals[-1].get("residual_total")

    # Convergence: check conv_tol from pickle or residual stagnation
    converged = False
    conv_tol = run_params.get("conv_tol")
    if conv_tol is not None and cfd_residual is not None:
        converged = cfd_residual <= conv_tol

    analysis: dict[str, Any] = {
        "iterations_completed": iterations_completed,
        "converged": converged,
        "_source": "solver",
    }
    if fidelity is not None:
        analysis["fidelity"] = fidelity
    if l2_error_normalized is not None:
        analysis["l2_error_normalized"] = l2_error_normalized
    if residual is not None:
        analysis["residual"] = residual
    if shots is not None:
        analysis["shots"] = shots
    if residual_reduction is not None:
        analysis["residual_reduction"] = residual_reduction
    analysis["hhl_metrics"] = hhl_metrics_out

    return analysis


def generate_metadata(
    outdir: Path,
    experiment_id: str | None = None,
    write_dir: Path | None = None,
) -> dict[str, Any]:
    """
    Generate structured metadata from FVM Euler 1D solver output.

    This harvester only writes solver-specific metadata fragments.
    The sweeper handles experiment/workflow IDs, user info, and params.

    Args:
        outdir: Path to the solver output directory (read artifacts from here)
        experiment_id: Experiment ID from sweeper (used for fragment filenames)
        write_dir: Directory to write fragment files to.  Defaults to *outdir*.

    Returns:
        Metadata dict conforming to make_meta schema
    """
    if write_dir is None:
        write_dir = outdir
    run_params = _extract_run_params(outdir)
    hhl_metrics = _extract_hhl_metrics(outdir)
    qc_metadata = _extract_qc_metadata(outdir)
    final_results = _extract_final_results(outdir)
    residuals = _extract_residuals(outdir)
    file_inventory = _inventory_files(outdir)

    # Build case section (problem definition - solver-specific)
    case = {
        "_source": "solver",
        "name": "nozzle_1d",
        "nelem": run_params.get("nelem"),
        "time_scheme": run_params.get("time_scheme"),
        "cfl": run_params.get("cfl"),
        "max_iters": run_params.get("max_iters"),
        "max_inner_iters": run_params.get("max_inner_iters"),
        "conv_tol": run_params.get("conv_tol"),
        "res_tol": run_params.get("res_tol"),
        "localdt": run_params.get("localdt"),
        "nondim": run_params.get("nondim"),
        "area_equation": run_params.get("area_equation"),
        "reference_values": {
            "rho_ref": run_params.get("rho_ref"),
            "u_ref": run_params.get("u_ref"),
            "p_ref": run_params.get("p_ref"),
        },
    }

    # Build code section (solver-specific; library_versions captured by sweeper via _env)
    code = {
        "_source": "solver",
        "algorithm": run_params.get("linear_solver", "HHL"),
    }

    # Build fragment sections
    backend = _build_backend(run_params, qc_metadata, outdir)
    artifacts = _build_artifacts(qc_metadata, file_inventory)
    results = _build_results(final_results, residuals, outdir)
    analysis = _build_analysis(hhl_metrics, residuals, run_params)

    # Write solver-specific fragments (sweeper handles experiment, params, IDs)
    write_case(write_dir, case, experiment_id=experiment_id)
    write_code(write_dir, code, experiment_id=experiment_id)
    write_backend(write_dir, backend, experiment_id=experiment_id)
    write_artifacts(write_dir, artifacts, experiment_id=experiment_id)
    write_results(write_dir, results, experiment_id=experiment_id)
    write_analysis(write_dir, analysis, experiment_id=experiment_id)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate metadata fragments from FVM Euler 1D solver output",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  fvm-euler-1d-meta --outdir /tmp/fvm
  fvm-euler-1d-meta /path/to/q8020_case_postproc.json  (sweep postproc mode)
""",
    )
    parser.add_argument(
        "--outdir", "-d",
        type=str,
        default=None,
        help="Path to solver output directory",
    )
    parser.add_argument(
        "postproc_json",
        nargs="?",
        default=None,
        help="Postproc JSON file from sweep (contains case_dir)",
    )

    args = parser.parse_args()

    # Determine outdir and experiment_id from either --outdir or postproc JSON
    experiment_id = None
    if args.postproc_json:
        with open(args.postproc_json, "r", encoding="utf-8") as f:
            postproc_data = json.load(f)
        outdir = Path(postproc_data["case_dir"]).expanduser().resolve()
        experiment_id = postproc_data.get("experiment_id")
    elif args.outdir:
        outdir = Path(args.outdir).expanduser().resolve()
    else:
        print("Error: Must specify --outdir or provide postproc JSON", file=sys.stderr)
        sys.exit(1)

    if not outdir.exists():
        print(f"Error: Output directory does not exist: {outdir}", file=sys.stderr)
        sys.exit(1)

    generate_metadata(outdir, experiment_id=experiment_id)

    print(f"✅ Metadata fragments written to: {outdir}", file=sys.stderr)


if __name__ == "__main__":
    main()
