# Cole-Hopf domain of utility vs Re — S=1, k=512 (q=8, A=0.3, shots=0)

**Date:** 2026-09-02 (UTC). **Code:** q8020-cfd-ch-lbm HEAD `ff32441`
(post commit `557b27a`, 2026-08-27, the QFT-layer collapse). All results
computed fresh with this code — no reuse of the earlier `ch_q8_nu_domain`
sweep (2026-08-25), which predates the collapse and used seams + bond-16
+ shots.

## What was run

Fixed operating point: q=8 (N=256, periodic), IC = 0.3·sin(2πx), source
none, CFL=0.1, n-steps=512 → T_end = 512·0.1/256 = **0.200 exactly**
(≈ 38% of the A=0.3 shock time t_shock = 1/(2πA) ≈ 0.531). Method
cole_hopf_circuit, evolution-mode single (**S=1, k=512**), **shots=0**
(pure statevector algorithm floor). phi-modes=8 set but inert at shots=0
(it low-passes shot noise only; the SV path has none) — so at shots=0 the
only live truncation knob is **bond-dim**.

Three bond arms per nu: **bond-dim 4, 8, 16**. bond-16 is the full/exact
MPS rank at q=8 (2^(q/2); the linear-algebra bound d_k=min(2^k,2^(q-k))
peaks at the central cut = 16, so it never truncates any q=8 state).

**22 nu → Re = A/nu, A=0.3** (built across 3 sweeps, merged by the scorer):

| Re | 2 | 2.5 | 3.75 | 6 | 10 | 15 | 20 | 30 | 40 | 60 | 100 | 120 | 150 | 200 | 300 | 400 | 600 | 750 | 1000 | 1200 | 1500 | 2000 |
|----|---|-----|------|---|----|----|----|----|----|----|-----|-----|-----|-----|-----|-----|-----|-----|------|------|------|------|
| nu | .15 | .12 | .08 | .05 | .03 | .02 | .015 | .01 | .0075 | .005 | .003 | .0025 | .002 | .0015 | .001 | .00075 | .0005 | .0004 | .0003 | .00025 | .0002 | .00015 |

**Reference (this study's key refinement):** `ftcs_reference`, but with an
**adaptive grid** so the truth resolves the shock at every Re. The shock
thickness scales ~nu/A, and plain FTCS-800 refines only to a 1024-pt grid
(≥8 pts/shock only for Re≤120). So:
- **Re ≤ 120:** FTCS-800 (1024-pt grid) — already ≥8.5 pts/shock, solid.
- **Re ≥ 150:** adaptive `--ref-points ≈ 2/nu` (grids 1280 → 13568 pts),
  giving ~6–8 pts/shock at each Re. These replace FTCS-800 in the score.
The plot shades the Re ≥ 150 region to mark the FTCS-800 → adaptive switch.
Scored pointwise on identical coordinates: relL2 = ‖u_CH−u_FTCS‖/‖u_FTCS‖,
cosine = shape agreement.

## Result — two distinct degradation mechanisms

**Low Re (≤ ~40): all three arms coincide at the ~1e-4 grid floor.**
bond-8 and bond-16 are identical to ~1e-10 across the ENTIRE range (green
rings sit exactly on blue squares) — for the sine IC, φ's central-cut
Schmidt rank caps at 8 at every nu (measured), so bond-8 is exact prep and
bond-16 buys nothing. bond-4 also coincides here (φ rank ≤ 4 where φ is
smooth).

**Mechanism 1 — MPS truncation (bond-4 only), onset Re ≈ 40:**
bond-4 separates from 8/16 above Re≈40 and climbs steeply, diverging
(relL2 > 1) by Re≈200. This is truncation error: bond-4 drops φ's 5th
Schmidt value, whose discarded weight grows with Re. bond-8/16 are immune.

**Mechanism 2 — solver-grid under-resolution (all arms), onset Re ≈ 150:**
the exact-prep 8/16 arms track together and stay "good" to Re≈150, then
rise sharply and diverge by Re≈300–600. This is the **256-pt SOLVER grid**
failing to resolve the CH-sharpened shock — NOT bond error (both arms move
as one) and NOT a reference artifact: the shock-resolved adaptive truth
did NOT rescue these points (they still diverge with a valid reference),
which confirms the error is in the q=8 solution itself. Above relL2≈1 the
field is unphysical (‖u‖ and max|u| blow up to 10–50× the A=0.3 scale, and
cosine collapses toward 0), so the non-monotonic wiggle out there is the
magnitude of a blow-up, not signal.

## Takeaways / regime of utility

- **bond-8 is the sweet spot.** It is exact for CH state prep at q=8 (=
  bond-16 to ~1e-10) yet ~3.2× cheaper: the MPS-prep circuit needs
  ⌈log2(bond)⌉ ancillas, so bond-8 = 3 ancillas / ~540 CX / depth ~1050 /
  11 qubits vs bond-16 = 4 ancillas / ~1700 CX / depth ~3310 / 12 qubits.
  bond-16 spends 3× the gates capturing Schmidt values already ≤ 1e-8.
- **bond-4 is trustworthy to Re ≈ 40**, then truncation-limited (diverges
  by Re≈200). Raising bond-dim to 8 fixes this at modest cost.
- **The CH method itself (with exact prep, bond ≥ 8) is trustworthy to
  Re ≈ 150** at q=8 / T_end=0.2. Past that the 256-pt grid can't resolve
  the shock — a SOLVER-grid limit, not a method or bond limit. Pushing
  utility to higher Re requires higher q (finer grid), not more bond.
- **Reference caveat retained:** even the adaptive truth is only ~6 pts/
  shock at the top; the Re ≥ 300 points are past where the 256-pt solver
  resolves the shock at all, so they document solver-grid breakdown, not a
  cleaner CH result. The fully interpretable, both-grids-resolved range is
  Re ≲ 150.

## Files

- Plot: `relL2_vs_Re_single.png` (this dir)
- Scores CSV (66 rows): `nu_domain_single_scores.csv` (this dir)
- Cases spreadsheet (66 rows, native .xlsx): `nu_domain_single_cases.xlsx`
  (this dir) — SEPARATE from `paper_cases_table.xlsx`, which is untouched.
- Sweep TOMLs (in `../cases/`): `nu_domain_q8_single.toml` (Re 2–120),
  `nu_domain_q8_single_hiRe.toml` (Re 150–600, FTCS-800),
  `nu_domain_q8_single_hiRe2.toml` (Re 750–2000 + adaptive FTCS for Re≥150).
- Scorer / xlsx builder (in `../cases/`): `score_nu_domain_single.py`,
  `xlsx_nu_domain_single.py`.
- Raw output run dirs (under
  `results/burgers-ch-lbm/ch_q8_nu_domain_single/2026-09-02/`):
  `_a8836ba5` (bond 4/16, Re 2–120), `_ce436320` (adds bond-8),
  `_83f4f49e` (Re 150–600), `_c2442f4c` (Re 750–2000 + adaptive refs).

## Reproduce

```
cd /Users/agallojr/proj/src/q8020
for t in nu_domain_q8_single nu_domain_q8_single_hiRe nu_domain_q8_single_hiRe2; do
  q8020-cfd-ch-lbm/.venv/bin/q8020-sweep \
    q8020-cfd-experiments/aux/burgers-ch-lbm/cases/$t.toml
done
q8020-cfd-ch-lbm/.venv/bin/python \
  q8020-cfd-experiments/aux/burgers-ch-lbm/cases/score_nu_domain_single.py
q8020-cfd-ch-lbm/.venv/bin/python \
  q8020-cfd-experiments/aux/burgers-ch-lbm/cases/xlsx_nu_domain_single.py
```

Note: the Re 1500 / 2000 adaptive FTCS refs (grids 10240 / 13568 pts) take
~1–1.5 h each in pure-Python FTCS (substeps ~ nu·grid²); budget for that.
