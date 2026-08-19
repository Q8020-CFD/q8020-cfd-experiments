#!/usr/bin/env python3
"""Post-hoc plot for the C9 s1_floor sweep _e9269811: relL2 error vs FTCS
truth at each saved time step (readout), per shots rung.

s2_k1 saves frames at t=0.1 and t=0.2 (steps 1, 2); the S=1 groups save only
the final frame at t=0.2 — s1_k1 and s1_k8 are bit-identical, so one diamond
marks both.  The FTCS q=8 reference (ch_ftcs_refs _3fa21a71, 512 steps to
T=0.2) supplies truth at steps 0 / 256 / 512.

Run from anywhere: paths are resolved relative to this file.
"""
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
SWEEP = HERE.parent
RESULTS_ROOT = SWEEP.parents[2]  # .../results/burgers-ch-lbm
FTCS_Q8 = RESULTS_ROOT / "ch_ftcs_refs/2026-08-13/_3fa21a71/9bbe98a3"

SHOTS = [16384, 32768, 65536, 131072, 262144, 524288]

# dataviz reference palette (light mode)
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"
RAMP6 = ["#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE, "font.family": "sans-serif",
    "axes.edgecolor": AXIS, "axes.linewidth": 0.8,
    "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.labelcolor": INK2, "text.color": INK,
    "grid.color": GRID, "grid.linewidth": 0.6,
    "legend.frameon": False,
})


def rel_l2(a, b):
    num = math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))
    return num / math.sqrt(sum(y * y for y in b))


def mean(xs):
    return sum(xs) / len(xs)


ftcs = json.load(open(FTCS_Q8 / "q8020_artifacts_0.json"))["solution_steps"]
truth = {0.0: ftcs["0"], 0.1: ftcs["256"], 0.2: ftcs["512"]}

meta = json.load(open(SWEEP / f"q8020_sweep_meta_{SWEEP.name[1:]}.json"))

# errs[group][shots][seed] = {t: relL2}
errs = {"s1_k1": {}, "s1_k8": {}, "s2_k1": {}}
for eid, case in meta["cases"].items():
    toks = case["command"][2].split()
    group = case["case_id"].rsplit("_", 1)[0]
    shots = int(toks[toks.index("--shots") + 1])
    seed = int(toks[toks.index("--seed") + 1])
    frames = json.load(open(SWEEP / eid / "q8020_artifacts_0.json"))["solution_steps"]
    n_steps = max(int(k) for k in frames)
    per_t = {}
    for step_key, u in frames.items():
        t = round(0.2 * int(step_key) / n_steps, 6)
        if t > 0:  # t=0 is the exact prepared IC (relL2 = 0, off the log axis)
            per_t[t] = rel_l2(u, truth[t])
    errs[group].setdefault(shots, {})[seed] = per_t

sv_floor = mean([e[0.2] for e in errs["s1_k1"][0].values()])

fig, ax = plt.subplots(figsize=(9.2, 5.6))

# --- s2_k1: two readouts, line per shots rung (seed mean), faint per-seed dots
for color, shots in zip(RAMP6, SHOTS):
    by_seed = errs["s2_k1"][shots]
    ts = [0.1, 0.2]
    ys = [mean([e[t] for e in by_seed.values()]) for t in ts]
    ax.plot(ts, ys, color=color, lw=2, marker="o", ms=5, zorder=3)
    for e in by_seed.values():
        ax.plot(ts, [e[t] for t in ts], color=color, lw=0, marker="o", ms=2.6,
                alpha=0.45, zorder=2)

# --- S=1 single readout at t=0.2 (s1_k1 == s1_k8 bit-identical: one marker)
X1 = 0.207
for color, shots in zip(RAMP6, SHOTS):
    by_seed = errs["s1_k1"][shots]
    y = mean([e[0.2] for e in by_seed.values()])
    ax.plot([X1], [y], marker="D", ms=6.5, mfc=SURFACE, mec=color, mew=1.6,
            lw=0, zorder=4)
    for e in by_seed.values():
        ax.plot([X1], [e[0.2]], marker="D", ms=2.6, mfc="none", mec=color,
                alpha=0.45, lw=0, zorder=2)

# --- statevector floor (shots=0 rung, measured in all three groups)
ax.plot([0.1, 0.2], [sv_floor, sv_floor], color=INK, lw=1.4, ls=(0, (4, 2)),
        zorder=3)
ax.annotate(f"statevector (shots=0): {sv_floor:.0e} — bias floor, all groups",
            (0.1, sv_floor), xytext=(0, 6), textcoords="offset points",
            fontsize=8, color=INK2)

# --- t=0 note: state prep is exact
ax.annotate("t = 0: state prep exact\nrelL2 = 0 (below axis)", (0.0, 1.6e-4),
            fontsize=8, color=MUTED, ha="center", va="bottom")

# --- direct labels for the shots ladder, collision-nudged in log space
labels = []
for color, shots in zip(RAMP6, SHOTS):
    y = mean([e[0.2] for e in errs["s2_k1"][shots].values()])
    labels.append([math.log10(y), f"$2^{{{round(math.log2(shots))}}}$ shots", color])
labels.sort()
MIN_GAP = 0.115  # decades
for i in range(1, len(labels)):
    if labels[i][0] - labels[i - 1][0] < MIN_GAP:
        labels[i][0] = labels[i - 1][0] + MIN_GAP
for ly, text, color in labels:
    ax.annotate(text, (X1, 10 ** ly), xytext=(10, 0), textcoords="offset points",
                fontsize=9, color=INK2, va="center")

ax.set_yscale("log")
ax.set_xlim(-0.022, 0.245)
ax.set_ylim(1.2e-4, 0.7)
ax.set_xticks([0.0, 0.1, 0.2])
ax.set_xlabel("t  (readout times; T_end = 0.2)")
ax.set_ylabel("relL2 vs FTCS truth")
ax.set_title("C9 s1_floor — error at each saved time step, by shots rung",
             fontsize=12, loc="left", pad=24)
ax.text(0, 1.018, "lines: S=2, readouts at t=0.1 and 0.2 · diamonds: S=1 "
        "single readout (k=1 ≡ k=8) · faint marks = per-seed",
        transform=ax.transAxes, fontsize=8.5, color=INK2)
ax.grid(True, axis="y", which="major")

from matplotlib.lines import Line2D
handles = [
    Line2D([], [], color=RAMP6[3], lw=2, marker="o", ms=5,
           label="S=2 (s2_k1), seed mean"),
    Line2D([], [], color=RAMP6[3], lw=0, marker="D", ms=6.5, mfc=SURFACE,
           mec=RAMP6[3], mew=1.6, label="S=1 (s1_k1 ≡ s1_k8), seed mean"),
    Line2D([], [], color=INK, lw=1.4, ls=(0, (4, 2)), label="statevector floor"),
]
ax.legend(handles=handles, fontsize=8.5, loc="upper left")

fig.tight_layout()
out = HERE / "figE_error_per_timestep.png"
fig.savefig(out, dpi=160)
print(f"wrote {out}")
