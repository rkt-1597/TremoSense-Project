#!/usr/bin/env python3
"""Paper figures for research/paper (print-size, IEEE column widths).

Class of each figure is stated in its paper caption:
  diagram    - architecture drawn from firmware/src (not data)
  analytic   - closed-form/numeric analysis of the implemented equations
  simulation - REAL firmware C code driven by synthetic input (assumed sensor model)
Nothing here is a hardware measurement.
Usage: python3 analysis/scripts/make_paper_figures.py   (writes research/figures/p_*.png)
"""
import json, pathlib, subprocess, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle, Circle, Polygon

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / "research" / "figures"; OUT.mkdir(parents=True, exist_ok=True)
INK, INK2, GRID, SURF = "#111111", "#4a4946", "#e1e0dc", "#ffffff"
C1, C2, C3 = "#2a78d6", "#eb6834", "#1baf7a"
FILL = {"in": "#e8eef8", "ctl": "#fbeee6", "act": "#e6f4ee", "sup": "#f6e9ec", "neu": "#f1f0ec", "warn": "#fbf3d9", "wh": "#ffffff"}
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 6.5, "axes.edgecolor": INK2, "axes.labelcolor": INK,
                     "xtick.color": INK2, "ytick.color": INK2, "figure.facecolor": SURF, "axes.facecolor": SURF,
                     "axes.linewidth": 0.6, "xtick.major.width": 0.6, "ytick.major.width": 0.6})
W1, W2 = 3.45, 7.1   # column / full width [in]


def save(fig, name):
    fig.savefig(OUT / f"p_{name}.png", dpi=300, bbox_inches="tight", pad_inches=0.04)
    plt.close(fig)


def canvas(w, h, wu=10.0):
    fig, ax = plt.subplots(figsize=(w, h)); ax.set_xlim(0, wu); ax.set_ylim(0, wu * h / w); ax.axis("off")
    return fig, ax


def box(ax, x, y, w, h, text, fc="neu", fs=6.0, bold=False, ls="-", ec=INK2, lw=0.7):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.0,rounding_size=0.08", fc=FILL.get(fc, fc), ec=ec, lw=lw, ls=ls))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, color=INK, weight="bold" if bold else "normal", linespacing=1.15)


def arr(ax, p, q, text=None, ls="-", dx=0.0, dy=0.12, ha="center", fs=5.4, rad=0.0, color=INK2):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=6, color=color, lw=0.8, linestyle=ls,
                                 connectionstyle=f"arc3,rad={rad}", shrinkA=0, shrinkB=0))
    if text:
        ax.text((p[0] + q[0]) / 2 + dx, (p[1] + q[1]) / 2 + dy, text, ha=ha, fontsize=fs, color=INK2)


def style(ax):
    for s in ("top", "right"): ax.spines[s].set_visible(False)
    ax.grid(color=GRID, lw=0.5); ax.set_axisbelow(True)


# ------------------------------------------------------------------ diagrams
def fig_system():
    fig, ax = canvas(W2, 3.1)
    ax.set_xlim(0, 14.2); ax.set_ylim(0, 6.2)
    X = [0.2, 3.9, 7.6, 11.3]; Wd = 2.9
    # row 1 (left -> right)
    box(ax, X[0], 4.0, Wd, 1.5, "Hand-held handle\n+ tremor motion\n(3–8 Hz band of interest)", "neu", fs=5.0)
    box(ax, X[1], 4.0, Wd, 1.5, "LSM6DS3 IMU\n3-axis accel + 3-axis gyro\n208 Hz · ±16 g · ±2000 dps", "in", fs=5.0)
    box(ax, X[2], 4.0, Wd, 1.5, "Acquisition + monitor\ncycle-counter timestamp\nplausibility checks, boot calibration", "in", fs=4.7)
    box(ax, X[3], 4.0, Wd, 1.5, "EKF  x = [φ, θ]ᵀ\n2 states, analytic Jacobian\nexact Δt, guarded 2×2 inverse", "ctl", fs=4.9)
    for i in range(3): arr(ax, (X[i] + Wd, 4.75), (X[i + 1], 4.75))
    ax.text(X[1] - 0.4, 4.9, "ω, a", fontsize=4.8, color=INK2, ha="center"); ax.text(X[3] - 0.4, 4.9, "a, ω", fontsize=4.8, color=INK2, ha="center")
    # row 2 (right -> left)
    box(ax, X[3], 1.7, Wd, 1.5, "LQR  u = −K [φ, p, θ, q]ᵀ\nservo = 90° ± u·R2D\n(K ∈ ℝ²ˣ⁴ from dlqr)", "ctl", fs=4.9)
    box(ax, X[2], 1.7, Wd, 1.5, "Actuator guard\nclamp · slew · hold ≤ 100 ms\n→ safe neutral", "sup", fs=4.9)
    box(ax, X[1], 1.7, Wd, 1.5, "50 Hz PWM\nroll 722–2278 µs\npitch 900–2100 µs", "act", fs=4.9)
    box(ax, X[0], 1.7, Wd, 1.5, "Two-axis gimbal + spoon\nroll servo (MG995 per README)\npitch servo (FS90MG)", "act", fs=4.7)
    arr(ax, (X[3] + Wd / 2, 4.0), (X[3] + Wd / 2, 3.2)); ax.text(X[3] + Wd / 2 + 0.15, 3.6, "φ̂, θ̂", fontsize=4.8, color=INK2)
    for i in (3, 2, 1): arr(ax, (X[i], 2.45), (X[i - 1] + Wd, 2.45))
    arr(ax, (X[0] + Wd / 2, 3.2), (X[0] + Wd / 2, 4.0), ls="--"); ax.text(X[0] + Wd / 2 + 0.15, 3.6, "physical coupling", fontsize=4.6, color=INK2)
    box(ax, 7.6, 0.2, 6.6, 0.9, "Supervisor: control + actuation heartbeats → nRF52 watchdog (500 ms)", "sup", fs=4.7)
    arr(ax, (9.05, 1.1), (9.05, 1.7), ls="--")
    ax.text(0.2, 0.65, "IMU placement relative to the gimbal and\nthe supply/battery are not documented\nin the repository.", fontsize=4.7, color=INK2)
    ax.text(0.2, 6.05, "Complete system block diagram: sensor → estimator → controller → guard → actuator", fontsize=6.2, weight="bold", va="top")
    save(fig, "system")


def fig_hardware():
    fig, ax = canvas(W1, 3.3)
    ax.set_ylim(0, 9.6)
    box(ax, 0.1, 5.6, 4.9, 3.6, "", "neu"); ax.text(0.25, 9.0, "Seeed XIAO nRF52840 Sense", fontsize=5.8, weight="bold", va="top")
    box(ax, 0.3, 7.3, 2.1, 1.3, "nRF52840\nCortex-M4F\n64 MHz, FPU", "in", fs=5.0)
    box(ax, 2.6, 7.3, 2.2, 1.3, "LSM6DS3 IMU\n(on-board, I²C)", "in", fs=5.0)
    box(ax, 0.3, 5.8, 2.1, 1.2, "PWM, 50 Hz\n2 channels", "ctl", fs=5.0)
    box(ax, 2.6, 5.8, 2.2, 1.2, "WDT 500 ms\nUSB-C", "sup", fs=5.0)
    box(ax, 6.0, 7.9, 3.9, 1.3, "Roll servo\nMG995 (README)\n722–2278 µs", "act", fs=5.0)
    box(ax, 6.0, 5.9, 3.9, 1.3, "Pitch servo\nFS90MG (README)\n900–2100 µs", "act", fs=5.0)
    arr(ax, (5.0, 6.5), (6.0, 8.5), rad=-0.1); arr(ax, (5.0, 6.3), (6.0, 6.5))
    ax.text(5.15, 7.7, "PWM", fontsize=4.8, color=INK2, rotation=55)
    box(ax, 0.1, 3.4, 4.9, 1.5, "Battery / servo supply:\nNOT DOCUMENTED (brown-out,\ncurrent, capacity: unknown)", "warn", fs=4.9, ls="--")
    box(ax, 6.0, 3.4, 3.9, 1.5, "Gimbal + spoon\n(50 g food assumed\nin simulation only)", "neu", fs=4.9)
    arr(ax, (7.95, 5.9), (7.95, 4.9)); arr(ax, (5.0, 4.15), (6.0, 6.2), ls="--", rad=-0.25)
    ax.text(0.1, 2.5, "Solid: documented in the repository.  Dashed: unknown.", fontsize=4.9, color=INK2)
    ax.text(0.1, 1.8, "No schematic, BOM, PCB or mechanical drawing is available.", fontsize=4.9, color=INK2)
    save(fig, "hardware")


def fig_mech():
    fig, ax = canvas(W1, 2.6)
    ax.set_ylim(0, 7.5)
    ax.add_patch(Rectangle((0.6, 0.6), 2.2, 0.8, fc=FILL["neu"], ec=INK2, lw=0.7)); ax.text(1.7, 1.0, "handle (hand)", ha="center", va="center", fontsize=5.4)
    ax.add_patch(Circle((3.6, 1.0), 0.45, fc=FILL["act"], ec=INK2, lw=0.7)); ax.text(3.6, 1.0, "R", ha="center", va="center", fontsize=5.6, weight="bold")
    ax.plot([2.8, 3.15], [1.0, 1.0], color=INK2, lw=0.9)
    ax.add_patch(Rectangle((4.05, 0.75), 1.5, 0.5, fc=FILL["act"], ec=INK2, lw=0.7)); ax.text(4.8, 1.0, "roll servo", ha="center", va="center", fontsize=4.8)
    ax.add_patch(Circle((6.2, 1.0), 0.45, fc=FILL["act"], ec=INK2, lw=0.7)); ax.text(6.2, 1.0, "P", ha="center", va="center", fontsize=5.6, weight="bold")
    ax.plot([5.55, 5.75], [1.0, 1.0], color=INK2, lw=0.9)
    ax.plot([6.65, 8.3], [1.0, 1.9], color=INK2, lw=2.0)
    ax.add_patch(plt.matplotlib.patches.Ellipse((8.85, 2.05), 1.3, 0.55, angle=20, fc=FILL["warn"], ec=INK2, lw=0.7)); ax.text(8.85, 2.05, "spoon", ha="center", va="center", fontsize=4.8)
    ax.annotate("", xy=(3.6, 2.4), xytext=(2.2, 2.4), arrowprops=dict(arrowstyle="<->", color=C2, lw=0.8, connectionstyle="arc3,rad=-0.4"))
    ax.text(2.9, 3.05, "roll φ", fontsize=5.4, color=C2, ha="center")
    ax.annotate("", xy=(7.6, 3.0), xytext=(6.0, 2.4), arrowprops=dict(arrowstyle="<->", color=C1, lw=0.8, connectionstyle="arc3,rad=-0.4"))
    ax.text(7.1, 3.35, "pitch θ", fontsize=5.4, color=C1, ha="center")
    ax.annotate("", xy=(1.0, 2.2), xytext=(1.0, 1.4), arrowprops=dict(arrowstyle="-|>", color=INK2, lw=0.7))
    ax.text(1.15, 1.8, "hand tremor\n(3–8 Hz)", fontsize=4.8, color=INK2, va="center")
    ax.text(0.2, 5.8, "Roll (R) then pitch (P) servo in series: hand-induced tilt is opposed by\ncounter-rotation of the spoon head. ILLUSTRATIVE concept, not a drawing\nof the built mechanism (no mechanical files exist in the repository).", fontsize=5.0, color=INK2, va="top")
    ax.text(0.2, 4.3, "Open: IMU on the handle (feed-forward) or on the spoon head (feedback)?", fontsize=5.0, color=C2)
    save(fig, "mechanical")


def fig_firmware():
    fig, ax = canvas(W2, 3.0)
    ax.set_xlim(0, 14.2); ax.set_ylim(0, 4.4)
    box(ax, 0.1, 2.8, 1.9, 1.1, "LSM6DS3\ndata-ready IRQ\n208 Hz", "in", fs=4.8)
    box(ax, 2.4, 2.8, 2.4, 1.1, "sensors/imu.c\ncycle-counter stamp\nspinlock slot + seq", "in", fs=4.8)
    box(ax, 5.2, 2.6, 2.6, 1.5, "control thread (prio 1)\nmonitor → EKF → LQR\n→ servo_cmd_t\n+ validity, fault flags", "ctl", fs=4.8)
    box(ax, 8.2, 2.8, 1.8, 1.1, "k_msgq depth 1\n(latest wins)", "neu", fs=4.8)
    box(ax, 10.4, 2.6, 2.4, 1.5, "actuation thread\n(prio 5): wait ≤ 50 ms,\nactuator guard,\npulse width", "act", fs=4.8)
    box(ax, 13.1, 2.8, 1.0, 1.1, "PWM\n50 Hz", "act", fs=4.8)
    for p, q in [((2.0, 3.35), (2.4, 3.35)), ((4.8, 3.35), (5.2, 3.35)), ((7.8, 3.35), (8.2, 3.35)), ((10.0, 3.35), (10.4, 3.35)), ((12.8, 3.35), (13.1, 3.35))]: arr(ax, p, q)
    box(ax, 5.2, 0.4, 4.4, 1.3, "safety/watchdog.c (supervisor, 100 ms)\nfeeds nRF52 WDT only if control AND\nactuation heartbeats advanced", "sup", fs=4.7)
    arr(ax, (6.5, 2.6), (6.5, 1.7), "heartbeat", ls="--", dx=-0.1, ha="right", fs=4.6); arr(ax, (11.6, 2.6), (9.6, 1.4), "heartbeat", ls="--", dx=0.9, dy=0.1, fs=4.6)
    box(ax, 0.1, 0.4, 4.7, 1.9, "main.c boot order\n1 actuation thread → neutral   2 watchdog\n3 tuning validation   4 IMU init\n5 calibration (≤ 3 tries)   6 control thread\n7 enable actuation only if 3 and 5 passed", "neu", fs=4.6)
    box(ax, 10.1, 0.3, 4.0, 1.5, "Portable C99 core (no RTOS, host-tested):\nekf · lqr · control · safety · imu_cal · timing\nZephyr glue: imu · pwm · watchdog · app", "wh", fs=4.3)
    ax.text(0.1, 4.35, "Firmware architecture (Zephyr v4.0.0, board xiao_ble/nrf52840/sense)", fontsize=6.2, weight="bold", va="top")
    save(fig, "firmware")


def fig_timeline():
    fig, ax = canvas(W1, 2.5)
    ax.set_ylim(0, 7.2)
    items = [("IMU sample period", 4.81, "in", "4.81 ms (exact)"), ("control wake-up +\nEKF + LQR compute", 0.0, "warn", "NOT MEASURED"),
             ("mailbox + guard +\npulse update", 0.0, "warn", "NOT MEASURED"), ("wait for next 50 Hz\nPWM frame", 20.0, "act", "0–20 ms (bound)"), ("servo mechanical\nresponse", 0.0, "warn", "NOT MEASURED")]
    y = 6.0; x0 = 3.4; sc = 4.2 / 25.0
    for name, w, c, lab in items:
        ax.text(0.1, y + 0.3, name, fontsize=4.9, va="center")
        if w > 0:
            ax.add_patch(Rectangle((x0, y), w * sc, 0.6, fc=FILL[c], ec=INK2, lw=0.6))
        else:
            ax.add_patch(Rectangle((x0, y), 0.3, 0.6, fc=FILL[c], ec=INK2, lw=0.6, ls="--"))
        ax.text(x0 + max(w * sc, 0.35) + 0.12, y + 0.3, lab, fontsize=4.9, va="center", color=INK2)
        y -= 1.1
    ax.text(0.1, 0.45, "Analytic bound for the known terms: ≤ 4.81 + 20 ms before servo motion\nbegins. Compute, scheduling and servo terms await TC-HW-002/003 (NOT RUN).", fontsize=4.8, color=INK2)
    save(fig, "latency_budget")


def fig_ekf_struct():
    fig, ax = canvas(W1, 3.6)
    ax.set_ylim(0, 10.4)
    box(ax, 0.1, 8.6, 4.5, 1.5, "Gyro ω = (p, q, r)\n− bias offsets", "in", fs=5.0)
    box(ax, 5.4, 8.6, 4.5, 1.5, "Accel a − offsets\nz = [φₐ, θₐ]ᵀ   (3)", "in", fs=5.0)
    box(ax, 0.1, 5.4, 4.5, 2.7, "PREDICT\nx⁻ = x + f(x, ω) Δt   (2)\nF = I + A Δt\nP⁻ = F P Fᵀ + q I₂   (4)", "ctl", fs=4.9)
    box(ax, 5.4, 5.4, 4.5, 2.7, "UPDATE (H = I₂)\nS = P⁻ + R I₂\nK = P⁻ S⁻¹\nx = x⁻ + K (z − x⁻)\nP = sym((I − K) P⁻)", "ctl", fs=4.9)
    box(ax, 0.1, 2.9, 4.5, 1.9, "Guards: finite inputs,\n0 < Δt ≤ Δt_max, det S > 0;\nstate unchanged on reject", "sup", fs=4.8)
    box(ax, 5.4, 2.9, 4.5, 1.9, "Optional gate (OFF):\n| ‖a‖ − g | > 3 m/s²\n⇒ R ← 100 R", "warn", fs=4.8)
    box(ax, 1.5, 0.3, 7.0, 1.6, "Output φ̂, θ̂ → LQR and monitor\n(|φ̂|, |θ̂| ≤ 80° else invalid)", "act", fs=4.9)
    arr(ax, (2.35, 8.6), (2.35, 8.1)); arr(ax, (7.65, 8.6), (7.65, 8.1)); arr(ax, (4.6, 6.75), (5.4, 6.75))
    ax.text(5.0, 7.0, "x⁻,P⁻", fontsize=4.4, color=INK2, ha="center")
    arr(ax, (7.65, 5.4), (6.2, 1.9)); arr(ax, (2.35, 2.9), (3.2, 1.9), ls="--")
    save(fig, "ekf_structure")


def fig_lqr_arch():
    fig, ax = canvas(W1, 3.0)
    ax.set_ylim(0, 8.7)
    box(ax, 0.1, 6.2, 2.9, 1.8, "EKF\nφ̂, θ̂", "ctl", fs=5.2)
    box(ax, 0.1, 3.6, 2.9, 1.8, "gyro rates p, q\n(offset-corrected)", "in", fs=4.9)
    box(ax, 3.6, 3.9, 3.2, 3.4, "x = [φ, p, θ, q]ᵀ\nu = −K x\nK ∈ ℝ²ˣ⁴\nconstants.h\n(all-zero K\nis rejected)", "ctl", fs=4.8)
    box(ax, 7.2, 4.9, 2.7, 2.2, "servo map\nroll: 90° − u_φ·R2D\npitch: 90° + u_θ·R2D", "act", fs=4.2)
    box(ax, 7.2, 2.0, 2.7, 1.8, "actuator guard\nclamp · slew · hold", "sup", fs=4.6)
    arr(ax, (3.0, 7.1), (3.6, 6.2)); arr(ax, (3.0, 4.5), (3.6, 5.0)); arr(ax, (6.8, 5.7), (7.2, 5.9)); arr(ax, (8.55, 4.9), (8.55, 3.8))
    ax.text(0.1, 1.5, "K comes from MATLAB dlqr (LQR_ARE.m). Plant parameters and\nweights are blank in the repository: the device K is unavailable.", fontsize=4.7, color=INK2, va="top")
    ax.text(0.1, 0.2, "Q = diag(W_φ/φ²max, 1/p²max, W_θ/θ²max, 1/q²max)   R = diag(1/u²φ,max, 1/u²θ,max)", fontsize=4.4, color=INK2)
    save(fig, "lqr_arch")


def fig_guard_states():
    fig, ax = canvas(W1, 3.3)
    ax.set_ylim(0, 9.6)
    box(ax, 0.2, 7.3, 4.2, 1.8, "ACTIVE\nfollow clamped command", "act", fs=5.0)
    box(ax, 0.2, 4.3, 4.2, 1.8, "HOLD\nlast good output, ≤ 100 ms", "warn", fs=5.0)
    box(ax, 0.2, 1.3, 4.2, 1.8, "SAFE_NEUTRAL\nslew to 90° at 60 °/s, hold", "sup", fs=5.0)
    arr(ax, (1.0, 7.3), (1.0, 6.1)); ax.text(1.15, 6.7, "invalid cmd,\ntimeout", fontsize=4.5, color=INK2, va="center")
    arr(ax, (3.2, 6.1), (3.2, 7.3)); ax.text(3.35, 6.7, "valid", fontsize=4.5, color=INK2, va="center")
    arr(ax, (1.0, 4.3), (1.0, 3.1)); ax.text(1.15, 3.7, "hold > 100 ms", fontsize=4.7, color=INK2)
    arr(ax, (4.4, 2.2), (4.4, 8.2), rad=-0.5, ls="--")
    ax.text(5.5, 5.5, "208 consecutive\nvalid commands,\nthen rate-limited\nre-entry (60 °/s)", fontsize=4.7, color=INK2, va="center")
    ax.text(5.5, 2.2, "Disabled (boot, invalid\ntuning, failed calibration):\noutput = neutral", fontsize=4.7, color=INK2, va="center")
    save(fig, "guard_states")


def fig_calibration():
    fig, ax = canvas(W1, 3.2)
    ax.set_ylim(0, 9.3)
    box(ax, 1.5, 8.0, 7.0, 1.0, "boot: LED on 3 s (board level, still)", "in", fs=5.0)
    box(ax, 1.5, 6.3, 7.0, 1.3, "accumulate N = 624 samples (3 s)\nWelford mean / variance per axis", "ctl", fs=5.0)
    box(ax, 0.1, 3.7, 9.8, 1.9, "accept iff  σ_gyro ≤ 0.02 rad/s\n∧  | ‖ā‖ − g | ≤ 0.5 m/s²  ∧  |ā_x|, |ā_y| ≤ 1.5 m/s²", "warn", fs=4.9)
    box(ax, 0.1, 1.2, 4.7, 1.9, "OK: offsets = ḡyro, ā_x, ā_y,\nā_z − g → control_set_offsets", "act", fs=4.7)
    box(ax, 5.2, 1.2, 4.7, 1.9, "reject: retry (max 3), then\nlatch FAULT_CAL: servos\nstay at neutral", "sup", fs=4.7)
    arr(ax, (5.0, 8.0), (5.0, 7.6)); arr(ax, (5.0, 6.3), (5.0, 5.6)); arr(ax, (2.4, 3.7), (2.4, 3.1)); arr(ax, (7.6, 3.7), (7.6, 3.1))
    save(fig, "calibration")


def fig_power():
    fig, ax = canvas(W1, 3.1)
    ax.set_ylim(0, 9.0)
    rows = [("reset / boot", "servos un-pulsed until firmware runs\n(hardware dependent, unknown)", "warn"),
            ("actuation thread", "outputs neutral (90°) before any\nestimation runs", "act"),
            ("tuning + calibration?", "invalid → stay at neutral; fault\nlogged (no indicator)", "ctl"),
            ("ACTIVE", "stabilisation; watchdog armed (500 ms)", "act"),
            ("fault / stall / brown-out", "IMU fault: hold ≤ 100 ms → neutral.\nstall, brown-out: NOT detectable", "sup")]
    y = 7.6
    for t, d, c in rows:
        box(ax, 0.1, y, 3.9, 1.0, t, c, fs=4.8); ax.text(4.2, y + 0.5, d, fontsize=4.6, va="center", color=INK)
        if t != rows[-1][0]: arr(ax, (2.05, y), (2.05, y - 0.35), dy=0)
        y -= 1.5
    ax.text(0.1, 0.2, "No supply, current, battery or thermal measurement exists (R-01, R-02).", fontsize=4.6, color=INK2)
    save(fig, "power_states")


def fig_testsetup():
    fig, ax = canvas(W1, 2.5)
    ax.set_ylim(0, 7.2)
    box(ax, 0.1, 4.4, 2.6, 1.8, "Tremor rig\n(motor-driven\nroll/pitch, known\nf, amplitude)", "neu", fs=5.0)
    box(ax, 3.2, 4.4, 2.8, 1.8, "TremoSense\nhandle + gimbal\n+ IMU", "act", fs=5.0)
    box(ax, 6.5, 4.4, 3.3, 1.8, "Reference IMU on\nspoon bowl (≥ 1 kHz,\nsynchronised clock)", "in", fs=5.0)
    box(ax, 0.1, 1.9, 4.6, 1.5, "Logging: firmware telemetry\n(φ̂, θ̂, cmd, faults, timestamps)", "ctl", fs=5.0)
    box(ax, 5.2, 1.9, 4.6, 1.5, "Metrics: RMS in/out per\nf, amplitude, axis; latency;\nvoluntary 0.2–1 Hz trial", "wh", fs=5.0)
    arr(ax, (2.7, 5.3), (3.2, 5.3)); arr(ax, (6.0, 5.3), (6.5, 5.3)); arr(ax, (4.6, 4.4), (2.5, 3.4)); arr(ax, (8.1, 4.4), (7.5, 3.4))
    ax.text(0.1, 0.9, "PLANNED protocol (TC-PERF-001…005). NOT EXECUTED: no data are shown.", fontsize=5.2, color=C2, weight="bold")
    save(fig, "test_setup")


def fig_req_status():
    import re
    txt = (ROOT / "documentation/requirements/REQUIREMENTS.md").read_text()
    rows = [l for l in txt.splitlines() if l.startswith("| TS-")]
    cls = {"Verified (host/build)": 0, "Implemented, hardware NOT RUN": 0, "Open / not implemented": 0, "NOT RUN (hardware)": 0}
    for l in rows:
        last = l.rstrip("|").split("|")[-1].strip().lower()
        if "open" in last: cls["Open / not implemented"] += 1
        elif "verified" in last or "inspected" in last and "not run" not in last: cls["Verified (host/build)"] += 1
        elif "implemented" in last or "sim done" in last or "inspected" in last: cls["Implemented, hardware NOT RUN"] += 1
        else: cls["NOT RUN (hardware)"] += 1
    fig, ax = plt.subplots(figsize=(W1, 1.9))
    names = list(cls); vals = [cls[k] for k in names]
    ax.barh(names, vals, color=[C3, C1, C2, "#8a8985"], height=0.6)
    for i, v in enumerate(vals): ax.text(v + 0.1, i, str(v), va="center", fontsize=6)
    ax.invert_yaxis(); ax.set_xlabel("number of requirements (of %d)" % len(rows)); style(ax); ax.grid(axis="y", visible=False)
    save(fig, "req_status")
    return cls, len(rows)


# ------------------------------------------------------------------ analytic
def fig_ekf_bandwidth():
    """Steady-state scalar Kalman gain of the EKF linearised at level (F = I, H = I) and its equivalent
    complementary-filter corner frequency f_c = K / (2π Δt)  (small-K approximation)."""
    dt = 1 / 208.0
    def kss(q, r):
        P = 0.1
        for _ in range(200000):
            Pm = P + q; K = Pm / (Pm + r); Pn = (1 - K) * Pm
            if abs(Pn - P) < 1e-18: P = Pn; break
            P = Pn
        Pm = P + q; return Pm / (Pm + r)
    qs = np.logspace(-11, -3, 100)
    fig, ax = plt.subplots(figsize=(W1, 2.2))
    for r, c, ls in [(1e-3, C1, "-"), (1e-2, C2, "--"), (1e-1, C3, ":")]:
        fc = [(-np.log(1 - kss(q, r))) / (2 * np.pi * dt) for q in qs]
        ax.loglog(qs, fc, color=c, ls=ls, lw=1.1, label=f"R = {r:g}")
    ax.axhspan(3, 8, color="#ffe9a8", alpha=0.7, lw=0); ax.text(1.3e-11, 4.0, "tremor band 3–8 Hz", fontsize=5.6, color=INK2)
    for q, nm in [(1e-9, "T1"), (1e-8, "T2"), (1e-7, "T3")]:
        ax.axvline(q, color="#bbbbbb", lw=0.6); ax.text(q * 1.1, 0.008, nm, fontsize=5.4, color=INK2)
    ax.set_xlabel("process noise q"); ax.set_ylabel("accel-correction corner $f_c$ (Hz)"); ax.set_ylim(0.005, 60); style(ax)
    ax.legend(frameon=False, fontsize=5.6, loc="upper left")
    save(fig, "ekf_bandwidth")


def fig_dt_quant():
    fs = 208.0; n = 20800
    ts = np.floor(np.arange(n) / fs * 1000.0); d = np.diff(ts) / 1000.0
    exact = 1 / fs
    fig, axs = plt.subplots(1, 2, figsize=(W1, 1.9), gridspec_kw={"width_ratios": [1, 1.3]})
    vals, cnt = np.unique(np.round(d * 1000), return_counts=True)
    axs[0].bar([str(int(v)) + " ms" for v in vals], cnt / cnt.sum() * 100, color=C1, width=0.5)
    axs[0].axvline(-0.5, alpha=0); axs[0].set_ylabel("share of steps (%)"); axs[0].set_title("baseline Δt", fontsize=6.2); style(axs[0])
    sc = d / exact
    axs[1].plot(np.arange(len(sc[:80])), sc[:80], color=C1, lw=0.8, marker="o", ms=1.8, label="baseline Δt / true Δt")
    axs[1].axhline(1.0, color=C2, lw=1.0, label="updated (exact Δt)")
    axs[1].set_xlabel("sample index"); axs[1].set_ylabel("integration scale"); style(axs[1]); axs[1].legend(frameon=False, fontsize=4.8, loc="center right")
    fig.tight_layout(pad=0.4)
    save(fig, "dt_quant")
    return float(d.mean() * 1000), float((d / exact).min()), float((d / exact).max())



def fig_zoh():
    """Analytic: zero-order hold of period T has H(jw) = sinc * exp(-jwT/2): magnitude sin(pi f T)/(pi f T), phase -pi f T."""
    f = np.linspace(0.1, 10, 300)
    fig, axs = plt.subplots(1, 2, figsize=(W1, 1.9))
    for T, c, lab in [(0.02, C2, "50 Hz PWM frame (20 ms)"), (1 / 208.0, C1, "208 Hz command (4.8 ms)")]:
        x = np.pi * f * T
        axs[0].plot(f, 20 * np.log10(np.sin(x) / x), color=c, lw=1.1, label=lab)
        axs[1].plot(f, -np.degrees(x), color=c, lw=1.1)
    for a in axs: a.axvspan(3, 8, color="#ffe9a8", alpha=0.6, lw=0); a.set_xlabel("frequency (Hz)"); style(a)
    axs[0].set_ylabel("hold magnitude (dB)"); axs[1].set_ylabel("hold phase (deg)")
    axs[0].legend(frameon=False, fontsize=4.6, loc="lower left")
    fig.tight_layout(pad=0.4); save(fig, "zoh")
    T = 0.02
    return {f"{ff}Hz": (round(float(20*np.log10(np.sin(np.pi*ff*T)/(np.pi*ff*T))), 2), round(float(-180*ff*T), 1)) for ff in (3, 5, 8)}


def fig_delay_limit():
    """Analytic: feed-forward cancellation with total delay tau leaves residual |1-exp(-jw tau)| = 2 sin(pi f tau)."""
    f = np.linspace(0.5, 10, 400)
    fig, ax = plt.subplots(1, 1, figsize=(W1, 2.05))
    taus = [(0.002, C3), (0.005, C1), (0.010, C2), (0.0248, "#555555")]
    for tau, c in taus:
        red = 100 * (1 - 2 * np.abs(np.sin(np.pi * f * tau)))
        ax.plot(f, np.clip(red, -100, 100), color=c, lw=1.1, label=f"delay {tau*1e3:.1f} ms")
    ax.axvspan(3, 8, color="#ffe9a8", alpha=0.6, lw=0)
    for y in (80, 90):
        ax.axhline(y, color="#999", lw=0.5, ls=":")
    ax.axhline(0, color="#999", lw=0.5)
    ax.set_ylim(-100, 100); ax.set_xlabel("tremor frequency (Hz)"); ax.set_ylabel("best-case reduction (%)")
    ax.legend(frameon=False, fontsize=4.6, loc="lower left"); style(ax)
    fig.tight_layout(pad=0.4); save(fig, "delay_limit")
    out = {}
    for tau in (0.002, 0.005, 0.010, 0.0248):
        out[f"{tau*1e3:.1f}ms"] = {f"{ff}Hz": round(float(100 * (1 - 2 * abs(np.sin(np.pi * ff * tau)))), 1) for ff in (3, 5, 8)}
    out["tau_for_90pct_ms"] = {f"{ff}Hz": round(float(np.arcsin(0.05) / (np.pi * ff) * 1e3), 2) for ff in (3, 5, 8)}
    out["tau_for_80pct_ms"] = {f"{ff}Hz": round(float(np.arcsin(0.10) / (np.pi * ff) * 1e3), 2) for ff in (3, 5, 8)}
    return out

# ------------------------------------------------------------------ simulation (REAL firmware code)
def build_lib():
    sys.path.insert(0, str(HERE))
    import importlib
    return importlib.import_module("ekf_comparison")


def fig_ekf_trace(ec):
    f, amp, L = 5.0, 5.0, 0.0
    t, x, tr, tp = ec.make_signal(f, amp, L, 7, dur=15.0)
    n = len(x); dt_exact = np.full(n, ec.DT, np.float32); dt_q = ec.ms_quantised_dt(n)
    q, r = 1e-8, 1e-3
    base, _ = ec.run("baseline", x, dt_exact, dt_q, q, r); upd, _ = ec.run("updated", x, dt_exact, dt_q, q, r)
    m = (t >= 12.0) & (t < 12.0 + 1.0)
    tt = t[m] - 12.0
    fig, axs = plt.subplots(2, 1, figsize=(W1, 3.2), sharex=True, gridspec_kw={"height_ratios": [2, 1]})
    axs[0].plot(tt, tr[m], color=INK, lw=1.3, label="true roll")
    axs[0].plot(tt, base[m, 0], color=C1, lw=0.9, ls="--", label="baseline EKF")
    axs[0].plot(tt, upd[m, 0], color=C2, lw=0.9, label="updated EKF")
    axs[0].set_ylabel("roll (deg)"); style(axs[0]); axs[0].legend(frameon=False, fontsize=5.2, ncol=3, loc="upper center", bbox_to_anchor=(0.5, 1.22))
    axs[1].plot(tt, base[m, 0] - tr[m], color=C1, lw=0.8, ls="--"); axs[1].plot(tt, upd[m, 0] - tr[m], color=C2, lw=0.8)
    axs[1].set_ylabel("error (deg)"); axs[1].set_xlabel("time (s)"); style(axs[1])
    fig.tight_layout(pad=0.4); save(fig, "ekf_trace")


def fig_gain_lag(R):
    T = R["tremor"]; tun = "T2 Q=1e-8 R=1e-3"
    fig, axs = plt.subplots(1, 2, figsize=(W1, 1.9))
    for cfg, c, mk in [("baseline", C1, "o"), ("updated", C2, "s"), ("gated", C3, "^")]:
        for ax_, key in [(axs[0], "gain"), (axs[1], "lag_ms")]:
            fs_ = sorted({r["freq_hz"] for r in T}); ys = []
            for fq in fs_:
                v = [r[key] for r in T if r["tuning"] == tun and r["lever_m"] == 0.0 and r["freq_hz"] == fq and r["config"] == cfg]
                ys.append(np.mean(v))
            ax_.plot(fs_, ys, color=c, marker=mk, ms=2.8, lw=0.9, label=cfg)
    axs[0].set_ylabel("estimate/true amplitude"); axs[1].set_ylabel("estimate lag (ms)")
    for a in axs: a.set_xlabel("tremor frequency (Hz)"); style(a)
    axs[0].set_ylim(0.98, 1.005); axs[1].set_ylim(-4, 0); axs[0].legend(frameon=False, fontsize=4.8, loc="lower left")
    fig.tight_layout(pad=0.4); save(fig, "gain_lag")


def fig_est_freq(R):
    T = R["tremor"]; tun = "T2 Q=1e-8 R=1e-3"
    fig, axs = plt.subplots(1, 2, figsize=(W2, 2.0), sharey=True)
    for ax_, L in zip(axs, (0.0, 0.06)):
        for cfg, c, mk in [("baseline", C1, "o"), ("updated", C2, "s"), ("gated", C3, "^")]:
            fs_ = sorted({r["freq_hz"] for r in T}); ys = [np.mean([r["rms_roll_deg"] for r in T if r["tuning"] == tun and r["lever_m"] == L and r["freq_hz"] == f and r["config"] == cfg]) for f in fs_]
            ax_.plot(fs_, ys, color=c, marker=mk, ms=3, lw=1.0, label={"baseline": "Baseline (legacy EKF, 1 ms Δt)", "updated": "Updated (exact Δt)", "gated": "Updated + accel gate"}[cfg])
        ax_.set_title(f"lever arm {L:.2f} m", fontsize=6.4); ax_.set_xlabel("tremor frequency (Hz)"); style(ax_)
    axs[0].set_ylabel("roll-estimate RMS error (deg)"); axs[1].legend(frameon=False, fontsize=5.4)
    fig.tight_layout(pad=0.5); save(fig, "est_vs_freq")


def fig_est_lever(R):
    T = R["tremor"]; tuns = list(R["assumptions"]["tunings"])
    fig, axs = plt.subplots(1, 4, figsize=(W2, 1.9), sharey=True)
    for ax_, tun in zip(axs, tuns):
        for cfg, c, mk in [("baseline", C1, "o"), ("updated", C2, "s"), ("gated", C3, "^")]:
            Ls = R["assumptions"]["levers_m"]
            ys = [np.mean([r["rms_roll_deg"] for r in T if r["tuning"] == tun and r["lever_m"] == L and r["config"] == cfg]) for L in Ls]
            ax_.plot(Ls, ys, color=c, marker=mk, ms=3, lw=1.0)
        ax_.set_title(tun, fontsize=6.0); ax_.set_xlabel("lever arm (m)"); style(ax_)
    axs[0].set_ylabel("mean 3–8 Hz roll RMS error (deg)")
    fig.tight_layout(pad=0.5); save(fig, "est_vs_lever")


def fig_guard_trace():
    import csv, io
    def run(ms):
        out = subprocess.check_output(["gcc", "-O2", "-std=gnu99", "-I", str(ROOT / "firmware/include"), str(HERE / "guard_trace.c"),
                                       str(ROOT / "firmware/src/safety/safety.c"), "-lm", "-o", "/tmp/guard_trace"])
        o = subprocess.check_output(["/tmp/guard_trace", str(ms)]).decode()
        a = np.genfromtxt(io.StringIO(o), delimiter=",", names=True); return a
    short, long_ = run(40), run(1500)
    fig, axs = plt.subplots(2, 1, figsize=(W1, 3.3), sharex=True)
    for ax_, a, ttl in [(axs[0], short, "40 ms invalid-command burst (< 100 ms hold)"), (axs[1], long_, "1.5 s invalid-command fault")]:
        ax_.plot(a["t"], a["cmd"], color="#9a9893", lw=0.6, label="command")
        ax_.plot(a["t"], a["out"], color=C2, lw=1.0, label="guard output")
        bad = a["valid"] == 0
        if bad.any(): ax_.axvspan(a["t"][bad][0], a["t"][bad][-1] + 1 / 208, color="#fadcdc", alpha=0.6, lw=0)
        ax_.axhline(90, color=C3, lw=0.6, ls=":"); ax_.set_ylabel("roll (deg)"); ax_.set_title(ttl, fontsize=6.0, loc="left"); style(ax_)
    axs[1].set_xlabel("time (s)"); axs[0].legend(frameon=False, fontsize=5.2, ncol=2, loc="lower right")
    axs[0].set_xlim(0.8, 1.6); axs[1].set_xlim(0.8, 3.0)
    fig.tight_layout(pad=0.4); save(fig, "guard_trace")
    # response numbers for the paper
    def t_neutral(a):
        i0 = np.argmax(a["valid"] == 0); idx = np.where((a["state"] == 0) & (np.arange(len(a)) >= i0))[0]
        return (a["t"][idx[0]] - a["t"][i0]) * 1000 if len(idx) else None
    def t_at90(a):
        i0 = np.argmax(a["valid"] == 0); idx = np.where((np.abs(a["out"] - 90) < 0.01) & (np.arange(len(a)) >= i0))[0]
        return (a["t"][idx[0]] - a["t"][i0]) * 1000 if len(idx) else None
    return {"short_to_safe_state_ms": t_neutral(short), "long_to_safe_state_ms": t_neutral(long_), "long_to_90deg_ms": t_at90(long_)}


if __name__ == "__main__":
    R = json.load(open(ROOT / "analysis/results/ekf_comparison.json"))
    for f in (fig_system, fig_hardware, fig_mech, fig_firmware, fig_timeline, fig_ekf_struct, fig_lqr_arch, fig_guard_states,
              fig_calibration, fig_power, fig_testsetup, fig_ekf_bandwidth):
        f()
    res = {}
    res["req"] = fig_req_status()
    res["dt"] = fig_dt_quant()
    res["zoh"] = fig_zoh()
    res["delay"] = fig_delay_limit()
    ec = build_lib()
    fig_ekf_trace(ec); fig_gain_lag(R); fig_est_freq(R); fig_est_lever(R)
    res["guard"] = fig_guard_trace()
    json.dump(res, open(ROOT / "analysis/results/paper_figure_numbers.json", "w"), indent=1, default=str)
    print(json.dumps(res, indent=1, default=str)); print(sorted(p.name for p in OUT.glob("p_*.png")))
