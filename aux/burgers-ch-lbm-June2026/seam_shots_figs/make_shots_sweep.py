#!/usr/bin/env python3
"""
Shots sweep figure for the Re=10 CH case, in the fig_seam_k_sweep single-panel
style (blue L2 on a log axis + orange circuit-depth twin axis + statevector
floor reference).

Standalone / self-contained on purpose: it does NOT import make_figs.py so it
can be edited independently while another agent works that file.

Source: ../paper_cases_table.xlsx, sheet 'Paper cases'. Cases are keyed by the
column-A case id (# col), NOT by spreadsheet row number -- rows may be inserted
or reordered, but a case keeps its id.
  C2 shots ladder : case ids 32-36, fixed in-segment k=8 (64 segments), shots
                    vary 16384 -> 1048576. The circuit is identical across the
                    ladder, so cost (width col T, depth col U) is constant --
                    the point being shots buy accuracy at no extra circuit
                    width or depth.
  statevector floor: case id 26 (C0 shots=0, noise-free) as the algorithm floor.
All cases share q=8, nu=0.03, A=0.3, cfl=0.1, steps=512, bond dim=4, phi modes=8.
"""

import zipfile
import re
from xml.etree import ElementTree as ET

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

HERE = "/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/burgers-ch-lbm-June2026"
XLSX = f"{HERE}/paper_cases_table.xlsx"
OUT = f"{HERE}/seam_shots_figs"

M_NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"


def load_sheet(path: str) -> dict:
    """Return {row_number: {col_letter: value}} for the single sheet."""
    ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    z = zipfile.ZipFile(path)
    strings = []
    root = ET.fromstring(z.read("xl/sharedStrings.xml"))
    for si in root.findall("m:si", ns):
        strings.append("".join(t.text or "" for t in si.iter(f"{M_NS}t")))
    sheet = ET.fromstring(z.read("xl/worksheets/sheet1.xml"))
    rows: dict = {}
    for row in sheet.findall(".//m:sheetData/m:row", ns):
        rnum = int(row.attrib["r"])
        cells: dict = {}
        for c in row.findall("m:c", ns):
            col = re.match(r"([A-Z]+)", c.attrib["r"]).group(1)
            v = c.find("m:v", ns)
            if v is None:
                continue
            cells[col] = strings[int(v.text)] if c.attrib.get("t") == "s" else v.text
        rows[rnum] = cells
    return rows


def index_by_case_id(rows: dict) -> dict:
    """Map column-A case id (str) -> that row's {col: value} cells.

    Keying on the case id (# col) rather than the spreadsheet row number keeps
    the figure stable if rows are inserted or reordered. Header/section rows
    (blank A, or a non-integer A) are skipped.
    """
    by_id: dict = {}
    for cells in rows.values():
        cid = cells.get("A")
        if cid is None:
            continue
        cid = str(cid).strip()
        if not cid.isdigit():
            continue
        by_id[cid] = cells
    return by_id


def num(cells, col):
    v = cells.get(col)
    if v in (None, "n/a", "None"):
        return None
    return float(v)


cases = index_by_case_id(load_sheet(XLSX))

# C2 shots ladder: fixed k=8 (64 segments), vary shots. Keyed by case id (col A);
# shots read from col K so the id list alone drives the ladder.
c2_ids = ["32", "33", "34", "35", "36"]
c2 = [cases[i] for i in c2_ids]
shot_n = np.array([num(c, "K") for c in c2])                  # shots per circuit
order = np.argsort(shot_n)
shot_n = shot_n[order]
shot_l2 = np.array([num(c, "S") for c in c2])[order]
shot_w = num(c2[0], "T")             # 18 qubits, constant across the ladder
shot_d = num(c2[0], "U")             # 124624 depth, constant across the ladder
shot_k = int(num(c2[0], "N"))        # 8
shot_seg = int(num(c2[0], "O"))      # 64
shot_q = int(num(c2[0], "E"))        # 8

# statevector floor (case id 26): C0 shots=0, noise-free -- the algorithm floor.
sv = cases["26"]
sv_floor = num(sv, "S")              # 1.69e-4
sv_seg = int(num(sv, "O"))           # 1
sv_k = int(num(sv, "N"))             # 512

# --- shared style (mirrors fig_seam_k_sweep) ---
plt.rcParams.update({
    "font.size": 10,
    "axes.grid": True,
    "grid.alpha": 0.3,
    "axes.axisbelow": True,
    "figure.dpi": 150,
})
C_L2 = "#0072B2"     # blue  -> accuracy
C_DEPTH = "#D55E00"  # orange-> circuit depth
C_REF = "#888888"


def style_l2_axis(ax):
    ax.set_yscale("log")
    ax.set_ylabel("L2 (rel vs FTCS)", color=C_L2)
    ax.tick_params(axis="y", colors=C_L2)


# =====================================================================
# Shots sweep, single-panel seam-style
# =====================================================================
fig, axa = plt.subplots(1, 1, figsize=(7.2, 4.6))

# accuracy vs shots -- one connected series; more shots -> lower L2.
axa.plot(shot_n, shot_l2, "o-", color=C_L2, lw=2, ms=7)
axa.axhline(sv_floor, color=C_REF, ls="--", lw=1.2)
axa.text(0.01, sv_floor,
         f" statevector floor (no shot noise, L2={sv_floor:.1e}; "
         f"S={sv_seg}, k={sv_k})",
         color=C_REF, va="bottom", ha="left", fontsize=8,
         transform=axa.get_yaxis_transform())
style_l2_axis(axa)
axa.set_title(
    rf"Cole-Hopf $\phi$, shot-noise error at a fixed circuit"
    rf"  (q={shot_q}, k={shot_k}, S={shot_seg}, Re=10)", pad=10)
axa.set_xscale("log", base=2)
axa.xaxis.set_major_formatter(mticker.ScalarFormatter())
axa.set_xticks(list(shot_n))
axa.ticklabel_format(axis="x", style="plain")
axa.set_xlabel("shots per circuit")
# label each point with its shot count (2^exp)
for s, l2 in zip(shot_n, shot_l2):
    axa.annotate(rf"$2^{{{int(round(np.log2(s)))}}}$", (s, l2),
                 textcoords="offset points", xytext=(6, 8),
                 fontsize=7, color=C_L2)

# right y-axis: circuit depth (col U) is CONSTANT across the ladder -- a flat
# line makes explicit that shots buy accuracy at no extra circuit cost.
axd = axa.twinx()
axd.axhline(shot_d, color=C_DEPTH, ls="--", lw=1.6, alpha=0.9,
            label=f"segment depth = {int(shot_d):,} (fixed); "
                  f"width = {int(shot_w)} qubits")
axd.set_yscale("log")
axd.set_ylabel("segment circuit depth", color=C_DEPTH)
axd.tick_params(axis="y", colors=C_DEPTH)
axd.set_ylim(shot_d / 3, shot_d * 3)
axd.grid(False)
axd.legend(fontsize=8, loc="upper right")

fig.tight_layout()
fig.savefig(f"{OUT}/fig_shots_sweep_seamstyle.png", bbox_inches="tight")
print("wrote fig_shots_sweep_seamstyle.png")
