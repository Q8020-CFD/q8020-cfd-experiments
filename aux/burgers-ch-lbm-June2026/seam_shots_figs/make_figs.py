#!/usr/bin/env python3
"""
Seam (in-segment-k) sweep and shots sweep figures for the Re=10 CH case.

Source: ../paper_cases_table.xlsx, sheet 'Paper cases', rows 31-44 (post-paper
C0/C1/C2 studies). All rows share q=8, nu=0.03, A=0.3, cfl=0.1, steps=512,
bond dim=4, phi modes=8; they vary only in-segment k / segments and shots.

Two figures, each pairing accuracy (L2 rel vs FTCS-800, col S) with circuit
cost (total width = q actual col T; avg depth col U):
  fig_seam_k_sweep  : C1 k=2,4,8,16 at shots=131072 (+ C0 k=512 endpoint,
                      + statevector floor reference).
  fig_shots_sweep   : C2 shots-ladder at k=8; circuit is fixed, so cost lines
                      are flat -- the point being shots buy accuracy at no
                      extra circuit width/depth.
"""

import zipfile
import re
from xml.etree import ElementTree as ET

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

HERE = "/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/burgers-ch-lbm-June2026"
XLSX = f"{HERE}/paper_cases_table.xlsx"
OUT = f"{HERE}/seam_shots_figs"

M_NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"


def load_sheet(path: str) -> dict:
    """Return {row_number: {col_letter: value}} for the single sheet.

    Handles both string encodings: a shared-strings table (how Excel and the
    original file store text) and inline strings (how openpyxl re-saves after
    a programmatic edit). sharedStrings.xml is absent in the inline case.
    """
    ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    z = zipfile.ZipFile(path)
    strings = []
    if "xl/sharedStrings.xml" in z.namelist():
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
            ctype = c.attrib.get("t")
            if ctype == "inlineStr":
                is_el = c.find("m:is", ns)
                if is_el is None:
                    continue
                cells[col] = "".join(t.text or "" for t in is_el.iter(f"{M_NS}t"))
                continue
            v = c.find("m:v", ns)
            if v is None:
                continue
            cells[col] = strings[int(v.text)] if ctype == "s" else v.text
        rows[rnum] = cells
    return rows


def _clean(v):
    if v in (None, "n/a", "None"):
        return None
    return float(v)


rows = load_sheet(XLSX)
# Index by the stable case id in column A (NOT the spreadsheet row number,
# which shifts when rows are inserted). Case ids are strings, e.g. "26a".
by_case = {c["A"]: c for c in rows.values() if c.get("A") is not None}


def val(case_id, col):
    """Numeric cell value for a case id (column A), or None."""
    return _clean(by_case[case_id].get(col))


# --- families (referenced by column-A case id) ---
# C1 seam study: fixed shots=131072, vary in-segment k (segments = 512 / k).
c1_ids = ["28", "29", "30", "31"]   # k = 2, 4, 8, 16
seam_k = np.array([val(c, "N") for c in c1_ids])
seam_l2 = np.array([val(c, "S") for c in c1_ids])
seam_w = np.array([val(c, "T") for c in c1_ids])
seam_d = np.array([val(c, "U") for c in c1_ids])
seam_seg = np.array([val(c, "O") for c in c1_ids])
seam_shots = int(val("28", "K"))    # 131072, fixed across the C1 sweep
seam_q = int(val("28", "E"))        # q=8, fixed across the C1 sweep

# C0 single-segment endpoint (case 27, k=512, shots=131072) and the
# statevector floor (case 26, shots=0, noise-free).
c0_k = val("27", "N")               # 512
c0_seg = val("27", "O")             # 1 (single segment)
c0_l2 = val("27", "S")              # shots=131072
c0_w = val("27", "T")
c0_d = val("27", "U")
sv_floor = val("26b", "S")          # C0 shots=0, noise-free statevector
sv_seg = int(val("26b", "O"))       # S=1 (single segment)
sv_k = int(val("26b", "N"))         # k=512  (26b: optimized-code rerun)

# C2 shots ladder (cases 32-36): fixed k=8 (segments=64), vary shots.
c2_ids = ["32", "33", "34", "35", "36"]
shot_n = np.array([val(c, "K") for c in c2_ids])
shot_l2 = np.array([val(c, "S") for c in c2_ids])
shot_w = val("32", "T")             # constant across the ladder
shot_d = val("32", "U")

# --- shared style ---
plt.rcParams.update({
    "font.size": 10,
    "axes.grid": True,
    "grid.alpha": 0.3,
    "axes.axisbelow": True,
    "figure.dpi": 150,
})
C_L2 = "#0072B2"     # blue  -> accuracy
C_DEPTH = "#D55E00"  # orange-> circuit depth
C_WIDTH = "#009E73"  # green -> circuit width
C_REF = "#888888"


def style_l2_axis(ax):
    ax.set_yscale("log")
    ax.set_ylabel("L2 (rel vs FTCS)", color=C_L2)
    ax.tick_params(axis="y", colors=C_L2)


# =====================================================================
# Figure 1: seam / in-segment-k sweep
# =====================================================================
fig, axa = plt.subplots(1, 1, figsize=(7.2, 4.6))

# accuracy vs segment count -- one connected series (k=512 is 1 segment).
# circuit depth (col U) is folded into each point's label as d=#, so the
# separate cost panel is no longer needed.
all_seg = np.append(seam_seg, c0_seg)
all_l2 = np.append(seam_l2, c0_l2)
all_k = np.append(seam_k, c0_k)
all_d = np.append(seam_d, c0_d)
order = np.argsort(all_seg)
all_seg, all_l2, all_k, all_d = (all_seg[order], all_l2[order],
                                 all_k[order], all_d[order])
axa.plot(all_seg, all_l2, "o-", color=C_L2, lw=2, ms=7)
axa.axhline(sv_floor, color=C_REF, ls="--", lw=1.2)
axa.text(0.01, sv_floor,
         f" statevector floor (no shot noise, L2={sv_floor:.1e}; "
         f"S={sv_seg}, k={sv_k})",
         color=C_REF, va="bottom", ha="left", fontsize=8,
         transform=axa.get_yaxis_transform())
style_l2_axis(axa)
shots_exp = int(round(np.log2(seam_shots)))   # 131072 = 2^17
axa.set_title(
    rf"Cole-Hopf $\phi$, evolution error over k-step segments"
    rf"  (q={seam_q}, shots=$2^{{{shots_exp}}}$, Re=10)", pad=10)
axa.set_xscale("log", base=2)
axa.xaxis.set_major_formatter(mticker.ScalarFormatter())
axa.set_xticks(list(all_seg))
axa.set_xlabel("segments (S)")
# label each point with its in-segment k (= 512 / S)
for seg, l2, k in zip(all_seg, all_l2, all_k):
    axa.annotate(f"k={int(k)}", (seg, l2), textcoords="offset points",
                 xytext=(6, 8), fontsize=7, color=C_L2)

# right y-axis: segment circuit depth (col U) vs segments. The single-segment
# point (S=1) is a different, non-segmented build but is connected into the
# series for continuity (per request).
axd = axa.twinx()
axd.plot(all_seg, all_d, "s--", color=C_DEPTH, lw=1.6, ms=5, alpha=0.9,
         label="segment depth")
axd.set_yscale("log")
axd.set_ylabel("segment circuit depth", color=C_DEPTH)
axd.tick_params(axis="y", colors=C_DEPTH)
# depth spans only ~1 decade, so a plain decade locator gives one label.
# Place explicit round ticks across the range, labelled compactly (k = 1e3).
depth_ticks = [2e4, 3e4, 5e4, 1e5, 2e5]
axd.yaxis.set_major_locator(mticker.FixedLocator(depth_ticks))
axd.yaxis.set_minor_locator(mticker.NullLocator())
axd.yaxis.set_major_formatter(
    mticker.FuncFormatter(lambda x, _: f"{x / 1e3:g}k"))
axd.grid(False)

fig.tight_layout()
fig.savefig(f"{OUT}/fig_seam_k_sweep.png", bbox_inches="tight")
print("wrote fig_seam_k_sweep.png")

# =====================================================================
# Figure 2: shots sweep (k=8 fixed)
# =====================================================================
fig, (axa, axb) = plt.subplots(2, 1, figsize=(7.2, 6.4), sharex=True,
                               gridspec_kw={"height_ratios": [1.1, 1]})

axa.plot(shot_n, shot_l2, "o-", color=C_L2, lw=2, ms=7, label="C2 shots ladder (k=8)")
style_l2_axis(axa)
axa.set_title("Re=10 CH — shots sweep  (k=8, 64 segments; circuit fixed)")
axa.legend(fontsize=8, loc="upper right")

# bottom: circuit cost is CONSTANT -> flat lines make the point explicit
axb.axhline(shot_d, color=C_DEPTH, lw=2, label=f"avg depth = {int(shot_d):,} (fixed)")
axb.set_yscale("log")
axb.set_ylabel("avg circuit depth", color=C_DEPTH)
axb.tick_params(axis="y", colors=C_DEPTH)
axb.set_ylim(shot_d / 3, shot_d * 3)
axb.set_xlabel("shots per circuit")
axb.set_xscale("log", base=2)
axb.xaxis.set_major_formatter(mticker.ScalarFormatter())
axb.set_xticks(shot_n)
axb.ticklabel_format(axis="x", style="plain")

axb2 = axb.twinx()
axb2.axhline(shot_w, color=C_WIDTH, lw=2, label=f"total width = {int(shot_w)} qubits (fixed)")
axb2.set_ylabel("total width (qubits)", color=C_WIDTH)
axb2.tick_params(axis="y", colors=C_WIDTH)
axb2.set_ylim(shot_w - 6, shot_w + 6)
axb2.grid(False)
h1, l1 = axb.get_legend_handles_labels()
h2, l2 = axb2.get_legend_handles_labels()
axb.legend(h1 + h2, l1 + l2, fontsize=8, loc="center right")

fig.tight_layout()
fig.savefig(f"{OUT}/fig_shots_sweep.png", bbox_inches="tight")
print("wrote fig_shots_sweep.png")
