# Host-side unit and integration tests for the portable firmware core.
# Not part of the Zephyr build:  cmake -S firmware/tests -B build-host && cmake --build build-host && ctest --test-dir build-host --output-on-failure
cmake_minimum_required(VERSION 3.16)
project(tremosense_host_tests C)

set(CMAKE_C_STANDARD 99)
set(CMAKE_C_STANDARD_REQUIRED ON)
set(FW ${CMAKE_CURRENT_SOURCE_DIR}/..)

option(TS_SANITIZE "Build with ASan/UBSan" ON)
set(WARN -Wall -Wextra -Wpedantic -Wshadow -Wconversion -Wno-sign-conversion -Wdouble-promotion -Werror)
if(TS_SANITIZE)
  set(SAN -fsanitize=address,undefined -fno-sanitize-recover=undefined)
endif()

add_library(ts_core STATIC
  ${FW}/src/estimation/ekf.c
  ${FW}/src/control/lqr.c
  ${FW}/src/control/control.c
  ${FW}/src/safety/safety.c
  ${FW}/src/sensors/imu_cal.c
  ${FW}/src/common/timing.c)
target_include_directories(ts_core PUBLIC ${FW}/include)
target_compile_options(ts_core PRIVATE ${WARN} ${SAN})
target_link_libraries(ts_core PUBLIC m ${SAN})

# Baseline: verbatim legacy EKF (renamed). MAX_PITCH_RAD is a macro in the legacy code.
add_library(ts_legacy STATIC reference/ekf_legacy.c)
target_include_directories(ts_legacy PUBLIC ${FW}/include ${CMAKE_CURRENT_SOURCE_DIR})
target_compile_definitions(ts_legacy PRIVATE MAX_PITCH_RAD=1.3962634f)
target_link_libraries(ts_legacy PUBLIC m)

enable_testing()
foreach(t test_ekf test_lqr_timing_cal test_safety test_control)
  add_executable(${t} ${t}.c)
  target_include_directories(${t} PRIVATE ${CMAKE_CURRENT_SOURCE_DIR})
  target_compile_options(${t} PRIVATE -Wall -Wextra -Werror ${SAN})
  target_link_libraries(${t} PRIVATE ts_core ts_legacy ${SAN})
  add_test(NAME ${t} COMMAND ${t})
endforeach()
