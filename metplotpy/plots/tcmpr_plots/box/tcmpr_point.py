import os
from datetime import datetime

from metplotpy.plots import util as util
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

        # Point plot
        ax = self.ax if series.y_axis == 1 else self.ax2

        # line plot, when connect_points is False in config file
        if 'point' not in self.config_obj.plot_type_list:
            return None

        y_list = series.series_points['mean']
        x_list = series.series_data['LEAD_HR']
        if len(x_list) != len(y_list):
            # Clean up None values in the series.series_points['mean'] list
            y_list = [y_values for y_values in y_list if y_values is not None]

        plot_obj = ax.plot(x_list, y_list, marker='o', label=series.user_legends,
                           linestyle='-' if self.config_obj.connect_points else 'None',
                           color=series.color,
                           )
        return plot_obj[0]
