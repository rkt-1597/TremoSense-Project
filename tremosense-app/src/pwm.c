#include "pwm.h"

LOG_MODULE_REGISTER(PWM, LOG_LEVEL_INF);

lqr_result_t lqr_val_to_servos;

const struct pwm_dt_spec roll = PWM_DT_SPEC_GET(DT_ALIAS(servo_roll));
const struct pwm_dt_spec pitch = PWM_DT_SPEC_GET(DT_ALIAS(servo_pitch));

#define ROLL_SERVO_MIN    PWM_USEC(DT_PROP(DT_ALIAS(servo_roll), min_pulse_us))
#define ROLL_SERVO_MAX    PWM_USEC(DT_PROP(DT_ALIAS(servo_roll), max_pulse_us))
#define ROLL_SERVO_PERIOD (ROLL_SERVO_MAX - ROLL_SERVO_MIN)

#define PITCH_SERVO_MIN    PWM_USEC(DT_PROP(DT_ALIAS(servo_pitch), min_pulse_us))
#define PITCH_SERVO_MAX    PWM_USEC(DT_PROP(DT_ALIAS(servo_pitch), max_pulse_us))
#define PITCH_SERVO_PERIOD (PITCH_SERVO_MAX - PITCH_SERVO_MIN)

int set_servo_angle(const struct pwm_dt_spec *pwm_dev_roll, 
                   const struct pwm_dt_spec *pwm_dev_pitch,
                   lqr_result_t *result)
{
	uint32_t err, pulse_roll = 0, pulse_pitch = 0;
	
	if (result->roll_to_servo > 180) 
		result->roll_to_servo = 180;
	if (result->pitch_to_servo > 180) 
		result->pitch_to_servo = 180;

	pulse_roll = ROLL_SERVO_MIN + ((ROLL_SERVO_PERIOD * result->roll_to_servo) / 180);
	if ((err = pwm_set_pulse_dt(pwm_dev_roll, pulse_roll)) < 0)
		return err;
	
	pulse_pitch = PITCH_SERVO_MIN + ((PITCH_SERVO_PERIOD * result->pitch_to_servo) / 180);
	if ((err = pwm_set_pulse_dt(pwm_dev_pitch, pulse_pitch)) < 0)
		return err;

    	return 0;
}

int servos_reset(void)
{
	uint32_t angle_roll = 90, angle_pitch = 90;
	uint32_t pulse_roll, pulse_pitch, err;

	pulse_roll = ROLL_SERVO_MIN + ((ROLL_SERVO_PERIOD * angle_roll) / 180);
	if ((err = pwm_set_pulse_dt(&roll, pulse_roll)) < 0)
		return err;
	
	pulse_pitch = PITCH_SERVO_MIN + ((PITCH_SERVO_PERIOD * angle_pitch) / 180);
	if ((err = pwm_set_pulse_dt(&pitch, pulse_pitch)) < 0)
		return err;

    	return 0;
}

int servo_sweep(const struct pwm_dt_spec *pwm_dev)
{
	uint32_t pulse = 0, ret = 0;

	for (uint32_t step = 0; step <= 360; step++) {
		uint32_t angle_deg = (step <= 180) ? step : (360 - step);
		if (pwm_dev == &roll)    
			pulse = ROLL_SERVO_MIN + ((ROLL_SERVO_PERIOD * angle_deg) / 180);
		else if (pwm_dev == &pitch)    
			pulse = PITCH_SERVO_MIN + ((PITCH_SERVO_PERIOD * angle_deg) / 180);

    		ret = pwm_set_pulse_dt(pwm_dev, pulse);
		if (ret != 0) {
			LOG_ERR("Error %d: failed to set pulse for angle %d\n", ret, angle_deg);
			return ret;
		}
		LOG_INF("Servo Angle set to: %d\n", angle_deg);
		#if CONFIG_PWM_TEST_RB_LED
			k_sleep(K_MSEC(1));
		#else
			k_sleep(K_MSEC(20));
		#endif
	}
	return 0;
}

void pwm_thread_function(void *arg1, void *arg2, void *arg3) {
	while(1) {
	#if CONFIG_PWM_TEST_RB_LED
		int err;
		if ((err = servo_sweep(&roll)) < 0) {
			LOG_ERR("Error sweeping roll servo: %d", err);
			k_thread_abort(pwm_tid);
		}

		k_sleep(K_MSEC(PWM_SLEEP_MS));

		if ((err = servo_sweep(&pitch)) < 0) {
			LOG_ERR("Error sweeping pitch servo: %d", err);
			k_thread_abort(pwm_tid);
		}

		k_sleep(K_MSEC(PWM_SLEEP_MS));
	#else
		k_msgq_get(&lqr_res, &lqr_val_to_servos, K_FOREVER);
		set_servo_angle(&roll, &pitch, &lqr_val_to_servos);

	#endif

	}
}