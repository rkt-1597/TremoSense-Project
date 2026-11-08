#include "lqr.h"

/* LQR State Vector
 *
 * x_state[0] -> Roll angle            (phi)   [rad]   from the EKF
 * x_state[1] -> Roll angular velocity (p)     [rad/s] gyroscope, bias-corrected
 * x_state[2] -> Pitch angle           (theta) [rad]   from the EKF
 * x_state[3] -> Pitch angular velocity(q)     [rad/s] gyroscope, bias-corrected
 */
void lqr_compute(const lqr_gain_t *gain, float phi_rad, float p_rads, float theta_rad, float q_rads,
                 float neutral_deg, lqr_result_t *out) {
    const float(*K)[4] = (const float(*)[4])gain->k;
    const float x[4] = {phi_rad, p_rads, theta_rad, q_rads};

    const float u_roll_rad = -(K[0][0] * x[0] + K[0][1] * x[1] + K[0][2] * x[2] + K[0][3] * x[3]);
    const float u_pitch_rad = -(K[1][0] * x[0] + K[1][1] * x[1] + K[1][2] * x[2] + K[1][3] * x[3]);

    out->roll_to_servo = -(u_roll_rad * RAD_TO_DEG) + neutral_deg;
    out->pitch_to_servo = (u_pitch_rad * RAD_TO_DEG) + neutral_deg;
}
