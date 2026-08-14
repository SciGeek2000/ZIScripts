# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Script for resonator data acqusition and characterization

Reference for if bandwidth and averaging:
http://anlage.umd.edu/Microwave%20Measurements%20for%20Personal%20Web%20Site/5980-2778EN.pdf


TODO: 
-calculate the confidence interval for qint
-add weighting to fit
-load fridge attenuation from file 
    what kind of file? csv, mat file? maybe mat file in standard format
-load fridge temp
-plot result for a given photon number

-auto peak find and auto-electrical delay. give a range to search over and a threshold Q. 

change smith data to complex
add option to specify how wide the span should be in terms of linewidths

-give option to plan a sequence of power steps based on the estimated photon number. will require the min and max vna powers. is there a command to get this?
-JM suggests 0.5 photons to 1e6 photons in 3dB steps. 
-

#### SETTINGS FOR AUTOMATICALLY SETTING POWER RANGE ######
powerStep = 3 #size of the power step in dB
minPhoton = 0.5 # minimum power in photons
maxPhoton = 1e6 # maximum power in photons
photons = np.power(10,1/20.0*np.linspace(20*np.log10(minPhoton),20*np.log10(maxPhoton),np.ceil(20*np.log10(maxPhoton/minPhoton)/powerStep))


FIX AGILENT VNA SCRIPT TO REMOVE %0.03E

"""
from __future__ import division
from __future__ import print_function
import numpy as np
import lmfit as lm
import numpy as np
# from labrad.units import s, Hz

def powerToPhotons(power=None, qext=None, q=None, f0=None, fridgeAttenuation=None):
    """Calculate the power in the resonator. ref? what is that constant? derive"""
    h = 6.626e-34
    pwatts = 0.001 * np.power(10, (power - np.abs(fridgeAttenuation)) / 10.0)
    photons = pwatts / np.pi * np.square(q) / (qext * h * np.square(f0))
    return photons

def hanger_resonator_params(A, f_inf, f_zero, tau=0, covar = None):
    '''Given generic resonator parameters, 

        Arguements:
        A: Overall complex amplitude
        f_inf: point in the frequency doamin mapping to infinity in the
                complex scattering plane. (aka a pole)
        f_zero: point in the frequency doamin mapping to zero in the
                complex scattering plane. (aka a zero)
        tau: real electrical delay
        covar: optional covariance matrix

        Returns:
        Dictionary containing relevent resonator data. if covar is specified, 
            the returned dictionary will also contain standard deviations.'''
    f0 = np.real(f_inf)
    f_int = np.real(f_zero)
    kappa = 2*np.imag(f_inf)
    kappa_int = 2*np.imag(f_zero)
    kappa_ext_complex = 2*(f_zero - f_inf) * 1j
    param_dict = dict()
    param_dict['a'] = np.real(A)
    param_dict['b'] = np.imag(A)
    param_dict['f0'] = f0
    param_dict['kappa'] = kappa
    param_dict['kappa_int'] = kappa_int
    param_dict['Q'] = f0 / kappa
    param_dict['Qi'] = f0 / kappa_int
    param_dict['Qe'] = f0 / abs(kappa_ext_complex)
    param_dict['phi'] = np.angle(kappa_ext_complex + np.pi)%(2*np.pi) - np.pi
    param_dict['tau'] = tau
    if covar is None:
        return param_dict
    # compute the standard deviation for the various quantities
    transform_vectors = dict()
    transform_vectors['a'] = np.array([1,0,0,0,0,0,0])
    transform_vectors['b'] = np.array([0,1,0,0,0,0,0])
    transform_vectors['f0'] = np.array([0,0,1,0,0,0,0])
    transform_vectors['kappa'] = np.array([0,0,0,2,0,0,0])
    transform_vectors['kappa_int'] = np.array([0,0,0,0,0,2,0])
    transform_vectors['Q'] = np.array([0,0,1/kappa, -2*f0/kappa**2,0,0,0])
    transform_vectors['Qi'] = np.array([0,0,1/kappa_int,0,0,-2*f0/kappa_int**2,0])
    transform_vectors['Qe'] = np.array([0,0,
                                (kappa-kappa_int)**2 + 4*f_int*(f_int-f0),
                                2*f0*(kappa_int-kappa),
                                4*f0*(f0-f_int),
                                2*f0*(kappa-kappa_int),
                                0])/abs(kappa_ext_complex)**3
    transform_vectors['phi'] = np.array([0,0,
                                        2*(kappa_int-kappa),
                                        4*(f0-f_int),
                                        2*(kappa-kappa_int),
                                        4*(f_int-f0),
                                        0])/abs(kappa_ext_complex)**2

    transform_vectors['tau'] = np.array([0,0,0,0,0,0,1])

    # take v.covar.v to get the variance of the new variable for gradient v
    for key in transform_vectors:
        vec = transform_vectors[key]
        param_dict[key+'_sd'] = np.sqrt(np.dot(np.dot(covar,vec),vec))
    return param_dict

def reflection_resonator_params(A, f_inf, f_zero, tau, covar=None):
    '''Given generic resonator parameters, 

        Arguements:
        A: Overall complex amplitude
        f_inf: point in the frequency doamin mapping to infinity in the
                complex scattering plane. (aka a pole)
        f_zero: point in the frequency doamin mapping to zero in the
                complex scattering plane. (aka a zero)
        tau: real electrical delay
        covar: optional covariance matrix

        Returns:
        Dictionary containing relevent resonator data. if covar is specified, 
            the returned dictionary will also contain standard deviations.'''
    f0 = np.real(f_inf)
    f_int = np.real(f_zero)
    kappa = 2*np.imag(f_inf)
    kappa_int = np.imag(f_inf)+np.imag(f_zero)
    kappa_ext_complex = np.imag(f_inf)-np.imag(f_zero)
    param_dict = dict()
    param_dict['a'] = np.real(A)
    param_dict['b'] = np.imag(A)
    param_dict['f0'] = f0
    param_dict['kappa'] = kappa
    param_dict['kappa_int'] = kappa_int
    param_dict['kappa_ext'] = np.abs(kappa_ext_complex)
    param_dict['Q'] = f0 / kappa
    param_dict['Qe'] = f0 / abs(kappa_ext_complex)
    param_dict['Qi'] = f0 / kappa_int
# To correct for Qi using DCM
    phi_i=np.angle(f_inf-f_zero)-np.pi/2
    Q_e_i=f0 / abs(kappa_ext_complex)
    param_dict['Qi'] = ((kappa_int/f0)+(1-np.cos(phi_i))/Q_e_i)**-1
    #param_dict['Qi'] = (kappa_int/f0)**-1
    #param_dict['Qe'] = f0 / abs(kappa_ext_complex)
    #param_dict['phi'] = np.angle(kappa_ext_complex + np.pi)%(2*np.pi) - np.pi
    param_dict['phi'] = np.angle(f_inf-f_zero)-np.pi/2# np.arctan((np.real(f_zero)-np.real(f_inf))/(np.imag(f_inf)-np.imag(f_zero)))
    param_dict['tau'] = tau
    if covar is None:
        return param_dict
       # compute the standard deviation for the various quantities TBD
        
#['A_r', 'A_i','f_inf_r','f_inf_i','f_zero_r','f_zero_i', 'tau']
    else:
	    transform_vectors = dict()
	    transform_vectors['a'] = np.array([1,0,0,0,0,0,0])
	    transform_vectors['b'] = np.array([0,1,0,0,0,0,0])
	    transform_vectors['f0'] = np.array([0,0,1,0,0,0,0])
	    transform_vectors['kappa'] = np.array([0,0,0,2,0,0,0])
	    transform_vectors['kappa_int'] = np.array([0,0,0,0,0,2,0])
	    transform_vectors['Q'] = np.array([0,0,1/kappa, -0.5*f0/kappa**2,0,0,0])
	    transform_vectors['Qi'] = np.array([0,0,1/kappa_int,-f0/kappa_int**2,0,-f0/kappa_int**2,0])
	    transform_vectors['Qe'] = np.array([0,0,1/abs(kappa_ext_complex), -f0/abs(kappa_ext_complex)**2,0,f0/abs(kappa_ext_complex)**2,0])
	    # transform_vectors['phi'] = np.array([0,0,
	    #                                     2*(kappa_int-kappa),
	    #                                     4*(f0-f_int),
	    #                                     2*(kappa-kappa_int),
	    #                                     4*(f_int-f0),
	    #                                     0])/abs(kappa_ext_complex)**2

	    transform_vectors['tau'] = np.array([0,0,0,0,0,0,1])

	    # take v.covar.v to get the variance of the new variable

	    for key in transform_vectors:
	        vec = transform_vectors[key]
	        param_dict[key+'_sd'] = np.sqrt(np.dot(np.dot(covar,vec),vec))
	    return param_dict


def show_reflection_resonator_params(A, f_inf, f_zero, tau=0, covar=None):
	"""Calculate and print reflection-resonator parameters.

	This is a convenience wrapper around :func:`reflection_resonator_params`
	for use in a notebook or interactive session.  The returned dictionary is
	unchanged, while the printed values use convenient frequency units.

	Parameters
	----------
	A : complex
	    Overall complex amplitude.
	f_inf : complex
	    Complex pole returned by ``resonator_regression``.
	f_zero : complex
	    Complex zero returned by ``resonator_regression``.
	tau : float, optional
	    Electrical delay in seconds.
	covar : array-like, optional
	    7x7 covariance matrix in the parameter order used by the fit.

	Returns
	-------
	dict
	    The same dictionary returned by ``reflection_resonator_params``.
	"""
	params = reflection_resonator_params(A, f_inf, f_zero, tau, covar=covar)

	print("Reflection resonator parameters:")
	print(f"  f0        = {params['f0'] / 1e9:.9f} GHz")
	print(f"  kappa     = {params['kappa'] / 1e6:.6g} MHz")
	print(f"  kappa_int = {params['kappa_int'] / 1e6:.6g} MHz")
	print(f"  kappa_ext = {params['kappa_ext'] / 1e6:.6g} MHz")
	print(f"  Q         = {params['Q']:.6g}")
	print(f"  Qi        = {params['Qi']:.6g}")
	print(f"  Qe        = {params['Qe']:.6g}")
	print(f"  phi       = {params['phi']:.6g} rad")
	print(f"  tau       = {params['tau'] * 1e9:.6g} ns")

	if covar is not None:
	    print("  uncertainties:")
	    for key in ('f0', 'kappa', 'kappa_int', 'kappa_ext', 'Q', 'Qi', 'Qe', 'phi', 'tau'):
	        sd_key = f'{key}_sd'
	        if sd_key in params:
	            print(f"    {key:>10}_sd = {params[sd_key]:.6g}")

	return params


def plot_reflection_resonator_fit(
    A,
    f_inf,
    f_zero,
    tau=0,
    frequency=None,
    IQ_data=None,
    num_points=2001,
    show=True,
):
    """Plot a reflection-resonator fit using the same three panels as analysis.

    The panels show the IQ plane, amplitude, and unwrapped phase. If ``IQ_data``
    is supplied, it is plotted as points and the resonator model is overlaid.
    If it is omitted, only the model curve is plotted.

    Parameters
    ----------
    A, f_inf, f_zero, tau :
        Resonator parameters accepted by :func:`resonator_f_to_S`.
    frequency : array-like, optional
        Frequency samples in Hz. If supplied, these define the model span and
        are also used for ``IQ_data``. If omitted, a span of 10 linewidths
        centered on ``real(f_inf)`` is generated.
    IQ_data : array-like, optional
        Measured complex scattering data corresponding to ``frequency``.
    num_points : int, optional
        Number of points in the smooth model curve when ``frequency`` is not
        supplied, or when the supplied frequency span is used.
    show : bool, optional
        Call ``plt.show()`` before returning. Set to ``False`` in scripts that
        manage figure display themselves.

    Returns
    -------
    tuple
        ``(fig, ax)`` containing the Matplotlib figure and three axes.
    """
    import matplotlib.pyplot as plt

    if frequency is None and IQ_data is not None:
        raise ValueError("frequency is required when IQ_data is supplied")

    if frequency is None:
        f0 = np.real(f_inf)
        linewidth = abs(2 * np.imag(f_inf))
        if linewidth == 0:
            raise ValueError("f_inf must have a non-zero imaginary part")
        frequency = np.linspace(
            f0 - 5 * linewidth,
            f0 + 5 * linewidth,
            num_points,
        )
    else:
        frequency = np.asarray(frequency, dtype=float)
        if frequency.ndim != 1 or frequency.size < 2:
            raise ValueError("frequency must be a one-dimensional array with at least two points")

    if IQ_data is not None:
        IQ_data = np.asarray(IQ_data, dtype=complex)
        if IQ_data.shape != frequency.shape:
            raise ValueError("IQ_data and frequency must have the same shape")

    f_dense = np.linspace(frequency.min(), frequency.max(), num_points)
    S_fit = resonator_f_to_S(f_dense, A, f_inf, f_zero, tau)

    fig, ax = plt.subplots(1, 3, figsize=(15, 5))
    if IQ_data is not None:
        ax[0].scatter(np.real(IQ_data), np.imag(IQ_data), s=15, label="data")
        ax[1].scatter(frequency, np.abs(IQ_data), s=15, label="data")
        ax[2].scatter(frequency, np.unwrap(np.angle(IQ_data)), s=15, label="data")

    ax[0].plot(np.real(S_fit), np.imag(S_fit), color="C1", label="fit")
    ax[0].set_title("Reflection Resonator IQ Plane")
    ax[0].set_xlabel("I (a.u.)")
    ax[0].set_ylabel("Q (a.u.)")
    ax[0].set_aspect("equal", adjustable="datalim")

    ax[1].plot(f_dense, np.abs(S_fit), color="C1", label="fit")
    ax[1].set_title("Reflection Resonator Amplitude")
    ax[1].set_xlabel("Frequency (Hz)")
    ax[1].set_ylabel("Amplitude (a.u.)")

    ax[2].plot(f_dense, np.unwrap(np.angle(S_fit)), color="C1", label="fit")
    ax[2].set_title("Reflection Resonator Phase")
    ax[2].set_xlabel("Frequency (Hz)")
    ax[2].set_ylabel("Phase (rad)")

    for axis in ax:
        axis.grid()
        axis.legend()
    fig.tight_layout()

    if show:
        plt.show()
    return fig, ax


def _params_to_complex_vals(params):
    '''internal use converting dictionary to complex values.'''
    A_r = params['A_r'].value
    A_i = params['A_i'].value
    f_inf_r = params['f_inf_r'].value
    f_inf_i = params['f_inf_i'].value
    f_zero_r = params['f_zero_r'].value
    f_zero_i = params['f_zero_i'].value
    tau = params['tau'].value

    A = A_r + A_i * 1j # scaling Amplitude
    f_inf = f_inf_r + f_inf_i * 1j # pole in the complex scattering plane
    f_zero = f_zero_r + f_zero_i * 1j # zero of the complex scattering plane
    return (A, f_inf, f_zero, tau)

def resonator_f_to_S(f, A, f_inf, f_zero, tau=0):
    '''Converts frequency data to scattering data given generic resonator
        parameters.

        Arguements:
        f: frequency or frequencies to be converted
        A: Overall complex amplitude
        f_inf: point in the frequency doamin mapping to infinity in the
                complex scattering plane. (aka a pole)
        f_zero: point in the frequency doamin mapping to zero in the
                complex scattering plane. (aka a zero)
        tau: real electrical delay'''
    return A * (f-f_zero)/(f-f_inf) * np.exp(1j * (f - np.real(f_inf)) * tau)

def residual(params, f, data, loss='linear'):
    """Return the residual vector used by the ``lmfit`` optimizer.

    ``lmfit`` minimizes the sum of squares of the returned vector.  The
    default ``linear`` loss therefore gives the usual complex least-squares
    objective.  ``quartic`` multiplies each complex residual by its magnitude,
    making the minimized objective proportional to the fourth power of the
    residual magnitude and consequently emphasizing large outliers.
    """
    if loss not in ('linear', 'quadratic', 'quartic'):
        raise ValueError(
            "loss must be one of 'linear', 'quadratic', or 'quartic'"
        )

    S21 = resonator_f_to_S(f, *_params_to_complex_vals(params))
    complex_residual = S21 - data
    if loss in ('linear', 'quadratic'):
        return complex_residual.view(np.float64)

    # Weight both I and Q components of each point by the point's complex
    # residual magnitude. The optimizer's sum-of-squares is then
    # sum(abs(complex_residual)**4), rather than sum(abs(complex_residual)**2).
    return (complex_residual * np.abs(complex_residual)).view(np.float64)

def resonator_regression(frequency, smith, tau0=0, f0=None, loss='linear'):
    '''Resonator regression for dimensionless units.
        Arguements:
            frequency: list of frequencies
            smith: list of complex scattering data
            tau0: initial guess for the electrical delay (seconds). Useful
                 to seed the nonlinear fit with a known/estimated cable delay
                 (e.g. from a separate delay calibration) instead of starting
                 from zero, which can help convergence when the delay is
                 large relative to the frequency span. Defaults to 0,
                 preserving prior behavior.
            f0: optional initial guess for the resonator frequency (Hz). When
                supplied, it seeds the real parts of both the fitted pole and
                zero. If omitted, both values are estimated from the data.
            loss: objective used by the nonlinear fit. ``'linear'`` and
                ``'quadratic'`` use the usual least-squares objective;
                ``'quartic'`` minimizes the fourth power of each complex
                residual magnitude and emphasizes large outliers. Defaults to
                ``'linear'``.

        Returns a tuple containing:
            0) list of generalized resonator parameters:
                0) A, overall complex amplitude
                1) f_inf, complex frequency where smith(f_inf) = infinity
                2) f_0, complex frequency where smith(f_0) = 0
                3) electrical delay
            1) covariance matrix with the following basis
                ['A_r', 'A_i','f_inf_r','f_inf_i','f_zero_r','f_zero_i', 'tau']
            2) reduced chi value'''

    # f_scaled is a rescaled frequency so matrix inversion doesn't get too singular during the initial guess

    df = frequency[-1] - frequency[0]
    f_scaled = (frequency - frequency[0])/df
    smith = np.array(smith)

    # pre-rotate out the initial delay guess before the linear (Mobius) autoguess,
    # so the linear pole/zero estimate isn't corrupted by a large unremoved delay.
    # tau0 is added back into the initial parameter guess below so the nonlinear
    # fit still starts from tau0, not from 0.
    smith_derot = smith * np.exp(-1j * tau0 * 2 * np.pi * frequency)

    # autoguess some starting values
    A = np.ones((len(frequency),3),dtype=complex)
    A[:,0] = f_scaled
    A[:,2] = -smith_derot
    y = np.multiply(f_scaled, smith_derot)
    mobius_fit = np.linalg.lstsq(A,y)[0]
    A = mobius_fit[0]
    f_inf = -mobius_fit[2]*df + frequency[0]
    f_zero = -mobius_fit[1]/mobius_fit[0]*df + frequency[0]
    
    # create a set of Parameters
    params = lm.Parameters()
    params.add('A_r', value=np.real(A))
    params.add('A_i', value=np.imag(A))
    if f0 is not None:
        if not np.isfinite(f0):
            raise ValueError('f0 must be a finite frequency in Hz')
        f_inf_r0 = f0
        f_zero_r0 = f0
    else:
        f_inf_r0 = np.real(f_inf)
        f_zero_r0 = np.real(f_zero)
    params.add('f_inf_r', value=f_inf_r0)
    params.add('f_inf_i', value=np.imag(f_inf))
    params.add('f_zero_r', value=f_zero_r0)
    params.add('f_zero_i', value=np.imag(f_zero))
    params.add('tau', value=tau0)

    # Validate before starting the optimizer so invalid options fail clearly.
    if loss not in ('linear', 'quadratic', 'quartic'):
        raise ValueError(
            "loss must be one of 'linear', 'quadratic', or 'quartic'"
        )

    # best Minimizer class documentation i've found so far
    # https://github.com/lmfit/lmfit-py/blob/master/doc/fitting.rst#id81
    mini = lm.Minimizer(
        residual,
        params,
        fcn_args=(frequency, smith),
        fcn_kws={'loss': loss},
    )
    minimized = mini.minimize()
    return (_params_to_complex_vals(minimized.params), minimized.covar, minimized.redchi)

# useful strings for datastore server
resonator_description = '''A: Overall complex amplitude
        f_inf: point in the frequency doamin mapping to infinity in the
                complex scattering plane. (aka a pole)
        f_zero: point in the frequency doamin mapping to zero in the
                complex scattering plane. (aka a zero)
        tau: real electrical delay'''
resonator_variables = ['Amplitude','f_inf','f_zero','tau']
resonator_covar_variables = ['A_r', 'A_i','f_inf_r','f_inf_i','f_zero_r','f_zero_i', 'tau']
