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


import re
import os
from typing import Union
from operator import add
from itertools import chain
import yaml
import pandas as pd

import plotly.graph_objects as go
from plotly.subplots import make_subplots
from plotly.graph_objects import Figure

import metcalcpy.util.utils as calc_util

from metplotpy.plots.base_plot import BasePlot
from metplotpy.plots.box.box_config import BoxConfig
from metplotpy.plots.box.box_series import BoxSeries
from metplotpy.plots import util
from metplotpy.plots.constants import PLOTLY_AXIS_LINE_COLOR, PLOTLY_AXIS_LINE_WIDTH, PLOTLY_PAPER_BGCOOR


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

        # Check that we have all the necessary settings for each series
        is_config_consistent = self.config_obj._config_consistency_check()
        if not is_config_consistent:
            raise ValueError("The number of series defined by series_val_1/2 and derived curves is"
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
        # such as line color, marker symbol,
        # line width, and criteria needed to subset the input dataframe.
        self.series_list = self._create_series(self.input_df)

        # create figure
        # pylint:disable=assignment-from-no-return
        # Need to have a self.figure that we can pass along to
        # the methods in base_plot.py (BasePlot class methods) to
        # create binary versions of the plot.
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
        file = self.config_obj.parameters['stat_input']
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

        return series_list

    def _create_figure(self):
        """ Create a box plot from default and custom parameters"""

        self.figure = self._create_layout()
        self._add_xaxis()
        self._add_yaxis()
        self._add_y2axis()
        self._add_legend()

        # placeholder for the number of stats
        n_stats = [0] * len(self.config_obj.indy_vals)

        # placeholder for the min and max values for y-axis
        yaxis_min = None
        yaxis_max = None

        if self.config_obj.xaxis_reverse is True:
            self.series_list.reverse()

        for series in self.series_list:
            # Don't generate the plot for this series if
            # it isn't requested (as set in the config file)
            if series.plot_disp:
                # collect min-max if we need to sync axis
                if self.config_obj.sync_yaxes is True:
                    yaxis_min, yaxis_max = self._find_min_max(series, yaxis_min, yaxis_max)

                self._draw_series(series)

                # aggregate number of stats
                n_stats = list(map(add, n_stats, series.series_points['nstat']))

        # add custom lines
        if len(self.series_list) > 0:
            self._add_lines(
                self.config_obj,
                sorted(self.series_list[0].series_data[self.config_obj.indy_var].unique())
                )

        # apply y axis limits
        self._yaxis_limits()
        self._y2axis_limits()

        # sync axis
        self._sync_yaxis(yaxis_min, yaxis_max)

        # add x2 axis
        self._add_x2axis(n_stats)

        self.figure.update_layout(boxmode='group')

    def _draw_series(self, series: BoxSeries) -> None:
        """
        Draws the boxes on the plot

        :param series: Line series object with data and parameters
        """

        # defaults markers and colors for the regular box plot
        line_color = dict(color='rgb(0,0,0)')
        fillcolor = series.color
        marker_color = 'rgb(0,0,0)'
        marker_line_color = 'rgb(0,0,0)'
        marker_symbol = 'circle-open'

        # markers and colors for points only  plot
        if self.config_obj.box_pts:
            line_color = dict(color='rgba(0,0,0,0)')
            fillcolor = 'rgba(0,0,0,0)'
            marker_color = series.color
            marker_symbol = 'circle'
            marker_line_color = series.color

        # create a trace
        self.figure.add_trace(
            go.Box(x=series.series_data[self.config_obj.indy_var],
                   y=series.series_data['stat_value'],
                   notched=self.config_obj.box_notch,
                   line=line_color,
                   fillcolor=fillcolor,
                   name=series.user_legends,
                   showlegend=True,
                   # quartilemethod='linear', #"exclusive", "inclusive", or "linear"
                   boxmean=self.config_obj.box_avg,
                   boxpoints=self.config_obj.boxpoints,  # outliers, all, False
                   pointpos=0,
                   marker=dict(size=4,
                               color=marker_color,
                               line=dict(
                                   width=1,
                                   color=marker_line_color
                               ),
                               symbol=marker_symbol,
                               ),
                   jitter=0
                   ),
            secondary_y=series.y_axis != 1
        )

    @staticmethod
    def _find_min_max(series: BoxSeries, yaxis_min: Union[float, None],
                      yaxis_max: Union[float, None]) -> tuple:
        """
        Finds min and max value between provided min and max and y-axis CI values of this series
        if yaxis_min or yaxis_max is None - min/max value of the series is returned

        :param series: series to use for calculations
        :param yaxis_min: previously calculated min value
        :param yaxis_max: previously calculated max value
        :return: a tuple with calculated min/max
        """
        # calculate series upper and lower limits of CIs
        indexes = range(len(series.series_points['dbl_med']))
        upper_range = [series.series_points['dbl_med'][i] + series.series_points['dbl_up_ci'][i]
                       for i in indexes]
        low_range = [series.series_points['dbl_med'][i] - series.series_points['dbl_lo_ci'][i]
                     for i in indexes]
        # find min max
        if yaxis_min is None or yaxis_max is None:
            return min(low_range), max(upper_range)

        return min(chain([yaxis_min], low_range)), max(chain([yaxis_max], upper_range))

    def _yaxis_limits(self) -> None:
        """
        Apply limits on y2 axis if needed
        """
        if len(self.config_obj.parameters['ylim']) > 0:
            self.figure.update_layout(yaxis={'range': [self.config_obj.parameters['ylim'][0],
                                                       self.config_obj.parameters['ylim'][1]],
                                             'autorange': False})

    def _y2axis_limits(self) -> None:
        """
        Apply limits on y2 axis if needed
        """
        if len(self.config_obj.parameters['y2lim']) > 0:
            self.figure.update_layout(yaxis2={'range': [self.config_obj.parameters['y2lim'][0],
                                                        self.config_obj.parameters['y2lim'][1]],
                                              'autorange': False})

    def _create_layout(self) -> Figure:
        """
        Creates a new layout based on the properties from the config file
        including plots size, annotation and title

        :return: Figure object
        """
        # create annotation
        annotation = [
            {'text': util.apply_weight_style(self.config_obj.parameters['plot_caption'],
                                             self.config_obj.parameters['caption_weight']),
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
                                                 self.config_obj.parameters['title_weight']),
                 'font': {
                     'size': self.config_obj.title_font_size,
                 },
                 'y': self.config_obj.title_offset,
                 'x': self.config_obj.parameters['title_align'],
                 'xanchor': 'center',
                 'xref': 'paper'
                 }

        # create a layout and allow y2 axis
        fig = make_subplots(specs=[[{"secondary_y": True}]])

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
                'ticktext': self.config_obj.indy_label
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
                                 title_standoff=abs(self.config_obj.parameters['xlab_offset']),
                                 tickangle=self.config_obj.x_tickangle,
                                 tickfont={'size': self.config_obj.x_tickfont_size}
                                 )
        # reverse xaxis if needed
        if hasattr( self.config_obj, 'xaxis_reverse' ) and self.config_obj.xaxis_reverse is True:
            self.figure.update_xaxes(autorange="reversed")

    def _add_yaxis(self) -> None:
        """
        Configures and adds y-axis to the plot
        """
        self.figure.update_yaxes(title_text=
                                 util.apply_weight_style(self.config_obj.yaxis_1,
                                                         self.config_obj.parameters['ylab_weight']),
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
                                 title_standoff=abs(self.config_obj.parameters['ylab_offset']),
                                 tickangle=self.config_obj.y_tickangle,
                                 tickfont={'size': self.config_obj.y_tickfont_size},
                                 exponentformat='none'
                                 )

    def _add_y2axis(self) -> None:
        """
        Adds y2-axis if needed
        """
        if self.config_obj.parameters['list_stat_2']:
            self.figure.update_yaxes(title_text=
                                     util.apply_weight_style(self.config_obj.yaxis_2,
                                                             self.config_obj.parameters['y2lab_weight']),
                                     secondary_y=True,
                                     linecolor=PLOTLY_AXIS_LINE_COLOR,
                                     linewidth=PLOTLY_AXIS_LINE_WIDTH,
                                     showgrid=False,
                                     zeroline=False,
                                     ticks="inside",
                                     title_font={
                                         'size': self.config_obj.y2_title_font_size
                                     },
                                     title_standoff=abs(self.config_obj.parameters['y2lab_offset']),
                                     tickangle=self.config_obj.y2_tickangle,
                                     tickfont={'size': self.config_obj.y2_tickfont_size},
                                     exponentformat='none'
                                     )

    def _sync_yaxis(self, yaxis_min: Union[float, None], yaxis_max: Union[float, None]) -> None:
        """
        Forces y1 and y2 axes sync if needed by specifying the same limits on both axis.
        Use ylim property to determine the limits. If this value is not provided -
        use method parameters

        :param yaxis_min: min value or None
        :param yaxis_max: max value or None
        """
        if self.config_obj.sync_yaxes is True:
            if len(self.config_obj.parameters['ylim']) > 0:
                # use plot config parameter
                range_min = self.config_obj.parameters['ylim'][0]
                range_max = self.config_obj.parameters['ylim'][1]
            else:
                # use method parameter
                range_min = yaxis_min
                range_max = yaxis_max

            if range_min is not None and range_max is not None:
                # update y axis
                self.figure.update_layout(yaxis={'range': [range_min,
                                                           range_max],
                                                 'autorange': False})

                # update y2 axis
                self.figure.update_layout(yaxis2={'range': [range_min,
                                                            range_max],
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
                                                                          self.config_obj.parameters['x2lab_weight']
                                                                          ),
                                              'linecolor': PLOTLY_AXIS_LINE_COLOR,
                                              'linewidth': PLOTLY_AXIS_LINE_WIDTH,
                                              'overlaying': 'x',
                                              'side': 'top',
                                              'showgrid': False,
                                              'zeroline': False,
                                              'ticks': "inside",
                                              'title_font': {
                                                  'size': self.config_obj.x2_title_font_size
                                              },
                                              'title_standoff': abs(
                                                  self.config_obj.parameters['x2lab_offset']
                                              ),
                                              'tickmode': 'array',
                                              'tickvals': self.config_obj.indy_vals,
                                              'ticktext': n_stats,
                                              'tickangle': self.config_obj.x2_tickangle,
                                              'tickfont': {
                                                  'size': self.config_obj.x2_tickfont_size
                                              },
                                              'scaleanchor': 'x'
                                              }
                                      )
            # reverse x2axis if needed
            if self.config_obj.xaxis_reverse is True:
                self.figure.update_layout(xaxis2={'autorange':"reversed"})

            # need to add an invisible line with all values = None
            self.figure.add_trace(
                go.Scatter(y=[None] * len(self.config_obj.indy_vals), x=self.config_obj.indy_vals,
                           xaxis='x2', showlegend=False)
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
                                          'bordercolor': self.config_obj.legend_border_color,
                                          'borderwidth': self.config_obj.legend_border_width,
                                          'orientation': self.config_obj.legend_orientation,
                                          'font': {
                                              'size': self.config_obj.legend_size,
                                              'color': "black"
                                          },
                                          'traceorder': 'normal'
                                          })
        if hasattr( self.config_obj, 'xaxis_reverse' ) and self.config_obj.xaxis_reverse is True:
            self.figure.update_layout(legend={'traceorder':'reversed'})

    def write_html(self) -> None:
        """
        Is needed - creates and saves the html representation of the plot WITHOUT Plotly.js
        """
        # is_create = self.config_obj.create_html
        if self.config_obj.create_html is True:
            # construct the file name from plot_filename
            name_arr = self.get_config_value('plot_filename').split('.')
            name_arr[-1] = 'html'
            html_name = ".".join(name_arr)

            # save html
            self.figure.write_html(html_name, include_plotlyjs=False)

    def write_output_file(self) -> None:
        """
        Formats y1 and y2 series point data to the 2-dim arrays and saves them to the files
        """

        # open file, name it based on the stat_input config setting,
        # (the input data file) except replace the .data
        # extension with .points1 extension
        # otherwise use points_path path

        match = re.match(r'(.*)(.data)', self.config_obj.parameters['stat_input'])
        if self.config_obj.dump_points_1 is True or self.config_obj.dump_points_2 is True and match:
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
            if os.path.exists(filename):
                os.remove(filename)
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

                    file_object = open(filename, 'a')
                    file_object.write('\n')
                    file_object.write(' '.join([str(elem) for elem in series.series_name]) + ' ' + indy_val)
                    file_object.write('\n')
                    file_object.close()
                    quantile_data = data_for_indy['stat_value'].quantile([0, 0.25, 0.5, 0.75, 1]).iloc[::-1]
                    quantile_data.to_csv(filename, header=False, index=None, sep=' ', mode='a')
                    file_object.close()


def main(config_filename=None):
    """
        Generates a sample, default, box plot using a combination of
        default and custom config files on sample data found in this directory.
        The location of the input data is defined in either the default or
        custom config file.
        Args:
                @param config_filename: default is None, the name of the custom config file to apply
    """

    # Retrieve the contents of the custom config file to over-ride
    # or augment settings defined by the default config file.
    # with open("./custom_box.yaml", 'r') as stream:
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
        plot = Box(docs)
        plot.save_to_file()
        #plot.show_in_browser()
        plot.write_html()
        plot.write_output_file()
    except ValueError as ve:
        print(ve)


if __name__ == "__main__":
    main()
