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
    Class to create a Plotly Hovmoeller plot from a 2D data array
    """
    def __init__(self, parameters, data):
        default_conf_filename = 'hovmoeller_defaults.yaml'

        super().__init__(parameters, default_conf_filename)
        logging.debug(self.parameters)

        self.data = data

    def _create_figure(self):
        pass

    def _lat_avg(self, data, lat_min, lat_max):
        """
        Compute latitudinal average
        :param data: input data (time, lat, lon)
        :type data: xarray.DataArray
        :param lat_min: southern latitude for averaging
        :type lat_min: float
        :param lat_max: northern latitude for averaging
        :type lat_max: float
        :return: data (time, lon)
        :rtype: xarray.DataArray
        """
        data = data.sel(lat=slice(lat_min, lat_max))
        units = data.attrs['units']
        data = data.mean(dim='lat')
        data.attrs['units'] = units
        data = data.squeeze()

        return data


if __name__ == "__main__":
    """
    Parse command line arguments
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=str,
                        default=os.path.join(os.getenv('METPLOTPY_BASE'),
                        'plots', 'config', 'hovmoeller_defaults.yaml'),
                        help='configuration file')
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

    """
    Construct input filename
    """
    filename_in = os.path.join(args.datadir, args.input)

    """
    Read YAML configuration file
    """
    try:
        config = yaml.load(
            open(args.config), Loader=yaml.FullLoader)
        logging.info(config)
    except yaml.YAMLError as exc:
        logging.error(exc)

    """
    Read dataset
    """
    try:
        logging.info('Opening ' + filename_in)
        ds = xr.open_dataset(filename_in)
    except IOError as exc:
        logging.error('Unable to open ' + filename_in)
        logging.error(exc)
        sys.exit(1)
    logging.debug(ds)

    data = ds[config['var_name']]
    logging.debug(data)

    data = data.sel(time=slice(config['date_start'], config['date_end']))
    time = ds.time.sel(time=slice(config['date_start'], config['date_end']))

    data = data * config['unit_conversion']
    data.attrs['units'] = config['var_units']

    plot = Hovmoeller(None, data)

