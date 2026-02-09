"""Batch-harvest Frontier nelem5 FVM runs into q8020 metadata.

Walks ~/q8020/fromFrontier/nelem5/statevector/ to find all leaf case
directories (exact, shots_*/trial_*), runs the FVM harvester on each,
assembles the unified metadata rollup, and renames each directory to
embed the experiment ID.

Usage:
    python harvest_frontier_nelem5.py [--data-root ~/q8020/fromFrontier/nelem5/statevector]
    python harvest_frontier_nelem5.py --dry-run
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from q8020_cfd_metautil.harvest import harvest_metadata
from q8020_cfd_metautil.meta_fragment import (
    generate_experiment_id,
    generate_workflow_id,
    make_user_meta,
    write_experiment,
)

# Import the FVM harvester's generate_metadata directly
from fvm_euler_1d_solver_harvester import generate_metadata


def discover_case_dirs(root: Path) -> list[Path]:
    """Find all leaf case directories under the statevector root.

    Returns sorted list of:
      - root/exact  (flat case, no trial subdirs)
      - root/shots_*/trial_*  (shot-sweep cases)
    """
    case_dirs: list[Path] = []

    for child in sorted(root.iterdir()):
        if not child.is_dir():
            continue

        if child.name == "exact":
            # Flat case: solver output lives directly here
            case_dirs.append(child)
        elif child.name.startswith("shots_"):
            # Shot-sweep: each trial_* subdir is a case
            trials = sorted(
                [t for t in child.iterdir() if t.is_dir() and t.name.startswith("trial_")],
                key=lambda p: int(p.name.split("_")[1]),
            )
            case_dirs.extend(trials)

    return case_dirs


def harvest_one(case_dir: Path, dry_run: bool = False) -> dict:
    """Harvest a single case directory.

    Returns dict with: experiment_id, original_path, new_path, and summary metrics.
    """
    exp_id = generate_experiment_id()
    wf_id = generate_workflow_id(exp_id)
    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    if dry_run:
        new_name = f"{case_dir.name}_{exp_id}"
        new_path = case_dir.parent / new_name
        return {
            "experiment_id": exp_id,
            "original_path": str(case_dir),
            "new_path": str(new_path),
            "dry_run": True,
        }

    # 1. Write experiment fragment (what the sweeper would normally do)
    experiment_data = {
        "_source": "harvest",
        "name": "frontier_nelem5",
        "experiment_id": exp_id,
        "workflow_id": wf_id,
        "timestamp": timestamp,
        "user": make_user_meta(),
    }
    write_experiment(case_dir, experiment_data, experiment_id=exp_id)

    # 2. Run FVM harvester -- writes case, code, backend, artifacts, results, analysis fragments
    generate_metadata(case_dir, experiment_id=exp_id)

    # 3. Assemble unified metadata rollup
    metadata, warnings, fragment_counts = harvest_metadata(case_dir)
    output_path = case_dir / f"q8020_metadata_{exp_id}.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    # 4. Extract summary metrics for reporting
    analysis_list = metadata.get("analysis", [])
    analysis = analysis_list[0] if analysis_list else {}
    iters = analysis.get("iterations_completed", "?")
    fidelity = analysis.get("fidelity")
    converged = analysis.get("converged")
    fidelity_str = f"{fidelity:.4f}" if fidelity is not None else "n/a"

    # 5. Rename directory to embed experiment ID
    new_name = f"{case_dir.name}_{exp_id}"
    new_path = case_dir.parent / new_name
    case_dir.rename(new_path)

    return {
        "experiment_id": exp_id,
        "original_path": str(case_dir),
        "new_path": str(new_path),
        "iterations": iters,
        "fidelity": fidelity_str,
        "converged": converged,
        "warnings": warnings,
        "fragment_counts": fragment_counts,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Batch-harvest Frontier nelem5 FVM runs",
    )
    parser.add_argument(
        "--data-root",
        type=str,
        default="~/q8020/fromFrontier/nelem5/statevector",
        help="Root directory containing exact/ and shots_*/ dirs",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Discover cases and print what would be done, without writing anything",
    )
    args = parser.parse_args()

    root = Path(args.data_root).expanduser().resolve()
    if not root.exists():
        print(f"Error: data root does not exist: {root}", file=sys.stderr)
        sys.exit(1)

    case_dirs = discover_case_dirs(root)
    print(f"Discovered {len(case_dirs)} case directories under {root}", file=sys.stderr)

    if not case_dirs:
        print("No case directories found.", file=sys.stderr)
        sys.exit(0)

    # Print header
    if args.dry_run:
        print(f"{'#':>3}  {'case_dir':<55} {'exp_id':<10}")
        print("-" * 70)
    else:
        print(
            f"{'#':>3}  {'case_dir':<55} {'exp_id':<10} {'iters':>5} {'fidelity':>10} {'conv':>5}"
        )
        print("-" * 100)

    results = []
    for i, case_dir in enumerate(case_dirs):
        # Show relative path from root's parent for readability
        try:
            rel = case_dir.relative_to(root)
        except ValueError:
            rel = case_dir
        label = str(rel)

        try:
            result = harvest_one(case_dir, dry_run=args.dry_run)
            results.append(result)

            if args.dry_run:
                print(f"{i+1:>3}  {label:<55} {result['experiment_id']:<10}")
            else:
                print(
                    f"{i+1:>3}  {label:<55} {result['experiment_id']:<10} "
                    f"{result['iterations']:>5} {result['fidelity']:>10} "
                    f"{str(result['converged']):>5}"
                )
        except Exception as e:
            print(f"{i+1:>3}  {label:<55} ERROR: {e}", file=sys.stderr)
            results.append({"error": str(e), "original_path": str(case_dir)})

    # Summary
    ok = sum(1 for r in results if "error" not in r)
    err = sum(1 for r in results if "error" in r)
    print(f"\nDone: {ok} harvested, {err} errors", file=sys.stderr)


if __name__ == "__main__":
    main()
