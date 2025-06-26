from all_imports import *
from helper import *
from qops_helper import *
from qelement_helper import *
from yoko_helper import change_current

# NOTE: All dsl.qubit_experiments naturally update the qubit parameters with the qubit.calibration() method


# Defining experiments
@dsl.qubit_experiment(name='Local Resonator Trace')
def local_trace(
    q: QuantumElement,
    rel_left_rf, #neg
    rel_right_rf, #pos
    ro_range: int=None,
    trace_pts: int=101,
    averages: int=2**8,
    drive_on: bool=False,
    qops: dsl.QuantumOperations=CustomGeneralOperations(),
):
    '''
    A local trace centered about the stated resonator frequency in
    qubit.parameters.readout_resonator_frequency
    '''
    if ro_range is None:
        ro_range = q.parameters.readout_range_out

    ro_rf_center_frequency = (
        q.parameters.readout_resonator_frequency
        - q.parameters.readout_lo_frequency
    )
    left_rf = ro_rf_center_frequency + rel_left_rf
    right_rf = ro_rf_center_frequency + rel_right_rf
    
    ro_rf_freqs = np.linspace(left_rf, right_rf, trace_pts)
    ro_freq_sweep = SweepParameter('ro_freq_sweep', ro_rf_freqs) 
    active_exp_cal = dsl.experiment_calibration()
    active_exp_sig_cal = active_exp_cal[q.signals['measure']]
    active_exp_sig_cal.oscillator.frequency = ro_freq_sweep
    active_exp_sig_cal.range = ro_range

    with dsl.acquire_loop_rt(
        name='Real Time Loop',
        count=averages,
        acquisition_type=AcquisitionType.SPECTROSCOPY
    ):
        with dsl.sweep(
            name='Readout Frequency Sweep',
            parameter=ro_freq_sweep,
        ):
            if drive_on is True:
                qops.arbitrary_drive(q, 'arb drive')
            qops.measure(q, 'results')
    return

@dsl.qubit_experiment(name='Global Trace')
def global_trace(
    q: QuantumElement,
    trace_pts: int=201,
    averages: int=2**8,
    qops: dsl.QuantumOperations = CustomGeneralOperations()
):
    '''
    A global trace which spans from 500MHz to 8.5GHz. trace_pts are for each 1GHz lo band.
    No client-facing customizability.
    '''
    
    ro_lo_sweep = dsl.LinearSweepParameter(
        axis_name='ro lo sweep',
        start=4e9,
        stop=8e9,
        count=5
    )
    ro_rf_sweep = dsl.LinearSweepParameter(
        axis_name='ro rf sweep',
        start=-500e6,
        stop=500e6,
        count=trace_pts
    )
    
    active_exp_cal = dsl.experiment_calibration()
    active_exp_sig_cal = active_exp_cal[q.signals['measure']]
    active_exp_sig_cal.local_oscillator.frequency = ro_lo_sweep
    active_exp_sig_cal.oscillator.frequency = ro_rf_sweep
    active_exp_sig_cal.range = 0

    with dsl.sweep(
        name='Readout LO Sweep',
        parameter=ro_lo_sweep
    ):
        with dsl.acquire_loop_rt(
            name='Real Time Loop',
            count=averages,
            acquisition_type=AcquisitionType.SPECTROSCOPY
        ):
            with dsl.sweep(
                name='Readout RF Sweep',
                parameter=ro_rf_sweep
            ):
                qops.measure(q, 'results')
    return

@dsl.qubit_experiment(name='Punchout')
def punchout(
    q: QuantumElement,
    ro_range_max: int,
    center_ro_freq=None,
    rel_ro_left_rf=-10e6,
    rel_ro_right_rf=10e6,
    lower_power=-1.5,
    higher_power=0,
    power_pts=10,
    ro_pts=51,
    averages=2**8,
    qops: dsl.QuantumOperations=CustomGeneralOperations(),
):
    ''' Typical punchout '''
    
    if center_ro_freq is None:
        center_ro_freq=q.parameters.readout_resonator_frequency
        
    # Round center ro_freq to set lo
    ro_lo_frequency = int(center_ro_freq/0.2e9)*0.2e9
    ro_rf_center_frequency = (center_ro_freq-ro_lo_frequency)
    left_rf = ro_rf_center_frequency + rel_ro_left_rf
    right_rf = ro_rf_center_frequency + rel_ro_right_rf

    ro_rf_freqs = np.linspace(left_rf, right_rf, ro_pts)
    ro_freq_sweep = SweepParameter('ro_freq_sweep', ro_rf_freqs)

    power_sweep = SweepParameter(
        uid='Readout_Power',
        values=np.logspace(start=lower_power,stop=higher_power,num=power_pts, base=10))

    # Calibration
    active_exp_cal = dsl.experiment_calibration()
    active_exp_sig_cal = active_exp_cal[q.signals['measure']]
    active_exp_sig_cal.local_oscillator.frequency = ro_lo_frequency
    active_exp_sig_cal.oscillator.frequency = ro_freq_sweep
    active_exp_sig_cal.range = ro_range_max

    with dsl.sweep(
        name='Power sweep',
        parameter=power_sweep
    ):
        with dsl.acquire_loop_rt(
            name='Real Time Loop',
            count=averages,
            acquisition_type=AcquisitionType.SPECTROSCOPY
        ):
           with dsl.sweep(
                name='Readout Frequency Sweep',
                parameter=ro_freq_sweep,
            ):
                qops.measure(q, 'results', amplitude=power_sweep)
    return

            
@dsl.qubit_experiment(name='Flux Sweep Trace')
def flux_sweep_trace(
    q: QuantumElement,
    yoko_dict_key: str,
    center_ro_freq=None,
    rel_ro_left_rf=-10e6,
    rel_ro_right_rf=10e6,
    left_current=-100e-6,
    right_current=100e-6,
    current_pts=101,
    trace_pts=101,
    averages=2**8,
    silence=True,
    qops: dsl.QuantumOperations=CustomGeneralOperations(),
):
    '''
    An experiment which sweeps a single yoko and sweeps the ro frequency to
    track the resonator's response. 2D results.
    '''
    
    if center_ro_freq is None:
        center_ro_freq=q.parameters.readout_resonator_frequency
    
    # Round center ro_freq to set lo
    ro_lo_frequency = int(center_ro_freq/0.2e9)*0.2e9
    ro_rf_center_frequency = (center_ro_freq-ro_lo_frequency)
    left_rf = ro_rf_center_frequency + rel_ro_left_rf
    right_rf = ro_rf_center_frequency + rel_ro_right_rf

    ro_rf_freqs = np.linspace(left_rf, right_rf, trace_pts)
    ro_freq_sweep = SweepParameter('ro_freq_sweep', ro_rf_freqs)

    current_sweep = LinearSweepParameter(
        f'Sweeping {yoko_dict_key}',
        left_current,
        right_current,
        current_pts
    )
                                         
    active_exp_cal = dsl.experiment_calibration()
    active_exp_sig_cal = active_exp_cal[q.signals['measure']]
    active_exp_sig_cal.local_oscillator.frequency = ro_lo_frequency
    active_exp_sig_cal.oscillator.frequency = ro_freq_sweep

    with dsl.sweep(
        name=f'Current Sweep of {yoko_dict_key}',
        parameter=current_sweep
    ):
        dsl.call(
            change_current,
            yoko_dict_key=yoko_dict_key,
            current_setpoint=current_sweep,
            step_time=0.01,
            silence=silence
        )
        with dsl.acquire_loop_rt(
            name='Real Time Loop',
            count=averages,
            acquisition_type=AcquisitionType.SPECTROSCOPY
        ):
            with dsl.sweep(
                name='Readout Frequency Sweep',
                parameter=ro_freq_sweep,
            ):
                qops.measure(q, 'results')
    return

@dsl.qubit_experiment(name='Flux Sweep Spectrum')
def flux_sweep_spectrum(
    q: QuantumElement,
    yoko_dict_key: str,
    center_drive_freq,
    rel_drive_left_rf,
    rel_drive_right_rf,
    left_current,
    right_current,
    current_pts,
    drive_pts,
    averages=2**8,
    silence=True,
    qops: dsl.QuantumOperations=CustomGeneralOperations()
):
    '''
    An experiment which uses a pre-defined map_flux_to_ro_freq function to set
    the readout frequency while sweeping the drive range and currents.
    If no mapping is provided, a warning will be printed but the default
    readout resonator frequency will be used instead.

    Can only sweep rf range.
    
    2D results.
    '''
    if q.parameters.res_to_current == None:
        print('WARNING: Not using a current to readout frequency mapping. Instead using the qubit default readout value')
        def current_ro_mapping(current):
            return q.parameters.readout_resonator_frequency
    else:
        print('Using res_to_current mapping')
        def current_ro_mapping(current):
            return q.parameters.res_to_current(current)

    drive_lo_frequency = int(center_drive_freq/0.2e9)*0.2e9
    drive_rf_center_frequency = (center_drive_freq-drive_lo_frequency)
    left_rf = drive_rf_center_frequency + rel_drive_left_rf
    right_rf = drive_rf_center_frequency + rel_drive_right_rf

    drive_freq_sweep = LinearSweepParameter(
        uid='Drive_Sweep',
        start=left_rf,
        stop=right_rf,
        count=drive_pts
    )
    current_sweep = LinearSweepParameter(
        f'Sweeping {yoko_dict_key}',
        left_current,
        right_current,
        current_pts
    )
    ro_rf_values = current_ro_mapping(current_sweep.values)
    ro_rf_sweep = SweepParameter('Readout Frequency Sweep', ro_rf_values)

    active_exp_cal = dsl.experiment_calibration()
    # active_exp_cal[q.signals['measure']].oscillator.frequency = ro_rf_sweep
    active_exp_cal[q.signals['acquire']].oscillator.frequency = ro_rf_sweep
    active_exp_cal[q.signals['drive']].local_oscillator.frequency = drive_lo_frequency
    active_exp_cal[q.signals['drive']].oscillator.frequency = drive_freq_sweep

    with dsl.sweep(
        name=f'Current Sweep of {yoko_dict_key}',
        parameter=[current_sweep, ro_rf_sweep],
    ):
        dsl.call(
            change_current,
            yoko_dict_key=yoko_dict_key,
            current_setpoint=current_sweep,
            step_time=0.01,
            silence=silence
        )
        with dsl.acquire_loop_rt(
            name='Real Time Loop',
            count=averages,
            acquisition_type=AcquisitionType.SPECTROSCOPY,
        ):
            with dsl.sweep(
                name='Drive Frequency Sweep',
                parameter=drive_freq_sweep,
            ):
                qops.arbitrary_drive(q, 'drive')
                qops.measure(q, 'results')
    return
                     
@dsl.qubit_experiment
def null_qubit_experiment(q):
    '''A completely empty qubit experiment. Used for debugging'''
    pass

@dsl.qubit_experiment(name='Simple Spectrum')
def sweep_spectrum(
    q: QuantumElement,
    yoko_dict_key: str,
    rel_drive_left_rf,
    rel_drive_right_rf,
    drive_pts,
    center_drive_freq=None,
    averages=2**8,
    qops: dsl.QuantumOperations=CustomGeneralOperations()
):
    '''
    A simple spectrum experiment
    '''

    if center_drive_freq is None:
        center_drive_freq = q.parameters.resonance_frequency_ge

    drive_lo_frequency = int(center_drive_freq/0.2e9)*0.2e9
    drive_rf_center_frequency = (center_drive_freq-drive_lo_frequency)
    left_rf = drive_rf_center_frequency + rel_drive_left_rf
    right_rf = drive_rf_center_frequency + rel_drive_right_rf

    drive_freq_sweep = LinearSweepParameter(
        uid='Drive_Sweep',
        start=left_rf,
        stop=right_rf,
        count=drive_pts
    )
    
    # Calibration
    active_exp_cal = dsl.experiment_calibration()
    if not hasattr(q, 'parameters.current_setpoint'):
        pass
    elif not hasattr(q.current_ro_mapping):
        print('WARNING: Not using a current to readout frequency mapping for a flux sensitive qubit')
    else:
        ro_rf_values = q.current_ro_mapping(yoko_dict[yoko_dict_key].current.get())
        active_exp_cal[q.signals['measure']].oscillator.frequency = ro_rf_values
    
    active_exp_cal[q.signals['drive']].local_oscillator.frequency = drive_lo_frequency
    active_exp_cal[q.signals['drive']].oscillator.frequency = drive_freq_sweep

    with dsl.acquire_loop_rt(
        name='Real Time Loop',
        count=averages,
        acquisition_type=AcquisitionType.SPECTROSCOPY,
    ):
        with dsl.sweep(
            name='Drive Frequency Sweep',
            parameter=drive_freq_sweep,
        ):
            qops.arbitrary_drive(q, 'drive')
            qops.measure(q, 'results')
    return

@dsl.qubit_experiment(name='Fast Flux Calibration')
def fast_flux_calib(
    q: QuantumElement,
):
    '''An experiment for calibrating the fast flux pulse procedure'''
    pass

@dsl.qubit_experiment(name='Fast Flux Drive Pulse')
def fast_flux_drive_pulse(
    q: QuantumElement,
):
    '''An experiment which drives while a calibrated fast flux pulse is active'''
    pass

@dsl.qubit_experiment(name='2D Flux Sweep')
def dual_flux_sweep(
    q: QuantumElement,
):
    '''An experiment which does a 2D sweep of yokos'''
    pass

@dsl.qubit_experiment(name='X90 Tuneup')
def X90_tuneup(
    q: QuantumElement,
):
    '''A amplitude sweep to calibrate an X90 pulse'''
    pass

@dsl.qubit_experiment(name='T1')
def T1(
    q: QuantumElement,
):
    '''A simple T1 experiment given a calibrated X90'''
    pass

# TODO: Refine existing functions (appropriately sets current setpoint etc etc)
# TODO: Add resonator tracking
# TODO: Add simple standard saving (like before) to each experiment