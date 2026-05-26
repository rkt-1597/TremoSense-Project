#include "ekf.h"
#include <math.h>

static float x[2];      
static float P[2][2];  

ekf_result_t ekf_calculated_results;

void ekf_init(void)
{
    x[0] = 0.0f; x[1] = 0.0f;
    P[0][0] = 0.1f; P[0][1] = 0.0f;
    P[1][0] = 0.0f; P[1][1] = 0.1f;
}

void ekf_update(float ax, float ay, float az,
                float gx, float gy, float gz,
                float dt, float Q_val, float R_val,
                ekf_result_t *result)
{
    float p = gx, q = gy, r = gz;

    float phi   = x[0];
    float theta = x[1];

    float s_phi = sinf(phi);
    float c_phi = cosf(phi);
    float s_the = sinf(theta);
    float c_the = cosf(theta);
    float t_the = s_the / c_the;

    float sec_the = (fabsf(c_the) < 0.01f) ? 100.0f : (1.0f / c_the);

    // PREDICT -----------------------------------------------------------------
    float phi_dot   = p + q * s_phi * t_the + r * c_phi * t_the;
    float theta_dot = q * c_phi - r * s_phi;

    x[0] += phi_dot   * dt;
    x[1] += theta_dot * dt;

    float A11 =  q * c_phi * t_the - r * s_phi * t_the;
    float A12 = (q * s_phi + r * c_phi) * (sec_the * sec_the);
    float A21 = -q * s_phi - r * c_phi;

    float F[2][2];
    F[0][0] = 1.0f + A11 * dt;
    F[0][1] =        A12 * dt;
    F[1][0] =        A21 * dt;
    F[1][1] = 1.0f;             // A22=0

    float tmp[2][2];
    tmp[0][0] = F[0][0]*P[0][0] + F[0][1]*P[1][0];
    tmp[0][1] = F[0][0]*P[0][1] + F[0][1]*P[1][1];
    tmp[1][0] = F[1][0]*P[0][0] + F[1][1]*P[1][0];
    tmp[1][1] = F[1][0]*P[0][1] + F[1][1]*P[1][1];

    P[0][0] = tmp[0][0]*F[0][0] + tmp[0][1]*F[0][1] + Q_val;
    P[0][1] = tmp[0][0]*F[1][0] + tmp[0][1]*F[1][1];
    P[1][0] = tmp[1][0]*F[0][0] + tmp[1][1]*F[0][1];
    P[1][1] = tmp[1][0]*F[1][0] + tmp[1][1]*F[1][1] + Q_val;

    // UPDATE ------------------------------------------------------------------
    float accel_roll  = atan2f(ay, az);
    float accel_pitch = atan2f(-ax, sqrtf(ay*ay + az*az));

    float y0 = accel_roll  - x[0];
    float y1 = accel_pitch - x[1];

    float S[2][2];
    S[0][0] = P[0][0] + R_val;
    S[0][1] = P[0][1];
    S[1][0] = P[1][0];
    S[1][1] = P[1][1] + R_val;

    float det_S = S[0][0]*S[1][1] - S[0][1]*S[1][0];
    float inv_S[2][2];
    inv_S[0][0] =  S[1][1] / det_S;
    inv_S[0][1] = -S[0][1] / det_S;
    inv_S[1][0] = -S[1][0] / det_S;
    inv_S[1][1] =  S[0][0] / det_S;

    float K[2][2];
    K[0][0] = P[0][0]*inv_S[0][0] + P[0][1]*inv_S[1][0];
    K[0][1] = P[0][0]*inv_S[0][1] + P[0][1]*inv_S[1][1];
    K[1][0] = P[1][0]*inv_S[0][0] + P[1][1]*inv_S[1][0];
    K[1][1] = P[1][0]*inv_S[0][1] + P[1][1]*inv_S[1][1];

    x[0] += K[0][0]*y0 + K[0][1]*y1;
    x[1] += K[1][0]*y0 + K[1][1]*y1;

    float IK[2][2];
    IK[0][0] = 1.0f - K[0][0]; IK[0][1] = -K[0][1];
    IK[1][0] = -K[1][0];       IK[1][1] = 1.0f - K[1][1];

    float Pn[2][2];
    Pn[0][0] = IK[0][0]*P[0][0] + IK[0][1]*P[1][0];
    Pn[0][1] = IK[0][0]*P[0][1] + IK[0][1]*P[1][1];
    Pn[1][0] = IK[1][0]*P[0][0] + IK[1][1]*P[1][0];
    Pn[1][1] = IK[1][0]*P[0][1] + IK[1][1]*P[1][1];
    P[0][0]=Pn[0][0]; P[0][1]=Pn[0][1];
    P[1][0]=Pn[1][0]; P[1][1]=Pn[1][1];

    result->roll  = x[0] * RAD_TO_DEG;
    result->pitch = x[1] * RAD_TO_DEG;
}