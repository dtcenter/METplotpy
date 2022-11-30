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
from typing import Union

import yaml
import numpy as np

import plotly.graph_objects as go

from metplotpy.plots.constants import PLOTLY_AXIS_LINE_COLOR, PLOTLY_AXIS_LINE_WIDTH
from metplotpy.plots.base_plot import BasePlot

from metplotpy.plots.line.line import Line
from metplotpy.plots import util
from metplotpy.plots.series import Series

import metcalcpy.util.utils as calc_util
from metplotpy.plots.revision_series.revision_series_config import RevisionSeriesConfig
from metplotpy.plots.revision_series.revision_series_series import RevisionSeriesSeries


class RevisionSeries(Line):
    """  Generates a Plotly Revision Series plot for 1 or more traces
         where each dot is represented by a text point data file.
    """

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

        # Check that we have all the necessary settings for each series
        is_config_consistent = self.config_obj._config_consistency_check()
        if not is_config_consistent:
            raise ValueError("The number of series defined by series_val_1 is"
                             " inconsistent with the number of settings"
                             " required for describing each series. Please check"
                             " the number of your configuration file's plot_i,"
                             " plot_disp, series_order, user_legend,"
                             " colors, and series_symbols settings.")

        # Read in input data, location specified in config file
        self.input_df = self._read_input_data()

        # Apply event equalization, if requested
        if self.config_obj.use_ee is True:
            self.input_df = calc_util.perform_event_equalization(self.parameters, self.input_df)

        # Create a list of series objects.
        # Each series object contains all the necessary information for plotting,
        # such as color, marker symbol,
        # line width, and criteria needed to subset the input dataframe.
        self.series_list = self._create_series(self.input_df)

        # create figure
        # pylint:disable=assignment-from-no-return
        # Need to have a self.figure that we can pass along to
        # the methods in base_plot.py (BasePlot class methods) to
        # create binary versions of the plot.
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
        # create and draw the plot
        self.figure = self._create_layout()
        self._add_xaxis()
        self._add_yaxis()
        self._add_legend()

        # calculate stag adjustments
        stag_adjustments = self._calc_stag_adjustments()
        if len(self.series_list) > 0:
            x_points_index = list(range(0, len(self.series_list[0].series_points['points'])))
            ordered_indy_label = self.series_list[0].series_points['points']['fcst_lead'].tolist()
            self.figure.update_layout(
                xaxis={
                    'tickmode': 'array',
                    'tickvals': x_points_index,
                    'ticktext': ordered_indy_label,
                    'tickangle': -90
                }
            )

        else:
            x_points_index = []

        # add series points
        for series in self.series_list:

            # Don't generate the plot for this series if
            # it isn't requested (as set in the config file)
            if series.plot_disp:

                # apply staggering offset if applicable
                if stag_adjustments[series.idx] == 0:
                    x_points_index_adj = x_points_index
                else:
                    x_points_index_adj = x_points_index + stag_adjustments[series.idx]

                self._draw_series(series, x_points_index_adj)

        # add custom lines
        self._add_lines(self.config_obj, x_points_index)

        # apply y axis limits
        self._yaxis_limits()

    def _draw_series(self, series: Series, x_points_index_adj: Union[list, None] = None) -> None:
        """
        Draws the formatted series points on the plot

        :param series: RevisionSeries  object with data and parameters
        :param x_points_index_adj: values for adjusting x-values position
        """

        y_points = series.series_points['points']['stat_value'].tolist()

        # add the plot
        self.figure.add_trace(
            go.Scatter(x=x_points_index_adj,
                       y=y_points,
                       showlegend=True,
                       mode='markers',
                       textposition="top right",
                       name=series.user_legends,
                       marker_symbol=self.config_obj.marker_list[series.idx],
                       marker_color=self.config_obj.colors_list[series.idx],
                       marker_line_color=self.config_obj.colors_list[series.idx],
                       marker_size=self.config_obj.marker_size[series.idx],
                       ),
            secondary_y=False
        )

    def _add_xaxis(self) -> None:
        """
        Configures and adds x-axis to the plot
        """
        self.figure.update_xaxes(title_text=self.config_obj.xaxis,
                                 linecolor=PLOTLY_AXIS_LINE_COLOR,
                                 linewidth=PLOTLY_AXIS_LINE_WIDTH,
                                 showgrid=self.config_obj.grid_on,
                                 ticks="inside",
                                 zeroline=False,
                                 gridwidth=self.config_obj.parameters['grid_lwd'],
                                 gridcolor=self.config_obj.blended_grid_col,
                                 automargin=True,
                                 title_font={
                                     'size': self.config_obj.x_title_font_size
                                 },
                                 title_standoff=abs(self.config_obj.parameters['xlab_offset']),
                                 tickangle=self.config_obj.x_tickangle,
                                 tickfont={'size': self.config_obj.x_tickfont_size}
                                 )

    def _calc_stag_adjustments(self) -> list:
        """
        Calculates the x-axis adjustment for each point if requested.
        It needed so the points  for each x-axis values don't be placed on top of each other

        :return: the list of the adjustment values
        """

        # get the total number of series
        num_stag = len(self.config_obj.all_series_y1)

        # init the result with 0
        stag_vals = [0] * num_stag

        # calculate staggering values
        if self.config_obj.indy_stagger is True:
            dbl_adj_scale = (len(self.config_obj.indy_vals) - 1) / 150
            stag_vals = np.linspace(-(num_stag / 2) * dbl_adj_scale,
                                    (num_stag / 2) * dbl_adj_scale,
                                    num_stag,
                                    True)
            stag_vals = stag_vals + dbl_adj_scale / 2
        return stag_vals

    def write_output_file(self) -> None:
        """
        Formats y1 series point data and saves them to the files
        """

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

    # Retrieve the contents of the custom config file to over-ride
    # or augment settings defined by the default config file.
    # with open("./revision_series_defaults.yaml", 'r') as stream:
    if not config_filename:
        config_file = util.read_config_from_command_line()
    else:
        config_file = config_filename
    with open(config_file, 'r') as stream:
        try:
            docs = yaml.load(stream, Loader=yaml.FullLoader)
        except yaml.YAMLError as exc:
            print(exc)

    try:
        plot = RevisionSeries(docs)
        plot.save_to_file()
        #plot.show_in_browser()
        plot.write_html()
        plot.write_output_file()
    except ValueError as val_er:
        print(val_er)


if __name__ == "__main__":
    main()
