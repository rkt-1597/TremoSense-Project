#include "lqr.h"
#include "timing.h"
#include "imu_cal.h"
#include "sim_common.h"

int main(void) {
    /* LQR: equals the original closed-form expression, sign convention preserved */
    const lqr_gain_t Kg = {{{1.5f, 0.2f, -0.3f, 0.1f}, {0.4f, -0.1f, 2.0f, 0.3f}}};
    const float(*K)[4] = (const float(*)[4])Kg.k;
    rng_seed(5);
    for (int i = 0; i < 500; i++) {
        float x[4] = {(float)(rng_normal() * 0.1), (float)(rng_normal() * 3),
                      (float)(rng_normal() * 0.1), (float)(rng_normal() * 3)};
        float ur = -(K[0][0] * x[0] + K[0][1] * x[1] + K[0][2] * x[2] + K[0][3] * x[3]);
        float up = -(K[1][0] * x[0] + K[1][1] * x[1] + K[1][2] * x[2] + K[1][3] * x[3]);
        lqr_result_t r;
        lqr_compute(&Kg, x[0], x[1], x[2], x[3], 90.0f, &r);
        CHECK_NEAR(r.roll_to_servo, -(ur * RAD_TO_DEG) + 90.0f, 1e-3);
        CHECK_NEAR(r.pitch_to_servo, (up * RAD_TO_DEG) + 90.0f, 1e-3);
    }
    const lqr_gain_t Z = {{{0}}};
    lqr_result_t z;
    lqr_compute(&Z, 0.3f, 1.0f, 0.2f, 1.0f, 90.0f, &z);
    CHECK(z.roll_to_servo == 90.0f && z.pitch_to_servo == 90.0f);

    /* timing: wrap-safe, sub-millisecond resolution */
    CHECK_NEAR(timing_dt_seconds(0xFFFFFF00u, 0x000000FFu, 64000000u), 511.0 / 64e6, 1e-9);
    CHECK_NEAR(timing_dt_seconds(1000u, 1000u + 307692u, 64000000u), 0.0048077, 1e-6);
    CHECK(timing_dt_seconds(1u, 2u, 0u) == 0.0f);
    /* the 1 ms-quantised legacy measurement of a 4.808 ms period errs by up to ~20 % */
    CHECK(fabs(0.004 - 1.0 / 208) / (1.0 / 208) > 0.15);

    /* calibration */
    imu_cal_limits_t lim = {0.02f, 0.5f, 1.5f, 9.80665f, 100u};
    imu_cal_acc_t acc;
    imu_cal_result_t res;
    rng_seed(11);
    imu_cal_reset(&acc);
    for (int i = 0; i < 624; i++) {
        float a[3] = {0.12f + (float)(0.01 * rng_normal()), -0.08f + (float)(0.01 * rng_normal()),
                      9.80665f + 0.20f + (float)(0.01 * rng_normal())};
        float g[3] = {0.004f + (float)(0.001 * rng_normal()),
                      -0.002f + (float)(0.001 * rng_normal()),
                      0.001f + (float)(0.001 * rng_normal())};
        CHECK(imu_cal_add(&acc, a, g) == 0);
    }
    CHECK(imu_cal_finish(&acc, &lim, &res) == IMU_CAL_OK);
    CHECK_NEAR(res.accel_offset[0], 0.12, 0.005);
    CHECK_NEAR(res.accel_offset[1], -0.08, 0.005);
    CHECK_NEAR(res.accel_offset[2], 0.20, 0.005);
    CHECK_NEAR(res.gyro_offset[0], 0.004, 2e-4);
    {
        float nan3[3] = {NAN, 0, 9.8f}, z3[3] = {0, 0, 0};
        unsigned n0 = acc.n;
        CHECK(imu_cal_add(&acc, nan3, z3) == -1);
        CHECK(acc.n == n0);
    }
    /* moving board */
    imu_cal_reset(&acc);
    for (int i = 0; i < 624; i++) {
        float a[3] = {0, 0, 9.80665f}, g[3] = {0.3f * (float)sin(i * 0.2), 0, 0};
        imu_cal_add(&acc, a, g);
    }
    CHECK(imu_cal_finish(&acc, &lim, &res) == IMU_CAL_ERR_MOTION);
    /* tilted board (would absorb gravity into the bias) */
    imu_cal_reset(&acc);
    for (int i = 0; i < 624; i++) {
        float a[3] = {3.0f, 0, 9.337f}, g[3] = {0, 0, 0};
        imu_cal_add(&acc, a, g);
    }
    CHECK(imu_cal_finish(&acc, &lim, &res) == IMU_CAL_ERR_ORIENTATION);
    /* free fall / wrong magnitude */
    imu_cal_reset(&acc);
    for (int i = 0; i < 624; i++) {
        float a[3] = {0, 0, 3.0f}, g[3] = {0, 0, 0};
        imu_cal_add(&acc, a, g);
    }
    CHECK(imu_cal_finish(&acc, &lim, &res) == IMU_CAL_ERR_ORIENTATION);
    /* too few samples */
    imu_cal_reset(&acc);
    for (int i = 0; i < 10; i++) {
        float a[3] = {0, 0, 9.80665f}, g[3] = {0, 0, 0};
        imu_cal_add(&acc, a, g);
    }
    CHECK(imu_cal_finish(&acc, &lim, &res) == IMU_CAL_ERR_SAMPLES);

    TEST_MAIN_END("test_lqr_timing_cal");
}
