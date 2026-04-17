# ============================*
 # ** Copyright UCAR (c) 2022
 # ** University Corporation for Atmospheric Research (UCAR)
 # ** National Center for Atmospheric Research (NCAR)
 # ** Research Applications Lab (RAL)
 # ** P.O.Box 3000, Boulder, Colorado, 80307-3000, USA
 # ============================*
 
 
 
"""
Class Name: ens_ss.py
 """
__author__ = 'Tatiana Burek'

import os
from datetime import datetime
import re
import itertools

import numpy as np
import pandas as pd

from matplotlib import pyplot as plt
from matplotlib import ticker

from metcalcpy.event_equalize import event_equalize
from metplotpy.plots.ens_ss.ens_ss_config import EnsSsConfig
from metplotpy.plots.ens_ss.ens_ss_series import EnsSsSeries
from metplotpy.plots.base_plot import BasePlot
import metplotpy.plots.util as util
import metcalcpy.util.utils as utils


class EnsSs(BasePlot):
    """  Generates a Plotly Ensemble spread-skill plot for 1 or more traces (lines)
         where each line is represented by a text point data file.
         RMSE of the ensemble mean should have roughly a 1-1 relationship with the ensemble spread
         (I.e. standard deviation of the ensemble member values).
         This plot measures that relationship.
    """

    def __init__(self, parameters: dict) -> None:
        """ Creates a Ensemble spread-skill plot consisting of one or more lines (traces), based on
            settings indicated by parameters.

            Args:
            @param parameters: dictionary containing user defined parameters

        """

        # init common layout
        super().__init__(parameters, "ens_ss_defaults.yaml")

        # instantiate a EnsSsConfig object, which holds all the necessary settings from the
        # config file that represents the BasePlot object (EnsSs).
        self.config_obj = EnsSsConfig(self.parameters)

        self.logger = self.config_obj.logger
        self.logger.info(f"Start Ens_ss plot: {datetime.now()}")

        # Check that we have all the necessary settings for each series
        self.config_obj.config_consistency_check()

        # if plotting points, add show_legend True in between each show legend value
        # do this after the consistency check to ensure the number of
        # show_legend values matches the number of series before adding to the list
        if self.config_obj.ensss_pts_disp:
            self.config_obj.show_legend = [val for item in self.config_obj.show_legend for val in (item, 1)]

        # Read in input data, location specified in config file
        self.logger.info(f"Begin reading input data: {datetime.now()}")
        self.input_df = self._read_input_data()

        # Apply event equalization, if requested
        if self.config_obj.use_ee is True:
            self.logger.info(f"Performing event equalization: {datetime.now()}")
            self._perform_event_equalization()
            self.logger.info(f"Finished event equalization: {datetime.now()}")

        # Create a list of series objects.
        # Each series object contains all the necessary information for plotting,
        # such as line color, marker symbol,
        # line width, and criteria needed to subset the input dataframe.
        self.series_list = self._create_series(self.input_df)

        self._create_figure()

    def _perform_event_equalization(self):
        """ Initialises EE criteria and performs EE

                Args:
        """
        fix_vals_permuted_list = []
        fix_vals_keys = []
        # use provided fixed parameters for the initial criteria
        if len(self.config_obj.fixed_vars_vals_input) > 0:
            for key in self.config_obj.fixed_vars_vals_input:
                vals_permuted = list(itertools.product(*self.config_obj.fixed_vars_vals_input[key].values()))
                vals_permuted_list = [item for sublist in vals_permuted for item in sublist]
                fix_vals_permuted_list.append(vals_permuted_list)

            fix_vals_keys = list(self.config_obj.fixed_vars_vals_input.keys())

        # add bin_n
        fix_vals_keys.append('bin_n')
        unique_bin_n = self.input_df['bin_n'].unique().tolist()
        fix_vals_permuted_list.append(unique_bin_n)
        if len(self.config_obj.series_val_names) > 0:
            input_df_ee = None
            all_fields_values_orig = self.config_obj.get_config_value('series_val_1').copy()
            all_fields_values = {}
            for field in reversed(list(all_fields_values_orig.keys())):
                all_fields_values[field] = all_fields_values_orig.get(field)

            for field_name, field_value in all_fields_values.items():
                all_filters = []
                for val in field_value:
                    filter_list = [val]
                    for i, filter_val in enumerate(filter_list):
                        if utils.is_string_integer(filter_val):
                            filter_list[i] = int(filter_val)
                        elif utils.is_string_strictly_float(filter_val):
                            filter_list[i] = float(filter_val)

                    all_filters.append((self.input_df[field_name].isin(filter_list)))

                # use numpy to select the rows where any record evaluates to True
                mask = np.array(all_filters).all(axis=0)
                series_data_for_ee = self.input_df.loc[mask]
                series_data_after_ee = \
                    event_equalize(series_data_for_ee, "fcst_valid_beg",
                                   self.config_obj.get_config_value('series_val_1'),
                                   fix_vals_keys,
                                   fix_vals_permuted_list, True,
                                   False)
                if input_df_ee is None:
                    input_df_ee = series_data_after_ee
                else:
                    input_df_ee = [input_df_ee, series_data_after_ee]

            self.input_df = input_df_ee

    def __repr__(self):
        """ Implement repr which can be useful for debugging this
            class.
        """

        return f'EnsSs({self.parameters!r})'

    def _read_input_data(self):
        """
            Read the input data file
            and store as a pandas dataframe so we can subset the
            data to represent each of the series defined by the
            series_val permutations.

            Args:

            Returns:

        """
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
        for i, name in enumerate(self.config_obj.get_series_y(1)):
            series_obj = EnsSsSeries(self.config_obj, i, input_data, series_list, name)
            series_list.append(series_obj)
            if self.config_obj.ensss_pts_disp:
                series_list.append(series_obj)

        # reorder series
        series_list = self.config_obj.create_list_by_series_ordering(series_list)

        self.logger.info(f"Finished creating series objects: {datetime.now()}")

        return series_list

    def _create_figure(self):
        """
        Create a Ensemble spread-skill plot from defaults and custom parameters
        """

        self.logger.info(f"Begin creating the figure: {datetime.now()}")

        # create and draw the plot
        _, ax = plt.subplots(figsize=(self.config_obj.plot_width, self.config_obj.plot_height))

        wts_size_styles = self.get_weights_size_styles()

        self._add_title(ax, wts_size_styles['title'])
        self._add_caption(plt, wts_size_styles['caption'])

        ax_y2 = None
        if self.config_obj.ensss_pts_disp:
            ax_y2 = self._add_y2axis(ax, wts_size_styles['y2lab'])

            # format large numbers like 3 million as 3M
            ax_y2.yaxis.set_major_formatter(ticker.EngFormatter())

        handles_and_labels = self._add_series(ax, ax_y2)

        self._add_xaxis(ax, wts_size_styles['xlab'])
        self._add_yaxis(ax, wts_size_styles['ylab'])

        self._add_legend(ax, handles_and_labels)

        self._add_custom_lines(ax)

        plt.tight_layout()

        self.logger.info(f"Finished creating the figure: {datetime.now()}")

    def _add_custom_lines(self, ax):
        # add custom lines if lines are defined in config
        if len(self.series_list) > 0:
            self._add_lines(ax, self.config_obj)

    def _add_series(self, ax, ax2):
        handles_and_labels = []
        i = 0
        counter = 1
        if self.config_obj.ensss_pts_disp:
            counter = 2

        # for series in self.series_list:
        for idx, series in enumerate(self.series_list):
            if not series.plot_disp:
                continue

            is_points_plot = self.config_obj.ensss_pts_disp and idx % 2 == 1
            plot_ax = ax2 if is_points_plot else ax
            handle = self._draw_series(plot_ax, series, idx, is_points_plot)
            handles_and_labels.append((handle, handle.get_label()))

        return handles_and_labels

    def _draw_series(self, ax, series: EnsSsSeries, index: int, is_points_plot: bool) -> None:
        """
        Draws the formatted line on the plot

        :param series: EnsSs series object with data and parameters
        """
        self.logger.info(f"Begin drawing the series on the plot: {datetime.now()}")

        # add the plot
        x = series.series_points['spread_skill']
        y = series.series_points['pts'] if is_points_plot else series.series_points['mse']

        # set arguments for the plot
        plot_args = self._get_plot_args(index)
        plot_obj = ax.plot(x, y, **plot_args)

        self.logger.info(f"Finished drawing the series on the plot: {datetime.now()}")
        return plot_obj[0]

    def _get_plot_args(self, idx):
        plot_mode = self.config_obj.mode[idx]
        marker = self.config_obj.marker_list[idx] if 'markers' in plot_mode else None
        line_style = self.config_obj.linestyles_list[idx] if 'lines' in plot_mode else 'None'

        plot_args = {
            'marker': marker,
            'markersize': self.config_obj.marker_size[idx],
            'label': self.config_obj.user_legends[idx],
            'color': self.config_obj.colors_list[idx],
            'linewidth': self.config_obj.linewidth_list[idx],
            'linestyle': line_style,
        }
        if self.config_obj.marker_open_list[idx]:
            plot_args['markerfacecolor'] = 'none'
            plot_args['markeredgecolor'] = self.config_obj.colors_list[idx]

        return plot_args

    def write_output_file(self) -> None:
        """
        Formats y1 and y2 series point data to the 2-dim arrays and saves them to the files
        """

        # if points_path parameter doesn't exist,
        # open file, name it based on the stat_input config setting,
        # (the input data file) except replace the .data
        # extension with .points1 extension
        # otherwise use points_path path
        if not self.config_obj.dump_points_1:
            return

        match = re.match(r'(.*)(.data)', self.config_obj.parameters['stat_input'])
        if not match:
            return

        i = 0
        counter = 1
        if self.config_obj.ensss_pts_disp is True:
            counter = 2

        filename = match.group(1)
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

        with open(filename, 'w') as file:
            while i < len(self.series_list):
                file.writelines(
                    map("{}\t{}\n".format,
                        [round(num, 6) for num in self.series_list[i].series_points['spread_skill']],
                        [round(num, 6) for num in self.series_list[i].series_points['mse']]))
                i = i + counter
            # print PTS values
            if self.config_obj.ensss_pts_disp is True:
                i = 0
                file.write('#PTS\n')
                while i < len(self.series_list):
                    file.writelines(
                        map("{}\t{}\n".format,
                            [round(num, 6) for num in self.series_list[i].series_points['spread_skill']],
                            [round(num, 6) for num in self.series_list[i].series_points['pts']])
                    )
                    i = i + counter


def main(config_filename=None):
    """
            Generates a sample, default, Plotly Ensemble spread-skill plot using the
            default and custom config files on sample data found in this directory.
            The location of the input data is defined in either the default or
            custom config file.
            Args:
                @param config_filename: default is None, the name of the custom config file to apply
        """
    util.make_plot(config_filename, EnsSs)


if __name__ == "__main__":
    main()
