#!/usr/bin/env python3
"""Make the September run-to-run UQ actually visible at segment 1.

The per-device profile figure (plot_smooth_movie_profile_per_device.py) is
honest but the shadow is ~1% of the y-range: per-node sd is 5-11e-3 against a
u(x) span of ~0.7, so the band is a couple of pixels wide.  Two views fix that:

  1. uq_detail_segment1_<dev>.png -- 2 rows sharing x.  Top: the profile as
     before.  Bottom: the SAME data replotted as deviation from the September
     mean, at its own 1e-3 scale, with every trial drawn individually.  The
     June run is drawn there too; where it leaves the panel, edge triangles
     mark how far outside the run-to-run band it sits.
  2. uq_relL2_segment1_strip.png -- the scalar that goes in a paper table:
     frame-1 relL2, one dot per trial, with the +/-1 sd bar, the 95% CI on the
     mean, the 95% prediction interval for a single re-run, and June's n=1
     value on the same axis.  This is the view that answers "is June inside
     the September band?" (it is not, on any device).

Reuses the loaders/truth from uq_smooth_movie_segment1 and the profile helpers
from plot_smooth_movie_profile_per_device so nothing can disagree numerically.
Run with the tooling venv python (~/.venvs/tooling/bin/python).
"""
from __future__ import annotations

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats

import uq_smooth_movie_segment1 as uq
from score_smooth_movie_rerun import ftcs800_full_frames
from plot_smooth_movie_profile_per_device import (
    ANALYSIS, BLUE, BLUE_BAND, BLUE_FAINT, DEVS, GRID, MUTED, ORANGE, SURFACE,
    TEXT_1, TEXT_2, TEXT_3, june_profile, sept_profiles, wrap, wrap_x,
)


def style(ax):
    ax.set_facecolor(SURFACE)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)
    ax.tick_params(colors=TEXT_2, labelsize=9, length=3, color=GRID)
    ax.yaxis.grid(True, color=GRID, lw=0.8)
    ax.set_axisbelow(True)


# =========================================================== per-device 2-row ===
def render_detail(dev: str) -> str:
    truth_nodes = uq.ftcs800_truth_frames()[uq.FRAME]
    x_ref, fine = ftcs800_full_frames()
    truth_fine = fine[uq.FRAME]
    xn = np.arange(uq.N) * uq.DX
    S = sept_profiles(dev)
    ju = june_profile(dev)
    n_s, m = S.shape[0], S.mean(0)
    sd = S.std(0, ddof=1)

    fig, (ax, bx) = plt.subplots(
        2, 1, figsize=(9.8, 7.8), dpi=170, sharex=True,
        gridspec_kw=dict(height_ratios=[2.25, 1.0], hspace=0.13))
    fig.patch.set_facecolor(SURFACE)
    for a in (ax, bx):
        style(a)

    # --- top: the profile (unchanged content) --------------------------------
    ax.axhline(0.0, color=GRID, lw=1.0, zorder=1)
    ax.plot(np.append(x_ref, 1.0), np.append(truth_fine, truth_fine[0]),
            color=MUTED, lw=1.7, ls=(0, (5, 2)), zorder=3,
            label="FTCS-800 reference (the sine)")
    ax.fill_between(wrap_x(xn), wrap(S.min(0)), wrap(S.max(0)),
                    color=BLUE_FAINT, lw=0, zorder=2, label="Sept min-max")
    ax.fill_between(wrap_x(xn), wrap(m - sd), wrap(m + sd), color=BLUE_BAND,
                    alpha=0.85, lw=0, zorder=2,
                    label="Sept $\\pm$1 sd (run-to-run)")
    ax.plot(wrap_x(xn), wrap(m), color=BLUE, lw=2.2, marker="o", ms=6.5,
            markeredgecolor=SURFACE, markeredgewidth=1.4, zorder=6,
            label=f"September 2026 mean (n={n_s})")
    ax.plot(wrap_x(xn), wrap(ju), color=ORANGE, lw=2.2, marker="D", ms=6.0,
            markeredgecolor=SURFACE, markeredgewidth=1.4, zorder=5,
            label="June 2026 (n=1)")
    ax.set_ylabel("$u(x)$  after segment 1", color=TEXT_2, fontsize=10)

    _, cj = uq.gc_of(ju, truth_nodes)
    l2 = np.array([uq.rel_l2(u, truth_nodes) for u in S])
    cs = np.array([uq.gc_of(u, truth_nodes)[1] for u in S])
    ax.set_title(f"{dev} - segment 1: the profile, and the run-to-run spread "
                 f"at its own scale",
                 color=TEXT_1, fontsize=12.5, loc="left", pad=26,
                 fontweight="bold")
    ax.text(0.0, 1.030,
            f"June  relL2 {uq.rel_l2(ju, truth_nodes):.3f}  cos {cj:.3f}"
            f"     Sept  relL2 {l2.mean():.3f} $\\pm$ {l2.std(ddof=1):.3f}  "
            f"cos {cs.mean():.3f}  (n={n_s})",
            transform=ax.transAxes, ha="left", va="bottom", fontsize=9.5,
            color=TEXT_2, family="monospace")

    # --- bottom: deviation from the September mean, in 1e-3 ------------------
    K = 1e3
    bx.axhline(0.0, color=BLUE, lw=1.1, zorder=4)
    bx.fill_between(wrap_x(xn), wrap(S.min(0) - m) * K, wrap(S.max(0) - m) * K,
                    color=BLUE_FAINT, lw=0, zorder=2)
    bx.fill_between(wrap_x(xn), wrap(-sd) * K, wrap(sd) * K, color=BLUE_BAND,
                    alpha=0.85, lw=0, zorder=2)
    for i, u in enumerate(S):
        bx.plot(wrap_x(xn), wrap(u - m) * K, color=BLUE, lw=0.95, alpha=0.55,
                zorder=3,
                label="individual September trials" if i == 0 else None)

    half = 1.55 * np.abs(np.concatenate([S.min(0) - m, S.max(0) - m])).max() * K
    bx.set_ylim(-half, half)
    # June, drawn as MARKERS only (a connecting line would streak across the
    # panel at this zoom); nodes beyond the panel get an edge triangle instead
    jr = (ju - m) * K
    inside = np.abs(jr) <= half
    if inside.any():
        bx.plot(xn[inside], jr[inside], ls="none", marker="D", ms=6.4,
                color=ORANGE, markeredgecolor=SURFACE, markeredgewidth=1.2,
                zorder=5, label="June 2026 (n=1);  $\\vartriangle$ = off scale")
    for x0, v in zip(xn, jr):
        if abs(v) > half:
            bx.plot([x0], [np.sign(v) * half * 0.76], marker="^" if v > 0
                    else "v", ms=9.0, color=ORANGE, clip_on=False, zorder=7)
    off = np.abs(ju - m) / sd
    bx.set_ylabel("deviation from Sept mean\n($\\times 10^{-3}$)",
                  color=TEXT_2, fontsize=9.5)
    bx.set_xlabel("$x$  (periodic domain, 8 q-nodes)", color=TEXT_2,
                  fontsize=10)
    bx.set_xlim(0, 1)
    bx.set_xticks(np.arange(0, 1.01, 0.125))
    bx.text(0.006, 0.965, f"per-node sd {sd.min()*K:.1f}-{sd.max()*K:.1f}"
            f"$\\times 10^{{-3}}$  (~{100*sd.max()/np.abs(m).max():.0f}% of "
            f"peak $|u|$)", transform=bx.transAxes, ha="left", va="top",
            fontsize=8.4, color=TEXT_2, family="monospace")
    bx.text(0.994, 0.965,
            f"June is {off.min():.1f}-{off.max():.0f} sd off the Sept mean "
            f"(median {np.median(off):.0f} sd)",
            transform=bx.transAxes, ha="right", va="top", fontsize=8.4,
            color=ORANGE, family="monospace")

    h1, l1 = ax.get_legend_handles_labels()
    h2, l2_ = bx.get_legend_handles_labels()
    leg = fig.legend(h1 + h2, l1 + l2_, loc="lower center", ncol=4,
                     frameon=False, fontsize=8.6, bbox_to_anchor=(0.5, 0.045),
                     handletextpad=0.6, columnspacing=1.5)
    for t in leg.get_texts():
        t.set_color(TEXT_2)

    fig.text(0.008, 0.026,
             "Cole-Hopf circuit, q=3 (8 nodes), nu=0.08, A=0.3, cfl=0.3, "
             "150000 shots, TREX+DD, opt-3.   Lower panel is the SAME data as "
             "the upper band, rescaled ~50x.",
             color=TEXT_3, fontsize=7.6)
    fig.text(0.008, 0.008,
             "September sweep _0ca9db0f (2026-09-10); June hardware_runs "
             "(2026-06-15).   Run-to-run scatter here is at or below the "
             "150000-shot sampling floor (uq_segment1_report.txt §4).",
             color=TEXT_3, fontsize=7.6)
    fig.subplots_adjust(left=0.088, right=0.985, top=0.888, bottom=0.185)
    out = os.path.join(ANALYSIS, f"uq_detail_segment1_{dev}.png")
    fig.savefig(out, facecolor=SURFACE)
    plt.close(fig)
    return out


# ============================================================= scalar strip ===
def render_strip() -> str:
    truth_nodes = uq.ftcs800_truth_frames()[uq.FRAME]
    fig, ax = plt.subplots(figsize=(9.8, 4.6), dpi=170)
    fig.patch.set_facecolor(SURFACE)
    style(ax)
    ax.yaxis.grid(False)
    ax.xaxis.grid(True, color=GRID, lw=0.8)
    rng = np.random.default_rng(7)

    rows = []
    for k, dev in enumerate(DEVS):
        y = len(DEVS) - 1 - k
        S = sept_profiles(dev)
        l2 = np.array([uq.rel_l2(u, truth_nodes) for u in S])
        ju = uq.rel_l2(june_profile(dev), truth_nodes)
        n, mu, s = len(l2), l2.mean(), l2.std(ddof=1)
        t = stats.t.ppf(0.975, n - 1)
        ci = t * s / np.sqrt(n)
        pi = t * s * np.sqrt(1 + 1 / n)
        first = k == 0

        ax.barh(y, 2 * pi, left=mu - pi, height=0.52, color=BLUE_FAINT,
                zorder=2, label="95% PI, a single re-run" if first else None)
        ax.barh(y, 2 * s, left=mu - s, height=0.52, color=BLUE_BAND,
                alpha=0.9, zorder=3,
                label="$\\pm$1 sd (run-to-run)" if first else None)
        ax.plot([mu - ci, mu + ci], [y, y], color=BLUE, lw=3.4,
                solid_capstyle="butt", zorder=5,
                label="95% CI on the mean" if first else None)
        ax.plot([mu, mu], [y - 0.26, y + 0.26], color=BLUE, lw=2.0, zorder=6)
        ax.plot(l2, y + rng.uniform(-0.15, 0.15, n), ls="none", marker="o",
                ms=6.0, color=BLUE, markeredgecolor=SURFACE,
                markeredgewidth=1.1, zorder=7,
                label="September trials" if first else None)
        ax.plot([ju], [y], ls="none", marker="D", ms=9.5, color=ORANGE,
                markeredgecolor=SURFACE, markeredgewidth=1.3, zorder=8,
                label="June 2026 (n=1)" if first else None)
        z = (ju - mu) / s
        ax.annotate(f"{z:+.1f} sd", (ju, y), textcoords="offset points",
                    xytext=(0, -21), ha="center", fontsize=8.6,
                    color=ORANGE, family="monospace")
        ax.text(mu, y + 0.34, f"{mu:.3f} $\\pm$ {s:.3f}", ha="center",
                va="bottom", fontsize=8.6, color=TEXT_2, family="monospace")
        rows.append((dev, n))

    ax.set_yticks(range(len(DEVS)))
    ax.set_yticklabels([f"{d}\nn={n}" for d, n in rows][::-1],
                       color=TEXT_1, fontsize=10.5, fontweight="bold")
    ax.set_ylim(-0.62, len(DEVS) - 0.30)
    ax.set_xlabel("relative $L_2$ error vs FTCS-800 at $T = 0.0375$ "
                  "(frame 1, lower is better)", color=TEXT_2, fontsize=10)
    ax.set_title("The UQ where it is actually resolvable: frame-1 relL2, "
                 "trial by trial",
                 color=TEXT_1, fontsize=12.5, loc="left", pad=24,
                 fontweight="bold")
    ax.text(0.0, 1.028,
            "run-to-run scatter is ~2% CV -- and every June n=1 value lands "
            "outside it, on all three devices",
            transform=ax.transAxes, ha="left", va="bottom", fontsize=9.5,
            color=TEXT_2)

    leg = ax.legend(loc="upper center", ncol=5, frameon=False, fontsize=8.8,
                    bbox_to_anchor=(0.5, -0.175), handletextpad=0.6,
                    columnspacing=1.6)
    for t in leg.get_texts():
        t.set_color(TEXT_2)
    fig.text(0.008, 0.012,
             "Cole-Hopf circuit, q=3, nu=0.08, A=0.3, cfl=0.3, 150000 shots, "
             "TREX+DD, opt-3.   Sept sweep _0ca9db0f; June hardware_runs.   "
             "PI/CI use Student t, dof = n-1.",
             color=TEXT_3, fontsize=7.6)
    fig.subplots_adjust(left=0.115, right=0.985, top=0.845, bottom=0.295)
    out = os.path.join(ANALYSIS, "uq_relL2_segment1_strip.png")
    fig.savefig(out, facecolor=SURFACE)
    plt.close(fig)
    return out


if __name__ == "__main__":
    for d in DEVS:
        print("wrote", render_detail(d))
    print("wrote", render_strip())
