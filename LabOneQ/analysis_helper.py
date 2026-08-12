from cProfile import label

from IPython.core.pylabtools import figsize
from matplotlib.patches import ArrowStyle
from helper import *
from qelement_helper import *
from qops_helper import *
from qubit_experiments import *
from scipy.optimize import curve_fit
import dill
import numpy as np 
import matplotlib.pyplot as plt 

def exp_analysis(exp: Experiment, session: Session, qubit, **kwargs):
    match exp.uid:
        case 'Flux Sweep Trace':
            analysis = analyze_flux_sweep_trace(exp, session, qubit, **kwargs)
            return analysis
        
        case '2D Flux Sweep': 
            analysis = analyze_2d_flux_sweep()
            return analysis 

def analyze_flux_sweep_trace(exp, session, qubit, **kwargs): # [ ] Normalize amplitude at each frequency value
    '''
    Returns a dictionary with amplitude and phase fits that map
    the current to the resonator's frequency
    '''
    my_results = session.get_results() # a deep copy of session.results
    my_acquired_results = my_results.acquired_results['results']
    freqs = my_acquired_results.axis[1] + exp.signals[f'{qubit.uid}/measure_line'].calibration.local_oscillator.frequency
    IQ_data = my_acquired_results.data
    amplitude = np.abs(IQ_data)
    phase = remove_local_phase_delay(IQ_data, freqs, exp.signals[f'{qubit.uid}/acquire_line'].calibration.port_delay)
    currents = my_acquired_results.axis[0]*1e6
    tracked_resonator = np.empty(amplitude.shape[0])

    def arctan_fit(freqs, omega, phs_offset, offset):
        '''Rough phase fitting after normalizing avg phase amplitude to zero'''
        phs_offset = phs_offset*1e9
        return 2*np.arctan(omega*(freqs-phs_offset)) + offset

    def make_ro_freq():
        '''A closure for new_ro_values which is to be assigned to a qubit'''
        old_currents = my_acquired_results.axis[0]
        old_values = tracked_resonator
        def res_to_current(new_currents: float|np.ndarray):
            new_ro_values = np.interp(new_currents, old_currents, old_values) # [ ] TODO: OFC HAS AN ISSUE REGARDING SWITCHING BETWEEN BRANCHES IF THE CURRENT SAMPLING IS NOT IDENTICAL, THE INTERPOLATION WILL BE WRONG/BAD
            return new_ro_values
        return res_to_current

    # for i, phs in enumerate(phase):
    #     try:
    #         (popt, b) = curve_fit(arctan_fit, freqs, phs, p0=[50e6, 6.8675e9/1e9, 1], bounds=([-np.inf, 1e9/1e9, -np.inf], [np.inf, 9e9/1e9, np.inf]),)
    #         opt_freq = popt[1]*1e9
    #         tracked_resonator[i] = opt_freq
    #     except Exception as e:
    #         tracked_resonator[i] = tracked_resonator[i-1]
    #         print(e)
    
    # Temporary solution is just picking out the argmin
    for i, amp in enumerate(amplitude):
        try:
            # (popt, b) = lorentzian.fit(freqs, amp, 1000e3, exp.signals[f'{qubit.uid}/measure_line'].calibration.local_oscillator.frequency, -1e7, 1)
            # opt_freq = popt[1]
            opt_freq = freqs[np.argmin(amp)]
            tracked_resonator[i] = opt_freq
        except Exception as e:
            tracked_resonator[i] = tracked_resonator[i-1]
            print(e)

    qubit.parameters.res_to_current = make_ro_freq()

    plt.scatter(currents, tracked_resonator) # [ ] It is currently plotting on phase even though it is argmin of amplitude for fitting
    # plt.ylim(6.8e9, 6.9e9)

    if 'save' in kwargs and kwargs['save'] is True:
        with open(f'make_ro_freq', 'wb') as f:
            dill.dump(make_ro_freq, f)

    return None


def analyze_2d_flux_sweep(results_list, labels = None, edge_margin_min=0.25, plot = True, **kwargs): 

    centers_uA = {} # label -> (x_uA, y_uA)
    centered = {} # label -> bool, False if the centre sits near a map edge
    margins = {} # label -> fractional distance to the nearest edge

    maps = {}

    #inputs 
    if labels is None: 
        labels = [f'map{i + 1}' for i in range(len(results_list))]
    if len(labels) != len(results_list): 
        raise ValueError(
            f'Got {len(labels)} labels for {len(results_list)} datasets.'
        )

    centers_index = {} #label ->(row, col) fractional indices 
    axes = {} #label -> (outer_axis, inner_axis)
    axis_names = None

    for label, results in zip(labels, results_list):
        
        acquired = results.acquired_results['results']
        outer = np.asarray(acquired.axis[0]) # x axis
        inner = np.asarray(acquired.axis[1]) # y axis
        names = (acquired.axis_name[0], acquired.axis_name[1])

        z = np.asarray(acquired.data).T

        if z.shape != (inner.size, outer.size):
            raise ValueError(
                f'{label}: expected data shape {(inner.size, outer.size)} '
                f'after transpose, got {z.shape}.'
            )
    
        #check dataset consistency 
        if axis_names is None:
            axis_names = names
        elif names != axis_names:
            raise ValueError(
                f'{label}: axes {names} do not match {axis_names}; '
                'the maps do not share a common flux space.'
            )

        #find centers
        r, c = find_symmetry_center(z)
        centers_index[label] = (r, c)
        axes[label] = (outer, inner)

        maps[label] = z

        x_uA = np.interp(c, np.arange(outer.size), outer) * 1e6
        y_uA = np.interp(r, np.arange(inner.size), inner) * 1e6
        centers_uA[label] = (x_uA, y_uA)

        margin_rows = min(r, inner.size - 1 - r) / (inner.size - 1)
        margin_cols = min(c, outer.size - 1 - c) / (outer.size - 1)
        edge_margin = float(min(margin_rows, margin_cols))
        centered[label] = edge_margin >= edge_margin_min
        margins[label] = edge_margin

    reference = labels[0]
    x0, y0 = centers_uA[reference]
    vectors = {
        label: (centers_uA[label][0] - x0, centers_uA[label][1] - y0)
        for label in labels[1:]
    }

    #compute parallel vectors 
    midlines = {}
    if len(labels) >= 3: 
        v1 = vectors[labels[1]]
        v2 = vectors[labels[2]]

        m1 = (x0 + v1[0]/2, y0 + v1[1]/2)
        m2 = (x0 + v2[0]/2, y0 + v2[1]/2)

        midlines = {
            f'mid_{labels[1]}': {'start': m1,
                                 'end': (m1[0] + v2[0], m1[1] + v2[1]),
                                 'delta': v2},
            f'mid_{labels[2]}': {'start': m2,
                                 'end': (m2[0] + v1[0], m2[1] + v1[1]),
                                 'delta': v1},
        }

    determinant = None

    #plotting 
    figs = []

    if plot: 
        views = [
            (lambda a: np.angle(a, deg = True), 'Phase (deg)', 'twilight_shifted'), 
            (np.abs, 'Magnitude', 'viridis'), 
        ]

        arrow_colors = ['red', 'cyan', 'lime', 'magenta']

        for quantity, qlabel, cmap in views: 
            vals = {label: quantity(maps[label]) for label in labels}
            vmin = min(v.min() for v in vals.values())
            vmax = max(v.max() for v in vals.values())

            fig, ax = plt.subplots(figsize = (8, 8))
            pcm  = None
            
            for label in labels: 
                outer, inner = axes[label]
                pcm = ax.pcolormesh(outer * 1e6, 
                                    inner * 1e6, 
                                    vals[label], 
                                    cmap = cmap, 
                                    shading = 'auto', 
                                    vmin = vmin, 
                                    vmax = vmax)
                xc, yc = centers_uA[label]
                ax.scatter(xc, yc, marker = '*', s = 260, facecolor = 'red', edgecolor = 'k', zorder = 5)
                ax.annotate(f'{label} ({xc:.1f}, {yc:.1f})', 
                            (xc, yc),
                            textcoords='offset points', 
                            xytext=(8, 8),
                            fontsize=8, 
                            color='k')

            x0, y0 = centers_uA[reference]
            for i, label in enumerate(vectors):
                ax.annotate('', xy=centers_uA[label], xytext=(x0, y0),
                            annotation_clip=False,
                            arrowprops=dict(arrowstyle='->', lw=2,
                                            color=arrow_colors[i % len(arrow_colors)]))
                dx, dy = vectors[label]
                ax.text(x0 + dx / 2, y0 + dy / 2, f'({dx:.0f}, {dy:.0f})',
                        color=arrow_colors[i % len(arrow_colors)],
                        fontsize=8, fontweight='bold',
                        ha='center', va='bottom')

            for j, md in enumerate(midlines.values()):
                ax.annotate('', xy=md['end'], xytext=md['start'],
                            annotation_clip=False,
                            arrowprops=dict(arrowstyle='->', color='k', lw=2))
                dx, dy = md['delta']
                t = 0.3 if j == 0 else 0.7          #see note below
                ax.text(md['start'][0] + t * dx, md['start'][1] + t * dy,
                        f'({dx:.0f}, {dy:.0f})',
                        color='k', fontsize=8, fontweight='bold',
                        ha='center', va='bottom')

            #dashed lines for reference only
            if len(labels) >= 3:
                corner = (x0 + vectors[labels[1]][0] + vectors[labels[2]][0],
                          y0 + vectors[labels[1]][1] + vectors[labels[2]][1])
                for label in (labels[1], labels[2]):
                    ax.plot([centers_uA[label][0], corner[0]],
                            [centers_uA[label][1], corner[1]],
                            ls='--', color='k', lw=1.5, zorder=4, clip_on=False)

            #everything is drawn by this point, so tight_layout sees it all
            fig.colorbar(pcm, ax = ax, label = qlabel)
            ax.set_xlabel(f'{axis_names[0]} (uA)')
            ax.set_ylabel(f'{axis_names[1]} (uA)')
            ax.set_title(f'Combined {qlabel} map with symmetry centers')
            fig.tight_layout()
            figs.append((fig, ax))


            #report the vectors as (x, y) 
            print(f'Lattice vectors from {reference}, (x, y) in uA:')

            for label, (dx, dy) in vectors.items():
                print(f'  {reference} -> {label}: ({dx:.3f}, {dy:.3f})')

            if midlines:
                print('Midline vectors, (x, y) in uA:')
                for name, md in midlines.items():
                    (sx, sy) = md['start']
                    (ex, ey) = md['end']
                    (dx, dy) = md['delta']
                    print(f'  {name}: ({sx:.3f}, {sy:.3f}) -> ({ex:.3f}, {ey:.3f}), '
                        f'delta=({dx:.3f}, {dy:.3f})')


    if len(labels) >= 3:
        (v1x, v1y), (v2x, v2y) = (vectors[labels[1]], vectors[labels[2]])
        determinant = float(v1x * v2y - v1y * v2x)

    return {
        'centers_uA': centers_uA, 
        'centers_index': centers_index, 
        'vectors_uA': vectors,  # two base vectors
        'reference': reference,
        'determinant_uA2': determinant,
        'axis_names': axis_names,   
        'midlines_uA': midlines,   # two black midline vectors 
        'units': 'uA',
        'centered': centered, 
        'edge_margins': margins, 
        'figures': figs, 
    }

#helper functions for analyze_flux_sweep_trace()

def clip_outliers(z, pct=99.0):
    mag = np.abs(z)
    hi = np.percentile(mag, pct)
    scale = np.minimum(1.0, hi / np.maximum(mag, 1e-30))
    return z * scale

def gaussian_subpixel(C, r0, c0):

    def offset(vm, v0, vp):
        vm, v0, vp = (np.log(max(v, 1e-12)) for v in (vm, v0, vp))
        denom = vm - 2 * v0 + vp
        return 0.0 if denom == 0 else float(np.clip(0.5 * (vm - vp) / denom, -1, 1))

    dr = offset(C[r0 - 1, c0], C[r0, c0], C[r0 + 1, c0]) if 0 < r0 < C.shape[0] - 1 else 0.0
    dc = offset(C[r0, c0 - 1], C[r0, c0], C[r0, c0 + 1]) if 0 < c0 < C.shape[1] - 1 else 0.0
    return r0 + dr, c0 + dc

def find_symmetry_center(z, window=True, clip_pct=99.0, min_overlap=0.5):
 
    z = clip_outliers(z, clip_pct)
    z = z - z.mean()
    Ny, Nx = z.shape

    #taper the edges so the discontinuity at the array boundary does not leak
    w = np.outer(np.hanning(Ny), np.hanning(Nx)) if window else np.ones((Ny, Nx))
    zw = z * w

    sy, sx = 2 * Ny - 1, 2 * Nx - 1
    F = np.fft.fft2(zw, s=(sy, sx))
    G = np.fft.fft2(np.conj(zw), s=(sy, sx))
    P = np.abs(np.fft.ifft2(F * G))

    Hf = np.fft.fft2(w, s=(sy, sx))
    env = np.abs(np.fft.ifft2(Hf * Hf))
    mask = env >= min_overlap * env.max()
    Pn = np.where(mask, P / np.maximum(env, 1e-12), 0.0)

    r0, c0 = np.unravel_index(np.argmax(Pn), Pn.shape)
    r, c = gaussian_subpixel(Pn, r0, c0)
    return r / 2.0, c / 2.0
