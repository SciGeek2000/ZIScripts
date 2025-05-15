# Imports #
###############################################################################

import datetime
import pandas as pd
import time
import sys
import os
import matplotlib.pyplot as plt
import numpy as np
import sys
import logging
import math as m
import statistics as stat
import attrs
from pathlib import Path
from datetime import date
from typing import Callable
from qcodes.instrument_drivers.yokogawa.GS200 import GS200

import laboneq
import laboneq.serializers
import laboneq.pulse_sheet_viewer.pulse_sheet_viewer as psv
from laboneq.simple import *
from laboneq.dsl.quantum import QPU, QuantumPlatform
from laboneq.contrib.example_helpers.plotting.plot_helpers import plot_simulation
from laboneq.contrib.example_helpers.generate_device_setup import (
    generate_device_setup,
)
from laboneq.analysis.fitting import (
    lorentzian,
    oscillatory,
    oscillatory_decay,
    exponential_decay,
)
import laboneq_applications
from laboneq_applications.qpu_types.tunable_transmon import (
    TunableTransmonOperations,
    TunableTransmonQubit,
    TunableTransmonQubitParameters
)


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
    readout_range_in: float | None = None
    pulse_length: float | None = None
    readout_len: float | None = None
    time_domain_reset_length: float | None = None
    cw_reset_length: float | None = None
    readout_amp: float | None = None
    amplitude_pi: float | None = None
    amplitude_pi_div_2: float | None = None
    

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
        
        # define the local oscillator if `drive_lo_frequency` was specified:
        if self.parameters.drive_lo_frequency is not None:
            drive_lo = Oscillator(
                uid=f"{self.uid}_drive_local_osc",
                frequency=self.parameters.drive_lo_frequency,
            )
        else:
            drive_lo = None
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
        calibration = {}
        # define the drive signal calibration:
        sig_cal = SignalCalibration()
        if drive_rf_frequency is not None:
            sig_cal.oscillator = Oscillator(
                uid=f"{self.uid}_drive_ge_osc",
                frequency=drive_rf_frequency,
                modulation_type=ModulationType.AUTO,
            )
        sig_cal.local_oscillator = drive_lo
        calibration[self.signals["drive"]] = sig_cal
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
    readout_range_in: float | None = None
    pulse_length: float | None = None
    readout_len: float | None = None
    time_domain_reset_length: float | None = None
    cw_reset_length: float | None = None
    readout_amp: float | None = None
    amplitude_pi: float | None = None
    amplitude_pi_div_2: float | None = None

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
        
        # define the local oscillator if `drive_lo_frequency` was specified:
        if self.parameters.drive_lo_frequency is not None:
            drive_lo = Oscillator(
                uid=f"{self.uid}_drive_local_osc",
                frequency=self.parameters.drive_lo_frequency,
            )
        else:
            drive_lo = None
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

        calibration = {}
        # define the drive signal calibration:
        sig_cal = SignalCalibration()
        if drive_rf_frequency is not None:
            sig_cal.oscillator = Oscillator(
                uid=f"{self.uid}_drive_ge_osc",
                frequency=drive_rf_frequency,
                modulation_type=ModulationType.AUTO,
            )
        sig_cal.local_oscillator = drive_lo
        calibration[self.signals["drive"]] = sig_cal

        sig_cal = SignalCalibration()
        readout_lo = Oscillator(
            uid=f'{self.uid}_readout_lo',
            frequency=self.parameters.readout_lo_frequency,
        )
        sig_cal.oscillator = Oscillator(
            uid=f'{self.uid}_readout_measure_rf_osc',
            frequency=readout_rf_frequency
        )
        sig_cal.local_oscillator = readout_lo
        calibration[self.signals['measure']] = sig_cal

        sig_cal = SignalCalibration()
        # sig_cal.oscillator = Oscillator(
        #     uid=f'{self.uid}_readout_acquire_rf_osc',
        #     frequency=(self.parameters.readout_resonator_frequency - self.parameters.readout_lo_frequency)
        # )
        sig_cal.local_oscillator = readout_lo
        calibration[self.signals['acquire']] = sig_cal

        return Calibration(calibration)


# General Quantum Operations Definition #
###############################################################################

class CustomGeneralOperations(dsl.QuantumOperations):
    '''
    Defines the general quantum operations which all qubits (explicitly defined
    within QUBIT_TYPES) should be applicable.
    '''
    
    QUBIT_TYPES = (Fluxonium, C2Phi)

    @dsl.quantum_operation
    def my_measure(
        self,
        q: QUBIT_TYPES,
        acquire_handle: str,
    ) -> None:

        session = dsl.active_section()
        session.name = 'Gettin fancy with it'
        '''Performs a measurement on the perscribed qubit'''
        readout_pulse = pulse_library.gaussian_square(
            uid=f"readout_pulse_{q.uid}",
            length=q.parameters.readout_len,
            amplitude=q.parameters.readout_amp,
            width=q.parameters.readout_len*0.9,
            sigma=0.2,)
        
        dsl.play(
            signal=q.signals['measure'],
            pulse=readout_pulse,
        )
        dsl.acquire(
            signal=q.signals['acquire'],
            handle=acquire_handle,
            length=2e-6,
            kernel=readout_pulse,
        )
        dsl.delay(
            signal=q.signals['acquire'],
            time=1000e-9,
        )
        dsl.delay(
            signal=q.signals['measure'],
            time=1000e-9,
        )
        return

    @dsl.quantum_operation
    def awg_sweep(
        self,
        q: QUBIT_TYPES,
        sig: None
    ) -> None:
        '''Sweeps through awg frequencies on the specified signal'''
        return