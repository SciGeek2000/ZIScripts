from all_imports import *
from qelement_helper import Fluxonium, C2Phi, Gridium, Transmon

# General Quantum Operations Definition #
###############################################################################

class CustomGeneralOperations(dsl.QuantumOperations):
    '''
    Defines the general quantum operations which all qubits (explicitly defined
    within QUBIT_CLASS) should be applicable.
    '''
    
    QUBIT_TYPES = (Fluxonium, C2Phi, Gridium, Transmon)
    QUBIT_CLASS_TYPE = list[QuantumElement] | QuantumElement

    @dsl.quantum_operation
    def measure(
        self,
        q: QUBIT_CLASS_TYPE,
        acquire_handle: str,
        amplitude=None,
        t_delay=1e-6
    ) -> None:
        '''Performs a measurement on the perscribed qubit'''
        
        if amplitude is None:
            amplitude = float(q.parameters.readout_amp)

        session = dsl.active_section()
        session.name = f'Measure {q.uid}'

        readout_pulse = dsl.pulse_library.gaussian_square(
            uid=f"{q.uid}_readout_pulse",
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
            time=t_delay,
        )
        dsl.delay(
            signal=q.signals['measure'],
            time=t_delay,
        )
        return

    @dsl.quantum_operation
    def arbitrary_drive(
        self,
        q: QUBIT_CLASS_TYPE,
        name: str,
        length=200e-9,
        amplitude=1,
    ) -> None:
        '''Configures and plays an arbitrary drive tone'''
        
        session = dsl.active_section()
        session.name = name
        drive_pulse = dsl.pulse_library.gaussian_square(
            uid=f'{q.uid}_arb_drive',
            length=length,
            amplitude=1,
            width=length*0.9,
            sigma=0.2
        )

        dsl.play(
            signal=q.signals['drive'],
            pulse=drive_pulse,
            amplitude=amplitude,
        )
        return
    
    @dsl.quantum_operation
    def x90(
        self,
        q: QUBIT_CLASS_TYPE,
        name: str,
        length=None,
        amplitude=None,
    ):
        '''Configures and plays an X90 pulse'''
        pass

    @dsl.quantum_operation
    def awg_sweep(
        self,
        q: QUBIT_CLASS_TYPE,
        sig: None
    ) -> None:
        '''Sweeps through awg frequencies on the specified signal'''
        return
    
    @dsl.quantum_operation
    def fast_flux_pulse(
        self,
        name: str,
        q: QUBIT_CLASS_TYPE,
        pulse_pts: np.ndarray,
        amplitude: float=1,
    ) -> None:
        '''Configures and plays a fast flux pulse'''

        session = dsl.active_section()
        session.name = name
        flux_pulse = dsl.pulse_library.sampled_pulse(
            samples=pulse_pts,
            uid=f'{q.uid}_ff_pulse',
            can_compress=True,
        )

        dsl.play(
            signal=q.signals['fast_flux'],
            pulse=flux_pulse,
            amplitude=amplitude,
        )
        return
