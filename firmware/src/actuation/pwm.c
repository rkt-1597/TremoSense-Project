#include "pwm.h"
#include "constants.h"
#include "safety.h"
#include "timing.h"
#include "watchdog.h"

#include <math.h>
#include <zephyr/logging/log.h>
#include <zephyr/sys/atomic.h>

LOG_MODULE_REGISTER(PWM, LOG_LEVEL_INF);

K_MSGQ_DEFINE(servo_cmd_q, sizeof(servo_cmd_t), 1, 4);

const struct pwm_dt_spec roll = PWM_DT_SPEC_GET(DT_ALIAS(servo_roll));
const struct pwm_dt_spec pitch = PWM_DT_SPEC_GET(DT_ALIAS(servo_pitch));

#define ROLL_SERVO_MIN    PWM_USEC(DT_PROP(DT_ALIAS(servo_roll), min_pulse_us))
#define ROLL_SERVO_MAX    PWM_USEC(DT_PROP(DT_ALIAS(servo_roll), max_pulse_us))
#define ROLL_SERVO_PERIOD (ROLL_SERVO_MAX - ROLL_SERVO_MIN)

#define PITCH_SERVO_MIN    PWM_USEC(DT_PROP(DT_ALIAS(servo_pitch), min_pulse_us))
#define PITCH_SERVO_MAX    PWM_USEC(DT_PROP(DT_ALIAS(servo_pitch), max_pulse_us))
#define PITCH_SERVO_PERIOD (PITCH_SERVO_MAX - PITCH_SERVO_MIN)

static atomic_t guard_enable_req;
static atomic_t guard_state_pub;

void actuation_enable(bool enable) { atomic_set(&guard_enable_req, enable ? 1 : 0); }
int actuation_state(void) { return (int)atomic_get(&guard_state_pub); }

static uint32_t angle_to_pulse(uint32_t min_ns, uint32_t span_ns, float angle_deg)
{
	if (!isfinite(angle_deg)) {
		angle_deg = SERVO_NEUTRAL_DEG;
	}
	/* Both ends are clamped (the original code only clamped the upper end,
	 * and converted a negative float to uint32_t, which is undefined). */
	if (angle_deg < 0.0f) {
		angle_deg = 0.0f;
	} else if (angle_deg > 180.0f) {
		angle_deg = 180.0f;
	}
	return min_ns + (uint32_t)((float)span_ns * angle_deg / 180.0f);
}

int servo_apply(float roll_deg, float pitch_deg)
{
	int err;

	/* int, not uint32_t: the original stored the (negative) error code in an
	 * unsigned variable, so `err < 0` was never true and PWM errors were lost. */
	err = pwm_set_pulse_dt(&roll, angle_to_pulse(ROLL_SERVO_MIN, ROLL_SERVO_PERIOD, roll_deg));
	if (err < 0) {
		return err;
	}
	err = pwm_set_pulse_dt(&pitch, angle_to_pulse(PITCH_SERVO_MIN, PITCH_SERVO_PERIOD, pitch_deg));
	return err < 0 ? err : 0;
}

int servos_reset(void)
{
	return servo_apply(SERVO_NEUTRAL_DEG, SERVO_NEUTRAL_DEG);
}

int servo_sweep(const struct pwm_dt_spec *pwm_dev)
{
	uint32_t pulse = 0;
	int ret;

	for (uint32_t step = 0; step <= 360; step++) {
		uint32_t angle_deg = (step <= 180) ? step : (360 - step);

		if (pwm_dev == &roll) {
			pulse = angle_to_pulse(ROLL_SERVO_MIN, ROLL_SERVO_PERIOD, (float)angle_deg);
		} else if (pwm_dev == &pitch) {
			pulse = angle_to_pulse(PITCH_SERVO_MIN, PITCH_SERVO_PERIOD, (float)angle_deg);
		}
		ret = pwm_set_pulse_dt(pwm_dev, pulse);
		if (ret != 0) {
			LOG_ERR("Error %d: failed to set pulse for angle %u", ret, angle_deg);
			return ret;
		}
		LOG_INF("Servo Angle set to: %u", angle_deg);
#if CONFIG_PWM_TEST_RB_LED
		k_sleep(K_MSEC(1));
#else
		k_sleep(K_MSEC(20));
#endif
	}
	return 0;
}

void pwm_thread_function(void *arg1, void *arg2, void *arg3)
{
	ARG_UNUSED(arg1);
	ARG_UNUSED(arg2);
	ARG_UNUSED(arg3);

#if CONFIG_PWM_TEST_RB_LED
	int err;

	while (1) {
		if ((err = servo_sweep(&roll)) < 0) {
			LOG_ERR("Error sweeping roll servo: %d", err);
			return;
		}
		k_sleep(K_MSEC(PWM_SLEEP_MS));
		if ((err = servo_sweep(&pitch)) < 0) {
			LOG_ERR("Error sweeping pitch servo: %d", err);
			return;
		}
		k_sleep(K_MSEC(PWM_SLEEP_MS));
	}
#else
	static const guard_config_t gcfg = {
		.neutral_deg = SERVO_NEUTRAL_DEG,
		.min_deg = SERVO_CMD_MIN_DEG,
		.max_deg = SERVO_CMD_MAX_DEG,
		.max_slew_dps = SERVO_MAX_SLEW_DPS,
		.safe_slew_dps = SERVO_SAFE_SLEW_DPS,
		.hold_ms = (float)GUARD_HOLD_MS,
		.recover_good = GUARD_RECOVER_GOOD,
	};
	guard_t guard;
	servo_cmd_t cmd;
	uint32_t prev = k_cycle_get_32();
	int fail_count = 0;

	guard_init(&guard, &gcfg);
	/* Level the spoon immediately at boot, before IMU init and calibration. */
	(void)servos_reset();

	while (1) {
		const int rc = k_msgq_get(&servo_cmd_q, &cmd, K_MSEC(GUARD_CMD_TIMEOUT_MS));
		const uint32_t now = k_cycle_get_32();
		float dt = timing_dt_seconds(prev, now, sys_clock_hw_cycles_per_sec());

		prev = now;
		if (dt > 0.5f) {
			dt = 0.5f;
		}
		guard_enable(&guard, atomic_get(&guard_enable_req) != 0);

		guard_out_t out;
		if (rc == 0) {
			out = guard_step(&guard, dt, cmd.valid, cmd.roll_deg, cmd.pitch_deg);
		} else {
			/* No command within the timeout: control loop stalled. */
			out = guard_step(&guard, dt, false, 0.0f, 0.0f);
		}
		atomic_set(&guard_state_pub, (atomic_val_t)out.state);

		if (servo_apply(out.roll_deg, out.pitch_deg) < 0) {
			if (++fail_count == 1 || fail_count % 200 == 0) {
				LOG_ERR("servo PWM update failed (%d consecutive)", fail_count);
			}
		} else {
			fail_count = 0;
		}
		watchdog_beat_actuator();
	}
#endif
}
