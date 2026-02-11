# plotting and fitting functionality

# from laboneq.analysis.fitting import (
#     lorentzian,
#     oscillatory,
#     oscillatory_decay,
#     exponential_decay,
# )

from pathlib import Path
import datetime
from datetime import date
import os
import numpy as np
from scipy.stats import linregress

def data_directory_update():
    date = datetime.date.today()
    datadir = Path('data/' + str(date) + '/')
    if not os.path.exists(datadir):
        os.makedirs(datadir)
    return datadir
datadir = data_directory_update()

def live_plotter(fig, new_data):
    pass

def non_redund_save_fig(fig, name):
# A function to prevent figure overwrite issues
    datadir = data_directory_update()
    i = 1
    while True:
        fig_name = Path(str(datadir) + f'/{name}_{i}.png')
        if os.path.isfile(fig_name) is False:
            fig_name = Path(str(datadir) + f'/{name}_{i}')
            fig.savefig(fig_name)
            break
        else:
            i = i+1

def non_redund_save_pd(pd_data, name):
    datadir = data_directory_update()
    i = 1
    while True:
        pd_name = Path(str(datadir) + f'/{name}_{i}.csv')
        if os.path.isfile(pd_name) is False:
            pd_name = Path(str(datadir) + f'/{name}_{i}.csv')
            pd_data.to_csv(pd_name)
            break
        else:
            i += 1

def non_redund_save_csv(csv_data, name):
    datadir = data_directory_update()
    i = 1
    while True:
        csv_name = Path(str(datadir) + f'/{name}_{i}.csv')
        if os.path.isfile(csv_name) is False:
            csv_name = Path(str(datadir) + f'/{name}_{i}.csv')
            csv_data.to_csv(csv_name)
            break
        else:
            i += 1

def remove_local_phase_delay(IQ_data: np.ndarray, frequency: np.ndarray, delay):
    '''Removes IQ bias, zeros phase delay (unique to that sweep), and returns data as cleaned IQ arrays'''
    IQ_data = IQ_data #- np.mean(IQ_data)
    cleaned_complex = np.exp(1j*delay*2*np.pi*frequency)*IQ_data
    return cleaned_complex

# The procedure I will follow for phase will be:
#   1.) Center the IQ blob by just removing the average of the data. NOTE! This was not something I was doing and accounts for net assymetric chain/mesurement.
#   2.) Find the np.angle and np.unwrap of the data.
#   3.) Find a linear fit for this region. This may be a slighly different electrical delay due to the TWPA's local frequency phase delay.
#   4.) Subtract out the linear phase background. NOTE! Do not then zero this phase data.
#   5.) Plot this data. This should then form nice circles in IQ space associated with the resonator itself.