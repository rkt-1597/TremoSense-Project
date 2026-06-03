#include "lqr.h"
#include "pwm.h"

/* LQR State Vector
 *
 * x_state[0] -> Roll angle            (phi)   [rad]
 * x_state[1] -> Roll angular velocity (p)     [rad/s]
 * x_state[2] -> Pitch angle           (theta) [rad]
 * x_state[3] -> Pitch angular velocity(q)     [rad/s]
 *
 * Roll and pitch angles are obtained from the EKF.
 * Roll and pitch rates are obtained directly from the gyroscope and used after 
 * bias correction.
 */

lqr_result_t obtained_lqr_values;

void lqr_update(float phi_deg, float theta_deg, 
                float p_raw, float q_raw, 
                float bias_phi, float bias_theta) 
{
    float phi_rad = phi_deg * DEG_TO_RAD;
    float theta_rad = theta_deg * DEG_TO_RAD;

    float p_clean = p_raw - bias_phi;
    float q_clean = q_raw - bias_theta;

    float x_state[4] = {phi_rad, p_clean, theta_rad, q_clean};

    float u_roll_rad  = -(K_lqr[0][0]*x_state[0] + K_lqr[0][1]*x_state[1] + 
                          K_lqr[0][2]*x_state[2] + K_lqr[0][3]*x_state[3]);
                          
    float u_pitch_rad = -(K_lqr[1][0]*x_state[0] + K_lqr[1][1]*x_state[1] + 
                          K_lqr[1][2]*x_state[2] + K_lqr[1][3]*x_state[3]);

    obtained_lqr_values.roll_to_servo  = -(u_roll_rad * RAD_TO_DEG) + 90.0f;
    obtained_lqr_values.pitch_to_servo = (u_pitch_rad * RAD_TO_DEG) + 90.0f;

    while (k_msgq_put(&lqr_res, &obtained_lqr_values, K_NO_WAIT) != 0) {
            k_msgq_purge(&lqr_res);
    }
}