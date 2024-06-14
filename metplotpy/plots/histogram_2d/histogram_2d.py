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
import os
import sys
from datetime import datetime
import re
import yaml
import xarray as xr
import plotly.graph_objects as go

import metplotpy.plots.util as util

"""
Import BasePlot class
"""
from metplotpy.plots.base_plot import BasePlot


class Histogram_2d(BasePlot):
    """
    Class to create a Plotly Histogram_2d plot from a 2D data array
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

        self.figure = go.Figure()

        self.create_figure()

    def create_figure(self):

        self.logger.info(f"Begin creating the figure: {datetime.now()}")
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

        self.logger.info(f"Finished creating the figure: {datetime.now()}")

    def save_to_file(self):
        """Saves the image to a file specified in the config file.
         Prints a message if fails

        Args:

        Returns:

        """
        image_name = self.get_config_value('plot_filename')
        self.logger.info(f"Saving plot to file {image_name}: {datetime.now()} ")
        if self.figure:
            try:
                self.figure.write_image(image_name)

            except FileNotFoundError:
                self.logger.error(f"FileNotFoundError: Can't save to file {image_name}")
            except ValueError:
                self.logger.error(f"ValueError: Some other error occurred "
                                  f"{datetime.now()}")
        else:
            self.logger.error(f"The figure was not created. Cannot save file.")

        self.logger.info(f"Finished saving plot to file: {datetime.now()}")

    def write_output_file(self):
        """
            No intermediate files to write, this plot is currently
            not incorporated into METviewer.

        :return:
        """
        self.logger.info(f"Begin writing plot to output file: {datetime.now()}")
        self.logger.info(f"No intermediate points1 file created. This plot type is not "
                "integrated into METviewer: {datetime.now()}")

        # if points_path parameter doesn't exist,
        # open file, name it based on the stat_input config setting,
        # (the input data file) except replace the .data
        # extension with .points1 extension
        # otherwise use points_path path
        match = re.match(r'(.*)(.data)', self.config_obj.parameters['stat_input'])
        if self.config_obj.dump_points_1 is True and match:
            filename = match.group(1)
            # replace the default path with the custom
            if self.config_obj.points_path is not None:
                # get the file name
                path = filename.split(os.path.sep)
                if len(path) > 0:
                    filename = path[-1]
                else:
                    filename = '.' + os.path.sep
                filename = self.config_obj.points_path + os.path.sep + filename

            output_file = filename + '.points1'

            # make sure this file doesn't already
            # exist, delete it if it does
            self.logger.info(f"Check if file exists, delete if it does. "
                             f"{datetime.now()}")
            try:
                if os.stat(output_file).st_size == 0:
                    open(output_file, 'a')
                else:
                    os.remove(output_file)
            except FileNotFoundError:
                # OK if no file was found
                self.logger.info(f"FileNotFound while checking if output file exists. "
                                 f" This is OK:{datetime.now()}")
                pass

        self.logger.info(f"Finished writing plot to output file: {datetime.now()}")

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
    params = util.get_params(config_filename)
    try:
        h = Histogram_2d(params)
        h.save_to_file()
        h.logger.info(f"Finished generating histogram 2D plot: {datetime.now()}")
    except ValueError as ve:
        print(ve)


if __name__ == "__main__":
    main()
