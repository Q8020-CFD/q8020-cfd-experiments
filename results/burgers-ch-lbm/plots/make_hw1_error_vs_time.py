#!/usr/bin/env python3
"""Per-timestep relL2 error vs the FTCS baseline for the HW1 q x S ladder.

The first real-hardware Cole-Hopf ladder (ibm_kingston, sweep _c0ccc727,
2026-08-24).  Five of six cases succeeded (q8_s2 died in transpile — a
qiskit Weyl-decomposition panic on segment 2).

Style matches make_error_vs_time.py (figE/figF), with two HW-specific twists:

  * The FTCS references were generated at cfl=0.1, so their integer step
    numbering does NOT line up with the large-cfl hardware steps.  Every
    hardware seam is therefore compared to the reference frame at the SAME
    PHYSICAL TIME (T_end = 0.2 on every rung).  x-axis is physical time.
  * No stored q=3 reference exists (the refs sweep was q4/q8/q16), so the
    q3 truth is regenerated here with the solver's own FTCS scheme
    (validated bit-exact against the stored q4 reference at T=0.2).

y-axis is LINEAR (not log like figE): every HW1 error sits in the narrow
0.55-1.03 band, and a log axis just compresses them all against the top.
Linear makes the q3 < q4 < q8 separation legible.
"""
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
BASE = HERE.parent

FTCS_Q4 = BASE / "ch_ftcs_refs/2026-08-13/_3fa21a71/e895390e"
FTCS_Q8 = BASE / "ch_ftcs_refs/2026-08-13/_3fa21a71/9bbe98a3"
HW1 = BASE / "ch_hw1_qs_ladder/2026-08-24/_c0ccc727"

T_END = 0.2
NU = 0.03
AMP = 0.3

# (experiment_id, case label, q, colour, marker, n_seams) — in ladder order.
# Single-seam rungs run the whole T=0.2 in one big-cfl step, so their only
# hardware measurement is at t=0.2 — they plot as a hollow ring so they stay
# visible where they land on top of their multi-seam twin.
CASES = [
    ("4d71c7b2", "q3_s1", 3, "#2a9d5c", "o", 1),   # real signal
    ("1413af3e", "q4_s1", 4, "#e9924a", "s", 1),   # marginal
    ("27ed87d6", "q4_s2", 4, "#c1121f", "D", 2),   # marginal
    ("4af61175", "q8_s1", 8, "#3987e5", "^", 1),   # depolarized
    ("2fbeed62", "q8_s4", 8, "#0d366b", "v", 4),   # depolarized
]

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"

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


def hw_frames(exp_id):
    """{step: field} snapshots from a hardware run."""
    j = json.load(open(HW1 / exp_id / "q8020_artifacts_0.json"))
    return {int(k): v for k, v in j["solution_steps"].items()}


def stored_ref_traj(case_dir):
    """{step: field} from a stored FTCS reference run (cfl=0.1)."""
    j = json.load(open(Path(case_dir) / "q8020_artifacts_0.json"))
    return {int(k): v for k, v in j["solution_steps"].items()}


def ftcs_field(q, t):
    """FTCS truth on the 2^q grid at physical time t, regenerated with the
    solver's own scheme (resolved >=800-pt grid, sub-stepped for the FTCS
    diffusion floor, subsampled back to the q-grid).  Central-difference
    periodic stencil, matching lib_fd.compute_rhs_shift."""
    N = 2 ** q
    k = max(1, int(math.ceil(800 / N)))
    M = N * k
    x = np.linspace(0.0, 1.0, M, endpoint=False)
    u = AMP * np.sin(2 * np.pi * x)
    dx = x[1] - x[0]
    if t <= 0:
        return u[::k].tolist()
    dt_stable = 0.25 * dx * dx / NU
    n_sub = max(1, int(math.ceil(t / dt_stable)))
    dts = t / n_sub
    for _ in range(n_sub):
        grad = (np.roll(u, -1) - np.roll(u, 1)) / (2 * dx)
        lap = (np.roll(u, -1) + np.roll(u, 1) - 2 * u) / dx ** 2
        u = u + dts * (NU * lap - u * grad)
    return u[::k].tolist()


# Reference lookups keyed by q. q4/q8 use the stored frame-aligned refs;
# q3 is regenerated. All three reach T_END=0.2 but at different step counts
# (q8 ref: step 512; q4 ref: step 32 — it ran to T=3.2 at cfl=0.1).
STORED = {4: (stored_ref_traj(FTCS_Q4), 32), 8: (stored_ref_traj(FTCS_Q8), 512)}


def truth_field(q, t):
    """FTCS field on the 2^q grid at physical time t (0 <= t <= T_END)."""
    if q in STORED:
        traj, step_at_tend = STORED[q]
        step = int(round(step_at_tend * t / T_END))
        step = min(traj, key=lambda s: abs(s - step))  # nearest saved frame
        return traj[step]
    return ftcs_field(q, t)


def error_series(exp_id, q):
    """(times, relL2) for a hardware case, one point per MEASURED seam.

    Step 0 (the exact re-prepared IC, relL2 == 0) is excluded, matching the
    figE convention: a single-seam rung then plots as one honest marker at
    t=0.2 rather than a diagonal from the origin that would falsely imply
    measured mid-run error growth."""
    fr = hw_frames(exp_id)
    n = max(fr)
    ts, errs = [], []
    for s in sorted(fr):
        if s == 0:
            continue
        t = T_END * s / n
        ts.append(t)
        errs.append(rel_l2(fr[s], truth_field(q, t)))
    return ts, errs


# ============================ figure ============================
# Two panels by q-family (the figE idiom). Left: the depolarized q8 rungs.
# Right: the low-q rungs where signal survives. Shared y-axis.
fig, (ax8, ax_lo) = plt.subplots(1, 2, figsize=(13, 5.2), sharey=True)

summary = {}


def draw(ax, eid, label, q, colour, marker, n_seams):
    ts, errs = error_series(eid, q)
    summary[label] = list(zip([round(t, 3) for t in ts],
                              [round(e, 4) for e in errs]))
    single = n_seams == 1
    ax.plot(
        ts, errs, color=colour, lw=2, marker=marker, ms=12 if single else 8,
        markerfacecolor="none" if single else colour,
        markeredgecolor=colour, markeredgewidth=2 if single else 1,
        zorder=5 if single else 3,
        label=f"{label}  ({n_seams} seam{'s' if n_seams != 1 else ''})",
    )


for ax, title in ((ax8, "q8 rungs — fully depolarized (19,301 CZ routed)"),
                  (ax_lo, "q4 / q3 rungs — signal survives as q drops")):
    ax.axhline(1.0, color=MUTED, ls=(0, (4, 2)), lw=1.2)
    ax.set_xlim(-0.005, 0.208)
    ax.set_ylim(0, 1.12)
    ax.set_xlabel("physical time  t   (T_end = 0.2, 1 marker / re-prepare seam)")
    ax.grid(True, axis="y")
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_title(title, fontsize=10.5, loc="left")

ax8.set_ylabel("rel. L2 error vs FTCS truth")
ax8.text(0.004, 1.006, "relL2 = 1  (100% error — depolarized)",
         fontsize=8, color=INK2, va="bottom")

for eid, label, q, colour, marker, n_seams in CASES:
    draw(ax8 if q == 8 else ax_lo, eid, label, q, colour, marker, n_seams)

ax8.legend(fontsize=9, loc="lower left", title="q8 cases", title_fontsize=9)
ax_lo.legend(fontsize=9, loc="center left", title="q4 / q3 cases",
             title_fontsize=9)

# The q4 single- and double-seam endpoints land on top of each other (~0.96):
# seam count barely moved the error — call it out rather than fight the overlap.
ax_lo.annotate("q4_s1 ≈ q4_s2 at t=0.2\n(seam count barely helps)",
               xy=(0.2, 0.96), xytext=(0.086, 0.66), fontsize=8, color=INK2,
               arrowprops={"arrowstyle": "->", "color": MUTED, "lw": 1})
ax_lo.annotate("q3: shape ~intact (cos 0.96),\nerror is mostly amplitude loss",
               xy=(0.2, 0.551), xytext=(0.045, 0.40), fontsize=8, color="#1f7a46",
               arrowprops={"arrowstyle": "->", "color": "#7bbf97", "lw": 1})

fig.suptitle("HW1 q x S ladder on ibm_kingston (2026-08-24) — per-seam relL2 error vs FTCS truth "
             "  ·  q8_s2 excluded (transpile crash)",
             fontsize=12, x=0.01, ha="left")
fig.tight_layout(rect=(0, 0, 1, 0.96))
out = HERE / "figG_hw1_error_vs_time.png"
fig.savefig(out, dpi=160)
plt.close(fig)

print("wrote:", out.name)
for label, pts in summary.items():
    tail = pts[-1]
    print(f"  {label:6s} final relL2 @ t={tail[0]}: {tail[1]:.4f}   "
          f"trajectory={pts}")
