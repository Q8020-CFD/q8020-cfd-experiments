"""CH q=8 C1 seam-sweep analysis (scratch).

Reads the C1 seam sweep + the C0 SV-floor baseline pulled into
q8020-cfd-experiments and produces:
  - c1_seam_sweep_summary.json : aux-style manifest (op point, per-case derived
    metrics, per-seam trajectory pointers, divergence onset, retention)
  - c1_seam_sweep.png          : 4-panel diagnostic figure

Key metrics pulled from the run artifacts:
  - q8020_artifacts_0.json / solution_steps  -> per-frame field -> amplitude(t)
  - q8020_analysis_0.json  / per_step_metrics -> p_success (retention),
    cumulative_norm, circuit depth / CX
  - q8020_results_0.json   / u_final_method   -> final field
  - C0 (evolution-mode=single) -> zero-seam SV floor (shots=0 and shots=131072)

Metric note: C1 runs used --no-classical/analytic-reference, so relL2-vs-FTCS
is NOT in these artifacts (deferred postproc). Reported metric is the final /
per-frame half-amplitude (max-min)/2. FTCS anchor (June sine q8 nu=0.03,
n_steps=920) is an approximate physics reference, not frame-aligned.
"""

import glob
import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

REPO = "/Users/agallojr/proj/src/q8020/q8020-cfd-experiments"
C1_DIR = f"{REPO}/results/burgers-ch-lbm/ch_q8_c1/2026-08-11/_b5c8743c"
C0_DIR = f"{REPO}/results/burgers-ch-lbm/ch_q8_c0/2026-08-06/_a66942a3"
HERE = os.path.dirname(os.path.abspath(__file__))
# Frame-aligned FTCS reference we generated at the C1 op point (n_steps=512,
# save-every=4) — the proper relL2 denominator. The June ref (n_steps=920) is
# only a physics anchor and is NOT used for relL2.
FTCS_REF = f"{HERE}/ftcs_ref_q8_nsteps512"
N_STEPS = 512

# case_id -> (experiment_id, k), in seam order
RUNS = [
    ("seam_k2", "2a3cbfeb", 2),
    ("seam_k4", "b15a9654", 4),
    ("seam_k8", "39a1f5ab", 8),
    ("seam_k16", "fe96b52e", 16),
]
COLORS = {2: "#C1121F", 4: "#E76F51", 8: "#457B9D", 16: "#1D3557"}


def half_amp(field):
    return (max(field) - min(field)) / 2.0


def rel(p):
    return os.path.relpath(p, REPO)


def amp_trajectory(exp_id):
    """(steps, amps) from solution_steps snapshots."""
    a = json.load(open(f"{C1_DIR}/{exp_id}/q8020_artifacts_0.json"))
    ss = a["solution_steps"]
    steps = sorted(int(s) for s in ss)
    return steps, [half_amp(ss[str(s)]) for s in steps]


def divergence_onset(steps, amps, thresh=1.0):
    """First step where amplitude exceeds thresh (blow-up marker)."""
    for s, a in zip(steps, amps):
        if a > thresh:
            return s
    return None


def load_analysis(exp_id):
    return json.load(open(f"{C1_DIR}/{exp_id}/q8020_analysis_0.json"))


def ref_amp():
    f = json.load(open(f"{FTCS_REF}/q8020_results_0.json"))
    uf = f.get("u_final_method") or f.get("u_final_classical")
    return half_amp(uf)


def _l2(v):
    return sum(x * x for x in v) ** 0.5


def rel_l2(u, uref):
    """Relative L2 error of field u vs reference uref (same length)."""
    if len(u) != len(uref):
        return None
    num = _l2([a - b for a, b in zip(u, uref)])
    den = _l2(uref)
    return num / den if den else None


def ref_trajectory():
    """{step: field} snapshots from the frame-aligned FTCS reference."""
    a = json.load(open(f"{FTCS_REF}/q8020_artifacts_0.json"))
    return {int(s): f for s, f in a["solution_steps"].items()}


def field_trajectory(exp_id):
    """{step: field} snapshots from a C1 run."""
    a = json.load(open(f"{C1_DIR}/{exp_id}/q8020_artifacts_0.json"))
    return {int(s): f for s, f in a["solution_steps"].items()}


def c0_floor():
    """C0 SV-floor final amplitudes (shots=0 and shots=131072)."""
    out = {}
    ec = json.load(open(f"{C0_DIR}/q8020_expanded_cases.json"))["cases"]
    for cid, cfg in ec.items():
        # find the run subdir whose params match this case shots
        shots = cfg.get("--shots")
        for sub in glob.glob(f"{C0_DIR}/*/"):
            pj = glob.glob(f"{sub}q8020_params_*.json")
            if not pj:
                continue
            p = json.load(open(pj[0]))
            if p.get("--shots") == shots and p.get("--evolution-mode") == "single":
                rf = f"{sub}q8020_results_0.json"
                if not os.path.exists(rf):
                    # e.g. C0 shots=131072: cluster wall-clock TIMEOUT (status
                    # in pipeline_result.json), not a crash — evolution-mode=
                    # single builds monolithic per-snapshot circuits whose
                    # build+transpile alone exceeded the allocation. Recoverable
                    # with more wall time. No result field written.
                    pr = f"{sub}pipeline_result.json"
                    status = "no-result"
                    if os.path.exists(pr):
                        status = json.load(open(pr)).get("status", "no-result")
                    out[shots] = {"status": status,
                                  "dir": rel(sub.rstrip("/"))}
                    break
                fields = json.load(open(rf))
                out[shots] = {
                    "final_half_amplitude": round(
                        half_amp(fields["u_final_method"]), 6
                    ),
                    "dir": rel(sub.rstrip("/")),
                }
                break
    return out


def main():
    ref = ref_amp()
    floor = c0_floor()
    ref_traj = ref_trajectory()
    cases = []
    trajectories = {}
    l2_trajectories = {}
    for case_id, exp_id, k in RUNS:
        steps, amps = amp_trajectory(exp_id)
        trajectories[k] = (steps, amps)
        an = load_analysis(exp_id)
        psm = an["per_step_metrics"]
        p_succ = [m.get("p_success") for m in psm if m.get("p_success") is not None]
        fields = json.load(open(f"{C1_DIR}/{exp_id}/q8020_results_0.json"))
        u_final = fields["u_final_method"]
        a1 = half_amp(u_final)
        onset = divergence_onset(steps, amps)

        # relL2 vs frame-aligned FTCS ref (final field + per-frame trajectory)
        u_ref_final = ref_traj.get(N_STEPS) or ref_traj.get(max(ref_traj))
        rl2_final = rel_l2(u_final, u_ref_final)
        ftraj = field_trajectory(exp_id)
        l2_steps, l2_vals = [], []
        for s in sorted(ftraj):
            if s in ref_traj:
                v = rel_l2(ftraj[s], ref_traj[s])
                if v is not None:
                    l2_steps.append(s)
                    l2_vals.append(v)
        l2_trajectories[k] = (l2_steps, l2_vals)

        cases.append(
            {
                "case_id": case_id,
                "experiment_id": exp_id,
                "segment_size_k": k,
                "n_segments_S": N_STEPS // k,
                "shots": an.get("shots"),
                "final_half_amplitude": round(a1, 6),
                "amp_ratio_vs_ref": round(a1 / ref, 4),
                "rel_l2_final": round(rl2_final, 6) if rl2_final is not None else None,
                "diverged": onset is not None,
                "divergence_onset_step": onset,
                "retention_p_success_min": round(min(p_succ), 5),
                "retention_p_success_mean": round(sum(p_succ) / len(p_succ), 5),
                "avg_circuit_depth": an.get("avg_circuit_depth"),
                "avg_cx_gates": an.get("avg_cx_gates"),
                "n_qubits": an.get("n_qubits"),
                "method_time_s": round(an.get("method_wall_time_s", 0), 1),
                "method_time_hr": round(an.get("method_wall_time_s", 0) / 3600, 2),
                "data_files": {
                    "fields": rel(f"{C1_DIR}/{exp_id}/q8020_results_0.json"),
                    "trajectory": rel(f"{C1_DIR}/{exp_id}/q8020_artifacts_0.json"),
                    "analysis": rel(f"{C1_DIR}/{exp_id}/q8020_analysis_0.json"),
                    "params": rel(
                        glob.glob(f"{C1_DIR}/{exp_id}/q8020_params_*.json")[0]
                    ),
                },
            }
        )

    manifest = {
        "study": "burgers-ch-lbm",
        "campaign": "C1 seam sweep (PRIMARY)",
        "workflow_id": "_b5c8743c",
        "run_date": "2026-08-11",
        "generated_utc": "2026-08-12T20:05:00Z",
        "generated_by": "agent-tmp/ch-q8-c1-analysis-2026-08-12/analyze_c1.py",
        "repo_root": REPO,
        "results_dir": rel(C1_DIR),
        "op_point": {
            "q": 8, "nu": 0.03, "ic": "sine", "ic_amplitude": 0.3,
            "bc": "periodic", "source": "none", "n_steps": N_STEPS,
            "evolution_mode": "measure_reprepare", "phi_modes": 8,
            "bond_dim": 4, "shots": 131072, "seed": 1234,
            "max_total_qubits": 26,
        },
        "swept_axis": "--segment-size (k) = [2,4,8,16] -> S = [256,128,64,32]",
        "metric_notes": (
            "relL2-vs-FTCS deferred (runs used --no-classical/analytic-"
            "reference; final_error is NaN). Metric = half-amplitude "
            "(max-min)/2 from the field snapshots."
        ),
        "ftcs_reference": {
            "half_amplitude": round(ref, 6),
            "note": (
                "Frame-aligned FTCS ref generated at the C1 op point "
                "(method=ftcs_reference, q=8, nu=0.03, ic=sine, A=0.3, "
                "n_steps=512, ref-points=800, save-every=4, seed=1234). "
                "129 frames aligned to the C1 cadence -> valid relL2 "
                "denominator. Final half-amp 0.2363 == C0 SV floor, "
                "cross-checking the exact algorithm against classical FTCS."
            ),
            "path": "agent-tmp/ch-q8-c1-analysis-2026-08-12/"
            "ftcs_ref_q8_nsteps512/q8020_results_0.json",
            "generated_by_this_analysis": True,
        },
        "c0_sv_floor": {
            "note": (
                "C0 evolution-mode=single (zero-seam). shots=0 = exact SV "
                "algorithm floor; shots=131072 = + sampling only, still no seams."
            ),
            "by_shots": floor,
        },
        "init_half_amplitude": 0.3,
        "cases": cases,
        "findings": [
            "Blow-up is a LATE-TIME INSTABILITY, not smooth seam-compounding: "
            "k=2 diverges by step ~148, k=4 only in the final quarter "
            "(~368), k=8/16 never diverge over 512 steps.",
            "Finer seams (smaller k, more re-prepare events) trigger the "
            "instability EARLIER -> seam count sets the onset time.",
            "Retention is NOT the failure mode: p_success ~= 0.997 for every k, "
            "including the blown-up k=2/4 runs.",
            "relL2 vs frame-aligned FTCS: k=16 best (see cases), improving "
            "monotonically as seams decrease; k=2/4 relL2 ~ O(1000s) (diverged).",
            "The exact algorithm is sound: C0 SV floor (0.2363) == FTCS ref "
            "(0.2363); ALL error is injected by the measure/re-prepare seams.",
            "Cost scales with k (depth/CX per segment): k=16 depth ~249k, "
            "CX ~124k, wall 25.8 hr vs k=2 depth ~32k, 13 min.",
        ],
    }

    out_json = f"{HERE}/c1_seam_sweep_summary.json"
    with open(out_json, "w") as f:
        json.dump(manifest, f, indent=2)
        f.write("\n")

    # ================= figure: 2x2 diagnostic =================
    fig, axes = plt.subplots(2, 2, figsize=(13, 9))
    axA, axB, axC, axD = axes.flat

    # A: amplitude vs time (the key panel)
    for k in (2, 4, 8, 16):
        steps, amps = trajectories[k]
        axA.plot(steps, amps, "-", color=COLORS[k], lw=2,
                 label=f"k={k}  (S={N_STEPS // k})")
    axA.axhline(ref, color="#2A9D8F", ls="--", lw=1.4)
    axA.axhline(0.3, color="#999", ls=":", lw=1.2)
    axA.set_yscale("log")
    axA.set_xlabel("time step")
    axA.set_ylabel("half-amplitude (max-min)/2  [log]")
    axA.set_title("A · amplitude vs time — blow-up is a late-time instability")
    axA.legend(fontsize=9)
    axA.grid(True, which="both", alpha=0.25)
    axA.annotate("FTCS ref / init", (5, 0.31), fontsize=8, color="#2A9D8F")

    # B: relL2 vs frame-aligned FTCS reference — per-frame trajectory + final
    # (skip step 0: IC is identical to the ref -> relL2~0 squashes the y-axis)
    for k in (2, 4, 8, 16):
        ls_, lv = l2_trajectories[k]
        pts = [(s, v) for s, v in zip(ls_, lv) if s > 0]
        axB.plot([s for s, _ in pts], [v for _, v in pts], "-",
                 color=COLORS[k], lw=2, label=f"k={k}")
    axB.axhline(1.0, color="#999", ls=":", lw=1.2)
    axB.text(5, 1.15, "relL2 = 1 (100% error)", fontsize=8, color="#666")
    axB.set_yscale("log")
    axB.set_ylim(1e-2, 2e3)
    axB.set_xlabel("time step")
    axB.set_ylabel("relL2 error vs FTCS ref  [log]")
    axB.set_title("B · relL2 vs frame-aligned FTCS (n_steps=512)")
    axB.legend(fontsize=9, loc="center right")
    axB.grid(True, which="both", alpha=0.25)
    # inset text: final relL2 per k
    lines = [
        f"k={c['segment_size_k']:>2}: relL2_final="
        f"{c['rel_l2_final']:.3g}"
        for c in cases
    ]
    axB.text(0.02, 0.02, "\n".join(lines), transform=axB.transAxes,
             fontsize=8, va="bottom", ha="left", family="monospace",
             bbox=dict(boxstyle="round", fc="white", ec="#ccc", alpha=0.85))

    # C: retention (p_success) vs k  — flat => not the cause
    ks = [c["segment_size_k"] for c in cases]
    ret = [c["retention_p_success_mean"] for c in cases]
    axC.plot(ks, ret, "D-", color="#2A9D8F", lw=2, ms=8)
    axC.set_xscale("log", base=2)
    axC.set_ylim(0.99, 1.0)
    axC.set_xlabel("segment size k")
    axC.set_ylabel("mean post-selection retention  p_success")
    axC.set_title("C · retention ~0.997 for all k — NOT the failure mode")
    axC.grid(True, which="both", alpha=0.25)
    for c in cases:
        axC.annotate(f"{c['retention_p_success_mean']:.4f}",
                     (c["segment_size_k"], c["retention_p_success_mean"]),
                     textcoords="offset points", xytext=(6, -12), fontsize=8)

    # D: circuit cost + wall time vs k (twin axis)
    depth = [c["avg_circuit_depth"] for c in cases]
    times = [c["method_time_hr"] for c in cases]
    axD.plot(ks, depth, "s-", color="#1D3557", lw=2, ms=8, label="avg circuit depth")
    axD.set_xscale("log", base=2)
    axD.set_yscale("log")
    axD.set_xlabel("segment size k")
    axD.set_ylabel("avg circuit depth  [log]", color="#1D3557")
    axD.tick_params(axis="y", labelcolor="#1D3557")
    axD.grid(True, which="both", alpha=0.25)
    axDt = axD.twinx()
    axDt.plot(ks, times, "o--", color="#C1121F", lw=2, ms=8, label="wall time (hr)")
    axDt.set_yscale("log")
    axDt.set_ylabel("method wall time [hr, log]", color="#C1121F")
    axDt.tick_params(axis="y", labelcolor="#C1121F")
    axD.set_title("D · cost: depth & wall time vs k")

    fig.suptitle(
        "CH q=8 · C1 seam sweep (2026-08-11) · nu=0.03 A=0.3 shots=131072 "
        "bond-dim=4 phi=8 — segment-size sweep",
        fontsize=12,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    out_png = f"{HERE}/c1_seam_sweep.png"
    fig.savefig(out_png, dpi=140)

    print("wrote", out_json)
    print("wrote", out_png)
    if 0 in floor:
        print(f"  C0 SV floor (shots=0)      {floor[0].get('final_half_amplitude', floor[0].get('status'))}")
    if 131072 in floor:
        print(f"  C0 floor  (shots=131072)   {floor[131072].get('final_half_amplitude', floor[131072].get('status'))}")
    print(f"  FTCS ref (frame-aligned) final half-amp = {ref:.4f}")
    for c in cases:
        print(
            f"  k={c['segment_size_k']:>2} S={c['n_segments_S']:>3} "
            f"amp={c['final_half_amplitude']:>9.3f} "
            f"relL2={c['rel_l2_final']:>10.4g} "
            f"onset={str(c['divergence_onset_step']):>5} "
            f"ret={c['retention_p_success_mean']:.4f} "
            f"t={c['method_time_hr']}hr"
        )


if __name__ == "__main__":
    main()
