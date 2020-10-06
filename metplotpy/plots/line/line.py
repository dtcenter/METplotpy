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
from typing import Union

import plotly.graph_objects as go
from plotly.subplots import make_subplots
from plotly.graph_objects import Figure

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

        # init common layout
        super().__init__(parameters, "line_defaults.yaml")

        # instantiate a LineConfig object, which holds all the necessary settings from the
        # config file that represents the MetPlot object (Line).
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
            series_obj = LineSeries(self.config_obj, num_series_y1 + i, input_data, series_list, name, 2)
            series_list.append(series_obj)

        # add derived for y1 axis
        num_series_y1_d = len(self.config_obj.get_config_value('derived_series_1'))
        for i, name in enumerate(self.config_obj.get_config_value('derived_series_1')):
            series_obj = LineSeries(self.config_obj, num_series_y1 + num_series_y2 + i, input_data, series_list, name)
            series_list.append(series_obj)

        # add derived for y2 axis
        for i, name in enumerate(self.config_obj.get_config_value('derived_series_2')):
            series_obj = LineSeries(self.config_obj, num_series_y1 + num_series_y2 + num_series_y1_d + i, input_data,
                                    series_list, name, 2)
            series_list.append(series_obj)

        # reorder series
        series_list = self.config_obj.create_list_by_series_ordering(series_list)

        return series_list

    def _create_figure(self):
        """ Create a line plot from default and custom parameters"""

        fig = self._create_layout()
        self._add_xaxis(fig)
        self._add_yaxis(fig)

        if self.config_obj.parameters['list_stat_2']:
            self._add_y2axis(fig)

        self._add_legend(fig)

        x_points = self.config_obj.indy_vals
        x_points_index = list(range(0, len(x_points)))
        n_stats = [0] * len(x_points)

        # add indy labels to appropriate axis
        if self.config_obj.vert_plot is True:
            fig.update_layout(
                yaxis={
                    'tickmode': 'array',
                    'tickvals': x_points_index,
                    'ticktext': self.config_obj.indy_label
                }
            )
        else:
            fig.update_layout(
                xaxis={
                    'tickmode': 'array',
                    'tickvals': x_points_index,
                    'ticktext': self.config_obj.indy_label
                }
            )

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

                legend_label = self.config_obj.user_legends[series.idx]

                # show or not ci

                error_y_thickness = self.config_obj.linewidth_list[series.idx]
                no_ci_up = all(v == 0 for v in series.series_points['dbl_up_ci'])
                no_ci_lo = all(v == 0 for v in series.series_points['dbl_lo_ci'])
                error_y_visible = True
                if no_ci_up is True and no_ci_lo is True:
                    error_y_visible = False

                # apply staggering offset if applicable
                if stag_vals[series.idx] == 0:
                    x_points_index_adj = x_points_index
                else:
                    x_points_index_adj = x_points_index + stag_vals[series.idx]

                if self.config_obj.vert_plot is True:
                    y_points, x_points_index_adj = x_points_index_adj, y_points

                # add the plot
                fig.add_trace(
                    go.Scatter(x=x_points_index_adj,
                               y=y_points,
                               showlegend=True,
                               mode=self.config_obj.mode[series.idx],
                               textposition="top right",
                               name=legend_label,
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
                                        'thickness': error_y_thickness}
                               ),
                    secondary_y=series.y_axis != 1
                )
                n_stats = list(map(add, n_stats, series.series_points['nstat']))

        # reverse xaxis if needed
        if self.config_obj.xaxis_reverse is True:
            fig.update_xaxes(autorange="reversed")

        self._yaxis_limits(fig)
        self._y2axis_limits(fig)
        self._sync_yaxis(fig, yaxis_min, yaxis_max)

        self._add_x2axis(fig, x_points, n_stats)

        return fig

    def _create_layout(self) -> Figure:
        fig = make_subplots(specs=[[{"secondary_y": True}]])

        fig.update_layout(
            width=self.config_obj.plot_width,
            height=self.config_obj.plot_height,
            margin=self.config_obj.plot_margins,
            paper_bgcolor=self.config_obj.paper_bgcolor,
            annotations=[
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
                 }],
            title={'text': util.apply_weight_style(self.config_obj.title,
                                                   self.config_obj.parameters['title_weight']),
                   'font': {
                       'size': self.config_obj.title_font_size,
                   },
                   'y': self.config_obj.title_offset,
                   'x': self.config_obj.parameters['title_align'],
                   'xanchor': 'center',
                   'xref': 'paper'
                   },
            plot_bgcolor=self.config_obj.paper_bgcolor
        )
        return fig

    def _add_xaxis(self, fig: Figure) -> None:
        fig.update_xaxes(title_text=self.config_obj.xaxis,
                         linecolor=self.config_obj.line_color,
                         linewidth=self.config_obj.line_width,
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

    def _add_yaxis(self, fig: Figure) -> None:
        fig.update_yaxes(title_text=
                         util.apply_weight_style(self.config_obj.yaxis_1,
                                                 self.config_obj.parameters['ylab_weight']),
                         secondary_y=False,
                         linecolor=self.config_obj.line_color,
                         linewidth=self.config_obj.line_width,
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

    def _add_y2axis(self, fig: Figure) -> None:
        fig.update_yaxes(title_text=
                         util.apply_weight_style(self.config_obj.yaxis_2,
                                                 self.config_obj.parameters['y2lab_weight']),
                         secondary_y=True,
                         linecolor=self.config_obj.line_color,
                         linewidth=self.config_obj.line_width,
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

    def _add_legend(self, fig: Figure) -> None:
        fig.update_layout(legend={'x': self.config_obj.bbox_x,
                                  'y': self.config_obj.bbox_y,
                                  'xanchor': 'center',
                                  'yanchor': 'top',
                                  'bordercolor': self.config_obj.legend_border_color,
                                  'borderwidth': self.config_obj.legend_border_width,
                                  'orientation': self.config_obj.legend_orientation,
                                  'font': {
                                      'size': self.config_obj.legend_size,
                                      'color': "black"
                                  },
                                  #'traceorder': 'normal'
                                  })

    def _yaxis_limits(self, fig: Figure) -> None:
        if len(self.config_obj.parameters['ylim']) > 0:
            fig.update_layout(yaxis={'range': [self.config_obj.parameters['ylim'][0],
                                               self.config_obj.parameters['ylim'][1]],
                                     'autorange': False})

    def _y2axis_limits(self, fig: Figure) -> None:
        if len(self.config_obj.parameters['y2lim']) > 0:
            fig.update_layout(yaxis2={'range': [self.config_obj.parameters['y2lim'][0],
                                                self.config_obj.parameters['y2lim'][1]],
                                      'autorange': False})

    def _sync_yaxis(self, fig: Figure, yaxis_min: Union[float, None], yaxis_max: Union[float, None]) -> None:
        if self.config_obj.sync_yaxes is True:
            if len(self.config_obj.parameters['ylim']) > 0:
                fig.update_layout(yaxis={'range': [self.config_obj.parameters['ylim'][0],
                                                   self.config_obj.parameters['ylim'][1]],
                                         'autorange': False})
                fig.update_layout(yaxis2={'range': [self.config_obj.parameters['ylim'][0],
                                                    self.config_obj.parameters['ylim'][1]],
                                          'autorange': False})
            else:
                if yaxis_min is not None and yaxis_max is not None:
                    fig.update_layout(yaxis={'range': [yaxis_min, yaxis_max],
                                             'autorange': False})
                    fig.update_layout(yaxis2={'range': [yaxis_min, yaxis_max],
                                              'autorange': False})

    def _add_x2axis(self, fig: Figure, x_points, n_stats) -> None:
        if self.config_obj.show_nstats:
            x_points_index = list(range(0, len(x_points)))
            fig.update_layout(xaxis2={'title_text':
                                          util.apply_weight_style('NStats',
                                                                  self.config_obj.parameters['x2lab_weight']),
                                      'linecolor': self.config_obj.line_color,
                                      'linewidth': self.config_obj.line_width,
                                      'overlaying': 'x',
                                      'side': 'top',
                                      'showgrid': False,
                                      'zeroline': False,
                                      'ticks': "inside",
                                      'title_font': {
                                          'size': self.config_obj.x2_title_font_size
                                      },
                                      'title_standoff': abs(self.config_obj.parameters['x2lab_offset']),
                                      'tickmode': 'array',
                                      'tickvals': x_points_index,
                                      'ticktext': n_stats,
                                      'tickangle': self.config_obj.x2_tickangle,
                                      'tickfont': {'size': self.config_obj.x2_tickfont_size},
                                      'scaleanchor': 'x'
                                      }
                              )

            fig.add_trace(
                go.Scatter(y=[None] * len(x_points), x=x_points_index,
                           xaxis='x2', showlegend=False)
            )

    def remove_file(self):
        """
           Removes previously made image file .  Invoked by the parent class before self.output_file
           attribute can be created, but overridden here.
        """

        super(Line, self).remove_file()
        self._remove_html()

    def _remove_html(self):

        name_arr = self.get_config_value('plot_filename').split('.')
        html_name = name_arr[0] + ".html"
        # remove the old file if it exist
        if os.path.exists(html_name):
            os.remove(html_name)

    def write_html(self):
        if self.config_obj.create_html is True:
            name_arr = self.get_config_value('plot_filename').split('.')
            html_name = name_arr[0] + ".html"
            self.figure.write_html(html_name, include_plotlyjs=False)

    def write_output_file(self):
        """

        """

        # Open file, name it based on the stat_input config setting,
        # (the input data file) except replace the .data
        # extension with .points1 extension

        if self.config_obj.dump_points_1 is True or self.config_obj.dump_points_2 is True:

            all_points_1 = [[0 for x in range(len(self.config_obj.all_series_y1) * 3)] for y in
                            range(len(self.config_obj.indy_vals))]
            if self.config_obj.series_vals_2:
                all_points_2 = [[0 for x in range(len(self.config_obj.all_series_y2) * 3)] for y in
                                range(len(self.config_obj.indy_vals))]
            else:
                all_points_2 = []

            series_idx_y1 = 0
            series_idx_y2 = 0
            for series in self.series_list:
                if series.y_axis == 1:
                    self._record_points(all_points_1, series_idx_y1, series)
                    series_idx_y1 = series_idx_y1 + 1
                else:
                    self._record_points(all_points_2, series_idx_y2, series)
                    series_idx_y2 = series_idx_y2 + 1

            match = re.match(r'(.*)(.data)', self.config_obj.parameters['stat_input'])
            if match:
                filename_only = match.group(1)
            else:
                filename_only = 'points'

            if self.config_obj.dump_points_1 is True:
                self.save_points(all_points_1, filename_only + ".points1")

            if self.config_obj.series_vals_2 and self.config_obj.dump_points_2 is True:
                self.save_points(all_points_2, filename_only + ".points2")

    def _record_points(self, all_points: list, series_idx: int, series: LineSeries) -> None:
        y_points = series.series_points['dbl_med']
        dbl_up_ci = series.series_points['dbl_up_ci']
        dbl_lo_ci = series.series_points['dbl_lo_ci']
        for indy_val_idx in range(len(self.config_obj.indy_vals)):
            all_points[indy_val_idx][series_idx * 3] = y_points[indy_val_idx]

            if not y_points[indy_val_idx] is None \
                    and not dbl_lo_ci[indy_val_idx] is None:
                all_points[indy_val_idx][series_idx * 3 + 1] = \
                    y_points[indy_val_idx] - dbl_lo_ci[indy_val_idx]
            else:
                all_points[indy_val_idx][series_idx * 3 + 1] = None

            if not y_points[indy_val_idx] is None \
                    and not dbl_up_ci[indy_val_idx] is None:
                all_points[indy_val_idx][series_idx * 3 + 2] = \
                    y_points[indy_val_idx] + dbl_up_ci[indy_val_idx]
            else:
                all_points[indy_val_idx][series_idx * 3 + 2] = None

    @staticmethod
    def save_points(points: list, output_file: str) -> None:
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
        plot.write_output_file()
    except ValueError as val_er:
        print(val_er)


if __name__ == "__main__":
    main()
