#include "imu_cal.h"

#include <math.h>
#include <string.h>

void imu_cal_reset(imu_cal_acc_t *acc) {
    memset(acc, 0, sizeof(*acc));
}

int imu_cal_add(imu_cal_acc_t *acc, const float accel[3], const float gyro[3]) {
    const float v[6] = {accel[0], accel[1], accel[2], gyro[0], gyro[1], gyro[2]};

    for (int i = 0; i < 6; i++) {
        if (!isfinite(v[i])) {
            return -1;
        }
    }
    acc->n++;
    for (int i = 0; i < 6; i++) {
        const float d = v[i] - acc->mean[i];
        acc->mean[i] += d / (float)acc->n;
        acc->m2[i] += d * (v[i] - acc->mean[i]);
    }
    return 0;
}

imu_cal_status_t imu_cal_finish(const imu_cal_acc_t *acc, const imu_cal_limits_t *lim,
                                imu_cal_result_t *res) {
    memset(res, 0, sizeof(*res));
    if (acc->n < lim->min_samples || acc->n < 2U) {
        return IMU_CAL_ERR_SAMPLES;
    }

    res->accel_offset[0] = acc->mean[0];
    res->accel_offset[1] = acc->mean[1];
    res->accel_offset[2] = acc->mean[2] - lim->gravity_ms2;
    for (int i = 0; i < 3; i++) {
        res->gyro_offset[i] = acc->mean[3 + i];
        const float sd = sqrtf(acc->m2[3 + i] / (float)(acc->n - 1U));
        if (sd > res->gyro_std_max) {
            res->gyro_std_max = sd;
        }
    }
    res->accel_norm_mean = sqrtf(acc->mean[0] * acc->mean[0] + acc->mean[1] * acc->mean[1] +
                                 acc->mean[2] * acc->mean[2]);

    if (res->gyro_std_max > lim->gyro_std_max_rads) {
        return IMU_CAL_ERR_MOTION;
    }
    if (fabsf(res->accel_norm_mean - lim->gravity_ms2) > lim->accel_norm_tol_ms2 ||
        fabsf(acc->mean[0]) > lim->tilt_max_ms2 || fabsf(acc->mean[1]) > lim->tilt_max_ms2) {
        return IMU_CAL_ERR_ORIENTATION;
    }
    return IMU_CAL_OK;
}
