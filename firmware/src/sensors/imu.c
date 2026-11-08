#include "imu.h"
#include "constants.h"

#include <zephyr/drivers/sensor.h>
#include <zephyr/logging/log.h>
#include <zephyr/spinlock.h>

LOG_MODULE_REGISTER(IMU, LOG_LEVEL_INF);

/* Static initialisation: the data-ready trigger can fire as soon as it is
 * installed, so the semaphore must exist before imu_driver_init() runs
 * (the original code initialised it afterwards in main()). */
K_SEM_DEFINE(imu_sem, 0, 1);

static struct k_spinlock sample_lock;
static struct imu_sample latest;
static uint32_t consumed_seq;
static uint32_t total_dropped;
static uint32_t fetch_errors;

static void lsm6ds3_trc_trigger_handler(const struct device *dev,
					const struct sensor_trigger *trig)
{
	struct sensor_value v[6];
	struct imu_sample s;

	ARG_UNUSED(trig);
	s.cycles = k_cycle_get_32();

	if (sensor_sample_fetch_chan(dev, SENSOR_CHAN_ACCEL_XYZ) < 0 ||
	    sensor_sample_fetch_chan(dev, SENSOR_CHAN_GYRO_XYZ) < 0 ||
	    sensor_channel_get(dev, SENSOR_CHAN_ACCEL_X, &v[0]) < 0 ||
	    sensor_channel_get(dev, SENSOR_CHAN_ACCEL_Y, &v[1]) < 0 ||
	    sensor_channel_get(dev, SENSOR_CHAN_ACCEL_Z, &v[2]) < 0 ||
	    sensor_channel_get(dev, SENSOR_CHAN_GYRO_X, &v[3]) < 0 ||
	    sensor_channel_get(dev, SENSOR_CHAN_GYRO_Y, &v[4]) < 0 ||
	    sensor_channel_get(dev, SENSOR_CHAN_GYRO_Z, &v[5]) < 0) {
		/* Publish nothing: the control thread's timeout path handles it. */
		fetch_errors++;
		return;
	}
	for (int i = 0; i < 3; i++) {
		s.accel[i] = sensor_value_to_float(&v[i]);
		s.gyro[i] = sensor_value_to_float(&v[3 + i]);
	}

	k_spinlock_key_t key = k_spin_lock(&sample_lock);
	s.seq = latest.seq + 1U;
	latest = s;
	k_spin_unlock(&sample_lock, key);

	k_sem_give(&imu_sem);
}

int imu_driver_init(const struct device *imu_dev)
{
	int err;
	struct sensor_trigger trig = {
		.type = SENSOR_TRIG_DATA_READY,
		.chan = SENSOR_CHAN_ACCEL_XYZ,
	};
	struct sensor_value odr_attr = { .val1 = (int32_t)IMU_ODR_HZ, .val2 = 0 };
	/* 16 g accel full scale (156.9064 m/s^2) and 2000 dps gyro (34.906585 rad/s):
	 * unchanged from the original firmware. */
	struct sensor_value acc_full_scale = { .val1 = 156, .val2 = 906400 };
	struct sensor_value gyro_full_scale = { .val1 = 34, .val2 = 906585 };

	if (!device_is_ready(imu_dev)) {
		LOG_ERR("device not ready");
		return -EIO;
	}

	err = sensor_attr_set(imu_dev, SENSOR_CHAN_ACCEL_XYZ,
			      SENSOR_ATTR_SAMPLING_FREQUENCY, &odr_attr);
	if (err < 0) {
		LOG_ERR("Cannot set sampling frequency for accel: %d", err);
		return err;
	}
	err = sensor_attr_set(imu_dev, SENSOR_CHAN_GYRO_XYZ,
			      SENSOR_ATTR_SAMPLING_FREQUENCY, &odr_attr);
	if (err < 0) {
		LOG_ERR("Cannot set sampling frequency for gyro: %d", err);
		return err;
	}
	err = sensor_attr_set(imu_dev, SENSOR_CHAN_ACCEL_XYZ,
			      SENSOR_ATTR_FULL_SCALE, &acc_full_scale);
	if (err < 0) {
		LOG_ERR("Cannot set full scale for accel: %d", err);
		return err;
	}
	err = sensor_attr_set(imu_dev, SENSOR_CHAN_GYRO_XYZ,
			      SENSOR_ATTR_FULL_SCALE, &gyro_full_scale);
	if (err < 0) {
		LOG_ERR("Cannot set full scale for gyro: %d", err);
		return err;
	}
	err = sensor_trigger_set(imu_dev, &trig, lsm6ds3_trc_trigger_handler);
	if (err != 0) {
		LOG_ERR("Could not set sensor type and channel: %d", err);
		return err;
	}
	err = sensor_sample_fetch(imu_dev);
	if (err < 0) {
		LOG_ERR("Sensor sample update error: %d", err);
		return err;
	}
	return 0;
}

int imu_wait_sample(struct imu_sample *out, k_timeout_t timeout, uint32_t *dropped)
{
	if (k_sem_take(&imu_sem, timeout) != 0) {
		return -EAGAIN;
	}
	k_spinlock_key_t key = k_spin_lock(&sample_lock);
	*out = latest;
	k_spin_unlock(&sample_lock, key);

	uint32_t gap = 0U;
	if (consumed_seq != 0U && out->seq != consumed_seq + 1U) {
		gap = out->seq - consumed_seq - 1U;
	}
	consumed_seq = out->seq;
	total_dropped += gap;
	if (dropped != NULL) {
		*dropped = gap;
	}
	return 0;
}

uint32_t imu_total_dropped(void) { return total_dropped; }
uint32_t imu_fetch_errors(void) { return fetch_errors; }
