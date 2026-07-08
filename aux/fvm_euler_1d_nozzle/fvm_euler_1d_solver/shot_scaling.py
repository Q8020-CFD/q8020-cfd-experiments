#!/usr/bin/env python3
"""Shot Scaling Study for FVM Euler 1D (nelem=5).

Compare how shot count affects convergence quality, circuit cost, and runtime
across two experiment sets: the original 2025-11-11 runs and the 2026-02-26-LuGo
runs, both at nelem=5.

Views:
  S1  Final residual vs shots (box plot)
  S2  Final fidelity vs shots (box plot)
  S3  Final L2 error vs shots (box plot)
  S4  Iterations to converge vs shots
  S5  Circuit cost (gate count / depth) vs shots
  S6  Total wall time vs shots
  S7  Efficiency frontier: L2 error vs total wall time
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Styling
# ---------------------------------------------------------------------------
COLOR_OLD = "#1f77b4"
COLOR_LUGO = "#d62728"
ALPHA_BAND = 0.2
ALPHA_BOX = 0.7

# ---------------------------------------------------------------------------
# 1. Loader
# ---------------------------------------------------------------------------

def _find_fragment(trial_dir: Path, section: str) -> Path | None:
    for p in trial_dir.iterdir():
        if p.name.startswith(f"q8020_{section}_") and p.name.endswith(".json"):
            return p
    return None


def load_trial(trial_dir: Path) -> dict:
    sections = ("results", "analysis", "artifacts", "case", "backend", "code")
    data: dict = {"_dir": trial_dir}
    for section in sections:
        fpath = _find_fragment(trial_dir, section)
        if fpath is not None:
            with open(fpath) as f:
                data[section] = json.load(f)
        else:
            data[section] = None
    return data


def load_shots_dir(shots_dir: Path) -> list[dict]:
    """Load all trial_* subdirectories under a shots_N directory."""
    trials = sorted(
        d for d in shots_dir.iterdir()
        if d.is_dir() and d.name.startswith("trial")
    )
    return [load_trial(t) for t in trials]


def discover_shot_counts(base_path: Path) -> dict[int, Path]:
    """Return {shot_count: path} for all shots_* directories."""
    result = {}
    for d in base_path.iterdir():
        if d.is_dir() and d.name.startswith("shots_"):
            try:
                n = int(d.name.split("_", 1)[1])
                result[n] = d
            except ValueError:
                pass
    return dict(sorted(result.items()))


# ---------------------------------------------------------------------------
# 2. DataFrame builders
# ---------------------------------------------------------------------------

def build_master_df(
    shot_dirs: dict[int, Path], series_label: str,
) -> pd.DataFrame:
    """Build one big DataFrame with per-trial final metrics for every shot count.

    Columns: series, shots, trial, final_residual, final_l2_abs,
             final_fidelity, final_linsys_resid, iters_to_converge,
             gate_count_median, depth_median,
             total_generate_s, total_transpile_s, total_execute_s, total_wall_s
    """
    rows = []
    for shots, sdir in shot_dirs.items():
        trials = load_shots_dir(sdir)
        for i, t in enumerate(trials):
            row: dict = {
                "series": series_label,
                "shots": shots,
                "trial": i,
            }

            # --- results fragment: residuals ---
            res = t.get("results")
            if res:
                rh = res.get("residual_history", [])
                if rh:
                    last = rh[-1]
                    row["final_residual"] = last["residual_total"]
                    row["iters_to_converge"] = int(last["iters"])

            # --- analysis fragment: HHL metrics ---
            ana = t.get("analysis")
            if ana:
                hm = ana.get("hhl_metrics", [])
                if hm:
                    last = hm[-1]
                    row["final_l2_abs"] = last["l2_error_abs"]
                    row["final_fidelity"] = last["fidelity"]
                    row["final_linsys_resid"] = last["linsys_residual"]

            # --- artifacts fragment: circuit cost + timing ---
            art = t.get("artifacts")
            if art:
                tp = art.get("transpile_passes", [])
                if tp:
                    gates = [r["after"]["gate_count"] for r in tp]
                    depths = [r["after"]["depth"] for r in tp]
                    row["gate_count_median"] = float(np.median(gates))
                    row["depth_median"] = float(np.median(depths))

                ct = art.get("circuit_timing_total_s", {})
                if ct:
                    row["total_generate_s"] = ct.get("generate", 0)
                    row["total_transpile_s"] = ct.get("transpile", 0)
                    row["total_execute_s"] = ct.get("execute", 0)
                    row["total_wall_s"] = ct.get("total", 0)
                elif tp:
                    # Fall back to summing per-step times
                    row["total_generate_s"] = sum(
                        r.get("wall_time_generate_s", 0) for r in tp)
                    row["total_transpile_s"] = sum(
                        r.get("wall_time_transpile_s", 0) for r in tp)
                    row["total_execute_s"] = sum(
                        r.get("wall_time_execute_s", 0) for r in tp)
                    row["total_wall_s"] = (
                        row["total_generate_s"]
                        + row["total_transpile_s"]
                        + row["total_execute_s"]
                    )

            rows.append(row)

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# 3. Plot helpers
# ---------------------------------------------------------------------------

def _paired_box(
    df: pd.DataFrame,
    ycol: str,
    ylabel: str,
    title: str,
    outpath: Path,
    logy: bool = True,
    subtitle: str = "",
):
    """Side-by-side box plots: old vs LuGo at each shot count."""
    shot_counts = sorted(df["shots"].unique())
    series_labels = sorted(df["series"].unique())
    n_shots = len(shot_counts)

    fig, ax = plt.subplots(figsize=(max(10, n_shots * 1.5), 5))
    width = 0.35
    x = np.arange(n_shots)

    color_map = {}
    for s in series_labels:
        if "lugo" in s.lower():
            color_map[s] = COLOR_LUGO
        else:
            color_map[s] = COLOR_OLD

    for j, series in enumerate(series_labels):
        data = []
        for sc in shot_counts:
            vals = df[(df["series"] == series) & (df["shots"] == sc)][ycol].dropna()
            data.append(vals.values)

        positions = x + (j - 0.5) * width + width / 2
        bp = ax.boxplot(
            data, positions=positions, widths=width * 0.8,
            patch_artist=True, showfliers=True,
            flierprops=dict(marker="o", markersize=3),
        )
        color = color_map[series]
        for patch in bp["boxes"]:
            patch.set_facecolor(color)
            patch.set_alpha(ALPHA_BOX)
        for element in ["whiskers", "caps", "medians"]:
            for line in bp[element]:
                line.set_color(color)
        # Invisible scatter for legend
        ax.scatter([], [], color=color, label=series, s=40)

    ax.set_xticks(x)
    ax.set_xticklabels([f"{sc:,}" for sc in shot_counts])
    ax.set_xlabel("Shots")
    ax.set_ylabel(ylabel)
    if logy:
        ax.set_yscale("log")
    ax.set_title(title, pad=16)
    if subtitle:
        ax.text(0.5, 1.0, subtitle, transform=ax.transAxes,
                ha="center", va="top", fontsize=9, color="0.4")
    ax.legend()
    ax.grid(True, alpha=0.3, axis="y")
    fig.tight_layout()
    fig.savefig(outpath, dpi=150)
    plt.close(fig)
    print(f"  Saved {outpath}")


def _paired_line(
    df_summary: pd.DataFrame,
    ycol: str,
    ylabel: str,
    title: str,
    outpath: Path,
    logy: bool = False,
    subtitle: str = "",
    err_col: str | None = None,
):
    """Line plot of a summary metric vs shots, one line per series."""
    fig, ax = plt.subplots(figsize=(9, 5))
    for series in sorted(df_summary["series"].unique()):
        sub = df_summary[df_summary["series"] == series].sort_values("shots")
        color = COLOR_LUGO if "lugo" in series.lower() else COLOR_OLD
        if err_col and err_col in sub.columns:
            ax.errorbar(
                sub["shots"], sub[ycol], yerr=sub[err_col],
                fmt="-o", color=color, label=series, capsize=4, markersize=5,
            )
        else:
            ax.plot(sub["shots"], sub[ycol], "-o", color=color,
                    label=series, markersize=5)

    ax.set_xscale("log")
    if logy:
        ax.set_yscale("log")
    ax.set_xlabel("Shots")
    ax.set_ylabel(ylabel)
    ax.set_title(title, pad=16)
    if subtitle:
        ax.text(0.5, 1.0, subtitle, transform=ax.transAxes,
                ha="center", va="top", fontsize=9, color="0.4")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(outpath, dpi=150)
    plt.close(fig)
    print(f"  Saved {outpath}")


# ---------------------------------------------------------------------------
# 4. View functions
# ---------------------------------------------------------------------------

def plot_s1_residual(df: pd.DataFrame, outdir: Path, subtitle: str = ""):
    """S1: Final residual vs shots."""
    _paired_box(df, "final_residual", "Final Residual",
                "Final Residual vs Shot Count", outdir / "s1_residual_vs_shots.png",
                logy=True, subtitle=subtitle)


def plot_s2_fidelity(df: pd.DataFrame, outdir: Path, subtitle: str = ""):
    """S2: Final fidelity vs shots."""
    _paired_box(df, "final_fidelity", "Fidelity",
                "Final Fidelity vs Shot Count", outdir / "s2_fidelity_vs_shots.png",
                logy=False, subtitle=subtitle)


def plot_s3_l2_error(df: pd.DataFrame, outdir: Path, subtitle: str = ""):
    """S3: Final L2 absolute error vs shots."""
    _paired_box(df, "final_l2_abs", "L2 Absolute Error",
                "Final L2 Error vs Shot Count", outdir / "s3_l2_error_vs_shots.png",
                logy=True, subtitle=subtitle)


def plot_s4_iterations(df: pd.DataFrame, outdir: Path, subtitle: str = ""):
    """S4: Iterations to converge vs shots."""
    _paired_box(df, "iters_to_converge", "Final Iteration",
                "Iterations to Converge vs Shot Count",
                outdir / "s4_iterations_vs_shots.png",
                logy=False, subtitle=subtitle)


def plot_s5_circuit_cost(df: pd.DataFrame, outdir: Path, subtitle: str = ""):
    """S5: Circuit cost (gate count and depth) vs shots."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    for ax, col, ylabel, title in [
        (axes[0], "gate_count_median", "Median Gate Count",
         "Gate Count vs Shot Count"),
        (axes[1], "depth_median", "Median Circuit Depth",
         "Circuit Depth vs Shot Count"),
    ]:
        for series in sorted(df["series"].unique()):
            sub = df[df["series"] == series]
            color = COLOR_LUGO if "lugo" in series.lower() else COLOR_OLD
            stats = sub.groupby("shots")[col].agg(["mean", "std"]).reset_index()
            stats = stats.sort_values("shots")
            ax.errorbar(
                stats["shots"], stats["mean"], yerr=stats["std"],
                fmt="-o", color=color, label=series, capsize=4, markersize=5,
            )
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlabel("Shots")
        ax.set_ylabel(ylabel)
        ax.set_title(title)
        ax.legend()
        ax.grid(True, alpha=0.3)

    if subtitle:
        fig.suptitle(subtitle, fontsize=9, color="0.4", y=1.01)
    fig.tight_layout()
    fig.savefig(outdir / "s5_circuit_cost_vs_shots.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {outdir / 's5_circuit_cost_vs_shots.png'}")


def plot_s6_wall_time(df: pd.DataFrame, outdir: Path, subtitle: str = ""):
    """S6: Total wall time breakdown vs shots."""
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))

    time_cols = [
        ("total_generate_s", "Generate Time (s)", "Generate"),
        ("total_transpile_s", "Transpile Time (s)", "Transpile"),
        ("total_execute_s", "Execute Time (s)", "Execute"),
    ]

    for ax, (col, ylabel, panel_title) in zip(axes, time_cols):
        for series in sorted(df["series"].unique()):
            sub = df[df["series"] == series]
            color = COLOR_LUGO if "lugo" in series.lower() else COLOR_OLD
            stats = sub.groupby("shots")[col].agg(["mean", "std"]).reset_index()
            stats = stats.sort_values("shots")
            ax.errorbar(
                stats["shots"], stats["mean"], yerr=stats["std"],
                fmt="-o", color=color, label=series, capsize=4, markersize=5,
            )
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlabel("Shots")
        ax.set_ylabel(ylabel)
        ax.set_title(f"{panel_title} vs Shot Count")
        ax.legend()
        ax.grid(True, alpha=0.3)

    if subtitle:
        fig.suptitle(subtitle, fontsize=9, color="0.4", y=1.01)
    fig.tight_layout()
    fig.savefig(outdir / "s6_wall_time_vs_shots.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {outdir / 's6_wall_time_vs_shots.png'}")


def _build_efficiency_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate per-series, per-shot-count means for efficiency views."""
    return (
        df.groupby(["series", "shots"])
        .agg(
            l2_mean=("final_l2_abs", "mean"),
            l2_std=("final_l2_abs", "std"),
            wall_mean=("total_wall_s", "mean"),
            wall_std=("total_wall_s", "std"),
            resid_mean=("final_residual", "mean"),
        )
        .reset_index()
        .sort_values(["series", "shots"])
    )


def plot_s7a_arrows(df: pd.DataFrame, outdir: Path, subtitle: str = ""):
    """S7a: Improvement arrows — old → LuGo at each shared shot count."""
    stats = _build_efficiency_stats(df)
    series_list = sorted(stats["series"].unique())
    if len(series_list) < 2:
        return

    # Identify old vs LuGo
    old_label = [s for s in series_list if "lugo" not in s.lower()][0]
    lugo_label = [s for s in series_list if "lugo" in s.lower()][0]
    old_df = stats[stats["series"] == old_label].set_index("shots")
    lugo_df = stats[stats["series"] == lugo_label].set_index("shots")
    shared = sorted(set(old_df.index) & set(lugo_df.index))

    fig, ax = plt.subplots(figsize=(9, 6))

    # Plot both series as scatter
    for lbl, sdf, color, marker in [
        (old_label, old_df, COLOR_OLD, "s"),
        (lugo_label, lugo_df, COLOR_LUGO, "o"),
    ]:
        sub = sdf.loc[shared]
        ax.scatter(sub["wall_mean"], sub["l2_mean"], color=color,
                   marker=marker, s=60, zorder=5, label=lbl)
        for sc in shared:
            r = sdf.loc[sc]
            ax.annotate(
                f"{sc:,}", xy=(r["wall_mean"], r["l2_mean"]),
                xytext=(6, 6), textcoords="offset points",
                fontsize=7, color=color, fontweight="bold",
            )

    # Draw arrows from old to LuGo
    for sc in shared:
        o = old_df.loc[sc]
        l = lugo_df.loc[sc]
        ax.annotate(
            "", xy=(l["wall_mean"], l["l2_mean"]),
            xytext=(o["wall_mean"], o["l2_mean"]),
            arrowprops=dict(
                arrowstyle="->", color="0.4", lw=1.2,
                connectionstyle="arc3,rad=0.15",
            ),
        )
        # Speedup label at midpoint
        speedup = o["wall_mean"] / l["wall_mean"]
        mid_x = np.sqrt(o["wall_mean"] * l["wall_mean"])
        mid_y = np.sqrt(o["l2_mean"] * l["l2_mean"])
        ax.text(mid_x, mid_y, f"{speedup:.0f}×",
                fontsize=8, color="0.3", ha="center", va="bottom",
                fontweight="bold", bbox=dict(boxstyle="round,pad=0.2",
                fc="white", ec="0.7", alpha=0.8))

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Total Wall Time (s)")
    ax.set_ylabel("Final L2 Absolute Error")
    ax.set_title("Speedup: Old → LuGo at Each Shot Count", pad=16)
    if subtitle:
        ax.text(0.5, 1.0, subtitle, transform=ax.transAxes,
                ha="center", va="top", fontsize=9, color="0.4")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(outdir / "s7a_speedup_arrows.png", dpi=150)
    plt.close(fig)
    print(f"  Saved {outdir / 's7a_speedup_arrows.png'}")


def plot_s7b_dual_axis(df: pd.DataFrame, outdir: Path, subtitle: str = ""):
    """S7b: Dual-axis — L2 error (left) and wall time (right) vs shots."""
    stats = _build_efficiency_stats(df)

    fig, ax1 = plt.subplots(figsize=(10, 5))
    ax2 = ax1.twinx()

    for series in sorted(stats["series"].unique()):
        sub = stats[stats["series"] == series]
        color = COLOR_LUGO if "lugo" in series.lower() else COLOR_OLD

        # L2 error on left axis (solid line)
        ax1.plot(sub["shots"], sub["l2_mean"], "-o", color=color,
                 label=f"{series} — L2 error", markersize=5)
        # Wall time on right axis (dashed line)
        ax2.plot(sub["shots"], sub["wall_mean"], "--s", color=color,
                 label=f"{series} — wall time", markersize=5, alpha=0.7)

    ax1.set_xscale("log")
    ax1.set_yscale("log")
    ax2.set_yscale("log")
    ax1.set_xlabel("Shots")
    ax1.set_ylabel("Final L2 Absolute Error (solid)")
    ax2.set_ylabel("Total Wall Time, s (dashed)")
    ax1.set_title("Accuracy & Cost vs Shot Count", pad=16)
    if subtitle:
        ax1.text(0.5, 1.0, subtitle, transform=ax1.transAxes,
                 ha="center", va="top", fontsize=9, color="0.4")

    # Combined legend
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, fontsize=8, loc="upper right")
    ax1.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(outdir / "s7b_dual_axis.png", dpi=150)
    plt.close(fig)
    print(f"  Saved {outdir / 's7b_dual_axis.png'}")


def plot_s7c_summary_table(df: pd.DataFrame, outdir: Path, subtitle: str = ""):
    """S7c: Visual summary table — shot count × series with key metrics."""
    stats = _build_efficiency_stats(df)
    series_list = sorted(stats["series"].unique())
    shot_counts = sorted(stats["shots"].unique())

    fig, ax = plt.subplots(figsize=(12, max(3, len(shot_counts) * 0.6 + 1.5)))
    ax.axis("off")

    col_headers = []
    for s in series_list:
        col_headers.extend([f"{s}\nL2 error", f"{s}\nWall (s)"])
        if "lugo" in s.lower():
            col_headers.append(f"{s}\nSpeedup")

    cell_data = []
    cell_colors = []
    for sc in shot_counts:
        row = []
        row_colors = []
        vals = {}
        for s in series_list:
            sub = stats[(stats["series"] == s) & (stats["shots"] == sc)]
            if sub.empty:
                vals[s] = (None, None)
                row.extend(["—", "—"])
                row_colors.extend(["white"] * 2)
                if "lugo" in s.lower():
                    row.append("—")
                    row_colors.append("white")
            else:
                l2 = sub["l2_mean"].values[0]
                wall = sub["wall_mean"].values[0]
                vals[s] = (l2, wall)
                row.append(f"{l2:.2e}")
                row.append(f"{wall:,.0f}")
                row_colors.extend(["white"] * 2)
                if "lugo" in s.lower():
                    row.append("")  # placeholder for speedup
                    row_colors.append("white")

        # Fill in LuGo speedup column
        old_vals = [vals[s] for s in series_list if "lugo" not in s.lower()]
        lugo_vals = [vals[s] for s in series_list if "lugo" in s.lower()]
        if old_vals and lugo_vals:
            o_l2, o_wall = old_vals[0]
            l_l2, l_wall = lugo_vals[0]
            if o_wall and l_wall and l_wall > 0:
                speed = o_wall / l_wall
                # Speedup is always the last cell in the row
                row[-1] = f"{speed:.0f}×"
                if speed >= 10:
                    row_colors[-1] = "#d4edda"
                elif speed >= 2:
                    row_colors[-1] = "#fff3cd"

        cell_data.append(row)
        cell_colors.append(row_colors)

    row_labels = [f"{sc:,}" for sc in shot_counts]
    table = ax.table(
        cellText=cell_data,
        rowLabels=row_labels,
        colLabels=col_headers,
        cellColours=cell_colors,
        rowColours=["#f0f0f0"] * len(shot_counts),
        colColours=["#e0e0e0"] * len(col_headers),
        loc="center",
        cellLoc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1.0, 1.6)

    ax.set_title("Shot Scaling Summary: Accuracy, Cost & Speedup", pad=20,
                 fontsize=12, fontweight="bold")
    if subtitle:
        fig.text(0.5, 0.95, subtitle, ha="center", fontsize=9, color="0.4")

    fig.tight_layout()
    fig.savefig(outdir / "s7c_summary_table.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved {outdir / 's7c_summary_table.png'}")


# ---------------------------------------------------------------------------
# 5. Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Shot Scaling Study: nelem=5, old vs LuGo.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--old-base", type=Path,
        default=Path(__file__).resolve().parent.parent.parent
        / "results" / "fvm_euler_1d_solver" / "2025-11-11",
        help="Base directory for 2025-11-11 experiment (contains shots_* dirs)",
    )
    parser.add_argument(
        "--lugo-base", type=Path,
        default=Path(__file__).resolve().parent.parent.parent
        / "results" / "fvm_euler_1d_solver" / "2026-02-26-LuGo"
        / "nelem5" / "statevector",
        help="Base directory for LuGo nelem5 statevector (contains shots_* dirs)",
    )
    parser.add_argument(
        "--label-old", type=str, default="2025-11-11",
        help="Display label for old set",
    )
    parser.add_argument(
        "--label-lugo", type=str, default="2026-02-26-LuGo",
        help="Display label for LuGo set",
    )
    parser.add_argument(
        "--outdir", type=Path, default=Path("shot_scaling_output"),
        help="Output directory for plots",
    )
    args = parser.parse_args()

    old_base = args.old_base.resolve()
    lugo_base = args.lugo_base.resolve()
    outdir = args.outdir.resolve()
    outdir.mkdir(parents=True, exist_ok=True)

    # Discover shot counts
    old_shots = discover_shot_counts(old_base)
    lugo_shots = discover_shot_counts(lugo_base)
    print(f"Old  shots: {sorted(old_shots.keys())}")
    print(f"LuGo shots: {sorted(lugo_shots.keys())}")

    # Only keep shot counts that exist in both sets
    shared_shots = sorted(set(old_shots) & set(lugo_shots))
    old_shots = {k: old_shots[k] for k in shared_shots}
    lugo_shots = {k: lugo_shots[k] for k in shared_shots}
    print(f"Shared shots: {shared_shots}")

    # Build master DataFrames
    print("\nLoading trials...")
    df_old = build_master_df(old_shots, args.label_old)
    df_lugo = build_master_df(lugo_shots, args.label_lugo)
    df = pd.concat([df_old, df_lugo], ignore_index=True)

    # Drop trials with 0 iterations (failed/truncated runs)
    before = len(df)
    df = df[df["iters_to_converge"] > 0].reset_index(drop=True)
    dropped = before - len(df)
    if dropped:
        print(f"  Dropped {dropped} failed trial(s) with 0 iterations")

    n_old = len(df[df["series"] == args.label_old])
    n_lugo = len(df[df["series"] == args.label_lugo])
    print(f"  {n_old} old trials, {n_lugo} LuGo trials ({n_old + n_lugo} total)")

    # Subtitle
    subtitle = f"nelem=5, statevector, 10 trials per shot count"

    # Generate plots
    print(f"\nGenerating plots in {outdir}/")
    plot_s1_residual(df, outdir, subtitle=subtitle)
    plot_s2_fidelity(df, outdir, subtitle=subtitle)
    plot_s3_l2_error(df, outdir, subtitle=subtitle)
    plot_s4_iterations(df, outdir, subtitle=subtitle)
    plot_s5_circuit_cost(df, outdir, subtitle=subtitle)
    plot_s6_wall_time(df, outdir, subtitle=subtitle)
    plot_s7a_arrows(df, outdir, subtitle=subtitle)
    plot_s7b_dual_axis(df, outdir, subtitle=subtitle)
    plot_s7c_summary_table(df, outdir, subtitle=subtitle)

    # Save raw data
    csv_path = outdir / "shot_scaling_data.csv"
    df.to_csv(csv_path, index=False)
    print(f"\n  Saved {csv_path}")

    print(f"\nDone. {len(list(outdir.glob('*.png')))} plots + 1 CSV in {outdir}/")


if __name__ == "__main__":
    main()
