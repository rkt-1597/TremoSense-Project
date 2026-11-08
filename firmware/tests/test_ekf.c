#include "ekf.h"
#include "sim_common.h"
#include "reference/ekf_legacy.h"
#include <string.h>

int main(void) {
    /* 1. config validation: the public-repo placeholder constants are rejected */
    ekf_config_t bad = test_ekf_cfg();
    bad.r = 0.0f;
    CHECK(ekf_config_check(&bad) == EKF_ERR_CONFIG);
    bad = test_ekf_cfg();
    bad.max_pitch_rad = 0.0f;
    CHECK(ekf_config_check(&bad) == EKF_ERR_CONFIG);
    bad = test_ekf_cfg();
    bad.q = -1.0f;
    CHECK(ekf_config_check(&bad) == EKF_ERR_CONFIG);
    bad = test_ekf_cfg();
    bad.max_pitch_rad = 1.6f;
    CHECK(ekf_config_check(&bad) == EKF_ERR_CONFIG);
    bad = test_ekf_cfg();
    bad.q = NAN;
    CHECK(ekf_config_check(&bad) == EKF_ERR_CONFIG);
    ekf_config_t good = test_ekf_cfg();
    CHECK(ekf_config_check(&good) == EKF_OK);

    /* 2. static tilt convergence */
    ekf_t f;
    ekf_result_t out;
    CHECK(ekf_init(&f, &good) == EKF_OK);
    const double G = 9.80665, d2r = M_PI / 180.0;
    float ax = (float)(-G * sin(5 * d2r)), ay = (float)(G * cos(5 * d2r) * sin(10 * d2r)),
          az = (float)(G * cos(5 * d2r) * cos(10 * d2r));
    for (int i = 0; i < 1040; i++)
        CHECK(ekf_update(&f, ax, ay, az, 0, 0, 0, 1.0f / 208, &out) == EKF_OK);
    CHECK_NEAR(out.roll, 10.0, 0.05);
    CHECK_NEAR(out.pitch, 5.0, 0.05);

    /* 3. invalid input leaves state untouched and *out unwritten */
    ekf_t before = f;
    ekf_result_t o2 = {-1234.0f, -1234.0f};
    CHECK(ekf_update(&f, NAN, ay, az, 0, 0, 0, 0.005f, &o2) == EKF_ERR_INPUT);
    CHECK(ekf_update(&f, ax, ay, az, INFINITY, 0, 0, 0.005f, &o2) == EKF_ERR_INPUT);
    CHECK(ekf_update(&f, ax, ay, az, 0, 0, 0, 0.0f, &o2) == EKF_ERR_DT);
    CHECK(ekf_update(&f, ax, ay, az, 0, 0, 0, -0.001f, &o2) == EKF_ERR_DT);
    CHECK(ekf_update(&f, ax, ay, az, 0, 0, 0, 0.5f, &o2) == EKF_ERR_DT);
    CHECK(memcmp(&before, &f, sizeof(f)) == 0);
    CHECK(o2.roll == -1234.0f);

    /* 4. degenerate covariance never yields a non-finite estimate (legacy: NaN) */
    ekf_config_t deg = test_ekf_cfg();
    deg.q = 0.0f;
    deg.r = 1e-20f;
    ekf_init(&f, &deg);
    int numeric = 0;
    for (int i = 0; i < 2000; i++) {
        ekf_status_t st = ekf_update(&f, ax, ay, az, 0, 0, 0, 1.0f / 208, &out);
        if (st == EKF_ERR_NUMERIC) {
            numeric++;
            ekf_reset(&f, ax, ay, az);
        } else
            CHECK(isfinite(out.roll) && isfinite(out.pitch));
        CHECK(isfinite(f.x[0]) && isfinite(f.P[0][0]) && f.P[0][0] >= 0.0f);
    }
    printf("  degenerate-config run: %d numeric rejections handled\n", numeric);

    /* 5. reset seeds from the accelerometer */
    ekf_reset(&f, ax, ay, az);
    CHECK_NEAR(f.x[0] / d2r, 10.0, 0.01);
    CHECK_NEAR(f.x[1] / d2r, 5.0, 0.01);
    ekf_reset(&f, NAN, 0, 0);
    CHECK(f.x[0] == 0.0f && f.x[1] == 0.0f);

    /* 6. baseline equivalence: gate disabled == legacy filter on noisy tremor */
    rng_seed(777);
    ekf_init(&f, &good);
    legacy_ekf_init();
    ekf_result_t lo;
    double maxd = 0.0;
    for (int i = 0; i < 6000; i++) {
        double t = i / 208.0;
        simsample_t s = sim_tremor(t, 5.0, 5.0, 0.01, 0.002);
        legacy_ekf_update(s.a[0], s.a[1], s.a[2], s.g[0], s.g[1], s.g[2], 1.0f / 208, TEST_Q,
                          TEST_R, &lo);
        CHECK(ekf_update(&f, s.a[0], s.a[1], s.a[2], s.g[0], s.g[1], s.g[2], 1.0f / 208, &out) ==
              EKF_OK);
        double d = fmax(fabs(out.roll - lo.roll), fabs(out.pitch - lo.pitch));
        if (d > maxd)
            maxd = d;
    }
    printf("  max |new - legacy| over 6000 samples = %.3e deg\n", maxd);
    CHECK(maxd < 1e-2);

    /* 7. gating reduces error under a transient linear acceleration */
    ekf_config_t gc = test_ekf_cfg();
    gc.gate_enable = true;
    ekf_t fg, fn;
    ekf_init(&fg, &gc);
    ekf_init(&fn, &good);
    double e_g = 0, e_n = 0;
    int n = 0;
    rng_seed(99);
    for (int i = 0; i < 2080; i++) {
        double t = i / 208.0;
        simsample_t s = sim_tremor(t, 4.0, 3.0, 0.01, 0.002);
        if (i > 800 && i < 1000)
            s.a[1] += 12.0f; /* 12 m/s^2 linear-acceleration burst */
        ekf_result_t og, on;
        ekf_update(&fg, s.a[0], s.a[1], s.a[2], s.g[0], s.g[1], s.g[2], 1.0f / 208, &og);
        ekf_update(&fn, s.a[0], s.a[1], s.a[2], s.g[0], s.g[1], s.g[2], 1.0f / 208, &on);
        if (i > 800 && i < 1100) {
            e_g += fabs(og.roll - s.roll_deg);
            e_n += fabs(on.roll - s.roll_deg);
            n++;
        }
    }
    printf("  burst window mean |roll err|: gated %.3f deg, ungated %.3f deg\n", e_g / n, e_n / n);
    CHECK(e_g < e_n);
    CHECK(fg.gated_count > 0);

    /* 8. DEFECT EVIDENCE: the legacy filter with the shipped placeholder constants
     *    (Q = R = 0) produces NaN within a few updates. */
    legacy_ekf_init();
    ekf_result_t ln = {0, 0};
    for (int i = 0; i < 5; i++)
        legacy_ekf_update(ax, ay, az, 0, 0, 0, 1.0f / 208, 0.0f, 0.0f, &ln);
    printf("  legacy EKF, Q=R=0, after 5 updates: roll=%f pitch=%f\n", (double)ln.roll,
           (double)ln.pitch);
    CHECK(!isfinite(ln.roll));

    TEST_MAIN_END("test_ekf");
}
