amp_roll = 0;
amplitudes = 2:7;
colors = lines(length(amplitudes));

fig = figure('Name','Tremor Suppression Analysis', ...
             'Position',[100 50 1000 900], ...
             'Color','k');

subplot(2,1,1); hold on; grid on;

yline(-13.98,'w--','LineWidth',1.5, 'DisplayName','80% Suppress');

yline(-20,'w:','LineWidth',1.5, 'DisplayName','90% Suppress');

subplot(2,1,2); hold on; grid on;

for i = 1:length(amplitudes)

    amp = amplitudes(i);

    assignin('base','amp_pitch',amp);

    out = sim('TremoSense_Model.slx',15);

    x = detrend(squeeze(out.input_pitch.Data));
    y = detrend(squeeze(out.sum_pitch.Data));

    [txy,f] = tfestimate(x,y,hanning(500),250,32768,1000);

    idx = f <= 8;

    mag = smoothdata(20*log10(abs(txy(idx))),'gaussian',50);

    phase = smoothdata(unwrap(angle(txy(idx)))*(180/pi),'gaussian',50);

    subplot(2,1,1);
    plot(f(idx),mag,'Color',colors(i,:),'LineWidth',1.3,'DisplayName', ...
         sprintf('%d°',amp));

    subplot(2,1,2);
    plot(f(idx),phase-phase(1),'Color',colors(i,:),'LineWidth',1.3,...
        'DisplayName',sprintf('%d°',amp));

end

subplot(2,1,1)

xlim([0 8])
ylim([-30 0])

title('Magnitude Response (0-8 Hz)','Color','w')
ylabel('Magnitude (dB)','Color','w')

set(gca, 'Color','k', 'XColor','w', 'YColor','w')

legend('TextColor','w','Color','k','EdgeColor','w','Location','southwest',...
    'NumColumns',2)

subplot(2,1,2)

xlim([0 8])

title('Phase Response (0-8 Hz)','Color','w')
ylabel('Phase (deg)','Color','w')
xlabel('Frequency (Hz)','Color','w')

set(gca,'Color','k','XColor','w','YColor','w')

legend('TextColor','w','Color','k','EdgeColor','w','Location','southwest',...
    'NumColumns',2)