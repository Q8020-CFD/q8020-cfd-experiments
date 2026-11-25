"""Recreate AIAA27 QCFD paper Figs 5-12 from the latest_pkgs run (qiskit 2.6.2, nelem=5, HHL, ideal statevector).

Run (needs numpy, pandas, scipy, matplotlib):  python make_paper_figures.py
Writes PNGs and fig7_l2_error.csv next to this script.

Inputs
  RUN   = ../../latest_pkgs/2026-11-11/_ea180c7c   (shots_0..shots_6 x 10 trials; 11b8064a = exact statevector case)
  REF   = <workspace>/fvm_euler_1d_solver/post_process/ref_sol/nelem{3,4,5,200}  (classical LU solutions)
Notes on choices that the paper does not state are in README.md ("Assumptions").
"""
import glob, json, os, re
import numpy as np, pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
RUN = os.path.abspath(os.path.join(HERE, '..', '..', 'latest_pkgs', '2026-11-11', '_ea180c7c'))
REF = os.path.abspath(os.path.join(HERE, *['..'] * 6, 'fvm_euler_1d_solver', 'post_process', 'ref_sol'))
NOTE = 'latest_pkgs: qiskit 2.6.2, fvm ef7f0a8b, nelem=5, CFL=1e10, 15 iterations, ideal statevector'
SHOTS = [500, 1000, 5000, 10000, 50000, 100000, 150000]
CMAP = plt.get_cmap('viridis')


def rd(path):
    return pd.read_csv(path, skipinitialspace=True)


def one(pattern):
    g = sorted(glob.glob(pattern))
    return g[0] if g else None


def shots_of(case):
    cmd = ' '.join(json.load(open(os.path.join(case, 'pipeline_args.json')))['cmd'])
    return int(re.search(r'-shots\s+(\d+)', cmd).group(1))


# ---- load cases: exactly N_TRIALS complete trials per shot count ----
# Original sweep: every COMPLETE case (residual, final solution and 15 qc rows). Crashed cases are dropped everywhere.
# Shot counts that fall short are topped up with the first completed cases (by trial index) of the rerun sweep
# (latest_pkgs_rerun), labelled rerun_<k> so they never collide with the paper's trial_1.
N_TRIALS = 10
RERUN = os.path.abspath(os.path.join(HERE, '..', '..', 'latest_pkgs_rerun', '2026-11-24', '_2ddbef9a'))


def load_case(case, label):
    f = lambda pat: (lambda p: rd(p) if p else None)(one(os.path.join(case, pat)))
    c = dict(dir=case, label=label, qc=f('qc_metadata_*.csv'), hm=f('hhl_metrics_*.csv'),
             res=f('residual_*.csv'), final=f('final_results_*.csv'))
    c['complete'] = c['res'] is not None and c['final'] is not None and c['qc'] is not None and len(c['qc']) == 15
    return c


def trial_index(case):
    return int(re.search(r'trial_(\d+)_', os.path.basename(case)).group(1))


cases = {s: [] for s in SHOTS}; crashed = {s: [] for s in SHOTS}; reruns_used = {s: [] for s in SHOTS}
for case in sorted(glob.glob(os.path.join(RUN, 'shots_*', 'trial_*')), key=lambda c: (shots_of(c), trial_index(c))):
    s = shots_of(case); c = load_case(case, f'trial_{trial_index(case)}')
    (cases if c['complete'] else crashed)[s].append(c)
for s in SHOTS:
    need = N_TRIALS - len(cases[s])
    if need <= 0: continue
    pool = [c for c in (load_case(p, f'rerun_{trial_index(p)}') for p in sorted(
        glob.glob(os.path.join(RERUN, f'rerun_{s}', 'trial_*')), key=trial_index)) if c['complete']]
    assert len(pool) >= need, f'shots={s}: need {need} rerun trials, only {len(pool)} complete'
    cases[s] += pool[:need]; reruns_used[s] = [os.path.basename(c['dir']) for c in pool[:need]]
for s in SHOTS: assert len(cases[s]) == N_TRIALS, (s, len(cases[s]))
EX = os.path.join(RUN, '11b8064a')
exact = dict(qc=rd(one(os.path.join(EX, 'qc_metadata_*.csv'))), res=rd(one(os.path.join(EX, 'residual_*.csv'))),
             final=rd(one(os.path.join(EX, 'final_results_*.csv'))), hm=rd(one(os.path.join(EX, 'hhl_metrics_*.csv'))))
lu = {n: rd(os.path.join(REF, f'nelem{n}', f'final_results_nelem{n}_LU.csv')) for n in (3, 4, 5, 200)}
lu_res = rd(os.path.join(REF, 'nelem5', 'residual_nelem5_LU.csv'))
color = {s: CMAP(i / (len(SHOTS) - 1)) for i, s in enumerate(SHOTS)}
PRIM = ['rho', 'u', 'p']


def save(fig, name, note=None):
    """Save without an in-figure footnote; `note` is kept for call-site documentation only (details are in README.md)."""
    fig.savefig(os.path.join(HERE, name), dpi=150, bbox_inches='tight')
    plt.close(fig)


def mean_final(s, cols):
    arr = [c['final'][cols].values for c in cases[s] if c['final'] is not None]
    return np.mean(arr, axis=0), len(arr)


# ---- Fig 5: LU vs HHL(ideal), nelem=5 only (the only mesh with HHL data), density and Mach ----
for var, ylab, fn in (('rho', r'$\rho/\rho_{ref}$', 'fig05_density_lu_vs_hhl_ideal.png'), ('Mach', 'M', 'fig05_mach_lu_vs_hhl_ideal.png')):
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.plot(lu[200].xp, lu[200][var], color='#2b6cb0', lw=2, label='Ref sol (LU, nelem=200)')
    ax.plot(lu[5].xp, lu[5][var], marker='s', color='tab:orange', ls='--', label='LU (Nelem=5)')
    ax.plot(exact['final'].xp, exact['final'][var], marker='^', color='tab:green', ls=':', label='HHL (ideal) (Nelem=5)')
    ax.set_xlabel('x/L'); ax.set_ylabel(ylab); ax.grid(alpha=.3); ax.legend(fontsize=8)
    ax.set_title('Density' if var == 'rho' else 'Mach number')
    save(fig, fn)

# ---- Fig 6: final solution vs shots (mean of trials) ----
for var, ylab, fn in (('rho', 'Density', 'fig06_density_vs_shots.png'), ('Mach', 'Mach Number', 'fig06_mach_vs_shots.png')):
    fig, ax = plt.subplots(figsize=(7, 4.6))
    ax.plot(lu[200].xp, lu[200][var], 'k', lw=2.5, label='Ref Sol')
    ax.plot(lu[5].xp, lu[5][var], 'r--o', label='LU Classical')
    for s in SHOTS:
        m, n = mean_final(s, [var])
        ax.plot(lu[5].xp, m[:, 0], color=color[s], label=f'Shots={s}')
    ax.set_xlabel('x/L'); ax.set_ylabel(ylab); ax.grid(alpha=.3); ax.legend(fontsize=8)
    save(fig, fn, NOTE + '. Mean over the 10 trials.')

# ---- Fig 7: L2 error of the trial-MEAN primitive solution (rho,u,p) vs LU nelem=5 ----
ref5 = lu[5][PRIM].values; nref = np.linalg.norm(ref5)
rows = []
for s in SHOTS:
    m, n = mean_final(s, PRIM)
    per = [np.linalg.norm(c['final'][PRIM].values - ref5) for c in cases[s] if c['final'] is not None]
    rows.append(dict(shots=s, n_trials=n, n_original=sum(c['label'].startswith('trial_') for c in cases[s]), n_rerun=sum(c['label'].startswith('rerun_') for c in cases[s]), n_crashed_original=len(crashed[s]), l2_abs_of_mean=np.linalg.norm(m - ref5),
                     l2_rel_of_mean=np.linalg.norm(m - ref5) / nref, l2_abs_mean_of_errors=np.mean(per)))
e = pd.DataFrame(rows); e.to_csv(os.path.join(HERE, 'fig7_l2_error.csv'), index=False)
fig, ax = plt.subplots(1, 2, figsize=(13.9, 5.1))   # paper image is 2084x763 px (aspect 2.73)
ax[0].loglog(e.shots, e.l2_abs_of_mean, 'o-', color='tab:blue', lw=2, ms=7)
ax[0].set_title('Absolute L2 Error'); ax[0].set_ylabel('L2 Error (Absolute)')
ax[1].loglog(e.shots, e.l2_rel_of_mean, 's-', color='tab:orange', lw=2, ms=7)
ax[1].set_title('Relative L2 Error'); ax[1].set_ylabel('L2 Error (Relative)')
for a in ax: a.set_xlabel('Number of Shots'); a.grid(alpha=.3, which='major')   # paper: major gridlines only
fig.suptitle('Final Solution L2 Error vs LU (nelem=5, ntrials=10)', fontsize=15, fontweight='bold')
fig.tight_layout()
save(fig, 'fig07_l2_error_vs_shots.png', NOTE + f'. Error of the trial-mean (rho,u,p) vs LU; relative = / ||LU|| = {nref:.3f}. '
     '10 complete trials per point (see README).')

# ---- Fig 8: fidelity vs shots, per iteration, mean with 95% CI (Student t) ----
fig, ax = plt.subplots(figsize=(11, 6))
for it in range(15):
    xs, ms, lo, hi = [], [], [], []
    for s in SHOTS:
        v = np.array([c['hm'].loc[c['hm'].step == it, 'fidelity'].iloc[0] for c in cases[s]
                      if c['hm'] is not None and (c['hm'].step == it).any()])
        if len(v) < 2: continue
        h = stats.sem(v) * stats.t.ppf(.975, len(v) - 1)
        xs.append(s); ms.append(v.mean()); lo.append(v.mean() - h); hi.append(v.mean() + h)
    c = CMAP(it / 14)
    ax.plot(xs, ms, marker='os^vd<>ph*Hx+'[it % 13], color=c, label=f'Iteration {it}')
    ax.fill_between(xs, lo, hi, color=c, alpha=.1)
ax.set_xscale('log'); ax.set_ylim(0, 1.05); ax.set_xlabel('Number of Shots'); ax.set_ylabel('Fidelity'); ax.grid(alpha=.3)
ax.legend(ncol=2, fontsize=8, loc='lower right'); ax.set_title('Fidelity vs Shots - All Iterations (95% CI, nelem=5)')
save(fig, 'fig08_fidelity_vs_shots.png', NOTE + '. Mean over every trial that reached the iteration (crashed trials contribute their early iterations).')

# ---- Fig 9: total residual history, ONE trial (trial_1), as in the paper ----
fig, ax = plt.subplots(figsize=(7.5, 5.4))
for s in SHOTS:
    c = next((c for c in cases[s] if c['label'] == 'trial_1'), None)
    if c is None or c['res'] is None: print('Fig 9: no complete trial_1 for shots', s); continue
    ax.semilogy(c['res'].residual_total.values, 'o-', ms=4, color=color[s], label=f'HHL (shots={s})')
ax.semilogy(exact['res'].residual_total.values, 'p-', color='olive', label='HHL exact statevector')
ax.semilogy(lu_res.residual_total.values, '*-', color='c', label='LU')
ax.set_xlabel('Iteration'); ax.set_ylabel('Residual'); ax.set_title('Total Residual'); ax.grid(alpha=.3, which='both'); ax.legend(fontsize=8)
save(fig, 'fig09_total_residual.png', NOTE + '. Shot curves: trial_1 of each shot count (one trial, as in the paper).')

# ---- Figs 10-12: per-iteration circuit metrics ----
PAPER_TRIAL = 'trial_1'   # verified: the paper's Figs 9, 11, 12 are trial index 1 of the 2025 run


def full_trial(s):
    """Trial index 1 (as in the paper); None if it is missing or crashed."""
    for c in cases[s]:
        if c['label'] == PAPER_TRIAL: return c
    return None


def stack(s, col):
    a = [c['qc'].sort_values('step')[col].values for c in cases[s] if c['qc'] is not None]
    n = max(len(x) for x in a)
    m = np.full((len(a), n), np.nan)
    for i, x in enumerate(a): m[i, :len(x)] = x
    return m


fig, axs = plt.subplots(1, 3, figsize=(16, 4.6))
for ax, col, t in zip(axs, ('circ_generate_time', 'circ_transpile_time', 'circ_run_time'),
                      ('Generation Time (s)', 'Transpilation Time (s)', 'Execution Time (s)')):
    for s in SHOTS:
        m = stack(s, col); mu, sd = np.nanmean(m, 0), np.nanstd(m, 0); x = np.arange(len(mu))
        ax.plot(x, mu, 'o-', ms=4, color=color[s], label=f'Shots={s}'); ax.fill_between(x, mu - sd, mu + sd, color=color[s], alpha=.15)
    ax.set_title(t, fontsize=10, fontweight='bold'); ax.set_xlabel('Iteration'); ax.set_ylabel('Time (s)'); ax.grid(alpha=.3)
axs[0].legend(fontsize=7)
fig.suptitle('Circuit Timing (Mean ± Std, nelem=5)', fontweight='bold')
save(fig, 'fig10_circuit_timing.png', NOTE + '. Mean ± population std over all trials that reached the iteration.')

fig, axs = plt.subplots(1, 3, figsize=(16, 4.6)); setc = plt.get_cmap('Set2')
for ax, col, t in zip(axs, ('circ_depth_transpile', 'circ_gates_transpile', 'circ_qubits_transpile'),
                      ('Circuit Depth', 'Number of Gates', 'Number of Qubits')):
    for i, s in enumerate(SHOTS):
        c = full_trial(s)
        if c is not None: ax.plot(c['qc'].sort_values('step')[col].values, 'o-', ms=4, color=setc(i), label=f'shots={s}')
    ax.plot(exact['qc'].sort_values('step')[col].values, 'o-', ms=4, color='#b3b3b3', label='exact statevector')
    ax.set_title(t, fontsize=10, fontweight='bold'); ax.set_xlabel('Iteration'); ax.set_ylabel(t); ax.grid(alpha=.3)
axs[0].legend(fontsize=7); fig.suptitle('Circuit Complexity (Transpiled)', fontweight='bold')
save(fig, 'fig11_circuit_complexity.png', NOTE + '. trial_1 of each shot count (as in the paper); exact case has 8 steps.')

fig, ax = plt.subplots(figsize=(6.4, 5.4))
for i, s in enumerate(SHOTS):
    c = full_trial(s)
    if c is not None: ax.semilogy(c['qc'].sort_values('step').condition_number.values, 'o-', color=setc(i), label=f'shots={s}')
ax.semilogy(exact['qc'].sort_values('step').condition_number.values, 'o-', color='#b3b3b3', label='exact statevector')
ax.set_xlabel('Iteration'); ax.set_ylabel('Condition Number'); ax.set_title('Condition Number', fontweight='bold'); ax.grid(alpha=.3, which='both'); ax.legend(fontsize=7)
save(fig, 'fig12_condition_number.png', NOTE + '. trial_1 of each shot count (as in the paper).')

print(e.to_string(float_format=lambda v: f'{v:.4g}'))
print('crashed originals dropped:', {s: [os.path.basename(c['dir']) for c in crashed[s]] for s in SHOTS if crashed[s]})
print('rerun trials used:', {s: v for s, v in reruns_used.items() if v})
