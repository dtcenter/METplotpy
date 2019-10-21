"""
Class Name: line.py
 """
__author__ = 'Minna Win'
__email__ = 'met_help@ucar.edu'

import plotly.graph_objects as go
import yaml
import pandas as pd
from plots.met_plot import MetPlot

class Line(MetPlot):
    """  Generates a Plotly line plot for 1 or more traces (lines),
         where each line is represented by a text point data file.
         A default config file for two lines is provided, along with
         sample/dummy data (line1_plot_data.txt and line2_plot_data.txt).
         A setting is over-ridden in the default configuration file if
         it is defined in the custom configuration file.

    """
    def __init__(self, parameters):
        """ Creates a line plot consisting of one or more lines (traces), based on
            settings indicated by parameters.

            Args:
            @param parameters: dictionary containing user defined parameters

        """

        default_conf_filename = "line_defaults.yaml"
        # init common layout
        super().__init__(parameters, default_conf_filename)

        # create figure
        # pylint:disable=assignment-from-no-return
        # Need to have a self.figure that we can pass along to
        # the methods in met_plot.py (MetPlot class methods) to
        # create binary versions of the plot.
        self.figure = self._create_figure()

    def __repr__(self):
        """ Implement repr which can be useful for debugging this
            class.
        """

        return f'Line({self.parameters!r})'

    def _get_all_lines(self):
        """ Retrieve a list of all lines.  Each line is a dictionary comprised of
            key-values that represent the necessary settings to create a line plot.
            Each line has an associated text data file containing point data.

            Returns:
                lines :  a list of dictionaries representing settings for each line plot.

        """

        return self.get_config_value('lines')

    def get_xaxis_title(self):
        """ Override the method in the parent class, MetPlot, as this is located
            in a different location in the config file.
        """

        return self.parameters['xaxis']['title']


    def get_yaxis_title(self):
        """ Override the method in the parent class, MetPlot, as this is located
            in a different location in the config file.
        """

        return self.parameters['yaxis']['title']


    def _create_figure(self):
        """ Create a line plot from default and custom parameters"""

        # pylint:disable=too-many-locals
        # Need to have all these local variables input
        # to Plotly to generate a line plot.

        fig = go.Figure()

        # Generate each trace/line based on settings in the default and
        # custom parameters specified in the YAML files.
        lines = self._get_all_lines()

        connect_gap = self.parameters['connect_data_gaps']

        # Retrieve the settings for the n-lines/traces specified
        # in the default or custom config file.
        for line_dict in lines:
            name = line_dict['name']

            # Extract the data defined in the custom config file
            # A list of 1..n entries, with each data file corresponding
            # to a line/trace on the plot.
            input_data_file = line_dict['data_file']
            data = pd.read_csv(input_data_file, delim_whitespace=True)

            color = line_dict['color']
            width = line_dict['width']
            dash = line_dict['dash']
            line_x = data['x']
            line_y = data['y']
            fig.add_trace(go.Scatter(
                x=line_x, y=line_y, name=name, connectgaps=connect_gap,
                line=dict(color=color, width=width, dash=dash)
            ))


        # Edit the final layout, set the plot title and axis labels
        fig.update_layout(legend=self.get_legend(), title=self.get_title(), xaxis_title=self.get_xaxis_title(), yaxis_title=self.get_yaxis_title())

        return fig


def main():
    """
        Generates a sample, default, two-trace line plot using a combination of
        default and custom config files on sample data found in this directory.
        The location of the input data is defined in either the default or
        custom config file.
    """

    # Retrieve the contents of the custom config file to over-ride
    # or augment settings defined by the default config file.
    with open("./custom_line.yaml", 'r') as stream:
        try:
            docs = yaml.load(stream, Loader=yaml.FullLoader)
        except yaml.YAMLError as exc:
            print(exc)


    try:
      l = Line(docs)
      l.save_to_file()
      l.show_in_browser()
    except ValueError as ve:
        print(ve)


if __name__ == "__main__":
    main()
