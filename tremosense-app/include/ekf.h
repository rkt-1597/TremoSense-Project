#ifndef EKF_H
#define EKF_H

#include <zephyr/logging/log.h>
#include "constants.h"

typedef struct {
    float roll; 
    float pitch;
} ekf_result_t;

extern ekf_result_t ekf_calculated_results;

#define RAD_TO_DEG 57.2957795f

void ekf_init(void);

void ekf_update(float ax, float ay, float az,
                float gx, float gy, float gz,
                float dt, float Q_val, float R_val,
                ekf_result_t *result);

#endif /* EKF_H */