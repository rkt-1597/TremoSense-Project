#ifndef PWM_H
#define PWM_H

#include <zephyr/drivers/pwm.h>

extern const struct pwm_dt_spec roll;
extern const struct pwm_dt_spec pitch;

#define PWM_SLEEP_MS 1000      // 100 ms sleep time between consecutive readings

int set_servo_angle(const struct pwm_dt_spec *pwm_dev, uint8_t angle_deg);

int servo_sweep(const struct pwm_dt_spec *pwm_dev);

#endif /* PWM_H */