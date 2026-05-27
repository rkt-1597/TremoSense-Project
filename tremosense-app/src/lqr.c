#include "lqr.h"
#include "pwm.h"

float target_servo_roll_deg, target_servo_pitch_deg;

void lqr_update(float phi_deg, float theta_deg, 
                float p_raw, float q_raw, 
                float bias_phi, float bias_theta, 
                float *u_roll_deg, float *u_pitch_deg) 
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

    *u_roll_deg  = -(u_roll_rad * RAD_TO_DEG) + 90.0f;
    *u_pitch_deg = (u_pitch_rad * RAD_TO_DEG) + 90.0f;
}