function [phi, theta, bias_phi, bias_theta] = fcn(Ax, Ay, Az, p_raw, q_raw, r_raw, dt, Q_val, R_val)
    persistent x P
    if isempty(x)
        x = zeros(4,1); 
        P = eye(4) * 1.0; 
    end

    p = p_raw - x(3); 
    q = q_raw - x(4);
    r = r_raw;    
    phi_prev = x(1); 
    theta_prev = x(2);
    
    s_ph = sin(phi_prev); c_ph = cos(phi_prev);
    t_th = tan(theta_prev); c_th = cos(theta_prev);
    sec_th = 1/max(c_th, 0.01); 

    phi_dot   = p + q*s_ph*t_th + r*c_ph*t_th;
    theta_dot = q*c_ph - r*s_ph;
    
    
    x(1) = x(1) + phi_dot * dt;
    x(2) = x(2) + theta_dot * dt;
    
    A = zeros(4,4);
    A(1,1) = q*c_ph*t_th - r*s_ph*t_th;
    A(1,2) = (q*s_ph + r*c_ph) * (sec_th^2);
    A(1,3) = -1; 
    A(2,1) = -q*s_ph - r*c_ph;
    A(2,4) = -1; 
    
    F = eye(4) + A*dt;
    Q = eye(4) * Q_val; 
    P = F * P * F' + Q;

    phi_acc   = atan2(Ay, Az);
    theta_acc = atan2(-Ax, sqrt(Ay^2 + Az^2));    
    z = [phi_acc; theta_acc];
    C = [1 0 0 0; 0 1 0 0];

    R = eye(2) * R_val;
    K = P * C' / (C * P * C' + R);
    x = x + K * (z - C*x);
    P = (eye(4) - K * C) * P;

    phi        = x(1) * (180/pi);
    theta      = x(2) * (180/pi);
    bias_phi   = x(3);
    bias_theta = x(4);
end