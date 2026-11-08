out = sim('TremoSense_Model.slx', 4);

roll_input    = squeeze(out.input_roll.Data);
roll_residual = squeeze(out.sum_roll.Data);

roll_rms_input    = rms(roll_input);
roll_rms_residual = rms(roll_residual);

pitch_input    = squeeze(out.input_pitch.Data);
pitch_residual = squeeze(out.sum_pitch.Data);

pitch_rms_input    = rms(pitch_input);
pitch_rms_residual = rms(pitch_residual);

fprintf('\n===== ROLL AXIS =====\n');
fprintf('Input RMS      = %.4f deg\n', roll_rms_input);
fprintf('Residual RMS   = %.4f deg\n', roll_rms_residual);

fprintf('\n===== PITCH AXIS =====\n');
fprintf('Input RMS      = %.4f deg\n', pitch_rms_input);
fprintf('Residual RMS   = %.4f deg\n', pitch_rms_residual);