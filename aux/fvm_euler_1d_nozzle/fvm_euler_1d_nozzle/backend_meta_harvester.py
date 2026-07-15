"""Extract rich backend metadata for FVM Euler 1D solver cases.

Reads the postproc JSON to find the -backend param, instantiates
the backend object via qutil, extracts full noise-model metadata
via metautil, and writes a q8020_backend_* fragment that overwrites
the thin one produced by the FVM harvester.

Usage (as _case_postproc):
    python q8020-cfd-experiments/codes/fvm_euler_1d_nozzle/backend_meta_harvester.py <postproc_json>
"""

import json
import sys
from pathlib import Path

from q8020_cfd_metautil.meta_fragment import write_backend
from q8020_backend_utils.ibm.backend import get_backend
from q8020_backend_utils.ibm.backend_meta import make_backend_meta


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: backend_meta_harvester.py <postproc_json>", file=sys.stderr)
        sys.exit(1)

    postproc_path = Path(sys.argv[1])
    with open(postproc_path, "r", encoding="utf-8") as f:
        postproc = json.load(f)

    case_dir = Path(postproc["case_dir"])
    experiment_id = postproc.get("experiment_id")
    params = postproc.get("params", {})

    # Get the -backend param, e.g. "fake fake_melbourne"
    backend_str = params.get("-backend")
    if not backend_str:
        # No backend specified — ideal statevector, nothing to enrich
        print("No -backend param, skipping backend meta enrichment", file=sys.stderr)
        return

    # Parse "fake fake_melbourne" → backend_type="sim", name="melbourne"
    parts = backend_str.strip().split()
    if len(parts) == 2 and parts[0] == "fake":
        backend_type = "sim"
        # Strip "fake_" prefix if present: "fake_melbourne" → "melbourne"
        name = parts[1]
        if name.startswith("fake_"):
            name = name[len("fake_"):]
    else:
        # Fallback: pass through as-is
        backend_type = parts[0] if parts else "sim"
        name = parts[1] if len(parts) > 1 else None

    # Instantiate backend and extract metadata
    backend = get_backend(name=name, backend_type=backend_type)
    backend_data = make_backend_meta(backend)

    # Add shots from params if available
    shots = params.get("-shots")
    if shots is not None:
        backend_data["nshots"] = shots

    # Write fragment — overwrites the thin one from the FVM harvester
    write_backend(case_dir, backend_data, experiment_id=experiment_id)
    print(f"✅ Rich backend metadata written to: {case_dir}", file=sys.stderr)


if __name__ == "__main__":
    main()
