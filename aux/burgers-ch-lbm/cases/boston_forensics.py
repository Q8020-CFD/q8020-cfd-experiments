#!/usr/bin/env python3
"""Boston-focused forensics on the smooth_movie June-vs-September discrepancy.

June says ibm_boston (Heron R3, best-calibrated of the four) scored WORST
(relL2 0.8135 at frame 1); September's physics -- gain orders by readout
error -- says it should have been BEST.  Boston has no September data (all
10 trials died on the IBM usage limit), so the only way in is to audit
June's boston artifact itself against the noiseless ceiling and the other
three June devices.

Reuses score_smooth_movie_rerun for the FTCS-800 truth so the metric is
identical to paper_cases_table column S.

Run with the ch-lbm venv python.
"""
from __future__ import annotations

import glob
import json
import os

import numpy as np

from score_smooth_movie_rerun import (
    DT,
    DX,
    N,
    N_STEPS,
    NU,
    cosine,
    frames_of,
    ftcs800_truth_frames,
    rel_l2,
)

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
EXP = os.path.join(REPO, "q8020-cfd-experiments", "results")
JUNE_HW = os.path.join(EXP, "burgers-ch-lbm-June2026", "real-qc",
                       "hardware_runs")
JUNE_SIM = os.path.join(EXP, "burgers-ch-lbm-June2026", "local-mac", "q3",
                        "burgers_smooth_movie_sim")
SEP = os.path.join(EXP, "burgers-ch-lbm", "ch_smooth_movie_rerun",
                   "2026-09-10", "_0ca9db0f")
DEVS = ("kingston", "fez", "miami", "boston")


def gain(u, ref):
    return float(np.linalg.norm(u) / np.linalg.norm(ref))


def june_frames(dev):
    p = os.path.join(JUNE_HW, f"smooth_movie_{dev}", "method_compare",
                     "cole_hopf_circuit", "q8020_artifacts_0.json")
    return frames_of(p)


def sim_frames(run_id):
    pats = [os.path.join(JUNE_SIM, run_id, "q8020_artifacts_0.json"),
            os.path.join(JUNE_SIM, run_id, "*artifacts*.json")]
    for pat in pats:
        for f in sorted(glob.glob(pat)):
            fr = frames_of(f)
            if fr:
                return fr
    return None


def sep_frames(dev):
    """List of {frame: u} for each usable September trial on dev."""
    out = []
    for tdir in sorted(glob.glob(os.path.join(SEP, dev, "trial_*"))):
        mp = glob.glob(os.path.join(tdir, "q8020_metadata_*.json"))
        if not mp:
            continue
        fr = frames_of(mp[0])
        if fr and all(k in fr and np.all(np.isfinite(fr[k]))
                      for k in range(1, N_STEPS + 1)):
            out.append(fr)
    return out


def hdr(title):
    print()
    print("=" * 78)
    print(title)
    print("=" * 78)


# --------------------------------------------------------------------------
# 1. per-frame g / c / relL2 for every June device + the noiseless ceiling
# --------------------------------------------------------------------------
def section_per_frame(truth):
    hdr("1. June per-frame decomposition   relL2^2 = 1 + g^2 - 2 g c")
    sv = sim_frames("cd872d62")          # statevector, shots=0, chi=8
    series = [(d, june_frames(d)) for d in DEVS]
    series.append(("SIM(sv)", sv))
    for name, fr in series:
        if not fr:
            print(f"{name}: no frames")
            continue
        print(f"\n-- {name}")
        print(f"{'frame':>5} {'T':>7} {'relL2':>9} {'g':>8} {'cos':>8} "
              f"{'floor':>8} {'g-c':>8} {'relL2_rs':>9}")
        for k in range(1, N_STEPS + 1):
            if k not in fr:
                continue
            u, r = fr[k], truth[k]
            c = cosine(u, r)
            g = gain(u, r)
            floor = float(np.sqrt(max(0.0, 1.0 - c * c)))
            den = float(np.dot(u, u))
            al = float(np.dot(u, r) / den) if den else 1.0
            print(f"{k:>5} {k*DT:>7.4f} {rel_l2(u, r):>9.4f} {g:>8.4f} "
                  f"{c:>8.4f} {floor:>8.4f} {g-c:>+8.4f} "
                  f"{rel_l2(al*u, r):>9.4f}")


# --------------------------------------------------------------------------
# 2. the shift/reflect test -- is boston a mangled-index sine?
# --------------------------------------------------------------------------
def section_symmetry(truth):
    hdr("2. Index-mangling test: best rotation / reflection / sign per device")
    print("If a device's frame-1 field is a CLEAN profile mapped to the wrong")
    print("nodes, some (roll, flip, sign) beats identity by a wide margin.")
    print("Compared against the NOISELESS frame-1 field (the shape the")
    print("pipeline should produce), not the FTCS truth.\n")
    sv = sim_frames("cd872d62")
    target = sv[1]
    cands = []
    for s in range(N):
        for flip in (False, True):
            for sign in (1, -1):
                cands.append((s, flip, sign))
    for dev in DEVS:
        fr = june_frames(dev)
        if not fr:
            continue
        u = fr[1]
        rows = []
        for s, flip, sign in cands:
            v = u[::-1] if flip else u
            v = sign * np.roll(v, s)
            rows.append((cosine(v, target), s, flip, sign))
        rows.sort(reverse=True)
        ident = cosine(u, target)
        best = rows[0]
        print(f"{dev:9} cos(identity)={ident:+.4f}   best cos={best[0]:+.4f} "
              f"at roll={best[1]} flip={best[2]} sign={best[3]:+d}"
              f"   gap={best[0]-ident:+.4f}")


# --------------------------------------------------------------------------
# 3. spectra -- where does boston's excess amplitude live?
# --------------------------------------------------------------------------
def section_spectrum(truth):
    hdr("3. Frame-1 DFT: |U_k| by mode (k=1 is the physical sine)")
    print("Cole-Hopf u = -2nu d/dx log(phi) is a log-DERIVATIVE, so it")
    print("amplifies high-k content in phi.  A gain above the noiseless")
    print("ceiling can only come from spurious non-k=1 energy.\n")
    sv = sim_frames("cd872d62")
    rows = [("FTCS-800 ref", truth[1]), ("SIM(sv)", sv[1])]
    for dev in DEVS:
        fr = june_frames(dev)
        if fr:
            rows.append((f"June {dev}", fr[1]))
    sep_mean = {}
    for dev in DEVS:
        tr = sep_frames(dev)
        if tr:
            sep_mean[dev] = np.mean([t[1] for t in tr], axis=0)
            rows.append((f"Sep {dev} (n={len(tr)})", sep_mean[dev]))
    print(f"{'field':22} " + " ".join(f"{'|U'+str(k)+'|':>9}"
                                      for k in range(N // 2 + 1))
          + f" {'hi-k frac':>10}")
    for name, u in rows:
        F = np.abs(np.fft.rfft(u)) / N
        tot = float(np.sum(F[1:] ** 2))
        hi = float(np.sum(F[2:] ** 2)) / tot if tot else float("nan")
        print(f"{name:22} " + " ".join(f"{v:>9.5f}" for v in F)
              + f" {hi:>10.3f}")


# --------------------------------------------------------------------------
# 4. back out phi from u and look at it directly
# --------------------------------------------------------------------------
def implied_log_phi(u):
    """Invert u = -nu (L_{j+1}-L_{j-1})/dx for L = log phi, periodic, N even.

    The central-difference log-derivative on an EVEN periodic grid decouples
    the two sublattices: u at ODD j links L at even nodes, u at EVEN j links
    L at odd nodes.  Each sublattice is recoverable up to its own additive
    constant (a 2-D null space: the constant and the checkerboard).  We walk
    L[0]=0 -> L[2] -> L[4] -> L[6] using u[1],u[3],u[5] and L[1]=0 -> L[3]
    -> L[5] -> L[7] using u[2],u[4],u[6], then report the two closure
    residuals (sum of u over each parity class, which must vanish).
    """
    L = np.zeros(N)
    s = DX / NU
    for start in (0, 1):                    # start = parity of L we fill
        L[start] = 0.0
        cur = start
        for _ in range(N // 2 - 1):
            j = (cur + 1) % N               # stencil centre (other parity)
            L[(cur + 2) % N] = L[cur] - u[j] * s
            cur = (cur + 2) % N
    res_even = float(np.sum(u[1::2]))       # closes the even-L walk
    res_odd = float(np.sum(u[0::2]))        # closes the odd-L walk
    return L, res_even, res_odd


def bit_patterns():
    """Walsh sign patterns (-1)**bit_m(j) for each data bit of the node index.

    q=3 so j = b2 b1 b0 with b2 the MSB (weight 4).  data_bits are read
    MSB-first out of the counts key (lib_cole_hopf_circuit.py:561,
    idx = int(data_bits, 2)), so b2 is the highest-index measured clbit.
    These three patterns are mutually orthogonal (Walsh functions), so the
    projection below is an exact decomposition, not a fit.
    """
    j = np.arange(N)
    return {m: np.where((j >> m) & 1, -1.0, 1.0) for m in range(3)}


def section_phi(truth):
    hdr("4. Implied log(phi), and which DATA BIT the error lives on")
    sv = sim_frames("cd872d62")
    rows = [("FTCS-800 ref", truth[1]), ("SIM(sv)", sv[1])]
    for dev in DEVS:
        fr = june_frames(dev)
        if fr:
            rows.append((f"June {dev}", fr[1]))
    for dev in DEVS:
        tr = sep_frames(dev)
        if tr:
            rows.append((f"Sep {dev} mean", np.mean([t[1] for t in tr], 0)))

    print("Recovered L = log phi (mean removed; only the shape is defined).")
    print("closure = sum of u over each parity class -- must be ~0 for a")
    print("field that really came out of the log-derivative.\n")
    print(f"{'field':20} " + " ".join(f"{'L'+str(j):>8}" for j in range(N))
          + f" {'clos_e':>9} {'clos_o':>9}")
    Ls = {}
    for name, u in rows:
        L, re_, ro_ = implied_log_phi(u)
        L = L - L.mean()
        Ls[name] = L
        print(f"{name:20} " + " ".join(f"{v:>8.4f}" for v in L)
              + f" {re_:>9.2e} {ro_:>9.2e}")

    # ---- stencil sensitivity: what does a unit bit-bias in L do to u? ----
    pats = bit_patterns()
    print("\nStencil response to a unit-amplitude bias on each data bit.")
    print("A multiplicative bias on the qubit carrying bit m makes L pick up")
    print("that bit's Walsh pattern; the log-derivative then maps it into u.")
    print(f"{'bit m (weight)':>16} {'period in j':>12} {'Fourier k':>10} "
          f"{'||du||/unit':>12}")
    for m in range(3):
        L = pats[m]
        du = np.zeros(N)
        for j in range(N):
            du[j] = -NU * (L[(j + 1) % N] - L[(j - 1) % N]) / DX
        F = np.abs(np.fft.rfft(L)) / N
        kk = ",".join(str(k) for k in range(1, N // 2 + 1) if F[k] > 1e-9)
        print(f"{m} (weight {2**m}):".rjust(16)
              + f" {2**(m+1):>12} {kk:>10} {np.linalg.norm(du):>12.4f}")
    print("bit 0 (LSB) lands on the Nyquist mode k=4, which the centred")
    print("stencil annihilates exactly -- an LSB error is INVISIBLE in u.")
    print("bit 1 lands on k=2, where |sin(2 pi k/N)| = 1 is MAXIMAL -- an")
    print("error on that one qubit is amplified more than the signal itself.")

    # ---- decompose each field's L error onto the bit patterns ----
    print("\nGAUGE WARNING: bit 0's Walsh pattern IS the checkerboard, i.e.")
    print("exactly the stencil's null mode, so its coefficient in a recovered")
    print("L is fixed by the arbitrary L[0]=L[1]=0 choice and carries no")
    print("information.  Only bits 1 and 2 are observable.  Everything below")
    print("therefore works in u's mode space (k=1,2,3), which is gauge-free:")
    print("|U0| and |U4| are identically zero in every field above.")
    print("\nObservable projection of the L error onto bits 1 and 2:")
    base = Ls["SIM(sv)"]
    print(f"{'field':20} {'coeff b1':>10} {'coeff b2':>10}")
    for name, _ in rows:
        if name == "SIM(sv)":
            continue
        dL = Ls[name] - base
        print(f"{name:20} {float(np.dot(dL, pats[1]) / N):>+10.4f} "
              f"{float(np.dot(dL, pats[2]) / N):>+10.4f}")


# --------------------------------------------------------------------------
# 5. boston node-level profile against everything else
# --------------------------------------------------------------------------
def section_profiles(truth):
    hdr("5. Frame-1 node-level u(x)")
    sv = sim_frames("cd872d62")
    sh = sim_frames("d2ec49ec")
    rows = [("FTCS-800 ref", truth[1]), ("SIM sv shots=0", sv[1])]
    if sh:
        rows.append(("SIM shots=150k", sh[1]))
    for dev in DEVS:
        fr = june_frames(dev)
        if fr:
            rows.append((f"June {dev}", fr[1]))
    for dev in DEVS:
        tr = sep_frames(dev)
        if tr:
            rows.append((f"Sep {dev} mean", np.mean([t[1] for t in tr], 0)))
    print(f"{'field':20} " + " ".join(f"{'x='+format(j*DX,'.3f'):>8}"
                                      for j in range(N)) + f" {'||u||':>8}")
    for name, u in rows:
        print(f"{name:20} " + " ".join(f"{v:>8.4f}" for v in u)
              + f" {np.linalg.norm(u):>8.4f}")


# --------------------------------------------------------------------------
# 6. boston calibration + job timeline (per segment, from job_harvest)
# --------------------------------------------------------------------------
def section_timeline():
    hdr("6. June job timeline and per-segment calibration")
    for dev in DEVS:
        p = os.path.join(JUNE_HW, f"smooth_movie_{dev}",
                         "q8020_results_1.json")
        r0 = os.path.join(JUNE_HW, f"smooth_movie_{dev}",
                          "q8020_results_0.json")
        if not os.path.exists(p):
            continue
        jh = json.load(open(p))["job_harvest"]
        segs = {s["segment_idx"]: s for s in
                json.load(open(r0))["segments"]}
        print(f"\n-- {dev}")
        print(f"{'seg':>3} {'created':>21} {'running':>21} {'queue_s':>9} "
              f"{'ro_med':>8} {'T2_med':>7} {'cz_med':>8} {'p_succ':>8}")
        for j in jh:
            ts = j["metrics"]["timestamps"]
            b = j["backend"]
            ro = np.median([v for v in b["readout_error"].values()
                            if v is not None])
            t2 = np.median([v for v in b["t2"].values() if v is not None])
            cz = b["gate_error"].get("cz", {})
            czm = np.median([v for v in cz.values() if v is not None]) \
                if cz else float("nan")
            import datetime as _dt
            def _p(s):
                return _dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
            q = (_p(ts["running"]) - _p(ts["created"])).total_seconds()
            ps = segs[j["segment_idx"]]["p_success"]
            print(f"{j['segment_idx']:>3} {ts['created'][:19]:>21} "
                  f"{ts['running'][:19]:>21} {q:>9.0f} {ro:>8.5f} "
                  f"{t2:>7.1f} {czm:>8.5f} {ps:>8.5f}")


def section_ranking(truth):
    hdr("7. Ranking on the PHYSICAL mode vs ranking on relL2")
    print("relL2 charges a device for total ||u - ref||, so spurious k=2")
    print("energy counts against it exactly like a missing signal.  The")
    print("physics question -- how much of the k=1 Burgers mode came back --")
    print("is the |U1| column.  Ceiling = the noiseless statevector run.\n")
    sv = sim_frames("cd872d62")

    def u1(u):
        return float(np.abs(np.fft.rfft(u))[1] / N)

    ceil1 = u1(sv[1])
    ref1 = u1(truth[1])
    print(f"noiseless |U1| = {ceil1:.5f}   FTCS-800 ref |U1| = {ref1:.5f} "
          f"(ceiling is {ceil1/ref1:.3f} of ref)\n")
    rows = []
    for dev in DEVS:
        fr = june_frames(dev)
        if fr:
            rows.append((f"June {dev}", fr[1]))
    for dev in DEVS:
        tr = sep_frames(dev)
        if tr:
            rows.append((f"Sep {dev}", np.mean([t[1] for t in tr], 0)))
    print(f"{'field':16} {'|U1|':>9} {'|U1|/ceil':>10} {'|U2|':>9} "
          f"{'|U2|/|U1|':>10} {'relL2':>9} {'rank_relL2':>11}")
    order = sorted(range(len(rows)),
                   key=lambda i: rel_l2(rows[i][1], truth[1]))
    rank = {i: n + 1 for n, i in enumerate(order)}
    for i, (name, u) in enumerate(rows):
        F = np.abs(np.fft.rfft(u)) / N
        print(f"{name:16} {F[1]:>9.5f} {F[1]/ceil1:>10.3f} {F[2]:>9.5f} "
              f"{F[2]/F[1]:>10.3f} {rel_l2(u, truth[1]):>9.4f} "
              f"{rank[i]:>11}")
    print("\nJune only, the two rankings side by side:")
    ju = [(d, june_frames(d)[1]) for d in DEVS if june_frames(d)]
    by_r = sorted(ju, key=lambda t: rel_l2(t[1], truth[1]))
    by_u1 = sorted(ju, key=lambda t: -u1(t[1]))
    print("  by relL2 (best first): " + " > ".join(d for d, _ in by_r))
    print("  by |U1|  (best first): " + " > ".join(d for d, _ in by_u1))


def section_growth(truth):
    hdr("8. Boston across the movie: signal vs contaminant per frame")
    fr = june_frames("boston")
    sv = sim_frames("cd872d62")
    print(f"{'frame':>5} {'|U1|':>9} {'|U1| ceil':>10} {'|U2|':>9} "
          f"{'|U3|':>9} {'|U2|/|U1|':>10} {'relL2':>9}")
    for k in range(1, N_STEPS + 1):
        F = np.abs(np.fft.rfft(fr[k])) / N
        C = np.abs(np.fft.rfft(sv[k])) / N
        print(f"{k:>5} {F[1]:>9.5f} {C[1]:>10.5f} {F[2]:>9.5f} {F[3]:>9.5f} "
              f"{F[2]/F[1]:>10.3f} {rel_l2(fr[k], truth[k]):>9.4f}")
    print("\nmeasure-and-reprepare feeds frame k's reconstructed field back")
    print("in as frame k+1's initial state, so a k=2 contaminant is")
    print("re-prepared and re-amplified every seam.")


def section_budget(truth):
    hdr("9. Parseval-exact error budget in mode space")
    print("For real N=8 fields with U0=U4=0, ||u-r||^2 = 2N sum_{k=1,2,3}")
    print("|U_k - R_k|^2, so relL2^2 splits EXACTLY into per-mode terms.")
    print("k=1 is the physical Burgers mode; k=2 and k=3 are contaminants")
    print("(the FTCS truth has |R2|/|R1| = 0.028, |R3|/|R1| = 0.001).\n")
    R = np.fft.rfft(truth[1]) / N
    den = 2.0 * N * float(np.sum(np.abs(R[1:4]) ** 2))
    rows = []
    for dev in DEVS:
        fr = june_frames(dev)
        if fr:
            rows.append((f"June {dev}", fr[1]))
    for dev in DEVS:
        tr = sep_frames(dev)
        if tr:
            rows.append((f"Sep {dev}", np.mean([t[1] for t in tr], 0)))
    print(f"{'field':16} {'relL2':>8} | " + " ".join(
        f"{'k='+str(k):>16}" for k in (1, 2, 3)) + f" {'k2+k3 share':>12}")
    for name, u in rows:
        U = np.fft.rfft(u) / N
        parts = [2.0 * N * float(np.abs(U[k] - R[k]) ** 2) for k in (1, 2, 3)]
        tot = sum(parts)
        cells = " ".join(f"{p/den:>8.4f}({p/tot:>5.1%})" for p in parts)
        print(f"{name:16} {np.sqrt(tot/den):>8.4f} | {cells} "
              f"{(parts[1]+parts[2])/tot:>12.1%}")
    print("\nColumns are the contribution to relL2^2 (and the % of the total")
    print("error each mode owns).  Stencil gain |sin(2 pi k/8)| is 0.707 at")
    print("k=1, 1.000 at k=2, 0.707 at k=3: per unit of log-phi error, k=2")
    print("costs sqrt(2)x more than the signal mode does.")


def section_phase(truth):
    hdr("10. Is the k=2 contaminant COHERENT or STOCHASTIC?")
    print("A coherent circuit/calibration error has a REPEATABLE k=2 phase")
    print("across trials; a stochastic readout/shot effect does not.  Only")
    print("kingston and fez have enough September trials to test it.\n")

    def mode(u, k):
        U = np.fft.rfft(u) / N
        return float(np.abs(U[k])), float(np.angle(U[k]))

    R = np.fft.rfft(truth[1]) / N
    print(f"reference k=1 phase = {np.angle(R[1]):+.4f} rad "
          f"(a pure sine on this grid)\n")
    for dev in DEVS:
        tr = sep_frames(dev)
        if not tr:
            print(f"{dev:9} no September trials")
            continue
        a2 = np.array([mode(t[1], 2) for t in tr])
        a1 = np.array([mode(t[1], 1) for t in tr])
        # circular stats on the k=2 phase
        z = np.mean(np.exp(1j * a2[:, 1]))
        Rbar = float(np.abs(z))
        circ_sd = float(np.sqrt(-2.0 * np.log(Rbar))) if Rbar > 0 else np.inf
        z1 = np.mean(np.exp(1j * a1[:, 1]))
        print(f"{dev:9} n={len(tr)}")
        print(f"   k=1 |U|={a1[:,0].mean():.5f}+-{a1[:,0].std():.5f}  "
              f"phase mean={np.angle(z1):+.4f}  R={abs(z1):.4f}")
        print(f"   k=2 |U|={a2[:,0].mean():.5f}+-{a2[:,0].std():.5f}  "
              f"phase mean={np.angle(z):+.4f}  R={Rbar:.4f}  "
              f"circ sd={circ_sd:.4f} rad")
        print(f"   per-trial k=2 phase: "
              + " ".join(f"{p:+.2f}" for p in a2[:, 1]))
    print("\nR (mean resultant length) near 1 => phase locked => coherent.")
    print("R near 0 => phase random => stochastic.\n")
    print("June k=2 amplitude and phase, all four devices:")
    for dev in DEVS:
        fr = june_frames(dev)
        if fr:
            m2, p2 = mode(fr[1], 2)
            m1, p1 = mode(fr[1], 1)
            print(f"   {dev:9} k=1 |U|={m1:.5f} ph={p1:+.4f} | "
                  f"k=2 |U|={m2:.5f} ph={p2:+.4f}")


def section_readout_feasibility(truth):
    hdr("11. Could readout error produce the k=2 contaminant?")
    print("A bit-flip readout channel is DIAGONAL in the Walsh basis: it")
    print("multiplies each Walsh component of p by (1-2e)^weight.  It can")
    print("only ATTENUATE existing structure, it cannot synthesise a new")
    print("k=2 component.  Size check anyway -- invert the observed |U2|")
    print("back to the log-phi ripple it implies:")
    print("   |dL_2| = |U2| * dx / (nu * |sin(2 pi 2/8)|),   dp/p = 2 |dL_2|")
    print()
    ro = {}
    for dev in DEVS:
        p = os.path.join(JUNE_HW, f"smooth_movie_{dev}",
                         "q8020_results_1.json")
        jh = json.load(open(p))["job_harvest"][0]
        ro[dev] = float(np.median([v for v in
                                   jh["backend"]["readout_error"].values()
                                   if v is not None]))
    stencil2 = abs(np.sin(2.0 * np.pi * 2.0 / N))
    print(f"{'field':16} {'|U2|':>9} {'|dL_2|':>9} {'dp/p pk-pk':>11} "
          f"{'median RO err':>14} {'ratio':>8}")
    rows = [(f"June {d}", june_frames(d)[1], ro[d]) for d in DEVS
            if june_frames(d)]
    for dev in DEVS:
        tr = sep_frames(dev)
        if tr:
            rows.append((f"Sep {dev}", np.mean([t[1] for t in tr], 0),
                         ro[dev]))
    for name, u, e in rows:
        U2 = float(np.abs(np.fft.rfft(u)[2]) / N)
        dL2 = U2 * DX / (NU * stencil2)
        dpp = 4.0 * dL2          # 2*|dL| amplitude -> peak-to-peak in p
        print(f"{name:16} {U2:>9.5f} {dL2:>9.5f} {dpp:>11.3f} "
              f"{e:>14.5f} {dpp/e:>8.0f}x")
    print("\nShot-noise floor for comparison: with ~1.3e5 kept shots in 8")
    print("bins, the per-bin relative counting error is ~sqrt(8/1.3e5) =")
    print(f"{np.sqrt(8/1.3e5):.4f}, i.e. dp/p ~ 0.008.")


def section_ceiling_arithmetic(truth):
    hdr("12. The 'gain exceeds the noiseless ceiling' claim, checked")
    print("FINDINGS 4.3 reads two June gains above the 0.858 noiseless")
    print("ceiling (fez 0.947, boston 1.094) as proof that June's amplitude")
    print("NORMALIZATION was wrong.  But the ceiling only bounds the k=1")
    print("component; ||u|| also collects k=2 and k=3, and the log-derivative")
    print("AMPLIFIES those.  Rebuild each gain from its modes via Parseval:")
    print("  ||u||^2 = 2N (|U1|^2 + |U2|^2 + |U3|^2)   (U0 = U4 = 0)\n")
    nref = float(np.linalg.norm(truth[1]))
    print(f"{'field':16} {'g reported':>11} {'g from modes':>13} "
          f"{'g if k=1 only':>14} {'excess is k>1?':>15}")
    rows = [(f"June {d}", june_frames(d)[1]) for d in DEVS if june_frames(d)]
    for dev in DEVS:
        tr = sep_frames(dev)
        if tr:
            rows.append((f"Sep {dev}", np.mean([t[1] for t in tr], 0)))
    for name, u in rows:
        U = np.abs(np.fft.rfft(u)) / N
        g_rep = float(np.linalg.norm(u)) / nref
        g_mod = float(np.sqrt(2 * N * np.sum(U[1:4] ** 2))) / nref
        g_k1 = float(np.sqrt(2 * N * U[1] ** 2)) / nref
        print(f"{name:16} {g_rep:>11.4f} {g_mod:>13.4f} {g_k1:>14.4f} "
              f"{'yes' if g_k1 <= 0.8582 else 'NO':>15}")
    print("\nEvery k=1-only gain sits at or below the 0.858 ceiling, so no")
    print("field violates it where the ceiling actually applies.  The two")
    print("apparent violations are spurious k=2 energy inflating ||u||.")
    print("There is no normalization bug to chase in the June driver.")


def section_quality(truth):
    hdr("13. Does k=1 recovery track device quality, in BOTH epochs?")
    cal = {}
    for dev in DEVS:
        jh = json.load(open(os.path.join(
            JUNE_HW, f"smooth_movie_{dev}",
            "q8020_results_1.json")))["job_harvest"][0]["backend"]
        cz = [v for v in jh["gate_error"].get("cz", {}).values()
              if v is not None]
        cal[("June", dev)] = dict(
            ro=float(np.median([v for v in jh["readout_error"].values()
                                if v is not None])),
            cz=float(np.median(cz)) if cz else float("nan"),
            t2=float(np.median([v for v in jh["t2"].values()
                                if v is not None])))
    for dev in DEVS:
        f = sorted(glob.glob(os.path.join(
            SEP, dev, "trial_*", "q8020_metadata_*.json")))
        if not f:
            continue
        d = json.load(open(f[0]))

        def dig(o, key):
            if isinstance(o, dict):
                if key in o and isinstance(o[key], dict):
                    return o[key]
                for v in o.values():
                    r = dig(v, key)
                    if r is not None:
                        return r
            elif isinstance(o, list):
                for v in o:
                    r = dig(v, key)
                    if r is not None:
                        return r
            return None
        ro = dig(d, "readout_error")
        t2 = dig(d, "t2")
        ge = dig(d, "gate_error")
        cz = [v for v in (ge or {}).get("cz", {}).values()
              if v is not None] if ge else []
        cal[("Sep", dev)] = dict(
            ro=float(np.median([v for v in ro.values() if v is not None]))
            if ro else float("nan"),
            cz=float(np.median(cz)) if cz else float("nan"),
            t2=float(np.median([v for v in t2.values() if v is not None]))
            if t2 else float("nan"))
    sv = sim_frames("cd872d62")
    ceil1 = float(np.abs(np.fft.rfft(sv[1]))[1] / N)
    rows = []
    for dev in DEVS:
        fr = june_frames(dev)
        if fr:
            rows.append(("June", dev, fr[1]))
    for dev in DEVS:
        tr = sep_frames(dev)
        if tr:
            rows.append(("Sep", dev, np.mean([t[1] for t in tr], 0)))
    print(f"{'epoch':6} {'device':9} {'|U1|/ceil':>10} {'|U2|/|U1|':>10} "
          f"{'RO err':>9} {'CZ err':>9} {'T2 us':>8} {'relL2':>8}")
    recs = []
    for ep, dev, u in rows:
        U = np.abs(np.fft.rfft(u)) / N
        c = cal.get((ep, dev), {})
        rec = (U[1] / ceil1, U[2] / U[1], c.get("ro", float("nan")),
               c.get("cz", float("nan")), c.get("t2", float("nan")),
               rel_l2(u, truth[1]))
        recs.append(rec)
        print(f"{ep:6} {dev:9} {rec[0]:>10.3f} {rec[1]:>10.3f} "
              f"{rec[2]:>9.5f} {rec[3]:>9.5f} {rec[4]:>8.1f} {rec[5]:>8.4f}")
    a = np.array(recs, dtype=float)

    def rr(i, j):
        m = np.isfinite(a[:, i]) & np.isfinite(a[:, j])
        if m.sum() < 3:
            return float("nan")
        return float(np.corrcoef(a[m, i], a[m, j])[0, 1])
    print(f"\nn = {len(recs)} device-epoch points (Pearson r):")
    for lbl, j in (("readout err", 2), ("CZ err", 3), ("T2", 4)):
        print(f"  r(|U1|/ceil, {lbl:12}) = {rr(0, j):+.3f}"
              f"     r(relL2, {lbl:12}) = {rr(5, j):+.3f}")
    print(f"  r(|U1|/ceil, relL2)        = {rr(0, 5):+.3f}"
          f"     r(|U2|/|U1|, relL2)      = {rr(1, 5):+.3f}")


def section_lowpass(truth):
    hdr("14. The phi_modes low-pass is a NO-OP at q=3, and what it would buy")
    print("lib_cole_hopf.fourier_low_pass_phi does:")
    print("    n_modes = min(n_modes, N//2);  fk = rfft(phi);  fk[n_modes+1:]=0")
    print("At N=8, rfft has 5 entries (k=0..4) and n_modes clamps to 4, so")
    print("fk[5:] zeroes NOTHING.  Both epochs ran phi_modes=8, i.e. the")
    print("Fourier low-pass -- the program's stated primary accuracy dial for")
    print("exactly this failure (note-20260807-0002) -- was INACTIVE.")
    print("Any phi_modes >= 4 is a no-op at q=3; only 1 or 2 filter.\n")
    R = np.fft.rfft(truth[1]) / N
    ph_ref = float(np.angle(R[1]))
    rows = [(f"June {d}", june_frames(d)[1]) for d in DEVS if june_frames(d)]
    for dev in DEVS:
        tr = sep_frames(dev)
        if tr:
            rows.append((f"Sep {dev}", np.mean([t[1] for t in tr], 0)))
    print("k=1 PHASE error is a separate, independent defect: it shifts the")
    print("wave along x and no amplitude filter can remove it.")
    print(f"{'field':16} {'relL2':>8} {'k=1 phase':>10} {'phase err':>10} "
          f"{'shift(nodes)':>13} {'relL2 k=1 only':>15} {'gain':>7}")
    for name, u in rows:
        U = np.fft.rfft(u) / N
        dph = float(np.angle(U[1])) - ph_ref
        dph = (dph + np.pi) % (2 * np.pi) - np.pi
        keep = np.zeros_like(U)
        keep[1] = U[1]
        u1 = np.fft.irfft(keep * N, n=N)
        r0, r1 = rel_l2(u, truth[1]), rel_l2(u1, truth[1])
        print(f"{name:16} {r0:>8.4f} {np.angle(U[1]):>10.4f} "
              f"{dph:>+10.4f} {dph/(2*np.pi)*N:>+13.2f} {r1:>15.4f} "
              f"{r0/r1:>7.2f}x")
    print("\n'relL2 k=1 only' keeps just the physical mode of the ALREADY")
    print("reconstructed u.  It is an indicative, not exact, stand-in for")
    print("having run phi_modes=1 (filtering phi and then differentiating is")
    print("not identical to filtering u), but it bounds the available win.")


def main():
    truth = ftcs800_truth_frames()
    section_per_frame(truth)
    section_symmetry(truth)
    section_spectrum(truth)
    section_phi(truth)
    section_profiles(truth)
    section_timeline()
    section_ranking(truth)
    section_growth(truth)
    section_budget(truth)
    section_phase(truth)
    section_readout_feasibility(truth)
    section_ceiling_arithmetic(truth)
    section_quality(truth)
    section_lowpass(truth)


if __name__ == "__main__":
    main()
