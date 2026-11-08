#!/usr/bin/env python3
"""Builds research/paper/TremoSense_Paper.docx from verified repository facts.

Every number below comes from: firmware/ source, documentation/, analysis/results/
(ekf_comparison.json, evidence logs) or the author-reported Simulink results in the
repository README. Nothing here is a hardware measurement.
Run: python3 research/paper/build_paper.py   (then convert with soffice for the PDF)
"""
import collections
import json
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt

ROOT = Path(__file__).resolve().parents[2]
FIG = ROOT / "research" / "figures"
SIM = ROOT / "algorithms" / "matlab" / "assets"
OUT = ROOT / "research" / "paper" / "TremoSense_Paper.docx"
data = json.load(open(ROOT / "analysis" / "results" / "ekf_comparison.json"))

doc = Document()
sec = doc.sections[0]
sec.left_margin = sec.right_margin = Inches(1.0)
sec.top_margin = sec.bottom_margin = Inches(0.9)
st = doc.styles["Normal"]
st.font.name = "Times New Roman"
st.font.size = Pt(10.5)
st.element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
st.paragraph_format.space_after = Pt(6)
for name, size in (("Heading 1", 13), ("Heading 2", 11)):
    h = doc.styles[name]
    h.font.name = "Times New Roman"
    h.font.size = Pt(size)
    h.font.bold = True
    h.font.color.rgb = None
    for k in ("w:ascii", "w:hAnsi", "w:eastAsia"):
        h.element.rPr.rFonts.set(qn(k), "Times New Roman")
    for k in ("w:asciiTheme", "w:hAnsiTheme"):
        h.element.rPr.rFonts.attrib.pop(qn(k), None)
    h.paragraph_format.space_before = Pt(12 if name == "Heading 1" else 8)
    h.paragraph_format.space_after = Pt(4)

nfig = [0]
ntab = [0]
neq = [0]


def para(text, bold=False, italic=False, align=None, size=None, after=None):
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.bold, r.italic = bold, italic
    if size:
        r.font.size = Pt(size)
    if align == "c":
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    elif align == "j":
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    if after is not None:
        p.paragraph_format.space_after = Pt(after)
    return p


def body(text):
    return para(text, align="j")


def h1(t):
    doc.add_heading(t, level=1)


def h2(t):
    doc.add_heading(t, level=2)


def bullets(items):
    for it in items:
        p = doc.add_paragraph(style="List Bullet")
        p.add_run(it)
        p.paragraph_format.space_after = Pt(2)


def eq(text):
    neq[0] += 1
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(text)
    r.italic = True
    p.add_run(f"    ({neq[0]})")
    p.paragraph_format.space_after = Pt(4)


def figure(path, caption, width=6.0):
    nfig[0] += 1
    doc.add_picture(str(path), width=Inches(width))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    p = para(f"Fig. {nfig[0]}. {caption}", italic=True, align="c", size=9)
    p.paragraph_format.space_after = Pt(10)


def table(caption, header, rows, widths=None, size=9):
    ntab[0] += 1
    para(f"Table {ntab[0]}. {caption}", italic=True, align="c", size=9, after=2)
    t = doc.add_table(rows=1, cols=len(header))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    for i, h in enumerate(header):
        c = t.rows[0].cells[i]
        c.text = ""
        r = c.paragraphs[0].add_run(h)
        r.bold = True
        r.font.size = Pt(size)
    for row in rows:
        cells = t.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = ""
            r = cells[i].paragraphs[0].add_run(str(v))
            r.font.size = Pt(size)
    if widths:
        for i, w in enumerate(widths):
            t.columns[i].width = Inches(w)
        for row in t.rows:
            for i, w in enumerate(widths):
                row.cells[i].width = Inches(w)
    doc.add_paragraph().paragraph_format.space_after = Pt(4)


def footer_page_number():
    p = sec.footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run()
    for tag, txt in (("begin", None), (None, "PAGE"), ("end", None)):
        if tag:
            el = OxmlElement("w:fldChar")
            el.set(qn("w:fldCharType"), tag)
        else:
            el = OxmlElement("w:instrText")
            el.set(qn("xml:space"), "preserve")
            el.text = txt
        run._r.append(el)


footer_page_number()

# ---------------------------------------------------------------- title block
para("TremoSense: A Two-Axis EKF–LQR Stabilisation Platform for an Assistive Utensil on Zephyr RTOS — "
     "Implementation, Safety Architecture and Simulation-Based Evaluation", bold=True, align="c", size=16, after=8)
para("Prithvi Tambewagh, Pawan Shinde, Pranshu Kumar", align="c", size=11, after=0)
para("B.Tech. Electronics and Telecommunication Engineering, Veermata Jijabai Technological Institute (VJTI), Mumbai, India",
     italic=True, align="c", size=10, after=10)
para("Status of this manuscript: engineering report of a research prototype. No hardware performance data, user trials or "
     "regulatory assessment are reported. Results labelled “simulation” are not measurements of the device.",
     italic=True, align="j", size=9.5)

# ---------------------------------------------------------------- 2 abstract
h1("Abstract")
body("TremoSense is a handheld spoon-stabilisation prototype that senses hand motion with a 6-axis inertial measurement "
     "unit (IMU) and drives a two-servo gimbal (roll and pitch) to oppose tremor-induced tilt. The embedded firmware runs "
     "on a Seeed XIAO nRF52840 Sense under Zephyr RTOS: a two-state extended Kalman filter (EKF) estimates roll and "
     "pitch from accelerometer and gyroscope data at 208 Hz, and a linear quadratic regulator (LQR) state-feedback law "
     "computes the servo commands. This paper documents the current implementation, which was audited against its "
     "source code and re-engineered into a host-testable portable core with an explicit safety layer (input "
     "plausibility monitor, actuator guard with safe-neutral state, watchdog supervision, validated calibration). The "
     "audit found that the shipped constants (Q = R = K = 0) drive the legacy EKF to NaN and that sample timing was "
     "quantised to 1 ms; both are corrected. We report what is and is not supported by evidence: 29 000 host-side "
     "checks pass (including bit-identical agreement of the refactored EKF with the legacy EKF on valid data); a "
     "simulation under an assumed sensor model shows lower roll-estimate error with exact sample timing in all 16 "
     "tested tuning/lever-arm combinations; and the author-reported Simulink model (1 kHz) indicates 93.9 % roll and "
     "89.9 % pitch residual-RMS reduction at a single 8 Hz, 8° operating point. We explain why the Simulink figures cannot be "
     "taken as hardware performance. No on-device latency, power, rejection or user-study data exist yet; a "
     "verification plan with hardware test cases is provided.")
para("Keywords: tremor suppression; assistive device; extended Kalman filter; LQR; Zephyr RTOS; nRF52840; "
     "embedded safety; IMU calibration.", italic=True, align="j")

# ---------------------------------------------------------------- 4 intro
h1("1. Introduction")
body("Tremor interferes with eating, particularly with carrying a loaded spoon. Pathological tremor is most often "
     "characterised in the 4–12 Hz range depending on aetiology, with Parkinsonian rest tremor typically near 4–6 Hz [1], [2]. "
     "Handheld active stabilisers sense hand motion and counter-rotate the utensil head [3]. TremoSense follows this "
     "concept using low-cost hobby servos and a microcontroller development board, and was originally framed around "
     "tremor in Parkinson’s disease; the present work makes no clinical claim and treats the device as a motion-"
     "stabilisation prototype.")
body("Contributions of this report: (i) a source-verified description of the current firmware and algorithms; "
     "(ii) a safety architecture that keeps the servos at a defined neutral pose whenever sensing, timing, tuning or "
     "calibration is invalid; (iii) a host-side test suite that includes a regression against the original estimator; "
     "(iv) a clearly labelled simulation study of the estimator; and (v) an explicit account of the evidence gaps "
     "(hardware, latency, power, users) and how they will be closed.")

# ---------------------------------------------------------------- 5 background
h1("2. Background and Related Work")
body("Commercial and research handheld stabilisers exist; a pilot study of an active handheld utensil for essential "
     "tremor is reported in [3]. Gyroscope-based real-time tremor parameter estimation was studied in [4], and wearable "
     "exoskeleton approaches to tremor assessment and suppression in [5]. Attitude estimation from low-cost IMUs commonly "
     "uses complementary or Kalman-type filters [6], [7], with well-known alternatives on SO(3) [9] and gradient-descent "
     "filters [10]. We use a minimal two-state EKF on Euler angles because it is compact enough for a small MCU and "
     "was the filter already present in the repository; we make no claim that it is superior to the "
     "alternatives, and have not compared against them. LQR state feedback [8] is used for the control law; discretisation "
     "follows standard zero-order-hold practice [12].")
body("Limitations of Euler-angle estimation are well known: the roll/pitch kinematics are singular at ±90° pitch, and "
     "an accelerometer-derived angle is corrupted by linear acceleration, which is large for a hand-held object "
     "performing tremor motion. Both matter for this device and are discussed in Sections 8, 15 and 18.")

# ---------------------------------------------------------------- 6 problem
h1("3. Problem Statement")
body("Given a spoon mounted on a two-axis servo gimbal at the end of a hand-held body, compute servo angles at the "
     "control-loop rate such that the spoon’s orientation in roll and pitch is stabilised against tremor-band hand "
     "motion (test band 3–8 Hz) without opposing slow, intentional orientation changes needed to bring food to the "
     "mouth, and such that no sensing, timing or software fault can drive the servos to an unsafe or undefined position.")
body("Two requirements are easily overlooked: non-opposition of voluntary motion is not quantified by the earlier "
     "simulation (Section 15), and defined fault behaviour was not addressed by the original firmware (Section 13).")

# ---------------------------------------------------------------- 7 requirements
h1("4. System Requirements")
body("Requirements are tracked in the repository (documentation/requirements/REQUIREMENTS.md) with unique identifiers and a "
     "traceability matrix to verification cases. Standards such as ISO 14971 [15] and IEC 62304 [16] are used only as "
     "structuring references; no compliance or certification is claimed. Representative requirements and their "
     "verification status as of this report:")
table("Representative requirements and verification status (status in last column).",
      ["ID", "Requirement (abridged)", "Status"],
      [["TS-SW-002", "Estimator uses exact dt; reject dt outside [0.5, 20] ms", "Verified on host"],
       ["TS-SW-003", "EKF never emits non-finite output; state unchanged on rejected update", "Verified on host"],
       ["TS-SW-004", "Refactored EKF/LQR reproduce baseline for valid inputs", "Verified on host (max diff 0.0°)"],
       ["TS-SW-005", "Invalid tuning prevents actuation", "Verified on host"],
       ["TS-SAF-002", "IMU loss reaches neutral ≤ 150 ms (proposed limit)", "Verified on host (96.2 ms)"],
       ["TS-SAF-005", "Hang in either loop → reset ≤ 500 ms", "Implemented; NOT RUN on hardware"],
       ["TS-SAF-006", "Servo stall detection", "Open — no sensing hardware"],
       ["TS-SAF-007", "Supply under-voltage handling", "Open — not implemented"],
       ["TS-PERF-001", "Estimator error/lag vs reference, per frequency", "Simulation done; rig NOT RUN"],
       ["TS-PERF-002", "End-to-end latency measured and reported", "NOT RUN"],
       ["TS-SYS-003", "Tremor attenuation target over 4–8 Hz (proposed ≥ 80 %)", "NOT RUN (no hardware data)"]],
      widths=[0.9, 4.0, 1.6])

# ---------------------------------------------------------------- 8 architecture
h1("5. Proposed System Architecture")
body("Fig. 1 shows the per-sample signal flow and Fig. 2 the firmware structure. The IMU delivers samples at 208 Hz "
     "through a data-ready interrupt; a control thread runs plausibility monitoring, the EKF and the LQR; the resulting "
     "servo command is posted to a depth-one mailbox consumed by a lower-priority actuation thread that applies the "
     "actuator guard and generates the PWM output. A supervisor thread feeds the hardware watchdog only when both "
     "loops are making progress.")
figure(FIG / "fig_ekf_lqr_flow.png", "Estimation and control signal flow per IMU sample (architecture diagram, not data).")
figure(FIG / "fig_firmware_architecture.png",
       "Firmware architecture as implemented on branch pranshu-updates. Servo models are as stated in the repository README "
       "(see Section 6 on the unresolved inconsistency).")

# ---------------------------------------------------------------- 9 hardware
h1("6. Hardware Design")
table("Hardware as documented in the repository. Items not documented are marked unknown.",
      ["Item", "Content", "Source / status"],
      [["MCU board", "Seeed XIAO nRF52840 Sense (Nordic nRF52840, Cortex-M4F) [14]", "README, device tree"],
       ["IMU", "LSM6DS3, accel ±16 g, gyro ±2000 dps, 208 Hz ODR [13]", "firmware configuration"],
       ["Roll servo", "MG995 (README); owner notes elsewhere cite MG92B", "Inconsistent — unresolved"],
       ["Pitch servo", "FS90MG", "README"],
       ["Servo drive", "50 Hz PWM; roll pulse 722–2278 µs, pitch 900–2100 µs; neutral 90°", "device tree"],
       ["IMU mounting position relative to gimbal pivots", "unknown", "not documented"],
       ["Schematic, BOM, supply, battery, current draw", "unknown", "not in repository"]],
      widths=[1.7, 3.3, 1.5])
body("The mounting location of the IMU determines whether the loop is feedback (IMU on the stabilised spoon) or "
     "feed-forward (IMU on the hand-side body), and thereby how the LQR measurements should be interpreted. "
     "It is not documented and is therefore listed as an open item rather than assumed. No schematic or power data "
     "exist in the repository, so the hardware description here is limited to what the source and configuration files state.")

# ---------------------------------------------------------------- 10 acquisition/calibration
h1("7. Sensor Acquisition and Calibration")
body("The IMU is configured for 208 Hz output with full-scale ranges of ±16 g and ±2000 dps. The driver’s data-ready "
     "handler timestamps each sample with the 32-bit cycle counter, checks for fetch errors, and stores the latest sample "
     "under a spinlock with a sequence number so that the control thread never reads a torn sample and missed samples "
     "are counted. The original firmware derived the time step from millisecond timestamps, which quantises a nominal 4.81 ms "
     "period to 4 or 5 ms (−17 % / +4 %); the updated firmware computes Δt in seconds from the cycle counter, wrap-safe, and "
     "rejects Δt outside [0.5, 20] ms.")
body("At boot the device is held level and still; 624 samples (3 s) are accumulated with Welford’s online mean/variance [11]. "
     "The attempt is accepted only if the per-axis gyro standard deviation is ≤ 0.02 rad/s, |‖ā‖ − g| ≤ 0.5 m/s² and "
     "|ā_x|, |ā_y| ≤ 1.5 m/s² (≈ 8.8° tilt). Offsets are the gyro means, the x/y accelerometer means and (ā_z − g); up to three "
     "attempts are made, after which the servos remain at neutral. These thresholds are engineering choices "
     "documented in PARAMETERS.md; they have been exercised only with synthetic data.")

# ---------------------------------------------------------------- 11 signal processing
h1("8. Signal Processing and Orientation Estimation")
body("Offsets are subtracted from the raw measurements, giving body-frame acceleration a = (a_x, a_y, a_z) and angular "
     "rate ω = (p, q, r). Roll φ and pitch θ are the Euler angles (ZYX convention). An accelerometer-only estimate is")
eq("φ_a = atan2(a_y, a_z),    θ_a = atan2(−a_x, √(a_y² + a_z²))")
body("which is exact only when the specific force equals gravity. During tremor the hand accelerates, so the estimate "
     "contains a linear-acceleration error that grows with tremor frequency and with the distance between the IMU "
     "and the rotation centre (lever arm). The filter in Section 9 fuses this with gyroscope integration. An optional "
     "acceleration-norm gate (inflating the measurement noise when | ‖a‖ − g | exceeds 3 m/s²) is implemented but "
     "disabled by default because simulation shows it is not uniformly beneficial (Section 15).")

# ---------------------------------------------------------------- 12 EKF
h1("9. EKF Methodology")
body("The state is x = [φ, θ]ᵀ. The prediction integrates the Euler-angle kinematics driven by the measured rates:")
eq("φ̇ = p + q sinφ tanθ + r cosφ tanθ,    θ̇ = q cosφ − r sinφ")
body("With sample interval Δt, x⁻ = x + f(x, ω)Δt, and the state-transition matrix is F = I + AΔt with A = ∂f/∂x "
     "(analytic; sec²θ is limited when |cosθ| < 0.01). The covariance is propagated as")
eq("P⁻ = F P Fᵀ + q I₂")
body("where q is a scalar process-noise level applied to both states. The measurement is z = [φ_a, θ_a]ᵀ with H = I₂ and "
     "R = r I₂:")
eq("S = P⁻ + r I₂,    K = P⁻ S⁻¹,    x = x⁻ + K (z − x⁻),    P = (I − K) P⁻")
body("The implementation guards the 2×2 inverse (determinant check), symmetrises P, rejects non-finite inputs, and operates "
     "on copies so that any rejected update leaves the filter state untouched. On valid inputs its output is "
     "bit-identical to the original implementation (Section 15). Two differences from the MATLAB/Simulink model must be "
     "stated: the model’s EKF has four states including gyroscope bias and subtracts the bias from the rates, whereas "
     "the firmware filter has two states and relies on the boot-time offset calibration; and the model runs at 1 kHz while "
     "the firmware runs at 208 Hz. The simulation results in Section 15 therefore describe a related, not identical, system.")
body("Tuning values (q, r, and the maximum-pitch limit) for the physical device are not stored in the repository. The "
     "shipped placeholders are zero, for which the legacy filter returns NaN after a few updates (demonstrated in "
     "the host tests); the updated firmware validates the configuration at boot and refuses to actuate until real "
     "values are supplied.")

# ---------------------------------------------------------------- 13 LQR
h1("10. LQR Control Design")
body("Each axis is modelled as a rate-damped inertia driven by servo torque; with state x = [φ, p, θ, q]ᵀ and input "
     "u = [u_φ, u_θ]ᵀ the continuous model is")
eq("ẋ = A x + B u,    A = [[0,1,0,0],[0,−α_φ,0,0],[0,0,0,1],[0,0,0,−α_θ]],    B = [[0,0],[β_φ,0],[0,0],[0,β_θ]]")
body("discretised by zero-order hold at T_s [12]. The cost is J = Σ (xᵀQx + uᵀRu) with")
eq("Q = diag(W_φ/φ²_max, 1/p²_max, W_θ/θ²_max, 1/q²_max),    R = diag(1/u²_φ,max, 1/u²_θ,max)")
body("and the gain K is the solution of the discrete algebraic Riccati equation (dlqr in MATLAB) [8]. The law is "
     "u = −K x, and servo commands are 90° ± (180/π)u with the sign convention fixed in the implementation "
     "(roll: 90° − u_φ·180/π; pitch: 90° + u_θ·180/π). The firmware applies a 2×4 gain to [φ, p, θ, q] where φ, θ come from "
     "the EKF and p, q are the offset-corrected gyro rates. The plant parameters (masses, radii, servo torque, damping, "
     "weights) are blank in the repository script, so K cannot be regenerated from the repository and the "
     "numerical gain used in the original experiments is not available to this work. We also note that the Simulink "
     "model sets the rate inputs differently from the firmware (audit finding D-14).")

# ---------------------------------------------------------------- 14 servo/power
h1("11. Servo Actuation and Power Management")
body("Servos are driven by 50 Hz PWM; the angle-to-pulse mapping clamps at both ends and treats NaN as neutral. "
     "The actuation thread performs servo initialisation to neutral before any estimation runs. The actuator guard "
     "(Section 13) bounds, rate-limits and, when necessary, overrides the commanded angles. A configurable slew limit "
     "exists but is disabled by default (0 °/s) to preserve the original dynamic behaviour; the fault-return slew is 60 °/s.")
body("Power management is not implemented in firmware beyond the neutral-first boot order, and no power or current "
     "measurement exists. Brown-out and servo-stall detection are not possible with the current hardware and are recorded as open "
     "risks (R-01, R-02 in the safety architecture). Battery life, peak servo current and supply droop are therefore "
     "unknown; any runtime figure quoted elsewhere for the prototype is not supported by this repository.")

# ---------------------------------------------------------------- 15 firmware
h1("12. Firmware and Real-Time Implementation")
body("The firmware targets board xiao_ble/nrf52840/sense under Zephyr v4.0.0 [12]. It is organised in modules "
     "(sensors, estimation, control, actuation, safety, application, common) with a portable C99 core "
     "(EKF, LQR, control step, calibration, safety monitor and guard, timing) that has no RTOS dependency and is "
     "compiled and tested on a host. Threads: IMU data-ready handler → control thread (priority 1) → latest-wins message queue "
     "(depth 1) → actuation thread (priority 5); a supervisor thread monitors heartbeats. The original blocking console "
     "print inside the control loop was replaced by decimated telemetry (every 26th sample by default); an uninitialised "
     "semaphore and an unprotected shared-sample handoff in the original driver were corrected.")
table("Build facts (compile check against Zephyr v4.0.0 with the apt arm-none-eabi toolchain; not a hardware run).",
      ["Build", "Flash (B)", "RAM (B)"],
      [["Baseline (main) firmware", "86 696 (10.74 %)", "22 592 (8.62 %)"],
       ["Updated firmware", "92 772 (11.50 %)", "25 560 (9.75 %)"],
       ["Updated, LED-test configuration", "90 164 (11.17 %)", "24 536 (9.36 %)"]],
      widths=[3.0, 1.7, 1.7])
body("Timing margins (jitter, CPU load, stack use, interrupt latency) have not been measured; the control loop has "
     "been inspected only at source level. Measuring them is test case TC-HW-002/003 in the verification plan.")

# ---------------------------------------------------------------- 16 safety
h1("13. Safety Architecture")
body("The design principle is that a defined neutral pose, held with the PWM energised, is the safe state for a "
     "food-carrying spoon, preferred over de-energised (limp) servos that would let the head fall. Layers:")
bullets([
    "Boot: the actuation thread starts first and outputs neutral; actuation is enabled only after tuning validation "
    "and a successful calibration. Invalid configuration or three failed calibrations latch a permanent fault.",
    "Input monitor: non-finite, out-of-range, stuck (32 identical raw samples), timing, and timeout faults; EKF numeric "
    "and range faults (|φ| or |θ| beyond 80°); invalid-command faults. Ten consecutive bad samples (≈ 48 ms) are required to "
    "invalidate output; 208 good samples (≈ 1 s) are required to recover.",
    "Actuator guard: clamps to the servo range; on an invalid command holds the last good output for ≤ 100 ms, then "
    "slews to 90° at 60 °/s and holds; resumes only after 208 consecutive valid commands, with rate-limited re-entry.",
    "Supervision: the actuation thread declares a missing command after 50 ms; a supervisor feeds the nRF52 watchdog "
    "(500 ms) only if both control and actuation heartbeats advance.",
])
figure(FIG / "fig_safety_states.png", "Actuator guard state machine (design diagram).", width=5.8)
body("Hazard analysis (ISO 14971-informed [15], not a compliance claim) identifies ten hazards; the unresolved ones "
     "are servo stall (R-01), supply droop (R-02), non-opposition of voluntary motion (R-03), lack of user-visible fault "
     "indication (R-04), overheating, and electrical/battery hazards. These are open risks, not mitigated ones.")

# ---------------------------------------------------------------- 17 experimental method
h1("14. Experimental Methodology")
body("Three evidence classes exist today; none is a hardware performance test.")
table("Evidence classes used in this report.",
      ["Class", "What was done", "What it can support"],
      [["Host unit/integration tests", "Portable core compiled with -Wall -Wextra -Wpedantic -Wshadow -Wconversion -Werror and "
        "ASan/UBSan; deterministic synthetic inputs; regression against the original EKF", "Logic, numerical robustness, fault handling"],
       ["Estimator simulation", "Batch harness driving the legacy and updated EKF with synthetic tremor under an assumed IMU noise model "
        "(≈0.9 mg, ≈0.07 dps rms, residual gyro bias), lever arms 0–0.10 m, 3–8 Hz, 5°, 10 seeds, four tunings", "Relative estimator behaviour under stated assumptions"],
       ["Compile check", "Zephyr v4.0.0 build for the target board", "Buildability and footprint"]],
      widths=[1.5, 3.4, 1.6])
body("The Simulink results come from the authors’ model at 1 kHz with 50 g of food mass; only the exported PDF of the model "
     "and the result plots are in the repository (the .slx file and plant parameters are not), so these results are "
     "reproduced here as author-reported. Planned bench protocol (not yet executed): a motor-driven tremor rig with a "
     "reference IMU on the spoon bowl and one on the hand-side body, logged at ≥ 1 kHz with synchronised timestamps; "
     "input and residual RMS per frequency, amplitude and axis; ≥ 5 repeats; a slow (0.2–1 Hz) voluntary-motion trial; "
     "and end-to-end latency from IMU sample to servo motion. Section 18 lists what is therefore unknown.")

# ---------------------------------------------------------------- 18 results
h1("15. Results and Performance Analysis")
h2("15.1 Host tests (evidence class: host simulation)")
table("Host test outcomes (full log: analysis/results/evidence/host_tests_20261108.log; report TEST_REPORT.md).",
      ["Test target", "Checks", "Failures"],
      [["EKF (incl. legacy comparison)", "10 397", "0"], ["LQR, timing, calibration", "1 640", "0"],
       ["Safety monitor and guard", "2 532", "0"], ["Control step integration", "14 453", "0"]],
      widths=[3.4, 1.4, 1.4])
bullets([
    "Legacy EKF with the shipped Q = R = 0: roll and pitch become NaN after 5 updates; the updated EKF rejects this "
    "configuration at initialisation.",
    "Updated vs legacy EKF on 6000 valid samples: maximum difference 0.000° (bit-identical).",
    "Held-then-neutral behaviour: with IMU data lost, the guard reaches safe neutral after 20 control steps (96.2 ms), within the "
    "proposed 150 ms limit.",
    "Accelerometer-burst test: gated EKF mean |roll error| 0.264° vs 15.644° ungated in the burst window (a synthetic stress "
    "case, not typical tremor).",
    "Nominal run (5 Hz, 5° roll, test tuning Q = 1e-8, R = 1e-3): roll estimate RMS error 0.267° (synthetic; these tunings are "
    "assumed, not the device’s).",
])
h2("15.2 Estimator simulation under an assumed sensor model")
agg = collections.defaultdict(list)
for r in data["tremor"]:
    agg[(r["tuning"], r["lever_m"], r["config"])].append(r["rms_roll_deg"])


def m(t, L, c):
    v = agg[(t, L, c)]
    return sum(v) / len(v)


rows = []
for t in data["assumptions"]["tunings"]:
    for L in (0.0, 0.06):
        rows.append([t, f"{L:.2f}", f"{m(t, L, 'baseline'):.3f}", f"{m(t, L, 'updated'):.3f}", f"{m(t, L, 'gated'):.3f}"])
table("Mean roll-estimate RMS error over 3–8 Hz, 5° tremor (deg; simulation, assumed noise, assumed tunings; selected lever arms — full set in EKF_COMPARISON.md).",
      ["Tuning", "Lever (m)", "Baseline (1 ms dt)", "Updated (exact dt)", "Updated + gate"],
      rows, widths=[1.9, 0.8, 1.3, 1.3, 1.2])
body("Across all 16 tuning/lever-arm combinations the exact-Δt update had a mean error not larger than the baseline, "
     "with gains from negligible (high-Q, large lever arm) to ≈ 0.1–0.15° (Figs. 4–5). Acceleration gating helped in some "
     "high-Q, large-lever cases and hurt in others and is therefore left off. With high Q and a large lever arm every "
     "configuration degraded (error > 1° at Q = 1e-7, 0.10 m), showing that the estimate is sensitive to unknown mounting "
     "and tuning. These are estimator-error results; they are not closed-loop tremor rejection.")
figure(FIG / "fig_estimator_vs_freq.png", "Simulated roll-estimate RMS error versus tremor frequency (assumed noise model and tuning; not device data).")
figure(FIG / "fig_estimator_vs_lever.png", "Simulated mean 3–8 Hz roll-estimate error versus IMU lever arm for four assumed tunings (not device data).")
h2("15.3 Author-reported Simulink results (1 kHz model; not hardware)")
body("The authors’ Simulink model reports a roll-axis residual RMS of 0.346° and a pitch-axis residual RMS of 0.573° for "
     "an 8° amplitude, 8 Hz tremor applied on all three axes. Using reduction = 1 − RMS_residual/RMS_input this "
     "corresponds to 93.9 % (roll) and 89.9 % (pitch) at that single operating point; the frequency sweeps (2–7° "
     "amplitude) are reported as > 90 % (roll) and > 80 % (pitch) across most of 3–7 Hz. These numbers are consistent with the "
     "“~90 %” figure used in the project README.")
figure(SIM / "roll_freq_analysis.png", "Roll-axis frequency analysis from the authors’ Simulink model (author-reported simulation, reproduced from the repository; not a hardware measurement).", width=5.2)
figure(SIM / "pitch_freq_analysis.png", "Pitch-axis frequency analysis from the authors’ Simulink model (author-reported simulation).", width=5.2)
figure(SIM / "lqr_vs_ip.png", "LQR response versus input in the Simulink model, 8°/8 Hz on all axes (author-reported simulation).", width=5.2)
body("Why these figures do not establish device performance: (i) the plant parameters and the model file are not "
     "available, so the result cannot be reproduced; (ii) the model has a four-state EKF with bias and 1 kHz sampling versus "
     "the two-state EKF at 208 Hz in firmware; (iii) the magnitude response is about −25 dB even at 0–2 Hz, i.e. the "
     "model attenuates slow motion as strongly as tremor, so a high rejection figure says nothing about preserving "
     "intentional movement; (iv) the repository does not show whether servo saturation, backlash or latency are modelled. "
     "Figures that would require measurements — experimental test setup, tremor-input versus residual-output plots from "
     "hardware, frequency-wise rejection from hardware, latency and response-time plots, and power-management measurements — are "
     "intentionally absent because no such data exist.")

# ---------------------------------------------------------------- 19 comparison
h1("16. Comparison with the Earlier Prototype")
body("The earlier prototype paper is not in the repository and could not be reviewed; its reported mean rejection of "
     "77.3 % over 4–8 Hz is quoted from the project owners and is unverified here. A like-for-like performance comparison "
     "between that prototype and the present build is therefore not possible. What can be compared with evidence is "
     "the firmware before and after this work (same repository, baseline = main branch):")
table("Baseline vs updated firmware (code-level and simulation-level; no hardware comparison).",
      ["Aspect", "Baseline", "Updated"],
      [["Shipped tuning (Q = R = K = 0)", "Runs; EKF yields NaN", "Rejected at boot; servos held neutral"],
       ["Time step", "ms-quantised", "Exact, from cycle counter, bounded"],
       ["Invalid IMU data / EKF failure", "Passed through", "Monitored; hold ≤ 100 ms then neutral"],
       ["Loop stall", "Undetected", "Command timeout + supervised watchdog"],
       ["Calibration", "Single pass, unvalidated", "Validated, retried, latched on failure"],
       ["Per-sample console I/O in control path", "Yes", "Decimated telemetry"],
       ["Estimator error (simulation, 16 cases)", "Reference", "≤ baseline in 16/16 (assumed model)"],
       ["Flash / RAM", "86.7 kB / 22.6 kB", "92.8 kB / 25.6 kB"],
       ["Automated tests", "None", "29 000 host checks (4 programs) + CI definition"]],
      widths=[2.4, 2.0, 2.1])

# ---------------------------------------------------------------- 20 discussion
h1("17. Discussion")
body("The most consequential finding is not a performance number but an integrity one: the repository as shipped could "
     "not actuate safely because its tuning placeholders make the estimator diverge, and nothing would have stopped a "
     "diverged estimate from driving a servo. The refactoring preserves the original numerical behaviour for valid "
     "data (so prior results are not invalidated) while adding the missing protections. The estimator simulation "
     "suggests that, for a hand-held tremor source, mounting distance and process-noise tuning can matter more than the "
     "filter timing correction; this argues for measuring on a rig before further estimator refinement. The simulation "
     "also cautions against assuming that more sophisticated gating helps.")
body("The second consequence concerns what “rejection” means. A controller that attenuates every frequency "
     "equally would score well on a tremor-rejection metric yet make the device unusable, because the user must still tilt "
     "the spoon; the planned voluntary-motion trial exists to expose this.")

# ---------------------------------------------------------------- 21 limitations
h1("18. Limitations")
bullets([
    "No hardware experiments of any kind: no latency, jitter, power, thermal, rejection or reliability data; no user or clinical data.",
    "Device tuning (Q, R, K, plant parameters), the Simulink model file, hardware drawings and the earlier paper are not in the repository.",
    "IMU mounting position and the roll servo model (MG995 vs MG92B) are unresolved.",
    "Simulation uses assumed noise and lever arms, roll-only excitation and no servo dynamics; estimator error is not tremor rejection.",
    "Servo stall, over-temperature and brown-out cannot be detected; no user-visible fault indicator; Euler-angle singularity at ±90° pitch.",
    "Safety timing constants (100 ms hold, 10-sample trip, 208-sample recovery, 60 °/s) are engineering choices, not validated limits.",
    "The device is a research prototype; no regulatory, clinical or safety-certification status is claimed.",
])

# ---------------------------------------------------------------- 22 future
h1("19. Future Work")
bullets([
    "Execute the hardware verification plan: end-to-end latency and jitter, runtime stability ≥ 1 h, watchdog fault injection, "
    "power/stall characterisation, and rig-based frequency-wise rejection with a voluntary-motion trial.",
    "Fix and document IMU placement; record schematic, BOM and measured current; add a visible fault indicator and supply monitoring.",
    "Re-tune Q, R and K for the physical plant and regenerate K from a published parameter set; compare 2-state and 4-state (bias) estimators on hardware.",
    "Evaluate high-pass/voluntary-motion-aware control and alternative estimators [9], [10] against the present EKF on the same rig.",
])

# ---------------------------------------------------------------- 23 conclusion
h1("20. Conclusion")
body("The TremoSense firmware has been audited, corrected and restructured into a tested core with an explicit safety "
     "layer, while preserving the original estimation and control mathematics for valid data. The evidence available "
     "today supports software correctness claims on a host and relative estimator behaviour in simulation; it does not support "
     "any claim about on-device tremor rejection, latency, power or clinical benefit. Closing those gaps requires the bench "
     "measurements specified in the verification plan, which is the next milestone.")

# ---------------------------------------------------------------- reproducibility
h1("Reproducibility")
body("Repository: github.com/rkt-1597/TremoSense-Project, branch pranshu-updates. Host tests: cmake -S firmware/tests -B "
     "build-host -G Ninja && cmake --build build-host && ctest --test-dir build-host (GCC 13.3, Ubuntu). Firmware: Zephyr "
     "v4.0.0, west build -b xiao_ble/nrf52840/sense from firmware/ with the board overlay and conf (README). "
     "Simulation: analysis/scripts/ekf_comparison.py (deterministic seeds) writes analysis/results/ekf_comparison.json; "
     "figures: analysis/scripts/make_figures.py. Paper: research/paper/build_paper.py.")

# ---------------------------------------------------------------- 24 references
h1("References")
refs = [
    "G. Deuschl, P. Bain, M. Brin, “Consensus statement of the Movement Disorder Society on tremor,” Movement Disorders, vol. 13, suppl. 3, pp. 2–23, 1998.",
    "K. P. Bhatia et al., “Consensus statement on the classification of tremors,” Movement Disorders, vol. 33, no. 1, pp. 75–87, 2018.",
    "A. Pathak, J. A. Redmond, M. Allen, K. L. Chou, “A noninvasive handheld assistive device to accommodate essential tremor: a pilot study,” Movement Disorders, vol. 29, no. 6, pp. 838–842, 2014.",
    "J. A. Gallego, E. Rocon, J. O. Roa, J. C. Moreno, J. L. Pons, “Real-time estimation of pathological tremor parameters from gyroscope data,” Sensors, vol. 10, no. 3, pp. 2129–2149, 2010.",
    "E. Rocon, J. M. Belda-Lois, A. F. Ruiz, M. Manto, J. C. Moreno, J. L. Pons, “Design and validation of a rehabilitation robotic exoskeleton for tremor assessment and suppression,” IEEE Trans. Neural Syst. Rehabil. Eng., vol. 15, no. 3, pp. 367–378, 2007.",
    "R. E. Kalman, “A new approach to linear filtering and prediction problems,” J. Basic Eng., vol. 82, no. 1, pp. 35–45, 1960.",
    "D. Simon, Optimal State Estimation. Wiley, 2006.",
    "B. D. O. Anderson, J. B. Moore, Optimal Control: Linear Quadratic Methods. Prentice-Hall, 1990.",
    "R. Mahony, T. Hamel, J.-M. Pflimlin, “Nonlinear complementary filters on the special orthogonal group,” IEEE Trans. Autom. Control, vol. 53, no. 5, pp. 1203–1218, 2008.",
    "S. O. H. Madgwick, A. J. L. Harrison, R. Vaidyanathan, “Estimation of IMU and MARG orientation using a gradient descent algorithm,” in Proc. IEEE ICORR, 2011.",
    "B. P. Welford, “Note on a method for calculating corrected sums of squares and products,” Technometrics, vol. 4, no. 3, pp. 419–420, 1962.",
    "G. F. Franklin, J. D. Powell, M. L. Workman, Digital Control of Dynamic Systems, 3rd ed. Addison-Wesley, 1998; and Zephyr Project documentation, release 4.0.0, docs.zephyrproject.org.",
    "STMicroelectronics, “LSM6DS3 iNEMO inertial module” datasheet.",
    "Nordic Semiconductor, “nRF52840 Product Specification.”",
    "ISO 14971:2019, Medical devices — Application of risk management to medical devices (used as a reference only).",
    "IEC 62304:2006+AMD1:2015, Medical device software — Software life cycle processes (used as a reference only).",
]
for i, r in enumerate(refs, 1):
    p = para(f"[{i}] {r}", size=9, after=2)
    p.paragraph_format.left_indent = Inches(0.3)
    p.paragraph_format.first_line_indent = Inches(-0.3)

doc.save(OUT)
print("wrote", OUT)
