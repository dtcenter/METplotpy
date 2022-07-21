# ============================*
 # ** Copyright UCAR (c) 2020
 # ** University Corporation for Atmospheric Research (UCAR)
 # ** National Center for Atmospheric Research (NCAR)
 # ** Research Applications Lab (RAL)
 # ** P.O.Box 3000, Boulder, Colorado, 80307-3000, USA
 # ============================*
 
 
 
"""
Class Name: line.py
 """
__author__ = 'Tatiana Burek'

import os
import re
import csv
from operator import add
from typing import Union
from itertools import chain

import yaml
import numpy as np
import pandas as pd

import plotly.graph_objects as go
from plotly.subplots import make_subplots
from plotly.graph_objects import Figure

from metplotpy.plots.constants import PLOTLY_AXIS_LINE_COLOR, PLOTLY_AXIS_LINE_WIDTH, PLOTLY_PAPER_BGCOOR
from metplotpy.plots.line.line_config import LineConfig
from metplotpy.plots.line.line_series import LineSeries
from metplotpy.plots.base_plot import BasePlot
from metplotpy.plots import util
from metplotpy.plots.series import Series

import metcalcpy.util.utils as calc_util


class Line(BasePlot):
    """  Generates a Plotly line plot for 1 or more traces (lines)
         where each line is represented by a text point data file.
    """

    defaults_name = 'line_defaults.yaml'

    def __init__(self, parameters: dict) -> None:
        """ Creates a line plot consisting of one or more lines (traces), based on
            settings indicated by parameters.

            Args:
            @param parameters: dictionary containing user defined parameters

        """

        # init common layout
        super().__init__(parameters, self.defaults_name)

        self.allow_secondary_y = True

        # instantiate a LineConfig object, which holds all the necessary settings from the
        # config file that represents the BasePlot object (Line).
        self.config_obj = LineConfig(self.parameters)

        # Check that we have all the necessary settings for each series
        is_config_consistent = self.config_obj._config_consistency_check()
        if not is_config_consistent:
            raise ValueError("The number of series defined by series_val_1/2 and derived curves is"
                             " inconsistent with the number of settings"
                             " required for describing each series. Please check"
                             " the number of your configuration file's plot_i,"
                             " plot_disp, series_order, user_legend,"
                             " colors, and series_symbols settings.")

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
        # the methods in base_plot.py (BasePlot class methods) to
        # create binary versions of the plot.
        self._create_figure()

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
        return pd.read_csv(self.config_obj.parameters['stat_input'], sep='\t',
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
        num_series_y1 = len(self.config_obj.get_series_y(1))
        for i, name in enumerate(self.config_obj.get_series_y(1)):
            series_obj = LineSeries(self.config_obj, i, input_data, series_list, name)
            series_list.append(series_obj)

        # add series for y2 axis
        num_series_y2 = len(self.config_obj.get_series_y(2))
        for i, name in enumerate(self.config_obj.get_series_y(2)):
            series_obj = LineSeries(self.config_obj, num_series_y1 + i,
                                    input_data, series_list, name, 2)
            series_list.append(series_obj)

        # add derived for y1 axis
        num_series_y1_d = len(self.config_obj.get_config_value('derived_series_1'))
        for i, name in enumerate(self.config_obj.get_config_value('derived_series_1')):
            # add default operation value if it is not provided
            if len(name) == 2:
                name.append("DIFF")
            # include the series only if the name is valid
            if len(name) == 3:
                series_obj = LineSeries(self.config_obj, num_series_y1 + num_series_y2 + i,
                                    input_data, series_list, name)
                series_list.append(series_obj)

        # add derived for y2 axis
        for i, name in enumerate(self.config_obj.get_config_value('derived_series_2')):
            # add default operation value if it is not provided
            if len(name) == 2:
                name.append("DIFF")
            # include the series only if the name is valid
            if len(name) == 3:
                series_obj = LineSeries(self.config_obj,
                                    num_series_y1 + num_series_y2 + num_series_y1_d + i,
                                    input_data, series_list, name, 2)
                series_list.append(series_obj)

        # reorder series
        series_list = self.config_obj.create_list_by_series_ordering(series_list)

        return series_list

    def _create_figure(self):
        """
        Create a line plot from defaults and custom parameters
        """
        # create and draw the plot
        self.figure = self._create_layout()
        self._add_xaxis()
        self._add_yaxis()
        self._add_y2axis()
        self._add_legend()


        # calculate stag adjustments
        stag_adjustments = self._calc_stag_adjustments()

        x_points_index = list(range(0, len(self.config_obj.indy_vals)))

        # create a vertical plot if needed
        self._adjust_for_vertical(x_points_index)

        # reverse xaxis if needed
        if self.config_obj.xaxis_reverse is True:
            if self.config_obj.vert_plot is True:
                self.figure.update_yaxes(autorange="reversed")
            else:
                self.figure.update_xaxes(autorange="reversed")

        # placeholder for the number of stats
        n_stats = [0] * len(self.config_obj.indy_vals)

        # placeholder for the min and max values for y-axis
        yaxis_min = None
        yaxis_max = None

        # add series lines
        for series in self.series_list:

            # Don't generate the plot for this series if
            # it isn't requested (as set in the config file)
            if series.plot_disp:

                # collect min-max if we need to sync axis
                if self.config_obj.sync_yaxes is True:
                    yaxis_min, yaxis_max = self._find_min_max(series, yaxis_min, yaxis_max)

                # apply staggering offset if applicable
                if stag_adjustments[series.idx] == 0:
                    x_points_index_adj = x_points_index
                else:
                    x_points_index_adj = x_points_index + stag_adjustments[series.idx]

                self._draw_series(series, x_points_index_adj)

                # aggregate number of stats
                n_stats = list(map(add, n_stats, series.series_points['nstat']))

        # add custom lines
        self._add_lines(self.config_obj, x_points_index)

        # apply y axis limits
        self._yaxis_limits()
        self._y2axis_limits()

        # sync axis
        self._sync_yaxis(yaxis_min, yaxis_max)

        # add x2 axis
        self._add_x2axis(n_stats)

        # Allow plots to start from the y=0 line if set in the config file
        if self.config_obj.start_from_zero is True:
            self.figure.update_xaxes(range=[0, len(x_points_index) - 1])

    def _draw_series(self, series: Series, x_points_index_adj: Union[list, None] = None) -> None:
        """
        Draws the formatted line with CIs if needed on the plot

        :param series: Line series object with data and parameters
        :param x_points_index_adj: values for adjusting x-values position
        """

        y_points = series.series_points['dbl_med']

        # show or not ci
        # see if any ci values in not 0
        no_ci_up = all(v == 0 for v in series.series_points['dbl_up_ci'])
        no_ci_lo = all(v == 0 for v in series.series_points['dbl_lo_ci'])
        error_y_visible = True
        if (no_ci_up is True and no_ci_lo is True) or self.config_obj.plot_ci[series.idx] == 'NONE':
            error_y_visible = False

        # switch x amd y values for the vertical plot
        if self.config_obj.vert_plot is True:
            y_points, x_points_index_adj = x_points_index_adj, y_points

        # add the plot
        self.figure.add_trace(
            go.Scatter(x=x_points_index_adj,
                       y=y_points,
                       showlegend=True,
                       mode=self.config_obj.mode[series.idx],
                       textposition="top right",
                       name=self.config_obj.user_legends[series.idx],
                       connectgaps=self.config_obj.con_series[series.idx] == 1,
                       line={'color': self.config_obj.colors_list[series.idx],
                             'width': self.config_obj.linewidth_list[series.idx],
                             'dash': self.config_obj.linestyles_list[series.idx]},
                       marker_symbol=self.config_obj.marker_list[series.idx],
                       marker_color=self.config_obj.colors_list[series.idx],
                       marker_line_color=self.config_obj.colors_list[series.idx],
                       marker_size=self.config_obj.marker_size[series.idx],
                       error_y={'type': 'data',
                                'symmetric': False,
                                'array': series.series_points['dbl_up_ci'],
                                'arrayminus': series.series_points['dbl_lo_ci'],
                                'visible': error_y_visible,
                                'thickness': self.config_obj.linewidth_list[series.idx]}
                       ),
            secondary_y=series.y_axis != 1
        )

    def _create_layout(self) -> Figure:
        """
        Creates a new layout based on the properties from the config file
        including plots size, annotation and title

        :return: Figure object
        """
        # create annotation
        annotation = [
            {'text': util.apply_weight_style(self.config_obj.parameters['plot_caption'],
                                             self.config_obj.parameters['caption_weight']),
             'align': 'left',
             'showarrow': False,
             'xref': 'paper',
             'yref': 'paper',
             'x': self.config_obj.parameters['caption_align'],
             'y': self.config_obj.caption_offset,
             'font': {
                 'size': self.config_obj.caption_size,
                 'color': self.config_obj.parameters['caption_col']
             }
             }]
        # create title
        title = {'text': util.apply_weight_style(self.config_obj.title,
                                                 self.config_obj.parameters['title_weight']),
                 'font': {
                     'size': self.config_obj.title_font_size,
                 },
                 'y': self.config_obj.title_offset,
                 'x': self.config_obj.parameters['title_align'],
                 'xanchor': 'center',
                 'xref': 'paper'
                 }

        # create a layout and allow y2 axis
        fig = make_subplots(specs=[[{"secondary_y": self.allow_secondary_y}]])

        # add size, annotation, title
        fig.update_layout(
            width=self.config_obj.plot_width,
            height=self.config_obj.plot_height,
            margin=self.config_obj.plot_margins,
            paper_bgcolor=PLOTLY_PAPER_BGCOOR,
            annotations=annotation,
            title=title,
            plot_bgcolor=PLOTLY_PAPER_BGCOOR
        )
        return fig

    def _calc_stag_adjustments(self) -> list:
        """
        Calculates the x-axis adjustment for each point if requested.
        It needed so hte points and CIs for each x-axis values don't be placed on top of each other

        :return: the list of the adjustment values
        """

        # get the total number of series
        num_stag = len(self.config_obj.all_series_y1) + len(self.config_obj.all_series_y2)

        # init the result with 0
        stag_vals = [0] * num_stag

        # calculate staggering values
        if self.config_obj.indy_stagger is True:
            dbl_adj_scale = (len(self.config_obj.indy_vals) - 1) / 150
            stag_vals = np.linspace(-(num_stag / 2) * dbl_adj_scale,
                                    (num_stag / 2) * dbl_adj_scale,
                                    num_stag,
                                    True)
            stag_vals = stag_vals + dbl_adj_scale / 2
        return stag_vals

    def _adjust_for_vertical(self, x_points_index: list) -> None:
        """
        Switches x and y axis (creates a vertical plot) if needed

        :param x_points_index: list of indexws for the original x -axis
        """

        odered_indy_label = self.config_obj.create_list_by_plot_val_ordering(self.config_obj.indy_label)
        if self.config_obj.vert_plot is True:
            self.figure.update_layout(
                yaxis={
                    'tickmode': 'array',
                    'tickvals': x_points_index,
                    'ticktext': odered_indy_label
                }
            )
        else:
            self.figure.update_layout(
                xaxis={
                    'tickmode': 'array',
                    'tickvals': x_points_index,
                    'ticktext': odered_indy_label
                }
            )

    def _add_xaxis(self) -> None:
        """
        Configures and adds x-axis to the plot
        """
        self.figure.update_xaxes(title_text=self.config_obj.xaxis,
                                 linecolor=PLOTLY_AXIS_LINE_COLOR,
                                 linewidth=PLOTLY_AXIS_LINE_WIDTH,
                                 showgrid=self.config_obj.grid_on,
                                 ticks="inside",
                                 zeroline=False,
                                 gridwidth=self.config_obj.parameters['grid_lwd'],
                                 gridcolor=self.config_obj.blended_grid_col,
                                 automargin=True,
                                 title_font={
                                     'size': self.config_obj.x_title_font_size
                                 },
                                 title_standoff=abs(self.config_obj.parameters['xlab_offset']),
                                 tickangle=self.config_obj.x_tickangle,
                                 tickfont={'size': self.config_obj.x_tickfont_size}
                                 )

    def _add_yaxis(self) -> None:
        """
        Configures and adds y-axis to the plot
        """
        self.figure.update_yaxes(title_text=
                                 util.apply_weight_style(self.config_obj.yaxis_1,
                                                         self.config_obj.parameters['ylab_weight']),
                                 secondary_y=False,
                                 linecolor=PLOTLY_AXIS_LINE_COLOR,
                                 linewidth=PLOTLY_AXIS_LINE_WIDTH,
                                 showgrid=self.config_obj.grid_on,
                                 zeroline=False,
                                 ticks="inside",
                                 gridwidth=self.config_obj.parameters['grid_lwd'],
                                 gridcolor=self.config_obj.blended_grid_col,
                                 automargin=True,
                                 title_font={
                                     'size': self.config_obj.y_title_font_size
                                 },
                                 title_standoff=abs(self.config_obj.parameters['ylab_offset']),
                                 tickangle=self.config_obj.y_tickangle,
                                 tickfont={'size': self.config_obj.y_tickfont_size}
                                 )

    def _add_y2axis(self) -> None:
        """
        Adds y2-axis if needed
        """
        if self.config_obj.parameters['list_stat_2']:
            self.figure.update_yaxes(title_text=
                                     util.apply_weight_style(self.config_obj.yaxis_2,
                                                             self.config_obj.parameters['y2lab_weight']),
                                     secondary_y=True,
                                     linecolor=PLOTLY_AXIS_LINE_COLOR,
                                     linewidth=PLOTLY_AXIS_LINE_WIDTH,
                                     showgrid=False,
                                     zeroline=False,
                                     ticks="inside",
                                     title_font={
                                         'size': self.config_obj.y2_title_font_size
                                     },
                                     title_standoff=abs(self.config_obj.parameters['y2lab_offset']),
                                     tickangle=self.config_obj.y2_tickangle,
                                     tickfont={'size': self.config_obj.y2_tickfont_size}
                                     )

    def _add_legend(self) -> None:
        """
        Creates a plot legend based on the properties from the config file
        and attaches it to the initial Figure
        """
        self.figure.update_layout(legend={'x': self.config_obj.bbox_x,
                                          'y': self.config_obj.bbox_y - 0.1,
                                          'xanchor': 'center',
                                          'yanchor': 'top',
                                          'bordercolor': self.config_obj.legend_border_color,
                                          'borderwidth': self.config_obj.legend_border_width,
                                          'orientation': self.config_obj.legend_orientation,
                                          'font': {
                                              'size': self.config_obj.legend_size,
                                              'color': "black"
                                          }
                                          })

    def _yaxis_limits(self) -> None:
        """
        Apply limits on y2 axis if needed
        """
        if len(self.config_obj.parameters['ylim']) > 0:
            self.figure.update_layout(yaxis={'range': [self.config_obj.parameters['ylim'][0],
                                                       self.config_obj.parameters['ylim'][1]],
                                             'autorange': False})

    def _y2axis_limits(self) -> None:
        """
        Apply limits on y2 axis if needed
        """
        if len(self.config_obj.parameters['y2lim']) > 0:
            self.figure.update_layout(yaxis2={'range': [self.config_obj.parameters['y2lim'][0],
                                                        self.config_obj.parameters['y2lim'][1]],
                                              'autorange': False})

    def _sync_yaxis(self, yaxis_min: Union[float, None], yaxis_max: Union[float, None]) -> None:
        """
        Forces y1 and y2 axes sync if needed by specifying the same limits on both axis.
        Use ylim property to determine the limits. If this value is not provided -
        use method parameters

        :param yaxis_min: min value or None
        :param yaxis_max: max value or None
        """
        if self.config_obj.sync_yaxes is True:
            if len(self.config_obj.parameters['ylim']) > 0:
                # use plot config parameter
                range_min = self.config_obj.parameters['ylim'][0]
                range_max = self.config_obj.parameters['ylim'][1]
            else:
                # use method parameter
                range_min = yaxis_min
                range_max = yaxis_max

            if range_min is not None and range_max is not None:
                # update y axis
                self.figure.update_layout(yaxis={'range': [range_min,
                                                           range_max],
                                                 'autorange': False})

                # update y2 axis
                self.figure.update_layout(yaxis2={'range': [range_min,
                                                            range_max],
                                                  'autorange': False})

    def _add_x2axis(self, n_stats) -> None:
        """
        Creates x2axis based on the properties from the config file
        and attaches it to the initial Figure

        :param n_stats: - labels for the axis
        """
        if self.config_obj.show_nstats:
            x_points_index = list(range(0, len(n_stats)))
            self.figure.update_layout(xaxis2={'title_text':
                                                  util.apply_weight_style('NStats',
                                                                          self.config_obj.parameters['x2lab_weight']
                                                                          ),
                                              'linecolor': PLOTLY_AXIS_LINE_COLOR,
                                              'linewidth': PLOTLY_AXIS_LINE_WIDTH,
                                              'overlaying': 'x',
                                              'side': 'top',
                                              'showgrid': False,
                                              'zeroline': False,
                                              'ticks': "inside",
                                              'title_font': {
                                                  'size': self.config_obj.x2_title_font_size
                                              },
                                              'title_standoff': abs(
                                                  self.config_obj.parameters['x2lab_offset']
                                              ),
                                              'tickmode': 'array',
                                              'tickvals': x_points_index,
                                              'ticktext': n_stats,
                                              'tickangle': self.config_obj.x2_tickangle,
                                              'tickfont': {
                                                  'size': self.config_obj.x2_tickfont_size
                                              },
                                              'scaleanchor': 'x'
                                              }
                                      )
            # reverse x2axis if needed
            if self.config_obj.xaxis_reverse is True:
                self.figure.update_layout(xaxis2={'autorange': "reversed"})

            # need to add an invisible line with all values = None
            self.figure.add_trace(
                go.Scatter(y=[None] * len(x_points_index), x=x_points_index,
                           xaxis='x2', showlegend=False)
            )

    def remove_file(self):
        """
           Removes previously made image file .  Invoked by the parent class before self.output_file
           attribute can be created, but overridden here.
        """

        super().remove_file()
        self._remove_html()

    def _remove_html(self) -> None:
        """
        Removes previously made HTML file.
        """

        name_arr = self.get_config_value('plot_filename').split('.')
        html_name = name_arr[0] + ".html"
        # remove the old file if it exist
        if os.path.exists(html_name):
            os.remove(html_name)

    def write_html(self) -> None:
        """
        Is needed - creates and saves the html representation of the plot WITHOUT Plotly.js
        """
        if self.config_obj.create_html is True:
            # construct the file name from plot_filename
            name_arr = self.get_config_value('plot_filename').split('.')
            name_arr[-1] = 'html'
            html_name = ".".join(name_arr)

            # save html
            self.figure.write_html(html_name, include_plotlyjs=False)

    def write_output_file(self) -> None:
        """
        Formats y1 and y2 series point data to the 2-dim arrays and saves them to the files
        """

        # if points_path parameter doesn't exist,
        # open file, name it based on the stat_input config setting,
        # (the input data file) except replace the .data
        # extension with .points1 extension
        # otherwise use points_path path
        match = re.match(r'(.*)(.data)', self.config_obj.parameters['stat_input'])
        if self.config_obj.dump_points_1 is True or self.config_obj.dump_points_2 is True and match:

            # create 2-dim array for y1 points and fill it with 0
            all_points_1 = [[0 for x in range(len(self.config_obj.all_series_y1) * 3)] for y in
                            range(len(self.config_obj.indy_vals))]
            if self.config_obj.series_vals_2:
                # create 2-dim array for y1 points and feel it with 0
                all_points_2 = [[0 for x in range(len(self.config_obj.all_series_y2) * 3)] for y in
                                range(len(self.config_obj.indy_vals))]
            else:
                all_points_2 = []

            # separate indexes for y1 and y2 series
            series_idx_y1 = 0
            series_idx_y2 = 0

            # get points from each series
            for series in self.series_list:
                if series.y_axis == 1:
                    self._record_points(all_points_1, series_idx_y1, series)
                    series_idx_y1 = series_idx_y1 + 1
                else:
                    self._record_points(all_points_2, series_idx_y2, series)
                    series_idx_y2 = series_idx_y2 + 1

            # replace the default path with the custom
            filename = match.group(1)
            if self.config_obj.points_path is not None:
                # get the file name
                path = filename.split(os.path.sep)
                if len(path) > 0:
                    filename = path[-1]
                else:
                    filename = '.' + os.path.sep
                filename = self.config_obj.points_path + os.path.sep + filename

            # save points
            self._save_points(all_points_1, filename + ".points1")
            self._save_points(all_points_2, filename + ".points2")

    @staticmethod
    def _find_min_max(series: LineSeries, yaxis_min: Union[float, None],
                      yaxis_max: Union[float, None]) -> tuple:
        """
        Finds min and max value between provided min and max and y-axis CI values of this series
        if yaxis_min or yaxis_max is None - min/max value of the series is returned

        :param series: series to use for calculations
        :param yaxis_min: previously calculated min value
        :param yaxis_max: previously calculated max value
        :return: a tuple with calculated min/max
        """
        # calculate series upper and lower limits of CIs
        indexes = range(len(series.series_points['dbl_med']))
        upper_range = [series.series_points['dbl_med'][i] + series.series_points['dbl_up_ci'][i]
                       for i in indexes]
        low_range = [series.series_points['dbl_med'][i] - series.series_points['dbl_lo_ci'][i]
                     for i in indexes]
        # find min max
        if yaxis_min is None or yaxis_max is None:
            return min(low_range), max(upper_range)

        return min(chain([yaxis_min], low_range)), max(chain([yaxis_max], upper_range))

    def _record_points(self, all_points: list, series_idx: int, series: LineSeries) -> None:
        """
        Put points from the series to the corresonding positions in the array
        :param all_points: 2-dim array to add points to
        :param series_idx:  the index
        :param series: LineSeries object that contains points
        """
        y_points = series.series_points['dbl_med']
        dbl_up_ci = series.series_points['dbl_up_ci']
        dbl_lo_ci = series.series_points['dbl_lo_ci']

        # for each x-axis point find y-point(s) and save them
        for indy_val_idx in range(len(self.config_obj.indy_vals)):
            # place actual value
            all_points[indy_val_idx][series_idx * 3] = y_points[indy_val_idx]

            # place CI-low value or None
            if not y_points[indy_val_idx] is None \
                    and not dbl_lo_ci[indy_val_idx] is None:

                all_points[indy_val_idx][series_idx * 3 + 1] = \
                    y_points[indy_val_idx] - dbl_lo_ci[indy_val_idx]
            else:
                all_points[indy_val_idx][series_idx * 3 + 1] = None

            # place CI-up value or None
            if not y_points[indy_val_idx] is None \
                    and not dbl_up_ci[indy_val_idx] is None:
                all_points[indy_val_idx][series_idx * 3 + 2] = \
                    y_points[indy_val_idx] + dbl_up_ci[indy_val_idx]
            else:
                all_points[indy_val_idx][series_idx * 3 + 2] = None

    @staticmethod
    def _save_points(points: list, output_file: str) -> None:
        """
        Saves array of points to the file. Ir replaces all None values to N/A and format floats
        :param points: 2-dimensional array. The 1st dimension is the number of x-axis points
            The 2nd - is the all y-points for a single  x-axis points. Each y-points has 3 numbers:
            actual value, CI low, CI high
        :param output_file: the name of the output file
        """
        try:
            all_points_formatted = []
            for row in points:
                formatted_row = []
                for val in row:
                    if val is None:
                        formatted_row.append("N/A")
                    else:
                        formatted_row.append("%.6f" % val)
                all_points_formatted.append(formatted_row)
            with open(output_file, "w+") as my_csv:
                csv_writer = csv.writer(my_csv, delimiter=' ')
                csv_writer.writerows(all_points_formatted)
            my_csv.close()

        except TypeError:
            print('Can\'t save points to a file')




def main(config_filename=None):
    """
            Generates a sample, default, line plot using the
            default and custom config files on sample data found in this directory.
            The location of the input data is defined in either the default or
            custom config file.
            Args:
                @param config_filename: default is None, the name of the custom config file to apply
        """

    # Retrieve the contents of the custom config file to over-ride
    # or augment settings defined by the default config file.
    # with open("./custom_line_plot.yaml", 'r') as stream:
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
        plot = Line(docs)
        plot.save_to_file()
        # plot.show_in_browser()
        plot.write_html()
        plot.write_output_file()
    except ValueError as val_er:
        print(val_er)


if __name__ == "__main__":
    main()
