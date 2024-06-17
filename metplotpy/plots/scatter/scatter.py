# ============================*
 # ** Copyright UCAR (c) 2019
 # ** University Corporation for Atmospheric Research (UCAR)
 # ** National Center for Atmospheric Research (NCAR)
 # ** Research Applications Lab (RAL)
 # ** P.O.Box 3000, Boulder, Colorado, 80307-3000, USA
 # ============================*
 
 
 
"""
Class Name: scatter.py
 """
__author__ = 'Hank Fisher'

import plotly.graph_objects as go
import yaml
import pandas as pd
from plots.base_plot import BasePlot

from metplotpy.plots import util


class Scatter(BasePlot):
    """  Generates a Plotly scatter plot,

    """
    def __init__(self, parameters):
        """ Creates a scatter plot, based on
            settings indicated by parameters.

            Args:
            @param parameters: dictionary containing user defined parameters

        """

        default_conf_filename = "scatter_defaults.yaml"
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

    def _get_all_scatters(self):
        """ Retrieve a list of all scatters.  Each scatters is a dictionary comprised of
            key-values that represent the necessary settings to create a scatter plot.
            Each scatter has an associated text data file containing point data.

            Returns:
                scatters :  a list of dictionaries representing settings for each scatter plot.

        """

        return self.get_config_value('scatters')

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
        """ Create a scatter plot from default and custom parameters"""

        # pylint:disable=too-many-locals
        # Need to have all these local variables input
        # to Plotly to generate a scatter plot.

        fig = go.Figure()

        # Generate each scatter based on settings in the default and
        # custom parameters specified in the YAML files.
        scatters = self._get_all_scatters()

        connect_gap = self.parameters['connect_data_gaps']

        # Retrieve the settings for the n-scatters specified
        # in the default or custom config file.
        for scatter_dict in scatters:
            name = scatter_dict['name']

            # Extract the data defined in the custom config file
            # A list of 1..n entries, with each data file corresponding
            # to a scatter on the plot.
            input_data_file = scatter_dict['data_file']
            data = pd.read_csv(input_data_file, delim_whitespace=True)

            #color = line_dict['color']
            #width = line_dict['width']
            #dash = line_dict['dash']
            scatter_x = data['x']
            scatter_y = data['y']
            fig.add_trace(go.Scatter(
                x=scatter_x, y=scatter_y, name=name
            ))


        # Edit the final layout, set the plot title and axis labels
        fig.update_layout(legend=self.get_legend(), title=self.get_title(), xaxis_title=self.get_xaxis_title(), yaxis_title=self.get_yaxis_title())

        return fig


def main():
    """
        Generates a sample, default, scatter plot using a combination of
        default and custom config files on sample data found in this directory.
        The location of the input data is defined in either the default or
        custom config file.
    """
    params = util.get_params("./custom_scatter.yaml")
    try:
        s = Scatter(params)
        s.save_to_file()
        s.show_in_browser()
    except ValueError as ve:
        print(ve)


if __name__ == "__main__":
    main()
