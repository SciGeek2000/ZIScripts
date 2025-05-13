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
# from __future__ import annotations

import laboneq
import laboneq.serializers
from laboneq.dsl.quantum import QPU
import laboneq.pulse_sheet_viewer.pulse_sheet_viewer as psv
from laboneq.simple import *
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


def global_trace(exp_signals, readout_lo_freq_sweep, readout_freq_sweep, readout_pulse, averages=2**8):
    '''Defines an experiment that does a global resonator trace'''

    averages=2**8
    #--- Defining Sections and Sweeps and Experiment ---
    exp = Experiment(
        uid='Global Resonator Trace',
        signals=exp_signals,)
    RO_LO_Sweep = Sweep(
        uid='Readout LO Frequency Sweep',
        parameters=readout_lo_freq_sweep)
    RT_Loop = AcquireLoopRt(
        uid='Shots',
        count=averages,
        averaging_mode=AveragingMode.CYCLIC,
        acquisition_type=AcquisitionType.SPECTROSCOPY,)
    AWG_Freq_Sweep = Sweep(
        uid='Readout Frequency Sweep',
        parameters=readout_freq_sweep,
        reset_oscillator_phase=False)
    Meas_Acquire = Section(uid='Pulsed Single Frequency Readout')
    Meas_Acquire.play(
        signal='measure',
        pulse=readout_pulse)
    Meas_Acquire.acquire(
        signal='acquire', 
        handle='single_freq_data', 
        length=qubit.parameters.readout_len)
    Delay_After_Count = Section(uid='Delay Between Readout')
    
    #--- Properly Defining Nesting Order ---
    exp.add(RO_LO_Sweep)
    RO_LO_Sweep.add(RT_Loop)
    RT_Loop.add(AWG_Freq_Sweep)
    AWG_Freq_Sweep.add(Meas_Acquire)
    AWG_Freq_Sweep.add(Delay_After_Count)
    Delay_After_Count.reserve(signal='measure')
    Delay_After_Count.reserve(signal='acquire')
    
    #--- Defines Oscillators ---
    readout_osc = Oscillator(
        "readout_osc",
        frequency=readout_freq_sweep,
        modulation_type=ModulationType.HARDWARE)
    readout_lo = Oscillator(
        "readout_lo",
        frequency=readout_lo_freq_sweep,
        modulation_type=ModulationType.HARDWARE)

    #---Calibration object Updates and Application ---
    exp_calibration = Calibration()
    exp_calibration["measure"] = SignalCalibration(
        oscillator=readout_osc,
        local_oscillator=readout_lo)
    exp_calibration["acquire"] = SignalCalibration(
        oscillator=readout_osc,
        local_oscillator=readout_lo)
    exp.set_calibration(exp_calibration)
    return exp