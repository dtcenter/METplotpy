from datetime import datetime

from metplotpy.plots.tcmpr_plots.tcmpr import Tcmpr
from metplotpy.plots.tcmpr_plots.tcmpr_series import TcmprSeries
from metplotpy.plots import util as util

class TcmprLine(Tcmpr):
    def __init__(self, config_obj, column_info, col, case_data, input_df, baseline_data, stat_name):
        super().__init__(config_obj, column_info, col, case_data, input_df, stat_name)

        # Set up Logging
        self.line_logger = util.get_common_logger(self.config_obj.log_level, self.config_obj.log_filename)

    def _create_figure(self, stat_name):
        """ Create a box plot from default and custom parameters"""
        start_time = datetime.now()
        handles_and_labels = []

        super()._create_figure()

        # placeholder for the min and max values for y-axis
        yaxis_min = None
        yaxis_max = None

        for series in self.series_list:
            # Don't generate the plot for this series if
            # it isn't requested (as set in the config file)
            if not series.plot_disp:
                continue

            # collect min-max if we need to sync axis
            yaxis_min, yaxis_max = self.find_min_max(series, yaxis_min, yaxis_max)
            x_points_index_adj, _ = self._get_x_locs_and_width(self.config_obj.indy_vals,
                                                               series.idx,
                                                               stagger_scale=0.1)
            handle = self._draw_series(series, x_points_index_adj)
            if handle is not None:
                handles_and_labels.append((handle, handle.get_label()))

        self.line_logger.info(f'Range of {stat_name}: {yaxis_min}, {yaxis_max}')

        self._add_hfip_baseline(self.ax)

        self.ax.axhline(0, color='#727273', linestyle=':', linewidth=1)

        # add custom lines
        if len(self.series_list) > 0:
            self._add_lines(
                self.ax,
                self.config_obj,
                sorted(self.series_list[0].series_data[self.config_obj.indy_var].unique())
            )

        self._add_xaxis()
        self._add_yaxis()
        self._add_legend(self.ax, handles_and_labels)

        # add x2 axis
        self._add_x2axis()

        end_time = datetime.now()
        total_time = end_time - start_time
        self.line_logger.info(f"Took {total_time} milliseconds to create figure for {stat_name}")

    def _draw_series(self, series: TcmprSeries, x_points_index_adj: list):
        """
        Draws the boxes on the plot

        :param series: Line series object with data and parameters
        """

        start_time = datetime.now()

        y_points = series.series_points['val']
        # show or not ci
        # see if any ci values in not 0
        no_ci_up = all(v == 0 for v in series.series_points['ncu'])
        no_ci_lo = all(v == 0 for v in series.series_points['ncl'])
        error_y_visible = True
        if ((no_ci_up and no_ci_lo)
                or self.config_obj.series_ci[series.idx] == 'NONE'
                or not self.config_obj.series_ci[series.idx]):
            error_y_visible = False

        ax = self.ax if series.y_axis == 1 else self.ax2

        yerr = None
        if error_y_visible:
            yerr = [series.series_points['ncl'], series.series_points['ncu']]

        plot = ax.errorbar(x_points_index_adj, y_points, yerr=yerr,
                           label=self.config_obj.user_legends[series.idx],
                           color=self.config_obj.colors_list[series.idx],
                           linewidth=self.config_obj.linewidth_list[series.idx],
                           linestyle=self.config_obj.linestyles_list[series.idx],
                           marker=self.config_obj.marker_list[series.idx],
                           markersize=self.config_obj.marker_size[series.idx])

        end_time = datetime.now()
        total_time = end_time - start_time
        self.line_logger.info(
            f"Took {total_time} milliseconds to draw the series for one of the series values in: {series.series_vals_1}")
        return plot[0]
