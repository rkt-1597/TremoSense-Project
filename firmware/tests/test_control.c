/* Integration tests: sensing -> estimation -> control -> actuator guard.
 * SIMULATION ONLY: synthetic sensor data, TEST-ONLY gains. No plant model. */
#include "control.h"
#include "sim_common.h"
#include <string.h>

static control_config_t test_cfg(void) {
    control_config_t c;
    control_default_config(&c);
    c.ekf = test_ekf_cfg();
    const lqr_gain_t K = {{{1.2f, 0.05f, 0.0f, 0.0f}, {0.0f, 0.0f, 1.1f, 0.04f}}};
    c.K = K;
    return c;
}
static const guard_config_t GCFG = {90.0f, 0.0f, 180.0f, 0.0f, 60.0f, 100.0f, 208};

int main(void) {
    const float dt = 1.0f / 208;
    float z3[3] = {0, 0, 0};

    /* 1. The shipped placeholder constants are refused: never valid, servos stay neutral. */
    control_config_t def;
    control_default_config(&def);
    control_t c;
    CHECK(control_init(&c, &def) != 0);
    guard_t gd;
    guard_init(&gd, &GCFG);
    guard_enable(&gd, true);
    float a0[3] = {0, 0, 9.80665f};
    for (int i = 0; i < 2000; i++) {
        servo_cmd_t s = control_step(&c, a0, z3, dt);
        CHECK(!s.valid);
        guard_out_t o = guard_step(&gd, dt, s.valid, s.roll_deg, s.pitch_deg);
        CHECK(isfinite(o.roll_deg) && isfinite(o.pitch_deg));
        if (i > 60)
            CHECK(o.state == GUARD_SAFE_NEUTRAL);
    }
    CHECK(gd.out[0] == 90.0f && gd.out[1] == 90.0f);

    /* 2. Nominal run: noisy 5 Hz tremor, all outputs finite and inside servo range. */
    control_config_t cfg = test_cfg();
    CHECK(control_init(&c, &cfg) == 0);
    guard_init(&gd, &GCFG);
    guard_enable(&gd, true);
    rng_seed(2024);
    int valid = 0, n = 3 * 208 * 5;
    double se = 0;
    int ne = 0;
    for (int i = 0; i < n; i++) {
        simsample_t s = sim_tremor(i * (double)dt, 5.0, 5.0, 0.01, 0.002);
        servo_cmd_t k = control_step(&c, s.a, s.g, dt);
        guard_out_t o = guard_step(&gd, dt, k.valid, k.roll_deg, k.pitch_deg);
        valid += k.valid;
        CHECK(isfinite(o.roll_deg) && o.roll_deg >= 0.0f && o.roll_deg <= 180.0f);
        CHECK(isfinite(o.pitch_deg) && o.pitch_deg >= 0.0f && o.pitch_deg <= 180.0f);
        if (i > 208) {
            double e = k.est_roll_deg - s.roll_deg;
            se += e * e;
            ne++;
        }
    }
    CHECK(valid == n);
    printf("  nominal 5 Hz/5 deg run: roll estimate RMS error %.3f deg (synthetic, test tuning)\n",
           sqrt(se / ne));
    CHECK(sqrt(se / ne) < 0.5);

    /* 3. Fault injection: IMU produces NaN for 50 ms, then recovers. */
    CHECK(control_init(&c, &cfg) == 0);
    guard_init(&gd, &GCFG);
    guard_enable(&gd, true);
    rng_seed(1);
    guard_state_t seen_hold = GUARD_ACTIVE, st_after = GUARD_ACTIVE;
    int safe_at = -1;
    for (int i = 0; i < 208 * 6; i++) {
        simsample_t s = sim_tremor(i * (double)dt, 5.0, 5.0, 0.01, 0.002);
        if (i >= 400 && i < 400 + 11)
            s.a[0] = NAN; /* 11 bad samples (>10) */
        servo_cmd_t k = control_step(&c, s.a, s.g, dt);
        guard_out_t o = guard_step(&gd, dt, k.valid, k.roll_deg, k.pitch_deg);
        CHECK(isfinite(o.roll_deg));
        if (o.state == GUARD_HOLD)
            seen_hold = GUARD_HOLD;
        if (o.state == GUARD_SAFE_NEUTRAL && safe_at < 0 && i > 400)
            safe_at = i;
        st_after = o.state;
    }
    CHECK(seen_hold == GUARD_HOLD);
    CHECK(safe_at < 0 || safe_at - 400 <= 25);
    CHECK(c.mon.seen_faults & FAULT_IMU_NONFINITE);
    CHECK(st_after == GUARD_ACTIVE); /* auto-recovered after ~1 s of good data */
    printf("  NaN burst -> guard recovered to ACTIVE; safe-neutral reached at step %d (burst began "
           "at 400)\n",
           safe_at);

    /* 4. A single glitch sample is rejected without leaving ACTIVE for long. */
    CHECK(control_init(&c, &cfg) == 0);
    guard_init(&gd, &GCFG);
    guard_enable(&gd, true);
    rng_seed(1);
    int safe_seen = 0;
    for (int i = 0; i < 208 * 3; i++) {
        simsample_t s = sim_tremor(i * (double)dt, 5.0, 5.0, 0.01, 0.002);
        if (i == 300)
            s.g[1] = 1000.0f;
        servo_cmd_t k = control_step(&c, s.a, s.g, dt);
        guard_out_t o = guard_step(&gd, dt, k.valid, k.roll_deg, k.pitch_deg);
        if (o.state == GUARD_SAFE_NEUTRAL)
            safe_seen = 1;
    }
    CHECK(!safe_seen);

    /* 5. Sensor timeout (no samples): guard reaches safe neutral within hold + one tick. */
    CHECK(control_init(&c, &cfg) == 0);
    guard_init(&gd, &GCFG);
    guard_enable(&gd, true);
    rng_seed(1);
    for (int i = 0; i < 300; i++) {
        simsample_t s = sim_tremor(i * (double)dt, 5.0, 5.0, 0.01, 0.002);
        servo_cmd_t k = control_step(&c, s.a, s.g, dt);
        guard_step(&gd, dt, k.valid, k.roll_deg, k.pitch_deg);
    }
    int t_safe = 0;
    guard_out_t o;
    for (; t_safe < 500; t_safe++) {
        servo_cmd_t k = control_timeout(&c);
        CHECK(!k.valid);
        o = guard_step(&gd, 0.050f, k.valid, k.roll_deg, k.pitch_deg);
        if (o.state == GUARD_SAFE_NEUTRAL)
            break;
    }
    CHECK(o.state == GUARD_SAFE_NEUTRAL);
    CHECK(t_safe <= 3);

    /* 6. Frozen (stuck) IMU is detected. */
    CHECK(control_init(&c, &cfg) == 0);
    guard_init(&gd, &GCFG);
    guard_enable(&gd, true);
    rng_seed(1);
    simsample_t fr = sim_tremor(0.3, 5.0, 5.0, 0.0, 0.0);
    int stuck_fault = 0, safe2 = 0;
    for (int i = 0; i < 400; i++) {
        servo_cmd_t k = control_step(&c, fr.a, fr.g, dt);
        guard_out_t o2 = guard_step(&gd, dt, k.valid, k.roll_deg, k.pitch_deg);
        if (c.mon.seen_faults & FAULT_IMU_STUCK)
            stuck_fault = 1;
        if (o2.state == GUARD_SAFE_NEUTRAL)
            safe2 = 1;
    }
    CHECK(stuck_fault);
    CHECK(safe2);

    /* 7. Calibration failure is latched: never valid again. */
    CHECK(control_init(&c, &cfg) == 0);
    control_fail_calibration(&c);
    rng_seed(1);
    for (int i = 0; i < 1000; i++) {
        simsample_t s = sim_tremor(i * (double)dt, 5.0, 5.0, 0.01, 0.002);
        CHECK(!control_step(&c, s.a, s.g, dt).valid);
    }

    /* 8. Offsets are applied: a constant gyro bias is removed before integration. */
    CHECK(control_init(&c, &cfg) == 0);
    float aoff[3] = {0.1f, -0.05f, 0.2f}, goff[3] = {0.02f, -0.01f, 0.005f};
    control_set_offsets(&c, aoff, goff);
    servo_cmd_t k = {0};
    rng_seed(8);
    for (int i = 0; i < 2000; i++) { /* LSB-level noise: a live sensor is never bit-identical */
        float n = (float)(0.002 * rng_normal());
        float a[3] = {aoff[0] + n, aoff[1], 9.80665f + aoff[2]},
              g[3] = {goff[0], goff[1] + n * 0.1f, goff[2]};
        k = control_step(&c, a, g, dt);
    }
    CHECK(k.valid);
    CHECK_NEAR(k.est_roll_deg, 0.0, 0.05);
    CHECK_NEAR(k.est_pitch_deg, 0.0, 0.05);

    TEST_MAIN_END("test_control");
}
