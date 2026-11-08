#ifndef WATCHDOG_H
#define WATCHDOG_H

/* Hardware watchdog supervision. The control and actuation loops each call
 * their beat function every iteration; the supervisor feeds the watchdog only
 * while both keep progressing, so a hang in either causes a reset. */

int watchdog_start(void);          /* begin supervising (boot phase) */
void watchdog_arm_runtime(void);   /* require loop heartbeats from now on */
void watchdog_beat_control(void);
void watchdog_beat_actuator(void);

#endif /* WATCHDOG_H */
