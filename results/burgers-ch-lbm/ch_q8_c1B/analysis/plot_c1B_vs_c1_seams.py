#!/usr/bin/env python3
"""C1B (post-collapse) seam ladder with the C1 (pre-collapse) sweep overlaid.

Same twin-axis layout as plot_c1B_seams.py (segments S on x, relL2 left/blue,
segment circuit depth right/orange), but overlays the older C1 seam sweep
(ch_q8_c1, 2026-08-11, k=[2,4,8,16] -> S=[256,128,64,32]) on BOTH axes so the
collapse story reads off the figure directly:

  * relL2 (left): the C1 points land EXACTLY on the C1B curve at every shared
    S -> collapse is a bit-exact rewrite in ideal sim (ratio 1.000, verified).
  * depth (right): C1's per-segment depth SCALES with k (rising to ~250k as
    segments grow), while C1B is FLAT ~15.8k for every k -> collapse's entire
    win is cost, not accuracy.  (C1 also carries q+n_bond+k qubits: 12..26 vs
    C1B's flat 11.)

Both runs share the op point (q=8, sine, A=0.3, nu=0.03, CFL=0.1, n_steps=512,
shots=2^17) and are scored against the same frame-aligned FTCS truth.

Run:  python plot_c1B_vs_c1_seams.py
"""
from __future__ import annotations

import csv
import glob
import json
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))  # experiments root
C1B_ROOT = os.path.join(HERE, "..")  # the ch_q8_c1B run tree (post-collapse)
C1_ROOT = os.path.join(REPO, "results", "burgers-ch-lbm", "ch_q8_c1")  # pre-collapse
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


def collect(root, ref):
    """Score every seam case under `root` (works for both C1 and C1B trees)."""
    rows = []
    for d in sorted(glob.glob(os.path.join(root, "**", ""), recursive=True)):
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
    c1b = collect(C1B_ROOT, ref)
    c1 = collect(C1_ROOT, ref)
    floor = sv_floor(ref)
    if not c1:
        raise SystemExit(f"no C1 (pre-collapse) runs under {C1_ROOT}")

    # --- table + CSV --------------------------------------------------
    print(f"FTCS ref half-amp = {(ref.max() - ref.min()) / 2:.4f}   "
          f"SV floor relL2 = {floor:.3e}" if floor else "SV floor: n/a")
    hdr = ("run", "S", "k", "relL2", "seg_depth", "seg_CX", "qubits", "p_succ")
    print(f"{hdr[0]:>5} {hdr[1]:>4} {hdr[2]:>4} {hdr[3]:>10} {hdr[4]:>10} "
          f"{hdr[5]:>8} {hdr[6]:>7} {hdr[7]:>8}")
    for tag, rows in (("C1B", c1b), ("C1", c1)):
        for r in rows:
            rl = "NaN" if r["relL2"] is None else f"{r['relL2']:.4g}"
            print(f"{tag:>5} {r['S']:>4} {r['k']:>4} {rl:>10} "
                  f"{r['seg_depth']:>10.0f} {r['seg_cx']:>8.0f} "
                  f"{r['n_qubits']:>7} {r['p_success_mean']:>8}")

    csv_path = os.path.join(HERE, "c1B_vs_c1_seam_scores.csv")
    with open(csv_path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["run"] + list(c1b[0].keys()))
        w.writeheader()
        for tag, rows in (("C1B", c1b), ("C1", c1)):
            for r in rows:
                w.writerow({"run": tag, **r})
    print("wrote", os.path.relpath(csv_path, REPO))

    # --- figure -------------------------------------------------------
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D

    BLUE, ORANGE, GREY = "#1f77b4", "#d1642a", "#7f7f7f"
    NAVY, CRIMSON = "#0b3d91", "#b3202c"  # pre-collapse (C1) overlays

    fig, axL = plt.subplots(figsize=(9.5, 5.8))

    # ---- left axis: relL2 --------------------------------------------
    xb = [r["S"] for r in c1b]
    yb = [r["relL2"] for r in c1b]
    x1 = [r["S"] for r in c1]
    y1 = [r["relL2"] for r in c1]

    axL.plot(xb, yb, "o-", color=BLUE, lw=2, ms=8, zorder=3)
    # C1 overlay: big hollow rings sitting on the C1B points -> "identical"
    axL.plot(x1, y1, "o", mfc="none", mec=NAVY, mew=2, ms=15, zorder=4)
    axL.set_xscale("log", base=2)
    axL.set_yscale("log")
    axL.set_xlabel("segments  S = n_steps / k")
    axL.set_ylabel("relL2  (CH final field vs FTCS truth)", color=BLUE)
    axL.tick_params(axis="y", labelcolor=BLUE)
    axL.set_xticks(xb)
    axL.set_xticklabels([str(s) for s in xb])
    axL.grid(True, which="both", alpha=0.22)
    for r in c1b:
        axL.annotate(f"k={r['k']}", (r["S"], r["relL2"]),
                     textcoords="offset points", xytext=(0, 10),
                     fontsize=8, color=BLUE, ha="center")
    axL.axhline(1.0, ls=":", lw=1, color=GREY, alpha=0.8)
    axL.text(xb[-1], 1.0, "relL2 = 1 (solution-scale error)", fontsize=8,
             color=GREY, va="bottom", ha="right")
    if floor is not None:
        axL.axhline(floor, ls="--", lw=1.2, color=GREY)
        axL.text(xb[0], floor, f"statevector floor "
                 f"(no shot noise, relL2={floor:.1e}; S=1, k={N_STEPS})",
                 fontsize=8, color=GREY, va="bottom", ha="left")
    # call out the coincidence on the shared range — anchor the S=32 ring and
    # drop the label into the empty lower-left quadrant (axes fraction).
    s32 = next((r for r in c1 if r["S"] == 32), c1[0])
    axL.annotate("C1 lands exactly on C1B\n(collapse is bit-exact in sim)",
                 (s32["S"], s32["relL2"]), xytext=(0.06, 0.30),
                 textcoords="axes fraction", fontsize=8, color=NAVY, ha="left",
                 arrowprops=dict(arrowstyle="->", color=NAVY, lw=1))

    # ---- right axis: segment circuit depth ---------------------------
    axR = axL.twinx()
    depb = [r["seg_depth"] for r in c1b]
    dep1 = [r["seg_depth"] for r in c1]
    axR.plot(xb, depb, "s--", color=ORANGE, lw=1.8, ms=7, zorder=2)
    axR.plot(x1, dep1, "^--", color=CRIMSON, lw=1.8, ms=9, zorder=2)
    axR.set_yscale("log")
    axR.set_ylabel("segment circuit depth (transpiled)", color=ORANGE)
    axR.tick_params(axis="y", labelcolor=ORANGE)
    axR.set_ylim(1e3, 1e6)  # honest window; both series live inside it
    axR.annotate(f"C1B depth ~{depb[0]:.0f}, flat in S\n"
                 f"(collapse: 1 layer / segment, 11 qubits)",
                 (xb[6], depb[6]), textcoords="offset points",
                 xytext=(0, -34), fontsize=8, color=ORANGE, ha="center")
    # label C1 depth growth with its qubit count
    for r in c1:
        axR.annotate(f"{r['seg_depth']:.0f}\n({r['n_qubits']}q)",
                     (r["S"], r["seg_depth"]),
                     textcoords="offset points", xytext=(6, 4),
                     fontsize=7.5, color=CRIMSON, ha="left", va="bottom")
    # anchor the tallest C1 depth point (S=32) and label just left of it
    top1 = c1[0]  # sorted by S -> S=32 (deepest, biggest k) is first
    axR.annotate("C1 depth ∝ k\n(q+n_bond+k qubits)",
                 (top1["S"], top1["seg_depth"]), textcoords="offset points",
                 xytext=(-104, 6), fontsize=8, color=CRIMSON, ha="left")

    # ---- combined legend (spans both axes) ---------------------------
    handles = [
        Line2D([], [], color=BLUE, marker="o", lw=2, ms=8,
               label="relL2 · C1B (post-collapse, k=2..512)"),
        Line2D([], [], color=NAVY, marker="o", mfc="none", mew=2, ls="none",
               ms=12, label="relL2 · C1 (pre-collapse, k=2..16)"),
        Line2D([], [], color=ORANGE, marker="s", ls="--", lw=1.8, ms=7,
               label="depth · C1B (flat ~15.8k)"),
        Line2D([], [], color=CRIMSON, marker="^", ls="--", lw=1.8, ms=9,
               label="depth · C1 (scales with k)"),
    ]
    axL.legend(handles=handles, loc="upper left", fontsize=8,
               framealpha=0.9, ncol=1)

    axL.set_title("Cole-Hopf seam ladder: pre-collapse (C1) vs post-collapse "
                  "(C1B)\nsame relL2, radically different cost  "
                  "(q=8, shots=$2^{17}$, Re=10)")
    fig.tight_layout()
    png = os.path.join(HERE, "segments_vs_relL2_c1_overlay.png")
    fig.savefig(png, dpi=150, bbox_inches="tight")
    print("wrote", os.path.relpath(png, REPO))


if __name__ == "__main__":
    main()
