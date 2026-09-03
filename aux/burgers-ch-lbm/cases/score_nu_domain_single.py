#!/usr/bin/env python3
"""Score the SINGLE-MODE CH nu-domain sweep vs a stable FTCS-800 truth.

Reads the sweep produced by nu_domain_q8_single.toml directly out of the
experiments results tree.  Every case (CH bond-4, CH bond-16, and the
ftcs_reference truth) lives in one run dir; parameters come from each
case's rich q8020_case_0.json metadata (method, nu, bond_dim, q,
n_steps, cfl) -- no command-string parsing.

For each nu we compute, per bond arm, the final-field error of the CH
solution against the ftcs_reference truth at the SAME nu:
  * relL2  = ||u_CH - u_FTCS|| / ||u_FTCS||   (the domain-of-utility metric)
  * cosine = <u_CH, u_FTCS> / (||u_CH|| ||u_FTCS||)  (shape agreement)
Re = A / nu with A = 0.3.

Outputs (default under <run_dir_parent>/analysis, i.e. the results tree,
with copies of code + plot living in aux/): a printed table, a CSV, and
a relL2-vs-Re PNG with both bond arms plus a nu top axis.

Run (from anywhere):
    q8020-cfd-ch-lbm/.venv/bin/python \\
        q8020-cfd-experiments/aux/burgers-ch-lbm/cases/score_nu_domain_single.py \\
        [--run-dir <sweep run dir>] [--outdir <dir>]
"""
from __future__ import annotations

import argparse
import csv
import json
import os
from glob import glob

import numpy as np

A_AMPLITUDE = 0.3  # --ic-amplitude; Re = A / nu

# default sweep output tree (matches nu_domain_q8_single.toml _output_dir)
DEFAULT_ROOT = (
    "/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/results/"
    "burgers-ch-lbm/ch_q8_nu_domain_single"
)
# analysis + plots live in aux/ (results/ holds only raw sweep output)
DEFAULT_OUTDIR = (
    "/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/"
    "burgers-ch-lbm/ch-q8-nu-domain-single-analysis-2026-09-02"
)


def load_json(path: str):
    try:
        with open(path) as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def first(v):
    """Fragments are sometimes a 1-element list, sometimes a dict."""
    if isinstance(v, list):
        return v[0] if v else {}
    return v or {}


def field(results0: dict) -> np.ndarray | None:
    """Final solved field: u_final_method (CH or ftcs), else classical."""
    for key in ("u_final_method", "u_final_quantum", "u_final_classical"):
        v = results0.get(key)
        if isinstance(v, list) and v:
            arr = np.asarray(v, dtype=float)
            if arr.size and np.all(np.isfinite(arr)):
                return arr
    return None


def all_run_dirs(root: str) -> list[str]:
    """Every finished <root>/<date>/_<workflow> run dir, oldest first.

    The high-Re extension appends a second run dir to the same output
    tree; merging all of them (deduped downstream by method/nu/bond,
    newest winning) lets one plot span every swept nu."""
    cands = [d for d in glob(os.path.join(root, "*", "_*"))
             if os.path.isdir(d)
             and glob(os.path.join(d, "*", "q8020_case_0.json"))]
    if not cands:
        raise SystemExit(f"No finished sweep run dirs under {root}")
    return sorted(cands, key=os.path.getmtime)


def ref_points_of(case_dir: str) -> int | None:
    """--ref-points from the recorded command line (ftcs_reference only)."""
    import re
    pa = load_json(os.path.join(case_dir, "pipeline_args.json")) or {}
    cmd = pa.get("cmd", "")
    cmd = " ".join(cmd) if isinstance(cmd, list) else str(cmd)
    m = re.search(r"--ref-points\s+(\d+)", cmd)
    return int(m.group(1)) if m else None


def collect_cases(run_dir: str) -> list[dict]:
    """One record per case: {method, nu, bond, ref_points, u, dir}."""
    cases = []
    for cpath in glob(os.path.join(run_dir, "*", "q8020_case_0.json")):
        c = first(load_json(cpath))
        d = os.path.dirname(cpath)
        u = field(first(load_json(os.path.join(d, "q8020_results_0.json"))))
        cases.append({
            "method": c.get("method"),
            "nu": None if c.get("nu") is None else round(float(c["nu"]), 6),
            "bond": c.get("bond_dim"),
            "ref_points": ref_points_of(d),
            "u": u,               # None if the run blew up / not finite
            "dir": d,
        })
    return cases


def rel_l2(u: np.ndarray, ref: np.ndarray) -> float:
    return float(np.linalg.norm(u - ref) / np.linalg.norm(ref))


def cosine(u: np.ndarray, ref: np.ndarray) -> float:
    n = np.linalg.norm(u) * np.linalg.norm(ref)
    return float(np.dot(u, ref) / n) if n else float("nan")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=DEFAULT_ROOT,
                    help="sweep output tree (default: the single-mode tree)")
    ap.add_argument("--run-dir", default=None,
                    help="explicit run dir; default = newest finished under --root")
    ap.add_argument("--outdir", default=None,
                    help="where to write CSV/PNG (default: the aux/ analysis dir)")
    args = ap.parse_args()

    if args.run_dir:
        run_dirs = [args.run_dir]
    else:
        run_dirs = all_run_dirs(args.root)
    run_dir = run_dirs[-1]  # for messages/outdir default

    # Merge every run dir; dedupe by (method, nu, bond) with the newest
    # run winning (run_dirs is oldest-first, so a later assignment wins).
    merged: dict[tuple, dict] = {}
    for d in run_dirs:
        for c in collect_cases(d):
            merged[(c["method"], c["nu"], c["bond"])] = c
    cases = list(merged.values())

    # index truths by nu
    truths = {c["nu"]: c for c in cases
              if c["method"] == "ftcs_reference" and c["u"] is not None}
    ch = [c for c in cases if c["method"] == "cole_hopf_circuit"]

    # Per-Re FTCS reference (ref-points), for the shaded bands on the plot.
    re_ref = sorted((A_AMPLITUDE / nu, (t.get("ref_points") or 0))
                    for nu, t in truths.items() if nu)

    if not ch:
        raise SystemExit(f"No CH cases under {args.root}")

    rows = []
    for c in sorted(ch, key=lambda r: (r["bond"] or 0, r["nu"])):
        nu = c["nu"]
        re = A_AMPLITUDE / nu if nu else float("nan")
        t = truths.get(nu)
        if c["u"] is None:
            rows.append({"bond": c["bond"], "nu": nu, "Re": round(re, 3),
                         "relL2": None, "cos": None, "verdict": "CH_nonfinite"})
            continue
        if t is None:
            rows.append({"bond": c["bond"], "nu": nu, "Re": round(re, 3),
                         "relL2": None, "cos": None, "verdict": "no_truth"})
            continue
        u, ref = c["u"], t["u"]
        n = min(u.size, ref.size)
        r = rel_l2(u[:n], ref[:n])
        verdict = ("diverged" if r > 2 else
                   "good" if r < 0.5 else "marginal")
        rows.append({"bond": c["bond"], "nu": nu, "Re": round(re, 3),
                     "relL2": r, "cos": cosine(u[:n], ref[:n]),
                     "verdict": verdict})

    # --- print table --------------------------------------------------
    print("\nmerged run dirs:")
    for d in run_dirs:
        print(f"  {d}")
    print()
    hdr = ("bond", "nu", "Re", "relL2", "cos", "verdict")
    print(f"{hdr[0]:>5} {hdr[1]:>8} {hdr[2]:>7} {hdr[3]:>10} "
          f"{hdr[4]:>8}  {hdr[5]}")
    for r in rows:
        rl = "-" if r["relL2"] is None else f"{r['relL2']:.4f}"
        co = "-" if r["cos"] is None else f"{r['cos']:.4f}"
        print(f"{str(r['bond']):>5} {r['nu']:>8} {r['Re']:>7} "
              f"{rl:>10} {co:>8}  {r['verdict']}")

    # --- CSV ----------------------------------------------------------
    outdir = args.outdir or DEFAULT_OUTDIR
    os.makedirs(outdir, exist_ok=True)
    csv_path = os.path.join(outdir, "nu_domain_single_scores.csv")
    with open(csv_path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"\nwrote {csv_path}")

    # --- plot: relL2 vs Re, one line per bond arm ---------------------
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib unavailable; skipped PNG")
        return

    fig, ax = plt.subplots(figsize=(8.5, 5.5))
    # bond-8 and bond-16 coincide to all digits (both already exact for
    # these phi states), so bond-16 is drawn first as filled squares and
    # bond-8 on TOP as larger OPEN markers with a dashed line -- the green
    # rings stay visible around the blue squares along the overlap.
    arms = (
        (16, dict(marker="s", color="#0058a3", lw=1.7, ms=7,
                  label="bond-dim 16", zorder=2)),
        (4,  dict(marker="o", color="#c1272d", lw=1.7, ms=7,
                  label="bond-dim 4", zorder=3)),
        (8,  dict(marker="^", mfc="none", mec="#2ca02c", color="#2ca02c",
                  ls="--", lw=1.4, ms=11, mew=1.8,
                  label="bond-dim 8", zorder=4)),
    )
    for bond, style in arms:
        pts = sorted((r for r in rows if r["bond"] == bond
                      and r["relL2"] is not None), key=lambda r: r["Re"])
        if not pts:
            continue
        xs = [p["Re"] for p in pts]
        ys = [p["relL2"] for p in pts]
        ax.plot(xs, ys, **style)

    ax.set_xscale("log")
    ax.set_yscale("log")

    # Shade the plot into bands by which FTCS reference (ref-points) each
    # Re region uses.  Each band spans the midpoints between adjacent Re
    # points; adjacent bands with the same ref-points merge, so the whole
    # Re<150 stretch reads as one "FTCS 800" band and each finer ref gets
    # its own band labelled "FTCS <ref-points>".
    if re_ref:
        xlo, xhi = ax.get_xlim()
        res = [r for r, _ in re_ref]
        # geometric-mean edges between neighbours (log x-axis)
        edges = [xlo] + [
            (res[i] * res[i + 1]) ** 0.5 for i in range(len(res) - 1)
        ] + [xhi]
        # merge consecutive same-ref bands
        bands = []  # (left, right, ref_points)
        for i, (_, rp) in enumerate(re_ref):
            lft, rgt = edges[i], edges[i + 1]
            if bands and bands[-1][2] == rp:
                bands[-1] = (bands[-1][0], rgt, rp)
            else:
                bands.append((lft, rgt, rp))
        ytop = ax.get_ylim()[1]
        for j, (lft, rgt, rp) in enumerate(bands):
            if j % 2:  # shade alternating bands so boundaries read clearly
                ax.axvspan(lft, rgt, color="#f2a900", alpha=0.10, zorder=0)
            if j:      # boundary line between refs
                ax.axvline(lft, color="#cc9a00", lw=0.8, ls=":", zorder=1)
            ax.text((lft * rgt) ** 0.5, ytop, f"FTCS {rp}",
                    color="#7a5c00", fontsize=7.5, rotation=90,
                    va="top", ha="center")

    ax.set_xlabel("Re = A/nu   (A = 0.3)")
    ax.set_ylabel("relL2 vs FTCS (shock-resolved)")
    ax.set_title("Cole-Hopf domain of utility vs Re, S=1, k=512\n"
                 "q=8, A=0.3, shots=0")
    ax.grid(True, which="both", alpha=0.25)
    # draw order is 16/4/8 (so bond-8 rings sit on top); show the legend
    # in ascending bond order 4, 8, 16 regardless of draw order.
    handles, labels = ax.get_legend_handles_labels()
    order = sorted(range(len(labels)),
                   key=lambda i: int(labels[i].split()[-1]))
    ax.legend([handles[i] for i in order], [labels[i] for i in order],
              loc="best")

    # top axis: nu (Re = A/nu, so nu = A/Re).  Guard the div at the probe
    # point 0 that matplotlib feeds the transform when picking ticks.
    def _re_to_nu(re):
        re = np.asarray(re, dtype=float)
        return np.divide(A_AMPLITUDE, re, out=np.full_like(re, np.nan),
                         where=re != 0)

    def _nu_to_re(nu):
        nu = np.asarray(nu, dtype=float)
        return np.divide(A_AMPLITUDE, nu, out=np.full_like(nu, np.nan),
                         where=nu != 0)

    secax = ax.secondary_xaxis("top", functions=(_re_to_nu, _nu_to_re))
    secax.set_xlabel("viscosity  nu")

    png_path = os.path.join(outdir, "relL2_vs_Re_single.png")
    fig.savefig(png_path, dpi=150, bbox_inches="tight")
    print(f"wrote {png_path}")


if __name__ == "__main__":
    main()
