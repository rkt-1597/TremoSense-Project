clear; clc; close all;

if ~isfile('controller_data.mat')
    error('Run LQR_Design.m first to generate controller_data.mat');
end
load('controller_data.mat');

A_cl = A_d - B_d * K_lqr;
C = [1, 0, 0, 0;
     0, 0, 1, 0];
sys_cl = ss(A_cl, B_d, C, zeros(2,2), Ts);

sys_cl.InputName = {'Roll Cmd', 'Pitch Cmd'};
sys_cl.OutputName = {'Roll Angle', 'Pitch Angle'};

info = stepinfo(sys_cl);
overshoots = [info(1,1).Overshoot, info(2,2).Overshoot];
settling_times = [info(1,1).SettlingTime, info(2,2).SettlingTime];
rise_times = [info(1,1).RiseTime, info(2,2).RiseTime];

fprintf('\n========================================================\n');
fprintf('  UNIT STEP RESPONSE (DIRECT-COUPLED AXES)\n');
fprintf('========================================================\n');
fprintf('Roll Axis  | Overshoot: %5.2f%% | Settling Time: %.4f s | Rise Time: %.4f s\n', overshoots(1), settling_times(1), rise_times(1));
fprintf('Pitch Axis | Overshoot: %5.2f%% | Settling Time: %.4f s | Rise Time: %.4f s\n', overshoots(2), settling_times(2), rise_times(2));
fprintf('--------------------------------------------------------\n');

fig = figure('Name', 'Unit Step Response', 'Color', 'k', 'WindowStyle', 'normal', 'Position', [150, 150, 900, 600]);
step(sys_cl);

all_axes = findall(fig, 'type', 'axes');
set(all_axes, 'Color', 'k', 'XColor', 'w', 'YColor', 'w', 'GridColor', [0.5 0.5 0.5], 'GridAlpha', 0.5);
grid(all_axes, 'on');

set(findall(fig, 'type', 'text'), 'Color', 'w');
set(findall(fig, 'type', 'line'), 'LineWidth', 2);

sgtitle('Unit Step Response', 'Color', 'w', 'FontSize', 14, 'FontWeight', 'bold');