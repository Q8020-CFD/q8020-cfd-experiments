#!/usr/bin/env python3
"""First-segment u(x) profiles: June n=1 lines with the September UQ as a shadow.

One small-multiple panel per device.  Each panel carries, from the bottom up:
  * the FTCS-800 reference curve (the "sine" the run is being scored against),
  * the noiseless statevector ceiling at the 8 q-nodes -- what this circuit
    recovers with zero device noise (clean sine, ~86% amplitude),
  * Melvina's June n=1 hardware profile,
  * the September mean with its run-to-run shadow (+/-1 sd, and min-max).

The point of the figure is that the September shadow is TIGHT but does not
overlap the June line, and neither epoch tracks the sine -- so a "June sine
with a Sept error band on it" reading is not available from this data.

Reuses the loaders/truth from uq_smooth_movie_segment1 and the fine reference
curve from score_smooth_movie_rerun so nothing can disagree numerically.
Run with the tooling venv python.
"""
from __future__ import annotations

import glob
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import uq_smooth_movie_segment1 as uq
from score_smooth_movie_rerun import ftcs800_full_frames

# --- validated palette (3 categorical slots, light mode; validator: PASS) ----
SURFACE = "#fcfcfb"
TEXT_1, TEXT_2, TEXT_3 = "#0b0b0b", "#52514e", "#84837c"
MUTED = "#898781"
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
BLUE_BAND, BLUE_FAINT = "#86b6ef", "#cde2fb"
GRID = "#e4e3df"

DEVS = ("kingston", "fez", "miami", "boston")
OUT = os.path.abspath(os.path.join(
    uq.REPO, "q8020-cfd-experiments", "results", "burgers-ch-lbm",
    "ch_smooth_movie_rerun", "analysis", "profiles_segment1.png"))


def sept_profiles(dev: str) -> np.ndarray:
    """All September frame-1 node profiles for a device, shape (n_trials, 8)."""
    root = os.path.join(
        uq.REPO, "q8020-cfd-experiments", "results", "burgers-ch-lbm",
        "ch_smooth_movie_rerun", "2026-09-10", "_0ca9db0f", dev)
    out = []
    for td in sorted(glob.glob(os.path.join(root, "trial_*"))):
        mp = glob.glob(os.path.join(td, "q8020_metadata_*.json"))
        if not mp:
            continue
        fr = uq.frames_of(mp[0])
        if fr and uq.FRAME in fr and np.all(np.isfinite(fr[uq.FRAME])):
            out.append(fr[uq.FRAME])
    return np.array(out) if out else np.empty((0, uq.N))


def june_profile(dev: str) -> np.ndarray | None:
    p = os.path.join(
        uq.REPO, "q8020-cfd-experiments", "results",
        "burgers-ch-lbm-June2026", "real-qc", "hardware_runs",
        f"smooth_movie_{dev}", "method_compare", "cole_hopf_circuit",
        "q8020_artifacts_0.json")
    fr = uq.frames_of(p)
    return fr[uq.FRAME] if fr and uq.FRAME in fr else None


def main():
    truth_nodes = uq.ftcs800_truth_frames()[uq.FRAME]
    x_ref, fine = ftcs800_full_frames()
    truth_fine = fine[uq.FRAME]
    sim = uq.load_sim(truth_nodes)
    xn = np.arange(uq.N) * uq.DX

    # close the periodic domain for drawing
    def wrap_x(x):
        return np.append(x, 1.0)

    def wrap(v):
        return np.append(v, v[0])

    fig, axes = plt.subplots(2, 2, figsize=(12.6, 8.0), sharex=True,
                             sharey=True)
    fig.patch.set_facecolor(SURFACE)

    for ax, dev in zip(axes.ravel(), DEVS):
        ax.set_facecolor(SURFACE)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        for side in ("left", "bottom"):
            ax.spines[side].set_color(GRID)
        ax.tick_params(colors=TEXT_2, labelsize=9, length=3, color=GRID)
        ax.axhline(0.0, color=GRID, lw=1.0, zorder=1)
        ax.yaxis.grid(True, color=GRID, lw=0.8)
        ax.set_axisbelow(True)

        first = dev == DEVS[0]

        # --- FTCS-800 reference (the sine) ---------------------------------
        ax.plot(np.append(x_ref, 1.0), np.append(truth_fine, truth_fine[0]),
                color=MUTED, lw=1.7, ls=(0, (5, 2)), zorder=3,
                label="FTCS-800 reference (the sine)" if first else None)

        # --- noiseless statevector ceiling ---------------------------------
        sv = sim["sv"]["u"]
        ax.plot(wrap_x(xn), wrap(sv), color=AQUA, lw=1.8,
                ls=(0, (1, 1.6)), marker="s", ms=5.0,
                markeredgecolor=SURFACE, markeredgewidth=1.2, zorder=4,
                label="noiseless sim ceiling" if first else None)

        # --- September shadow ---------------------------------------------
        S = sept_profiles(dev)
        if S.size:
            m = S.mean(0)
            if S.shape[0] > 1:
                sd = S.std(0, ddof=1)
                ax.fill_between(wrap_x(xn), wrap(S.min(0)), wrap(S.max(0)),
                                color=BLUE_FAINT, zorder=2, lw=0,
                                label="Sept min-max" if first else None)
                ax.fill_between(wrap_x(xn), wrap(m - sd), wrap(m + sd),
                                color=BLUE_BAND, alpha=0.85, zorder=2, lw=0,
                                label="Sept $\\pm$1 sd (run-to-run)"
                                if first else None)
            ax.plot(wrap_x(xn), wrap(m), color=BLUE, lw=2.0, marker="o",
                    ms=6.5, markeredgecolor=SURFACE, markeredgewidth=1.4,
                    zorder=6,
                    label=f"September mean" if first else None)

        # --- June n=1 ------------------------------------------------------
        ju = june_profile(dev)
        if ju is not None:
            ax.plot(wrap_x(xn), wrap(ju), color=ORANGE, lw=2.0, marker="D",
                    ms=6.0, markeredgecolor=SURFACE, markeredgewidth=1.4,
                    zorder=5, label="June n=1" if first else None)

        # --- per-panel numbers --------------------------------------------
        bits = []
        if ju is not None:
            g, c = uq.gc_of(ju, truth_nodes)
            bits.append(f"June  relL2 {uq.rel_l2(ju, truth_nodes):.3f}"
                        f"   cos {c:.3f}")
        if S.size:
            l2 = np.array([uq.rel_l2(u, truth_nodes) for u in S])
            cs = np.array([uq.gc_of(u, truth_nodes)[1] for u in S])
            bits.append(f"Sept  relL2 {l2.mean():.3f}"
                        f"{'' if S.shape[0] < 2 else f' ± {l2.std(ddof=1):.3f}'}"
                        f"   cos {cs.mean():.3f}   n={S.shape[0]}")
        else:
            bits.append("Sept  no data (IBM usage limit)")
        ax.set_title(dev, color=TEXT_1, fontsize=12, loc="left", pad=8,
                     fontweight="bold")
        # the annotation lives in reserved space BELOW the data (ylim floor is
        # set clear of the deepest trace) so it can never occlude a line
        ax.text(0.985, 0.018, "\n".join(bits), transform=ax.transAxes,
                ha="right", va="bottom", fontsize=8.6, color=TEXT_2,
                family="monospace",
                bbox=dict(facecolor=SURFACE, edgecolor=GRID, lw=0.8,
                          boxstyle="round,pad=0.35"))

        # direct label for the sub-3:1 aqua series (relief rule)
        if first:
            ax.annotate("noiseless", (xn[2], sv[2]),
                        textcoords="offset points", xytext=(4, 9),
                        fontsize=8.2, color=AQUA, fontweight="bold")

    for ax in axes[1]:
        ax.set_xlabel("$x$  (periodic domain)", color=TEXT_2, fontsize=10)
    for ax in axes[:, 0]:
        ax.set_ylabel("$u(x)$ after segment 1  ($T=0.0375$)",
                      color=TEXT_2, fontsize=10)
    axes[0, 0].set_xlim(0, 1)
    axes[0, 0].set_xticks(np.arange(0, 1.01, 0.125))
    # deepest trace is fez June at -0.338; floor at -0.56 reserves a clear
    # band for the per-panel stats box
    axes[0, 0].set_ylim(-0.56, 0.43)

    h, l = axes[0, 0].get_legend_handles_labels()
    leg = fig.legend(h, l, loc="lower center", ncol=6, frameon=False,
                     fontsize=9, bbox_to_anchor=(0.5, 0.035),
                     handletextpad=0.6, columnspacing=1.6)
    for t in leg.get_texts():
        t.set_color(TEXT_2)

    fig.suptitle("First segment: the recovered velocity profile, June vs "
                 "September\nthe September run-to-run shadow is tight -- but "
                 "neither epoch tracks the sine",
                 color=TEXT_1, fontsize=13, x=0.008, ha="left")
    fig.text(0.008, 0.005,
             "Cole-Hopf circuit, q=3 (8 nodes), nu=0.08, A=0.3, cfl=0.3, "
             "150000 shots, TREX+DD, opt-3.   Sept sweep _0ca9db0f "
             "(2026-09-10); June hardware_runs (2026-06-15).   "
             "relL2 / cos are vs the FTCS-800 reference at the 8 q-nodes.",
             color=TEXT_3, fontsize=7.8)
    fig.subplots_adjust(left=0.062, right=0.99, top=0.878, bottom=0.135,
                        wspace=0.08, hspace=0.20)
    fig.savefig(OUT, dpi=170, facecolor=SURFACE)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
