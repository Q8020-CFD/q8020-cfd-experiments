#!/usr/bin/env python3
"""ibm_fez: the June (n=1) vs September (n=10) smooth_movie gap.

Same device, same documented parameters, three months apart.  Asks whether
the gap is device drift, trial noise, or something in the stack, by pinning
each candidate against what the artifacts actually record.

Run with the ch-lbm venv python.
"""
from __future__ import annotations

import glob
import json
import os

import numpy as np

import boston_forensics as bf
from score_smooth_movie_rerun import (
    N,
    N_STEPS,
    cosine,
    ftcs800_truth_frames,
    rel_l2,
)

JUNE_FEZ = os.path.join(
    bf.EXP, "burgers-ch-lbm-June2026", "real-qc", "hardware_runs",
    "smooth_movie_fez")
SEP_ROOT = os.path.join(
    bf.EXP, "burgers-ch-lbm", "ch_smooth_movie_rerun", "2026-09-10",
    "_0ca9db0f", "fez")


def modes(u: np.ndarray) -> np.ndarray:
    return np.fft.rfft(u) / N


def measures(u: np.ndarray, ref: np.ndarray, sv1: np.ndarray,
             ceil1: float, pur_ceil: float) -> dict[str, float]:
    U = np.abs(modes(u))
    nrm = float(np.linalg.norm(u))
    return {
        "relL2": rel_l2(u, ref),
        "|U1|": float(U[1]),
        "|U1|/ceil": float(U[1]) / ceil1,
        "|U2|": float(U[2]),
        "||u||": nrm,
        "norm/noiseless": nrm / float(np.linalg.norm(sv1)),
        "purity/nl": (float(U[1]) / nrm) / pur_ceil,
        "cos vs nl": cosine(u, sv1),
        "ph(U1)": float(np.angle(modes(u)[1])),
        "ph(U2)": float(np.angle(modes(u)[2])),
    }


def circ_stats(ph: np.ndarray) -> tuple[float, float, float]:
    z = np.mean(np.exp(1j * ph))
    return float(np.angle(z)), float(abs(z)), float(
        np.sqrt(-2.0 * np.log(abs(z)))) if abs(z) > 0 else float("nan")


def main() -> None:
    truth = ftcs800_truth_frames()
    ref = truth[1]
    sv = bf.sim_frames("cd872d62")
    ceil1 = float(np.abs(modes(sv[1]))[1])
    pur_ceil = ceil1 / float(np.linalg.norm(sv[1]))

    jf = bf.june_frames("fez")
    sepf = bf.sep_frames("fez")

    print("=" * 78)
    print("1. Counts, and how the two epochs were configured")
    print("=" * 78)
    print(f"June  usable runs: {1 if jf else 0}   (one hardware run, "
          f"6 movie frames, no replicate anywhere in the tree)")
    print(f"Sept  usable runs: {len(sepf)}  (all 10 trials exit 0)")

    ja = json.load(open(os.path.join(JUNE_FEZ, "q8020_analysis_0.json")))
    jc = json.load(open(os.path.join(JUNE_FEZ, "q8020_case_0.json")))
    dt_ = ja.get("dry_run_transpile", {})
    sd = sorted(glob.glob(os.path.join(SEP_ROOT, "trial_*")))
    sa = json.load(open(os.path.join(sd[0], "q8020_analysis_0.json")))
    print()
    print(f"{'':30} {'June':>22} {'Sept trial_0':>22}")
    rows = [
        ("shots/segment", jc.get("shots"), sa.get("shots")),
        ("optimization_level",
         dt_.get("transpile_info", {}).get("optimization_level"),
         sa.get("optimization_level")),
        ("seed", 1234, sa.get("seed")),
        ("segments", ja.get("n_segments"), sa.get("n_circuits_executed")),
        ("circuit qubits", dt_.get("segment_qubits"), sa.get("n_qubits")),
        ("transpiled depth", dt_.get("transpiled_depth"),
         round(sa.get("avg_circuit_depth", float("nan")), 1)),
        ("transpiled 2q (cz)", dt_.get("transpiled_2q_gates"), "see ops"),
        ("total gate ops", sum(dt_.get("transpiled_ops", {}).values()),
         sa.get("avg_gate_count")),
        ("phi_modes", jc.get("phi_modes"), 8),
        ("bond_dim", jc.get("bond_dim"), None),
        ("TREX (measure_mitig.)", ja.get("measure_mitigation"), "auto->on"),
        ("dynamical_decoupling", ja.get("dynamical_decoupling"), "auto->on"),
    ]
    for k, a, b in rows:
        print(f"{k:30} {str(a):>22} {str(b):>22}")
    print(f"\nJune transpiled ops: {dt_.get('transpiled_ops')}")

    print()
    print("=" * 78)
    print("2. Calibration: did the DEVICE move between epochs?")
    print("=" * 78)
    jb = json.load(open(os.path.join(JUNE_FEZ, "q8020_backend_0.json")))
    sb = json.load(open(os.path.join(sd[0], "q8020_backend_0.json")))

    def med(b, key, sub=None):
        """Median of a backend metric.  t1/t2 are already in us in these
        files; gate_error is nested {gate: {qubit_pair: err}}."""
        v = b.get(key)
        if isinstance(v, dict):
            if sub is not None:
                v = v.get(sub, {})
            v = list(v.values())
        flat = [x for x in v if isinstance(x, (int, float))]
        return float(np.median(flat)) if flat else float("nan")

    print(f"{'metric':22} {'June':>12} {'Sept':>12} {'drift':>10}")
    for key, sub, lab in (("readout_error", None, "readout err"),
                          ("t1", None, "T1 (us)"),
                          ("t2", None, "T2 (us)"),
                          ("gate_error", "cz", "CZ err")):
        a, b = med(jb, key, sub), med(sb, key, sub)
        print(f"{lab:22} {a:12.5f} {b:12.5f} {(b-a)/a:+9.1%}")
    print(f"June backend captured_at: {jb.get('captured_at')}")
    print(f"Sept backend captured_at: {sb.get('captured_at')}")

    print()
    print("=" * 78)
    print("3. Frame-1 measures: June point vs the September distribution")
    print("=" * 78)
    jm = measures(jf[1], ref, sv[1], ceil1, pur_ceil)
    sm = [measures(t[1], ref, sv[1], ceil1, pur_ceil) for t in sepf]
    keys = ["relL2", "|U1|", "|U1|/ceil", "|U2|", "||u||",
            "norm/noiseless", "purity/nl", "cos vs nl"]
    print(f"{'measure':16} {'June':>9} {'Sep mean':>9} {'Sep sd':>8} "
          f"{'Sep min':>9} {'Sep max':>9} {'June-Sep':>9} {'in sd':>7} "
          f"{'June in Sep range?':>19}")
    for k in keys:
        v = np.array([m[k] for m in sm])
        d = jm[k] - v.mean()
        inr = "YES" if v.min() <= jm[k] <= v.max() else "NO"
        print(f"{k:16} {jm[k]:9.4f} {v.mean():9.4f} {v.std():8.4f} "
              f"{v.min():9.4f} {v.max():9.4f} {d:+9.4f} "
              f"{abs(d)/v.std():6.1f}x {inr:>19}")

    print()
    print("=" * 78)
    print("4. Mode PHASES: is it the same coherent error in both epochs?")
    print("=" * 78)
    for kk in (1, 2):
        sp = np.array([m[f"ph(U{kk})"] for m in sm])
        mu, R, csd = circ_stats(sp)
        dj = float(np.angle(np.exp(1j * (jm[f'ph(U{kk})'] - mu))))
        print(f"k={kk}:  June phase = {jm[f'ph(U{kk})']:+.4f} rad")
        print(f"      Sept mean   = {mu:+.4f} rad   Rbar={R:.4f}  "
              f"circ sd={csd:.4f} rad")
        print(f"      June - Sept = {dj:+.4f} rad "
              f"= {abs(dj)/csd:.0f}x the September circular sd")
    print("\nreference: a pure sine on this grid has k=1 phase "
          "= -1.5708 rad")

    print()
    print("=" * 78)
    print("5. Every frame, not just frame 1")
    print("=" * 78)
    print(f"{'frame':>5} {'June relL2':>11} {'Sep relL2':>16} "
          f"{'June |U1|':>10} {'Sep |U1|':>16} {'ceil |U1|':>10}")
    for f in range(1, N_STEPS + 1):
        sv_ = np.abs(modes(sv[f]))[1]
        jr = rel_l2(jf[f], truth[f])
        ju = float(np.abs(modes(jf[f]))[1])
        sr = np.array([rel_l2(t[f], truth[f]) for t in sepf])
        su = np.array([float(np.abs(modes(t[f]))[1]) for t in sepf])
        print(f"{f:5d} {jr:11.4f} {sr.mean():9.4f}+-{sr.std():5.4f} "
              f"{ju:10.5f} {su.mean():9.5f}+-{su.std():5.5f} {sv_:10.5f}")

    print()
    print("=" * 78)
    print("6. Software stack: what actually changed")
    print("=" * 78)
    jcode = json.load(open(os.path.join(JUNE_FEZ, "q8020_code_0.json")))
    scode = json.load(open(glob.glob(
        os.path.join(sd[0], "q8020_sweep_code_*.json"))[0]))
    print(f"June entry point: {jcode.get('entry_point'):<28} "
          f"(uncommitted fork, ZBook-only)")
    print(f"Sept entry point: {scode.get('entry_point'):<28} "
          f"(current ch-lbm)")
    jout = str(jcode.get("run_args", {}).get("outdir", ""))
    senv = scode.get("library_versions_before") or {}
    print(f"June host        : {jout[:24]!r}  -> Windows")
    print(f"Sept host        : {str(senv.get('path'))!r}  -> Linux")

    jv = (jcode.get("library_versions")
          or (jcode.get("library_versions_before") or {}).get("packages")
          or {})
    svv = senv.get("packages") or {}
    print(f"\nPackages recorded:  June {len(jv):>3}    Sept {len(svv):>3}")
    if not jv:
        print("  PROVENANCE GAP: June recorded NO library versions at all "
              "(q8020_code_0.json\n  holds only algorithm / entry_point / "
              "run_args), so the Qiskit-stack diff\n  across the two epochs "
              "is NOT recoverable from the artifacts.")
    print("  Sept stack:", ", ".join(
        f"{p}={svv[p]}" for p in sorted(svv)
        if any(w in p.lower() for w in ("qiskit", "numpy", "scipy"))))
    print("\n  Neither epoch records the transpiler's initial/final LAYOUT, "
          "so 'different\n  physical qubits' cannot be tested either "
          "(grep for initial_layout/physical_qubits\n  returns nothing in "
          "either tree).")


if __name__ == "__main__":
    main()
