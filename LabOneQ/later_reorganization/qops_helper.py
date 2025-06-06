from qelement_helper import *

# General Quantum Operations Definition #
###############################################################################

class CustomGeneralOperations(dsl.QuantumOperations):
    '''
    Defines the general quantum operations which all qubits (explicitly defined
    within QUBIT_TYPES) should be applicable.
    '''
    
    QUBIT_TYPES = (Fluxonium, C2Phi, Gridium, Transmon)

    @dsl.quantum_operation
    def measure(
        self,
        q: QUBIT_TYPES,
        acquire_handle: str,
        amplitude=None,
    ) -> None:
        '''Performs a measurement on the perscribed qubit'''
        
        if amplitude is None:
            amplitude = float(q.parameters.readout_amp)

        session = dsl.active_section()
        session.name = f'Measure f{q.uid}'

        readout_pulse = pulse_library.gaussian_square(
            uid=f"readout_pulse_{q.uid}",
            length=q.parameters.readout_len,
            amplitude=1,
            width=q.parameters.readout_len*0.9,
            sigma=0.2,)
        
        dsl.play(
            signal=q.signals['measure'],
            pulse=readout_pulse,
            amplitude=amplitude
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
    def arbitrary_drive(
        self,
        q: QUBIT_TYPES,
        name: str,
        length=100e-9,
        amplitude=1
    ) -> None:
        '''Configures an arbitrary drive tone'''
        
        session = dsl.active_section()
        session.name = name
        drive_pulse = pulse_library.gaussian_square(
            uid=name,
            length=length,
            amplitude=amplitude,
            width=length*0.9,
            sigma=0.2
        )

        dsl.play(
            signal=q.signals['drive'],
            pulse=drive_pulse
        )

    @dsl.quantum_operation
    def awg_sweep(
        self,
        q: QUBIT_TYPES,
        sig: None
    ) -> None:
        '''Sweeps through awg frequencies on the specified signal'''
        return