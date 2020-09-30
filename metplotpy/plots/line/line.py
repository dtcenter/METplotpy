"""
Class Name: line.py
 """
__author__ = 'Tatiana Burek'
__email__ = 'met_help@ucar.edu'

import os
import re
import csv
from operator import add
import yaml
import numpy as np
import pandas as pd

import plotly.graph_objects as go
from plotly.subplots import make_subplots
from plotly.graph_objs.layout import XAxis

from plots.constants import XAXIS_ORIENTATION, YAXIS_ORIENTATION
from plots.line.line_config import LineConfig
from plots.line.line_series import LineSeries
from plots.met_plot import MetPlot
import plots.util as util

import metcalcpy.util.utils as calc_util


class Line(MetPlot):
    """  Generates a Plotly line plot for 1 or more traces (lines)
         where each line is represented by a text point data file.
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
            Read the input data file
            and store as a pandas dataframe so we can subset the
            data to represent each of the series defined by the
            series_val permutations.

            Args:

            Returns:

        """
        return pd.read_csv(self.config_obj.stat_input, sep='\t',
                           header='infer', float_precision='round_trip')

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

        # add series for y1 axis
        num_series_y1 = len(self.config_obj.all_series_y1)
        for i in range(num_series_y1):
            series_obj = LineSeries(self.config_obj, i, input_data, series_list)
            series_list.append(series_obj)

        # add series for y2 axis
        num_series_y2 = len(self.config_obj.all_series_y2)
        for i in range(num_series_y2):
            series_obj = LineSeries(self.config_obj, num_series_y1 + i, input_data, series_list, 2)
            series_list.append(series_obj)

        # reorder series
        series_list = self.config_obj.create_list_by_series_ordering(series_list)

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
        fig.update_layout(width=width, height=height,
                          margin=self.config_obj.plot_margins,
                          paper_bgcolor="white"
                          )

        title = util.apply_weight_style(self.config_obj.title, self.config_obj.parameters['title_weight'])

        # Add figure title
        fig.update_layout(
            title={'text': title,
                   'font': {
                       'size': self.config_obj.parameters['title_size'] + 10,
                   },
                   'y': self.config_obj.parameters['title_offset'] * -0.45,
                   'x': self.config_obj.parameters['title_align'],
                   'xanchor': "center",
                   'yanchor': "top"
                   },
            plot_bgcolor="#FFF"

        )
        # Set x-axis title
        x_points = self.config_obj.indy_vals
        x_points_index = list(range(0, len(x_points)))

        blended_grid_col = util.alpha_blending(self.config_obj.get_config_value('grid_col'), 0.5)

        x_axis_title = util.apply_weight_style(self.config_obj.xaxis, self.config_obj.parameters['xlab_weight'])
        fig.update_xaxes(title_text=x_axis_title, linecolor="#c2c2c2", linewidth=2,
                         showgrid=self.config_obj.grid_on,
                         ticks="inside",
                         zeroline=False,
                         gridwidth=self.config_obj.get_config_value('grid_lwd') / 2,
                         gridcolor=blended_grid_col,
                         automargin=True,
                         title_font={'size': self.config_obj.parameters['xlab_size'] + 10},
                         title_standoff=abs(self.config_obj.parameters['xlab_offset'])
                         )

        # Set y-axes titles
        y_axis_title = util.apply_weight_style(self.config_obj.yaxis_1, self.config_obj.parameters['ylab_weight'])
        fig.update_yaxes(title_text=y_axis_title,
                         secondary_y=False, linecolor="#c2c2c2", linewidth=2,
                         showgrid=self.config_obj.grid_on,
                         zeroline=False, ticks="inside",
                         gridwidth=self.config_obj.get_config_value('grid_lwd') / 2,
                         gridcolor=blended_grid_col,
                         automargin=True,
                         title_font={'size': self.config_obj.parameters['ylab_size'] + 10},
                         title_standoff=abs(self.config_obj.parameters['ylab_offset'])
                         )
        if self.config_obj.parameters['list_stat_2']:
            y_axis_title = util.apply_weight_style(self.config_obj.yaxis_2, self.config_obj.parameters['y2lab_weight'])
            fig.update_yaxes(title_text=y_axis_title,
                             secondary_y=True, linecolor="#c2c2c2", linewidth=2,
                             showgrid=False, zeroline=False, ticks="inside",
                             title_font={'size': self.config_obj.parameters['y2lab_size'] + 10},
                             title_standoff=abs(self.config_obj.parameters['y2lab_offset']))

        # style the legend box
        border_width = 2
        if not self.config_obj.draw_box:
            border_width = 0
        orientation = 'h'
        if self.config_obj.parameters['legend_ncol'] == 1:
            orientation = 'v'
        fig.update_layout(legend=dict(x=self.config_obj.bbox_x, y=self.config_obj.bbox_y,
                                      xanchor='center',
                                      yanchor='top',
                                      bordercolor="black",
                                      borderwidth=border_width,
                                      orientation=orientation,
                                      font=dict(
                                          size=self.config_obj.legend_size,
                                          color="black"
                                      ),
                                      ))

        # x1 axis label formatting
        tickangle = self.config_obj.parameters['xtlab_orient']
        if tickangle in XAXIS_ORIENTATION.keys():
            tickangle = XAXIS_ORIENTATION[tickangle]

        tickfont_size = 10 * self.config_obj.parameters['xtlab_size']

        fig.update_layout(xaxis=dict(
            tickangle=tickangle,
            tickfont=dict(size=tickfont_size)
        ))

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

        yaxis_min = None
        yaxis_max = None

        for idx, series in enumerate(self.series_list):

            # Don't generate the plot for this series if
            # it isn't requested (as set in the config file)
            if series.plot_disp:
                y_points = series.series_points['dbl_med']

                # collect min-max if we need to sync axis
                if self.config_obj.sync_yaxes is True and series.y_axis == 1:
                    if yaxis_min is None:
                        yaxis_min = min(y_points)
                        yaxis_max = max(y_points)
                    else:
                        if yaxis_min > min(y_points):
                            yaxis_min = min(y_points)
                        if yaxis_max < max(y_points):
                            yaxis_max = max(y_points)

                legend_label = self.config_obj.user_legends[idx]

                # show or not ci
                error_y_visible = True

                error_y_thickness = self.config_obj.linewidth_list[idx]
                show_signif = self.config_obj.get_show_signif()[idx]

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
                    y_points, x_points_index_adj = x_points_index_adj, y_points

                # add the plot
                fig.add_trace(
                    go.Scatter(x=x_points_index_adj, y=y_points, showlegend=True,
                               mode=self.config_obj.mode[idx],
                               textposition="top right", name=legend_label,
                               connectgaps=self.config_obj.con_series[idx] == 1,
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
                                            visible=error_y_visible,
                                            thickness=error_y_thickness)
                               ),
                    secondary_y=series.y_axis != 1
                )
                n_stats = list(map(add, n_stats, series.series_points['nstat']))

        tickangle = self.config_obj.parameters['ytlab_orient']
        if tickangle in YAXIS_ORIENTATION.keys():
            tickangle = YAXIS_ORIENTATION[tickangle]
        tickfont_size = 10 * self.config_obj.parameters['ytlab_size']

        fig.update_layout(yaxis=dict(
            tickangle=tickangle,
            tickfont=dict(size=tickfont_size)
        ))

        if len(self.config_obj.all_series_y2) > 0:
            tickangle = self.config_obj.parameters['y2tlab_orient']
            if tickangle in YAXIS_ORIENTATION.keys():
                tickangle = YAXIS_ORIENTATION[tickangle]
            tickfont_size = 10 * self.config_obj.parameters['y2tlab_size']
            fig['layout']['yaxis2'].update(yaxis2=dict(
                tickangle=tickangle,
                tickfont=dict(size=tickfont_size)
            ))

        # update x1 or y1 axis ticks and tick text
        if self.config_obj.vert_plot is True:
            fig.update_layout(
                yaxis=dict(
                    tickmode='array',
                    tickvals=x_points_index,
                    ticktext=self.config_obj.indy_label
                )
            )
        else:
            fig.update_layout(
                xaxis=dict(
                    tickmode='array',
                    tickvals=x_points_index,
                    ticktext=self.config_obj.indy_label
                )
            )

        # reverse xaxis if needed
        if self.config_obj.xaxis_reverse is True:
            fig.update_xaxes(autorange="reversed")

        #  Synch y axis if needed
        if self.config_obj.sync_yaxes is True:
            fig['layout']['yaxis1'].update(range=[yaxis_min, yaxis_max], autorange=False)
            fig['layout']['yaxis2'].update(range=[yaxis_min, yaxis_max], autorange=False)

        # apply y-axis limits
        if len(self.config_obj.parameters['ylim']) > 0:
            fig['layout']['yaxis1'].update(range=[self.config_obj.parameters['ylim'][0],
                                                  self.config_obj.parameters['ylim'][1]],
                                           autorange=False)
        # apply y2-axis limits
        if len(self.config_obj.parameters['y2lim']) > 0:
            fig['layout']['yaxis2'].update(range=[self.config_obj.parameters['y2lim'][0],
                                                  self.config_obj.parameters['y2lim'][1]],
                                           autorange=False)

        # add x2 axis if applicable
        if self.config_obj.show_nstats:
            x_axis_title = util.apply_weight_style('NStats', self.config_obj.parameters['x2lab_weight'])
            fig.update_layout(xaxis2=XAxis(title_text=x_axis_title, overlaying='x',
                                           side='top', linecolor="#c2c2c2",
                                           linewidth=2, showgrid=False,
                                           zeroline=False, ticks="inside",
                                           title_font={'size': self.config_obj.parameters['x2lab_size'] + 10},
                                           title_standoff=abs(self.config_obj.parameters['x2lab_offset'])
                                           )
                              )
            fig.update_layout(
                xaxis2=dict(
                    tickmode='array',
                    tickvals=x_points_index,
                    ticktext=n_stats
                )
            )
            # x2 axis label formatting
            tickangle = self.config_obj.parameters['x2tlab_orient']
            if tickangle in XAXIS_ORIENTATION.keys():
                tickangle = XAXIS_ORIENTATION[tickangle]
            tickfont_size = 10 * self.config_obj.parameters['x2tlab_size']
            fig.update_layout(xaxis2=dict(tickangle=tickangle, tickfont=dict(size=tickfont_size)))
            fig.add_trace(
                go.Scatter(y=[None] * len(x_points), x=x_points_index,
                           xaxis='x2', showlegend=False),
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

            for series_idx, series in enumerate(self.series_list):
                y_points = series.series_points['dbl_med']
                dbl_up_ci = series.series_points['dbl_up_ci']
                dbl_lo_ci = series.series_points['dbl_lo_ci']
                if series.y_axis == 1:
                    for indy_val_idx in range(len(self.config_obj.indy_vals)):
                        all_points_1[indy_val_idx][series_idx * 3] = y_points[indy_val_idx]
                        if not y_points[indy_val_idx] is None \
                                and not dbl_lo_ci[indy_val_idx] is None:
                            all_points_1[indy_val_idx][series_idx * 3 + 1] = \
                                y_points[indy_val_idx] - dbl_lo_ci[indy_val_idx]
                        else:
                            all_points_1[indy_val_idx][series_idx * 3 + 1] = None

                        if not y_points[indy_val_idx] is None \
                                and not dbl_up_ci[indy_val_idx] is None:
                            all_points_1[indy_val_idx][series_idx * 3 + 2] = \
                                y_points[indy_val_idx] + dbl_up_ci[indy_val_idx]
                        else:
                            all_points_1[indy_val_idx][series_idx * 3 + 2] = None
                else:
                    adjusted_idx = series_idx - len(self.config_obj.all_series_y1)
                    for indy_val_idx in range(len(self.config_obj.indy_vals)):
                        all_points_2[indy_val_idx][adjusted_idx * 3] = y_points[indy_val_idx]
                        if not y_points[indy_val_idx] is None \
                                and not dbl_lo_ci[indy_val_idx] is None:
                            all_points_2[indy_val_idx][adjusted_idx * 3 + 1] = \
                                y_points[indy_val_idx] - dbl_lo_ci[indy_val_idx]
                        else:
                            all_points_2[indy_val_idx][adjusted_idx * 3 + 1] = None

                        if not y_points[indy_val_idx] is None \
                                and not dbl_up_ci[indy_val_idx] is None:
                            all_points_2[indy_val_idx][adjusted_idx * 3 + 2] = \
                                y_points[indy_val_idx] + dbl_up_ci[indy_val_idx]
                        else:
                            all_points_2[indy_val_idx][adjusted_idx * 3 + 2] = None

            if self.config_obj.dump_points_1 is True:
                try:
                    all_points_1_formatted = []
                    for row in all_points_1:
                        formatted_row = []
                        for val in row:
                            if val is None:
                                formatted_row.append("N/A")
                            else:
                                formatted_row.append("%.6f" % val)
                        all_points_1_formatted.append(formatted_row)
                    with open(output_file_1, "w+") as my_csv:
                        csv_writer = csv.writer(my_csv, delimiter=' ')
                        csv_writer.writerows(all_points_1_formatted)

                except TypeError:
                    print('Can\'t save points to a file')

            if self.config_obj.series_vals_2 and self.config_obj.dump_points_2 is True:
                try:
                    all_points_2_formatted = []
                    for row in all_points_2:
                        formatted_row = []
                        for val in row:
                            if val is None:
                                formatted_row.append("N/A")
                            else:
                                formatted_row.append("%.6f" % val)
                        all_points_2_formatted.append(formatted_row)
                    with open(output_file_2, "w+") as my_csv:
                        csv_writer = csv.writer(my_csv, delimiter=' ')
                        csv_writer.writerows(all_points_2_formatted)

                except TypeError:
                    print('Can\'t save points to a file')


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
        plot = Line(docs)
        plot.save_to_file()
        plot.show_in_browser()
        plot.write_html()
    except ValueError as val_er:
        print(val_er)


if __name__ == "__main__":
    main()
