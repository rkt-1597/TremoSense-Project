#include "pwm.h"

LOG_MODULE_REGISTER(PWM, LOG_LEVEL_INF);

const struct pwm_dt_spec roll = PWM_DT_SPEC_GET(DT_ALIAS(servo_roll));
const struct pwm_dt_spec pitch = PWM_DT_SPEC_GET(DT_ALIAS(servo_pitch));

#define ROLL_SERVO_MIN    PWM_USEC(DT_PROP(DT_ALIAS(servo_roll), min_pulse_us))
#define ROLL_SERVO_MAX    PWM_USEC(DT_PROP(DT_ALIAS(servo_roll), max_pulse_us))
#define ROLL_SERVO_PERIOD (ROLL_SERVO_MAX - ROLL_SERVO_MIN)

#define PITCH_SERVO_MIN    PWM_USEC(DT_PROP(DT_ALIAS(servo_pitch), min_pulse_us))
#define PITCH_SERVO_MAX    PWM_USEC(DT_PROP(DT_ALIAS(servo_pitch), max_pulse_us))
#define PITCH_SERVO_PERIOD (PITCH_SERVO_MAX - PITCH_SERVO_MIN)

int set_servo_angle(const struct pwm_dt_spec *pwm_dev, uint8_t angle_deg)
{
	uint32_t pulse = 0;
	
	if (angle_deg > 180) 
		angle_deg = 180;

	if (pwm_dev == &roll)    
		pulse = ROLL_SERVO_MIN + ((ROLL_SERVO_PERIOD * angle_deg) / 180);
	else if (pwm_dev == &pitch)    
		pulse = PITCH_SERVO_MIN + ((PITCH_SERVO_PERIOD * angle_deg) / 180);

    	return pwm_set_pulse_dt(pwm_dev, pulse);
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
	#endif
	}
}