"""C8 shots x cfl cross — per-frame relL2 error vs FTCS q8 reference.

One panel per cfl rung, one line per shots rung (mean over seeds, min-max
band). Frames land on seams (save-every = k = 8); errors are computed
against the FTCS reference frame at the SAME physical time
(ftcs step m = n * cfl / 0.1, exact — verified no interpolation needed).

Run from this directory:  python make_plots.py
Writes err_vs_timestep.png alongside.
"""
import json
import math
import os
from collections import defaultdict

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FixedLocator, NullFormatter, ScalarFormatter

HERE = os.path.dirname(os.path.abspath(__file__))
SWEEP = os.path.dirname(HERE)
FTCS_Q8 = os.path.join(
    SWEEP, "..", "..", "..", "ch_ftcs_refs", "2026-08-13", "_3fa21a71", "9bbe98a3"
)

CFLS = [(0.8, 8, 64), (1.6, 4, 32), (3.2, 2, 16)]  # (cfl, S, n_steps)
SHOTS = [16384, 32768, 65536, 131072, 262144, 524288]

# 6-step single-hue ordinal ramp (OKLab-even), validated light-mode:
# monotone L, adjacent dL >= 0.06, light end 2.06:1 on #fcfcfb.
RAMP = ["#86b6ef", "#6d9bd3", "#5480b8", "#3c679e", "#254e84", "#0d366b"]

SURFACE, PAGE = "#fcfcfb", "#f9f9f7"
INK, INK2, MUTED = "#0b0b0b", "#52514e", "#898781"
GRID, BASELINE = "#e1e0d9", "#c3c2b7"


def load_frames(case_dir, exp_id, n_steps):
    """{timestep: u_array} — seam frames plus the final step."""
    art = json.load(open(os.path.join(case_dir, "q8020_artifacts_0.json")))
    frames = {int(k): v for k, v in art["solution_steps"].items()}
    res = json.load(open(os.path.join(case_dir, "q8020_results_0.json")))
    frames[n_steps] = res["u_final_method"]
    return frames


def rel_l2(u, ref):
    num = math.sqrt(sum((a - b) ** 2 for a, b in zip(u, ref)))
    den = math.sqrt(sum(b * b for b in ref))
    return num / den


def main():
    ref_frames = load_frames(FTCS_Q8, "9bbe98a3", 512)

    # errs[(cfl, shots)][timestep] -> [relL2 per seed]
    errs = defaultdict(lambda: defaultdict(list))
    n_cases = 0
    for d in sorted(os.listdir(SWEEP)):
        case = os.path.join(SWEEP, d)
        if not (os.path.isdir(case) and len(d) == 8 and d != "plots"):
            continue
        stats = json.load(
            open(os.path.join(case, f"q8020_sweep_exec_stats_{d}_0.json"))
        )
        if not stats["success"]:
            continue
        params = json.load(open(os.path.join(case, f"q8020_params_{d}.json")))
        cfl, shots = params["--cfl"], params["--shots"]
        n_steps = params["--n-steps"]
        for n, u in load_frames(case, d, n_steps).items():
            if n == 0:
                continue  # step 0 is the shared IC, error ~0
            m = round(n * cfl / 0.1)  # matching FTCS step (exact)
            errs[(cfl, shots)][n].append(rel_l2(u, ref_frames[m]))
        n_cases += 1
    print(f"loaded {n_cases} successful cases")

    for x_mode, fname in (("timestep", "err_vs_timestep.png"),
                          ("time", "err_vs_time.png")):
        fig, axes = plt.subplots(
            1, 3, figsize=(13, 4.6), sharey=True, sharex=(x_mode == "time"),
            facecolor=PAGE,
        )
        for ax, (cfl, S, n_steps) in zip(axes, CFLS):
            ax.set_facecolor(SURFACE)
            dt = cfl / 256
            for shots, color in zip(SHOTS, RAMP):
                by_step = errs[(cfl, shots)]
                steps = sorted(by_step)
                xs = steps if x_mode == "timestep" else [n * dt for n in steps]
                mean = [sum(by_step[n]) / len(by_step[n]) for n in steps]
                lo = [min(by_step[n]) for n in steps]
                hi = [max(by_step[n]) for n in steps]
                ax.fill_between(xs, lo, hi, color=color, alpha=0.15, lw=0)
                ax.plot(
                    xs, mean, color=color, lw=2, marker="o", ms=5,
                    label=f"$2^{{{int(math.log2(shots))}}}$",
                )
            ax.set_title(
                f"cfl = {cfl}   (S = {S} seams, dt = {dt:.2e})",
                color=INK2, fontsize=10,
            )
            ax.set_yscale("log")
            ax.yaxis.set_major_locator(
                FixedLocator([0.03, 0.05, 0.1, 0.2, 0.3, 0.5])
            )
            ax.yaxis.set_major_formatter(ScalarFormatter())
            ax.yaxis.set_minor_formatter(NullFormatter())
            if x_mode == "timestep":
                ax.set_xlabel("timestep", color=MUTED)
                ax.set_xticks(range(0, n_steps + 1, 8))
            else:
                ax.set_xlabel("physical time t", color=MUTED)
                ax.set_xticks([0, 0.05, 0.1, 0.15, 0.2])
                ax.set_xlim(0, 0.205)
            ax.grid(True, which="major", color=GRID, lw=0.75)
            ax.tick_params(which="both", colors=MUTED, labelsize=9)
            for side in ("top", "right"):
                ax.spines[side].set_visible(False)
            for side in ("left", "bottom"):
                ax.spines[side].set_color(BASELINE)

        axes[0].set_ylabel("rel. L2 error vs FTCS reference", color=INK2)
        handles, labels = axes[0].get_legend_handles_labels()
        fig.legend(
            handles, labels, title="shots", loc="center left",
            bbox_to_anchor=(0.905, 0.5), fontsize=9, title_fontsize=9,
            frameon=False, labelcolor=INK2,
        )
        comparable = (
            "same t compares like-for-like across panels"
            if x_mode == "time"
            else "all rungs end at t = 0.2"
        )
        fig.suptitle(
            "C8 seam-noise growth per frame — every frame is a seam; "
            f"{comparable}  (band = seed min–max, n = 2–3)",
            color=INK, fontsize=11,
        )
        fig.tight_layout(rect=(0, 0, 0.9, 0.94))
        out = os.path.join(HERE, fname)
        fig.savefig(out, dpi=150, facecolor=PAGE)
        print("wrote", out)


if __name__ == "__main__":
    main()
