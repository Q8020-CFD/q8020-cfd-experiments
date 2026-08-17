"""SQLS vs HHL comparison for the FVM 1D Euler nozzle (nelem 5, BDF1,
localdt, ideal statevector, shots 150000, cfl 1e10). Same case, same
qiskit-2.5.2 stack; only the linear solver differs.

Reads both runs' metric/metadata CSVs and emits:
  - sqls_fidelity_collapse.png : SQLS per-iter fidelity (tail collapse).
  - sqls_vs_hhl_compare.png    : circuit width / runtime / fidelity.
Prints a text comparison table.
"""

import os

import numpy as np
import matplotlib.pyplot as plt

# ---- validated dataviz palette (light surface) ----------------------
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
BASE = "#c3c2b7"
SERIES_SQLS = "#2a78d6"   # slot 1 blue
SERIES_HHL = "#eb6834"    # slot 6 orange
CRITICAL = "#d03b3b"      # status critical (collapse marker)

RES = ("/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/results/"
       "fvm_euler_1d_solver")
# v2 run: same case, -v 2, so SQLS's diagnostic {u3,cx} transpile ran and
# cx_count / circuit_depth are populated (the non-v2 run logged -1 there).
SQLS_DIR = f"{RES}/2026-08-17-sqls-local-v2/trial_0"
HHL_DIR = f"{RES}/2026-08-17-qiskit25-local/trial_0"
OUT = os.path.dirname(os.path.abspath(__file__))


def _read_csv(path):
    """Return dict[column_name] -> np.ndarray. Headers are ', '-separated."""
    with open(path) as fh:
        header = [c.strip() for c in fh.readline().split(",")]
    data = np.genfromtxt(path, delimiter=",", skip_header=1)
    if data.ndim == 1:
        data = data.reshape(1, -1)
    return {name: data[:, i] for i, name in enumerate(header)}


def _style(ax):
    ax.set_facecolor(SURFACE)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(BASE)
    ax.tick_params(colors=MUTED, labelsize=9)
    ax.grid(True, color=GRID, linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)


# --------------------------------------------------------------------- #
# load
# --------------------------------------------------------------------- #
sqls_m = _read_csv(f"{SQLS_DIR}/hhl_metrics_nelem5_statevector_shots150000.csv")
sqls_qc = _read_csv(f"{SQLS_DIR}/qc_metadata_sqls_nelem5_full_svd_shots150000.csv")
hhl_m = _read_csv(f"{HHL_DIR}/hhl_metrics_nelem5_statevector_shots150000.csv")
hhl_qc = _read_csv(f"{HHL_DIR}/qc_metadata_nelem5_statevector_shots150000.csv")


def _meta(dir_, pattern):
    """Load the run's metadata pkl for whole-run scalars (elapsed etc.)."""
    import glob
    import pickle
    hits = glob.glob(f"{dir_}/{pattern}")
    return pickle.load(open(hits[0], "rb")) if hits else {}


sqls_meta = _meta(SQLS_DIR, "metadata_*SQLS*.pkl")
hhl_meta = _meta(HHL_DIR, "metadata_*HHL*.pkl")
sqls_repeats = int(sqls_qc["repeats"][0]) if "repeats" in sqls_qc else 1

# --------------------------------------------------------------------- #
# Plot 1 -- SQLS fidelity collapse at the converged tail
# --------------------------------------------------------------------- #
fig, ax = plt.subplots(figsize=(7.2, 4.2), dpi=140)
fig.patch.set_facecolor(SURFACE)
_style(ax)

# the metrics file uses 'step' as the row index here (initers=1 -> one per step)
fid = sqls_m["fidelity"]
xk = np.arange(len(fid))

ax.plot(xk, fid, color=SERIES_SQLS, linewidth=2, marker="o",
        markersize=6, markerfacecolor=SERIES_SQLS,
        markeredgecolor=SURFACE, markeredgewidth=1.5, zorder=3,
        label="SQLS full_svd")
# mark the collapse point
j = int(np.argmin(fid))
ax.scatter([xk[j]], [fid[j]], s=140, facecolor=CRITICAL,
           edgecolor=SURFACE, linewidth=1.8, zorder=4)
ax.annotate(f"tail collapse\nfidelity {fid[j]:.3f}",
            xy=(xk[j], fid[j]), xytext=(xk[j] - 1.7, fid[j] + 0.16),
            color=CRITICAL, fontsize=9, ha="left", va="bottom",
            arrowprops=dict(arrowstyle="->", color=CRITICAL, linewidth=1.4))

ax.set_xlabel("Newton iteration (outer step)", color=INK2, fontsize=10)
ax.set_ylabel("state fidelity  |⟨sqls | LU⟩|²", color=INK2, fontsize=10)
ax.set_title("SQLS solution fidelity per iteration — collapse at convergence",
             color=INK, fontsize=12, pad=10, loc="left")
ax.set_ylim(0.45, 1.03)
ax.set_xticks(xk)
fig.tight_layout()
p1 = f"{OUT}/sqls_fidelity_collapse.png"
fig.savefig(p1, facecolor=SURFACE)
print("wrote", p1)

# --------------------------------------------------------------------- #
# Plot 2 -- SQLS vs HHL: qubit width, per-iter runtime, fidelity
# small multiples (one axis each; never dual-axis)
# --------------------------------------------------------------------- #
fig, axes = plt.subplots(1, 4, figsize=(16.4, 4.3), dpi=140)
fig.patch.set_facecolor(SURFACE)

# HHL total per-iter time = generate + transpile + run
hhl_time = (hhl_qc["circ_generate_time"] + hhl_qc["circ_transpile_time"]
            + hhl_qc["circ_run_time"])
sqls_time = sqls_qc["solve_time"]

hhl_q = hhl_qc["circ_qubits_transpile"]
sqls_q = sqls_qc["n_data_qubits"]

# (a) circuit width -- bar
ax = axes[0]
_style(ax)
bars = ax.bar([0, 1], [sqls_q.max(), hhl_q.max()], width=0.55,
              color=[SERIES_SQLS, SERIES_HHL], zorder=3)
ax.set_xticks([0, 1])
ax.set_xticklabels(["SQLS", "HHL"], color=INK2, fontsize=10)
ax.set_ylabel("qubits (circuit width)", color=INK2, fontsize=10)
ax.set_title("Circuit width", color=INK, fontsize=12, loc="left", pad=8)
for x, v in zip([0, 1], [sqls_q.max(), hhl_q.max()]):
    ax.text(x, v + 0.3, str(int(v)), ha="center", va="bottom",
            color=INK, fontsize=11, fontweight="bold")
ax.set_ylim(0, 16)

# (b) per-iter runtime -- log scale bar (170x gap)
ax = axes[1]
_style(ax)
ax.bar([0, 1], [sqls_time.mean(), hhl_time.mean()], width=0.55,
       color=[SERIES_SQLS, SERIES_HHL], zorder=3)
ax.set_yscale("log")
ax.set_xticks([0, 1])
ax.set_xticklabels(["SQLS", "HHL"], color=INK2, fontsize=10)
ax.set_ylabel("mean time / linear solve (s, log)", color=INK2, fontsize=10)
ax.set_title("Runtime per solve", color=INK, fontsize=12, loc="left", pad=8)
for x, v in zip([0, 1], [sqls_time.mean(), hhl_time.mean()]):
    ax.text(x, v * 1.15, f"{v:.2f}s", ha="center", va="bottom",
            color=INK, fontsize=11, fontweight="bold")

# (c) two-qubit-gate cost -- log bar. Basis differs (see note): SQLS is
# {u3,cx} CX count; HHL is total gates in Aer's basis. Least-unfair axis.
ax = axes[2]
_style(ax)
sqls_cx = float(np.median(sqls_qc["cx_count"]))
hhl_gates = float(hhl_qc["circ_gates_transpile"][0])
ax.bar([0, 1], [sqls_cx, hhl_gates], width=0.55,
       color=[SERIES_SQLS, SERIES_HHL], zorder=3)
ax.set_yscale("log")
ax.set_xticks([0, 1])
ax.set_xticklabels(["SQLS\n(CX, {u3,cx})", "HHL\n(gates, Aer)"],
                   color=INK2, fontsize=9)
ax.set_ylabel("two-qubit / total gate count (log)", color=INK2, fontsize=10)
ax.set_title("Circuit gate cost", color=INK, fontsize=12, loc="left", pad=8)
for x, v in zip([0, 1], [sqls_cx, hhl_gates]):
    ax.text(x, v * 1.25, f"{int(v):,}", ha="center", va="bottom",
            color=INK, fontsize=10.5, fontweight="bold")
ax.set_ylim(top=hhl_gates * 6)

# (d) fidelity per iter -- both series, direct-labeled
ax = axes[3]
_style(ax)
fid_s = sqls_m["fidelity"]
fid_h = hhl_m["fidelity"]
xs = np.arange(len(fid_s))
xh = np.arange(len(fid_h))
ax.plot(xh, fid_h, color=SERIES_HHL, linewidth=2, marker="s",
        markersize=4, markeredgecolor=SURFACE, markeredgewidth=1, zorder=3)
ax.plot(xs, fid_s, color=SERIES_SQLS, linewidth=2, marker="o",
        markersize=4, markeredgecolor=SURFACE, markeredgewidth=1, zorder=3)
ax.text(len(fid_h) - 1, fid_h[-1] - 0.02, "HHL",
        color=SERIES_HHL, fontsize=10, ha="right", va="top",
        fontweight="bold")
jj = int(np.argmin(fid_s))
ax.text(xs[jj], fid_s[jj] - 0.02, "SQLS",
        color=SERIES_SQLS, fontsize=10, ha="center", va="top",
        fontweight="bold")
ax.set_xlabel("Newton iteration", color=INK2, fontsize=10)
ax.set_ylabel("state fidelity", color=INK2, fontsize=10)
ax.set_title("Solution fidelity", color=INK, fontsize=12, loc="left", pad=8)
ax.set_ylim(0.45, 1.03)

fig.suptitle("SQLS vs HHL — FVM 1D Euler nozzle, nelem 5, ideal statevector, "
             "150k shots, cfl 1e10", color=INK, fontsize=12.5, x=0.01,
             ha="left")
fig.tight_layout(rect=[0, 0, 1, 0.96])
p2 = f"{OUT}/sqls_vs_hhl_compare.png"
fig.savefig(p2, facecolor=SURFACE)
print("wrote", p2)

# --------------------------------------------------------------------- #
# text comparison table
# --------------------------------------------------------------------- #
def _fmt(x, u=""):
    return f"{x}{u}"

rows = [
    ("linear solver", "SQLS (full_svd)", "HHL"),
    ("circuit qubits (max)", int(sqls_q.max()), int(hhl_q.max())),
    ("data register qubits", int(sqls_qc['n_data_qubits'].max()),
     "5 (nqubits) / 14 w/ herm+QPE"),
    ("CX count [basis differs, see note]",
     f"{int(np.median(sqls_qc['cx_count']))}  ({{u3,cx}})",
     f"{int(hhl_qc['circ_gates_transpile'][0])} total gates  (Aer basis)"),
    ("circuit depth [basis differs]",
     f"{int(np.median(sqls_qc['circuit_depth']))}  ({{u3,cx}})",
     f"{int(hhl_qc['circ_depth_transpile'][0])}  (Aer basis)"),
    (f"SQLS shot repeats (×nshots)", sqls_repeats, "1 (single run)"),
    ("mean time / solve (s)", f"{sqls_time.mean():.3f}",
     f"{hhl_time.mean():.2f}"),
    ("total solver elapsed (s)",
     f"{sqls_meta.get('elapsed_time', float('nan')):.3f}",
     f"{hhl_meta.get('elapsed_time', float('nan')):.2f}"),
    ("Newton iters to converge",
     int(sqls_meta.get("final_iters", len(sqls_m["fidelity"]) - 1)),
     int(hhl_meta.get("final_iters", len(hhl_m["fidelity"]) - 1))),
    ("final residual (‖Ax-b‖ path)",
     f"{sqls_meta.get('final_residual', float('nan')):.2e}",
     f"{hhl_meta.get('final_residual', float('nan')):.2e}"),
    ("fidelity, iters 0..n-1 (pre-tail)",
     f"{fid_s[:-1].min():.5f}..{fid_s[:-1].max():.5f}",
     f"{fid_h.min():.4f}..{fid_h.max():.4f}"),
    ("fidelity, final iter (tail)",
     f"{fid_s[-1]:.4f}  (collapse)",
     f"{fid_h[-1]:.4f}"),
]

w = max(len(r[0]) for r in rows) + 2
print("\n" + "=" * 92)
print("SQLS vs HHL  |  FVM 1D Euler nozzle, nelem 5, ideal statevector, "
      "150k shots, cfl 1e10")
print("=" * 92)
for label, a, b in rows:
    print(f"{label:<{w}} {str(a):<26} {str(b)}")
print("=" * 92)
print("NOTE on circuit cost: SQLS numbers are a {u3,cx} synthesis "
      "(sqls count_cx diagnostic).")
print("     HHL numbers are transpile(circ, AerSimulator) in Aer's own "
      "basis, NOT {u3,cx}.")
print("     Depths are therefore not like-for-like; CX vs total-gates is "
      "the least-unfair axis")
print("     and still shows ~3 orders of magnitude. A true apples-to-apples "
      "needs both circuits")
print("     re-synthesized to {u3,cx}; HHL's ~1.5 GB .qpy circuits were not "
      "copied to results,")
print("     so that re-synthesis is not possible from this run's artifacts.")
