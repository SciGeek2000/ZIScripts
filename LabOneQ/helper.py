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

def adjust_phase(
        IQ_data: np.ndarray, frequency: np.ndarray, 
        electrical_delay: float,
        ) -> np.ndarray:
    '''Adjusts the phase to be flattened and unwrapped'''
    adjusted_complex = np.exp(1j*electrical_delay*2*np.pi*frequency)*IQ_data
    flattened_angle = np.unwrap(np.angle(adjusted_complex))
    flattened_angle = flattened_angle - np.mean(flattened_angle)
    return flattened_angle