# ============================*
 # ** Copyright UCAR (c) 2020
 # ** University Corporation for Atmospheric Research (UCAR)
 # ** National Center for Atmospheric Research (NCAR)
 # ** Research Applications Lab (RAL)
 # ** P.O.Box 3000, Boulder, Colorado, 80307-3000, USA
 # ============================*
 
 
 
"""
Class Name: box.py
 """

__author__ = 'Hank Fisher, Tatiana Burek'

from datetime import datetime
import re
import os
from typing import Union
from operator import add
from itertools import chain
import pandas as pd
import numpy as np

from matplotlib import pyplot as plt

import metcalcpy.util.utils as calc_util

from metplotpy.plots.base_plot import BasePlot
from metplotpy.plots.box.box_config import BoxConfig
from metplotpy.plots.box.box_series import BoxSeries
from metplotpy.plots import util
from metplotpy.plots.constants import MPL_DEFAULT_BOX_WIDTH


class Box(BasePlot):
    """  Generates a Plotly box plot for 1 or more traces
         where each box is represented by a text point data file.
    """

    def __init__(self, parameters):
        """ Creates a box plot, based on
            settings indicated by parameters.

            Args:
            @param parameters: dictionary containing user defined parameters

        """

        # init common layout
        super().__init__(parameters, "box_defaults.yaml")

        # instantiate a BoxConfig object, which holds all the necessary settings from the
        # config file that represents the BasePlot object (Box).
        self.config_obj = BoxConfig(self.parameters)

        self.logger = self.config_obj.logger

        self.logger.info(f"Start bar plot at {datetime.now()}")

        # Check that we have all the necessary settings for each series
        self.config_obj.config_consistency_check()

        # Read in input data, location specified in config file
        self.input_df = self._read_input_data()

        # Apply event equalization, if requested
        if self.config_obj.use_ee is True:
            self.logger.info(f"Start event equalization: {datetime.now()}")
            self.input_df = calc_util.perform_event_equalization(self.parameters, self.input_df)
            self.logger.info(f"Finish event equalization: {datetime.now()}")

        # Create a list of series objects.
        # Each series object contains all the necessary information for plotting,
        # such as line color, marker symbol,
        # line width, and criteria needed to subset the input dataframe.
        self.series_list = self._create_series(self.input_df)

        self._create_figure()

    def _read_input_data(self):
        """
            Read the input data file
            and store as a pandas dataframe so we can subset the
            data to represent each of the series defined by the
            series_val permutations.

            Args:

            Returns:

        """
        self.config_obj.logger.info(f"Begin reading input data: {datetime.now()}")
        file = self.config_obj.parameters['stat_input']
        self.config_obj.logger.info(f"Finish reading input data: {datetime.now()}")
        return pd.read_csv(file, sep='\t', header='infer', float_precision='round_trip')

    def _create_series(self, input_data):
        """
           Generate all the series objects that are to be displayed as specified by the plot_disp
           setting in the config file.  The points are all ordered by datetime.  Each series object
           is represented by a box in the diagram, so they also contain information
           for  plot-related/appearance-related settings (which were defined in the config file).

           Args:
               input_data:  The input data in the form of a Pandas dataframe.
                            This data will be subset to reflect the series data of interest.

           Returns:
               a list of series objects that are to be displayed


        """
        self.logger.info(f"Begin generating series objects: {datetime.now()}")
        series_list = []

        # add series for y1 axis
        num_series_y1 = len(self.config_obj.get_series_y(1))
        for i, name in enumerate(self.config_obj.get_series_y(1)):
            series_obj = BoxSeries(self.config_obj, i, input_data, series_list, name)
            series_list.append(series_obj)

        # add series for y2 axis
        num_series_y2 = len(self.config_obj.get_series_y(2))
        for i, name in enumerate(self.config_obj.get_series_y(2)):
            series_obj = BoxSeries(self.config_obj, num_series_y1 + i,
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
                series_obj = BoxSeries(self.config_obj, num_series_y1 + num_series_y2 + i,
                                   input_data, series_list, name)
                series_list.append(series_obj)

        # add derived for y2 axis
        for i, name in enumerate(self.config_obj.get_config_value('derived_series_2')):
            # add default operation value if it is not provided
            if len(name) == 2:
                name.append("DIFF")
            # include the series only if the name is valid
            if len(name) == 3:
                series_obj = BoxSeries(self.config_obj,
                                   num_series_y1 + num_series_y2 + num_series_y1_d + i,
                                   input_data, series_list, name, 2)
                series_list.append(series_obj)

        # reorder series
        series_list = self.config_obj.create_list_by_series_ordering(series_list)

        if self.config_obj.xaxis_reverse:
            series_list.reverse()

        self.logger.info(f"End generating series objects: {datetime.now()}")

        return series_list

    def _create_figure(self):
        """ Create a box plot from default and custom parameters"""
        self.logger.info(f"Begin creating the figure: {datetime.now()}")

        _, ax = plt.subplots(figsize=(self.config_obj.plot_width, self.config_obj.plot_height))

        wts_size_styles = self.get_weights_size_styles()

        self._add_title(ax, wts_size_styles['title'])
        self._add_caption(plt, wts_size_styles['caption'])

        ax_y2 = None
        if wts_size_styles.get('y2lab') and self.config_obj.parameters['list_stat_2']:
            ax_y2 = self._add_y2axis(ax, wts_size_styles['y2lab'])

        n_stats, handles_and_labels, yaxis_min, yaxis_max = self._add_series(ax, ax_y2)

        self._add_xaxis(ax, wts_size_styles['xlab'])
        self._add_yaxis(ax, wts_size_styles['ylab'])

        # add x2 axis
        if wts_size_styles.get('x2lab'):
            self._add_x2axis(ax, n_stats, wts_size_styles['x2lab'])

        self._sync_yaxes(ax, ax_y2, yaxis_min, yaxis_max)
        self._add_legend(ax, handles_and_labels)

        self._add_custom_lines(ax)

        plt.tight_layout()

        self.logger.info(f"End creating the figure: {datetime.now()}")

    def _add_custom_lines(self, ax):
        # add custom lines if lines are defined in config
        if len(self.series_list) > 0:
            self._add_lines(ax, self.config_obj, self.config_obj.indy_vals)

    def _sync_yaxes(self, ax, ax2, yaxis_min: Union[float, None], yaxis_max: Union[float, None]):
        if not self.config_obj.sync_yaxes:
            return

        # set y limits if defined in config or if min/max are provided
        if len(self.config_obj.parameters['ylim']) > 0:
            yaxis_min = self.config_obj.parameters['ylim'][0]
            yaxis_max = self.config_obj.parameters['ylim'][1]

        if yaxis_min is not None and yaxis_max is not None:
            ax.set_ylim(yaxis_min, yaxis_max)
            ax2.set_ylim(yaxis_min, yaxis_max)

    def _draw_series(self, ax: plt.Axes, ax2, series: BoxSeries, idx: int):
        """
        Draws the boxes on the plot

        :param series: Line series object with data and parameters
        """

        self.logger.info(f"Begin drawing the boxes on the plot for {series.series_name}: {datetime.now()}")

        # Group your 'stat_value' data by 'indy_var' categories first
        data_to_plot, x_locs, width = self._get_data_to_plot_and_x_locs(series, idx)

        plot_ax = ax
        if ax2 and ax2.get_ylabel() in series.series_data.stat_name.values:
            plot_ax = ax2

        # Define properties for median and mean lines
        median_props = {
            'color': 'black',
            'linewidth': 1,
        }
        mean_props = {
            'linestyle': '--',
            'color': 'black',
            'linewidth': 1,
        }

        boxplot = plot_ax.boxplot(data_to_plot, positions=x_locs,
                                  patch_artist=True,
                                  widths=width,
                                  label=self.config_obj.user_legends[series.idx],
                                  showmeans=self.config_obj.box_avg,
                                  meanline=self.config_obj.box_avg,
                                  medianprops=median_props,
                                  meanprops=mean_props,
                                  whis=self.config_obj.whis,
                                  showfliers=self.config_obj.showfliers,
                                  )

        for box in boxplot['boxes']:
            box.set_facecolor(series.color)

        return boxplot['boxes'][0]

    def _get_data_to_plot_and_x_locs(self, series, idx):
        x_locs, width = self._get_x_locs_and_width(self.config_obj.indy_vals, idx)

        data_to_plot =  [group_data for name, group_data in
                         series.series_data.groupby(self.config_obj.indy_var)['stat_value']]
        return data_to_plot, x_locs, width

    def _add_series(self, ax, ax2):
        handles_and_labels = []
        n_stats = [0] * len(self.config_obj.indy_vals)
        yaxis_min = None
        yaxis_max = None

        for idx, series in enumerate(self.series_list):
            # Don't generate the plot for this series if
            # it isn't requested (as set in the config file)
            if series.plot_disp:
                # collect min-max if we need to sync axis
                if self.config_obj.sync_yaxes:
                    yaxis_min, yaxis_max = self._find_min_max(series, yaxis_min, yaxis_max)

                handle = self._draw_series(ax, ax2, series, idx)
                handles_and_labels.append((handle, handle.get_label()))

                # aggregate number of stats
                # do not increment n_stats if it is not set, e.g. for revision_box
                if series.series_points.get('nstat'):
                    n_stats = list(map(add, n_stats, series.series_points['nstat']))

        return n_stats, handles_and_labels, yaxis_min, yaxis_max

    def _find_min_max(self, series: BoxSeries, yaxis_min: Union[float, None],
                      yaxis_max: Union[float, None]) -> tuple:
        """
        Finds min and max value between provided min and max and y-axis CI values of this series
        if yaxis_min or yaxis_max is None - min/max value of the series is returned

        :param series: series to use for calculations
        :param yaxis_min: previously calculated min value
        :param yaxis_max: previously calculated max value
        :return: a tuple with calculated min/max
        """
        self.logger.info(f"Begin finding min and max CI values: {datetime.now()}")
        # calculate series upper and lower limits of CIs
        indexes = range(len(series.series_points['dbl_med']))
        upper_range = [series.series_points['dbl_med'][i] + series.series_points['dbl_up_ci'][i]
                       for i in indexes]
        low_range = [series.series_points['dbl_med'][i] - series.series_points['dbl_lo_ci'][i]
                     for i in indexes]
        # find min max
        if yaxis_min is None or yaxis_max is None:
            return min(low_range), max(upper_range)

        self.logger.info(f"End finding min and max CI values: {datetime.now()}")

        return min(chain([yaxis_min], low_range)), max(chain([yaxis_max], upper_range))

    def write_output_file(self) -> None:
        """
        Formats y1 and y2 series point data to the 2-dim arrays and saves them to the files
        """

        # open file, name it based on the stat_input config setting,
        # (the input data file) except replace the .data
        # extension with .points1 extension
        # otherwise use points_path path

        match = re.match(r'(.*)(.data)', self.config_obj.parameters['stat_input'])
        if not self.config_obj.dump_points_1 and not self.config_obj.dump_points_2 or not match:
            return

        filename = match.group(1)
        # replace the default path with the custom
        if self.config_obj.points_path is not None:
            filename = os.path.join(self.config_obj.points_path, os.path.basename(filename))

        filename = f"{filename}.points1"
        if os.path.exists(filename):
            os.remove(filename)
        # create directory if needed
        os.makedirs(os.path.dirname(filename), exist_ok=True)

        for series in self.series_list:
            for indy_val in self.config_obj.indy_vals:
                if calc_util.is_string_integer(indy_val):
                    data_for_indy = series.series_data[
                        series.series_data[self.config_obj.indy_var] == int(indy_val)]
                elif calc_util.is_string_strictly_float(indy_val):
                    data_for_indy = series.series_data[
                        series.series_data[self.config_obj.indy_var] == float(indy_val)]
                else:
                    data_for_indy = series.series_data[
                        series.series_data[self.config_obj.indy_var] == indy_val]

                with open(filename, 'a') as file_object:
                    file_object.write('\n')
                    file_object.write(' '.join([str(elem) for elem in series.series_name]) + ' ' + indy_val)
                    file_object.write('\n')

                quantile_data = data_for_indy['stat_value'].quantile([0, 0.25, 0.5, 0.75, 1]).iloc[::-1]
                quantile_data.to_csv(filename, header=False, index=None, sep=' ', mode='a')


def main(config_filename=None):
    """
        Generates a sample, default, box plot using a combination of
        default and custom config files on sample data found in this directory.
        The location of the input data is defined in either the default or
        custom config file.
        Args:
                @param config_filename: default is None, the name of the custom config file to apply
    """
    util.make_plot(config_filename, Box)


if __name__ == "__main__":
    main()
