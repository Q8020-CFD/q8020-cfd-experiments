"""Sanity check: is the 2026 rerun on the reconstructed qiskit 1.2.4 stack comparable with the original
2025-11-11 results?  Writes figures/november_rerun_validation/.  Run with an env that has pandas + matplotlib."""
import glob, os, re
import numpy as np, pandas as pd
import matplotlib.pyplot as plt
from plot_common import finish, tidy

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
R25 = os.path.join(os.path.dirname(ROOT), '2025-11-11')
OUT = os.path.join(HERE, 'figures', 'november_rerun_validation'); os.makedirs(OUT, exist_ok=True)
C25, C26 = '#444444', '#1f77b4'
NOTE = "2025: original run (results/.../2025-11-11).  2026: rerun on the reconstructed stack (nov_pkgs, the 11-04 and 11-05 sweeps pooled)."


def case(path, shots, year):
    rd = lambda pat: pd.read_csv(glob.glob(os.path.join(path, pat))[0], skipinitialspace=True)
    res, qc, fin = rd('residual_*.csv'), rd('qc_metadata_*.csv').sort_values('step'), rd('final_results_*.csv')
    n = len(res)
    return dict(year=year, shots=shots, steps=n, res=res.residual_total.values, mach=fin.Mach.values,
                depth=qc.circ_depth_transpile.values, gen=qc.circ_generate_time.sum() / n, tp=qc.circ_transpile_time.sum() / n,
                run=qc.circ_run_time.sum() / n, res_final=res.residual_total.values[-1])


rows = []
for p in glob.glob(os.path.join(R25, 'exact_*')): rows.append(case(p, 0, 2025))
for p in glob.glob(os.path.join(R25, 'shots_*', 'trial_*')):
    if glob.glob(os.path.join(p, 'residual_*.csv')): rows.append(case(p, int(re.search(r'shots_(\d+)', p).group(1)), 2025))
c = pd.read_csv(os.path.join(HERE, 'cases.csv')); c = c[(c.top == 'nov_pkgs') & (c.nelem == 5)]
for _, r in c.iterrows(): rows.append(case(os.path.join(ROOT, r.case_dir), int(r.shots), 2026))
d = pd.DataFrame(rows)
ref = next(r['mach'] for r in rows if r['year'] == 2025 and r['shots'] == 0)           # common reference: the 2025 exact solution
d['relL2'] = d.mach.map(lambda m: np.linalg.norm(m - ref) / np.linalg.norm(ref))
ex, sh = d[d.shots == 0], d[d.shots > 0]

# 1. exact case
fig, ax = plt.subplots(1, 3, figsize=(14, 4.4))
for r in ex.itertuples():
    k = 'k' if r.year == 2025 else None
    ax[0].plot(r.res, color=C25 if r.year == 2025 else C26, lw=2.2 if r.year == 2025 else 1.2, ls='-' if r.year == 2025 else '--',
               label=f'{r.year}' if r.year == 2025 or r.Index == ex[ex.year == 2026].index[0] else None)
    ax[1].plot(range(1, 6), r.mach, marker='o' if r.year == 2025 else 'x', color=C25 if r.year == 2025 else C26, ls='-' if r.year == 2025 else '--',
               label=f'{r.year}' if r.year == 2025 or r.Index == ex[ex.year == 2026].index[0] else None)
    ax[2].plot(r.depth, color=C25 if r.year == 2025 else C26, lw=2.2 if r.year == 2025 else 1.2, ls='-' if r.year == 2025 else '--',
               marker='o' if r.year == 2025 else 'x', ms=4)
ax[0].set_yscale('log'); ax[0].set_xlabel('Newton step'); ax[0].set_ylabel('Total residual'); ax[0].set_title('Residual history', fontsize=10)
ax[1].set_xlabel('Cell'); ax[1].set_ylabel('Final Mach number'); ax[1].set_title('Final Mach profile', fontsize=10)
ax[2].set_xlabel('Newton step'); ax[2].set_ylabel('Transpiled circuit depth'); ax[2].set_title('Circuit depth per step', fontsize=10)
for a in ax: tidy(a, 'both')
ax[0].legend(fontsize=8)
fig.suptitle(f'Exact case (shots = 0): 2025 original vs {len(ex[ex.year == 2026])} runs in 2026', fontsize=10)
finish(fig, f'{OUT}/01_exact_case.png', note=NOTE)

# 2. accuracy vs shots
fig, ax = plt.subplots(1, 2, figsize=(11.5, 4.6))
for a, (col, yl) in zip(ax, (('relL2', 'Final Mach field relL2 error vs 2025 exact'), ('res_final', 'Residual after the 15-step cap'))):
    for yr, color, mk in ((2025, C25, 's'), (2026, C26, 'o')):
        g = sh[sh.year == yr].groupby('shots')[col]; m = g.median()
        a.plot(m.index, m.values, marker=mk, color=color, label=f'{yr} (n={len(sh[sh.year == yr])})', ms=5)
        a.fill_between(m.index, g.min(), g.max(), color=color, alpha=.12, lw=0)
    a.set_xscale('log'); a.set_yscale('log'); a.set_xlabel('Shots'); a.set_ylabel(yl); tidy(a, 'both')
ax[0].legend(fontsize=8)
fig.suptitle('Shot cases: median with min-max band over trials', fontsize=10)
finish(fig, f'{OUT}/02_accuracy_vs_shots.png', note=NOTE)

# 3. timing and depth per step, shot cases pooled
fig, ax = plt.subplots(1, 3, figsize=(12, 4.4))
for a, (col, yl) in zip(ax, (('gen', 'Generate [s per step]'), ('tp', 'Transpile [s per step]'), ('run', 'Run [s per step]'))):
    data = [sh[sh.year == y][col].values for y in (2025, 2026)]
    bp = a.boxplot(data, patch_artist=True, widths=.55, medianprops=dict(color='k'), flierprops=dict(markersize=3))
    for p, color in zip(bp['boxes'], (C25, C26)): p.set_facecolor(color); p.set_alpha(.7)
    a.set_xticks([1, 2]); a.set_xticklabels([f'2025\n(n={len(data[0])})', f'2026\n(n={len(data[1])})']); a.set_ylabel(yl); tidy(a)
fig.suptitle('Shot cases (all shot counts pooled), median and quartiles', fontsize=10)
finish(fig, f'{OUT}/03_timing_per_step.png', note=NOTE)

# numbers for the README / summary
e25, e26 = ex[ex.year == 2025].iloc[0], ex[ex.year == 2026]
print('exact: steps 2025', e25.steps, '| 2026', e26.steps.tolist())
print('exact: max |dMach|', max(np.abs(m - e25.mach).max() for m in e26.mach), '| final residual 2025 %.3e, 2026 %s' % (e25.res_final, [f'{x:.3e}' for x in e26.res_final]))
print('exact: depth identical at every step:', all(np.array_equal(x, e25.depth) for x in e26.depth), '| step-0 depth', e25.depth[0])
print('exact: max rel diff residual history', max(np.max(np.abs(r - e25.res) / e25.res) for r in e26.res))
print('shot cases per shots 2025:', sh[sh.year == 2025].groupby('shots').size().to_dict(), '\n  2026:', sh[sh.year == 2026].groupby('shots').size().to_dict())
for col in ('relL2', 'res_final'):
    t = sh.groupby(['shots', 'year'])[col].median().unstack(); t['ratio26/25'] = t[2026] / t[2025]
    lo, hi = sh[sh.year == 2026].groupby('shots')[col].min(), sh[sh.year == 2026].groupby('shots')[col].max()
    t['2025 median inside 2026 min-max'] = (t[2025] >= lo) & (t[2025] <= hi); print(col); print(t.to_string(float_format=lambda v: f'{v:.3g}'))
for col in ('gen', 'tp', 'run'): print(col, 'median s/step: 2025 %.1f, 2026 %.1f' % (sh[sh.year == 2025][col].median(), sh[sh.year == 2026][col].median()))
print('steps used by shot cases: 2025', sh[sh.year == 2025].steps.value_counts().to_dict(), '2026', sh[sh.year == 2026].steps.value_counts().to_dict())
