#include "safety.h"
#include "sim_common.h"

static const monitor_config_t MCFG = {156.9064f, 34.9066f, 0.0005f, 0.02f, 80.0f, 32, 10, 208};
static const guard_config_t GCFG = {90.0f, 0.0f, 180.0f, 0.0f, 60.0f, 100.0f, 208};

int main(void) {
    monitor_t m;
    float a[3] = {0.1f, 0.2f, 9.8f}, g[3] = {0.01f, 0.0f, 0.0f};
    monitor_init(&m, &MCFG);
    CHECK(monitor_classify_sample(&m, a, g, 0.0048f) == FAULT_NONE);
    float an[3] = {NAN, 0, 9.8f};
    CHECK(monitor_classify_sample(&m, an, g, 0.0048f) & FAULT_IMU_NONFINITE);
    float ar[3] = {0, 200.0f, 9.8f};
    CHECK(monitor_classify_sample(&m, ar, g, 0.0048f) & FAULT_IMU_RANGE);
    float gr[3] = {40.0f, 0, 0};
    CHECK(monitor_classify_sample(&m, a, gr, 0.0048f) & FAULT_IMU_RANGE);
    CHECK(monitor_classify_sample(&m, a, g, 0.0f) & FAULT_IMU_TIMING);
    CHECK(monitor_classify_sample(&m, a, g, 0.5f) & FAULT_IMU_TIMING);
    CHECK(monitor_classify_sample(&m, a, g, NAN) & FAULT_IMU_TIMING);

    /* stuck sensor: identical samples */
    monitor_init(&m, &MCFG);
    uint32_t f = 0;
    int first = -1;
    for (int i = 0; i < 100; i++) {
        f = monitor_classify_sample(&m, a, g, 0.0048f);
        if ((f & FAULT_IMU_STUCK) && first < 0)
            first = i;
    }
    CHECK(first == 32);
    /* a live sensor with LSB noise is never "stuck" */
    monitor_init(&m, &MCFG);
    rng_seed(3);
    int stuck = 0;
    for (int i = 0; i < 5000; i++) {
        float an2[3] = {a[0] + (float)(0.005 * rng_normal()), a[1], a[2]};
        if (monitor_classify_sample(&m, an2, g, 0.0048f) & FAULT_IMU_STUCK)
            stuck++;
    }
    CHECK(stuck == 0);

    /* estimate classification */
    ekf_result_t ok = {5, 5}, big = {85, 0};
    CHECK(monitor_classify_estimate(&m, EKF_OK, &ok) == 0);
    CHECK(monitor_classify_estimate(&m, EKF_OK, &big) & FAULT_EKF_RANGE);
    CHECK(monitor_classify_estimate(&m, EKF_ERR_NUMERIC, &ok) & FAULT_EKF_NUMERIC);

    /* fault assertion needs max_consec_bad, clearing needs recover_good */
    monitor_init(&m, &MCFG);
    for (int i = 0; i < 9; i++)
        CHECK(!monitor_note(&m, FAULT_IMU_RANGE));
    CHECK(m.active_faults == 0);
    CHECK(!monitor_note(&m, FAULT_IMU_RANGE));
    CHECK(m.active_faults & FAULT_IMU_RANGE);
    for (int i = 0; i < 207; i++)
        CHECK(!monitor_note(&m, 0)); /* still asserted */
    CHECK(monitor_note(&m, 0) == true);
    CHECK(m.active_faults == 0);
    /* a single glitch is rejected but never asserted */
    monitor_init(&m, &MCFG);
    CHECK(monitor_note(&m, 0));
    CHECK(!monitor_note(&m, FAULT_IMU_RANGE));
    CHECK(monitor_note(&m, 0));
    CHECK(m.active_faults == 0 && (m.seen_faults & FAULT_IMU_RANGE));
    /* permanent faults are not cleared by good samples */
    monitor_assert_permanent(&m, FAULT_CAL);
    for (int i = 0; i < 1000; i++)
        monitor_note(&m, 0);
    CHECK(m.active_faults & FAULT_CAL);
    CHECK(!monitor_note(&m, 0));

    /* ---------------- actuator guard ---------------- */
    guard_t gd;
    guard_init(&gd, &GCFG);
    const float dt = 1.0f / 208;
    guard_out_t o = guard_step(&gd, dt, true, 120.0f, 60.0f);
    CHECK(o.state == GUARD_SAFE_NEUTRAL && o.roll_deg == 90.0f &&
          o.pitch_deg == 90.0f); /* disabled */
    guard_enable(&gd, true);
    /* ramped start: bounded by safe slew (60 deg/s) */
    o = guard_step(&gd, dt, true, 120.0f, 60.0f);
    CHECK(o.state == GUARD_ACTIVE);
    CHECK(o.roll_deg - 90.0f <= 60.0f * dt + 1e-4);
    for (int i = 0; i < 400; i++)
        o = guard_step(&gd, dt, true, 120.0f, 60.0f);
    CHECK_NEAR(o.roll_deg, 120.0, 1e-3);
    CHECK_NEAR(o.pitch_deg, 60.0, 1e-3);
    CHECK(!gd.ramping);
    /* clamping to servo range */
    o = guard_step(&gd, dt, true, 400.0f, -400.0f);
    CHECK(o.roll_deg == 180.0f && o.pitch_deg == 0.0f);
    /* NaN command: never reaches the output; hold, then neutral */
    float held = o.roll_deg;
    o = guard_step(&gd, dt, true, NAN, 90.0f);
    CHECK(o.state == GUARD_HOLD && o.roll_deg == held);
    int steps_to_safe = 0;
    while (o.state == GUARD_HOLD && steps_to_safe < 1000) {
        o = guard_step(&gd, dt, false, 0, 0);
        steps_to_safe++;
        CHECK(isfinite(o.roll_deg));
    }
    printf("  hold -> safe-neutral after %d steps (%.1f ms)\n", steps_to_safe,
           steps_to_safe * dt * 1000);
    CHECK(o.state == GUARD_SAFE_NEUTRAL);
    CHECK(steps_to_safe <= (int)(0.100f / dt) + 3);
    /* return to level is slew-limited and monotonic */
    float prev = o.roll_deg;
    int mono = 1;
    for (int i = 0; i < 2000; i++) {
        o = guard_step(&gd, dt, false, 0, 0);
        if (o.roll_deg > prev + 1e-6)
            mono = 0;
        CHECK(prev - o.roll_deg <= 60.0f * dt + 1e-4);
        prev = o.roll_deg;
    }
    CHECK(mono);
    CHECK_NEAR(o.roll_deg, 90.0, 1e-3);
    /* recovery needs 208 consecutive valid commands */
    for (int i = 0; i < 207; i++) {
        o = guard_step(&gd, dt, true, 100.0f, 100.0f);
        CHECK(o.state == GUARD_SAFE_NEUTRAL);
    }
    o = guard_step(&gd, dt, true, 100.0f, 100.0f);
    CHECK(o.state == GUARD_ACTIVE);
    /* an invalid command in the middle resets the recovery counter */
    guard_init(&gd, &GCFG);
    guard_enable(&gd, true);
    for (int i = 0; i < 40; i++)
        guard_step(&gd, dt, false, 0, 0); /* -> safe neutral */
    CHECK(gd.state == GUARD_SAFE_NEUTRAL);
    for (int i = 0; i < 200; i++)
        guard_step(&gd, dt, true, 95, 95);
    guard_step(&gd, dt, false, 0, 0);
    for (int i = 0; i < 100; i++)
        o = guard_step(&gd, dt, true, 95, 95);
    CHECK(o.state == GUARD_SAFE_NEUTRAL);
    /* slew limit while ACTIVE (when configured) */
    guard_config_t sc = GCFG;
    sc.max_slew_dps = 300.0f;
    guard_init(&gd, &sc);
    guard_enable(&gd, true);
    for (int i = 0; i < 400; i++)
        guard_step(&gd, dt, true, 90, 90);
    prev = 90.0f;
    for (int i = 0; i < 50; i++) {
        o = guard_step(&gd, dt, true, 170, 90);
        CHECK(fabsf(o.roll_deg - prev) <= 300.0f * dt + 1e-3);
        prev = o.roll_deg;
    }
    /* disable returns to neutral */
    guard_enable(&gd, false);
    o = guard_step(&gd, dt, true, 170, 170);
    CHECK(o.state == GUARD_SAFE_NEUTRAL);

    TEST_MAIN_END("test_safety");
}
