"""Circuit-resource figure for a CH-vs-QLBM bakeoff dataset.

Reads a dataset JSON in the case1_bakeoff shape (a 'runs' list, each with a
'path' to a sweep case dir) and re-harvests the circuit cost of every run from
its q8020_analysis_*.json.  Because it reads the live analysis files via the
dataset's paths, regenerating any case and re-pointing its path in the JSON
then re-running this script regenerates the figure from the new numbers.

2x2 layout: a qubits panel (top-left), a combined per-frame panel (top-right)
and a combined cumulative panel (bottom-right), with the legend/notes in the
bottom-left.  The two combined panels each overlay three metrics for both
methods on one log-y axis -- colour = method, linestyle+marker = metric:
  per-frame  (per measure-reprepare segment): # circuits, deepest circuit
             depth, total CX in the frame (= # circuits x CX/circuit)
  cumulative (summed over the run's frames): # circuits, depth, CX

The qubits panel is a stacked bar: for CH the register width is split into
data (the 2^q grid), state-prep ancillas (MPS bond qubits) and evolution
ancillas (heat block-encoding / post-selection), reconstructed by rebuilding
the actual segment circuit; QLBM has no prep register and stays a flat bar.

Also writes a sidecar <out>.json of the harvested numbers so the figure's
values are inspectable / citable without re-running.

Usage:
    plot_circuit_resources_bakeoff.py <dataset.json> [--out fig.png]
"""

import argparse
import json
import re
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt

# Match the movie's per-method colours (plot_method_compare.METHOD_STYLE).
METHOD_STYLE = {
    "cole_hopf_circuit": {"color": "#17becf", "label": "Cole-Hopf"},
    "qlbm_circuit": {"color": "#d62728", "label": "QLBM"},
}

# Stacked-qubit segment colours (data / state-prep / evolution).
QUBIT_PARTS = [
    ("data", "CH data (2^q grid)", "#1f77b4"),
    ("prep", "CH state-prep ancillas", "#ff7f0e"),
    ("evo", "CH evolution ancillas", "#2ca02c"),
]


def _ch_qubit_split(q: int, segment_size: int, bond_dim: int | None,
                    propagator: str, total: int) -> dict:
    """Decompose a Cole-Hopf run's register width into data / state-prep /
    evolution qubits by rebuilding its actual segment circuit (the single
    source of truth for n_bond / n_heat_anc).  Falls back to the analytic
    split if the solver source can't be imported."""
    try:
        import numpy as np
        # lib_cole_hopf_circuit is normally importable from the ch-lbm venv;
        # as a fallback (e.g. run outside that venv) add the sibling solver
        # repo's src/ to the path.  This postproc tree lives under
        # q8020-cfd-experiments/aux/...; the solver is a sibling repo.
        src = (Path(__file__).resolve().parents[4]
               / "q8020-cfd-ch-lbm" / "src")
        if src.exists() and str(src) not in sys.path:
            sys.path.insert(0, str(src))
        from lib_cole_hopf_circuit import build_segment_circuit
        n = 2 ** q
        x = np.arange(n) / n
        phi = np.exp(0.3 * np.sin(2 * np.pi * x))      # generic positive state
        phi = phi / np.linalg.norm(phi)
        _, total_q, n_bond, n_heat_anc = build_segment_circuit(
            phi, q, nu=0.03, dt=0.1 / n, segment_size=segment_size,
            L_box=1.0, bc="periodic",
            bond_dim=bond_dim, use_mps_prep=True,
        )
        return {"data": q, "prep": n_bond, "evo": n_heat_anc}
    except Exception as e:           # pragma: no cover - diagnostic fallback
        print(f"  CH qubit-split rebuild failed ({e}); inferring from total",
              file=sys.stderr)
        n_heat_anc = min(q, segment_size)
        return {"data": q, "prep": max(total - q - n_heat_anc, 0),
                "evo": n_heat_anc}


def _find_analysis(o: dict | list) -> dict | None:
    """Locate the harvested analysis fragment (the one carrying the
    per-segment circuit metrics) anywhere in a results JSON."""
    if isinstance(o, dict):
        if "per_step_metrics" in o:
            return o
        for v in o.values():
            r = _find_analysis(v)
            if r is not None:
                return r
    elif isinstance(o, list):
        for v in o:
            r = _find_analysis(v)
            if r is not None:
                return r
    return None


def _depth(m: dict) -> int:
    """Post-transpile depth of the frame's circuit."""
    after = (m.get("transpile") or {}).get("after") or {}
    return int(m.get("circuit_depth", after.get("depth")) or 0)


def _cx(m: dict) -> int:
    """Post-transpile CX count of one circuit in the frame."""
    after = (m.get("transpile") or {}).get("after") or {}
    g = m.get("gate_counts", after.get("gate_counts")) or {}
    return int(g.get("cx", 0) or 0)


def _resolve_run_dir(base: Path, rel: str) -> Path:
    """Resolve a run's stored 'path' to an existing dir.  First try it as a
    plain relative path from the dataset's own dir; if that misses (the
    dataset may have been relocated so its ../.. prefix is stale), re-anchor
    on the 'results/<tail>' segment against the results/ tree found by walking
    up from the dataset.  Returns the plain resolution if neither exists."""
    direct = (base / rel).resolve()
    if direct.exists():
        return direct
    m = re.search(r"results/(.*)$", rel)
    if m:
        tail = m.group(1)
        for anc in [base, *base.parents]:
            cand = anc / "results" / tail
            if cand.exists():
                return cand.resolve()
    return direct


def _harvest(case_dir: Path) -> dict | None:
    """Pull per-frame and cumulative circuit metrics for one run.  Returns
    None if the case has no circuit analysis (e.g. the FTCS reference)."""
    hits = sorted(case_dir.glob("q8020_analysis_*.json"))
    if not hits:
        return None
    an = _find_analysis(json.loads(hits[0].read_text()))
    if an is None or an.get("n_qubits") is None:
        return None
    psm = sorted(
        (m for m in (an.get("per_step_metrics") or [])
         if m.get("step") is not None),
        key=lambda m: m["step"],
    )
    if not psm:
        return None
    # Per frame: # circuits, deepest depth, total CX (# circuits x CX/circuit).
    frame_ncirc = [int(m.get("n_circuits", 0) or 0) for m in psm]
    frame_depth = [_depth(m) for m in psm]
    frame_cx_each = [_cx(m) for m in psm]
    frame_cx_total = [n * c for n, c in zip(frame_ncirc, frame_cx_each)]
    return {
        "n_qubits": int(an["n_qubits"]),
        "n_frames": len(psm),
        # Per-frame representative values (max over frames; constant for these
        # runs, but max keeps the figure honest if a future run varies).
        "circ_per_frame": max(frame_ncirc, default=0),
        "deepest_depth": max(frame_depth, default=0),
        "cx_per_frame": max(frame_cx_total, default=0),
        "cx_per_circuit": max(frame_cx_each, default=0),
        # Cumulative over the run.
        "cum_circ": sum(frame_ncirc),
        "cum_depth": sum(frame_depth),
        "cum_cx": sum(frame_cx_total),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("dataset", help="path to the bakeoff dataset JSON")
    ap.add_argument("--out", default=None, help="output PNG path (combined)")
    ap.add_argument("--split", action="store_true",
                    help="emit the qubits and per-step panels as two "
                         "standalone PNGs instead of one combined figure")
    ap.add_argument("--out-a", default=None,
                    help="qubits-panel PNG path (implies --split)")
    ap.add_argument("--out-b", default=None,
                    help="per-step-panel PNG path (implies --split)")
    ap.add_argument("--out-twin", default=None,
                    help="compact single-panel PNG: qubit bars (left, "
                         "linear) + circuit cost lines (right, log)")
    args = ap.parse_args()
    if args.out_a or args.out_b:
        args.split = True

    ds_path = Path(args.dataset).resolve()
    ds = json.loads(ds_path.read_text())
    base = ds_path.parent

    # series[method] = list of harvested points (one per q), sorted by q.
    # inputs = provenance record of every run dir + analysis file consumed.
    series: dict[str, list[dict]] = {}
    inputs: list[dict] = []
    for run in ds.get("runs", []):
        method = run.get("method", "")
        if method not in METHOD_STYLE:
            continue  # skip FTCS reference / classical
        case_dir = _resolve_run_dir(base, run["path"])
        an_hits = sorted(case_dir.glob("q8020_analysis_*.json"))
        inputs.append({
            "label": run.get("label", ""),
            "method": method,
            "q": run.get("q"),
            "stored_path": run["path"],
            "resolved_dir": str(case_dir),
            "analysis_file": an_hits[0].name if an_hits else None,
            "exists": case_dir.exists(),
        })
        h = _harvest(case_dir)
        if h is None:
            print(f"  {run.get('label')}: no circuit metrics, skipping",
                  file=sys.stderr)
            continue
        h["q"] = int(run["q"])
        h["label"] = run.get("label", "")
        # CH register split (data / prep / evolution).  segment_size from the
        # dataset global; bond_dim / propagator from the run entry.
        if method == "cole_hopf_circuit":
            g = ds.get("global", {})
            h["qubit_split"] = _ch_qubit_split(
                q=h["q"],
                segment_size=int(g.get("segment_size", 5)),
                bond_dim=run.get("bond_dim"),
                propagator=run.get("propagator",
                                   g.get("propagator", "qft-diagonal")),
                total=h["n_qubits"],
            )
        series.setdefault(method, []).append(h)
    for method in series:
        series[method].sort(key=lambda p: p["q"])
    if not series:
        print("No circuit-bearing runs found in dataset.", file=sys.stderr)
        sys.exit(1)

    # The per-step panel overlays 3 metrics x 2 methods on a log y-axis:
    # colour = method, (linestyle, marker) = metric.  (key, label, ls, marker).
    per_step = [
        ("circ_per_frame", "circuits / step", ":", "o"),
        ("deepest_depth", "deepest depth", "-", "s"),
        ("cx_per_frame", "CX / step", "--", "^"),
    ]

    all_q = sorted({p["q"] for pts in series.values() for p in pts})

    def _draw_combined(ax, metrics, title):
        """Overlay several metrics for both methods on one log-y panel."""
        for method, pts in series.items():
            mcolor = METHOD_STYLE[method]["color"]
            xs = [p["q"] for p in pts]
            for key, _lbl, ls, _mk in metrics:
                ys = [p[key] for p in pts]
                ax.plot(xs, ys, ls=ls, marker="", lw=3.0, color=mcolor)
        ax.set_xlabel("problem size (q)", fontsize=17)
        ax.set_xticks(all_q)
        ax.set_yscale("log")
        ax.grid(True, which="both", alpha=0.3)
        ax.tick_params(labelsize=14)
        ax.set_title(title, fontsize=20, fontweight="bold")

    def _draw_faceted(fig, metrics):
        """One log-y panel per metric, shared x=q; colour = method.  Each
        panel is a clean two-line CH-vs-QLBM comparison, so no linestyle
        decoding is needed.  Markers mark the 3 discrete q measurements."""
        axes = fig.subplots(len(metrics), 1, sharex=True)
        for ax, (key, lbl, _ls, _mk) in zip(axes, metrics):
            for method, pts in series.items():
                mcolor = METHOD_STYLE[method]["color"]
                xs = [p["q"] for p in pts]
                ys = [p[key] for p in pts]
                ax.plot(xs, ys, marker="o", ms=8, lw=3.0, color=mcolor,
                        label=METHOD_STYLE[method]["label"])
            ax.set_yscale("log")
            ax.set_ylabel(lbl, fontsize=15)
            ax.set_xticks(all_q)
            ax.grid(True, which="both", alpha=0.3)
            ax.tick_params(labelsize=13)
        axes[-1].set_xlabel("problem size (q)", fontsize=17)
        axes[0].legend(loc="upper left", fontsize=13, frameon=False)
        return axes

    # Twin-panel right-axis metrics: colour = method, (linestyle, marker) =
    # metric.  (key, label, linestyle, marker).
    twin_metrics = [
        ("deepest_depth", "depth", "--", "o"),
    ]

    def _draw_twin(ax):
        """Single compact panel: stacked qubit bars on the left (linear)
        axis, per-method circuit-cost metrics overlaid as log-scale lines on
        a right twin axis.  x is the integer bar index (q = 4/6/8)."""
        ax2 = ax.twinx()
        # Bar total labels go on ax2 so they sit above the depth lines.
        _draw_qubits_stacked(ax, top_label_ax=ax2)
        ax.set_ylabel("qubits", fontsize=13)
        for method, pts in series.items():
            mcolor = METHOD_STYLE[method]["color"]
            pts = sorted(pts, key=lambda p: p["q"])
            xs = [all_q.index(p["q"]) for p in pts]
            for key, _lbl, ls, mk in twin_metrics:
                ys = [p[key] for p in pts]
                ax2.plot(xs, ys, ls=ls, marker=mk, ms=6, lw=2.5,
                         color=mcolor, zorder=3)
        ax2.set_yscale("log")
        ax2.set_ylabel("circuit depth", fontsize=13)
        ax2.tick_params(labelsize=12)
        # Headroom above the top line so the (flat, high) QLBM depth clears
        # the upper-left legend.
        lo, hi = ax2.get_ylim()
        ax2.set_ylim(lo, hi * 6.0)
        return ax2

    def _draw_qubits_stacked(ax, top_label_ax=None):
        """Grouped bars per q: CH stacked into data / prep / evolution,
        QLBM a single flat bar (no prep register).  Bar total-count labels
        go on top_label_ax (with a white background, above any twin-axis
        line) when given, else on ax."""
        tla = top_label_ax if top_label_ax is not None else ax
        tbbox = dict(boxstyle="round,pad=0.12", fc="white", ec="none",
                     alpha=0.95)
        bw = 0.36
        methods = list(series)
        for mi, method in enumerate(methods):
            pts = {p["q"]: p for p in series[method]}
            off = (mi - (len(methods) - 1) / 2) * (bw + 0.04)
            for q in all_q:
                p = pts.get(q)
                if p is None:
                    continue
                xpos = all_q.index(q) + off
                split = p.get("qubit_split")
                if split:
                    bottom = 0
                    for kkey, _lbl, kcol in QUBIT_PARTS:
                        hgt = split.get(kkey, 0)
                        if hgt <= 0:
                            continue
                        ax.bar(xpos, hgt, bw, bottom=bottom, color=kcol,
                               edgecolor="white", linewidth=1.2)
                        tla.annotate(
                            str(hgt), (xpos, bottom + hgt / 2),
                            xycoords=ax.transData, ha="center",
                            va="center", fontsize=9, color="white",
                            fontweight="bold", zorder=6)
                        bottom += hgt
                    tla.annotate(
                        str(p["n_qubits"]), (xpos, bottom),
                        xycoords=ax.transData, ha="center", va="bottom",
                        fontsize=10, color=METHOD_STYLE[method]["color"],
                        bbox=tbbox, zorder=6)
                else:
                    ax.bar(xpos, p["n_qubits"], bw,
                           color=METHOD_STYLE[method]["color"],
                           edgecolor="white", linewidth=1.2)
                    tla.annotate(
                        str(p["n_qubits"]), (xpos, p["n_qubits"]),
                        xycoords=ax.transData, ha="center", va="bottom",
                        fontsize=10, color=METHOD_STYLE[method]["color"],
                        bbox=tbbox, zorder=6)
        from matplotlib.ticker import MaxNLocator
        ax.set_xticks(range(len(all_q)))
        ax.set_xticklabels([str(q) for q in all_q])
        ax.margins(y=0.18)
        ax.set_ylim(bottom=0)
        ax.yaxis.set_major_locator(MaxNLocator(integer=True))
        ax.tick_params(labelsize=14)
        ax.grid(True, axis="y", alpha=0.3)
        # CH = stacked multicolour, QLBM = solid (per the legend); no per-bar
        # method label needed.
        ax.set_title("Total qubits", fontsize=13, fontweight="bold")

    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch

    # Legend handles reused by both layouts.
    part_h = [Patch(facecolor=c, label=lbl) for _, lbl, c in QUBIT_PARTS]
    method_h = [Line2D([], [], color=METHOD_STYLE[m]["color"], lw=3.0,
                       label=METHOD_STYLE[m]["label"]) for m in series]
    # QLBM as a solid patch so its bar-chart legend swatch matches the
    # stacked-part patches (a Line2D key renders shorter).
    qlbm_patch = Patch(facecolor=METHOD_STYLE["qlbm_circuit"]["color"],
                       label=METHOD_STYLE["qlbm_circuit"]["label"])
    metric_h = [Line2D([], [], color="0.35", ls=ls, marker="", lw=3.0,
                       label=lbl) for _key, lbl, ls, _mk in per_step]

    outs: list[Path] = []
    if args.out_twin:
        # Compact single panel: qubit bars (left, linear) + CX/step lines
        # (right, log).  Two colours (CH/QLBM) carry both the bar family and
        # the cost line, so one small legend covers everything.
        fig_t, ax_t = plt.subplots(figsize=(6.5, 4.2))
        _draw_twin(ax_t)
        ax_t.set_title("Circuit costs", fontsize=13, fontweight="bold")
        # One right-axis key per (method x metric), coloured by method so
        # both CH and QLBM depth lines are identified.
        method_abbr = {"cole_hopf_circuit": "CH", "qlbm_circuit": "QLBM"}
        cost_metric_h = [
            Line2D([], [], color=METHOD_STYLE[m]["color"], ls=ls, marker=mk,
                   ms=6, lw=2.5,
                   label=f"{method_abbr.get(m, METHOD_STYLE[m]['label'])} "
                   f"{lbl}")
            for m in series for _key, lbl, ls, mk in twin_metrics
        ]
        ax_t.legend(
            handles=part_h + [qlbm_patch] + cost_metric_h,
            loc="upper left", fontsize=8, frameon=False, ncol=2,
        )
        fig_t.tight_layout()
        out_t = Path(args.out_twin)
        fig_t.savefig(str(out_t), dpi=150)
        plt.close(fig_t)
        outs.append(out_t)
    if args.split:
        # Two standalone panels, each self-contained with its own legend.
        # (a) qubits stacked bar; (b) per-step log-y metric overlay.
        fig_a, ax_q = plt.subplots(figsize=(6.5, 5.2))
        _draw_qubits_stacked(ax_q)
        ax_q.legend(handles=part_h + [qlbm_patch], loc="upper left",
                    fontsize=11, frameon=False)
        fig_a.tight_layout()
        out_a = (Path(args.out_a) if args.out_a else ds_path.with_name(
            ds_path.stem + "_circuit_resources_fig1_a.png"))
        fig_a.savefig(str(out_a), dpi=150)
        plt.close(fig_a)
        outs.append(out_a)

        fig_b = plt.figure(figsize=(6.5, 8.5))
        _draw_faceted(fig_b, per_step)
        fig_b.suptitle("Per-step circuit cost", fontsize=20,
                       fontweight="bold")
        fig_b.tight_layout(rect=(0, 0, 1, 0.97))
        out_b = (Path(args.out_b) if args.out_b else ds_path.with_name(
            ds_path.stem + "_circuit_resources_fig2_b.png"))
        fig_b.savefig(str(out_b), dpi=150)
        plt.close(fig_b)
        outs.append(out_b)
    elif not args.out_twin:
        # 1x2: qubits (stacked) | per-step combined.  The qubits panel carries
        # the CH fill legend; a shared method+metric legend along the bottom.
        fig, (ax_q, ax_ps) = plt.subplots(1, 2, figsize=(13, 5.2))
        _draw_qubits_stacked(ax_q)
        _draw_combined(ax_ps, per_step, "per step")
        ax_q.legend(handles=part_h, loc="upper left", fontsize=8,
                    frameon=False)
        fig.legend(
            handles=method_h + metric_h, loc="lower center",
            ncol=len(method_h) + len(metric_h), fontsize=9, frameon=False,
            title="method (colour)      metric (line)", title_fontsize=9,
        )
        fig.suptitle(
            f"{ds.get('name', ds_path.stem)} — circuit resources "
            f"(CH grid-driven, QLBM grid-independent per-circuit)",
            fontsize=13, fontweight="bold",
        )
        fig.tight_layout(rect=(0, 0.08, 1, 0.95))
        out = Path(args.out) if args.out else ds_path.with_name(
            ds_path.stem + "_circuit_resources.png")
        fig.savefig(str(out), dpi=150)
        plt.close(fig)
        outs.append(out)

    # Provenance sidecar next to EACH figure: how it was made (code +
    # command), what it was made from (dataset + every resolved results/ run
    # dir and analysis file consumed), and the numbers actually plotted.
    script = Path(__file__).resolve()
    dump = {
        "figure": None,                       # filled per-output below
        "generated_by": {
            "script": script.name,
            "script_path": str(script),
            "command": " ".join(["python", script.name, *sys.argv[1:]]),
        },
        "source_dataset": {
            "name": ds.get("name", ds_path.stem),
            "path": str(ds_path),
            "global": ds.get("global", {}),
        },
        "inputs": inputs,                     # results/ run dirs + analysis files
        "series": {
            METHOD_STYLE[m]["label"]: series[m] for m in series
        },
    }
    for o in outs:
        prov = dict(dump, figure=o.name)
        o.with_suffix(".json").write_text(json.dumps(prov, indent=2))
        print(f"wrote {o}")
        print(f"wrote {o.with_suffix('.json')}")


if __name__ == "__main__":
    main()
