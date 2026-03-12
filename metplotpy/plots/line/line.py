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
__author__ = 'Tatiana Burek, Minna Win'

import os, sys
from datetime import datetime
import re
import csv
from operator import add
from typing import Union
from itertools import chain

import yaml
import numpy as np
import pandas as pd

import matplotlib.pyplot as plt

import metplotpy.plots.constants as const
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

        # instantiate a LineConfig object, which holds all the necessary settings
        # from the
        # config file that represents the BasePlot object (Line).
        self.config_obj = LineConfig(self.parameters)

        self.logger = self.config_obj.logger

        self.logger.info(f"Begin creating the line plot: {datetime.now()}")

        # Check that we have all the necessary settings for each series
        is_config_consistent = self.config_obj._config_consistency_check()
        if not is_config_consistent:
            error_msg = ("The number of series defined by series_val_1/2 and derived "
                         "curves is inconsistent with the number of settings "
                         "required for describing each series. Please check "
                         "the number of your configuration file's plot_ci, "
                         "plot_disp, series_order, user_legend, "
                         "colors, series_symbols, and show_legend settings.")
            self.logger.error(f"ValueError: {error_msg}: {datetime.now()}")
            raise ValueError(error_msg)

        # Read in input data, location specified in config file
        self.input_df = self._read_input_data()

        # Apply event equalization, if requested
        if self.config_obj.use_ee is True:
            self.logger.info(f"Begin event equalization: {datetime.now()}")
            self.input_df = calc_util.perform_event_equalization(
                self.parameters,
                self.input_df,
                )
            self.logger.info(f"Finished event equalization: {datetime.now()}")

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
        try:
            self.figure = self._create_figure()
        except AttributeError as ae:
            self.logger.error(f"AttributeError:{ae}")
        except ValueError as ve:
            self.logger.error(f"ValueError: {ve}")

        self.logger.info(f"Finished creating line plot: {datetime.now()}")

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
        return pd.read_csv(
            self.config_obj.parameters['stat_input'], sep='\t',
            header='infer', float_precision='round_trip',
            low_memory=False,
            )

    def _create_series(self, input_data):
        """
           Generate all the series objects that are to be displayed as specified by the
           plot_disp setting in the config file.  The points are all ordered by
           datetime.  Each series object is represented by a line in the diagram,
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
            series_obj = LineSeries(
                self.config_obj, num_series_y1 + i,
                input_data, series_list, name, 2,
                )
            series_list.append(series_obj)

        # add derived for y1 axis
        num_series_y1_d = len(self.config_obj.get_config_value('derived_series_1'))
        for i, name in enumerate(self.config_obj.get_config_value('derived_series_1')):
            # add default operation value if it is not provided
            if len(name) == 2:
                name.append("DIFF")
            # include the series only if the name is valid
            if len(name) == 3:
                series_obj = LineSeries(
                    self.config_obj,
                    num_series_y1 + num_series_y2 + i,
                    input_data, series_list, name,
                    )
                series_list.append(series_obj)

        # add derived for y2 axis
        for i, name in enumerate(self.config_obj.get_config_value('derived_series_2')):
            # add default operation value if it is not provided
            if len(name) == 2:
                name.append("DIFF")
            # include the series only if the name is valid
            if len(name) == 3:
                series_obj = LineSeries(
                    self.config_obj,
                    num_series_y1 + num_series_y2 +
                    num_series_y1_d + i,
                    input_data, series_list, name, 2,
                    )
                series_list.append(series_obj)

        # reorder series
        series_list = self.config_obj.create_list_by_series_ordering(series_list)

        #  Re-order the series_y data to reflect what was specified in the
        #  series_order setting in the config file.
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

        # calculate stag adjustments
        stag_adjustments = self._calc_stag_adjustments()

        x_points_index = list(range(0, len(self.config_obj.indy_vals)))

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

        fig, ax = plt.subplots()

        # legend settings
        legend_text_size = self.config_obj.parameters['legend_size']
        num_legend_cols = self.config_obj.parameters['legend_ncol']
        legend_x_pos = self.config_obj.parameters['legend_inset']['x']
        legend_y_pos = self.config_obj.parameters['legend_inset']['y']

        # add series lines
        all_legends = []
        all_y2_vals = []

        # ToDo get the min and max values for the y2 axis
        for  series in self.series_list:
            if series.y_axis == 2:

                # get the min and max y values to define the y2 axis

                all_y2_vals = list(series.series_data['stat_value']) + all_y2_vals

        all_y2 = pd.Series(all_y2_vals)
        y2axis_min = all_y2.min()
        y2axis_max = all_y2.max()

        print(f"y2 min: {y2axis_min}, y2max: {y2axis_max}")
        for idx, series in enumerate(self.series_list):

            # Don't generate the plot for this series if
            # it isn't requested (as set in the config file)

            if series.plot_disp:

                # collect min-max if we need to sync axis
                if self.config_obj.sync_yaxes is True:
                    yaxis_min, yaxis_max = self._find_min_max(
                        series, yaxis_min,
                        yaxis_max,
                        )
                # apply staggering offset if applicable

                if stag_adjustments[series.idx] == 0:
                    x_points_index_adj = x_points_index
                else:
                    x_points_index_adj = x_points_index + stag_adjustments[series.idx]

                y_points = series.series_points['dbl_med']



                # print(f" user legends: {series.user_legends}, index: {idx}, color: {self.config_obj.colors_list[
                # idx]}")

                # error bars (confidence limits)
                # see if any ci values in not 0
                no_ci_up = all(v == 0 for v in series.series_points['dbl_up_ci'])
                no_ci_lo = all(v == 0 for v in series.series_points['dbl_lo_ci'])
                upper_error = series.series_points['dbl_up_ci']
                lower_error = series.series_points['dbl_lo_ci']
                asymmetric_error = [lower_error, upper_error]

                error_y_visible = True
                if ((no_ci_up is True and no_ci_lo is True) or self.config_obj.plot_ci[
                    series.idx] == 'NONE'):
                    error_y_visible = False


                # Plot yaxis_1 and yaxis_2 onto their own axes
                if error_y_visible:
                    if series.y_axis == 1:
                        # line plot with error bars
                        all_legends.append(series.user_legends)
                        ax.errorbar(
                            x_points_index_adj, y_points, yerr=asymmetric_error,
                            fmt='.-', ecolor=self.config_obj.colors_list[idx], mfc=self.config_obj.colors_list[idx],
                            mec=self.config_obj.colors_list[idx],
                            )

                    elif series.y_axis == 2:
                        print("y2 axis plotting with err bars ")
                        all_legends.append(series.user_legends)
                        ax2 = ax.twinx()
                        ax2.errorbar(
                            x_points_index_adj, y_points, yerr=asymmetric_error,
                            fmt='.-', ecolor=self.config_obj.colors_list[idx], mfc=self.config_obj.colors_list[idx],
                            mec=self.config_obj.colors_list[idx],
                            )

                else:
                    # Plot the line without error bars
                    if series.y_axis == 1:
                        all_legends.append(series.user_legends)

                        ax.plot(
                            x_points_index_adj, y_points, color=self.config_obj.colors_list[idx], )

                    if series.y_axis == 2:
                        all_legends.append(series.user_legends)
                        ax2 = ax.twinx()
                        ax2.plot(
                            x_points_index_adj, y_points, color=self.config_obj.colors_list[idx],
                            )
                        ax2.set_ylim(y2axis_min, y2axis_max)
                        # ax2.set_ylim(-1.1, -1.6)
                    # print(f"legend after series_y1 and series_y2 check: {series.user_legends}")

        # Add title, x-, and y-axis labels, captions, x- and y-tick labels
        # fig.legend(all_legends)
        fig.legend(
            all_legends, fancybox=self.config_obj.draw_box, frameon=self.config_obj.draw_box,
            bbox_to_anchor=(1, 0.1), ncol=5, fontsize=6,

            )
        # fig.legend(
        #     all_legends, bbox_to_anchor=(legend_x_pos, legend_y_pos),
        #     fancybox=self.config_obj.draw_box, frameon=self.config_obj.draw_box,
        #     ncol=num_legend_cols,
        #     fontsize=legend_text_size
        #     )
        plt.title("sample title")

        output_dir = self.config_obj.output_image
        # os.makedirs(output_dir, exist_ok=True)
        plt.tight_layout()
        plt.savefig(output_dir)

        # aggregate number of stats
        # n_stats = list(map(add, n_stats, series.series_points['nstat']))

        # create a vertical plot if needed
        # self._adjust_for_vertical(x_points_index)

        # reverse xaxis if needed
        # if self.config_obj.xaxis_reverse is True:
        #     if self.config_obj.vert_plot is True:
        #         self.figure.update_yaxes(autorange="reversed")
        #     else:
        #         self.figure.update_xaxes(autorange="reversed")
        # add custom lines
        # self._add_lines(self.config_obj, x_points_index)

        # apply y axis limits
        # self._yaxis_limits()
        # self._y2axis_limits()

        # sync axis
        # self._sync_yaxis(yaxis_min, yaxis_max)

        # add x2 axis
        # self._add_x2axis(n_stats)

        # Allow plots to start from the y=0 line if set in the config file
        # if self.config_obj.start_from_zero is True:
        #     self.figure.update_xaxes(range=[0, len(x_points_index) - 1])

        self.logger.info(f"Finished creating the figure: {datetime.now()}")

    def _draw_series(
            self, series: Series, x_points_index_adj: Union[list, None] =
            None,
            ) \
            -> None:
        """
        Draws the formatted line with CIs if needed on the plot

        :param series: Line series object with data and parameters
        :param x_points_index_adj: values for adjusting x-values position
        """
        self.logger.info(f"Begin drawing the lines on the plot: {datetime.now()}")
        y_points = series.series_points['dbl_med']

        # show or not ci
        # see if any ci values in not 0
        no_ci_up = all(v == 0 for v in series.series_points['dbl_up_ci'])
        no_ci_lo = all(v == 0 for v in series.series_points['dbl_lo_ci'])
        error_y_visible = True
        if ((no_ci_up is True and no_ci_lo is True) or self.config_obj.plot_ci[
            series.idx] == 'NONE'):
            error_y_visible = False

        # switch x and y values for the vertical plot
        error_x = {}
        error_y = {}
        # if self.config_obj.vert_plot is True:
        #     y_points, x_points_index_adj = x_points_index_adj, y_points
        #     self._xaxis_limits()
        #     self.figure.update_xaxes(autorange=False)
        #
        #     # Error bars for vertical plot
        #     error_x = {'type': 'data',
        #                             'symmetric': False,
        #                             'array': series.series_points['dbl_up_ci'],
        #                             'arrayminus': series.series_points['dbl_lo_ci'],
        #                             'visible': error_y_visible,
        #                             'thickness': self.config_obj.linewidth_list[
        #                                 series.idx]}
        # else:
        #     # Error bars
        #     error_y = {
        #         'type': 'data',
        #         'symmetric': False,
        #         'array': series.series_points['dbl_up_ci'],
        #         'arrayminus': series.series_points['dbl_lo_ci'],
        #         'visible': error_y_visible,
        #         'thickness': self.config_obj.linewidth_list[series.idx]
        #         }

        # add the plot
        # orient the confidence interval bars based on the vert_plot setting in
        # the yaml configuration file.

        # self.figure.add_trace(
        #        go.Scatter(x=x_points_index_adj,
        #                    y=y_points,
        #                    showlegend=self.config_obj.show_legend[series.idx] == 1,
        #                    mode=self.config_obj.mode[series.idx],
        #                    textposition="top right",
        #                    name=self.config_obj.user_legends[series.idx],
        #                    connectgaps=self.config_obj.con_series[series.idx] == 1,
        #                    line={'color': self.config_obj.colors_list[series.idx],
        #                          'width': self.config_obj.linewidth_list[series.idx],
        #                          'dash': self.config_obj.linestyles_list[series.idx]},
        #                    marker_symbol=self.config_obj.marker_list[series.idx],
        #                    marker_color=self.config_obj.colors_list[series.idx],
        #                    marker_line_color=self.config_obj.colors_list[series.idx],
        #                    marker_size=self.config_obj.marker_size[series.idx],
        #                    error_x=error_x,
        #                    error_y=error_y
        #                    ),
        #       secondary_y=series.y_axis != 1
        #     )
        #

        self.logger.info(
            f"Finished drawing the lines on the plot:"
            f" {datetime.now()}",
            )

    def _calc_stag_adjustments(self) -> list:
        """
        Calculates the x-axis adjustment for each point if requested.
        It needed so hte points and CIs for each x-axis values don't be placed on top
        of each other

        :return: the list of the adjustment values
        """

        # get the total number of series
        num_stag = len(self.config_obj.all_series_y1) + len(
            self.config_obj.all_series_y2,
            )

        # init the result with 0
        stag_vals = [0] * num_stag

        # calculate staggering values
        if self.config_obj.indy_stagger is True:
            dbl_adj_scale = (len(self.config_obj.indy_vals) - 1) / 150
            stag_vals = np.linspace(
                -(num_stag / 2) * dbl_adj_scale,
                (num_stag / 2) * dbl_adj_scale,
                num_stag,
                True,
                )
            stag_vals = stag_vals + dbl_adj_scale / 2
        return stag_vals

    def remove_file(self):
        """
           Removes previously made image file .  Invoked by the parent class before
           self.output_file
           attribute can be created, but overridden here.
        """

        super().remove_file()

    def write_output_file(self) -> None:
        """
        Formats y1 and y2 series point data to the 2-dim arrays and saves them to the
        files
        """

        self.logger.info(f"Begin writing to output file: {datetime.now()}")
        # if points_path parameter doesn't exist,
        # open file, name it based on the stat_input config setting,
        # (the input data file) except replace the .data
        # extension with .points1 extension
        # otherwise use points_path path
        match = re.match(r'(.*)(.data)', self.config_obj.parameters['stat_input'])
        if (self.config_obj.dump_points_1 is True or self.config_obj.dump_points_2 is
                True and match):

            # create 2-dim array for y1 points and fill it with 0
            all_points_1 = [[0 for x in range(len(self.config_obj.all_series_y1) * 3)]
                            for y in
                            range(len(self.config_obj.indy_vals))]
            if self.config_obj.series_vals_2:
                # create 2-dim array for y1 points and feel it with 0
                all_points_2 = [
                    [0 for x in range(len(self.config_obj.all_series_y2) * 3)] for y in
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
                os.makedirs(filename, exist_ok=True)

            # save points
            self._save_points(all_points_1, filename + ".points1")
            self._save_points(all_points_2, filename + ".points2")

            self.logger.info(f"Finished writing to output file: {datetime.now()}")

    @staticmethod
    def _find_min_max(
            series: LineSeries, yaxis_min: Union[float, None],
            yaxis_max: Union[float, None],
            ) -> tuple:
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

    def _record_points(
            self, all_points: list, series_idx: int,
            series: LineSeries,
            ) -> None:
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
                @param config_filename: default is None, the name of the custom
                                        config file to apply
        """
    # util.make_plot(config_filename, Line)
    params = util.get_params(config_filename)
    try:
        Line(params)

    except ValueError as value_error:
        logger = util.get_common_logger(params['log_level'], params['log_filename'])
        logger.error(f"ValueError {value_error}")


if __name__ == "__main__":
    main()
