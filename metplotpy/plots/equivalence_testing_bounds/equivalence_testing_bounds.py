# ============================*
# ** Copyright UCAR (c) 2022
# ** University Corporation for Atmospheric Research (UCAR)
# ** National Center for Atmospheric Research (NCAR)
# ** Research Applications Lab (RAL)
# ** P.O.Box 3000, Boulder, Colorado, 80307-3000, USA
# ============================*


"""
Class Name: equivalence_testing_bounds.py
 """
__author__ = 'Tatiana Burek'

import os
from datetime import datetime
import re
import csv

import pandas as pd
import numpy as np

from matplotlib import pyplot as plt

from metplotpy.plots.equivalence_testing_bounds.equivalence_testing_bounds_series \
    import EquivalenceTestingBoundsSeries
from metplotpy.plots.line.line_config import LineConfig
from metplotpy.plots.line.line_series import LineSeries
from metplotpy.plots.base_plot import BasePlot
from metplotpy.plots import util

import metcalcpy.util.utils as calc_util


class EquivalenceTestingBounds(BasePlot):
    """  Generates a Plotly Equivalence Testing Bounds plot .
    """
    LONG_NAME = 'Equivalence Testing Bounds'

    def __init__(self, parameters: dict) -> None:
        """ Creates a Plotly Equivalence Testing Bounds plot, based on
            settings indicated by parameters.

            Args:
            @param parameters: dictionary containing user defined parameters

        """

        # init common layout
        super().__init__(parameters, "equivalence_testing_bounds_defaults.yaml")

        # instantiate a LineConfig object, which holds all the necessary settings
        # from the
        # config file that represents the BasePlot object (EquivalenceTestingBounds).
        self.config_obj = LineConfig(self.parameters)

        self.logger = self.config_obj.logger
        self.logger.info(f"Start equivalence testing bounds:  {datetime.now()}")

        # Check that we have all the necessary settings for each series
        self.config_obj.config_consistency_check()

        # Read in input data, location specified in config file
        self.input_df = self._read_input_data()
        self.logger.info(f"Finished reading input data: {datetime.now()}")

        # Apply event equalization, if requested
        if self.config_obj.use_ee is True:
            self.input_df = calc_util.perform_event_equalization(self.parameters,
                                                                 self.input_df)

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

        return f'EquivalenceTestingBounds({self.parameters!r})'

    def _read_input_data(self):
        """
            Read the input data file
            and store as a pandas dataframe so we can subset the
            data to represent each of the series defined by the
            series_val permutations.

            Args:

            Returns:

        """
        self.logger.info(f"Begin reading input data: {datetime.now()}")
        return pd.read_csv(self.config_obj.parameters['stat_input'], sep='\t',
                           header='infer', float_precision='round_trip')

    def _create_series(self, input_data):
        """
           Generate all the series objects that are to be displayed as specified by
           the plot_disp
           setting in the config file.  The points are all ordered by datetime.

           Args:
               input_data:  The input data in the form of a Pandas dataframe.
                            This data will be subset to reflect the series data of
                            interest.

           Returns:
               a list of series objects that are to be displayed


        """

        self.logger.info(f"Creating series object: {datetime.now()}")
        series_list = []

        # add series for y1 axis
        num_series_y1 = len(self.config_obj.get_series_y(1))
        for i, name in enumerate(self.config_obj.get_series_y(1)):
            series_obj = EquivalenceTestingBoundsSeries(self.config_obj, i, input_data,
                                                        series_list, name)
            # we don't need to display the regular series - set disp to false
            series_obj.plot_disp = False
            series_list.append(series_obj)

        # add series for y2 axis
        num_series_y2 = len(self.config_obj.get_series_y(2))
        for i, name in enumerate(self.config_obj.get_series_y(2)):
            series_obj = EquivalenceTestingBoundsSeries(self.config_obj,
                                                        num_series_y1 + i,
                                                        input_data, series_list, name,
                                                        2)
            # we don't need to display the regular series - set disp to false
            series_obj.plot_disp = False
            series_list.append(series_obj)

        # add derived for y1 axis
        num_series_y1_d = len(self.config_obj.get_config_value('derived_series_1'))
        for i, name in enumerate(self.config_obj.get_config_value('derived_series_1')):
            # add only ETB curves
            if name[2] == "ETB":
                series_obj = EquivalenceTestingBoundsSeries(self.config_obj,
                                                            num_series_y1 +
                                                            num_series_y2 + i,
                                                            input_data, series_list,
                                                            name)
                series_list.append(series_obj)

        # add derived for y2 axis
        for i, name in enumerate(self.config_obj.get_config_value('derived_series_2')):
            if name[2] == "ETB":
                # add only ETB curves
                series_obj = EquivalenceTestingBoundsSeries(self.config_obj,
                                                            num_series_y1 +
                                                            num_series_y2 +
                                                            num_series_y1_d + i,
                                                            input_data, series_list,
                                                            name, 2)
                series_list.append(series_obj)

        # reorder series
        series_list = self.config_obj.create_list_by_series_ordering(series_list)

        self.logger.info(f"Finished creating series object: {datetime.now()}")
        return series_list

    def _create_figure(self):
        """
        Create an Equivalence Testing Bounds plot from defaults and custom parameters
        """
        self.logger.info(f"Creating the figure: {datetime.now()}")

        # create and draw the plot
        _, ax = plt.subplots(figsize=(self.config_obj.plot_width, self.config_obj.plot_height))

        wts_size_styles = self.get_weights_size_styles()

        self._add_title(ax, wts_size_styles['title'])
        self._add_caption(plt, wts_size_styles['caption'])

        ax_y2 = None
        if self.config_obj.parameters['list_stat_2']:
            ax_y2 = self._add_y2axis(ax, wts_size_styles['y2lab'])

        handles_and_labels = self._add_series(ax, ax_y2)

        xlab_style = wts_size_styles['xlab'] if not self.config_obj.vert_plot else wts_size_styles['ylab']
        ylab_style = wts_size_styles['ylab'] if not self.config_obj.vert_plot else wts_size_styles['xlab']
        self._add_xaxis(ax, xlab_style)
        self._add_yaxis(ax, ylab_style, grid_on=False)
        # if y limits are not set, use -1 to 1
        if not getattr(self.config_obj, 'vert_plot', False) and not len(self.config_obj.parameters['ylim']):
            ax.set_ylim(-1, 1)

        self._add_legend(ax, handles_and_labels)

        # add custom lines
        self._add_lines(ax, self.config_obj, self.config_obj.indy_vals)

        plt.tight_layout()

        self.logger.info(f"Finished creating the figure: {datetime.now()}")

    def _add_series(self, ax, ax2):
        handles_and_labels = []
        ind = 0
        for series in self.series_list:

            # Don't generate the plot for this series if
            # it isn't requested (as set in the config file)
            if series.plot_disp:
                handle = self._draw_series(ax, ax2, series, ind)
                handles_and_labels.append((handle, handle.get_label()))
                ind = ind + 1

        return handles_and_labels

    def _draw_series(self, ax, ax2, series: LineSeries, ind: int):
        """
        Draws the formatted ETB line on the plot

        :param series: EquivalenceTestingBounds series object with data and parameters
        :param ind: index of the series
        """

        self.logger.info(f"Start drawing the lines on the plot: {datetime.now()}")
        ci_tost_up = series.series_points['ci_tost'][1]
        ci_tost_lo = series.series_points['ci_tost'][0]
        dif = series.series_points['dif']

        x_points = [dif]
        y_points = [ind]

        # add the plot
        # convert to a numpy array to change None values to NaN
        asymmetric_error = np.array([
            ci_tost_up - dif,
            dif - ci_tost_lo
        ], dtype=float).reshape(2, 1)

        # determine which y-axis to use for the plot
        plot_ax = ax if series.y_axis == 1 else ax2

        # plot error bar
        plot_mode = self.config_obj.mode[series.idx]
        marker = self.config_obj.marker_list[series.idx] if 'markers' in plot_mode else None
        line_style = self.config_obj.linestyles_list[series.idx] if 'lines' in plot_mode else 'None'

        # Swap x and y data if vertical plot
        plot_x = y_points if self.config_obj.vert_plot else x_points
        plot_y = x_points if self.config_obj.vert_plot else y_points

        # Swap error bars (yerr becomes xerr) if vertical plot
        x_err_val = asymmetric_error if not self.config_obj.vert_plot else None
        y_err_val = asymmetric_error if self.config_obj.vert_plot else None

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
            capsize=5,
        )

        # add bounds lines
        x = [series.series_points['eqbound'][0], series.series_points['eqbound'][0]]
        if len(self.config_obj.parameters['ylim']) > 0:
            y = [self.config_obj.parameters['ylim'][0], self.config_obj.parameters['ylim'][1]]
        else:
            y = [-1, 1]
        ax.plot(x, y, color=self.config_obj.colors_list[series.idx], linewidth=1, linestyle='--')

        x = [series.series_points['eqbound'][1], series.series_points['eqbound'][1]]
        ax.plot(x, y, color=self.config_obj.colors_list[series.idx], linewidth=1, linestyle='--')

        self.logger.info(f"Finished drawing the lines on the plot: {datetime.now()}")
        return plot_obj

    def write_output_file(self) -> None:
        """
        Formats y1 and y2 series point data to the 2-dim arrays and saves them to the
        files
        """
        self.logger.info(f"Write output file: {datetime.now()}")

        # if points_path parameter doesn't exist,
        # open file, name it based on the stat_input config setting,
        # (the input data file) except replace the .data
        # extension with .points1 extension
        # otherwise use points_path path

        ci_tost_df = pd.DataFrame(columns=['ci_tost_lo', 'diff', 'ci_tost_hi'],
                                  index=range(0, len(self.config_obj.get_config_value(
                                      'derived_series_1')) +
                                              len(self.config_obj.get_config_value(
                                                  'derived_series_2'))))
        ind = 0
        for series in self.series_list:
            if series.plot_disp:
                row = {
                    'ci_tost_lo': series.series_points['ci_tost'][0],
                    'diff': series.series_points['dif'],
                    'ci_tost_hi': series.series_points['ci_tost'][1],
                }
                ci_tost_df.loc[ind] = pd.Series(row)
                ind = ind + 1

        match = re.match(r'(.*)(.data)', self.config_obj.parameters['stat_input'])
        if self.config_obj.dump_points_1 is True and match:
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
            os.makedirs(os.path.dirname(filename), exist_ok=True)

            # save points
            self._save_points(ci_tost_df.to_numpy().tolist(), filename)

        self.logger.info(f"Finished writing the output file: {datetime.now()}")

    @staticmethod
    def _save_points(points: list, output_file: str) -> None:
        """
        Saves array of points to the file. Ir replaces all None values to N/A and
        format floats
        :param points: 2-dimensional array. The 1st dimension is the number of x-axis
        points
        The 2nd - is the all y-points for a single  x-axis points. Each y-points has
        3 numbers:
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
            Generates a sample, default, Equivalence Testing Bounds plot using the
            default and custom config files on sample data found in this directory.
            The location of the input data is defined in either the default or
            custom config file.
            Args:
                @param config_filename: default is None, the name of the custom config file to apply
        """
    util.make_plot(config_filename, EquivalenceTestingBounds)


if __name__ == "__main__":
    main()
