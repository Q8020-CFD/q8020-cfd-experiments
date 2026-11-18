# hhl-staircase-lugo-aqc74 on ibm_chicago

Staircase of mirrored HHL steps on IBM hardware: step k is the state preparation of b, the clock Hadamards and QPE blocks 1..k of the LuGo real-L AQC@74 circuit (nelem 5), then their exact inverse, so the ideal output is clock and ancilla 0 and the system as |b|^2. The decay of the return probability with two-qubit gate count measures the noise the full circuit sees on the same physical qubits.

| piece | value |
|---|---|
| backend | `ibm_chicago` ({'family': 'Nighthawk', 'revision': '2'}) |
| job | `dbue0jeps3fc73bil510`, status DONE, tags q8020, fvm-hhl-staircase, nelem5, lugo-realL-aqc74 |
| submitted | 2026-11-17T23:16:29.416361+00:00 from macos-laptop |
| ran | 2026-11-17T23:16:31.260168Z to 2026-11-17T23:35:38.870453Z (UTC) |
| QPU usage | 1017 s |
| code | aux `fcb86505a555` plus `code/aux.patch`, untracked figures/block_rewrite.png, figures/block_rewrite.py, figures/staircase_ibm_boston.pdf, figures/staircase_ibm_boston.png, figures/workflow_slots.d2, figures/workflow_slots.png, figures/workflow_slots.svg, ibm_capture.py, ibm_staircase.py, plot_staircase.py, real_structure.py, realfit.py, sign_check.py; experiments `eb7d2860432e`; metautil `2380796f056d`; qiskit 2.6.0, qiskit-aer 0.17.2, qiskit-ibm-runtime 0.50.0, numpy 2.5.2, scipy 1.18.0 |
| layout | 14 qubits [87, 88, 98, 99, 97, 96, 89, 86, 108, 95, 107, 106, 109, 77], optimization level 2 |
| options | {"dynamical_decoupling": {"enable": true, "sequence_type": "XY4", "scheduling_method": "alap"}, "twirling": {"enable_gates": true, "enable_measure": true, "num_randomizations": "auto", "shots_per_randomization": 10000}} |

| PUB | shots | 2q gates | duration us | ESP | return P (readout) | survival | system fidelity |
|---|---|---|---|---|---|---|---|
| step0 | 150000 | 43 | 6 | 8.71e-01 | 0.9470 | 0.9469 | 0.449 |
| step1 | 150000 | 486 | 44 | 3.99e-01 | 0.0955 | 0.0937 | 0.128 |
| step2 | 150000 | 940 | 80 | 2.07e-01 | 0.0305 | 0.0286 | 0.115 |
| step3 | 150000 | 1341 | 117 | 9.95e-02 | 0.0134 | 0.0115 | 0.119 |
| step4 | 1000000 | 1816 | 157 | 4.23e-02 | 0.0070 | 0.0050 | 0.114 |
| step6 | 1000000 | 2706 | 229 | 3.60e-03 | 0.0047 | 0.0028 | 0.120 |
| step8 | 1000000 | 3623 | 309 | 3.84e-03 | 0.0041 | 0.0022 | 0.118 |
| cal0 | 150000 |  | 1 |  |  |  |  |
| cal1 | 150000 |  | 1 |  |  |  |  |

No fit: fewer than two steps past step 0 keep system signal.

System fidelity of a maximally mixed system: 0.120. A step at that value carries no system signal, and any excess of its return P over the null is then more likely relaxation toward 0 than surviving signal, so its survival is an upper bound.

Return P is the probability that clock and ancilla read 0; its null (maximally mixed output) is 2^-9. Survival is (P - null) / (1 - null). Readout correction uses the cal0 and cal1 PUBs. The system fidelity is the classical fidelity of the system marginal, given clock and ancilla 0, against |b|^2.

Files: `prep.json`, `isa.qpy` (Git LFS), `counts.json`, `job.json`, `analysis.json`, `calibration/submit.json` (at submit) and `calibration/run.json` (in effect at the run start), `code/`, and one metautil case per PUB under `pubs/`.

Captured by `ibm_capture.py` at 2026-11-17T23:36:52.849256Z; code snapshot taken at 2026-11-17T23:16:27.072629Z.
