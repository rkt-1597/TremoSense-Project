#include "imu.h"
#include "pwm.h"
#include "ekf.h"
#include "lqr.h"

#include <stdio.h>
#include <zephyr/sys/util.h>

LOG_MODULE_REGISTER(IMU, LOG_LEVEL_INF);

int print_samples = 0, lsm6ds3_trc_trig_cnt = 0, cnt = 0;
char out_str[128];

const struct pwm_dt_spec imu_calib_led = PWM_DT_SPEC_GET(DT_ALIAS(imu_calib));
#define IMU_CALIB_LED_MIN    PWM_USEC(DT_PROP(DT_ALIAS(imu_calib), min_pulse_us))
#define IMU_CALIB_LED_MAX    PWM_USEC(DT_PROP(DT_ALIAS(imu_calib), max_pulse_us))
#define IMU_CALIB_LED_PERIOD (IMU_CALIB_LED_MAX - IMU_CALIB_LED_MIN)

struct sensor_value accel_x_out, accel_y_out, accel_z_out;
struct sensor_value gyro_x_out, gyro_y_out, gyro_z_out;
double accel_offset_x = 0, accel_offset_y = 0, accel_offset_z = 0;
double gyro_offset_x = 0, gyro_offset_y = 0, gyro_offset_z = 0;

void lsm6ds3_trc_trigger_handler(const struct device *dev,
				    const struct sensor_trigger *trig)
{
	static struct sensor_value accel_x, accel_y, accel_z;
	static struct sensor_value gyro_x, gyro_y, gyro_z;

	lsm6ds3_trc_trig_cnt++;

	sensor_sample_fetch_chan(dev, SENSOR_CHAN_ACCEL_XYZ);
	sensor_channel_get(dev, SENSOR_CHAN_ACCEL_X, &accel_x);
	sensor_channel_get(dev, SENSOR_CHAN_ACCEL_Y, &accel_y);
	sensor_channel_get(dev, SENSOR_CHAN_ACCEL_Z, &accel_z);

	sensor_sample_fetch_chan(dev, SENSOR_CHAN_GYRO_XYZ);
	sensor_channel_get(dev, SENSOR_CHAN_GYRO_X, &gyro_x);
	sensor_channel_get(dev, SENSOR_CHAN_GYRO_Y, &gyro_y);
	sensor_channel_get(dev, SENSOR_CHAN_GYRO_Z, &gyro_z);

	accel_x_out = accel_x;
	accel_y_out = accel_y;
	accel_z_out = accel_z;

	gyro_x_out = gyro_x;
	gyro_y_out = gyro_y;
	gyro_z_out = gyro_z;

	k_sem_give(&imu_sem);
}

void calibrate_imu(void)
{
        int samples = 300;
        double sum_ax = 0, sum_ay = 0, sum_az = 0;
        double sum_gx = 0, sum_gy = 0, sum_gz = 0;

        printk("Please place the board flat on a table and DO NOT TOUCH IT.\n");

	uint32_t pulse = IMU_CALIB_LED_MAX;
	pwm_set_pulse_dt(&imu_calib_led, pulse);

        k_msleep(3000);
        printk("\n--- STARTING CALIBRATION ---\n");

        for (int i = 0; i < samples; i++) {
		print_samples = 1;
                sum_ax += sensor_value_to_double(&accel_x_out);
                sum_ay += sensor_value_to_double(&accel_y_out);
                sum_az += sensor_value_to_double(&accel_z_out);

                sum_gx += sensor_value_to_double(&gyro_x_out);
                sum_gy += sensor_value_to_double(&gyro_y_out);
                sum_gz += sensor_value_to_double(&gyro_z_out);

                k_msleep(10); 
        }

        gyro_offset_x = sum_gx / samples;
        gyro_offset_y = sum_gy / samples;
        gyro_offset_z = sum_gz / samples;

        accel_offset_x = sum_ax / samples;
        accel_offset_y = sum_ay / samples;
        accel_offset_z = (sum_az / samples) - 9.80665; 

        printk("Calibration Complete! (5s pause for user to check offset)\n");
        printk("Accel Offsets: X: %.3f, Y: %.3f, Z: %.3f\n", accel_offset_x, accel_offset_y, accel_offset_z);
        printk("Gyro Offsets:  X: %.3f, Y: %.3f, Z: %.3f\n\n", gyro_offset_x, gyro_offset_y, gyro_offset_z);
        
	uint32_t wait_start = k_uptime_get_32();
        while ((k_uptime_get_32() - wait_start) < 5000) {
		if(pulse == IMU_CALIB_LED_MAX)
			pulse = IMU_CALIB_LED_MIN;
		else
			pulse = IMU_CALIB_LED_MAX; 
		pwm_set_pulse_dt(&imu_calib_led, pulse);
                k_msleep(200); 
        }
}

int imu_init(const struct device *imu_dev)
{
	int err;
	struct sensor_trigger trig;
        struct sensor_value odr_attr, acc_full_scale, gyro_full_scale;

	trig.type = SENSOR_TRIG_DATA_READY;
	trig.chan = SENSOR_CHAN_ACCEL_XYZ;

	if (!device_is_ready(imu_dev)) {
		LOG_ERR("device not ready");
		return -EIO;
	}

	odr_attr.val1 = 208;
	odr_attr.val2 = 0;

	if ((err = sensor_attr_set(imu_dev, SENSOR_CHAN_ACCEL_XYZ,
			    SENSOR_ATTR_SAMPLING_FREQUENCY, &odr_attr)) < 0) {
		LOG_ERR("Cannot set sampling frequency for accel: %d", err);
		return err;
	}

	if ((err = sensor_attr_set(imu_dev, SENSOR_CHAN_GYRO_XYZ,
			    SENSOR_ATTR_SAMPLING_FREQUENCY, &odr_attr)) < 0) {
		LOG_ERR("Cannot set sampling frequency for gyro: %d", err);
		return err;
	}

	/* 16g accel measurment range FS */
        acc_full_scale.val1 = 156;
        acc_full_scale.val2 = 906400;
        
        if ((err = sensor_attr_set(imu_dev, SENSOR_CHAN_ACCEL_XYZ,
			    SENSOR_ATTR_FULL_SCALE, &acc_full_scale)) < 0) {
		LOG_ERR("Cannot set sampling frequency for accel: %d", err);
		return err;
	}

	/* 2000 dps gyro measurment range FS */
        gyro_full_scale.val1 = 34;
        gyro_full_scale.val2 = 906585;
        
        if ((err = sensor_attr_set(imu_dev, SENSOR_CHAN_GYRO_XYZ,
			    SENSOR_ATTR_FULL_SCALE, &gyro_full_scale)) < 0) {
		LOG_ERR("Cannot set sampling frequency for gyro: %d", err);
		return err;
	}

	if ((err = sensor_trigger_set(imu_dev, &trig, lsm6ds3_trc_trigger_handler)) != 0) {
		LOG_ERR("Could not set sensor type and channel: %d", err);
		return err;
	}

	if ((err = sensor_sample_fetch(imu_dev)) < 0) {
		LOG_ERR("Sensor sample update error: %d", err);
		return err;
	}

	#if CONFIG_IMU_CALIBRATION_WHILE_TESTING
		calibrate_imu();
	#endif

        return 0;
}

int imu_readings(void)
{
	#if CONFIG_CLEAR_SCREEN
		printk("\033[2J\033[H");
	#endif

	/* lsm6ds3_trc accel */
	snprintf(out_str, sizeof(out_str), "accel x:%f m/s2 y:%f m/s2 z:%f m/s2",
							sensor_value_to_double(&accel_x_out) - accel_offset_x,
							sensor_value_to_double(&accel_y_out) - accel_offset_y,
							sensor_value_to_double(&accel_z_out) - accel_offset_z);
	printk("%s\n", out_str);

	/* lsm6ds3_trc gyro */
	snprintf(out_str, sizeof(out_str), "gyro  x:%f dps  y:%f dps  z:%f dps ",
							(sensor_value_to_double(&gyro_x_out)* RAD_TO_DEG) - gyro_offset_x* RAD_TO_DEG,
							(sensor_value_to_double(&gyro_y_out)* RAD_TO_DEG) - gyro_offset_y* RAD_TO_DEG,
							(sensor_value_to_double(&gyro_z_out)* RAD_TO_DEG) - gyro_offset_z* RAD_TO_DEG);
	printk("%s\n", out_str);

	LOG_INF("loop:%d trig_cnt:%d\n\n", ++cnt, lsm6ds3_trc_trig_cnt);


	return 0;
}

void imu_thread_function(const struct device *dev, void *arg2, void *arg3) {
	int err;

	uint32_t last_time = k_uptime_get_32();
	while (1) {
		 if (k_sem_take(&imu_sem, K_FOREVER) != 0) {
			printk("Input data not available!\n");
		} else {
			if ((err = imu_readings()) < 0) {
				LOG_ERR("Error reading IMU data: %d", err);
				k_thread_abort(imu_tid);
			}

			uint32_t current_time = k_uptime_get_32();
			float actual_dt_seconds = (float)(current_time - last_time) / 1000.0f;
			last_time = current_time;
			ekf_update(sensor_value_to_double(&accel_x_out) - accel_offset_x,
				sensor_value_to_double(&accel_y_out) - accel_offset_y,
				sensor_value_to_double(&accel_z_out) - accel_offset_z,
				sensor_value_to_double(&gyro_x_out) - gyro_offset_x,
				sensor_value_to_double(&gyro_y_out) - gyro_offset_y,
				sensor_value_to_double(&gyro_z_out) - gyro_offset_z,
				actual_dt_seconds, 
				Q_GYRO_PROCESS_NOISE, 
				R_ACCEL_MEASUREMENT_NOISE, 
				&ekf_calculated_results);

			printk("Est. Roll: %.2f deg | Est. Pitch: %.2f deg\n\n",
				ekf_calculated_results.roll, 
				ekf_calculated_results.pitch);

			lqr_update(ekf_calculated_results.roll, 
				ekf_calculated_results.pitch,
				sensor_value_to_double(&gyro_x_out), 
				sensor_value_to_double(&gyro_y_out), 
				gyro_offset_x, 
				gyro_offset_y);

			k_msgq_peek(&lqr_res, &obtained_lqr_values);
			
			printk("Servo Calc. Roll: %.2f deg | Pitch: %.2f deg\n\n",
				obtained_lqr_values.roll_to_servo, 
				obtained_lqr_values.pitch_to_servo);
		}
	}
}
