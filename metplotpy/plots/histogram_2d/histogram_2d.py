# ============================*
 # ** Copyright UCAR (c) 2021
 # ** University Corporation for Atmospheric Research (UCAR)
 # ** National Center for Atmospheric Research (NCAR)
 # ** Research Applications Lab (RAL)
 # ** P.O.Box 3000, Boulder, Colorado, 80307-3000, USA
 # ============================*
 
 
 
"""
Class Name: Histrogram_2d.py

Version  Date
0.1.0    2021/02/10 David Fillmore  Initial version
"""

__author__ = 'David Fillmore'
__version__ = '0.1.0'

"""
Import standard modules
"""

import sys
from datetime import datetime
import xarray as xr

from matplotlib import pyplot as plt

import metplotpy.plots.util as util

"""
Import BasePlot class
"""
from metplotpy.plots.base_plot import BasePlot


class Histogram2D(BasePlot):
    """
    Class to create a Plotly Histogram2d plot from a 2D data array
    """

    def __init__(self, parameters):
        default_conf_filename = 'histogram_2d_defaults.yaml'

        super().__init__(parameters, default_conf_filename)
        self.logger = self.config_obj.logger
        self.logger.info(f"Begin histogram 2D plotting: {datetime.now()}")

        # Read in input data, location specified in config file
        self.input_file = self.get_config_value('stat_input')
        self.input_ds = self._read_input_data()
        self.data = self.input_ds[self.get_config_value('var_name')]
        self.dims = self.data.dims
        self.coords = self.data.coords

        # Optional setting, indicates *where* to save the dump_points_1 file
        # used by METviewer
        self.points_path = self.get_config_value('points_path')
        self.dump_points_1 = self.get_config_value('dump_points_1')
        self.dump_points_2 = self.get_config_value('dump_points_2')

        # normalized probability distribution function
        self.pdf = self.data / self.data.sum()

        self.create_figure()

    def create_figure(self):

        self.logger.info(f"Begin creating the figure: {datetime.now()}")
        _, ax = plt.subplots(figsize=(self.config_obj.plot_width, self.config_obj.plot_height))

        wts_size_styles = self.get_weights_size_styles()

        self._add_title(ax, wts_size_styles['title'])
        self._add_caption(plt, wts_size_styles['caption'])

        self.config_obj.xaxis = self.get_config_value('xaxis_title')
        self.config_obj.yaxis_1 = self.get_config_value('yaxis_title')

        self._add_xaxis(ax, wts_size_styles['xlab'])
        self._add_yaxis(ax, wts_size_styles['ylab'])

        z_data = self.pdf if self.get_config_value('normalize_to_pdf') else self.data

        colormesh = ax.pcolormesh(
            self.data.coords[self.dims[1]],
            self.data.coords[self.dims[0]],
            z_data,
            vmin=self.get_config_value('pdf_min'),
            vmax=self.get_config_value('pdf_max'),
            shading='nearest'
        )
        plt.colorbar(colormesh, ax=ax)

        self.logger.info(f"Finished creating the figure: {datetime.now()}")

    def write_output_file(self):
        """
            No intermediate files to write, this plot is currently
            not incorporated into METviewer.

        :return:
        """
        self.logger.info("No intermediate points1 file created. This plot type is not "
                         f"integrated into METviewer: {datetime.now()}")

    def _read_input_data(self):
        """
                Read the input data file and store as an xarray
                dataset.

                Args:

                Returns: an xarray dataset representation of the gridded input data

        """

        self.logger.info(f"Reading input data: {datetime.now()}")
        try:
            ds = xr.open_dataset(self.input_file)
        except IOError:
            print(f"Unable to open input file: {self.input_file}")
            sys.exit(1)
        self.logger.info(f"Finished reading input data: {datetime.now()}")
        return ds


def main(config_filename=None):
    util.make_plot(config_filename, Histogram2D)

if __name__ == "__main__":
    main()
