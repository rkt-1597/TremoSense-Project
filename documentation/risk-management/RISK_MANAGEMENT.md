# Risk analysis (ISO 14971-informed working document)

Structure follows ISO 14971 (hazard → hazardous situation → harm → risk control → residual risk). It is a working
engineering analysis by the development team, not a formal risk management file: no risk acceptability criteria have been
agreed, no clinician/user input has been collected, and severity/probability below are **qualitative engineering estimates**.
S = severity (1 minor … 4 serious), P = probability *before* controls (L/M/H).

| ID | Hazard / failure | Hazardous situation → harm | S | P | Risk controls implemented | Residual risk / status |
|---|---|---|---|---|---|---|
| H-01 | IMU failure, corrupt data, EKF divergence, firmware crash | spoon driven to a wrong angle or frozen → food spill, burn, strike | 3 | M | monitor, EKF guards, guard timeout/hold/neutral, watchdog, boot neutral | controls exist and pass host tests; hardware behaviour unverified. Open |
| H-02 | Loop cancels slow orientation change (D-15) | user cannot tilt spoon to mouth / device fights the hand → spill, strain | 3 | H | none beyond bounded servo range | **unmitigated design limitation** |
| H-03 | Actuator command out of range / NaN / servo stall or jam | over-travel, jam, pinch, overheating | 3 | M | clamp + finite check + optional slew; no stall sensing | stall/jam **unmitigated** (R-01) |
| H-04 | Supply droop / brown-out / reset | MCU reset mid-motion; servos unpulsed until boot code runs | 3 | M | watchdog; neutral first at boot | supply monitoring **absent** (R-02); reset duration unmeasured |
| H-05 | Wrong calibration (board moved/tilted) or invalid tuning | systematic angle offset → persistent mis-tilt | 2 | M | calibration acceptance, retries, latch; tuning validation | residual: user ignores LED prompts |
| H-06 | Device in a degraded state without the user knowing | user relies on a non-functioning stabiliser | 3 | M | none (R-04) | **open** |
| H-07 | Excessive heating (servo/boost converter) | burn, damage | 3 | L–M | none | **open**, no sensing |
| H-08 | Electrical / EMC / battery hazards (Li-ion, boost converter) | fire, shock, interference | 4 | L | none in firmware; hardware design not in repo | **cannot be assessed** (IEC 60601-1, -1-2 not evaluated) |
| H-09 | Unsafe use by people with severe tremor/dyskinesia, unexpected movement | device saturates, mis-stabilises | 3 | M | servo bounds; neutral on fault | needs user testing; **open** |
| H-10 | Software update / cyber (no wireless link implemented) | n/a today | — | — | no network or command interface in firmware | re-assess if BLE is added (IEC 81001-5-1) |

## Standards status (for honesty)

| Standard | Used as | Assessment performed? |
|---|---|---|
| ISO 14971 | structure of this table | informal only |
| IEC 62304 | traceability (requirements → tests), configuration control, unit/integration tests | partial; no software safety classification assigned, no SOUP list (Zephyr, nrfx, picolibc) |
| ISO 13485 | change history, review via branch/PR | no QMS exists |
| IEC 62366-1 | list of usability risks (H-02, H-06, H-09) | no usability engineering performed |
| IEC 60601-1 / -1-2 | noted as not evaluated | no |
| IEC 81001-5-1 | noted for any future wireless interface | no |
| Indian MDR 2017 / CDSCO | — | no classification, no licence pathway assessed |

**No claim of compliance, certification or approval is made.**
