#!/usr/bin/env python3
"""Per-frame relL2 trajectories for the CH nu-domain sweep.

One panel per segment-size; physical time T on x, relL2 on y (log); one
line per nu (colored by a viscosity colormap).  For every saved frame
(steps 0,10,...,400) it scores the CH field against the STABLE
ftcs_reference truth at the same frame:

    relL2(t) = || u_CH(step) - u_truth(step) || / || u_truth(step) ||

This shows *when* each case diverges vs. settles, which the final-only
relL2-vs-nu plot (score_nu_domain.py) cannot.

Reuses score_nu_domain.py's loaders/truth-discovery.  Run:
    q8020-cfd-ch-lbm/.venv/bin/python \\
        q8020-cfd-experiments/aux/burgers-ch-lbm/cases/plot_nu_domain_trajectories.py
"""
from __future__ import annotations

import argparse
import os

import numpy as np

import score_nu_domain as sd  # same directory

DT = sd.CFL_EXPECT * sd.DX  # physical time per step = cfl*dx


def rel_l2(u: np.ndarray, ref: np.ndarray) -> float:
    n = np.linalg.norm(ref)
    return float(np.linalg.norm(u - ref) / n) if n else float("nan")


def trajectory_scores(ch_traj: dict[int, np.ndarray],
                      truth_traj: dict[int, np.ndarray]):
    """(times, relL2) over the frames common to CH and truth, skipping
    step 0 (relL2=0 there, unplottable on log-y) and any non-finite frame."""
    steps = sorted(set(ch_traj) & set(truth_traj))
    ts, rs = [], []
    for s in steps:
        if s == 0:
            continue
        u, ref = ch_traj[s], truth_traj[s]
        if not (np.all(np.isfinite(u)) and np.all(np.isfinite(ref))):
            continue
        n = min(u.size, ref.size)
        ts.append(s * DT)
        rs.append(rel_l2(u[:n], ref[:n]))
    return ts, rs


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ch-root",
                    default=os.path.join(sd.REPO, "results", "burgers-ch-lbm",
                                         "ch_q8_nu_domain"))
    ap.add_argument("--truth-root", action="append", default=None)
    ap.add_argument("--outdir", default=None)
    args = ap.parse_args()

    ch = sd.collect_ch(args.ch_root)
    truths = sd.collect_truths(sd.truth_roots(sd.REPO, args.truth_root))
    if not ch:
        raise SystemExit(f"No CH cases under {args.ch_root}")

    outdir = args.outdir or os.path.join(args.ch_root, "analysis")
    os.makedirs(outdir, exist_ok=True)

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import cm, colors

    segs = sorted({c["seg"] for c in ch})
    nus = sorted({c["nu"] for c in ch})
    # log-nu color mapping so the 8 values spread evenly
    norm = colors.LogNorm(vmin=min(nus), vmax=max(nus))
    cmap = cm.viridis

    fig, axes = plt.subplots(1, len(segs), figsize=(6.4 * len(segs), 5.4),
                             sharey=True, squeeze=False)
    axes = axes[0]
    missing = set()
    for ax, seg in zip(axes, segs):
        for c in sorted((c for c in ch if c["seg"] == seg),
                        key=lambda r: r["nu"]):
            t = sd.match_truth(c["nu"], truths)
            if t is None:
                missing.add(c["nu"])
                continue
            ts, rs = trajectory_scores(sd.load_trajectory(c["dir"]),
                                       sd.load_trajectory(t["dir"]))
            if not ts:
                continue
            ax.plot(ts, rs, color=cmap(norm(c["nu"])), lw=1.6,
                    marker=".", ms=4)
        ax.axhline(1.0, ls="--", lw=1, color="grey", alpha=0.7)
        ax.set_yscale("log")
        ax.set_xlabel("physical time  T  (= step x dt,  dt=%.2e)" % DT)
        ax.set_title(f"segment-size {seg}   (S = {400 // seg} seams)")
        ax.grid(True, which="both", alpha=0.25)
    axes[0].set_ylabel("relL2(t)   (CH vs stable FTCS truth)")

    sm = cm.ScalarMappable(norm=norm, cmap=cmap)
    cbar = fig.colorbar(sm, ax=list(axes), pad=0.02)
    cbar.set_label("viscosity  nu")
    cbar.minorticks_off()                       # suppress LogNorm auto-minors
    cbar.set_ticks(nus)
    cbar.set_ticklabels([f"{n:g}" for n in nus])

    fig.suptitle("CH domain of utility — relL2 trajectory per nu "
                 "(q=8, A=0.3, CFL=0.1, n-steps=400)")
    png = os.path.join(outdir, "relL2_trajectory_by_seg.png")
    fig.savefig(png, dpi=150, bbox_inches="tight")
    print(f"wrote {png}")
    if missing:
        print(f"no truth for nu={sorted(missing)} (run ftcs_ref_nu_domain_topup.toml)")


if __name__ == "__main__":
    main()
