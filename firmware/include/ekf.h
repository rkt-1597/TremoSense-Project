#ifndef EKF_H
#define EKF_H

/* Two-state (roll, pitch) Extended Kalman Filter. Portable C99: no RTOS
 * dependency, unit-tested on the host. */

#include <stdbool.h>
#include <stdint.h>

#ifndef RAD_TO_DEG
#define RAD_TO_DEG 57.2957795f
#endif

typedef struct {
    float roll;  /* [deg] */
    float pitch; /* [deg] */
} ekf_result_t;

typedef enum {
    EKF_OK = 0,
    EKF_ERR_CONFIG = -1, /* invalid configuration */
    EKF_ERR_INPUT = -2,  /* non-finite sensor input */
    EKF_ERR_DT = -3,     /* dt outside (0, dt_max] */
    EKF_ERR_NUMERIC = -4 /* singular S, non-finite or negative covariance */
} ekf_status_t;

typedef struct {
    float q;             /* process noise, per step, >= 0 */
    float r;             /* measurement noise, > 0 */
    float max_pitch_rad; /* in (0, pi/2) */
    float dt_max_s;      /* reject larger dt */
    bool gate_enable;    /* inflate R when | |a| - g | > gate_band_ms2 */
    float gate_band_ms2;
    float gate_r_scale; /* >= 1 */
    float gravity_ms2;
} ekf_config_t;

typedef struct {
    float x[2]; /* roll, pitch [rad] */
    float P[2][2];
    ekf_config_t cfg;
    uint32_t gated_count; /* updates whose R was inflated */
} ekf_t;

ekf_status_t ekf_config_check(const ekf_config_t *cfg);

/* Initialise to roll = pitch = 0, P = 0.1 I (identical to the legacy code). */
ekf_status_t ekf_init(ekf_t *f, const ekf_config_t *cfg);

/* Re-initialise after divergence; seeds the angles from the accelerometer
 * when it is finite and non-degenerate, otherwise from zero. */
void ekf_reset(ekf_t *f, float ax, float ay, float az);

/* One predict+update step. ax..az: accelerometer [m/s^2], gx..gz: bias-
 * corrected gyroscope [rad/s]. On any error the state is left unchanged and
 * *out is not written. */
ekf_status_t ekf_update(ekf_t *f, float ax, float ay, float az, float gx, float gy, float gz,
                        float dt, ekf_result_t *out);

#endif /* EKF_H */
