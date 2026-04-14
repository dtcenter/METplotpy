import os
from datetime import datetime
import numpy as np

from metcalcpy.util import utils
from metplotpy.plots.tcmpr_plots.tcmpr import Tcmpr
from metplotpy.plots.tcmpr_plots.tcmpr_series import TcmprSeries
from metplotpy.plots.tcmpr_plots.tcmpr_util import get_case_data
from metplotpy.plots import util as util


class TcmprRelPerf(Tcmpr):
    def __init__(self, config_obj, column_info, col, case_data, input_df, stat_name):
        super().__init__(config_obj, column_info, col, case_data, input_df, stat_name)

        # Set up Logging
        self.relperf_logger = util.get_common_logger(self.config_obj.log_level, self.config_obj.log_filename)
        self.relperf_logger.info("--------------------------------------------------------")

        if not self.config_obj.use_ee:
            self.relperf_logger.error(f"Plotting RELPERF time series by {self.config_obj.series_val_names[0]}")
            raise ValueError("ERROR: Cannot plot relative performance when event equalization is disabled.")

        self.relperf_logger.info(f"Plotting RELPERF time series by {stat_name}")

        self.relperf_logger.info("Plot HFIP Baseline:" + self.cur_baseline)
        self._adjust_titles()
        self.series_list = self._create_series(self.input_df, stat_name)
        if self.case_data is None:
            self.relperf_logger.info(f"Getting case data for {stat_name}")
            self.case_data = get_case_data(self.input_df, self.config_obj.series_vals_1, self.config_obj.indy_vals,
                                           self.config_obj.rp_diff, len(self.series_list))

        for series in self.series_list:
            series.create_relperf_points(self.case_data)

        if self.config_obj.prefix is None or len(self.config_obj.prefix) == 0:
            self.plot_filename = f"{self.config_obj.plot_dir}{os.path.sep}{stat_name}_relperf.png"
        else:
            self.plot_filename = f"{self.config_obj.plot_dir}{os.path.sep}{self.config_obj.prefix}_{stat_name}_relperf.png"
        # remove the old file if it exists
        if os.path.exists(self.plot_filename):
            os.remove(self.plot_filename)
        self.user_legends = self._create_user_legends(stat_name)
        self._create_figure(stat_name)

    def _create_user_legends(self, stat_name):
        all_user_legends = self.config_obj.get_config_value('user_legend')
        legend_list = []
        series = self.config_obj.get_series_y_relperf(1)

        for idx, ser_components in enumerate(series):
            if idx >= len(all_user_legends) or all_user_legends[idx].strip() == '':
                # user did not provide the legend - create it
                legend_list.append(' '.join(map(str, ser_components)))
            else:
                # user provided a legend - use it
                legend_list.append(all_user_legends[idx])

        # add to legend list  legends for y2-axis series
        # num_series_y1 = len(self.config_obj.get_series_y(1))
        num_series_y1 = len(stat_name)

        for idx, ser_components in enumerate(self.get_config_value('derived_series_1')):
            # index of the legend
            legend_idx = idx + num_series_y1
            if legend_idx >= len(all_user_legends) or all_user_legends[legend_idx].strip() == '':
                # user did not provide the legend - create it
                legend_list.append(utils.get_derived_curve_name(ser_components))
            else:
                # user provided a legend - use it
                legend_list.append(all_user_legends[legend_idx])

        return self.config_obj.create_list_by_series_ordering(legend_list)

    def _create_figure(self, stat_name):
        """ Create a box plot from default and custom parameters"""
        start_time = datetime.now()
        handles_and_labels = []
        super()._create_figure()

        yaxis_min = None
        yaxis_max = None

        for series in self.series_list:
            # Don't generate the plot for this series if
            # it isn't requested (as set in the config file)
            if series.plot_disp:
                # collect min-max if we need to sync axis
                yaxis_min, yaxis_max = self.find_min_max(series, yaxis_min, yaxis_max)
                x_points_index_adj, _ = self._get_x_locs_and_width(self.config_obj.indy_vals,
                                                                   series.idx,
                                                                   stagger_scale=0.1)
                handle = self._draw_series(series, x_points_index_adj)
                handles_and_labels.append((handle, handle.get_label()))

        series = TcmprSeries(self.config_obj, len(self.series_list), self.input_df, [], ['TIE'], stat_name)
        # Reset some series values.  Series should be grouped by the plot type and not by the series_val
        # series = self._setup_series(self.config_obj, len(self.series_list), self.input_df, [], ['TIE'], stat_name)
        series.create_relperf_points(self.case_data)
        yaxis_min, yaxis_max = self.find_min_max(series, yaxis_min, yaxis_max)
        self.relperf_logger.info(f'Range of {stat_name}: {yaxis_min}, {yaxis_max}')
        tie_conf = {
            'line_color': '#808080',
            'name': 'TIE',
            'line_width': 1,
            'line_dash': 'solid',
            'marker_symbol': '*',
            'marker_size': self.config_obj.marker_size[-1],
            'series_ci': True
        }
        x_points_index_adj, _ = self._get_x_locs_and_width(self.config_obj.indy_vals,
                                                           series.idx,
                                                           stagger_scale=0.1)
        handle = self._draw_series(series, x_points_index_adj, tie_conf)
        handles_and_labels.append((handle, handle.get_label()))
        self.ax.axhline(y=0, color='#e5e7e9', linestyle='-', linewidth=1)

        # add CI legend proxy
        self.ax.plot([], [], color='#7b7d7d', linestyle=':', linewidth=1, label=str(int(100 * (1 - self.config_obj.alpha))) + '% CI')

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
        self.relperf_logger.info(f"Took {total_time} milliseconds to create the relative performance figure")

    def _draw_series(self, series: TcmprSeries, x_points_index_adj: list, tie_conf=None):
        """
        Draws the boxes on the plot

        :param series: Line series object with data and parameters
        """

        start_time = datetime.now()

        if tie_conf is None:
            color = self.config_obj.colors_list[series.idx]
            width = self.config_obj.linewidth_list[series.idx]
            dash = self.config_obj.linestyles_list[series.idx]
            marker_symbol = self.config_obj.marker_list[series.idx]
            marker_size = self.config_obj.marker_size[series.idx]
            name = self.user_legends[series.idx]
        else:
            color = tie_conf['line_color']
            width = tie_conf['line_width']
            dash = tie_conf['line_dash']
            marker_symbol = tie_conf['marker_symbol']
            marker_size = tie_conf['marker_size']
            name = tie_conf['name']

        markerfacecolor = color
        markeredgecolor = color
        if tie_conf is None and self.config_obj.marker_open_list[series.idx]:
            markerfacecolor = 'none'
            markeredgecolor = self.config_obj.colors_list[series.idx]

        y_points = series.series_points['val']

        ax = self.ax if series.y_axis == 1 else self.ax2

        plot_obj = ax.plot(x_points_index_adj, y_points,
                           label=name,
                           # line style
                           color=color,
                           linewidth=width,
                           linestyle=dash,
                           # marker style
                           marker=marker_symbol,
                           markersize=marker_size,
                           markeredgecolor=markeredgecolor,
                           markerfacecolor=markerfacecolor,
                           )

        # Plot relative performance confidence intervals
        if series.idx >= series.series_len:
            idx = 0
        else:
            idx = series.idx
        if self.config_obj.series_ci[idx]:
             ax.plot(x_points_index_adj, series.series_points['ncl'], color=color, linewidth=width, linestyle=':')
             ax.plot(x_points_index_adj, series.series_points['ncu'], color=color, linewidth=width, linestyle=':')

        end_time = datetime.now()
        total_time = end_time - start_time
        self.relperf_logger.info(f"Took {total_time} milliseconds to draw the series")
        return plot_obj[0]

    def _adjust_titles(self, y_label=None, title_prefix=None, title_suffix=None, add_units=False):
        series_val_name = self.column_info[self.column_info["COLUMN"] == self.config_obj.series_val_names[0]]["DESCRIPTION"].tolist()[0]
        title_suffix = f"by {series_val_name}"
        if len(np.unique(self.config_obj.rp_diff)) == 1:
            title_suffix = f"Difference {self.config_obj.rp_diff[0]}{self.col['units']} {title_suffix}"

        super()._adjust_titles(y_label="Percent of Cases",
                               title_prefix="Relative Performance of",
                               title_suffix=title_suffix,
                               add_units=False)
