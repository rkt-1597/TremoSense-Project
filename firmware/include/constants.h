#ifndef CONSTANTS_H
#define CONSTANTS_H

/* ------------------------------------------------------------------------
 * Tuning constants.
 *
 * The first four values below are deliberately left at 0 in the public
 * repository: they are device-specific and come from the MATLAB workflow in
 * algorithms/matlab (K_lqr from LQR_ARE.m, Q/R from the EKF block of the
 * Simulink model). The firmware REFUSES TO ACTUATE while they are invalid
 * (see config_validate() in control_config.c) and holds the servos at
 * neutral instead of running with undefined behaviour.
 * ---------------------------------------------------------------------- */

/* EKF process noise covariance (Q), added to each diagonal element of P per
 * step. Higher values increase reliance on accelerometer corrections.
 * Must be >= 0.
 */
#define Q_GYRO_PROCESS_NOISE 0.0f

/* EKF measurement noise covariance (R) for the accelerometer angle
 * measurements. Higher values increase reliance on gyroscope integration.
 * Must be > 0.
 */
#define R_ACCEL_MEASUREMENT_NOISE 0.0f

/* LQR Controller Gain :
 * Row 0 -> Roll servo controller gains
 * Row 1 -> Pitch servo controller gains
 *
 * Column 0 -> Roll angle gain
 * Column 1 -> Roll angular velocity gain
 * Column 2 -> Pitch angle gain
 * Column 3 -> Pitch angular velocity gain
 */
static const float K_lqr[2][4] = {
    { 0.0f, 0.0f, 0.0f, 0.0f },
    { 0.0f, 0.0f, 0.0f, 0.0f }
};

/* Limit pitch estimate to avoid Euler-angle singularities
 * (tan(), sec()) near +-90 deg. Must be in (0, pi/2).
 */
#define MAX_PITCH_RAD 0.0f

/* ------------------------------------------------------------------------
 * Safety and robustness parameters (added on branch pranshu-updates).
 * Defaults are engineering judgements, NOT validated on hardware; the
 * rationale for each is in documentation/architecture/PARAMETERS.md.
 * ---------------------------------------------------------------------- */

#define GRAVITY_MS2 9.80665f

/* Nominal IMU output data rate [Hz] (must match imu_driver_init()). */
#define IMU_ODR_HZ 208.0f

/* --- IMU sample validation --- */
#define SAFETY_ACCEL_MAX_MS2   156.9064f  /* +-16 g full scale */
#define SAFETY_GYRO_MAX_RADS   34.9066f   /* +-2000 dps full scale */
#define SAFETY_DT_MIN_S        0.0005f    /* 0.5 ms */
#define SAFETY_DT_MAX_S        0.0200f    /* ~4 nominal periods */
#define SAFETY_STUCK_SAMPLES   32         /* identical consecutive raw samples */
#define SAFETY_MAX_CONSEC_BAD  10         /* ~48 ms at 208 Hz */
#define SAFETY_RECOVER_GOOD    208        /* ~1 s of good samples to clear */
#define SAFETY_ANGLE_LIMIT_DEG 80.0f      /* |roll| above this => estimate invalid */

/* --- Optional accelerometer gating in the EKF (disabled: legacy behaviour) --- */
#define EKF_GATE_ENABLE        0
#define EKF_GATE_BAND_MS2      3.0f       /* | |a| - g | above this => inflate R */
#define EKF_GATE_R_SCALE       100.0f

/* --- Actuator guard --- */
#define SERVO_NEUTRAL_DEG      90.0f
#define SERVO_CMD_MIN_DEG      0.0f       /* full servo range: legacy behaviour */
#define SERVO_CMD_MAX_DEG      180.0f
#define SERVO_MAX_SLEW_DPS     0.0f       /* 0 = disabled (legacy behaviour) */
#define SERVO_SAFE_SLEW_DPS    60.0f      /* gentle return to level in a fault */
#define GUARD_HOLD_MS          100        /* max time to hold last-good output */
#define GUARD_CMD_TIMEOUT_MS   50         /* no command from control loop */
#define GUARD_RECOVER_GOOD     208        /* valid commands needed to resume */

/* --- Boot calibration acceptance --- */
#define CAL_SAMPLES            624        /* 3 s at 208 Hz */
#define CAL_GYRO_STD_MAX_RADS  0.02f      /* ~1.1 dps: board must be still */
#define CAL_ACCEL_NORM_TOL_MS2 0.5f       /* |mean|a| - g| */
#define CAL_TILT_MAX_MS2       1.5f       /* |mean ax|,|mean ay| (~8.8 deg) */
#define CAL_MAX_ATTEMPTS       3

#endif /* CONSTANTS_H */
