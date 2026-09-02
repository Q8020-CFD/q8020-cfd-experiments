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
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    BLUE, ORANGE, GREY = "#1f77b4", "#d1642a", "#7f7f7f"
    xs = [r["S"] for r in rows]
    ys = [r["relL2"] for r in rows]
    dep = [r["seg_depth"] for r in rows]

    fig, axL = plt.subplots(figsize=(9, 5.5))

    # left: relL2 (blue)
    axL.plot(xs, ys, "o-", color=BLUE, lw=2, ms=8, zorder=3)
    axL.set_xscale("log", base=2)
    axL.set_yscale("log")
    axL.set_xlabel("segments  S = n_steps / k")
    axL.set_ylabel("relL2  (CH final field vs FTCS truth)", color=BLUE)
    axL.tick_params(axis="y", labelcolor=BLUE)
    axL.set_xticks(xs)
    axL.set_xticklabels([str(s) for s in xs])
    axL.grid(True, which="both", alpha=0.22)
    # per-point k labels
    for r in rows:
        axL.annotate(f"k={r['k']}", (r["S"], r["relL2"]),
                     textcoords="offset points", xytext=(0, 9),
                     fontsize=8, color=BLUE, ha="center")
    # relL2 = 1 marker and SV floor
    axL.axhline(1.0, ls=":", lw=1, color=GREY, alpha=0.8)
    axL.text(xs[-1], 1.0, "relL2 = 1 (solution-scale error)", fontsize=8,
             color=GREY, va="bottom", ha="right")
    if floor is not None:
        axL.axhline(floor, ls="--", lw=1.2, color=GREY)
        axL.text(xs[0], floor, f"statevector floor "
                 f"(no shot noise, relL2={floor:.1e}; S=1, k={N_STEPS})",
                 fontsize=8, color=GREY, va="bottom", ha="left")

    # right: segment circuit depth (orange)
    axR = axL.twinx()
    axR.plot(xs, dep, "s--", color=ORANGE, lw=1.8, ms=7, zorder=2)
    axR.set_yscale("log")
    axR.set_ylabel("segment circuit depth (transpiled)", color=ORANGE)
    axR.tick_params(axis="y", labelcolor=ORANGE)
    axR.set_ylim(1e3, 1e6)  # honest window so the flat depth reads as flat
    axR.annotate(f"depth ~ {dep[0]:.0f}, flat in S\n(collapse: 1 layer/segment)",
                 (xs[len(xs) // 2], dep[len(xs) // 2]),
                 textcoords="offset points", xytext=(0, -34),
                 fontsize=8, color=ORANGE, ha="center")

    axL.set_title("Cole-Hopf phi, evolution error over k-step segments "
                  "(q=8, shots=$2^{17}$, Re=10)")
    fig.tight_layout()
    png = os.path.join(HERE, "segments_vs_relL2.png")
    fig.savefig(png, dpi=150, bbox_inches="tight")
    print("wrote", os.path.relpath(png, REPO))


if __name__ == "__main__":
    main()
