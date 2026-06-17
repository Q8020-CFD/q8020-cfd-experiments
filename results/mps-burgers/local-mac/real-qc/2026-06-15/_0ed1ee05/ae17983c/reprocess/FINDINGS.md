# Post-hoc reprocessing of the q3 Cole–Hopf "stunt" hardware run

**Run:** `_0ed1ee05/ae17983c` — `smooth_stunt` (q=3, single exact step, T=0.375)
on `ibm_kingston`, pinned layout `82,81,80,83,96`, job `d8o2g3832u0s73fd4msg`.
**On-device result:** rel-L2 vs FTCS = **2.19**.

## What was attempted
Pull the saved hardware counts back from the IBM job and re-run **only the
classical reconstruction** (post-select → φ → spectral low-pass → inverse
Cole–Hopf), sweeping the `phi_modes` cutoff, plus a norm-matched variant that
rescales u to the reference amplitude. No new QPU time.

Code: [`reprocess_denoise.py`](reprocess_denoise.py) · Data:
[`reprocess_results.json`](reprocess_results.json)

## Result: post-processing does NOT recover the run

| phi_modes | rel-L2 | rel-L2 (norm-matched) | corr | ‖u‖ |
|-----------|--------|-----------------------|------|-----|
| 0 (no filter = the run) | 2.1925 | 0.9607 | 0.539 | 0.428 |
| 1 | 2.1343 | 0.9534 | 0.546 | 0.419 |
| 2 | 2.1939 | 0.9601 | 0.539 | 0.428 |
| 3 | 2.1887 | 0.9594 | 0.540 | 0.428 |
| 4 (Nyquist, no-op) | 2.1925 | 0.9607 | 0.539 | 0.428 |

(phi_modes=0 reproduces the recorded 2.1925 exactly → the reconstruction
pipeline here is faithful to the runner.)

## Conclusion
- **Denoising fails.** No spectral cutoff helps; the best (`phi_modes=1`) is
  2.13, still garbage. At q=3 there are only ~4 modes, and the corruption sits
  in the *low* modes (the fundamental itself), not in filterable high-frequency
  ripple.
- **Renormalization fails too.** Even with the amplitude rescaled to match the
  reference, rel-L2 is **0.96** — i.e. the *shape* is ~96% wrong. The
  correlation of 0.54 sounds like "half signal" but at matched amplitude it
  corresponds to ≈96% relative error (rel-L2 ≈ √(2(1−corr))).
- **The earlier "amplitude inflation" read was incomplete.** The inverse-CH
  log-derivative is scale-invariant in φ, so the ‖u‖=0.43-vs-0.17 gap is not a
  normalization artifact and is not fixable by rescaling — the measured
  probability distribution itself is too corrupted.

**Bottom line:** the hardware-measured distribution for this circuit is too far
from ideal to recover in post-processing. Combined with the three on-device
attempts (q4 deep 1.71 → q3 stunt 1.34 → q3 stunt + good-qubit layout 2.19),
the failure is upstream of reconstruction and is not addressed by depth,
operating point, qubit layout, denoising, or renormalization. The dominant
error is something the depolarizing+readout noise model does not capture
(coherent/systematic — likely QFT phase sensitivity / crosstalk), which is why
every noisy-sim prediction (~0.16) overshot the hardware.
