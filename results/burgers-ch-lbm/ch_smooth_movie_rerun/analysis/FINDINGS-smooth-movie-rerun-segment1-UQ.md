# Smooth-movie rerun: asset inventory, June-vs-September confirmation, and first-segment $L_2$ UQ

Author: Andy Gallo · Written 2026-09-12 · Runs analysed 2026-09-10T21:11Z → 2026-09-11T18:00Z (UTC)

Subject: the September 2026 hardware rerun of Melvina's June-2026 Cole–Hopf
"smooth movie" case (paper_cases_table rows #19–22) on the current `ch-lbm`
solver and a newer Qiskit stack.

---

## 1. The assets

**New (September) sweep — the "10× / 3×" runs**

| what | path |
|---|---|
| sweep root | `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/results/burgers-ch-lbm/ch_smooth_movie_rerun/2026-09-10/_0ca9db0f/` |
| sweep input | `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/results/burgers-ch-lbm/ch_smooth_movie_rerun/2026-09-10/_0ca9db0f/q8020_sweep.toml` |
| authored toml | `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/burgers-ch-lbm/cases/smooth_movie_rerun_4dev.toml` |
| expanded cases | `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/results/burgers-ch-lbm/ch_smooth_movie_rerun/2026-09-10/_0ca9db0f/q8020_expanded_cases.json` |
| analysis / figures | `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/results/burgers-ch-lbm/ch_smooth_movie_rerun/analysis/` |

The toml asked for `_trials = 10` on each of four devices (240 QPU jobs).
What actually landed:

| device | hardware | planned | usable | why |
|---|---|---|---|---|
| `ibm_kingston` | Heron R2 | 10 | **10** | all exit 0 |
| `ibm_fez` | Heron R2 | 10 | **10** | all exit 0 |
| `ibm_miami` | Nighthawk R1 | 10 | **3** | trials 3–9 exit 1 — IBM instance usage limit |
| `ibm_boston` | Heron R3 | 10 | **0** | all 10 exit 1 — usage limit, never executed |

So the sweep is **10× on the two Heron R2 devices and 3× on Nighthawk**, which
is the 10× / 3× split. `boston` contributes nothing. Every failed trial died at
**segment 1/6** (`RuntimeJobFailureError` / `RuntimeInvalidStateError`, all
downstream of the same "instance has met its usage limit" warning), so no
partial movie contaminates the usable set — the 23 usable trials each have all
6 frames. miami `trial_3` blocked 40 558 s (11.3 h) on a session that was then
closed, which is why the sweep wall-clock overran badly.

QPU charge actually spent:
kingston 2 580 s, fez 2 520 s, miami 10 890 s — **15 990 s ≈ 4.44 QPU-hours**,
against the toml's 12.2 QPU-hour projection for the full 4 × 10 plan. Miami
alone took 68 % of it (3 630 s/trial = 605 s/segment), which is what exhausted
the quota before boston.

**Old (June) counterparts**

| what | path |
|---|---|
| hardware runs (4 devices, n=1 each) | `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/results/burgers-ch-lbm-June2026/real-qc/hardware_runs/smooth_movie_{kingston,fez,miami,boston}/` |
| noiseless sim counterpart (shots 150000 and 0) | `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/results/burgers-ch-lbm-June2026/local-mac/q3/burgers_smooth_movie_sim/` |
| June case dataset | `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/burgers-ch-lbm-June2026/datasets/ch_smooth_movie_q3.json` |

**Tooling written for this analysis**

| what | path |
|---|---|
| all-frame scorer (pre-existing) | `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/burgers-ch-lbm/cases/score_smooth_movie_rerun.py` |
| first-segment UQ (new) | `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/burgers-ch-lbm/cases/uq_smooth_movie_segment1.py` |
| UQ figure (new) | `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/burgers-ch-lbm/cases/plot_smooth_movie_uq_segment1.py` |
| UQ text report | `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/results/burgers-ch-lbm/ch_smooth_movie_rerun/analysis/uq_segment1_report.txt` |
| UQ figure output | `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/results/burgers-ch-lbm/ch_smooth_movie_rerun/analysis/uq_segment1_relL2.png` |
| profile figure (new) | `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/aux/burgers-ch-lbm/cases/plot_smooth_movie_profiles_segment1.py` |
| profile figure output | `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/results/burgers-ch-lbm/ch_smooth_movie_rerun/analysis/profiles_segment1.png` |

---

## 2. Confirmation: are the September runs the same experiment?

### 2.1 Arguments — physics and circuit shape are identical

June's parameters come from `q8020_case_0.json` in each hardware-run directory;
September's from the sweep's `q8020_sweep_case_*.json`. Every physics and
case-shape argument matches:

| argument | June (`burgers_ch_hw_runner.py`, case `smooth_movie`) | September (`burgers_solver.py`) |
|---|---|---|
| `q` / `N` | 3 / 8 | 3 / 8 |
| `nu` | 0.08 | 0.08 |
| `ic` / amplitude | sine, 0.3 | sine, 0.3 |
| `cfl` → `dt` | 0.3 → 0.0375 | 0.3 → 0.0375 |
| `n_steps` | 6 | 6 |
| `segment_size` / `save_every` | 1 / 1 | 1 / 1 |
| `bc` | periodic | periodic |
| propagator | qft-diagonal | qft-diagonal (default; confirmed in stderr) |
| `bond_dim` | 8 (cap; realizes $\chi=2$) | 8 (cap; realizes $\chi=2$) |
| `phi_modes` | 8 | 8 |
| evolution | measure–reprepare | measure–reprepare |
| target / shots | hardware / 150 000 | hardware / 150 000 |
| TREX / DD | on / on | `auto` → on / on |
| optimization level | 3 | 3 |
| seed | 1234 | 1234 |

Realized circuit also matches: **5 qubits, 97 routed CZ, raw depth 13** in both;
transpiled depth 286 (June) vs 309 (September mean 308.8) — a
transpiler-version difference, not a case difference. $Re = A/\nu = 3.75$ in both.

### 2.2 What genuinely differs

| | June 2026-06-15 | September 2026-09-10 |
|---|---|---|
| solver | `burgers_ch_hw_runner.py` (Melvina's uncommitted ZBook fork) | `burgers_solver.py` (`q8020-cfd-ch-lbm`) |
| qiskit | 2.4.1 | 2.4.2 |
| qiskit-ibm-runtime | 0.47.0 | 0.49.0 |
| qiskit-aer | 0.17.2 | 0.17.2 |
| host | Windows laptop | Linux EC2 (`ip-10-159-170-106`) |
| replicates | 1 per device | 10 / 10 / 3 / 0 |
| usage field | `usage.quantum_seconds` | `usage.qpu_charge_time_seconds` |

Hardware sampling is not seedable, so bit-identity was never possible; the
rerun reproduces the circuit and the physics, not the counts.

### 2.3 $L_2$ fidelity — old vs new

All numbers are $\mathrm{relL_2} = \lVert u - u_\mathrm{ref}\rVert / \lVert u_\mathrm{ref}\rVert$
against the FTCS-800 reference subsampled to the 8 $q$-nodes — the same
definition as paper_cases_table column S. The scorer reproduces Melvina's four
published column-S values **exactly** from her artifacts (0.634146, 0.595078,
0.813514, 0.576395), so the metric is confirmed before any comparison.

Frame 1 (first segment, $T = 0.0375$):

| device | June $n{=}1$ | September mean ± 1 sd | $n$ | $z$ = (June − Sep)/sd |
|---|---|---|---|---|
| kingston | 0.6341 | **0.6749 ± 0.0162** | 10 | −2.51 |
| fez | 0.5951 | **0.7191 ± 0.0152** | 10 | −8.17 |
| miami | 0.5764 | **0.7940 ± 0.0137** | 3 | −15.94 |
| boston | 0.8135 | — | 0 | — |

Final frame 6 ($T = 0.225$):

| device | June $n{=}1$ | September mean ± 1 sd | $n$ | direction |
|---|---|---|---|---|
| kingston | 2.224 | **1.697 ± 0.157** | 10 | new **better** (+3.4 sd) |
| fez | 1.652 | **1.763 ± 0.095** | 10 | comparable (−1.2 sd) |
| miami | 1.416 | **2.719 ± 0.061** | 3 | new much worse |
| boston | 3.534 | — | 0 | — |

**Verdict.** Same experiment, different outcome, and the difference is not
run-to-run scatter. At the first segment the new stack is systematically worse
on all three devices (mean $z = -8.9$ sd; June's value falls outside the 95 %
prediction interval for a single new trial on every device). By the last frame
the ordering flips on kingston and is a wash on fez, so this is not a uniform
regression — it is a change in how the error accumulates across the six
measure–reprepare seams.

Segment-1 conditions that shifted alongside it:

| device | $p_\mathrm{success}$ June | $p_\mathrm{success}$ Sep | gain $g$ June | $g$ Sep | $\cos$ June | $\cos$ Sep |
|---|---|---|---|---|---|---|
| kingston | 0.8819 | 0.5813 | 0.682 | 0.736 | 0.779 | 0.738 |
| fez | 0.8621 | 0.8250 | 0.947 | 0.692 | 0.815 | 0.695 |
| miami | 0.8714 | 0.8622 | 0.690 | 0.414 | 0.829 | 0.654 |

Two things worth chasing separately, both outside the scope of this note:
kingston's post-selection survival dropped 0.88 → 0.58 while fez and miami barely
moved (device-specific, so most likely a kingston recalibration, not a code
change); and fez's amplitude gain fell from a near-correct 0.95 to 0.69.

---

## 3. UQ of the first-segment $L_2$

Figure: `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/results/burgers-ch-lbm/ch_smooth_movie_rerun/analysis/uq_segment1_relL2.png`

### 3.1 The band

| device | $n$ | mean | 1 sd | SEM | 95 % CI on the mean | 95 % PI, one new trial | CV |
|---|---|---|---|---|---|---|---|
| kingston | 10 | 0.6749 | 0.0162 | 0.0051 | [0.6633, 0.6865] | [0.6364, 0.7133] | 2.40 % |
| fez | 10 | 0.7191 | 0.0152 | 0.0048 | [0.7083, 0.7300] | [0.6831, 0.7552] | 2.11 % |
| miami | 3 | 0.7940 | 0.0137 | 0.0079 | [0.7601, 0.8279] | [0.7262, 0.8619] | 1.72 % |

The CI is the uncertainty on the device mean — the right thing for a paper table
cell. The PI is the spread a single re-run lands in — the right thing for judging
June's $n{=}1$ numbers. **Quotable: relL2$(T{=}0.0375)$ = 0.675 ± 0.016 on
kingston, 0.719 ± 0.015 on fez, 0.794 ± 0.014 on miami (1 sd).**

Run-to-run scatter at frame 1 is small and remarkably uniform across devices
(sd ≈ 0.014–0.016 regardless of device quality), i.e. **≈ 2 % of the value**.

### 3.2 Where the error lives — and where its variance lives

With $g = \lVert u\rVert/\lVert u_\mathrm{ref}\rVert$ (gain) and
$c = \cos(u, u_\mathrm{ref})$ (shape), the metric factorizes exactly:

$$\mathrm{relL_2}^2 = 1 + g^2 - 2gc$$

so $\min_g \mathrm{relL_2} = \sqrt{1-c^2}$ — the irreducible shape error, reached
at $g = c$.

| device | $g$ | sd($g$) | $c$ | sd($c$) | shape floor $\sqrt{1-c^2}$ | observed relL2 |
|---|---|---|---|---|---|---|
| kingston | 0.7359 | 0.0117 | 0.7379 | 0.0150 | 0.6746 | 0.6749 |
| fez | 0.6916 | 0.0225 | 0.6953 | 0.0157 | 0.7184 | 0.7191 |
| miami | 0.4137 | 0.0104 | 0.6538 | 0.0311 | 0.7559 | 0.7940 |

On both Heron devices $g \simeq c$ to three decimals, so the frame-1 relL2 **is
already sitting on its shape floor**: amplitude rescaling buys nothing (the
attenuation happens to land at the optimum), and the whole 0.67–0.72 is genuine
shape/phase error. On miami $g$ is well below $c$, so a scalar rescale would
recover 0.794 → 0.756.

First-order variance attribution confirms the same thing — the variance is
essentially all in the cosine:

| device | $\partial_g \cdot$ sd($g$) | $\partial_c \cdot$ sd($c$) | corr($g,c$) | predicted sd | observed sd |
|---|---|---|---|---|---|
| kingston | −0.00004 | −0.01636 | −0.265 | 0.01635 | 0.01620 |
| fez | −0.00012 | −0.01515 | −0.659 | 0.01507 | 0.01518 |
| miami | −0.00315 | −0.01620 | −0.824 | 0.01373 | 0.01365 |

Prediction matches observation to within 1 %, which validates the decomposition.

### 3.3 Error budget at frame 1

From the June noiseless-sim pair at identical parameters
(`cd872d62` = statevector, `d2ec49ec` = shots 150 000):

| component | relL2 contribution |
|---|---|
| algorithm / MPS-truncation floor (statevector, shots = 0) | 0.1426 |
| + shot sampling at 150 000 shots | +0.0099 |
| + device noise → kingston / fez / miami | +0.522 / +0.567 / +0.642 |

Of the total 0.675 on kingston: 21 % is the algorithmic floor, 1.5 % is shot
sampling, **77 % is device noise** — and device noise is **98 % of everything
above the statevector floor** (0.522 of 0.532). Dropping shots would barely move
the mean, consistent with the toml's note that the per-job charge is
overhead-dominated at this depth.

### 3.4 Is the ±0.016 band sampling noise or device drift?

Because relL2 sits on its shape floor, the honest place to compare is the angle
$\theta = \arccos c$ (where relL2 $\approx \sin\theta$). Scaling the sim's
sampling perturbation by $1/\sqrt{n_\mathrm{kept}}$:

| device | $n_\mathrm{kept}$ | shot-noise $\theta$ scale | observed sd($\theta$) | obs / shot |
|---|---|---|---|---|
| kingston | 87 188 | 0.0251 rad | 0.0222 rad | 0.88 |
| fez | 123 750 | 0.0211 rad | 0.0218 rad | 1.03 |
| miami | 129 333 | 0.0206 rad | 0.0415 rad | 2.01 |

On the two 10× devices the run-to-run band is **at or just below the sampling
floor** — i.e. frame-1 replication is shot-noise-limited, and there is no room
left for a device-drift term. Corroborating evidence:

- **No drift in the series.** OLS slope of relL2 on trial index is
  insignificant everywhere (kingston −0.0020/trial, $p = 0.29$; fez
  +0.0014/trial, $p = 0.44$; miami +0.0121/trial, $p = 0.30$), and lag-1
  autocorrelation is small (0.10, −0.34, −0.14). The ~1 h back-to-back series
  shows no calibration walk.
- **Survival fraction scatter is near its multinomial floor** on kingston
  (observed sd 0.00141 vs $\sqrt{p(1-p)/\text{shots}} = 0.00127$, ratio 1.11).
  fez and miami run 2.8–3.1×, so those two do carry a small real drift in
  $p_\mathrm{success}$ — but it does not propagate into relL2 (corr(relL2,
  $p_\mathrm{success}$) = −0.69 kingston, +0.29 fez).

miami's obs/shot = 2.0 is **not** evidence of drift: with $n = 3$ the 95 %
interval on an sd spans roughly 0.5×–3.7× the point estimate, so it is
statistically indistinguishable from the Heron devices.

**Caveat, stated plainly:** the sampling floor above rests on a *single*
sampled-sim draw, so it is an order-of-magnitude bound, not a measured sd. To
close it properly, replicate the noiseless sim (statevector $q{=}3$, no QPU,
seconds per run) — I have not run this, since it generates new solver output:

```
q8020-sweep smooth_movie_rerun_4dev.toml kingston \
  --set backend-type=sim --set shots=150000 --set seed=<1234,1235,...>
```

### 3.5 The dominant uncertainty is the device, not the run

One-way random-effects split of the frame-1 relL2 over the three devices:

- $\sigma_\mathrm{within}$ (run-to-run, one device) = **0.0155**
- $\sigma_\mathrm{between}$ (device-to-device) = **0.0493**
- ratio **3.2×**; ANOVA $F = 71.4$, $p = 7.8\times10^{-10}$

Every pairwise device difference is significant well past the run-to-run band:
kingston vs fez $\Delta = -0.044$ ($p = 6\times10^{-6}$), kingston vs miami
$\Delta = -0.119$ ($p = 2.6\times10^{-4}$), fez vs miami $\Delta = -0.075$
($p = 1.8\times10^{-3}$) — and kingston and fez are the *same* Heron R2
generation. **Backend identity, not replication count, is the leading term in
the frame-1 uncertainty budget.**

### 3.6 Replication budget

From the observed sd ≈ 0.015, the trials needed for a 95 % half-width on the
device mean (normal approximation; small-$n$ needs $t$ inflation on top):

| target half-width | kingston | fez | miami |
|---|---|---|---|
| ±0.010 | 11 | 9 | 8 |
| ±0.005 | 41 | 36 | 29 |

So **10× is the right order for ±0.01 and no more**; buying ±0.005 costs ~4× the
QPU time for a precision that is 5× finer than the device-to-device spread it
would be compared against. Given §3.5, the next marginal QPU-hour is better
spent on the missing **boston** arm (the one device with no September data at
all, and the June outlier at 0.814) than on more kingston trials.

---

## 4. Why miami went from best (June) to worst (September)

Figure: `/Users/agallojr/proj/src/q8020/q8020-cfd-experiments/results/burgers-ch-lbm/ch_smooth_movie_rerun/analysis/profiles_segment1.png`

The observation is correct. Frame-1 ranking by $\mathrm{relL_2}$:

| rank | June ($n{=}1$ each) | September |
|---|---|---|
| 1 (best) | miami 0.5764 | kingston 0.6749 |
| 2 | fez 0.5951 | fez 0.7191 |
| 3 | kingston 0.6341 | miami 0.7940 |
| 4 (worst) | boston 0.8135 | *(boston: no data)* |

miami is first in June and last in September, and the same flip shows at frame 6
(1.416 → 2.719). One caveat on the June side: it is $n{=}1$ per device, and the
June miami-to-fez gap is 0.019 against a run-to-run sd of ~0.015, so "miami was
**the** best" rests on a single draw. miami-worst in September is solid (3
trials, all above fez's maximum, $p = 1.8\times10^{-3}$).

### 4.1 What did NOT change

Everything on the hardware side is the same, so none of these can explain it:

| | June | September |
|---|---|---|
| miami median CZ error | 0.00298 | 0.00298 |
| miami median $T_1$ / $T_2$ | 323.3 / 242.8 µs | 314.9 / 204.7 µs |
| miami median readout error | 0.02075 | 0.01935 (*better*) |
| transpiled depth / CZ count | 307 / 98 | 294 / 98 |
| logical qubits, raw depth | 5, 13 | 5, 13 |
| $p_\mathrm{success}$ (segment 1) | 0.8714 | 0.8652 |
| TREX / DD | True / True (recorded) | on / on (`auto` → `lib_fw.py:142`) |
| QPU charge per segment | 605 s | 605 s |

Note the last row: miami's 605 s/segment is **inherent to Nighthawk, not a
September regression** — it cost exactly the same in June. September simply ran
3 trials instead of 1, which is why it consumed the quota.

### 4.2 The reconstruction is the amplifier

The Cole–Hopf inverse (`lib_cole_hopf.py:111`) is a *log-derivative* of the
measured amplitude:

$$u(x) = -2\nu\,\frac{d}{dx}\log\phi(x), \qquad
\hat\phi_j = \sqrt{c_j / n_\mathrm{kept}}$$

and `lib_cole_hopf_circuit.py:562` takes that square root from **raw
frequencies** — the current codebase contains no classical readout correction
at all (no `mthree`, no unfolding, no calibration matrix; TREX twirls the
measurement, it does not unbias the distribution a Sampler returns). So readout
error, which flattens the measured $p$ toward uniform, directly shrinks the
node-to-node differences in $\log\phi$ and therefore attenuates $u$.

That predicts the gain should order by readout error, and in September it does
so perfectly:

| September | median readout err | gain $g$ | $\mathrm{relL_2}$ |
|---|---|---|---|
| kingston | 0.00769 | 0.7359 | 0.6749 |
| fez | 0.00934 | 0.6916 | 0.7191 |
| miami | 0.01935 | 0.4137 | 0.7940 |

$r(\text{readout}, g) = -1.000$, $r(\text{readout}, \mathrm{relL_2}) = +0.970$.
miami's readout error is 2.5× kingston's, it has no correction applied, and the
metric it feeds amplifies exactly that defect. **September's device ordering is
physically consistent: miami is worst because it is the noisiest reader and the
pipeline is unprotected against that.**

### 4.3 June's ordering is the part that does not hold up

June's ranking runs the *wrong way* against device quality —
$r(\text{readout}, \mathrm{relL_2}) = -0.735$ — and the clearest symptom is
boston: the best-calibrated device of the four (readout 0.00385, $T_2$ 321 µs)
scored **worst** in June (0.8135).

The decisive check is the amplitude ceiling. The noiseless statevector run at
these exact parameters returns $g = 0.858$ with $\cos = 0.9999$ — a clean sine
at 86 % amplitude (the residual is Cole–Hopf discretization plus MPS
truncation). That 0.858 is the **most** amplitude this circuit can recover;
device noise in a decoherence-limited pipeline attenuates, it cannot amplify.

| gain $g$ at frame 1 | kingston | fez | miami | boston |
|---|---|---|---|---|
| noiseless ceiling | 0.858 | 0.858 | 0.858 | 0.858 |
| June | 0.682 | **0.947** | 0.690 | **1.094** |
| September | 0.736 | 0.692 | 0.414 | — |

Two of four June gains **exceed the noiseless ceiling**, boston's by 28 %. That
is not physically reachable by adding noise to this circuit, so June's amplitude
normalization differed from September's. Since $\mathrm{relL_2}$ is measured
against a reference whose gain is 1.0 by definition, an inflated gain flatters
the score — which is how June's fez and boston numbers were produced, and why
the June ranking does not track device quality.

### 4.4 What remains unexplained

miami's June advantage was **shape, not amplitude**: $\cos$ 0.829 (June) vs
0.654 ± 0.031 (September) — a 5.6 sd gap that the normalization argument above
does not cover. That difference is systematic and real, and it cannot be
attributed from the artifacts, because the June driver
(`burgers_ch_hw_runner.py`, Melvina's uncommitted ZBook fork) is not in version
control and cannot be diffed against `burgers_solver.py`. This is the single
biggest provenance gap in the comparison.

A second gap: September's `q8020_sweep_case_*.json` does **not** record the
resolved `measure_mitigation` / `dynamical_decoupling` values at all — only the
requested string `"auto"` (June recorded both as `True`). The tri-state had to be
resolved by reading `lib_fw.py`. Worth fixing so a run's mitigation state is
recoverable from its own artifacts.

Third, and the one that actually blocks the obvious follow-up: **no raw
measurement counts are persisted** in any artifact, in either epoch. Only the
reconstructed `solution_steps` fields plus aggregate `n_kept` / `p_success`
survive. So the highest-leverage experiment here — retrofit a classical readout
correction onto the counts we already paid for and see how much of miami's gap
closes — is not possible without new QPU time. For $q=3$ the counts are at most
16 bins per segment (~96 numbers per trial); persisting them is free and would
make readout-mitigation studies a pure post-processing exercise. Recommend adding
that to the harness before the next hardware sweep.

### 4.5 The profile figure, and why "June sine + September shadow" is not available

At frame 1 **neither epoch produces a recognizable sine**. The noiseless run
does ($\cos = 0.9999$); on hardware the cosines are 0.70–0.83 (June) and
0.65–0.74 (September), i.e. 34–49° off in the 8-node space. The figure shows
each device's June curve, the September mean with its run-to-run shadow, the
noiseless ceiling, and the FTCS-800 reference together. The shadow is a
hairline — September's per-node sd is 0.005–0.011, ~2–4 % of the sine amplitude
— and it sits nowhere near the June curve. So the run-to-run UQ is small, the
epoch-to-epoch difference is large, and both are dwarfed by the distance from
the reference. **±0.016 is the reproducibility of a wrong answer, not its
accuracy.**

---

## 5. Bottom line

1. The September assets are a faithful rerun: every physics and circuit argument
   matches June, and the scorer reproduces Melvina's four published column-S
   values exactly from her own artifacts.
2. The sweep delivered 10 trials on kingston and fez, 3 on miami, and 0 on
   boston — the IBM instance usage limit was exhausted by miami's 605 s/segment
   Nighthawk charge (10 890 s of the 15 990 s total).
3. First-segment relL2 = **0.675 ± 0.016** (kingston), **0.719 ± 0.015** (fez),
   **0.794 ± 0.014** (miami), 1 sd, with 95 % CIs on the mean of ±0.012, ±0.011,
   ±0.034.
4. That ±0.016 band is shot-noise-limited with no detectable drift, and the
   error itself is 77 % device noise (98 % of everything above the statevector
   floor), sitting exactly on its shape floor — amplitude rescaling would not
   help on the Heron devices.
5. Device-to-device variance is **3.2×** the run-to-run variance, so the
   uncertainty that matters for the paper is which backend, not how many runs.
6. June's single-run frame-1 values are systematically *better* than the
   September band on all three devices (mean −8.9 sd) — a real code/stack
   difference, not scatter — but the sign flips by frame 6 on kingston. The
   seam-to-seam error accumulation, and kingston's 0.88 → 0.58 survival drop,
   are the two open threads.
7. **miami really did go from best (June) to worst (September), and it is not
   the device** — miami's calibration, circuit, post-selection, mitigation and
   QPU cost are all unchanged. September's ordering is physically consistent
   (gain orders perfectly by readout error, $r = -1.000$, and every gain sits
   below the 0.858 noiseless ceiling); June's is not (ranking anti-correlated
   with device quality, and two of four June gains *exceed* the noiseless
   ceiling, boston's by 28 %). The most defensible reading is that June's
   amplitude normalization was wrong and its device ranking was not measuring
   device quality. miami's June *shape* advantage (cos 0.829 vs 0.654, 5.6 sd)
   stays unexplained because the June driver is uncommitted and cannot be
   diffed.
8. **At frame 1 neither epoch recovers a sine** (hardware cos 0.65–0.83 vs
   0.9999 noiseless). The September run-to-run shadow is a hairline (per-node
   sd 0.005–0.011) and does not overlap the June curve. So ±0.016 is the
   reproducibility of a wrong answer, not its accuracy — the headline
   uncertainty for the paper is systematic, not statistical.
