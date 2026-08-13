#!/usr/bin/env python3
"""Per-timestep relL2 error vs the FTCS baseline for every quantum run.

Uses the `solution_steps` frame history in each case's q8020_artifacts_0.json.
Frames are compared at the steps both the run and the FTCS baseline saved
(all cadences are multiples of 4, so every quantum frame has a truth frame).
"""
import json
import math
from pathlib import Path

import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
BASE = HERE.parent

FTCS_Q8 = BASE / "ch_ftcs_refs/2026-08-13/_3fa21a71/9bbe98a3"
SV_CASE = BASE / "ch_q8_c0/2026-08-06/_a66942a3/1f33d059"
C1 = BASE / "ch_q8_c1/2026-08-11/_b5c8743c"
C2 = BASE / "ch_q8_c2_k8/2026-08-12/_6fade974"

C1_CASES = [("2a3cbfeb", 2), ("b15a9654", 4), ("39a1f5ab", 8), ("fe96b52e", 16)]
C2_CASES = [("c1e5d7e4", 16384), ("00e609d3", 65536), ("1cc667ab", 131072),
            ("3dcb7c60", 524288), ("70416813", 1048576)]

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"
RAMP4 = ["#86b6ef", "#3987e5", "#1c5cab", "#0d366b"]
RAMP5 = ["#86b6ef", "#5598e7", "#2a78d6", "#1c5cab", "#0d366b"]

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE, "font.family": "sans-serif",
    "axes.edgecolor": AXIS, "axes.linewidth": 0.8,
    "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.labelcolor": INK2, "text.color": INK,
    "grid.color": GRID, "grid.linewidth": 0.6,
    "legend.frameon": False,
})


def frames(case_dir):
    j = json.load(open(Path(case_dir) / "q8020_artifacts_0.json"))
    return {int(k): v for k, v in j["solution_steps"].items()}


def rel_l2(a, b):
    num = math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))
    return num / math.sqrt(sum(y * y for y in b))


truth = frames(FTCS_Q8)


def error_series(case_dir):
    """(steps, relL2-vs-truth) at shared snapshot steps, excluding step 0."""
    fr = frames(case_dir)
    steps = sorted(s for s in fr if s in truth and s > 0)
    return steps, [rel_l2(fr[s], truth[s]) for s in steps]


fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12.5, 4.9), sharey=True)

sv_steps, sv_err = error_series(SV_CASE)
for ax in (ax1, ax2):
    ax.plot(sv_steps, sv_err, color=INK, lw=1.6, ls=(0, (4, 2)),
            label="C0 statevector (shots = 0)")
    ax.set_yscale("log")
    ax.set_xlabel("time step")
    ax.grid(True, axis="y")
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_xlim(0, 512)

for c, (eid, k) in zip(RAMP4, C1_CASES):
    steps, err = error_series(C1 / eid)
    ax1.plot(steps, err, color=c, lw=2, label=f"k = {k}")
ax1.set_ylabel("rel. L2 error vs FTCS truth (log)")
ax1.set_title("C1 seam sweep — error growth over time (2^17 shots)",
              fontsize=11, loc="left")
ax1.legend(fontsize=8, loc="lower right", bbox_to_anchor=(0.99, 0.16))

for c, (eid, s) in zip(RAMP5, C2_CASES):
    steps, err = error_series(C2 / eid)
    ax2.plot(steps, err, color=c, lw=2, label=f"2^{int(math.log2(s))} shots")
ax2.set_title("C2 shots ladder — error growth over time (k = 8)",
              fontsize=11, loc="left")
ax2.legend(fontsize=8, loc="lower right", bbox_to_anchor=(0.99, 0.16))

fig.tight_layout()
fig.savefig(HERE / "figE_error_vs_time.png", dpi=160)
plt.close(fig)

# Standalone C2-only version: step vs relL2, one line per shot count.
fig, ax = plt.subplots(figsize=(8.2, 5.2))
ax.plot(sv_steps, sv_err, color=INK, lw=1.6, ls=(0, (4, 2)),
        label="C0 statevector (shots = 0)")
for c, (eid, s) in zip(RAMP5, C2_CASES):
    steps, err = error_series(C2 / eid)
    ax.plot(steps, err, color=c, lw=2, label=f"2^{int(math.log2(s))} = {s:,} shots")
ax.annotate("2^14 diverges (~step 325):\nφ dead cells → Cole–Hopf division blowup",
            xy=(328, 30), xytext=(80, 60), textcoords="offset points",
            fontsize=8, color=INK2,
            arrowprops={"arrowstyle": "->", "color": MUTED, "lw": 1})
ax.set_yscale("log")
ax.set_xlim(0, 512)
ax.set_xlabel("time step")
ax.set_ylabel("rel. L2 error vs FTCS truth (log)")
ax.set_title("C2 shots ladder (k = 8) — error vs time, one line per shot count",
             fontsize=11, loc="left")
ax.grid(True, axis="y")
ax.spines[["top", "right"]].set_visible(False)
ax.legend(fontsize=8, loc="lower right", bbox_to_anchor=(0.99, 0.14))
fig.tight_layout()
fig.savefig(HERE / "figF_c2_error_vs_time.png", dpi=160)
plt.close(fig)
print("wrote: figE_error_vs_time.png, figF_c2_error_vs_time.png")
