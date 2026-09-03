#!/usr/bin/env python3
"""C1B full seam ladder (S = 256 .. 1) — score & plot (offline).

The C1B run used --no-classical/analytic-reference, so relL2-vs-FTCS is not in
the artifacts.  This script scores each saved CH final field
(results.u_final_method) against the frame-aligned FTCS truth at the identical
op point (q=8, sine, A=0.3, nu=0.03, CFL=0.1, n_steps=512) and produces:

  * a printed table + CSV (segments S, k, relL2, segment depth, CX, p_success,
    wall time)
  * segments_vs_relL2.png : S on x (log2), relL2 on left y (log, blue), and
    segment circuit depth on the right y (log, orange) — the requested twin-axis
    figure.  The shots=0 statevector floor (zero-seam, no shot noise) is drawn
    as the dashed baseline.

Note (collapse): because `collapse` is ON, every segment is ONE QFT/diagonal/
QFT^-1 layer at 11 qubits regardless of k, so the segment circuit DEPTH is flat
(~15.8k) across the whole ladder.  Contrast the pre-collapse C1 figure, where
depth scaled with k.  Total cost still scales with S (see wall time).

Run:  python plot_c1B_seams.py
"""
from __future__ import annotations

import csv
import glob
import json
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))  # experiments root
C1B_ROOT = os.path.join(HERE, "..")  # the ch_q8_c1B run tree
FTCS_REF = os.path.join(
    REPO, "results", "burgers-ch-lbm", "ch_ftcs_refs",
    "2026-08-13", "_3fa21a71", "9bbe98a3", "q8020_results_0.json",
)
C0_ROOT = os.path.join(REPO, "results", "burgers-ch-lbm", "ch_q8_c0")
N_STEPS = 512


def load(p):
    try:
        with open(p) as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def field(r0):
    v = (r0 or {}).get("u_final_method")
    if isinstance(v, list) and v:
        a = np.asarray(v, float)
        if np.all(np.isfinite(a)):
            return a
    return None


def rel_l2(u, ref):
    n = min(u.size, ref.size)
    return float(np.linalg.norm(u[:n] - ref[:n]) / np.linalg.norm(ref[:n]))


def sv_floor(ref):
    """shots=0, zero-seam statevector floor at this op point (C0), vs FTCS."""
    for d in sorted(glob.glob(os.path.join(C0_ROOT, "**", ""), recursive=True)):
        pj = glob.glob(os.path.join(d, "q8020_params_*.json"))
        if not pj:
            continue
        p = load(pj[0]) or {}
        if p.get("--shots") != 0 or int(p.get("--n-steps") or -1) != N_STEPS:
            continue
        u = field(load(os.path.join(d, "q8020_results_0.json")))
        if u is not None:
            return rel_l2(u, ref)
    return None


def collect(ref):
    rows = []
    for d in sorted(glob.glob(os.path.join(C1B_ROOT, "**", ""), recursive=True)):
        pj = glob.glob(os.path.join(d, "q8020_params_*.json"))
        if not pj:
            continue
        p = load(pj[0]) or {}
        k = p.get("--segment-size")
        if k is None or p.get("_case_id") is None:
            continue
        an = load(os.path.join(d, "q8020_analysis_0.json")) or {}
        u = field(load(os.path.join(d, "q8020_results_0.json")))
        psm = an.get("per_step_metrics") or []
        ps = [m["p_success"] for m in psm if m.get("p_success") is not None]
        rows.append({
            "case_id": p.get("_case_id"),
            "k": int(k),
            "S": N_STEPS // int(k),
            "relL2": rel_l2(u, ref) if u is not None else None,
            "seg_depth": an.get("avg_circuit_depth"),
            "seg_cx": an.get("avg_cx_gates"),
            "n_qubits": an.get("n_qubits"),
            "p_success_mean": round(sum(ps) / len(ps), 5) if ps else None,
            "wall_s": round(an.get("method_wall_time_s") or 0, 1),
        })
    rows.sort(key=lambda r: r["S"])
    return rows


def main():
    ref = field(load(FTCS_REF))
    if ref is None:
        raise SystemExit(f"FTCS reference missing/blown-up: {FTCS_REF}")
    rows = collect(ref)
    floor = sv_floor(ref)

    # --- table + CSV --------------------------------------------------
    print(f"FTCS ref half-amp = {(ref.max()-ref.min())/2:.4f}  "
          f"(relL2 denominator);  SV floor relL2 = "
          f"{floor:.3e}" if floor else "SV floor: n/a")
    hdr = ("S", "k", "relL2", "seg_depth", "seg_CX", "p_succ", "wall_s")
    print(f"{hdr[0]:>4} {hdr[1]:>4} {hdr[2]:>10} {hdr[3]:>10} "
          f"{hdr[4]:>8} {hdr[5]:>8} {hdr[6]:>9}")
    for r in rows:
        rl = "NaN" if r["relL2"] is None else f"{r['relL2']:.4g}"
        print(f"{r['S']:>4} {r['k']:>4} {rl:>10} {r['seg_depth']:>10.0f} "
              f"{r['seg_cx']:>8.0f} {r['p_success_mean']:>8} {r['wall_s']:>9}")

    csv_path = os.path.join(HERE, "c1B_seam_scores.csv")
    with open(csv_path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print("wrote", os.path.relpath(csv_path, REPO))

    # --- figure -------------------------------------------------------
    # Labels/format deliberately match the June reference figure
    # (aux/burgers-ch-lbm-June2026/seam_shots_figs/fig_seam_k_sweep.png):
    # same title, axis labels, x ticks (ScalarFormatter), "k"-suffixed depth
    # ticks, statevector-floor annotation, colorblind palette, and rcParams.
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.ticker as mticker

    plt.rcParams.update({
        "font.size": 10,
        "axes.grid": True,
        "grid.alpha": 0.3,
        "axes.axisbelow": True,
        "figure.dpi": 150,
    })
    C_L2, C_DEPTH, C_REF = "#0072B2", "#D55E00", "#888888"  # June palette

    xs = [r["S"] for r in rows]
    ys = [r["relL2"] for r in rows]
    dep = [r["seg_depth"] for r in rows]
    ks = [r["k"] for r in rows]

    fig, axa = plt.subplots(1, 1, figsize=(7.2, 4.6))

    # left: accuracy (blue) — relative L2 vs the FTCS truth
    axa.plot(xs, ys, "o-", color=C_L2, lw=2, ms=7)
    if floor is not None:
        axa.axhline(floor, color=C_REF, ls="--", lw=1.2)
        axa.text(0.01, floor,
                 f" statevector floor (no shot noise, L2={floor:.1e}; "
                 f"S={xs[0]}, k={ks[0]})",
                 color=C_REF, va="bottom", ha="left", fontsize=8,
                 transform=axa.get_yaxis_transform())
    axa.set_yscale("log")
    axa.set_ylabel("L2 (rel vs FTCS)", color=C_L2)
    axa.tick_params(axis="y", colors=C_L2)
    axa.set_xscale("log", base=2)
    axa.xaxis.set_major_formatter(mticker.ScalarFormatter())
    axa.set_xticks(xs)
    axa.set_xlabel("segments (S)")
    axa.set_title(
        r"Cole-Hopf $\phi$, evolution error over k-step segments"
        r"  (q=8, shots=$2^{17}$, Re=10)", pad=10)
    # label each point with its in-segment k (= n_steps / S)
    for seg, l2, k in zip(xs, ys, ks):
        axa.annotate(f"k={int(k)}", (seg, l2), textcoords="offset points",
                     xytext=(6, 8), fontsize=7, color=C_L2)

    # right: segment circuit depth (orange). Under collapse this is FLAT in S
    # (~15.8k), so keep a >=1-decade window: the flatness reads as flat and the
    # ~1% build drift is not inflated into a spurious trend.
    axd = axa.twinx()
    axd.plot(xs, dep, "s--", color=C_DEPTH, lw=1.6, ms=5, alpha=0.9)
    axd.set_yscale("log")
    axd.set_ylabel("segment circuit depth", color=C_DEPTH)
    axd.tick_params(axis="y", colors=C_DEPTH)
    axd.set_ylim(7e3, 2e5)
    axd.yaxis.set_major_locator(mticker.FixedLocator([1e4, 2e4, 5e4, 1e5]))
    axd.yaxis.set_minor_locator(mticker.NullLocator())
    axd.yaxis.set_major_formatter(
        mticker.FuncFormatter(lambda x, _: f"{x / 1e3:g}k"))
    axd.grid(False)

    fig.tight_layout()
    png = os.path.join(HERE, "segments_vs_relL2.png")
    fig.savefig(png, dpi=150, bbox_inches="tight")
    print("wrote", os.path.relpath(png, REPO))


if __name__ == "__main__":
    main()
