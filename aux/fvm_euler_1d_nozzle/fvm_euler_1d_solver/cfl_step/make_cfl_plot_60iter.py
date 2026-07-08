"""Generate CFL comparison plots for the 2026-04-08 60-iteration sweep.

CFL = {1, 5, 10}, 150k shots, up to 60 Newton iterations, 10 trials each.
Produces two figures:
  1. Residual convergence (mean ± min/max band) per CFL
  2. Box-plot of final L2 error + infidelity + wall time per CFL
"""

from __future__ import annotations

import csv
import json
import os
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
import numpy as np

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.normpath(
    os.path.join(
        SCRIPT_DIR, "..", "..", "..",
        "results", "fvm_euler_1d_solver",
        "2026-04-08", "_85fd6d17",
    )
)

CFL_MAP: dict[str, float] = {
    "more_iters_0": 1,
    "more_iters_1": 5,
    "more_iters_2": 10,
}

RESIDUAL_FILE = "residual_nelem5_HHL_statevector_nshots150000.csv"


# ---------- Residual convergence -------------------------------------------

def read_residuals(trial_dir: str) -> np.ndarray | None:
    fpath = os.path.join(trial_dir, RESIDUAL_FILE)
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
    for name in sorted(os.listdir(parent_dir)):
        if name.startswith("trial_"):
            arr = read_residuals(os.path.join(parent_dir, name))
            if arr is not None:
                trials.append(arr)
    return trials


def stats(trials: list[np.ndarray]):
    max_len = max(len(t) for t in trials)
    mat = np.full((len(trials), max_len), np.nan)
    for i, t in enumerate(trials):
        mat[i, : len(t)] = t
    return np.nanmean(mat, axis=0), np.nanmin(mat, axis=0), np.nanmax(mat, axis=0)


def make_residual_plot(outpath: str) -> None:
    plt.style.use("seaborn-v0_8-whitegrid")
    fig, ax = plt.subplots(figsize=(10, 6))

    colors = {"CFL=1": "#27ae60", "CFL=5": "#2980b9", "CFL=10": "#8e44ad"}
    markers = {"CFL=1": "^", "CFL=5": "D", "CFL=10": "v"}

    for group, cfl in CFL_MAP.items():
        label = f"CFL={int(cfl)}"
        trials = collect_trials(os.path.join(BASE, group))
        if not trials:
            continue
        mean, lo, hi = stats(trials)
        iters = np.arange(len(mean))
        ax.semilogy(
            iters, mean, f"{markers[label]}-",
            color=colors[label], label=label,
            linewidth=2, markersize=6, markevery=5, zorder=5,
        )
        ax.fill_between(iters, lo, hi, color=colors[label], alpha=0.12, zorder=2)

    ax.set_xlabel("Newton Iteration", fontsize=13)
    ax.set_ylabel("Total Residual", fontsize=13)
    ax.set_title(
        "Residual Convergence: CFL Sweep (60 iters max)\n"
        "(150k shots, statevector, 10 trials — band = min/max)",
        fontsize=12,
    )
    ax.legend(fontsize=11, loc="best")
    ax.tick_params(labelsize=11)
    ax.set_xlim(left=0)

    fig.text(
        0.5, 0.01,
        "FVM Euler 1D nozzle | nelem=5 | BDF1 | HHL statevector | 150k shots | Apr 2026",
        fontsize=9, color="gray", ha="center",
    )
    plt.tight_layout(rect=[0, 0.04, 1, 1])
    fig.savefig(outpath, dpi=200, bbox_inches="tight", facecolor="white")
    print(f"Saved to {outpath}")


# ---------- Summary box-plot -----------------------------------------------

def load_summary_data(
    base: str,
) -> tuple[dict[float, list[float]], dict[float, list[float]], dict[float, list[float]]]:
    error_data: dict[float, list[float]] = {}
    infidelity_data: dict[float, list[float]] = {}
    time_data: dict[float, list[float]] = {}

    for group, cfl in CFL_MAP.items():
        error_data[cfl] = []
        infidelity_data[cfl] = []
        time_data[cfl] = []
        group_dir = os.path.join(base, group)
        for trial in sorted(os.listdir(group_dir)):
            trial_dir = os.path.join(group_dir, trial)
            if not os.path.isdir(trial_dir):
                continue
            for f in os.listdir(trial_dir):
                if f.startswith("q8020_analysis_") and f.endswith(".json"):
                    with open(os.path.join(trial_dir, f)) as fh:
                        d: dict[str, Any] = json.load(fh)
                    if "l2_error_normalized" in d:
                        error_data[cfl].append(d["l2_error_normalized"] * 100)
                    if "fidelity" in d:
                        infidelity_data[cfl].append((1 - d["fidelity"]) * 100)
            for f in os.listdir(trial_dir):
                if "exec_stats" in f and f.endswith(".json"):
                    with open(os.path.join(trial_dir, f)) as fh:
                        d = json.load(fh)
                    if "duration_seconds" in d:
                        time_data[cfl].append(d["duration_seconds"] / 60)
                    break

    return error_data, infidelity_data, time_data


def make_summary_plot(
    error_data: dict[float, list[float]],
    infidelity_data: dict[float, list[float]],
    time_data: dict[float, list[float]],
    outpath: str,
) -> None:
    plt.style.use("seaborn-v0_8-whitegrid")
    fig, ax1 = plt.subplots(figsize=(7, 5))

    cfls = [1, 5, 10]
    labels = ["1", "5", "10"]
    blue = "#2980b9"
    purple = "#8e44ad"
    box_fill = "#b0c4de"
    dot_color = "#2c3e50"
    rng = np.random.default_rng(42)

    bp_err = ax1.boxplot(
        [error_data.get(c, []) for c in cfls],
        positions=range(len(cfls)),
        widths=0.5,
        patch_artist=True,
        showfliers=False,
        medianprops=dict(color=dot_color, linewidth=1.5),
        whiskerprops=dict(color=dot_color, linewidth=1.2),
        capprops=dict(color=dot_color, linewidth=1.2),
    )
    for patch in bp_err["boxes"]:
        patch.set_facecolor(box_fill)
        patch.set_edgecolor(dot_color)
        patch.set_alpha(0.6)

    for i, cfl in enumerate(cfls):
        vals = error_data.get(cfl, [])
        if vals:
            jitter = rng.normal(0, 0.06, len(vals))
            ax1.scatter(
                [i + j for j in jitter], vals,
                color=dot_color, alpha=0.6, s=40,
                zorder=3, edgecolors="white", linewidth=0.4,
            )

    mean_infid = [np.mean(infidelity_data.get(c, [0])) for c in cfls]
    ax1.plot(
        range(len(cfls)), mean_infid, "o-",
        color=blue, linewidth=2, markersize=8, zorder=5,
    )

    ax1.set_yscale("log")
    ax1.set_ylabel("Percentage (%)", fontsize=13)

    ax2 = ax1.twinx()
    mean_time = [np.mean(time_data.get(c, [0])) for c in cfls]
    ax2.plot(
        range(len(cfls)), mean_time, "s--",
        color=purple, linewidth=2, markersize=8, zorder=5, alpha=0.8,
    )
    ax2.set_ylabel("Wall Time (min)", fontsize=13, color=purple)
    ax2.tick_params(axis="y", labelcolor=purple, labelsize=11)

    ax1.set_xticks(range(len(cfls)))
    ax1.set_xticklabels(labels, fontsize=12)
    ax1.set_xlabel("CFL Number", fontsize=13)
    ax1.set_title(
        "HHL Solver: Error, Infidelity, and Wall Time vs CFL\n"
        "(60 iterations max)",
        fontsize=12, pad=10,
    )
    ax1.tick_params(labelsize=11)

    legend_elements = [
        Patch(facecolor=box_fill, edgecolor=dot_color, alpha=0.6,
              label=r"$L_2$ relative error"),
        Line2D([0], [0], color=blue, marker="o", linewidth=2,
               markersize=8, label="Mean infidelity"),
        Line2D([0], [0], color=purple, marker="s", linewidth=2,
               markersize=8, linestyle="--", label="Mean wall time"),
    ]
    ax1.legend(handles=legend_elements, loc="upper left", fontsize=9)

    fig.text(
        0.5, 0.01,
        "FVM Euler 1D nozzle | 5 elements | BDF1 | 150k shots | "
        "statevector | 10 trials | 60 iters max | Apr 2026",
        fontsize=9, color="gray", ha="center",
    )
    plt.tight_layout(rect=[0, 0.04, 1, 1])
    fig.savefig(outpath, dpi=200, bbox_inches="tight", facecolor="white")
    print(f"Saved to {outpath}")


# ---------- Main -----------------------------------------------------------

if __name__ == "__main__":
    residual_out = os.path.join(SCRIPT_DIR, "residual_convergence_60iter.png")
    make_residual_plot(residual_out)

    error_data, infidelity_data, time_data = load_summary_data(BASE)
    summary_out = os.path.join(SCRIPT_DIR, "cfl_comparison_60iter.png")
    make_summary_plot(error_data, infidelity_data, time_data, summary_out)
