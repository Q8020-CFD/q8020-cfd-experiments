#!/usr/bin/env python3
"""Figure for the FIRST-SEGMENT (frame 1) relL2 UQ of ch_smooth_movie_rerun.

Left  : every trial as a dot, per device, with the mean and its 95% t-CI, and
        Melvina's June n=1 value (paper col S) marked for comparison.
Right : the frame-1 error budget -- algorithmic/truncation floor, + shot
        sampling, + device noise -- as an ordered stack.

Imports the loaders from uq_smooth_movie_segment1.py so the numbers in the
figure and in the text report can never disagree.  Writes the PNG next to the
other rerun analysis figures.  Run with the tooling venv python.
"""
from __future__ import annotations

import math
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import uq_smooth_movie_segment1 as uq

# --- validated palette (dataviz reference instance, light mode) -------------
SURFACE = "#fcfcfb"
TEXT_1, TEXT_2, TEXT_3 = "#0b0b0b", "#52514e", "#84837c"
SERIES = {"kingston": "#2a78d6", "fez": "#eb6834", "miami": "#1baf7a"}
STACK = ["#86b6ef", "#2a78d6", "#104281"]        # ordinal blue: floor/shot/dev
GRID = "#e4e3df"

DEVS = ("kingston", "fez", "miami")
OUT = os.path.abspath(os.path.join(
    uq.REPO, "q8020-cfd-experiments", "results", "burgers-ch-lbm",
    "ch_smooth_movie_rerun", "analysis", "uq_segment1_relL2.png"))


def main():
    truth1 = uq.ftcs800_truth_frames()[uq.FRAME]
    new = uq.load_new(truth1)
    june = uq.load_june(truth1)
    sim = uq.load_sim(truth1)

    fig, (axA, axB) = plt.subplots(
        1, 2, figsize=(13.2, 5.2), gridspec_kw={"width_ratios": [1.8, 1.0]})
    fig.patch.set_facecolor(SURFACE)
    for ax in (axA, axB):
        ax.set_facecolor(SURFACE)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        for side in ("left", "bottom"):
            ax.spines[side].set_color(GRID)
        ax.tick_params(colors=TEXT_2, labelsize=9, length=3, color=GRID)

    # ================= A: per-trial dots + mean/CI + June ==================
    rng = np.random.default_rng(7)
    ypos = {d: len(DEVS) - 1 - i for i, d in enumerate(DEVS)}
    for dev in DEVS:
        s, y, col = new[dev], ypos[dev], SERIES[dev]
        if s.n == 0:
            continue
        l2 = s.arr("l2")
        d = uq.describe(l2)
        jit = rng.uniform(-0.11, 0.11, size=l2.size)
        # 2px surface ring keeps overlapping dots separable
        axA.scatter(l2, np.full_like(l2, y) + jit, s=52, color=col,
                    edgecolors=SURFACE, linewidths=1.6, zorder=4,
                    label="individual trial" if dev == DEVS[0] else None)
        if s.n > 1:
            axA.plot([d["ci_lo"], d["ci_hi"]], [y - 0.30] * 2, color=col,
                     lw=2.4, solid_capstyle="butt", zorder=3,
                     label="95% CI on mean" if dev == DEVS[0] else None)
            axA.plot([d["mean"]] * 2, [y - 0.38, y - 0.22], color=TEXT_1,
                     lw=2.0, zorder=5,
                     label="mean" if dev == DEVS[0] else None)
        j = june.get(dev, {})
        if j:
            axA.scatter([j["l2"]], [y], s=110, marker="D",
                        facecolors=SURFACE, edgecolors=TEXT_1, linewidths=1.8,
                        zorder=6,
                        label="June 2026, n=1 (paper col S)"
                        if dev == DEVS[0] else None)
            axA.annotate(f"{j['l2']:.3f}", (j["l2"], y), textcoords="offset points",
                         xytext=(0, 15), ha="center", fontsize=8.5,
                         color=TEXT_2)
        # direct label in clear space at the right (relief rule: aqua is
        # under 3:1 on this surface, so identity is never color-alone)
        axA.text(0.845, y + 0.02,
                 f"{d['mean']:.3f} $\\pm$ {d['sd']:.3f}", color=TEXT_1,
                 fontsize=9.5, va="center")
        axA.text(0.845, y - 0.20, f"1 sd, n={s.n}", color=TEXT_3,
                 fontsize=8.5, va="center")

    axA.set_yticks(list(ypos.values()))
    axA.set_yticklabels(list(ypos.keys()), fontsize=11, fontweight="bold")
    for lbl, dev in zip(axA.get_yticklabels(), ypos.keys()):
        lbl.set_color(SERIES[dev])
    axA.tick_params(axis="y", length=0)
    axA.spines["left"].set_visible(False)
    axA.set_ylim(-0.62, len(DEVS) - 0.42)
    axA.set_xlim(0.552, 0.925)
    axA.set_xticks(np.arange(0.60, 0.81 + 1e-9, 0.05))
    axA.xaxis.grid(True, color=GRID, lw=0.8)
    axA.set_axisbelow(True)
    axA.set_xlabel("relative $L_2$ vs FTCS-800 at frame 1  ($T=0.0375$)",
                   color=TEXT_2, fontsize=10)
    axA.set_title("First segment: every trial, and where June's single run sat",
                  color=TEXT_1, fontsize=11.5, loc="left", pad=10)
    leg = axA.legend(loc="upper left", bbox_to_anchor=(0.0, -0.155), ncol=4,
                     frameon=False, fontsize=8.5, handletextpad=0.5,
                     columnspacing=1.4, borderpad=0.0)
    for t in leg.get_texts():
        t.set_color(TEXT_2)

    # ================= B: frame-1 error budget stack =======================
    floor = sim["sv"]["l2"]
    shot = sim["sampled"]["l2"] - floor
    labels, parts = [], []
    for dev in DEVS:
        s = new[dev]
        if s.n == 0:
            continue
        labels.append(dev)
        parts.append(s.arr("l2").mean() - floor - shot)
    y = np.arange(len(labels))[::-1].astype(float)
    names = ["algorithm / MPS truncation floor (statevector)",
             f"+ shot sampling ({uq.SHOTS:,} shots)",
             "+ device noise (hardware)"]
    for k, (w, col) in enumerate(zip(
            (np.full(len(labels), floor), np.full(len(labels), shot),
             np.array(parts)), STACK)):
        left = (np.zeros(len(labels)) if k == 0
                else np.full(len(labels), floor) if k == 1
                else np.full(len(labels), floor + shot))
        # 2px surface gap between stacked segments
        axB.barh(y, w, left=left, height=0.42, color=col,
                 edgecolor=SURFACE, linewidth=2.0, label=names[k], zorder=3)
    for i, dev in enumerate(labels):
        tot = floor + shot + parts[i]
        axB.text(tot + 0.014, y[i], f"{tot:.3f}", va="center", fontsize=9,
                 color=TEXT_1)
    axB.set_yticks(list(y))
    axB.set_yticklabels(labels, fontsize=11, fontweight="bold")
    for lbl, dev in zip(axB.get_yticklabels(), labels):
        lbl.set_color(SERIES[dev])
    axB.tick_params(axis="y", length=0)
    axB.spines["left"].set_visible(False)
    axB.set_ylim(-0.62, len(labels) - 0.42)
    axB.set_xlim(0, 0.90)
    axB.xaxis.grid(True, color=GRID, lw=0.8)
    axB.set_axisbelow(True)
    axB.set_xlabel("relative $L_2$ at frame 1", color=TEXT_2, fontsize=10)
    axB.set_title("What the frame-1 error is made of", color=TEXT_1,
                  fontsize=11.5, loc="left", pad=10)
    leg = axB.legend(loc="upper left", bbox_to_anchor=(0.0, -0.155), ncol=1,
                     frameon=False, fontsize=8.2, handletextpad=0.6,
                     borderpad=0.0, labelspacing=0.35)
    for t in leg.get_texts():
        t.set_color(TEXT_2)

    sw, sb, f, p, _ = uq.variance_components([new[d] for d in uq.DEVICES])
    fig.text(0.008, 0.015,
             f"ch_smooth_movie_rerun 2026-09-10 (_0ca9db0f), q=3 "
             f"nu=0.08 A=0.3 cfl=0.3 shots=150000, TREX+DD, opt-3.   "
             f"run-to-run $\\sigma$ = {sw:.4f}, device-to-device "
             f"$\\sigma$ = {sb:.4f} (ratio {sb / sw:.1f}).   "
             f"boston: 0 trials (IBM usage limit).",
             color=TEXT_3, fontsize=7.8)
    fig.subplots_adjust(left=0.072, right=0.99, top=0.91, bottom=0.30,
                        wspace=0.13)
    fig.savefig(OUT, dpi=170, facecolor=SURFACE)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
