'''Could later provide a global set of figure properties to make graphs look ~extra fancy~!'''

from matplotlib import pyplot as plt

custom_style = {
    "figure.figsize": (8, 5),
    "figure.frameon": True,
    "figure.facecolor": '#ffffff',
    "figure.edgecolor": 'black',

    "text.color": 'black',

    "scatter.marker": '.',

    "axes.titlesize": 10,
    "axes.titleweight": 'semibold',
    "axes.labelsize": 10,
    "axes.labelweight": 'semibold',
    "axes.linewidth": 1.0, #2.5
    "axes.titlepad": 3.5,
    "axes.labelpad": 3,

    "xtick.bottom": True,
    "xtick.direction": 'in',
    "xtick.minor.visible": False,
    "xtick.labelsize": 10,
    "xtick.major.width": 2,

    "ytick.left": True,
    "ytick.direction": 'in',
    "ytick.minor.visible": False,
    "ytick.labelsize": 10,
    "ytick.major.width": 2,
}

plt.rcParams.update(custom_style)

'''
DejaVu Serif,
Bitstream Vera Serif,
Computer Modern Roman,
New Century Schoolbook,
Century Schoolbook L,
Utopia,
ITC Bookman,
Bookman,
Nimbus Roman No9 L,
Times New Roman,
Times,
Palatino,
Charter,
serif
'''
# "font.family": 'Computer Modern Roman', # FONT FAMILY NOT FOUND
# "font.serif": 'Computer Modern Roman', # FONT FAMILY NOT FOUND