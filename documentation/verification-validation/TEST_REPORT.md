# Host test report

- Commit tested: `df223ba` (working tree clean: yes)
- Date: 2026-11-08
- Host: Linux x86_64, gcc (Ubuntu 13.3.0-6ubuntu2~24.04.1) 13.3.0
- Flags: -Wall -Wextra -Wpedantic -Wshadow -Wconversion -Werror, AddressSanitizer + UBSan
- Evidence class: **host simulation/unit test**. No target hardware, no Zephyr runtime, no servos.

```
1: test_ekf: 10397 checks, 0 failures
1/4 Test #1: test_ekf .........................   Passed    0.02 sec
2: test_lqr_timing_cal: 1640 checks, 0 failures
2/4 Test #2: test_lqr_timing_cal ..............   Passed    0.01 sec
3: test_safety: 2532 checks, 0 failures
3/4 Test #3: test_safety ......................   Passed    0.01 sec
4: test_control: 14453 checks, 0 failures
4/4 Test #4: test_control .....................   Passed    0.02 sec
100% tests passed, 0 tests failed out of 4
Total Test time (real) =   0.06 sec
```

Regenerate with `sh analysis/scripts/run_host_tests.sh`. Hardware test cases remain NOT RUN (see `VV_PLAN.md`).
