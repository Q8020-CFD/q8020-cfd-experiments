"""
Compare FVM Euler 1D solver results: Qiskit 1.2 (Nov 2025) vs
Qiskit 2.3 (Apr 2026).

Produces a 2x2 panel figure:
  Row 1: fidelity, residual vs Newton iteration
  Row 2: final density profile, final Mach profile

Both runs: nelem=5, CFL=1e10, 150k shots, 15 iters, 10 trials.

Usage:
    python compare_qiskit_versions.py
"""

import csv
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np

RESULTS = Path(__file__).resolve().parent.parent.parent / "results"

NOV_BASE = (
    RESULTS / "fvm_euler_1d_solver" / "2025-11-11" / "shots_150000"
)
APR_BASE = (
    RESULTS
    / "fvm_euler_1d_solver"
    / "2026-04-05"
    / "_52d087d1"
    / "time_steps_4"
)

OUT_DIR = Path(__file__).resolve().parent
OUT_FILE = OUT_DIR / "qiskit_version_comparison.png"

METRICS_CSV = "hhl_metrics_nelem5_statevector_shots150000.csv"
FINAL_CSV = "final_results_nelem5_HHL_statevector_nshots150000.csv"

N_ITERS = 15


def _read_metrics(trial_dir: Path) -> dict[str, list[float]]:
    path = trial_dir / METRICS_CSV
    rows: list[dict[str, Any]] = []
    with open(path, newline="") as f:
        reader = csv.DictReader(f, skipinitialspace=True)
        for row in reader:
            rows.append({
                "step": int(row["step"].strip()),
                "fidelity": float(row["fidelity"].strip()),
                "l2_abs": float(row["l2_error_abs"].strip()),
                "l2_norm": float(
                    row["l2_error_normalized"].strip()
                ),
                "residual": float(
                    row["linsys_residual"].strip()
                ),
            })
    return {
        "steps": [r["step"] for r in rows],
        "fidelity": [r["fidelity"] for r in rows],
        "l2_abs": [r["l2_abs"] for r in rows],
        "l2_norm": [r["l2_norm"] for r in rows],
        "residual": [r["residual"] for r in rows],
    }


def _read_final(trial_dir: Path) -> dict[str, list[float]]:
    path = trial_dir / FINAL_CSV
    xp: list[float] = []
    rho: list[float] = []
    mach: list[float] = []
    with open(path, newline="") as f:
        reader = csv.DictReader(f, skipinitialspace=True)
        for row in reader:
            xp.append(float(row["xp"].strip()))
            rho.append(float(row["rho"].strip()))
            mach.append(float(row["Mach"].strip()))
    return {"xp": xp, "rho": rho, "Mach": mach}


def _find_trials(base: Path) -> list[Path]:
    return sorted(
        d
        for d in base.iterdir()
        if d.is_dir() and (d / METRICS_CSV).exists()
    )


def _load_all(
    base: Path,
) -> tuple[list[dict[str, list[float]]], list[dict[str, list[float]]]]:
    trials = _find_trials(base)
    metrics = [_read_metrics(t) for t in trials]
    finals = [_read_final(t) for t in trials]
    return metrics, finals


def _stack(
    trials: list[dict[str, list[float]]], key: str,
) -> np.ndarray:
    return np.array([t[key][:N_ITERS] for t in trials])


def _band(
    ax: plt.Axes,
    x: np.ndarray,
    data: np.ndarray,
    color: str,
    label: str,
) -> None:
    med = np.median(data, axis=0)
    lo = np.percentile(data, 10, axis=0)
    hi = np.percentile(data, 90, axis=0)
    ax.plot(x, med, color=color, lw=2, label=label)
    ax.fill_between(x, lo, hi, color=color, alpha=0.15)


def main() -> None:
    nov_m, nov_f = _load_all(NOV_BASE)
    apr_m, apr_f = _load_all(APR_BASE)
    print(
        f"Loaded {len(nov_m)} Nov trials, {len(apr_m)} Apr trials"
    )

    iters = np.arange(N_ITERS)

    nov_fid = _stack(nov_m, "fidelity")
    apr_fid = _stack(apr_m, "fidelity")
    nov_res = _stack(nov_m, "residual")
    apr_res = _stack(apr_m, "residual")
    c_nov = "#1f77b4"
    c_apr = "#d62728"

    fig, axes = plt.subplots(
        2, 2, figsize=(11, 9),
        gridspec_kw={"hspace": 0.38, "wspace": 0.30},
    )
    fig.suptitle(
        "FVM Euler 1D \u2014 Qiskit 1.2 (Nov 2025) vs"
        " Qiskit 2.3 (Apr 2026)\n"
        "nelem=5, CFL=1e10, 150k shots, 15 iters,"
        " 10 trials each",
        fontsize=13, fontweight="bold", y=0.98,
    )

    # (0,0) Fidelity
    ax = axes[0, 0]
    _band(ax, iters, nov_fid, c_nov, "Qiskit 1.2")
    _band(ax, iters, apr_fid, c_apr, "Qiskit 2.3")
    ax.set_xlabel("Newton iteration")
    ax.set_ylabel("HHL fidelity")
    ax.set_title("HHL Fidelity")
    ax.legend(fontsize=9)
    ax.set_ylim(0.90, 1.005)
    ax.grid(True, alpha=0.3)

    # (0,1) Residual
    ax = axes[0, 1]
    _band(ax, iters, nov_res, c_nov, "Qiskit 1.2")
    _band(ax, iters, apr_res, c_apr, "Qiskit 2.3")
    ax.set_yscale("log")
    ax.set_xlabel("Newton iteration")
    ax.set_ylabel("Linear system residual")
    ax.set_title("Residual Convergence")
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3, which="both")

    # (1,0) Density profiles
    ax = axes[1, 0]
    for f in nov_f:
        ax.plot(f["xp"], f["rho"], c_nov, alpha=0.3, lw=1)
    for f in apr_f:
        ax.plot(f["xp"], f["rho"], c_apr, alpha=0.3, lw=1)
    ax.plot([], [], color=c_nov, lw=2, label="Qiskit 1.2")
    ax.plot([], [], color=c_apr, lw=2, label="Qiskit 2.3")
    ax.set_xlabel("x")
    ax.set_ylabel("Density (\u03c1)")
    ax.set_title("Final Density Profile")
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

    # (1,1) Mach
    ax = axes[1, 1]
    for f in nov_f:
        ax.plot(f["xp"], f["Mach"], c_nov, alpha=0.3, lw=1)
    for f in apr_f:
        ax.plot(f["xp"], f["Mach"], c_apr, alpha=0.3, lw=1)
    ax.plot([], [], color=c_nov, lw=2, label="Qiskit 1.2")
    ax.plot([], [], color=c_apr, lw=2, label="Qiskit 2.3")
    ax.set_xlabel("x")
    ax.set_ylabel("Mach number")
    ax.set_title("Final Mach Profile")
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

    plt.savefig(OUT_FILE, dpi=150, bbox_inches="tight")
    print(f"Saved: {OUT_FILE}")
    plt.close()


if __name__ == "__main__":
    main()
