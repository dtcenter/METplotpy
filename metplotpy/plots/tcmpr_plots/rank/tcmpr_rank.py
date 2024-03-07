# ============================*
# ** Copyright UCAR (c) 2023
# ** University Corporation for Atmospheric Research (UCAR)
# ** National Center for Atmospheric Research (NCAR)
# ** Research Applications Lab (RAL)
# ** P.O.Box 3000, Boulder, Colorado, 80307-3000, USA
# ============================*


"""
Class Name:TcmprRank
 """

import os
import datetime

import plotly.graph_objects as go

from metplotpy.plots.tcmpr_plots.tcmpr import Tcmpr
from metplotpy.plots.tcmpr_plots.tcmpr_config import TcmprConfig
from metplotpy.plots.tcmpr_plots.tcmpr_series import TcmprSeries
from metplotpy.plots.tcmpr_plots.tcmpr_util import get_case_data
import metplotpy.plots.util as util


class TcmprRank(Tcmpr):
    """  Generates a TcmprRank plot for 1 or more traces

    """

    def __init__(self, config_obj, column_info, col, case_data, input_df, stat_name):
        """ Creates a rank plot, based on
            settings indicated by parameters.

            Args:

        """

        # init common layout
        super().__init__(config_obj, column_info, col, case_data, input_df, stat_name)


        # Set up Logging
        self.rank_logger = util.get_common_logger(self.config_obj.log_level, self.config_obj.log_filename)

        self.rank_logger.info(f"--------------------------------------------------------")

        if not self.config_obj.use_ee:
            raise Exception("ERROR: Cannot plot relative rank frequency when event equalization is disabled.")
        self.rank_logger.info("Creating Rank plot")
        self.rank_logger.info("Plot HFIP Baseline:" + self.cur_baseline)

        self._adjust_titles(stat_name)
        # Create a list of series objects.
        # Each series object contains all the necessary information for plotting,
        # such as line color, marker symbol,
        # line width, and criteria needed to subset the input dataframe.
        self.series_list = self._create_series(self.input_df, stat_name)

        # Get the case data when necessary
        if self.case_data is None:
            self.rank_logger.info("Getting case data")
            self.case_data = get_case_data(self.input_df, self.config_obj.series_vals_1, self.config_obj.indy_vals,
                                           self.config_obj.rp_diff, len(self.series_list))

        if self.config_obj.prefix is None or len(self.config_obj.prefix) == 0:
            self.plot_filename = f"{self.config_obj.plot_dir}{os.path.sep}{stat_name}_rank.png"
        else:
            self.plot_filename = f"{self.config_obj.plot_dir}{os.path.sep}{self.config_obj.prefix}_{stat_name}_rank.png"
        self.rank_logger.info(f"Plot will be saved as {self.plot_filename}" )

        # remove the old file if it exists
        if os.path.exists(self.plot_filename):
            os.remove(self.plot_filename)
        # create figure
        # pylint:disable=assignment-from-no-return
        # Need to have a self.figure that we can pass along to
        # the methods in base_plot.py (BasePlot class methods) to
        # create binary versions of the plot.
        self.rank_logger.info(f"Creating figure {datetime.datetime.now()}")
        self._create_figure(stat_name)


    def _adjust_titles(self, stat_name):
        if self.yaxis_1 is None or len(self.yaxis_1) == 0:
            self.yaxis_1 = f'Percent of Cases for  {stat_name}'

        if self.title is None or len(self.title) == 0:
            self.title = self.config_obj.series_vals_1[0][0] + ' ' + \
                         self.column_info[
                             self.column_info['COLUMN'] == self.config_obj.series_val_names[0]][
                             "DESCRIPTION"].tolist()[0] + ' ' \
                         + self.col['desc'] + 'Rank Frequency'

    def _create_figure(self, stat_name):

        self.rank_logger.info(f"Creating the rank plot figure...")
        """ Create a box plot from default and custom parameters"""
        start_time = datetime.datetime.now()
        self.figure = self._create_layout()
        self._add_xaxis()
        self._add_yaxis()
        self._add_legend()

        if self.config_obj.xaxis_reverse is True:
            self.series_list.reverse()
        # calculate stag adjustments
        stag_adjustments = self._calc_stag_adjustments()

        x_points_index = list(range(0, len(self.config_obj.indy_vals)))
        # add x ticks for line plots
        self.figure.update_layout(
            xaxis={
                'tickmode': 'array',
                'tickvals': x_points_index,
                'ticktext': self.config_obj.indy_label
            }
        )

        rank_str = ["Best", "2nd", "3rd", "Worst"]
        n_series = len(self.config_obj.get_series_y(1))
        rank_str_index = min(3, n_series - 1)
        legend_str = rank_str[0: rank_str_index]
        if n_series >= 5:
            for i in range(4, n_series - 1, -1):
                legend_str.append(str(i) + "th")
        legend_str.append(rank_str[3])
        self.config_obj.user_legends = legend_str
        yaxis_min = None
        yaxis_max = None
        for idx, series in enumerate(self.series_list):
            # Don't generate the plot for this series if
            # it isn't requested (as set in the config file)
            if series.plot_disp:
                x_points_index_adj = x_points_index + stag_adjustments[series.idx]
                series.create_rank_points(self.case_data)
                yaxis_min, yaxis_max = self.find_min_max(series, yaxis_min, yaxis_max)
                self.rank_logger.info(f"Drawing series for {stat_name} and {series.series_vals_1[idx-1][idx]}")
                self._draw_series(series, x_points_index_adj)

        # Draw a reference line at 100/n_series
        self.figure.add_hline(y=100 / len(self.series_list), line_width=1, line_dash="solid", line_color="#e5e7e9")

        self.rank_logger.info(f'Range of {stat_name}: {yaxis_min}, {yaxis_max}')
        # Draw an invisible line to create a CI legend
        self.figure.add_trace(
            go.Scatter(x=[0],
                       y=[0],
                       showlegend=True,
                       mode='lines',
                       visible='legendonly',
                       line={'color': '#7b7d7d',
                             'width': 1,
                             'dash': 'dot'},
                       name=str(int(100 * (1 - self.config_obj.alpha))) + '% CI'
                       )
        )

        # add custom lines
        if len(self.series_list) > 0:
            self._add_lines(
                self.config_obj,
                sorted(self.series_list[0].series_data[self.config_obj.indy_var].unique())
            )
        # apply y axis limits
        self._yaxis_limits()
        # add x2 axis
        self._add_x2axis(list(range(0, len(self.config_obj.indy_vals))))

        end_time = datetime.datetime.now()
        total_time = end_time - start_time
        self.rank_logger.info(f"Creating rank plot figure took {total_time} milliseconds")

    def _draw_series(self, series: TcmprSeries, x_points_index_adj: list) -> None:
        """
        Draws the line on the plot

        :param series: Line series object with data and parameters
        """

        start_time = datetime.datetime.now()
        color = self.config_obj.colors_list[series.idx]
        width = self.config_obj.linewidth_list[series.idx]
        dash = self.config_obj.linestyles_list[series.idx]
        series_ci = self.config_obj.series_ci[series.idx]

        y_points = series.series_points['val']
        # show or not ci
        # see if any ci values in not 0
        no_ci_up = all(v is None or v == 0 for v in series.series_points['ncu'])
        no_ci_lo = all(v is None or v == 0 for v in series.series_points['ncl'])
        error_y_visible = True
        if (no_ci_up is True and no_ci_lo is True) or series_ci is False:
            error_y_visible = False

        rank_min_text = [str(series.idx + 1)] * len(x_points_index_adj)

        # create a trace
        self.figure.add_trace(
            go.Scatter(x=x_points_index_adj,
                       y=y_points,
                       showlegend=True,
                       mode='lines+text',
                       textposition="middle center",
                       name=self.config_obj.user_legends[series.idx],
                       line={'color': color,
                             'width': width,
                             'dash': dash},
                       text=rank_min_text,
                       textfont={
                           'size': 18,
                           'color': color
                       }
                       )
        )

        if error_y_visible is True:
            # add ci lo
            self.figure.add_trace(
                go.Scatter(x=x_points_index_adj,
                           y=series.series_points['ncl'],
                           showlegend=False,
                           mode='lines',
                           name=self.config_obj.user_legends[series.idx],
                           line={'color': color,
                                 'width': width,
                                 'dash': 'dot'}
                           )
            )

            # add ci up
            self.figure.add_trace(
                go.Scatter(x=x_points_index_adj,
                           y=series.series_points['ncu'],
                           showlegend=False,
                           mode='lines',
                           name=self.config_obj.user_legends[series.idx],
                           line={'color': color,
                                 'width': width,
                                 'dash': 'dot'}
                           )
            )

        # For the BEST and WORST series, plot the RANK_MIN values
        if len(series.rank_min_val) > 0:
            self.figure.add_trace(
                go.Scatter(
                    x=x_points_index_adj,
                    y=series.rank_min_val,
                    showlegend=False,
                    mode="text",
                    name="RANK MIN",
                    text=rank_min_text,
                    textfont={
                        'size': 18
                    },
                    textposition="middle center"
                ),
                secondary_y=series.y_axis != 1
            )
        end_time = datetime.datetime.now()
        total_time = end_time - start_time
        self.rank_logger.debug(f"Drawing series points took {total_time} millisecs")