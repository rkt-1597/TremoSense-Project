#include "safety.h"

#include <math.h>
#include <string.h>

/* ======================= monitor ======================= */

void monitor_init(monitor_t *m, const monitor_config_t *cfg) {
    memset(m, 0, sizeof(*m));
    m->cfg = *cfg;
}

uint32_t monitor_classify_sample(monitor_t *m, const float accel[3], const float gyro[3],
                                 float dt) {
    uint32_t f = FAULT_NONE;
    const float v[6] = {accel[0], accel[1], accel[2], gyro[0], gyro[1], gyro[2]};

    for (int i = 0; i < 6; i++) {
        if (!isfinite(v[i])) {
            f |= FAULT_IMU_NONFINITE;
        }
    }
    if (!isfinite(dt) || dt < m->cfg.dt_min_s || dt > m->cfg.dt_max_s) {
        f |= FAULT_IMU_TIMING;
    }
    if (f & FAULT_IMU_NONFINITE) {
        return f;
    }
    for (int i = 0; i < 3; i++) {
        if (fabsf(v[i]) > m->cfg.accel_max_ms2) {
            f |= FAULT_IMU_RANGE;
        }
        if (fabsf(v[3 + i]) > m->cfg.gyro_max_rads) {
            f |= FAULT_IMU_RANGE;
        }
    }

    /* Stuck detection: bit-identical raw readings across all six channels.
     * A live MEMS sensor always shows LSB-level noise, so a long identical
     * run indicates a frozen bus/driver. */
    if (m->cfg.stuck_samples > 0U) {
        if (m->have_last && memcmp(v, m->last_raw, sizeof(v)) == 0) {
            if (m->stuck_run < UINT16_MAX) {
                m->stuck_run++;
            }
        } else {
            m->stuck_run = 0U;
        }
        memcpy(m->last_raw, v, sizeof(v));
        m->have_last = true;
        if (m->stuck_run >= m->cfg.stuck_samples) {
            f |= FAULT_IMU_STUCK;
        }
    }
    return f;
}

uint32_t monitor_classify_estimate(const monitor_t *m, ekf_status_t st, const ekf_result_t *est) {
    uint32_t f = FAULT_NONE;

    if (st == EKF_ERR_NUMERIC) {
        f |= FAULT_EKF_NUMERIC;
    } else if (st == EKF_ERR_INPUT) {
        f |= FAULT_IMU_NONFINITE;
    } else if (st == EKF_ERR_DT) {
        f |= FAULT_IMU_TIMING;
    } else if (st != EKF_OK) {
        f |= FAULT_CONFIG;
    } else if (est != NULL && (fabsf(est->roll) > m->cfg.angle_limit_deg ||
                               fabsf(est->pitch) > m->cfg.angle_limit_deg)) {
        f |= FAULT_EKF_RANGE;
    }
    return f;
}

bool monitor_note(monitor_t *m, uint32_t flags) {
    if (flags & FAULT_PERMANENT) {
        monitor_assert_permanent(m, flags & FAULT_PERMANENT);
    }
    flags &= ~FAULT_PERMANENT;

    if (flags != 0U) {
        m->consec_good = 0U;
        if (m->consec_bad < UINT16_MAX) {
            m->consec_bad++;
        }
        m->bad_total++;
        m->seen_faults |= flags;
        if (m->consec_bad >= m->cfg.max_consec_bad) {
            m->active_faults |= flags;
        }
    } else {
        m->consec_bad = 0U;
        if (m->consec_good < UINT16_MAX) {
            m->consec_good++;
        }
        if ((m->active_faults & ~FAULT_PERMANENT) != 0U && m->consec_good >= m->cfg.recover_good) {
            m->active_faults &= FAULT_PERMANENT;
        }
    }
    return (flags == 0U) && (m->active_faults == 0U);
}

void monitor_assert_permanent(monitor_t *m, uint32_t flags) {
    m->active_faults |= (flags & FAULT_PERMANENT);
    m->seen_faults |= (flags & FAULT_PERMANENT);
}

/* ======================= actuator guard ======================= */

static float clampf(float v, float lo, float hi) {
    return (v < lo) ? lo : ((v > hi) ? hi : v);
}

void guard_init(guard_t *g, const guard_config_t *cfg) {
    memset(g, 0, sizeof(*g));
    g->cfg = *cfg;
    g->state = GUARD_SAFE_NEUTRAL;
    g->out[0] = cfg->neutral_deg;
    g->out[1] = cfg->neutral_deg;
}

void guard_enable(guard_t *g, bool enable) {
    if (enable && !g->enabled) {
        g->enabled = true;
        g->state = GUARD_ACTIVE;
        g->ramping = true;
        g->good = g->cfg.recover_good;
        g->hold_elapsed_ms = 0.0f;
    } else if (!enable) {
        g->enabled = false;
        g->state = GUARD_SAFE_NEUTRAL;
        g->good = 0U;
    }
}

static float slew_toward(float cur, float target, float rate_dps, float dt_s) {
    if (!(rate_dps > 0.0f) || !(dt_s > 0.0f)) {
        return target;
    }
    const float step = rate_dps * dt_s;
    const float d = target - cur;
    if (d > step) {
        return cur + step;
    }
    if (d < -step) {
        return cur - step;
    }
    return target;
}

guard_out_t guard_step(guard_t *g, float dt_s, bool valid, float roll_cmd_deg,
                       float pitch_cmd_deg) {
    const guard_config_t *c = &g->cfg;
    float tgt[2] = {c->neutral_deg, c->neutral_deg};
    float rate = c->safe_slew_dps;
    const bool cmd_ok = valid && isfinite(roll_cmd_deg) && isfinite(pitch_cmd_deg);
    const float dt = (isfinite(dt_s) && dt_s > 0.0f) ? dt_s : 0.0f;

    if (!g->enabled) {
        g->state = GUARD_SAFE_NEUTRAL;
        g->good = 0U;
    } else if (cmd_ok) {
        if (g->good < UINT16_MAX) {
            g->good++;
        }
        g->hold_elapsed_ms = 0.0f;
        if (g->state == GUARD_SAFE_NEUTRAL && g->good >= c->recover_good) {
            g->state = GUARD_ACTIVE;
            g->ramping = true;
        } else if (g->state == GUARD_HOLD) {
            g->state = GUARD_ACTIVE;
            g->ramping = true;
        }
    } else {
        g->good = 0U;
        if (g->state == GUARD_ACTIVE) {
            g->state = GUARD_HOLD;
            g->hold_elapsed_ms = 0.0f;
        }
        if (g->state == GUARD_HOLD) {
            g->hold_elapsed_ms += dt * 1000.0f;
            if (g->hold_elapsed_ms > c->hold_ms) {
                g->state = GUARD_SAFE_NEUTRAL;
            }
        }
    }

    switch (g->state) {
    case GUARD_ACTIVE:
        tgt[0] = clampf(roll_cmd_deg, c->min_deg, c->max_deg);
        tgt[1] = clampf(pitch_cmd_deg, c->min_deg, c->max_deg);
        rate = g->ramping ? c->safe_slew_dps : c->max_slew_dps;
        break;
    case GUARD_HOLD:
        tgt[0] = g->out[0];
        tgt[1] = g->out[1];
        break;
    case GUARD_SAFE_NEUTRAL:
    default:
        break;
    }

    g->out[0] = slew_toward(g->out[0], tgt[0], rate, dt);
    g->out[1] = slew_toward(g->out[1], tgt[1], rate, dt);

    if (g->ramping && g->state == GUARD_ACTIVE && fabsf(g->out[0] - tgt[0]) < 0.5f &&
        fabsf(g->out[1] - tgt[1]) < 0.5f) {
        g->ramping = false;
    }

    guard_out_t o = {g->out[0], g->out[1], g->state};
    return o;
}
