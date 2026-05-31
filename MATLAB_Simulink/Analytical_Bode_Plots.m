clear; clc; close all;

if ~isfile('controller_data.mat')
    error('Run LQR_ARE.m first to generate controller_data.mat');
end
load('controller_data.mat');

A_cl = A_d - B_d * K_lqr;
C = [1, 0, 0, 0; 
     0, 0, 1, 0];
sys_cl = ss(A_cl, B_d, C, zeros(2,2), Ts);

w = logspace(0, 3, 1000);

[mag_11, ~] = bode(sys_cl(1,1), w);
[mag_12, ~] = bode(sys_cl(1,2), w);
[mag_21, ~] = bode(sys_cl(2,1), w);
[mag_22, ~] = bode(sys_cl(2,2), w);

mag_11_db = squeeze(20*log10(mag_11));
mag_12_db = squeeze(20*log10(mag_12));
mag_21_db = squeeze(20*log10(mag_21));
mag_22_db = squeeze(20*log10(mag_22));

fig1 = figure('Name', 'Magnitude Bode Plots', 'Color', 'k', 'WindowStyle', 'normal', 'Position', [50, 150, 1000, 700]);

subplot(2,2,1);
semilogx(w, mag_11_db, 'c', 'LineWidth', 2); grid on;
title('Roll Cmd \rightarrow Roll Angle (Main)', 'Color', 'w'); ylabel('Magnitude (dB)', 'Color', 'w');

subplot(2,2,2);
semilogx(w, mag_12_db, 'r', 'LineWidth', 2); grid on;
title('Pitch Cmd \rightarrow Roll Angle (Cross-Coupling)', 'Color', 'w'); ylabel('Magnitude (dB)', 'Color', 'w');
ylim([-350, 10]); 

subplot(2,2,3);
semilogx(w, mag_21_db, 'r', 'LineWidth', 2); grid on;
title('Roll Cmd \rightarrow Pitch Angle (Cross-Coupling)', 'Color', 'w'); xlabel('Frequency (rad/s)', 'Color', 'w'); ylabel('Magnitude (dB)', 'Color', 'w');
ylim([-350, 10]);

subplot(2,2,4);
semilogx(w, mag_22_db, 'm', 'LineWidth', 2); grid on;
title('Pitch Cmd \rightarrow Pitch Angle (Main)', 'Color', 'w'); xlabel('Frequency (rad/s)', 'Color', 'w'); ylabel('Magnitude (dB)', 'Color', 'w');

all_axes1 = findall(fig1, 'type', 'axes');
set(all_axes1, 'Color', 'k', 'XColor', 'w', 'YColor', 'w', 'GridColor', [0.5 0.5 0.5], 'GridAlpha', 0.5);
sgtitle('Magnitude Bode Plots', 'Color', 'w', 'FontSize', 16, 'FontWeight', 'bold');


sys_roll  = sys_cl(1,1);
sys_pitch = sys_cl(2,2);

[~, phase_11] = bode(sys_roll, w);
[~, phase_22] = bode(sys_pitch, w);

phase_11_deg = squeeze(phase_11);
phase_22_deg = squeeze(phase_22);

mag_limit_db = -3;
phase_limit_deg = -45;

idx = find(mag_11_db <= mag_limit_db, 1);
if ~isempty(idx) && idx > 1, w_mag_r = interp1(mag_11_db(idx-1:idx), w(idx-1:idx), mag_limit_db); else, w_mag_r = Inf; end

idx = find(phase_11_deg <= phase_limit_deg, 1);
if ~isempty(idx) && idx > 1, w_phase_r = interp1(phase_11_deg(idx-1:idx), w(idx-1:idx), phase_limit_deg); else, w_phase_r = Inf; end

idx = find(mag_22_db <= mag_limit_db, 1);
if ~isempty(idx) && idx > 1, w_mag_p = interp1(mag_22_db(idx-1:idx), w(idx-1:idx), mag_limit_db); else, w_mag_p = Inf; end

idx = find(phase_22_deg <= phase_limit_deg, 1);
if ~isempty(idx) && idx > 1, w_phase_p = interp1(phase_22_deg(idx-1:idx), w(idx-1:idx), phase_limit_deg); else, w_phase_p = Inf; end

f_mag_r = w_mag_r / (2*pi);
f_phase_r = w_phase_r / (2*pi);
f_mag_p = w_mag_p / (2*pi);
f_phase_p = w_phase_p / (2*pi);

global_min_hz = min([f_mag_r, f_phase_r, f_mag_p, f_phase_p]);

fig2 = figure('Name', 'System Limits based on Direct-Coupled Axes', 'Color', 'k', 'WindowStyle', 'normal', 'Position', [100, 100, 1000, 700]);

subplot(2,2,1);
semilogx(w, mag_11_db, 'c', 'LineWidth', 2); hold on; grid on;
yline(mag_limit_db, 'w--');
if ~isinf(w_mag_r), xline(w_mag_r, 'r--', sprintf('%.1f Hz', f_mag_r), 'LabelVerticalAlignment', 'bottom', 'Color', 'r', 'FontWeight', 'bold'); end
title('Roll Axis: Magnitude', 'Color', 'w'); ylabel('Magnitude (dB)', 'Color', 'w');

subplot(2,2,3);
semilogx(w, phase_11_deg, 'c', 'LineWidth', 2); hold on; grid on;
yline(phase_limit_deg, 'w--');
if ~isinf(w_phase_r), xline(w_phase_r, 'r--', sprintf('%.1f Hz', f_phase_r), 'LabelVerticalAlignment', 'bottom', 'Color', 'r', 'FontWeight', 'bold'); end
xlabel('Frequency (rad/s)', 'Color', 'w'); ylabel('Phase (deg)', 'Color', 'w');

subplot(2,2,2);
semilogx(w, mag_22_db, 'm', 'LineWidth', 2); hold on; grid on;
yline(mag_limit_db, 'w--');
if ~isinf(w_mag_p), xline(w_mag_p, 'r--', sprintf('%.1f Hz', f_mag_p), 'LabelVerticalAlignment', 'bottom', 'Color', 'r', 'FontWeight', 'bold'); end
title('Pitch Axis: Magnitude', 'Color', 'w'); ylabel('Magnitude (dB)', 'Color', 'w');

subplot(2,2,4);
semilogx(w, phase_22_deg, 'm', 'LineWidth', 2); hold on; grid on;
yline(phase_limit_deg, 'w--');
if ~isinf(w_phase_p), xline(w_phase_p, 'r--', sprintf('%.1f Hz', f_phase_p), 'LabelVerticalAlignment', 'bottom', 'Color', 'r', 'FontWeight', 'bold'); end
xlabel('Frequency (rad/s)', 'Color', 'w'); ylabel('Phase (deg)', 'Color', 'w');

all_axes2 = findall(fig2, 'type', 'axes');
set(all_axes2, 'Color', 'k', 'XColor', 'w', 'YColor', 'w', 'GridColor', [0.5 0.5 0.5], 'GridAlpha', 0.5);
sgtitle(sprintf('System Limits (Global Min: %.2f Hz)', global_min_hz), 'Color', 'w', 'FontSize', 16, 'FontWeight', 'bold');