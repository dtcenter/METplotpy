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

"""
Import standard modules
"""

from datetime import datetime
import getpass
import sys

import numpy as np
import xarray as xr

from matplotlib import pyplot as plt
import matplotlib.dates as mdates

from metplotpy.plots import util
from metplotpy.plots.hovmoeller.hovmoeller_config import HovmoellerConfig

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

        self.logger = util.get_common_logger(self.config_obj.log_level,
                                             self.config_obj.log_filename)
        self.user = getpass.getuser()
        self.logger.info('Begin hovmoeller', extra={'User':self.user}  )

        # Read in input data
        dataset = self.read_data_set()
        self.time = self.ds.time.sel(
            time=slice(self.config_obj.date_start, self.config_obj.date_end))
        self.lon = self.ds.lon
        self.data = self.lat_avg(dataset,
                                 self.config_obj.lat_min, self.config_obj.lat_max)
        self.lat_str = self.get_lat_str(
            self.config_obj.lat_min, self.config_obj.lat_max)
        self.config_obj.title = f"{self.config_obj.title}    {self.lat_str}"

        self.create_figure()

    def create_figure(self):
        self.logger.info(f"Begin creating the figure: {datetime.now()}")

        _, ax = plt.subplots(figsize=(self.config_obj.plot_width, self.config_obj.plot_height))

        wts_size_styles = self.get_weights_size_styles()

        self._add_title(ax, wts_size_styles['title'])
        self._add_caption(plt, wts_size_styles['caption'])

        levels = np.arange(self.config_obj.contour_min,
                           self.config_obj.contour_max + self.config_obj.contour_del,
                           self.config_obj.contour_del)
        contour_filled = ax.contourf(
            self.lon,
            self.time,
            self.data.values,
            levels=levels,
            cmap=self.get_config_value('colorscale'),
            extend='both',
        )

        # add color bar
        colorbar = plt.colorbar(contour_filled, ax=ax, shrink=0.6, extend='both')
        colorbar.set_label(self.data.attrs['units'])


        self._add_xaxis(ax, wts_size_styles['xlab'])
        self._add_yaxis(ax, wts_size_styles['ylab'])

        # auto space time values on y-axis and use dynamic formatting
        locator = mdates.AutoDateLocator()
        ax.yaxis.set_major_locator(locator)
        formatter = mdates.ConciseDateFormatter(locator)

        # change day format to Month Day format
        formatter.formats[2] = '%b %d'

        # change 1st of the month (zero day) to Month Day format
        formatter.zero_formats[2] = '%b %d'

        ax.yaxis.set_major_formatter(formatter)

        plt.tight_layout()
        self.logger.info(f"Finished creating the figure: {datetime.now()}")

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
    config = util.get_params(config_filename)
    try:
        plot = Hovmoeller(config)
        plot.save_to_file()
        plot.logger.info(f"Finished Hovmoeller plotting: {datetime.now()}")
    except ValueError as ve:
        print(ve)


if __name__ == "__main__":
    main()
