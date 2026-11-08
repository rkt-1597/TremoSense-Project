# Requirements and traceability matrix

IDs are stable. **Proposed** targets are engineering proposals made during this upgrade, not agreed clinical or product
requirements; the project owners and, for performance, input from clinicians/users must confirm them.
Status values: **Verified-host** (executed on a PC with synthetic data), **Verified-build** (compiles for the target),
**NOT RUN** (needs hardware/people), **Open** (not implemented or not resolved). Nothing here is hardware-verified.

| ID | Requirement | Basis | Method | Test case(s) | Status |
|---|---|---|---|---|---|
| TS-SYS-001 | The device shall stabilise the spoon in roll and pitch against hand motion. | project aim | Test (hardware) | TC-PERF-001..004 | NOT RUN |
| TS-SYS-002 | The device shall not oppose intentional spoon motion more than an agreed limit. | assistive-use risk (R-03) | Test (hardware, users) | TC-PERF-003, TC-HW-011 | NOT RUN — design gap (D-15) |
| TS-SYS-003 | Tremor attenuation target over 4–8 Hz on the bench rig. *Proposed*: ≥ 80 % amplitude reduction, matching the 80 %/90 % lines already used in the repository. | repo README | Test (rig) | TC-PERF-001 | NOT RUN |
| TS-SW-001 | The IMU shall be sampled at 208 Hz via the data-ready interrupt path. | design | Inspection + test | TC-HW-001 | Inspected; timing NOT RUN |
| TS-SW-002 | The estimator step shall use `dt` derived from the sample's own timestamp at ≤ 1 µs resolution, and reject `dt` outside [0.5 ms, 20 ms]. | audit D-06 | Test | TC-TIM-001, TC-SAF-001, TC-SIM-001 | Verified-host |
| TS-SW-003 | The EKF shall never emit a non-finite estimate and shall leave its state unchanged on a rejected update. | audit D-01/D-11 | Test | TC-EKF-003, -004, -008 | Verified-host |
| TS-SW-004 | For valid inputs the refactored EKF and LQR shall reproduce the baseline output. | preserve working code | Test | TC-EKF-006, TC-LQR-001 | Verified-host |
| TS-SW-005 | Tuning constants shall be validated at boot; invalid tuning shall prevent actuation. | audit D-01 | Test | TC-EKF-001, TC-INT-001 | Verified-host |
| TS-SW-006 | Calibration shall be accepted only if the board is still, level and gravity-consistent, and retried; repeated failure shall prevent actuation. | audit D-12 | Test | TC-CAL-001..004, TC-INT-007 | Verified-host |
| TS-SW-007 | Sensor hand-off between driver and control threads shall be free of torn reads and uninitialised synchronisation objects. | audit D-04/D-05 | Inspection + build | TC-BLD-002 | Verified-build; concurrency stress NOT RUN |
| TS-SW-008 | The control path shall not perform blocking console I/O per sample. | audit D-07 | Inspection + (latency) test | TC-BLD-002, TC-HW-002 | Inspected; latency NOT RUN |
| TS-SW-009 | The actuation thread shall act on the latest command only. | audit D-08 | Inspection | TC-BLD-002 | Verified-build |
| TS-SW-010 | Static analysis shall be clean on the portable core; the firmware shall build for the target. | quality | Analysis | TC-BLD-001..005 | Verified-host / -build |
| TS-SAF-001 | Servo commands shall be finite and within the servo range before reaching the PWM. | D-03 | Test | TC-SAF-005, TC-INT-002 | Verified-host |
| TS-SAF-002 | On IMU loss the actuator guard shall enter SAFE_NEUTRAL (start the slew-limited return to 90°) within 150 ms (hold ≤ 100 ms + one actuation tick). The pose itself reaches 90° after a further ≤ tilt/60 °/s (≤ 1.5 s over the full range; 0.42 s measured in simulation from a +20° tilt). *Proposed.* | safety policy | Test | TC-SAF-006, TC-INT-005, TC-HW-007 | Verified-host; hardware NOT RUN |
| TS-SAF-003 | Return to neutral shall be slew-limited (≤ 60 °/s) and monotonic. *Proposed.* | comfort/spill risk | Test | TC-SAF-007 | Verified-host |
| TS-SAF-004 | Recovery after a fault shall require 208 consecutive valid commands. *Proposed.* | avoid chatter | Test | TC-SAF-008 | Verified-host |
| TS-SAF-005 | A firmware hang in either loop shall cause a hardware reset within 500 ms; the servos shall be levelled at boot. | D-09, D-13 | Test (hardware) | TC-HW-005, TC-HW-006 | Implemented; NOT RUN |
| TS-SAF-006 | Servo stall/obstruction shall be detected and the servo de-energised. | R-01 | Test (hardware) | TC-HW-010 | **Open — no sensing** |
| TS-SAF-007 | Supply under-voltage shall be detected and handled. | R-02 | Test (hardware) | TC-HW-004 | **Open — not implemented** |
| TS-SAF-008 | A fault shall be visible to the user. | R-04 | Demonstration | TC-HW-011 | **Open — not implemented** |
| TS-PERF-001 | Estimator RMS error and lag vs. a reference orientation, per frequency. | audit | Analysis (sim) / Test (rig) | TC-SIM-001 / TC-PERF-002 | Sim done; rig NOT RUN |
| TS-PERF-002 | End-to-end latency (sample → servo motion) shall be measured and reported. | audit D-16 | Test (hardware) | TC-HW-002, TC-HW-003 | NOT RUN |
| TS-PERF-003 | Runtime stability: ≥ 1 h continuous operation without fault/reset. *Proposed.* | reliability | Test (hardware) | TC-PERF-005 | NOT RUN |
| TS-PERF-004 | Battery runtime and supply stability under servo load shall be measured. | audit | Test (hardware) | TC-HW-004, TC-HW-008 | NOT RUN |
| TS-HW-001 | Hardware documentation (schematic, BOM, mounting, power) shall be in the repository. | traceability | Inspection | — | **Open — owner input** |

## Hazard ↔ requirement trace

| Hazard (see [RISK_MANAGEMENT](../risk-management/RISK_MANAGEMENT.md)) | Requirements |
|---|---|
| H-01 spill/injury from loss of control | TS-SAF-001, -002, -003, -005 |
| H-02 resistance to intentional movement | TS-SYS-002 |
| H-03 actuator overdrive / stall | TS-SAF-001, -006 |
| H-04 power failure | TS-SAF-005, -007 |
| H-05 wrong calibration / tuning | TS-SW-005, -006 |
| H-06 undetected failure | TS-SAF-008 |
