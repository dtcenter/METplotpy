"""
Class Name: Hovmoeller.py

Version  Date
0.1.0    2020/11/15 David Fillmore  Initial version
"""

__author__ = 'David Fillmore'
__version__ = '0.1.0'

"""
Import standard modules
"""
import os
import sys
import argparse
import logging
import yaml
import numpy as np
import xarray as xr  # http://xarray.pydata.org/
import plotly.graph_objects as go
from netCDF4 import num2date

"""
Import BasePlot class
"""
from plots.base_plot import BasePlot
# sys.path.append("..") # Adds higher directory to python modules path.
# from base_plot import BasePlot


class Hovmoeller(BasePlot):
    """
    Class to create a Plotly Hovmoeller plot from a 2D data array
    """
    def __init__(self, parameters, time, lon, data):
        default_conf_filename = 'hovmoeller_defaults.yaml'

        super().__init__(parameters, default_conf_filename)
        logging.debug(self.parameters)

        self.time = time
        self.time_str = self.get_time_str(time)
        self.lon = lon
        self.data = self.lat_avg(data,
            self.get_config_value('lat_min'), self.get_config_value('lat_max'))
        self.lat_str = self.get_lat_str(
            self.get_config_value('lat_min'), self.get_config_value('lat_max'))

        self.figure = go.Figure()

        self.create_figure()

    def create_figure(self):

        contour_plot = go.Contour(
            z=self.data.values,
            x=self.lon,
            y=self.time_str,
            colorscale=self.get_config_value('colorscale'),
            contours=dict(start=self.get_config_value('contour_min'),
                          end=self.get_config_value('contour_max'),
                          size=self.get_config_value('contour_del'),
                          showlines=False),
            colorbar=dict(title=self.data.attrs['units'],
                          len=0.6,
                          lenmode='fraction')
        )

        self.figure.add_trace(contour_plot)

        self.figure.update_layout(
            height=self.get_config_value('height'),
            width=self.get_config_value('width'),
            title=self.get_config_value('title') + '    ' + self.lat_str,
            font=dict(size=self.get_config_value('font_size')),
            xaxis_title=self.get_config_value('xaxis_title'),
            yaxis_title=self.get_config_value('yaxis_title'),
        )

    def get_time_str(self, time):
        """
        Generate time string for y-axis labels.
        :param time: time coordinate
        :type time: datetime object
        :return: time_str
        :rtype: str
        """
        ts = (time - np.datetime64('1970-01-01T00:00:00Z')) / np.timedelta64(1, 'h')
        date = num2date(ts, 'hours since 1970-01-01T00:00:00Z')
        time_str = [i.strftime("%Y-%m-%d %H:%M") for i in date]

        return time_str

    def get_lat_str(self, lat_min, lat_max):
        """
        Generate string describing the latitude band averaged over.
        :param lat_min: southern latitude limit of the average
        :type lat_min: float
        :param lat_max: northern latitude limit of the average
        :type lat_max: float
        :return: lat_str
        :rtype: str
        """
        if lat_min < 0:
            hem_min = 'S'
            lat_min = -lat_min
        else:
            hem_min = 'N'
        if lat_max < 0:
            hem_max = 'S'
            lat_max = -lat_max
        else:
            hem_max = 'N'

        lat_str = str(lat_min) + hem_min + " - " + str(lat_max) + hem_max

        return lat_str

    def lat_avg(self, data, lat_min, lat_max):
        """
        Compute latitudinal average.
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
    parser = argparse.ArgumentParser(description="Hovmoeller diagram", 
         epilog="METPLOTPY_BASE needs to be set to your METplotpy/metplotpy directory")

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
    parser.print_help()

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
    lon = ds.lon

    data = data * config['unit_conversion']
    data.attrs['units'] = config['var_units']

    plot = Hovmoeller(None, time, lon, data)

    #plot.show_in_browser()
    plot.save_to_file()

