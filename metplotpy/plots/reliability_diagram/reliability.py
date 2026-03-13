# ============================*
 # ** Copyright UCAR (c) 2020
 # ** University Corporation for Atmospheric Research (UCAR)
 # ** National Center for Atmospheric Research (NCAR)
 # ** Research Applications Lab (RAL)
 # ** P.O.Box 3000, Boulder, Colorado, 80307-3000, USA
 # ============================*
 
 
 
"""
Class Name: reliability.py
 """
__author__ = 'Tatiana Burek'

import os
import re
import csv
from datetime import datetime
from typing import Union

import numpy as np
import pandas as pd

from matplotlib import pyplot as plt
from matplotlib import ticker

from metplotpy.plots.base_plot import BasePlot
from metplotpy.plots import util
from metplotpy.plots.constants import MPL_DEFAULT_BAR_WIDTH
from metplotpy.plots.reliability_diagram.reliability_config import ReliabilityConfig
from metplotpy.plots.reliability_diagram.reliability_series import ReliabilitySeries


class Reliability(BasePlot):
    """  Generates a Plotly line plot for 1 or more traces (lines)
         where each line is represented by a text point data file.
    """

    def __init__(self, parameters: dict) -> None:
        """ Creates a line plot consisting of one or more lines (traces), based on
            settings indicated by parameters.

            Args:
            @param parameters: dictionary containing user defined parameters

        """

        # init common layout
        super().__init__(parameters, "reliability_defaults.yaml")

        # instantiate a LineConfig object, which holds all the necessary settings from the
        # config file that represents the BasePlot object (Line).
        self.config_obj = ReliabilityConfig(self.parameters)

        self.logger = self.config_obj.logger
        self.logger.info(f"Begin reliability diagram: {datetime.now()}")

        # Check that we have all the necessary settings for each series
        self.config_obj.config_consistency_check()

        # Read in input data, location specified in config file
        self.input_df = self._read_input_data()

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

        return f'Reliability({self.parameters!r})'

    def _read_input_data(self):
        """
            Read the input data file
            and store as a pandas dataframe so we can subset the
            data to represent each of the series defined by the
            series_val permutations.

            Args:

            Returns:

        """
        self.logger.info("Reading input data")
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
        self.logger.info(f"Begin creating series objects: {datetime.now()}")
        series_list = []
        # add series for y1 axis
        for i, name in enumerate(self.config_obj.get_series_y()):
            series_obj = ReliabilitySeries(self.config_obj, i, input_data, series_list, name)
            series_list.append(series_obj)

        # add derived
        for i, name in enumerate(self.config_obj.summary_curves):
            series_obj = ReliabilitySeries(self.config_obj, len(self.config_obj.get_series_y()) + i,
                                           input_data, series_list, name)
            series_list.append(series_obj)

        # reorder series
        series_list = self.config_obj.create_list_by_series_ordering(series_list)

        self.logger.info(f"Finished creating series object: {datetime.now()}")

        return series_list

    def _create_figure(self):
        """
        Create a line plot from defaults and custom parameters
        """
        # create and draw the plot

        self.logger.info(f"Begin creating the lines on the reliability plot: {datetime.now()}")

        fig, ax = plt.subplots(figsize=(self.config_obj.plot_width, self.config_obj.plot_height))

        wts_size_styles = self.get_weights_size_styles()

        self._add_title(ax, wts_size_styles['title'])
        self._add_caption(plt, wts_size_styles['caption'])

        ax2 = None
        if self.config_obj.rely_event_hist:
            # create inset or create 2nd y-axis
            if self.config_obj.inset_hist:
                ax2 = ax.inset_axes((0.08, 0.7, 0.47, 0.28))
            else:
                ax2 = self._add_y2axis(ax, None)

            self._add_xaxis(ax2, wts_size_styles['xlab'])
            ax2.set_xlim(0, 1)
            self._add_yaxis(ax2, wts_size_styles['ylab'], label="# Forecasts", grid_on=True)

            # format large numbers like 3 million as 3M
            ax2.yaxis.set_major_formatter(ticker.EngFormatter())

        self._add_series(ax, ax2)

        self._add_xaxis(ax, wts_size_styles['xlab'])
        ax.set_xlim(0, 1)
        self._add_yaxis(ax, wts_size_styles['ylab'])
        ax.set_ylim(0, 1)
        ax.set_yticks(np.linspace(0, 1, 11))

        self._add_legend(ax)

        self._add_custom_lines(ax)

        plt.tight_layout()

        self.logger.info(f"Finished drawing lines on reliability diagram {datetime.now()}")

    def _add_custom_lines(self, ax):
        # add custom lines if lines are defined in config
        # TODO: move to base_plot?
        if len(self.series_list) > 0:
            self._add_lines(ax, self.config_obj, self.config_obj.indy_vals)

    def _add_series(self, ax, ax2):
        # calculate stag adjustments
        stag_adjustments = self._calc_stag_adjustments()

        x_points_index = self.series_list[-1].series_points['thresh_i'].tolist()

        # add series lines
        for index, series in enumerate(self.series_list):
            # apply staggering offset if applicable
            if stag_adjustments[series.idx] == 0:
                x_points_index_adj = x_points_index
            else:
                x_points_index_adj = x_points_index + stag_adjustments[series.idx]

            # Don't generate the plot for this series if
            # it isn't requested (as set in the config file)
            if series.plot_disp:
                self._draw_series(ax, ax2, series, x_points_index_adj, index)

    def _draw_series(self, ax, ax2, series: ReliabilitySeries, x_points_index_adj: list, idx) -> None:
        """
        Draws the formatted line with CIs if needed on the plot

        :param series: Line series object with data and parameters
        :param x_points_index_adj: values for adjusting x-values position
        """

        self.logger.info(f"Draw the bar plot and skill lines: {datetime.now()}")
        if series.idx == 0:
            self._add_noskill_polygon(ax, series.series_points['stat_value'][0])

        # determine whether to add to the inset plot or the main plot
        plot_ax = ax
        if self.config_obj.inset_hist:
            plot_ax = ax2

        if self.config_obj.rely_event_hist and 'n_i' in series.series_points:

            n_visible_series = sum(1 for s in self.series_list if s.plot_disp)
            n = max(n_visible_series, 1)
            width = MPL_DEFAULT_BAR_WIDTH / 40
            offset = (idx - (n - 1) / 2.0) * width
            x_locs = [item + offset for item in x_points_index_adj]

            plot_ax.bar(x=x_locs, height=series.series_points['n_i'].tolist(), align='center',
                        width=width,
                        color=self.config_obj.colors_list[series.idx],
                        label="Absolute_cases")

        self._add_noskill_line(ax, series.series_points['stat_value'][0])
        self._add_perfect_reliability_line(ax)
        self._add_noresolution_line(ax, series.series_points['stat_value'][0])

        y_points = series.series_points['stat_value'].tolist()
        stat_bcu = all(v == 0 for v in series.series_points['stat_btcu'])
        stat_bcl = all(v == 0 for v in series.series_points['stat_btcl'])

        error_y_visible = True

        if (stat_bcu is True and stat_bcl is True) or self.config_obj.plot_ci[series.idx] == 'NONE':
            error_y_visible = False

        # add the plot
        y_errors = [series.series_points['stat_btcl'], series.series_points['stat_btcu']]
        plot_mode = self.config_obj.mode[series.idx]
        marker = self.config_obj.marker_list[series.idx] if 'markers' in plot_mode else None
        line_style = self.config_obj.linestyles_list[series.idx] if 'lines' in plot_mode else 'None'

        ax.errorbar(
            x=x_points_index_adj,
            y=y_points,
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
            yerr=y_errors if error_y_visible else None,
            elinewidth=self.config_obj.linewidth_list[series.idx],
        )

        self.logger.info(f"Finished with bar plot and skill lines :{datetime.now()}")

    def _add_noskill_polygon(self, ax, o_bar: Union[float, None]) -> None:
        """
        Adds no-skill polygon to the graph if needed and o_bar is not None
        :param o_bar: o_bar value or None
        """
        if not self.config_obj.add_noskill_line:
            return

        if not o_bar:
            print(" WARNING: no-skill polygon can't be created for the series")
            return

        self.logger.info("Adding no-skill polygon")

        x = [o_bar, o_bar, 1, 1, o_bar, 0, 0]
        y = [0, 1, 1, (1 - o_bar) / 2 + o_bar, o_bar, o_bar, 0]
        ax.fill(x, y,
                facecolor='#ededed',
                edgecolor='#ededed',
                alpha=0.5,
                label='_no-skill-poly_')

    def _add_noskill_line(self, ax, o_bar: Union[float, None]) -> None:
        """
        Adds no-skill line to the graph if needed and o_bar is not None
        :param o_bar: o_bar value or None
        """
        if not self.config_obj.add_noskill_line:
            return
        self.logger.info("Adding no-skill line")
        if not o_bar:
            print(" WARNING: no-skill line can't be created for the series")
            return

        # create a line
        intercept = 0.5 * o_bar
        x = [0, 1]
        y = [util.abline(0, intercept, 0.5), util.abline(1, intercept, 0.5)]
        ax.plot(x, y, label='_No-Skill_', color=self.config_obj.noskill_line_col, linewidth=1, linestyle='--')

        # create annotation
        ax.text(
            1, util.abline(1, intercept, 0.5),
            "No-Skill",
            size=self.config_obj.x_tickfont_size,
            color='#636363',
            rotation=270,
            transform=ax.transAxes,
        )

    def _add_perfect_reliability_line(self, ax) -> None:
        """
         Adds perfect reliability line to the graph if needed
        """
        if not self.config_obj.add_skill_line:
            return

        self.logger.info("Adding perfect reliability line")
        x = [0., 1.]
        y = [util.abline(0, 0, 1), util.abline(1, 0, 1)]
        ax.plot(x, y, label='_Perfect reliability_', color='grey', zorder=0, linewidth=1)

        ax.text(
            1, util.abline(1, 0, 1),
            "Perfect reliability",
            size=self.config_obj.x_tickfont_size,
            color='#636363',
            rotation=270,
            transform=ax.transAxes,
        )

    def _add_noresolution_line(self, ax, o_bar: Union[float, None]) -> None:
        """
        Adds no-resolution line to the graph if needed and o_bar is not None
        :param o_bar: o_bar value or None
        """
        if not self.config_obj.add_reference_line:
            return

        self.logger.info("Adding no-resolution line")

        if not o_bar:
            print(" WARNING: no-resolution line can't be created for the series")
            return

        end_to_end = [0, 1]
        ab_line = [util.abline(0, o_bar, 0), util.abline(1, o_bar, 0)]
        ax.plot(end_to_end, ab_line, label='_No-resolution_',
                color=self.config_obj.reference_line_col, linestyle='--', zorder=0, linewidth=1)

        ax.plot(ab_line, end_to_end, label='_No-resolution_',
                color=self.config_obj.reference_line_col, linestyle='--', zorder=0, linewidth=1)

        ax.text(
            1, util.abline(1, o_bar, 0),
            "No-resolution",
            size=self.config_obj.x_tickfont_size,
            color='#636363',
            rotation=270,
            transform=ax.transAxes,
        )

    def write_output_file(self) -> None:
        """
        Formats series point data to the 2-dim array and saves it to the files
        """
        self.logger.info("Writing output file.")

        # if points_path parameter doesn't exist,
        # open file, name it based on the stat_input config setting,
        # (the input data file) except replace the .data
        # extension with .points1 extension
        # otherwise use points_path path

        match = re.match(r'(.*)(.data)', self.config_obj.parameters['stat_input'])
        if self.config_obj.dump_points_1 is True and match:

            # create an array for y1 points
            all_points_1 = []

            # get points from each series
            for series in self.series_list:
                series.series_points['stat_btcl'] \
                    = series.series_points['stat_value'] - series.series_points['stat_btcl']
                series.series_points['stat_btcu'] \
                    = series.series_points['stat_value'] + series.series_points['stat_btcu']
                columns_for_print \
                    = series.series_points[["thresh_i", "stat_value", 'stat_btcl', 'stat_btcu']]
                all_points_1.append(columns_for_print.head().values.tolist())

            all_points_1 = [item for sublist in all_points_1 for item in sublist]

            filename = match.group(1)
            # replace the default path with the custom
            if self.config_obj.points_path is not None:
                # get the file name
                path = filename.split(os.path.sep)
                if len(path) > 0:
                    filename = path[-1]
                else:
                    filename = '.' + os.path.sep
                filename = self.config_obj.points_path + os.path.sep + filename

            filename = filename + '.points1'

            # save points
            self._save_points(all_points_1, filename)

    def _calc_stag_adjustments(self) -> list:
        """
        Calculates the x-axis adjustment for each point if requested.
        It needed so hte points and CIs for each x-axis values don't be placed on top of each other

        :return: the list of the adjustment values
        """

        self.logger.info("Calculate x-axis adjustment")

        # get the total number of series
        num_stag = len(self.config_obj.all_series_y1) + len(self.config_obj.summary_curves)

        # init the result with 0
        stag_vals = [0] * num_stag

        # calculate staggering values
        if self.config_obj.indy_stagger is True:
            dbl_adj_scale = (self.series_list[-1].series_points['thresh_i'].tolist()[-1] -
                             self.series_list[-1].series_points['thresh_i'].tolist()[0]) / 150
            stag_vals = np.linspace(-(num_stag / 2) * dbl_adj_scale,
                                    (num_stag / 2) * dbl_adj_scale,
                                    num_stag,
                                    True)
            stag_vals = stag_vals + dbl_adj_scale / 2
        return stag_vals

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
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
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
    util.make_plot(config_filename, Reliability)


if __name__ == "__main__":
    main()
