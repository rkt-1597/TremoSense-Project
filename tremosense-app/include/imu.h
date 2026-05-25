#ifndef IMU_H
#define IMU_H

#include <zephyr/kernel.h>
#include <zephyr/device.h>
#include <zephyr/logging/log.h>
#include <zephyr/drivers/sensor.h>
#include <zephyr/devicetree.h>

#define IMU_SLEEP_MS 10
#define IMU_THREAD_STACK_SIZE_BYTES 2048

extern k_tid_t imu_tid;

extern struct k_sem imu_sem;

void lsm6ds3_trc_trigger_handler(const struct device *dev,
			     const struct sensor_trigger *trig);

int imu_init(const struct device *imu_dev);

void calibrate_imu(void);

int imu_readings(void);

void imu_thread_function(const struct device *dev, void *arg2, void *arg3);

#endif /* IMU_H */