#include "control.h"

#include <math.h>
#include <string.h>

#include "constants.h"

void control_default_config(control_config_t *cfg) {
    memset(cfg, 0, sizeof(*cfg));

    cfg->ekf.q = Q_GYRO_PROCESS_NOISE;
    cfg->ekf.r = R_ACCEL_MEASUREMENT_NOISE;
    cfg->ekf.max_pitch_rad = MAX_PITCH_RAD;
    cfg->ekf.dt_max_s = SAFETY_DT_MAX_S;
    cfg->ekf.gate_enable = (EKF_GATE_ENABLE != 0);
    cfg->ekf.gate_band_ms2 = EKF_GATE_BAND_MS2;
    cfg->ekf.gate_r_scale = EKF_GATE_R_SCALE;
    cfg->ekf.gravity_ms2 = GRAVITY_MS2;

    cfg->monitor.accel_max_ms2 = SAFETY_ACCEL_MAX_MS2;
    cfg->monitor.gyro_max_rads = SAFETY_GYRO_MAX_RADS;
    cfg->monitor.dt_min_s = SAFETY_DT_MIN_S;
    cfg->monitor.dt_max_s = SAFETY_DT_MAX_S;
    cfg->monitor.angle_limit_deg = SAFETY_ANGLE_LIMIT_DEG;
    cfg->monitor.stuck_samples = SAFETY_STUCK_SAMPLES;
    cfg->monitor.max_consec_bad = SAFETY_MAX_CONSEC_BAD;
    cfg->monitor.recover_good = SAFETY_RECOVER_GOOD;

    memcpy(cfg->K.k, K_lqr, sizeof(cfg->K.k));
    cfg->neutral_deg = SERVO_NEUTRAL_DEG;
}

int control_init(control_t *c, const control_config_t *cfg) {
    memset(c, 0, sizeof(*c));
    c->cfg = *cfg;
    monitor_init(&c->mon, &cfg->monitor);

    int rc = 0;
    if (ekf_init(&c->ekf, &cfg->ekf) != EKF_OK) {
        rc = -1;
    }
    for (int i = 0; i < 2 && rc == 0; i++) {
        for (int j = 0; j < 4; j++) {
            if (!isfinite(cfg->K.k[i][j])) {
                rc = -1;
            }
        }
    }
    if (rc != 0) {
        monitor_assert_permanent(&c->mon, FAULT_CONFIG);
    }
    return rc;
}

void control_set_offsets(control_t *c, const float accel_off[3], const float gyro_off[3]) {
    memcpy(c->accel_offset, accel_off, sizeof(c->accel_offset));
    memcpy(c->gyro_offset, gyro_off, sizeof(c->gyro_offset));
}

void control_fail_calibration(control_t *c) {
    monitor_assert_permanent(&c->mon, FAULT_CAL);
}

servo_cmd_t control_timeout(control_t *c) {
    servo_cmd_t out;
    memset(&out, 0, sizeof(out));
    out.roll_deg = c->cfg.neutral_deg;
    out.pitch_deg = c->cfg.neutral_deg;
    out.faults = FAULT_IMU_TIMEOUT;
    (void)monitor_note(&c->mon, FAULT_IMU_TIMEOUT);
    out.valid = false; /* a timeout never yields a usable command */
    return out;
}

servo_cmd_t control_step(control_t *c, const float accel_raw[3], const float gyro_raw[3],
                         float dt) {
    servo_cmd_t out;
    memset(&out, 0, sizeof(out));
    out.roll_deg = c->cfg.neutral_deg;
    out.pitch_deg = c->cfg.neutral_deg;

    uint32_t flags = monitor_classify_sample(&c->mon, accel_raw, gyro_raw, dt);

    float a[3], g[3];
    for (int i = 0; i < 3; i++) {
        a[i] = accel_raw[i] - c->accel_offset[i];
        g[i] = gyro_raw[i] - c->gyro_offset[i];
    }

    ekf_result_t est = {0.0f, 0.0f};
    lqr_result_t cmd = {c->cfg.neutral_deg, c->cfg.neutral_deg};
    bool have_cmd = false;

    if (flags == FAULT_NONE) {
        const ekf_status_t st = ekf_update(&c->ekf, a[0], a[1], a[2], g[0], g[1], g[2], dt, &est);
        flags |= monitor_classify_estimate(&c->mon, st, &est);
        if (st == EKF_ERR_NUMERIC) {
            ekf_reset(&c->ekf, a[0], a[1], a[2]);
            c->ekf_resets++;
        } else if (st == EKF_OK) {
            lqr_compute(&c->cfg.K, est.roll * DEG_TO_RAD, g[0], est.pitch * DEG_TO_RAD, g[1],
                        c->cfg.neutral_deg, &cmd);
            have_cmd = true;
            if (!isfinite(cmd.roll_to_servo) || !isfinite(cmd.pitch_to_servo)) {
                flags |= FAULT_CMD_INVALID;
                have_cmd = false;
            }
        }
    }

    out.est_roll_deg = est.roll;
    out.est_pitch_deg = est.pitch;
    out.faults = flags;
    const bool usable = monitor_note(&c->mon, flags);
    if (usable && have_cmd) {
        out.roll_deg = cmd.roll_to_servo;
        out.pitch_deg = cmd.pitch_to_servo;
        out.valid = true;
    }
    return out;
}
