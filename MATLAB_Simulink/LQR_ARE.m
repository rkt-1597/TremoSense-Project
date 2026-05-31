clear; clc; close all;

Ts = 0;
Q_EKF = 0
R_EKF = 0;

alpha_roll  = 0;  
alpha_pitch = 0;  
beta_roll  = 0;    
beta_pitch = 0; 

angle_lim = 0;
servo_lim = 0;

A_cont = [0,  1,           0,  0; 
          0, -alpha_roll,  0,  0; 
          0,  0,           0,  1; 
          0,  0,           0, -alpha_pitch];
      
B_cont = [0,           0; 
          beta_roll,   0; 
          0,           0; 
          0,           beta_pitch];

sys_c = ss(A_cont, B_cont, eye(4), zeros(4,2));
sys_d = c2d(sys_c, Ts, 'zoh');
A_d = sys_d.A;
B_d = sys_d.B;

max_angle_error = deg2rad(angle_lim);
max_servo_angle = deg2rad(servo_lim);

Q = diag([1/(max_angle_error^2), 0, 1/(max_angle_error^2), 0]);
R = diag([1/(max_servo_angle^2), 1/(max_servo_angle^2)]);

warning('off', 'Control:design:lqr1');
[K_lqr, ~, ~] = dlqr(A_d, B_d, Q, R);
warning('on', 'Control:design:lqr1');

disp(K_lqr);

save('controller_data.mat', 'A_d', 'B_d', 'K_lqr', 'Ts');