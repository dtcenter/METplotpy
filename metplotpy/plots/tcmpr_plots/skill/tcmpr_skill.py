from typing import Union
import plotly.graph_objects as go
from datetime import datetime

from metplotpy.plots.tcmpr_plots.tcmpr import Tcmpr
from metplotpy.plots.tcmpr_plots.tcmpr_series import TcmprSeries
from metcalcpy.util import utils
import metplotpy.plots.util as util


class TcmprSkill(Tcmpr):
    def __init__(self, config_obj, column_info, col, case_data, input_df,  baseline_data, stat_name):
        super().__init__(config_obj, column_info, col, case_data, input_df, stat_name)

        # Set up Logging
        self.skill_logger = util.get_common_logger(config_obj.log_level, config_obj.log_filename)

    def _create_figure(self, stat_name):
        """ Create a skill line plot from default and custom parameters

            Args:
                stat_name: the name of the current 'statistic' (eg TK_ERR, AMSLP-BMSLP, etc.)
                           corresponding to list_stat_1 in the config file


        """

        start_time = datetime.now()
        self.figure = self._create_layout()
        self._add_xaxis()
        self._add_yaxis()
        self._add_legend()

        # placeholder for the min and max values for y-axis
        yaxis_min = None
        yaxis_max = None

        if self.config_obj.xaxis_reverse is True:
            self.series_list.reverse()
        # calculate stag adjustments
        stag_adjustments = self._calc_stag_adjustments()

        x_points_index = list(range(0, len(self.config_obj.indy_vals)))
        # add x ticks for line plots
        odered_indy_label = self.config_obj.create_list_by_plot_val_ordering(self.config_obj.indy_label)
        self.figure.update_layout(
            xaxis={
                'tickmode': 'array',
                'tickvals': x_points_index,
                'ticktext': odered_indy_label
            }
        )

        for series in self.series_list:
            # Don't generate the plot for this series if
            # it isn't requested (as set in the config file)
            if series.plot_disp:
                # collect min-max if we need to sync axis
                yaxis_min, yaxis_max = self.find_min_max(series, yaxis_min, yaxis_max)

                x_points_index_adj = x_points_index + stag_adjustments[series.idx]
                self._draw_series(series, x_points_index_adj)

        self.skill_logger.info(f'Range of {stat_name}: {yaxis_min}, {yaxis_max}')

        if self.config_obj.hfip_bsln != 'no':
           # This will be a valid value for hfip_bsln. This has been
           # validated/vetted in the configuration code (tcmpr_config.py).
           super()._add_hfip_baseline()

        self.figure.update_layout(shapes=[dict(
            type='line',
            yref='y', y0=0, y1=0,
            xref='paper', x0=0, x1=0.95,
            line={'color': '#727273',
                  'dash': 'dot',
                  'width': 1},
        )])

        # add custom lines
        num_series = len(self.series_list)
        if num_series > 0:
            for idx in range(num_series):
                self._add_lines(self.config_obj,
                    sorted(self.series_list[idx].series_data[self.config_obj.indy_var].unique())
                )
        # apply y axis limits
        self._yaxis_limits()

        # add x2 axis
        self._add_x2axis(list(range(0, len(self.config_obj.indy_vals))))

        end_time = datetime.now()
        total_time = end_time - start_time
        self.skill_logger.info(f"Took {total_time} milliseconds to create the figure for {stat_name}")

    def _draw_series(self, series: TcmprSeries, x_points_index_adj: list) -> None:
        """
        Draws the boxes on the plot

        :param series: Line series object with data and parameters
        """

        y_points = series.series_points['val']

        # create a trace
        self.figure.add_trace(
            go.Scatter(x=x_points_index_adj,
                       y=y_points,
                       showlegend=True,
                       mode='lines+markers',
                       textposition="top right",
                       name=self.config_obj.user_legends[series.idx],
                       line={'color': self.config_obj.colors_list[series.idx],
                             'width': self.config_obj.linewidth_list[series.idx],
                             'dash': self.config_obj.linestyles_list[series.idx]},
                       marker_symbol=self.config_obj.marker_list[series.idx],
                       marker_color=self.config_obj.colors_list[series.idx],
                       marker_line_color=self.config_obj.colors_list[series.idx],
                       marker_size=self.config_obj.marker_size[series.idx],

                       ),
            secondary_y=series.y_axis != 1
        )

    def _find_min_max(self, series: TcmprSeries, yaxis_min: Union[float, None],
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

        # Skip lead times for which no data is found
        if len(series.series_data) == 0:
            return yaxis_min, yaxis_max


        if self.cur_baseline_data is not None and len(self.cur_baseline_data) > 0:
            OCD5 = self.cur_baseline_data.loc[(self.cur_baseline_data['LEAD'].isin( self.config_obj.indy_vals)) & (self.cur_baseline_data['TYPE'] == 'OCD5')]['VALUE'].tolist()
            CONS = self.cur_baseline_data.loc[(self.cur_baseline_data['LEAD'].isin( self.config_obj.indy_vals)) & (self.cur_baseline_data['TYPE'] == 'CONS')]['VALUE'].tolist()
            baseline_lead = [  utils.round_half_up(100 * (ocd5-cons)/ocd5,1) for (ocd5,cons) in zip(OCD5,CONS )]
        else:
            baseline_lead = []


        # Get the values to be plotted for this lead times
        all_values = series.series_points['val'] +  baseline_lead
        low_range = min([v for v in all_values if v is not None])
        upper_range = max([v for v in all_values if v is not None])

        # find min max
        if yaxis_min is None or yaxis_max is None:
            return low_range, upper_range

        return min(yaxis_min, low_range), max(yaxis_max, upper_range)


