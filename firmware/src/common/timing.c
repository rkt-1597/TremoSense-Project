#include "timing.h"

float timing_dt_seconds(uint32_t prev_cycles, uint32_t now_cycles, uint32_t cycles_per_sec) {
    if (cycles_per_sec == 0U) {
        return 0.0f;
    }
    const uint32_t delta = now_cycles - prev_cycles; /* unsigned: wrap-safe */
    return (float)((double)delta / (double)cycles_per_sec);
}
