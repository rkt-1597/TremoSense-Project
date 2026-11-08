#ifndef IMU_CAL_H
#define IMU_CAL_H

/* Boot-time IMU offset estimation with acceptance checks. Portable C99. */

#include <stdint.h>

typedef struct {
    uint32_t n;
    float mean[6]; /* ax ay az gx gy gz */
    float m2[6];   /* Welford sum of squared deviations */
} imu_cal_acc_t;

typedef struct {
    float gyro_std_max_rads;
    float accel_norm_tol_ms2;
    float tilt_max_ms2;
    float gravity_ms2;
    uint32_t min_samples;
} imu_cal_limits_t;

typedef struct {
    float accel_offset[3];
    float gyro_offset[3];
    float gyro_std_max;    /* worst-axis standard deviation [rad/s] */
    float accel_norm_mean; /* [m/s^2] */
} imu_cal_result_t;

typedef enum {
    IMU_CAL_OK = 0,
    IMU_CAL_ERR_SAMPLES = -1,    /* too few or non-finite samples */
    IMU_CAL_ERR_MOTION = -2,     /* gyro noise too high: board not still */
    IMU_CAL_ERR_ORIENTATION = -3 /* not level / gravity magnitude wrong */
} imu_cal_status_t;

void imu_cal_reset(imu_cal_acc_t *acc);

/* Returns 0 on success, -1 if any value is non-finite (sample ignored). */
int imu_cal_add(imu_cal_acc_t *acc, const float accel[3], const float gyro[3]);

/* Offsets follow the original firmware: gyro offset = mean gyro; accel
 * offset x,y = mean; z = mean - g (assumes the board is level). The result
 * is filled even on failure so it can be logged, but must not be used. */
imu_cal_status_t imu_cal_finish(const imu_cal_acc_t *acc, const imu_cal_limits_t *lim,
                                imu_cal_result_t *res);

#endif /* IMU_CAL_H */
