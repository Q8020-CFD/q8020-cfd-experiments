#!/usr/bin/env python3
"""Score the CH nu-domain sweep against a stable FTCS reference (offline).

The nu_domain run's in-process FTCS reference blew up for nu >= 0.03
(explicit-diffusion instability), so those cases stored final_error = NaN
even though the CH field itself (results.u_final_method) is finite and on
disk.  This script rebuilds the domain-of-utility curve by scoring each
saved CH field against a STABLE, sub-stepped `ftcs_reference` truth at the
identical operating point, sourced from two places and joined by nu:

  * BORROWED  : q8=n400=cfl0.1 ftcs_reference runs already on disk
                (burgers_ab_mutual_q8_nu0XX / show_q8_ch_smooth) covering
                nu in {0.015, 0.02, 0.03, 0.05, 0.08}.
  * TOP-UP    : the three nu with no truth yet (0.010, 0.0125, 0.10),
                produced by ftcs_ref_nu_domain_topup.toml.

Outputs: a printed table, a CSV, and a relL2-vs-nu PNG (seg5 & seg10).

Run (from anywhere):
    q8020-cfd-ch-lbm/.venv/bin/python \\
        q8020-cfd-experiments/aux/burgers-ch-lbm/cases/score_nu_domain.py
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import re
from glob import glob

import numpy as np

# --- operating point the truth must match exactly ---------------------
Q_EXPECT = 8
NSTEPS_EXPECT = 400
CFL_EXPECT = 0.1
DX = 1.0 / 256.0
# old in-process ref: diff# = nu*dt/dx^2 = nu*(cfl*dx)/dx^2 = nu*cfl/dx.
# It goes unstable (diff# > 0.5) above this nu.
FTCS_STABILITY_NU = 0.5 / (CFL_EXPECT / DX)  # = 0.5*dx/cfl ~ 0.0195

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))  # experiments repo root


def load_json(path: str):
    try:
        with open(path) as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def first(v):
    """Result fragments are sometimes a 1-element list, sometimes a dict."""
    if isinstance(v, list):
        return v[0] if v else {}
    return v or {}


def field(results0: dict) -> np.ndarray | None:
    """The solved final field: u_final_method (CH or ftcs), else classical."""
    for key in ("u_final_method", "u_final_quantum", "u_final_classical"):
        v = results0.get(key)
        if isinstance(v, list) and v:
            arr = np.asarray(v, dtype=float)
            if arr.size and np.all(np.isfinite(arr)):
                return arr
    return None


def load_trajectory(case_dir: str) -> dict[int, np.ndarray]:
    """Per-frame field snapshots {step: array} from artifacts.solution_steps.

    CH cases store the CH trajectory here; ftcs_reference cases store the
    (sub-sampled) FTCS trajectory.  Non-finite frames are kept as-is so the
    caller can see where a run blew up."""
    a = first(load_json(os.path.join(case_dir, "q8020_artifacts_0.json")))
    ss = a.get("solution_steps") if isinstance(a, dict) else None
    if not isinstance(ss, dict):
        return {}
    out: dict[int, np.ndarray] = {}
    for k, v in ss.items():
        if isinstance(v, list) and v:
            out[int(k)] = np.asarray(v, dtype=float)
    return out


def truth_roots(repo: str, extra: list[str] | None = None) -> list[str]:
    """Where stable ftcs_reference truths live: borrowed ab-q8 runs, the
    top-up run in the repo tree, and the raw top-up run dir."""
    return [
        os.path.join(repo, "results", "burgers-ch-lbm-June2026", "burgers_ab"),
        os.path.join(repo, "results", "burgers-ch-lbm", "ch_ftcs_refs_nu_domain"),
        os.path.expanduser("~/q8020-runs/ch_ftcs_refs_nu_domain"),
    ] + (extra or [])


def cmd_of(case_dir: str) -> str:
    pa = load_json(os.path.join(case_dir, "pipeline_args.json")) or {}
    cmd = pa.get("cmd", "")
    return " ".join(cmd) if isinstance(cmd, list) else str(cmd)


def flag(cmd: str, name: str) -> float | None:
    m = re.search(rf"{re.escape(name)}\s+([0-9.eE+-]+)", cmd)
    return float(m.group(1)) if m else None


# --- collect CH cases -------------------------------------------------
def collect_ch(ch_root: str) -> list[dict]:
    cases = []
    for r0 in glob(os.path.join(ch_root, "**", "q8020_results_0.json"),
                   recursive=True):
        d = os.path.dirname(r0)
        cmd = cmd_of(d)
        nu, seg = flag(cmd, "--nu"), flag(cmd, "--segment-size")
        if nu is None or seg is None:
            continue
        u = field(first(load_json(r0)))
        if u is None:
            continue
        cases.append({"nu": nu, "seg": int(seg), "u": u, "dir": d})
    return cases


# --- collect ftcs_reference truths, indexed by nu ---------------------
def collect_truths(roots: list[str]) -> dict[float, dict]:
    truths: dict[float, dict] = {}
    for root in roots:
        if not root or not os.path.isdir(root):
            continue
        for r1 in glob(os.path.join(root, "**", "q8020_results_1.json"),
                       recursive=True):
            rec = first(load_json(r1))
            if not isinstance(rec, dict):
                continue
            if "ftcs_reference" not in str(rec.get("method", "")):
                continue
            d = os.path.dirname(r1)
            case = first(load_json(os.path.join(d, "q8020_case_0.json")))
            # guard: identical grid / cadence / physics
            if int(rec.get("q") or case.get("q") or -1) != Q_EXPECT:
                continue
            if int(rec.get("n_steps") or -1) != NSTEPS_EXPECT:
                continue
            cfl = case.get("cfl")
            if cfl is not None and abs(float(cfl) - CFL_EXPECT) > 1e-9:
                continue
            u = field(first(load_json(os.path.join(d, "q8020_results_0.json"))))
            if u is None:
                continue
            nu = round(float(rec.get("nu")), 6)
            truths.setdefault(nu, {"u": u, "dir": d,
                                   "src": "topup" if "nu_domain" in root
                                   or "ftcs_refs_nu_domain" in root
                                   else "borrowed"})
    return truths


def match_truth(nu: float, truths: dict[float, dict]):
    for k, v in truths.items():
        if abs(k - nu) < 1e-6:
            return v
    return None


def rel_l2(u: np.ndarray, ref: np.ndarray) -> float:
    return float(np.linalg.norm(u - ref) / np.linalg.norm(ref))


def cosine(u: np.ndarray, ref: np.ndarray) -> float:
    n = np.linalg.norm(u) * np.linalg.norm(ref)
    return float(np.dot(u, ref) / n) if n else float("nan")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ch-root",
                    default=os.path.join(REPO, "results", "burgers-ch-lbm",
                                         "ch_q8_nu_domain"))
    ap.add_argument("--truth-root", action="append", default=None,
                    help="extra dir(s) to search for ftcs_reference truths")
    ap.add_argument("--outdir", default=None,
                    help="where to write table.csv / relL2_vs_nu.png "
                         "(default: <ch-root>/analysis)")
    args = ap.parse_args()

    ch = collect_ch(args.ch_root)
    truths = collect_truths(truth_roots(REPO, args.truth_root))
    if not ch:
        raise SystemExit(f"No CH cases found under {args.ch_root}")

    outdir = args.outdir or os.path.join(args.ch_root, "analysis")
    os.makedirs(outdir, exist_ok=True)

    rows = []
    for c in sorted(ch, key=lambda r: (r["seg"], r["nu"])):
        t = match_truth(c["nu"], truths)
        # diffusion number of the OLD in-process ref: nu*dt/dx^2, dt=cfl*dx
        diff_num = c["nu"] * (CFL_EXPECT * DX) / (DX * DX)
        if t is None:
            rows.append({"seg": c["seg"], "nu": c["nu"],
                         "diff_num": diff_num, "relL2": None, "cos": None,
                         "src": "MISSING", "verdict": "no truth yet"})
            continue
        u, ref = c["u"], t["u"]
        n = min(u.size, ref.size)
        r = rel_l2(u[:n], ref[:n])
        verdict = ("diverged" if r > 2 else
                   "good" if r < 0.5 else "marginal")
        rows.append({"seg": c["seg"], "nu": c["nu"], "diff_num": diff_num,
                     "relL2": r, "cos": cosine(u[:n], ref[:n]),
                     "src": t["src"], "verdict": verdict})

    # --- print table --------------------------------------------------
    hdr = ("seg", "nu", "old_diff#", "truth", "relL2", "cos", "verdict")
    print(f"{hdr[0]:>4} {hdr[1]:>8} {hdr[2]:>9} {hdr[3]:>9} "
          f"{hdr[4]:>10} {hdr[5]:>7}  {hdr[6]}")
    for r in rows:
        rl = "MISSING" if r["relL2"] is None else f"{r['relL2']:.4f}"
        co = "" if r["cos"] is None else f"{r['cos']:.4f}"
        print(f"{r['seg']:>4} {r['nu']:>8} {r['diff_num']:>9.3f} "
              f"{r['src']:>9} {rl:>10} {co:>7}  {r['verdict']}")
    unstable = FTCS_STABILITY_NU
    print(f"\nold in-process FTCS ref was unstable for nu > {unstable:.4f} "
          f"(diff# > 0.5); this table uses the stable sub-stepped truth.")
    missing = sorted({r["nu"] for r in rows if r["relL2"] is None})
    if missing:
        print(f"MISSING truths for nu={missing} -> run "
              f"ftcs_ref_nu_domain_topup.toml, then re-run this script.")

    # --- CSV ----------------------------------------------------------
    csv_path = os.path.join(outdir, "nu_domain_scores.csv")
    with open(csv_path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"\nwrote {csv_path}")

    # --- plot ---------------------------------------------------------
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib unavailable; skipped PNG")
        return

    fig, ax = plt.subplots(figsize=(8, 5.5))
    for seg, marker, color in ((5, "o", "#c1272d"), (10, "s", "#0058a3")):
        pts = sorted((r for r in rows if r["seg"] == seg
                      and r["relL2"] is not None), key=lambda r: r["nu"])
        if not pts:
            continue
        xs = [p["nu"] for p in pts]
        ys = [p["relL2"] for p in pts]
        seams = 400 // seg
        ax.plot(xs, ys, marker=marker, color=color, lw=1.6, ms=7,
                label=f"segment-size {seg}  (S={seams} seams)")
        # ring the points whose truth came from the top-up run
        tx = [p["nu"] for p in pts if p["src"] == "topup"]
        ty = [p["relL2"] for p in pts if p["src"] == "topup"]
        if tx:
            ax.scatter(tx, ty, s=150, facecolors="none",
                       edgecolors=color, linewidths=1.6, zorder=5)

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.axhline(1.0, ls="--", lw=1, color="grey", alpha=0.7)
    ax.text(0.99, 1.0, "relL2 = 1 (solution-scale error)", transform=ax.get_yaxis_transform(),
            fontsize=8, color="grey", va="bottom", ha="right")
    ax.axvline(FTCS_STABILITY_NU, ls=":", lw=1.3, color="green", alpha=0.8)
    ax.text(FTCS_STABILITY_NU * 1.03, 0.02, "old FTCS-ref\nstability limit",
            transform=ax.get_xaxis_transform(),
            fontsize=8, color="green", va="bottom", ha="left")

    ax.set_xlabel("viscosity  nu")
    ax.set_ylabel("relL2  (CH vs stable FTCS truth)")
    ax.set_title("CH domain of utility (q=8, A=0.3, CFL=0.1, n-steps=400)\n"
                 "open rings = truth from top-up run; others borrowed")
    ax.grid(True, which="both", alpha=0.25)
    ax.legend()
    png_path = os.path.join(outdir, "relL2_vs_nu.png")
    fig.savefig(png_path, dpi=150, bbox_inches="tight")
    print(f"wrote {png_path}")


if __name__ == "__main__":
    main()
