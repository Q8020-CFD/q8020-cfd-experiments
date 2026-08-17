"""Gather apples-to-apples stats for the FVM Euler 1D HHL nozzle case run under
qiskit 1.x (Nov 2025) vs qiskit 2.x (Apr 2026). Both groups: base FVM (HHL,
not LuGo), ideal_statevector backend, 150000 shots, identical case JSON.

Reads the q8020 result trees directly; prints a text table and dumps a JSON
summary next to this script. Read-only."""

import json
import glob
import os
import csv
import statistics as st

RES = ("/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/results/"
       "fvm_euler_1d_solver")
NOV_DIR = f"{RES}/2025-11-11/shots_150000"
APR_DIR = f"{RES}/2026-04-05/_52d087d1/time_steps_4"
OUT = os.path.dirname(os.path.abspath(__file__))


def load(path: str) -> dict | None:
    try:
        return json.load(open(path))
    except Exception:
        return None


def first(pattern: str) -> str | None:
    hits = glob.glob(pattern)
    return hits[0] if hits else None


def is_target(trial: str) -> bool:
    """base FVM HHL, nelem5, cfl=1e10, statevector, 150k shots."""
    m = first(f"{trial}/q8020_metadata_*.json")
    if not m:
        return False
    d = load(m) or {}
    try:
        algo = d["code"][0].get("algorithm")
        c = d["case"][0]
    except Exception:
        return False
    if algo != "HHL" or c.get("cfl") != 1e10 or c.get("nelem") != 5:
        return False
    b = first(f"{trial}/q8020_backend_*.json")
    bd = load(b) or {}
    return bd.get("method") == "statevector" and bd.get("nshots") == 150000


def trial_stats(trial: str) -> dict:
    """Per-trial circuit + convergence stats."""
    art = load(first(f"{trial}/q8020_artifacts_*.json") or "") or {}
    tp = art.get("transpile_passes", [])
    ct = art.get("circuit_timing_total_s", {})
    ls = art.get("linear_system", {})
    # per-step depth/gates/qubits (transpiled = 'after')
    depths = [p["after"]["depth"] for p in tp if "after" in p]
    gates = [p["after"]["gate_count"] for p in tp if "after" in p]
    qubits = [p["after"]["num_qubits"] for p in tp if "after" in p]
    gen = [p.get("wall_time_generate_s") for p in tp]
    tr = [p.get("wall_time_transpile_s") for p in tp]
    ex = [p.get("wall_time_execute_s") for p in tp]
    # convergence: final residual + mean HHL solve error
    resid = None
    rf = first(f"{trial}/residual_*.csv")
    if rf:
        rows = list(csv.reader(open(rf)))
        if len(rows) > 1:
            resid = float(rows[-1][1])
    l2n = None
    fid = None
    hf = first(f"{trial}/hhl_metrics_*.csv")
    if hf:
        rows = list(csv.reader(open(hf)))[1:]
        l2vals = [float(r[5]) for r in rows if len(r) > 5]
        fidvals = [float(r[2]) for r in rows if len(r) > 2]
        if l2vals:
            l2n = st.mean(l2vals)
        if fidvals:
            fid = st.mean(fidvals)
    return {
        "trial": os.path.basename(trial),
        "n_iters": len(tp),
        "qubits_transpiled": max(qubits) if qubits else None,
        "depth_min": min(depths) if depths else None,
        "depth_max": max(depths) if depths else None,
        "gates_max": max(gates) if gates else None,
        "gen_s_total": ct.get("generate"),
        "transpile_s_total": ct.get("transpile"),
        "execute_s_total": ct.get("execute"),
        "total_s": ct.get("total"),
        "gen_s_per_iter": st.mean([g for g in gen if g]) if any(gen) else None,
        "transpile_s_per_iter": (st.mean([t for t in tr if t])
                                 if any(tr) else None),
        "execute_s_per_iter": (st.mean([e for e in ex if e])
                               if any(ex) else None),
        "condition_number_range": ls.get("condition_number_range"),
        "final_residual": resid,
        "mean_hhl_l2_error_normalized": l2n,
        "mean_hhl_fidelity": fid,
    }


def host_of(trial: str) -> dict:
    """Best-effort host + stack extraction."""
    info = {}
    # sweep experiment (April) carries the true compute-node hostname
    se = first(f"{trial}/q8020_sweep_experiment_*.json")
    if se:
        d = load(se) or {}
        info["hostname"] = d.get("user", {}).get("hostname")
        info["source"] = d.get("_source")
        info["timestamp"] = d.get("timestamp")
    else:
        ex = first(f"{trial}/q8020_experiment_*.json")
        if ex:
            d = load(ex) or {}
            info["hostname"] = d.get("user", {}).get("hostname")
            info["source"] = d.get("_source")
            info["name"] = d.get("name")
            info["timestamp"] = d.get("timestamp")
    # library stack from env snapshot if present
    envf = first(f"{trial}/q8020_env_before_*.json")
    if envf:
        p = (load(envf) or {}).get("packages", {})
        info["stack"] = {k: p.get(k) for k in
                         ["python", "qiskit", "qiskit-aer",
                          "qiskit-ibm-runtime", "quantum-linear-solvers",
                          "numpy", "scipy"]}
    return info


def group(label: str, root: str) -> dict:
    trials = sorted(t for t in glob.glob(f"{root}/trial_*") if is_target(t))
    rows = [trial_stats(t) for t in trials]
    host = host_of(trials[0]) if trials else {}

    def agg(key: str) -> dict | None:
        vals = [r[key] for r in rows if r.get(key) is not None]
        if not vals:
            return None
        return {
            "n": len(vals),
            "min": min(vals),
            "max": max(vals),
            "mean": st.mean(vals),
            "std": st.pstdev(vals) if len(vals) > 1 else 0.0,
        }

    return {
        "label": label,
        "root": root,
        "n_target_trials": len(trials),
        "host": host,
        "per_trial": rows,
        "agg": {k: agg(k) for k in
                ["depth_max", "gates_max", "gen_s_per_iter",
                 "transpile_s_per_iter", "execute_s_per_iter", "total_s",
                 "final_residual", "mean_hhl_l2_error_normalized",
                 "mean_hhl_fidelity"]},
    }


def main() -> None:
    nov = group("Nov 2025 - qiskit 1.2.4", NOV_DIR)
    apr = group("Apr 2026 - qiskit 2.3.1", APR_DIR)
    summary = {"nov": nov, "apr": apr}
    with open(f"{OUT}/summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    for g in (nov, apr):
        print(f"\n===== {g['label']} =====")
        print(f"  dir: {g['root']}")
        print(f"  host: {g['host'].get('hostname')} "
              f"(source={g['host'].get('source')}"
              f"{', name=' + g['host'].get('name', '') if g['host'].get('name') else ''})")
        stk = g["host"].get("stack")
        if stk:
            print(f"  stack: {stk}")
        print(f"  target trials: {g['n_target_trials']}")
        a = g["agg"]

        def line(key: str, fmt: str) -> None:
            v = a.get(key)
            if not v:
                print(f"    {key:32}: (n/a)")
                return
            print(f"    {key:32}: mean={fmt.format(v['mean'])} "
                  f"min={fmt.format(v['min'])} max={fmt.format(v['max'])} "
                  f"std={fmt.format(v['std'])} (n={v['n']})")
        line("qubits/depth_max", "{:.0f}")
        line("gates_max", "{:.0f}")
        line("gen_s_per_iter", "{:.2f}")
        line("transpile_s_per_iter", "{:.2f}")
        line("execute_s_per_iter", "{:.2f}")
        line("total_s", "{:.1f}")
        line("final_residual", "{:.4f}")
        line("mean_hhl_l2_error_normalized", "{:.4f}")
        line("mean_hhl_fidelity", "{:.4f}")

    print(f"\nWrote {OUT}/summary.json")


if __name__ == "__main__":
    main()
