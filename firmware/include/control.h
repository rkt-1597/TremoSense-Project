#ifndef CONTROL_H
#define CONTROL_H

/* Sensing -> estimation -> control step as one pure function, so that the
 * complete loop can be exercised on the host without an RTOS. */

#include <stdbool.h>
#include <stdint.h>
#include "ekf.h"
#include "lqr.h"
#include "safety.h"

typedef struct {
    ekf_config_t ekf;
    monitor_config_t monitor;
    lqr_gain_t K;
    float neutral_deg;
} control_config_t;

typedef struct {
    float roll_deg; /* servo command */
    float pitch_deg;
    bool valid;      /* false => the guard must not follow this command */
    uint32_t faults; /* flags raised on this step */
    float est_roll_deg;
    float est_pitch_deg;
} servo_cmd_t;

typedef struct {
    ekf_t ekf;
    monitor_t mon;
    control_config_t cfg;
    float accel_offset[3];
    float gyro_offset[3];
    uint32_t ekf_resets;
} control_t;

/* Fill 'cfg' from constants.h. */
void control_default_config(control_config_t *cfg);

/* Returns 0 if the configuration is usable. On a non-zero return the
 * control_t is still initialised, with FAULT_CONFIG asserted permanently, so
 * that every subsequent step reports valid = false. */
int control_init(control_t *c, const control_config_t *cfg);

void control_set_offsets(control_t *c, const float accel_off[3], const float gyro_off[3]);

/* Called when calibration fails: latches FAULT_CAL. */
void control_fail_calibration(control_t *c);

/* Called when no sample arrived in time. */
servo_cmd_t control_timeout(control_t *c);

/* One control step from raw (not offset-corrected) IMU values.
 * accel [m/s^2], gyro [rad/s], dt [s]. */
servo_cmd_t control_step(control_t *c, const float accel_raw[3], const float gyro_raw[3], float dt);

#endif /* CONTROL_H */
