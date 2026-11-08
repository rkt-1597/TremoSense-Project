# Contributing

- Host tests must pass before a change: `cmake -S firmware/tests -B build-host -G Ninja && cmake --build build-host && ctest --test-dir build-host --output-on-failure`.
- Keep the portable core (`ekf`, `lqr`, `control`, `safety`, `imu_cal`, `timing`) free of Zephyr includes.
- Format core and tests with `clang-format -style=file:.clang-format`.
- Do not state hardware or clinical results without logs; label evidence as simulation, bench, HIL or user testing.
- Do not claim regulatory compliance; standards are references only.
- New requirements need an ID in `documentation/requirements/REQUIREMENTS.md` and a verification entry in `VV_PLAN.md`.
