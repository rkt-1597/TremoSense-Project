#ifndef LQR_H
#define LQR_H

/* LQR state-feedback law. Portable C99, no RTOS dependency. */

#ifndef DEG_TO_RAD
#define DEG_TO_RAD 0.01745329f
#endif
#ifndef RAD_TO_DEG
#define RAD_TO_DEG 57.2957795f
#endif

typedef struct {
    float k[2][4]; /* row 0: roll servo, row 1: pitch servo */
} lqr_gain_t;

typedef struct {
    float roll_to_servo; /* servo command [deg], neutral = 90 */
    float pitch_to_servo;
} lqr_result_t;

/* State order: [roll [rad], roll rate [rad/s], pitch [rad], pitch rate [rad/s]].
 * Row 0 of K drives the roll servo, row 1 the pitch servo. The sign
 * convention (roll inverted, pitch not) is that of the original firmware.
 * No saturation is applied here: the actuator guard is the single clamp point. */
void lqr_compute(const lqr_gain_t *K, float phi_rad, float p_rads, float theta_rad, float q_rads,
                 float neutral_deg, lqr_result_t *out);

#endif /* LQR_H */
