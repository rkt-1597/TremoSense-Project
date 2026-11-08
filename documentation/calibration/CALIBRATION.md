# IMU calibration

Implemented in `firmware/src/sensors/imu_cal.c` (portable) and `src/application/calibration.c` (Zephyr, LED behaviour kept from the original).

## Procedure (user-facing)

1. Power on with the board **level and still**. Blue LED on for 3 s, then calibration collects 624 samples (3 s at 208 Hz), then the LED blinks 5 s while offsets print on the console.
2. If motion or non-level orientation is detected the attempt is rejected and repeated (max 3). After 3 failures the servos stay at neutral and the failure is logged.

## Method

Welford mean/variance per axis. Accepted only if gyro std ≤ `CAL_GYRO_STD_MAX_RADS`, |mean |a| − g| ≤ `CAL_ACCEL_NORM_TOL_MS2`, and |mean a_x|, |mean a_y| ≤ `CAL_TILT_MAX_MS2`. Offsets: gyro = mean; accel x,y = mean; accel z = mean − g (as in the original).

## Evidence

Host tests (`test_lqr_timing_cal.c`) cover acceptance, motion rejection, tilt rejection and too-few samples with synthetic data. **Not tested:** real IMU noise/temperature drift, repeatability across power cycles (test TC-HW cases in `VV_PLAN.md`, NOT RUN).

## Known limitations

Calibration is only at boot; no temperature compensation; accel offsets assume the level reference is truly level.
