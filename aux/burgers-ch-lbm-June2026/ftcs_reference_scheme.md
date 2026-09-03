# FTCS reference scheme (viscous Burgers)

The classical "truth" for the QLBM / Cole–Hopf comparison is a textbook **FTCS
(Forward-Time, Centered-Space)** integrator for the **1-D viscous Burgers
equation** — not the heat equation. The nonlinear self-advection is retained:

$$\frac{\partial u}{\partial t} + u\,\frac{\partial u}{\partial x}
  = \nu\,\frac{\partial^2 u}{\partial x^2} + g,
\qquad\text{conservative form}\quad
\frac{\partial u}{\partial t} + \tfrac{1}{2}\frac{\partial (u^2)}{\partial x}
  = \nu\,\frac{\partial^2 u}{\partial x^2}.$$

The convective term $u\,\partial_x u$ steepens the profile into a shock of
thickness $\sim \nu/A$; the linear term $\nu\,\partial_{xx} u$ supplies the
physical dissipation that arrests it.

Both spatial operators are **second-order centered** on a uniform periodic grid
and advanced by **explicit forward Euler**:

$$u^{n+1}_j = u^n_j + \Delta t\left[
  \nu\,\frac{u_{j+1} - 2u_j + u_{j-1}}{\Delta x^2}
  - u_j\,\frac{u_{j+1} - u_{j-1}}{2\,\Delta x}
\right], \qquad \mathcal{O}(\Delta t,\ \Delta x^2).$$

Two consequences a CFD reader will note: the convection is **centered, not
upwinded** — purely dispersive, zero numerical diffusion, so it leans entirely
on the real $\nu$ to damp the $2\Delta x$ mode. And since centered-advection
forward-Euler is unconditionally unstable on its own, stability comes from the
diffusion term via the **diffusion-number bound** $d = \nu\,\Delta t/\Delta x^2
\le \tfrac{1}{2}$; the code uses a $\tfrac{1}{4}$ safety cap (which also covers
the advective CFL) and **sub-steps** the macro $\Delta t$ to satisfy it. To act
as a converged reference rather than a peer of the quantum run, it is solved on
a **refined grid of $\ge 800$ points** (the quantum $2^q$ nodes kept as an exact
subset, so scoring is pointwise with no interpolation error) and subsampled back
to the $q$-grid; at high $Re$ the point count is raised (up to 13568) to keep
6–8 cells across the shock.

```python
# Viscous Burgers, 1-D, periodic, uniform grid.  nu = viscosity, A = amplitude.

# --- one RHS eval: centered convection + centered diffusion ---
def rhs(u, dx, nu):
    conv = u * (roll(u, -1) - roll(u, +1)) / (2 * dx)      # u . du/dx  (centered, NO upwind)
    diff =     (roll(u, -1) - 2*u + roll(u, +1)) / dx**2   # d2u/dx2    (centered)
    return nu * diff - conv                                # du/dt = nu u_xx - u u_x

# --- FTCS = explicit forward Euler on top of that RHS ---
def solve(u, dx, nu, dt, nsteps):
    for _ in range(nsteps):
        u = u + dt * rhs(u, dx, nu)        # O(dt, dx^2)
    return u

# --- reference "truth": refine grid, sub-step for stability, subsample back ---
def ftcs_reference(u0_q, N_q, nu, dt, nsteps, ref_points=800):
    k      = ceil(ref_points / N_q)        # refine so q-nodes stay an EXACT subset
    x_ref  = uniform_grid(0, 1, N_q * k)   # >= 800 pts (per-Re: up to 13568)
    dx     = x_ref[1] - x_ref[0]
    d_max  = 0.25 * dx**2 / nu             # diffusion number d = nu dt/dx^2 <= 1/4 (covers CFL)
    sub    = ceil(dt / d_max)              # split macro dt into stable micro-steps
    u      = solve(sample_ic(u0_q, x_ref), dx, nu, dt / sub, nsteps * sub)
    return u[::k]                          # subsample fine grid -> q-grid (no interp error)
```

Canonical source: `q8020-cfd-ch-lbm/src/lib_fd.py` (`compute_rhs_shift`) and
`src/lib_classical.py` (`solve_burgers`, `solve_burgers_subsampled`,
`make_reference_grid`), driven by `burgers_solver.py --method ftcs_reference
--ref-points N`. The shift-operator form there is algebraically identical to the
`roll`-based stencil above.
