# `ibm_boston` scored worst in June and the score was right: a mode-space forensics

Author: Andy Gallo · Written 2026-09-12 · Artifacts analysed: June 2026 hardware
runs (executed 2026-06-15/16 UTC) and the September 2026 rerun
(2026-09-10T21:11Z → 2026-09-11T18:00Z)

Companion to
`/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/results/burgers-ch-lbm/ch_smooth_movie_rerun/analysis/FINDINGS-smooth-movie-rerun-segment1-UQ.md`.

**Supersedes §4.3 of that note** (the "June's amplitude normalization was wrong"
reading) — see §7 here. Everything else in that note stands.

> **Revision note.** An earlier draft of this note concluded that boston was the
> best *performer* and that relL$_2$ had mis-ranked it. That was wrong, and §4
> below is the correction: boston leads only on the one measure that an overall
> field inflation flatters (raw $\lvert U_1\rvert$), and it is **last** on both
> normalization-free measures. June's ranking of boston last is corroborated,
> not contradicted. The mode-space mechanism, the coherence result, and the
> `phi_modes` defect are unaffected.

---

## 0. The question and the answer

June's paper table ranks `ibm_boston` **worst** of four devices (frame-1
relL$_2$ = 0.813514, against miami 0.576395, fez 0.595078, kingston 0.634146),
which contradicts every calibration figure — boston is a Heron R3 and the best
machine in the set. September cannot arbitrate: all 10 boston trials died on the
IBM instance usage limit at segment 1/6, so boston has **zero** September data.

**Answer, in three parts:**

1. **Boston really is the best-calibrated device** (§1), and that is not a
   one-day artifact — readout error is stable to within ±7.3 % across the
   three-month gap for the three devices that ran in both epochs, and boston's
   margin is 2.4×.
2. **Boston nevertheless returned the worst field of the four, and June's
   ranking is correct** (§4). Its field is inflated 1.27× over the noiseless
   norm and has the *lowest* signal purity and the *lowest* cosine of any
   device. The apparent "boston recovers 99 % of the ceiling" is an artifact of
   reading raw $\lvert U_1\rvert$, which inflation flatters.
3. **The mechanism is a coherent period-4-node ($k$=2) contaminant** (§3, §5,
   §6) that the Cole–Hopf log-derivative amplifies maximally. It owns 63.8 % of
   boston's error, it is phase-locked ($\bar R$ = 0.999 over $n$=10 repeats), and
   it is not readout or shot noise. The program's stated remedy for it —
   `--phi-modes` — was a **silent no-op** at $q$=3 in both epochs (§8).

**So the original puzzle is a real physical result, not a metrology artifact: the
best-calibrated device produced the most contaminated field.** Why remains open,
and §2 is explicit that with $n$=1 on a different calibration day there is not
enough data here to close it.

Figure:
`/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/results/burgers-ch-lbm/ch_smooth_movie_rerun/analysis/boston_mode_budget.png`

Reproduce:

```
cd /Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/burgers-ch-lbm/cases
/Users/agallojr/proj/src/q8020/q8020-cfd-ch-lbm/.venv/bin/python boston_forensics.py
/Users/agallojr/proj/src/q8020/q8020-cfd-ch-lbm/.venv/bin/python plot_boston_mode_budget.py
```

Both scripts import the metric and case constants from
`/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/burgers-ch-lbm/cases/score_smooth_movie_rerun.py`,
so every relL$_2$ quoted here is byte-identical to `paper_cases_table` column S;
that script reproduces all four published June values to $<$ 1e-4.

---

## 1. Boston is the best-calibrated device — and that part is durable

Median calibration values from the `backend` snapshot captured inside each June
job record (156 qubits, `metrics.timestamps` + `captured_at`):

| device | hardware | readout err (median) | $T_2$ (median) | CZ err (median) | post-select survival |
|---|---|---|---|---|---|
| `ibm_boston` | Heron R3 | **0.00342** | **314.3 µs** | **0.00123** | **0.913** |
| `ibm_kingston` | Heron R2 | 0.00830 | 138.0 µs | 0.00199 | 0.882 |
| `ibm_fez` | Heron R2 | 0.00903 | 93.8 µs | 0.00266 | 0.860 |
| `ibm_miami` | Nighthawk R1 | 0.01947 | 242.8 µs | 0.00298 | 0.871 |

Boston wins every column. The obvious objection is that this is a single
calibration snapshot, so it could be a lucky day. It is not: median readout error
for the three devices with both epochs drifts only

| device | June RO err | Sep RO err | drift over ~3 months |
|---|---|---|---|
| kingston | 0.00830 | 0.00769 | −7.3 % |
| fez | 0.00903 | 0.00934 | +3.4 % |
| miami | 0.01947 | 0.01935 | −0.6 % |

Median readout error is a **stable device property** at the few-percent level
over three months. Boston's 2.4× margin over the next-best device cannot be
closed by that drift, and Heron R3 vs Heron R2 vs Nighthawk R1 is an
architecture-generation fact independent of any run. Claim 1 is well supported.

**Comparability caveat.** Boston's segment 0 sat in the queue **53 484 s**
(≈14.9 h) — created 2026-06-15T22:00:36Z, running 2026-06-16T12:52:00Z — so
boston executed on a **different calibration day (June 16)** than its three peers
(all June 15). Once started, all 6 segments ran back-to-back within 4 minutes on
one snapshot, so the measure-and-reprepare seam chain is intact. But the
cross-device comparison carries a one-day calibration offset for boston alone,
and §2 shows that is the axis along which the largest variance lives.

---

## 2. What the evidence base actually is, and what it will not support

Boston has **one** run: one frame-1 field, on one day, with no repeat anywhere in
the tree (`find` over all of `results/` returns exactly one June boston artifact
and ten empty September trial directories). Everything device-specific about
boston below is $n$=1. Two questions follow: how noisy is a single trial, and how
much does a device move between days?

**(a) Trial-to-trial spread is small.** Per-trial $\lvert U_1\rvert$/ceiling
across September repeats:

| device | $n$ | mean | sd | rel sd | min | max |
|---|---|---|---|---|---|---|
| kingston | 10 | 0.6432 | 0.0131 | 2.0 % | 0.6216 | 0.6647 |
| fez | 10 | 0.6192 | 0.0165 | 2.7 % | 0.5959 | 0.6415 |
| miami | 3 | 0.3319 | 0.0104 | 3.1 % | 0.3217 | 0.3462 |

So a single trial pins down *that device on that day* to ~2–3 %. On that basis
boston's June lead is far outside trial noise (pooled sd = 0.0134 in ceiling
units): boston − fez = +0.0963 = **7.2×** sd; boston − miami = +0.3116 = 23.3×;
boston − kingston = +0.3183 = 23.8×. The June ordering is not a fluke of one
trial's randomness.

**(b) The between-epoch term is enormous, and it dwarfs (a).** Same device, same
case, three months apart:

| device | June | Sep mean | shift | in units of that device's trial sd |
|---|---|---|---|---|
| kingston | 0.6713 | 0.6432 | −0.0281 | 2.1× |
| fez | 0.8933 | 0.6192 | **−0.2740** | **16.6×** |
| miami | 0.6779 | 0.3319 | **−0.3460** | **33.2×** |
| **boston** | **0.9895** | — | — | — |

fez moved by 16.6 of its own trial sds and miami by 33.2. **The epoch shift for
fez and miami is comparable to boston's entire lead over the other devices.** A
September boston could plausibly have landed at 0.6–0.7 like everyone else; there
is no way to know. Note also that boston's 0.9895 is above the best *single* trial
of any device in September (0.6647), i.e. it is an outlier with respect to all 23
usable September trials as well as its own three June peers — which is a reason
for caution about that number, not confidence in it.

**What the data supports:** boston's June field is what it is, measured
precisely, and §4's ranking of it against its three same-epoch peers is solid.
**What it does not support:** any claim that boston-the-device systematically
behaves this way. That needs the September rerun (§9).

---

## 3. The mode structure: why $k$=2 is the expensive mode

Frame 1 (the paper-comparable single-step point, $T$ = 0.0375) on $N$ = 8 nodes,
$q$ = 3, $\nu$ = 0.08, $A$ = 0.3, CFL = 0.3, periodic.

Cole–Hopf reconstructs velocity as a **log-derivative**,

$$u_j = -2\nu\,\frac{\log\phi_{j+1} - \log\phi_{j-1}}{2\,\Delta x},$$

with $\hat\phi_j = \sqrt{c_j / n_\mathrm{kept}}$ straight from raw post-selected
frequencies — no readout mitigation anywhere (no mthree, no unfolding; TREX
twirls but does not unbias). In Fourier space the centred stencil has transfer
function $\propto \lvert\sin(2\pi k/N)\rvert$:

| $k$ | period in nodes | stencil gain $\lvert\sin(2\pi k/8)\rvert$ | role |
|---|---|---|---|
| 1 | 8 | 0.7071 | **the physical Burgers sine** |
| 2 | 4 | **1.0000 (maximal)** | contaminant, amplified $\sqrt2\times$ more than the signal |
| 3 | 8/3 | 0.7071 | contaminant |
| 4 | 2 | **0** | annihilated exactly — invisible in $u$ |

Two consequences worth stating separately:

- **An LSB error is free; a middle-qubit error is the worst possible.** Node
  index $j = b_2b_1b_0$; a multiplicative bias on the qubit carrying bit $m$
  imprints that bit's Walsh pattern (period $2^{m+1}$) on $\log\phi$. Bit 0 →
  $k$=4 → annihilated. Bit 1 → $k$=2 → maximally amplified. Bit 2 → $k$=1 and
  $k$=3. Measured stencil response per unit bias, in $\lVert\delta u\rVert$:
  bit 0 → 0.0000, bit 1 → 3.6204, bit 2 → 2.5600.
- **Bit 0's coefficient is pure gauge.** On an even periodic grid the centred
  log-derivative decouples even and odd sublattices, so $\log\phi$ is recoverable
  only per-sublattice up to one constant each — a 2-D null space spanned by the
  constant and the checkerboard. Bit 0's Walsh pattern *is* the checkerboard. Any
  analysis in $\log\phi$ space must therefore report only bits 1 and 2;
  everything below works in $u$'s mode space ($k$ = 1, 2, 3), which is gauge-free
  ($U_0$ and $U_4$ are identically zero in every field measured).

Since $U_0 = U_4 = 0$ for every real field here, Parseval splits the error
**exactly**:

$$\lVert u - r\rVert^2 = 2N \sum_{k=1,2,3} \lvert U_k - R_k\rvert^2 .$$

---

## 4. Boston returned the worst field, and the June ranking is right

This is the section that corrects the earlier draft. Raw $\lvert U_1\rvert$ is
**not** a fair figure of merit, because it rewards a field whose *overall* scale
is too large. Boston's is: $\lVert u\rVert$ = 0.5831 against the noiseless
0.4573, i.e. inflated **1.27×** — the largest norm of any device, June or
September. Two normalization-free measures remove that confound. Purity
$\lvert U_1\rvert / \lVert u\rVert$ asks what fraction of the returned energy is
signal; cosine asks about shape alone. Both are reported as a fraction of the
noiseless field, so 1.0 is the ceiling in every column.

| epoch/device | $\lvert U_1\rvert$ | raw $\lvert U_1\rvert$/ceil | $\lVert u\rVert$ | purity | purity/noiseless | cos vs noiseless | relL$_2$ |
|---|---|---|---|---|---|---|---|
| noiseless ceiling | 0.11432 | 1.000 | 0.4573 | 0.2500 | 1.000 | 1.0000 | 0.1426 |
| June kingston | 0.07674 | 0.671 | 0.3637 | 0.2110 | **0.844** | **0.7844** | 0.6341 |
| June fez | 0.10211 | 0.893 | 0.5048 | 0.2023 | 0.809 | 0.8070 | 0.5951 |
| June miami | 0.07750 | 0.678 | 0.3678 | 0.2107 | 0.843 | **0.8237** | 0.5764 |
| **June boston** | 0.11312 | **0.990** | **0.5831** | **0.1940** | **0.776** | **0.6932** | **0.8135** |
| Sep kingston ($n$=10) | 0.07350 | 0.643 | 0.3918 | 0.1876 | 0.750 | 0.7424 | 0.6743 |
| Sep fez ($n$=10) | 0.07076 | 0.619 | 0.3683 | 0.1921 | 0.768 | 0.7052 | 0.7184 |
| Sep miami ($n$=3) | 0.03794 | 0.332 | 0.2198 | 0.1726 | 0.690 | 0.6539 | 0.7933 |

**Rank the four June devices, best first, four ways:**

| measure | ranking | boston |
|---|---|---|
| raw $\lvert U_1\rvert$ | boston > fez > miami > kingston | **1st** |
| purity $\lvert U_1\rvert/\lVert u\rVert$ | kingston > miami > fez > boston | **4th** |
| cosine vs noiseless (shape) | miami > fez > kingston > boston | **4th** |
| relL$_2$ (paper col S) | miami > fez > kingston > boston | **4th** |

Boston leads on exactly one measure — the one that inflation flatters — and is
last on the other three, including both that are normalization-free. Rescaling
every June field to the noiseless norm before comparing $\lvert U_1\rvert$ puts
boston last too (kingston 0.844, miami 0.843, fez 0.809, boston 0.776).
**relL$_2$ agrees with cosine here; it did not mis-rank anything.** Boston's
field is simultaneously the largest, the least pure, and the most misaligned in
shape.

**Parseval-exact error budget** — contribution to relL$_2^2$ per mode, and the
share of total error each mode owns. The FTCS truth has
$\lvert R_2\rvert/\lvert R_1\rvert$ = 0.028, so $k$=2 is essentially pure
contamination:

| epoch/device | relL$_2$ | $k$=1 | $k$=2 | $k$=3 | $k$2+$k$3 share |
|---|---|---|---|---|---|
| June kingston | 0.6341 | 0.2549 (63.4 %) | 0.1340 (33.3 %) | 0.0132 (3.3 %) | 36.6 % |
| June fez | 0.5951 | 0.0715 (20.2 %) | 0.2589 (73.1 %) | 0.0237 (6.7 %) | 79.8 % |
| June miami | 0.5764 | 0.2076 (62.5 %) | 0.1130 (34.0 %) | 0.0117 (3.5 %) | 37.5 % |
| **June boston** | **0.8135** | 0.2205 (33.3 %) | **0.4222 (63.8 %)** | 0.0192 (2.9 %) | **66.7 %** |
| Sep kingston | 0.6743 | 0.2075 (45.6 %) | 0.2438 (53.6 %) | 0.0034 (0.7 %) | 54.4 % |
| Sep fez | 0.7184 | 0.2953 (57.2 %) | 0.2185 (42.3 %) | 0.0024 (0.5 %) | 42.8 % |
| Sep miami | 0.7933 | 0.5425 (86.2 %) | 0.0821 (13.0 %) | 0.0048 (0.8 %) | 13.8 % |

**63.8 % of boston's error is the single mode the stencil amplifies hardest.**
That is the substantive finding, and it survives the correction above intact: it
explains *how* boston's field went wrong (one specific spurious mode, not
diffuse noise), which is exactly what a bare relL$_2$ cannot tell you. The
diagnostic value of the mode decomposition is real; the claim that it overturns
the ranking is not.

---

## 5. The contaminant is coherent, not readout or shot noise

Two independent lines rule out readout error.

**(a) Repeatability.** Across September trials the $k$=2 *phase* is locked:

| device | $n$ | $k$=2 mean phase | mean resultant $\bar R$ | circular sd |
|---|---|---|---|---|
| kingston | 10 | −2.7547 rad | **0.9993** | 0.0367 rad (≈ 2.1°) |
| fez | 10 | −1.4662 rad | **0.9995** | 0.0301 rad (≈ 1.7°) |
| miami | 3 | +2.9667 rad | 0.9963 | 0.0864 rad (≈ 5.0°) |

$\bar R \to 1$ means phase-locked: a deterministic circuit /
state-preparation / calibration error reproduced on every shot-set. Stochastic
readout or shot noise would scatter the phase and drive $\bar R \to 0$. Note the
mean phase *differs per device* (−2.75, −1.47, +2.97 rad) — each device has its
own locked phase, which is itself evidence of a per-device systematic rather than
a shared algorithmic artifact.

Boston has no September trials, so its $k$=2 phase (+1.8697 rad in June) is
$n$=1 with **no repeatability test of its own**. The coherence result is
established on the three devices that have repeats and applied to boston by
analogy; that inference is not independently verified for boston.

**(b) A bit-flip channel cannot create $k$=2 at all.** A symmetric bit-flip
readout channel is *diagonal in the Walsh basis*: it multiplies each Walsh
component of the probability vector by $(1-2\epsilon)^{\mathrm{weight}}$. It can
only **attenuate** structure already present; it cannot synthesize a new $k$=2
component. Size check anyway — invert the observed $\lvert U_2\rvert$ back to the
$\log\phi$ ripple it implies via
$\lvert\delta L_2\rvert = \lvert U_2\rvert\,\Delta x / (\nu\lvert\sin(4\pi/8)\rvert)$,
$\delta p/p = 2\lvert\delta L_2\rvert$:

| epoch/device | $\lvert U_2\rvert$ | implied $\delta p/p$ pk-pk | median readout err | ratio |
|---|---|---|---|---|
| **June boston** | 0.09011 | **0.563** | 0.00342 | **165×** |
| June fez | 0.07123 | 0.445 | 0.00903 | 49× |
| June kingston | 0.04627 | 0.289 | 0.00830 | 35× |
| June miami | 0.04732 | 0.296 | 0.01947 | 15× |
| Sep kingston | 0.06429 | 0.402 | 0.00769 | 48× |
| Sep fez | 0.05857 | 0.366 | 0.00934 | 41× |
| Sep miami | 0.03867 | 0.242 | 0.01935 | 12× |

Boston's contaminant is **165×** its readout error and ~72× the shot-noise floor
(≈ 0.0078 relative per bin at ~1.3e5 kept shots in 8 bins). The ratio is
*largest* for the device with the *smallest* readout error — the opposite of a
readout explanation, and the sharpest form of the open puzzle in §0.

**Index mangling tested and rejected.** If boston's field were a clean profile
mapped onto the wrong nodes, some (roll, flip, sign) would beat identity by a
wide margin. Best-case improvement against the noiseless field: boston
cos +0.6932 → +0.7442 (gap +0.0510); kingston +0.7844 → +0.7930; fez and miami
gain exactly 0.0000. No permutation rescues any device.

---

## 6. FINDINGS §4.3 revisited: no normalization bug

§4.3 of the companion note reads two June gains above the 0.858 noiseless ceiling
(fez $g$ = 0.9472, boston $g$ = 1.0942) as evidence that "June's amplitude
normalization was wrong." Rebuilding each gain from its own modes,
$\lVert u\rVert^2 = 2N(\lvert U_1\rvert^2 + \lvert U_2\rvert^2 + \lvert U_3\rvert^2)$:

| epoch/device | $g$ reported | $g$ from modes | $g$ if $k$=1 only | above 0.858 ceiling? |
|---|---|---|---|---|
| June kingston | 0.6824 | 0.6824 | 0.5760 | no |
| June fez | 0.9472 | 0.9472 | 0.7664 | no |
| June miami | 0.6902 | 0.6902 | 0.5817 | no |
| **June boston** | **1.0942** | 1.0942 | **0.8490** | **no** |
| Sep kingston | 0.7352 | 0.7352 | 0.5517 | no |
| Sep fez | 0.6911 | 0.6911 | 0.5311 | no |
| Sep miami | 0.4124 | 0.4124 | 0.2847 | no |

Every $k$=1-only gain sits at or below the ceiling. The ceiling bounds the $k$=1
component; $\lVert u\rVert$ additionally collects $k$=2 and $k$=3, which the
log-derivative amplifies. **Noise in a log-derivative pipeline can and does
inflate $\lVert u\rVert$ past the noiseless norm — expected behaviour, not a
normalization error.** §4.3's conclusion should be withdrawn; the June driver's
amplitude handling is consistent with the September stack.

Note this is the *same* inflation that §4 uses against boston. The two readings
are consistent: the excess norm is real spurious energy (so no code bug), and it
is a defect of the field (so boston is not thereby better). §4.4's provenance
findings are untouched — the June driver `burgers_ch_hw_runner.py` is still
uncommitted and neither epoch persisted raw counts.

---

## 7. The measure-and-reprepare loop is anti-dissipative

Boston across the movie. Physical diffusion should make the field *decay*; the
noiseless ceiling does exactly that. Boston's does the opposite.

| frame | $T$ (s) | $\lvert U_1\rvert$ | ceiling $\lvert U_1\rvert$ | $\lvert U_2\rvert$ | $\lvert U_2\rvert/\lvert U_1\rvert$ | relL$_2$ |
|---|---|---|---|---|---|---|
| 1 | 0.0375 | 0.11312 | 0.11432 | 0.09011 | 0.797 | 0.8135 |
| 2 | 0.0750 | 0.12302 | 0.10205 | 0.15179 | 1.234 | 1.5509 |
| 3 | 0.1125 | 0.15313 | 0.09109 | 0.14755 | 0.964 | 2.0912 |
| 4 | 0.1500 | 0.17843 | 0.08132 | 0.14525 | 0.814 | 2.5692 |
| 5 | 0.1875 | 0.18710 | 0.07260 | 0.16389 | 0.876 | 3.1084 |
| 6 | 0.2250 | 0.18422 | 0.06482 | 0.17001 | 0.923 | 3.5336 |

$\lvert U_1\rvert$ **grows** 0.11312 → 0.18422 (×1.63) while the true amplitude
**decays** 0.11432 → 0.06482 (×0.57), and $\lvert U_2\rvert$ nearly doubles. This
is the clearest evidence that boston's frame-1 $\lvert U_1\rvert$ is inflation
rather than fidelity: the same growth continues past the physical value until
$\lvert U_1\rvert$ is 2.8× the ceiling by frame 6. Frame $k$'s reconstructed
field is re-prepared as frame $k+1$'s initial state (6 segments,
`segment_size = 1`), so contaminant energy is re-encoded and re-amplified at
every seam. That feedback, not any single frame's noise, carries boston to
relL$_2$ = 3.53.

**Frame 1 sits at the crossover** where boston's inflating $\lvert U_1\rvert$
happens to coincide with the decaying true amplitude (0.11312 vs 0.11432, hence
the 99.0 % coincidence). Reading that as fidelity was the specific error in the
earlier draft.

---

## 8. Actionable: `phi_modes = 8` is a silent no-op at $q$=3

`fourier_low_pass_phi` in
`/Users/agallojr/proj/src/q8020/q8020-cfd-ch-lbm/src/lib_cole_hopf.py`:

```python
n_modes = min(n_modes, N // 2)
fk = np.fft.rfft(phi)
fk[n_modes + 1:] = 0.0
```

At $N$ = 8, `rfft` returns 5 entries ($k$ = 0…4) and `n_modes` clamps to 4, so
`fk[5:] = 0` zeroes **nothing**. Verified by direct import: `phi_modes` of 0, 4,
8 and 32 all leave $\phi$ unchanged to 2.2e-16; only 1 and 2 filter anything.

**Both epochs ran `phi_modes = 8`.** June: `"phi_modes": 8` at line 13 of
`/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/results/burgers-ch-lbm-June2026/real-qc/hardware_runs/smooth_movie_boston/q8020_case_0.json`.
September: `"phi-modes" = 8` in
`/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/results/burgers-ch-lbm/ch_smooth_movie_rerun/2026-09-10/_0ca9db0f/q8020_sweep.toml`,
carried through to `phi_modes=8` in each trial's `q8020_metadata_*.json`. So the
program's own stated primary accuracy dial for exactly this failure mode (mesh
`note-20260807-0002` line 447: "`--phi-modes` (Fourier low-pass) is your most
direct accuracy dial") was **inactive in every smooth_movie run in both epochs**,
and nothing in the logs says so. Any `phi_modes` $\ge N/2$ is a silent no-op; the
function should warn or clamp visibly.

Indicative available win — relL$_2$ recomputed keeping only the $k$=1 mode of
the already-reconstructed $u$:

| epoch/device | relL$_2$ as run | relL$_2$, $k$=1 only | gain |
|---|---|---|---|
| June fez | 0.5951 | 0.2689 | **2.21×** |
| **June boston** | **0.8135** | **0.4704** | **1.73×** |
| Sep kingston | 0.6743 | 0.4563 | 1.48× |
| Sep fez | 0.7184 | 0.5442 | 1.32× |
| June miami | 0.5764 | 0.4565 | 1.26× |
| June kingston | 0.6341 | 0.5057 | 1.25× |
| Sep miami | 0.7933 | 0.7371 | 1.08× |

Indicative, not exact — filtering $\phi$ then differentiating is not identical to
filtering $u$ — but it bounds the win, and it is large.

**A separate defect no amplitude filter can fix: the $k$=1 phase.** The physical
mode does not just change amplitude, it shifts along $x$:

| epoch/device | $k$=1 phase (rad) | phase err vs pure sine | shift (nodes) |
|---|---|---|---|
| **June boston** | −2.0584 | **−0.4876** | **−0.62** |
| Sep fez | −1.1905 | +0.3803 | +0.48 |
| Sep miami | −1.2368 | +0.3340 | +0.43 |
| June kingston | −1.9348 | −0.3640 | −0.46 |
| June miami | −1.8094 | −0.2386 | −0.30 |
| June fez | −1.4211 | +0.1497 | +0.19 |
| Sep kingston | −1.6821 | −0.1113 | −0.14 |

(reference: a pure sine on this grid has $k$=1 phase = −1.5708 rad). Boston's is
the largest of the four June devices — its recovered sine is displaced 0.62 of a
node. A low-pass on $\phi$ leaves this in place, so it bounds what mode filtering
alone can achieve. This is a third independent way boston's field is the worst of
the four.

---

## 9. What to change

1. **Boston needs a September rerun — this is the blocking gap.** All 10 trials
   died on the instance usage limit, so the strongest device in the set has
   $n$=1, on a calibration day none of its peers shared, and §2(b) shows the
   between-epoch term is large enough to have produced its whole anomaly. Until
   boston has repeats, "the best-calibrated device returns the most contaminated
   field" is a one-run observation, not an established result.
2. **Report the mode-resolved budget alongside relL$_2$, not instead of it.**
   relL$_2$ was right about the ranking; what it cannot say is *which* mode
   failed, and §4's budget answers that (63.8 % of boston's error in one mode).
   Both belong in the table.
3. **Never rank on raw $\lvert U_1\rvert$.** It rewards field inflation. Use
   purity $\lvert U_1\rvert/\lVert u\rVert$ or cosine, which are
   normalization-free — that was the error in this note's first draft.
4. **Fix `fourier_low_pass_phi` to fail loudly.** `phi_modes` $\ge N/2$ silently
   does nothing. Warn, or clamp to $N/2 - 1$ and log the clamp.
5. **Rerun smooth_movie with `phi_modes = 1` and `phi_modes = 2`** to convert
   §8's indicative 1.7–2.2× into a measured one. (New solver output — needs
   explicit approval before launching.)
6. **Persist raw counts.** The whole $k$=2 attribution is inferred from
   reconstructed $u$. With counts on disk the Walsh decomposition could run on
   $\phi$ directly and the responsible qubit be identified rather than deduced —
   which is what it would take to explain §5's inverted readout-error ordering.

---

## Appendix: provenance

| what | path |
|---|---|
| June boston artifact (fields) | `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/results/burgers-ch-lbm-June2026/real-qc/hardware_runs/smooth_movie_boston/method_compare/cole_hopf_circuit/q8020_artifacts_0.json` |
| June boston job records (calibration + timestamps) | `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/results/burgers-ch-lbm-June2026/real-qc/hardware_runs/smooth_movie_boston/q8020_results_1.json` |
| June boston case config (`phi_modes`) | `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/results/burgers-ch-lbm-June2026/real-qc/hardware_runs/smooth_movie_boston/q8020_case_0.json` |
| September trials | `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/results/burgers-ch-lbm/ch_smooth_movie_rerun/2026-09-10/_0ca9db0f/<device>/trial_*/q8020_metadata_*.json` |
| noiseless ceiling ($\chi$=2, shots 0) | `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/results/burgers-ch-lbm/local-mac/q3/burgers_smooth_movie_sim/cd872d62/` |
| 150k-shot sim comparison | `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/results/burgers-ch-lbm/local-mac/q3/burgers_smooth_movie_sim/d2ec49ec/` |
| forensics script (14 sections) | `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/burgers-ch-lbm/cases/boston_forensics.py` |
| figure script | `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/burgers-ch-lbm/cases/plot_boston_mode_budget.py` |
| metric source (= paper col S) | `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/burgers-ch-lbm/cases/score_smooth_movie_rerun.py` |
| reconstruction under audit | `/Users/agallojr/proj/src/q8020/q8020-cfd-ch-lbm/src/lib_cole_hopf.py`, `/Users/agallojr/proj/src/q8020/q8020-cfd-ch-lbm/src/lib_cole_hopf_circuit.py` |
| figure | `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/results/burgers-ch-lbm/ch_smooth_movie_rerun/analysis/boston_mode_budget.png` |

Sanity check on the mode analysis: the per-parity closure residuals
$\sum_j u_{2j+1}$ and $\sum_j u_{2j}$ are $\le$ 5.6e-17 for every field
examined, confirming each really came out of the centred log-derivative and that
the mode decomposition is applied to the right object.
