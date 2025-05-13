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
from laboneq_applications.qpu_types.tunable_transmon import TunableTransmonOperations, TunableTransmonQubit, TunableTransmonQubitParameters

import experiments

# Defining QuantumElement with their associated QuantumParameters class

# C2PHI
@attrs.define(kw_only=True)
class C2PhiParameters(QuantumParameters):
    """C2PhiParams parameters.

    Attributes
    ----------
    resonance_frequency_ge:
        The resonance frequency of the 0-1 transition (Hz).
    drive_lo_frequency:
        The frequency of the drive signal local oscillator (Hz).
    """

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
        """Calibration for the C2Phi"""
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

###############################################################################

# Fluxonium
@attrs.define(kw_only=True)
class FluxoniumParameters(QuantumParameters):
    """Fluxonium parameters.

    Attributes
    ----------
    resonance_frequency_ge:
        The resonance frequency of the 0-1 transition (Hz).
    drive_lo_frequency:
        The frequency of the drive signal local oscillator (Hz).
    readout_len:
        The length that the readout pulse is played (s).
    readout_amp:
        The amplitude of the readout pulse (arb).
    """

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
        """Calibration for the Fluxonium"""
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
        # calibration[self.signals["drive"]] = sig_cal
        return Calibration(calibration)