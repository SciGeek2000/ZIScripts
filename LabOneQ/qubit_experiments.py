from all_imports import *
from helper import *
from qops_helper import *
from qelement_helper import *
from yoko_helper import change_current, get_current

# NOTE: All dsl.qubit_experiments naturally update the qubit parameters with the qubit.calibration() method

# -- Defining experiments --
@dsl.qubit_experiment(name='Local Resonator Trace')
def local_trace(
    q: QuantumElement,
    rel_left_rf, #neg
    rel_right_rf, #pos
    ro_range: int=None,
    trace_pts: int=101,
    averages: int=2**8,
    drive_on: bool=False,
    yoko_dict_key: str=None,
    qops: dsl.QuantumOperations=CustomGeneralOperations(),
):
    '''
    A local trace centered about the stated resonator frequency in
    qubit.parameters.readout_resonator_frequency
    '''
    if ro_range is None:
        ro_range = q.parameters.readout_range_out
    
    if hasattr(q.parameters, 'res_to_current') is False:
        print('Does not have a res_to_current')
        ro_frequency = q.parameters.readout_resonator_frequency
    elif q.parameters.res_to_current is None:
        print('Not using current mapping')
        ro_frequency = q.parameters.readout_resonator_frequency
    elif yoko_dict_key is None:
        print('WARNING: did not provide a yoko_dict_key keyword so using default readout_resonator_frequency')
        ro_frequency = q.parameters.readout_resonator_frequency
    elif q.parameters.flux_sweetspot is None:
        print('Using current mapping at current current')
        ro_frequency = q.parameters.res_to_current(get_current(yoko_dict_key))
    elif q.parameters.flux_sweetspot is not None:
        print('Using current mapping at sweepspot current')
        _ = None
        change_current(_, yoko_dict_key, q.parameters.flux_sweetspot, 0.01)
        ro_frequency = q.parameters.res_to_current(get_current(yoko_dict_key))

    ro_rf_center_frequency = (
        ro_frequency
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
        acquisition_type=AcquisitionType.SPECTROSCOPY,
        
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
    
    ro_lo_sweep = LinearSweepParameter(
        axis_name='ro lo sweep',
        start=4e9,
        stop=8e9,
        count=5,
    )
    ro_rf_sweep = LinearSweepParameter(
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

@dsl.qubit_experiment(name='Full Spectrum')
def full_spectrum(
    q: QuantumElement,
    yoko_dict_key: str,
    drive_pts,
    averages=2**8,
    t_delay=5e-6,
    qops: dsl.QuantumOperations=CustomGeneralOperations()
):
    '''
    Goes from LF to RF freqs
    '''

    active_exp_cal = dsl.experiment_calibration()

    if hasattr(q.parameters, 'res_to_current') is False:
        print('Does not have a res_to_current')
        pass
    elif q.parameters.res_to_current is None:
        print('Not using current mapping')
    elif q.parameters.flux_sweetspot is None:
        print('Using current mapping at current current')
        ro_frequency = q.parameters.res_to_current(get_current(yoko_dict_key))
        ro_rf_frequency = ro_frequency - q.parameters.readout_lo_frequency
        active_exp_cal[q.signals['measure']].oscillator.frequency = ro_rf_frequency
    elif q.parameters.flux_sweetspot is not None:
        print('Using current mapping at sweepspot current')
        change_current(dsl.active_session(), yoko_dict_key, q.parameters.flux_sweetspot, 0.01)
        ro_frequency = q.parameters.res_to_current(get_current(yoko_dict_key))
        ro_rf_frequency = ro_frequency - q.parameters.readout_lo_frequency
        active_exp_cal[q.signals['measure']].oscillator.frequency = ro_rf_frequency

    drive_lo_sweep = LinearSweepParameter(
        axis_name='Drive LO Sweep',
        start=1e9,
        stop=9e9,
        count=9,
    )

    drive_rf_sweep = LinearSweepParameter(
        axis_name='Drive RF Sweep',
        start=-500e6,
        stop=500e6,
        count=drive_pts,
    )

    active_exp_cal[q.signals['drive']].local_oscillator.frequency = drive_lo_sweep
    active_exp_cal[q.signals['drive']].oscillator.frequency = drive_rf_sweep

    # NT_Section = AcquireLoopNt(count=3, averaging_mode=AveragingMode.CYCLIC)
    
    with dsl.sweep(
        name='Drive LO Sweep',
        parameter=drive_lo_sweep,
    ):
        with dsl.acquire_loop_rt(
            name='Real Time Loop',
            count=averages,
            acquisition_type=AcquisitionType.INTEGRATION,
            averaging_mode=AveragingMode.CYCLIC,
        ):
            with dsl.sweep(
                name='Drive RF Sweep',
                parameter=drive_rf_sweep
            ):
                qops.arbitrary_drive(q, 'drive')
                qops.measure(q, 'results', t_delay=t_delay)
    return

@dsl.qubit_experiment(name='Simple Spectrum')
def sweep_spectrum(
    q: QuantumElement,
    yoko_dict_key: str,
    rel_drive_left_rf,
    rel_drive_right_rf,
    drive_pts,
    t_delay=1e-6,
    center_drive_freq=None,
    averages=2**8,
    drive_length=200e-6,
    qops: dsl.QuantumOperations=CustomGeneralOperations()
):
    '''
    A simple spectrum experiment
    '''
    active_exp_cal = dsl.experiment_calibration()

    # Track resonator if flux dependent
    if hasattr(q.parameters, 'res_to_current') is False:
        print('Does not have a res_to_current')
        pass
    elif q.parameters.res_to_current is None:
        print('Not using current mapping')
    elif q.parameters.flux_sweetspot is None:
        print('Using current mapping at current current')
        ro_frequency = q.parameters.res_to_current(get_current(yoko_dict_key))
        ro_rf_frequency = ro_frequency - q.parameters.readout_lo_frequency
        active_exp_cal[q.signals['measure']].oscillator.frequency = ro_rf_frequency
    elif q.parameters.flux_sweetspot is not None:
        print('Using current mapping at sweepspot current')
        _ = None
        change_current(_, yoko_dict_key, q.parameters.flux_sweetspot, 0.01)
        ro_frequency = q.parameters.res_to_current(get_current(yoko_dict_key))
        ro_rf_frequency = ro_frequency - q.parameters.readout_lo_frequency
        active_exp_cal[q.signals['measure']].oscillator.frequency = ro_rf_frequency

    if center_drive_freq is None:
        center_drive_freq = q.parameters.resonance_frequency_ge

    # Configure drive for LF or RF mode as necessary
    if center_drive_freq > 1e9:
        drive_lo_frequency = int(center_drive_freq/0.2e9)*0.2e9
        drive_rf_center_frequency = (center_drive_freq-drive_lo_frequency)
    elif center_drive_freq < 1e9:
        active_exp_cal[q.signals['drive']].port_mode = PortMode.LF
        drive_lo_frequency = 0
        drive_rf_center_frequency = center_drive_freq

    left_rf = drive_rf_center_frequency + rel_drive_left_rf
    right_rf = drive_rf_center_frequency + rel_drive_right_rf

    # Setup drive sweep
    drive_freq_sweep = LinearSweepParameter(
        uid='Drive_Sweep',
        start=left_rf,
        stop=right_rf,
        count=drive_pts
    )
    
    active_exp_cal[q.signals['drive']].local_oscillator.frequency = drive_lo_frequency
    active_exp_cal[q.signals['drive']].oscillator.frequency = drive_freq_sweep

    with dsl.acquire_loop_rt(
        name='Real Time Loop',
        count=averages,
        # acquisition_type=AcquisitionType.SPECTROSCOPY, # These both work roughly equally well here
        acquisition_type=AcquisitionType.INTEGRATION, # Technically the above could be used for continuous drives
        averaging_mode=AveragingMode.CYCLIC,
    ):
        with dsl.sweep(
            name='Drive Frequency Sweep',
            parameter=drive_freq_sweep,
        ):
            qops.arbitrary_drive(q, 'drive', length=drive_length)
            qops.measure(q, 'results', t_delay=t_delay)
    return

@dsl.qubit_experiment(name='Flux Sweep Full Spectrum')
def flux_sweep_full_spectrum(
    q: QuantumElement,
    yoko_dict_key: str,
    left_current,
    right_current,
    current_pts,
    drive_pts,
    averages=2**8,
    t_delay=5e-6,
    silence=False,
    qops: dsl.QuantumOperations=CustomGeneralOperations()
):
    '''
    Goes from LF to RF freqs
    '''

    active_exp_cal = dsl.experiment_calibration()

    # [ ] TODO: This paragraph can very likely be deleted, since a flux sweep is assumed to be without this
    if hasattr(q.parameters, 'res_to_current') is False:
        print('Does not have a res_to_current')
        pass
    elif q.parameters.res_to_current is None:
        print('Not using current mapping')
    elif q.parameters.flux_sweetspot is None:
        print('Using current mapping at current current')
        ro_frequency = q.parameters.res_to_current(get_current(yoko_dict_key))
        ro_rf_frequency = ro_frequency - q.parameters.readout_lo_frequency
        active_exp_cal[q.signals['measure']].oscillator.frequency = ro_rf_frequency
    elif q.parameters.flux_sweetspot is not None:
        print('Using current mapping at sweepspot current')
        change_current(dsl.active_session(), yoko_dict_key, q.parameters.flux_sweetspot, 0.01)
        ro_frequency = q.parameters.res_to_current(get_current(yoko_dict_key))
        ro_rf_frequency = ro_frequency - q.parameters.readout_lo_frequency
        active_exp_cal[q.signals['measure']].oscillator.frequency = ro_rf_frequency

    current_values = np.linspace(left_current, right_current, current_pts)
    ro_rf_values = q.parameters.res_to_current(current_values) - q.parameters.readout_lo_frequency

    current_sweep = SweepParameter(
        axis_name='Current Sweep',
        values=current_values,
    )

    ro_rf_sweep = SweepParameter(
        axis_name='Readout Frequency Sweep',
        values=ro_rf_values,
    )

    drive_lo_sweep = LinearSweepParameter(
        axis_name='Drive LO Sweep',
        start=1e9,
        stop=9e9,
        count=9,
    )

    drive_rf_sweep = LinearSweepParameter(
        axis_name='Drive RF Sweep',
        start=-500e6,
        stop=500e6,
        count=drive_pts,
    )

    active_exp_cal[q.signals['drive']].local_oscillator.frequency = drive_lo_sweep
    active_exp_cal[q.signals['drive']].oscillator.frequency = drive_rf_sweep
    active_exp_cal[q.signals['measure']].oscillator.frequency = ro_rf_sweep

    
    with dsl.sweep(
        name='Current/RO Sweep',
        parameter=[current_sweep, ro_rf_sweep],
    ):
        dsl.call(
            change_current,
            yoko_dict_key=yoko_dict_key,
            current_setpoint=current_sweep,
            step_time=0.01,
            silence=silence,
        )
        with dsl.sweep(
            name='Drive LO Sweep',
            parameter=drive_lo_sweep,
        ):
            with dsl.acquire_loop_rt(
                name='Real Time Loop',
                count=averages,
                acquisition_type=AcquisitionType.INTEGRATION,
                averaging_mode=AveragingMode.CYCLIC,
            ):
                with dsl.sweep(
                    name='Drive RF Sweep',
                    parameter=drive_rf_sweep
                ):
                    qops.arbitrary_drive(q, 'drive')
                    qops.measure(q, 'results', t_delay=t_delay)
    return

@dsl.qubit_experiment(name='Flux Sweep Spectrum')
def flux_sweep_spectrum(
    q: QuantumElement,
    yoko_dict_key: str,
    left_current,
    right_current,
    current_pts,
    rel_drive_left_rf,
    rel_drive_right_rf,
    drive_pts,
    t_delay=1e-6,
    center_drive_freq=None,
    averages=2**8,
    LF_mode = False,
    silence=False,
    qops: dsl.QuantumOperations=CustomGeneralOperations()
):
    '''
    A simple spectrum experiment
    '''

    active_exp_cal = dsl.experiment_calibration()

    if center_drive_freq is None:
        center_drive_freq = q.parameters.resonance_frequency_ge

    # Configure drive for LF or RF mode as necessary
    if center_drive_freq > 1e9:
        drive_lo_frequency = int(center_drive_freq/0.2e9)*0.2e9
        drive_rf_center_frequency = (center_drive_freq-drive_lo_frequency)
    elif center_drive_freq < 1e9:
        active_exp_cal[q.signals['drive']].port_mode = PortMode.LF
        drive_lo_frequency = 0
        drive_rf_center_frequency = center_drive_freq

    left_rf = drive_rf_center_frequency + rel_drive_left_rf
    right_rf = drive_rf_center_frequency + rel_drive_right_rf

    current_values = np.linspace(left_current, right_current, current_pts)
    ro_rf_values = q.parameters.res_to_current(current_values) - q.parameters.readout_lo_frequency

    current_sweep = SweepParameter(
        axis_name='Current Sweep',
        values=current_values,
    )

    ro_rf_sweep = SweepParameter(
        axis_name='Readout Frequency Sweep',
        values=ro_rf_values,
    )

    # Setup drive sweep
    drive_freq_sweep = LinearSweepParameter(
        uid='Drive_Sweep',
        start=left_rf,
        stop=right_rf,
        count=drive_pts
    )
    
    active_exp_cal[q.signals['drive']].local_oscillator.frequency = drive_lo_frequency
    active_exp_cal[q.signals['drive']].oscillator.frequency = drive_freq_sweep
    active_exp_cal[q.signals['measure']].oscillator.frequency = ro_rf_sweep

    with dsl.sweep(
        name='Current/RO Sweep',
        parameter=[current_sweep, ro_rf_sweep],
    ):
        dsl.call(
            change_current,
            yoko_dict_key=yoko_dict_key,
            current_setpoint=current_sweep,
            step_time=0.01,
            silence=silence,
        )
        with dsl.acquire_loop_rt(
            name='Real Time Loop',
            count=averages,
            # acquisition_type=AcquisitionType.SPECTROSCOPY, # These both work roughly equally well here
            acquisition_type=AcquisitionType.INTEGRATION, # Technically the above could be used for continuous drives
            averaging_mode=AveragingMode.CYCLIC,
        ):
            with dsl.sweep(
                name='Drive Frequency Sweep',
                parameter=drive_freq_sweep,
            ):
                qops.arbitrary_drive(q, 'drive')
                qops.measure(q, 'results', t_delay=t_delay)
        return

@dsl.qubit_experiment(name='2D Flux Sweep')
def dual_flux_sweep(
    q: QuantumElement,
    yoko_dict_key_outer: str,
    yoko_dict_key_inner: str,
    outer_left_current,
    outer_right_current,
    outer_current_count,
    inner_left_current,
    inner_right_current,
    inner_current_count,
    averages=2**6,
    silence=False,
    qops: dsl.QuantumOperations=CustomGeneralOperations(),
):
    '''An experiment which does a 2D sweep of yokos'''
    outer_current_sweep = LinearSweepParameter(
        f'Sweeping {yoko_dict_key_outer}',
        outer_left_current,
        outer_right_current,
        outer_current_count,
    )

    inner_current_sweep = LinearSweepParameter(
        f'Sweeping {yoko_dict_key_inner}',
        inner_left_current,
        inner_right_current,
        inner_current_count,
    )

    with dsl.sweep(
        name=f'Current Sweep of {yoko_dict_key_outer} (outer)',
        parameter=outer_current_sweep,
    ):
        dsl.call(change_current,
                 yoko_dict_key=yoko_dict_key_outer,
                 current_setpoint=outer_current_sweep,
                 step_time=0.01,
                 silence=silence,
        )
        with dsl.sweep(
            name=f'Current Sweep of {yoko_dict_key_inner} (inner)',
            parameter=inner_current_sweep,
        ):
            dsl.call(change_current,
                    yoko_dict_key=yoko_dict_key_inner,
                    current_setpoint=inner_current_sweep,
                    step_time=0.01,
                    silence=True,
            )
            with dsl.acquire_loop_rt(
                name='Real Time Loop',
                count=averages,
                acquisition_type=AcquisitionType.SPECTROSCOPY,
                averaging_mode=AveragingMode.CYCLIC,
            ):
                qops.measure(q, 'results')
    return

@dsl.qubit_experiment(name='X90 Tuneup') # [ ] TODO: Add a sweetspot flux auto config
def X90_tuneup(
    q: QuantumElement,
    yoko_dict_key: str,
    lower_amp,
    upper_amp,
    amp_count,
    averages=2**8,
    t_drive=200e-6,
    t_delay=200e-6,
    qops: dsl.QuantumOperations=CustomGeneralOperations()
):
    '''A amplitude sweep to calibrate an X90 pulse'''

    active_exp_cal = dsl.experiment_calibration()

    # Track resonator if flux dependent
    if hasattr(q.parameters, 'res_to_current') is False:
        print('Does not have a res_to_current')
        pass
    elif q.parameters.res_to_current is None:
        print('Not using current mapping')
    elif q.parameters.flux_sweetspot is None:
        print('Using current mapping at current current')
        ro_frequency = q.parameters.res_to_current(get_current(yoko_dict_key))
        ro_rf_frequency = ro_frequency - q.parameters.readout_lo_frequency
        active_exp_cal[q.signals['measure']].oscillator.frequency = ro_rf_frequency
    elif q.parameters.flux_sweetspot is not None:
        print('Using current mapping at sweepspot current')
        _ = None
        change_current(_, yoko_dict_key, q.parameters.flux_sweetspot, 0.01)
        ro_frequency = q.parameters.res_to_current(get_current(yoko_dict_key))
        ro_rf_frequency = ro_frequency - q.parameters.readout_lo_frequency
        active_exp_cal[q.signals['measure']].oscillator.frequency = ro_rf_frequency


    active_exp_cal = active_exp_cal[q.signals['acquire']]
    active_exp_cal.oscillator.modulation_type=ModulationType.SOFTWARE
    
    drive_amp_sweep = LinearSweepParameter(
        f'Sweeping {q.uid} drive amplitude',
        lower_amp,
        upper_amp,
        amp_count
    )

    with dsl.acquire_loop_rt(
        name='Real Time Loop',
        count=averages,
        acquisition_type=AcquisitionType.INTEGRATION,
        averaging_mode=AveragingMode.CYCLIC,
    ):
        with dsl.sweep(
            name='Drive Amplitude Sweep',
            parameter=drive_amp_sweep,
        ):
            qops.arbitrary_drive(q, 'arb drive', amplitude=drive_amp_sweep, length=t_drive)
            qops.measure(q, 'results', t_delay=t_delay)
    return

@dsl.qubit_experiment(name='T1 Exp')
def T1_exp(
    q: QuantumElement,
    min_time,
    max_time,
    t_count,
    averages=2*8,
    qops: dsl.QuantumOperations = CustomGeneralOperations()
):
    '''A simple T1 experiment given a calibrated X90'''

    t_total = max_time*1.5

    t_delay_sweep = LinearSweepParameter(
        f'Time Delay',
        min_time,
        max_time,
        t_count,
    )

    with dsl.acquire_loop_rt(
        name='Real Time Loop',
        count=averages,
        acquisition_type=AcquisitionType.INTEGRATION,
        averaging_mode=AveragingMode.CYCLIC,
    ):
        with dsl.sweep(
            name='Readout Delay Sweep',
            parameter=t_delay_sweep,
        ):
            drive_section = qops.arbitrary_drive(q, 'x90', amplitude=q.parameters.amplitude_pi)
            drive_section.delay(q.signals['drive'], t_delay_sweep)
            # drive_section.reserve(q.signals['measure'])
            # drive_section.reserve(q.signals['acquire'])
            # with dsl.section(
            #     uid='T_delay',
            #     length=t_delay_sweep
            # ):
            #     dsl.reserve(q.signals['measure'])
            #     dsl.reserve(q.signals['acquire'])
            #     dsl.reserve(q.signals['drive'])
            # qops.arbitrary_drive(q, 'arb drive', amplitude=q.parameters.amplitude_pi_div_2)
            qops.measure(q, 'results', t_delay=t_total-t_delay_sweep)
    return

@dsl.qubit_experiment(name='T2 Star')
def T2_star(
    q: QuantumElement,
    min_time,
    max_time,
    t_count,
    detuning=None,
    averages=2**8,
    reset_delay=100e-6,
    qops: dsl.QuantumOperations=CustomGeneralOperations()
):
    '''A simple T2 star experiment'''

    if detuning is None:
        pass
    else:
        active_exp_cal = dsl.experiment_calibration()
        active_exp_cal[q.signals['drive']].oscillator.frequency += detuning

    t_delay_sweep = LinearSweepParameter(
        f'Time Delay',
        min_time,
        max_time,
        t_count,
    )

    with dsl.acquire_loop_rt(
        name='Real Time Loop',
        count=averages,
        acquisition_type=AcquisitionType.INTEGRATION,
        averaging_mode=AveragingMode.CYCLIC,
    ):
        with dsl.sweep(
            name='Readout Delay Sweep',
            parameter=t_delay_sweep,
        ):
            drive_section = qops.arbitrary_drive(q, 'x90', amplitude=q.parameters.amplitude_pi_div_2)
            drive_section.delay(q.signals['drive'], t_delay_sweep)
            # drive_section.add(qops.arbitrary_drive.omit_section(q, 'x90', amplitude=q.parameters.amplitude_pi_div_2))

            qops.arbitrary_drive(q, 'x90', amplitude=q.parameters.amplitude_pi_div_2)
            qops.measure(q, 'results', t_delay=reset_delay)

    
    return

@dsl.qubit_experiment(name='T2 Echo')
def T2_echo(
    q: QuantumElement,
    min_time,
    max_time,
    t_count,
    detuning=None,
    averages=2**8,
    reset_delay=100e-6,
    qops: dsl.QuantumOperations=CustomGeneralOperations()
):
    '''A simple T2 echo experiment'''

    if detuning is None:
        pass
    else:
        active_exp_cal = dsl.experiment_calibration()
        active_exp_cal[q.signals['drive']].oscillator.frequency += detuning

    t_delay_sweep = LinearSweepParameter(
        f'Time Delay',
        min_time,
        max_time,
        t_count,
    )

    with dsl.acquire_loop_rt(
        name='Real Time Loop',
        count=averages,
        acquisition_type=AcquisitionType.INTEGRATION,
        averaging_mode=AveragingMode.CYCLIC,
    ):
        with dsl.sweep(
            name='Readout Delay Sweep',
            parameter=t_delay_sweep,
        ):
            first_drive = qops.arbitrary_drive(q, 'x90', amplitude=q.parameters.amplitude_pi_div_2)
            first_drive.delay(q.signals['drive'], t_delay_sweep/2)
            flip_section = qops.arbitrary_drive(q, 'x180', amplitude=q.parameters.amplitude_pi)
            flip_section.delay(q.signals['drive'], t_delay_sweep/2)
            qops.arbitrary_drive(q, 'x90_2', amplitude=q.parameters.amplitude_pi_div_2)
            qops.measure(q, 'results', t_delay=reset_delay)
    return

@dsl.qubit_experiment(name='Fast Flux Calibration') # [ ] TODO: Placeholder exp
def fast_flux_calib(
    q: QuantumElement,
):
    '''An experiment for calibrating the fast flux pulse procedure'''
    pass

@dsl.qubit_experiment(name='Fast Flux Drive Pulse') # [ ] TODO: Placeholder exp
def fast_flux_drive_pulse(
    q: QuantumElement,
):
    '''An experiment which drives while a calibrated fast flux pulse is active'''
    pass
