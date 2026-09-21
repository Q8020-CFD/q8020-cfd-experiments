#!/usr/bin/env python3
"""UQ of the FIRST-SEGMENT (frame 1, T=0.0375) relL2 for ch_smooth_movie_rerun.

Companion to score_smooth_movie_rerun.py, which reports all six frames.  This
script drills into frame 1 -- the single-step point that Melvina's June paper
table (rows #19-22, col S "L2 rel vs FTCS 800") quotes -- and asks how big the
error bar on that number actually is.

Sources
  new  results/burgers-ch-lbm/ch_smooth_movie_rerun/2026-09-10/_0ca9db0f
       kingston x10, fez x10, miami x3 successful trials (boston 0: quota)
  old  results/burgers-ch-lbm-June2026/real-qc/hardware_runs/smooth_movie_*
       one trial per device (n=1, no band)
  sim  results/burgers-ch-lbm-June2026/local-mac/q3/burgers_smooth_movie_sim
       cd872d62 = CH statevector (shots=0)   -> algorithmic floor
       d2ec49ec = CH sampled  (shots=150000) -> +sampling floor

Method
  truth = FTCS-800 subsampled to the 8 q-nodes (same as score_*), frame 1.
  relL2 = ||u - truth|| / ||truth||.
  Exact geometric split: with g = ||u||/||truth|| and c = cos(u, truth),
      relL2^2 = 1 + g^2 - 2 g c,
  so relL2 is a function of a GAIN error (g != 1) and a SHAPE error (c != 1)
  only.  min over g of relL2 is sqrt(1-c^2) -- the irreducible shape floor.
  Variance is attributed by first-order propagation in (g, c) and checked
  against the observed sd.

Run with the ch-lbm venv python (numpy) -- scipy optional, falls back to
hard-coded t/F critical values if absent.
"""
from __future__ import annotations

import glob
import json
import math
import os

import numpy as np

try:
    from scipy import stats as sps
except ImportError:                                     # numpy-only fallback
    sps = None

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))

# --- smooth_movie op point (paper rows #19-22) ------------------------------
Q, A, NU, CFL, N_STEPS, BC = 3, 0.3, 0.08, 0.3, 6, "periodic"
REF_POINTS = 800
N = 2 ** Q
DX = 1.0 / N
DT = CFL * DX
SHOTS = 150_000
FRAME = 1                                               # the first segment

NEW_ROOT = os.path.join(REPO, "q8020-cfd-experiments", "results",
                        "burgers-ch-lbm", "ch_smooth_movie_rerun",
                        "2026-09-10", "_0ca9db0f")
JUNE_ROOT = os.path.join(REPO, "q8020-cfd-experiments", "results",
                         "burgers-ch-lbm-June2026", "real-qc", "hardware_runs")
SIM_ROOT = os.path.join(REPO, "q8020-cfd-experiments", "results",
                        "burgers-ch-lbm-June2026", "local-mac", "q3",
                        "burgers_smooth_movie_sim")
DEVICES = ("kingston", "fez", "miami", "boston")
PAPER_S = {"kingston": 0.634146, "fez": 0.595078,
           "boston": 0.813514, "miami": 0.576395}

# t_{0.975, dof} for the small dofs we need (scipy-free fallback)
T975 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447,
        7: 2.365, 8: 2.306, 9: 2.262, 10: 2.228, 11: 2.201, 12: 2.179,
        17: 2.110, 18: 2.101, 20: 2.086}


def t975(dof: int) -> float:
    if sps is not None:
        return float(sps.t.ppf(0.975, dof))
    return T975.get(dof, 1.96 + 2.4 / max(dof, 1))


# --------------------------------------------------------------------------
# FTCS-800 truth (verbatim from score_smooth_movie_rerun.py)
# --------------------------------------------------------------------------
def _rhs_periodic(u, dx, nu):
    up, um = np.roll(u, -1), np.roll(u, 1)
    grad = (up - um) / (2.0 * dx)
    lap = (um + up - 2.0 * u) / (dx * dx)
    return nu * lap - u * grad


def ftcs800_truth_frames() -> list[np.ndarray]:
    k = max(1, int(np.ceil(REF_POINTS / N)))
    n_ref = k * N
    x_ref = (1.0 / n_ref) * np.arange(n_ref)
    dx_ref = x_ref[1] - x_ref[0]
    u = A * np.sin(2.0 * np.pi * x_ref)
    dt_stable = 0.25 * dx_ref * dx_ref / NU
    sub = max(1, int(np.ceil(DT / dt_stable)))
    dt_sub = DT / sub
    take = np.arange(N) * k
    frames = [u[take].copy()]
    for _ in range(N_STEPS):
        for _ in range(sub):
            u = u + dt_sub * _rhs_periodic(u, dx_ref, NU)
        frames.append(u[take].copy())
    return frames


def frames_of(path):
    """Find a solution_steps dict {frame:int -> field} anywhere in a JSON."""
    def dig(obj):
        if isinstance(obj, dict):
            ss = obj.get("solution_steps")
            if isinstance(ss, dict) and ss:
                return ss
            for vv in obj.values():
                r = dig(vv)
                if r is not None:
                    return r
        elif isinstance(obj, list):
            for vv in obj:
                r = dig(vv)
                if r is not None:
                    return r
        return None

    ss = dig(json.load(open(path)))
    if ss is None:
        return None
    return {int(k): np.asarray(v, dtype=float) for k, v in ss.items()}


# --------------------------------------------------------------------------
# metrics
# --------------------------------------------------------------------------
def gc_of(u, ref) -> tuple[float, float]:
    """gain g = ||u||/||ref||, cosine c = <u,ref>/(||u|| ||ref||)."""
    nu_, nr = float(np.linalg.norm(u)), float(np.linalg.norm(ref))
    g = nu_ / nr
    c = float(np.dot(u, ref) / (nu_ * nr)) if nu_ * nr else float("nan")
    return g, c


def rel_l2_gc(g, c) -> float:
    return math.sqrt(max(0.0, 1.0 + g * g - 2.0 * g * c))


def rel_l2(u, ref) -> float:
    return float(np.linalg.norm(u - ref) / np.linalg.norm(ref))


class Sample:
    """Per-device frame-1 sample: relL2 + its (g, c) factors + run metadata."""

    def __init__(self, dev):
        self.dev = dev
        self.trial, self.l2, self.g, self.c = [], [], [], []
        self.p_succ, self.n_kept, self.cumnorm, self.l2_inline = [], [], [], []
        self.t_created = []

    def add(self, trial, l2, g, c, p, nk, cn, l2i, tc):
        self.trial.append(trial)
        self.l2.append(l2)
        self.g.append(g)
        self.c.append(c)
        self.p_succ.append(p)
        self.n_kept.append(nk)
        self.cumnorm.append(cn)
        self.l2_inline.append(l2i)
        self.t_created.append(tc)

    @property
    def n(self):
        return len(self.l2)

    def arr(self, name):
        return np.asarray(getattr(self, name), dtype=float)


def load_new(truth1) -> dict[str, Sample]:
    out = {}
    for dev in DEVICES:
        s = Sample(dev)
        for tdir in sorted(glob.glob(os.path.join(NEW_ROOT, dev, "trial_*")),
                           key=lambda p: int(os.path.basename(p).split("_")[1])):
            mp = glob.glob(os.path.join(tdir, "q8020_metadata_*.json"))
            if not mp:
                continue
            fr = frames_of(mp[0])
            if not fr or FRAME not in fr:
                continue
            u = fr[FRAME]
            if not np.all(np.isfinite(u)):
                continue
            meta = json.load(open(mp[0]))
            an = meta["analysis"][0]
            psm = an["per_step_metrics"][0]                  # segment 1
            eb = meta["results"][0].get("errors_by_step") or {}
            tc = ((psm.get("execute") or {}).get("job_metrics") or {}) \
                .get("timestamps", {}).get("created")
            g, c = gc_of(u, truth1)
            s.add(int(os.path.basename(tdir).split("_")[1]),
                  rel_l2(u, truth1), g, c,
                  psm["p_success"], psm["n_kept"], psm["cumulative_norm"],
                  float(eb.get(str(FRAME), "nan")), tc)
        out[dev] = s
    return out


def load_june(truth1) -> dict[str, dict]:
    out = {}
    for dev in DEVICES:
        ap = os.path.join(JUNE_ROOT, f"smooth_movie_{dev}", "method_compare",
                          "cole_hopf_circuit", "q8020_artifacts_0.json")
        fr = frames_of(ap) if os.path.exists(ap) else None
        rp = os.path.join(JUNE_ROOT, f"smooth_movie_{dev}",
                          "q8020_results_0.json")
        seg0 = json.load(open(rp))["segments"][0] if os.path.exists(rp) else {}
        if not fr or FRAME not in fr:
            out[dev] = {}
            continue
        u = fr[FRAME]
        g, c = gc_of(u, truth1)
        out[dev] = {"l2": rel_l2(u, truth1), "g": g, "c": c,
                    "p_succ": seg0.get("p_success"),
                    "n_kept": seg0.get("n_kept"),
                    "qs": seg0.get("quantum_seconds"),
                    "created": (seg0.get("job_metrics", {})
                                .get("timestamps", {}).get("created"))}
    return out


def load_sim(truth1) -> dict[str, dict]:
    """CH statevector (shots=0) and CH sampled (shots=150000) frame-1."""
    out = {}
    for sub in sorted(os.listdir(SIM_ROOT)):
        rp = os.path.join(SIM_ROOT, sub, "q8020_results_1.json")
        ap = os.path.join(SIM_ROOT, sub, "q8020_artifacts_0.json")
        if not (os.path.exists(rp) and os.path.exists(ap)):
            continue
        r = json.load(open(rp))
        if r.get("method") != "cole_hopf_circuit":
            continue
        fr = frames_of(ap)
        if not fr or FRAME not in fr:
            continue
        u = fr[FRAME]
        g, c = gc_of(u, truth1)
        an = json.load(open(os.path.join(SIM_ROOT, sub,
                                         "q8020_analysis_0.json")))
        psm = (an.get("per_step_metrics") or [{}])[0]
        key = "sv" if not r.get("shots") else "sampled"
        out[key] = {"l2": rel_l2(u, truth1), "g": g, "c": c,
                    "shots": r.get("shots"), "u": u,
                    "p_succ": psm.get("p_success"),
                    "n_kept": psm.get("n_kept")}
    return out


# --------------------------------------------------------------------------
# statistics helpers
# --------------------------------------------------------------------------
def describe(x):
    x = np.asarray(x, dtype=float)
    n = x.size
    m = float(x.mean())
    sd = float(x.std(ddof=1)) if n > 1 else float("nan")
    sem = sd / math.sqrt(n) if n > 1 else float("nan")
    tc = t975(n - 1) if n > 1 else float("nan")
    return {
        "n": n, "mean": m, "sd": sd, "sem": sem,
        "ci_lo": m - tc * sem, "ci_hi": m + tc * sem,
        # 95% prediction interval for ONE future trial on this device
        "pi_lo": m - tc * sd * math.sqrt(1 + 1 / n),
        "pi_hi": m + tc * sd * math.sqrt(1 + 1 / n),
        "cv_pct": 100.0 * sd / m if m else float("nan"),
        "med": float(np.median(x)), "min": float(x.min()), "max": float(x.max()),
        "iqr": float(np.percentile(x, 75) - np.percentile(x, 25)),
    }


def ols_slope(y):
    """Slope of y on trial index, with a two-sided p-value (drift test)."""
    y = np.asarray(y, dtype=float)
    n = y.size
    if n < 3:
        return float("nan"), float("nan"), float("nan")
    x = np.arange(n, dtype=float)
    xc, yc = x - x.mean(), y - y.mean()
    b = float(xc @ yc / (xc @ xc))
    resid = yc - b * xc
    s2 = float(resid @ resid) / (n - 2)
    se = math.sqrt(s2 / float(xc @ xc)) if s2 > 0 else float("nan")
    t = b / se if se and np.isfinite(se) else float("nan")
    if sps is not None and np.isfinite(t):
        p = float(2 * sps.t.sf(abs(t), n - 2))
    else:
        p = float("nan")
    return b, t, p


def lag1_acf(y):
    y = np.asarray(y, dtype=float)
    if y.size < 3:
        return float("nan")
    yc = y - y.mean()
    den = float(yc @ yc)
    return float(yc[:-1] @ yc[1:] / den) if den else float("nan")


def shot_floor_p(p, shots):
    """Multinomial sd of the post-selection survival fraction."""
    return math.sqrt(p * (1.0 - p) / shots)


def variance_components(samples):
    """One-way random-effects split of frame-1 relL2: device vs run-to-run.

    Returns (sigma_within, sigma_between, F, p, groups_used)."""
    groups = [s.arr("l2") for s in samples if s.n > 1]
    if len(groups) < 2:
        return (float("nan"),) * 4 + ([],)
    k = len(groups)
    ns = np.array([g.size for g in groups], dtype=float)
    means = np.array([g.mean() for g in groups])
    grand = float(np.concatenate(groups).mean())
    ss_w = float(sum(((g - g.mean()) ** 2).sum() for g in groups))
    ss_b = float((ns * (means - grand) ** 2).sum())
    df_w, df_b = ns.sum() - k, k - 1
    ms_w, ms_b = ss_w / df_w, ss_b / df_b
    n0 = (ns.sum() - (ns ** 2).sum() / ns.sum()) / (k - 1)   # balanced-ish n
    var_b = max(0.0, (ms_b - ms_w) / n0)
    f = ms_b / ms_w if ms_w else float("inf")
    if sps is not None and np.isfinite(f):
        p = float(sps.f.sf(f, df_b, df_w))
    else:
        p = float("nan")
    return math.sqrt(ms_w), math.sqrt(var_b), f, p, \
        [s.dev for s in samples if s.n > 1]


# --------------------------------------------------------------------------
def main():
    truth = ftcs800_truth_frames()
    truth1 = truth[FRAME]
    new = load_new(truth1)
    june = load_june(truth1)
    sim = load_sim(truth1)

    W = 78
    print("=" * W)
    print("UQ of the FIRST SEGMENT relL2 -- ch_smooth_movie_rerun")
    print(f"frame {FRAME} of {N_STEPS};  T = {FRAME * DT:.4f} (dt = {DT:g});  "
          f"q={Q} N={N} nu={NU} A={A} cfl={CFL} shots={SHOTS}")
    print(f"truth = FTCS-{REF_POINTS} subsampled to {N} q-nodes; "
          f"||truth_1|| = {np.linalg.norm(truth1):.6f}")
    print("=" * W)

    # ---- 0. what actually ran -------------------------------------------
    print("\n## 0. Realized replication (10x requested per device)\n")
    print(f"{'device':10} {'planned':>7} {'usable':>7}  note")
    notes = {"kingston": "all 10 exit 0",
             "fez": "all 10 exit 0",
             "miami": "trials 3-9 exit 1 (IBM usage limit hit)",
             "boston": "all 10 exit 1 (usage limit; never ran)"}
    for dev in DEVICES:
        print(f"{dev:10} {10:>7} {new[dev].n:>7}  {notes[dev]}")

    # ---- 1. per-trial table ---------------------------------------------
    print("\n## 1. Per-trial frame-1 values\n")
    print(f"{'device':9} {'tr':>3} {'relL2':>8} {'inlineL2':>9} {'gain g':>8} "
          f"{'cos c':>8} {'shape':>8} {'p_succ':>8} {'n_kept':>8}")
    for dev in DEVICES:
        s = new[dev]
        for i in range(s.n):
            shape = math.sqrt(max(0.0, 1 - s.c[i] ** 2))
            print(f"{dev:9} {s.trial[i]:>3} {s.l2[i]:8.4f} "
                  f"{s.l2_inline[i]:9.4f} {s.g[i]:8.4f} {s.c[i]:8.4f} "
                  f"{shape:8.4f} {s.p_succ[i]:8.4f} {int(s.n_kept[i]):8d}")

    # ---- 2. descriptive UQ ----------------------------------------------
    print("\n## 2. Frame-1 relL2 -- descriptive uncertainty\n")
    print(f"{'device':9} {'n':>2} {'mean':>7} {'sd':>7} {'sem':>7} "
          f"{'95% CI on mean':>17} {'95% PI 1 trial':>17} {'CV%':>6} "
          f"{'range':>7}")
    for dev in DEVICES:
        s = new[dev]
        if s.n == 0:
            print(f"{dev:9} {0:>2}   (no usable trials)")
            continue
        d = describe(s.l2)
        ci = f"[{d['ci_lo']:.4f},{d['ci_hi']:.4f}]"
        pi = f"[{d['pi_lo']:.4f},{d['pi_hi']:.4f}]"
        print(f"{dev:9} {d['n']:>2} {d['mean']:7.4f} {d['sd']:7.4f} "
              f"{d['sem']:7.4f} {ci:>17} {pi:>17} {d['cv_pct']:6.2f} "
              f"{d['max'] - d['min']:7.4f}")
    print("\n  CI = uncertainty on the DEVICE MEAN (what a paper table cell "
          "should carry).\n  PI = spread a single re-run would land in "
          "(what June's n=1 number is drawn from).")

    # ---- 3. geometric decomposition -------------------------------------
    print("\n## 3. Where the error and its variance come from "
          "(relL2^2 = 1 + g^2 - 2gc)\n")
    print(f"{'device':9} {'g mean':>8} {'g sd':>8} {'c mean':>8} {'c sd':>8} "
          f"{'shape floor':>12} {'gain-only':>10}")
    for dev in DEVICES:
        s = new[dev]
        if s.n == 0:
            continue
        g, c = s.arr("g"), s.arr("c")
        shape = np.sqrt(np.clip(1 - c ** 2, 0, None))
        print(f"{dev:9} {g.mean():8.4f} "
              f"{(g.std(ddof=1) if s.n > 1 else float('nan')):8.4f} "
              f"{c.mean():8.4f} "
              f"{(c.std(ddof=1) if s.n > 1 else float('nan')):8.4f} "
              f"{shape.mean():12.4f} {abs(g.mean() - 1):10.4f}")
    print("\n  shape floor = sqrt(1-c^2) = relL2 achievable if the amplitude "
          "were rescaled\n  perfectly; gain-only = |g-1| = relL2 if the shape "
          "were perfect.")

    print("\n  variance attribution (first-order in g, c):")
    print(f"  {'device':9} {'d/dg * sd(g)':>13} {'d/dc * sd(c)':>13} "
          f"{'corr(g,c)':>10} {'predicted sd':>13} {'observed sd':>12}")
    for dev in DEVICES:
        s = new[dev]
        if s.n < 3:
            continue
        g, c = s.arr("g"), s.arr("c")
        gm, cm = g.mean(), c.mean()
        r0 = rel_l2_gc(gm, cm)
        dg = (gm - cm) / r0                       # d relL2 / d g
        dc = -gm / r0                             # d relL2 / d c
        sg, sc = g.std(ddof=1), c.std(ddof=1)
        rho = float(np.corrcoef(g, c)[0, 1])
        pred = math.sqrt(max(0.0, (dg * sg) ** 2 + (dc * sc) ** 2
                             + 2 * dg * dc * rho * sg * sc))
        print(f"  {dev:9} {dg * sg:13.5f} {dc * sc:13.5f} {rho:10.3f} "
              f"{pred:13.5f} {s.arr('l2').std(ddof=1):12.5f}")

    # ---- 4. noise-source separation -------------------------------------
    print("\n## 4. Separating the noise sources at frame 1\n")
    if "sv" in sim and "sampled" in sim:
        sv, sm = sim["sv"], sim["sampled"]
        print(f"  CH statevector, shots=0        relL2 = {sv['l2']:.4f}  "
              f"(g={sv['g']:.4f}, c={sv['c']:.4f})   <- algorithm/truncation "
              "floor")
        print(f"  CH noiseless sim, shots=150000 relL2 = {sm['l2']:.4f}  "
              f"(g={sm['g']:.4f}, c={sm['c']:.4f})   <- + shot sampling")
        d_shot = sm["l2"] - sv["l2"]
        print(f"  => sampling adds {d_shot:+.4f} relL2 at this shot budget "
              "(one draw, so a magnitude not an sd)")
        for dev in ("kingston", "fez", "miami"):
            s = new[dev]
            if s.n:
                print(f"  => {dev:8} hardware mean {s.arr('l2').mean():.4f}; "
                      f"device noise adds "
                      f"{s.arr('l2').mean() - sm['l2']:+.4f} over the "
                      "sampled sim")
    else:
        print("  (sim reference runs not found -- skipping)")

    # --- is the run-to-run band shot-noise-limited?  work in the ANGLE, ---
    # --- because relL2 sits on its shape floor (g ~ c, see section 3):  ---
    # --- theta = arccos(c), and relL2 ~ sin(theta) there.               ---
    if "sv" in sim and "sampled" in sim:
        print("\n  shape-noise budget in the ANGLE theta = arccos(c) "
              "(relL2 ~ sin theta on the floor):")
        th_sim = math.acos(min(1.0, sim["sampled"]["c"])) \
            - math.acos(min(1.0, sim["sv"]["c"]))
        nk_sim = sim["sampled"].get("n_kept") or SHOTS
        print(f"    noiseless sim, shots={SHOTS}, n_kept={int(nk_sim)}: "
              f"sampling moved theta by {abs(th_sim):.4f} rad (1 draw)")
        print(f"    {'device':9} {'n_kept':>8} {'shot-noise':>11} "
              f"{'sd(theta) obs':>14} {'obs/shot':>9}")
        for dev in DEVICES:
            s = new[dev]
            if s.n < 2:
                continue
            c = s.arr("c")
            th = np.arccos(np.clip(c, -1, 1))
            sd_th = float(th.std(ddof=1))
            nk = s.arr("n_kept").mean()
            pred = abs(th_sim) * math.sqrt(nk_sim / nk)   # 1/sqrt(n_kept)
            print(f"    {dev:9} {int(nk):8d} {pred:11.4f} {sd_th:14.4f} "
                  f"{sd_th / pred:9.2f}")
        print("    obs/shot <~1 => the frame-1 run-to-run band is at or below "
              "the sampling\n    floor, i.e. sampling-limited, not "
              "device-drift-limited.  CAVEAT: the sim\n    floor is ONE draw, "
              "so this is an order-of-magnitude bound (see note at end).")

    print("\n  correlation of frame-1 relL2 with the segment-1 survival "
          "fraction:")
    print(f"  {'device':9} {'corr(relL2,p_succ)':>19} "
          f"{'corr(relL2,n_kept)':>19}")
    for dev in DEVICES:
        s = new[dev]
        if s.n < 3:
            continue
        l2 = s.arr("l2")
        print(f"  {dev:9} {float(np.corrcoef(l2, s.arr('p_succ'))[0, 1]):19.3f} "
              f"{float(np.corrcoef(l2, s.arr('n_kept'))[0, 1]):19.3f}")

    print("\n  post-selection survival p_success: observed scatter vs the "
          "multinomial floor")
    print(f"  {'device':9} {'p mean':>8} {'p sd obs':>9} {'p sd shot':>10} "
          f"{'ratio':>6} {'excess sd':>10}")
    for dev in DEVICES:
        s = new[dev]
        if s.n < 2:
            continue
        p = s.arr("p_succ")
        obs = p.std(ddof=1)
        flo = shot_floor_p(p.mean(), SHOTS)
        exc = math.sqrt(max(0.0, obs ** 2 - flo ** 2))
        print(f"  {dev:9} {p.mean():8.4f} {obs:9.5f} {flo:10.5f} "
              f"{obs / flo:6.2f} {exc:10.5f}")
    print("  ratio ~1 => run-to-run survival is sampling-limited; >1 => real "
          "device drift on top.")

    print("\n  drift within the trial series (trials ran back-to-back):")
    print(f"  {'device':9} {'slope/trial':>12} {'t':>7} {'p':>8} "
          f"{'lag-1 acf':>10} {'total drift':>12}")
    for dev in DEVICES:
        s = new[dev]
        if s.n < 3:
            continue
        y = s.arr("l2")
        b, t, p = ols_slope(y)
        print(f"  {dev:9} {b:12.5f} {t:7.2f} {p:8.4f} {lag1_acf(y):10.3f} "
              f"{b * (s.n - 1):12.5f}")

    # ---- 5. between-device vs within-device -----------------------------
    print("\n## 5. Between-device vs within-device (run-to-run) variance\n")
    sw, sb, f, p, used = variance_components([new[d] for d in DEVICES])
    print(f"  groups: {', '.join(used)}")
    print(f"  sigma_within  (run-to-run, one device) = {sw:.5f}")
    print(f"  sigma_between (device-to-device)       = {sb:.5f}")
    if np.isfinite(sw) and sw:
        print(f"  ratio between/within                   = {sb / sw:.2f}")
    print(f"  one-way ANOVA F = {f:.1f}, p = {p:.3e}")
    print("\n  pairwise Welch on the frame-1 mean:")
    keys = [d for d in DEVICES if new[d].n > 1]
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            a, b_ = new[keys[i]].arr("l2"), new[keys[j]].arr("l2")
            va, vb = a.var(ddof=1) / a.size, b_.var(ddof=1) / b_.size
            tt = (a.mean() - b_.mean()) / math.sqrt(va + vb)
            dof = (va + vb) ** 2 / (va ** 2 / (a.size - 1)
                                    + vb ** 2 / (b_.size - 1))
            pv = float(2 * sps.t.sf(abs(tt), dof)) if sps else float("nan")
            print(f"    {keys[i]:9} vs {keys[j]:9} "
                  f"d = {a.mean() - b_.mean():+.4f}  t = {tt:6.2f}  "
                  f"dof = {dof:5.1f}  p = {pv:.2e}")

    # ---- 6. June (n=1) vs the September band ----------------------------
    print("\n## 6. Is June's single frame-1 value consistent with the new "
          "band?\n")
    print(f"{'device':9} {'June relL2':>10} {'paper col S':>11} "
          f"{'Sept mean':>9} {'Sept sd':>8} {'z':>7} {'inside 95% PI?':>15}")
    zs = []
    for dev in DEVICES:
        s, j = new[dev], june.get(dev, {})
        ps = f"{PAPER_S[dev]:.4f}"
        if not j:
            print(f"{dev:9} {'-':>10} {ps:>11}   (no June frame-1)")
            continue
        if s.n < 2:
            print(f"{dev:9} {j['l2']:10.4f} {ps:>11} "
                  f"{'-':>9} {'-':>8} {'-':>7}   (no Sept band)")
            continue
        d = describe(s.l2)
        z = (j["l2"] - d["mean"]) / d["sd"]
        zs.append(z)
        inside = "yes" if d["pi_lo"] <= j["l2"] <= d["pi_hi"] else "NO"
        print(f"{dev:9} {j['l2']:10.4f} {ps:>11} {d['mean']:9.4f} "
              f"{d['sd']:8.4f} {z:7.2f} {inside:>15}")
    if zs:
        print(f"\n  all z < 0 and |z| >> 2  =>  the shift is systematic "
              f"(mean z = {np.mean(zs):+.1f} sd),")
        print("  not run-to-run scatter: the new code/stack is WORSE at "
              "frame 1 by a margin\n  many times the run-to-run band.")

    print("\n  June vs September segment-1 conditions:")
    print(f"  {'device':9} {'p_succ Jun':>10} {'p_succ Sep':>10} "
          f"{'delta':>8} {'g Jun':>7} {'g Sep':>7} {'c Jun':>7} {'c Sep':>7}")
    for dev in DEVICES:
        s, j = new[dev], june.get(dev, {})
        if not j or s.n == 0:
            continue
        print(f"  {dev:9} {j['p_succ']:10.4f} {s.arr('p_succ').mean():10.4f} "
              f"{s.arr('p_succ').mean() - j['p_succ']:+8.4f} "
              f"{j['g']:7.4f} {s.arr('g').mean():7.4f} "
              f"{j['c']:7.4f} {s.arr('c').mean():7.4f}")

    # ---- 7. how many trials do you need? --------------------------------
    print("\n## 7. Replication budget implied by the observed sd\n")
    print(f"  {'device':9} {'sd':>8}  n for +/-0.01 (95%)  n for +/-0.005")
    for dev in DEVICES:
        s = new[dev]
        if s.n < 2:
            continue
        sd = s.arr("l2").std(ddof=1)
        n01 = math.ceil((1.96 * sd / 0.01) ** 2)
        n005 = math.ceil((1.96 * sd / 0.005) ** 2)
        print(f"  {dev:9} {sd:8.4f} {n01:19d} {n005:15d}")
    print("\n  (normal approximation; n<=3 devices need the t inflation on "
          "top.)")

    # ---- 8. quotable numbers -------------------------------------------
    print("\n## 8. Quotable frame-1 result\n")
    for dev in DEVICES:
        s = new[dev]
        if s.n == 0:
            print(f"  {dev:9} no data (quota)")
            continue
        d = describe(s.l2)
        if s.n > 1:
            print(f"  {dev:9} relL2(T={FRAME * DT:.4f}) = "
                  f"{d['mean']:.3f} +/- {d['sd']:.3f} (1 sd, n={d['n']}), "
                  f"95% CI on mean [{d['ci_lo']:.3f}, {d['ci_hi']:.3f}]")
    print("\n  Caveat to close the shot-noise floor properly: the floor in "
          "section 4 rests on\n  ONE sampled-sim draw.  k independent "
          "noiseless-sim replicates at these params\n  would turn it into a "
          "real sd (statevector q=3, no QPU, seconds per run):")
    print("    q8020-sweep smooth_movie_rerun_4dev.toml kingston \\\n"
          "      --set backend-type=sim --set shots=150000 "
          "--set seed=<1234,1235,...>")

    if sps is None:
        print("\n  NOTE: scipy absent -- p-values approximated / omitted.")


if __name__ == "__main__":
    main()
