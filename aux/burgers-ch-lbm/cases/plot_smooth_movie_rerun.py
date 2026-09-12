#!/usr/bin/env python3
"""relL2-vs-t figures for the ch_smooth_movie_rerun HW sweep.

Emits three PNGs into <results>/ch_smooth_movie_rerun/analysis/, all sharing
one style (validated categorical palette, lighter mean line over a darker
+/-1 std band, direct end-labels, FTCS-800 footnote):

  relL2_vs_t_september.png           Sep-2026 rerun, kingston/fez/miami
  relL2_vs_t_september_no_miami.png  same, miami dropped
  relL2_vs_t_june.png                June-2026 single run,
                                     kingston/fez/miami/boston (no bands --
                                     one run per device, so no trial spread)
  relL2_vs_t_all.png                 June (dashed) over September (solid +
                                     band); colour = device, style = era

Each curve is per-frame relL2 vs an 800-point FTCS reference. x-axis is
physical time t = frame*dt (dt = cfl*dx = 0.3/8 = 0.0375), frames 1..6 =>
t 0.0375..0.225 (= T_end); frame 0 is the IC (relL2 == 0), omitted. Truth +
frame extraction reuse score_smooth_movie_rerun.py.

Run with the ch-lbm venv python.
"""
from __future__ import annotations
import glob, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

from score_smooth_movie_rerun import (
    REPO, N_STEPS, DT, ftcs800_truth_frames, frames_of, rel_l2,
)

# --- validated categorical palette (dataviz skill, light surface) -----------
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK2 = "#52514e"
GRID = "#e6e5e1"
# device -> (colour, marker, end-label y-nudge in pts to de-collide close lines)
# colour follows the entity across every figure (fixed categorical order).
STYLE = {
    "kingston": ("#2a78d6", "o", -9),   # slot 1 blue   Heron R2
    "fez":      ("#eb6834", "s", +9),   # slot 2 orange Heron R2
    "miami":    ("#1baf7a", "^",  0),   # slot 3 aqua   Nighthawk R1
    "boston":   ("#eda100", "D",  0),   # slot 4 yellow Heron R3 (June only)
}


def devs(names):
    """(name, colour, marker, dy) tuples for the given device names."""
    return [(n, *STYLE[n]) for n in names]


# line = lighter tint of the hue (recessive connector); band = full hue at a
# higher alpha (darker fill) -- so the +/-1 std spread reads clearly.
LINE_LIGHTEN = 0.1        # fraction toward white for the mean line
BAND_ALPHA = 0.32         # band opacity (was 0.16)

FOOTNOTE = ("error = relative L2 between the 8-node quantum solution and a "
            "fine 800-point FTCS reference sampled to those same 8 nodes "
            "(paper's 'FTCS 800')")


def lighten(hexcol, f):
    """Mix a hex colour f of the way toward white; returns an (r,g,b) tuple."""
    r = int(hexcol[1:3], 16); g = int(hexcol[3:5], 16); b = int(hexcol[5:7], 16)
    mix = lambda c: (c + (255 - c) * f) / 255.0
    return (mix(r), mix(g), mix(b))


NEW_ROOT = os.path.join(
    REPO, "q8020-cfd-experiments", "results", "burgers-ch-lbm",
    "ch_smooth_movie_rerun", "2026-09-10", "_0ca9db0f")
JUNE_ROOT = os.path.join(
    REPO, "q8020-cfd-experiments", "results", "burgers-ch-lbm-June2026",
    "real-qc", "hardware_runs")
OUT_DIR = os.path.join(
    REPO, "q8020-cfd-experiments", "results", "burgers-ch-lbm",
    "ch_smooth_movie_rerun", "analysis")


def new_run_stats(dev, truth):
    """relL2 per frame across successful trials; (t, mean, std, n).

    std = population standard deviation of the trials (the spread), NOT the
    std error of the mean -- so miami's n=3 band reflects its (tight) actual
    scatter, not the lower confidence in that scatter from few trials."""
    by_frame = {k: [] for k in range(1, N_STEPS + 1)}
    n_tr = 0
    for tdir in sorted(glob.glob(os.path.join(NEW_ROOT, dev, "trial_*"))):
        mp = glob.glob(os.path.join(tdir, "q8020_metadata_*.json"))
        if not mp:
            continue
        fr = frames_of(mp[0])
        if not fr:
            continue
        n_tr += 1
        for k in range(1, N_STEPS + 1):
            if k in fr and np.all(np.isfinite(fr[k])):
                by_frame[k].append(rel_l2(fr[k], truth[k]))
    ks = [k for k in range(1, N_STEPS + 1) if by_frame[k]]
    t = np.array([k * DT for k in ks])
    mean = np.array([np.mean(by_frame[k]) for k in ks])
    std = np.array([np.std(by_frame[k]) for k in ks])
    return t, mean, std, n_tr


def june_curve(dev, truth):
    """Melvina's June-2026 single run: relL2 per frame; (t, relL2)."""
    ap = os.path.join(JUNE_ROOT, f"smooth_movie_{dev}", "method_compare",
                      "cole_hopf_circuit", "q8020_artifacts_0.json")
    fr = frames_of(ap)
    if not fr:
        return np.array([]), np.array([])
    ks = [k for k in range(1, N_STEPS + 1) if k in fr]
    t = np.array([k * DT for k in ks])
    r = np.array([rel_l2(fr[k], truth[k]) for k in ks])
    return t, r


def _new_fig():
    """Blank styled axes with the relL2=1 reference line."""
    fig, ax = plt.subplots(figsize=(9.0, 5.6), dpi=150)
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)
    # relL2 = 1 reference: output no closer to truth than truth's own norm
    # (attenuation-dominated NISQ output collapses toward this line).
    ax.axhline(1.0, color=GRID, lw=1.2, ls=(0, (1, 3)), zorder=1)
    ax.text(0.226, 1.0, " relL2 = 1", color=INK2, fontsize=8,
            va="center", ha="left")
    return fig, ax


def _finish(fig, ax, ymax, title, legend_handles, out_name):
    """Shared frame cosmetics, legend, footnote, and save."""
    ax.set_xlim(0.028, 0.283)
    ax.set_ylim(0.0, ymax * 1.08)
    ax.set_xticks([k * DT for k in range(1, N_STEPS + 1)])
    ax.set_xticklabels([f"{k*DT:.4f}" for k in range(1, N_STEPS + 1)],
                       fontsize=9)
    ax.set_xlabel("time  t", color=INK2, fontsize=10)
    ax.set_ylabel("relative L2 error", color=INK2, fontsize=10)
    ax.set_title(title, color=INK, fontsize=13, loc="left", pad=10)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(GRID)
    ax.tick_params(colors=INK2, labelsize=8)
    ax.grid(axis="y", color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    ax.legend(handles=legend_handles, loc="upper left", frameon=False,
              fontsize=9, handlelength=2.6, borderaxespad=0.6)
    fig.text(0.008, 0.008, FOOTNOTE, color=INK2, fontsize=7.5,
             ha="left", va="bottom")
    os.makedirs(OUT_DIR, exist_ok=True)
    out = os.path.join(OUT_DIR, out_name)
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(out, facecolor=SURFACE, bbox_inches="tight")
    print("wrote", out)


def render_new(devices, out_name, title):
    """Sep-2026 rerun: trial-mean line + shaded +/-1 std band per device."""
    truth = ftcs800_truth_frames()
    fig, ax = _new_fig()
    ymax = 0.0
    for dev, col, mk, dy in devices:
        tn, mn, sd, n = new_run_stats(dev, truth)
        if not tn.size:
            continue
        light = lighten(col, LINE_LIGHTEN)
        # darker +/-1 std band (full hue) under a lighter mean line; markers
        # and end-label keep the full saturated hue so identity stays crisp.
        ax.fill_between(tn, mn - sd, mn + sd, color=col, alpha=BAND_ALPHA,
                        lw=0, zorder=2)
        ax.plot(tn, mn, color=light, lw=2.2, marker=mk, ms=1,
                mfc=col, mec=SURFACE, mew=1.0, zorder=4)
        ax.annotate(f"{dev} (n={n})", xy=(tn[-1], mn[-1]), xytext=(6, dy),
                    textcoords="offset points", color=col, fontsize=10,
                    fontweight="bold", va="center", ha="left")
        ymax = max(ymax, (mn + sd).max())
    enc = [
        Line2D([0], [0], color=lighten(INK2, LINE_LIGHTEN), lw=2.2, ls="-",
               marker="o", mfc=INK2, mec=SURFACE, label="trial mean"),
        Patch(facecolor=INK2, alpha=BAND_ALPHA, edgecolor="none",
              label="+/- 1 std  (trial spread)"),
    ]
    _finish(fig, ax, ymax, title, enc, out_name)


def render_june(devices, out_name, title):
    """Melvina's June-2026 single run: one line per device, no bands."""
    truth = ftcs800_truth_frames()
    fig, ax = _new_fig()
    ymax = 0.0
    for dev, col, mk, dy in devices:
        t, y = june_curve(dev, truth)
        if not t.size:
            continue
        light = lighten(col, LINE_LIGHTEN)
        ax.plot(t, y, color=light, lw=2.2, marker=mk, ms=1,
                mfc=col, mec=SURFACE, mew=1.0, zorder=4)
        ax.annotate(dev, xy=(t[-1], y[-1]), xytext=(6, dy),
                    textcoords="offset points", color=col, fontsize=10,
                    fontweight="bold", va="center", ha="left")
        ymax = max(ymax, y.max())
    enc = [
        Line2D([0], [0], color=lighten(INK2, LINE_LIGHTEN), lw=2.2, ls="-",
               marker="o", mfc=INK2, mec=SURFACE,
               label="single run (June 2026)"),
    ]
    _finish(fig, ax, ymax, title, enc, out_name)


JUNE_DASH = (0, (5, 2))    # June single-run line style (era cue, not colour)


def render_overlay(out_name, title):
    """Both eras on one axis: colour = device, line style = era.

    September rerun -> solid line + shaded +/-1 std band (kingston/fez/miami).
    June single run -> dashed line, no band (kingston/fez/miami + boston,
    which has no September counterpart).  Device identity is the hue, carried
    by direct end-labels on the September lines (and boston's June line); the
    legend distinguishes the two eras."""
    truth = ftcs800_truth_frames()
    fig, ax = _new_fig()
    ymax = 0.0
    # September: solid mean + darker band, direct-labelled per device.
    for dev, col, mk, dy in devs(["kingston", "fez", "miami"]):
        tn, mn, sd, n = new_run_stats(dev, truth)
        if not tn.size:
            continue
        ax.fill_between(tn, mn - sd, mn + sd, color=col, alpha=BAND_ALPHA,
                        lw=0, zorder=2)
        ax.plot(tn, mn, color=lighten(col, LINE_LIGHTEN), lw=2.2, ls="-",
                marker=mk, ms=1, mfc=col, mec=SURFACE, mew=1.0, zorder=5)
        ax.annotate(dev, xy=(tn[-1], mn[-1]), xytext=(6, dy),
                    textcoords="offset points", color=col, fontsize=10,
                    fontweight="bold", va="center", ha="left")
        ymax = max(ymax, (mn + sd).max())
    # June: dashed, no band; boston is June-only so it gets its own label.
    for dev, col, mk, dy in devs(["kingston", "fez", "miami", "boston"]):
        t, y = june_curve(dev, truth)
        if not t.size:
            continue
        ax.plot(t, y, color=lighten(col, LINE_LIGHTEN), lw=1.8, ls=JUNE_DASH,
                marker=mk, ms=1, mfc=col, mec=SURFACE, mew=1.0, zorder=4)
        if dev == "boston":
            ax.annotate("boston (June only)", xy=(t[-1], y[-1]), xytext=(6, 0),
                        textcoords="offset points", color=col, fontsize=10,
                        fontweight="bold", va="center", ha="left")
        ymax = max(ymax, y.max())
    enc = [
        Line2D([0], [0], color=lighten(INK2, LINE_LIGHTEN), lw=2.2, ls="-",
               label="September 2026  (mean +/- 1 std)"),
        Line2D([0], [0], color=lighten(INK2, LINE_LIGHTEN), lw=1.8,
               ls=JUNE_DASH, label="June 2026  (single run)"),
    ]
    _finish(fig, ax, ymax, title, enc, out_name)


def main():
    render_new(devs(["kingston", "fez", "miami"]),
               "relL2_vs_t_september.png",
               "Cole-Hopf HW movie: error growth over time (September 2026)")
    render_new(devs(["kingston", "fez"]),
               "relL2_vs_t_september_no_miami.png",
               "Cole-Hopf HW movie: error growth over time (September 2026)")
    render_june(devs(["kingston", "fez", "miami", "boston"]),
                "relL2_vs_t_june.png",
                "Cole-Hopf HW movie: error growth over time (June 2026)")
    render_overlay("relL2_vs_t_all.png",
                   "Cole-Hopf HW movie: error growth over time "
                   "(June vs September 2026)")


if __name__ == "__main__":
    main()
