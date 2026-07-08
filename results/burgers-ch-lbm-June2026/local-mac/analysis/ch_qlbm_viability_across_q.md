# Cole-Hopf vs QLBM viability across the q-ladder

Date: 2026-06-17. Source: every CH / QLBM case under
`experiments/results/mps-burgers/` (`burgers_ab/`, `local-mac/q{4,6,7}/`),
excluding `real-qc/`. The old probe runs `burgers_quantum/` and
`burgers_gaussian/` are set aside: they carry no `ftcs_reference` case, so no
error can be scored against them.

## Method note on errors

As elsewhere in this tree, the solver wrote `final_error: NaN` because the
in-solver classical/analytic references were disabled
(`--no-classical-reference --no-analytic-reference`). Error here is computed
post hoc against the `ftcs_reference` series in the same run:
relL2 = RMS(final profile - FTCS final) / RMS(FTCS final), with the coarser
grid linearly interpolated onto the method grid. `amp` = (max-min)/2 of the
final profile; under diffusion it must DECAY from the IC amplitude, so the FTCS
`amp` is the truth target.

## Headline

The two quantum methods are **complementary across the q-ladder**, with
opposite failure modes:

- **Cole-Hopf is viable only at q4-q6, then detonates by q8.**
- **QLBM collapses at low q / low nu, but is the only viable method at q8.**

So the q10 "long" CH result (amp grew 0.30 -> 0.34, relL2 ~0.30) is not a
one-off: it is the leading edge of the same instability that fully explodes at
q8, just caught at 100 steps before it runs away.

## Cole-Hopf (CH)

| q  | n_steps | CH relL2 vs FTCS | amplitude vs FTCS         | verdict           |
|----|---------|------------------|---------------------------|-------------------|
| q4 | 30-60   | 0.08 - 0.18      | tracks (e.g. 0.262/0.267) | viable            |
| q6 | 100     | 0.11 - 0.26      | slight under/over-diffuse | viable (nu>=0.15) |
| q7 | 200     | 0.21 - 0.64      | amp stuck ~0.30, won't decay | marginal-poor  |
| q8 | 400     | 266, 304, 1.6, 1.8 | amp 242, 325, 0.96, 0.74 | catastrophic blow-up |
| q10 long | 100 | 0.30             | 0.339 (grew, should decay)| degraded, not exploded |

Best CH results in the whole tree are q4 (mutual/stress, relL2 ~0.08-0.12) and
q6 mutual at nu 0.15-0.30 (~0.11-0.15). At q8/n_steps=400 the final amplitude
reaches the hundreds. The instability scales with **q x n_steps**: more
measure/re-prepare cycles on a finer grid let the log/exp + sign-recovery +
phi-mode=8 truncation chain accumulate error until it diverges.

## QLBM

The mirror image of CH: collapses at low q / low nu, stabilizes as q grows.

| regime              | QLBM relL2  | amplitude              | verdict                |
|---------------------|-------------|------------------------|------------------------|
| q4 (all nu)         | 0.60 - 0.88 | -> 0.003-0.09 (flat)   | over-diffuses to zero  |
| q6, nu 0.15/0.20    | 0.80 - 0.999| -> 0.001-0.05 (flat)   | collapses              |
| q6, nu 0.30/0.50    | 0.10 / 0.19 | tracks (0.247, 0.256)  | viable                 |
| q7 (all nu)         | 0.15 - 0.24 | tracks (0.23-0.30)     | viable                 |
| q8 (all nu)         | 0.22 - 0.35 | tracks (0.24-0.29)     | viable & stable        |

QLBM's failure mode is the opposite of CH: at low resolution / low viscosity it
over-damps and collapses the profile to ~zero amplitude, but it stays bounded
and accurate as q grows.

## Implication

- CH wins at q4-q6 (relL2 ~0.1) but detonates by q8.
- QLBM is useless at q4 (collapses) but is the only viable method at q8 --
  exactly where CH explodes.

For a trustworthy q8-q10 smooth movie, the evidence points to **QLBM**, not
Cole-Hopf, as the method that survives at that resolution.
