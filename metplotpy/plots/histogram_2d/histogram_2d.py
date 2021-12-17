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
import re
import yaml
import xarray as xr
import plotly.graph_objects as go
import plots.util as util

"""
Import BasePlot class
"""
from plots.base_plot import BasePlot


class Histogram_2d(BasePlot):
    """
    Class to create a Plotly Histogram_2d plot from a 2D data array
    """

    def __init__(self, parameters):
        default_conf_filename = 'histogram_2d_defaults.yaml'

        super().__init__(parameters, default_conf_filename)
        # logging.debug(self.parameters)

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

    def save_to_file(self):
        """Saves the image to a file specified in the config file.
         Prints a message if fails

        Args:

        Returns:

        """
        image_name = self.get_config_value('plot_filename')
        if self.figure:
            try:
                self.figure.write_image(image_name)

            except FileNotFoundError:
                print("Can't save to file " + image_name)
            except ValueError as ex:
                print(ex)
        else:
            print("Oops!  The figure was not created. Can't save.")

    def write_output_file(self):
        """
            No intermediate files to write, this plot is currently
            not incorporated into METviewer.

        :return:
        """
        print("No intermediate points1 file created. This plot type is not integrated into METviewer")

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
            try:
                if os.stat(output_file).st_size == 0:
                    fileobj = open(output_file, 'a')
                else:
                    os.remove(output_file)
            except FileNotFoundError as fnfe:
                # OK if no file was found
                pass



        pass

    def _read_input_data(self):
        """
                Read the input data file and store as an xarray
                dataset.

                Args:

                Returns: an xarray dataset representation of the gridded input data

        """
        try:
            ds = xr.open_dataset(self.input_file)
        except IOError as ioe:
            print("Unable to open input file")
            sys.exit(1)
        return ds


def main(config_filename=None):
    metplotpy_base = os.getenv('METPLOTPY_BASE')
    if not metplotpy_base:
        metplotpy_base = ''

    # Retrieve the contents of the custom config file to over-ride
    # or augment settings defined by the default config file.
    if not config_filename:
        config_file = util.read_config_from_command_line()
    else:
        config_file = config_filename

    with open(config_file, 'r') as stream:
        try:
            docs = yaml.load(stream, Loader=yaml.FullLoader)
        except yaml.YAMLError as exc:
            print(exc)

    try:
        h = Histogram_2d(docs)
        h.save_to_file()
    except ValueError as ve:
        print(ve)


if __name__ == "__main__":
    main()
