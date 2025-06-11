# Imports #
###############################################################################
from all_imports import *
import attrs

def general_calibration(self: QuantumElement) -> dict:
    '''
    Function for returning a dict object for all the lines for a
    given general QuantumElement.

    A base class which will be called for all QuantumElements but can be
    overwritten. Ultimately needs to be converted into a Calibration object
    via Calibration()

    Generally will be called by a DeviceSetup.set_calibration(Calibration)
    or Experiment.set_calibration(Calibration)
    '''       

    calibration = {}

    # --- Readout Line ---

    # define the local oscillator for the readout line if specified
    if self.parameters.readout_lo_frequency is None:
        readout_lo = None
    else:
        readout_lo = Oscillator(
            uid=f"{self.uid}_readout_lo",
            frequency=self.parameters.readout_lo_frequency,
        )

    # calculate the readout line RF frequency:
    if (
        self.parameters.readout_lo_frequency is not None
        and self.parameters.readout_resonator_frequency is not None
    ):
        readout_rf_frequency = (
            self.parameters.readout_resonator_frequency
            - self.parameters.readout_lo_frequency
        )
    else:
        readout_rf_frequency = None

    # creates and sets a signal calibration object for readout
    sig_cal = SignalCalibration()
    sig_cal.local_oscillator = readout_lo
    sig_cal.range = self.parameters.readout_range_out
    sig_cal.oscillator = Oscillator(
        uid=f'{self.uid}_readout_measure_rf_osc',
        frequency=readout_rf_frequency,
        modulation_type=ModulationType.AUTO,
    )
    if readout_lo.frequency < 1e9:
        sig_cal.port_mode = PortMode.LF
    
    # adds entries into the calibration dictionary with measure and acquire
    calibration[self.signals['measure']] = sig_cal
    calibration[self.signals['acquire']] = sig_cal


    # --- Drive Line ---
    # define the local oscillator if `drive_lo_frequency` was specified:
    if self.parameters.drive_lo_frequency is None:
        drive_lo = None
    else:
        drive_lo = Oscillator(
            uid=f"{self.uid}_drive_lo",
            frequency=self.parameters.drive_lo_frequency,   
        )

    # calculate the drive line RF frequency:
    if (
        self.parameters.drive_lo_frequency is not None
        and self.parameters.resonance_frequency_ge is not None
    ):
        drive_rf_frequency = (
            self.parameters.resonance_frequency_ge
            - self.parameters.drive_lo_frequency
        )
    else:
        drive_rf_frequency = None
    
    # define the drive signal calibration:
    sig_cal = SignalCalibration()
    sig_cal.local_oscillator = drive_lo
    sig_cal.range = self.parameters.drive_range
    sig_cal.oscillator = Oscillator(
        uid=f"{self.uid}_drive_ge_osc",
        frequency=drive_rf_frequency,
        modulation_type=ModulationType.AUTO,
    )
    if drive_lo.frequency < 1e9:
        sig_cal.port_mode = PortMode.LF

    # adds entries into the calibration dictionary with drive
    calibration[self.signals["drive"]] = sig_cal


    return calibration


# Set default calibration behavior
QuantumElement.calibration = general_calibration


def fast_flux_line_calib(self: QuantumElement) -> dict:
    '''Calibrates a fast flux line and returns the associated dictionary'''
    
    calibration = {}

    # --- Fast Flux Line ---
    ff_lo = Oscillator(
        uid=f'{self.uid}_ff_lo',
        frequency=0,
    )
    ff_osc = Oscillator(
        uid=f'{self.uid}_ff_osc',
        frequency=0,
    )
    sig_cal = SignalCalibration()
    sig_cal.local_oscillator = ff_lo
    sig_cal.oscillator = ff_osc
    sig_cal.range = self.parameters.fast_flux_range
    sig_cal.port_mode = PortMode.LF

    calibration[self.signals['fast_flux']] = sig_cal

    return calibration


@attrs.define(kw_only=True)
class TransmonParameters(QuantumParameters):
    '''Transmon parameters'''

    resonance_frequency_ge: float | None = None
    drive_lo_frequency: float | None = None
    readout_resonator_frequency: float | None
    readout_lo_frequency: float | None = None 
    resonance_frequency_ge: float | None = None
    drive_lo_frequency: float | None = None
    readout_integration_delay: float | None = None
    readout_range_out: float | None = None
    drive_range: float | None = None
    readout_range_in: float | None = None
    pulse_length: float | None = None
    readout_len: float | None = None
    time_domain_reset_length: float | None = None
    cw_reset_length: float | None = None
    readout_amp: float | None = None
    amplitude_pi: float | None = None
    amplitude_pi_div_2: float | None = None
    
@attrs.define()
class Transmon(QuantumElement):
    '''
    Defines the paramters, signals, calibration and other functions of a
    Transmon QuantumElement
    '''
    
    PARAMETERS_TYPE = TransmonParameters

    REQUIRED_SIGNALS = (
        "acquire",
        "drive",
        "measure",
    )

    OPTIONAL_SIGNALS = ()

    SIGNAL_ALIASES = {}

    def calibration(self) -> Calibration:
        '''
        Function for returning the proper calibration for a Transmon element

        Generally will be called by a DeviceSetup.set_calibration(Calibration)
        or Experiment.set_calibration(Calibration)
        '''       
        calibration = super().calibration()
        return Calibration(calibration)
    
# Gridium Definition #
###############################################################################

@attrs.define(kw_only=True)
class GridiumParameters(QuantumParameters):
    '''Gridium parameters.'''

    resonance_frequency_ge: float | None = None
    drive_lo_frequency: float | None = None
    readout_resonator_frequency: float | None
    readout_lo_frequency: float | None = None 
    resonance_frequency_ge: float | None = None
    drive_lo_frequency: float | None = None
    readout_integration_delay: float | None = None
    readout_range_out: float | None = None
    drive_range: float | None = None
    fast_flux_range: float | None = None
    readout_range_in: float | None = None
    pulse_length: float | None = None
    readout_len: float | None = None
    time_domain_reset_length: float | None = None
    cw_reset_length: float | None = None
    readout_amp: float | None = None
    amplitude_pi: float | None = None
    amplitude_pi_div_2: float | None = None
    flux_sweetspot: float | None = None
    flux_setpoint: float | None = None

@attrs.define()
class Gridium(QuantumElement):
    '''
    Defines the parameters, signals, and calibration of a Gridium QuantumElement
    '''
    
    PARAMETERS_TYPE = GridiumParameters
    
    REQUIRED_SIGNALS = (
        "acquire",
        "drive",
        "measure",
    )
    
    OPTIONAL_SIGNALS = (
        "fast_flux",
        "slow_flux",
    )
    
    SIGNAL_ALIASES = {}
   
    def calibration(self) -> Calibration:
        '''
        Function for returning the proper calibration for a Gridium element

        Generally will be called by a DeviceSetup.set_calibration(Calibration)
        or Experiment.set_calibration(Calibration)
        '''
        calibration = super().calibration()
        ff_dict = fast_flux_line_calib()
        calibration.update(ff_dict)
        return Calibration(calibration)

# Cos(2phi) Definition #
###############################################################################

@attrs.define(kw_only=True)
class C2PhiParameters(QuantumParameters):
    '''C2PhiParams parameters.'''

    resonance_frequency_ge: float | None = None
    drive_lo_frequency: float | None = None
    readout_resonator_frequency: float | None
    readout_lo_frequency: float | None = None 
    resonance_frequency_ge: float | None = None
    drive_lo_frequency: float | None = None
    readout_integration_delay: float | None = None
    readout_range_out: float | None = None
    drive_range: float | None = None
    fast_flux_range: float | None = None
    readout_range_in: float | None = None
    pulse_length: float | None = None
    readout_len: float | None = None
    time_domain_reset_length: float | None = None
    cw_reset_length: float | None = None
    readout_amp: float | None = None
    amplitude_pi: float | None = None
    amplitude_pi_div_2: float | None = None
    flux_sweetspot: float | None = None
    flux_setpoint: float | None = None 

@attrs.define()
class C2Phi(QuantumElement):
    '''
    Defines the parameters, signals, and calibration of a C2Phi QuantumElement
    '''
    
    PARAMETERS_TYPE = C2PhiParameters
    
    REQUIRED_SIGNALS = (
        "acquire",
        "drive",
        "measure",
    )
    
    OPTIONAL_SIGNALS = (
        "fast_flux",
        "slow_flux",
    )
    
    SIGNAL_ALIASES = {}
   
    def calibration(self) -> Calibration:
        '''
        Function for returning the proper calibration for a C2Phi element

        Generally will be called by a DeviceSetup.set_calibration(Calibration)
        or Experiment.set_calibration(Calibration)
        '''
        calibration = super().calibration()
        ff_dict = fast_flux_line_calib()
        calibration.update(ff_dict)
        return Calibration(calibration)

# Fluxonium Definition #
###############################################################################

@attrs.define(kw_only=True)
class FluxoniumParameters(QuantumParameters):
    '''Fluxonium parameters.'''

    resonance_frequency_ge: float | None = None
    drive_lo_frequency: float | None = None
    readout_resonator_frequency: float | None
    readout_lo_frequency: float | None = None 
    resonance_frequency_ge: float | None = None
    drive_lo_frequency: float | None = None
    readout_integration_delay: float | None = None
    readout_range_out: float | None = None
    drive_range: float | None = None
    fast_flux_range: float | None = None
    readout_range_in: float | None = None
    pulse_length: float | None = None
    readout_len: float | None = None
    time_domain_reset_length: float | None = None
    cw_reset_length: float | None = None
    readout_amp: float | None = None
    amplitude_pi: float | None = None
    amplitude_pi_div_2: float | None = None
    flux_sweetspot: float | None = None
    flux_setpoint: float | None = None

@attrs.define()
class Fluxonium(QuantumElement):
    '''
    Defines the parameters, signals, calibration and other functions of a
    Fluxonium QuantumElement
    '''
    
    PARAMETERS_TYPE = FluxoniumParameters
    
    REQUIRED_SIGNALS = (
        "acquire",
        "drive",
        "measure",
    )
    
    OPTIONAL_SIGNALS = (
        "fast_flux",
        "slow_flux"
    )
    
    SIGNAL_ALIASES = {}

    def calibration(self) -> Calibration:
        '''
        Function for returning the proper calibration for a Fluxonium element

        Generally will be called by a DeviceSetup.set_calibration(Calibration)
        or Experiment.set_calibration(Calibration)
        '''       

        calibration = super().calibration()
        ff_dict = fast_flux_line_calib()
        calibration.update(ff_dict)
        return Calibration(calibration)