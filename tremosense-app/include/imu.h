#ifndef IMU_H
#define IMU_H

#include <zephyr/drivers/sensor.h>
#include <zephyr/device.h>
#include <zephyr/logging/log.h>

#define IMU_SLEEP_MS 100       // 100 ms sleep time between consecutive readings
#define CONFIG_IMU_CALIBRATION_TESTING 1

void lsm6ds3_trc_trigger_handler(const struct device *dev,
			     const struct sensor_trigger *trig);

int imu_init(const struct device *imu_dev);

void calibrate_imu(void);

int imu_readings(void);

#endif /* IMU_H */