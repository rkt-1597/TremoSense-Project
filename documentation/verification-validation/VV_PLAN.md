# Verification and validation plan

Levels: **S** simulation (synthetic data on a PC), **B** build/static analysis, **HIL** bench with real electronics,
**U** tests with intended users. Hardware (HIL/U) cases are *defined here and NOT RUN* — no hardware was available.

Environment for executed cases: Ubuntu, gcc, CMake/Ninja; target build with Zephyr v4.0.0 and GNU Arm Embedded 13.2.rel1
(apt `gcc-arm-none-eabi`), board `xiao_ble/nrf52840/sense`. Results and versions: [TEST_REPORT](TEST_REPORT.md).

| TC | Level | Input / procedure | Expected | Req. | Executed |
|---|---|---|---|---|---|
| TC-EKF-001 | S | configs with R=0, max pitch 0, Q<0, NaN | `EKF_ERR_CONFIG` | TS-SW-005 | yes |
| TC-EKF-002 | S | static tilt 10°/5°, 1040 steps | |err| ≤ 0.05° | TS-SW-003 | yes |
| TC-EKF-003 | S | NaN/Inf input, dt ≤ 0, dt > max | error code, state bit-identical, output untouched | TS-SW-003 | yes |
| TC-EKF-004 | S | Q=0, R=1e-20, 2000 steps | never non-finite | TS-SW-003 | yes |
| TC-EKF-005 | S | `ekf_reset` from accel / from NaN | seeded / zero | TS-SW-003 | yes |
| TC-EKF-006 | S | 6000 noisy tremor samples through legacy and new filters | max \|Δ\| < 0.01° (observed 0.0) | TS-SW-004 | yes |
| TC-EKF-007 | S | 12 m/s² lateral acceleration burst, gating on/off | gated error < ungated | (analysis) | yes |
| TC-EKF-008 | S | legacy filter with the shipped constants | NaN (defect evidence) | TS-SW-005 | yes |
| TC-LQR-001 | S | 500 random states vs the original expression | equal, sign convention preserved | TS-SW-004 | yes |
| TC-TIM-001 | S | wrap, resolution, zero rate | exact | TS-SW-002 | yes |
| TC-CAL-001..004 | S | good / moving / tilted / free-fall / too few samples | OK / MOTION / ORIENTATION / ORIENTATION / SAMPLES | TS-SW-006 | yes |
| TC-SAF-001..004 | S | monitor classification, stuck run, assert/clear, permanent faults | per spec | TS-SW-002, TS-SAF-004 | yes |
| TC-SAF-005..009 | S | guard clamp, NaN, hold→neutral timing, slew, recovery, disable | per spec | TS-SAF-001..004 | yes |
| TC-INT-001..008 | S | full sensing→control→guard loop with fault injection | per spec | TS-SW-005/006, TS-SAF-001/002 | yes |
| TC-SIM-001 | S | baseline vs updated vs gated estimator, 3–8 Hz, 4 tunings, 4 lever arms, 10 seeds | report RMS, gain, lag | TS-PERF-001 | yes |
| TC-BLD-001..003 | B | Zephyr build: baseline main, updated, LED-test variant | builds | TS-SW-010 | yes |
| TC-BLD-004/005 | B | cppcheck, `gcc -fanalyzer`, `-Werror -Wconversion`, ASan/UBSan | clean | TS-SW-010 | yes |
| TC-HW-001 | HIL | log data-ready timestamps ≥ 10 min | ODR 208 Hz ± tol, jitter distribution, drops = 0 | TS-SW-001 | **NOT RUN** |
| TC-HW-002 | HIL | GPIO toggle at sample arrival and at PWM update, logic analyser | latency distribution, max | TS-PERF-002, TS-SW-008 | **NOT RUN** |
| TC-HW-003 | HIL | servo step response, per axis, with the real linkage and load | rise time, overshoot | TS-PERF-002 | **NOT RUN** |
| TC-HW-004 | HIL | scope on supply rail during servo transients; battery discharge | droop, ripple, brown-out margin | TS-PERF-004, TS-SAF-007 | **NOT RUN** |
| TC-HW-005 | HIL | force a loop hang (debug build) | reset ≤ 500 ms | TS-SAF-005 | **NOT RUN** |
| TC-HW-006 | HIL | power-cycle with scope on PWM pins | neutral pulse train time-to-first-pulse | TS-SAF-005 | **NOT RUN** |
| TC-HW-007 | HIL | disconnect IMU during run | SAFE_NEUTRAL entered ≤ 150 ms; pose at 90° within tilt/60 °/s thereafter; no spill with a test load | TS-SAF-002 | **NOT RUN** |
| TC-HW-008 | HIL | continuous run on battery | runtime, voltage vs time | TS-PERF-004 | **NOT RUN** |
| TC-HW-009 | HIL | mechanical range / pinch-point check at limits | no collision; set safe limits | R-05 | **NOT RUN** |
| TC-HW-010 | HIL | block servo | detection/de-energise (not implemented) | TS-SAF-006 | **NOT RUN** |
| TC-HW-011 | U | usability and fault visibility with intended users, ethics approval first | per protocol | TS-SYS-002, TS-SAF-008 | **NOT RUN** |
| TC-PERF-001 | HIL | motor-driven tremor rig, 3–8 Hz × 2–7°, reference IMU on spoon bowl | input/residual RMS per f, axis | TS-SYS-003 | **NOT RUN** |
| TC-PERF-002 | HIL | as above, residual angular error and phase | report | TS-PERF-001 | **NOT RUN** |
| TC-PERF-003 | HIL | slow 0.2–1 Hz commanded rotation | residual resistance | TS-SYS-002 | **NOT RUN** |
| TC-PERF-004 | HIL | step/impulse disturbance | overshoot, settling | TS-SYS-001 | **NOT RUN** |
| TC-PERF-005 | HIL | ≥ 1 h soak | 0 faults/resets | TS-PERF-003 | **NOT RUN** |

Every hardware result must be recorded with firmware commit hash, board serial/revision, servo models, supply, and raw logs
under `data/raw/` (not yet created: no data exist). Simulation, bench and user results must be labelled as such in every
document and paper.
