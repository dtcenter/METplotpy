"""
Class Name: box.py
 """
__author__ = 'Hank Fisher'
__email__ = 'met_help@ucar.edu'

import plotly.graph_objects as go
import yaml
import pandas as pd
from plots.base_plot import BasePlot

class Box(BasePlot):
    """  Generates a Plotly box plot,

    """
    def __init__(self, parameters):
        """ Creates a box plot, based on
            settings indicated by parameters.

            Args:
            @param parameters: dictionary containing user defined parameters

        """

        default_conf_filename = "box_defaults.yaml"
        # init common layout
        super().__init__(parameters, default_conf_filename)

        # create figure
        # pylint:disable=assignment-from-no-return
        # Need to have a self.figure that we can pass along to
        # the methods in base_plot.py (BasePlot class methods) to
        # create binary versions of the plot.
        self.figure = self._create_figure()

    def __repr__(self):
        """ Implement repr which can be useful for debugging this
            class.
        """

        return f'Line({self.parameters!r})'

    def _get_all_boxes(self):
        """ Retrieve a list of all box data.  Each boxes is a dictionary comprised of
            key-values that represent the necessary settings to create a box plot.
            Each box has an associated text data file containing point data.

            Returns:
                boxes :  a list of dictionaries representing settings for each box plot.

        """

        return self.get_config_value('boxes')

    def get_xaxis_title(self):
        """ Override the method in the parent class, BasePlot, as this is located
            in a different location in the config file.
        """

        return self.parameters['xaxis']['title']


    def get_yaxis_title(self):
        """ Override the method in the parent class, BasePlot, as this is located
            in a different location in the config file.
        """

        return self.parameters['yaxis']['title']


    def _create_figure(self):
        """ Create a box plot from default and custom parameters"""

        # pylint:disable=too-many-locals
        # Need to have all these local variables input
        # to Plotly to generate a box plot.

        fig = go.Figure()

        # Generate each box based on settings in the default and
        # custom parameters specified in the YAML files.
        boxes = self._get_all_boxes()

        connect_gap = self.parameters['connect_data_gaps']

        # Retrieve the settings for the n-boxes specified
        # in the default or custom config file.
        for box_dict in boxes:
            name = box_dict['name']

            # Extract the data defined in the custom config file
            # A list of 1..n entries, with each data file corresponding
            # to a box on the plot.
            input_data_file = box_dict['data_file']
            data = pd.read_csv(input_data_file, delim_whitespace=True)

            color = box_dict['color']
            #width = box_dict['width']
            box_x = data['y0']
            box_y = data['y1']
            fig.add_trace(go.Box(y=box_x, name=name, marker_color=color))
            fig.add_trace(go.Box(y=box_y, name=name, marker_color=color))


        # Edit the final layout, set the plot title and axis labels
        fig.update_layout(legend=self.get_legend(), title=self.get_title(), xaxis_title=self.get_xaxis_title(), yaxis_title=self.get_yaxis_title())

        return fig


def main():
    """
        Generates a sample, default, box plot using a combination of
        default and custom config files on sample data found in this directory.
        The location of the input data is defined in either the default or
        custom config file.
    """

    # Retrieve the contents of the custom config file to over-ride
    # or augment settings defined by the default config file.
    with open("./custom_box.yaml", 'r') as stream:
        try:
            docs = yaml.load(stream, Loader=yaml.FullLoader)
        except yaml.YAMLError as exc:
            print(exc)


    try:
      s = Box(docs)
      s.save_to_file()
      s.show_in_browser()
    except ValueError as ve:
        print(ve)


if __name__ == "__main__":
    main()
