# hhl-staircase-lugo-aqc74 on ibm_boston

Staircase of mirrored HHL steps on IBM hardware: step k is the state preparation of b, the clock Hadamards and QPE blocks 1..k of the LuGo real-L AQC@74 circuit (nelem 5), then their exact inverse, so the ideal output is clock and ancilla 0 and the system as |b|^2. The decay of the return probability with two-qubit gate count measures the noise the full circuit sees on the same physical qubits.

| piece | value |
|---|---|
| backend | `ibm_boston` ({'family': 'Heron', 'revision': '3'}) |
| job | `dbucr8n82tmc73dt4jog`, status DONE, tags q8020, fvm-hhl-staircase, nelem5, lugo-realL-aqc74 |
| submitted | 2026-11-17T21:56:50.333233+00:00 from macos-laptop |
| ran | 2026-11-17T21:56:52.122032Z to 2026-11-17T22:30:15.188866Z (UTC) |
| QPU usage | 1873 s |
| code | aux `fcb86505a555` plus `code/aux.patch`, untracked figures/block_rewrite.png, figures/block_rewrite.py, figures/workflow_slots.d2, figures/workflow_slots.png, figures/workflow_slots.svg, ibm_capture.py, ibm_staircase.py, real_structure.py, realfit.py, sign_check.py; experiments `eb7d2860432e`; metautil `2380796f056d`; qiskit 2.6.0, qiskit-aer 0.17.2, qiskit-ibm-runtime 0.50.0, numpy 2.5.2, scipy 1.18.0 |
| layout | 14 qubits [129, 130, 131, 132, 128, 127, 118, 126, 125, 117, 124, 123, 105, 137], optimization level 2 |
| options | {"dynamical_decoupling": {"enable": true, "sequence_type": "XY4", "scheduling_method": "alap"}, "twirling": {"enable_gates": true, "enable_measure": true, "num_randomizations": "auto", "shots_per_randomization": 10000}} |

| PUB | shots | 2q gates | duration us | ESP | return P (readout) | survival | system fidelity |
|---|---|---|---|---|---|---|---|
| step0 | 150000 | 58 | 8 | 8.72e-01 | 0.9935 | 0.9935 | 0.779 |
| step1 | 150000 | 526 | 47 | 4.91e-01 | 0.2259 | 0.2244 | 0.278 |
| step2 | 150000 | 994 | 86 | 2.82e-01 | 0.0686 | 0.0668 | 0.174 |
| step3 | 150000 | 1460 | 124 | 1.58e-01 | 0.0339 | 0.0320 | 0.123 |
| step4 | 1000000 | 1942 | 163 | 8.86e-02 | 0.0147 | 0.0128 | 0.124 |
| step6 | 1000000 | 2916 | 240 | 2.70e-02 | 0.0068 | 0.0048 | 0.119 |
| step8 | 1000000 | 3906 | 318 | 7.74e-03 | 0.0047 | 0.0027 | 0.116 |
| cal0 | 150000 |  | 2 |  |  |  |  |
| cal1 | 150000 |  | 2 |  |  |  |  |

Fit over the 2 steps past step 0 whose system still carries signal: ln(survival) = -0.132 -2.590e-03 x (2q gates), an effective 2.59e-03 per two-qubit gate.
At the full circuit's 4727 two-qubit gates that predicts a survival of 4.22e-06.

System fidelity of a maximally mixed system: 0.120. A step at that value carries no system signal, and any excess of its return P over the null is then more likely relaxation toward 0 than surviving signal, so its survival is an upper bound.

Return P is the probability that clock and ancilla read 0; its null (maximally mixed output) is 2^-9. Survival is (P - null) / (1 - null). Readout correction uses the cal0 and cal1 PUBs. The system fidelity is the classical fidelity of the system marginal, given clock and ancilla 0, against |b|^2.

Files: `prep.json`, `isa.qpy` (Git LFS), `counts.json`, `job.json`, `analysis.json`, `calibration/submit.json` (at submit) and `calibration/run.json` (in effect at the run start), `code/`, and one metautil case per PUB under `pubs/`.

Captured by `ibm_capture.py` at 2026-11-17T22:31:39.349606Z; code snapshot taken at 2026-11-17T21:56:48.254004Z.
