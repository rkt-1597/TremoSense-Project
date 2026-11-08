#ifndef IMU_H
#define IMU_H

#include <stdint.h>
#include <zephyr/kernel.h>
#include <zephyr/device.h>

/* One IMU sample as handed from the driver thread to the control thread. */
struct imu_sample {
	float accel[3];     /* [m/s^2] raw, not offset-corrected */
	float gyro[3];      /* [rad/s] raw, not offset-corrected */
	uint32_t cycles;    /* k_cycle_get_32() when the data-ready event ran */
	uint32_t seq;       /* increments on every published sample */
};

/* Configure ODR / full scale and install the data-ready trigger. */
int imu_driver_init(const struct device *imu_dev);

/* Block until a new sample is available. Returns 0, or -EAGAIN on timeout.
 * Sets *dropped to the number of samples lost since the previous call. */
int imu_wait_sample(struct imu_sample *out, k_timeout_t timeout, uint32_t *dropped);

uint32_t imu_total_dropped(void);
uint32_t imu_fetch_errors(void);

#endif /* IMU_H */
