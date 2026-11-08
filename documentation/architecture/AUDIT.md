# TremoSense technical audit

Baseline: `main` @ `9ae4958` ("Refine README.md, tuning guide, and control-system annotations"). Audit method: source
reading of every firmware file and MATLAB script, a real Zephyr build of the baseline, and host tests that exercise the
baseline EKF directly (`firmware/tests/reference/ekf_legacy.c` is a verbatim renamed copy). Findings are about the
repository as committed; anything that lives only on the authors' bench is listed as *unverifiable*.

## 1. Claimed vs verified

| Claim | Verdict | Evidence |
|---|---|---|
| Zephyr RTOS, multi-threaded, msgq + semaphore | **Verified** | `src/application/main.c` (2 threads, 1 msgq, 1 sem in baseline) |
| LSM6DS3 IMU | **Verified (driver)** | DT node `st,lsm6dsl` (the driver used for the LSM6DS3TR-C on the XIAO Sense); part number not in repo docs |
| 208 Hz IMU sampling, data-ready trigger | **Verified** | `imu_init()`: ODR 208 Hz, `SENSOR_TRIG_DATA_READY`. Actual ODR accuracy and timing jitter: **not measured** |
| Two-state EKF (roll, pitch) | **Verified (firmware)** | `ekf.c`. Note the *MATLAB* EKF has 4 states (adds two gyro biases): see D-14 |
| LQR → servos | **Verified** | `lqr.c` (state-feedback, 2×4 gain), `pwm.c` |
| MG995 (roll) + FS90MG (pitch) | **README only** | firmware has only per-axis pulse ranges (722–2278 µs roll, 900–2100 µs pitch). Note: a different servo model appears in other project notes — confirm the BOM |
| Boost converter + capacitor stabilisation | **Not in repo** | no schematic, BOM or power documentation exists; cannot be audited |
| Validated at 1000 Hz in Simulink | **Documented, not reproducible** | `TremoSense_Model.slx` is not in the repo (PDF export only); `LQR_ARE.m` plant parameters are blank. Deployed rate is 208 Hz (D-19) |
| "~90 % tremor rejection" | **Not verifiable from hardware logs** | see [CLAIM_AUDIT](../verification-validation/CLAIM_AUDIT.md) |
| Tuned Q, R, K | **Blank** | `constants.h` ships all zeros (D-01) |

## 2. Findings

Status: **Fixed** = changed and tested on the host / compiled for the target; **Mitigated** = risk reduced, residual
risk remains; **Open** = not resolved. "Fixed" never means hardware-verified: no hardware was available.

| ID | Sev | Finding (baseline behaviour) | Evidence | Status |
|---|---|---|---|---|
| D-01 | High | Shipped `Q=R=0`, `K=0`, `MAX_PITCH_RAD=0`. With `R=0` the gain is `K=I`, `P→0`, then `det(S)=0` → division by zero → **NaN estimate forever**; `MAX_PITCH_RAD=0` pins pitch to 0; `K=0` commands nothing. NaN then reaches the servo conversion (undefined behaviour). | `test_ekf` §8: legacy output `-nan` after 5 updates | **Mitigated**: config validated at boot; invalid tuning → servos held neutral, never actuates. Real device tuning must be supplied by the owners |
| D-02 | High | `uint32_t err; if ((err = pwm_set_pulse_dt(..)) < 0)` — unsigned, so the test is never true; **all PWM errors silently ignored** (also in `servos_reset`) | code inspection (`pwm.c`) | Fixed (`int`) |
| D-03 | High | `set_servo_angle` clamps only `> 180`. Negative or NaN commands convert a negative/NaN float to `uint32_t` (undefined). No mechanical-range limit | code inspection | Fixed: single clamp point in the actuator guard + `angle_to_pulse` |
| D-04 | High | `k_sem_init(&imu_sem)` runs **after** `imu_init()`, which already installs the data-ready trigger and runs the 3 s + 3 s + 5 s calibration; the handler calls `k_sem_give` on an uninitialised semaphore | `main.c` order | Fixed (`K_SEM_DEFINE`) |
| D-05 | High | Six `sensor_value` globals written by the driver thread and read unsynchronised by the control thread and the calibration loop: torn reads are possible (8-byte non-atomic structs); accel and gyro fetched in two bursts with no pairing | code inspection | Fixed: spinlock-protected latest sample + sequence number; drops counted |
| D-06 | Med | `dt` from `k_uptime_get_32()` (1 ms): a 4.808 ms period is seen as 4 ms (−17 %) or 5 ms (+4 %); measured at processing time, not sample time; no bounds (dt=0 possible, first dt unbounded) | code; sim | Fixed: cycle-counter timestamp at the data-ready event, validated. Simulated effect: [EKF_COMPARISON](../verification-validation/EKF_COMPARISON.md) |
| D-07 | Med | `printk` + three `LOG_INF` float lines per sample (208 Hz) inside the control path; `printk` is synchronous and can block on the console | code | Fixed: decimated telemetry (default 1 in 26), deferred log. Latency effect **not measured** |
| D-08 | Med | FIFO of depth 20 between control and actuation threads: a slow consumer acts on commands up to ~96 ms old | code | Fixed: depth-1 latest-wins mailbox |
| D-09 | High | No watchdog. On an IMU error the control thread `k_thread_abort`s itself and the servos keep the last pulse indefinitely | code | Mitigated: WDT supervisor + guard timeout → neutral. Needs hardware validation |
| D-10 | High | No validation of IMU samples (NaN, range, stuck, timing) or of the estimate | code | Fixed (`monitor_*`), 30+ unit tests |
| D-11 | Low | EKF: `(I−KH)P` not symmetrised; singular `S` unguarded | code | Fixed. Output identical to legacy on valid data (max Δ = 0.0 over 6000 samples) |
| D-12 | Med | Calibration accepts any data (board moving or tilted ⇒ wrong offsets, silently); polls a 208 Hz variable at ~100 Hz; assumes level | code | Fixed: stillness/level/gravity acceptance, 3 attempts, then latch fault |
| D-13 | Med | No PWM output until the first command: for the ≥ 11 s boot + calibration the servos receive no pulses | code | Mitigated: neutral commanded at boot before IMU init. Hardware verification needed |
| D-14 | Med | MATLAB EKF is 4-state with gyro-bias states; firmware EKF is 2-state without bias. MATLAB `LQR.m` zeroes the rate states (`x_state=[φ;0;θ;0]`); firmware feeds measured rates. Simulink results therefore do not directly validate the deployed algorithm | code comparison | **Open** (documented; do not port without hardware A/B) |
| D-15 | High | Simulink magnitude response is ≈ −25 dB from 0 Hz upward (`roll_freq_analysis.png`): the loop attenuates *all* low-frequency motion about as much as tremor. No tremor-band selectivity, and no voluntary-movement test exists | figure inspection | **Open**: design limitation, see [SAFETY_ARCHITECTURE](../risk-management/SAFETY_ARCHITECTURE.md) |
| D-16 | Med | Servo PWM period is 20 ms (50 Hz) while commands are issued at 208 Hz: effective actuation update/latency (zero-order hold up to 20 ms, driver behaviour when updating mid-period) is unmeasured | design | **Open** |
| D-17 | Low | Duplicate `RAD_TO_DEG` definitions; `ekf.h` pulled in Zephyr logging (non-portable core); stray `w` after the README table | code | Fixed |
| D-18 | Med | IMU full-scale ±16 g / ±2000 dps, while tremor needs ≲ ±500 dps: coarse gyro LSB (70 mdps). Effect on noise unmeasured | code | **Open** (candidate improvement; needs bench A/B) |
| D-19 | Med | Validation rate (1 kHz) ≠ deployed rate (208 Hz control, 50 Hz PWM) | README vs code | **Open** |
| D-20 | Info | No hardware documentation (schematic, BOM, enclosure, battery, regulator) in the repo; IMU mounting location (hand-side vs platform-side) is not stated, which decides whether the loop is feedback or feed-forward | repo | **Open** (owner input needed) |

## 3. Things deliberately not changed

Control and estimator mathematics, sign conventions, the IMU ODR/full-scale, pin assignments, servo pulse ranges and
the device-tree bindings are unchanged. For valid inputs and zero-fault operation the refactored EKF and LQR produce
the same numbers as the baseline (`test_ekf` §6, `test_lqr_timing_cal`).
