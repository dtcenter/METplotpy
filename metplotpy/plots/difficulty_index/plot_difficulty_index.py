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
import metplotpy.plots.difficulty_index.mycolormaps as mcmap

__author__ = 'Bill Campbell (NRL) and Lindsay Blank (NCAR)'
__version__ = '0.1.0'
__email__ = 'met_help@ucar.edu'

# Enforce positive definiteness of quantities such as standard deviations
EPS = np.finfo(np.float32).eps
# Only allow 2D fields for now
FIELD_DIM = 2

def plot_field(field, lats, lons, vmin, vmax,
        xlab, ylab, cmap, clab, title):
    """
    Parameters
    ----------
    field : 2D numpy array
        Field you want to plot (difficulty index)
    lats : 1D numpy array
        Latitude values
    lons : 1D numpy array
        Longitude values
    vmin : float
        Minimum value on the colorbar
    vmax : float
        Maximum value on the colorbar
    xlab : String
        x-axis label
    ylab : String
        y-axis label
    cmap: Matplotlib Colormap Class Object
        Color map for plot
    clab: String
        Label for colorbar
    title: String
        Plot title

    Returns
    -------
    fig : plot
        Difficulty index plot
    """

    X, Y = np.meshgrid(lons, lats, indexing='ij')
    fig, ax = plt.subplots(figsize=(8, 5))
    plt.title(title)
    if cmap is None:
        cmap = mcmap.stoplight()
    
    plt.pcolormesh(X, Y, field.T, shading='interp', cmap=cmap)
    cbar = plt.colorbar(orientation='horizontal', aspect=30)
    cbar.set_label(clab)
    plt.clim(vmin=vmin, vmax=vmax)
    plt.xlabel(xlab)
    plt.ylabel(ylab)
    
    return fig

if __name__ == "__main__":
    pass
