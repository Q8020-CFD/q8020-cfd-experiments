#!/usr/bin/env python3
"""One figure PER DEVICE: the segment-1 u(x) profile, June line vs September band.

Same data as profiles_segment1.png (the 2x2 small-multiple), but split into a
full-size panel per device and stripped to the three series that answer "is the
June sine inside the September run-to-run spread?":

  * FTCS-800 reference  -- the sine the run is scored against (grey dashed),
  * June 2026, n=1      -- Melvina's single hardware profile (orange),
  * September 2026 mean -- with its run-to-run shadow: +/-1 sd, plus a fainter
    min-max envelope (blue).

Frame 1 = end of segment 1, T = 0.0375 (the paper-comparable single-step point).
Writes profile_segment1_<device>.png into the campaign's analysis/ dir.
Palette and mark specs are lifted verbatim from
plot_smooth_movie_profiles_segment1.py so every figure in the campaign agrees.

Run with the tooling venv python (~/.venvs/tooling/bin/python).
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

# --- validated palette (light mode; same slots as the 2x2 figure) ------------
SURFACE = "#fcfcfb"
TEXT_1, TEXT_2, TEXT_3 = "#0b0b0b", "#52514e", "#84837c"
MUTED = "#898781"
BLUE, ORANGE = "#2a78d6", "#eb6834"
BLUE_BAND, BLUE_FAINT = "#86b6ef", "#cde2fb"
GRID = "#e4e3df"

DEVS = ("kingston", "fez", "miami")
ANALYSIS = os.path.join(
    uq.REPO, "q8020-cfd-experiments", "results", "burgers-ch-lbm",
    "ch_smooth_movie_rerun", "analysis")
SEPT_ROOT = os.path.join(
    uq.REPO, "q8020-cfd-experiments", "results", "burgers-ch-lbm",
    "ch_smooth_movie_rerun", "2026-09-10", "_0ca9db0f")
JUNE_ROOT = os.path.join(
    uq.REPO, "q8020-cfd-experiments", "results", "burgers-ch-lbm-June2026",
    "real-qc", "hardware_runs")


def sept_profiles(dev: str) -> np.ndarray:
    """September frame-1 node profiles for a device, shape (n_trials, 8)."""
    out = []
    for td in sorted(glob.glob(os.path.join(SEPT_ROOT, dev, "trial_*"))):
        mp = glob.glob(os.path.join(td, "q8020_metadata_*.json"))
        if not mp:
            continue
        fr = uq.frames_of(mp[0])
        if fr and uq.FRAME in fr and np.all(np.isfinite(fr[uq.FRAME])):
            out.append(fr[uq.FRAME])
    return np.array(out) if out else np.empty((0, uq.N))


def june_profile(dev: str) -> np.ndarray | None:
    fr = uq.frames_of(os.path.join(
        JUNE_ROOT, f"smooth_movie_{dev}", "method_compare",
        "cole_hopf_circuit", "q8020_artifacts_0.json"))
    return fr[uq.FRAME] if fr and uq.FRAME in fr else None


def wrap_x(x):
    """Close the periodic domain for drawing: x -> x + [1.0]."""
    return np.append(x, 1.0)


def wrap(v):
    """Close the periodic domain for drawing: v -> v + [v[0]]."""
    return np.append(v, v[0])


def render(dev: str) -> str:
    truth_nodes = uq.ftcs800_truth_frames()[uq.FRAME]
    x_ref, fine = ftcs800_full_frames()
    truth_fine = fine[uq.FRAME]
    xn = np.arange(uq.N) * uq.DX
    S = sept_profiles(dev)
    ju = june_profile(dev)

    fig, ax = plt.subplots(figsize=(9.8, 5.6), dpi=170)
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)
    ax.tick_params(colors=TEXT_2, labelsize=9, length=3, color=GRID)
    ax.axhline(0.0, color=GRID, lw=1.0, zorder=1)
    ax.yaxis.grid(True, color=GRID, lw=0.8)
    ax.set_axisbelow(True)

    # --- the sine being scored against ---------------------------------------
    ax.plot(np.append(x_ref, 1.0), np.append(truth_fine, truth_fine[0]),
            color=MUTED, lw=1.7, ls=(0, (5, 2)), zorder=3,
            label="FTCS-800 reference (the sine)")

    # --- September: min-max envelope, +/-1 sd shadow, mean line --------------
    n_s = S.shape[0]
    if n_s:
        m = S.mean(0)
        if n_s > 1:
            sd = S.std(0, ddof=1)
            ax.fill_between(wrap_x(xn), wrap(S.min(0)), wrap(S.max(0)),
                            color=BLUE_FAINT, lw=0, zorder=2,
                            label="Sept min-max")
            ax.fill_between(wrap_x(xn), wrap(m - sd), wrap(m + sd),
                            color=BLUE_BAND, alpha=0.85, lw=0, zorder=2,
                            label="Sept $\\pm$1 sd (run-to-run)")
        ax.plot(wrap_x(xn), wrap(m), color=BLUE, lw=2.2, marker="o", ms=6.5,
                markeredgecolor=SURFACE, markeredgewidth=1.4, zorder=6,
                label=f"September 2026 mean (n={n_s})")

    # --- June single run -----------------------------------------------------
    if ju is not None:
        ax.plot(wrap_x(xn), wrap(ju), color=ORANGE, lw=2.2, marker="D", ms=6.0,
                markeredgecolor=SURFACE, markeredgewidth=1.4, zorder=5,
                label="June 2026 (n=1)")

    # --- headline numbers, as a subtitle (never occludes the data) -----------
    bits = []
    if ju is not None:
        _, c = uq.gc_of(ju, truth_nodes)
        bits.append(f"June  relL2 {uq.rel_l2(ju, truth_nodes):.3f}  cos {c:.3f}")
    if n_s:
        l2 = np.array([uq.rel_l2(u, truth_nodes) for u in S])
        cs = np.array([uq.gc_of(u, truth_nodes)[1] for u in S])
        sdtxt = f" $\\pm$ {l2.std(ddof=1):.3f}" if n_s > 1 else ""
        bits.append(f"Sept  relL2 {l2.mean():.3f}{sdtxt}  "
                    f"cos {cs.mean():.3f}  (n={n_s})")
    ax.set_title(f"{dev} - velocity profile after segment 1  ($T = 0.0375$)",
                 color=TEXT_1, fontsize=13, loc="left", pad=26,
                 fontweight="bold")
    ax.text(0.0, 1.028, "     ".join(bits), transform=ax.transAxes,
            ha="left", va="bottom", fontsize=9.5, color=TEXT_2,
            family="monospace")

    ax.set_xlim(0, 1)
    ax.set_xticks(np.arange(0, 1.01, 0.125))
    lo = min([truth_fine.min(), ju.min() if ju is not None else 0.0]
             + ([S.min()] if n_s else []))
    hi = max([truth_fine.max(), ju.max() if ju is not None else 0.0]
             + ([S.max()] if n_s else []))
    pad = 0.16 * (hi - lo)
    ax.set_ylim(lo - pad, hi + pad)
    ax.set_xlabel("$x$  (periodic domain, 8 q-nodes)", color=TEXT_2,
                  fontsize=10)
    ax.set_ylabel("$u(x)$  after segment 1", color=TEXT_2, fontsize=10)

    leg = ax.legend(loc="upper center", ncol=3, frameon=False, fontsize=8.8,
                    bbox_to_anchor=(0.5, -0.135), handletextpad=0.6,
                    columnspacing=1.8)
    for t in leg.get_texts():
        t.set_color(TEXT_2)

    fig.text(0.008, 0.036,
             "Cole-Hopf circuit, q=3 (8 nodes), nu=0.08, A=0.3, cfl=0.3, "
             "150000 shots, TREX+DD, opt-3.   relL2 / cos are vs the FTCS-800 "
             "reference at the 8 q-nodes.",
             color=TEXT_3, fontsize=7.6)
    fig.text(0.008, 0.012,
             "September sweep _0ca9db0f (2026-09-10, one trial per QPU job "
             "series); June hardware_runs (2026-06-15, single run).",
             color=TEXT_3, fontsize=7.6)
    fig.subplots_adjust(left=0.075, right=0.985, top=0.855, bottom=0.295)
    out = os.path.join(ANALYSIS, f"profile_segment1_{dev}.png")
    fig.savefig(out, facecolor=SURFACE)
    plt.close(fig)
    return out


if __name__ == "__main__":
    for d in DEVS:
        print("wrote", render(d))
