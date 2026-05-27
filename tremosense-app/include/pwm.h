#ifndef PWM_H
#define PWM_H

#include "lqr.h"

#include <zephyr/kernel.h>
#include <zephyr/drivers/pwm.h>
#include <zephyr/logging/log.h>

#include "lqr.h"

extern const struct pwm_dt_spec roll;
extern const struct pwm_dt_spec pitch;

extern float target_servo_roll_deg, target_servo_pitch_deg;

#define PWM_TASK_STACK_SIZE_BYTES 1024

#define PWM_SLEEP_MS 10 

extern k_tid_t pwm_tid;

int servos_reset(void);

int set_servo_angle(const struct pwm_dt_spec *pwm_dev_roll, 
                   const struct pwm_dt_spec *pwm_dev_pitch,
                   lqr_result_t *result);

int servo_sweep(const struct pwm_dt_spec *pwm_dev);

void pwm_thread_function(void *arg1, void *arg2, void *arg3);

#endif /* PWM_H */