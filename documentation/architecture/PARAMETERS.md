# Parameters and rationale (`firmware/include/constants.h`)

Defaults marked **engineering choice** are not validated on hardware and should be revisited during bench testing.

## Device-specific tuning (intentionally invalid by default)

| Name | Default | Note |
|---|---|---|
| `Q_GYRO_PROCESS_NOISE`, `R_ACCEL_MEASUREMENT_NOISE`, `MAX_PITCH_RAD`, `K_lqr` | 0 | The device's tuned values are not in the repository. The legacy shipped zeros make the EKF return NaN (shown in host tests). Firmware now rejects them (`FAULT_CONFIG`) and holds neutral. Fill from `algorithms/matlab/LQR_ARE.m` and EKF tuning. |

## Safety monitor

| Name | Default | Rationale |
|---|---|---|
| `SAFETY_ACCEL_MAX_MS2` / `GYRO_MAX_RADS` | 156.9 / 34.9 | ±16 g / ±2000 dps configured full scale; larger is a sensor/driver error |
| `SAFETY_DT_MIN_S` / `MAX_S` | 0.5 ms / 20 ms | bounds around the 4.8 ms nominal period; > ~4 periods means missed samples |
| `SAFETY_STUCK_SAMPLES` | 32 | identical raw samples indicate a frozen bus/sensor (real MEMS noise makes this implausible) — **engineering choice** |
| `SAFETY_MAX_CONSEC_BAD` | 10 (~48 ms) | tolerate isolated glitches, trip on sustained faults — **engineering choice** |
| `SAFETY_RECOVER_GOOD` | 208 (~1 s) | avoid chatter on recovery |
| `SAFETY_ANGLE_LIMIT_DEG` | 80 | accel-angle estimate is ill-conditioned near 90° pitch |

## EKF gating (default off)

`EKF_GATE_ENABLE=0`, band 3 m/s², R×100. Simulation shows it is not a uniform win (`EKF_COMPARISON.md`), so it is opt-in.

## Servo guard

| Name | Default | Rationale |
|---|---|---|
| `SERVO_CMD_MIN/MAX_DEG` | 0 / 180 | legacy full range; narrow once mechanical limits of the gimbal are known |
| `SERVO_MAX_SLEW_DPS` | 0 (off) | legacy behaviour preserved; a limit would add phase lag at tremor frequencies |
| `SERVO_SAFE_SLEW_DPS` | 60 | gentle return to level in a fault, avoids spilling food |
| `GUARD_HOLD_MS` | 100 | ≈ half a 5 Hz tremor period; long enough to ride out one bad sample burst — **engineering choice** |
| `GUARD_CMD_TIMEOUT_MS` | 50 | ~10 missed control periods |
| `GUARD_RECOVER_GOOD` | 208 | ~1 s of valid commands before resuming |

## Calibration

| Name | Default | Rationale |
|---|---|---|
| `CAL_SAMPLES` | 624 | 3 s at 208 Hz (original duration) |
| `CAL_GYRO_STD_MAX_RADS` | 0.02 | board must be still; ~1.1 dps — **engineering choice** |
| `CAL_ACCEL_NORM_TOL_MS2` | 0.5 | gravity magnitude check |
| `CAL_TILT_MAX_MS2` | 1.5 | ≈ 8.8° tilt limit; accel offsets assume level |
| `CAL_MAX_ATTEMPTS` | 3 | then latch fault, neutral |
