"""Condition number (kappa) vs Newton iteration for all CFL/iter datasets.

Combines:
  - 2026-04-05  CFL sweep at 15 iters
  - 2026-04-08  CFL={1,5,10} at 60 iters
  - 2026-04-10  CFL={2,3} at 120 iters

Each trial has a qc_metadata CSV with per-step condition_number.
We plot mean kappa across 10 trials with min/max bands.
"""

from __future__ import annotations

import csv
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_BASE = os.path.normpath(
    os.path.join(SCRIPT_DIR, "..", "..", "..", "results", "fvm_euler_1d_solver")
)

APR05_BASE = os.path.join(RESULTS_BASE, "2026-04-05", "_52d087d1")
APR08_BASE = os.path.join(RESULTS_BASE, "2026-04-08", "_85fd6d17")
APR10_BASE = os.path.join(RESULTS_BASE, "2026-04-10", "_f1112a1f")

QC_META_GLOB = "qc_metadata_nelem5_statevector_shots150000.csv"

APR05_CFL = {
    "time_steps_0": 1,
    "time_steps_1": 5,
    "time_steps_2": 10,
    "time_steps_3": 25,
    "time_steps_4": 1e10,
}
APR08_CFL = {
    "more_iters_0": 1,
    "more_iters_1": 5,
    "more_iters_2": 10,
}
APR10_CFL = {
    "more_iters_0": 2,
    "more_iters_1": 3,
}


def read_kappa(trial_dir: str) -> np.ndarray | None:
    """Read condition_number column from qc_metadata CSV, indexed by step."""
    fpath = os.path.join(trial_dir, QC_META_GLOB)
    if not os.path.isfile(fpath):
        return None
    kappas: list[tuple[int, float]] = []
    with open(fpath) as fh:
        reader = csv.DictReader(fh, skipinitialspace=True)
        for row in reader:
            step = int(float(row["step"]))
            kappa = float(row["condition_number"])
            kappas.append((step, kappa))
    if not kappas:
        return None
    kappas.sort()
    max_step = kappas[-1][0]
    arr = np.full(max_step + 1, np.nan)
    for s, k in kappas:
        arr[s] = k
    return arr


def collect_trials(parent_dir: str) -> list[np.ndarray]:
    trials = []
    if not os.path.isdir(parent_dir):
        return trials
    for name in sorted(os.listdir(parent_dir)):
        if name.startswith("trial_"):
            arr = read_kappa(os.path.join(parent_dir, name))
            if arr is not None:
                trials.append(arr)
    return trials


def stats(
    trials: list[np.ndarray],
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    max_len = max(len(t) for t in trials)
    mat = np.full((len(trials), max_len), np.nan)
    for i, t in enumerate(trials):
        mat[i, : len(t)] = t
    return np.nanmean(mat, axis=0), np.nanmin(mat, axis=0), np.nanmax(mat, axis=0)


SERIES_STYLE: dict[str, tuple[str, str, str]] = {
    "CFL=1 (15i)":    ("#27ae60", "^", "--"),
    "CFL=5 (15i)":    ("#2980b9", "D", "--"),
    "CFL=10 (15i)":   ("#8e44ad", "v", "--"),
    "CFL=25 (15i)":   ("#e67e22", "P", "--"),
    "CFL=1e10 (15i)": ("#e74c3c", "s", "--"),
    "CFL=1 (60i)":    ("#27ae60", "^", "-"),
    "CFL=5 (60i)":    ("#2980b9", "D", "-"),
    "CFL=10 (60i)":   ("#8e44ad", "v", "-"),
    "CFL=2 (120i)":   ("#f39c12", "o", "-"),
    "CFL=3 (120i)":   ("#d35400", "h", "-"),
}

PLOT_ORDER = list(SERIES_STYLE.keys())


def make_plot(outpath: str) -> None:
    plt.style.use("seaborn-v0_8-whitegrid")
    fig, ax = plt.subplots(figsize=(12, 7))

    datasets: dict[str, list[np.ndarray]] = {}

    for group, cfl in APR05_CFL.items():
        trials = collect_trials(os.path.join(APR05_BASE, group))
        if trials:
            cfl_s = "1e10" if cfl == 1e10 else str(int(cfl))
            datasets[f"CFL={cfl_s} (15i)"] = trials

    for group, cfl in APR08_CFL.items():
        trials = collect_trials(os.path.join(APR08_BASE, group))
        if trials:
            datasets[f"CFL={int(cfl)} (60i)"] = trials

    for group, cfl in APR10_CFL.items():
        trials = collect_trials(os.path.join(APR10_BASE, group))
        if trials:
            datasets[f"CFL={int(cfl)} (120i)"] = trials

    for label in PLOT_ORDER:
        if label not in datasets:
            continue
        mean, lo, hi = stats(datasets[label])
        iters = np.arange(len(mean))
        color, marker, ls = SERIES_STYLE[label]
        ax.semilogy(
            iters, mean, marker=marker, linestyle=ls,
            color=color, label=label,
            linewidth=2, markersize=6,
            markevery=max(1, len(mean) // 15),
            zorder=5,
        )
        ax.fill_between(iters, lo, hi, color=color, alpha=0.10, zorder=2)

    ax.set_xlabel("Newton Iteration", fontsize=13)
    ax.set_ylabel("Condition Number (κ)", fontsize=13)
    ax.set_title(
        "Condition Number vs Newton Iteration: 15 / 60 / 120 Iterations\n"
        "(nelem=5, 150k shots, statevector, 10 trials — band = min/max)",
        fontsize=12,
    )
    ax.legend(fontsize=9, ncol=2, loc="best")
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
    out = os.path.join(SCRIPT_DIR, "kappa_vs_iteration.png")
    make_plot(out)
