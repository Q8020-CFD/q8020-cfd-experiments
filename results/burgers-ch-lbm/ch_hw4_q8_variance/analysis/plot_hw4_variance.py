#!/usr/bin/env python3
"""HW4 q8 variance run (ibm_kingston) — score & plot (offline).

The HW4 run used --no-classical/analytic-reference (cfl=51.2 macro-dt breaks the
inline FTCS baseline), so relL2-vs-truth is NOT in the artifacts.  This script
scores each trial's saved CH final field (results.u_final_method) against the
frame-aligned FTCS truth at the identical op point (q=8, sine, A=0.3, nu=0.03,
T_end=0.2) and produces, per group:

  * raw relL2, unit-norm-rescaled relL2 (removes pure attenuation), cosine
    ("is any shape left"), reconstructed ||u||, p_success, routed CZ, QPU sec
  * per-trial CSV (hw4_variance_scores.csv)
  * hw4_variance.png : two panels sharing the group x-axis —
      (a) cosine per trial (scatter) with mean+/-std; 0 = pure noise
      (b) raw relL2 per trial (log y) with mean+/-std; the classical
          statevector floors (chi=4 ~1.7e-4, chi=2 ~2.1e-2, from the prior
          q8 C-series / this run's TOML) as dashed baselines and the
          full-depolarization line at 1.0.  The gap between the SV floor and
          the HW band IS the depolarization wall.

The three groups (10 non-seedable trials each) measure the run-to-run error bar
on the q8 depolarization floor, chi=2 (10q) vs chi=4 (11q), and S=1 vs S=2
(segmenting does not firewall decoherence for the exact-CH path).

Run:  python plot_hw4_variance.py
"""
from __future__ import annotations

import csv
import glob
import json
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))  # experiments root
RUN_ROOT = os.path.join(HERE, "..")  # the ch_hw4_q8_variance run tree
FTCS_REF = os.path.join(
    REPO, "results", "burgers-ch-lbm", "ch_ftcs_refs",
    "2026-08-13", "_3fa21a71", "9bbe98a3", "q8020_results_0.json",
)

# groups in submission order; the classical statevector floor (shots=0, zero
# seam) for each chi at this op point is documented in the run TOML and the
# prior q8 C6 chi-ladder (chi=4: 1.7e-4, chi=2: 2.1e-2).
GROUPS = [
    ("q8_s1_ideal",       "S=1  chi=4 (11q)", 1.7e-4),
    ("q8_s1_ideal_chi2",  "S=1  chi=2 (10q)", 2.1e-2),
    ("q8_s2",             "S=2  chi=2 (10q)", 2.1e-2),
]


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


def score(u, ref):
    n = min(u.size, ref.size)
    u, ref = u[:n], ref[:n]
    rn = np.linalg.norm(ref)
    rel_raw = float(np.linalg.norm(u - ref) / rn)
    un = float(np.linalg.norm(u))
    cos = float(np.dot(u, ref) / (un * rn)) if un > 0 else float("nan")
    # optimal scalar rescale of u onto ref removes the pure-attenuation component
    denom = float(np.dot(u, u))
    alpha = float(np.dot(u, ref) / denom) if denom > 0 else 0.0
    rel_rescaled = float(np.linalg.norm(alpha * u - ref) / rn)
    return rel_raw, rel_rescaled, cos, un


def collect(ref):
    rows = []
    for grp, _, _ in GROUPS:
        for d in sorted(glob.glob(os.path.join(RUN_ROOT, "**", grp, "trial_*", ""),
                                  recursive=True)):
            an = load(os.path.join(d, "q8020_analysis_0.json")) or {}
            u = field(load(os.path.join(d, "q8020_results_0.json")))
            if u is None:
                continue
            rel_raw, rel_rescaled, cos, un = score(u, ref)
            psm = an.get("per_step_metrics") or []
            segs = psm[-1].get("segments_full", psm) if psm else []
            ps_final = segs[-1].get("p_success") if segs else None
            ps_seam = segs[0].get("p_success") if len(segs) > 1 else None
            qpu = sum(
                (s.get("execute", {}).get("job_metrics", {})
                 .get("usage", {}).get("qpu_charge_time_seconds") or 0)
                for s in segs)
            cz = None
            if psm and "transpile" in psm[0]:
                cz = psm[0]["transpile"]["after"]["gate_counts"].get("cz")
            rows.append({
                "group": grp,
                "trial": os.path.basename(os.path.normpath(d)),
                "relL2_raw": round(rel_raw, 5),
                "relL2_rescaled": round(rel_rescaled, 5),
                "cosine": round(cos, 5),
                "u_norm": round(un, 5),
                "p_success_final": ps_final,
                "p_success_seam": ps_seam,
                "cz_routed": cz,
                "qpu_charge_s": qpu,
                "opt_level": an.get("optimization_level"),
            })
    return rows


def main():
    ref = field(load(FTCS_REF))
    if ref is None:
        raise SystemExit(f"FTCS reference missing/blown-up: {FTCS_REF}")
    rows = collect(ref)
    if not rows:
        raise SystemExit("no trials found")

    # --- CSV ----------------------------------------------------------
    csv_path = os.path.join(HERE, "hw4_variance_scores.csv")
    with open(csv_path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print("wrote", os.path.relpath(csv_path, REPO))

    # --- per-group aggregate table ------------------------------------
    print(f"\nFTCS truth ||u|| = {np.linalg.norm(ref):.4f}  "
          f"(peak {ref.max():.3f})\n")
    hdr = ("group", "relL2_raw", "relL2_resc", "cosine", "p_succ", "QPU_s")
    print(f"{hdr[0]:<18}{hdr[1]:>16}{hdr[2]:>14}{hdr[3]:>16}{hdr[4]:>9}{hdr[5]:>8}")
    for grp, _, _ in GROUPS:
        g = [r for r in rows if r["group"] == grp]
        raw = np.array([r["relL2_raw"] for r in g])
        res = np.array([r["relL2_rescaled"] for r in g])
        cos = np.array([r["cosine"] for r in g])
        ps = np.mean([r["p_success_final"] for r in g])
        qpu = sum(r["qpu_charge_s"] for r in g)
        print(f"{grp:<18}{raw.mean():>8.4f}+/-{raw.std():<5.3f}"
              f"{res.mean():>7.4f}+/-{res.std():<5.3f}"
              f"{cos.mean():>8.4f}+/-{cos.std():<5.3f}"
              f"{ps:>9.4f}{qpu:>8}")

    # --- figure -------------------------------------------------------
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({
        "font.size": 10,
        "axes.grid": True,
        "grid.alpha": 0.3,
        "axes.axisbelow": True,
        "figure.dpi": 150,
    })
    C_HW, C_FLOOR, C_NOISE = "#0072B2", "#009E73", "#D55E00"  # Okabe-Ito

    labels = [lbl for _, lbl, _ in GROUPS]
    xpos = np.arange(len(GROUPS))
    rng = np.random.default_rng(0)  # jitter only; not physics

    fig, (axc, axl) = plt.subplots(1, 2, figsize=(10.5, 4.8))

    # (a) cosine per trial + mean/std
    for i, (grp, _, _) in enumerate(GROUPS):
        g = [r for r in rows if r["group"] == grp]
        cvals = np.array([r["cosine"] for r in g])
        jit = (rng.random(cvals.size) - 0.5) * 0.28
        axc.scatter(xpos[i] + jit, cvals, s=28, color=C_HW, alpha=0.55,
                    edgecolor="none", zorder=3)
        axc.errorbar(xpos[i], cvals.mean(), yerr=cvals.std(), fmt="D",
                     color=C_HW, ms=8, capsize=5, lw=2, zorder=4)
    axc.axhline(0.0, color=C_NOISE, ls="--", lw=1.4)
    axc.text(len(GROUPS) - 1, 0.0, " pure noise (cos=0)", color=C_NOISE,
             va="bottom", ha="right", fontsize=8)
    axc.set_xticks(xpos)
    axc.set_xticklabels(labels, fontsize=8.5)
    axc.set_ylabel("cosine similarity vs FTCS truth")
    axc.set_title("(a) shape survival  (10 trials/group)", fontsize=10)
    axc.set_ylim(-0.25, 0.35)

    # (b) raw relL2 per trial (log) + SV floors + depolarization line
    for i, (grp, _, floor) in enumerate(GROUPS):
        g = [r for r in rows if r["group"] == grp]
        lvals = np.array([r["relL2_raw"] for r in g])
        jit = (rng.random(lvals.size) - 0.5) * 0.28
        axl.scatter(xpos[i] + jit, lvals, s=28, color=C_HW, alpha=0.55,
                    edgecolor="none", zorder=3)
        axl.errorbar(xpos[i], lvals.mean(), yerr=lvals.std(), fmt="D",
                     color=C_HW, ms=8, capsize=5, lw=2, zorder=4)
        # per-group statevector floor tick (dashed, classical, no shot noise)
        axl.plot([xpos[i] - 0.35, xpos[i] + 0.35], [floor, floor],
                 color=C_FLOOR, ls="--", lw=1.6, zorder=2)
    axl.axhline(1.0, color=C_NOISE, ls="--", lw=1.4)
    axl.text(len(GROUPS) - 1, 1.0, " full depolarization (relL2=1)",
             color=C_NOISE, va="bottom", ha="right", fontsize=8)
    axl.text(0, GROUPS[0][2], " SV floor (classical, no shot noise)",
             color=C_FLOOR, va="bottom", ha="left", fontsize=8)
    axl.set_yscale("log")
    axl.set_ylim(8e-5, 1.6)
    axl.set_xticks(xpos)
    axl.set_xticklabels(labels, fontsize=8.5)
    axl.set_ylabel("relative L2 vs FTCS truth")
    axl.set_title("(b) accuracy vs statevector floor", fontsize=10)

    fig.suptitle(
        "HW4  q8 Cole-Hopf on ibm_kingston  (nu=0.03, Re=10, T=0.2, "
        "shots=$2^{16}$, ~19k routed CZ)",
        fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    png = os.path.join(HERE, "hw4_variance.png")
    fig.savefig(png, dpi=150, bbox_inches="tight")
    print("wrote", os.path.relpath(png, REPO))


if __name__ == "__main__":
    main()
