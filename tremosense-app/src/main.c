#include "imu.h"
#include "pwm.h"
#include "ekf.h"

LOG_MODULE_REGISTER(main, LOG_LEVEL_INF);

static struct k_thread imu_thread_data;
static struct k_thread pwm_thread_data;

k_tid_t imu_tid, pwm_tid;

K_THREAD_STACK_DEFINE(imu_thread_stack, IMU_THREAD_STACK_SIZE_BYTES);
K_THREAD_STACK_DEFINE(pwm_thread_stack, PWM_TASK_STACK_SIZE_BYTES);


int main(void)
{
	int err;

	const struct device *const lsm6ds3_trc_dev = DEVICE_DT_GET_ONE(st_lsm6dsl);
	err = imu_init(lsm6ds3_trc_dev);
	if (err) {
		LOG_ERR("Failed to initialize IMU: %d", err);
		return err;
	}


	ekf_init();	

	imu_tid = k_thread_create(&imu_thread_data, 
				  imu_thread_stack,
				  K_THREAD_STACK_SIZEOF(imu_thread_stack),
				  (k_thread_entry_t)imu_thread_function,
				  NULL, NULL, NULL,
				  K_PRIO_PREEMPT(1), 0, K_NO_WAIT);
	
	pwm_tid = k_thread_create(&pwm_thread_data, 
				  pwm_thread_stack,
				  K_THREAD_STACK_SIZEOF(pwm_thread_stack),
				  (k_thread_entry_t)pwm_thread_function,
				  NULL, NULL, NULL,
				  K_PRIO_PREEMPT(5), 0, K_NO_WAIT);


	return 0;
}
