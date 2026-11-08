#!/usr/bin/env python3
"""Generate paper/documentation figures from repository data.

Data figures use analysis/results/ekf_comparison.json (SIMULATION). Diagrams are
drawn from the firmware structure in firmware/src and are architecture, not data.
Usage: python3 analysis/scripts/make_figures.py   (writes research/figures/*.png)
"""
import json, pathlib
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "research" / "figures"; OUT.mkdir(parents=True, exist_ok=True)
INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#e3e2de", "#fcfcfb"
COL = {"baseline": "#2a78d6", "updated": "#eb6834", "gated": "#1baf7a"}
MARK = {"baseline": "o", "updated": "s", "gated": "^"}
LAB = {"baseline": "Baseline (legacy EKF, 1 ms dt)", "updated": "Updated (exact dt)", "gated": "Updated + accel gating"}
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.edgecolor": INK2, "axes.labelcolor": INK,
                     "xtick.color": INK2, "ytick.color": INK2, "figure.facecolor": SURF, "axes.facecolor": SURF})

R = json.load(open(ROOT / "analysis/results/ekf_comparison.json")); T = R["tremor"]
TUN = "T2 Q=1e-8 R=1e-3"

def style(ax):
    for s in ("top", "right"): ax.spines[s].set_visible(False)
    ax.grid(axis="y", color=GRID, lw=0.8); ax.set_axisbelow(True)

# 1. RMS error vs frequency (lever 0.06 m, tuning T2)
def fig_freq():
    fig, axs = plt.subplots(1, 2, figsize=(7.4, 3.0), sharey=True)
    for ax, (L, ttl) in zip(axs, [(0.0, "IMU at pivot (lever arm 0 m)"), (0.06, "IMU 0.06 m from pivot")]):
        for c in ("baseline", "updated", "gated"):
            rows = sorted([d for d in T if d["tuning"] == TUN and d["lever_m"] == L and d["config"] == c], key=lambda d: d["freq_hz"])
            f = [d["freq_hz"] for d in rows]; y = [d["rms_roll_deg"] for d in rows]
            ax.plot(f, y, color=COL[c], marker=MARK[c], ms=5, lw=1.8, label=LAB[c])
        ax.set_title(ttl, fontsize=9, color=INK, loc="left"); ax.set_xlabel("Tremor frequency (Hz)"); style(ax)
    axs[0].set_ylabel("Roll estimate RMS error (deg)")
    axs[1].legend(frameon=False, fontsize=7.5, loc="upper left")
    fig.suptitle("Simulation: estimator error, 5° tremor, tuning Q=1e-8, R=1e-3 (assumed, not the device's)", fontsize=8.5, color=INK2, x=0.01, ha="left")
    fig.tight_layout(rect=(0, 0, 1, 0.94)); fig.savefig(OUT / "fig_estimator_vs_freq.png", dpi=200); plt.close(fig)

# 2. mean RMS vs lever arm, per tuning
def fig_lever():
    tunes = sorted({d["tuning"] for d in T}); levers = R["assumptions"]["levers_m"]
    fig, axs = plt.subplots(1, len(tunes), figsize=(7.4, 2.7), sharey=True)
    for ax, t in zip(axs, tunes):
        for c in ("baseline", "updated", "gated"):
            y = [np.mean([d["rms_roll_deg"] for d in T if d["tuning"] == t and d["lever_m"] == L and d["config"] == c]) for L in levers]
            ax.plot(levers, y, color=COL[c], marker=MARK[c], ms=4.5, lw=1.6, label=LAB[c])
        ax.set_title(t.split(" ", 1)[1], fontsize=8, color=INK, loc="left"); ax.set_xlabel("Lever arm (m)"); style(ax)
    axs[0].set_ylabel("Mean roll RMS error,\n3–8 Hz (deg)"); axs[-1].legend(frameon=False, fontsize=6.5, loc="upper left")
    fig.tight_layout(); fig.savefig(OUT / "fig_estimator_vs_lever.png", dpi=200); plt.close(fig)

# --- diagram helpers ---
def box(ax, x, y, w, h, text, fc="#f1f0ec", ec=INK2, fs=7, bold=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08", fc=fc, ec=ec, lw=1.0))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, color=INK, weight="bold" if bold else "normal", wrap=True)
def arrow(ax, p, q, text=None, ls="-", dx=0.0, dy=0.1, ha="center"):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=9, color=INK2, lw=1.1, linestyle=ls))
    if text: ax.text((p[0] + q[0]) / 2 + dx, (p[1] + q[1]) / 2 + dy, text, ha=ha, fontsize=6.5, color=INK2)
def canvas(w, h, title):
    fig, ax = plt.subplots(figsize=(w, h)); ax.set_xlim(0, 10); ax.set_ylim(0, 10 * h / w); ax.axis("off")
    ax.text(0.05, 10 * h / w - 0.25, title, fontsize=9, weight="bold", color=INK, va="top"); return fig, ax

def fig_firmware():
    fig, ax = canvas(7.4, 4.6, "Firmware architecture (as implemented on branch pranshu-updates)")
    H = 10 * 4.6 / 7.4
    box(ax, 0.2, 4.1, 1.7, 1.0, "LSM6DS3\nIMU (I²C)\n208 Hz ODR", fc="#e8eef8")
    box(ax, 2.3, 4.1, 2.0, 1.0, "sensors/imu.c\ndata-ready thread\ntimestamp + spinlock", fc="#e8eef8")
    box(ax, 4.7, 3.6, 2.5, 2.0, "control thread (prio 1)\nmonitor → EKF (2-state)\n→ LQR (2×4 gain)\nvalidity flags", fc="#fbeee6", bold=False)
    box(ax, 7.6, 4.1, 2.3, 1.0, "mailbox\n(depth 1,\nlatest wins)", fc="#f1f0ec")
    box(ax, 7.6, 2.4, 2.3, 1.1, "actuation thread (prio 5)\nactuator guard:\nclamp · slew · hold · neutral", fc="#e6f4ee")
    box(ax, 7.6, 0.9, 2.3, 1.0, "PWM 50 Hz\nroll: MG995 (per README)\npitch: FS90MG (per README)", fc="#e6f4ee", fs=6.3)
    box(ax, 4.5, 0.9, 2.8, 1.2, "safety/watchdog.c\nfeeds nRF52 WDT only\nif BOTH loops beat", fc="#f6e9ec")
    box(ax, 0.2, 2.0, 4.0, 1.4, "application/main.c  boot order:\n1 actuation thread (neutral)  2 watchdog\n3 tuning validation  4 IMU init\n5 calibration (retry, latch)  6 control thread", fc="#f1f0ec", fs=7.2)
    box(ax, 0.2, 0.4, 4.0, 1.1, "portable core (host-tested, no RTOS):\nekf · lqr · control · safety · imu_cal · timing", fc="#ffffff", fs=7.2)
    arrow(ax, (1.9, 4.6), (2.3, 4.6)); arrow(ax, (4.3, 4.6), (4.7, 4.6)); arrow(ax, (7.2, 4.6), (7.6, 4.6))
    arrow(ax, (8.65, 4.1), (8.65, 3.5)); arrow(ax, (8.65, 2.4), (8.65, 1.9))
    arrow(ax, (5.5, 3.6), (5.5, 2.1), "heartbeat", ls="--", dx=-0.1, dy=0, ha="right"); arrow(ax, (7.9, 2.4), (7.0, 2.1), "heartbeat", ls="--", dx=-0.15, dy=0.15, ha="right")
    fig.savefig(OUT / "fig_firmware_architecture.png", dpi=200, bbox_inches="tight"); plt.close(fig)

def fig_safety():
    fig, ax = canvas(7.4, 3.4, "Actuator guard states (safety/safety.c)")
    box(ax, 0.2, 1.4, 2.4, 1.2, "ACTIVE\nfollow clamped command\n(optional slew limit)", fc="#e6f4ee", bold=False)
    box(ax, 4.0, 1.4, 2.0, 1.2, "HOLD\nhold last good output\n≤ 100 ms", fc="#fbf3d9")
    box(ax, 7.4, 1.4, 2.5, 1.2, "SAFE_NEUTRAL\nslew to 90° at 60 °/s\nand hold, PWM energised", fc="#f6e9ec")
    arrow(ax, (2.6, 2.15), (4.0, 2.15), "invalid cmd /\ntimeout", dy=0.12); arrow(ax, (6.0, 2.15), (7.4, 2.15), "hold > 100 ms", dy=0.12)
    arrow(ax, (4.0, 1.65), (2.6, 1.65), "valid cmd", dy=0.08)
    arrow(ax, (8.6, 1.4), (1.4, 1.4), None, ls="--"); ax.text(5.0, 1.05, "208 consecutive valid commands, then rate-limited re-entry", ha="center", fontsize=7, color=INK2)
    ax.text(0.2, 0.05, "Disabled (boot, invalid tuning, failed calibration): output is neutral, state SAFE_NEUTRAL.\nFault classes (monitor): non-finite · range · stuck · timing · timeout · EKF numeric · EKF range · command ·\nconfig · calibration.", fontsize=6.8, color=INK2, va="bottom")
    fig.savefig(OUT / "fig_safety_states.png", dpi=200, bbox_inches="tight"); plt.close(fig)

def fig_ekf_lqr():
    fig, ax = canvas(7.4, 2.8, "Estimation and control signal flow (per 208 Hz sample)")
    box(ax, 0.2, 1.0, 1.7, 1.2, "IMU\na, ω\n(− offsets)", fc="#e8eef8")
    box(ax, 2.3, 0.9, 3.0, 1.4, "EKF  x = [φ, θ]\npredict: Euler-rate kinematics\nupdate: φ_a = atan2(a_y, a_z)\nθ_a = atan2(−a_x, √(a_y²+a_z²))", fc="#fbeee6", fs=6.3)
    box(ax, 5.9, 1.0, 2.0, 1.2, "LQR\nu = −K·[φ, p, θ, q]ᵀ\nservo = 90° ± u", fc="#fbeee6", fs=7.5)
    box(ax, 8.3, 1.0, 1.5, 1.2, "guard → PWM\n(roll, pitch)", fc="#e6f4ee")
    arrow(ax, (1.9, 1.6), (2.3, 1.6)); arrow(ax, (5.3, 1.6), (5.9, 1.6), "φ, θ"); arrow(ax, (7.9, 1.6), (8.3, 1.6))
    ax.annotate("", xy=(6.9, 1.0), xytext=(1.05, 1.0), arrowprops=dict(arrowstyle="-|>", color=INK2, lw=1.0, ls="--", connectionstyle="arc3,rad=0.22"))
    ax.text(4.0, 0.05, "gyro rates p, q (bias-corrected) go directly to the LQR", fontsize=7, color=INK2, ha="center", va="top")
    fig.savefig(OUT / "fig_ekf_lqr_flow.png", dpi=200, bbox_inches="tight"); plt.close(fig)

if __name__ == "__main__":
    fig_freq(); fig_lever(); fig_firmware(); fig_safety(); fig_ekf_lqr()
    print(sorted(p.name for p in OUT.glob("*.png")))
