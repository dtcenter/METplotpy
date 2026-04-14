# ============================*
# ** Copyright UCAR (c) 2022
# ** University Corporation for Atmospheric Research (UCAR)
# ** National Center for Atmospheric Research (NCAR)
# ** Research Applications Lab (RAL)
# ** P.O.Box 3000, Boulder, Colorado, 80307-3000, USA
# ============================*


"""
Class Name: revision_series.py
 """

import os
import re
from datetime import datetime

from typing import Union

from matplotlib import pyplot as plt

from metplotpy.plots.base_plot import BasePlot

from metplotpy.plots.line.line import Line
from metplotpy.plots import util as util
from metplotpy.plots.series import Series

import metcalcpy.util.utils as calc_util
from metplotpy.plots.revision_series.revision_series_config import RevisionSeriesConfig
from metplotpy.plots.revision_series.revision_series_series import RevisionSeriesSeries


class RevisionSeries(Line):
    """  Generates a Plotly Revision Series plot for 1 or more traces
         where each dot is represented by a text point data file.
    """
    LONG_NAME = 'revision series'
    defaults_name = 'revision_series_defaults.yaml'

    def __init__(self, parameters: dict) -> None:
        """ Creates a Revision Series plot consisting of one or more traces, based on
            settings indicated by parameters.

            Args:
            @param parameters: dictionary containing user defined parameters

        """

        # init common layout
        BasePlot.__init__(self, parameters, self.defaults_name)

        self.allow_secondary_y = False

        # instantiate a RevisionSeriesConfig object, which holds all the necessary settings from the
        # config file that represents the BasePlot object (RevisionSeries).
        self.config_obj = RevisionSeriesConfig(self.parameters)

        self.logger = self.config_obj.logger
        self.logger.info('Begin revision series plotting.')

        # Check that we have all the necessary settings for each series
        self.config_obj.config_consistency_check()

        # Read in input data, location specified in config file
        self.input_df = self._read_input_data()

        # Apply event equalization, if requested
        if self.config_obj.use_ee is True:
            self.input_df = calc_util.perform_event_equalization(self.parameters, self.input_df)

        self.series_list = self._create_series(self.input_df)

        self._create_figure()

    def __repr__(self):
        """ Implement repr which can be useful for debugging this
            class.
        """

        return f'RevisionSeries({self.parameters!r})'

    def _create_series(self, input_data):
        """
           Generate all the series objects that are to be displayed as specified by the plot_disp
           setting in the config file.  The points are all ordered by datetime.  Each series object
           is represented by a trace in the diagram, so they also contain information
           for marker colors, style, and other plot-related/
           appearance-related settings (which were defined in the config file).

           Args:
               input_data:  The input data in the form of a Pandas dataframe.
                            This data will be subset to reflect the series data of interest.

           Returns:
               a list of series objects that are to be displayed


        """
        series_list = []

        # add series for y1 axis
        for i, name in enumerate(self.config_obj.get_series_y()):
            series_obj = RevisionSeriesSeries(self.config_obj, i, input_data, series_list, name)
            series_list.append(series_obj)
        # reorder series
        series_list = self.config_obj.create_list_by_series_ordering(series_list)

        return series_list

    def _create_figure(self):
        """
        Create a Revision Series plot from defaults and custom parameters
        """

        self.logger.info(f"Begin creating the {self.LONG_NAME} figure: {datetime.now()}")
        # create and draw the plot
        _, ax = plt.subplots(figsize=(self.config_obj.plot_width, self.config_obj.plot_height))

        wts_size_styles = self.get_weights_size_styles()

        self._add_title(ax, wts_size_styles['title'])
        self._add_caption(plt, wts_size_styles['caption'])

        x_points_index = self._add_series(ax)

        xlab_style = wts_size_styles['xlab'] if not self.config_obj.vert_plot else wts_size_styles['ylab']
        ylab_style = wts_size_styles['ylab'] if not self.config_obj.vert_plot else wts_size_styles['xlab']
        self._add_xaxis(ax, xlab_style)
        self._add_yaxis(ax, ylab_style)

        self._add_legend(ax)

        # add custom lines
        self._add_lines(ax, self.config_obj, x_points_index)

        plt.tight_layout()

        self.logger.info(f"Finish creating {self.LONG_NAME} figure: {datetime.now()}")

    def _add_series(self, ax, ax2=None):
        x_points_index = []
        ordered_indy_label = []
        if len(self.series_list) > 0:
            x_points_index = list(range(0, len(self.series_list[0].series_points['points'])))
            ordered_indy_label = self.series_list[0].series_points['points']['fcst_lead'].tolist()

        self.config_obj.indy_label = ordered_indy_label
        self.config_obj.indy_vals = x_points_index

        # add series points
        for series in self.series_list:

            # Don't generate the plot for this series if
            # it isn't requested (as set in the config file)
            if not series.plot_disp:
                continue

            x_points_index_adj = x_points_index
            if self.config_obj.indy_stagger:
                x_points_index_adj, _ = self._get_x_locs_and_width(x_points_index, series.idx,
                                                                   stagger_scale=0.1)
            self._draw_series(ax, None, series, x_points_index_adj)

        return x_points_index

    def _draw_series(self, ax, ax2, series: Series, x_points_adj: Union[list, None] = None) -> None:
        """
        Draws the formatted series points on the plot

        :param series: RevisionSeries  object with data and parameters
        :param x_points_adj: values for adjusting x-values position
        """

        self.logger.info(f"Draw the formatted series: {datetime.now()}")
        ax.plot(
            x_points_adj, series.series_points['points']['stat_value'].tolist(),
            label=series.user_legends,
            # marker style
            marker=self.config_obj.marker_list[series.idx],
            markersize=self.config_obj.marker_size[series.idx],
            markeredgecolor=self.config_obj.colors_list[series.idx],
            markerfacecolor=self.config_obj.colors_list[series.idx],
            # no lines
            linestyle='None',
        )
        self.logger.info(f"Finished drawing series: {datetime.now()}")

    def write_output_file(self) -> None:
        """
        Formats y1 series point data and saves them to the files
        """
        self.logger.info("Write output file")
        # if points_path parameter doesn't exist,
        # open file, name it based on the stat_input config setting,
        # (the input data file) except replace the .data
        # extension with .points1 extension
        # otherwise use points_path path
        match = re.match(r'(.*)(.data)', self.config_obj.parameters['stat_input'])
        if self.config_obj.dump_points_1 is True and match:
            filename = match.group(1)
            if self.config_obj.points_path is not None:
                # get the file name
                path = filename.split(os.path.sep)
                if len(path) > 0:
                    filename = path[-1]
                else:
                    filename = '.' + os.path.sep
                filename = self.config_obj.points_path + os.path.sep + filename
            else:
                filename = 'points'

            filename = filename + '.points1'
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            with open(filename, 'w') as file:
                for series in self.series_list:
                    file.writelines(
                        "revision_run={}, auto_cor_r={},auto_cor_p={}\n".format(
                            round(series.series_points['revision_run'], 6),
                            round(series.series_points['auto_cor_r'], 6),
                            round(series.series_points['auto_cor_p'], 6)))
                    file.writelines(
                        map("{}\t".format,
                            [round(num, 6) for num in series.series_points['points']['stat_value'].tolist()])
                    )
                    file.writelines('\n\n')
            file.close()


def main(config_filename=None):
    """
            Generates a sample, default, RevisionSeries plot using the
            default and custom config files on sample data found in this directory.
            The location of the input data is defined in either the default or
            custom config file.
            Args:
                @param config_filename: default is None, the name of the custom config file to apply
        """
    util.make_plot(config_filename, RevisionSeries)


if __name__ == "__main__":
    main()
