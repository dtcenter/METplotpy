"""
Class Name: histogram_ini.py
 """
__author__ = 'Tatiana Burek and Minna Win'
__email__ = 'met_help@ucar.edu'

import os
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from plots.met_plot_ini import MetPlotIni
import config_metplus
import util.config_utils as cu

class HistogramIni(MetPlotIni):
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
            parameters - dictionary containing default and user defined parameters
            data       - two dimensional data array
        """

        # read defaults stored in INI formatted file into the dictionary
        # location = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
        # location of the histogram_defaults.conf file
        if os.environ['METPLOTPY_BASE']:
            location = os.path.join(os.environ['METPLOTPY_BASE'], "plots/configs")
        else:
            location = os.path.realpath(os.path.join(os.getcwd(),"../../metplotpy/plots/configs"))


        # a list of default configs is the expected input arg by config_metplus.setup(). Here, we
        # create a list of one default config file for the histogram plot.
        histogram_default_path = [os.path.join(location, 'histogram_defaults.conf')]
        histo_default_config = config_metplus.setup(histogram_default_path)
        histogram_default = cu.get_config_dict(histo_default_config)

        # init common layout
        super().__init__(histogram_default, parameters)
        # create figure
        self.figure = self._create_figure(data)

    def _create_figure(self, data):
        """Draws histogram data on the layout

        Args:
            data - two dimensional data array

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
                bargap=float(self.get_config_value('config','bargap')),
                # bargroupgap=0.1  # gap between bars of the same location coordinates\
                showlegend=self.convert_str_to_bool(self.get_config_value('config', 'show_legend')),
                legend_orientation=self.get_config_value('legend', 'orientation'),
                legend=self.get_legend(),
                plot_bgcolor=self.get_config_value('config', 'plot_bgcolor'),
                height=int(self.get_config_value('config', 'height')),
                width=int(self.get_config_value('config', 'width')),
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
                    histnorm=self.get_config_value('config', 'histnorm'),
                    name=self._get_marker_title(i),  # name used in legend and hover labels
                    xbins=dict(  # bins used for histogram
                        start=self.get_config_value('xbins', 'start'),
                        end=self.get_config_value('xbins', 'end'),
                        size=xbins_size
                    ),
                    marker_color=self._get_marker_color(i),
                    opacity=int(self.get_config_value('config', 'opacity')),
                    showlegend=self.convert_str_to_bool(self.get_config_value('config', 'show_legend')),
                    marker=dict(
                        line=dict(
                            width=self._get_line_width(i)
                        )
                    ),
                    orientation=self.get_config_value('config', 'orientation'),

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
            i - the index if the marker data in the input array
        Returns:
            name of the marker
        """
        legend_titles = self.get_config_value('config', 'legend_titles')
        if legend_titles is None or len(legend_titles) <= i:
            return self.DEFAULT_TITLE_FORMAT.format(i + 1)
        return self.get_config_value('config', 'legend_titles')[i]


    def _get_line_width(self, i):
        """Returns user defined marker line width or a default value.

        Args:
            i - the index if the marker data in the input array
        Returns:
            line width
        """
        line_width = self.get_config_value('config', 'line_width')
        if line_width is None or len(line_width) <= i:
            return self.DEFAULT_LINE_WIDTH

        return line_width[i]

    def _get_xline_width(self, i):
        """Returns user defined marker line width or a default value.

        Args:
            i - the index if the marker data in the input array
        Returns:
            line width
        """
        line_width = self.get_config_value('xaxis', 'line_width')
        if line_width is None or len(line_width) <= i:
            return self.DEFAULT_LINE_WIDTH

        return line_width[i]

    def _get_yline_width(self, i):
        """Returns user defined marker line width or a default value.

        Args:
            i - the index if the marker data in the input array
        Returns:
            line width
        """
        line_width = self.get_config_value('yaxis', 'line_width')
        if line_width is None or len(line_width) <= i:
            return self.DEFAULT_LINE_WIDTH

        return line_width[i]

    def _get_marker_color(self, i):
        """Returns user defined marker color or a default value.

        Args:
            i - the index if the marker data in the input array
        Returns:
            color
        """
        hist_marker_colors = self.get_config_value('config', 'marker_color')
        if hist_marker_colors is None or len(hist_marker_colors) <= i:
            return self.DEFAULT_COLOR
        return self.get_config_value('config', 'marker_color')[i]


def main():
    """ Example how to use Histogram"""
    # open user's config file(s) via METplus and produtil modules that utilize
    # Python's ConfigParser. Use the default histogram default
    config_list = ['../configs/histogram_defaults.conf']
    config = config_metplus.setup(config_list)
    config_dict = cu.get_config_dict(config)


    # read user's data from file and arrange it in the array
    # input_data_file = "/Users/tatiana/Rscript/test_data.txt"
    # input_data = pd.read_csv(input_data_file, header=[0], sep=' ')
    # data = []
    # data.append(input_data['FCST'])
    # data.append(input_data['OBS'])
    data = [np.random.randn(500), np.random.randn(500) + 1]

    # create a histogram
    try:
        histogram = HistogramIni(config_dict, data)
        # img_bytes = histogram.get_img_bytes()

        # save to file
        histogram.save_to_file()
        # histogram.show()
    except ValueError as v_error:
        print(v_error)


if __name__ == "__main__":
    # main()
    data = [np.random.randn(500), np.random.randn(500) + 1]
    config_list = ['../configs/histogram_defaults.conf']
    config = config_metplus.setup(config_list)
    config_dict = cu.get_config_dict(config)

    histogram = HistogramIni(config_dict, dat       a)
    histogram.show_in_browser()