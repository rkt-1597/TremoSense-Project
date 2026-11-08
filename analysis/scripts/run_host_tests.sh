#!/bin/sh
# Builds and runs the host tests and writes documentation/verification-validation/TEST_REPORT.md
# stamped with the commit the tests ran on. Usage: sh analysis/scripts/run_host_tests.sh
set -e
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
B=$(mktemp -d)
OUT="$ROOT/documentation/verification-validation/TEST_REPORT.md"
cmake -S "$ROOT/firmware/tests" -B "$B" -G Ninja >/dev/null
cmake --build "$B" 2>&1 | tail -1
LOG=$(ctest --test-dir "$B" -V 2>&1 | grep -E "checks,|Test +#|tests passed|Total Test|^ +(hold|nominal|NaN|legacy|max |burst|degenerate)" || true)
{
echo "# Host test report"
echo
echo "- Commit tested: \`$(git -C "$ROOT" rev-parse --short HEAD)\` (working tree clean: $(git -C "$ROOT" diff --quiet && echo yes || echo NO))"
echo "- Date: $(date -u +%Y-%m-%d)"
echo "- Host: $(uname -sm), $(gcc --version | head -1)"
echo "- Flags: -Wall -Wextra -Wpedantic -Wshadow -Wconversion -Werror, AddressSanitizer + UBSan"
echo "- Evidence class: **host simulation/unit test**. No target hardware, no Zephyr runtime, no servos."
echo
echo '```'
echo "$LOG"
echo '```'
echo
echo "Regenerate with \`sh analysis/scripts/run_host_tests.sh\`. Hardware test cases remain NOT RUN (see \`VV_PLAN.md\`)."
} > "$OUT"
rm -rf "$B"
