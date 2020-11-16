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
    """
    Parse command line arguments
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--datadir', type=str,
                        default=os.getenv('DATA_DIR'),
                        help='top-level data directory (default $DATA_DIR)')
    parser.add_argument('--input', type=str,
                        required=True,
                        help='input file name')
    parser.add_argument('--logfile', type=str,
                        default=sys.stdout,
                        help='log file (default stdout)')
    parser.add_argument('--debug', action='store_true',
                        help='set logging level to debug')
    args = parser.parse_args()

    """
    Setup logging
    """
    logging_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(stream=args.logfile, level=logging_level)

    if os.path.isdir(args.datadir):
        logging.info(args.datadir)
    else:
        logging.error(args.datadir + ' not found')
        sys.exit(1)
    logging.info(args.input)


    data = None
    plot = Hovmoeller(None, data)

