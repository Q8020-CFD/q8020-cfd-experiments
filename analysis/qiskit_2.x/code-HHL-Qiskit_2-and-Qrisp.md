Following up on some claims I previously made from observation that Qrisp was producing more shallow circuits than Qiskit for the HHL implementation. Turns out their code (taken from their online tutorial) was making some gross assumptions about tidy eigenvalues. Once I started modifying it for generality, it started looking more like the quantum_linear_solver code we’re already using, so saw no benefit of using Qrisp.

Looking at quantum_linear_solver, after forking it yet again and porting it to latest Qiskit and again dropping the non-IBM dependencies, and using it to drive the fvm nozzle nelem=5, iters=15, it demonstrates the runtime benefit of the new SDK for circuit pre-processing, the new Aer for sims, even if it provides no meaningful difference on circuit depth/gates.

Key Differences

| Aspect | _b0afe787 (new, Mar 2026) | trial_5_9e98b39b (old, Nov 2025) |
|---|---|---|
| Host | MH-DT9TLJQR2V (local Mac) | Frontier HPC |
| Qiskit | 2.3.0 / Aer 0.17.2 | older version |
| Circuit gen time | 10–20s/iter | 214–280s/iter (14x slower) |
| Transpile time | 1.6–3.5s/iter | 37–48s/iter (14x slower) |
| Execute time | 7–18s/iter | 55–67s/iter (5x slower) |
| Transpiled depth | 317k–638k | 343k–689k (slightly larger) |
| Transpiled gates | 323k–649k | 343k–689k (slightly larger) |


The new Qiskit Sampler/Estimator makes turning on PEC techniques very accessible. A run of the nozzle with Dynamic Decoupling turned on gives a slightly better result in a random comparison:

| Metric | 395dcfab (new) | trial_5_9e98b39b (old) |
|---|---|---|
| Final residual (iter 14) | 0.031 | 0.050 |
| Residual reduction | 394x | 248x |
| HHL fidelity range | 0.985–0.999 | 0.997–0.999 |
| HHL l2_error_abs (final) | 0.0025 | 0.0079 |
| HHL linsys_residual (final) | 0.030 | 0.045 |



However, we’ve not improved the circuit depth here much, and LuGo does. 