#!/usr/bin/env python3
"""Post-hoc plots for the C2 shots ladder (k=8) sweep _6fade974.

Reads the per-case q8020_results_0.json / q8020_analysis_0.json fragments and
the C0 statevector-floor case, and renders three PNGs into this directory.
Run from anywhere: paths are resolved relative to this file.
"""
import json
import math
from pathlib import Path

import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
SWEEP = HERE.parent
RESULTS_ROOT = SWEEP.parents[2]  # .../results/burgers-ch-lbm
SV_CASE = RESULTS_ROOT / "ch_q8_c0/2026-08-06/_a66942a3/1f33d059"
C1_K16 = RESULTS_ROOT / "ch_q8_c1/2026-08-11/_b5c8743c/fe96b52e"

CASES = [  # (experiment_id, shots) in ladder order
    ("c1e5d7e4", 16384),
    ("00e609d3", 65536),
    ("1cc667ab", 131072),
    ("3dcb7c60", 524288),
    ("70416813", 1048576),
]

# dataviz reference palette (light mode)
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"
BLUE1 = "#2a78d6"           # categorical slot 1
ORANGE = "#eb6834"          # categorical slot 2
RAMP5 = ["#86b6ef", "#5598e7", "#2a78d6", "#1c5cab", "#0d366b"]  # ordinal, validated
RAMP4 = ["#86b6ef", "#3987e5", "#1c5cab", "#0d366b"]

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE, "font.family": "sans-serif",
    "axes.edgecolor": AXIS, "axes.linewidth": 0.8,
    "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.labelcolor": INK2, "text.color": INK,
    "grid.color": GRID, "grid.linewidth": 0.6,
    "legend.frameon": False,
})


def load(case_dir, name):
    return json.load(open(case_dir / name))


def rel_l2(a, b):
    num = math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))
    return num / math.sqrt(sum(y * y for y in b))


def shot_label(s):
    return f"2^{int(math.log2(s))} = {s:,}"


grid = load(SWEEP / CASES[0][0], "q8020_artifacts_0.json")["grid"]
u_ref = load(SV_CASE, "q8020_results_0.json")["u_final_method"]
u = {s: load(SWEEP / eid, "q8020_results_0.json")["u_final_method"] for eid, s in CASES}
norms = {
    s: [m["cumulative_norm"] for m in load(SWEEP / eid, "q8020_analysis_0.json")["per_step_metrics"]]
    for eid, s in CASES
}
u_c1k16 = load(C1_K16, "q8020_results_0.json")["u_final_method"]

# ---------------------------------------------------------------- fig 1: fields
fig, (ax, ax2) = plt.subplots(
    1, 2, figsize=(11, 4.4), gridspec_kw={"width_ratios": [2.6, 1]}
)
ax.plot(grid, u_ref, color=INK, lw=1.6, ls=(0, (4, 2)), label="statevector (shots = 0)", zorder=5)
for c, (eid, s) in zip(RAMP4, CASES[1:]):
    ax.plot(grid, u[s], color=c, lw=2, label=shot_label(s))
ax.set_xlabel("x")
ax.set_ylabel("u(x, t final)")
ax.set_title("Final velocity field vs statevector reference (k = 8, 512 steps)", fontsize=11, loc="left")
ax.grid(True, axis="y")
ax.legend(fontsize=8, loc="upper right")

clip = 3.0
ax2.plot(grid, [max(-clip, min(clip, v)) for v in u[16384]], color=ORANGE, lw=1.2)
ax2.axhspan(clip * 0.98, clip, color=ORANGE, alpha=0.15, lw=0)
ax2.set_ylim(-clip, clip)
ax2.set_xlabel("x")
ax2.set_title("2^14 = 16,384 shots — diverged", fontsize=10, loc="left", color=INK2)
ax2.text(0.03, 0.95, "clipped at ±3\npeaks reach ±495", transform=ax2.transAxes,
         va="top", fontsize=8, color=INK2)
ax2.grid(True, axis="y")
for a in (ax, ax2):
    a.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig(HERE / "fig1_final_fields.png", dpi=160)
plt.close(fig)

# ---------------------------------------------------------------- fig 2: ladder
pts = [(s, rel_l2(u[s], u_ref)) for _, s in CASES[1:]]
c1pt = (131072, rel_l2(u_c1k16, u_ref))

fig, ax = plt.subplots(figsize=(6.6, 4.6))
xs = [p[0] for p in pts]
ys = [p[1] for p in pts]
# 1/sqrt(shots) guide anchored on the top rung
gx = [xs[0] / 2, xs[-1] * 4]
anchor = ys[-1] * math.sqrt(xs[-1])
ax.plot(gx, [anchor / math.sqrt(x) for x in gx], color=MUTED, lw=1.2, ls=(0, (4, 2)))
ax.annotate("pure shot noise\n(error ∝ 1/√shots)", xy=(gx[-1], anchor / math.sqrt(gx[-1])),
            xytext=(-8, 14), textcoords="offset points", ha="right", fontsize=8, color=MUTED)
ax.plot(xs, ys, color=BLUE1, lw=2, marker="o", ms=7, mec=SURFACE, mew=1.5, label="k = 8 shots ladder (C2)")
for x, y in pts:
    ax.annotate(f"{y:.2f}", xy=(x, y), xytext=(0, -14), textcoords="offset points",
                ha="center", fontsize=8, color=INK2)
ax.plot(*c1pt, marker="D", ms=7, color=ORANGE, mec=SURFACE, mew=1.5, ls="none",
        label="k = 16 @ 2^17 (C1 winner)")
ax.annotate(f"{c1pt[1]:.2f}", xy=c1pt, xytext=(0, -14), textcoords="offset points",
            ha="center", fontsize=8, color=INK2)
ax.set_xscale("log", base=2)
ax.set_yscale("log")
ax.set_xlabel("shots per segment")
ax.set_ylabel("rel. L2 error vs statevector field")
ax.set_title("Shot-noise ladder at k = 8 — no truncation floor visible", fontsize=11, loc="left")
ax.text(0.02, 0.03, "2^14 rung diverged (relL2 ≈ 365) — omitted", transform=ax.transAxes,
        fontsize=8, color=INK2)
ax.grid(True, which="major")
ax.legend(fontsize=8, loc="upper right")
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig(HERE / "fig2_shots_ladder.png", dpi=160)
plt.close(fig)

# ---------------------------------------------------------------- fig 3: norms
fig, ax = plt.subplots(figsize=(7.2, 4.6))
segs = list(range(1, 65))
for c, (eid, s) in zip(RAMP5, CASES):
    ax.plot(segs, norms[s], color=c, lw=2, label=shot_label(s))
# direct end labels — lines ending within a hair of each other share one label
end_groups = [("2^14", [16384]), ("2^16, 2^17", [65536, 131072]),
              ("2^19, 2^20", [524288, 1048576])]
for text, group in end_groups:
    y = sum(norms[s][-1] for s in group) / len(group)
    ax.annotate(text, xy=(segs[-1], y), xytext=(4, 0), textcoords="offset points",
                va="center", fontsize=8, color=INK2)
ax.set_xlabel("segment (8 steps each)")
ax.set_ylabel("cumulative norm")
ax.set_title("Norm decay across measure-reprepare seams", fontsize=11, loc="left")
ax.grid(True, axis="y")
ax.legend(fontsize=8, loc="lower left")
ax.spines[["top", "right"]].set_visible(False)
ax.set_xlim(1, 70)
fig.tight_layout()
fig.savefig(HERE / "fig3_norm_decay.png", dpi=160)
plt.close(fig)

print("wrote:", *[p.name for p in sorted(HERE.glob("fig*.png"))])
