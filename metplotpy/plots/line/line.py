"""
Class Name: line.py
 """
__author__ = 'Minna Win'
__email__ = 'met_help@ucar.edu'

import os
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
            settings indicated by the parameters.

        """
        # read defaults stored in YAML formatted file into the dictionary
        location = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
        with open(os.path.join(location, 'line_defaults.yaml'), 'r') as stream:
            try:
                defaults = yaml.load(stream, Loader=yaml.FullLoader)
            except yaml.YAMLError as exc:
                print(exc)

        # init common layout
        super().__init__(parameters, defaults)

        # create figure
        self._create_figure()

    def _get_all_lines(self):
        """ Retrieve a list of all lines.  Each line is a dictionary comprised of
            key-values that represent the necessary settings to create a line plot.

            Returns:
                lines :  a list of dictionaries representing settings for each line plot
        """

        return self.get_config_value('lines')


    def _create_figure(self):
        """ Create a line plot from default and custom parameters"""
        fig = go.Figure()

        # Generate each trace/line based on settings in the default and
        # custom parameters specified in the YAML files.
        lines = self._get_all_lines()
        title = self.parameters['title']
        x_axis_title = self.parameters['xaxis_title']
        y_axis_title = self.parameters['yaxis_title']
        connect_gap = self.parameters['connect_data_gaps']
        for line in lines:
            name = line['name']
            input_data_file = line['data_file']
            data = pd.read_csv(input_data_file, delim_whitespace=True)
            color = line['color']
            width = line['width']
            dash = line['dash']
            line_x = data['x']
            line_y = data['y']
            fig.add_trace(go.Scatter(
                x=line_x, y=line_y, name=name, connectgaps=connect_gap,
                line=dict(color=color, width=width, dash=dash)
            ))


        # Edit the final layout
        fig.update_layout(title=title, xaxis_title=x_axis_title, yaxis_title=y_axis_title)

        fig.show()


def main():
    """
        Generates a sample, two-trace line plot using default and custom config files,
        and sample data found in this directory.  The location of the input
        data is defined in either the default or custom config file.


    """

    # Generate a sample two-trace line plot on
    # example data found in this directory.
    # Use the custom config file and default config files
    # found in this directory.
    with open("./custom_line.yaml", 'r') as stream:
        try:
            docs = yaml.load(stream, Loader=yaml.FullLoader)
        except yaml.YAMLError as exc:
            print(exc)

    Line(docs)


if __name__ == "__main__":
    main()
