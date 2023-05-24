# ============================*
# ** Copyright UCAR (c) 2020
# ** University Corporation for Atmospheric Research (UCAR)
# ** National Center for Atmospheric Research (NCAR)
# ** Research Applications Lab (RAL)
# ** P.O.Box 3000, Boulder, Colorado, 80307-3000, USA
# ============================*


"""
Class Name: Hovmoeller.py

Version  Date
0.1.0    2020/11/15 David Fillmore  Initial version
"""

__author__ = 'David Fillmore'
__version__ = '0.1.0'

import metcalcpy.util.read_env_vars_in_config

"""
Import standard modules
"""
from datetime import datetime
import sys
import yaml
import numpy as np
import xarray as xr
import plotly.graph_objects as go
from netCDF4 import num2date
from metplotpy.plots import util
from metplotpy.plots.hovmoeller.hovmoeller_config import HovmoellerConfig
import metcalcpy

"""
Import BasePlot class
"""
from metplotpy.plots.base_plot import BasePlot


class Hovmoeller(BasePlot):
    """
    Class to create a Plotly Hovmoeller plot from a 2D data array
    """

    def __init__(self, parameters):
        default_conf_filename = 'hovmoeller_defaults.yaml'

        super().__init__(parameters, default_conf_filename)

        # instantiate a HovmoellerConfig object, which holds all the necessary
        # settings from the
        # config file that represents the BasePlot object (Hovmoeller diagram).
        self.config_obj = HovmoellerConfig(self.parameters)

        self.logger.info(f"Begin hovmoeller plotting: {datetime.now()}")

        # Read in input data
        dataset = self.read_data_set()
        self.time = self.ds.time.sel(
            time=slice(self.config_obj.date_start, self.config_obj.date_end))
        self.time_str = self.get_time_str(self.time)
        self.lon = self.ds.lon
        self.data = self.lat_avg(dataset,
                                 self.config_obj.lat_min, self.config_obj.lat_max)
        self.lat_str = self.get_lat_str(
            self.config_obj.lat_min, self.config_obj.lat_max)

        self.figure = go.Figure()

        self.create_figure()

    def create_figure(self):

        self.logger.info(f"Begin creating the figure: {datetime.now()}")
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

        self.logger.info(f"Adding the contour plot: {datetime.now()}")
        self.figure.add_trace(contour_plot)

        self.logger.info(f"Update the layout: {datetime.now()}")
        self.figure.update_layout(
            height=self.config_obj.plot_height,
            width=self.config_obj.plot_width,
            title=self.config_obj.title + '    ' + self.lat_str,
            font=dict(size=self.config_obj.xy_label_fontsize),
            title_font_size=self.config_obj.title_size,
            xaxis_title=self.config_obj.xaxis,
            yaxis_title=self.config_obj.yaxis,
        )

        self.logger.info(f"Finished creating the figure: {datetime.now()}")

    def get_time_str(self, time):
        """
        Generate time string for y-axis labels.
        :param time: time coordinate
        :type time: datetime object
        :return: time_str
        :rtype: str
        """
        ts = (time - np.datetime64('1970-01-01T00:00:00')) / np.timedelta64(1, 'h')
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

    def read_data_set(self):
        """
        Read the input netCDF data and return an xarray dataset

        Args:

            Returns:
                dataset: xarray dataset
       """

        self.logger.info(f"Reading data: {datetime.now()}")
        filename_in = self.config_obj.input_data_file
        try:
            self.logger.info(f"Opening {filename_in}: {datetime.now()}")
            self.ds = xr.open_dataset(filename_in)
        except IOError:
            self.logger.error(f"IOError: Unable to"
                              f" open {filename_in}: {datetime.now()}")
            sys.exit(1)

        dataset = self.ds[self.config_obj.var_name]
        self.logger.debug(f"Data for {self.config_obj.var_name}")
        dataset = dataset.sel(
            time=slice(self.config_obj.date_start, self.config_obj.date_end))

        dataset = dataset * self.config_obj.unit_conversion
        dataset.attrs['units'] = self.config_obj.var_units

        self.logger.info(f"Finished reading input data: {datetime.now()}")

        return dataset

    def write_html(self) -> None:
        """
        Is needed - creates and saves the html representation of the plot WITHOUT
        Plotly.js
        """

        self.logger.info(f"Begin writing html output: {datetime.now()}")
        if self.config_obj.create_html is True:
            # construct the fle name from plot_filename
            name_arr = self.get_config_value('plot_filename').split('.')
            html_name = name_arr[0] + ".html"

            # save html
            self.figure.write_html(html_name, include_plotlyjs=False)

        self.logger.info(f"Finished writing html output: {datetime.now()}")


def main(config_filename=None):
    """
                Generates a sample hovmoeller diagram using the
                default and custom config files on sample data.
                The location of the input data is defined in the default
                config file and can be overridden in the custom config file.

                 Args:
                    @param config_filename: default is None, the name of the custom
                    config file to apply
                Returns:


    """
    # Retrieve the contents of the custom config file to over-ride
    # or augment settings defined by the default config file.
    if not config_filename:
        config_file = util.read_config_from_command_line()
    else:
        config_file = config_filename
    with open(config_file, 'r'):
        try:
            # Use the METcalcpy parser to parse config files with environment
            # variables that
            # look like:
            #   input_file: !ENV '${ENV_NAME}/some_input_file.nc'
            # This supports METplus hovmoeller use case.
            config = metcalcpy.util.read_env_vars_in_config.parse_config(config_file)
        except yaml.YAMLError as exc:
            print(exc)

    try:
        plot = Hovmoeller(config)
        plot.save_to_file()
        plot.logger.info(f"Finished Hovmoeller plotting: {datetime.now()}")
    except ValueError as ve:
        print(ve)


if __name__ == "__main__":
    main()
