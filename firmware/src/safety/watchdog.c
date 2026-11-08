#include "watchdog.h"

#include <zephyr/kernel.h>
#include <zephyr/device.h>
#include <zephyr/logging/log.h>
#include <zephyr/sys/atomic.h>

LOG_MODULE_REGISTER(WDG, LOG_LEVEL_INF);

#if CONFIG_TREMOSENSE_WATCHDOG && !CONFIG_PWM_TEST_RB_LED

#include <zephyr/drivers/watchdog.h>

#define SUPERVISOR_PERIOD_MS 100
/* Boot (calibration) can legitimately run for tens of seconds. If the system
 * has not reached run phase by then the watchdog is no longer fed and the
 * board resets and retries. */
#define BOOT_WINDOW_MS 60000

static const struct device *const wdt = DEVICE_DT_GET_OR_NULL(DT_ALIAS(watchdog0));
static int channel = -1;
static atomic_t beat_ctl, beat_act, run_phase;

K_THREAD_STACK_DEFINE(sup_stack, 768);
static struct k_thread sup_thread;

static void supervisor(void *a, void *b, void *c)
{
	atomic_val_t last_ctl = 0, last_act = 0;

	ARG_UNUSED(a); ARG_UNUSED(b); ARG_UNUSED(c);
	while (1) {
		k_msleep(SUPERVISOR_PERIOD_MS);
		const atomic_val_t c_now = atomic_get(&beat_ctl);
		const atomic_val_t a_now = atomic_get(&beat_act);
		bool healthy;

		if (atomic_get(&run_phase) == 0) {
			healthy = k_uptime_get() < BOOT_WINDOW_MS;
		} else {
			healthy = (c_now != last_ctl) && (a_now != last_act);
		}
		last_ctl = c_now;
		last_act = a_now;
		if (healthy) {
			(void)wdt_feed(wdt, channel);
		}
	}
}

int watchdog_start(void)
{
	if (wdt == NULL || !device_is_ready(wdt)) {
		LOG_ERR("watchdog device not available: running WITHOUT watchdog");
		return -ENODEV;
	}
	struct wdt_timeout_cfg cfg = {
		.window = { .min = 0U, .max = CONFIG_TREMOSENSE_WDT_TIMEOUT_MS },
		.callback = NULL,
		.flags = WDT_FLAG_RESET_SOC,
	};
	channel = wdt_install_timeout(wdt, &cfg);
	if (channel < 0) {
		LOG_ERR("wdt_install_timeout failed: %d", channel);
		return channel;
	}
	int err = wdt_setup(wdt, WDT_OPT_PAUSE_HALTED_BY_DBG);
	if (err < 0) {
		LOG_ERR("wdt_setup failed: %d", err);
		return err;
	}
	k_thread_create(&sup_thread, sup_stack, K_THREAD_STACK_SIZEOF(sup_stack),
			supervisor, NULL, NULL, NULL, K_PRIO_PREEMPT(0), 0, K_NO_WAIT);
	LOG_INF("watchdog started: timeout %d ms", CONFIG_TREMOSENSE_WDT_TIMEOUT_MS);
	return 0;
}

void watchdog_arm_runtime(void) { atomic_set(&run_phase, 1); }
void watchdog_beat_control(void) { atomic_inc(&beat_ctl); }
void watchdog_beat_actuator(void) { atomic_inc(&beat_act); }

#else /* watchdog disabled by configuration */

int watchdog_start(void)
{
	LOG_WRN("watchdog disabled by configuration");
	return 0;
}
void watchdog_arm_runtime(void) {}
void watchdog_beat_control(void) {}
void watchdog_beat_actuator(void) {}

#endif
