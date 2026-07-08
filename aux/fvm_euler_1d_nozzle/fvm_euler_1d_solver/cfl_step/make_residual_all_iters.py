"""Total residual convergence: 15-iter, 60-iter, and 120-iter runs on one plot.

Combines:
  - 2025-11-11  exact statevector (single run, CFL=1e10)
  - 2026-04-05  CFL sweep at 15 iters
  - 2026-04-08  CFL={1,5,10} at 60 iters
  - 2026-04-10  CFL={2,3} at 120 iters
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

NOV_2025_EXACT = os.path.join(RESULTS_BASE, "2025-11-11", "exact_09899a29")
APR05_BASE = os.path.join(RESULTS_BASE, "2026-04-05", "_52d087d1")
APR08_BASE = os.path.join(RESULTS_BASE, "2026-04-08", "_85fd6d17")
APR10_BASE = os.path.join(RESULTS_BASE, "2026-04-10", "_f1112a1f")

RESIDUAL_GLOB = "residual_nelem5_HHL_statevector_nshots150000.csv"

# Map group subdirectory name -> CFL value
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


def read_residuals(trial_dir: str) -> np.ndarray | None:
    fpath = os.path.join(trial_dir, RESIDUAL_GLOB)
    if not os.path.isfile(fpath):
        for f in os.listdir(trial_dir):
            if "residual" in f and f.endswith(".csv"):
                fpath = os.path.join(trial_dir, f)
                break
        else:
            return None
    residuals = []
    with open(fpath) as fh:
        reader = csv.DictReader(fh, skipinitialspace=True)
        for row in reader:
            residuals.append(float(row["residual_total"]))
    return np.array(residuals)


def collect_trials(parent_dir: str) -> list[np.ndarray]:
    trials = []
    if not os.path.isdir(parent_dir):
        return trials
    for name in sorted(os.listdir(parent_dir)):
        if name.startswith("trial_"):
            arr = read_residuals(os.path.join(parent_dir, name))
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


# ---------- dataset definition ----------
# (label, color, marker, linestyle)
SERIES_STYLE: dict[str, tuple[str, str, str]] = {
    "Exact SV":          ("#1abc9c", "*", "-"),
    "CFL=1 (15i)":       ("#27ae60", "^", "--"),
    "CFL=5 (15i)":       ("#2980b9", "D", "--"),
    "CFL=10 (15i)":      ("#8e44ad", "v", "--"),
    "CFL=25 (15i)":      ("#e67e22", "P", "--"),
    "CFL=1e10 (15i)":    ("#e74c3c", "s", "--"),
    "CFL=1 (60i)":       ("#27ae60", "^", "-"),
    "CFL=5 (60i)":       ("#2980b9", "D", "-"),
    "CFL=10 (60i)":      ("#8e44ad", "v", "-"),
    "CFL=2 (120i)":      ("#f39c12", "o", "-"),
    "CFL=3 (120i)":      ("#d35400", "h", "-"),
}

PLOT_ORDER = list(SERIES_STYLE.keys())


def make_plot(outpath: str) -> None:
    plt.style.use("seaborn-v0_8-whitegrid")
    fig, ax = plt.subplots(figsize=(12, 7))

    datasets: dict[str, list[np.ndarray]] = {}

    # exact statevector
    exact_arr = read_residuals(NOV_2025_EXACT)
    if exact_arr is not None:
        datasets["Exact SV"] = [exact_arr]

    # 15-iter CFL sweep (Apr 05)
    for group, cfl in APR05_CFL.items():
        trials = collect_trials(os.path.join(APR05_BASE, group))
        if trials:
            cfl_s = "1e10" if cfl == 1e10 else str(int(cfl))
            datasets[f"CFL={cfl_s} (15i)"] = trials

    # 60-iter runs (Apr 08)
    for group, cfl in APR08_CFL.items():
        trials = collect_trials(os.path.join(APR08_BASE, group))
        if trials:
            datasets[f"CFL={int(cfl)} (60i)"] = trials

    # 120-iter runs (Apr 10)
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
            linewidth=2, markersize=6, markevery=max(1, len(mean) // 15),
            zorder=5,
        )
        ax.fill_between(iters, lo, hi, color=color, alpha=0.10, zorder=2)

    ax.set_xlabel("Newton Iteration", fontsize=13)
    ax.set_ylabel("Total Residual", fontsize=13)
    ax.set_title(
        "Total Residual Convergence: 15 / 60 / 120 Iterations\n"
        "(nelem=5, 150k shots, statevector, 10 trials — band = min/max)",
        fontsize=12,
    )
    ax.legend(fontsize=9, ncol=2, loc="upper right")
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
    out = os.path.join(SCRIPT_DIR, "residual_convergence_all_iters.png")
    make_plot(out)
