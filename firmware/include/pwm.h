#ifndef PWM_H
#define PWM_H

#include <zephyr/kernel.h>
#include <zephyr/drivers/pwm.h>
#include "control.h"

extern const struct pwm_dt_spec roll;
extern const struct pwm_dt_spec pitch;

#define PWM_TASK_STACK_SIZE_BYTES 2048
#define PWM_SLEEP_MS 10

/* Latest-wins mailbox (depth 1) from the control thread to the actuation
 * thread, so a stalled consumer can never act on stale commands. */
extern struct k_msgq servo_cmd_q;

int servo_apply(float roll_deg, float pitch_deg);
int servos_reset(void);
int servo_sweep(const struct pwm_dt_spec *pwm_dev);

/* Guard control (thread-safe). Until enabled the servos are held at neutral. */
void actuation_enable(bool enable);
int actuation_state(void);   /* guard_state_t */

void pwm_thread_function(void *arg1, void *arg2, void *arg3);

#endif /* PWM_H */
