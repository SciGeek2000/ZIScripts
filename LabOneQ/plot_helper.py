"""Interactive Plotly renderers for LabOneQ experiment results.

The public function names intentionally match the original plotting module so
existing notebook imports continue to work.  Every renderer returns a
``plotly.graph_objects.Figure``; subplot axes are addressed by Plotly trace
names and ``fig.update_*`` methods rather than Matplotlib axes.
"""

from __future__ import annotations

from typing import Any, Callable

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from all_imports import *
from helper import *
from qelement_helper import *
from qops_helper import *
from qubit_experiments import *


def _results(session):
    return session.get_results().acquired_results["results"]


def _lo(exp, qubit, signal="measure_line"):
    return exp.signals[f"{qubit.uid}/{signal}"].calibration.local_oscillator.frequency


def _delay(exp, qubit):
    return exp.signals[f"{qubit.uid}/acquire_line"].calibration.port_delay


def _iq(exp, session, qubit, axis_index=0, signal="measure_line", correct_delay=False):
    acquired = _results(session)
    axis = np.asarray(acquired.axis[axis_index]) + _lo(exp, qubit, signal)
    data = np.asarray(acquired.data)
    if correct_delay:
        data = remove_local_phase_delay(data, axis, _delay(exp, qubit))
    return acquired, axis, data


def _layout(fig, title=None, height=None):
    fig.update_layout(
        template="plotly_white", hovermode="closest", title=title,
        legend=dict(orientation="h", y=1.08), margin=dict(l=70, r=30, t=80, b=60),
        height=height,
    )
    return fig


def _line_pair(x, y1, y2, title, xlabel, labels=("Amplitude", "Phase"), marker=False):
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.12,
                        subplot_titles=labels)
    cls = go.Scatter if not marker else go.Scatter
    mode = "markers" if marker else "lines"
    fig.add_trace(cls(x=x, y=y1, mode=mode, name=labels[0]), row=1, col=1)
    fig.add_trace(cls(x=x, y=y2, mode=mode, name=labels[1]), row=2, col=1)
    fig.update_xaxes(title_text=xlabel, row=2, col=1)
    fig.update_yaxes(title_text=labels[0], row=1, col=1)
    fig.update_yaxes(title_text=labels[1], row=2, col=1)
    return _layout(fig, title, 650)


def _heat_pair(x, y, z1, z2, title, x_label, y_label, colors=("Viridis", "Plasma")):
    fig = make_subplots(rows=1, cols=2, horizontal_spacing=0.12,
                        subplot_titles=("Amplitude", "Phase"),
                        shared_yaxes=True)
    fig.add_trace(go.Heatmap(x=x, y=y, z=np.asarray(z1), colorscale=colors[0],
                             colorbar=dict(title="Amplitude", x=0.46),
                             hovertemplate=f"{x_label}: %{{x:.6g}}<br>{y_label}: %{{y:.6g}}<br>Value: %{{z:.6g}}<extra></extra>",
                             name="Amplitude"), row=1, col=1)
    fig.add_trace(go.Heatmap(x=x, y=y, z=np.asarray(z2), colorscale=colors[1],
                             colorbar=dict(title="Phase", x=1.02),
                             hovertemplate=f"{x_label}: %{{x:.6g}}<br>{y_label}: %{{y:.6g}}<br>Value: %{{z:.6g}}<extra></extra>",
                             name="Phase"), row=1, col=2)
    fig.update_xaxes(title_text=x_label, row=1, col=1)
    fig.update_xaxes(title_text=x_label, row=1, col=2)
    fig.update_yaxes(title_text=y_label, row=1, col=1)
    return _layout(fig, title, 600)


def _spectrum_data(exp, session, qubit, axis_index, signal):
    acquired = _results(session)
    x = np.asarray(acquired.axis[axis_index]) + _lo(exp, qubit, signal)
    data = np.asarray(acquired.data).ravel()
    return x, np.abs(data), np.unwrap(np.angle(data))


def plot_global_resonator_trace(exp, session, qubit, **kwargs):
    acquired = _results(session)
    lo = np.asarray(acquired.axis[0])
    awg = np.asarray(acquired.axis[1])
    freqs = np.concatenate([value + awg for value in lo])
    data = remove_local_phase_delay(np.asarray(acquired.data).ravel(), freqs, _delay(exp, qubit))
    return _line_pair(freqs, np.abs(data), np.unwrap(np.angle(data)),
                      "Wide Range Pulsed Trace", "Frequency (GHz)")


def plot_local_resonator_trace(exp, session, qubit, **kwargs):
    _, freqs, data = _iq(exp, session, qubit, correct_delay=True)
    return _line_pair(freqs, np.abs(data), np.unwrap(np.angle(data)),
                      f"{qubit.uid} Near Resonator Pulsed Trace", "Frequency (GHz)", marker=True)


def plot_full_spectrum(exp, session, qubit, **kwargs):
    x, amp, phase = _spectrum_data(exp, session, qubit, 1, "drive_line")
    return _line_pair(x, amp, phase, f"{qubit.uid} Spectrum", "Drive Frequency (GHz)")


def plot_simple_spectrum(exp, session, qubit, **kwargs):
    x, amp, phase = _spectrum_data(exp, session, qubit, 0, "drive_line")
    return _line_pair(x, amp, phase, f"{qubit.uid} Spectrum near Transition", "Drive Frequency (GHz)")


def plot_flux_sweep_trace(exp, session, qubit, **kwargs):
    acquired = _results(session)
    freqs = np.asarray(acquired.axis[1]) + _lo(exp, qubit)
    data = remove_local_phase_delay(np.asarray(acquired.data), freqs, _delay(exp, qubit))
    return _heat_pair(np.asarray(acquired.axis[0]) * 1e6, freqs,
                      np.abs(data).T, np.unwrap(np.angle(data), axis=1).T,
                      f"{qubit.uid} Resonator Current Response", "Current (uA)", "Readout Frequency (GHz)")


def plot_punchout(exp, session, qubit, data_type="Phase", **kwargs):
    acquired = _results(session)
    freqs = np.asarray(acquired.axis[1]) + _lo(exp, qubit)
    data = remove_local_phase_delay(np.asarray(acquired.data), freqs, _delay(exp, qubit))
    amp_axis = np.asarray(acquired.axis[0])
    power = 10 * np.log10(amp_axis ** 2) + exp.signals[f"{qubit.uid}/measure_line"].calibration.range
    amplitude = np.abs(data)
    phase = np.unwrap(np.angle(data), axis=1)
    phase -= np.mean(phase, axis=1, keepdims=True)
    norm_db = np.log10((amplitude.T / np.mean(amplitude, axis=1)).T)
    z = phase.T if data_type == "Phase" else norm_db.T if data_type == "Amplitude" else None
    if z is None:
        raise ValueError("data_type must be 'Phase' or 'Amplitude'")
    fig = make_subplots(rows=1, cols=2, shared_yaxes=True,
                        subplot_titles=("Readout amplitude", "Effective power"))
    for col, x, label in ((1, amp_axis, "Pulse Amplitude at Max Power"),
                          (2, power, "Effective dBm at Max Amp")):
        fig.add_trace(go.Heatmap(x=x, y=freqs, z=z, colorscale="Viridis",
                                 colorbar=dict(title=data_type), name=data_type,
                                 hovertemplate=f"{label}: %{{x:.6g}}<br>Frequency: %{{y:.6g}}<br>Value: %{{z:.6g}}<extra></extra>"), row=1, col=col)
        fig.update_xaxes(title_text=label, type="log" if col == 1 else None, row=1, col=col)
    fig.update_yaxes(title_text="Readout Frequency (GHz)", row=1, col=1)
    return _layout(fig, f"{qubit.uid} Punchout ({data_type})", 600)


def _flux_spectrum(exp, session, qubit, full):
    acquired = _results(session)
    current = np.asarray(acquired.axis[0][0])
    if full:
        drive_awg = np.asarray(acquired.axis[2])
        drive_lo = np.asarray(acquired.axis[1])
        drive = np.concatenate([lo + drive_awg for lo in drive_lo])
    else:
        drive = np.asarray(acquired.axis[1]) + _lo(exp, qubit, "drive_line")
    data = np.asarray(acquired.data).reshape((current.size, drive.size))
    data = data - np.mean(data, axis=1, keepdims=True)
    phase = np.angle(data)
    phase -= np.mean(phase, axis=1, keepdims=True)
    return current * 1e6, drive, np.abs(data).T, phase.T


def plot_flux_sweep_full_spectrum(exp, session, qubit, **kwargs):
    x, y, amp, phase = _flux_spectrum(exp, session, qubit, True)
    return _heat_pair(x, y, amp, phase, f"{qubit.uid} Two Tone Spectroscopy", "Current (uA)", "Drive Frequency (GHz)")


def plot_flux_sweep_spectrum(exp, session, qubit, **kwargs):
    x, y, amp, phase = _flux_spectrum(exp, session, qubit, False)
    return _heat_pair(x, y, amp, phase, f"{qubit.uid} Two Tone Spectroscopy", "Current (uA)", "Drive Frequency (GHz)")


def plot_twpa_optimization(exp, session, qubit, **kwargs):
    acquired = _results(session)
    data = np.asarray(acquired.data)
    return _heat_pair(np.asarray(acquired.axis[0]) * 1e6, np.asarray(acquired.axis[1]) * 1e6,
                      np.log10(np.abs(data)).T, np.angle(data).T,
                      f"{qubit.uid} Resonator TWPA Response",
                      acquired.axis_name[0], acquired.axis_name[1])


def plot_dual_flux_sweep(exp, session, qubit, **kwargs):
    acquired = _results(session)
    data = np.asarray(acquired.data)
    return _heat_pair(np.asarray(acquired.axis[0]) * 1e6, np.asarray(acquired.axis[1]) * 1e6,
                      np.log10(np.abs(data)).T, np.angle(data).T,
                      f"{qubit.uid} Resonator 2D Flux Response",
                      acquired.axis_name[0], acquired.axis_name[1])


def _fit_trace(fig, row, x, y, model, params, name):
    if params is not None:
        dense = np.linspace(np.min(x), np.max(x), 501)
        fig.add_trace(go.Scatter(x=dense, y=model(dense, *params), mode="lines",
                                 line=dict(color="red"), name=name), row=row, col=1)


def plot_x90_tuneup(exp, session, qubit, **kwargs):
    acquired = _results(session)
    x = np.asarray(acquired.axis[0]); data = np.asarray(acquired.data)
    amp = np.abs(data); phase = np.unwrap(np.angle(data))
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, subplot_titles=("Amplitude", "Phase"))
    fig.add_trace(go.Scatter(x=x, y=amp, mode="markers", name="Amplitude"), row=1, col=1)
    fig.add_trace(go.Scatter(x=x, y=phase, mode="markers", name="Phase"), row=2, col=1)
    for row, values, guess in ((1, amp, (10, 0, .5, 0)), (2, phase, (10, 0, .5, 0))):
        try:
            params, _ = oscillatory.fit(x, values, *guess)
            _fit_trace(fig, row, x, values, oscillatory, params, "Fit")
        except Exception:
            pass
    fig.update_xaxes(title_text="Rabi Pulse Amplitude", row=2, col=1)
    return _layout(fig, f"{qubit.uid} Amplitude Sweep", 650)


def _decay_plot(exp, session, qubit, echo=False):
    acquired = _results(session); x = np.asarray(acquired.axis[0]); data = np.asarray(acquired.data)
    amp = np.abs(data); phase = np.unwrap(np.angle(data)); phase -= np.mean(phase)
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, subplot_titles=("Amplitude", "Phase"))
    for row, values in ((1, amp), (2, phase)):
        fig.add_trace(go.Scatter(x=x * 1e6, y=values, mode="markers", name=("Amplitude" if row == 1 else "Phase")), row=row, col=1)
        try:
            guess = (1e6, 0, 1) if echo else ((2e6, 0, 1e5, .1) if row == 1 else (1e6, 0, 1e6, .5, 0))
            model = exponential_decay if echo else oscillatory_decay
            params, _ = model.fit(x, values, *guess)
            dense = np.linspace(x[0], x[-1], 501)
            fig.add_trace(go.Scatter(x=dense * 1e6, y=model(dense, *params), mode="lines", name="Fit"), row=row, col=1)
        except Exception:
            pass
    fig.update_xaxes(title_text="Time Delay (us)", row=2, col=1)
    return _layout(fig, f"{qubit.uid} {'T2 Echo' if echo else 'Ramsey Oscillations'}", 650)


def plot_T1_exp(exp, session, qubit, **kwargs):
    acquired = _results(session); x = np.asarray(acquired.axis[0]); phase = np.unwrap(np.angle(acquired.data)); phase -= np.mean(phase)
    fig = go.Figure(go.Scatter(x=x * 1e6, y=phase, mode="markers", name="Phase"))
    try:
        params, _ = exponential_decay.fit(x, phase, 1 / 50e-6, .08, .1)
        dense = np.linspace(x[0], x[-1], 501)
        fig.add_trace(go.Scatter(x=dense * 1e6, y=exponential_decay(dense, *params), name="Fit"))
    except Exception:
        pass
    fig.update_xaxes(title="Delay (us)"); fig.update_yaxes(title="Phase")
    return _layout(fig, f"{qubit.uid}'s T1", 500)


def plot_T2_star(exp, session, qubit, **kwargs):
    return _decay_plot(exp, session, qubit, echo=False)


def plot_T2_echo(exp, session, qubit, **kwargs):
    return _decay_plot(exp, session, qubit, echo=True)


_RENDERERS: dict[str, Callable[..., go.Figure]] = {
    "TWPA Optimization": plot_twpa_optimization,
    "Global Trace": plot_global_resonator_trace,
    "Local Resonator Trace": plot_local_resonator_trace,
    "Punchout": plot_punchout,
    "Flux Sweep Trace": plot_flux_sweep_trace,
    "Full Spectrum": plot_full_spectrum,
    "Simple Spectrum": plot_simple_spectrum,
    "Flux Sweep Full Spectrum": plot_flux_sweep_full_spectrum,
    "Flux Sweep Spectrum": plot_flux_sweep_spectrum,
    "2D Flux Sweep": plot_dual_flux_sweep,
    "X90 Tuneup": plot_x90_tuneup,
    "T1 Exp": plot_T1_exp,
    "T2 Star": plot_T2_star,
    "T2 Echo": plot_T2_echo,
}


def plot_exp(exp: Experiment, session: Session, qubit, **kwargs) -> go.Figure:
    """Render an experiment as an interactive Plotly figure."""
    try:
        renderer = _RENDERERS[exp.uid]
    except KeyError as exc:
        supported = ", ".join(_RENDERERS)
        raise ValueError(f"Unsupported experiment UID {exp.uid!r}. Supported: {supported}") from exc
    return renderer(exp, session, qubit, **kwargs)


def update_colorbar_limits(fig: go.Figure, new_min: float, new_max: float):
    """Update all heatmap color scales in a Plotly figure."""
    updated = False
    for trace in fig.data:
        if isinstance(trace, go.Heatmap):
            trace.update(zmin=new_min, zmax=new_max)
            updated = True
    return updated


__all__ = ["plot_exp", "update_colorbar_limits"] + [
    renderer.__name__ for renderer in _RENDERERS.values()
]
