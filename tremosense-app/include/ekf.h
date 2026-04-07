#ifndef EKF_H
#define EKF_H

typedef struct {
    float roll; 
    float pitch;
} ekf_result_t;

void ekf_init(void);

void ekf_update(float ax, float ay, float az,
                float gx, float gy, float gz,
                float dt, float Q_val, float R_val,
                ekf_result_t *result);

#endif /* EKF_H */