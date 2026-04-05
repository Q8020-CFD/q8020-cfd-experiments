"""Generate CFL comparison summary plot.

Reads experiment data from the 2026-04-05 CFL sweep and produces
a combined box-plot of L2 error, mean infidelity line, and
wall-time on a second y-axis.
"""

from __future__ import annotations

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
        "2026-04-05", "_52d087d1",
    )
)

CFL_MAP: dict[str, float] = {
    "time_steps_0": 1,
    "time_steps_1": 5,
    "time_steps_2": 10,
    "time_steps_3": 25,
    "time_steps_4": 1e10,
}


def load_data(
    base: str,
) -> tuple[
    dict[float, list[float]],
    dict[float, list[float]],
    dict[float, list[float]],
]:
    """Load error, infidelity, and timing data."""
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
                if (
                    f.startswith("q8020_analysis_")
                    and f.endswith(".json")
                ):
                    fpath = os.path.join(trial_dir, f)
                    with open(fpath) as fh:
                        d: dict[str, Any] = json.load(fh)
                    error_data[cfl].append(
                        d["l2_error_normalized"] * 100
                    )
                    infidelity_data[cfl].append(
                        (1 - d["fidelity"]) * 100
                    )
            for f in os.listdir(trial_dir):
                if "exec_stats" in f and f.endswith(".json"):
                    fpath = os.path.join(trial_dir, f)
                    with open(fpath) as fh:
                        d = json.load(fh)
                    time_data[cfl].append(
                        d["duration_seconds"] / 60
                    )
                    break

    return error_data, infidelity_data, time_data


def make_plot(
    error_data: dict[float, list[float]],
    infidelity_data: dict[float, list[float]],
    time_data: dict[float, list[float]],
    outpath: str,
) -> None:
    """Create and save the CFL comparison plot."""
    plt.style.use("seaborn-v0_8-whitegrid")
    fig, ax1 = plt.subplots(figsize=(8, 5))

    cfls = [1, 5, 10, 25, 1e10]
    labels = ["1", "5", "10", "25", r"$10^{10}$"]
    green = "#27ae60"
    red = "#e74c3c"
    orange = "#e67e22"
    blue = "#2980b9"
    purple = "#8e44ad"

    box_fill = "#b0c4de"
    dot_color = "#2c3e50"
    rng = np.random.default_rng(42)

    bp_err = ax1.boxplot(
        [error_data[c] for c in cfls],
        positions=range(len(cfls)),
        widths=0.5,
        patch_artist=True,
        showfliers=False,
        medianprops=dict(color=dot_color, linewidth=1.5),
        whiskerprops=dict(
            color=dot_color, linewidth=1.2,
        ),
        capprops=dict(color=dot_color, linewidth=1.2),
    )
    for patch in bp_err["boxes"]:
        patch.set_facecolor(box_fill)
        patch.set_edgecolor(dot_color)
        patch.set_alpha(0.6)

    for i, cfl in enumerate(cfls):
        jitter = rng.normal(
            0, 0.06, len(error_data[cfl])
        )
        ax1.scatter(
            [i + j for j in jitter],
            error_data[cfl],
            color=dot_color,
            alpha=0.6,
            s=40,
            zorder=3,
            edgecolors="white",
            linewidth=0.4,
        )

    mean_infid = [
        np.mean(infidelity_data[c]) for c in cfls
    ]
    ax1.plot(
        range(len(cfls)),
        mean_infid,
        "o-",
        color=blue,
        linewidth=2,
        markersize=8,
        zorder=5,
    )

    ax1.set_yscale("log")
    ax1.set_ylim(0.01, 50)
    ax1.set_yticks([0.01, 0.1, 1, 10])
    ax1.set_yticklabels(["0.01", "0.1", "1", "10"])
    ax1.set_ylabel("Percentage (%)", fontsize=13)

    ax2 = ax1.twinx()
    mean_time = [np.mean(time_data[c]) for c in cfls]
    ax2.plot(
        range(len(cfls)),
        mean_time,
        "s--",
        color=purple,
        linewidth=2,
        markersize=8,
        zorder=5,
        alpha=0.8,
    )
    ax2.set_ylabel(
        "Wall Time (min)", fontsize=13, color=purple
    )
    ax2.tick_params(
        axis="y", labelcolor=purple, labelsize=11
    )
    ax2.set_ylim(10, 45)

    ax1.set_xticks(range(len(cfls)))
    ax1.set_xticklabels(labels, fontsize=12)
    ax1.set_xlabel("CFL Number", fontsize=13)
    ax1.set_title(
        "HHL Solver: Error, Infidelity,"
        " and Wall Time vs CFL",
        fontsize=13,
        pad=10,
    )
    ax1.tick_params(labelsize=11)

    legend_elements = [
        Patch(
            facecolor=box_fill,
            edgecolor=dot_color,
            alpha=0.6,
            label=r"$L_2$ relative error",
        ),
        Line2D(
            [0], [0],
            color=blue,
            marker="o",
            linewidth=2,
            markersize=8,
            label="Mean infidelity",
        ),
        Line2D(
            [0], [0],
            color=purple,
            marker="s",
            linewidth=2,
            markersize=8,
            linestyle="--",
            label="Mean wall time (per trial)",
        ),
    ]
    ax1.legend(
        handles=legend_elements,
        loc="upper left",
        fontsize=9,
    )

    fig.text(
        0.5,
        0.01,
        "FVM Euler 1D nozzle | 5 elements | BDF1 | "
        "150k shots | statevector | 10 trials per CFL",
        fontsize=9,
        color="gray",
        ha="center",
    )

    plt.tight_layout(rect=[0, 0.04, 1, 1])
    fig.savefig(
        outpath,
        dpi=200,
        bbox_inches="tight",
        facecolor="white",
    )
    print(f"Saved to {outpath}")


if __name__ == "__main__":
    error_data, infidelity_data, time_data = load_data(
        BASE
    )
    out = os.path.join(
        SCRIPT_DIR, "cfl_comparison_summary.png"
    )
    make_plot(error_data, infidelity_data, time_data, out)
