# ============================*
# ** Copyright UCAR (c) 2022
# ** University Corporation for Atmospheric Research (UCAR)
# ** National Center for Atmospheric Research (NCAR)
# ** Research Applications Lab (RAL)
# ** P.O.Box 3000, Boulder, Colorado, 80307-3000, USA
# ============================*


"""
Class Name: eclv.py
 """
__author__ = 'Tatiana Burek'

import os
import re
import csv
from operator import add
from typing import Union
import itertools
from datetime import datetime

from matplotlib import pyplot as plt

from metcalcpy.event_equalize import event_equalize

from metplotpy.plots.base_plot import BasePlot
from metplotpy.plots.eclv.eclv_config import EclvConfig
from metplotpy.plots.eclv.eclv_series import EclvSeries
from metplotpy.plots.line.line import Line
from metplotpy.plots import util
from metplotpy.plots.series import Series


class Eclv(Line):
    """  Generates a Plotly Economic Cost Loss Relative Value plot for 1 or more
    traces (lines)
         where each line is represented by a text point data file.
    """
    defaults_name = "eclv_defaults.yaml"
    ECLV_INDY_VAR = 'x_pnt_i'

    def __init__(self, parameters: dict) -> None:
        """ Creates a eclv plot consisting of one or more lines (traces), based on
            settings indicated by parameters.

            Args:
            @param parameters: dictionary containing user defined parameters

        """

        # init common layout
        BasePlot.__init__(self, parameters, self.defaults_name)
        self.x_axis_ticktext = []
        self.allow_secondary_y = False

        # instantiate an EclvConfig object, which holds all the necessary settings
        # from the
        # config file that represents the BasePlot object (Eclv).
        self.config_obj = EclvConfig(self.parameters)

        self.logger = self.config_obj.logger

        self.logger.info(f"Start eclv plot: {datetime.now()}")

        # Check that we have all the necessary settings for each series
        self.config_obj.config_consistency_check()

        # Read in input data, location specified in config file
        self.logger.info(f"Begin reading input data: {datetime.now()}")
        self.input_df = self._read_input_data()

        # Apply event equalization, if requested
        if self.config_obj.use_ee is True:
            self.logger.info(f"Performing event equalization: {datetime.now()}")
            fix_vals_permuted_list = []

            for key in self.config_obj.fixed_vars_vals_input:
                vals_permuted = list(itertools.product(
                    *self.config_obj.fixed_vars_vals_input[key].values()))
                vals_permuted_list = [item for sublist in vals_permuted for item in
                                      sublist]
                fix_vals_permuted_list.append(vals_permuted_list)

            fix_vals_keys = list(self.config_obj.fixed_vars_vals_input.keys())

            self.input_df = event_equalize(self.input_df, self.ECLV_INDY_VAR,
                                           self.parameters['series_val_1'],
                                           fix_vals_keys,
                                           fix_vals_permuted_list, True, True)
        self.logger.info(f"End even equalization: {datetime.now()}")

        # Create a list of series objects.
        # Each series object contains all the necessary information for plotting,
        # such as line color, marker symbol,
        # line width, and criteria needed to subset the input dataframe.
        self.series_list = self._create_series(self.input_df)

        self.logger.info(f"Begin creating the figure: {datetime.now()}")
        self._create_figure()
        self.logger.info(f"End creating the figure: {datetime.now()}")

    def __repr__(self):
        """ Implement repr which can be useful for debugging this
            class.
        """

        return f'Eclv({self.parameters!r})'

    def _create_series(self, input_data):
        """
           Generate all the series objects that are to be displayed as specified by
           the plot_disp
           setting in the config file.  Each series object
           is represented by a line in the diagram, so they also contain information
           for line width, line- and marker-colors, line style, and other plot-related/
           appearance-related settings (which were defined in the config file).

           Args:
               input_data:  The input data in the form of a Pandas dataframe.
                            This data will be subset to reflect the series data of
                            interest.

           Returns:
               a list of series objects that are to be displayed


        """

        self.logger.info(f"Begin creating series objects: {datetime.now()}")
        series_list = []

        # add series for y1 axis
        for i, name in enumerate(self.config_obj.get_series_y(1)):
            if isinstance(name, str):
                name = [name]
            series_obj = EclvSeries(self.config_obj, i, input_data, series_list, name)
            series_list.append(series_obj)

        # reorder series
        series_list = self.config_obj.create_list_by_series_ordering(series_list)

        self.logger.info(f"Finished creating series objects:"
                                    f" {datetime.now()}")
        return series_list

    def _create_figure(self):
        """
        Create a eclv plot from defaults and custom parameters
        """
        self.logger.info(f"Begin creating the figure: {datetime.now()}")

        # some x points could be very close to each other and the x-axis  ticktext is
        # bunched up do not print the ticktext for the first points by creating the
        # custom array of x values
        for ind, val in enumerate(self.series_list[0].series_points[0]['x_pnt']):
            var_round = round(val, 2)
            if ind != 0 and var_round < 0.06:
                self.x_axis_ticktext.append('')
            else:
                self.x_axis_ticktext.append(var_round)
        self.config_obj.indy_label = self.x_axis_ticktext
        self.config_obj.indy_vals = self.series_list[0].series_points[0]['x_pnt']

        # create and draw the plot
        _, ax = plt.subplots(figsize=(self.config_obj.plot_width, self.config_obj.plot_height))

        wts_size_styles = self.get_weights_size_styles()

        self._add_title(ax, wts_size_styles['title'])
        self._add_caption(plt, wts_size_styles['caption'])

        self._add_series(ax)

        self._add_xaxis(ax, wts_size_styles['xlab'])
        self._add_yaxis(ax, wts_size_styles['ylab'])

        # add x2 axis
        if wts_size_styles.get('x2lab'):
            self._add_x2axis(ax, wts_size_styles['x2lab'])

        self._add_legend(ax)

        # add custom lines
        self._add_lines(ax, self.config_obj, self.config_obj.indy_vals)

        plt.tight_layout()

        self.logger.info(f"Finished creating the figure: {datetime.now()}")

    def _add_series(self, ax, ax2=None):
        for series in self.series_list:
            if not series.plot_disp:
                continue

            self._draw_series(ax, ax2, series)

    def _get_nstats(self) -> list:
        """
        Calculates n_stats for the x2 axis.
        """
        n_stats = [0] * len(self.series_list[0].series_points[0]['x_pnt'])
        for series in self.series_list:
            if not series.plot_disp:
                continue

            # aggregate number of stats
            for series_points in series.series_points:
                n_stats = list(map(add, n_stats, series_points['nstat']))

        x_points = []

        # create ticktext array similar to x-axis ticktext
        for idx, val in enumerate(self.x_axis_ticktext):
            if val != '':
                x_points.append(n_stats[idx])
            else:
                x_points.append('')

        return x_points

    def _draw_series(self, ax: plt.Axes, ax2, series: Series,
                     x_points_index_adj: Union[list, None] = None) -> None:
        """
        Draws the formatted line with CIs if needed on the plot

        :param series: Eclv series object with data and parameters
        :param x_points_index_adj: values for adjusting x-values position
        """
        self.logger.info(f"Begin drawing the series : {datetime.now()}")

        # pct series can have more than one line
        for ind, series_points in enumerate(series.series_points):
            y_points = series_points['dbl_med']
            x_points = series_points['x_pnt']

            self._draw_series_item(series, series_points, ax, ax2, x_points, y_points)

            self.logger.info(f"Finished  drawing the series : {datetime.now()}")

    def write_output_file(self) -> None:
        """
        saves series points to the files
        """
        if not self.config_obj.dump_points_1:
            return

        self.logger.info(f"Begin writing output file: {datetime.now()}")

        # Open file, name it based on the stat_input config setting,
        # (the input data file) except replace the .data
        # extension with .points1 extension
        match = re.match(r'(.*)(.data)', self.config_obj.parameters['stat_input'])
        if not match:
            return

        filename = match.group(1)
        # replace the default path with the custom
        if self.config_obj.points_path is not None:
            filename = os.path.join(self.config_obj.points_path, os.path.basename(filename))

        filename = filename + '.points1'
        os.makedirs(os.path.dirname(filename), exist_ok=True)

        with open(filename, 'w') as file_handle:
            writer = csv.writer(file_handle, delimiter='\t')
            for series in self.series_list:
                for vals_ind, vals in enumerate(series.series_points):
                    keys = sorted(vals.keys())
                    if vals_ind == 0:
                        writer.writerow(keys)
                    else:
                        file_handle.writelines('\n')
                    for ind, dbl_med in enumerate(vals['dbl_med']):
                        vals['dbl_lo_ci'][ind] = dbl_med - vals['dbl_lo_ci'][ind]
                        vals['dbl_up_ci'][ind] = dbl_med + vals['dbl_up_ci'][ind]
                    writer.writerows(
                        zip(*[[round(num, 6) for num in vals[key]] for key in
                              keys]))
                file_handle.writelines('\n')
                file_handle.writelines('\n')

        self.logger.info(f"Finished writing output file: {datetime.now()}")


def main(config_filename=None):
    """
            Generates a sample, default, eclv plot using the
            default and custom config files on sample data found in this directory.
            The location of the input data is defined in either the default or
            custom config file.
            Args:
                @param config_filename: default is None, the name of the custom
                config file to apply
        """
    util.make_plot(config_filename, Eclv)


if __name__ == "__main__":
    main()
