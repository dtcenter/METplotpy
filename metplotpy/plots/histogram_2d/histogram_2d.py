"""
Class Name: Histrogram_2d.py

Version  Date
0.1.0    2021/02/10 David Fillmore  Initial version
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
import numpy as np
import xarray as xr
import plotly.graph_objects as go

"""
Import BasePlot class
"""
from plots.base_plot import BasePlot


class Histogram_2d(BasePlot):
    """
    Class to create a Plotly Histogram_2d plot from a 2D data array
    """
    def __init__(self, parameters, data):
        default_conf_filename = 'histogram_2d_defaults.yaml'

        super().__init__(parameters, default_conf_filename)
        logging.debug(self.parameters)

        self.data = data
        self.dims = data.dims
        self.coords = data.coords

        # normalized probability distribution function
        self.pdf = data / data.sum()

        self.figure = go.Figure()

        self.create_figure()

    def create_figure(self):

        if self.get_config_value('normalize_to_pdf'):
            z_data = self.pdf
        else:
            z_data = self.data

        self.figure.add_heatmap(
            x=self.data.coords[self.dims[0]],
            y=self.data.coords[self.dims[1]],
            z=z_data,
            zmin=self.get_config_value('pdf_min'),
            zmax=self.get_config_value('pdf_max'))

        self.figure.update_layout(
            height=self.get_config_value('height'),
            width=self.get_config_value('width'),
            font=dict(size=self.get_config_value('font_size')),
            title=self.get_config_value('title'),
            xaxis_title=self.get_config_value('xaxis_title'),
            yaxis_title=self.get_config_value('yaxis_title'),
        )


def create_test_data(filename_in):
    logging.debug('Creating test data')
    nx, ny = 21, 21
    x_coord = np.linspace(-2, 2, nx)
    y_coord = np.linspace(-2, 2, ny)
    x_mesh, y_mesh = np.meshgrid(x_coord, y_coord, indexing='ij')
    f_mesh = 4 - np.square(x_mesh - y_mesh + 1)
    f_mesh = np.clip(f_mesh, 0, 4)
    logging.debug(f_mesh.max())
    f_array = xr.DataArray(f_mesh,
        dims=['x', 'y'],
        coords={'x': x_coord, 'y': y_coord})
    ds = xr.Dataset({'hist_x_y': f_array})
    ds.to_netcdf(filename_in)


if __name__ == "__main__":
    """
    Parse command line arguments
    """
    metplotpy_base = os.getenv('METPLOTPY_BASE')
    if not metplotpy_base:
        metplotpy_base = ''
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=str,
        default=os.path.join(metplotpy_base,
        'plots', 'config', 'histogram_2d_defaults.yaml'),
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
    parser.add_argument('--test', action='store_true',
                        help='internal test')
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
    Create test dataset
    """
    if args.test:
        create_test_data(filename_in)

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

    plot = Histogram_2d(None, data)

    #plot.show_in_browser()
    plot.save_to_file()
