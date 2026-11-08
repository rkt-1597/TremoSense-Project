#!/usr/bin/env python3
"""Builds research/paper/TremoSense_Paper.docx (IEEE-style, two-column) from verified repository facts.

Numbers come from: firmware/ source and constants, documentation/ (requirements, audit, risk, V&V),
analysis/results/ (ekf_comparison.json, paper_figure_numbers.json, evidence logs) and the author-reported
Simulink results shown in the repository README. Nothing here is a hardware measurement.
Run:  python3 research/paper/build_paper.py && soffice --headless --convert-to pdf --outdir research/paper research/paper/TremoSense_Paper.docx
"""
import collections
import json
import re
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from ieee_docx import Paper  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
FIG = ROOT / "research" / "figures"
SIM = ROOT / "algorithms" / "matlab" / "assets"
OUT = ROOT / "research" / "paper" / "TremoSense_Paper.docx"
EKF = json.load(open(ROOT / "analysis" / "results" / "ekf_comparison.json"))
NUM = json.load(open(ROOT / "analysis" / "results" / "paper_figure_numbers.json"))
LOG = (ROOT / "analysis" / "results" / "evidence" / "host_tests_20261108.log").read_text()
REQMD = (ROOT / "documentation" / "requirements" / "REQUIREMENTS.md").read_text()

G, FS = 9.80665, 208.0
DT = 1.0 / FS


# ----------------------------------------------------------------------------- derived numbers
def kss(q, r):
    """Steady-state Kalman gain of the scalar random-walk filter (F ~ I)."""
    pm = (q + np.sqrt(q * q + 4 * q * r)) / 2
    return pm / (pm + r)


def fcorner(q, r):
    k = kss(q, r)
    return -np.log(1 - k) / (2 * np.pi * DT)


def lag_model_ms(q, r, L, f):
    """Predicted estimate lag (ms): integration lead of dt/2 plus lever-arm phase error through the accel low-pass."""
    k = kss(q, r)
    w = 2 * np.pi * f
    lp = k / (1 - (1 - k) * np.exp(-1j * w * DT))
    est = 1 + lp * (L * w * w / G)
    return float(-np.angle(est) / w * 1e3 - DT / 2 * 1e3)


TUN = {k.split()[0]: v for k, v in EKF["assumptions"]["tunings"].items()}
TUNFULL = {k.split()[0]: k for k in EKF["assumptions"]["tunings"]}
TR = EKF["tremor"]
LEVERS = (0.0, 0.03, 0.06, 0.10)


def pick(tn, L, f, key, cfg="updated"):
    return [r[key] for r in TR if r["tuning"] == TUNFULL[tn] and r["lever_m"] == L and r["freq_hz"] == f and r["config"] == cfg][0]


lag_err = [pick(t, L, f, "lag_ms") - lag_model_ms(*TUN[t], L, f) for t in TUN for L in LEVERS for f in (3, 5, 8)]
LAG_RMS, LAG_MAX = float(np.sqrt(np.mean(np.square(lag_err)))), float(np.max(np.abs(lag_err)))
agg = collections.defaultdict(list)
for r in TR:
    agg[(r["tuning"], r["lever_m"], r["config"])].append(r["rms_roll_deg"])
mean_rms = lambda t, L, c: float(np.mean(agg[(TUNFULL[t], L, c)]))  # noqa: E731
upd = [r for r in TR if r["config"] == "updated"]
GAIN_ALL = (min(r["gain"] for r in upd), max(r["gain"] for r in upd))
LAG_ALL = (min(r["lag_ms"] for r in upd), max(r["lag_ms"] for r in upd))
DIFFS = [mean_rms(t, L, "baseline") - mean_rms(t, L, "updated") for t in TUN for L in LEVERS]
n_improved = sum(1 for d in DIFFS if d >= 0)
assert n_improved == 16, DIFFS
CHK = {m.group(1): int(m.group(2)) for m in re.finditer(r"(test_\w+): (\d+) checks, 0 failures", LOG)}
TOTAL_CHECKS = sum(CHK.values())
assert len(CHK) == 4 and TOTAL_CHECKS == 29022, CHK
REQ = NUM["req"][0]
dt_mean, dt_lo, dt_hi = NUM["dt"]
FC = {t: fcorner(*TUN[t]) for t in TUN}


def parse_reqs():
    rows = []
    for line in REQMD.splitlines():
        if line.startswith("| TS-"):
            c = [x.strip() for x in line.strip().strip("|").split("|")]
            clean = lambda s: re.sub(r"[*`]", "", s)  # noqa: E731
            rows.append([c[0], clean(c[1]), clean(c[3]), clean(c[5])])
    return rows


REQROWS = parse_reqs()
assert len(REQROWS) == 26

# ----------------------------------------------------------------------------- bibliography
REFS = {
    "deuschl98": "G. Deuschl, P. Bain, and M. Brin, “Consensus statement of the Movement Disorder Society on tremor,” <i>Mov. Disord.</i>, vol. 13, suppl. 3, pp. 2–23, 1998.",
    "bhatia18": "K. P. Bhatia <i>et al.</i>, “Consensus statement on the classification of tremors,” <i>Mov. Disord.</i>, vol. 33, no. 1, pp. 75–87, 2018.",
    "elble90": "R. J. Elble and W. C. Koller, <i>Tremor</i>. Baltimore, MD, USA: Johns Hopkins Univ. Press, 1990.",
    "pathak14": "A. Pathak, J. A. Redmond, M. Allen, and K. L. Chou, “A noninvasive handheld assistive device to accommodate essential tremor: A pilot study,” <i>Mov. Disord.</i>, vol. 29, no. 6, pp. 838–842, 2014.",
    "gallego10": "J. A. Gallego, E. Rocon, J. O. Roa, J. C. Moreno, and J. L. Pons, “Real-time estimation of pathological tremor parameters from gyroscope data,” <i>Sensors</i>, vol. 10, no. 3, pp. 2129–2149, 2010.",
    "rocon07": "E. Rocon, J. M. Belda-Lois, A. F. Ruiz, M. Manto, J. C. Moreno, and J. L. Pons, “Design and validation of a rehabilitation robotic exoskeleton for tremor assessment and suppression,” <i>IEEE Trans. Neural Syst. Rehabil. Eng.</i>, vol. 15, no. 3, pp. 367–378, 2007.",
    "kalman60": "R. E. Kalman, “A new approach to linear filtering and prediction problems,” <i>J. Basic Eng.</i>, vol. 82, no. 1, pp. 35–45, 1960.",
    "gelb74": "A. Gelb, Ed., <i>Applied Optimal Estimation</i>. Cambridge, MA, USA: MIT Press, 1974.",
    "simon06": "D. Simon, <i>Optimal State Estimation</i>. Hoboken, NJ, USA: Wiley, 2006.",
    "barshalom01": "Y. Bar-Shalom, X. R. Li, and T. Kirubarajan, <i>Estimation with Applications to Tracking and Navigation</i>. New York, NY, USA: Wiley, 2001.",
    "sabatini06": "A. M. Sabatini, “Quaternion-based extended Kalman filter for determining orientation by inertial and magnetic sensing,” <i>IEEE Trans. Biomed. Eng.</i>, vol. 53, no. 7, pp. 1346–1356, 2006.",
    "euston08": "M. Euston, P. Coote, R. Mahony, J. Kim, and T. Hamel, “A complementary filter for attitude estimation of a fixed-wing UAV,” in <i>Proc. IEEE/RSJ Int. Conf. Intell. Robots Syst. (IROS)</i>, 2008, pp. 340–345.",
    "mahony08": "R. Mahony, T. Hamel, and J.-M. Pflimlin, “Nonlinear complementary filters on the special orthogonal group,” <i>IEEE Trans. Autom. Control</i>, vol. 53, no. 5, pp. 1203–1218, 2008.",
    "madgwick11": "S. O. H. Madgwick, A. J. L. Harrison, and R. Vaidyanathan, “Estimation of IMU and MARG orientation using a gradient descent algorithm,” in <i>Proc. IEEE Int. Conf. Rehabil. Robot. (ICORR)</i>, 2011.",
    "titterton04": "D. H. Titterton and J. L. Weston, <i>Strapdown Inertial Navigation Technology</i>, 2nd ed. Stevenage, U.K.: IEE, 2004.",
    "woodman07": "O. J. Woodman, “An introduction to inertial navigation,” Univ. Cambridge Comput. Lab., Cambridge, U.K., Tech. Rep. UCAM-CL-TR-696, 2007.",
    "welford62": "B. P. Welford, “Note on a method for calculating corrected sums of squares and products,” <i>Technometrics</i>, vol. 4, no. 3, pp. 419–420, 1962.",
    "anderson90": "B. D. O. Anderson and J. B. Moore, <i>Optimal Control: Linear Quadratic Methods</i>. Englewood Cliffs, NJ, USA: Prentice-Hall, 1990.",
    "bryson75": "A. E. Bryson and Y.-C. Ho, <i>Applied Optimal Control</i>. Washington, DC, USA: Hemisphere, 1975.",
    "astrom08": "K. J. Åström and R. M. Murray, <i>Feedback Systems: An Introduction for Scientists and Engineers</i>. Princeton, NJ, USA: Princeton Univ. Press, 2008.",
    "skogestad05": "S. Skogestad and I. Postlethwaite, <i>Multivariable Feedback Control: Analysis and Design</i>, 2nd ed. Chichester, U.K.: Wiley, 2005.",
    "franklin98": "G. F. Franklin, J. D. Powell, and M. L. Workman, <i>Digital Control of Dynamic Systems</i>, 3rd ed. Menlo Park, CA, USA: Addison-Wesley, 1998.",
    "astrom97": "K. J. Åström and B. Wittenmark, <i>Computer-Controlled Systems: Theory and Design</i>, 3rd ed. Upper Saddle River, NJ, USA: Prentice-Hall, 1997.",
    "leveson11": "N. G. Leveson, <i>Engineering a Safer World: Systems Thinking Applied to Safety</i>. Cambridge, MA, USA: MIT Press, 2011.",
    "zephyr": "Zephyr Project, “Zephyr Project documentation, release 4.0.0.” [Online]. Available: https://docs.zephyrproject.org",
    "lsm6ds3": "STMicroelectronics, “LSM6DS3: iNEMO inertial module: always-on 3D accelerometer and 3D gyroscope,” datasheet.",
    "nrf52840": "Nordic Semiconductor, “nRF52840 Product Specification.”",
    "iso14971": "<i>Medical devices—Application of risk management to medical devices</i>, ISO 14971:2019 (structuring reference only).",
    "iec62304": "<i>Medical device software—Software life cycle processes</i>, IEC 62304:2006+AMD1:2015 (structuring reference only).",
    "iso13485": "<i>Medical devices—Quality management systems—Requirements for regulatory purposes</i>, ISO 13485:2016 (reference only).",
    "iec60601": "<i>Medical electrical equipment—Part 1: General requirements for basic safety and essential performance</i>, IEC 60601-1:2005+AMD1:2012+AMD2:2020 (reference only).",
    "iec62366": "<i>Medical devices—Part 1: Application of usability engineering to medical devices</i>, IEC 62366-1:2015 (reference only).",
}


# ----------------------------------------------------------------------------- the paper
def build(prev=None):
    P = Paper(**(prev or {}))
    B, S, SUB = P.body, P.sec, P.sub

    # -------------------------------------------------------------- title block
    P.para("TremoSense: A Two-Axis EKF–LQR Stabilisation Platform for an Assistive Utensil on Zephyr RTOS — "
           "Implementation, Safety Architecture and Evidence-Graded Evaluation", align="c", size=17, bold=True, after=5, before=2)
    P.para("Prithvi Tambewagh, Pawan Shinde, and Pranshu Kumar", align="c", size=11, after=0)
    P.para("B.Tech. Electronics and Telecommunication Engineering, Veermata Jijabai Technological Institute (VJTI), Mumbai, India",
           align="c", size=9, italic=True, after=4)
    P.para("Manuscript status: engineering report on a research prototype. No hardware performance data, user trials or regulatory "
           "assessment are reported. Every result is labelled with its evidence class (host test, simulation, compile check, or "
           "author-reported model); none is a measurement of the assembled device.", align="c", size=8, italic=True, after=4)
    P.two_columns()

    # -------------------------------------------------------------- abstract
    P.para("<bi>Abstract—</bi><b>TremoSense is a hand-held spoon stabiliser that senses hand motion with a 6-axis inertial measurement "
           "unit (IMU) and drives a two-servo gimbal (roll and pitch) to oppose tremor-induced tilt. The firmware runs on a Seeed XIAO nRF52840 "
           "Sense under Zephyr RTOS: a two-state extended Kalman filter (EKF) estimates roll and pitch at 208 Hz and a linear-quadratic "
           "regulator (LQR) computes the servo commands. We audit the shipped firmware, record 20 findings (the shipped constants Q = R = K = 0 drive the "
           "estimator to NaN; time steps are quantised to 1 ms; PWM errors are silently ignored; there is no watchdog), and re-engineer it into "
           "a portable C99 core with an explicit safety layer: an input-plausibility monitor, an actuator guard with a defined neutral state, "
           "watchdog supervision and validated calibration. We derive the steady-state EKF as a complementary filter whose accelerometer corner "
           "(0.01–0.33 Hz for the tunings studied) lies far below the tremor band, derive the lever-arm-induced estimator lag, and bound the "
           f"achievable reduction by the 20 ms PWM frame. Evidence is graded: {TOTAL_CHECKS:,} host-side checks pass, including bit-identical agreement of "
           f"the refactored EKF with the legacy EKF on valid data; the exact-Δt estimator is no worse than the baseline in {n_improved} of 16 simulated "
           "tuning and lever-arm cases, and an analytic lag model agrees with simulation to "
           f"{LAG_RMS:.1f} ms RMS. Author-reported Simulink results (1 kHz) show 93.9 % roll and 89.9 % pitch residual reduction at one operating "
           "point, which we show cannot be read as hardware performance. No on-device latency, power, rejection or user data exist; a "
           "verification plan with hardware test cases closes the gap.</b>", size=8.5, after=3)
    P.para("<bi>Index Terms—</bi><i>tremor suppression, assistive technology, extended Kalman filter, linear-quadratic regulator, attitude "
           "estimation, Zephyr RTOS, nRF52840, embedded safety, IMU calibration.</i>", size=8.5, after=4)

    # -------------------------------------------------------------- I Introduction
    S("Introduction", "intro")
    B("Tremor, an involuntary rhythmic oscillation of a body part, makes eating difficult because a loaded spoon must be carried "
      "from plate to mouth against gravity. Pathological tremor is characterised across roughly 4–12 Hz depending on aetiology, with "
      "Parkinsonian rest tremor typically near 4–6 Hz and essential tremor typically higher {c:deuschl98,bhatia18,elble90}. "
      "Hand-held active stabilisers sense the motion of the handle and counter-rotate the utensil head; a pilot study of such a device in "
      "essential tremor is reported in {c:pathak14}. TremoSense pursues the same concept with low-cost hobby servos and a microcontroller "
      "development board. It was originally motivated by tremor in Parkinson’s disease; this report makes no clinical claim and treats the "
      "device strictly as a motion-stabilisation prototype.")
    B("The work reported here began as an audit of an existing prototype firmware. Three observations shaped it. First, the firmware as "
      "shipped could not actuate safely: its tuning placeholders (Q = R = K = 0) make the estimator diverge, and nothing would have "
      "stopped a diverged estimate from reaching a servo. Second, the only performance evidence in the repository is a 1 kHz Simulink "
      "model whose structure differs from the deployed 208 Hz firmware. Third, there are no hardware logs, schematics or measured "
      "latency, power or rejection data. The report therefore has two aims: to document and harden what exists, and to state exactly what "
      "that evidence does and does not support.")
    B("<b>Contributions.</b> (i) A source-verified description of the firmware, the estimator and the controller, with the discrete-time "
      "equations as implemented ({sec:est}, {sec:ctl}). (ii) A derivation of the steady-state EKF as a complementary filter, an analytic "
      "model of the estimate’s lead and lever-arm lag that matches simulation, and a delay-limited bound on achievable reduction "
      "({sec:est}, {sec:disc}). (iii) A safety architecture that holds the servos at a defined neutral pose whenever sensing, timing, tuning "
      "or calibration is invalid, with a fault-injection trace of the real guard code ({sec:safety}). (iv) A portable, host-tested core with a "
      "regression against the original estimator ({sec:results}). (v) A structured account of 20 audit findings, 26 requirements and the "
      "open evidence gaps, with a hardware verification plan ({sec:req}, {sec:method}, {sec:limits}).")
    B("<b>Organisation.</b> {sec:related} reviews related work; {sec:req} states the problem and requirements; {sec:arch} and {sec:hw} "
      "describe the architecture and hardware; {sec:acq} covers acquisition and calibration; {sec:est} and {sec:ctl} the estimator and "
      "controller; {sec:fw} the firmware; {sec:safety} the safety architecture; {sec:method} the evaluation methodology; "
      "{sec:results} the results; {sec:compare} the comparison with the baseline and the earlier prototype; {sec:disc} the discussion; and "
      "{sec:limits}–{sec:concl} the limitations, future work and conclusions.")

    # -------------------------------------------------------------- II Related work
    S("Background and Related Work", "related")
    SUB("Tremor stabilisation and suppression")
    B("Tremor-suppression devices span three approaches: wearable orthoses and exoskeletons that apply force across a joint "
      "{c:rocon07}; hand-held tools that stabilise the end effector in the inertial frame {c:pathak14}; and signal-processing methods "
      "that estimate tremor parameters in real time for use in either {c:gallego10}. Hand-held stabilisers have the lowest burden on the "
      "user, because nothing is worn, and are the class TremoSense belongs to. Their central engineering problems are the same as in any "
      "inertial stabilisation task: estimating orientation from low-cost sensors with limited bandwidth, closing a loop through "
      "actuators with delay and finite range, and doing so safely near a person.")
    SUB("Attitude estimation from low-cost IMUs")
    B("Attitude from an accelerometer and a gyroscope is classically obtained with complementary filters {c:euston08,mahony08}, "
      "gradient-descent filters {c:madgwick11} or Kalman-type filters {c:sabatini06,simon06,barshalom01}. Gyroscope integration is accurate "
      "at high frequency but drifts; the accelerometer provides a gravity reference but is corrupted by linear acceleration {c:titterton04,woodman07}. "
      "The latter is severe for a hand-held tremor source, where tangential acceleration scales with the distance between the IMU and the "
      "rotation centre (<i>lever arm</i>) and with the square of frequency ({sec:est}). Euler-angle kinematics are singular at ±90° pitch; "
      "quaternion and SO(3) formulations avoid this {c:sabatini06,mahony08} at higher implementation cost. TremoSense uses a minimal two-state EKF "
      "on Euler angles because it is compact and was already present; we do not claim it is superior to the alternatives and have not "
      "compared against them.")
    SUB("Linear-quadratic control and discretisation")
    B("The LQR gives an optimal state-feedback gain for a linear plant and quadratic cost {c:anderson90}; weighting by the inverse "
      "squares of admissible deviations (Bryson’s rule {c:bryson75}) is a standard starting point. Sampled-data implementation follows "
      "zero-order-hold practice {c:franklin98,astrom97}, and the effect of delay on achievable disturbance rejection is treated in "
      "{c:astrom08,skogestad05}.")
    SUB("Safety framing")
    B("Medical-device standards {c:iso14971,iec62304,iso13485,iec60601,iec62366} are used here as vocabulary for hazards, requirements "
      "and traceability only. No compliance, certification or clinical status is claimed. The design follows the control-theoretic safety "
      "view in {c:leveson11}: unsafe behaviour is prevented by constraints on the control action, here the actuator guard of "
      "{sec:safety}, rather than by assuming the controller is correct.")
    P.table("Positioning of this work against related approaches", "related",
            ["Approach", "Sensing / actuation", "Evidence level in source", "Relevance here"],
            [["Hand-held active stabiliser {c:pathak14}", "IMU; two-axis actuation of utensil head", "Pilot study, essential tremor", "Same concept; no comparison made"],
             ["Real-time tremor parameter estimation {c:gallego10}", "Gyroscopes; adaptive filtering", "Recorded patient data", "Estimator design alternative; not used"],
             ["Wearable exoskeleton {c:rocon07}", "Worn orthosis, joint actuation", "Design and validation study", "Different class (worn, force-applying)"],
             ["Complementary / SO(3) filters {c:euston08,mahony08,madgwick11}", "IMU attitude estimation", "UAV and motion-capture studies", "Alternatives to the Euler EKF; not compared"],
             ["Kalman-type attitude filters {c:sabatini06,simon06}", "IMU (± magnetometer)", "Bench and human-motion studies", "Basis of the EKF used"],
             ["<b>This work</b>", "6-axis IMU; two hobby servos", "Host tests, simulation, compile check", "Firmware and safety hardening; no hardware performance data"]],
            widths=[1.5, 1.4, 1.3, 1.5], wide=True)

    # -------------------------------------------------------------- III Problem & requirements
    S("Problem Statement and Requirements", "req")
    SUB("Problem statement")
    B("Given a spoon mounted on a two-axis servo gimbal at the end of a hand-held body, compute servo angles at the control-loop rate so "
      "that the spoon’s roll and pitch are stabilised against tremor-band hand motion (test band 3–8 Hz), without opposing, beyond an agreed "
      "limit, the slow intentional orientation changes the user needs, and such that no sensing, timing, software or configuration fault "
      "can drive the servos to an unsafe or undefined position. Two requirements are easily overlooked: the non-opposition of voluntary "
      "motion, which the existing Simulink evidence does not address ({sec:results}), and defined fault behaviour, which the original "
      "firmware did not provide ({sec:safety}).")
    SUB("Requirements and traceability", "reqtab")
    B("Requirements are kept in the repository with stable identifiers and a traceability matrix to 33 verification cases. "
      "Items marked <i>Proposed</i> are engineering proposals made during this work, not agreed clinical or product requirements, and "
      "need confirmation by the project owners and, for performance, by clinicians and users. {tab:reqs} lists all 26; "
      f"{{fig:reqstatus}} summarises their status: {REQ['Verified (host/build)']} are verified on a host or by a build, {REQ['Implemented, hardware NOT RUN']} are implemented but "
      f"not yet run on hardware, {REQ['Open / not implemented']} are open (not implemented or unresolved) and {REQ['NOT RUN (hardware)']} require hardware or people and have not been run.")
    P.table("Requirements and verification status (as of this report)", "reqs",
            ["ID", "Requirement", "Method", "Status"], REQROWS, widths=[0.7, 3.6, 1.0, 1.8], size=7, wide=True)
    P.figure(FIG / "p_req_status.png", "Verification status of the 26 requirements by status class. “Verified” means executed on a host with synthetic data "
             "or by a successful build; nothing is hardware-verified.", "reqstatus")
    SUB("Evidence classes")
    B("Because no hardware experiment exists, every result carries one of four evidence classes: <i>host test</i> (the portable C core "
      "executed on a PC against deterministic synthetic inputs), <i>simulation</i> (numerical experiments that drive the real firmware "
      "estimator code with an assumed sensor model), <i>compile check</i> (a Zephyr build for the target board) and <i>author-reported</i> "
      "(Simulink results reproduced from the repository README, not independently reproducible). Statements in this paper never promote a result "
      "to a higher class than the evidence supports.")

    # -------------------------------------------------------------- IV Architecture
    S("System Architecture", "arch")
    B("{fig:system} shows the per-sample signal flow. The IMU delivers samples at 208 Hz through a data-ready interrupt. The control "
      "thread validates each sample, runs the EKF and the LQR, and posts the servo command to a depth-one mailbox. A lower-priority "
      "actuation thread consumes the latest command, applies the actuator guard and generates the 50 Hz PWM output. A supervisor "
      "thread feeds the hardware watchdog only while both loops make progress. Four design principles follow from the audit.")
    P.bullets([
        "<b>Defined safe state.</b> A neutral pose (90° on both servos) held with the PWM energised is preferred to de-energised servos, "
        "which would let the head fall and spill; the actuator never acts on an estimate the monitor has not accepted.",
        "<b>Preserve working numerics.</b> The refactored estimator and controller reproduce the original outputs bit-for-bit on valid data, so prior "
        "results are not invalidated ({sec:results}).",
        "<b>Portable core.</b> Estimation, control, calibration and safety logic is plain C99 with no RTOS dependency, so it can be tested on a host "
        "with sanitizers; Zephyr-specific code is confined to glue modules.",
        "<b>Honest evidence.</b> Requirements, tests and claims are tied to evidence classes, and anything not measured is labelled as such.",
    ])
    P.figure(FIG / "p_system.png", "Signal flow per IMU sample, from the LSM6DS3 through monitoring, EKF, LQR and actuator guard to the servos. Architecture diagram, not data.",
             "system", wide=True)

    # -------------------------------------------------------------- V Hardware
    S("Hardware Design", "hw")
    SUB("Components and documented parameters")
    B("{tab:hw} lists the hardware as documented in the repository. Items the repository does not document are marked unknown rather "
      "than assumed; no schematic, bill of materials, supply, battery or current data are present.")
    P.table("Hardware as documented in the repository", "hw",
            ["Item", "Content", "Source / status"],
            [["MCU board", "Seeed XIAO nRF52840 Sense (Cortex-M4F) {c:nrf52840}", "README, device tree"],
             ["IMU", "LSM6DS3 {c:lsm6ds3}: ±16 g, ±2000 dps, 208 Hz ODR (gyro LSB ≈ 70 mdps)", "firmware configuration"],
             ["Roll servo", "MG995 (README); owner notes elsewhere cite MG92B", "<b>inconsistent</b> — unresolved"],
             ["Pitch servo", "FS90MG", "README"],
             ["Servo drive", "50 Hz PWM; roll 722–2278 µs, pitch 900–2100 µs; neutral 90°", "device tree"],
             ["RTOS / SDK", "Zephyr v4.0.0 {c:zephyr}, board xiao_ble/nrf52840/sense", "build files"],
             ["IMU mounting vs. gimbal pivots", "unknown", "not documented (D-20)"],
             ["Schematic, BOM, supply, battery, current draw", "unknown", "not in repository"]],
            widths=[1.2, 1.9, 1.1])
    P.figure(FIG / "p_hardware.png", "Hardware block diagram as documented. Dashed or marked items are unknown or unmeasured (supply, mounting, servo model).", "hw")
    SUB("Mechanical concept and the mounting question")
    B("{fig:mech} sketches the concept: a handle carries the electronics, and two orthogonal servos tilt the spoon head about roll and pitch "
      "axes to counter handle tilt. Where the IMU is mounted determines the loop topology. With the IMU on the hand-side body it measures the "
      "<i>disturbance</i> and the loop is feed-forward: the servo angles are computed to cancel the measured tilt, and any error in the servo "
      "response appears directly as residual motion. With the IMU on the stabilised spoon it measures the <i>residual</i> and the loop is "
      "feedback, which can correct servo error but is limited in bandwidth by loop delay {c:astrom08,skogestad05}. The repository does not state which "
      "applies (audit D-20), so we analyse both where it matters ({sec:disc}) and do not assume one.")
    P.figure(FIG / "p_mechanical.png", "Illustrative mechanical concept (not to scale; geometry, masses and IMU position are not documented).", "mech")
    SUB("Power and electrical considerations")
    B("The device is battery powered and drives two hobby servos whose stall and transient currents are typically far above the "
      "microcontroller’s own consumption; the servo and logic supply arrangement is not documented. Three consequences are relevant and, at present, "
      "unquantified: supply droop during servo transients can brown out the MCU; a stalled or obstructed servo draws high current and heats; and "
      "battery runtime depends on the average duty of both servos, i.e.")
    P.eq(r"t_{run} \approx \frac{E_{batt}\,\eta}{P_{avg}}", "runtime")
    P.eq(r"P_{avg} = P_{mcu} + P_{imu} + \overline{P_{servo}}", "pavg")
    B("with every term unknown today. {fig:power} shows the power and boot state flow that <i>is</i> implemented (neutral-first, "
      "validation-gated, watchdog-supervised); no supply, current or thermal sensing exists (risks R-01 and R-02, {tab:risks}). "
      "Design recommendations that follow from the analysis, not yet implemented or verified, are a servo supply separate from the logic rail with "
      "a common ground, bulk capacitance sized from measured transient current, and a supply-voltage ADC channel feeding the monitor.")
    P.figure(FIG / "p_power_states.png", "Power and boot state flow as implemented. Stall and brown-out are not detectable with the current hardware.", "power")

    # -------------------------------------------------------------- VI Acquisition & calibration
    S("Sensor Acquisition and Calibration", "acq")
    SUB("Acquisition and timing")
    B("The IMU is configured for 208 Hz with ±16 g and ±2000 dps full scale. The data-ready handler timestamps each sample with the 32-bit "
      "cycle counter, checks fetch status and stores the latest sample under a spinlock together with a sequence number, so that the control "
      "thread never reads a torn sample and missed samples are counted. The original firmware derived the time step from a 1 ms "
      "timestamp, which quantises a nominal 4.808 ms period to 4 or 5 ms ({fig:dtq}). The updated firmware computes")
    P.eq(r"\Delta t_k = (c_k - c_{k-1}) / f_{cpu}", "dt")
    B(f"with unsigned wrap-safe subtraction and rejects any step outside [0.5, 20] ms. For the baseline, 80.8 % of steps use 5 ms and 19.2 % use 4 ms, giving a per-step "
      f"integration scale of {dt_lo:.3f}–{dt_hi:.3f} with an unbiased mean of {dt_mean:.4f} ms: the quantisation adds jitter to the estimate "
      "but no net bias.")
    P.figure(FIG / "p_dt_quant.png", "Baseline time-step quantisation. A 4.808 ms sample period seen through a 1 ms clock yields 4 or 5 ms steps (analytic).", "dtq")
    SUB("Boot-time calibration")
    B("At boot the device must be held level and still. 624 samples (3 s) are accumulated with Welford’s online mean and variance {c:welford62}. "
      "The attempt is accepted only if, for each gyroscope axis <i>i</i>,")
    P.eq(r"\sigma_{g,i} \le 0.02\ \mathrm{rad/s}", "cal1")
    P.eq(r"\left|\lVert\bar a\rVert - g\right| \le 0.5\ \mathrm{m/s^2},\quad |\bar a_x|,|\bar a_y| \le 1.5\ \mathrm{m/s^2}", "cal")
    B("where the last bound corresponds to a tilt of about 8.8°. The offsets are the gyroscope means, the x and y accelerometer means "
      "and (ā<sub>z</sub> − g). Up to three attempts are made; after the third failure the device latches a fault and the servos stay at neutral "
      "({fig:cal}). The original firmware accepted any calibration data, so a moving or tilted board silently produced wrong offsets (D-12). "
      "These thresholds are engineering choices ({tab:params}); they have been exercised with synthetic data only.")
    P.figure(FIG / "p_calibration.png", "Boot calibration with acceptance checks, retry logic and latched failure (design diagram).", "cal")
    P.table("Principal parameters and rationale (defaults are engineering choices unless stated)", "params",
            ["Parameter", "Value", "Rationale"],
            [["Q, R, K<sub>lqr</sub>, max. pitch", "0 (placeholders)", "device-specific; not in repo. Boot validation refuses zeros"],
             ["IMU ODR / ranges", "208 Hz; ±16 g; ±2000 dps", "original configuration; coarse gyro LSB (D-18)"],
             ["Δt bounds", "0.5–20 ms", "around 4.81 ms nominal; &gt; 4 periods = missed samples"],
             ["Stuck-sensor threshold", "32 identical raw samples", "frozen bus; MEMS noise makes it implausible"],
             ["Trip / recover", "10 bad (≈ 48 ms) / 208 good (≈ 1 s)", "ride out glitches; avoid chatter"],
             ["Angle plausibility", "|φ|, |θ| ≤ 80°", "accelerometer angle ill-conditioned near 90° pitch"],
             ["Hold / command timeout", "100 ms / 50 ms", "≈ half a 5 Hz period; ≈ 10 control periods"],
             ["Safe slew; run slew", "60 °/s; 0 (off)", "gentle return; a limit would add phase lag"],
             ["Calibration", "624 samples; 3 attempts", "3 s as original; then latch fault"]],
            widths=[1.2, 1.1, 1.9], size=7)

    # -------------------------------------------------------------- VII Estimation
    S("Orientation Estimation", "est")
    SUB("Measurement model")
    B("After offset subtraction the body-frame specific force is <i>a</i> = (a<sub>x</sub>, a<sub>y</sub>, a<sub>z</sub>) and the angular rate "
      "is ω = (<i>p</i>, <i>q</i>, <i>r</i>). Roll φ and pitch θ are ZYX Euler angles. When the specific force equals gravity, the accelerometer gives")
    P.eq(r"\phi_a = \mathrm{atan2}(a_y, a_z)", "acc")
    P.eq(r"\theta_a = \mathrm{atan2}\!\left(-a_x, \sqrt{a_y^2 + a_z^2}\right)", "acc2")
    B("During tremor the hand accelerates and the measured force contains a linear-acceleration term. For rotation about the pivot with the IMU offset "
      "by <i>L</i> along the body z axis, the tangential component for a sinusoidal roll φ = φ<sub>0</sub> sin(2π<i>f</i>t) is "
      "<i>L</i>(2π<i>f</i>)²φ<sub>0</sub>, i.e. it adds <i>L</i>(2π<i>f</i>)²/<i>g</i> to the relative amplitude of the accelerometer angle. For <i>L</i> = 0.06 m "
      "and <i>f</i> = 5 Hz this ratio is 6.0, so the accelerometer angle is an unreliable tremor-band measurement and the filter must lean on the gyroscope.")
    SUB("Extended Kalman filter", "ekf")
    B("The filter follows the standard extended Kalman formulation {c:kalman60,gelb74,simon06}. The state is <b>x</b> = [φ, θ]<sup>T</sup>. The prediction integrates the "
      "Euler-angle kinematics driven by the measured rates:")
    P.eq(r"\dot\phi = p + (q\sin\phi + r\cos\phi)\tan\theta", "k1")
    P.eq(r"\dot\theta = q\cos\phi - r\sin\phi", "k2")
    B("With the measured step Δt, <b>x</b><sup>−</sup> = <b>x</b> + <b>f</b>(<b>x</b>, ω)Δt, and the transition matrix is "
      "<b>F</b> = <b>I</b> + <b>A</b>Δt with the analytic Jacobian")
    P.eq(r"A = \begin{bmatrix} (q c_\phi - r s_\phi)\tan\theta & (q s_\phi + r c_\phi)\sec^2\theta \\ -q s_\phi - r c_\phi & 0 \end{bmatrix}", "jac")
    B("where sec²θ is limited when |cosθ| &lt; 0.01. The covariance is propagated with a scalar process-noise level <i>q</i>, and the "
      "accelerometer angles are the measurement <b>z</b> = [φ<sub>a</sub>, θ<sub>a</sub>]<sup>T</sup> with <b>H</b> = <b>I</b><sub>2</sub> and "
      "<b>R</b> = <i>r</i><b>I</b><sub>2</sub>:")
    P.eq(r"P^- = F P F^{T} + q I_2", "pred")
    P.eq(r"S = P^- + r I_2,\quad K = P^- S^{-1}", "gain")
    P.eq(r"x = x^- + K(z - x^-),\quad P = (I - K)P^-", "upd")
    P.figure(FIG / "p_ekf_structure.png", "EKF structure as implemented: predict from gyroscope rates, update from accelerometer angles, with input and output guards.", "ekfs")
    SUB("Numerical safeguards", "num")
    B("The implementation rejects non-finite inputs and Δt outside the bound, guards the 2×2 inverse with a determinant test "
      "(det <b>S</b> &gt; 10<sup>−30</sup>), symmetrises <b>P</b> (the product (<b>I</b> − <b>K</b>)<b>P</b><sup>−</sup> drifts from symmetry in single precision), and "
      "works on copies so that a rejected update leaves the filter state unchanged. Configuration is validated at initialisation "
      "(<i>q</i> ≥ 0, <i>r</i> &gt; 0, 0 &lt; max pitch &lt; π/2). With the shipped values <i>q</i> = <i>r</i> = 0 the legacy filter reaches P → 0, then det <b>S</b> = 0 and a division "
      "by zero, giving a NaN estimate permanently (D-01); this is reproduced in the host tests ({sec:results}). An optional acceleration-norm gate "
      "inflates <i>r</i> by 100 when | ‖<i>a</i>‖ − <i>g</i> | exceeds 3 m/s²; it is implemented but disabled by default because simulation shows it is not uniformly beneficial.")
    SUB("Steady-state behaviour: a complementary filter", "ss")
    B("For small angles <b>F</b> ≈ <b>I</b> and each axis is a scalar random-walk filter. Setting P<sup>−</sup> = P + <i>q</i> and P = (1 − K)P<sup>−</sup> gives "
      "P<sup>−</sup>² = <i>q</i>P<sup>−</sup> + <i>qr</i>, so")
    P.eq(r"P^-_{ss} = \frac{q + \sqrt{q^2 + 4qr}}{2}", "pss")
    P.eq(r"K_{ss} = \frac{P^-_{ss}}{P^-_{ss} + r}", "kss")
    B("The recursion φ̂<sub>k</sub> = (1 − K)(φ̂<sub>k−1</sub> + ωΔt) + Kφ<sub>a,k</sub> is a first-order complementary filter {c:euston08}: the gyroscope path is "
      "high-passed and the accelerometer path low-passed with pole (1 − K), i.e. time constant and corner")
    P.eq(r"\tau = \frac{-\Delta t}{\ln(1 - K_{ss})} \approx \frac{\Delta t}{K_{ss}}", "tau")
    P.eq(r"f_c = \frac{1}{2\pi\tau} = \frac{-\ln(1 - K_{ss})}{2\pi\,\Delta t}", "fc")
    tun_rows = [[k, f"{TUN[k][0]:.0e}", f"{TUN[k][1]:.0e}", f"{kss(*TUN[k]):.5f}", f"{FC[k]:.3f}", f"{-DT / np.log(1 - kss(*TUN[k])):.2f}"] for k in TUN]
    P.table("Steady-state gain and accelerometer corner for the four simulated tunings (analytic; Δt = 1/208 s)", "fc",
            ["Tuning", "<i>q</i>", "<i>r</i>", "<i>K</i><sub>ss</sub>", "<i>f</i><sub>c</sub> (Hz)", "τ (s)"], tun_rows,
            widths=[0.6, 0.7, 0.7, 0.8, 0.8, 0.6])
    B("{tab:fc} and {fig:ekfbw} show that for every tuning studied the accelerometer corner (0.01–0.33 Hz) lies one to three orders of magnitude below the 3–8 Hz tremor band. "
      "At tremor frequencies the estimate is therefore essentially the integrated gyroscope signal, and the accelerometer only sets the "
      "slow tilt reference and corrects drift. Two consequences follow: tremor-band estimate quality is governed by gyroscope scale, noise, "
      "residual bias and the integration scheme rather than by fine tuning of <i>q</i> and <i>r</i>; and any accelerometer corruption is attenuated by roughly "
      "<i>f</i><sub>c</sub>/<i>f</i>, but is not removed.")
    P.figure(FIG / "p_ekf_bandwidth.png", "Accelerometer-path corner frequency <i>f</i><sub>c</sub> versus process-noise level <i>q</i> for several measurement-noise levels <i>r</i> (analytic), with the tremor band shaded.", "ekfbw")
    SUB("Integration lead and lever-arm lag", "lag")
    B("Two analytic effects explain the simulation results of {sec:results}. First, the filter integrates the sample ω<sub>k</sub> over the interval "
      "(<i>t</i><sub>k−1</sub>, <i>t</i><sub>k</sub>], a backward-rectangular rule whose frequency response is Δt/(1 − e<sup>−jωΔt</sup>): unit gain to second order and a "
      "phase <i>lead</i> of Δt/2 = 2.40 ms at 208 Hz. For a sinusoid of amplitude <i>A</i> this produces an RMS estimate error")
    P.eq(r"e_{rms} \approx \frac{A}{\sqrt 2}\,2\pi f\,\frac{\Delta t}{2}", "lead")
    B("which is 0.161°, 0.268° and 0.429° at 3, 5 and 8 Hz for <i>A</i> = 5°. Second, the lever-arm term above enters through the low-pass "
      "H<sub>a</sub>(e<sup>jωΔt</sup>) = K/(1 − (1 − K)e<sup>−jωΔt</sup>). Writing the estimate as the true tilt plus the low-passed accelerometer error,")
    P.eq(r"\frac{\hat\phi}{\phi} \approx 1 + H_a\,\frac{L(2\pi f)^2}{g}", "lagr")
    P.eq(r"\tau_{lag} = -\frac{\arg(\hat\phi/\phi)}{2\pi f} - \frac{\Delta t}{2}", "lagm")
    B("Because H<sub>a</sub> is nearly in quadrature at tremor frequencies, the lever-arm term appears mainly as a phase (lag), not a gain, error, which is why "
      "estimate gain stays within a few percent while lag reaches 16 ms in the worst case ({tab:lag}). The model is a first-order approximation: it ignores the "
      "pitch-axis excitation, centripetal terms and the covariance dynamics.")
    P.figure(FIG / "p_zoh.png", "Magnitude and phase of a zero-order hold of period 20 ms (50 Hz PWM frame) and 4.8 ms (208 Hz command), analytic; tremor band shaded.", "zoh")
    SUB("Relation to the Simulink model", "sl")
    B("The authors’ MATLAB/Simulink model is the source of the repository’s performance figures, but it differs from the firmware "
      "in ways that matter ({tab:slfw}). Its EKF has four states, including gyroscope bias, and subtracts the bias from the rates; the firmware has two "
      "states and relies on the boot-time offset. The LQR script zeroes the rate states, whereas the firmware feeds the measured rates. The model runs at 1 kHz; "
      "the firmware at 208 Hz with a 50 Hz PWM output. Simulink results therefore describe a related, not identical, system (D-14, D-19).")
    P.table("Differences between the Simulink model and the deployed firmware", "slfw",
            ["Aspect", "Simulink model (author-reported)", "Firmware (this work)"],
            [["EKF states", "4 (angles + gyro bias)", "2 (angles); boot offset only"],
             ["LQR rate states", "zeroed in script", "measured gyro rates p, q"],
             ["Rate", "1 kHz", "208 Hz control; 50 Hz PWM"],
             ["Plant parameters", "not in repository", "not in repository"],
             ["Actuator model", "not stated", "PWM, guard, slew limit"],
             ["Load", "50 g of food", "unknown"]],
            widths=[1.0, 1.6, 1.6])

    # -------------------------------------------------------------- VIII Control
    S("Control Design", "ctl")
    SUB("Plant model and LQR")
    B("Each axis is modelled as a rate-damped inertia driven by servo torque. With state <b>x</b> = [φ, <i>p</i>, θ, <i>q</i>]<sup>T</sup> and input "
      "<b>u</b> = [u<sub>φ</sub>, u<sub>θ</sub>]<sup>T</sup>, the continuous model is block-diagonal:")
    P.eq(r"\dot x = A_c x + B_c u", "plant")
    P.eq(r"A_c = \mathrm{diag}(A_\phi, A_\theta),\quad B_c = \mathrm{diag}(b_\phi, b_\theta)", "plant1")
    P.eq(r"A_i = \begin{bmatrix}0&1\\0&-\alpha_i\end{bmatrix},\quad b_i = \begin{bmatrix}0\\ \beta_i\end{bmatrix}", "plant2")
    B("discretised by zero-order hold at the control period {c:franklin98,astrom97}. The cost is J = Σ(<b>x</b><sup>T</sup><b>Qx</b> + <b>u</b><sup>T</sup><b>Ru</b>) with "
      "Bryson-style weights {c:bryson75}")
    P.eq(r"Q = \mathrm{diag}\!\left(\tfrac{W_\phi}{\phi_{max}^2}, \tfrac{1}{p_{max}^2}, \tfrac{W_\theta}{\theta_{max}^2}, \tfrac{1}{q_{max}^2}\right)", "costq")
    P.eq(r"R = \mathrm{diag}\!\left(\tfrac{1}{u_{\phi,max}^2}, \tfrac{1}{u_{\theta,max}^2}\right)", "costr")
    B("and the gain <b>K</b> ∈ ℝ<sup>2×4</sup> solves the discrete algebraic Riccati equation (dlqr) {c:anderson90}, giving")
    P.eq(r"u = -K x", "lqr")
    B("The plant parameters (masses, radii, servo torque, damping, weights) are blank in the repository script, so <b>K</b> cannot be regenerated, and the "
      "numerical gain of the original experiments is unavailable. The firmware therefore treats <b>K</b> as a configuration input, validates it "
      "({sec:safety}) and refuses to actuate while it is invalid.")
    P.figure(FIG / "p_lqr_arch.png", "Controller structure: EKF angles and offset-corrected gyro rates form the state fed to <i>u</i> = −<i>Kx</i>, then the servo mapping and the actuator guard.", "lqrarch")
    SUB("Servo mapping and actuator guard")
    B("Commands are mapped to servo angles about the 90° neutral as")
    P.eq(r"\delta_{roll} = 90^\circ - \tfrac{180}{\pi}u_\phi", "servo1")
    P.eq(r"\delta_{pitch} = 90^\circ + \tfrac{180}{\pi}u_\theta", "servo")
    B("then passed through the actuator guard ({sec:safety}) and converted to a pulse width: pulse = p<sub>min</sub> + (p<sub>max</sub> − p<sub>min</sub>)δ/180°, clamped at both "
      "ends, with non-finite inputs mapped to neutral. Each microsecond of pulse corresponds to 0.116° (roll) and 0.150° (pitch); the resolution of the underlying PWM "
      "timer is not documented in the repository, so command quantisation is bounded only by that figure. A slew limit exists but is off by default "
      "(0 °/s) to preserve the original dynamics; the fault-return slew is 60 °/s.")
    SUB("Actuation and delay", "delay")
    B("Commands are issued at up to 208 Hz but the PWM frame is 20 ms, so the servo sees a zero-order hold of the command with magnitude and phase")
    P.eq(r"|H_{zoh}(f)| = |\mathrm{sinc}(fT)|,\quad \mathrm{sinc}(x) = \frac{\sin(\pi x)}{\pi x}", "zohm")
    P.eq(r"\angle H_{zoh}(f) = -\pi f T", "zoh")
    B("which for <i>T</i> = 20 ms gives −0.05, −0.14 and −0.37 dB and phase −10.8°, −18.0° and −28.8° at 3, 5 and 8 Hz ({fig:zoh}). More important than the magnitude is "
      "the delay. In a feed-forward arrangement that commands the cancelling angle with a total delay τ, the residual relative amplitude is")
    P.eq(r"\left|1 - e^{-j2\pi f\tau}\right| = 2\left|\sin(\pi f\tau)\right|", "res")
    B("so a reduction of 90 % (the repository’s stated target) requires τ ≤ 5.3, 3.2 and 2.0 ms at 3, 5 and 8 Hz, and 80 % requires τ ≤ 10.6, 6.4 and 4.0 ms "
      "({fig:dlim}, {tab:dlim}). The 4.81 ms sample period plus an up-to-20 ms PWM frame bound the known part of the delay to 24.8 ms, "
      "for which the best case is 54 %, 24 % and −17 % (amplification) at 3, 5 and 8 Hz. This is an illustrative first-order bound, not a prediction of device "
      "performance: it neglects servo dynamics, assumes a feed-forward topology and a pure delay, and the average zero-order-hold delay is half the frame. It nevertheless "
      "identifies the 20 ms PWM frame (D-16) as the highest-value open measurement and design question ({sec:disc}).")
    P.figure(FIG / "p_delay_limit.png", "Best-case tremor reduction of a feed-forward canceller with pure delay τ, 1 − 2|sin(π<i>f</i>τ)|, with the 80 % and 90 % lines of the repository dotted (analytic).", "dlim")
    dl = NUM["delay"]
    P.table("Delay-limited best-case reduction (%) of a feed-forward canceller (analytic; illustrative, not device data)", "dlim",
            ["Total delay τ", "3 Hz", "5 Hz", "8 Hz"],
            [[k.replace("ms", " ms"), *[f"{dl[k][f'{f}Hz']:.1f}" for f in (3, 5, 8)]] for k in ("2.0ms", "5.0ms", "10.0ms", "24.8ms")]
            + [["τ for 90 % (ms)", *[f"{dl['tau_for_90pct_ms'][f'{f}Hz']:.2f}" for f in (3, 5, 8)]],
               ["τ for 80 % (ms)", *[f"{dl['tau_for_80pct_ms'][f'{f}Hz']:.2f}" for f in (3, 5, 8)]]],
            widths=[1.4, 0.9, 0.9, 0.9])

    # -------------------------------------------------------------- IX Firmware
    S("Firmware and Real-Time Implementation", "fw")
    B("The firmware targets xiao_ble/nrf52840/sense under Zephyr v4.0.0 {c:zephyr}. It is organised in seven modules — sensors, estimation, control, "
      "actuation, safety, application and common — with a portable C99 core (EKF, LQR, control step, calibration, monitor, guard, timing) that has no RTOS "
      "dependency and is compiled and tested on a host. {fig:fw} shows the module and thread structure and {tab:threads} the tasks.")
    P.figure(FIG / "p_firmware.png", "Firmware architecture: portable core (left), Zephyr glue (middle) and hardware (right); threads and data hand-off paths.", "fw", wide=True)
    P.table("Threads and hand-off paths", "threads",
            ["Task", "Role", "Notes"],
            [["IMU data-ready handler", "timestamp, fetch, store latest sample", "spinlock + sequence number (D-05)"],
             ["Control thread (priority 1)", "monitor → EKF → LQR → command", "decimated telemetry (1 in 26)"],
             ["Mailbox (depth 1)", "latest command wins", "replaces depth-20 FIFO (D-08)"],
             ["Actuation thread (priority 5)", "guard → PWM", "neutral output before estimation starts"],
             ["Supervisor thread", "feeds nRF52 watchdog (500 ms)", "only if both heartbeats advance"]],
            widths=[1.2, 1.5, 1.5])
    SUB("Boot sequence")
    B("Order matters for safety. (1) The actuation thread starts and drives neutral. (2) The watchdog is armed. (3) Tuning constants are "
      "validated. (4) The IMU is initialised. (5) Calibration runs, with up to three attempts. (6) The control thread starts. (7) Actuation is enabled "
      "<i>only</i> if validation and calibration both succeeded; otherwise the servos stay at neutral and a fault is logged. The original firmware ran 11 s "
      "of boot and calibration with no PWM output at all (D-13).")
    SUB("Timing budget and footprint")
    B("{fig:lat} gives the latency budget. Only two terms are known analytically — the 4.81 ms sample period and the 0–20 ms PWM frame wait — and the "
      "compute, scheduling and servo response terms are not measured; measuring them is TC-HW-002/003 ({tab:hwtests}). Blocking console output, which the "
      "original control loop performed per sample, was replaced with decimated telemetry, but its latency effect was not measured either. {tab:foot} gives the build "
      "footprint (compile check against Zephyr v4.0.0 with the arm-none-eabi toolchain; not a hardware run). Jitter, CPU load, stack use and interrupt "
      "latency have not been measured.")
    P.figure(FIG / "p_latency_budget.png", "Latency budget. Known terms are analytic; unmeasured terms are marked (analytic bound, no hardware data).", "lat")
    P.table("Build facts (compile check only)", "foot",
            ["Build", "Flash (B)", "RAM (B)"],
            [["Baseline (main) firmware", "86 696 (10.74 %)", "22 592 (8.62 %)"],
             ["Updated firmware", "92 772 (11.50 %)", "25 560 (9.75 %)"],
             ["Updated, LED-test configuration", "90 164 (11.17 %)", "24 536 (9.36 %)"]],
            widths=[1.8, 1.2, 1.2])

    # -------------------------------------------------------------- X Safety
    S("Safety Architecture", "safety")
    B("The design principle is that a defined neutral pose, held with the PWM energised, is the safe state for a food-carrying spoon. The layers are "
      "boot gating, the input monitor, the actuator guard and supervision; {tab:faults} lists every fault considered, its detection, response and verification.")
    SUB("Input monitor")
    B("Each IMU sample is checked for non-finite values, out-of-range values (|a| &gt; 16 g, |ω| &gt; 2000 dps), a stuck sensor (32 bit-identical raw samples), a "
      "time step outside [0.5, 20] ms and a data timeout; the EKF output is checked for numeric failure and for |φ| or |θ| beyond 80°. Ten consecutive bad "
      "samples (≈ 48 ms) invalidate the output; 208 good samples (≈ 1 s) are required to recover. The thresholds are engineering choices ({tab:params}).")
    SUB("Actuator guard", "guard")
    B("The guard is the single point at which servo commands reach the PWM. It clamps to the servo range, rejects non-finite commands, and implements the three-state "
      "machine of {fig:guard}. On an invalid command it holds the last good output for at most 100 ms, then slews to 90° at 60 °/s and holds; it resumes only "
      "after 208 consecutive valid commands, and re-entry is rate-limited. With the slew rate limit <i>s</i>, each step moves the output by")
    P.eq(r"y_k = y_{k-1} + \mathrm{clip}\!\left(u_k - y_{k-1},\, -s\Delta t,\, +s\Delta t\right)", "slew")
    P.figure(FIG / "p_guard_states.png", "Actuator-guard state machine: ACTIVE, HOLD (≤ 100 ms) and SAFE_NEUTRAL, with recovery after 208 valid commands.", "guard")
    SUB("Supervision")
    B("The actuation thread declares a missing command after 50 ms. A supervisor thread feeds the nRF52 watchdog (500 ms timeout) only if both the control and actuation "
      "heartbeats advance, so a hang in either loop causes a reset, after which the servos are levelled at boot. This path is implemented and compiled but "
      "has not been run on hardware, and the duration for which servos are unpulsed across a reset is unknown.")
    P.table("Fault handling and its verification", "faults",
            ["Fault", "Detection", "Response", "Implemented", "Verified"],
            [["IMU failure / no data", "50 ms timeout", "HOLD ≤ 100 ms → neutral", "yes", "host test (sim)"],
             ["Non-finite / out-of-range sample", "per-sample check", "reject; assert after 10 → neutral", "yes", "host test"],
             ["Stuck sensor (bit-identical × 32)", "per-sample", "as above", "yes", "host test"],
             ["Bad timing (Δt ∉ [0.5, 20] ms)", "per-sample", "as above", "yes", "host test"],
             ["EKF numeric failure", "status + finite checks", "reset from accel; assert → neutral", "yes", "host test"],
             ["Implausible estimate (|angle| &gt; 80°)", "per-estimate", "as above", "yes", "host test"],
             ["Excessive / NaN command", "guard clamp, finite check", "clamp to range; NaN → hold", "yes", "host test"],
             ["Invalid tuning (Q, R, K, max pitch)", "boot validation", "never actuate; neutral", "yes", "host test"],
             ["Failed calibration", "stillness / level / gravity; 3 attempts", "never actuate; neutral", "yes", "host test"],
             ["Firmware hang / crash", "watchdog, both loops", "SoC reset → neutral at boot", "yes", "<b>compiled only</b>"],
             ["Servo stall / disconnect / obstruction", "—", "—", "<b>no</b> (no sensing)", "—"],
             ["Battery under-voltage / supply droop", "—", "—", "<b>no</b> (no ADC path)", "—"],
             ["Excessive heating", "—", "—", "<b>no</b> (no sensing)", "—"],
             ["User-visible fault indication", "—", "—", "<b>no</b> (calibration LED only)", "—"]],
            widths=[1.9, 1.5, 1.7, 1.0, 1.0], size=7, wide=True)
    SUB("Hazards and open risks")
    B("A hazard analysis informed by {c:iso14971} (a structuring reference, not a compliance claim) identifies spill or injury from loss of control, resistance to intentional "
      "movement, actuator overdrive or stall, power failure, wrong calibration or tuning, and an undetected degraded state. {tab:risks} lists the risks that remain "
      "open after mitigation: they are open risks, not mitigated ones.")
    P.table("Open risks after the implemented mitigations", "risks",
            ["ID", "Risk", "Status"],
            [["R-01", "Servo stall / jam undetected (no sensing)", "open; TC-HW-010 NOT RUN"],
             ["R-02", "Supply droop / brown-out unmonitored", "open; TC-HW-004 NOT RUN"],
             ["R-03", "Opposition to voluntary motion unquantified", "open (design gap D-15)"],
             ["R-04", "No user-visible fault indication", "open; not implemented"],
             ["R-05", "Full 0–180° servo range not validated against gimbal limits", "open; TC-HW-009 NOT RUN"],
             ["R-06", "Recovery and hold timings are engineering choices", "unvalidated"],
             ["R-07", "Watchdog behaviour unobserved on hardware", "TC-HW-005/006 NOT RUN"]],
            widths=[0.4, 2.3, 1.5])
    P.figure(FIG / "p_guard_trace.png", "Fault-injection trace of the real guard code at 208 Hz: a 40 ms burst gives HOLD only and a rate-limited re-entry; a 1.5 s fault reaches SAFE_NEUTRAL and slews to 90° (host simulation).", "gtrace")

    # -------------------------------------------------------------- XI Methodology
    S("Experimental Methodology", "method")
    SUB("Evidence generated so far")
    B("Three evidence classes exist today ({tab:ev}); none is a hardware performance test. The Simulink results come from the authors’ model; the repository contains "
      "the exported PDF and result plots but not the <tt>.slx</tt> file or the plant parameters, so they are reproduced here as author-reported.")
    P.table("Evidence classes used in this report", "ev",
            ["Class", "What was done", "What it can support"],
            [["Host tests", "Portable core built with -Wall -Wextra -Wpedantic -Wshadow -Wconversion (sign conversion excluded) -Werror, ASan/UBSan; deterministic synthetic inputs; regression vs. the original EKF; cppcheck and clang-format", "Logic, numerical robustness, fault handling"],
             ["Estimator simulation", "Real firmware EKF code driven by a batch harness: 5° roll (3° pitch) sinusoid, random phases, 3–8 Hz, lever 0–0.10 m along body z, 15 s, 10 seeds, four tunings; noise density 0.9 mg/√Hz (accel), 0.007 dps/√Hz (gyro), residual gyro bias ≈ 0.01 dps", "Relative estimator behaviour under stated assumptions"],
             ["Compile check", "Zephyr v4.0.0 build for the target board", "Buildability, footprint"]],
            widths=[0.9, 2.3, 1.0], size=7)
    SUB("Metrics")
    B("For an uncompensated motion of RMS amplitude <i>X</i><sub>ref</sub> and residual RMS <i>X</i><sub>res</sub> at the same frequency, reduction and its decibel form are")
    P.eq(r"\rho = 1 - \frac{X_{res}}{X_{ref}}", "rho")
    P.eq(r"G_{dB} = 20\log_{10}\frac{X_{res}}{X_{ref}}", "gdb")
    B("Estimator quality is reported as RMS error over the last 10 s of each 15 s run (to exclude the transient), and as gain and lag from a least-squares sinusoid fit at the "
      "excitation frequency. Reduction as defined by {eq:rho} is not an estimator metric and is used only for the author-reported Simulink results.")
    SUB("Planned bench protocol (not executed)", "bench")
    B("The hardware protocol of {fig:setup} and {tab:hwtests} is planned, not run. A motor-driven tremor rig applies known roll/pitch motion; a reference IMU on the spoon bowl and one on the "
      "hand-side body log at ≥ 1 kHz on a synchronised clock; input and residual RMS are computed per frequency (3–8 Hz), amplitude (2–7°) and axis with ≥ 5 repeats and "
      "reported as mean ± SD with confidence intervals; a slow 0.2–1 Hz commanded rotation measures resistance to intentional motion; and end-to-end latency is measured with GPIO "
      "toggles at sample arrival and PWM update on a logic analyser. User trials require prior ethics approval.")
    P.figure(FIG / "p_test_setup.png", "Planned bench protocol. <b>Not executed:</b> no data are shown.", "setup")
    P.table("Planned hardware and rig verification cases (all NOT RUN)", "hwtests",
            ["Case", "Procedure", "Output"],
            [["TC-HW-001", "log data-ready timestamps ≥ 10 min", "ODR, jitter, drops"],
             ["TC-HW-002", "GPIO at sample arrival and PWM update", "latency distribution"],
             ["TC-HW-003", "servo step response with real linkage and load", "rise time, overshoot"],
             ["TC-HW-004", "supply rail on scope during transients", "droop, ripple, brown-out margin"],
             ["TC-HW-005/006", "forced loop hang; power-cycle with PWM on scope", "reset ≤ 500 ms; time to first pulse"],
             ["TC-HW-007", "disconnect IMU during run", "SAFE_NEUTRAL ≤ 150 ms; pose at 90°"],
             ["TC-HW-008", "continuous run on battery", "runtime, V(t)"],
             ["TC-PERF-001/002", "tremor rig 3–8 Hz × 2–7°, reference IMU", "input/residual RMS, phase"],
             ["TC-PERF-003", "slow 0.2–1 Hz rotation", "resistance to voluntary motion"],
             ["TC-PERF-005", "≥ 1 h soak", "0 faults / resets"]],
            widths=[0.9, 2.0, 1.3], size=7)

    # -------------------------------------------------------------- XII Results
    S("Results and Performance Analysis", "results")
    SUB("Host tests (evidence class: host test)")
    P.table(f"Host test outcomes ({TOTAL_CHECKS:,} checks, 0 failures)", "host",
            ["Test program", "Checks", "Failures"],
            [["EKF, incl. comparison with the legacy EKF", f"{CHK['test_ekf']:,}", "0"], ["LQR, timing, calibration", f"{CHK['test_lqr_timing_cal']:,}", "0"],
             ["Safety monitor and guard", f"{CHK['test_safety']:,}", "0"], ["Control-step integration", f"{CHK['test_control']:,}", "0"]],
            widths=[2.5, 0.9, 0.8])
    P.bullets([
        "With the shipped Q = R = 0 the legacy EKF returns NaN after 5 updates; the updated EKF rejects the configuration at initialisation.",
        "Updated versus legacy EKF on 6000 valid samples: maximum difference 0.000° (bit-identical).",
        "With IMU data lost, the guard enters SAFE_NEUTRAL after 20 control steps (96.2 ms), within the proposed 150 ms limit; the pose then slews at 60 °/s.",
        "Accelerometer-burst stress test: gated EKF mean |roll error| 0.264° versus 15.644° ungated in the burst window (a synthetic stress case, not typical tremor).",
        "Nominal run (5 Hz, 5° roll, test tuning <i>q</i> = 10<sup>−8</sup>, <i>r</i> = 10<sup>−3</sup>): roll RMS error 0.267° (assumed tuning, not the device’s).",
    ])
    SUB("Estimator simulation under an assumed sensor model (evidence class: simulation)", "simres")
    B("{fig:trace} shows one representative run and {tab:rms} the mean roll-estimate RMS error over 3–8 Hz for all 16 tuning and lever-arm combinations. "
      f"The exact-Δt update has a mean error not larger than the baseline in {n_improved} of 16 combinations, with differences from {min(DIFFS):.3f}° (large <i>q</i>, large lever arm) to {max(DIFFS):.3f}° "
      "(small <i>q</i>, large <i>r</i>). Acceleration gating helped in some high-<i>q</i> cases and hurt in others and is left off. With <i>q</i> = 10<sup>−7</sup> and a 0.10 m lever arm every configuration "
      f"degraded (error ≈ {mean_rms('T3', 0.10, 'updated'):.1f}° for the update, {mean_rms('T3', 0.10, 'gated'):.2f}° gated), showing that the estimate is sensitive to unknown mounting and tuning.")
    P.figure(FIG / "p_ekf_trace.png", "Representative simulated run (5 Hz, 5° roll; assumed noise; test tuning): truth, baseline and updated estimates, and error (simulation, not device data).", "trace")
    rows = []
    for t in TUN:
        for L in LEVERS:
            rows.append([t, f"{L:.2f}", f"{mean_rms(t, L, 'baseline'):.3f}", f"{mean_rms(t, L, 'updated'):.3f}", f"{mean_rms(t, L, 'gated'):.3f}"])
    P.table("Mean roll-estimate RMS error over 3–8 Hz, 5° tremor (deg; simulation, assumed noise, assumed tunings)", "rms",
            ["Tuning", "Lever (m)", "Baseline (1 ms dt)", "Updated (exact dt)", "Updated + gate"], rows,
            widths=[0.6, 0.7, 1.0, 1.0, 0.9], size=7)
    B("<b>Analytic cross-check.</b> At zero lever arm the error is almost entirely the integration lead of {sec:lag}: the model of {eq:lead} predicts 0.161°, 0.268° and "
      "0.429° at 3, 5 and 8 Hz and the simulation gives "
      f"{pick('T2', 0.0, 3, 'rms_roll_deg'):.3f}°, {pick('T2', 0.0, 5, 'rms_roll_deg'):.3f}° and {pick('T2', 0.0, 8, 'rms_roll_deg'):.3f}° for tuning T2. "
      "Whether this lead is an <i>error</i> depends on the reference used; it is a fixed time offset of Δt/2 and not noise. For non-zero lever arms, "
      f"the lag model of {{eq:lagm}} matches the simulated lag across all 48 tuning, lever-arm and frequency combinations with {LAG_RMS:.2f} ms RMS and {LAG_MAX:.2f} ms maximum discrepancy ({{tab:lag}}). "
      f"Over the whole grid the simulated gain spans {GAIN_ALL[0]:.3f}–{GAIN_ALL[1]:.3f} and the lag {LAG_ALL[0]:.1f}–{LAG_ALL[1]:.1f} ms ({{fig:gl}}).")
    lag_rows = []
    for t, L, f in (("T1", 0.0, 5), ("T2", 0.03, 5), ("T2", 0.06, 3), ("T2", 0.06, 8), ("T2", 0.10, 5), ("T3", 0.03, 5), ("T3", 0.06, 5), ("T3", 0.10, 3),
                    ("T3", 0.10, 5), ("T3", 0.10, 8), ("T4", 0.10, 5)):
        lag_rows.append([t, f"{L:.2f}", f, f"{FC[t]:.3f}", f"{lag_model_ms(*TUN[t], L, f):.2f}", f"{pick(t, L, f, 'lag_ms'):.2f}"])
    P.table("Estimate lag (ms): analytic lag model versus simulation (selected cases; negative = lead)", "lag",
            ["Tuning", "<i>L</i> (m)", "<i>f</i> (Hz)", "<i>f</i><sub>c</sub> (Hz)", "Model", "Simulated"], lag_rows,
            widths=[0.6, 0.6, 0.6, 0.8, 0.8, 0.8], size=7)
    P.figure(FIG / "p_gain_lag.png", "Simulated estimate gain and lag versus frequency at zero lever arm, tuning T2 (simulation): the lead of Δt/2 ≈ 2.4 ms is constant.", "gl")
    P.figure(FIG / "p_est_vs_freq.png", "Simulated roll-estimate RMS error versus tremor frequency for the baseline and updated estimators at several lever arms (assumed noise and tuning; not device data).",
             "evf", wide=True)
    P.figure(FIG / "p_est_vs_lever.png", "Simulated mean 3–8 Hz roll-estimate error versus IMU lever arm for four assumed tunings (not device data).", "evl", wide=True)
    SUB("Guard fault injection (evidence class: host test)")
    B("{fig:gtrace} shows the real guard code driven at 208 Hz with a held +20° tilt and a 5 Hz, 4° command. A 40 ms burst of invalid commands produces HOLD only and "
      "resumes with a rate-limited re-entry ramp; it never reaches neutral. A 1.5 s fault enters SAFE_NEUTRAL at 96.15 ms (20 control steps) and the output reaches 90° at 418 ms, "
      "the extra ≈ 0.32 s being the 60 °/s slew from a 20° tilt. The 150 ms requirement (TS-SAF-002) is therefore met for <i>entering</i> the safe state, not for reaching the "
      "neutral pose, which is bounded by tilt/60 °/s (≤ 1.5 s over the full range); the requirement text was corrected accordingly.")
    SUB("Author-reported Simulink results (1 kHz model; not hardware)", "simulink")
    B("The authors’ model reports a roll residual RMS of 0.346° and a pitch residual RMS of 0.573° for 8° amplitude, 8 Hz tremor applied on all three axes. With ρ from {eq:rho} "
      "this corresponds to 93.9 % (roll) and 89.9 % (pitch) at that single operating point; frequency sweeps (2–7° amplitude) are reported as &gt; 90 % (roll) and &gt; 80 % (pitch) across "
      "most of 3–7 Hz, consistent with the ≈ 90 % figure in the README.")
    P.figure(FIG / "p_simulink_pair.png", "Frequency analysis from the authors’ Simulink model, roll axis (left) and pitch axis (right): author-reported simulation reproduced unchanged from the repository (algorithms/matlab/assets); not hardware.", "simpair", wide=True)
    B("<b>Why these figures do not establish device performance.</b> (i) The plant parameters and model file are unavailable, so the result cannot be reproduced. (ii) The model has a "
      "four-state EKF with bias at 1 kHz versus the two-state EKF at 208 Hz in firmware ({tab:slfw}). (iii) The magnitude response is about −25 dB even at 0–2 Hz: the model "
      "attenuates slow motion as strongly as tremor, so a high rejection figure says nothing about preserving intentional movement (D-15). (iv) The repository does not show "
      "whether servo saturation, backlash or latency are modelled, and {eq:res} shows that a 20 ms PWM frame alone can cap the achievable reduction well below 90 % in a feed-forward "
      "arrangement. Figures that would need measurements — a photographed test setup, tremor-input versus residual-output plots from hardware, frequency-wise rejection from hardware, "
      "latency and response-time plots, and power-management measurements — are intentionally absent because no such data exist.")

    # -------------------------------------------------------------- XIII Comparison
    S("Comparison with the Baseline and the Earlier Prototype", "compare")
    B("The earlier prototype paper is not in the repository and could not be reviewed. Its reported mean rejection of 77.3 % over 4–8 Hz is quoted from the project owners and is "
      "unverified here, so a like-for-like performance comparison between that prototype and the present build is not possible. What can be compared with evidence is the firmware before and "
      "after this work ({tab:cmp}); the 20 findings that drove the changes are listed in {tab:audit}.")
    P.table("Baseline versus updated firmware (code-level and simulation-level; no hardware comparison)", "cmp",
            ["Aspect", "Baseline (main)", "Updated"],
            [["Shipped tuning (Q = R = K = 0)", "Runs; EKF yields NaN", "Rejected at boot; servos held neutral"],
             ["Time step", "1 ms-quantised", "Exact, from cycle counter, bounded"],
             ["Invalid IMU data / EKF failure", "Passed through", "Monitored; hold ≤ 100 ms then neutral"],
             ["Loop stall", "Undetected", "Command timeout + supervised watchdog"],
             ["Calibration", "Single pass, unvalidated", "Validated, retried, latched on failure"],
             ["Per-sample console I/O in control path", "Yes", "Decimated telemetry"],
             ["Estimator error (simulation)", "Reference", f"≤ baseline in {n_improved}/16 (assumed model)"],
             ["Flash / RAM", "86.7 kB / 22.6 kB", "92.8 kB / 25.6 kB"],
             ["Automated tests", "None", f"{TOTAL_CHECKS:,} host checks (4 programs); CI defined"]],
            widths=[1.8, 1.4, 1.8], wide=True)
    audit = [("D-01", "High", "Shipped Q = R = K = 0 gives NaN estimate; pitch limit 0", "Fixed (boot validation)"),
             ("D-02", "High", "Unsigned error variable hides all PWM errors", "Fixed"),
             ("D-03", "High", "No negative/NaN clamp before PWM conversion (undefined behaviour)", "Fixed (single clamp point)"),
             ("D-04", "High", "Semaphore initialised after IMU init (uninitialised use)", "Fixed"),
             ("D-05", "High", "Unsynchronised shared samples; torn reads possible", "Fixed (spinlock + sequence)"),
             ("D-06", "Med", "1 ms-quantised, unbounded Δt", "Fixed (cycle counter, bounds)"),
             ("D-07", "Med", "Blocking console prints per sample in control path", "Fixed; latency effect unmeasured"),
             ("D-08", "Med", "Depth-20 FIFO acts on commands up to ≈ 96 ms old", "Fixed (latest-wins mailbox)"),
             ("D-09", "High", "No watchdog; IMU error leaves last pulse indefinitely", "Mitigated; hardware NOT RUN"),
             ("D-10", "High", "No validation of samples or estimates", "Fixed (monitor)"),
             ("D-11", "Low", "Covariance not symmetrised; singular S unguarded", "Fixed; output identical"),
             ("D-12", "Med", "Calibration accepts any data; assumes level", "Fixed (validated, retried)"),
             ("D-13", "Med", "No PWM during ≥ 11 s boot and calibration", "Mitigated; hardware NOT RUN"),
             ("D-14", "Med", "Simulink 4-state EKF; rate states zeroed vs firmware", "<b>Open</b>"),
             ("D-15", "High", "Simulink ≈ −25 dB at all low frequencies; no voluntary-motion test", "<b>Open</b>"),
             ("D-16", "Med", "20 ms PWM frame vs 208 Hz commands; latency unmeasured", "<b>Open</b>"),
             ("D-17", "Low", "Duplicate definitions; non-portable includes", "Fixed"),
             ("D-18", "Med", "±2000 dps full scale coarse for tremor (≈ 70 mdps LSB)", "<b>Open</b> (needs bench A/B)"),
             ("D-19", "Med", "Validation rate 1 kHz vs deployed 208 Hz", "<b>Open</b>"),
             ("D-20", "Info", "No hardware documentation; IMU mounting unknown", "<b>Open</b> (owner input)")]
    P.table("Audit findings of the baseline firmware and their status", "audit", ["ID", "Severity", "Finding", "Status"], [list(a) for a in audit],
            widths=[0.5, 0.6, 4.1, 1.9], size=7, wide=True)

    # -------------------------------------------------------------- XIV Discussion
    S("Discussion", "disc")
    B("<b>Integrity before performance.</b> The most consequential finding is not a performance number: the repository as shipped could not actuate safely, because its tuning "
      "placeholders make the estimator diverge and nothing would have prevented a diverged estimate from driving a servo. The refactoring preserves the original numerics for valid "
      "data, so prior results are not invalidated, while adding the missing protections.")
    B("<b>What limits tremor-band performance.</b> The steady-state analysis ({sec:ss}) shows the estimate is gyroscope-dominated across the tremor band for every tuning studied, "
      "so tuning of <i>q</i> and <i>r</i> mainly shapes drift correction and the lever-arm coupling, not the tremor-band estimate itself. The simulation shows that mounting distance and "
      "process-noise level change the estimate’s lag by up to 16 ms ({tab:lag}) and its RMS error by more than 1° ({tab:rms}), whereas the time-step correction improves the RMS error by at most 0.14°. The analytic delay bound ({sec:delay}) "
      "shows that, for a feed-forward arrangement, total delay rather than estimator accuracy is likely the first-order limit: a reduction of 90 % at 5 Hz needs τ ≤ 3.2 ms, "
      "while the 20 ms PWM frame alone has an average hold delay of 10 ms. We therefore regard measuring end-to-end latency (TC-HW-002/003) and the PWM frame (D-16) as the "
      "most informative next experiments; a higher-rate servo interface or a faster-response actuator are candidate remedies, but they are untested. For a feedback arrangement the "
      "same delay costs ωτ radians of phase margin at crossover {c:astrom08}, limiting attainable bandwidth instead.")
    B("<b>What “reduction” means.</b> A controller that attenuates every frequency equally would score well on a tremor-reduction metric yet be unusable, because the user "
      "must still tilt the spoon. The Simulink response’s flat −25 dB at low frequencies (D-15) is exactly this pattern, and the planned slow-rotation trial (TC-PERF-003) exists to expose it. "
      "Whether the device <i>should</i> oppose slow tilt is an application decision: a level-keeping spoon helps carrying but conflicts with deliberately tipping the spoon to unload it.")
    B("<b>Safe-state design.</b> Holding a defined neutral pose with the PWM energised is a design judgement: it avoids a dropped spoon head but cannot protect against a "
      "jammed servo (R-01) or a supply failure (R-02), and a fault the user cannot see (R-04) means a degraded device may be relied upon. These are the highest-priority hardware additions.")

    # -------------------------------------------------------------- XV Limitations
    S("Limitations", "limits")
    P.bullets([
        "No hardware experiments of any kind: no latency, jitter, power, thermal, rejection or reliability data, and no user or clinical data.",
        "The device’s tuning (Q, R, K, plant parameters), the Simulink model file, hardware drawings and the earlier paper are not in the repository.",
        "The IMU mounting position (feed-forward or feedback) and the roll servo model (MG995 versus MG92B) are unresolved.",
        "The simulation uses an assumed noise model, a pure-rotation excitation with the IMU offset along one axis, zero yaw rate and no servo dynamics; estimator error is not "
        "tremor rejection, and the analytic delay bound is illustrative.",
        "Servo stall, over-temperature and brown-out cannot be detected; there is no user-visible fault indicator; Euler-angle kinematics are singular at ±90° pitch.",
        "The safety timing constants (100 ms hold, 10-sample trip, 208-sample recovery, 60 °/s slew) are engineering choices, not validated limits.",
        "The CI workflow is defined but has not been executed on a hosted runner; the host results come from a local run.",
        "The device is a research prototype; no regulatory, clinical or safety-certification status is claimed.",
    ])

    # -------------------------------------------------------------- XVI Future work
    S("Future Work", "future")
    P.bullets([
        "Execute the hardware verification plan: end-to-end latency and jitter, runtime stability ≥ 1 h, watchdog fault injection, power and stall characterisation, and rig-based "
        "frequency-wise rejection with a voluntary-motion trial.",
        "Resolve IMU placement; record the schematic, bill of materials and measured current; add a visible fault indicator, supply monitoring and stall detection.",
        "Re-tune Q, R and K for the physical plant and regenerate K from a published parameter set; compare two-state and four-state (bias) estimators on hardware.",
        "Evaluate a faster servo interface and a frequency-selective (tremor-band) control law that passes voluntary motion; compare against quaternion and SO(3) filters {c:sabatini06,mahony08}.",
        "Define hazard analysis and usability engineering to a recognised process {c:iso14971,iec62366} before any user contact.",
    ])

    # -------------------------------------------------------------- XVII Conclusion
    S("Conclusion", "concl")
    B("The TremoSense firmware has been audited, corrected and restructured into a tested portable core with an explicit safety layer, while preserving the original estimation and control "
      "mathematics for valid data. The analysis shows that the deployed estimator is a gyroscope-dominated complementary filter at tremor frequencies, that lever-arm coupling appears mainly as "
      "estimate lag which an analytic model reproduces to within a millisecond RMS, and that the 20 ms PWM frame may limit achievable reduction more than the estimator. The evidence available today "
      "supports software-correctness claims on a host and relative estimator behaviour in simulation; it does not support any claim about on-device tremor rejection, latency, power or clinical benefit. "
      "Closing those gaps requires the bench measurements specified in the verification plan, which is the next milestone.")

    # -------------------------------------------------------------- availability
    P.para("DATA AND CODE AVAILABILITY", align="c", size=9, bold=True, before=7, after=3, keep_next=True)
    P.para("Repository: github.com/rkt-1597/TremoSense-Project, branch <tt>pranshu-updates</tt>. Host tests: <tt>cmake -S firmware/tests -B build-host -G Ninja &amp;&amp; cmake --build build-host &amp;&amp; ctest --test-dir build-host</tt> "
      "(GCC 13.3, Ubuntu). Firmware: Zephyr v4.0.0, <tt>west build -b xiao_ble/nrf52840/sense</tt> with the board overlay and configuration (README). "
      "Simulation: <tt>analysis/scripts/ekf_comparison.py</tt> (deterministic seeds); figures and numbers: <tt>analysis/scripts/make_paper_figures.py</tt> and <tt>paper_figure_numbers.json</tt>. "
      "Paper: <tt>research/paper/build_paper.py</tt>. The author-reported Simulink plots are copied from <tt>algorithms/matlab/assets</tt>.", align="l", first=0.17)
    P.references(REFS)
    return P


if __name__ == "__main__":
    p1 = build()
    state = p1.finish()
    p2 = build(dict(refs_prev=state["refs"], cites_prev=state["cites"]))
    assert not p2.unresolved, sorted(p2.unresolved)
    p2.doc.core_properties.author = "Prithvi Tambewagh; Pawan Shinde; Pranshu Kumar"
    p2.doc.core_properties.title = "TremoSense: A Two-Axis EKF-LQR Stabilisation Platform for an Assistive Utensil on Zephyr RTOS"
    p2.doc.core_properties.comments = ""
    p2.doc.core_properties.last_modified_by = "Pranshu Kumar"
    p2.doc.save(OUT)
    print("wrote", OUT, "| figs", p2.nfig, "tables", p2.ntab, "eqs", p2.neq, "refs", len(p2.cite_order))
