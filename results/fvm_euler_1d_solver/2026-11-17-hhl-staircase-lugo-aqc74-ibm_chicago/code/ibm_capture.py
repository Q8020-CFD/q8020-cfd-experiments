"""Capture a finished IBM Quantum job into experiments/results, with metautil
metadata and calibration snapshots.

Reads the prep JSON that ibm_submit.py or ibm_staircase.py wrote at submit
time (it holds the job id), fetches the job's counts, metrics and the
calibration in effect when it ran, and writes one results folder:

  <results>/<YYYY-MM-DD>-<label>-<backend>/      (date of the run, UTC)
    README.md              what ran, when, where, on what code
    prep.json, isa.qpy     the submit-time record and the executed circuits
    counts.json            raw counts per PUB, clbit 0 rightmost
    job.json               status, tags, timestamps, usage
    analysis.json          per-PUB scores (staircase jobs)
    calibration/submit.json, calibration/run.json
    code/                  the modules as run, aux.patch, provenance.json
    pubs/<name>/           one metautil case per PUB: q8020_<section>_<id>_0
                           fragments and the assembled q8020_metadata_<id>.json

At submit time ibm_staircase.py calls calibration_snapshot() and
code_snapshot() from here, so both copies come from the same code.
"""
import argparse
import hashlib
import json
import math
import platform
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path
from typing import Any

import numpy as np

HERE = Path(__file__).resolve().parent
AUX = HERE.parents[1]
EXP = HERE.parents[2]
Q8020 = HERE.parents[3]
RESULTS = EXP / "results" / "fvm_euler_1d_solver"
for _p in (Q8020 / "q8020-backend-utils" / "src",
           Q8020 / "q8020-cfd-metautil" / "src"):
    sys.path.insert(0, str(_p))
from q8020_backend_utils.ibm import backend_meta as bm  # noqa: E402
from q8020_cfd_metautil import meta_fragment as mf  # noqa: E402
from q8020_cfd_metautil.harvest import harvest_metadata  # noqa: E402

NB, NL = 5, 8              # system and clock qubits of the nelem 5 circuit
PACKAGES = ("qiskit", "qiskit-aer", "qiskit-ibm-runtime", "numpy", "scipy")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _git(repo: Path, *args: str) -> str:
    p = subprocess.run(["git", "-C", str(repo), *args], text=True,
                       stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    return p.stdout.strip() if p.returncode == 0 else ""


def _repo(repo: Path, sub: str | None = None) -> dict[str, Any]:
    """Commit, dirty flag and credential-free remote of a repo."""
    url = re.sub(r"//[^@/]+@", "//", _git(repo, "remote", "get-url", "origin"))
    args = ["status", "--porcelain"] + (["--", sub] if sub else [])
    return {"path": str(repo), "remote": url,
            "commit": _git(repo, "rev-parse", "HEAD"),
            "dirty": bool(_git(repo, *args))}


def code_snapshot(dest: Path) -> dict[str, Any]:
    """Copy every module loaded from the aux repo into dest, with the aux
    diff against HEAD and a provenance record. Call after all imports."""
    dest.mkdir(parents=True, exist_ok=True)
    mods = sorted({Path(m.__file__).resolve() for m in list(sys.modules.values())
                   if getattr(m, "__file__", None)
                   and str(Path(m.__file__).resolve()).startswith(str(AUX))})
    files = {}
    for f in mods:
        rel = f.relative_to(AUX)
        shutil.copy2(f, dest / f.name)
        files[str(rel)] = sha256(f)
    patch = _git(AUX, "diff", "HEAD", "--", str(HERE.relative_to(AUX)))
    (dest / "aux.patch").write_text(patch + "\n" if patch else "")
    rel = str(HERE.relative_to(AUX))
    prov = {
        "captured_utc": utc_now(),
        "aux": {**_repo(AUX, rel),
                "untracked": [Path(u).relative_to(rel).as_posix() for u in
                              _git(AUX, "ls-files", "--others",
                                   "--exclude-standard", "--", rel).split()],
                "patch": "aux.patch", "patch_sha256":
                hashlib.sha256((dest / "aux.patch").read_bytes()).hexdigest()},
        "experiments": _repo(EXP, "results"),
        "metautil": _repo(Q8020 / "q8020-cfd-metautil"),
        "backend_utils": _repo(Q8020 / "q8020-backend-utils"),
        "modules": files,
        "python": platform.python_version(), "interpreter": sys.executable,
        "packages": {p: version(p) for p in PACKAGES},
    }
    (dest / "provenance.json").write_text(json.dumps(prov, indent=1) + "\n")
    return prov


class _AtTime:
    """An IBMBackend as calibrated at a past time."""

    def __init__(self, backend: Any, when: datetime) -> None:
        self.name = backend.name
        self.target = backend.target_history(datetime=when)
        self._props = backend.properties(datetime=when)

    def properties(self) -> Any:
        return self._props


def calibration_snapshot(backend: Any, when: datetime | None = None) -> dict:
    """The device calibration now, or in effect at `when`: the metautil
    BackendMeta for the whole device plus the raw backend properties."""
    src = _AtTime(backend, when) if when else backend
    props = src.properties()
    meta = bm._make_ibm_runtime_backend_meta(src)
    meta.update({
        "captured_at": utc_now(),
        "calibration_for": when.isoformat() if when else "current",
        "calibration_last_update": str(getattr(props, "last_update_date", "")),
        "processor_type": getattr(backend, "processor_type", None),
    })
    cfg = backend.configuration()
    return {"backend_meta": meta,
            "default_rep_delay": getattr(cfg, "default_rep_delay", None),
            "properties": props.to_dict() if props else None}


def subset_meta(meta: dict, qubits: list[int]) -> dict:
    """BackendMeta restricted to the qubits a PUB used."""
    s = set(qubits)
    out = {k: v for k, v in meta.items()
           if k not in ("t1", "t2", "readout_error", "gate_error",
                        "coupling_map")}
    for k in ("t1", "t2", "readout_error"):
        v = meta.get(k) or {}
        out[k] = {q: v.get(q, v.get(str(q))) for q in qubits
                  if q in v or str(q) in v}
    out["gate_error"] = {
        g: {qa: e for qa, e in d.items() if set(map(int, qa.split(","))) <= s}
        for g, d in (meta.get("gate_error") or {}).items()}
    out["coupling_map"] = [e for e in meta.get("coupling_map") or []
                           if set(e) <= s]
    out["physical_qubits"] = list(qubits)
    return out


def pubs_of(prep: dict) -> list[dict]:
    """PUB records in submit order; ibm_submit.py jobs predate the list."""
    if "pubs" in prep:
        return prep["pubs"]
    phys = prep["physical_qubits"]
    return [{"name": "main", "shots": prep["shots"], "physical_qubits": phys,
             "two_qubit_gates": prep.get("two_qubit_gates")},
            {"name": "cal0", "shots": prep["cal_shots"], "physical_qubits": phys},
            {"name": "cal1", "shots": prep["cal_shots"], "physical_qubits": phys},
            {"name": "ctrl", "shots": prep["cal_shots"],
             "physical_qubits": prep.get("control_physical_qubits", phys),
             "two_qubit_gates": prep.get("control_two_qubit_gates")}]


def to_prob(counts: dict, n: int) -> tuple[np.ndarray, int]:
    p = np.zeros(2 ** n)
    for k, v in counts.items():
        p[int(k.replace(" ", ""), 2)] += v
    shots = int(p.sum())
    return p / shots, shots


def flip_rates(cal0: dict, cal1: dict, n: int) -> np.ndarray:
    """e[c] = (P(1 | 0), P(0 | 1)) for clbit c."""
    p0, _ = to_prob(cal0, n)
    p1, _ = to_prob(cal1, n)
    bit = (np.arange(2 ** n)[:, None] >> np.arange(n)) & 1
    return np.stack([(p0[:, None] * bit).sum(0),
                     (p1[:, None] * (1 - bit)).sum(0)], axis=1)


def readout_correct(p: np.ndarray, e: np.ndarray) -> np.ndarray:
    """Tensored inverse of the per-clbit flip matrices, clipped, renormalized
    (as ibm_analyze.py)."""
    n = e.shape[0]
    t = p.reshape((2,) * n)  # axis j is clbit n - 1 - j
    for c in range(n):
        a = np.array([[1 - e[c, 0], e[c, 1]], [e[c, 0], 1 - e[c, 1]]])
        t = np.moveaxis(np.tensordot(np.linalg.inv(a), t,
                                     axes=([1], [n - 1 - c])), 0, n - 1 - c)
    q = np.clip(t.reshape(-1), 0, None)
    return q / q.sum()


def score_step(p: np.ndarray, shots: int, b2: np.ndarray) -> dict:
    """Clock and ancilla back to 0 (outcome index < 2^NB), and the system
    marginal there against |b|^2. Survival s is the global-depolarizing
    estimate from the return probability."""
    n = int(round(math.log2(p.size)))
    null = 2.0 ** -(n - NB)
    p0 = float(p[: 2 ** NB].sum())
    sysd = p[: 2 ** NB] / p0 if p0 > 0 else np.zeros(2 ** NB)
    fid = float(np.sum(np.sqrt(sysd * b2)) ** 2)
    return {"p_return": p0,
            "p_return_sigma": math.sqrt(max(p0 * (1 - p0), null) / shots),
            "p_return_null": null,
            "survival": (p0 - null) / (1 - null),
            "system_fidelity": fid,
            "system_fidelity_null": float(np.sum(np.sqrt(b2 / 2 ** NB)) ** 2)}


def analyze(prep: dict, counts: dict) -> dict:
    """Per-PUB scores for a staircase job, raw and readout-corrected, and a
    fit of ln(survival) against the two-qubit gate count."""
    if prep.get("kind") != "staircase":
        return {}
    n = len(prep["physical_qubits"])
    e = flip_rates(counts["cal0"], counts["cal1"], n)
    b2 = np.asarray(prep["b_herm"][: 2 ** NB], dtype=float)
    b2 = b2 / b2.sum()
    out = {"flip_rates": e.tolist(), "steps": []}
    for pub in prep["pubs"]:
        if not pub["name"].startswith("step"):
            continue
        p, shots = to_prob(counts[pub["name"]], n)
        row = {"name": pub["name"], "blocks": pub["blocks"], "shots": shots,
               "two_qubit_gates": pub["two_qubit_gates"],
               "esp": pub["esp"], "raw": score_step(p, shots, b2),
               "readout": score_step(readout_correct(p, e), shots, b2)}
        out["steps"].append(row)
    # step 0 never touches clock or ancilla, so its return is trivial
    pts = [(r["two_qubit_gates"], r["readout"]["survival"]) for r in out["steps"]
           if r["blocks"] > 0
           and r["readout"]["survival"] > 3 * r["readout"]["p_return_sigma"]]
    if len(pts) >= 2:
        x, y = np.array([q[0] for q in pts]), np.log([q[1] for q in pts])
        slope, icept = np.polyfit(x, y, 1)
        full = prep.get("full_circuit_two_qubit_gates")
        out["fit"] = {"points": len(pts), "ln_survival_per_2q": float(slope),
                      "intercept": float(icept),
                      "error_per_2q_effective": float(1 - math.exp(slope))}
        if full:
            out["fit"]["full_circuit_two_qubit_gates"] = full
            out["fit"]["predicted_full_survival"] = float(
                math.exp(icept + slope * full))
    return out


def qpu_seconds(usage: dict) -> Any:
    return usage.get("quantum_seconds", usage.get("qpu_charge_time_seconds"))


def readme(dest: Path, prep: dict, job: dict, prov: dict, ana: dict,
           label: str) -> None:
    """A short, generated README; the JSON files hold the full record."""
    ts, use = job["metrics"].get("timestamps", {}), job["metrics"].get("usage", {})
    aux = prov.get("aux", {})
    dirty = (" plus `code/aux.patch`, untracked "
             + ", ".join(aux.get("untracked") or []) if aux.get("dirty") else "")
    lines = [
        f"# {label} on {prep['backend']}", "",
        prep.get("description", "").strip(), "",
        "| piece | value |", "|---|---|",
        f"| backend | `{prep['backend']}` ({prep.get('processor')}) |",
        f"| job | `{job['job_id']}`, status {job['status']}, tags "
        f"{', '.join(job.get('tags') or [])} |",
        f"| submitted | {prep.get('submitted_utc')} from "
        f"{(prep.get('submitted_from') or {}).get('context', '?')} |",
        f"| ran | {ts.get('running')} to {ts.get('finished')} (UTC) |",
        f"| QPU usage | {qpu_seconds(use)} s |",
        f"| code | aux `{aux.get('commit', '')[:12]}`"
        f"{dirty}; "
        f"experiments `{prov.get('experiments', {}).get('commit', '')[:12]}`; "
        f"metautil `{prov.get('metautil', {}).get('commit', '')[:12]}`; "
        + ", ".join(f"{k} {v}" for k, v in prov.get("packages", {}).items()) + " |",
        f"| layout | {len(prep['physical_qubits'])} qubits "
        f"{prep['physical_qubits']}, optimization level "
        f"{prep.get('optimization_level')} |",
        f"| options | {json.dumps(prep.get('options'))} |", "",
        "| PUB | shots | 2q gates | duration us | ESP | return P (readout) | "
        "survival | system fidelity |", "|---|---|---|---|---|---|---|---|"]
    scored = {r["name"]: r for r in ana.get("steps", [])}
    for pub in pubs_of(prep):
        r = scored.get(pub["name"], {}).get("readout", {})
        fmt = (lambda v, f: format(v, f) if isinstance(v, (int, float)) else "")
        lines.append(
            f"| {pub['name']} | {pub['shots']} | {pub.get('two_qubit_gates', '')}"
            f" | {fmt(pub.get('duration_us'), '.0f')} | {fmt(pub.get('esp'), '.2e')}"
            f" | {fmt(r.get('p_return'), '.4f')} | {fmt(r.get('survival'), '.4f')}"
            f" | {fmt(r.get('system_fidelity'), '.3f')} |")
    if "fit" in ana:
        f = ana["fit"]
        lines += ["", f"Fit over the {f['points']} steps past step 0 with survival"
                  " above 3 sigma:"
                  f" ln(survival) = {f['intercept']:.3f} "
                  f"{f['ln_survival_per_2q']:+.3e} x (2q gates), an effective "
                  f"{f['error_per_2q_effective']:.2e} per two-qubit gate."]
        if "predicted_full_survival" in f:
            lines.append(f"At the full circuit's {f['full_circuit_two_qubit_gates']}"
                         f" two-qubit gates that predicts a survival of "
                         f"{f['predicted_full_survival']:.2e}.")
    if ana.get("steps"):
        lines += ["", "System fidelity of a maximally mixed system: "
                  f"{ana['steps'][0]['readout']['system_fidelity_null']:.3f}. A "
                  "step at that value carries no system signal, and any excess "
                  "of its return P over the null is then more likely relaxation "
                  "toward 0 than surviving signal, so its survival is an upper "
                  "bound."]
    lines += ["", "Return P is the probability that clock and ancilla read 0; "
              "its null (maximally mixed output) is 2^-9. Survival is "
              "(P - null) / (1 - null). Readout correction uses the cal0 and "
              "cal1 PUBs. The system fidelity is the classical fidelity of the "
              "system marginal, given clock and ancilla 0, against |b|^2.", "",
              "Files: `prep.json`, `isa.qpy` (Git LFS), `counts.json`, "
              "`job.json`, `analysis.json`, `calibration/submit.json` (at "
              "submit) and `calibration/run.json` (in effect at the run "
              "start), `code/`, and one metautil case per PUB under `pubs/`.",
              "", "Captured by `ibm_capture.py` at "
              f"{job.get('captured_utc', utc_now())}; code snapshot taken at "
              f"{prov.get('captured_utc', '?')}."]
    (dest / "README.md").write_text("\n".join(lines) + "\n")


def write_cases(dest: Path, prep: dict, job: dict, counts: dict, ana: dict,
                run_meta: dict, prov: dict) -> list[str]:
    """One metautil case per PUB, assembled with harvest_metadata."""
    exp_id = mf.generate_experiment_id()
    sub = prep.get("submitted_from") or {}
    ts, use = job["metrics"].get("timestamps", {}), job["metrics"].get("usage", {})
    t0, t1 = ts.get("running"), ts.get("finished")
    dur = None
    if t0 and t1:
        dur = (datetime.fromisoformat(t1) - datetime.fromisoformat(t0)).total_seconds()
    scored = {r["name"]: r for r in ana.get("steps", [])}
    warns = []
    for i, pub in enumerate(pubs_of(prep)):
        case = dest / "pubs" / pub["name"]
        cid = mf.generate_experiment_id()
        exp = mf.make_experiment_meta(prep.get("label", "ibm-job"),
                                      experiment_id=exp_id,
                                      workflow_id=job["job_id"])
        exp.update({"_source": "harvest", "timestamp": prep.get("submitted_utc"),
                    "user": {"username": sub.get("username"),
                             "hostname": sub.get("hostname"),
                             "context": sub.get("context")},
                    "captured_utc": prov.get("captured_utc"),
                    "captured_by": mf.make_user_meta()})
        mf.write_experiment(case, exp, experiment_id=cid)
        keys = ("step", "blocks", "shots", "two_qubit_gates", "two_qubit_depth",
                "depth", "duration_us", "log_esp", "esp", "physical_qubits")
        mf.write_case(case, {"_source": "harvest", **mf.make_case_meta(
            pub["name"], pub_index=i, input_qpy=prep.get("input_qpy"),
            input_sha256=prep.get("input_sha256"),
            **{k: pub[k] for k in keys if k in pub})}, experiment_id=cid)
        mf.write_code(case, {"_source": "harvest", **mf.make_code_meta(
            prep.get("algorithm", "hhl"), prep.get("entry_point", "ibm_submit.py"),
            run_args=prep.get("options"), interpreter=prep.get("interpreter"),
            code_provenance=prov)}, experiment_id=cid)
        mf.write_backend(case, {"_source": "harvest", "job_id": job["job_id"],
                                "full_calibration": "../../calibration/run.json",
                                **subset_meta(run_meta, pub["physical_qubits"])},
                         experiment_id=cid)
        mf.write_artifacts(case, {"_source": "harvest",
                                  "counts": "../../counts.json", "counts_key":
                                  pub["name"], "isa_qpy": "../../isa.qpy",
                                  "isa_index": i}, experiment_id=cid)
        mf.write_exec_stats(case, {"_source": "harvest", "start_time": t0,
                                   "end_time": t1, "duration_seconds": dur,
                                   "exit_code": 0 if job["status"] == "DONE" else 1,
                                   "success": job["status"] == "DONE",
                                   "job_id": job["job_id"],
                                   "job_quantum_seconds": qpu_seconds(use)},
                            experiment_id=cid)
        res = {"_source": "harvest", "shots": sum(counts[pub["name"]].values()),
               "distinct_outcomes": len(counts[pub["name"]])}
        if pub["name"] in scored:
            res.update({k: scored[pub["name"]][k] for k in ("raw", "readout")})
        mf.write_results(case, res, experiment_id=cid)
        meta, w, _ = harvest_metadata(case, read_only=True)
        (case / f"q8020_metadata_{cid}.json").write_text(
            json.dumps(meta, indent=2, default=str) + "\n")
        warns += [f"{pub['name']}: {x}" for x in w]
    return warns


def capture(prep_path: Path, label: str | None, dest_root: Path,
            account: str | None, wait: bool, poll: int) -> Path:
    from qiskit_ibm_runtime import QiskitRuntimeService

    prep = json.loads(prep_path.read_text())
    label = label or prep.get("label") or "ibm-job"
    svc = QiskitRuntimeService(name=account or prep.get("account",
                                                        "default-ibm-cloud"))
    job = svc.job(prep["job_id"])
    status = str(job.status())
    while wait and status not in ("DONE", "ERROR", "CANCELLED"):
        print(f"{utc_now()} job {prep['job_id']}: {status}", flush=True)
        time.sleep(poll)
        status = str(job.status())
    if status != "DONE":
        sys.exit(f"job {prep['job_id']} is {status}; nothing captured")
    res = job.result()
    names = [p["name"] for p in pubs_of(prep)]
    counts = {}
    for i, name in enumerate(names):
        data = res[i].data
        reg = getattr(data, "meas", None) or next(iter(data.values()))
        counts[name] = reg.get_counts()
    metrics = job.metrics()
    ts = metrics.get("timestamps", {})
    run_start = datetime.fromisoformat(ts["running"].replace("Z", "+00:00"))
    dest = dest_root / f"{run_start:%Y-%m-%d}-{label}-{prep['backend']}"
    if dest.exists():
        sys.exit(f"{dest} exists; not overwriting")
    (dest / "calibration").mkdir(parents=True)
    backend = svc.backend(prep["backend"])
    run_cal = calibration_snapshot(backend, run_start)
    (dest / "calibration" / "run.json").write_text(
        json.dumps(run_cal, indent=1, default=str) + "\n")
    sub_cal = prep_path.parent / (prep.get("calibration_submit") or "")
    if prep.get("calibration_submit") and sub_cal.is_file():
        shutil.copy2(sub_cal, dest / "calibration" / "submit.json")
    shutil.copy2(prep_path, dest / "prep.json")
    if prep.get("layout_from") and Path(prep["layout_from"]).is_file():
        shutil.copy2(prep["layout_from"], dest / "layout-from-prep.json")
    isa = (prep_path.with_name(prep_path.name[:-len("-prep.json")] + "-isa.qpy")
           if prep_path.name.endswith("-prep.json")
           else prep_path.with_name("isa.qpy"))
    if isa.is_file():
        shutil.copy2(isa, dest / "isa.qpy")
    code_dir = prep_path.parent / (prep.get("code_dir") or "")
    if prep.get("code_dir") and code_dir.is_dir():
        shutil.copytree(code_dir, dest / "code")
        prov = json.loads((dest / "code" / "provenance.json").read_text())
    else:  # older jobs: what is on disk now, flagged as such
        prov = code_snapshot(dest / "code")
        prov["note"] = "captured at harvest time, not at submit time"
        (dest / "code" / "provenance.json").write_text(json.dumps(prov, indent=1))
    jrec = {"job_id": prep["job_id"], "status": status,
            "tags": list(getattr(job, "tags", []) or []),
            "backend": prep["backend"], "metrics": metrics,
            "captured_utc": utc_now()}
    (dest / "job.json").write_text(json.dumps(jrec, indent=1, default=str) + "\n")
    (dest / "counts.json").write_text(json.dumps(counts) + "\n")
    ana = analyze(prep, counts)
    (dest / "analysis.json").write_text(json.dumps(ana, indent=1) + "\n")
    warns = write_cases(dest, prep, jrec, counts, ana, run_cal["backend_meta"],
                        prov)
    readme(dest, prep, jrec, prov, ana, label)
    for w in warns:
        print("metautil warning:", w)
    print(f"captured job {prep['job_id']} into {dest}")
    return dest


def reanalyze(dest: Path, label: str | None) -> None:
    """Redo analysis.json and README.md of a captured folder from its own
    files; nothing is fetched and no metadata fragment is touched."""
    prep = json.loads((dest / "prep.json").read_text())
    counts = json.loads((dest / "counts.json").read_text())
    jrec = json.loads((dest / "job.json").read_text())
    prov = json.loads((dest / "code" / "provenance.json").read_text())
    ana = analyze(prep, counts)
    (dest / "analysis.json").write_text(json.dumps(ana, indent=1) + "\n")
    readme(dest, prep, jrec, prov, ana, label or prep.get("label") or "ibm-job")
    print(f"reanalyzed {dest}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("prep", type=Path, help="prep JSON written at submit time, "
                    "or with --reanalyze a captured results folder")
    ap.add_argument("--reanalyze", action="store_true")
    ap.add_argument("--label", help="results folder label (default: prep's)")
    ap.add_argument("--dest-root", type=Path, default=RESULTS)
    ap.add_argument("--account")
    ap.add_argument("--wait", action="store_true",
                    help="poll until the job finishes, then capture")
    ap.add_argument("--poll", type=int, default=120, help="seconds")
    a = ap.parse_args()
    if a.reanalyze:
        reanalyze(a.prep, a.label)
    else:
        capture(a.prep, a.label, a.dest_root, a.account, a.wait, a.poll)


if __name__ == "__main__":
    main()
