"""Animate every run listed in a datasets JSON onto one set of axes.

Unlike plot_method_compare.py (which globs a single sweep dir and keys
series by method), this reads a curated dataset descriptor -- a group of
runs with shared physics but different runtime params (target, backend,
shots) -- and draws each run as its own labelled line in one movie.

Usage:
    plot_dataset_movie.py <dataset.json> [--out movie.gif] [--fps 2]

The dataset JSON shape (see analysis/.../smooth_movie_q3.json):
    {
      "name": "...", "global": {...},
      "runs": [
        {"label": "...", "method": "...", "path": "<rel-to-json>", ...},
        ...
      ]
    }

Each run's solution curves come from a q8020_artifacts_*.json holding
{"grid": [...], "solution_steps": {"0": [...], ...}}.  Hardware runs
store theirs under <path>/method_compare/<method>/; sim/reference runs
store theirs directly in <path>.  Both layouts are resolved here.
"""

import argparse
import json
import re
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.animation as manimation
import matplotlib.pyplot as plt
import numpy as np


def _grid_legend(ax, err_runs: list, color: dict) -> None:
    """Compact 2-column legend for a CH/QLBM q-dialup error panel: bold
    column headers 'CH' | 'QLBM' centred over each column, rows 'q4' 'q6'
    'q8' each with a short colour bar.  Falls back to a plain legend if
    labels aren't the expected q{n}_{method} shape.  Header space is
    reserved with a blank legend title; the two headers are drawn as
    independent fig.text (legend children get re-laid on every draw, so
    they can't be repositioned in place) centred on the measured column x."""
    from matplotlib.lines import Line2D

    cols = [("CH", "_ch"), ("QLBM", "_qlbm")]
    by_col: dict[str, list] = {suf: [] for _h, suf in cols}
    for r in err_runs:
        for _hdr, suf in cols:
            if r["label"].endswith(suf):
                by_col[suf].append(r)
                break
    if not all(by_col[suf] for _h, suf in cols):
        ax.legend(loc="upper left", ncol=2)          # unexpected labels
        return

    handles, labels = [], []
    for _hdr, suf in cols:
        for r in sorted(by_col[suf], key=lambda d: d["label"]):
            handles.append(Line2D([], [], color=color[r["label"]], lw=3.0))
            labels.append(r["label"].split("_")[0])   # 'q4' etc.
    fs = 12
    leg = ax.legend(
        handles, labels, loc="upper left", ncol=2, fontsize=fs,
        handlelength=1.2, columnspacing=1.0, handletextpad=0.5,
        labelspacing=0.3, borderaxespad=0.4, title=" ", title_fontsize=fs,
    )

    # Centre a bold header over each column, using the rendered positions of
    # the q-row labels (cluster the 6 by x into two columns, so this is
    # independent of matplotlib's fill order).
    fig = ax.figure
    fig.canvas.draw()
    rend = fig.canvas.get_renderer()
    exts = [t.get_window_extent(rend) for t in leg.get_texts()]
    xmid = (min(e.x0 for e in exts) + max(e.x0 for e in exts)) / 2
    em = fs * fig.dpi / 72.0
    handle_off = (1.2 + 0.5) * em                    # bar length + text pad
    leg_top = leg.get_window_extent(rend).y1
    fw, fh = fig.bbox.width, fig.bbox.height
    for hdr, _suf in cols:
        grp = [e for e in exts
               if (e.x0 < xmid) == (hdr == cols[0][0])]
        cx = (min(e.x0 for e in grp) - handle_off
              + max(e.x1 for e in grp)) / 2
        # Sit just above the q-rows inside the reserved title strip (bias
        # toward the row tops so the header stays within the small box).
        row_top = max(e.y1 for e in grp)
        cy = 0.78 * row_top + 0.22 * leg_top
        fig.text(cx / fw, cy / fh, hdr, ha="center", va="center",
                 fontsize=fs, fontweight="bold")


def _shock_pct(g: dict, run: dict | None = None) -> float | None:
    """Effective % of inviscid shock time a run reached.  q and n_steps may
    live on the run (they differ across a q-dialup dataset) or, for a single-
    physics dataset, on the global block; the run value wins when present.
    Uses an explicit shock_pct_effective if given, else derives it from
    t_end = n_steps * cfl * dx, t_shock = 1/max|du0/dx| on the N=2^q grid for
    the sine IC u0 = A*sin(2*pi*x).  Note t_shock is evaluated on the run's
    own grid, so a coarse grid's under-resolved gradient is reflected."""
    src = {**g, **(run or {})}
    if "shock_pct_effective" in src:
        return float(src["shock_pct_effective"])
    try:
        q = int(src["q"])
        cfl = float(src["cfl"])
        n_steps = int(src["n_steps"])
        amp = float(src["ic_amplitude"])
    except (KeyError, TypeError, ValueError):
        return None
    n = 2 ** q
    dx = 1.0 / n
    x = np.arange(n) * dx
    u0 = amp * np.sin(2 * np.pi * x)
    max_grad = float(np.max(np.abs(np.gradient(u0, dx))))
    if max_grad <= 0:
        return None
    t_shock = 1.0 / max_grad
    t_end = n_steps * cfl * dx
    return 100.0 * t_end / t_shock


def _resolve_run_dir(base: Path, rel: str) -> Path:
    """Resolve a run's stored 'path' to an existing dir.  Try it as a plain
    relative path from the dataset's dir first; if that misses (the dataset
    may have been relocated so its ../.. prefix is stale), re-anchor on the
    'results/<tail>' segment against the results/ tree found by walking up."""
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


def _find_artifacts(run_dir: Path, method: str) -> Path | None:
    """Locate the artifacts JSON for a run, trying the direct case dir
    first, then the hardware method_compare/<method>/ subdir."""
    candidates = [
        run_dir,
        run_dir / "method_compare" / method,
    ]
    for d in candidates:
        hits = sorted(d.glob("q8020_artifacts_*.json"))
        if hits:
            return hits[0]
    return None


def _run_inputs(run: dict, base: Path) -> dict:
    """Provenance record for one run: the resolved results/ dir, the artifacts
    file actually consumed, and ALL prior per-run artifacts present alongside
    it (every q8020_artifacts_* / q8020_analysis_* in the dir and, for
    hardware runs, the method_compare/<method>/ subdir)."""
    method = run.get("method", "")
    run_dir = _resolve_run_dir(base, run["path"])
    art = _find_artifacts(run_dir, method)
    search_dirs = [run_dir, run_dir / "method_compare" / method]
    found = []
    for d in search_dirs:
        for pat in ("q8020_artifacts_*.json", "q8020_analysis_*.json"):
            found += [str(p) for p in sorted(d.glob(pat))]
    return {
        "label": run.get("label", ""),
        "method": method,
        "target": run.get("target"),
        "stored_path": run["path"],
        "resolved_dir": str(run_dir),
        "artifacts_file": str(art) if art else None,
        "prior_artifacts": found,
        "exists": run_dir.exists(),
    }


def _load_run(run: dict, base: Path) -> dict | None:
    """Read a run's grid + per-step snapshots; None if unavailable."""
    run_dir = _resolve_run_dir(base, run["path"])
    art = _find_artifacts(run_dir, run.get("method", ""))
    if art is None:
        print(f"  {run['label']}: no artifacts under {run_dir}",
              file=sys.stderr)
        return None
    data = json.loads(art.read_text())
    grid = np.array(data.get("grid", []))
    steps = {
        int(k): np.array(v)
        for k, v in data.get("solution_steps", {}).items()
    }
    if grid.size == 0 or not steps:
        print(f"  {run['label']}: empty grid/steps", file=sys.stderr)
        return None
    # Normalize each run's timeline to [0, 1] (step / max_step).  Runs
    # differ in grid size AND step count but all end at the same physical
    # point, so the normalized fraction is the shared movie clock.
    keys = sorted(steps)
    smax = keys[-1] or 1
    times = [k / smax for k in keys]
    snaps = [steps[k] for k in keys]
    return {
        "label": run["label"], "grid": grid,
        "times": times, "snaps": snaps,
    }


def _sample(run: dict, t: float) -> np.ndarray:
    """Profile at the snapshot nearest normalized time t, on run's grid."""
    i = min(range(len(run["times"])),
            key=lambda j: abs(run["times"][j] - t))
    return run["snaps"][i]


def _sample_on(run: dict, t: float, target_grid: np.ndarray) -> np.ndarray:
    """Run's profile at time t interpolated onto target_grid (for error
    against a reference on a different grid)."""
    y = _sample(run, t)
    if len(run["grid"]) == len(target_grid) and np.allclose(
        run["grid"], target_grid
    ):
        return y
    return np.interp(target_grid, run["grid"], y)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("dataset", help="path to the dataset JSON")
    ap.add_argument("--out", default=None, help="output GIF path")
    ap.add_argument("--fps", type=int, default=2, help="frames per second")
    ap.add_argument(
        "--ylim", type=float, default=None,
        help="clamp profile panel to +/- this value (a detonating run "
             "otherwise auto-scales the axis and hides the others); "
             "overrides the dataset's global.ylim if set",
    )
    ap.add_argument(
        "--still", default=None,
        help="save one frame as a static PNG instead of the GIF: "
             "'first', 'last', or an integer frame index.",
    )
    ap.add_argument(
        "--panel", default="both", choices=["both", "profile", "error"],
        help="with --still, which panel to save (default both). 'profile' "
             "= the u(x,t) panel, 'error' = the L2 panel only.",
    )
    args = ap.parse_args()

    # Shared figure style (must match the sibling script's figures): large
    # fonts, thick markerless curves.  Set before any Axes are created so
    # titles, labels and ticks all pick it up.
    plt.rcParams.update({
        "axes.titlesize": 20,
        "axes.titleweight": "bold",
        "axes.labelsize": 17,
        "xtick.labelsize": 14,
        "ytick.labelsize": 14,
        "legend.fontsize": 14,
        "lines.linewidth": 3.0,
        "lines.markersize": 0,
    })

    ds_path = Path(args.dataset).resolve()
    ds = json.loads(ds_path.read_text())
    base = ds_path.parent

    g = ds.get("global", {})
    runs = []
    inputs = []
    for r in ds.get("runs", []):
        inputs.append(_run_inputs(r, base))   # provenance, incl. prior artifacts
        loaded = _load_run(r, base)
        if loaded is not None:
            loaded["shock_pct"] = _shock_pct(g, r)
            runs.append(loaded)
    if not runs:
        print("No usable runs found.", file=sys.stderr)
        sys.exit(1)

    # Shared movie clock = union of every run's NORMALIZED times.  Runs
    # differ in grid size and step count but all end at the same physical
    # point, so step/max_step is the common timeline.
    frame_times = sorted({t for run in runs for t in run["times"]})

    # Identify the reference run (the error baseline) from the dataset.
    # Error panel measures every OTHER run's L2 distance to it; the
    # reference itself is drawn in the profile panel but not the error
    # panel (its error is zero by definition).
    ref_label = None
    for r in ds.get("runs", []):
        if r.get("method") == "ftcs_reference" or r.get("target") == "reference":
            ref_label = r["label"]
            break
    ref_run = next((r for r in runs if r["label"] == ref_label), None)

    # Per-frame L2 error of each non-reference run vs the reference,
    # interpolated onto the reference grid (runs live on different grids).
    err_runs = [r for r in runs if r["label"] != ref_label]
    err_curve: dict[str, list[float]] = {}
    if ref_run is not None:
        rgrid = ref_run["grid"]
        for run in err_runs:
            errs = []
            for t in frame_times:
                diff = _sample_on(run, t, rgrid) - _sample(ref_run, t)
                errs.append(float(np.sqrt(np.mean(diff ** 2))))
            err_curve[run["label"]] = errs

    # y-limits across every snapshot, with a small margin.
    all_vals = np.concatenate(
        [v for run in runs for v in run["snaps"]]
    )
    ymin, ymax = float(all_vals.min()), float(all_vals.max())
    pad = 0.08 * (ymax - ymin or 1.0)
    ymin, ymax = ymin - pad, ymax + pad
    # Profile clamp: CLI --ylim wins, else the dataset's global.ylim (so a
    # detonating run doesn't auto-scale the axis and hide the others).
    ylim = args.ylim if args.ylim is not None else g.get("ylim")
    if ylim is not None:
        ymin, ymax = -float(ylim), float(ylim)

    have_err = bool(err_curve)
    if have_err:
        fig, (ax, ax_err) = plt.subplots(
            2, 1, figsize=(9, 9), height_ratios=[2, 1],
        )
    else:
        fig, ax = plt.subplots(figsize=(9, 5.5))
        ax_err = None

    cmap = plt.get_cmap("tab10")
    color = {run["label"]: cmap(i % 10) for i, run in enumerate(runs)}

    # ── profile panel ──────────────────────────────────────────────
    lines = {}
    for run in runs:
        lbl = run["label"].removeprefix("hw_")
        lbl = lbl.replace("sim_shots_0_ideal", "sim_ideal")
        (ln,) = ax.plot(
            [], [], marker="", lw=3.0,
            color=color[run["label"]], label=lbl,
        )
        lines[run["label"]] = ln

    ax.set_xlim(0.0, 1.0)
    ax.set_ylim(ymin, ymax)
    ax.set_xlabel("x", fontsize=22)
    ax.set_ylabel("u(x, t)", fontsize=22)
    ax.tick_params(labelsize=18)
    ax.grid(True, alpha=0.3)
    ax.legend(loc="upper right", ncol=2, handlelength=1.2,
              columnspacing=1.0, handletextpad=0.5, borderaxespad=0.4)
    title = ax.set_title("", fontweight="normal")
    # Title shock %: a single value if every run reached the same fraction,
    # else the min-max range across runs (a q-dialup set with mismatched
    # n_steps lands the coarse grids at a different % than the fine ones).
    sps = sorted({round(r["shock_pct"], 1) for r in runs
                  if r.get("shock_pct") is not None})
    if not sps:
        shock_str = ""
    elif len(sps) == 1:
        shock_str = f", to shock {sps[0]:.0f}%"
    else:
        shock_str = f", to shock {sps[0]:.0f}-{sps[-1]:.0f}%"
    # q: use the global scalar if set, else the range swept across runs.
    if "q" in g:
        q_str = str(g["q"])
    else:
        qs = sorted({r["q"] for r in ds.get("runs", []) if "q" in r})
        if not qs:
            q_str = "sweep"
        elif len(qs) == 1:
            q_str = str(qs[0])
        else:
            q_str = f"{qs[0]}-{qs[-1]}"
    subtitle = (
        f"q={q_str}, nu={g.get('nu', '?')}, "
        f"A={g.get('ic_amplitude', '?')}, cfl={g.get('cfl', '?')}"
        f"{shock_str}"
    )

    # ── error panel ────────────────────────────────────────────────
    err_lines = {}
    if have_err:
        # Robust y-limit: a detonating run (error in the 10s-100s) would
        # crush every meaningful curve into the floor.  Scale to the
        # NON-detonated runs only -- a run is "detonated" if its final
        # error exceeds 5x the median final error across runs -- so the
        # comparison band is legible and blown-up curves clip off the top.
        finals = {k: v[-1] for k, v in err_curve.items()}
        med = float(np.median(list(finals.values()))) or 1.0
        tame = [v for k, vals in err_curve.items()
                for v in vals if finals[k] <= 5.0 * med]
        emax = (max(tame) if tame else max(finals.values())) * 1.4 or 1.0
        for run in err_runs:
            (ln,) = ax_err.plot(
                [], [], marker="", lw=3.0,
                color=color[run["label"]], label=run["label"],
            )
            err_lines[run["label"]] = ln
        ax_err.set_xlim(frame_times[0], frame_times[-1])
        ax_err.set_ylim(0.0, emax)
        ax_err.set_xlabel("normalized time (t / t_end)")
        ax_err.set_ylabel("L2 error vs FTCS")
        ax_err.grid(True, alpha=0.3)
        _grid_legend(ax_err, err_runs, color)

    def update(frame_idx: int):
        t = frame_times[frame_idx]
        for run in runs:
            lines[run["label"]].set_data(run["grid"], _sample(run, t))
        title.set_text(subtitle)
        artists = list(lines.values()) + [title]
        if have_err:
            xs = frame_times[: frame_idx + 1]
            for label, ln in err_lines.items():
                ln.set_data(xs, err_curve[label][: frame_idx + 1])
            artists += list(err_lines.values())
        return artists

    fig.tight_layout(rect=(0, 0, 1, 0.94))

    # ── still: render one frame's panel(s) as a static PNG ─────────────
    if args.still is not None:
        tok = args.still.strip().lower()
        if tok == "first":
            fidx = 0
        elif tok == "last":
            fidx = len(frame_times) - 1
        else:
            fidx = int(tok)
        fidx = max(0, min(fidx, len(frame_times) - 1))
        update(fidx)
        out = Path(args.out) if args.out else ds_path.with_name(
            f"{ds_path.stem}_still_{fidx}_{args.panel}.png")
        fig.canvas.draw()
        if args.panel == "both" or not have_err:
            fig.savefig(str(out), dpi=150)
        else:
            panel_ax = ax if args.panel == "profile" else ax_err
            other_ax = ax_err if args.panel == "profile" else ax
            # Hide the other panel and let matplotlib compute the tight crop.
            # Pass the panel's axis labels as extra artists so the tall,
            # rotated y-label is fully included at large font sizes (the
            # plain tight bbox under-measures it and clips the last chars).
            other_ax.set_visible(False)
            fig.canvas.draw()
            fig.savefig(str(out), dpi=150, bbox_inches="tight", pad_inches=0.1,
                        bbox_extra_artists=[panel_ax.yaxis.label,
                                            panel_ax.xaxis.label])
            other_ax.set_visible(True)
        plt.close(fig)
        # Provenance sidecar next to the still: how it was made (code +
        # command) and what from (dataset + every resolved results/ run dir,
        # the artifacts consumed, and any prior artifacts alongside them).
        script = Path(__file__).resolve()
        prov = {
            "figure": out.name,
            "generated_by": {
                "script": script.name,
                "script_path": str(script),
                "command": " ".join(["python", script.name, *sys.argv[1:]]),
            },
            "source_dataset": {
                "name": ds.get("name", ds_path.stem),
                "path": str(ds_path),
                "global": g,
            },
            "still": {
                "frame": fidx,
                "n_frames": len(frame_times),
                "t_over_t_end": frame_times[fidx],
                "panel": args.panel,
                "reference_run": ref_label,
            },
            "inputs": inputs,
            "l2_error_final": {
                lbl: errs[fidx] for lbl, errs in err_curve.items()
            } if err_curve else {},
        }
        out.with_suffix(".json").write_text(json.dumps(prov, indent=2))
        print(f"wrote {out}  (frame {fidx}/{len(frame_times) - 1}, "
              f"t/t_end={frame_times[fidx]:.2f}, panel={args.panel})")
        print(f"wrote {out.with_suffix('.json')}")
        return

    anim = manimation.FuncAnimation(
        fig, update, frames=len(frame_times), interval=1000 / args.fps,
        blit=False,
    )

    out = Path(args.out) if args.out else ds_path.with_suffix(".gif")
    anim.save(str(out), writer=manimation.PillowWriter(fps=args.fps))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
