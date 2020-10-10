# -*- coding: utf-8 -*-
"""
Program name: plot_difficulty_index.py

Plot forecast decision difficulty indices.
Plot a set of decision difficulty indices for forecasts of postive
definite quantities such as wind speed and wave height.

"""

import numpy as np
import matplotlib.pyplot as plt
from metcalcpy.calc_difficulty_index import forecast_difficulty as di
from metcalcpy.piecewise_linear import PiecewiseLinear as plin
from mycolormaps import spectral, stoplight

__author__ = 'Bill Campbell (NRL) and Lindsay Blank (NCAR)'
__version__ = '0.1.0'
__email__ = 'met_help@ucar.edu'

# Enforce positive definiteness of quantities such as standard deviations
EPS = np.finfo(np.float32).eps
# Only allow 2D fields for now
FIELD_DIM = 2

def plot_field(field, vmin, vmax, xlab, ylab, title):
    """Auxiliary plot routine."""
    fig, ax = plt.subplots(figsize=(15, 10))

    # Set the tick labels font
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_fontname('Arial')
        label.set_fontsize(18)
        label.set_fontweight('normal')

    plt.imshow(field, cmap='jet', vmin=vmin, vmax=vmax)

    # Set the font dictionaries (for plot title and axis titles)
    title_font = {'fontname': 'Arial', 'size': '32', 'color': 'black',
                  'weight': 'bold', 'verticalalignment': 'bottom'}
    axis_font = {'fontname': 'Arial', 'size': '24', 'weight': 'bold'}

    plt.xlabel(xlab, **axis_font)
    plt.ylabel(ylab, **axis_font)
    plt.title(title, **title_font)
    plt.colorbar()
    plt.show()

    return fig

def main():
    """
    Calculate and plot public version (v7) of difficulty index.

    Returns
    -------
    None.

    """
    plt.close('all')
    nlon = 18
    nlat = 9
    nmembers = 10
    np.random.seed(12345)
    # Wave heights and wind speeds generally follow the Rayleigh distribution,
    # which is a Weibull distribution with a scale factor of 2,
    # and any shape parameter.
    # If the shape parameter is 1, then it is the same as a chi-square
    # distribution with 2 dofs.
    # Expected value E[x] = sigma * sqrt(pi/2)
    # mean_windspeed = 6.64  # meters/second
    xunits = 'feet'
    mean_height = 11.0  # mean wave height in feet
    # var_height = mean_height * mean_height * ((4.0 - np.pi) / 2.0)
    mode_height = np.sqrt(2.0 / np.pi) * mean_height
    fieldijn = np.random.rayleigh(scale=mode_height,
                                  size=(nlat, nlon, nmembers))
    muij = np.mean(fieldijn, axis=-1)
    pertijn = fieldijn - np.dstack([muij] * nmembers)
    sigmaij = np.sqrt(np.mean(pertijn * pertijn, axis=-1))
    threshold = 9.0
    regularizer = 0.01
    smax = 9.0
    sigma_max = smax + np.zeros_like(sigmaij)
    thresh_eps = 2.0
    kwargs = {'thresh_eps': thresh_eps, 'threshold_type': 'proximity'}

    # Calculate the difficulty index. 
    dijfd = di(sigmaij, muij, threshold, fieldijn, Aplin=None, sigma_over_mu_ref=EPS)
    
    # Plot the difficulty index.
    imfd = plot_field(dijfd, 0.0, 1.0, 'Longitude', 'Latitude',
            'Forecast Difficulty Index')

    imfd_fmt = 'png'
    imfd_name = './test_diff_index.' + imfd_fmt
    print(f'Saving {imfd_name}...\n')
    imfd.savefig(imfd_name, format=imfd_fmt)

    return imfd


if __name__ == "__main__":
    imfd = main()
