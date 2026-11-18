"""Capture the fvm nozzle step-0 linear system A, b for one nelem.

Runs nozzle_1d_solver.py through its own CLI (argument parsing, case setup,
init_sol, residual, finite-difference Jacobian) and intercepts the first
linear_sys_solve: A and b are pickled as fvm's hhl_solve pickles them, then
the run stops. No time step, linear solve or circuit is made.
Usage: gen_step0.py NELEM OUTDIR
"""

import pickle
import runpy
import sys
from pathlib import Path

FVM = Path("/Users/agallojr/proj/src/q8020/fvm_euler_1d_solver")
sys.path.insert(0, str(FVM))
import time_solvers as ts  # noqa: E402


class Captured(Exception):
    pass


def main() -> None:
    nelem, outdir = int(sys.argv[1]), Path(sys.argv[2]).expanduser()
    outdir.mkdir(parents=True, exist_ok=True)

    def capture(self, A, b, x0=None, tol=1e-2, step=0):
        with open(outdir / f"system_Ab_nelem{nelem}_iter0.pkl", "wb") as fh:
            pickle.dump({"A": A, "b": b}, fh)
        raise Captured

    ts.LinearSystemSolver.linear_sys_solve = capture
    sys.argv = ["nozzle_1d_solver.py", "-nelem", str(nelem), "-linsolver",
                "LU", "-time_scheme", "BDF1", "-cfl", "1e10", "-localdt",
                "-iters", "1", "-initers", "1", "-noshow", "-outdir",
                str(outdir)]
    try:
        runpy.run_path(str(FVM / "nozzle_1d_solver.py"), run_name="__main__")
    except Captured:
        print(f"nelem {nelem}: captured step-0 system in {outdir}")
        return
    sys.exit(f"nelem {nelem}: no linear solve reached")


if __name__ == "__main__":
    main()
