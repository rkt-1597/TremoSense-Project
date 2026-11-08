#include "app.h"
#include "constants.h"
#include "imu.h"
#include "imu_cal.h"
#include "watchdog.h"

#include <zephyr/drivers/pwm.h>
#include <zephyr/logging/log.h>

LOG_MODULE_REGISTER(CAL, LOG_LEVEL_INF);

static const struct pwm_dt_spec imu_calib_led = PWM_DT_SPEC_GET(DT_ALIAS(imu_calib));
#define IMU_CALIB_LED_MIN PWM_USEC(DT_PROP(DT_ALIAS(imu_calib), min_pulse_us))
#define IMU_CALIB_LED_MAX PWM_USEC(DT_PROP(DT_ALIAS(imu_calib), max_pulse_us))

static void blink_ms(uint32_t duration_ms, uint32_t half_period_ms)
{
	uint32_t pulse = IMU_CALIB_LED_MAX;
	uint32_t start = k_uptime_get_32();

	while ((k_uptime_get_32() - start) < duration_ms) {
		pulse = (pulse == IMU_CALIB_LED_MAX) ? IMU_CALIB_LED_MIN : IMU_CALIB_LED_MAX;
		(void)pwm_set_pulse_dt(&imu_calib_led, pulse);
		k_msleep(half_period_ms);
	}
}

static int collect_once(imu_cal_result_t *res)
{
	static const imu_cal_limits_t lim = {
		.gyro_std_max_rads = CAL_GYRO_STD_MAX_RADS,
		.accel_norm_tol_ms2 = CAL_ACCEL_NORM_TOL_MS2,
		.tilt_max_ms2 = CAL_TILT_MAX_MS2,
		.gravity_ms2 = GRAVITY_MS2,
		.min_samples = CAL_SAMPLES,
	};
	imu_cal_acc_t acc;
	struct imu_sample s;
	uint32_t dropped;

	imu_cal_reset(&acc);
	LOG_INF("Hold the board flat and still: calibration starts in 3 s");
	(void)pwm_set_pulse_dt(&imu_calib_led, IMU_CALIB_LED_MAX);
	k_msleep(3000);
	LOG_INF("--- STARTING CALIBRATION ---");

	while (acc.n < CAL_SAMPLES) {
		if (imu_wait_sample(&s, K_MSEC(200), &dropped) != 0) {
			LOG_ERR("calibration: no IMU samples (200 ms timeout)");
			return IMU_CAL_ERR_SAMPLES;
		}
		(void)imu_cal_add(&acc, s.accel, s.gyro);
	}
	return imu_cal_finish(&acc, &lim, res);
}

int calibrate_imu(control_t *ctl)
{
#if CONFIG_IMU_CALIBRATION_WHILE_TESTING
	imu_cal_result_t res;

	for (int attempt = 1; attempt <= CAL_MAX_ATTEMPTS; attempt++) {
		int rc = collect_once(&res);

		if (rc == IMU_CAL_OK) {
			control_set_offsets(ctl, res.accel_offset, res.gyro_offset);
			LOG_INF("Calibration complete (attempt %d). Check offsets (5 s):", attempt);
			LOG_INF("Accel offsets: X: %.3f, Y: %.3f, Z: %.3f",
				(double)res.accel_offset[0], (double)res.accel_offset[1],
				(double)res.accel_offset[2]);
			LOG_INF("Gyro offsets:  X: %.3f, Y: %.3f, Z: %.3f (gyro sd max %.4f rad/s)",
				(double)res.gyro_offset[0], (double)res.gyro_offset[1],
				(double)res.gyro_offset[2], (double)res.gyro_std_max);
			blink_ms(5000, 200);
			return 0;
		}
		LOG_ERR("Calibration attempt %d/%d rejected (code %d): gyro sd %.4f rad/s, |a| %.2f m/s2",
			attempt, CAL_MAX_ATTEMPTS, rc, (double)res.gyro_std_max,
			(double)res.accel_norm_mean);
		blink_ms(2000, 50);
	}
	return -1;
#else
	ARG_UNUSED(ctl);
	LOG_WRN("IMU calibration disabled by configuration: offsets are zero");
	return 0;
#endif
}
