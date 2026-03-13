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
__author__ = 'Tatiana Burek, George McCabe'

import os
from datetime import datetime
import re
import csv
from operator import add
from typing import Union
from itertools import chain

import numpy as np
import pandas as pd

from matplotlib import pyplot as plt

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

        # instantiate a LineConfig object, which holds all the necessary settings
        # from the
        # config file that represents the BasePlot object (Line).
        self.config_obj = LineConfig(self.parameters)

        self.logger = self.config_obj.logger

        self.logger.info(f"Begin creating the line plot: {datetime.now()}")

        # Check that we have all the necessary settings for each series
        self.config_obj.config_consistency_check()

        # Read in input data, location specified in config file
        self.input_df = self._read_input_data()

        # Apply event equalization, if requested
        if self.config_obj.use_ee is True:
            self.logger.info(f"Begin event equalization: {datetime.now()}")
            self.input_df = calc_util.perform_event_equalization(self.parameters,
                                                                 self.input_df)
            self.logger.info(f"Finished event equalization: {datetime.now()}")

        # Create a list of series objects.
        # Each series object contains all the necessary information for plotting,
        # such as line color, marker symbol,
        # line width, and criteria needed to subset the input dataframe.
        self.series_list = self._create_series(self.input_df)

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
        self.config_obj.logger.info(f"Reading input data: {datetime.now()}")
        return pd.read_csv(self.config_obj.parameters['stat_input'], sep='\t',
                           header='infer', float_precision='round_trip',
                           low_memory=False)

    def _create_series(self, input_data):
        """
           Generate all the series objects that are to be displayed as specified by the
           plot_disp setting in the config file.  The points are all ordered by
           datetime.  Each series objectis represented by a line in the diagram,
           so they also contain information for line width, line- and marker-colors,
           line style, and other plot-related/appearance-related settings
           (which were defined in the config file).

           Args:
               input_data:  The input data in the form of a Pandas dataframe.
                            This data will be subset to reflect the series data of
                            interest.

           Returns:
               a list of series objects that are to be displayed


        """
        self.logger.info(f"Begin creating the series objects: {datetime.now()}")
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
                series_obj = LineSeries(self.config_obj,
                                        num_series_y1 + num_series_y2 + i,
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
                                        num_series_y1 + num_series_y2 +
                                        num_series_y1_d + i,
                                        input_data, series_list, name, 2)
                series_list.append(series_obj)

        # reorder series
        series_list = self.config_obj.create_list_by_series_ordering(series_list)

        # Plotly only plots legends based on the underlying order of the data. Re-order the
        # series_y data to reflect what was specified in the series_order setting in the config file.
        series_ordering = self.config_obj.series_ordering_zb
        reordered_series_list = []

        # Store the series data in a dictionary, using the index/position of series entry as the key
        series_y_dict = {}
        for i, cur_series in enumerate(series_list):
            series_y_dict[i] = cur_series

        # Order the series based on the ordering specified in the config file
        for order in series_ordering:
            reordered_series_list.append(series_y_dict[order])

        self.logger.info(f"Finished creating the series objects: {datetime.now()}")
        return reordered_series_list

    def _create_figure(self) -> None:
        """
        Create a line plot from defaults and custom parameters
        """
        self.logger.info(f"Begin create the figure: {datetime.now()}")

        # create and draw the plot
        _, ax = plt.subplots(figsize=(self.config_obj.plot_width, self.config_obj.plot_height))

        wts_size_styles = self.get_weights_size_styles()

        self._add_title(ax, wts_size_styles['title'])
        self._add_caption(plt, wts_size_styles['caption'])

        ax_y2 = None
        if self.config_obj.parameters['list_stat_2']:
            ax_y2 = self._add_y2axis(ax, wts_size_styles['y2lab'])

        n_stats, yaxis_min, yaxis_max, handles_and_labels = self._add_series(ax, ax_y2)

        xlab_style = wts_size_styles['xlab'] if not self.config_obj.vert_plot else wts_size_styles['ylab']
        ylab_style = wts_size_styles['ylab'] if not self.config_obj.vert_plot else wts_size_styles['xlab']
        self._add_xaxis(ax, xlab_style)
        self._add_yaxis(ax, ylab_style)

        # add x2 axis
        if wts_size_styles.get('x2lab'):
            self._add_x2axis(ax, n_stats, wts_size_styles['x2lab'])

        self._add_legend(ax, handles_and_labels)

        # add custom lines
        self._add_lines(ax, self.config_obj, self.config_obj.indy_vals)

        plt.tight_layout()

        #self._add_lines(self.config_obj, x_points_index)

        # sync axis
        self._sync_yaxes(ax, ax_y2, yaxis_min, yaxis_max)

        self.logger.info(f"Finished creating the figure: {datetime.now()}")

    def _add_series(self,ax, ax2):
        handles_and_labels = []

        # placeholder for the number of stats
        n_stats = [0] * len(self.config_obj.indy_vals)

        # placeholder for the min and max values for y-axis
        yaxis_min = None
        yaxis_max = None

        # add series lines
        for series in self.series_list:

            # Don't generate the plot for this series if it isn't requested
            if not series.plot_disp:
                continue

            # collect min-max if we need to sync axis
            if self.config_obj.sync_yaxes:
                yaxis_min, yaxis_max = self._find_min_max(series, yaxis_min,
                                                          yaxis_max)

            handle = self._draw_series(ax, ax2, series)
            handles_and_labels.append((handle, handle.get_label()))

            # aggregate number of stats
            n_stats = list(map(add, n_stats, series.series_points['nstat']))

        return n_stats, yaxis_min, yaxis_max, handles_and_labels

    def _draw_series(self, ax: plt.Axes, ax2, series: Series):
        """
        Draws the formatted line with CIs if needed on the plot

        :param series: Line series object with data and parameters
        """
        self.logger.info(f"Begin drawing the lines on the plot: {datetime.now()}")

        # adjust the x points to stagger them to prevent points from overlapping
        x_points_index_adj, _ = self._get_x_locs_and_width(self.config_obj.indy_vals, series.idx,
                                                           stagger_scale=0.1)

        # convert to a numpy array to change None values to NaN
        y_points = np.array(series.series_points['dbl_med'], dtype=float)

        # show or not ci - see if any ci values in not 0
        no_ci_up = all(v == 0 for v in series.series_points['dbl_up_ci'])
        no_ci_lo = all(v == 0 for v in series.series_points['dbl_lo_ci'])

        # convert to a numpy array to change None values to NaN
        asymmetric_error = np.array([
            series.series_points['dbl_up_ci'],
            series.series_points['dbl_lo_ci']
        ], dtype=float)

        error_y_visible = True
        if (no_ci_up and no_ci_lo) or self.config_obj.plot_ci[series.idx] == 'NONE':
            error_y_visible = False

        # determine which y-axis to use for the plot
        plot_ax = ax if series.y_axis == 1 else ax2

        # plot error bar
        plot_mode = self.config_obj.mode[series.idx]
        marker = self.config_obj.marker_list[series.idx] if 'markers' in plot_mode else None
        line_style = self.config_obj.linestyles_list[series.idx] if 'lines' in plot_mode else 'None'

        # Swap x and y data if vertical plot
        plot_x = y_points if self.config_obj.vert_plot else x_points_index_adj
        plot_y = x_points_index_adj if self.config_obj.vert_plot else y_points

        # Swap error bars (yerr becomes xerr) if vertical plot
        x_err_val = asymmetric_error if (self.config_obj.vert_plot and error_y_visible) else None
        y_err_val = asymmetric_error if (not self.config_obj.vert_plot and error_y_visible) else None

        plot_obj = plot_ax.errorbar(
            x=plot_x,
            y=plot_y,
            label=self.config_obj.user_legends[series.idx],
            # line style
            color=self.config_obj.colors_list[series.idx],
            linestyle=line_style,
            linewidth=self.config_obj.linewidth_list[series.idx],
            # marker style
            marker=marker,
            markersize=self.config_obj.marker_size[series.idx],
            markeredgecolor=self.config_obj.colors_list[series.idx],
            markerfacecolor=self.config_obj.colors_list[series.idx],
            # error bar
            xerr=x_err_val,
            yerr=y_err_val,
            elinewidth=self.config_obj.linewidth_list[series.idx],
        )

        self.logger.info(f"Finished drawing the lines on the plot: {datetime.now()}")
        return plot_obj

    def write_output_file(self) -> None:
        """
        Formats y1 and y2 series point data to the 2-dim arrays and saves them to the
        files
        """
        if not self.config_obj.dump_points_1 and not self.config_obj.dump_points_2:
            return

        self.logger.info(f"Begin writing to output file: {datetime.now()}")
        # if points_path parameter doesn't exist,
        # open file, name it based on the stat_input config setting,
        # (the input data file) except replace the .data
        # extension with .points1 extension
        # otherwise use points_path path
        match = re.match(r'(.*)(.data)', self.config_obj.parameters['stat_input'])
        if not match:
            return

        # create 2-dim array for y1 points and fill it with 0
        all_points_1 = [[0 for _ in range(len(self.config_obj.all_series_y1) * 3)]
                        for _ in range(len(self.config_obj.indy_vals))]
        if self.config_obj.series_vals_2:
            # create 2-dim array for y1 points and feel it with 0
            all_points_2 = [
                [0 for _ in range(len(self.config_obj.all_series_y2) * 3)]
                for _ in range(len(self.config_obj.indy_vals))
            ]
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
            os.makedirs(filename, exist_ok=True)

        # save points
        self._save_points(all_points_1, filename + ".points1")
        self._save_points(all_points_2, filename + ".points2")

        self.logger.info(f"Finished writing to output file: {datetime.now()}")

    @staticmethod
    def _find_min_max(series: LineSeries, yaxis_min: Union[float, None],
                      yaxis_max: Union[float, None]) -> tuple:
        """
        Finds min and max value between provided min and max and y-axis CI values of
        this series
        if yaxis_min or yaxis_max is None - min/max value of the series is returned

        :param series: series to use for calculations
        :param yaxis_min: previously calculated min value
        :param yaxis_max: previously calculated max value
        :return: a tuple with calculated min/max
        """
        # calculate series upper and lower limits of CIs
        indexes = range(len(series.series_points['dbl_med']))

        # Check for NA/None values when searching for upper range values and
        # ignore them.
        upper_range = []
        for i in indexes:
            if series.series_points['dbl_med'][i] is not None and series.series_points['dbl_up_ci'][i] is not None:
                upper_range.append(series.series_points['dbl_med'][i] + series.series_points['dbl_up_ci'][i])

        # Check for NA/None values when searching for lower range values and
        # ignore them.
        low_range = []
        for i in indexes:
            if series.series_points['dbl_med'][i] is not None and series.series_points['dbl_lo_ci'][i] is not None:
                low_range.append(series.series_points['dbl_med'][i] - series.series_points['dbl_lo_ci'][i])

        # find min max
        if yaxis_min is None or yaxis_max is None:
            return min(low_range), max(upper_range)

        return min(chain([yaxis_min], low_range)), max(chain([yaxis_max], upper_range))

    def _record_points(self, all_points: list, series_idx: int,
                       series: LineSeries) -> None:
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
            if y_points[indy_val_idx] is not None and dbl_lo_ci[indy_val_idx] is not None:
                all_points[indy_val_idx][series_idx * 3 + 1] = \
                    y_points[indy_val_idx] - dbl_lo_ci[indy_val_idx]
            else:
                all_points[indy_val_idx][series_idx * 3 + 1] = None

            # place CI-up value or None
            if y_points[indy_val_idx] is not None and dbl_up_ci[indy_val_idx] is not None:
                all_points[indy_val_idx][series_idx * 3 + 2] = \
                    y_points[indy_val_idx] + dbl_up_ci[indy_val_idx]
            else:
                all_points[indy_val_idx][series_idx * 3 + 2] = None

    @staticmethod
    def _save_points(points: list, output_file: str) -> None:
        """
        Saves array of points to the file. Ir replaces all None values to N/A and
        format floats
        :param points: 2-dimensional array. The 1st dimension is the number of x-axis
         points
            The 2nd - is the all y-points for a single  x-axis points. Each y-points
            has 3 numbers:
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
        except TypeError:
            print('Can\'t save points to a file')


def main(config_filename=None):
    """
            Generates a sample, default, line plot using the
            default and custom config files on sample data found in this directory.
            The location of the input data is defined in either the default or
            custom config file.
            Args:
                @param config_filename: default is None, the name of the custom
                                        config file to apply
        """
    util.make_plot(config_filename, Line)


if __name__ == "__main__":
    main()
