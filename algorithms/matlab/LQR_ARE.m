fs = 1000;           
Ts = 1/fs;     

% Configure data according to use case
mass_food = 0.0;   
mass_pitch_servo = 0.0;  
alpha_roll  = 0.0;  
alpha_pitch = 0.0; 
% ====================================

radius_pitch = 0.0; 
pitch_servo_torque = 0.0;
J_pitch = mass_food * (radius_pitch^2); 
beta_pitch = (pitch_servo_torque * 0.098) / J_pitch; 

radius_roll = 0.0; 
roll_servo_torque = 0.0;
pitch_servo_offset = 0.0; 
J_servo_cm = (1/12) * mass_pitch_servo * (0.022^2 + 0.022^2); 
J_roll = J_servo_cm + (mass_pitch_servo * pitch_servo_offset^2) + (mass_food * radius_roll^2);
beta_roll = (roll_servo_torque * 0.098) / J_roll; 

A_cont = [0, 1, 0, 0; 0, -alpha_roll, 0, 0;  0, 0, 0, 1;  0, 0, 0, -alpha_pitch];
B_cont = [0, 0;  beta_roll, 0;  0, 0;  0, beta_pitch];
sys_d = c2d(ss(A_cont, B_cont, eye(4), zeros(4,2)), Ts, 'zoh');

% Configure data according to use case
max_roll_angle  = 0.0;   
max_roll_rate   = 0.0;   
max_roll_servo  = 0.0;
W_roll  = 0.0;   
max_pitch_angle  = 0.0;   
max_pitch_rate   = 0.0;   
max_pitch_servo  = 0.0;
W_pitch  = 0.0; 
% ====================================  

Q = diag([W_roll * (1/(max_roll_angle^2)), 1/(max_roll_rate^2), ...
          W_pitch * (1/(max_pitch_angle^2)), 1/(max_pitch_rate^2)]);
R = diag([1/(max_roll_servo^2), 1/(max_pitch_servo^2)]);

K_lqr = dlqr(sys_d.A, sys_d.B, Q, R);

assignin('base', 'K_lqr', K_lqr);
assignin('base', 'A_d', sys_d.A);
assignin('base', 'B_d', sys_d.B);
assignin('base', 'Ts', Ts);
fprintf('\nK_lqr\n');
disp(K_lqr);