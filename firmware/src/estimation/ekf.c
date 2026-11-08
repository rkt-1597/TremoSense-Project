#include "ekf.h"

#include <math.h>
#include <string.h>

ekf_status_t ekf_config_check(const ekf_config_t *c) {
    if (c == NULL) {
        return EKF_ERR_CONFIG;
    }
    if (!isfinite(c->q) || c->q < 0.0f) {
        return EKF_ERR_CONFIG;
    }
    if (!isfinite(c->r) || c->r <= 0.0f) {
        return EKF_ERR_CONFIG;
    }
    if (!isfinite(c->max_pitch_rad) || c->max_pitch_rad <= 0.0f || c->max_pitch_rad >= 1.5707963f) {
        return EKF_ERR_CONFIG;
    }
    if (!isfinite(c->dt_max_s) || c->dt_max_s <= 0.0f) {
        return EKF_ERR_CONFIG;
    }
    if (c->gate_enable &&
        (!isfinite(c->gate_band_ms2) || c->gate_band_ms2 <= 0.0f || !isfinite(c->gate_r_scale) ||
         c->gate_r_scale < 1.0f || !isfinite(c->gravity_ms2) || c->gravity_ms2 <= 0.0f)) {
        return EKF_ERR_CONFIG;
    }
    return EKF_OK;
}

static void set_initial(ekf_t *f, float roll, float pitch) {
    f->x[0] = roll;
    f->x[1] = pitch;
    f->P[0][0] = 0.1f;
    f->P[0][1] = 0.0f;
    f->P[1][0] = 0.0f;
    f->P[1][1] = 0.1f;
}

ekf_status_t ekf_init(ekf_t *f, const ekf_config_t *cfg) {
    ekf_status_t st = ekf_config_check(cfg);

    if (f == NULL) {
        return EKF_ERR_CONFIG;
    }
    memset(f, 0, sizeof(*f));
    if (st != EKF_OK) {
        return st;
    }
    f->cfg = *cfg;
    set_initial(f, 0.0f, 0.0f);
    return EKF_OK;
}

void ekf_reset(ekf_t *f, float ax, float ay, float az) {
    float roll = 0.0f, pitch = 0.0f;
    float yz = sqrtf(ay * ay + az * az);

    if (isfinite(ax) && isfinite(ay) && isfinite(az) && (yz > 1e-3f)) {
        roll = atan2f(ay, az);
        pitch = atan2f(-ax, yz);
        if (pitch > f->cfg.max_pitch_rad) {
            pitch = f->cfg.max_pitch_rad;
        } else if (pitch < -f->cfg.max_pitch_rad) {
            pitch = -f->cfg.max_pitch_rad;
        }
    }
    set_initial(f, roll, pitch);
}

ekf_status_t ekf_update(ekf_t *f, float ax, float ay, float az, float gx, float gy, float gz,
                        float dt, ekf_result_t *out) {
    if (f == NULL || out == NULL) {
        return EKF_ERR_CONFIG;
    }
    if (!isfinite(ax) || !isfinite(ay) || !isfinite(az) || !isfinite(gx) || !isfinite(gy) ||
        !isfinite(gz) || !isfinite(dt)) {
        return EKF_ERR_INPUT;
    }
    if (dt <= 0.0f || dt > f->cfg.dt_max_s) {
        return EKF_ERR_DT;
    }

    /* Work on copies so that a numeric failure leaves the filter untouched. */
    float x0 = f->x[0], x1 = f->x[1];
    float P[2][2];
    memcpy(P, f->P, sizeof(P));

    const float p = gx, q = gy, r = gz;
    const float s_phi = sinf(x0);
    const float c_phi = cosf(x0);
    const float s_the = sinf(x1);
    const float c_the = cosf(x1);
    const float t_the = s_the / c_the;
    const float sec_the = (fabsf(c_the) < 0.01f) ? 100.0f : (1.0f / c_the);

    /* PREDICT ---------------------------------------------------------- */
    const float phi_dot = p + q * s_phi * t_the + r * c_phi * t_the;
    const float theta_dot = q * c_phi - r * s_phi;

    x0 += phi_dot * dt;
    x1 += theta_dot * dt;

    const float A11 = q * c_phi * t_the - r * s_phi * t_the;
    const float A12 = (q * s_phi + r * c_phi) * (sec_the * sec_the);
    const float A21 = -q * s_phi - r * c_phi;

    float F[2][2];
    F[0][0] = 1.0f + A11 * dt;
    F[0][1] = A12 * dt;
    F[1][0] = A21 * dt;
    F[1][1] = 1.0f;

    float tmp[2][2];
    tmp[0][0] = F[0][0] * P[0][0] + F[0][1] * P[1][0];
    tmp[0][1] = F[0][0] * P[0][1] + F[0][1] * P[1][1];
    tmp[1][0] = F[1][0] * P[0][0] + F[1][1] * P[1][0];
    tmp[1][1] = F[1][0] * P[0][1] + F[1][1] * P[1][1];

    P[0][0] = tmp[0][0] * F[0][0] + tmp[0][1] * F[0][1] + f->cfg.q;
    P[0][1] = tmp[0][0] * F[1][0] + tmp[0][1] * F[1][1];
    P[1][0] = tmp[1][0] * F[0][0] + tmp[1][1] * F[0][1];
    P[1][1] = tmp[1][0] * F[1][0] + tmp[1][1] * F[1][1] + f->cfg.q;

    /* UPDATE ----------------------------------------------------------- */
    const float accel_roll = atan2f(ay, az);
    const float accel_pitch = atan2f(-ax, sqrtf(ay * ay + az * az));

    float R_eff = f->cfg.r;
    bool gated = false;
    if (f->cfg.gate_enable) {
        const float norm = sqrtf(ax * ax + ay * ay + az * az);
        if (fabsf(norm - f->cfg.gravity_ms2) > f->cfg.gate_band_ms2) {
            R_eff = f->cfg.r * f->cfg.gate_r_scale;
            gated = true;
        }
    }

    const float y0 = accel_roll - x0;
    const float y1 = accel_pitch - x1;

    float S[2][2];
    S[0][0] = P[0][0] + R_eff;
    S[0][1] = P[0][1];
    S[1][0] = P[1][0];
    S[1][1] = P[1][1] + R_eff;

    const float det_S = S[0][0] * S[1][1] - S[0][1] * S[1][0];
    if (!isfinite(det_S) || det_S <= 1e-30f) {
        return EKF_ERR_NUMERIC;
    }
    float inv_S[2][2];
    inv_S[0][0] = S[1][1] / det_S;
    inv_S[0][1] = -S[0][1] / det_S;
    inv_S[1][0] = -S[1][0] / det_S;
    inv_S[1][1] = S[0][0] / det_S;

    float K[2][2];
    K[0][0] = P[0][0] * inv_S[0][0] + P[0][1] * inv_S[1][0];
    K[0][1] = P[0][0] * inv_S[0][1] + P[0][1] * inv_S[1][1];
    K[1][0] = P[1][0] * inv_S[0][0] + P[1][1] * inv_S[1][0];
    K[1][1] = P[1][0] * inv_S[0][1] + P[1][1] * inv_S[1][1];

    x0 += K[0][0] * y0 + K[0][1] * y1;
    x1 += K[1][0] * y0 + K[1][1] * y1;

    float Pn[2][2];
    Pn[0][0] = (1.0f - K[0][0]) * P[0][0] - K[0][1] * P[1][0];
    Pn[0][1] = (1.0f - K[0][0]) * P[0][1] - K[0][1] * P[1][1];
    Pn[1][0] = -K[1][0] * P[0][0] + (1.0f - K[1][1]) * P[1][0];
    Pn[1][1] = -K[1][0] * P[0][1] + (1.0f - K[1][1]) * P[1][1];

    /* Symmetrise: (I-KH)P drifts away from symmetry in float32. */
    const float off = 0.5f * (Pn[0][1] + Pn[1][0]);
    Pn[0][1] = off;
    Pn[1][0] = off;

    if (x1 > f->cfg.max_pitch_rad) {
        x1 = f->cfg.max_pitch_rad;
    } else if (x1 < -f->cfg.max_pitch_rad) {
        x1 = -f->cfg.max_pitch_rad;
    }

    if (!isfinite(x0) || !isfinite(x1) || !isfinite(Pn[0][0]) || !isfinite(Pn[1][1]) ||
        !isfinite(off) || Pn[0][0] < 0.0f || Pn[1][1] < 0.0f) {
        return EKF_ERR_NUMERIC;
    }

    f->x[0] = x0;
    f->x[1] = x1;
    memcpy(f->P, Pn, sizeof(Pn));
    if (gated) {
        f->gated_count++;
    }
    out->roll = x0 * RAD_TO_DEG;
    out->pitch = x1 * RAD_TO_DEG;
    return EKF_OK;
}
