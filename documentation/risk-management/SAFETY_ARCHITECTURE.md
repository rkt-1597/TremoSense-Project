# Safety architecture

Engineering reference only. TremoSense is a research prototype. It is **not** certified, cleared or approved under
ISO 13485, IEC 62304, ISO 14971, IEC 60601-1 or the Indian Medical Device Rules (CDSCO), and no regulatory assessment has been performed.
These standards are used as engineering guidance for structure and traceability.

## Layers

```
 IMU (data-ready, 208 Hz) ──► [imu.c] timestamped sample (spinlock, seq, drops counted)
        │
        ▼  control thread (prio 1)                              actuation thread (prio 5)
 monitor_classify_sample ─► ekf_update ─► monitor_classify_estimate ─► lqr_compute ─► latest-wins mailbox ─► guard_step ─► PWM
   NaN / range / stuck / dt     input & numeric checks    |angle| limit      finite check        (depth 1)      clamp, slew, hold,
        │                                                                                                      neutral, recovery
        └── heartbeat ─┐                                                                          heartbeat ──┐
                       ▼                                                                                    ▼
                 watchdog supervisor (feeds the nRF52 WDT only while BOTH loops progress; 500 ms)
```

* **Monitor** (control thread): classifies every sample and estimate; a single bad sample is rejected (command marked invalid); a fault is *asserted* after 10 consecutive bad steps (~48 ms) and cleared after 208 consecutive good ones (~1 s). `FAULT_CONFIG` / `FAULT_CAL` are permanent until reboot.
* **Actuator guard** (actuation thread, the last gate before the PWM): independent of control-thread correctness. States: `ACTIVE` (follow the clamped command), `HOLD` (hold the last good output for ≤ 100 ms), `SAFE_NEUTRAL` (slew to neutral at 60 °/s and hold, PWM stays energised). Re-entry to `ACTIVE` needs 208 consecutive valid commands and is rate-limited.
* **Timeout**: no command for 50 ms (control loop stalled) ⇒ guard treats it as invalid ⇒ `HOLD` then `SAFE_NEUTRAL`.
* **Watchdog**: hardware reset if either loop stops (500 ms). After reset the actuation thread levels the servos before IMU init and calibration.
* **Boot**: servos are commanded neutral first. Actuation is enabled only after (a) the tuning passed validation and (b) calibration passed its stillness/level checks.

## Safe-state policy (why "servos off" is not the default)

For a spoon carrying food, an unpowered hobby servo goes limp: the spoon can tilt under load and spill, or swing into
the user. A held **neutral** pose is mechanically predictable, so it is the default safe state for *data/estimation*
faults (IMU, EKF, command, timeout, config, calibration). Exceptions where continuing to energise the servo is itself the
hazard (stall, obstruction, over-temperature, brown-out) call for **de-energising**, but **none of these can be detected
with the current hardware** (no current, temperature or supply sensing in firmware). They are listed as unresolved below.

## Fault table

| Fault | Detection | Response | Implemented | Verified |
|---|---|---|---|---|
| IMU failure / no data | 50 ms timeout | HOLD ≤ 100 ms → neutral | yes | host test (sim) |
| Non-finite / out-of-range sample | per-sample check | reject; assert after 10 → neutral | yes | host test |
| Stuck sensor (bit-identical ×32) | per-sample | as above | yes | host test |
| Bad timing (dt ∉ [0.5, 20] ms) | per-sample | as above | yes | host test |
| EKF numeric failure | status + finite checks | reset from accel; assert → neutral | yes | host test |
| Implausible estimate (|angle| > 80°) | per-estimate | as above | yes | host test |
| Excessive / NaN command | guard clamp, finite check | clamp to servo range; NaN → hold | yes | host test |
| Invalid tuning (Q/R/K/max pitch) | boot validation | never actuate; neutral | yes | host test |
| Failed calibration | stillness/level/gravity checks, 3 attempts | never actuate; neutral | yes | host test |
| Firmware hang / crash | watchdog (both loops) | SoC reset → neutral at boot | yes | **compiled only** |
| Servo stall / disconnect / obstruction | — | — | **no** (no sensing) | — |
| Battery under-voltage / supply droop | — | — | **no** (no ADC path implemented) | — |
| Excessive heating | — | — | **no** (no sensing) | — |
| Communication failure | n/a: no wireless/serial command interface is implemented | — | n/a | — |
| User-visible fault indication | — | — | **no** (only the calibration LED exists) | — |

"host test (sim)" = executed on synthetic data on a PC; it is not a hardware test.

## Unresolved risks (must be addressed before any use with people)

1. **R-01 No stall/obstruction/over-current protection.** A jammed servo can be driven continuously.
2. **R-02 No supply monitoring.** A sagging supply can brown-out the MCU mid-motion; the watchdog/reset path then leaves the servos unpulsed for the time between reset and boot code (not measured).
3. **R-03 Resistance to intentional movement (audit D-15).** The loop cancels slow orientation changes as well as tremor. Turning the spoon toward the mouth may be opposed. No tremor-band separation exists; no voluntary-movement test exists.
4. **R-04 Loss of function is not visible to the user.** No indicator or alarm outside calibration.
5. **R-05 Servo-range limits are the full servo range** (0–180°); the mechanical linkage's safe range is unknown and must be set from the mechanical design.
6. **R-06 Recovery timing** (1 s good data) and hold time (100 ms) are engineering judgements, not validated against user comfort or spill risk.
7. **R-07 Watchdog behaviour on hardware has not been observed** (reset time, PWM state during reset, boot time).
