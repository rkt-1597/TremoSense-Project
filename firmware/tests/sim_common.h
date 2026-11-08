#ifndef SIM_COMMON_H
#define SIM_COMMON_H
/* Synthetic IMU generator for host tests (ideal sensor, optional noise).
 * Aerospace convention matching the EKF: a_body = (-g sin th, g cos th sin ph,
 * g cos th cos ph); gyro from Euler rates with zero yaw rate. */
#include <math.h>
#include "test_util.h"
#include "ekf.h"

typedef struct {
    float a[3];
    float g[3];
    float roll_deg, pitch_deg;
} simsample_t;

static inline simsample_t sim_tremor(double t, double f_hz, double amp_deg, double noise_a,
                                     double noise_g) {
    const double w = 2.0 * M_PI * f_hz, d2r = M_PI / 180.0, G = 9.80665;
    double ph = amp_deg * d2r * sin(w * t);
    double th = 0.6 * amp_deg * d2r * sin(w * t + 1.0);
    double phd = amp_deg * d2r * w * cos(w * t);
    double thd = 0.6 * amp_deg * d2r * w * cos(w * t + 1.0);
    simsample_t s;
    s.a[0] = (float)(-G * sin(th) + noise_a * rng_normal());
    s.a[1] = (float)(G * cos(th) * sin(ph) + noise_a * rng_normal());
    s.a[2] = (float)(G * cos(th) * cos(ph) + noise_a * rng_normal());
    s.g[0] = (float)(phd + noise_g * rng_normal());
    s.g[1] = (float)(thd * cos(ph) + noise_g * rng_normal());
    s.g[2] = (float)(-thd * sin(ph) + noise_g * rng_normal());
    s.roll_deg = (float)(ph / d2r);
    s.pitch_deg = (float)(th / d2r);
    return s;
}

/* TEST-ONLY tuning (not the device's): used to exercise the code paths. */
#define TEST_Q 1e-8f
#define TEST_R 1e-3f
static inline ekf_config_t test_ekf_cfg(void) {
    ekf_config_t c = {TEST_Q, TEST_R, 1.3962634f, 0.02f, false, 3.0f, 100.0f, 9.80665f};
    return c;
}
#endif
