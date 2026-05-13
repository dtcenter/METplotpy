# ============================*
 # ** Copyright UCAR (c) 2022
 # ** University Corporation for Atmospheric Research (UCAR)
 # ** National Center for Atmospheric Research (NCAR)
 # ** Research Applications Lab (RAL)
 # ** P.O.Box 3000, Boulder, Colorado, 80307-3000, USA
 # ============================*
 
 
 
"""
Class Name: contour.py
 """
__author__ = 'Tatiana Burek'

import os
from datetime import datetime
import re
import csv

from typing import Union

import pandas as pd

from matplotlib import pyplot as plt
from matplotlib.colors import ListedColormap

from metplotpy.plots.base_plot import BasePlot
from metplotpy.plots import util
from metplotpy.plots.contour.contour_config import ContourConfig
from metplotpy.plots.contour.contour_series import ContourSeries
from metplotpy.plots.series import Series

import metcalcpy.util.utils as calc_util


class Contour(BasePlot):
    """Generates a contour plot"""

    defaults_name = 'contour_defaults.yaml'

    def __init__(self, parameters: dict) -> None:
        """ Creates a contour plot based on
            settings indicated by parameters.

            Args:
            @param parameters: dictionary containing user defined parameters

        """

        # init common layout
        super().__init__(parameters, self.defaults_name)

        self.allow_secondary_y = False

        # instantiate a ContourConfig object, which holds all the necessary settings from the
        # config file that represents the BasePlot object (Line).
        self.config_obj = ContourConfig(self.parameters)

        self.logger = self.config_obj.logger
        self.logger.info(f"Start contour plot: {datetime.now()}")

        # Check that we have all the necessary settings for each series
        self.config_obj.config_consistency_check()

        # Read in input data, location specified in config file
        self.logger.info(f"Begin reading input data: {datetime.now()}")
        self.input_df = self._read_input_data()

        # Apply event equalization, if requested

        if self.config_obj.use_ee is True:
            self.logger.info(f"Begin event equalization: {datetime.now()} ")
            self.input_df = calc_util.perform_event_equalization(self.parameters, self.input_df)
            self.logger.info(f"Event equalization complete: {datetime.now()}")

        self.series_list = self._create_series(self.input_df)

        self._create_figure()

    def __repr__(self):
        """Implement repr which can be useful for debugging this class."""

        return f'Countur({self.parameters!r})'

    def _read_input_data(self):
        """
            Read the input data file
            and store as a pandas dataframe.

            Args:

            Returns:

        """
        return pd.read_csv(self.config_obj.parameters['stat_input'], sep='\t',
                           header='infer', float_precision='round_trip')

    def _create_series(self, input_data):
        """
           Generate all the series objects that are to be displayed as specified by the plot_disp
           setting in the config file.  The points are all ordered by datetime.

           Args:
               input_data:  The input data in the form of a Pandas dataframe.
                            This data will be subset to reflect the series data of interest.

           Returns:
               a list of series objects that are to be displayed


        """
        series_list = []

        self.logger.info(f"Generating series objects: {datetime.now()}")
        # add series for y1 axis
        for i, name in enumerate(self.config_obj.get_series_y()):
            series_obj = ContourSeries(self.config_obj, i, input_data, series_list, name)
            series_list.append(series_obj)

        # reorder series
        series_list = self.config_obj.create_list_by_series_ordering(series_list)

        self.logger.info(f"Finished creating series objects: {datetime.now()}")
        return series_list

    def _create_figure(self):
        """
        Create a Contour plot from defaults and custom parameters
        """

        self.logger.info(f"Creating the figure: {datetime.now()}")
        # create and draw the plot
        _, ax = plt.subplots(figsize=(self.config_obj.plot_width, self.config_obj.plot_height))

        wts_size_styles = self.get_weights_size_styles()

        self._add_title(ax, wts_size_styles['title'])
        self._add_caption(plt, wts_size_styles['caption'])

        self._add_series(ax)

        xlab_style = wts_size_styles['xlab'] if not self.config_obj.vert_plot else wts_size_styles['ylab']
        ylab_style = wts_size_styles['ylab'] if not self.config_obj.vert_plot else wts_size_styles['xlab']
        self._add_xaxis(ax, xlab_style, grid_on=False)
        self._add_yaxis(ax, ylab_style, grid_on=False)

        plt.tight_layout()

        self.logger.info(f"Figure creating complete: {datetime.now()}")

    def _add_series(self, ax):

        # display only 5 tick labels on the x-axis if
        # - it is a date and
        # - the size of labels is more than 5 and
        # - user did not provide custom labels (the x values and labels array are the same)

        ordered_indy_label = self.config_obj.create_list_by_plot_val_ordering(self.config_obj.indy_label)
        ordered_indy_vals = self.config_obj.create_list_by_plot_val_ordering(self.config_obj.indy_vals)

        if (self.config_obj.indy_var in ['fcst_init_beg', 'fcst_valid_beg']
                and len(self.config_obj.indy_vals) > 5
                and ordered_indy_label == self.series_list[0].series_points['x']):
            step = int(len(self.config_obj.indy_vals) / 5)
            indices_to_keep = list(range(0, len(ordered_indy_label), step))
            ordered_indy_label = [ordered_indy_label[i] for i in indices_to_keep]

            # Use indices as positions if not numeric (e.g. for dates)
            try:
                [float(i) for i in ordered_indy_vals]
                ordered_indy_vals = [ordered_indy_vals[i] for i in indices_to_keep]
            except (ValueError, TypeError):
                ordered_indy_vals = indices_to_keep

        # add series points
        for series in self.series_list:

            # Don't generate the plot for this series if
            # it isn't requested (as set in the config file)
            if not series.plot_disp:
                continue

            self._draw_series(ax, series)

        self.config_obj.indy_label = ordered_indy_label
        self.config_obj.indy_vals = ordered_indy_vals

    def _draw_series(self, ax, series: Series) -> None:
        """
        Draws the data

        :param series: Contour series object with data and parameters
        """
        self.logger.info(f"Drawing the data: {datetime.now()}")
        line_width = self.config_obj.linewidth_list[series.idx]
        if not self.config_obj.add_contour_overlay:
            line_width = 0

        ylim = self.config_obj.parameters.get('ylim', [])
        z_range = {'vmin': ylim[0], 'vmax': ylim[1]} if len(ylim) > 0 else {'vmin': None,
                                                                            'vmax': None}

        # add filled contours
        contour_filled = ax.contourf(
            series.series_points['x'],
            series.series_points['y'],
            series.series_points['z'],
            levels=self.config_obj.contour_intervals,
            cmap=ListedColormap(self.config_obj.color_palette),
            **z_range
        )

        # add lines
        if line_width > 0:
            contour_lines = ax.contour(
                series.series_points['x'],
                series.series_points['y'],
                series.series_points['z'],
                levels=self.config_obj.contour_intervals,
                colors=self.config_obj.colors_list[series.idx],
                linewidths=line_width,
                linestyles=self.config_obj.linestyles_list[series.idx],
                **z_range
            )

            # add line labels
            ax.clabel(
                contour_lines,
                inline=True,
                fontsize=10,
                colors=self.config_obj.colors_list[series.idx]
            )

        # add color bar
        if self.config_obj.add_color_bar:
            plt.colorbar(contour_filled, ax=ax, ticks=contour_filled.levels)

        self.logger.info(f"Finished drawing data: {datetime.now()}")

    def write_output_file(self) -> None:
        """
        saves series points to the files
        """
        self.logger.info(f"Writing output file: {datetime.now()}")

        # Open file, name it based on the stat_input config setting,
        # (the input data file) except replace the .data
        # extension with .points1 extension
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

            with open(filename, 'w') as file:
                writer = csv.writer(file, delimiter='\t')
                for series in self.series_list:
                    writer.writerow(['X values:'])
                    writer.writerow(series.series_points['x'])
                    file.writelines('\n')
                    writer.writerow(['Y values:'])
                    writer.writerow(series.series_points['y'])
                    file.writelines('\n')
                    writer.writerow(['Z values (X,Y):'])
                    writer.writerows(series.series_points['z'])
                    file.writelines('\n')
                    file.writelines('\n')

        self.logger.info(f"Finished writing output file: {datetime.now()}")


def main(config_filename=None):
    """
            Generates a sample, default, Contour plot using the
            default and custom config files on sample data found in this directory.
            The location of the input data is defined in either the default or
            custom config file.
            Args:
                @param config_filename: default is None, the name of the custom config file to apply
        """
    util.make_plot(config_filename, Contour)


if __name__ == "__main__":
    main()
