# 2026-11-19 HHL branch check: feature/hhl-lugo-csd against feature/sqls-aiaa-4q26

The quantum_linear_solvers `feature/hhl-lugo-csd` default build is the AIAA
4Q26 real-L rewrite: structured QPE, real L and 1/x as one UCRY. This
folder compares it, and the branch's other builds, against its parent
`feature/sqls-aiaa-4q26` at `99231b8`.

- **What ran:** exact statevector, Aer shots (150000 x seeds 1 to 10) and
  transpile-only counts for all-to-all, Heron r2, Heron r3 and Nighthawk.
  No hardware.
- **Where and when:** macos-laptop, 2026-11-19, about 23:40Z to 23:55Z.
- **Supersedes:** the same-day run of about 20:30Z, made before the real L.

Method, results table and regenerate commands are in
`aux/fvm_euler_1d_nozzle/hhl-csd-branch-check-2026-11/README.md`.

- **Code:**
  - script `aux/fvm_euler_1d_nozzle/hhl-csd-branch-check-2026-11/compare_branches.py`;
  - baseline: quantum_linear_solvers `99231b85` (the fvm venv install),
    qiskit 2.6.0, Python 3.12.10;
  - new: branch `feature/hhl-lugo-csd`, an uncommitted working tree on
    `2b8bb7b` that adds the real L (`linear_solvers/real_l.py`), qiskit
    2.6.0, Python 3.12.12;
  - `hw`: the fvm venv (qiskit-ibm-runtime fake backends, qiskit-aer
    0.17.2).
- **Inputs:**
  - `rand3`, `rand4`: random embedded systems, seeds 7 and 11;
  - `fvm5`, `fvm10`: H*t and b_herm from
    `results/fvm_euler_1d_solver/2026-02-26-LuGo/circuits/circuit_generated_nelem{5,10}_iter0.qpy`.
- **Files:**
  - `summary.json` and `summary.xlsx`: one row per case and build, with
    all-to-all, Heron r2, Heron r3 and Nighthawk counts, and the shot
    fidelities;
  - `base/`, `new/`: per-case build records, including QPE info and L
    method;
  - `new/hw.json`: the IBM counts and the per-seed shot fidelities;
  - `*.log`: console output.
- **Not kept:** the statevector npz and circuit qpy files (about 25 MB);
  they regenerate.
- **No TOML:** no solver run is involved.
