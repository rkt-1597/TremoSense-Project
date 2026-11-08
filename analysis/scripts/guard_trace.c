/* Drives the REAL actuator guard (firmware/src/safety/safety.c) with a synthetic command stream and a
 * fault injected at t = 1.0 s, printing CSV: t, valid, cmd_roll, out_roll, state.  SIMULATION: no servo model.
 * Usage: guard_trace <fault_duration_ms> */
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include "safety.h"

int main(int argc, char **argv) {
    const double fault_ms = argc > 1 ? atof(argv[1]) : 40.0;
    const guard_config_t cfg = {90.0f, 0.0f, 180.0f, 0.0f, 60.0f, 100.0f, 208};
    guard_t g;
    guard_init(&g, &cfg);
    guard_enable(&g, true);
    const double dt = 1.0 / 208.0;
    printf("t,valid,cmd,out,state\n");
    for (int i = 0; i < (int)(3.0 / dt); i++) {
        double t = i * dt;
        int valid = !(t >= 1.0 && t < 1.0 + fault_ms / 1000.0);
        /* held tilt of +20 deg plus a 5 Hz, 4 deg compensation command around neutral */
        float cmd = (float)(90.0 + 20.0 + 4.0 * sin(2.0 * M_PI * 5.0 * t));
        guard_out_t o = guard_step(&g, (float)dt, valid, cmd, 90.0f);
        printf("%.5f,%d,%.3f,%.3f,%d\n", t, valid, cmd, o.roll_deg, (int)o.state);
    }
    return 0;
}
