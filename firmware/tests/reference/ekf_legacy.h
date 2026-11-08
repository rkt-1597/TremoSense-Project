#ifndef EKF_LEGACY_H
#define EKF_LEGACY_H
#include "ekf.h"
void legacy_ekf_init(void);
void legacy_ekf_update(float ax, float ay, float az, float gx, float gy, float gz,
                       float dt, float Q_val, float R_val, ekf_result_t *result);
#endif
