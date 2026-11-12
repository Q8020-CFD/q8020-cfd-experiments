"""HHL on qiskit 1.2.4 vs 2.5.2 vs 2.6.2 (nelem 5): figures into figures/qiskit_version_comparison/.
Reads cases.csv (see load_runs.py) plus the per-step qc_metadata CSVs and run metadata JSONs.
Run with an env that has pandas + matplotlib:  python make_qiskit_version_plots.py"""
import csv, glob, json, os
import numpy as np, pandas as pd
import matplotlib.pyplot as plt
from plot_common import VERSIONS, MARKERS, finish, commas, tidy

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
OUT = os.path.join(HERE, 'figures', 'qiskit_version_comparison'); os.makedirs(OUT, exist_ok=True)
d = pd.read_csv(os.path.join(HERE, 'cases.csv'))
d = d[(d.nelem == 5) & d.top.isin(VERSIONS)]
TOPS = list(VERSIONS); NAME = {t: VERSIONS[t][0] for t in TOPS}; COL = {t: VERSIONS[t][1] for t in TOPS}
exact = d[d.shots == 0]; shot = d[d.shots > 0]
PHASES = (('generate_s', 'generate', '#9ecae1'), ('transpile_s', 'transpile', '#fd8d3c'), ('circ_run_s', 'run (statevector)', '#74c476'))


def xlabels(ax, tops=TOPS):
    ax.set_xticks(range(len(tops))); ax.set_xticklabels([NAME[t].replace(' ', '\n', 1) for t in tops], fontsize=9)


# 1. depth at step 0
fig, ax = plt.subplots(figsize=(6, 4.6))
v = [exact[exact.top == t].depth_tp_step0.median() for t in TOPS]
ax.bar(range(3), v, color=[COL[t] for t in TOPS]); xlabels(ax); commas(ax); tidy(ax)
ax.set_ylim(0, max(v) * 1.15); ax.set_ylabel('Circuit depth (layers)')
for i, y in enumerate(v):
    ax.text(i, y + max(v) * .01, f'{y:,.0f}' + ('' if i == 0 else f'\n({y / v[0] - 1:+.0%})'), ha='center', va='bottom', fontsize=8)
ax.set_title('HHL circuit depth after transpilation\n(nelem 5 nozzle, Newton step 0)', fontsize=10)
finish(fig, f'{OUT}/01_depth_step0.png')

# 2. exact case, per Newton step
per = {t: [] for t in TOPS}
for t in TOPS:
    for cd in exact[exact.top == t].case_dir:
        f = glob.glob(os.path.join(ROOT, cd, 'qc_metadata_*.csv'))[0]
        per[t].append(pd.read_csv(f, skipinitialspace=True).sort_values('step'))
panels = (('circ_depth_transpile', 'Circuit depth (layers)'), ('circ_generate_time', 'Generate time [s]'),
          ('circ_transpile_time', 'Transpile time [s]'), ('circ_run_time', 'Run time [s]'))
fig, axs = plt.subplots(2, 2, figsize=(11, 7))
for ax, (col, yl) in zip(axs.flat, panels):
    for t in TOPS:
        m = np.median(np.stack([p[col].values for p in per[t]]), axis=0)
        ax.plot(range(len(m)), m, marker=MARKERS[t], color=COL[t], label=NAME[t], ms=5)
    ax.set_xlabel('Newton step'); ax.set_ylabel(yl); tidy(ax, 'both')
    if col == 'circ_depth_transpile': commas(ax)
axs[0, 0].legend(fontsize=8)
fig.suptitle('Exact case (shots = 0), per Newton step; qiskit 1.2.4 is the median of 3 exact runs', fontsize=10)
finish(fig, f'{OUT}/02_exact_case_per_step.png')

# 3. exact case time breakdown
fig, ax = plt.subplots(figsize=(6.5, 4.8)); b = np.zeros(3)
for col, nm, c in PHASES:
    vals = np.array([exact[exact.top == t][col].median() for t in TOPS])
    ax.bar(range(3), vals, bottom=b, color=c, label=nm)
    for i, (y0, y) in enumerate(zip(b, vals)): ax.text(i, y0 + y / 2, f'{y:,.0f}', ha='center', va='center', fontsize=8)
    b += vals
for i, y in enumerate(b): ax.text(i, y + b.max() * .01, f'{y:,.0f} s', ha='center', va='bottom', fontsize=9, fontweight='bold')
xlabels(ax); tidy(ax); commas(ax); ax.set_ylim(0, b.max() * 1.22); ax.set_ylabel('Seconds, summed over the 8 Newton steps')
ax.set_title('Where the time goes: exact case', fontsize=10); ax.legend(fontsize=8, loc='upper center', ncol=3, frameon=False)
finish(fig, f'{OUT}/03_exact_time_breakdown.png')

# 4. shot cases: per-step time and wall time, one point per case
s = shot.copy()
for col in ('generate_s', 'transpile_s', 'circ_run_s'): s[col + '_per_step'] = s[col] / s.steps
s['wall_min'] = s.wall_s / 60
panels = (('generate_s_per_step', 'Generate [s per step]'), ('transpile_s_per_step', 'Transpile [s per step]'),
          ('circ_run_s_per_step', 'Run [s per step]'), ('wall_min', 'Wall time per case [min]'))
fig, axs = plt.subplots(2, 2, figsize=(10, 8))
ncase = {t: len(s[s.top == t]) for t in TOPS}  # the same cases feed every panel, so n is shown once (bottom row)
for k, (ax, (col, yl)) in enumerate(zip(axs.flat, panels)):
    data = [s[s.top == t][col].dropna().values for t in TOPS]
    bp = ax.boxplot(data, patch_artist=True, widths=.6, medianprops=dict(color='k'), showfliers=True, flierprops=dict(markersize=3))
    for p, t in zip(bp['boxes'], TOPS): p.set_facecolor(COL[t]); p.set_alpha(.75)
    ax.set_xticks(range(1, 4))
    ax.set_xticklabels([NAME[t].replace(' ', '\n', 1) + (f'\n(n={ncase[t]})' if k >= 2 else '') for t in TOPS], fontsize=9)
    ax.set_ylabel(yl); tidy(ax)
fig.suptitle('Shot cases (all shot counts pooled), median and quartiles', fontsize=10)
finish(fig, f'{OUT}/04_shot_cases_time.png')

# 5. numerics vs shots: should not depend on the qiskit version
fig, axs = plt.subplots(1, 2, figsize=(11.5, 4.6))
for ax, (col, yl) in zip(axs, (('mach_relL2', 'Final Mach field relL2 error vs exact'), ('res_final', 'Residual after the 15-step cap'))):
    for t in TOPS:
        g = shot[shot.top == t].groupby('shots')[col]; m = g.median()
        ax.plot(m.index, m.values, marker=MARKERS[t], color=COL[t], label=NAME[t], ms=5)
        ax.fill_between(m.index, g.min(), g.max(), color=COL[t], alpha=.1, lw=0)
    ax.set_xscale('log'); ax.set_yscale('log'); ax.set_xlabel('Shots'); ax.set_ylabel(yl); tidy(ax, 'both')
axs[0].legend(fontsize=8)
fig.suptitle('Accuracy vs shots, median with min-max band over trials', fontsize=10)
finish(fig, f'{OUT}/05_accuracy_vs_shots.png')

# 6. reliability: shot cases that crashed (run 2026-11-03 of nov_pkgs died on disk quota and is excluded)
ok = {t: [0, 0] for t in TOPS}
for t in TOPS:
    for f in glob.glob(os.path.join(ROOT, t, '20*', '_*', '**', 'q8020_metadata_*.json'), recursive=True):
        if '/2026-11-03/' in f: continue
        j = json.load(open(f)); e = [x for x in j['exec_stats'] if 'success' in x]
        sh = next(x for x in j['case'] if 'params' in x)['params'].get('-shots')
        if sh and e: ok[t][0 if e[0]['success'] else 1] += 1
fig, ax = plt.subplots(figsize=(6, 4.6))
good = np.array([ok[t][0] for t in TOPS]); bad = np.array([ok[t][1] for t in TOPS]); rate = 100 * bad / (good + bad)
ax.bar(range(3), rate, color=[COL[t] for t in TOPS])
for i in range(3): ax.text(i, rate[i] + .15, f'{bad[i]} of {good[i] + bad[i]}\n({rate[i]:.1f}%)', ha='center', va='bottom', fontsize=9)
xlabels(ax); tidy(ax); ax.set_ylim(0, rate.max() * 1.35); ax.set_ylabel('Shot cases that crashed [%]')
ax.set_title('Shot-case crash rate (LinAlgError)\nqiskit 1.2.4 pools two sweeps; trials are unseeded, counts are small', fontsize=10)
finish(fig, f'{OUT}/06_reliability.png')
print('wrote', sorted(os.listdir(OUT)), {NAME[t]: ok[t] for t in TOPS})
