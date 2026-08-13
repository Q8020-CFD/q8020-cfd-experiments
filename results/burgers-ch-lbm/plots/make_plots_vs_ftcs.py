#!/usr/bin/env python3
"""Cross-sweep comparison of every burgers-ch-lbm quantum run against the
FTCS classical baseline (ch_ftcs_refs q=8, resolved 4x and subsampled).

Covers C0 (statevector), C1 (seam sweep k=2..16 @ 2^17 shots), and the
C2 k=8 shots ladder.  Renders four PNGs into this directory.
"""
import json
import math
from pathlib import Path

import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
BASE = HERE.parent  # .../results/burgers-ch-lbm

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
BLUE1 = "#2a78d6"   # categorical slot 1 — C0 / primary series
ORANGE = "#eb6834"  # categorical slot 2 — C1
AQUA = "#1baf7a"    # categorical slot 3 — C2
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


def field(case_dir):
    return json.load(open(Path(case_dir) / "q8020_results_0.json"))["u_final_method"]


def rel_l2(a, b):
    num = math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))
    return num / math.sqrt(sum(y * y for y in b))


ftcs = field(FTCS_Q8)
sv = field(SV_CASE)
grid = json.load(open(C2 / C2_CASES[0][0] / "q8020_artifacts_0.json"))["grid"]
u_c1 = {k: field(C1 / eid) for eid, k in C1_CASES}
u_c2 = {s: field(C2 / eid) for eid, s in C2_CASES}
sv_floor = rel_l2(sv, ftcs)

# ------------------------------------------------- fig A: C0 SV vs FTCS
fig, (ax, ax2) = plt.subplots(1, 2, figsize=(11, 4.2),
                              gridspec_kw={"width_ratios": [1.4, 1]})
ax.plot(grid, ftcs, color=INK, lw=1.6, ls=(0, (4, 2)), label="FTCS truth (resolved 4x)")
ax.plot(grid, sv, color=BLUE1, lw=2, label="C0 statevector circuit")
ax.set_xlabel("x")
ax.set_ylabel("u(x, t final)")
ax.set_title("C0 statevector vs FTCS truth — visually identical", fontsize=11, loc="left")
ax.legend(fontsize=8, loc="upper right")
ax.grid(True, axis="y")

diff = [(a - b) * 1e4 for a, b in zip(sv, ftcs)]
ax2.plot(grid, diff, color=BLUE1, lw=1.5)
ax2.axhline(0, color=AXIS, lw=0.8)
ax2.set_xlabel("x")
ax2.set_ylabel("(SV − FTCS) × 10⁻⁴")
ax2.set_title(f"pointwise gap (relL2 = {sv_floor:.1e})", fontsize=10, loc="left", color=INK2)
ax2.grid(True, axis="y")
for a in (ax, ax2):
    a.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig(HERE / "figA_c0_sv_vs_ftcs.png", dpi=160)
plt.close(fig)

# ------------------------------------------------- fig B: C1 seam sweep vs FTCS
fig, (ax, ax2) = plt.subplots(1, 2, figsize=(11, 4.4),
                              gridspec_kw={"width_ratios": [1.6, 1]})
ax.plot(grid, ftcs, color=INK, lw=1.6, ls=(0, (4, 2)), label="FTCS truth", zorder=5)
ax.plot(grid, u_c1[8], color=RAMP4[1], lw=2, label="k = 8")
ax.plot(grid, u_c1[16], color=RAMP4[3], lw=2, label="k = 16")
ax.set_xlabel("x")
ax.set_ylabel("u(x, t final)")
ax.set_title("C1 final fields vs FTCS truth (2^17 shots; k = 2, 4 diverged — see right)",
             fontsize=11, loc="left")
ax.legend(fontsize=8, loc="upper right")
ax.grid(True, axis="y")

ks = [k for _, k in C1_CASES]
errs = [rel_l2(u_c1[k], ftcs) for k in ks]
diverged = [e > 10 for e in errs]
colors = [ORANGE if d else BLUE1 for d in diverged]
ax2.bar([str(k) for k in ks], errs, color=colors, width=0.62)
for i, (e, d) in enumerate(zip(errs, diverged)):
    label = f"{e:.0f}\ndiverged" if d else f"{e:.2f}"
    ax2.annotate(label, xy=(i, e), xytext=(0, 4), textcoords="offset points",
                 ha="center", va="bottom", fontsize=8,
                 color=ORANGE if d else INK2)
ax2.set_yscale("log")
ax2.set_ylim(0.1, max(errs) * 30)
ax2.set_xlabel("segment size k")
ax2.set_ylabel("rel. L2 error vs FTCS truth")
ax2.set_title("error vs k (log)", fontsize=10, loc="left", color=INK2)
for a in (ax, ax2):
    a.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig(HERE / "figB_c1_seam_sweep_vs_ftcs.png", dpi=160)
plt.close(fig)

# ------------------------------------------------- fig C: C2 ladder vs FTCS
fig, ax = plt.subplots(figsize=(6.8, 4.8))
pts = [(s, rel_l2(u_c2[s], ftcs)) for _, s in C2_CASES[1:]]
xs, ys = [p[0] for p in pts], [p[1] for p in pts]
gx = [xs[0] / 2, xs[-1] * 4]
anchor = ys[-1] * math.sqrt(xs[-1])
ax.plot(gx, [anchor / math.sqrt(x) for x in gx], color=MUTED, lw=1.2, ls=(0, (4, 2)))
ax.annotate("error ∝ 1/√shots", xy=(gx[-1], anchor / math.sqrt(gx[-1])),
            xytext=(-6, 12), textcoords="offset points", ha="right",
            fontsize=8, color=MUTED)
ax.plot(xs, ys, color=AQUA, lw=2, marker="o", ms=7, mec=SURFACE, mew=1.5,
        label="C2 k = 8 shots ladder")
for x, y in pts:
    ax.annotate(f"{y:.2f}", xy=(x, y), xytext=(0, -14), textcoords="offset points",
                ha="center", fontsize=8, color=INK2)
ax.axhline(sv_floor, color=BLUE1, lw=1.4, ls=(0, (4, 2)))
ax.annotate(f"C0 statevector floor ({sv_floor:.0e}) — 3 orders of headroom",
            xy=(xs[0], sv_floor), xytext=(0, 6), textcoords="offset points",
            fontsize=8, color=BLUE1)
ax.set_xscale("log", base=2)
ax.set_yscale("log")
ax.set_ylim(sv_floor / 4, 4)
ax.set_xlabel("shots per segment")
ax.set_ylabel("rel. L2 error vs FTCS truth")
ax.set_title("C2 shots ladder vs FTCS truth — all error is seam noise",
             fontsize=11, loc="left")
ax.text(0.02, 0.03, "2^14 rung diverged (relL2 ≈ 365) — omitted",
        transform=ax.transAxes, fontsize=8, color=INK2)
ax.grid(True, which="major")
ax.legend(fontsize=8, loc="upper right")
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig(HERE / "figC_c2_ladder_vs_ftcs.png", dpi=160)
plt.close(fig)

# ------------------------------------------------- fig D: summary, all runs
runs = [("C0  statevector (shots = 0)", rel_l2(sv, ftcs), BLUE1, False)]
runs += [(f"C1  k = {k} @ 2^17 shots", rel_l2(u_c1[k], ftcs), ORANGE, rel_l2(u_c1[k], ftcs) > 10)
         for k in [2, 4, 8, 16]]
runs += [(f"C2  k = 8 @ 2^{int(math.log2(s))} shots", rel_l2(u_c2[s], ftcs), AQUA,
          rel_l2(u_c2[s], ftcs) > 10) for _, s in C2_CASES]

fig, ax = plt.subplots(figsize=(8.4, 5.2))
labels = [r[0] for r in runs][::-1]
vals = [r[1] for r in runs][::-1]
cols = [r[2] for r in runs][::-1]
divs = [r[3] for r in runs][::-1]
bars = ax.barh(labels, vals, color=[c if not d else "none" for c, d in zip(cols, divs)],
               edgecolor=[c for c in cols], height=0.62,
               hatch=["///" if d else "" for d in divs])
for i, (v, d) in enumerate(zip(vals, divs)):
    txt = f"{v:.0f}  diverged" if d else (f"{v:.1e}" if v < 1e-2 else f"{v:.2f}")
    ax.annotate(txt, xy=(v, i), xytext=(5, 0), textcoords="offset points",
                va="center", fontsize=8, color=INK2)
ax.set_xscale("log")
ax.set_xlim(sv_floor / 5, max(vals) * 60)
ax.set_xlabel("rel. L2 error vs FTCS truth (log)")
ax.set_title("All burgers-ch-lbm runs vs the FTCS classical baseline",
             fontsize=11, loc="left")
ax.grid(True, axis="x")
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig(HERE / "figD_all_runs_vs_ftcs.png", dpi=160)
plt.close(fig)

print("wrote:", *[p.name for p in sorted(HERE.glob("fig*.png"))])
