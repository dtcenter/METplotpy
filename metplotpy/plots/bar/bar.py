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

import pandas as pd
import plotly.graph_objects as go
from plotly.graph_objects import Figure
from plotly.subplots import make_subplots

import metcalcpy.util.utils as calc_util
from metplotpy.plots import util
from metplotpy.plots.bar.bar_config import BarConfig
from metplotpy.plots.bar.bar_series import BarSeries
from metplotpy.plots.base_plot import BasePlot
from metplotpy.plots.constants import PLOTLY_AXIS_LINE_COLOR, PLOTLY_AXIS_LINE_WIDTH, \
    PLOTLY_PAPER_BGCOOR


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
        self.logger.info(f"Consistency checking of config settings for colors, "
                        f"legends, etc.")
        is_config_consistent = self.config_obj._config_consistency_check()
        if not is_config_consistent:
            value_error_msg = ("ValueError: The number of series defined by series_val_1 and "
                               "derived curves is inconsistent with the number of "
                               "settings required for describing each series. Please "
                               "check the number of your configuration file's "
                               "plot_i, plot_disp, series_order, user_legend, show_legend and "
                               "colors settings.")
            self.logger.error(value_error_msg)
            raise ValueError(value_error_msg)

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

        return series_list

    def _create_figure(self):
        """
        Create a bar plot from defaults and custom parameters
        """
        # create and draw the plot
        self.figure = self._create_layout()
        self._add_xaxis()
        self._add_yaxis()
        self._add_legend()

        # placeholder for the number of stats
        n_stats = [0] * len(self.config_obj.indy_vals)

        if self.config_obj.xaxis_reverse is True:
            self.series_list.reverse()

        # add series lines
        for series in self.series_list:

            # Don't generate the plot for this series if
            # it isn't requested (as set in the config file)
            if series.plot_disp:
                self._draw_series(series)

                # aggregate number of stats
                n_stats = list(map(add, n_stats, series.series_points['nstat']))

        # add custom lines
        if len(self.series_list) > 0:
            self._add_lines(
                self.config_obj,
                sorted(
                    self.series_list[0].series_data[self.config_obj.indy_var].unique())
            )

        # apply y axis limits
        self._yaxis_limits()

        # add x2 axis
        self._add_x2axis(n_stats)

    def _draw_series(self, series: BarSeries) -> None:
        """
        Draws the formatted Bar on the plot
        :param series: Bar series object with data and parameters
        """

        y_points = series.series_points['dbl_med']
        is_threshold, is_percent_threshold = util.is_threshold_value(
            series.series_data[self.config_obj.indy_var])

        # If there are any None types in the series_points['dbl_med'] list, then use the
        # indy_vals defined in the config file to ensure that the number of y_points
        # is the
        # same number of x_points.
        if None in y_points:
            x_points = self.config_obj.indy_vals
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

        # add the plot
        self.figure.add_trace(
            go.Bar(
                x=x_points,
                y=y_points,
                showlegend=self.config_obj.show_legend[series.idx] == 1,
                name=self.config_obj.user_legends[series.idx],
                marker_color=self.config_obj.colors_list[series.idx],
                marker_line_color=self.config_obj.colors_list[series.idx]
            )
        )

    def _create_layout(self) -> Figure:
        """
        Creates a new layout based on the properties from the config file
        including plots size, annotation and title

        :return: Figure object
        """
        # create annotation
        annotation = [
            {'text': util.apply_weight_style(self.config_obj.parameters['plot_caption'],
                                             self.config_obj.parameters[
                                                 'caption_weight']),
             'align': 'left',
             'showarrow': False,
             'xref': 'paper',
             'yref': 'paper',
             'x': self.config_obj.parameters['caption_align'],
             'y': self.config_obj.caption_offset,
             'font': {
                 'size': self.config_obj.caption_size,
                 'color': self.config_obj.parameters['caption_col']
             }
             }]
        # create title
        title = {'text': util.apply_weight_style(self.config_obj.title,
                                                 self.config_obj.parameters[
                                                     'title_weight']),
                 'font': {
                     'size': self.config_obj.title_font_size,
                 },
                 'y': self.config_obj.title_offset,
                 'x': self.config_obj.parameters['title_align'],
                 'xanchor': 'center',
                 'xref': 'paper'
                 }

        # create a layout
        fig = make_subplots(specs=[[{"secondary_y": False}]])

        # add size, annotation, title
        fig.update_layout(
            width=self.config_obj.plot_width,
            height=self.config_obj.plot_height,
            margin=self.config_obj.plot_margins,
            paper_bgcolor=PLOTLY_PAPER_BGCOOR,
            annotations=annotation,
            title=title,
            plot_bgcolor=PLOTLY_PAPER_BGCOOR
        )
        fig.update_layout(
            xaxis={
                'tickmode': 'array',
                'tickvals': self.config_obj.indy_vals,
                'ticktext': self.config_obj.indy_label,
            }
        )

        return fig

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
                                 title_standoff=abs(
                                     self.config_obj.parameters['xlab_offset']),
                                 tickangle=self.config_obj.x_tickangle,
                                 tickfont={'size': self.config_obj.x_tickfont_size},
                                 type='category'
                                 )
        # reverse xaxis if needed
        if self.config_obj.xaxis_reverse is True:
            self.figure.update_xaxes(autorange="reversed")

    def _add_yaxis(self) -> None:
        """
        Configures and adds y-axis to the plot
        """
        self.figure.update_yaxes(title_text=
                                 util.apply_weight_style(self.config_obj.yaxis_1,
                                                         self.config_obj.parameters[
                                                             'ylab_weight']),
                                 secondary_y=False,
                                 linecolor=PLOTLY_AXIS_LINE_COLOR,
                                 linewidth=PLOTLY_AXIS_LINE_WIDTH,
                                 showgrid=self.config_obj.grid_on,
                                 zeroline=False,
                                 ticks="inside",
                                 gridwidth=self.config_obj.parameters['grid_lwd'],
                                 gridcolor=self.config_obj.blended_grid_col,
                                 automargin=True,
                                 title_font={
                                     'size': self.config_obj.y_title_font_size
                                 },
                                 title_standoff=abs(
                                     self.config_obj.parameters['ylab_offset']),
                                 tickangle=self.config_obj.y_tickangle,
                                 tickfont={'size': self.config_obj.y_tickfont_size}
                                 )

    def _add_legend(self) -> None:
        """
        Creates a plot legend based on the properties from the config file
        and attaches it to the initial Figure
        """
        self.figure.update_layout(legend={'x': self.config_obj.bbox_x,
                                          'y': self.config_obj.bbox_y,
                                          'xanchor': 'center',
                                          'yanchor': 'top',
                                          'bordercolor':
                                              self.config_obj.legend_border_color,
                                          'borderwidth':
                                              self.config_obj.legend_border_width,
                                          'orientation':
                                              self.config_obj.legend_orientation,
                                          'font': {
                                              'size': self.config_obj.legend_size,
                                              'color': "black"
                                          }
                                          })

    def _yaxis_limits(self) -> None:
        """
        Apply limits on y axis if needed
        """
        if len(self.config_obj.parameters['ylim']) > 0:
            self.figure.update_layout(
                yaxis={'range': [self.config_obj.parameters['ylim'][0],
                                 self.config_obj.parameters['ylim'][1]],
                       'autorange': False})

    def _add_x2axis(self, n_stats) -> None:
        """
        Creates x2axis based on the properties from the config file
        and attaches it to the initial Figure

        :param n_stats: - labels for the axis
        """
        if self.config_obj.show_nstats:
            self.figure.update_layout(xaxis2={'title_text':
                                                  util.apply_weight_style('NStats',
                                                                          self.config_obj.parameters[
                                                                              'x2lab_weight']
                                                                          ),
                                              'linecolor': PLOTLY_AXIS_LINE_COLOR,
                                              'linewidth': PLOTLY_AXIS_LINE_WIDTH,
                                              'overlaying': 'x',
                                              'side': 'top',
                                              'showgrid': False,
                                              'zeroline': False,
                                              'ticks': "inside",
                                              'title_font': {
                                                  'size':
                                                      self.config_obj.x2_title_font_size
                                              },
                                              'title_standoff': abs(
                                                  self.config_obj.parameters[
                                                      'x2lab_offset']
                                              ),
                                              'tickmode': 'array',
                                              'tickvals': self.config_obj.indy_vals,
                                              'ticktext': n_stats,
                                              'tickangle': self.config_obj.x2_tickangle,
                                              'tickfont': {
                                                  'size':
                                                      self.config_obj.x2_tickfont_size
                                              },
                                              'scaleanchor': 'x'
                                              }
                                      )
            # reverse x2axis if needed
            if self.config_obj.xaxis_reverse is True:
                self.figure.update_layout(xaxis2={'autorange': "reversed"})

            # need to add an invisible line with all values = None
            self.figure.add_trace(
                go.Scatter(y=[None] * len(self.config_obj.indy_vals),
                           x=self.config_obj.indy_vals,
                           xaxis='x2', showlegend=False)
            )

    def remove_file(self):
        """
           Removes previously made image file .  Invoked by the parent class before
           self.output_file
           attribute can be created, but overridden here.
        """

        super().remove_file()
        self._remove_html()

    def _remove_html(self) -> None:
        """
        Removes previously made HTML file.
        """

        name_arr = self.get_config_value('plot_filename').split('.')
        html_name = name_arr[0] + ".html"
        # remove the old file if it exist
        if os.path.exists(html_name):
            os.remove(html_name)

    def write_html(self) -> None:
        """
        Is needed - creates and saves the html representation of the plot WITHOUT
        Plotly.js
        """
        if self.config_obj.create_html is True:
            # construct the file name from plot_filename
            name_arr = self.get_config_value('plot_filename').split('.')
            name_arr[-1] = 'html'
            html_name = ".".join(name_arr)

            # save html
            self.figure.write_html(html_name, include_plotlyjs=False)

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

            with open(filename, 'w') as f:
                for series in self.series_list:
                    f.write(f"{series.series_points['dbl_med']}\n")
            f.close()


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
