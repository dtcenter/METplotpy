# ============================*
# ** Copyright UCAR (c) 2020
# ** University Corporation for Atmospheric Research (UCAR)
# ** National Center for Atmospheric Research (NCAR)
# ** Research Applications Lab (RAL)
# ** P.O.Box 3000, Boulder, Colorado, 80307-3000, USA
# ============================*


"""
Class Name: bar.py
 """
__author__ = 'Tatiana Burek'

from datetime import datetime
import os
import re
from operator import add

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt

import metcalcpy.util.utils as calc_util

from metplotpy.plots import util
from metplotpy.plots import constants
from metplotpy.plots.bar.bar_config import BarConfig
from metplotpy.plots.bar.bar_series import BarSeries
from metplotpy.plots.base_plot import BasePlot


class Bar(BasePlot):
    """  Generates a Plotly bar plot for 1 or more traces (bars)
         where each bar is represented by a text point data file.
    """

    def __init__(self, parameters: dict) -> None:
        """ Creates a bar plot consisting of one or more bars (traces), based on
            settings indicated by parameters.

            Args:
            @param parameters: dictionary containing user defined parameters

        """

        # init common layout
        super().__init__(parameters, "bar_defaults.yaml")

        # instantiate a BarConfig object, which holds all the necessary settings from
        # the
        # config file that represents the BasePlot object (Bar).
        self.config_obj = BarConfig(self.parameters)
        self.logger = self.config_obj.logger
        self.logger.info(f"Start bar plot: {datetime.now()}")
        # Check that we have all the necessary settings for each series
        self.config_obj.config_consistency_check()

        # Read in input data, location specified in config file
        self.logger.info(f"Begin reading input data: {datetime.now()}")
        self.input_df = self._read_input_data()

        # Apply event equalization, if requested
        if self.config_obj.use_ee is True:
            self.logger.info(f"Performing event equalization: {datetime.now()}")
            self.input_df = calc_util.perform_event_equalization(self.parameters,
                                                                 self.input_df)
            self.logger.info(f"End event equalization: {datetime.now()}")

        # Create a list of series objects.
        # Each series object contains all the necessary information for plotting,
        # such as bar color and criteria needed to subset the input dataframe.
        self.series_list = self._create_series(self.input_df)

        # create figure
        # pylint:disable=assignment-from-no-return
        # Need to have a self.figure that we can pass along to
        # the methods in base_plot.py (BasePlot class methods) to
        # create binary versions of the plot.
        self.logger.info(f"Begin creating the figure: {datetime.now()}")
        self._create_figure()
        self.logger.info(f"End creating the figure: {datetime.now()}")

    def __repr__(self):
        """ Implement repr which can be useful for debugging this
            class.
        """

        return f'Bar({self.parameters!r})'

    def _read_input_data(self):
        """
            Read the input data file
            and store as a pandas dataframe so we can subset the
            data to represent each of the series defined by the
            series_val permutations.

            Args:

            Returns:

        """
        self.logger.info(f"Finished reading input data: "
                                    f"{datetime.now()}")
        return pd.read_csv(self.config_obj.parameters['stat_input'], sep='\t',
                           header='infer', float_precision='round_trip')

    def _create_series(self, input_data):
        """
           Generate all the series objects that are to be displayed as specified by
           the plot_disp
           setting in the config file.  The points are all ordered by datetime.  Each
           series object
           is represented by a bar in the diagram, so they also contain information
           for bar width, colors and other plot-related/
           appearance-related settings (which were defined in the config file).

           Args:
               input_data:  The input data in the form of a Pandas dataframe.
                            This data will be subset to reflect the series data of
                            interest.

           Returns:
               a list of series objects that are to be displayed


        """
        series_list = []

        # add series for y1 axis
        num_series_y1 = len(self.config_obj.get_series_y())
        for i, name in enumerate(self.config_obj.get_series_y()):
            series_obj = BarSeries(self.config_obj, i, input_data, series_list, name)
            series_list.append(series_obj)

        # add derived for y1 axis
        for i, name in enumerate(self.config_obj.get_config_value('derived_series_1')):
            # add default operation value if it is not provided
            if len(name) == 2:
                name.append("DIFF")
            # include the series only if the name is valid
            if len(name) == 3:
                series_obj = BarSeries(self.config_obj, num_series_y1 + i,
                                       input_data, series_list, name)
                series_list.append(series_obj)

        # reorder series
        series_list = self.config_obj.create_list_by_series_ordering(series_list)

        if self.config_obj.xaxis_reverse:
            series_list.reverse()

        return series_list

    def _create_figure(self):
        """
        Create a bar plot from defaults and custom parameters
        """
        # create and draw the plot
        _, ax = plt.subplots(figsize=(self.config_obj.plot_width, self.config_obj.plot_height))

        wts_size_styles = self.get_weights_size_styles()

        self._add_title(ax, wts_size_styles['title'])
        self._add_caption(plt, wts_size_styles['caption'])

        self._add_xaxis(ax, wts_size_styles['xlab'])
        self._add_yaxis(ax, wts_size_styles['ylab'])

        n_stats = self._add_series(ax)
        self._add_x2axis(ax, n_stats, wts_size_styles['x2lab'])

        self._add_legend(ax)

        # add custom lines if lines are defined in config
        if len(self.series_list) > 0:
            self._add_lines(ax, self.config_obj, self.config_obj.indy_vals)

        plt.tight_layout()

    def _add_series(self, ax):
        # placeholder for the number of stats
        n_stats = [0] * len(self.config_obj.indy_vals)

        # add series lines
        for idx, series in enumerate(self.series_list):

            # Don't generate the plot for this series if
            # it isn't requested (as set in the config file)
            if series.plot_disp:
                self._draw_series(ax, series, idx)

                # aggregate number of stats
                n_stats = list(map(add, n_stats, series.series_points['nstat']))

        return n_stats

    def _draw_series(self, ax: plt.Axes, series: BarSeries, idx: int) -> None:
        """
        Draws the formatted Bar on the plot
        :param series: Bar series object with data and parameters
        """

        y_points = series.series_points['dbl_med']
        is_threshold, is_percent_threshold = util.is_threshold_value(
            series.series_data[self.config_obj.indy_var]
        )

        # If there are any None types in the series_points['dbl_med'] list, then use the
        # indy_vals defined in the config file to ensure that the number of y_points
        # is the
        # same number of x_points.
        if None in y_points:
            x_points = self.config_obj.indy_vals
            y_points = [item if item is not None else 0 for item in y_points]
        elif is_percent_threshold:
            x_points = self.config_obj.indy_var
        elif is_threshold:
            # Sort the threshold values after getting unique values because the
            # order
            # of the threshold
            # is lost during the unique() operation.  If there are percent
            # thresholds
            # in the fcst_thresh
            # column, then use the indy_vals specified in the config file.
            x_points = util.sort_threshold_values(
                series.series_data[self.config_obj.indy_var].unique())
        else:
            x_points = sorted(series.series_data[self.config_obj.indy_var].unique())

        base = np.arange(len(x_points))
        n_visible_series = sum(1 for s in self.series_list if s.plot_disp)
        n = max(n_visible_series, 1)
        width = constants.MPL_DEFAULT_BAR_WIDTH / n
        offset = (idx - (n - 1) / 2.0) * width
        x_locs = base + offset

        # add the plot
        ax.bar(x=x_locs, height=y_points, width=width, align='center', color=self.config_obj.colors_list[series.idx],
               label=self.config_obj.user_legends[series.idx])

    def write_output_file(self) -> None:
        """
        Formats series point data to the 2-dim arrays and saves them to the files
        """

        # if points_path parameter doesn't exist,
        # open file, name it based on the stat_input config setting,
        # (the input data file) except replace the .data
        # extension with .points1 extension
        # otherwise use points_path path

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

            # create directory if needed
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            with open(filename, 'w') as f:
                for series in self.series_list:
                    f.write(f"{series.series_points['dbl_med']}\n")


def main(config_filename=None):
    """
            Generates a sample, default, bar plot using the
            default and custom config files on sample data found in this directory.
            The location of the input data is defined in either the default or
            custom config file.
            Args:
                @param config_filename: default is None, the name of the custom
                config file to apply
        """
    util.make_plot(config_filename, Bar)


if __name__ == "__main__":
    main()
