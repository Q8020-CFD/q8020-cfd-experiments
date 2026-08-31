#!/usr/bin/env python3
"""relL2(t) vs the FTCS reference for each --phi-modes case in ch_q8_phi_sweep.

Each Cole-Hopf run stores errors_by_step (relL2 of its reconstruction against the
in-process FTCS baseline at every saved frame). FTCS is the reference, so its own
relL2 is identically 0 (the x-axis floor); every plotted line is one phi value.

Encoding: phi=2 is the lone physical result -> aqua accent, bold, direct-labeled.
The other 8 are a single "blown-up" family -> blue sequential ramp ordered by phi
(light = few modes, dark = many modes). Log-y spans the ~200x dynamic range.
"""
import json
import glob
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "2026-08-28", "_ea9fbc06")
DT = 0.1 / 256  # cfl * dx = 3.90625e-4

# --- gather (phi -> (times, relL2)) from every case dir -----------------
series = {}
for d in sorted(glob.glob(os.path.join(ROOT, "*", ""))):
    cid = os.path.basename(d.rstrip("/"))
    params = json.load(open(os.path.join(d, f"q8020_params_{cid}.json")))
    phi = params.get("--phi-modes")
    eb = json.load(open(os.path.join(d, "q8020_results_0.json")))["errors_by_step"]
    steps = sorted(eb.keys(), key=int)
    # drop step 0 (relL2 == 0, not representable on a log axis)
    xs = [int(s) * DT for s in steps if eb[s] > 0]
    ys = [eb[s] for s in steps if eb[s] > 0]
    series[phi] = (xs, ys)

# --- palette (validated dataviz reference instance) ---------------------
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK2 = "#52514e"
ACCENT = "#1baf7a"  # aqua "good" -> phi=2, the physical reconstruction
# blue sequential ramp, light->dark (palette steps 250..600), 8 shades
BLUE_RAMP = ["#86b6ef", "#6da7ec", "#5598e7", "#3987e5",
             "#2a78d6", "#256abf", "#1c5cab", "#184f95"]

family = [p for p in sorted(series) if p != 2]  # 0,1,3,4,5,8,16,32
ramp = {p: BLUE_RAMP[i] for i, p in enumerate(family)}

# --- plot ---------------------------------------------------------------
fig, ax = plt.subplots(figsize=(10.5, 6.2), dpi=150)
fig.patch.set_facecolor(SURFACE)
ax.set_facecolor(SURFACE)

# yardstick: relL2 = 1 means the error norm equals the signal norm
ax.axhline(1.0, ls="--", lw=1.0, color=INK2, alpha=0.5, zorder=1)
ax.text(series[2][0][-1], 1.06, "relL2 = 1  (error = signal magnitude)",
        ha="right", va="bottom", fontsize=8.5, color=INK2)

# blown-up family first (recessive), then phi=2 on top
for p in family:
    xs, ys = series[p]
    ax.plot(xs, ys, lw=1.4, color=ramp[p], alpha=0.9, label=f"φ={p}", zorder=2)

xs, ys = series[2]
ax.plot(xs, ys, lw=2.6, color=ACCENT, marker="o", markersize=4,
        label="φ=2  (physical)", zorder=5)

# direct label for phi=2, placed in the open region below its line
ax.text(0.088, 0.33, "φ=2  (only physical case)", color=ACCENT,
        fontsize=10.5, fontweight="bold", ha="left", va="center")
for p, tag in [(32, "φ=32"), (0, "φ=0 (no filter)")]:
    fx, fy = series[p][0][-1], series[p][1][-1]
    ax.annotate(tag, (fx, fy), xytext=(6, 0), textcoords="offset points",
                va="center", color=ramp[p], fontsize=9)

ax.set_yscale("log")
ax.set_xlabel("time  t", fontsize=11, color=INK)
ax.set_ylabel("relative L2 error vs FTCS reference   (log scale)",
              fontsize=11, color=INK)
ax.set_title("Cole–Hopf φ-modes sweep — reconstruction error vs FTCS over time\n"
             "q=8 (256 grid),  ν=0.015,  A=0.3,  cfl=0.1,  150k shots,  seg-10  "
             "(T_end=0.156)", fontsize=12, color=INK, pad=12)

ax.grid(True, which="both", color=INK2, alpha=0.18, lw=0.6)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK2)
ax.tick_params(colors=INK2)

# FTCS-is-the-reference note
ax.text(0.012, 0.02, "FTCS is the reference → its own relL2 ≡ 0 (the x-axis floor)",
        transform=ax.transAxes, fontsize=8.5, color=INK2, style="italic")

leg = ax.legend(title="φ (Fourier modes kept)", loc="center left",
                bbox_to_anchor=(1.01, 0.5), frameon=False, fontsize=9,
                title_fontsize=9.5)
leg.get_title().set_color(INK)

fig.tight_layout()
out = os.path.join(HERE, "phi_sweep_relL2_vs_time.png")
fig.savefig(out, bbox_inches="tight", facecolor=SURFACE)
print("wrote", out)
