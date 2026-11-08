#!/usr/bin/env python3
"""Baseline vs updated estimator comparison on identical synthetic data.

SIMULATION ONLY. The IMU model, noise levels, gyro bias, lever arm and the
(Q, R) tunings below are ASSUMPTIONS made for this study; they are not
measurements of the TremoSense hardware and the (Q, R) pairs are not the
device's tuned values (those are not in the repository).

Configurations (same input samples for all):
  baseline : verbatim legacy EKF, dt quantised to 1 ms (k_uptime_get_32 timing)
  updated  : refactored EKF, exact dt, accelerometer gating OFF
  gated    : refactored EKF, exact dt, accelerometer gating ON
Usage: python3 ekf_comparison.py [--quick]
"""
import ctypes, json, subprocess, sys, pathlib
import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
FW = HERE.parents[1] / "firmware"
BUILD = pathlib.Path("/tmp/ts_analysis"); BUILD.mkdir(exist_ok=True)
LIB = BUILD / "libekfbatch.so"
subprocess.check_call(["gcc", "-O2", "-shared", "-fPIC", "-std=gnu99", "-DMAX_PITCH_RAD=1.3962634f",
    "-I", str(FW / "include"), "-I", str(FW / "tests"),
    str(HERE / "ekf_batch.c"), str(FW / "src/estimation/ekf.c"),
    str(FW / "tests/reference/ekf_legacy.c"), "-lm", "-o", str(LIB)])
lib = ctypes.CDLL(str(LIB))
fp = ctypes.POINTER(ctypes.c_float)
lib.run_new.argtypes = [ctypes.c_float]*2 + [ctypes.c_int] + [ctypes.c_float]*2 + [ctypes.c_int, fp, fp, fp]
lib.run_legacy.argtypes = [ctypes.c_float]*2 + [ctypes.c_int, fp, fp, fp]
P = lambda a: a.ctypes.data_as(fp)

G, D2R, FS = 9.80665, np.pi/180, 208.0
DT = 1.0/FS
# --- assumptions (documented in documentation/verification-validation/EKF_COMPARISON.md) ---
ACC_NOISE = 0.0009 * G * np.sqrt(FS/2)     # density 0.9 mg/rtHz -> ~9 mg (0.09 m/s^2) rms per sample at 104 Hz bandwidth: assumed, MEMS-class
GYR_NOISE = np.deg2rad(0.007) * np.sqrt(FS/2)  # density 0.007 dps/rtHz -> ~0.07 dps rms per sample: assumed
GYR_BIAS = np.deg2rad(np.array([0.15, -0.10, 0.05]))  # raw bias; 90 % removed by calibration (residual = 0.1x): assumed
TUNINGS = {"T1 Q=1e-9 R=1e-3": (1e-9, 1e-3), "T2 Q=1e-8 R=1e-3": (1e-8, 1e-3), "T3 Q=1e-7 R=1e-3": (1e-7, 1e-3), "T4 Q=1e-8 R=1e-1": (1e-8, 1e-1)}
GATE = dict(band=3.0, scale=100.0)

def make_signal(f_hz, amp_deg, lever_m, seed, dur=15.0, vol_amp_deg=0.0, vol_hz=0.5):
    rng = np.random.default_rng(seed)
    t = np.arange(int(dur*FS)) * DT
    w = 2*np.pi*f_hz; wv = 2*np.pi*vol_hz
    ph0, th0 = rng.uniform(0, 2*np.pi, 2)
    phi = amp_deg*D2R*np.sin(w*t+ph0) + vol_amp_deg*D2R*np.sin(wv*t)
    th = 0.6*amp_deg*D2R*np.sin(w*t+th0) + 0.5*vol_amp_deg*D2R*np.sin(wv*t+0.7)
    phd = np.gradient(phi, DT); thd = np.gradient(th, DT)
    p, q, r = phd, thd*np.cos(phi), -thd*np.sin(phi)      # zero yaw rate
    wv_ = np.stack([p, q, r], 1)
    wd = np.gradient(wv_, DT, axis=0)
    rv = np.array([0.0, 0.0, lever_m])                    # IMU offset from pivot along body z
    a_lin = np.cross(wd, rv) + np.cross(wv_, np.cross(wv_, rv))
    f_spec = np.stack([-G*np.sin(th), G*np.cos(th)*np.sin(phi), G*np.cos(th)*np.cos(phi)], 1) + a_lin
    acc = f_spec + rng.normal(0, ACC_NOISE, f_spec.shape)
    gyr = wv_ + GYR_BIAS + rng.normal(0, GYR_NOISE, wv_.shape)
    # gyro bias is removed by the boot calibration in firmware; keep the *residual* only:
    gyr = gyr - GYR_BIAS*0.9
    x = np.ascontiguousarray(np.hstack([acc, gyr]).astype(np.float32))
    return t, x, np.rad2deg(phi), np.rad2deg(th)

def ms_quantised_dt(n):
    ts = np.floor(np.arange(n) * DT * 1000.0)            # k_uptime_get_32() timestamps [ms]
    d = np.diff(ts, prepend=ts[0] - 4.0) / 1000.0
    return np.ascontiguousarray(d.astype(np.float32))

def fit(est, truth, t, f):
    """Gain, phase lag [ms] and residual rms of the estimate at tremor frequency f (last 10 s)."""
    m = t >= (t[-1] - 10.0)
    A = np.stack([np.sin(2*np.pi*f*t[m]), np.cos(2*np.pi*f*t[m]), np.ones(m.sum())], 1)
    ce, *_ = np.linalg.lstsq(A, est[m], rcond=None); ct, *_ = np.linalg.lstsq(A, truth[m], rcond=None)
    ae, at = np.hypot(ce[0], ce[1]), np.hypot(ct[0], ct[1])
    lag = (np.arctan2(ct[1], ct[0]) - np.arctan2(ce[1], ce[0]))      # est lags truth by this phase
    lag = (lag + np.pi) % (2*np.pi) - np.pi
    return ae/at, lag/(2*np.pi*f)*1000.0, float(np.sqrt(np.mean((est[m]-truth[m])**2)))

def run(cfgname, x, dt_exact, dt_q, q, r):
    n = len(x); out = np.zeros((n, 2), np.float32)
    if cfgname == "baseline":
        lib.run_legacy(q, r, n, P(x), P(dt_q), P(out)); rej = 0
    else:
        gate = 1 if cfgname == "gated" else 0
        rej = lib.run_new(q, r, gate, GATE["band"], GATE["scale"], n, P(x), P(dt_exact), P(out))
    return out, rej

def main(quick=False):
    freqs = [3, 4, 5, 6, 7, 8]; levers = [0.0, 0.03, 0.06, 0.10]
    seeds = range(3 if quick else 10); amp = 5.0
    cfgs = ["baseline", "updated", "gated"]
    res = {"assumptions": dict(fs_hz=FS, amp_deg=amp, acc_noise_ms2=ACC_NOISE, gyro_noise_rads=GYR_NOISE,
           gyro_residual_bias_dps=[0.015, -0.01, 0.005], tunings=TUNINGS, gate=GATE, levers_m=levers, seeds=len(list(seeds)),
           note="synthetic; assumed sensor model; tunings are NOT the device's"), "tremor": [], "voluntary": []}
    dt_exact = np.full(int(15*FS), DT, np.float32); dt_q = ms_quantised_dt(len(dt_exact))
    for tname, (q, r) in TUNINGS.items():
        for L in levers:
            for f in freqs:
                acc = {c: {"rms_roll": [], "rms_pitch": [], "gain": [], "lag_ms": [], "rej": 0} for c in cfgs}
                for s in seeds:
                    t, x, tr, tp = make_signal(f, amp, L, 1000*s+f)
                    for c in cfgs:
                        out, rej = run(c, x, dt_exact, dt_q, q, r)
                        g, lag, rms = fit(out[:, 0].astype(float), tr, t, f)
                        _, _, rmsp = fit(out[:, 1].astype(float), tp, t, f)
                        a = acc[c]; a["rms_roll"].append(rms); a["rms_pitch"].append(rmsp); a["gain"].append(g); a["lag_ms"].append(lag); a["rej"] += int(rej)
                for c in cfgs:
                    a = acc[c]
                    res["tremor"].append(dict(tuning=tname, lever_m=L, freq_hz=f, config=c,
                        rms_roll_deg=float(np.mean(a["rms_roll"])), rms_roll_sd=float(np.std(a["rms_roll"])),
                        rms_pitch_deg=float(np.mean(a["rms_pitch"])), gain=float(np.mean(a["gain"])),
                        lag_ms=float(np.mean(a["lag_ms"])), numeric_rejects=a["rej"]))
        # voluntary movement: 0.5 Hz 15 deg + 5 Hz 3 deg tremor, lever 0.06
        for L in (0.0, 0.06):
            row = {}
            for c in cfgs:
                e = []
                for s in seeds:
                    t, x, tr, tp = make_signal(5.0, 3.0, L, 77+s, vol_amp_deg=15.0)
                    out, _ = run(c, x, dt_exact, dt_q, q, r)
                    m = t >= 5.0
                    e.append(np.sqrt(np.mean((out[m, 0]-tr[m])**2)))
                row[c] = float(np.mean(e))
            res["voluntary"].append(dict(tuning=tname, lever_m=L, rms_roll_deg=row))
    out = HERE.parent / "results" / ("ekf_comparison_quick.json" if quick else "ekf_comparison.json")
    out.write_text(json.dumps(res, indent=1)); print("wrote", out)
    # console summary: tuning T1, mean over freqs
    for L in levers:
        line = f"L={L:.2f} m  " + "  ".join(
            f"{c}: {np.mean([d['rms_roll_deg'] for d in res['tremor'] if d['tuning']==list(TUNINGS)[0] and d['lever_m']==L and d['config']==c]):.3f} deg"
            for c in cfgs)
        print(line)

if __name__ == "__main__":
    main("--quick" in sys.argv)
