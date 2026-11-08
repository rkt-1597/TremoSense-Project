#include "app.h"
#include "constants.h"
#include "imu.h"
#include "pwm.h"
#include "timing.h"
#include "watchdog.h"

#include <zephyr/logging/log.h>

LOG_MODULE_REGISTER(CTRL, LOG_LEVEL_INF);

static void publish(const servo_cmd_t *cmd)
{
	/* Latest-wins: drop any command the actuator has not consumed yet. */
	while (k_msgq_put(&servo_cmd_q, cmd, K_NO_WAIT) != 0) {
		k_msgq_purge(&servo_cmd_q);
	}
}

void control_thread_function(void *arg1, void *arg2, void *arg3)
{
	control_t *ctl = arg1;
	struct imu_sample s;
	uint32_t dropped, prev_cycles = 0U, n = 0U;
	bool have_prev = false;

	ARG_UNUSED(arg2);
	ARG_UNUSED(arg3);

	while (1) {
		servo_cmd_t cmd;

		if (imu_wait_sample(&s, K_MSEC(GUARD_CMD_TIMEOUT_MS), &dropped) != 0) {
			cmd = control_timeout(ctl);
			have_prev = false;
		} else {
			/* dt from the data-ready timestamp: not affected by thread
			 * scheduling jitter and not quantised to 1 ms. */
			float dt = have_prev
				? timing_dt_seconds(prev_cycles, s.cycles, sys_clock_hw_cycles_per_sec())
				: 1.0f / IMU_ODR_HZ;

			prev_cycles = s.cycles;
			have_prev = true;
			cmd = control_step(ctl, s.accel, s.gyro, dt);
		}
		publish(&cmd);
		watchdog_beat_control();

#if CONFIG_TREMOSENSE_TELEMETRY_DECIMATION > 0
		if ((++n % CONFIG_TREMOSENSE_TELEMETRY_DECIMATION) == 0U) {
#if CONFIG_CLEAR_SCREEN
			printk("\033[2J\033[H");
#endif
			LOG_INF("roll %.2f pitch %.2f deg | servo %.1f/%.1f | guard %d faults 0x%x | drop %u fetcherr %u",
				(double)cmd.est_roll_deg, (double)cmd.est_pitch_deg,
				(double)cmd.roll_deg, (double)cmd.pitch_deg,
				actuation_state(), ctl->mon.active_faults,
				imu_total_dropped(), imu_fetch_errors());
		}
#else
		ARG_UNUSED(n);
#endif
	}
}
