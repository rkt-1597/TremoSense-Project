#ifndef APP_H
#define APP_H

#include "control.h"

#define CONTROL_THREAD_STACK_SIZE_BYTES 3072

/* Boot calibration with acceptance checks and retries. Returns 0 on success;
 * on failure the offsets are NOT applied and the caller must latch FAULT_CAL. */
int calibrate_imu(control_t *ctl);

/* arg1: control_t * */
void control_thread_function(void *arg1, void *arg2, void *arg3);

#endif /* APP_H */
