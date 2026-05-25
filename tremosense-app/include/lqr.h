#ifndef LQR_H
#define LQR_H

#include "constants.h"
#include <zephyr/kernel.h>

#define DEG_TO_RAD 0.01745329f
#define RAD_TO_DEG 57.2957795f

typedef struct {
    float roll_to_servo; 
    float pitch_to_servo;
} lqr_result_t;

extern struct k_msgq lqr_res;

extern lqr_result_t obtained_lqr_values;
extern lqr_result_t lqr_val_to_servos;

void lqr_update(float phi_deg, float theta_deg, 
                float p_raw, float q_raw, 
                float bias_phi, float bias_theta);

#endif /* LQR_H */