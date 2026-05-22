#include "imu.h"

LOG_MODULE_REGISTER(main, LOG_LEVEL_INF);

int main(void)
{
	int err;

	const struct device *const lsm6ds3_trc_dev = DEVICE_DT_GET_ONE(st_lsm6dsl);
	err = imu_init(lsm6ds3_trc_dev);
	if (err) {
		LOG_ERR("Failed to initialize IMU: %d", err);
		return err;
	}

	while (1) {
		if ((err = imu_readings()) < 0) {
			return err;
		}
		k_sleep(K_MSEC(IMU_SLEEP_MS));
	}

	return 0;
}
