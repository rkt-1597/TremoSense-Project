# Changelog

## Unreleased (branch `pranshu-updates`)

### Changed
- Repository restructured: `firmware/`, `algorithms/matlab/`, `analysis/`, `documentation/`, `research/`. Build now runs from `firmware/`.
- Firmware split into portable core (EKF, LQR, control, safety, calibration, timing) and Zephyr glue; control math unchanged (bit-identical to legacy on valid data).
- `dt` now taken from the cycle counter instead of ms-quantised timestamps.
- Servo actuation only enabled when tuning constants are valid and calibration succeeded.

### Added
- Safety monitor and actuator guard (clamp, hold, safe neutral), watchdog supervisor.
- Validated IMU calibration with retries.
- Host unit/integration tests with ASan/UBSan, legacy-EKF regression, simulation study.
- Audit, requirements, risk, V&V documents; CI workflow (host tests, cppcheck, clang-format; Zephyr compile job not yet run in CI).

### Fixed
- Shipped zero tuning produced NaN estimates and unvalidated actuation; now rejected and held at neutral.
- README: stray character, stale paths, simulation claims labelled as simulation.

### Not verified
No hardware testing was performed. See `documentation/verification-validation/VV_PLAN.md`.
