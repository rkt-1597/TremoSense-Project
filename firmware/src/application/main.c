#include "app.h"
#include "constants.h"
#include "imu.h"
#include "pwm.h"
#include "watchdog.h"

#include <zephyr/logging/log.h>

LOG_MODULE_REGISTER(main, LOG_LEVEL_INF);

static struct k_thread control_thread_data;
static struct k_thread pwm_thread_data;
K_THREAD_STACK_DEFINE(control_thread_stack, CONTROL_THREAD_STACK_SIZE_BYTES);
K_THREAD_STACK_DEFINE(pwm_thread_stack, PWM_TASK_STACK_SIZE_BYTES);

static control_t control;

int main(void)
{
	const struct device *const imu_dev = DEVICE_DT_GET_ONE(st_lsm6dsl);
	control_config_t cfg;
	int err;

	/* 1. Actuation first: the guard levels the spoon immediately and holds
	 *    neutral until actuation_enable(true). */
	k_thread_create(&pwm_thread_data, pwm_thread_stack,
			K_THREAD_STACK_SIZEOF(pwm_thread_stack),
			pwm_thread_function, NULL, NULL, NULL,
			K_PRIO_PREEMPT(5), 0, K_NO_WAIT);

	/* 2. Watchdog in boot phase. */
	(void)watchdog_start();

	/* 3. Configuration check: refuse to actuate with invalid tuning. */
	control_default_config(&cfg);
	const int cfg_err = control_init(&control, &cfg);
	if (cfg_err != 0) {
		LOG_ERR("INVALID TUNING (Q/R/K/MAX_PITCH in constants.h): refusing to actuate; servos held at neutral");
	}

	/* 4. IMU. */
	err = imu_driver_init(imu_dev);
	if (err) {
		LOG_ERR("Failed to initialize IMU: %d. Servos held at neutral; the watchdog will reset and retry", err);
		return err;
	}

	/* 5. Calibration. */
	const int cal_err = calibrate_imu(&control);
	if (cal_err != 0) {
		control_fail_calibration(&control);
		LOG_ERR("IMU calibration failed %d times: servos held at neutral", CAL_MAX_ATTEMPTS);
	}

	/* 6. Control loop. */
	k_thread_create(&control_thread_data, control_thread_stack,
			K_THREAD_STACK_SIZEOF(control_thread_stack),
			control_thread_function, &control, NULL, NULL,
			K_PRIO_PREEMPT(1), 0, K_NO_WAIT);

	if (cfg_err == 0 && cal_err == 0) {
		actuation_enable(true);
	}
	watchdog_arm_runtime();
	return 0;
}
