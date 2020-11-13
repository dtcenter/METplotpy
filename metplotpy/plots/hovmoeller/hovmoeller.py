"""
Class Name: Hovmoeller.py

Version  Date
0.1.0    2020/11/15 David Fillmore  Initial version
"""

__author__ = 'David Fillmore'
__version__ = '0.1.0'
__email__ = 'met_help@ucar.edu'

"""
Import standard modules
"""
import os
import sys
import argparse
import logging
import yaml
from datetime import datetime
import numpy as np
import xarray as xr  # http://xarray.pydata.org/
import plotly.graph_objects as go

"""
Import MetPlot class
"""
from plots.met_plot import MetPlot

class Hovmoeller(MetPlot):
    """
    Class to create of Plotly Hovmoeller plot from a 2D data array
    """
    def __init__(self, parameters, data):
        default_conf_filename = 'hovmoeller_defaults.yaml'

        super().__init__(parameters, default_conf_filename)

if __name__ == "__main__":

    plot = Hovmoeller(None, None)

