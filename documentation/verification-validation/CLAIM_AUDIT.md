# Audit of the "~90 % tremor rejection" claim

**Verdict: the ~90 % figure is a Simulink simulation result. It cannot be verified from hardware logs, because the
repository contains none.** It must not be presented as measured hardware performance.

## What exists in the repository

| Source | Statement | Nature |
|---|---|---|
| `README.md` | residual RMS 0.346° (roll), 0.573° (pitch) for an 8° / 8 Hz tremor on all three axes | Simulink, model-based |
| `README.md` | ">90 %" roll and ">80 %" pitch suppression across "most of" 3–7 Hz, amplitudes 2–7° | Simulink, `tfestimate` of input vs residual |
| `algorithms/matlab/assets/*.png` | scope screenshots / frequency-response plots | Simulink output images |
| `algorithms/matlab/RMS.m`, `*_Freq_Analysis.m` | scripts that read `TremoSense_Model.slx` | cannot be run: the `.slx` model is not in the repository |
| hardware logs, CSVs, test-rig description | — | **absent** |

## Arithmetic from the stated numbers

A sinusoid of 8° amplitude has an RMS of 8/√2 = 5.657°. Taking that as the input RMS (`RMS.m` would print the actual value):

| Axis | Residual RMS | Reduction = 1 − residual/input |
|---|---|---|
| Roll | 0.346° | **93.9 %** |
| Pitch | 0.573° | **89.9 %** |

So "~90 %" is consistent with the *pitch* simulation figure at one operating point (8 Hz, 8°), and roll is higher.
The roll plot reads about −25 dB (94.4 %) at low frequency and no worse than about −20 dB (90 %) anywhere in 0–8 Hz.

## Why this is not a hardware result

1. The plant parameters in `LQR_ARE.m` (masses, radii, torques, weights) are blank in the repository, so `K_lqr` cannot be regenerated or the simulation reproduced.
2. The model uses a 4-state EKF and zeroes the rate states in `LQR.m`; the firmware uses a 2-state EKF and measured rates (audit D-14).
3. The simulation runs at 1 kHz; the firmware runs the loop at 208 Hz with a 50 Hz servo PWM (D-19).
4. The magnitude response is ≈ −25 dB even at 0–2 Hz: the model attenuates slow, voluntary-scale motion as much as tremor (D-15). A high "rejection" number therefore says nothing about preserving intentional movement.
5. The earlier paper prototype reported 77.3 % mean rejection over 4–8 Hz (per the project owners); that document is not in this repository either and could not be checked here.

## What would verify it

Instrumented bench test (motor-driven tremor rig or a second reference IMU on the spoon bowl and a hand-side IMU), logged
at ≥ 1 kHz with synchronised timestamps; input and residual RMS per frequency, per amplitude, per axis; repeatability over
≥ 5 runs; also a voluntary-motion trial (slow 0.2–1 Hz commanded rotation) to quantify resistance. Procedure: TC-PERF-001..003
in the [V&V plan](VV_PLAN.md). **Status: NOT RUN.**
