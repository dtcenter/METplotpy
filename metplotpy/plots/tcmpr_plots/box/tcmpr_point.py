import os
from datetime import datetime

import plotly.graph_objects as go

from metplotpy.plots import util
from metplotpy.plots.tcmpr_plots.box.tcmpr_box_point import TcmprBoxPoint
from metplotpy.plots.tcmpr_plots.tcmpr_series import TcmprSeries


class TcmprPoint(TcmprBoxPoint):
    def __init__(self, config_obj, column_info, col, case_data, input_df, baseline_data, stat_name):
        super().__init__(config_obj, column_info, col, case_data, input_df, baseline_data, stat_name)
        # Set up Logging
        self.point_logger = util.get_common_logger(self.config_obj.log_level, self.config_obj.log_filename)

        self.point_logger.info("--------------------------------------------------------")
        self.point_logger.info(f"Plotting POINT time series by {self.config_obj.series_val_names[0]}")
        start = datetime.now()

        self._adjust_titles(stat_name)
        self.series_list = self._create_series(self.input_df, stat_name)
        self.case_data = None
        self.cur_baseline = baseline_data['cur_baseline']
        self.cur_baseline_data = baseline_data['cur_baseline_data']
        self._init_hfip_baseline_for_plot()

        if self.config_obj.prefix is None or len(self.config_obj.prefix) == 0:
            self.plot_filename = f"{self.config_obj.plot_dir}{os.path.sep}{stat_name}_pointplot.png"
        else:
            self.plot_filename = f"{self.config_obj.plot_dir}{os.path.sep}{self.config_obj.prefix}_{stat_name}_pointplot.png"
        # remove the old file if it exists

        if os.path.exists(self.plot_filename):
            os.remove(self.plot_filename)
        self._create_figure()

        self.point_logger.info(f"Finished generating the TCMPR points  in {datetime.now() - start} ms")

    def _adjust_titles(self, stat_name):
        if self.yaxis_1 is None or len(self.yaxis_1) == 0:
            self.yaxis_1 = stat_name + '(' + self.col['units'] + ')'

        if self.title is None or len(self.title) == 0:
            self.title = 'Point Plots  of ' + self.col['desc'] + ' by ' \
                         + self.column_info[self.column_info['COLUMN'] == self.config_obj.series_val_names[0]][
                             "DESCRIPTION"].tolist()[0]

    def _draw_series(self, series: TcmprSeries) -> None:
        """
        Draws the boxes on the plot

        :param series: Line series object with data and parameters
        """

        # defaults markers and colors for the regular box plot
        marker_color = series.color
        marker_line_color = series.color

        # Point plot

        line_color = dict(color='rgba(0,0,0,0)')
        fillcolor = 'rgba(0,0,0,0)'
        marker_symbol = 'circle'
        boxpoints = 'all'

        # create a trace

        # line plot, when connect_points is False in config file
        if 'point' in self.config_obj.plot_type_list:
            if self.config_obj.connect_points:
                # line plot
                mode = 'lines+markers'
            else:
                # points only
                mode = 'markers'
            # Create a point plot

            # Ensure that the size of the list of x and y values
            # are the same, or the resulting plot will be incorrect.
            # This mismatch occurs when the x_list represents the
            # available lead hours in the series data and the
            # series_points has None where there isn't data corresponding
            # to lead hours in the series_points dataframe.
            #
            y_list = series.series_points['mean']
            x_list = series.series_data['LEAD_HR']
            if len(x_list) != len(y_list):
                # Clean up None values in the series.series_points['mean'] list
                # The None values are assigned by the _create_series_points() method.
                y_list = [y_values for y_values in y_list if y_values is not None]

            self.figure.add_trace(
                go.Scatter(x=x_list,
                           y=y_list,
                           showlegend=True,
                           mode=mode,
                           name=self.config_obj.user_legends[series.idx],
                           marker=dict(
                               color=marker_line_color,
                               size=8,
                               opacity=0.7,
                               line=dict(
                                   color=self.config_obj.colors_list[series.idx],
                                   width=1
                               )
                           ),
                           ),
                secondary_y=series.y_axis != 1
            )

            # When a line plot is requested, connect any gaps
            if self.config_obj.connect_points:
                self.figure.update_traces(connectgaps=True)

        else:
            # Boxplot
            self.figure.add_trace(
                go.Box(x=series.series_data['LEAD_HR'],
                       y=series.series_data['PLOT'],
                       mean=series.series_points['mean'],
                       notched=self.config_obj.box_notch,
                       line=line_color,
                       fillcolor=fillcolor,
                       name=series.user_legends,
                       showlegend=True,
                       boxmean=self.config_obj.box_avg,
                       boxpoints=boxpoints,  # outliers, all, False
                       pointpos=0,
                       marker=dict(size=4,
                                   color=marker_color,
                                   line=dict(
                                       width=1,
                                       color=marker_line_color
                                   ),
                                   symbol=marker_symbol,
                                   ),
                       jitter=0
                       ),
                secondary_y=series.y_axis != 1
            )

