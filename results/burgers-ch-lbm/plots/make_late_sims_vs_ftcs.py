#!/usr/bin/env python3
"""relL2-vs-FTCS lever plots for the later q=8 Aer-simulation sweeps.

figA-figF (make_plots_vs_ftcs.py / make_error_vs_time.py) stop at C2. These
cover the parameter sweeps that followed, all backend_type=sim (noiseless Aer;
error = shot sampling + MPS bond-dim truncation only), all q=8, all T_end=0.2
so every u_final is scored against the same FTCS q8 final field:

  figH  C6 chi ladder      — error vs bond dim chi   (NULL: truncation is no
                             denoiser)
        C7 cfl/seam ladder — error vs seam count S    (err ~ S^0.84)
  figI  C8 shots x cfl     — error vs shots, one line per S (shots ~ S^-0.5;
                             low S wins a fixed budget)
  figJ  C9 s1 floor        — error vs shots at S=1 down to the exact SV floor;
                             the cfl=51.2 <-> cfl=6.4 k-collapse overlays exactly

Style matches make_error_vs_time.py.
"""
import glob
import json
import math
import os
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
BASE = HERE.parent

FTCS_Q8 = BASE / "ch_ftcs_refs/2026-08-13/_3fa21a71/9bbe98a3"

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"
RAMP3 = ["#86b6ef", "#2a78d6", "#0d366b"]   # S = 2, 4, 8 (light->dark)
RED = "#c1121f"
GREEN = "#2a9d5c"
ORANGE = "#e9924a"

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE, "font.family": "sans-serif",
    "axes.edgecolor": AXIS, "axes.linewidth": 0.8,
    "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.labelcolor": INK2, "text.color": INK,
    "grid.color": GRID, "grid.linewidth": 0.6,
    "legend.frameon": False,
})


def _l2(v):
    return math.sqrt(sum(x * x for x in v))


def rel_l2(u, r):
    return _l2([a - b for a, b in zip(u, r)]) / _l2(r)


TRUTH = json.load(open(FTCS_Q8 / "q8020_results_0.json"))["u_final_method"]


def load_cases(sweep):
    """List of dicts (one per case) with params + relL2 vs FTCS truth.

    Cases whose u_final is missing / non-finite / OOM (wrong length) get
    relL2 = None so callers can drop them explicitly rather than silently.
    """
    out = []
    for cd in sorted(glob.glob(f"{BASE / sweep}/*/*/*/")):
        pf = glob.glob(f"{cd}q8020_params_*.json")
        rf = f"{cd}q8020_results_0.json"
        if not pf or not os.path.exists(rf):
            continue
        p = json.load(open(pf[0]))
        try:
            uf = json.load(open(rf)).get("u_final_method")
            e = rel_l2(uf, TRUTH) if uf and len(uf) == len(TRUTH) else None
            if e is not None and not math.isfinite(e):
                e = None
        except Exception:
            e = None
        seg = p.get("--segment-size") or 1
        ns = p.get("--n-steps")
        out.append({
            "exp": os.path.basename(cd.rstrip("/")),
            "cfl": p.get("--cfl"), "n_steps": ns,
            "shots": p.get("--shots"), "chi": p.get("--bond-dim"),
            "seg": seg, "S": (ns // seg) if ns else None, "relL2": e,
        })
    return out


def mean(v):
    return sum(v) / len(v)


def powerlaw_fit(xs, ys):
    """Least-squares slope/intercept of log(y) = a*log(x) + b."""
    lx = [math.log(x) for x in xs]
    ly = [math.log(y) for y in ys]
    n = len(lx)
    mx, my = mean(lx), mean(ly)
    a = sum((x - mx) * (y - my) for x, y in zip(lx, ly)) / sum((x - mx) ** 2 for x in lx)
    return a, math.exp(my - a * mx)


# SV algorithm floor (shots = 0, exact statevector) — appears in C9.
SV_FLOOR = 1.687e-4

# ============================================================ figH: C6 + C7
c6 = [c for c in load_cases("ch_q8_c6_chi") if c["relL2"] is not None]
c7 = [c for c in load_cases("ch_q8_c7_cfl") if c["relL2"] is not None]

fig, (axc, axs) = plt.subplots(1, 2, figsize=(13, 5.0))

# --- C6: error vs chi (bar) — all pinned near relL2 = 1
c6.sort(key=lambda c: c["chi"])
chis = [c["chi"] for c in c6]
errs = [c["relL2"] for c in c6]
axc.bar([str(x) for x in chis], errs, color=RAMP3[1], width=0.6)
for i, e in enumerate(errs):
    axc.annotate(f"{e:.2f}", xy=(i, e), xytext=(0, 4), textcoords="offset points",
                 ha="center", fontsize=9, color=INK2)
axc.axhline(1.0, color=MUTED, ls=(0, (4, 2)), lw=1.2)
axc.set_ylim(0, 1.35)
axc.set_xlabel("MPS bond dimension  chi")
axc.set_ylabel("rel. L2 error vs FTCS truth")
axc.set_title("C6 chi ladder — truncation is NOT a denoiser\n"
              "(cfl=0.1, S=64, 2^16 shots; every chi pinned at relL2 ~ 1)",
              fontsize=10.5, loc="left")
axc.spines[["top", "right"]].set_visible(False)
axc.grid(True, axis="y")

# --- C7: error vs seam count S (log-log) + power-law fit
c7.sort(key=lambda c: c["S"])
S7 = [c["S"] for c in c7]
e7 = [c["relL2"] for c in c7]
a, b = powerlaw_fit(S7, e7)
gx = [min(S7) * 0.85, max(S7) * 1.18]
axs.plot(gx, [b * x ** a for x in gx], color=MUTED, ls=(0, (4, 2)), lw=1.2,
         zorder=1)
axs.annotate(f"relL2 ~ S^{a:.2f}", xy=(gx[0], b * gx[0] ** a),
             xytext=(6, -16), textcoords="offset points", ha="left",
             fontsize=9, color=MUTED)
axs.plot(S7, e7, color=RED, lw=2, marker="o", ms=8, mec=SURFACE, mew=1.3,
         zorder=3)
for c in c7:
    axs.annotate(f"cfl={c['cfl']}\n{c['relL2']:.2f}", xy=(c["S"], c["relL2"]),
                 xytext=(8, -2), textcoords="offset points", fontsize=8,
                 color=INK2, va="center")
axs.set_xscale("log", base=2)
axs.set_yscale("log")
axs.set_xlabel("seam count  S  (= n_steps / segment_size)")
axs.set_ylabel("rel. L2 error vs FTCS truth")
axs.set_title("C7 cfl / seam ladder — seam count is the lever\n"
              "(fewer seams -> less re-prepare noise; 2^16 shots, chi=4)",
              fontsize=10.5, loc="left")
axs.spines[["top", "right"]].set_visible(False)
axs.grid(True, which="both")

fig.suptitle("Later q=8 Aer-sim sweeps vs FTCS truth (I) — bond dim & seam-count levers",
             fontsize=12, x=0.01, ha="left")
fig.tight_layout(rect=(0, 0, 1, 0.95))
fig.savefig(HERE / "figH_c6_c7_levers.png", dpi=160)
plt.close(fig)

# ============================================================ figI: C8 cross
c8 = [c for c in load_cases("ch_shots_cfl_cross") if c["relL2"] is not None]
# group by (S, shots) -> list of trial relL2
groups = {}
for c in c8:
    groups.setdefault((c["S"], c["shots"]), []).append(c["relL2"])

fig, ax = plt.subplots(figsize=(8.6, 5.6))
S_LABEL = {2: "cfl=3.2  (S=2)", 4: "cfl=1.6  (S=4)", 8: "cfl=0.8  (S=8)"}
for colour, S in zip(RAMP3, (2, 4, 8)):
    shots = sorted({sh for (s, sh) in groups if s == S})
    means = [mean(groups[(S, sh)]) for sh in shots]
    # individual trials (faint) to show shot-noise realization spread
    for sh in shots:
        for e in groups[(S, sh)]:
            ax.plot(sh, e, marker="o", ms=3.5, color=colour, alpha=0.32, zorder=2)
    ax.plot(shots, means, color=colour, lw=2, marker="o", ms=7, mec=SURFACE,
            mew=1.3, zorder=3, label=S_LABEL[S])

# shots^-1/2 reference slope anchored on the S=2 curve
s2_shots = sorted({sh for (s, sh) in groups if s == 2})
s2_last = mean(groups[(2, s2_shots[-1])])
anchor = s2_last * math.sqrt(s2_shots[-1])
gx = [s2_shots[0] * 0.8, s2_shots[-1] * 1.3]
ax.plot(gx, [anchor / math.sqrt(x) for x in gx], color=MUTED, ls=(0, (4, 2)),
        lw=1.2, zorder=1)
lx = 2 ** 16
ax.annotate("error ~ shots^-1/2", xy=(lx, anchor / math.sqrt(lx)),
            xytext=(6, -15), textcoords="offset points", fontsize=8.5, color=MUTED)

# champion point — caption up-left of the marker so it clears the x-tick labels
champ = min(c8, key=lambda c: c["relL2"])
ax.annotate(f"champion: {champ['relL2']:.3f}\n(cfl={champ['cfl']}, "
            f"2^{int(math.log2(champ['shots']))} shots)",
            xy=(champ["shots"], champ["relL2"]), xytext=(-22, 34),
            textcoords="offset points", ha="right", fontsize=8, color=INK2,
            arrowprops={"arrowstyle": "->", "color": MUTED, "lw": 1})

ax.set_xscale("log", base=2)
ax.set_yscale("log")
ax.set_xlabel("shots per segment")
ax.set_ylabel("rel. L2 error vs FTCS truth")
ax.set_title("C8 shots x cfl cross — a fixed shot budget buys more at low seam count\n"
             "(q=8, chi=4; points = individual trials, line = mean)",
             fontsize=10.5, loc="left")
ax.spines[["top", "right"]].set_visible(False)
ax.grid(True, which="both")
ax.legend(fontsize=9, loc="upper right", title="seam count", title_fontsize=9)
fig.tight_layout()
fig.savefig(HERE / "figI_c8_shots_cfl_cross.png", dpi=160)
plt.close(fig)

# ============================================================ figJ: C9 floor
c9 = load_cases("ch_s1_floor")
# S=1 configs: cfl=51.2 (1 step) and cfl=6.4 (8 steps, 1 segment) — should
# collapse. S=2: cfl=25.6. Split by cfl, shots>0 only for the power law.
by_cfl = {}
for c in c9:
    if c["relL2"] is None:
        continue
    by_cfl.setdefault(c["cfl"], {}).setdefault(c["shots"], []).append(c["relL2"])

fig, ax = plt.subplots(figsize=(8.6, 5.6))
SERIES = [
    (51.2, GREEN, "o", "cfl=51.2, 1 step        (S=1)"),
    (6.4,  ORANGE, "s", "cfl=6.4, 8 steps/1 seg  (S=1, sample-once)"),
    (25.6, RED,    "D", "cfl=25.6, 2 steps       (S=2)"),
]
fit_x, fit_y = [], []
for cfl, colour, mk, lbl in SERIES:
    d = by_cfl.get(cfl, {})
    shots = sorted(sh for sh in d if sh and sh > 0)
    means = [mean(d[sh]) for sh in shots]
    hollow = cfl == 6.4  # overlay marker for the k-collapse twin
    ax.plot(shots, means, color=colour, lw=2, marker=mk, ms=9 if hollow else 7,
            mec=colour, mew=2 if hollow else 1.2,
            markerfacecolor="none" if hollow else colour,
            zorder=5 if hollow else 3, label=lbl)
    if cfl == 51.2:  # fit the S=1 power law on the canonical 1-step series
        fit_x, fit_y = shots, means

a, b = powerlaw_fit(fit_x, fit_y)
gx = [min(fit_x) * 0.8, max(fit_x) * 1.25]
ax.plot(gx, [b * x ** a for x in gx], color=MUTED, ls=(0, (4, 2)), lw=1.2, zorder=1)
ax.annotate(f"S=1 floor: relL2 ~ shots^{a:.2f}",
            xy=(gx[0], b * gx[0] ** a), xytext=(6, 10), textcoords="offset points",
            fontsize=8.5, color=MUTED)

# exact statevector floor
ax.axhline(SV_FLOOR, color=INK, ls=(0, (1, 2)), lw=1.3)
ax.annotate(f"exact statevector floor (shots=0):  relL2 = {SV_FLOOR:.1e}",
            xy=(min(fit_x), SV_FLOOR), xytext=(0, 6), textcoords="offset points",
            fontsize=8.5, color=INK)

# mark the 2^17 operating point on the S=1 curve (below-left, clear of legend)
op = by_cfl.get(51.2, {}).get(131072)
if op:
    ax.annotate(f"2^17 shots: {mean(op):.3f}", xy=(131072, mean(op)),
                xytext=(-12, -34), textcoords="offset points", ha="right",
                fontsize=8, color=INK2,
                arrowprops={"arrowstyle": "->", "color": MUTED, "lw": 1})

ax.set_xscale("log", base=2)
ax.set_yscale("log")
ax.set_xlabel("shots per segment")
ax.set_ylabel("rel. L2 error vs FTCS truth")
ax.set_title("C9 S=1 shot floor — the hardware operating point\n"
             "(q=8, chi=4; cfl=51.2 and cfl=6.4 collapse to the same curve)",
             fontsize=10.5, loc="left")
ax.spines[["top", "right"]].set_visible(False)
ax.grid(True, which="both")
# the empty band between the shot data and the floor line IS the finding:
ax.annotate("shot sampling plateaus ~2.5 decades\nabove the exact algorithm — "
            "more shots,\nnot a better circuit, is the only lever here",
            xy=(2 ** 16, 3e-3), ha="center", fontsize=8.5, color=MUTED)
ax.legend(fontsize=8.5, loc="center right", title="S=1 (and S=2 for contrast)",
          title_fontsize=8.5)
fig.tight_layout()
fig.savefig(HERE / "figJ_c9_s1_floor.png", dpi=160)
plt.close(fig)

print("wrote: figH_c6_c7_levers.png, figI_c8_shots_cfl_cross.png, figJ_c9_s1_floor.png")
print(f"  C6 chi: all relL2 = {[round(c['relL2'], 2) for c in sorted(c6, key=lambda c: c['chi'])]} (chi={[c['chi'] for c in sorted(c6, key=lambda c: c['chi'])]})")
print(f"  C7 seam power law: relL2 ~ S^{powerlaw_fit([c['S'] for c in c7],[c['relL2'] for c in c7])[0]:.2f}")
print(f"  C8 champion: relL2={champ['relL2']:.4f} (cfl={champ['cfl']}, 2^{int(math.log2(champ['shots']))} shots)")
print(f"  C9 S=1 power law: relL2 ~ shots^{a:.2f}; exact SV floor {SV_FLOOR:.2e}")
