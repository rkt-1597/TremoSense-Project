#ifndef LQR_H
#define LQR_H

#include "constants.h"

#define DEG_TO_RAD 0.01745329f
#define RAD_TO_DEG 57.2957795f

#define MAX_PITCH_RAD 1.39626f

void lqr_update(float phi_deg, float theta_deg, 
                float p_raw, float q_raw, 
                float bias_phi, float bias_theta, 
                float *u_roll_deg, float *u_pitch_deg);

#endif /* LQR_H */