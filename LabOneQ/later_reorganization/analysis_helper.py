from helper import *
from qelement_helper import *
from qops_helper import *
from qubit_experiments import *
from scipy.optimize import curve_fit
import dill

def exp_analysis(exp: Experiment, session: Session, qubit, **kwargs):
    match exp.uid:
        case 'Flux Sweep Trace':
            analysis = analyze_flux_sweep_trace(exp, session, qubit, **kwargs)
            return analysis
        
def analyze_flux_sweep_trace(exp, session, qubit, **kwargs): # [ ] Normalize amplitude at each frequency value
    '''
    Returns a dictionary with amplitude and phase fits that map
    the current to the resonator's frequency
    '''
    my_results = session.get_results() # a deep copy of session.results
    my_acquired_results = my_results.acquired_results['results']
    freqs = my_acquired_results.axis[1] + exp.signals[f'{qubit.uid}/measure_line'].calibration.local_oscillator.frequency
    IQ_data = my_acquired_results.data
    amplitude = np.abs(IQ_data)
    phase = adjust_phase(IQ_data, freqs, exp.signals[f'{qubit.uid}/acquire_line'].calibration.port_delay)
    currents = my_acquired_results.axis[0]*1e6
    tracked_resonator = np.empty(amplitude.shape[0])

    def arctan_fit(freqs, omega, phs_offset, offset):
        '''Rough phase fitting after normalizing avg phase amplitude to zero'''
        phs_offset = phs_offset*1e9
        return 2*np.arctan(omega*(freqs-phs_offset)) + offset

    def make_ro_freq():
        '''A closure for new_ro_values which is to be assigned to a qubit'''
        old_currents = my_acquired_results.axis[0]
        old_values = tracked_resonator
        def res_to_current(new_currents: float|np.ndarray):
            new_ro_values = np.interp(new_currents, old_currents, old_values)
            return new_ro_values
        return res_to_current

    # for i, phs in enumerate(phase):
    #     try:
    #         (popt, b) = curve_fit(arctan_fit, freqs, phs, p0=[50e6, 6.8675e9/1e9, 1], bounds=([-np.inf, 1e9/1e9, -np.inf], [np.inf, 9e9/1e9, np.inf]),)
    #         opt_freq = popt[1]*1e9
    #         tracked_resonator[i] = opt_freq
    #     except Exception as e:
    #         tracked_resonator[i] = tracked_resonator[i-1]
    #         print(e)
    
    # Temporary solution is just picking out the argmin
    for i, amp in enumerate(amplitude):
        try:
            # (popt, b) = lorentzian.fit(freqs, amp, 1000e3, exp.signals[f'{qubit.uid}/measure_line'].calibration.local_oscillator.frequency, -1e7, 1)
            # opt_freq = popt[1]
            opt_freq = freqs[np.argmin(amp)]
            tracked_resonator[i] = opt_freq
        except Exception as e:
            tracked_resonator[i] = tracked_resonator[i-1]
            print(e)

    qubit.parameters.res_to_current = make_ro_freq()

    plt.scatter(currents, tracked_resonator) # [ ] It is currently plotting on phase even though it is argmin of amplitude for fitting
    # plt.ylim(6.8e9, 6.9e9)

    if 'save' in kwargs and kwargs['save'] is True:
        with open(f'make_ro_freq', 'wb') as f:
            dill.dump(make_ro_freq, f)

    return None
