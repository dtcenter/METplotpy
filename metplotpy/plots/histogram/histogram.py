"""
Class Name: histogram.py
 """
__author__ = 'Tatiana Burek'

import os
import plotly.graph_objects as go
import yaml
import pandas as pd
import numpy as np

from plots.base_plot import BasePlot


class Histogram(BasePlot):
    """A class that creates histogram using Plotly using a two dimensional data array

    To use:
        >>> data = [np.random.randn(500),np.random.randn(500) + 1]
        >>> histogram = Histogram(None, data)
        >>> histogram.show_in_browser()
    """
    DEFAULT_XBINS_SIZE = 10
    DEFAULT_LINE_WIDTH = 1
    DEFAULT_COLOR = 'white'
    DEFAULT_TITLE_FORMAT = 'Series {}'

    def __init__(self, parameters, data):
        """Inits Histogram with user defined  dictionary and a data array.
        Creates a Plotly histogram figure using the data

        Args:
            @param parameters - dictionary containing user defined parameters
            @param data       - two dimensional data array
        Raises:
            ValueError: If the data array has dimension not equal 2.
        """

        default_conf_filename = "histogram_defaults.yml"
        # init common layout
        super().__init__(parameters, default_conf_filename)


        # validate the input array - should be 2-dimensional
        dim = Histogram.get_array_dimensions(data)
        if dim is None or dim != 2:
            raise ValueError('Data array dimension should be 2 but it is {0}'.format(dim))

        # create figure
        self.figure = self._create_figure(data)

    def _create_figure(self, data):
        """Draws histogram data on the layout

        Args:
            @param data - two dimensional data array

        Returns:
            Figure
        """

        # init Figure
        fig = go.Figure()

        try:
            # create layout with title, axises, legend ...
            fig.update_layout(
                title=self.get_title(),
                xaxis=self.get_xaxis(),
                yaxis=self.get_yaxis(),
                # gap between bars of adjacent location coordinates
                bargap=self.get_config_value('bargap'),
                # bargroupgap=0.1  # gap between bars of the same location coordinates\
                showlegend=self.get_config_value('showlegend'),
                legend_orientation=self.get_config_value('legend_orientation'),
                legend=self.get_legend(),
                plot_bgcolor=self.get_config_value('plot_bgcolor'),
                height=self.get_config_value('height'),
                width=self.get_config_value('width'),
                annotations=[
                    self.get_xaxis_title(),
                    self.get_yaxis_title()
                ],
            )
            # calculate bins_size
            xbins_size = self._get_bins_size()

            # add histogram's markers
            for i, marker_data in enumerate(data):
                fig.add_trace(go.Histogram(
                    x=marker_data,
                    histnorm=self.get_config_value('histnorm'),
                    name=self._get_marker_title(i),  # name used in legend and hover labels
                    xbins=dict(  # bins used for histogram
                        start=self.get_config_value('xbins', 'start'),
                        end=self.get_config_value('xbins', 'end'),
                        size=xbins_size
                    ),
                    marker_color=self._get_marker_color(i),
                    opacity=self.get_config_value('opacity'),
                    showlegend=self.get_config_value('showlegend'),
                    marker=dict(
                        line=dict(
                            width=self._get_line_width(i)
                        )
                    ),
                    orientation=self.get_config_value('orientation'),

                ))
        except ValueError as ex:
            raise ValueError(
                "An exception of type {0} occurred. Check your data or config file values."
                    .format(type(ex).__name__))

        return fig

    def _get_bins_size(self):
        """Returns user defined bin size or a default value.

        Args:

        Returns:
            xbins size
        """
        xbins_size = self.get_config_value('xbins', 'size')
        if xbins_size is None:
            xbins_size = self.DEFAULT_XBINS_SIZE
        return xbins_size

    def _get_marker_title(self, i):
        """Returns user defined marker title or a default value.

        Args:
            @param i - the index if the marker data in the input array
        Returns:
            name of the marker
        """
        legend_titles = self.get_config_value('legend_titles')
        if legend_titles is None or len(legend_titles) <= i:
            return self.DEFAULT_TITLE_FORMAT.format(i + 1)
        return self.get_config_value('legend_titles')[i]

    def _get_line_width(self, i):
        """Returns user defined marker line width or a default value.

        Args:
            @param i - the index if the marker data in the input array
        Returns:
            line width
        """
        line_width = self.get_config_value('line_width')
        if line_width is None or len(line_width) <= i:
            return self.DEFAULT_LINE_WIDTH

        return line_width[i]

    def _get_marker_color(self, i):
        """Returns user defined marker color or a default value.

        Args:
            @param i - the index if the marker data in the input array
        Returns:
            color
        """
        hist_marker_colors = self.get_config_value('colors')
        if hist_marker_colors is None or len(hist_marker_colors) <= i:
            return self.DEFAULT_COLOR
        return self.get_config_value('colors')[i]


def main():
    """ Example how to use Histogram"""
    # open user's config file
    with open("/Users/tatiana/histogram.yml", 'r') as stream:
        try:
            docs = yaml.load(stream, Loader=yaml.FullLoader)
        except yaml.YAMLError as exc:
            print(exc)

    # read user's data from file and arrange it in the array
    input_data_file = "/Users/tatiana/Rscript/test_data.txt"
    input_data = pd.read_csv(input_data_file, header=[0], sep=' ')
    data = []
    data.append(input_data['FCST'])
    data.append(input_data['OBS'])

    # create a histogram
    try:
        histogram = Histogram(docs, data)
        # img_bytes = histogram.get_img_bytes()

        # save to file
        histogram.save_to_file()
        # histogram.show()
    except ValueError as v_error:
        print(v_error)


if __name__ == "__main__":
    # main()
    data = [np.random.randn(500), np.random.randn(500) + 1]
    try:
        histogram = Histogram(None, data)
        histogram.show_in_browser()
        histogram.save_to_file()
    except ValueError as ve:
        print(ve)
