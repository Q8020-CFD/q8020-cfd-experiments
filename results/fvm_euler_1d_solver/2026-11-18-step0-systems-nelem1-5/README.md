# fvm nozzle step-0 linear systems, nelem 1 to 5

This folder holds the step-0 Newton system A, b of the fvm Euler nozzle
solver for nelem 1 to 5, in the same form fvm's `hhl_solve` pickles it. They
were captured for the hardware-wall figure (scratch spike
`hhl-kappa-depth-nelem5`).

| piece | value |
|---|---|
| node | macos-laptop (`MH-DT9TLJQR2V`) |
| run | 2026-11-18, under 2 s wall per nelem |
| code | fvm `9f6fe461` (clean), its `.venv` (Python 3.12.10, qiskit 2.6.0) |
| driver | `gen_step0.py` (in this folder) |
| experiments repo | `daacd86b5` |

## How the systems were captured

`gen_step0.py` runs `nozzle_1d_solver.py` through its own CLI:

```
-nelem N -linsolver LU -time_scheme BDF1 -cfl 1e10 -localdt -iters 1 -initers 1 -noshow
```

It intercepts the first `linear_sys_solve`, pickles A and b, and stops. No
linear solve, time step or circuit is made. The solver's defaults cover the
rest.

Read the systems with `pickle.load(fh)` to get `{"A": ..., "b": ...}`.

## Systems

| nelem | A | kappa(A) | sha256 |
|---|---|---|---|
| 1 | 3 x 3 | 13.80 | `fcc8a510...0a94b24d` |
| 2 | 6 x 6 | 38.31 | `b0354a9d...5cb5ce631` |
| 3 | 9 x 9 | 50.82 | `63eb65b9...e2d645d5454` |
| 4 | 12 x 12 | 77.02 | `e9f6caed...561f7f3040` |
| 5 | 15 x 15 | 95.98 | `7c2551de...f113b148f` |

nelem 2, 4 and 5 equal the stored pickles bit for bit (max |dA| = max |db|
= 0):

- nelem 5: `nov2025-rerun/nov_pkgs/2026-11-03/_9f0fbf67/719a35aa/system_Ab_nelem5_iter0.pkl`,
  the system used by the LuGo and rewrite runs;
- nelem 4: `~/q8020/Z-IGNORE-OLD/2026-02-02/_23ba1d16/16b2c39d/`;
- nelem 2: `~/q8020/Z-IGNORE-OLD/2026-02-08/_a2132b9e/268e76bd/`.

nelem 1 and 3 are new. Each `nelemN/gen_step0.log` holds that capture's
solver output.
