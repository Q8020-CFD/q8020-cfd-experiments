"""Compare total residual convergence: Nov 2025 baseline vs Qiskit upgrade vs CFL sweep.

Plots mean residual_total across 10 trials with min/max bands.
"""

from __future__ import annotations

import os
import csv

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_BASE = os.path.normpath(
    os.path.join(SCRIPT_DIR, "..", "..", "..", "results", "fvm_euler_1d_solver")
)

# --- Dataset paths ---
NOV_2025_DIR = os.path.join(RESULTS_BASE, "2025-11-11", "shots_150000")
NOV_2025_EXACT = os.path.join(RESULTS_BASE, "2025-11-11", "exact_09899a29")
APR_2026_BASE = os.path.join(RESULTS_BASE, "2026-04-05", "_52d087d1")

CFL_MAP = {
    "time_steps_0": 1,
    "time_steps_1": 5,
    "time_steps_2": 10,
    "time_steps_3": 25,
    "time_steps_4": 1e10,
}

RESIDUAL_GLOB = "residual_nelem5_HHL_statevector_nshots150000.csv"


def read_residuals(trial_dir: str) -> np.ndarray | None:
    """Read residual_total column from a trial directory. Returns (N,) array."""
    fpath = os.path.join(trial_dir, RESIDUAL_GLOB)
    if not os.path.isfile(fpath):
        # Try alternate naming
        for f in os.listdir(trial_dir):
            if "residual" in f and f.endswith(".csv"):
                fpath = os.path.join(trial_dir, f)
                break
        else:
            return None
    iters = []
    residuals = []
    with open(fpath) as fh:
        reader = csv.DictReader(fh, skipinitialspace=True)
        for row in reader:
            iters.append(float(row["iters"]))
            residuals.append(float(row["residual_total"]))
    return np.array(residuals)


def collect_trials(parent_dir: str) -> list[np.ndarray]:
    """Collect residual arrays from all trial_* subdirs."""
    trials = []
    for name in sorted(os.listdir(parent_dir)):
        if name.startswith("trial_"):
            arr = read_residuals(os.path.join(parent_dir, name))
            if arr is not None:
                trials.append(arr)
    return trials


def stats(trials: list[np.ndarray]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return (mean, min, max) across trials, padding shorter arrays with NaN."""
    max_len = max(len(t) for t in trials)
    mat = np.full((len(trials), max_len), np.nan)
    for i, t in enumerate(trials):
        mat[i, :len(t)] = t
    return np.nanmean(mat, axis=0), np.nanmin(mat, axis=0), np.nanmax(mat, axis=0)


def make_plot(outpath: str) -> None:
    plt.style.use("seaborn-v0_8-whitegrid")
    fig, ax = plt.subplots(figsize=(10, 7))

    colors = {
        "HHL Exact Statevector": "#1abc9c",
        "Nov 2025 (Qiskit 1.2, CFL=1e10)": "#2c3e50",
        "CFL=1": "#27ae60",
        "CFL=5": "#2980b9",
        "CFL=10": "#8e44ad",
        "CFL=25": "#e67e22",
        "CFL=1e10": "#e74c3c",
    }
    markers = {
        "HHL Exact Statevector": "*",
        "Nov 2025 (Qiskit 1.2, CFL=1e10)": "o",
        "CFL=1": "^",
        "CFL=5": "D",
        "CFL=10": "v",
        "CFL=25": "P",
        "CFL=1e10": "s",
    }

    datasets: dict[str, list[np.ndarray]] = {}

    # 0) Exact statevector (single run, no band)
    exact_arr = read_residuals(NOV_2025_EXACT)
    if exact_arr is not None:
        datasets["HHL Exact Statevector"] = [exact_arr]

    # 1) Nov 2025 baseline
    nov_trials = collect_trials(NOV_2025_DIR)
    if nov_trials:
        datasets["Nov 2025 (Qiskit 1.2, CFL=1e10)"] = nov_trials

    # 2) CFL sweep (Apr 2026) — CFL=1e10 serves as both qiskit upgrade and sweep point
    for group, cfl in CFL_MAP.items():
        group_dir = os.path.join(APR_2026_BASE, group)
        trials = collect_trials(group_dir)
        if not trials:
            continue
        if cfl == 1e10:
            datasets["CFL=1e10"] = trials
        else:
            datasets[f"CFL={int(cfl)}"] = trials

    plot_order = [
        "HHL Exact Statevector",
        "Nov 2025 (Qiskit 1.2, CFL=1e10)",
        "CFL=1",
        "CFL=5",
        "CFL=10",
        "CFL=25",
        "CFL=1e10",
    ]

    for label in plot_order:
        if label not in datasets:
            continue
        mean, lo, hi = stats(datasets[label])
        iters = np.arange(len(mean))
        color = colors[label]
        marker = markers[label]
        ax.semilogy(iters, mean, f"{marker}-", color=color, label=label,
                     linewidth=2, markersize=7, zorder=5)
        ax.fill_between(iters, lo, hi, color=color, alpha=0.12, zorder=2)

    ax.set_xlabel("Newton Iteration", fontsize=13)
    ax.set_ylabel("Total Residual", fontsize=13)
    ax.set_title(
        "Total Residual Convergence: Nov 2025 Baseline vs Apr 2026 CFL Sweep\n"
        "(150k shots, statevector, 10 trials — band = min/max)",
        fontsize=12,
    )
    ax.legend(fontsize=10, loc="best")
    ax.tick_params(labelsize=11)
    ax.set_xlim(left=0)

    fig.text(
        0.5, 0.01,
        "FVM Euler 1D nozzle | nelem=5 | BDF1 | HHL statevector | 150k shots",
        fontsize=9, color="gray", ha="center",
    )

    plt.tight_layout(rect=[0, 0.04, 1, 1])
    fig.savefig(outpath, dpi=200, bbox_inches="tight", facecolor="white")
    print(f"Saved to {outpath}")


if __name__ == "__main__":
    out = os.path.join(SCRIPT_DIR, "residual_convergence_comparison.png")
    make_plot(out)
