#ifndef CONSTANTS_H
#define CONSTANTS_H

/* EKF process noise covariance (Q).
 * Represents uncertainty in the gyroscope-based prediction model.
 * Higher values increase reliance on accelerometer corrections.
 */
#define Q_GYRO_PROCESS_NOISE 0.0f

/* EKF measurement noise covariance (R).
 * Represents uncertainty in accelerometer angle measurements.
 * Higher values increase reliance on gyroscope integration.
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
 * (tan(), sec()) near ±90°.
 */
#define MAX_PITCH_RAD 0.0f

#endif /* CONSTANTS_H */