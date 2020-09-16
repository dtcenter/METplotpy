"""
Class Name: line.py
 """
__author__ = 'Tatiana Burek'
__email__ = 'met_help@ucar.edu'

import os

import plotly.graph_objects as go
import numpy as np
import yaml
import pandas as pd
import re

from plots.line.line_config import LineConfig
from plots.line.line_series import LineSeries
from plots.met_plot import MetPlot

import metcalcpy.util.utils as calc_util
import plots.util as util
from plotly.subplots import make_subplots
from plotly.graph_objs.layout import XAxis
from operator import add


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

        # instantiate a LineConfig object, which holds all the necessary settings from the
        # config file that represents the MetPlot object (Line).
        self.config_obj = LineConfig(self.parameters)

        # Read in input data, location specified in config file
        self.input_df = self._read_input_data()

        # Apply event equalization, if requested
        if self.config_obj.use_ee is True:
            self.input_df = calc_util.perform_event_equalization(self.parameters, self.input_df)

        # Create a list of series objects.
        # Each series object contains all the necessary information for plotting,
        # such as line color, marker symbol,
        # line width, and criteria needed to subset the input dataframe.
        self.series_list = self._create_series(self.input_df)

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

    def _read_input_data(self):
        """
            Read the input data file (either CTC or PCT linetype)
            and store as a pandas dataframe so we can subset the
            data to represent each of the series defined by the
            series_val permutations.

            Args:

            Returns:

        """
        return pd.read_csv(self.config_obj.stat_input, sep='\t', header='infer', float_precision='round_trip')

    def _create_series(self, input_data):
        """
           Generate all the series objects that are to be displayed as specified by the plot_disp
           setting in the config file.  The points are all ordered by datetime.  Each series object
           is represented by a line in the diagram, so they also contain information
           for line width, line- and marker-colors, line style, and other plot-related/
           appearance-related settings (which were defined in the config file).

           Args:
               input_data:  The input data in the form of a Pandas dataframe.
                            This data will be subset to reflect the series data of interest.

           Returns:
               a list of series objects that are to be displayed


        """
        series_list = []

        # use the list of series ordering values to determine how many series objects we need.
        num_series_y1 = len(self.config_obj.all_series_y1)
        for i, series in enumerate(range(num_series_y1)):
            series_obj = LineSeries(self.config_obj, i, input_data)
            series_list.append(series_obj)

        num_series_y2 = len(self.config_obj.all_series_y2)
        for i, series in enumerate(range(num_series_y2)):
            series_obj = LineSeries(self.config_obj, num_series_y1 + i, input_data, 2)
            series_list.append(series_obj)

        return series_list

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

        fig = make_subplots(specs=[[{"secondary_y": True}]])

        # Set plot height and width in pixel value
        width = self.config_obj.plot_width
        height = self.config_obj.plot_height
        # fig.update_layout(width=width, height=height, paper_bgcolor="white")
        fig.update_layout(width=width, height=height)

        # Add figure title
        fig.update_layout(
            title={'text': self.config_obj.title,
                   'y': 0.95,
                   'x': 0.5,
                   'xanchor': "center",
                   'yanchor': "top"},
            plot_bgcolor="#FFF"

        )
        # Set x-axis title
        x_points = self.config_obj.indy_vals
        x_points_index = list(range(0, len(x_points)))

        fig.update_xaxes(title_text=self.config_obj.xaxis, linecolor="#c2c2c2", linewidth=2, showgrid=True,
                         ticks="inside",
                         gridwidth=0.5, gridcolor='#F8F8F8')

        # Set y-axes titles
        fig.update_yaxes(title_text=self.config_obj.yaxis_1, secondary_y=False, linecolor="#c2c2c2", linewidth=2,
                         showgrid=True, zeroline=False, ticks="inside", gridwidth=0.5, gridcolor='#F8F8F8')
        if self.config_obj.parameters['list_stat_2']:
            fig.update_yaxes(title_text=self.config_obj.yaxis_2, secondary_y=True, linecolor="#c2c2c2", linewidth=2,
                             showgrid=False, zeroline=False, ticks="inside", gridwidth=0.5, gridcolor='#F8F8F8')


        # style the legend box
        if self.config_obj.draw_box:
            fig.update_layout(legend=dict(x=self.config_obj.bbox_x,
                                          y=self.config_obj.bbox_y,
                                          bordercolor="black",
                                          borderwidth=2
                                          ))

        else:
            fig.update_layout(legend=dict(x=self.config_obj.bbox_x,
                                          y=self.config_obj.bbox_y
                                          ))

        # can't support number of columns in legend, can only choose
        # between horizontal or vertical alignment of legend labels
        # so only support vertical legends (ie num columns = 1)
        fig.update_layout(legend=dict(x=self.config_obj.bbox_x,
                                      y=self.config_obj.bbox_y,
                                      bordercolor="black",
                                      borderwidth=2
                                      ))

        # x1 axis label formatting
        fig.update_layout(xaxis=dict(tickangle=0, tickfont=dict(size=9)))

        n_stats = [0] * len(x_points)
        # "Dump" False Detection Rate (POFD) and PODY points to an output
        # file based on the output image filename (useful in debugging)
        if self.config_obj.dump_points_1 is True or self.config_obj.dump_points_2 is True:
            self.write_output_file()

        # TODO add diff series
        num_stag = len(self.config_obj.all_series_y1) + len(self.config_obj.all_series_y2)
        stag_vals = [0] * num_stag

        # calculate staggering values
        if self.config_obj.indy_stagger is True:
            dbl_adj_scale = (len(self.config_obj.indy_vals) - 1) / 150
            stag_vals = np.linspace(-(num_stag / 2) * dbl_adj_scale,
                                    (num_stag / 2) * dbl_adj_scale,
                                    num_stag,
                                    True)
            stag_vals = stag_vals + dbl_adj_scale / 2

        for idx, series in enumerate(self.series_list):

            # Don't generate the plot for this series if
            # it isn't requested (as set in the config file)
            if series.plot_disp:
                y_points = series.series_points['dbl_med']
                legend_label = self.config_obj.user_legends[idx]

                # show or not ci
                error_y_visible = True
                no_ci_up = all(v == 0 for v in series.series_points['dbl_up_ci'])
                no_ci_lo = all(v == 0 for v in series.series_points['dbl_lo_ci'])
                if no_ci_up is True and no_ci_lo is True:
                    error_y_visible = False

                # apply staggering offset if applicable
                if stag_vals[idx] == 0:
                    x_points_index_adj = x_points_index
                else:
                    x_points_index_adj = x_points_index + stag_vals[idx]

                if self.config_obj.vert_plot is True:
                    temp = y_points
                    y_points = x_points_index_adj
                    x_points_index_adj = temp




                # add the plot
                fig.add_trace(
                    go.Scatter(x=x_points_index_adj, y=y_points, showlegend=True, mode=self.config_obj.mode[idx],
                               textposition="top right", name=legend_label,
                               line=dict(color=self.config_obj.colors_list[idx],
                                         width=self.config_obj.linewidth_list[idx],
                                         dash=self.config_obj.linestyles_list[idx]),
                               marker_symbol=self.config_obj.marker_list[idx],
                               marker_color=self.config_obj.colors_list[idx],
                               marker_line_color=self.config_obj.colors_list[idx],
                               marker_size=self.config_obj.marker_size[idx],
                               error_y=dict(type="data",
                                            symmetric=False,
                                            array=series.series_points['dbl_up_ci'],
                                            arrayminus=series.series_points['dbl_lo_ci'],
                                            visible=error_y_visible)
                               ),
                    secondary_y=series.y_axis != 1
                )
                n_stats = list(map(add, n_stats, series.series_points['nstat']))

        # update x1 or y1 axis ticks and tick text
        if self.config_obj.vert_plot is True:
            fig.update_layout(
                yaxis=dict(
                    tickmode='array',
                    tickvals=x_points_index,
                    ticktext=x_points
                )
            )
        else:
            fig.update_layout(
                xaxis=dict(
                    tickmode='array',
                    tickvals=x_points_index,
                    ticktext=x_points
                )
            )

        if self.config_obj.xaxis_reverse is True:
            fig.update_xaxes(autorange="reversed")

        # add x2 axis if applicable
        if self.config_obj.show_nstats:
            fig.update_layout(xaxis2=XAxis(title_text='NStats', overlaying='x', side='top', linecolor="#c2c2c2",
                                           linewidth=2, showgrid=False, zeroline=False, ticks="inside"))
            fig.update_layout(
                xaxis2=dict(
                    tickmode='array',
                    tickvals=x_points_index,
                    ticktext=n_stats
                )
            )
            # x2 axis label formatting
            fig.update_layout(xaxis2=dict(tickangle=0, tickfont=dict(size=9)))
            fig.add_trace(
                go.Scatter(y=[None] * len(x_points), x=x_points_index, xaxis='x2', showlegend=False),
            )

        return fig

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

    def remove_file(self):
        """
           Removes previously made image file .  Invoked by the parent class before self.output_file
           attribute can be created, but overridden here.
        """

        image_name = self.get_config_value('plot_filename')

        # remove the old file if it exist
        if os.path.exists(image_name):
            os.remove(image_name)

    def write_html(self):
        name_arr = self.get_config_value('plot_filename').split('.')
        html_name = name_arr[0] + ".html"
        self.figure.write_html(html_name, include_plotlyjs=False)

    def write_output_file(self):
        """
            Writes the POFD (False alarm ratio) and PODY data points that are
            being plotted

        """

        # Open file, name it based on the stat_input config setting,
        # (the input data file) except replace the .data
        # extension with .points1 extension
        input_filename = self.config_obj.stat_input
        match = re.match(r'(.*)(.data)', input_filename)
        if match:
            filename_only = match.group(1)
            output_file_1 = filename_only + ".points1"
            output_file_2 = filename_only + ".points2"

            all_points_1 = [[0 for x in range(len(self.config_obj.all_series_y1) * 3)] for y in
                            range(len(self.config_obj.indy_vals))]
            if self.config_obj.series_vals_2:
                all_points_2 = [[0 for x in range(len(self.config_obj.all_series_y2) * 3)] for y in
                                range(len(self.config_obj.indy_vals))]

            for idx, series in enumerate(self.series_list):
                y_points = series.series_points['dbl_med']
                dbl_up_ci = series.series_points['dbl_up_ci']
                dbl_lo_ci = series.series_points['dbl_lo_ci']
                if series.y_axis == 1:
                    for x in range(len(self.config_obj.indy_vals)):
                        all_points_1[x][idx * 3] = y_points[x]
                        all_points_1[x][idx * 3 + 1] = y_points[x] -dbl_lo_ci[x]
                        all_points_1[x][idx * 3 + 2] = y_points[x] +dbl_up_ci[x]
                else:
                    adjusted_idx = idx - len(self.config_obj.all_series_y1)
                    for x in range(len(self.config_obj.indy_vals)):
                        all_points_2[x][adjusted_idx * 3] = y_points[x]
                        all_points_2[x][adjusted_idx * 3 + 1] = y_points[x] - dbl_lo_ci[x]
                        all_points_2[x][adjusted_idx * 3 + 2] = y_points[x] + dbl_up_ci[x]

            if self.config_obj.dump_points_1 is True:
                np.savetxt(output_file_1, all_points_1, fmt='%.6f')
            if self.config_obj.series_vals_2 and self.config_obj.dump_points_2 is True:
                np.savetxt(output_file_2, all_points_2, fmt='%.6f')


def main():
    """
            Generates a sample, default, ROC diagram using the
            default and custom config files on sample data found in this directory.
            The location of the input data is defined in either the default or
            custom config file.
        """

    # Retrieve the contents of the custom config file to over-ride
    # or augment settings defined by the default config file.
    # with open("./custom_roc_diagram.yaml", 'r') as stream:
    config_file = util.read_config_from_command_line()
    with open(config_file, 'r') as stream:
        try:
            docs = yaml.load(stream, Loader=yaml.FullLoader)
        except yaml.YAMLError as exc:
            print(exc)

    try:
        r = Line(docs)
        r.save_to_file()
        r.show_in_browser()
        r.write_html()
    except ValueError as ve:
        print(ve)


if __name__ == "__main__":
    main()
