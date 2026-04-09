"""Harvest legacy frontier-qlsa (qt02-cfd) lwfm results into metautil fragments.

Reads results.json files produced by the frontier-qlsa Hele-Shaw / tridiagonal
QLSA code (run via lwfm) and writes q8020 metadata fragments matching the
standard metautil schema.

The legacy results.json is an array of case records, each containing:
    input_parameters, matrix_properties, circuit_properties, timing,
    results (fidelity, quantum_solution, classical_solution), metadata.

This harvester maps each case record to the standard fragment set:
    experiment, case, code, backend, artifacts, results, analysis.

Input structure (lwfm):
    ~/.lwfm/out/qt02-cfd/<wf_id>/results.json
    ~/.lwfm/out/qt02-cfd/<wf_id>/checkpoint_<case_id>.json
    ~/.lwfm/out/qt02-cfd/<wf_id>/<case_id>/results.out
    ~/.lwfm/out/qt02-cfd/<wf_id>/<case_id>/input_vars_<case_id>.yaml
    ~/.lwfm/out/qt02-cfd/<wf_id>/<case_id>/hele-shaw_circ_*.qpy
    ~/.lwfm/out/qt02-cfd/<wf_id>/<case_id>/hele-shaw_metadata.pkl

Output structure (q8020):
    <output_dir>/<date>/_<wf_id>/<experiment_id>/q8020_*.json

Usage:
    # Harvest a single sweep
    python frontier_qlsa_harvester.py ~/.lwfm/out/qt02-cfd/df2add62/results.json

    # Harvest all sweeps under qt02-cfd
    python frontier_qlsa_harvester.py --lwfm-root ~/.lwfm/out/qt02-cfd

    # Specify output directory (default: ~/q8020)
    python frontier_qlsa_harvester.py --outdir ~/q8020 --lwfm-root ~/.lwfm/out/qt02-cfd

    # Dry run (show what would be written)
    python frontier_qlsa_harvester.py --dry-run --lwfm-root ~/.lwfm/out/qt02-cfd
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

from q8020_cfd_metautil.meta_fragment import (
    generate_experiment_id,
    make_case_meta,
    make_code_meta,
    make_experiment_meta,
    write_analysis,
    write_artifacts,
    write_backend,
    write_case,
    write_code,
    write_experiment,
    write_results,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _compute_fidelity(quantum: list[float], classical: list[float]) -> float:
    """Compute state fidelity |<q|c>|^2 between normalised solution vectors."""
    q = np.array(quantum, dtype=float)
    c = np.array(classical, dtype=float)
    qn = np.linalg.norm(q)
    cn = np.linalg.norm(c)
    if qn == 0 or cn == 0:
        return 0.0
    return float(np.abs(np.dot(q / qn, c / cn)) ** 2)


def _compute_l2_error(quantum: list[float], classical: list[float]) -> dict[str, float]:
    """Compute L2 error metrics between quantum and classical solutions."""
    q = np.array(quantum, dtype=float)
    c = np.array(classical, dtype=float)
    cn = np.linalg.norm(c)
    diff = np.linalg.norm(q - c)
    return {
        "l2_error_abs": float(diff),
        "l2_error_rel": float(diff / cn) if cn > 0 else float("inf"),
    }


def _backend_type_from_name(name: str) -> str:
    """Infer backend type string from backend name."""
    if name.startswith("ibm_") or name.startswith("ibmq_"):
        return "hardware"
    if "statevector" in name:
        return "simulator"
    if "density_matrix" in name:
        return "simulator"
    if "matrix_product_state" in name:
        return "simulator"
    return "simulator"


def _inventory_case_dir(case_dir: Path) -> dict[str, list[dict[str, Any]]]:
    """Build file inventory for a legacy case subdirectory."""
    inventory: dict[str, list[dict[str, Any]]] = {
        "qpy": [],
        "pkl": [],
        "yaml": [],
        "png": [],
        "csv": [],
        "other": [],
    }

    if not case_dir.is_dir():
        return inventory

    for fp in case_dir.iterdir():
        if not fp.is_file():
            continue
        stat = fp.stat()
        info = {
            "name": fp.name,
            "size_bytes": stat.st_size,
            "modified": datetime.fromtimestamp(
                stat.st_mtime, tz=timezone.utc
            ).isoformat().replace("+00:00", "Z"),
        }
        ext = fp.suffix.lower()
        if ext == ".qpy":
            inventory["qpy"].append(info)
        elif ext == ".pkl":
            inventory["pkl"].append(info)
        elif ext in (".yaml", ".yml"):
            inventory["yaml"].append(info)
        elif ext == ".png":
            inventory["png"].append(info)
        elif ext == ".csv":
            inventory["csv"].append(info)
        else:
            inventory["other"].append(info)

    return inventory


# ---------------------------------------------------------------------------
# Fragment builders (one case record → fragment dicts)
# ---------------------------------------------------------------------------

def _build_experiment(wf_id: str, experiment_id: str) -> dict[str, Any]:
    """Build experiment fragment for a legacy case."""
    return make_experiment_meta(
        name=f"frontier-qlsa-{wf_id}",
        experiment_id=experiment_id,
        workflow_id=wf_id,
    )


def _build_case(record: dict[str, Any]) -> dict[str, Any]:
    """Build case fragment from a legacy results.json record."""
    inp = record.get("input_parameters", {})
    mat = record.get("matrix_properties", {})

    case = make_case_meta(
        name=inp.get("case", "hele-shaw"),
        case_id=record.get("case_id", "unknown"),
        nx=inp.get("nx"),
        ny=inp.get("ny"),
        mu=inp.get("mu"),
        NQ_MATRIX=inp.get("NQ_MATRIX"),
        max_condition_number=inp.get("max_condition_number"),
        matrix_size_original=mat.get("size_original"),
        matrix_size_hermitian=mat.get("size_hermitian"),
        condition_number_original=mat.get("condition_number_original"),
        condition_number_hermitian=mat.get("condition_number_hermitian"),
    )
    case["_source"] = "harvester"
    return case


def _build_code(record: dict[str, Any]) -> dict[str, Any]:
    """Build code fragment."""
    code = make_code_meta(
        algorithm="hhl",
        entry_point="circuit_HHL.py",
        run_args={
            "qc_shots": record.get("input_parameters", {}).get("qc_shots"),
            "qc_backend": record.get("input_parameters", {}).get("qc_backend"),
        },
    )
    code["_source"] = "harvester"
    return code


def _build_backend(record: dict[str, Any]) -> dict[str, Any]:
    """Build backend fragment from case record."""
    inp = record.get("input_parameters", {})
    circ = record.get("circuit_properties", {})
    backend_name = inp.get("qc_backend", "unknown")

    backend: dict[str, Any] = {
        "name": backend_name,
        "vendor": "ibm",
        "type": _backend_type_from_name(backend_name),
        "noise": _backend_type_from_name(backend_name) == "hardware",
        "nshots": inp.get("qc_shots"),
        "_source": "harvester",
    }

    num_qubits = circ.get("num_qubits")
    if num_qubits is not None:
        backend["num_qubits"] = num_qubits

    return backend


def _build_artifacts(
    record: dict[str, Any],
    case_dir: Path | None = None,
) -> dict[str, Any]:
    """Build artifacts fragment from circuit_properties and timing."""
    circ = record.get("circuit_properties", {})
    timing = record.get("timing", {})

    # Guard against explicit None values in the JSON (key present, value null)
    gen_time = timing.get("circuit_generation_sec") or 0.0
    construct_time = timing.get("circuit_construction_sec") or 0.0
    exec_time = timing.get("execution_sec") or 0.0

    transpile_pass: dict[str, Any] = {
        "step": 0,
        "wall_time_generate_s": round(gen_time + construct_time, 6),
        "wall_time_transpile_s": 0.0,
        "wall_time_execute_s": round(exec_time, 6),
        "before": {
            "depth": circ.get("depth") or 0,
            "num_qubits": circ.get("num_qubits") or 0,
            "gate_count": circ.get("num_gates") or 0,
        },
        "after": {
            "depth": circ.get("depth_transpiled") or 0,
            "num_qubits": circ.get("num_qubits") or 0,
            "gate_count": circ.get("num_gates_transpiled") or 0,
        },
    }

    mat = record.get("matrix_properties", {})
    linear_system: dict[str, Any] = {}
    if mat:
        linear_system["matrix_size_original"] = mat.get("size_original") or 0
        linear_system["matrix_size_hermitian"] = mat.get("size_hermitian") or 0
        cond = mat.get("condition_number_original")
        if cond is not None:
            linear_system["condition_number_range"] = [
                round(float(cond), 4),
                round(float(cond), 4),
            ]

    total_time = gen_time + construct_time + exec_time

    file_inventory = _inventory_case_dir(case_dir) if case_dir else {}

    artifacts: dict[str, Any] = {
        "transpile_passes": [transpile_pass],
        "circuit_timing_total_s": {
            "generate": round(gen_time + construct_time, 6),
            "transpile": 0.0,
            "execute": round(exec_time, 6),
            "total": round(total_time, 6),
        },
        "linear_system": linear_system,
        "_source": "harvester",
    }
    if file_inventory:
        artifacts["file_inventory"] = file_inventory

    return artifacts


def _build_results(record: dict[str, Any]) -> dict[str, Any]:
    """Build results fragment with quantum and classical solutions."""
    res = record.get("results", {})

    results: dict[str, Any] = {
        "quantum_solution": res.get("quantum_solution", []),
        "classical_solution": res.get("classical_solution", []),
        "_source": "harvester",
    }

    return results


def _build_analysis(record: dict[str, Any]) -> dict[str, Any]:
    """Build analysis fragment with fidelity and error metrics."""
    res = record.get("results", {})
    inp = record.get("input_parameters", {})

    fidelity = res.get("fidelity")
    quantum_sol = res.get("quantum_solution", [])
    classical_sol = res.get("classical_solution", [])

    # Recompute fidelity if not present but solutions are
    if fidelity is None and quantum_sol and classical_sol:
        fidelity = _compute_fidelity(quantum_sol, classical_sol)

    analysis: dict[str, Any] = {
        "iterations_completed": 1,
        "converged": True,
        "_source": "harvester",
    }

    if fidelity is not None:
        analysis["fidelity"] = fidelity

    shots = inp.get("qc_shots")
    if shots is not None:
        analysis["shots"] = shots

    # Compute L2 error if solutions available
    if quantum_sol and classical_sol:
        l2 = _compute_l2_error(quantum_sol, classical_sol)
        analysis["l2_error_abs"] = l2["l2_error_abs"]
        analysis["l2_error_rel"] = l2["l2_error_rel"]

    return analysis


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def harvest_results_json(
    results_path: Path,
    output_root: Path,
    dry_run: bool = False,
    in_place: bool = False,
) -> list[Path]:
    """Harvest a single results.json into q8020 fragments.

    Args:
        results_path: Path to results.json
        output_root: Root output directory (e.g. ~/q8020)
        dry_run: If True, print what would be written but don't write
        in_place: If True, write fragments into case subdirs next to
                  results.json (or its copy in experiment project)

    Returns:
        List of output directories created (one per case)
    """
    with open(results_path, "r", encoding="utf-8") as f:
        records = json.load(f)

    if not isinstance(records, list):
        records = [records]

    # Derive wf_id from parent directory name
    wf_id = results_path.parent.name
    wf_dir = results_path.parent

    # Use a fixed date derived from the results.json mtime
    results_mtime = results_path.stat().st_mtime
    date_str = datetime.fromtimestamp(results_mtime, tz=timezone.utc).strftime(
        "%Y-%m-%d"
    )

    output_dirs: list[Path] = []

    # Also build a sweep-level summary
    sweep_summary: list[dict[str, Any]] = []

    for record in records:
        case_id = record.get("case_id", "unknown")
        experiment_id = generate_experiment_id()

        if in_place:
            # Write fragments into the case subdir alongside existing data
            case_outdir = wf_dir / case_id
            if not case_outdir.is_dir():
                case_outdir.mkdir(parents=True, exist_ok=True)
        else:
            # Output directory: <output_root>/<date>/_<wf_id>/<experiment_id>/
            case_outdir = output_root / date_str / f"_{wf_id}" / experiment_id

        # Find the legacy case subdirectory for file inventory
        case_subdir = wf_dir / case_id
        if not case_subdir.is_dir():
            case_subdir = None

        if dry_run:
            inp = record.get("input_parameters", {})
            backend = inp.get("qc_backend", "?")
            shots = inp.get("qc_shots", "?")
            fidelity = record.get("results", {}).get("fidelity", "?")
            print(
                f"  {case_id}: backend={backend}, shots={shots}, "
                f"fidelity={fidelity} → {case_outdir}"
            )
            output_dirs.append(case_outdir)
            continue

        # Build and write all fragments
        experiment = _build_experiment(wf_id, experiment_id)
        case = _build_case(record)
        code = _build_code(record)
        backend = _build_backend(record)
        artifacts = _build_artifacts(record, case_subdir)
        results = _build_results(record)
        analysis = _build_analysis(record)

        write_experiment(case_outdir, experiment, experiment_id=experiment_id)
        write_case(case_outdir, case, experiment_id=experiment_id)
        write_code(case_outdir, code, experiment_id=experiment_id)
        write_backend(case_outdir, backend, experiment_id=experiment_id)
        write_artifacts(case_outdir, artifacts, experiment_id=experiment_id)
        write_results(case_outdir, results, experiment_id=experiment_id)
        write_analysis(case_outdir, analysis, experiment_id=experiment_id)

        output_dirs.append(case_outdir)

        # Collect summary record
        sweep_summary.append({
            "case_id": case_id,
            "experiment_id": experiment_id,
            "output_dir": str(case_outdir),
            "backend": record.get("input_parameters", {}).get("qc_backend"),
            "shots": record.get("input_parameters", {}).get("qc_shots"),
            "fidelity": record.get("results", {}).get("fidelity"),
            "quantum_solution": record.get("results", {}).get("quantum_solution"),
            "classical_solution": record.get("results", {}).get("classical_solution"),
            "num_qubits": record.get("circuit_properties", {}).get("num_qubits"),
            "circuit_depth": record.get("circuit_properties", {}).get("depth_transpiled"),
            "execution_sec": record.get("timing", {}).get("execution_sec"),
        })

    # Write sweep-level summary JSON
    if not dry_run and sweep_summary:
        summary_path = wf_dir / "q8020_sweep_summary.json"
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "wf_id": wf_id,
                    "date": date_str,
                    "num_cases": len(sweep_summary),
                    "cases": sweep_summary,
                    "_source": "harvester",
                },
                f,
                indent=2,
            )
        print(f"  Summary → {summary_path}", file=sys.stderr)

    return output_dirs


def harvest_lwfm_root(
    lwfm_root: Path,
    output_root: Path,
    dry_run: bool = False,
    in_place: bool = False,
) -> list[Path]:
    """Scan an lwfm output tree for results.json files and harvest all.

    Args:
        lwfm_root: Root of lwfm output tree (e.g. ~/.lwfm/out/qt02-cfd)
        output_root: Root output directory (e.g. ~/q8020)
        dry_run: If True, print what would be written but don't write
        in_place: If True, write fragments into case subdirs

    Returns:
        List of all output directories created
    """
    all_dirs: list[Path] = []

    results_files = sorted(lwfm_root.glob("*/results.json"))
    if not results_files:
        print(f"No results.json files found under {lwfm_root}", file=sys.stderr)
        return all_dirs

    print(
        f"Found {len(results_files)} completed sweeps under {lwfm_root}",
        file=sys.stderr,
    )

    for results_path in results_files:
        wf_id = results_path.parent.name
        print(f"\n--- Sweep {wf_id} ---", file=sys.stderr)
        dirs = harvest_results_json(
            results_path, output_root, dry_run=dry_run, in_place=in_place,
        )
        all_dirs.extend(dirs)

    return all_dirs


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Harvest legacy frontier-qlsa (qt02-cfd) results into q8020 metautil fragments",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  # Single sweep
  python frontier_qlsa_harvester.py ~/.lwfm/out/qt02-cfd/df2add62/results.json

  # All sweeps
  python frontier_qlsa_harvester.py --lwfm-root ~/.lwfm/out/qt02-cfd

  # Dry run
  python frontier_qlsa_harvester.py --dry-run --lwfm-root ~/.lwfm/out/qt02-cfd

  # Custom output dir
  python frontier_qlsa_harvester.py --outdir /tmp/q8020 --lwfm-root ~/.lwfm/out/qt02-cfd
""",
    )
    parser.add_argument(
        "results_json",
        nargs="?",
        default=None,
        help="Path to a single results.json file",
    )
    parser.add_argument(
        "--lwfm-root",
        type=str,
        default=None,
        help="Root of lwfm output tree (scans for */results.json)",
    )
    parser.add_argument(
        "--outdir",
        type=str,
        default="~/q8020",
        help="Output root directory (default: ~/q8020)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be written without writing",
    )
    parser.add_argument(
        "--in-place",
        action="store_true",
        help="Write fragments into case subdirs alongside results.json",
    )

    args = parser.parse_args()
    output_root = Path(args.outdir).expanduser().resolve()

    if args.results_json:
        results_path = Path(args.results_json).expanduser().resolve()
        if not results_path.exists():
            print(f"Error: {results_path} not found", file=sys.stderr)
            sys.exit(1)
        print(f"Harvesting {results_path}", file=sys.stderr)
        dirs = harvest_results_json(
            results_path, output_root,
            dry_run=args.dry_run, in_place=args.in_place,
        )

    elif args.lwfm_root:
        lwfm_root = Path(args.lwfm_root).expanduser().resolve()
        if not lwfm_root.exists():
            print(f"Error: {lwfm_root} not found", file=sys.stderr)
            sys.exit(1)
        dirs = harvest_lwfm_root(
            lwfm_root, output_root,
            dry_run=args.dry_run, in_place=args.in_place,
        )

    else:
        print(
            "Error: Must specify either a results.json path or --lwfm-root",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"\n{'Would write' if args.dry_run else 'Wrote'} {len(dirs)} case fragments", file=sys.stderr)
    if not args.dry_run and dirs:
        print(f"Output root: {output_root}", file=sys.stderr)


if __name__ == "__main__":
    main()
