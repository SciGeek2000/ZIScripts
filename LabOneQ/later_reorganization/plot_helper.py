# This should be basically a match case of all the possible expermient types, while returning the ax, fig
from all_imports import *
from helper import *
from qelement_helper import *
from qops_helper import *
from qubit_experiments import *

def plot_exp(exp: Experiment, session: Session, qubit, **kwargs):
    match exp.uid:
        case 'Local Resonator Trace':
            fig, ax = plot_local_resonator_trace(exp, session, qubit, **kwargs)
            return fig, ax
        case 'Global Trace':
            fig, ax = plot_global_resonator_trace(exp, session, qubit, **kwargs)
            return fig, ax
        case 'Punchout':
            fig, ax = plot_punchout(exp, session, qubit, **kwargs)
            return fig, ax
        case 'Simple Spectrum':
            fig, ax = plot_simple_spectrum(exp, session, qubit, **kwargs)
            return fig, ax
        case 'Flux Sweep Trace':
            fig, ax = plot_flux_sweep_trace(exp, session, qubit, **kwargs)
            return fig, ax
        case 'Flux Sweep Spectrum':
            fig, ax = plot_flux_sweep_spectrum(exp, session, qubit, **kwargs)
            return fig, ax
        case '2D Flux Sweep':
            fig, ax = plot_dual_flux_sweep(exp, session, qubit, **kwargs)
            return fig, ax

def plot_local_resonator_trace(exp, session, qubit):
    # TODO: Would be nice for this to just be independent of qubit so that it truly is displaying what occured
    my_results = session.get_results() #a deep copy of session.results

    # Extracts data from the exp.acquire method with the same key name
    my_acquired_results = my_results.acquired_results['results']

    # For plotting current vs single resonator point
    freqs = my_acquired_results.axis[0] + qubit.parameters.readout_lo_frequency
    IQ_data = my_acquired_results.data
    amplitude = np.abs(IQ_data)
    phase = adjust_phase(IQ_data, freqs, qubit.parameters.readout_integration_delay)

    # Plots
    fig, ax = plt.subplots(2,1, figsize=(8,6))
    ax[0].plot(freqs, amplitude)
    ax[0].set_title(f'{qubit.uid} Near Resonator Pulsed Trace')
    ax[0].set_xlabel('Frequency (GHz)')
    ax[0].set_ylabel('Amplitude (a.u.)')
    ax[0].grid()
    ax[1].plot(freqs, phase)
    ax[1].set_title(f'{qubit.uid} Near Resonator Pulsed Trace')
    ax[1].set_xlabel('Frequency (GHz)')
    ax[1].set_ylabel('Phase')
    ax[1].grid()
    fig.tight_layout()
    return fig, ax

def plot_global_resonator_trace(exp, session, qubit):
    my_results = session.get_results() #a deep copy of session.results
    # Extracts data from the exp.acquire method with the same key name
    my_acquired_results = my_results.acquired_results['results']
    
    lo_array = my_acquired_results.axis[0]
    AWG_freqs = my_acquired_results.axis[1]
    freqs = np.empty((0))
    for lo in lo_array:
        freqs = np.append(freqs, lo + AWG_freqs,)
    IQ_data = my_acquired_results.data.ravel()
    amplitude = np.abs(IQ_data)
    phase = adjust_phase(IQ_data, freqs, qubit.parameters.readout_integration_delay)

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

def plot_punchout(exp, session, qubit, data_type:str='Phase'):
    my_results = session.get_results() #a deep copy of session.results
    # Extracts data from the exp.acquire method with the same key name
    my_acquired_results = my_results.acquired_results['results']

    # For plotting punchout
    freqs = my_acquired_results.axis[1]+exp.signals[f'{qubit.uid}/measure_line'].calibration.local_oscillator.frequency
    IQ_data = my_acquired_results.data
    normalized_amp_data = np.divide(np.abs(IQ_data).T, np.mean(np.abs(IQ_data), axis=1))
    normalized_dB_data = np.log10(normalized_amp_data)
    phase = adjust_phase(IQ_data, freqs, qubit.parameters.readout_integration_delay)

    amplitude = my_acquired_results.axis[0]
    power = 10*np.log10(amplitude**2)+exp.signals[f'{qubit.uid}/measure_line'].calibration.range

    if data_type=='Phase':
        graphing_data = normalized_dB_data
    elif data_type=='Amplitude':
        graphing_data = phase.T
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

def plot_flux_sweep_trace(exp, session, qubit):
    my_results = session.get_results() #a deep copy of session.results
    # Extracts data from the exp.acquire method with the same key name
    my_acquired_results = my_results.acquired_results['results']
    # For plotting current vs single resonator point
    # For plotting 1D flux sweep
    freqs = my_acquired_results.axis[1] + exp.signals[f'{qubit.uid}/measure_line'].calibration.local_oscillator.frequency
    IQ_data = my_acquired_results.data
    amplitude = np.abs(IQ_data)
    phase = adjust_phase(IQ_data, freqs, qubit.parameters.readout_integration_delay)
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

def plot_flux_sweep_spectrum(exp, session, qubit, **kwargs):
    '''Plots a flux sweep spectrum'''
    my_results = session.get_results() #a deep copy of session.results
    # Extracts data from the exp.acquire method with the same key name
    my_acquired_results = my_results.acquired_results['results']
    print(my_acquired_results.axis_name)
    currents = my_acquired_results.axis[0][0]
    data = my_acquired_results.data
    freqs = my_acquired_results.axis[1]+exp.signals[f'{qubit.uid}/drive_line'].calibration.local_oscillator.frequency
    # freqs = np.tile(freqs, (201, 1)).T
    # print(freqs[0,:])
    IQ_data = data
    amplitude = np.abs(IQ_data)
    # phase = adjust_phase(IQ_data, freqs, qubit.parameters.readout_integration_delay)
    phase = np.unwrap(np.angle(IQ_data))
    phase = phase - np.mean(phase, axis=1)[:, None]
    fig, ax = plt.subplots(1,2, figsize=(16,9))
    cmap0 = ax[0].pcolor(currents*1e6,
        freqs,
        amplitude.T,
        shading='nearest',)
        # vmax=3)
        # vmax=0.5)
        # vmin=0,
        # vmax=1)
    ax[0].set_title(f'{qubit.uid} Two Tone Spectroscopy')
    ax[0].set_xlabel('Currents (uA)')
    ax[0].set_ylabel('Drive Frequency (GHz)')
    cmap1 = ax[1].pcolor(currents*1e6,
        freqs,
        phase.T,
        shading='nearest',)
        # vmin=,
        # vmax=
    # ax[0].axvline(x=-25, color='red', linestyle='--', linewidth=2)
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
    ax[0].set_xlabel(f'{outer_name} (uA)')
    ax[0].set_ylabel(f'{inner_name} (uA)')
    cmap1 = ax[1].pcolor(outer_currents*1e6,
                inner_current*1e6,
                phase_data.T,
                shading='nearest')
    ax[1].set_title(f'{qubit.uid} Resonator 2D Flux Response')
    ax[1].set_xlabel(f'{outer_name} (uA)')
    ax[1].set_ylabel(f'{inner_name} (uA)')
    fig.colorbar(cmap0, ax=ax[0])
    fig.colorbar(cmap1, ax=ax[1])
    fig.tight_layout()

    return fig, ax