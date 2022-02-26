# ============================*
 # ** Copyright UCAR (c) 2021
 # ** University Corporation for Atmospheric Research (UCAR)
 # ** National Center for Atmospheric Research (NCAR)
 # ** Research Applications Lab (RAL)
 # ** P.O.Box 3000, Boulder, Colorado, 80307-3000, USA
 # ** NAVAL Research Lab (NRL)
 # ============================*
 
 
 
# -*- coding: utf-8 -*-
"""
Created on Wed Apr  8 16:57:07 2020

@author: campbell
"""
import numpy as np
import matplotlib.colors as colors
from scipy.interpolate import pchip


def spectral(n=100):
    """
    Visually linear colormap based on linspecer Matlab map.
    A vast improvement on the jet colormap
    """
    if n == 1:
        cmap = np.array([0.2005, 0.5593, 0.7380])
    elif n == 2:
        cmap = np.array([[0.2005, 0.5593, 0.7380],
                         [0.9684, 0.4799, 0.2723]])
    else:
        cmapp = np.array([
                [158, 1, 66],     # dark red
                [213, 62, 79],    # red
                [244, 109, 67],   # dark orange
                [253, 174, 97],   # orange
                [254, 224, 139],  # light orange
                [255, 255, 191],  # light yellow
                [230, 245, 152],  # yellow green
                [171, 221, 164],  # light green
                [102, 194, 165],  # green
                [50, 136, 189],   # blue
                [94, 79, 162],    # violet
                ])
        x = np.linspace(0, n-1, np.shape(cmapp)[0])
        xi = np.arange(n)
        interp = pchip(x, cmapp, axis=0)
        cmap = np.flipud(interp(xi)) / 255
        cmap = colors.ListedColormap(cmap, name='spectral')

    return cmap


def stoplight(n=100):
    """
    An attempta at a visually nice stoplight colormap
    """
    if n == 1:
        cmap = np.array([0.2005, 0.5593, 0.7380])
    elif n == 2:
        cmap = np.array([[0.2005, 0.5593, 0.7380],
                         [0.9684, 0.4799, 0.2723]])
    else:
        cmapp = np.array([
                # [90, 1, 33],     # very dark red
                [158, 1, 66],     # dark red
                [213, 62, 79],    # red
                [244, 109, 67],   # dark orange
                [253, 174, 97],   # orange
                [254, 224, 139],  # light orange
                [255, 255, 191],  # light yellow
                [230, 245, 152],  # yellow green
                [171, 221, 164],  # light green
                # [102, 194, 165],  # green
                [80, 165, 110],   # dark green
                [40, 115, 50],   # very dark green
                # [50, 136, 189],   # blue
                # [94, 79, 162],    # violet
                ])
        x = np.linspace(0, n-1, np.shape(cmapp)[0])
        xi = np.arange(n)
        interp = pchip(x, cmapp, axis=0)
        cmap = np.flipud(interp(xi)) / 255
        cmap = colors.ListedColormap(cmap, name='spectral')

    return cmap
