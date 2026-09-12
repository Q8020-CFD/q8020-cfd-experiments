#!/usr/bin/env python3
"""Paper 'Figure CH-2' look, redrawn for the ch_smooth_movie sweeps.

Matches the u(x,t) panel produced by the June postproc
burgers-ch-lbm-June2026/postproc/plot_dataset_movie.py: the single-step
profile (frame 1, t=0.0375) in default matplotlib tab10 colours, markerless
lw-3 lines, a boxed 2-column upper-right legend, full axis box, grid alpha 0.3,
a modest non-bold title, title/labels at the paper's font sizes.

Emits three PNGs into <results>/ch_smooth_movie_rerun/analysis/:

  velocity_profile_september.png  Sep-2026 rerun (fez/kingston/miami), per-node
                                  MEAN over trials + shaded +/-1 std band;
                                  legend carries n.
  velocity_profile_june.png       June-2026 paper run (fez/kingston/boston/
                                  miami), SINGLE run per device, so no bands
                                  (nothing to average).
  velocity_profile_all.png        both eras on one axis: colour = device, line
                                  style = era (September solid + band, June
                                  dashed).

Frame 1 is what the reference figure actually shows (its ftcs_reference peaks
at ~0.27 = the June truth's step 1; step 6 has diffused down to ~0.15) and is
the paper-comparable single-step point.  The "n_steps=6" in the title is run
config, not the displayed frame, and is kept verbatim to match the reference.

Colours are pinned PER DEVICE to the paper figure's run order (fez=blue,
kingston=orange, boston=green, miami=red; ftcs=pink), so each entity keeps its
paper hue across both eras even where a series is missing.

Data differences from the June paper figure:
  * September ran HARDWARE ONLY -> no sim_ideal / sim_shots_150k baselines
    (June had them; not reproduced here).
  * ibm_boston produced no valid September trials -> omitted from that figure
    (it is present in the June figure, where it is green).
  * September lines are the MEAN over valid trials (kingston/fez n=10, miami
    n=3) with a shaded +/-1 std band; June is one run per device -> no band.

Run with the ch-lbm venv python.
"""
from __future__ import annotations
import glob, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from score_smooth_movie_rerun import ftcs800_truth_frames, frames_of, N
from plot_smooth_movie_rerun import OUT_DIR, NEW_ROOT, JUNE_ROOT, JUNE_DASH

FRAME = 1                       # single-step profile (t=0.0375); see docstring
XNODES = np.arange(N) / N       # periodic q-nodes [0, 1/8, .., 7/8]
TAB10 = plt.get_cmap("tab10")
# device -> tab10 index in the paper 'Figure CH-2' run order, so hues match it.
DEV_COLOR = {"fez": 0, "kingston": 1, "boston": 2, "miami": 3}
FTCS_COLOR = 6                  # pink, as in the paper figure
SEP_DEVICES = ["fez", "kingston", "miami"]            # boston: no valid Sep trials
JUNE_DEVICES = ["fez", "kingston", "boston", "miami"] # paper run order (all four)
BAND_ALPHA = 0.22               # +/-1 std band opacity (same hue as the device)
TITLE = "Figure CH-2:  q=3, nu=0.08, A=0.3, cfl=0.3, n_steps=6"
# y-scale per figure.  September's trial std is tiny (~0.008 in u) so a +/-0.6
# axis hides the bands; None = fit to the data so they stay visible.  June has
# no bands, so it reproduces the paper's fixed +/-0.6 exactly.  The overlay
# carries June's larger single-run swings, so it fits to the data too.
SEP_YLIM = None
JUNE_YLIM = 0.6
OVERLAY_YLIM = None
SEP_OUT = "velocity_profile_september.png"
JUNE_OUT = "velocity_profile_june.png"
OVERLAY_OUT = "velocity_profile_all.png"


# --- data extractors (frame-1 spatial profiles) -----------------------------
def new_run_profile(dev, frame):
    """Per-node u at `frame` across Sep trials; (mean[N], std[N], n_trials)."""
    cols = [[] for _ in range(N)]
    n_tr = 0
    for tdir in sorted(glob.glob(os.path.join(NEW_ROOT, dev, "trial_*"))):
        mp = glob.glob(os.path.join(tdir, "q8020_metadata_*.json"))
        if not mp:
            continue
        fr = frames_of(mp[0])
        if not fr or frame not in fr or not np.all(np.isfinite(fr[frame])):
            continue
        n_tr += 1
        for j in range(N):
            cols[j].append(fr[frame][j])
    if n_tr == 0:
        return None, None, 0
    mean = np.array([np.mean(c) for c in cols])
    std = np.array([np.std(c) for c in cols])
    return mean, std, n_tr


def june_profile(dev, frame):
    """June-2026 single-run u at `frame` on the 8 nodes, or None."""
    ap = os.path.join(JUNE_ROOT, f"smooth_movie_{dev}", "method_compare",
                      "cole_hopf_circuit", "q8020_artifacts_0.json")
    fr = frames_of(ap)
    if not fr or frame not in fr:
        return None
    return fr[frame]


# --- shared styling ---------------------------------------------------------
def _apply_rcparams():
    """Paper figure style (see plot_dataset_movie.py); modest non-bold title
    (~14pt) and ~15pt labels, matching the reference proportions."""
    plt.rcParams.update({
        "axes.titlesize": 14, "axes.titleweight": "normal",
        "axes.labelsize": 15, "xtick.labelsize": 13, "ytick.labelsize": 13,
        "legend.fontsize": 12, "lines.linewidth": 3.0, "lines.markersize": 0,
    })


def _finish(fig, ax, ymax, ylim, out_name, handles=None):
    """Shared axis cosmetics, boxed 2-col legend, title, and save.

    `handles` overrides the auto legend (the overlay needs a two-key legend:
    device colour + era line style); otherwise labels drive it."""
    ax.set_xlim(0.0, 1.0)
    ax.set_ylim(-ylim, ylim) if ylim else ax.set_ylim(-ymax * 1.15, ymax * 1.15)
    ax.set_xlabel("x")
    ax.set_ylabel("u(x, t)")
    ax.grid(True, alpha=0.3)
    leg_kw = dict(loc="upper right", ncol=2, handlelength=1.6,
                  columnspacing=1.0, handletextpad=0.5, borderaxespad=0.4)
    ax.legend(handles=handles, **leg_kw) if handles else ax.legend(**leg_kw)
    ax.set_title(TITLE, fontweight="normal")
    fig.tight_layout()
    os.makedirs(OUT_DIR, exist_ok=True)
    out = os.path.join(OUT_DIR, out_name)
    fig.savefig(out, dpi=150)
    print("wrote", out)


def _add_ftcs(ax):
    """Draw the FTCS-800 reference sampled to the 8 nodes; return its peak |u|."""
    truth = ftcs800_truth_frames()[FRAME]
    ax.plot(XNODES, truth, marker="", lw=3.0,
            color=TAB10(FTCS_COLOR), label="ftcs_reference")
    return np.abs(truth).max()


# --- figures ----------------------------------------------------------------
def render_september():
    """Sep-2026 rerun: trial-mean profile + shaded +/-1 std band, n in legend."""
    _apply_rcparams()
    fig, ax = plt.subplots(figsize=(9, 5.5))
    ymax = 0.0
    for dev in SEP_DEVICES:
        mean, std, n = new_run_profile(dev, FRAME)
        if n == 0:
            continue
        col = TAB10(DEV_COLOR[dev])
        ax.fill_between(XNODES, mean - std, mean + std, color=col,
                        alpha=BAND_ALPHA, lw=0, zorder=1)
        ax.plot(XNODES, mean, marker="", lw=3.0, color=col,
                label=f"ibm_{dev} (n={n})", zorder=3)
        ymax = max(ymax, np.abs(mean + std).max(), np.abs(mean - std).max())
    ymax = max(ymax, _add_ftcs(ax))
    _finish(fig, ax, ymax, SEP_YLIM, SEP_OUT)


def render_june():
    """June-2026 paper run: one single-run profile per device, no bands."""
    _apply_rcparams()
    fig, ax = plt.subplots(figsize=(9, 5.5))
    ymax = 0.0
    for dev in JUNE_DEVICES:
        u = june_profile(dev, FRAME)
        if u is None:
            continue
        col = TAB10(DEV_COLOR[dev])
        ax.plot(XNODES, u, marker="", lw=3.0, color=col,
                label=f"ibm_{dev}", zorder=3)
        ymax = max(ymax, np.abs(u).max())
    ymax = max(ymax, _add_ftcs(ax))
    _finish(fig, ax, ymax, JUNE_YLIM, JUNE_OUT)


def render_overlay():
    """Both eras on one paper-style axis: colour = device, style = era.

    September solid line + shaded +/-1 std band (fez/kingston/miami); June
    dashed single run (all four devices).  A two-key legend keeps device
    identity (colour) separate from era (line style)."""
    _apply_rcparams()
    fig, ax = plt.subplots(figsize=(9, 5.5))
    ymax = 0.0
    # September: solid mean + band
    for dev in SEP_DEVICES:
        mean, std, n = new_run_profile(dev, FRAME)
        if n == 0:
            continue
        col = TAB10(DEV_COLOR[dev])
        ax.fill_between(XNODES, mean - std, mean + std, color=col,
                        alpha=BAND_ALPHA, lw=0, zorder=2)
        ax.plot(XNODES, mean, marker="", lw=3.0, ls="-", color=col, zorder=4)
        ymax = max(ymax, np.abs(mean + std).max(), np.abs(mean - std).max())
    # June: dashed single run (boston is June-only)
    for dev in JUNE_DEVICES:
        u = june_profile(dev, FRAME)
        if u is None:
            continue
        col = TAB10(DEV_COLOR[dev])
        ax.plot(XNODES, u, marker="", lw=2.6, ls=JUNE_DASH, color=col, zorder=3)
        ymax = max(ymax, np.abs(u).max())
    ymax = max(ymax, _add_ftcs(ax))
    # two-key boxed legend: device colour (identity) then era line style
    handles = [Line2D([0], [0], color=TAB10(DEV_COLOR[d]), lw=3.0,
                      label=f"ibm_{d}") for d in JUNE_DEVICES]
    handles += [
        Line2D([0], [0], color=TAB10(FTCS_COLOR), lw=3.0, label="ftcs_reference"),
        Line2D([0], [0], color="0.35", lw=3.0, ls="-",
               label="September (mean +/- 1 std)"),
        Line2D([0], [0], color="0.35", lw=2.6, ls=JUNE_DASH,
               label="June (single run)"),
    ]
    _finish(fig, ax, ymax, OVERLAY_YLIM, OVERLAY_OUT, handles=handles)


def main():
    render_september()
    render_june()
    render_overlay()


if __name__ == "__main__":
    main()
