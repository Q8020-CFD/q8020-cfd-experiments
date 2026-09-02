#!/usr/bin/env python3
"""Emit a native .xlsx of the single-mode CH nu-domain cases.

Standalone table for the nu/Re sweep (bond 4/8/16 at every nu, scored vs
the adaptive shock-resolved FTCS truth).  Writes to its OWN file in the
analysis dir -- it never opens or modifies paper_cases_table.xlsx.

Columns mirror paper_cases_table.xlsx where they overlap (Method, q, nu,
A, cfl, steps, Re, Shots, Bond dim, Phi modes, In-segment k, Segments,
L2 rel vs FTCS, wall s, results/ dir) and add the reference provenance
(FTCS ref-points / grid / pts-per-shock) that this study turns on.

Reads the merged scores the same way score_nu_domain_single.py does, so
run it after the scorer.  Native .xlsx via the stdlib zip+XML path (no
openpyxl dependency, matches operator guidance for no-nag Excel files).

Run:
    q8020-cfd-ch-lbm/.venv/bin/python \\
        q8020-cfd-experiments/aux/burgers-ch-lbm/cases/xlsx_nu_domain_single.py
"""
from __future__ import annotations

import glob
import json
import os
import re
import zipfile
from xml.sax.saxutils import escape

import numpy as np

A_AMPLITUDE = 0.3
DEFAULT_ROOT = (
    "/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/results/"
    "burgers-ch-lbm/ch_q8_nu_domain_single"
)
DEFAULT_OUTDIR = (
    "/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/"
    "burgers-ch-lbm/ch-q8-nu-domain-single-analysis-2026-09-02"
)
OUT_NAME = "nu_domain_single_cases.xlsx"

COLS = [
    "Method", "q", "nu", "A", "cfl", "steps", "Re", "Shots", "Bond dim",
    "Phi modes", "In-segment k", "Segments", "L2 (rel vs FTCS)", "cos",
    "FTCS ref-points", "FTCS grid", "pts/shock (ref)", "wall s",
    "verdict", "results/ dir",
]


def one(p):
    try:
        d = json.load(open(p))
    except (OSError, ValueError):
        return {}
    return (d[0] if isinstance(d, list) else d) or {}


def field(r):
    for k in ("u_final_method", "u_final_classical"):
        v = r.get(k)
        if isinstance(v, list) and v:
            arr = np.asarray(v, float)
            if arr.size and np.all(np.isfinite(arr)):
                return arr
    return None


def ref_points_of(d):
    pa = one(os.path.join(d, "pipeline_args.json"))
    cmd = pa.get("cmd", "")
    cmd = " ".join(cmd) if isinstance(cmd, list) else str(cmd)
    m = re.search(r"--ref-points\s+(\d+)", cmd)
    return int(m.group(1)) if m else None


def collect(root):
    """Merged CH + truth records across all run dirs, newest wins."""
    ch, truth = {}, {}
    run_dirs = sorted(
        (d for d in glob.glob(os.path.join(root, "*", "_*"))
         if os.path.isdir(d)),
        key=os.path.getmtime,
    )
    for rd in run_dirs:
        for cpath in glob.glob(os.path.join(rd, "*", "q8020_case_0.json")):
            c = one(cpath)
            d = os.path.dirname(cpath)
            nu = None if c.get("nu") is None else round(float(c["nu"]), 6)
            rec = {
                "method": c.get("method"), "nu": nu, "q": c.get("q"),
                "cfl": c.get("cfl"), "steps": c.get("n_steps"),
                "shots": c.get("shots"), "bond": c.get("bond_dim"),
                "u": field(one(os.path.join(d, "q8020_results_0.json"))),
                "wall": one(os.path.join(d, "q8020_analysis_0.json"))
                .get("method_wall_time_s"),
                "ref_points": ref_points_of(d),
                "dir": d,
            }
            if c.get("method") == "ftcs_reference":
                truth[nu] = rec
            elif c.get("method") == "cole_hopf_circuit":
                ch[(nu, c.get("bond_dim"))] = rec
    return ch, truth


def rel_l2(u, r):
    n = min(u.size, r.size)
    return float(np.linalg.norm(u[:n] - r[:n]) / np.linalg.norm(r[:n]))


def cosine(u, r):
    n = min(u.size, r.size)
    d = np.linalg.norm(u[:n]) * np.linalg.norm(r[:n])
    return float(np.dot(u[:n], r[:n]) / d) if d else float("nan")


def build_rows(root):
    ch, truth = collect(root)
    rows = []
    for (nu, bond), c in sorted(ch.items(), key=lambda kv: (kv[0][1] or 0,
                                                             -(kv[0][0] or 0))):
        re_val = A_AMPLITUDE / nu if nu else float("nan")
        t = truth.get(nu)
        rp = t.get("ref_points") if t else None
        grid = (256 * int(np.ceil(rp / 256))) if rp else None
        pshock = ((nu / A_AMPLITUDE) * grid) if (grid and nu) else None
        if c["u"] is not None and t and t["u"] is not None:
            r = rel_l2(c["u"], t["u"])
            cos = cosine(c["u"], t["u"])
            verdict = "diverged" if r > 1 else ("good" if r < 0.5
                                                else "marginal")
        else:
            r = cos = None
            verdict = "CH_nonfinite" if c["u"] is None else "no_truth"
        rel = os.path.relpath(
            c["dir"],
            "/Users/agallojr/proj/src/q8020/q8020-cfd-experiments",
        )
        rows.append([
            "CH", c["q"], nu, A_AMPLITUDE, c["cfl"], c["steps"],
            round(re_val, 1), c["shots"], bond, 8, c["steps"], 1,
            None if r is None else round(r, 6),
            None if cos is None else round(cos, 4),
            rp, grid, None if pshock is None else round(pshock, 1),
            None if c["wall"] is None else round(c["wall"], 1),
            verdict, rel,
        ])
    return rows


# ---- minimal .xlsx writer (stdlib zip + inline-string XML) -----------
def _cell(col, row, val):
    ref = f"{chr(65 + col) if col < 26 else 'A' + chr(65 + col - 26)}{row}"
    if val is None:
        return f'<c r="{ref}"/>'
    if isinstance(val, bool):
        val = str(val)
    if isinstance(val, (int, float)):
        return f'<c r="{ref}"><v>{val}</v></c>'
    return f'<c r="{ref}" t="inlineStr"><is><t xml:space="preserve">' \
           f'{escape(str(val))}</t></is></c>'


def write_xlsx(path, header, rows, sheet="nu-domain cases"):
    xml_rows = []
    xml_rows.append("<row r=\"1\">"
                    + "".join(_cell(c, 1, h) for c, h in enumerate(header))
                    + "</row>")
    for ri, row in enumerate(rows, start=2):
        xml_rows.append(f'<row r="{ri}">'
                        + "".join(_cell(c, ri, v) for c, v in enumerate(row))
                        + "</row>")
    sheet_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/'
        'spreadsheetml/2006/main"><sheetData>'
        + "".join(xml_rows) + "</sheetData></worksheet>"
    )
    wb_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/'
        'spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats'
        '.org/officeDocument/2006/relationships"><sheets>'
        f'<sheet name="{escape(sheet)}" sheetId="1" r:id="rId1"/>'
        "</sheets></workbook>"
    )
    wb_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/'
        'package/2006/relationships"><Relationship Id="rId1" Type='
        '"http://schemas.openxmlformats.org/officeDocument/2006/'
        'relationships/worksheet" Target="worksheets/sheet1.xml"/>'
        "</Relationships>"
    )
    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/'
        'content-types"><Default Extension="rels" ContentType='
        '"application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" ContentType="application/'
        'vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        '<Override PartName="/xl/worksheets/sheet1.xml" ContentType='
        '"application/vnd.openxmlformats-officedocument.spreadsheetml.'
        'worksheet+xml"/></Types>'
    )
    root_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/'
        '2006/relationships"><Relationship Id="rId1" Type="http://schemas'
        '.openxmlformats.org/officeDocument/2006/relationships/'
        'officeDocument" Target="xl/workbook.xml"/></Relationships>'
    )
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", content_types)
        z.writestr("_rels/.rels", root_rels)
        z.writestr("xl/workbook.xml", wb_xml)
        z.writestr("xl/_rels/workbook.xml.rels", wb_rels)
        z.writestr("xl/worksheets/sheet1.xml", sheet_xml)


def main():
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=DEFAULT_ROOT)
    ap.add_argument("--outdir", default=DEFAULT_OUTDIR)
    args = ap.parse_args()

    rows = build_rows(args.root)
    os.makedirs(args.outdir, exist_ok=True)
    out = os.path.join(args.outdir, OUT_NAME)
    write_xlsx(out, COLS, rows)
    print(f"wrote {out}  ({len(rows)} case rows)")


if __name__ == "__main__":
    main()
