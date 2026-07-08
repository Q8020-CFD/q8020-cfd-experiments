# Kappa Stabilization and Potential Optimizations

## Observation

For CFL=2 (nelem=5, 150k shots, BDF1), the condition number κ of the
Jacobian stabilizes to **κ = 13.2020** by approximately Newton iteration
10 and remains constant through convergence at iteration ~67.  The same
pattern holds for CFL=3 and other CFL values — κ flattens well before
the residual reaches its converged floor.

This means the Jacobian's **spectral structure** (eigenvalue range,
conditioning) is frozen even though the matrix entries and the RHS
residual vector continue to evolve with each Newton update.

## Why convergence continues with constant κ

The Newton iteration solves `J·δu = -R` at each step.  Near the
steady-state solution, `J` changes negligibly (hence constant κ), but
the residual `R` keeps shrinking.  HHL solves a different `Ax=b` each
iteration where `A` has the same κ but `b` is getting smaller, driving
the residual down at a constant rate (linear convergence on the
semilogy plot).

## Potential optimizations

### 1. Cache the transpiled HHL circuit

The dominant cost per iteration is **circuit generation + transpilation**
(~32s + ~4s at nelem=5).  If the matrix structure (and hence the HHL
circuit) is not changing, the same transpiled circuit can be reused
across iterations — only the state-preparation subcircuit (encoding the
new RHS) needs updating.

**Estimated speedup**: iterations 10–67 reuse one circuit → ~3–4x
reduction in total wall time at nelem=5.  Savings grow with nelem since
circuit build scales superlinearly.

### 2. Lock eigenvalue parameters

HHL's clock register size and controlled-rotation angles depend on
(λ_min, λ_max).  Once κ stabilizes, these are fixed.  Pre-computing the
optimal number of QPE qubits for the locked κ avoids redundant
eigenvalue estimation and may allow tighter rotation precision.

### 3. Classical preconditioner with cached factorization

Once the Jacobian is static, a single LU/ILU factorization enables O(N)
classical solves for all remaining iterations.  This is relevant for
hybrid workflows: use HHL while the matrix is evolving, then switch to
a cached classical factorization once κ stabilizes.

### 4. Automatic κ-freeze detection

Add a runtime check in the Newton loop:

```
if |κ_n - κ_{n-1}| / κ_n < tol_kappa:
    freeze HHL circuit; reuse for remaining iterations
```

A tolerance of `tol_kappa = 1e-4` would trigger the freeze by iteration
~10 for CFL=2.  This could be implemented as a flag in the solver
pipeline without changing the HHL builder itself.

## Supporting data

| CFL | κ (stabilized) | Stabilizes by iter | Converges at iter |
|-----|----------------|--------------------|-------------------|
| 1   | ~5.7           | ~5                 | >60 (not converged at 60i) |
| 2   | 13.20          | ~10                | ~67               |
| 3   | 19.0           | ~8                 | ~58               |
| 5   | 27.5           | ~5                 | ~44               |
| 10  | 39.5           | ~3                 | ~41               |
| 1e10| ~65            | ~5                 | >15 (15i budget)  |

See `kappa_vs_iteration.png` and `residual_convergence_all_iters.png`
in this directory.
