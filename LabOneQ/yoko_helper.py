"""Helpers for Yokogawa GS200 instruments used from notebooks.

The GS200 can retain a VXI-11 link when a kernel is killed during an I/O
operation.  Closing instruments on normal shutdown and on interrupts greatly
reduces the chance of leaving such a link behind.  A hard process kill cannot
be handled by Python; the instrument's LAN timeout or a power cycle may still
be required in that case.
"""

import atexit
import signal
import threading
from typing import Optional

from qcodes.instrument_drivers.yokogawa.Yokogawa_GS200 import YokogawaGS200


VISA_TIMEOUT_MS = 5_000
YOKO_ADDRESSES = {
    "DC1": "TCPIP0::192.168.1.76::inst0::INSTR",
    "DC2": "GPIB::5::INSTR",
}

# Preserve the dictionary when this module is reloaded in an ipykernel.
if "yoko_dict" not in globals():
    yoko_dict = {}


def _set_visa_timeout(instrument, timeout_ms: int = VISA_TIMEOUT_MS) -> None:
    """Set the timeout on a QCoDeS VISA-backed instrument when available."""
    visa_handle = getattr(instrument, "visa_handle", None)
    if visa_handle is not None:
        visa_handle.timeout = timeout_ms


def _open_yoko(name: str, address: str):
    """Open one GS200 and configure a finite I/O timeout."""
    instrument = YokogawaGS200(name, address=address)
    _set_visa_timeout(instrument)
    return instrument


def close_yokos() -> None:
    """Close every instrument owned by this helper.

    Errors are deliberately ignored during interpreter shutdown because VISA
    objects may already have been partially torn down.
    """
    for name, instrument in list(yoko_dict.items()):
        try:
            instrument.close()
        except Exception as exc:
            print(f"Could not close {name}: {exc}")
    yoko_dict.clear()


def _interrupt_handler(signum, frame) -> None:
    """Close VISA sessions before allowing the usual interrupt behavior."""
    close_yokos()
    if signum == signal.SIGINT:
        raise KeyboardInterrupt


# These handlers only affect the main thread, which is where Python delivers
# notebook interrupts.  Do not replace handlers from worker threads.
if threading.current_thread() is threading.main_thread():
    signal.signal(signal.SIGINT, _interrupt_handler)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, _interrupt_handler)
atexit.register(close_yokos)


for name, address in YOKO_ADDRESSES.items():
    if name not in yoko_dict:
        try:
            yoko_dict[name] = _open_yoko(name, address)
        except Exception as exc:
            print(f"Could not connect to {name} ({address}): {exc}")


def reconnect_yoko(
    yoko_dict_key: str,
    address: Optional[str] = None,
):
    """Close and reopen one instrument using its configured VISA address.

    This is useful after a recoverable communication exception.  It cannot
    reclaim a VXI-11 link left by a hard-killed process; in that case wait for
    the GS200 LAN timeout or power-cycle the instrument.
    """
    old_instrument = yoko_dict.pop(yoko_dict_key, None)
    if old_instrument is not None:
        try:
            old_instrument.close()
        except Exception as exc:
            print(f"Could not close {yoko_dict_key} before reconnecting: {exc}")

    reconnect_address = address or YOKO_ADDRESSES[yoko_dict_key]
    instrument = _open_yoko(yoko_dict_key, reconnect_address)
    yoko_dict[yoko_dict_key] = instrument
    return instrument


def change_current(session, yoko_dict_key, current_setpoint, step_time, silence: bool = True):
    """Set current using the selected Yokogawa instrument."""
    yoko_dict[yoko_dict_key].ramp_current(current_setpoint, 10e-6, step_time)
    if silence is False:
        print(f"{yoko_dict_key} is at {current_setpoint * 1e6:3f}")


def get_current(yoko_dict_key):
    return yoko_dict[yoko_dict_key].current.get()