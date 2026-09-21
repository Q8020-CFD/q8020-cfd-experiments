#!/usr/bin/env python3
"""Figure for the boston June-vs-September forensics.

A: mode-space error budget -- relL2^2 split EXACTLY (Parseval) into the k=1
   physical Burgers mode and the k=2/k=3 contaminants, per device-epoch.
B: physics recovered (|U1| as a fraction of the noiseless ceiling) against the
   paper's relL2 score -- the two disagree, and boston is the extreme case.
C: boston's frame-1 profile: FTCS truth, noiseless ceiling, what boston
   returned, and boston with the k=2/k=3 contaminants removed.
D: per-trial k=2 phase in September -- phase-locked, so the contaminant is a
   coherent circuit error, not shot or readout noise.

Imports the loaders from boston_forensics.py so the figure and the text
analysis can never disagree.  Run with the ch-lbm venv python.
"""
from __future__ import annotations

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import boston_forensics as bf
from score_smooth_movie_rerun import N, ftcs800_truth_frames, rel_l2

# --- validated palette (dataviz reference instance, light mode) -------------
SURFACE = "#fcfcfb"
TEXT_1, TEXT_2, TEXT_3 = "#0b0b0b", "#52514e", "#84837c"
K_COLOR = {1: "#2a78d6", 2: "#eb6834", 3: "#1baf7a"}   # slots 1-3, all-pairs OK
DEV_COLOR = {"kingston": "#2a78d6", "fez": "#eb6834",
             "miami": "#1baf7a", "boston": "#4a3aa7"}
GRID = "#e4e3df"

OUT = os.path.abspath(os.path.join(
    bf.EXP, "burgers-ch-lbm", "ch_smooth_movie_rerun", "analysis",
    "boston_mode_budget.png"))


def tidy(ax, left=True):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(GRID)
    if not left:
        ax.spines["left"].set_visible(False)
    ax.tick_params(colors=TEXT_2, labelsize=8.5, length=3)


def collect(truth):
    """[(label, dev, epoch, u_frame1)] for every device-epoch with data."""
    rows = []
    for d in bf.DEVS:
        fr = bf.june_frames(d)
        if fr:
            rows.append((f"{d}\nJun", d, "Jun", fr[1], 1))
    for d in bf.DEVS:
        tr = bf.sep_frames(d)
        if tr:
            rows.append((f"{d}\nSep", d, "Sep",
                         np.mean([t[1] for t in tr], 0), len(tr)))
    return rows


def main():
    truth = ftcs800_truth_frames()
    ref = truth[1]
    R = np.fft.rfft(ref) / N
    sv = bf.sim_frames("cd872d62")
    ceil1 = float(np.abs(np.fft.rfft(sv[1]))[1] / N)
    rows = collect(truth)
    den = 2.0 * N * float(np.sum(np.abs(R[1:4]) ** 2))

    fig, axes = plt.subplots(2, 2, figsize=(13.4, 9.0),
                             facecolor=SURFACE)
    (axA, axB), (axC, axD) = axes
    for ax in axes.ravel():
        ax.set_facecolor(SURFACE)

    # ---------------- A: stacked mode-space error budget -------------------
    labels = [r[0] for r in rows]
    x = np.arange(len(rows))
    parts = {k: [] for k in (1, 2, 3)}
    tot = []
    for _, _, _, u, _ in rows:
        U = np.fft.rfft(u) / N
        p = {k: 2.0 * N * float(np.abs(U[k] - R[k]) ** 2) for k in (1, 2, 3)}
        for k in (1, 2, 3):
            parts[k].append(p[k] / den)
        tot.append(sum(p.values()) / den)
    bot = np.zeros(len(rows))
    for k in (1, 2, 3):
        v = np.array(parts[k])
        axA.bar(x, v, bottom=bot, width=0.62, color=K_COLOR[k],
                edgecolor=SURFACE, linewidth=2.0,
                label=("$k=1$  physical Burgers mode" if k == 1
                       else f"$k={k}$  contaminant"))
        for xi, vi, bi in zip(x, v, bot):
            if vi / max(tot) > 0.07:
                axA.text(xi, bi + vi / 2, f"{vi/tot[xi]:.0%}", ha="center",
                         va="center", fontsize=8, color="white",
                         fontweight="bold")
        bot += v
    for xi, t in zip(x, tot):
        axA.text(xi, t + 0.012, f"relL2\n{np.sqrt(t):.3f}", ha="center",
                 va="bottom", fontsize=8, color=TEXT_2)
    axA.set_xticks(x)
    axA.set_xticklabels(labels, fontsize=8.5, color=TEXT_1)
    axA.set_ylabel("contribution to relL$_2^2$", fontsize=9.5,
                   color=TEXT_2)
    axA.set_ylim(0, max(tot) * 1.30)
    axA.yaxis.grid(True, color=GRID, lw=0.8)
    axA.set_axisbelow(True)
    tidy(axA)
    axA.legend(frameon=False, fontsize=8.5, loc="upper left",
               labelcolor=TEXT_2)
    axA.set_title("A  Where the error lives: relL$_2^2$ split by Fourier mode "
                  "(Parseval-exact)", fontsize=10.5, color=TEXT_1,
                  loc="left", pad=10)

    # ---------------- B: only RAW amplitude flatters boston ----------------
    # Three measures, each normalised so 1.0 = the noiseless field, so they
    # sit on one axis.  Raw |U1| ignores the overall inflation of the field;
    # purity and cosine do not, and they reverse the verdict.
    jd = {d: bf.june_frames(d)[1] for d in bf.DEVS if bf.june_frames(d)}
    pur_ceil = float(np.abs(np.fft.rfft(sv[1]))[1] / N
                     / np.linalg.norm(sv[1]))
    meas = [
        ("raw $|U_1|$\n(ignores inflation)",
         lambda u: float(np.abs(np.fft.rfft(u))[1] / N) / ceil1),
        ("purity $|U_1|/\\|u\\|$\n(normalisation-free)",
         lambda u: float(np.abs(np.fft.rfft(u))[1] / N
                         / np.linalg.norm(u)) / pur_ceil),
        ("cosine vs noiseless\n(shape only)",
         lambda u: bf.cosine(u, sv[1])),
    ]
    devs_j = [d for d in ("kingston", "fez", "miami", "boston") if d in jd]
    w = 0.19
    xg = np.arange(len(meas))
    for i, d in enumerate(devs_j):
        off = (i - (len(devs_j) - 1) / 2) * w
        vals = [f(jd[d]) for _, f in meas]
        axB.bar(xg + off, vals, width=w * 0.88, color=DEV_COLOR[d],
                edgecolor=SURFACE, linewidth=1.6, label=d, zorder=3)
        for xi, v in zip(xg + off, vals):
            axB.text(xi, v + 0.012, f"{v:.2f}", ha="center", va="bottom",
                     fontsize=7.5, color=TEXT_2, rotation=90)
    axB.axhline(1.0, color=TEXT_3, lw=1.0, ls="--", zorder=2)
    axB.text(len(meas) - 0.42, 1.015, "noiseless", fontsize=8,
             color=TEXT_3, ha="right", va="bottom")
    axB.set_xticks(xg)
    axB.set_xticklabels([m for m, _ in meas], fontsize=8.5, color=TEXT_1)
    axB.set_ylabel("fraction of the noiseless field  (1.0 = ceiling)",
                   fontsize=9.5, color=TEXT_2)
    axB.set_ylim(0, 1.22)
    axB.yaxis.grid(True, color=GRID, lw=0.8)
    axB.set_axisbelow(True)
    tidy(axB)
    axB.legend(frameon=False, fontsize=8.0, loc="upper center",
               bbox_to_anchor=(0.5, -0.17), ncol=4, labelcolor=TEXT_2)
    axB.set_title("B  Only RAW amplitude flatters boston; both "
                  "normalisation-free\n    measures rank it LAST  (June)",
                  fontsize=10.5, color=TEXT_1, loc="left", pad=8)

    # ---------------- C: boston frame-1 profile ---------------------------
    xg = np.arange(N) / N
    bos = bf.june_frames("boston")[1]
    U = np.fft.rfft(bos) / N
    keep = np.zeros_like(U)
    keep[1] = U[1]
    bos_k1 = np.fft.irfft(keep * N, n=N)
    xf, ff = None, None
    try:
        from score_smooth_movie_rerun import ftcs800_full_frames
        xf, fr_full = ftcs800_full_frames()
        ff = fr_full[1]
    except Exception:
        pass
    if ff is not None:
        axC.plot(np.append(xf, 1.0), np.append(ff, ff[0]), color=TEXT_3,
                 lw=1.6, label="FTCS-800 truth")
    cyc = lambda a: np.append(a, a[0])
    xc = np.append(xg, 1.0)
    axC.plot(xc, cyc(sv[1]), color=TEXT_1, lw=1.8, ls="--", marker="o",
             ms=5, label="noiseless ceiling ($\\chi$=2, shots 0)")
    axC.plot(xc, cyc(bos), color=DEV_COLOR["boston"], lw=2.0, marker="o",
             ms=7, label="boston June, as returned")
    axC.plot(xc, cyc(bos_k1), color=K_COLOR[1], lw=2.0, ls=":", marker="s",
             ms=6, label="boston June, $k=1$ only")
    axC.axhline(0, color=GRID, lw=0.8)
    axC.set_xlabel("$x$", fontsize=9.5, color=TEXT_2)
    axC.set_ylabel("$u$   at $T=0.0375$", fontsize=9.5, color=TEXT_2)
    axC.grid(True, color=GRID, lw=0.8)
    axC.set_axisbelow(True)
    tidy(axC)
    axC.legend(frameon=False, fontsize=8.0, loc="upper center",
               bbox_to_anchor=(0.5, -0.16), ncol=2, labelcolor=TEXT_2)
    axC.set_title("C  boston frame 1: the sine is there, buried under a "
                  "period-4 ripple", fontsize=10.5, color=TEXT_1,
                  loc="left", pad=10)

    # ---------------- D: k=2 phase locking -------------------------------
    yi, ylab = 0, []
    for dev in bf.DEVS:
        tr = bf.sep_frames(dev)
        if not tr:
            continue
        ph = np.array([float(np.angle(np.fft.rfft(t[1])[2])) for t in tr])
        z = np.mean(np.exp(1j * ph))
        axD.scatter(ph, np.full(len(ph), yi), s=70, marker="s",
                    color=DEV_COLOR[dev], edgecolor=SURFACE, linewidth=1.6,
                    zorder=3)
        axD.text(np.pi * 1.16, yi, f"$\\bar R$ = {abs(z):.4f}", fontsize=8.5,
                 color=TEXT_2, va="center")
        ylab.append(f"{dev} Sep (n={len(tr)})")
        yi += 1
    for dev in bf.DEVS:
        fr = bf.june_frames(dev)
        if not fr:
            continue
        ph = float(np.angle(np.fft.rfft(fr[1])[2]))
        axD.scatter([ph], [yi], s=110, marker="o", color=DEV_COLOR[dev],
                    edgecolor=SURFACE, linewidth=1.8, zorder=3)
        ylab.append(f"{dev} Jun (n=1)")
        yi += 1
    axD.set_yticks(range(yi))
    axD.set_yticklabels(ylab, fontsize=8.5, color=TEXT_1)
    axD.set_xlim(-np.pi * 1.06, np.pi * 1.62)
    axD.set_xticks([-np.pi, -np.pi/2, 0, np.pi/2, np.pi])
    axD.set_xticklabels(["$-\\pi$", "$-\\pi/2$", "0", "$\\pi/2$", "$\\pi$"])
    axD.set_xlabel("phase of the $k=2$ contaminant (rad)", fontsize=9.5,
                   color=TEXT_2)
    axD.axvline(np.pi * 1.10, color=GRID, lw=0.8)
    axD.xaxis.grid(True, color=GRID, lw=0.8)
    axD.set_axisbelow(True)
    tidy(axD, left=False)
    axD.invert_yaxis()
    axD.set_title("D  The contaminant is COHERENT: 10 repeats land on one "
                  "phase ($\\bar R\\to1$)", fontsize=10.5, color=TEXT_1,
                  loc="left", pad=10)

    fig.suptitle("ibm_boston is the best-calibrated device and still returns "
                 "the worst field\nThe contaminant is real, not a metric "
                 "artifact  —  smooth_movie frame 1, $q$=3, $\\nu$=0.08, "
                 "June $n$=1 per device",
                 fontsize=12, color=TEXT_1, x=0.012, ha="left", y=0.992,
                 va="top")
    fig.tight_layout(rect=(0, 0, 1, 0.925))
    fig.savefig(OUT, dpi=170, facecolor=SURFACE)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
