#ifndef TEST_UTIL_H
#define TEST_UTIL_H
#include <math.h>
#include <stdio.h>
#include <stdint.h>

static int g_failures;
static int g_checks;

#define CHECK(cond)                                                                                \
    do {                                                                                           \
        g_checks++;                                                                                \
        if (!(cond)) {                                                                             \
            g_failures++;                                                                          \
            printf("  FAIL %s:%d: %s\n", __FILE__, __LINE__, #cond);                               \
        }                                                                                          \
    } while (0)
#define CHECK_NEAR(a, b, tol)                                                                      \
    do {                                                                                           \
        g_checks++;                                                                                \
        double _a = (a), _b = (b);                                                                 \
        if (!(fabs(_a - _b) <= (tol))) {                                                           \
            g_failures++;                                                                          \
            printf("  FAIL %s:%d: |%g - %g| > %g\n", __FILE__, __LINE__, _a, _b, (double)(tol));   \
        }                                                                                          \
    } while (0)

/* Deterministic PRNG (LCG) + Box-Muller so results are reproducible. */
static uint32_t g_rng = 12345u;
static inline void rng_seed(uint32_t s) {
    g_rng = s;
}
static inline double rng_uniform(void) {
    g_rng = g_rng * 1664525u + 1013904223u;
    return ((double)(g_rng >> 8) + 0.5) / 16777216.0;
}
static inline double rng_normal(void) {
    double u1 = rng_uniform(), u2 = rng_uniform();
    return sqrt(-2.0 * log(u1)) * cos(6.283185307179586 * u2);
}

#define TEST_MAIN_END(name)                                                                        \
    do {                                                                                           \
        printf("%s: %d checks, %d failures\n", name, g_checks, g_failures);                        \
        return g_failures ? 1 : 0;                                                                 \
    } while (0)
#endif
