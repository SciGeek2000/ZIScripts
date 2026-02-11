from qcodes.instrument_drivers.yokogawa.GS200 import GS200

# Yoko dict for later usage in function calls
if 'yoko_dict' not in globals():
    yoko_dict = dict()
try:
    name = 'coil'
    if name not in yoko_dict:
        yoko = GS200(name, address = 'TCPIP0::192.168.4.208::inst0::INSTR',)
        yoko_dict[name] = yoko
except Exception as e:
    print(e)
try:
    name = 'dc'
    if name not in yoko_dict:
        yoko = GS200(name, address = 'TCPIP0::192.168.4.157::inst0::INSTR',)
        yoko_dict[name] = yoko
except Exception as e:
    print(e)

def change_current(session, yoko_dict_key, current_setpoint, step_time, silence: bool=True):
    '''To be used in neartime loops for the ZI box'''
    yoko_dict[yoko_dict_key].ramp_current(current_setpoint, 10e-6, step_time)
    if silence is False:
        print(f'{yoko_dict_key} is at {current_setpoint*1e6:3f}')

def get_current(yoko_dict_key):
    return yoko_dict[yoko_dict_key].current.get()