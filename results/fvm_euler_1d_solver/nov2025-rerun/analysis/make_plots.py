"""Summary tables + figures from cases.csv (see load_runs.py). Run with claude_env."""
import glob, os, sys
import numpy as np, pandas as pd
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, LogLocator, NullFormatter

HERE = os.path.dirname(os.path.abspath(__file__)); FIG = os.path.join(HERE, 'figures')
ROOT = os.path.dirname(HERE)
d = pd.read_csv(os.path.join(HERE, 'cases.csv'))
d = d[(d.nelem == 5) & ~d.run.str.startswith('2026-11-04/_c02436fe')]
# Left out of tables and plots, but kept in cases.csv: nelem10 (LuGo only) and the SQLS 11-04
# sweep, which duplicates 11-05 case for case (seeded).


def label(r):
    date = r['run'].split('/')[0][5:] if r['run'] != 'LuGo' else ''
    if r['family'] == 'HHL+LuGo': return f"HHL+LuGo nelem{int(r['nelem'])}"
    if r['family'] == 'SQLS': return 'SQLS'
    if r['top'] == 'nov_pkgs': return 'HHL qiskit1.2.4'  # the 11-04 and 11-05 sweeps are pooled
    q = {'new_pkgs': 'qiskit2.5.2', 'latest_pkgs': 'qiskit2.6.2'}[r['top']]
    return f"HHL {q} {date}"


d['cfg'] = d.apply(label, axis=1)
d['circ_total_s'] = d[['generate_s', 'transpile_s', 'circ_run_s']].sum(axis=1, min_count=1)
d.loc[d.family == 'SQLS', 'circ_total_s'] = np.nan
ORDER = ['HHL qiskit1.2.4', 'HHL qiskit2.5.2 11-05', 'HHL qiskit2.6.2 11-11',
         'HHL+LuGo nelem5', 'SQLS']
COL = {'HHL qiskit1.2.4': '#1f77b4', 'HHL qiskit2.5.2 11-05': '#d62728', 'HHL qiskit2.6.2 11-11': '#8c1a8c',
       'HHL+LuGo nelem5': '#2ca02c', 'SQLS': '#ff7f0e'}
MK = {k: m for k, m in zip(ORDER, 'osD<^v*PX')}
d = d[d.cfg.isin(ORDER)]

# Display names for legends and tick labels (cfg strings above stay as internal keys / CSV values)
PRETTY = {'HHL qiskit1.2.4': 'HHL, qiskit 1.2.4', 'HHL qiskit2.5.2 11-05': 'HHL, qiskit 2.5.2',
          'HHL qiskit2.6.2 11-11': 'HHL, qiskit 2.6.2', 'HHL+LuGo nelem5': 'HHL + LuGo', 'SQLS': 'SQLS'}


def pretty(c): return PRETTY.get(c, c)


def tick(c): return pretty(c).replace(', ', '\n')  # two-line tick label, no rotation needed

TRANSPILE_NOTE = ("HHL transpile uses qiskit's default settings (no optimization level set): "
                  "level 1 on qiskit 1.2.4, level 2 on 2.5.2 and 2.6.2")


def note_layout(fig, text=TRANSPILE_NOTE):
    """tight_layout leaving room for a one-line footnote about transpile settings."""
    fig.tight_layout(rect=(0, 0.045, 1, 1))
    fig.text(0.01, 0.01, text, fontsize=7.5, color='#555555', ha='left', va='bottom')



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
        ax.plot(m.index, m.values, marker=MK[c], color=COL[c], label=pretty(c), ms=5, lw=1.4)
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
    if c in cv: ax[2].plot(cv.index, cv[c], marker=MK[c], color=COL[c], label=pretty(c))
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
note_layout(fig); fig.savefig(f'{FIG}/03_walltime_vs_shots.png', dpi=140); plt.close(fig)

# 4 time breakdown, exact + shot cases
hh = [c for c in ORDER if not c.startswith('SQLS')]
fig, ax = plt.subplots(1, 2, figsize=(14, 4.8), sharey=False)
for a, sel, t in ((ax[0], d.shots == 0, 'exact (shots=0) case'), (ax[1], d.shots == 50000, 'shots=50000, median of trials')):
    b = np.zeros(len(hh)); sub = d[sel]
    for k, nm, cc in (('generate_s', 'generate', '#9ecae1'), ('transpile_s', 'transpile', '#fd8d3c'), ('circ_run_s', 'run (statevector)', '#74c476')):
        v = np.array([sub[sub.cfg == c][k].median() if (sub.cfg == c).any() else 0 for c in hh]); v = np.nan_to_num(v)
        a.bar(range(len(hh)), v, bottom=b, color=cc, label=nm); b += v
    a.set_xticks(range(len(hh))); a.set_xticklabels([tick(c) for c in hh], fontsize=9)
    a.set_ylabel('seconds, summed over Newton steps'); a.set_title(t); a.grid(alpha=.3, axis='y')
ax[0].legend(fontsize=8)
note_layout(fig); fig.savefig(f'{FIG}/04_circuit_time_breakdown.png', dpi=140); plt.close(fig)

# 5 circuit depth: all configs, and a duplicate without SQLS
ex_all = d[d.shots == 0]


def clean_log_axis(a):
    a.yaxis.set_major_locator(LogLocator(base=10, subs=(1, 2, 5)))
    a.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f'{v:,.0f}'))
    a.yaxis.set_minor_formatter(NullFormatter())
    a.grid(alpha=.3, axis='y'); a.set_axisbelow(True)
    a.spines[['top', 'right']].set_visible(False)


def depth_figure(cf, step0_title, fname, total_panel=True, ylabel='Transpiled circuit depth'):
    fig, ax = plt.subplots(1, 2 if total_panel else 1, figsize=(13 if total_panel else 6.5, 4.6), squeeze=False)
    ax = ax[0]
    v = [ex_all[ex_all.cfg == c].depth_tp_step0.median() for c in cf]
    ax[0].bar(range(len(cf)), v, color=[COL[c] for c in cf]); ax[0].set_yscale('log')
    ax[0].set_xticks(range(len(cf))); ax[0].set_xticklabels([tick(c) for c in cf], fontsize=9)
    for i, y in enumerate(v): ax[0].text(i, y * 1.1, f'{y:,.0f}', ha='center', fontsize=7)
    ax[0].set_ylabel(ylabel); ax[0].set_title(step0_title, fontsize=10); clean_log_axis(ax[0])
    if total_panel:
        hs = [c for c in cf if not c.startswith('SQLS')]
        v2 = [ex_all[ex_all.cfg == c].depth_tp_sum.median() for c in hs]
        ax[1].bar(range(len(hs)), v2, color=[COL[c] for c in hs]); ax[1].set_yscale('log')
        ax[1].set_xticks(range(len(hs))); ax[1].set_xticklabels([tick(c) for c in hs], fontsize=9)
        for i, y in enumerate(v2): ax[1].text(i, y * 1.1, f'{y:,.0f}', ha='center', fontsize=7)
        ax[1].set_ylabel('Transpiled depth, summed over steps'); ax[1].set_title('Total depth, exact case', fontsize=10); clean_log_axis(ax[1])
    note_layout(fig); fig.savefig(f'{FIG}/{fname}', dpi=140); plt.close(fig)


cf = [c for c in ORDER if (ex_all.cfg == c).any()]
depth_figure(cf, 'Circuit depth at Newton step 0\n(SQLS: {u3,cx}, opt level 0 - not like-for-like)',
             '05_circuit_depth.png')
# 05b: HHL only, step 0 only, without the qiskit 2.5.2 bar (identical depth to 2.6.2)
depth_figure([c for c in cf if not c.startswith('SQLS') and c != 'HHL qiskit2.5.2 11-05'],
             'HHL circuit depth after transpilation\n(nelem 5 nozzle, Newton step 0)', '05b_circuit_depth_no_sqls.png',
             total_panel=False, ylabel='Circuit depth (layers)')

# 6 residual traces per step by shots (HHL qiskit2.5.2, qiskit1.2.4, SQLS 11-05, LuGo n5)
def traces(case_rel):
    f = glob.glob(os.path.join(ROOT, case_rel, 'residual_*.csv'))[0]
    return pd.read_csv(f, skipinitialspace=True).residual_total.values
panels = [(c, pretty(c)) for c in ('HHL qiskit1.2.4', 'HHL qiskit2.5.2 11-05', 'HHL+LuGo nelem5', 'SQLS')]
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

# 7 stack comparison, all shot cases pooled: wall, transpile, depth
fig, ax = plt.subplots(1, 3, figsize=(16, 4.4))
for a, col, t in zip(ax, ['wall_s', 'transpile_s', 'depth_tp_step0'], ['wall time [s]', 'transpile time [s]', 'step-0 depth']):
    data = [d[(d.cfg == c) & (d.shots > 0)][col].dropna().values for c in hh]
    bp = a.boxplot(data, patch_artist=True, showfliers=True)
    for p, c in zip(bp['boxes'], hh): p.set_facecolor(COL[c]); p.set_alpha(.7)
    a.set_xticks(range(1, len(hh) + 1)); a.set_xticklabels([tick(c) for c in hh], fontsize=9)
    a.set_title(f'{t} - all shot cases pooled'); a.grid(alpha=.3, axis='y')
note_layout(fig); fig.savefig(f'{FIG}/07_hhl_stack_comparison.png', dpi=140); plt.close(fig)
print(summ.groupby('cfg', observed=True).size()); print(ex.to_string())
