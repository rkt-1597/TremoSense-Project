#ifndef TIMING_H
#define TIMING_H

#include <stdint.h>

/* Wrap-safe elapsed time between two free-running 32-bit cycle counters.
 * Returns 0 for cycles_per_sec == 0. Resolution is one cycle (the legacy
 * code used k_uptime_get_32(), i.e. 1 ms quantisation: at 208 Hz the
 * 4.81 ms period was measured as 4 or 5 ms: -17 % / +4 % per step). */
float timing_dt_seconds(uint32_t prev_cycles, uint32_t now_cycles, uint32_t cycles_per_sec);

#endif /* TIMING_H */
