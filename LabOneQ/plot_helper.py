# This should be basically a match case of all the possible expermient types, while returning the ax, fig
from all_imports import *
from helper import *
from qelement_helper import *
from qops_helper import *
from qubit_experiments import *

def plot_exp(exp: Experiment, session: Session, qubit, **kwargs):
    match exp.uid:
        case 'TWPA Optimization':
            fig, ax = plot_twpa_optimization(exp, session, qubit, **kwargs)
            return fig, ax
        case 'Global Trace':
            fig, ax = plot_global_resonator_trace(exp, session, qubit, **kwargs)
            return fig, ax
        case 'Local Resonator Trace':
            fig, ax = plot_local_resonator_trace(exp, session, qubit, **kwargs)
            return fig, ax
        case 'Punchout':
            fig, ax = plot_punchout(exp, session, qubit, **kwargs)
            return fig, ax
        case 'Flux Sweep Trace':
            fig, ax = plot_flux_sweep_trace(exp, session, qubit, **kwargs)
            return fig, ax
        case 'Full Spectrum':
            fig, ax = plot_full_spectrum(exp, session, qubit, **kwargs)
            return fig, ax
        case 'Simple Spectrum':
            fig, ax = plot_simple_spectrum(exp, session, qubit, **kwargs)
            return fig, ax
        case 'Flux Sweep Full Spectrum':
            fig, ax = plot_flux_sweep_full_spectrum(exp, session, qubit, **kwargs)
            return fig, ax
        case 'Flux Sweep Spectrum':
            fig, ax = plot_flux_sweep_spectrum(exp, session, qubit, **kwargs)
            return fig, ax
        case '2D Flux Sweep':
            fig, ax = plot_dual_flux_sweep(exp, session, qubit, **kwargs)
            return fig, ax
        case 'X90 Tuneup':
            fig, ax = plot_x90_tuneup(exp, session, qubit, **kwargs)
            return fig, ax
        case 'T1 Exp':
            fig, ax = plot_T1_exp(exp, session, qubit, **kwargs)
            return fig, ax
        case 'T2 Star':
            fig, ax = plot_T2_star(exp, session, qubit, **kwargs)
            return fig, ax
        case 'T2 Echo':
            fig, ax = plot_T2_echo(exp, session, qubit, **kwargs)
            return fig, ax

def plot_twpa_optimization(exp, session, qubit):
    '''Plots a dual flux sweep (like for GKP)'''
    my_results = session.get_results()
    my_acquired_results = my_results.acquired_results['results']

    #plotting resonator over flux
    amp_data = np.abs(my_acquired_results.data)
    phase_data = np.angle(my_acquired_results.data)
    db_data = np.log10(amp_data)

    outer_currents = my_acquired_results.axis[0]
    outer_name = my_acquired_results.axis_name[0]
    inner_current = my_acquired_results.axis[1]
    inner_name = my_acquired_results.axis_name[1]

    fig, ax = plt.subplots(1,2, figsize=(15,6))
    cmap0 = ax[0].pcolor(outer_currents*1e6,
                inner_current*1e6,
                db_data.T,
                shading='nearest')
    ax[0].set_title(f'{qubit.uid} Resonator TWPA Response')
    ax[0].set_xlabel(f'{outer_name}')
    ax[0].set_ylabel(f'{inner_name}')
    cmap1 = ax[1].pcolor(outer_currents*1e6,
                inner_current*1e6,
                phase_data.T,
                shading='nearest')
    ax[1].set_title(f'{qubit.uid} Resonator TWPA Response')
    ax[1].set_xlabel(f'{outer_name}')
    ax[1].set_ylabel(f'{inner_name}')
    fig.colorbar(cmap0, ax=ax[0])
    fig.colorbar(cmap1, ax=ax[1])
    fig.tight_layout()

    return fig, ax

def plot_global_resonator_trace(exp, session, qubit):
    my_results = session.get_results() #a deep copy of session.results
    my_acquired_results = my_results.acquired_results['results']
    lo_array = my_acquired_results.axis[0]
    AWG_freqs = my_acquired_results.axis[1]
    freqs = np.empty((0))
    for lo in lo_array:
        freqs = np.append(freqs, lo + AWG_freqs,)
    IQ_data = my_acquired_results.data.ravel()
    IQ_data = remove_local_phase_delay(IQ_data, freqs, exp.signals[f'{qubit.uid}/acquire_line'].calibration.port_delay)
    amplitude = np.abs(IQ_data)
    phase = np.unwrap(np.angle(IQ_data))

    # Plot
    fig, ax = plt.subplots(2,1, figsize=(8,6))
    ax[0].plot(freqs, amplitude)
    ax[0].set_title('Wide Range Pulsed Trace')
    ax[0].set_xlabel('Frequency (GHz)')
    ax[0].set_ylabel('Amplitude (a.u.)')
    ax[1].plot(freqs, phase)
    ax[1].set_title('Wide Range Pulsed Trace')
    ax[1].set_xlabel('Frequency (GHz)')
    ax[1].set_ylabel('Phase')
    fig.tight_layout()
    return fig, ax

def plot_local_resonator_trace(exp, session, qubit):
    my_results = session.get_results() #a deep copy of session.results

    # Extracts data from the exp.acquire method with the same key name
    my_acquired_results = my_results.acquired_results['results']

    # For plotting current vs single resonator point
    freqs = my_acquired_results.axis[0] + exp.signals[f'{qubit.uid}/measure_line'].calibration.local_oscillator.frequency
    IQ_data = my_acquired_results.data
    IQ_data = remove_local_phase_delay(IQ_data, freqs, exp.signals[f'{qubit.uid}/acquire_line'].calibration.port_delay)
    amplitude = np.abs(IQ_data)
    phase = np.unwrap(np.angle(IQ_data))

    # Plots
    fig, ax = plt.subplots(2,1, figsize=(8,6))
    ax[0].scatter(freqs, amplitude)
    ax[0].set_title(f'{qubit.uid} Near Resonator Pulsed Trace')
    ax[0].set_xlabel('Frequency (GHz)')
    ax[0].set_ylabel('Amplitude (a.u.)')
    ax[0].autoscale(enable=True, axis='y', tight=False)
    ax[0].grid()
    ax[1].scatter(freqs, phase)
    ax[1].set_title(f'{qubit.uid} Near Resonator Pulsed Trace')
    ax[1].set_xlabel('Frequency (GHz)')
    ax[1].set_ylabel('Phase')
    ax[1].grid()
    fig.tight_layout()
    return fig, ax

def plot_punchout(exp, session, qubit, data_type:str='Phase'):
    my_results = session.get_results() #a deep copy of session.results
    my_acquired_results = my_results.acquired_results['results']
    freqs = my_acquired_results.axis[1]+exp.signals[f'{qubit.uid}/measure_line'].calibration.local_oscillator.frequency
    IQ_data = my_acquired_results.data
    IQ_data = remove_local_phase_delay(IQ_data, freqs, exp.signals[f'{qubit.uid}/acquire_line'].calibration.port_delay)
    normalized_amp_data = np.divide(np.abs(IQ_data).T, np.mean(np.abs(IQ_data), axis=1))
    normalized_dB_data = np.log10(normalized_amp_data)
    amplitude = np.abs(IQ_data)
    phase = np.unwrap(np.angle(IQ_data))
    phase = np.subtract(phase, np.expand_dims(np.mean(phase, axis=1), axis=1))

    amplitude = my_acquired_results.axis[0]
    power = 10*np.log10(amplitude**2)+exp.signals[f'{qubit.uid}/measure_line'].calibration.range

    if data_type=='Phase':
        graphing_data = phase.T
    elif data_type=='Amplitude':
        graphing_data = normalized_dB_data
    else:
        raise Exception('Not a valid data_type str')

    fig, ax = plt.subplots(1,2, figsize=(9,6))
    cmap0 = ax[0].pcolor(amplitude,
                freqs,
                graphing_data,
                shading='nearest')
    ax[0].set_title(f'{qubit.uid} Punchout of Resonator ({data_type})')
    ax[0].set_xlabel('Pulse Amplitude at Max Power')
    ax[0].set_ylabel('Readout Frequency (GHz)')
    ax[0].set_xscale('log')
    cmap1 = ax[1].pcolor(power,
                freqs,
                graphing_data,
                shading='nearest',)
    fig.colorbar(cmap0, ax=ax[0])
    fig.colorbar(cmap1, ax=ax[1])
    ax[1].set_title(f'{qubit.uid} Punchout of Resonator ({data_type})')
    ax[1].set_xlabel('Pulse Amplitude (Effective dBm at Max Amp)')
    ax[1].set_ylabel('Readout Frequency (GHz)')
    fig.tight_layout()
    return fig, ax

def plot_flux_sweep_trace(exp, session, qubit): 
    my_results = session.get_results() #a deep copy of session.results
    my_acquired_results = my_results.acquired_results['results']
    freqs = my_acquired_results.axis[1] + exp.signals[f'{qubit.uid}/measure_line'].calibration.local_oscillator.frequency
    IQ_data = my_acquired_results.data
    IQ_data = remove_local_phase_delay(IQ_data, freqs, exp.signals[f'{qubit.uid}/acquire_line'].calibration.port_delay)
    amplitude = np.abs(IQ_data)
    phase = np.unwrap(np.angle(IQ_data))
    phase = np.subtract(phase, np.expand_dims(np.mean(phase, axis=1), axis=1))

    currents = my_acquired_results.axis[0]*1e6
    
    fig, ax = plt.subplots(1,2, figsize=(15,6))
    cmap0 = ax[0].pcolor(currents,
        freqs,
        amplitude.T,
        shading='nearest')
    ax[0].set_title(f'{qubit.uid} Resonator Current Response')
    ax[0].set_xlabel('Currents (uA)')
    ax[0].set_ylabel('Readout Frequency (GHz)')
    cmap1 = ax[1].pcolor(currents,
        freqs,
        phase.T,
        shading='nearest',)
    fig.colorbar(cmap0, ax=ax[0])
    fig.colorbar(cmap1, ax=ax[1])
    ax[1].set_title(f'{qubit.uid} Resonator Current Response')
    ax[1].set_xlabel('Currents (uA)')
    ax[1].set_ylabel('Readout Frequency (GHz)')
    fig.tight_layout()
    return fig, ax

def plot_full_spectrum(exp, session, qubit, **kwargs):
    '''Plots a full spectrum'''
    my_results = session.get_results()
    my_acquired_results = my_results.acquired_results['results']
    drive_lo_array = my_acquired_results.axis[0]
    drive_AWG_freqs = my_acquired_results.axis[1]
    drive_freqs = np.empty((0))
    for drive_lo in drive_lo_array:
        drive_freqs = np.append(drive_freqs, drive_lo + drive_AWG_freqs)
    IQ_data = my_acquired_results.data.ravel()
    amplitude = np.abs(IQ_data)
    phase = np.unwrap(np.angle(IQ_data))

    fig, ax = plt.subplots(2,1, figsize=(8,6))
    ax[0].plot(drive_freqs, amplitude)
    ax[0].set_title(f'{qubit.uid} Spectrum')
    ax[0].set_xlabel('Frequency (GHz)')
    ax[0].set_ylabel('Amplitude')
    # ax[0].set_ylim(1, 5)
    ax[0].grid()
    ax[1].plot(drive_freqs, phase)
    ax[1].set_title(f'{qubit.uid} Spectrum')
    ax[1].set_xlabel('Drive Frequency (GHz)')
    ax[1].set_ylabel('Phase')
    # ax[1].set_ylim(2, 2.7)
    ax[1].grid()
    fig.tight_layout()
    return fig, ax

def plot_simple_spectrum(exp, session, qubit):
    my_results = session.get_results() #a deep copy of session.results
    # Extracts data from the exp.acquire method with the same key name
    my_acquired_results = my_results.acquired_results['results']
    # For plotting current vs single resonator point
    freqs = my_acquired_results.axis[0] + exp.signals[f'{qubit.uid}/drive_line'].calibration.local_oscillator.frequency
    # freqs = my_acquired_results.axis[0] + qubit.parameters.drive_lo_frequency
    IQ_data = my_acquired_results.data
    amplitude = np.abs(IQ_data)
    phase = np.unwrap(np.angle(IQ_data))
    phase = phase - np.mean(phase)

    fig, ax = plt.subplots(2,1, figsize=(8,6))
    ax[0].plot(freqs, amplitude)
    ax[0].set_title(f'{qubit.uid} Spectrum near Transition')
    ax[0].set_xlabel('Drive Frequency (GHz)')
    ax[0].set_ylabel('Amplitude')
    ax[0].grid()
    # ax[0].vlines(qubit.parameters.drive_frequency_ge+qubit.parameters.drive_lo_frequency, np.min(amplitude), np.max(amplitude), colors='r');
    ax[1].plot(freqs, phase)
    ax[1].set_title(f'{qubit.uid} Spectrum near Transition')
    ax[1].set_xlabel('Drive Frequency (GHz)')
    ax[1].set_ylabel('Phase')
    ax[1].grid()
    # ax[0].vlines(qubit.parameters.resonance_frequency_ge, np.min(amplitude), np.max(amplitude), colors='r');
    # ax[1].vlines(qubit.parameters.resonance_frequency_ge, np.min(phase), np.max(phase), colors='r')
    fig.tight_layout()
    return fig, ax

def plot_flux_sweep_full_spectrum(exp, session, qubit, **kwargs):
    my_results = session.get_results()
    my_acquired_results = my_results.acquired_results['results']
    drive_AWG_freqs = my_acquired_results.axis[2]
    drive_lo_array = my_acquired_results.axis[1]
    drive_freqs = np.empty((0))
    for drive_lo in drive_lo_array:
        drive_freqs = np.append(drive_freqs, drive_lo + drive_AWG_freqs,)

    currents = my_acquired_results.axis[0][0]
    ro_freqs = my_acquired_results.axis[0][1] + exp.signals[f'{qubit.uid}/measure_line'].calibration.local_oscillator.frequency
    repeated_ro_freqs = np.repeat(ro_freqs[:, np.newaxis], drive_freqs.size, axis=1)
    print(repeated_ro_freqs)

    data = my_acquired_results.data
    freq_shape = my_acquired_results.data.shape[1]*my_acquired_results.data.shape[2]
    shape_tuple = (currents.shape[0], freq_shape)
    IQ_data = data.reshape(shape_tuple)
    IQ_data = IQ_data - np.mean(IQ_data, axis=1)[:,None]
    amplitude = np.abs(IQ_data)
    IQ_data = remove_local_phase_delay(IQ_data, np.tile(ro_freqs, (np.shape(IQ_data)[1], 1)).T, exp.signals[f'{qubit.uid}/acquire_line'].calibration.port_delay)
    phase = np.unwrap(np.angle(IQ_data))

    fig, ax = plt.subplots(1,2, figsize=(8,5))
    cmap0 = ax[0].pcolor(currents*1e6,
        drive_freqs,
        amplitude.T,
        # vmin=0,
        # vmax=5,
        shading='nearest',)
    ax[0].set_title(f'{qubit.uid} Two Tone Spectroscopy')
    ax[0].set_xlabel('Currents (uA)')
    ax[0].set_ylabel('Drive Frequency (GHz)')
    cmap1 = ax[1].pcolor(currents*1e6,
        drive_freqs,
        phase.T,
        shading='nearest',)
    fig.colorbar(cmap0, ax=ax[0])
    ax[1].set_title(f'{qubit.uid} Two Tone Spectroscopy')
    ax[1].set_xlabel('Currents (uA)')
    ax[1].set_ylabel('Drive Frequency (GHz)')
    fig.colorbar(cmap1, ax=ax[1])
    fig.tight_layout()
    return fig, ax

def plot_flux_sweep_spectrum(exp, session, qubit, **kwargs):
    my_results = session.get_results()
    my_acquired_results = my_results.acquired_results['results']
    drive_freqs = my_acquired_results.axis[1]+exp.signals[f'{qubit.uid}/drive_line'].calibration.local_oscillator.frequency
    currents = my_acquired_results.axis[0][0]
    data = my_acquired_results.data
    ro_freqs = my_acquired_results.axis[0][1]+exp.signals[f'{qubit.uid}/measure_line'].calibration.local_oscillator.frequency
    # freqs = np.tile(freqs, (201, 1)).T
    # print(freqs[0,:])

    shape_tuple = (currents.shape[0], drive_freqs.shape[0])
    IQ_data = data.reshape(shape_tuple)
    IQ_data = IQ_data - np.mean(IQ_data, axis=1)[:,None]
    amplitude = np.abs(IQ_data)
    phase = np.angle(IQ_data)
    # phase = adjust_phase(IQ_data, freqs, qubit.parameters.readout_integration_delay)
    phase = phase - np.mean(phase, axis=1)[:, None]
    fig, ax = plt.subplots(1,2, figsize=(8,5))
    cmap0 = ax[0].pcolor(currents*1e6,
        drive_freqs,
        amplitude.T,
        shading='nearest',)
    ax[0].set_title(f'{qubit.uid} Two Tone Spectroscopy')
    ax[0].set_xlabel('Currents (uA)')
    ax[0].set_ylabel('Drive Frequency (GHz)')
    cmap1 = ax[1].pcolor(currents*1e6,
        drive_freqs,
        phase.T,
        shading='nearest',)
    fig.colorbar(cmap0, ax=ax[0])
    ax[1].set_title(f'{qubit.uid} Two Tone Spectroscopy')
    ax[1].set_xlabel('Currents (uA)')
    ax[1].set_ylabel('Drive Frequency (GHz)')
    fig.colorbar(cmap1, ax=ax[1])
    fig.tight_layout()
    return fig, ax

def plot_dual_flux_sweep(exp, session, qubit, **kwargs):
    '''Plots a dual flux sweep (like for GKP)'''
    my_results = session.get_results()
    my_acquired_results = my_results.acquired_results['results']

    #plotting resonator over flux
    amp_data = np.abs(my_acquired_results.data)
    phase_data = np.angle(my_acquired_results.data)
    db_data = np.log10(amp_data)

    outer_currents = my_acquired_results.axis[0]
    outer_name = my_acquired_results.axis_name[0]
    inner_current = my_acquired_results.axis[1]
    inner_name = my_acquired_results.axis_name[1]

    fig, ax = plt.subplots(1,2, figsize=(15,6))
    cmap0 = ax[0].pcolor(outer_currents*1e6,
                inner_current*1e6,
                db_data.T,
                shading='nearest')
    ax[0].set_title(f'{qubit.uid} Resonator 2D Flux Response')
    ax[0].set_xlabel(f'{outer_name}')
    ax[0].set_ylabel(f'{inner_name}')
    cmap1 = ax[1].pcolor(outer_currents*1e6,
                inner_current*1e6,
                phase_data.T,
                shading='nearest')
    ax[1].set_title(f'{qubit.uid} Resonator 2D Flux Response')
    ax[1].set_xlabel(f'{outer_name}')
    ax[1].set_ylabel(f'{inner_name}')
    fig.colorbar(cmap0, ax=ax[0])
    fig.colorbar(cmap1, ax=ax[1])
    fig.tight_layout()

    return fig, ax

def plot_x90_tuneup(exp, session, qubit, **kwargs):
    '''Plots an amplitude sweep x90 tuneup'''
    my_results = session.get_results()
    my_acquired_results = my_results.acquired_results['results']

    # plot measurement data
    drive_amp = my_acquired_results.axis[0]
    IQ_data = my_acquired_results.data
    amplitude = np.abs(IQ_data)
    phase = np.unwrap(np.angle(IQ_data))
    phase = phase #-np.mean(phase)

    fitting_plot_x = np.linspace(
        my_acquired_results.axis[0][0],
        my_acquired_results.axis[0][-1],
        501
    )

    try: popt_amp, pcov_amp = oscillatory.fit(drive_amp, amplitude, 10, 0, 0.5, 0)
    except: pass

    try: popt_phase, pcov_phase = oscillatory.fit(drive_amp, phase, 10, 0, 0.5, 0) #frequency, phase, amplitude, offset
    except: pass

    fig, ax = plt.subplots(2, 1, figsize=(8,6))
    ax[0].plot(drive_amp, amplitude)
    try: ax[0].plot(fitting_plot_x, oscillatory(fitting_plot_x, *popt_amp), '-r')
    except: pass
    ax[0].set_title(f'{qubit.uid} Amplitude Sweep')
    ax[0].set_xlabel('Rabi Pulse Amplitude')
    ax[0].set_ylabel('Amplitude (a.u.)')
    # ax[0].vlines(0.81, ymin=np.min(amplitude), ymax=np.max(amplitude), color='orange')
    # ax[0].vlines(0.32, ymin=np.min(amplitude), ymax=np.max(amplitude), color='orange')
    ax[0].grid()
    ax[1].plot(drive_amp, phase)
    try: ax[1].plot(fitting_plot_x, oscillatory(fitting_plot_x, *popt_phase), '-r')
    except: pass
    ax[1].set_title(f'{qubit.uid} Amplitude Sweep')
    ax[1].set_xlabel('Rabi Pulse Amplitude')
    ax[1].set_ylabel('Phase (a.u.)')
    # ax[1].vlines(qubit.parameters.user_defined['amplitude_pi']-0.01, ymin=np.min(phase), ymax=np.max(phase), color='orange')
    # ax[1].vlines(qubit.parameters.user_defined['amplitude_pi/2']-0.01, ymin=np.min(phase), ymax=np.max(phase), color='orange')
    ax[1].grid()
    fig.tight_layout()
    try: print(f"Fitted parameters (amplitude): {popt_amp}")
    except: pass
    try: print(f"Fitted parameters (phase): {popt_phase}")
    except: pass
    
    return fig, ax

def plot_T1_exp(exp, session, qubit, **kwargs):
    '''Plots a classic T1 exp'''
    my_results = session.get_results()
    my_acquired_results = my_results.acquired_results['results']

    time_delay = my_acquired_results.axis[0]
    delay_plot = np.linspace(time_delay[0], time_delay[-1], 501)

    amplitude = np.abs(my_acquired_results.data)
    phase = np.unwrap(np.angle(my_acquired_results.data))
    phase = phase - np.mean(phase)

    fig, ax = plt.subplots(1,1, figsize=(4,4))
    ax.plot(time_delay*1e6, phase, '.k')
    ax.set_title(f"{qubit.uid}'s T1")
    ax.set_xlabel('Delay (us)')
    ax.set_ylabel('Phase')
    ax.grid()

    try:
        popt, pcov = exponential_decay.fit(time_delay, phase, 1/50e-6, 0.08, 0.1, plot=False)
        ax.plot(delay_plot*1e6, exponential_decay(delay_plot, *popt), '-r');
        print(f"Fitted parameters: {popt}")
        print('T1 time ' + str(1/popt[0]*1e6) + ' us') 
    except:
        print('Could not find fit')



    return fig, ax

def plot_T2_star(exp, session, qubit, **kwargs):
    my_results = session.get_results()
    my_acquired_results = my_results.acquired_results['results']
    IQ_data = my_acquired_results.data
    amplitude = np.abs(IQ_data)
    phase = np.unwrap(np.angle(IQ_data))
    phase = phase-np.mean(phase)

    time_delay=my_acquired_results.axis[0]

    fitting_plot_x = np.linspace(time_delay[0], time_delay[-1], 501)

    try: popt_amp, pcov_amp = oscillatory_decay.fit(time_delay, amplitude, 2e6, 0, 1e5, 0.1, 3)
    except: pass

    try: popt_phase, pcov_phase = oscillatory_decay.fit(time_delay, phase, 1e6, 0, 1e6, 0.5, 0) #frequency, phase, decay_rate, amplitude, offset
    except: pass

    fig, ax = plt.subplots(2, 1, figsize=(8,6))
    ax[0].scatter(time_delay*1e6, amplitude)
    try: ax[0].plot(fitting_plot_x*1e6, oscillatory_decay(fitting_plot_x, *popt_amp), '-r')
    except: pass
    ax[0].set_title(f'{qubit.uid} Ramsey Oscillations')
    ax[0].set_xlabel('Time Delay (us)')
    ax[0].set_ylabel('Amplitude (a.u.)')
    ax[0].grid()
    ax[1].scatter(time_delay*1e6, phase)
    try: ax[1].plot(fitting_plot_x*1e6, oscillatory_decay(fitting_plot_x, *popt_phase), '-r')
    except: pass
    ax[1].set_title(f'{qubit.uid} Ramsey Oscillations')
    ax[1].set_xlabel('Time Delay (us)')
    ax[1].set_ylabel('Phase (a.u.)')
    ax[1].grid()
    fig.tight_layout()
    try:
        print(f"Fitted parameters (amplitude): {popt_amp}")
        print(f'detuning = {popt_amp[0]*1e-6} MHz, T2r = {1e6/popt_amp[2]} us')
    except: pass
    try:
        print(f"Fitted parameters (phase): {popt_phase}")
        print(f'detuning = {popt_phase[0]*1e-6} MHz, T2r = {1e6/popt_phase[2]} us')
    except: pass

    return fig, ax

def plot_T2_echo(exp, session, qubit, **kwargs):
    '''Plots single T2 Echo experiment'''
    my_results = session.get_results()
    my_acquired_results = my_results.acquired_results['results']

    IQ_data = my_acquired_results.data
    amplitude = np.abs(IQ_data)
    phase = np.unwrap(np.angle(IQ_data))
    phase = phase-np.mean(phase)
    time_delay = my_acquired_results.axis[0]

    fitting_plot_x = np.linspace(time_delay[0], time_delay[-1], 501)

    try: popt_amp, pcov_amp = exponential_decay.fit(time_delay, amplitude, 1e6, 0 , 1)
    except: pass

    try: popt_phase, pcov_phase = exponential_decay.fit(time_delay, phase, 1e6, 0, 1) #decay rate, offset, amplitude
    except: pass

    fig, ax = plt.subplots(2, 1, figsize=(4,8))
    ax[0].plot(time_delay*1e6, amplitude, '.k')
    try: ax[0].plot(fitting_plot_x*1e6, exponential_decay(fitting_plot_x, *popt_amp), '-r')
    except: pass
    ax[0].set_title(f'{qubit.uid} T2 Echo')
    ax[0].set_xlabel('Time Delay (us)')
    ax[0].set_ylabel('Amplitude (a.u.)')
    ax[0].grid()
    ax[1].plot(time_delay*1e6, phase, '.k')
    try: ax[1].plot(fitting_plot_x*1e6, exponential_decay(fitting_plot_x, *popt_phase), '-r')
    except: pass
    ax[1].set_title(f'{qubit.uid} T2 Echo')
    ax[1].set_xlabel('Time Delay (us)')
    ax[1].set_ylabel('Phase (a.u.)')
    ax[1].grid()
    fig.tight_layout()
    try:
        print(f"Fitted parameters (amplitude): {popt_amp}")
        print('T2e time ' + str(1/popt_amp[0]*1e6) + ' us') 
    except: pass
    try:
        print(f"Fitted parameters (phase): {popt_phase}")
        print('T2e time ' + str(1/popt_phase[0]*1e6) + ' us') 
    except: pass
    return fig, ax


def update_colorbar_limits(fig, new_min, new_max):
    """Update colorbar limits for a figure."""
    updated = False

    # Find and update mappable objects.
    for ax in fig.get_axes():
        for child in ax.get_children():
            if hasattr(child, 'set_clim'):
                child.set_clim(vmin=new_min, vmax=new_max)
                updated = True

    if updated:
        fig.canvas.draw_idle()

    return updated