#ifndef SAFETY_H
#define SAFETY_H

/* Safety layer: (1) sample/estimate monitor in the control loop and (2) the
 * actuator guard, which is the last gate before the servos and is owned by
 * the actuation thread. Portable C99, host-tested. See
 * documentation/risk-management/SAFETY_ARCHITECTURE.md for the fault policy. */

#include <stdbool.h>
#include <stdint.h>
#include "ekf.h"

/* ---- fault flags ---- */
#define FAULT_NONE 0u
#define FAULT_IMU_NONFINITE (1u << 0)
#define FAULT_IMU_RANGE (1u << 1)
#define FAULT_IMU_STUCK (1u << 2)
#define FAULT_IMU_TIMING (1u << 3)
#define FAULT_IMU_TIMEOUT (1u << 4)
#define FAULT_EKF_NUMERIC (1u << 5)
#define FAULT_EKF_RANGE (1u << 6)
#define FAULT_CMD_INVALID (1u << 7)
#define FAULT_CONFIG (1u << 8) /* permanent until reboot */
#define FAULT_CAL (1u << 9)    /* permanent until reboot */
#define FAULT_PERMANENT (FAULT_CONFIG | FAULT_CAL)

/* ---- monitor ---- */
typedef struct {
    float accel_max_ms2;
    float gyro_max_rads;
    float dt_min_s;
    float dt_max_s;
    float angle_limit_deg;
    uint16_t stuck_samples;  /* 0 disables stuck detection */
    uint16_t max_consec_bad; /* bad samples before a fault is asserted */
    uint16_t recover_good;   /* good samples before a fault is cleared */
} monitor_config_t;

typedef struct {
    monitor_config_t cfg;
    uint32_t active_faults; /* asserted now */
    uint32_t seen_faults;   /* sticky since boot (diagnostics) */
    uint32_t bad_total;
    uint16_t consec_bad;
    uint16_t consec_good;
    uint16_t stuck_run;
    float last_raw[6];
    bool have_last;
} monitor_t;

void monitor_init(monitor_t *m, const monitor_config_t *cfg);

/* Classification only (no fault bookkeeping except stuck-run tracking). */
uint32_t monitor_classify_sample(monitor_t *m, const float accel[3], const float gyro[3], float dt);
uint32_t monitor_classify_estimate(const monitor_t *m, ekf_status_t st, const ekf_result_t *est);

/* Record this step's flags. Returns true iff the step is usable, i.e. no
 * flags this step and no fault currently asserted. */
bool monitor_note(monitor_t *m, uint32_t flags);

void monitor_assert_permanent(monitor_t *m, uint32_t flags);

/* ---- actuator guard ---- */
typedef enum {
    GUARD_SAFE_NEUTRAL = 0, /* output slews to neutral and holds it */
    GUARD_ACTIVE,           /* output follows the (clamped) command */
    GUARD_HOLD              /* holding last good output, time-limited */
} guard_state_t;

typedef struct {
    float neutral_deg;
    float min_deg;
    float max_deg;
    float max_slew_dps;  /* 0 disables slew limiting while ACTIVE */
    float safe_slew_dps; /* used for return-to-neutral and re-entry */
    float hold_ms;
    uint16_t recover_good;
} guard_config_t;

typedef struct {
    guard_config_t cfg;
    guard_state_t state;
    bool enabled;
    bool ramping;
    float out[2]; /* roll, pitch [deg] */
    float hold_elapsed_ms;
    uint16_t good;
} guard_t;

typedef struct {
    float roll_deg;
    float pitch_deg;
    guard_state_t state;
} guard_out_t;

void guard_init(guard_t *g, const guard_config_t *cfg);

/* While disabled the output is neutral. Enabling goes straight to ACTIVE
 * (after a ramped start); disabling returns to SAFE_NEUTRAL. */
void guard_enable(guard_t *g, bool enable);

/* One actuation tick. 'valid' = a command with no active fault. */
guard_out_t guard_step(guard_t *g, float dt_s, bool valid, float roll_cmd_deg, float pitch_cmd_deg);

#endif /* SAFETY_H */
