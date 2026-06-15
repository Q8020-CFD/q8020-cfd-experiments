#!/usr/bin/env python3
"""Post-hoc reprocessing of the q3 Cole-Hopf "stunt" hardware run
(_0ed1ee05/ae17983c, ibm_kingston, job d8o2g3832u0s73fd4msg).

The on-device run reported rel-L2 vs FTCS = 2.19, but the reconstructed
profile is NOT random: it correlates 0.54 with the reference and is mainly
*amplitude-inflated* (||u_hw||=0.43 vs ||u_ref||=0.17).  The inverse
Cole-Hopf u = -2 nu d(log phi)/dx is INVARIANT to the overall scale of phi
(log(c*phi) -> the constant drops under the derivative), so the inflation
comes entirely from high-frequency RIPPLE in the measured phi, amplified by
the log-derivative.  That ripple is exactly what the spectral low-pass
(phi_modes) removes.

This script pulls the saved hardware counts back from the IBM job, then
re-runs ONLY the classical reconstruction at several phi_modes cutoffs and
compares to a stable (substepped) FTCS reference.  No new QPU time.

Run:  python reprocess_denoise.py
Writes: reprocess_results.json next to this file.
"""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, "/home/agallojr/proj/src/q8020/q8020-mps-burgers/src")
from burgers_ch_hw_runner import CASES, build_inputs, compute_reference
from burgers_cole_hopf_circuit import post_select_counts, permute_from_encoding
from burgers_cole_hopf import fourier_low_pass_phi, cole_hopf_inverse
from q8020_cfd_qutil.job import get_job_result

JOB_ID = "d8o2g3832u0s73fd4msg"
HERE = Path(__file__).resolve().parent
RUN = HERE.parent  # the experiment dir ae17983c


def rl2(a, b):
    a, b = np.asarray(a), np.asarray(b)
    return float(np.linalg.norm(a - b) / np.linalg.norm(b))


def main():
    case = dict(CASES["smooth_stunt"])
    q = case["q"]
    u0, x, dt, nu = build_inputs(case)
    dx = float(x[1] - x[0])
    N = 1 << q

    # Stable reference at the same physical time T = n_steps*dt.
    ref = np.asarray(compute_reference(u0, x, nu, dt, case["n_steps"],
                                       case["bc"])[-1])

    # --- pull the hardware counts back from the IBM job (no new QPU) ---
    res = get_job_result(JOB_ID)
    counts = res["results"][0]["counts"]
    n_kept, data_counts = post_select_counts(counts, q)
    shots = sum(counts.values())
    p_success = n_kept / shots

    # Reconstruct phi shape: amplitude = sqrt(probability), phase-free
    # (the CH field is non-negative by construction).  Overall scale is
    # irrelevant to u, so we leave psi un-rescaled.
    psi = np.zeros(N)
    for bits, cnt in data_counts.items():
        psi[int(bits, 2)] = np.sqrt(cnt / n_kept)
    psi = permute_from_encoding(psi, q, "binary")

    # Sweep the spectral cutoff.  phi_modes>=N//2 == no filtering (what the
    # run used, phi_modes=8 on an 8-point grid).
    out = {
        "job_id": JOB_ID,
        "backend": res.get("backend_name"),
        "q": q, "nu": nu, "dt": dt, "n_steps": case["n_steps"],
        "T": case["n_steps"] * dt,
        "shots": shots, "n_kept": n_kept, "p_success": p_success,
        "reference_ftcs_stable": ref.tolist(),
        "ref_norm": float(np.linalg.norm(ref)),
        "sweep": [],
    }
    for modes in [0, 1, 2, 3, 4]:   # 0 = no filter; 4 = Nyquist (no-op at q3)
        phi = fourier_low_pass_phi(psi.copy(), modes) if modes > 0 else psi.copy()
        u = cole_hopf_inverse(phi, dx, nu, bc=case["bc"])
        u = np.asarray(u)
        r = rl2(u, ref)
        # also a norm-matched variant (rescale u to the reference norm) to
        # separate "wrong shape" from "wrong amplitude"
        u_rescaled = u * (np.linalg.norm(ref) / (np.linalg.norm(u) or 1.0))
        out["sweep"].append({
            "phi_modes": modes,
            "label": "no filter (= the run)" if modes in (0, 4) else f"low-pass {modes}",
            "rel_l2": r,
            "rel_l2_norm_matched": rl2(u_rescaled, ref),
            "u_norm": float(np.linalg.norm(u)),
            "corr": float(np.corrcoef(u, ref)[0, 1]),
            "u": u.tolist(),
        })

    best = min(out["sweep"], key=lambda s: s["rel_l2"])
    out["best"] = {"phi_modes": best["phi_modes"], "rel_l2": best["rel_l2"]}

    (HERE / "reprocess_results.json").write_text(json.dumps(out, indent=2))

    print(f"job {JOB_ID}  shots={shots}  n_kept={n_kept}  p_success={p_success:.3f}")
    print(f"reference ||u||={out['ref_norm']:.3f}  (T={out['T']:.4f}, q={q})\n")
    print("phi_modes  rel-L2   rel-L2(norm-matched)  corr   ||u||")
    for s in out["sweep"]:
        print(f"  {s['phi_modes']:>2}      {s['rel_l2']:.4f}      "
              f"{s['rel_l2_norm_matched']:.4f}          {s['corr']:.3f}  {s['u_norm']:.3f}")
    print(f"\nBEST phi_modes={out['best']['phi_modes']}  rel-L2={out['best']['rel_l2']:.4f}")
    print("wrote", HERE / "reprocess_results.json")


if __name__ == "__main__":
    main()
