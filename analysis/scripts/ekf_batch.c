/* Batch runners for the analysis harness: the REAL firmware EKF (updated) and
 * the verbatim legacy EKF (baseline). Built by ekf_comparison.py. */
#include "ekf.h"
#include "reference/ekf_legacy.h"

int run_new(float q, float r, int gate, float band, float scale, int n,
            const float *in, const float *dt, float *out)
{
    ekf_config_t c = { q, r, 1.3962634f, 0.1f, gate != 0, band, scale, 9.80665f };
    ekf_t f; ekf_result_t o = { 0, 0 }; int rejects = 0;
    if (ekf_init(&f, &c) != EKF_OK) return -1;
    for (int i = 0; i < n; i++) {
        const float *s = in + 6 * i;
        if (ekf_update(&f, s[0], s[1], s[2], s[3], s[4], s[5], dt[i], &o) != EKF_OK) rejects++;
        out[2 * i] = o.roll; out[2 * i + 1] = o.pitch;
    }
    return rejects;
}

int run_legacy(float q, float r, int n, const float *in, const float *dt, float *out)
{
    ekf_result_t o = { 0, 0 };
    legacy_ekf_init();
    for (int i = 0; i < n; i++) {
        const float *s = in + 6 * i;
        legacy_ekf_update(s[0], s[1], s[2], s[3], s[4], s[5], dt[i], q, r, &o);
        out[2 * i] = o.roll; out[2 * i + 1] = o.pitch;
    }
    return 0;
}
