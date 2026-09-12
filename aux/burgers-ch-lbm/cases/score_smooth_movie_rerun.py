#!/usr/bin/env python3
"""Offline rescore the ch_smooth_movie_rerun HW trials vs the paper FTCS-800
truth, and validate the method against Melvina's four June paper-table values.

Method (matches paper_cases_table col S, "L2 (rel vs FTCS 800)"):
  * build the sine IC (A=0.3) on a >=800-pt periodic grid that contains the
    q=3 (N=8) nodes as an exact subset (make_reference_grid),
  * evolve FTCS via solve_burgers_subsampled to the final frame (T=0.225),
    subsample to the 8 q-nodes -> the FTCS-800 truth,
  * relL2(u_final_method, truth) = ||u - truth|| / ||truth||.
Also reports an amplitude-rescaled relL2 (LSQ scalar alpha) and cosine, since
NISQ CH output is attenuation-dominated.

Run with the ch-lbm venv python.
"""
from __future__ import annotations
import glob, json, os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))

# --- smooth_movie op point (paper rows #19-22) ------------------------------
Q, A, NU, CFL, N_STEPS, BC = 3, 0.3, 0.08, 0.3, 6, "periodic"
REF_POINTS = 800
N = 2 ** Q
DX = 1.0 / N
DT = CFL * DX


def _rhs_periodic(u, dx, nu):
    """FTCS RHS, O(N) roll form of lib_fd.compute_rhs_shift (periodic).

    grad = (u_{j+1}-u_{j-1})/(2dx); lap = (u_{j-1}+u_{j+1}-2u_j)/dx^2;
    rhs = nu*lap - u*grad.  Bit-equivalent to the dense shift-matrix
    stencil, without building N x N matrices."""
    up, um = np.roll(u, -1), np.roll(u, 1)      # u_{j+1}, u_{j-1}
    grad = (up - um) / (2.0 * dx)
    lap = (um + up - 2.0 * u) / (dx * dx)
    return nu * lap - u * grad


def ftcs800_full_frames() -> tuple[np.ndarray, list[np.ndarray]]:
    """FTCS-800 truth at FULL 800-pt resolution: (x_ref, frames[0..N_STEPS]).

    The fine reference curve itself, before sampling to the 8 q-nodes -- used
    to draw a smooth truth line in the u(x) profile plots.  Mirrors
    make_reference_grid (periodic, k=ceil(800/8)=100 -> 800 pts) and
    solve_burgers_subsampled (sub-step to the FTCS diffusion floor).
    ftcs800_truth_frames subsamples THESE frames, so the two never diverge."""
    k = max(1, int(np.ceil(REF_POINTS / N)))
    n_ref = k * N
    x_ref = (1.0 / n_ref) * np.arange(n_ref)   # length = N*dx = 1.0
    dx_ref = x_ref[1] - x_ref[0]
    u = A * np.sin(2.0 * np.pi * x_ref)        # initial_condition_sine * A
    dt_stable = 0.25 * dx_ref * dx_ref / NU
    sub = max(1, int(np.ceil(DT / dt_stable)))
    dt_sub = DT / sub
    frames = [u.copy()]
    for _ in range(N_STEPS):
        for _ in range(sub):
            u = u + dt_sub * _rhs_periodic(u, dx_ref, NU)
        frames.append(u.copy())
    return x_ref, frames


def ftcs800_truth_frames() -> list[np.ndarray]:
    """FTCS-800 truth at each macro frame [0..N_STEPS] on the 8 q-nodes.

    q-nodes are an exact subset of the 800-pt grid (take=[0,100,..,700]);
    subsamples ftcs800_full_frames so the fine and node-level references
    are the same evolution."""
    k = max(1, int(np.ceil(REF_POINTS / N)))
    take = np.arange(N) * k
    _, frames = ftcs800_full_frames()
    return [f[take].copy() for f in frames]


def rel_l2(u, ref):
    return float(np.linalg.norm(u - ref) / np.linalg.norm(ref))


def cosine(u, ref):
    n = np.linalg.norm(u) * np.linalg.norm(ref)
    return float(np.dot(u, ref) / n) if n else float("nan")


def rescaled_rel_l2(u, ref):
    """relL2 after best-fit scalar alpha = <u,ref>/<u,u> (attenuation fix)."""
    denom = float(np.dot(u, u))
    alpha = float(np.dot(u, ref) / denom) if denom else 1.0
    return rel_l2(alpha * u, ref), alpha


def frames_of(path) -> dict[int, np.ndarray] | None:
    """Find a solution_steps dict {frame:int -> field} anywhere in a JSON."""
    d = json.load(open(path))

    def dig(obj):
        if isinstance(obj, dict):
            ss = obj.get("solution_steps")
            if isinstance(ss, dict) and ss:
                return ss
            for vv in obj.values():
                r = dig(vv)
                if r is not None:
                    return r
        elif isinstance(obj, list):
            for vv in obj:
                r = dig(vv)
                if r is not None:
                    return r
        return None

    ss = dig(d)
    if ss is None:
        return None
    return {int(k): np.asarray(v, dtype=float) for k, v in ss.items()}


def _stats(vals):
    a = np.array(vals, dtype=float)
    return a.mean(), a.std(), a.min(), a.max()


def main():
    truth = ftcs800_truth_frames()      # truth[frame], frame 0..6
    print(f"FTCS-{REF_POINTS} truth norms by frame (T=k*{DT:g}):")
    print("  " + "  ".join(f"f{k}:{np.linalg.norm(truth[k]):.3f}"
                           for k in range(N_STEPS + 1)))
    print()

    # ---- VALIDATION: paper rows #19-22 are the steps=1 point => FRAME 1 -
    june_root = os.path.join(
        REPO, "q8020-cfd-experiments", "results", "burgers-ch-lbm-June2026",
        "real-qc", "hardware_runs")
    paper = {"kingston": 0.634146, "fez": 0.595078,
             "boston": 0.813514, "miami": 0.576395}
    print("=== VALIDATION: June FRAME 1 (single step) vs paper col S ===")
    print(f"{'device':9} {'paper':>9} {'frame1 relL2':>13} {'match?':>7} "
          f"{'cos':>7}")
    for dev, tgt in paper.items():
        ap = os.path.join(june_root, f"smooth_movie_{dev}",
                          "method_compare", "cole_hopf_circuit",
                          "q8020_artifacts_0.json")
        fr = frames_of(ap)
        if not fr or 1 not in fr:
            print(f"{dev:9} {tgt:9.4f}   NO frame1")
            continue
        u1 = fr[1]
        r = rel_l2(u1, truth[1])
        ok = "OK" if abs(r - tgt) < 0.02 else ("~" if abs(r - tgt) < 0.05 else "XX")
        print(f"{dev:9} {tgt:9.4f} {r:13.4f} {ok:>7} {cosine(u1, truth[1]):7.4f}")
    print()

    # ---- NEW RUN: per-frame relL2 vs FTCS-800, all successful trials ----
    new_root = os.path.join(
        REPO, "q8020-cfd-experiments", "results", "burgers-ch-lbm",
        "ch_smooth_movie_rerun", "2026-09-10", "_0ca9db0f")
    # per_dev[dev][frame] = list of relL2 across trials
    per_dev = {}
    for dev in ("kingston", "fez", "miami", "boston"):
        by_frame = {k: [] for k in range(1, N_STEPS + 1)}
        n_tr = 0
        for tdir in sorted(glob.glob(os.path.join(new_root, dev, "trial_*"))):
            mp = glob.glob(os.path.join(tdir, "q8020_metadata_*.json"))
            if not mp:
                continue
            fr = frames_of(mp[0])
            if not fr:
                continue
            n_tr += 1
            for k in range(1, N_STEPS + 1):
                if k in fr and np.all(np.isfinite(fr[k])):
                    by_frame[k].append(rel_l2(fr[k], truth[k]))
        per_dev[dev] = (n_tr, by_frame)

    print("=== NEW RUN: relL2 vs FTCS-800, per frame (mean +/- std, n trials) ===")
    print("frame 1 == paper single-step point (compare to col S above)\n")
    hdr = "device    n  " + " ".join(f"{'f'+str(k):>14}" for k in range(1, N_STEPS + 1))
    print(hdr)
    for dev, (n_tr, by_frame) in per_dev.items():
        if n_tr == 0:
            print(f"{dev:9} 0   (no successful trials)")
            continue
        cells = []
        for k in range(1, N_STEPS + 1):
            v = by_frame[k]
            if v:
                m, s, _, _ = _stats(v)
                cells.append(f"{m:.3f}±{s:.3f}")
            else:
                cells.append("-")
        print(f"{dev:9} {n_tr:<2} " + " ".join(f"{c:>14}" for c in cells))

    # frame-1 focused summary (the paper-comparable number)
    print("\n=== FRAME-1 (paper-comparable) summary ===")
    print(f"{'device':9} {'paper(Jun)':>10} {'new mean':>9} {'std':>7} "
          f"{'min':>7} {'max':>7} {'n':>3}")
    for dev, (n_tr, by_frame) in per_dev.items():
        v = by_frame.get(1, [])
        p = paper.get(dev)
        ps = f"{p:.4f}" if p else "-"
        if v:
            m, s, lo, hi = _stats(v)
            print(f"{dev:9} {ps:>10} {m:9.4f} {s:7.4f} {lo:7.4f} {hi:7.4f} {len(v):>3}")
        else:
            print(f"{dev:9} {ps:>10}   (no data)")


if __name__ == "__main__":
    main()
