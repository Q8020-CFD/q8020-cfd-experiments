"""Build a tidy per-case table for every run under nov2025-rerun.

Usage: python load_runs.py <nov2025-rerun dir> <out.csv>
One row per case directory (a dir holding residual_*.csv). Works from the raw
case files so the file-only LuGo-rerun (no q8020 metadata) is covered too.
"""
import csv, glob, json, math, os, re, sys

ROOT = os.path.abspath(sys.argv[1]); OUT = sys.argv[2]
# run label -> (code family, stack)
FAMILY = {
    'nov_pkgs': ('HHL', 'qiskit 1.2.4 (nov pkgs)'),
    'new_pkgs': ('HHL', 'qiskit 2.5.2 (new pkgs)'),
    'latest_pkgs': ('HHL', 'qiskit 2.6.2 (latest pkgs)'),
    'LuGo-rerun': ('HHL+LuGo', 'LuGo'),
    'sqls_aiaa4q26': ('SQLS', 'sqls aiaa4q26'),
}
SENTINEL_TOL = 1e-10


def read_csv(path):
    with open(path) as f:
        return list(csv.DictReader(f, skipinitialspace=True))


def fnum(x):
    try: return float(x)
    except (TypeError, ValueError): return math.nan


def first(case, pat):
    g = sorted(glob.glob(os.path.join(case, pat)))
    return g[0] if g else None


def load_meta(case):
    g = glob.glob(os.path.join(case, 'q8020_metadata_*.json'))
    if not g: return None
    d = json.load(open(g[0]))
    ex = [x for x in d.get('exec_stats', []) if 'success' in x]
    return ex[0] if ex else None


def shots_of(case):
    pa = os.path.join(case, 'pipeline_args.json')
    if os.path.exists(pa):
        cmd = ' '.join(json.load(open(pa)).get('cmd', []))
        m = re.search(r'-shots\s+(\d+)', cmd)
        if m: return int(m.group(1))
    m = re.search(r'shots_?(\d+)', ' '.join(os.listdir(case)) + ' ' + case)
    return int(m.group(1)) if m else 0


def nelem_of(case):
    m = re.search(r'nelem(\d+)', ' '.join(os.listdir(case)))
    return int(m.group(1)) if m else None


def mach_final(case):
    f = first(case, 'final_results_*.csv')
    return [fnum(r['Mach']) for r in read_csv(f)] if f else []


def sums(rows, key):
    v = [fnum(r.get(key)) for r in rows]
    v = [x for x in v if not math.isnan(x)]
    return (sum(v), max(v)) if v else (math.nan, math.nan)


rows = []
for rf in glob.glob(os.path.join(ROOT, '**', 'residual_*.csv'), recursive=True):
    case = os.path.dirname(rf); rel = os.path.relpath(case, ROOT).split(os.sep)
    top = rel[0]
    if top not in FAMILY or 'analysis' in rel: continue
    fam, stack = FAMILY[top]
    run = '/'.join(rel[1:3]) if top != 'LuGo-rerun' else 'LuGo'
    res = read_csv(rf)
    meta = load_meta(case)
    qf = first(case, 'qc_metadata_*.csv')
    qc = read_csv(qf) if qf else []
    hf = first(case, 'hhl_metrics_*.csv')
    hm = read_csv(hf) if hf else []
    steps = len(res)
    r_first = fnum(res[0]['residual_total']); r_last = fnum(res[-1]['residual_total'])
    shots = shots_of(case)
    row = dict(family=fam, stack=stack, top=top, run=run, case_dir=os.path.relpath(case, ROOT),
               nelem=nelem_of(case), shots=shots,
               exit_ok=(meta['success'] if meta else None),
               wall_s=(meta['duration_seconds'] if meta else math.nan),
               steps=steps, res_first=r_first, res_final=r_last,
               res_reduction=r_last / r_first if r_first else math.nan,
               converged=int(steps < 15 and r_last < 1e-6),
               mach=json.dumps(mach_final(case)))
    if hm:  # first-step linear-solve quality
        row['step0_l2_rel'] = fnum(hm[0].get('l2_error_rel'))
        row['mean_l2_rel'] = sum(fnum(h.get('l2_error_rel')) for h in hm) / len(hm)
        row['step0_fidelity'] = fnum(hm[0].get('fidelity'))
    if qc and 'circ_transpile_time' in qc[0]:  # HHL circuit metrics
        for k, out in (('circ_transpile_time', 'transpile_s'), ('circ_generate_time', 'generate_s'),
                       ('circ_run_time', 'circ_run_s'), ('circ_depth_transpile', 'depth_tp'),
                       ('circ_gates_transpile', 'gates_tp')):
            s, m = sums(qc, k); row[out] = s if k.endswith('time') else math.nan
            if not k.endswith('time'): row[out + '_max'] = m; row[out + '_sum'] = s
        row['depth_tp_step0'] = fnum(qc[0]['circ_depth_transpile'])
        row['cond'] = fnum(qc[0]['condition_number'])
    elif qc:  # SQLS
        row['sqls_solve_s'] = sums(qc, 'solve_time')[0]
        row['sqls_tcount_s'] = sums(qc, 't_count_s')[0]
        row['depth_tp_step0'] = fnum(qc[0].get('fb_depth'))
        row['cx_step0'] = fnum(qc[0].get('fb_cx_count'))
    rows.append(row)

# reference Mach per nelem: the HHL exact case from nov_pkgs (fallback LuGo exact)
ref = {}
for pref in ('nov_pkgs', 'LuGo-rerun'):
    for r in rows:
        if r['top'] == pref and r['shots'] == 0 and r['nelem'] not in ref and json.loads(r['mach']):
            ref[r['nelem']] = json.loads(r['mach'])
for r in rows:
    m = json.loads(r['mach']); b = ref.get(r['nelem'])
    r['mach_relL2'] = (math.sqrt(sum((x - y) ** 2 for x, y in zip(m, b)) / sum(y * y for y in b))
                       if m and b and len(m) == len(b) else math.nan)
    del r['mach']
keys = sorted({k for r in rows for k in r}, key=lambda k: (k not in ('family', 'stack', 'run', 'nelem', 'shots'), k))
rows.sort(key=lambda r: (r['family'], r['run'], r['nelem'] or 0, r['shots'], r['case_dir']))
with open(OUT, 'w', newline='') as f:
    w = csv.DictWriter(f, keys); w.writeheader(); w.writerows(rows)
print(len(rows), 'cases ->', OUT)
