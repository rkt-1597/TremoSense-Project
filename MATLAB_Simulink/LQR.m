function [u_roll, u_pitch] = LQR(phi_deg, theta_deg, p_raw, q_raw, bias_phi, bias_theta, K_lqr)
    phi_rad = phi_deg * (pi/180);
    theta_rad = theta_deg * (pi/180);
    p_clean = p_raw - bias_phi;
    q_clean = q_raw - bias_theta;

    x_state = [phi_rad; 0; theta_rad; 0];
    u = -K_lqr * x_state;
    
    u_roll = u(1) * (180/pi);
    u_pitch = u(2) * (180/pi);
end