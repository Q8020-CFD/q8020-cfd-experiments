"""Summary tables + figures from cases.csv (see load_runs.py). Run with claude_env."""
import glob, os, sys
import numpy as np, pandas as pd
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__)); FIG = os.path.join(HERE, 'figures')
ROOT = os.path.dirname(HERE)
d = pd.read_csv(os.path.join(HERE, 'cases.csv'))


def label(r):
    date = r['run'].split('/')[0][5:] if r['run'] != 'LuGo' else ''
    if r['family'] == 'HHL+LuGo': return f"HHL+LuGo nelem{int(r['nelem'])}"
    if r['family'] == 'SQLS': return f"SQLS {date}"
    return f"HHL {'qiskit2.5.2' if r['top']=='new_pkgs' else 'qiskit1.2.4'} {date}"


d['cfg'] = d.apply(label, axis=1)
d['circ_total_s'] = d[['generate_s', 'transpile_s', 'circ_run_s']].sum(axis=1, min_count=1)
d.loc[d.family == 'SQLS', 'circ_total_s'] = np.nan
ORDER = ['HHL qiskit1.2.4 11-04', 'HHL qiskit1.2.4 11-05', 'HHL qiskit2.5.2 11-05',
         'HHL+LuGo nelem5', 'HHL+LuGo nelem10', 'SQLS 11-04', 'SQLS 11-05']
COL = {'HHL qiskit1.2.4 11-04': '#1f77b4', 'HHL qiskit1.2.4 11-05': '#6baed6', 'HHL qiskit2.5.2 11-05': '#d62728',
       'HHL+LuGo nelem5': '#2ca02c', 'HHL+LuGo nelem10': '#98df8a', 'SQLS 11-04': '#ff7f0e', 'SQLS 11-05': '#fdbe85'}
MK = {k: m for k, m in zip(ORDER, 'osD^v*P')}
d = d[d.cfg.isin(ORDER)]

# ---------------- summary tables
g = d[d.shots > 0].groupby(['cfg', 'shots'])
summ = g.agg(n=('shots', 'size'), n_exit_ok=('exit_ok', 'sum'), steps_med=('steps', 'median'),
             steps_max=('steps', 'max'), frac_converged=('converged', 'mean'),
             res_final_med=('res_final', 'median'), res_final_max=('res_final', 'max'),
             mach_relL2_med=('mach_relL2', 'median'), mach_relL2_max=('mach_relL2', 'max'),
             step0_l2_rel_med=('step0_l2_rel', 'median'),
             wall_min_med=('wall_s', lambda s: s.median() / 60),
             transpile_s_med=('transpile_s', 'median'), generate_s_med=('generate_s', 'median'),
             circ_run_s_med=('circ_run_s', 'median'), depth_step0=('depth_tp_step0', 'median')).reset_index()
summ['cfg'] = pd.Categorical(summ.cfg, ORDER); summ = summ.sort_values(['cfg', 'shots'])
summ.to_csv(os.path.join(HERE, 'summary_by_config_shots.csv'), index=False, float_format='%.4g')

ex = d[d.shots == 0].groupby('cfg').agg(n=('shots', 'size'), steps=('steps', 'median'), res_final=('res_final', 'median'),
        wall_min=('wall_s', lambda s: s.median() / 60), generate_s=('generate_s', 'median'),
        transpile_s=('transpile_s', 'median'), circ_run_s=('circ_run_s', 'median'),
        depth_step0=('depth_tp_step0', 'median'), depth_sum=('depth_tp_sum', 'median'),
        gates_sum=('gates_tp_sum', 'median')).reindex(ORDER).dropna(how='all')
ex.to_csv(os.path.join(HERE, 'summary_exact_case.csv'), float_format='%.4g')


def style(ax, xl='shots', yl=''):
    ax.set_xscale('log'); ax.set_xlabel(xl); ax.set_ylabel(yl); ax.grid(alpha=.3, which='both')


def shot_lines(ax, col, logy=True, cfgs=ORDER, band=True):
    for c in cfgs:
        s = d[(d.cfg == c) & (d.shots > 0)].groupby('shots')[col]
        if not len(s): continue
        m = s.median(); lo, hi = s.min(), s.max()
        ax.plot(m.index, m.values, marker=MK[c], color=COL[c], label=c, ms=5, lw=1.4)
        if band: ax.fill_between(m.index, lo, hi, color=COL[c], alpha=.12, lw=0)
    if logy: ax.set_yscale('log')


# 1 convergence: final residual + steps
fig, ax = plt.subplots(1, 3, figsize=(17, 4.6))
shot_lines(ax[0], 'res_final'); style(ax[0], yl='final total residual (median, min-max band)')
ax[0].axhline(1e-10, color='k', ls='--', lw=.8); ax[0].text(520, 1.3e-10, 'exact-case level', fontsize=8)
ax[0].set_title('Residual reached after the 15-iteration cap')
shot_lines(ax[1], 'steps', logy=False, band=False); style(ax[1], yl='Newton steps used (median; cap = 15)')
ax[1].set_title('Steps to converge'); ax[1].set_ylim(0, 16.5)
cv = d[d.shots > 0].groupby(['cfg', 'shots']).converged.mean().unstack(0)
for c in ORDER:
    if c in cv: ax[2].plot(cv.index, cv[c], marker=MK[c], color=COL[c], label=c)
style(ax[2], yl='fraction of trials converged (<15 steps)'); ax[2].set_ylim(-.05, 1.05)
ax[2].set_title('Convergence rate'); ax[0].legend(fontsize=7, loc='lower left')
fig.tight_layout(); fig.savefig(f'{FIG}/01_convergence_vs_shots.png', dpi=140); plt.close(fig)

# 2 solution error
fig, ax = plt.subplots(1, 2, figsize=(12, 4.6))
shot_lines(ax[0], 'mach_relL2'); style(ax[0], yl='relL2 of final Mach vs exact'); ax[0].set_title('Final-state error (nelem=5)')
ax[0].legend(fontsize=7)
shot_lines(ax[1], 'step0_l2_rel'); style(ax[1], yl='step-0 linear-solve relL2 error'); ax[1].set_title('Linear-solver accuracy (first Newton step)')
fig.tight_layout(); fig.savefig(f'{FIG}/02_error_vs_shots.png', dpi=140); plt.close(fig)

# 3 walltime
fig, ax = plt.subplots(1, 2, figsize=(12, 4.6))
shot_lines(ax[0], 'wall_s'); style(ax[0], yl='case wall time [s]'); ax[0].set_title('Wall time per case (sweeper-measured)')
ax[0].legend(fontsize=7)
shot_lines(ax[1], 'circ_total_s'); style(ax[1], yl='generate+transpile+run [s]'); ax[1].set_title('Circuit time per case (HHL / LuGo)')
fig.tight_layout(); fig.savefig(f'{FIG}/03_walltime_vs_shots.png', dpi=140); plt.close(fig)

# 4 time breakdown, exact + shot cases
hh = [c for c in ORDER if not c.startswith('SQLS')]
fig, ax = plt.subplots(1, 2, figsize=(14, 4.8), sharey=False)
for a, sel, t in ((ax[0], d.shots == 0, 'exact (shots=0) case'), (ax[1], d.shots == 50000, 'shots=50000, median of trials')):
    b = np.zeros(len(hh)); sub = d[sel]
    for k, nm, cc in (('generate_s', 'generate', '#9ecae1'), ('transpile_s', 'transpile', '#fd8d3c'), ('circ_run_s', 'run (statevector)', '#74c476')):
        v = np.array([sub[sub.cfg == c][k].median() if (sub.cfg == c).any() else 0 for c in hh]); v = np.nan_to_num(v)
        a.bar(range(len(hh)), v, bottom=b, color=cc, label=nm); b += v
    a.set_xticks(range(len(hh))); a.set_xticklabels([c.replace('HHL ', '') for c in hh], rotation=25, ha='right', fontsize=8)
    a.set_ylabel('seconds, summed over Newton steps'); a.set_title(t); a.grid(alpha=.3, axis='y')
ax[0].legend(fontsize=8)
fig.tight_layout(); fig.savefig(f'{FIG}/04_circuit_time_breakdown.png', dpi=140); plt.close(fig)

# 5 depth per step + sizes
ex_all = d[d.shots == 0]
fig, ax = plt.subplots(1, 2, figsize=(13, 4.6))
cf = [c for c in ORDER if (ex_all.cfg == c).any()]
v = [ex_all[ex_all.cfg == c].depth_tp_step0.median() for c in cf]
ax[0].bar(range(len(cf)), v, color=[COL[c] for c in cf]); ax[0].set_yscale('log')
ax[0].set_xticks(range(len(cf))); ax[0].set_xticklabels(cf, rotation=30, ha='right', fontsize=8)
for i, y in enumerate(v): ax[0].text(i, y * 1.1, f'{y:,.0f}', ha='center', fontsize=7)
ax[0].set_ylabel('transpiled depth, Newton step 0'); ax[0].set_title('Circuit depth (SQLS = fb_depth, different compile path)')
hs = [c for c in cf if not c.startswith('SQLS')]
v2 = [ex_all[ex_all.cfg == c].depth_tp_sum.median() for c in hs]
ax[1].bar(range(len(hs)), v2, color=[COL[c] for c in hs]); ax[1].set_yscale('log')
ax[1].set_xticks(range(len(hs))); ax[1].set_xticklabels(hs, rotation=30, ha='right', fontsize=8)
for i, y in enumerate(v2): ax[1].text(i, y * 1.1, f'{y:,.0f}', ha='center', fontsize=7)
ax[1].set_ylabel('sum of transpiled depth over steps (exact case)'); ax[1].set_title('Total depth, exact case')
fig.tight_layout(); fig.savefig(f'{FIG}/05_circuit_depth.png', dpi=140); plt.close(fig)

# 6 residual traces per step by shots (HHL qiskit2.5.2, qiskit1.2.4, SQLS 11-05, LuGo n5)
def traces(case_rel):
    f = glob.glob(os.path.join(ROOT, case_rel, 'residual_*.csv'))[0]
    return pd.read_csv(f, skipinitialspace=True).residual_total.values
panels = [('HHL qiskit2.5.2 11-05', 'HHL qiskit 2.5.2'), ('HHL qiskit1.2.4 11-05', 'HHL qiskit 1.2.4'),
          ('HHL+LuGo nelem5', 'HHL+LuGo nelem5'), ('SQLS 11-05', 'SQLS')]
SH = sorted(d[d.shots > 0].shots.unique()); cm = plt.cm.viridis(np.linspace(0, .9, len(SH)))
fig, ax = plt.subplots(1, 4, figsize=(20, 4.6), sharey=True)
for a, (c, t) in zip(ax, panels):
    sub = d[d.cfg == c]
    e = sub[sub.shots == 0]
    if len(e): a.plot(traces(e.case_dir.iloc[0]), 'k-', lw=2.2, label='exact')
    for s, col in zip(SH, cm):
        q = sub[sub.shots == s]
        if not len(q): continue
        a.plot(traces(q.sort_values('res_final').case_dir.iloc[len(q) // 2]), color=col, lw=1, label=f'{s} shots (median trial)')
    a.set_yscale('log'); a.set_title(t); a.set_xlabel('Newton step'); a.grid(alpha=.3)
ax[0].set_ylabel('total residual'); ax[0].legend(fontsize=7)
fig.tight_layout(); fig.savefig(f'{FIG}/06_residual_traces.png', dpi=140); plt.close(fig)

# 7 replicate spread: 11-04 vs 11-05 nov-pkgs, wall and transpile
fig, ax = plt.subplots(1, 3, figsize=(16, 4.4))
for a, col, t in zip(ax, ['wall_s', 'transpile_s', 'depth_tp_step0'], ['wall time [s]', 'transpile time [s]', 'step-0 depth']):
    data = [d[(d.cfg == c) & (d.shots > 0)][col].dropna().values for c in hh]
    bp = a.boxplot(data, patch_artist=True, showfliers=True)
    for p, c in zip(bp['boxes'], hh): p.set_facecolor(COL[c]); p.set_alpha(.7)
    a.set_xticks(range(1, len(hh) + 1)); a.set_xticklabels([c.replace('HHL ', '') for c in hh], rotation=25, ha='right', fontsize=8)
    a.set_title(f'{t} - all shot cases pooled'); a.grid(alpha=.3, axis='y')
fig.tight_layout(); fig.savefig(f'{FIG}/07_hhl_stack_comparison.png', dpi=140); plt.close(fig)
print(summ.groupby('cfg', observed=True).size()); print(ex.to_string())
