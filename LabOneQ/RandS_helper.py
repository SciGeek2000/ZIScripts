from qcodes.instrument_drivers.rohde_schwarz.SGS100A import RohdeSchwarzSGS100A

try:
    name = 'TWPA_Drive'
    TWPADrive = RohdeSchwarzSGS100A(
        name=name,
        address='TCPIP0::192.168.1.78::inst0::INSTR',
        )
except Exception as e:
    print(e)

def RandS_set_power(session, power:float, silence=False) -> None:
    'Sets the power for the Rhode&Schwarz'
    TWPADrive.power.set(power)
    if not silence:
        print(f'Power is {TWPADrive.power.get()} dBm')

def RandS_set_frequency(session, freq:float, silence=False) -> None:
    'Sets the frequency for the Rhode&Schwarz'
    TWPADrive.frequency.set(freq)
    if silence:
        print(f'Frequency is {TWPADrive.frequency.get()/1e9} GHz')