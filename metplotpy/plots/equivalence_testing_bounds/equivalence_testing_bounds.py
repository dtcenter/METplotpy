"""
Class Name: equivalence_testing_bounds.py
 """
__author__ = 'Tatiana Burek'
__email__ = 'met_help@ucar.edu'

import os
import re
import csv

import yaml
import pandas as pd

import plotly.graph_objects as go
from plotly.subplots import make_subplots
from plotly.graph_objects import Figure

from plots.constants import PLOTLY_AXIS_LINE_COLOR, PLOTLY_AXIS_LINE_WIDTH, PLOTLY_PAPER_BGCOOR
from plots.equivalence_testing_bounds.equivalence_testing_bounds_series \
    import EquivalenceTestingBoundsSeries
from plots.line.line_config import LineConfig
from plots.line.line_series import LineSeries
from plots.met_plot import BasePlot
import plots.util as util

import metcalcpy.util.utils as calc_util


class EquivalenceTestingBounds(BasePlot):
    """  Generates a Plotly Equivalence Testing Bounds plot .
    """

    def __init__(self, parameters: dict) -> None:
        """ Creates a Plotly Equivalence Testing Bounds plot, based on
            settings indicated by parameters.

            Args:
            @param parameters: dictionary containing user defined parameters

        """

        # init common layout
        super().__init__(parameters, "equivalence_testing_bounds_defaults.yaml")

        # instantiate a LineConfig object, which holds all the necessary settings from the
        # config file that represents the BasePlot object (EquivalenceTestingBounds).
        self.config_obj = LineConfig(self.parameters)

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
        # the methods in met_plot.py (BasePlot class methods) to
        # create binary versions of the plot.
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

        # add series for y1 axis
        num_series_y1 = len(self.config_obj.get_series_y(1))
        for i, name in enumerate(self.config_obj.get_series_y(1)):
            series_obj = EquivalenceTestingBoundsSeries(self.config_obj, i, input_data, series_list, name)
            # we don't need to display the regular series - set disp to false
            series_obj.plot_disp = False
            series_list.append(series_obj)

        # add series for y2 axis
        num_series_y2 = len(self.config_obj.get_series_y(2))
        for i, name in enumerate(self.config_obj.get_series_y(2)):
            series_obj = EquivalenceTestingBoundsSeries(self.config_obj, num_series_y1 + i,
                                                        input_data, series_list, name, 2)
            # we don't need to display the regular series - set disp to false
            series_obj.plot_disp = False
            series_list.append(series_obj)

        # add derived for y1 axis
        num_series_y1_d = len(self.config_obj.get_config_value('derived_series_1'))
        for i, name in enumerate(self.config_obj.get_config_value('derived_series_1')):
            # add only ETB curves
            if name[2] == "ETB":
                series_obj = EquivalenceTestingBoundsSeries(self.config_obj, num_series_y1 + num_series_y2 + i,
                                                            input_data, series_list, name)
                series_list.append(series_obj)

        # add derived for y2 axis
        for i, name in enumerate(self.config_obj.get_config_value('derived_series_2')):
            if name[2] == "ETB":
                # add only ETB curves
                series_obj = EquivalenceTestingBoundsSeries(self.config_obj,
                                                            num_series_y1 + num_series_y2 + num_series_y1_d + i,
                                                            input_data, series_list, name, 2)
                series_list.append(series_obj)

        # reorder series
        series_list = self.config_obj.create_list_by_series_ordering(series_list)

        return series_list

    def _create_figure(self):
        """
        Create a Equivalence Testing Bounds plot from defaults and custom parameters
        """
        # create and draw the plot
        self.figure = self._create_layout()
        self._add_xaxis()
        self._add_yaxis()
        self._add_y2axis()
        self._add_legend()

        # add series lines
        ind = 0
        for series in self.series_list:

            # Don't generate the plot for this series if
            # it isn't requested (as set in the config file)
            if series.plot_disp:
                self._draw_series(series, ind)
                ind = ind + 1

    def _draw_series(self, series: LineSeries, ind: int) -> None:
        """
        Draws the formatted ETB line on the plot

        :param series: EquivalenceTestingBounds series object with data and parameters
        :param x_points_index_adj: values for adjusting x-values position
        """

        ci_tost_up = series.series_points['ci_tost'][1]
        ci_tost_lo = series.series_points['ci_tost'][0]
        dif = series.series_points['dif']
        # add the plot
        self.figure.add_trace(
            go.Scatter(x=[dif],
                       y=[ind],
                       showlegend=True,
                       mode=self.config_obj.mode[series.idx],
                       textposition="top right",
                       name=self.config_obj.user_legends[series.idx],
                       connectgaps=self.config_obj.con_series[series.idx] == 1,
                       line={'color': self.config_obj.colors_list[series.idx],
                             'width': self.config_obj.linewidth_list[series.idx],
                             'dash': self.config_obj.linestyles_list[series.idx]},
                       marker_symbol=self.config_obj.marker_list[series.idx],
                       marker_color=self.config_obj.colors_list[series.idx],
                       marker_line_color=self.config_obj.colors_list[series.idx],
                       marker_size=self.config_obj.marker_size[series.idx],
                       error_x={'type': 'data',
                                'symmetric': False,
                                'array': [ci_tost_up - dif],
                                'arrayminus': [dif - ci_tost_lo],
                                'visible': True,
                                'thickness': self.config_obj.linewidth_list[series.idx],
                                'width': 0
                                }
                       ),
            secondary_y=series.y_axis != 1
        )
        # add bounds lines
        self.figure.add_shape(type="line",
                              x0=series.series_points['eqbound'][0],
                              y0=0,
                              x1=series.series_points['eqbound'][0],
                              y1=1,
                              yref='paper',
                              xref='x',
                              line={'color': self.config_obj.colors_list[series.idx],
                                    'width': 1,
                                    'dash': 'dash'
                                    }
                              )

        self.figure.add_shape(type="line",
                              x0=series.series_points['eqbound'][1],
                              y0=0,
                              x1=series.series_points['eqbound'][1],
                              y1=1,
                              yref='paper',
                              xref='x',
                              line={'color': self.config_obj.colors_list[series.idx],
                                    'width': 1,
                                    'dash': 'dash'
                                    }
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
                                 showgrid=False,
                                 zeroline=False,
                                 ticks="",
                                 gridwidth=self.config_obj.parameters['grid_lwd'],
                                 gridcolor=self.config_obj.blended_grid_col,
                                 automargin=True,
                                 title_font={
                                     'size': self.config_obj.y_title_font_size
                                 },
                                 title_standoff=abs(self.config_obj.parameters['ylab_offset']) + 15,
                                 tickangle=self.config_obj.y_tickangle,
                                 tickfont={'size': self.config_obj.y_tickfont_size},
                                 showticklabels=False
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
                                     tickfont={'size': self.config_obj.y2_tickfont_size}
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
                                          }
                                          })

    def _add_x2axis(self, n_stats) -> None:
        """
        Creates x2axis based on the properties from the config file
        and attaches it to the initial Figure

        :param n_stats: - labels for the axis
        """
        if self.config_obj.show_nstats:
            x_points_index = list(range(0, len(n_stats)))
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
                                              'tickvals': x_points_index,
                                              'ticktext': n_stats,
                                              'tickangle': self.config_obj.x2_tickangle,
                                              'tickfont': {
                                                  'size': self.config_obj.x2_tickfont_size
                                              },
                                              'scaleanchor': 'x'
                                              }
                                      )

            # need to add an invisible line with all values = None
            self.figure.add_trace(
                go.Scatter(y=[None] * len(x_points_index), x=x_points_index,
                           xaxis='x2', showlegend=False)
            )

    def remove_file(self):
        """
           Removes previously made image file .  Invoked by the parent class before self.output_file
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
        Is needed - creates and saves the html representation of the plot WITHOUT Plotly.js
        """
        if self.config_obj.create_html is True:
            # construct the fle name from plot_filename
            name_arr = self.get_config_value('plot_filename').split('.')
            html_name = name_arr[0] + ".html"

            # save html
            self.figure.write_html(html_name, include_plotlyjs=False)

    def write_output_file(self) -> None:
        """
        Formats y1 and y2 series point data to the 2-dim arrays and saves them to the files
        """

        # Open file, name it based on the stat_input config setting,
        # (the input data file) except replace the .data
        # extension with .points1 extension

        ci_tost_df = pd.DataFrame(columns=['ci_tost_lo', 'diff', 'ci_tost_hi'],
                                  index=range(0, len(self.config_obj.get_config_value('derived_series_1')) +
                                              len(self.config_obj.get_config_value('derived_series_2'))))
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

        # create a file name from stat_input parameter
        match = re.match(r'(.*)(.data)', self.config_obj.parameters['stat_input'])
        if match:
            filename_only = match.group(1)
        else:
            filename_only = 'points'

        # save points
        if self.config_obj.dump_points_1 is True:
            self._save_points(ci_tost_df.values.tolist(), filename_only + ".points1")

    @staticmethod
    def _save_points(points: list, output_file: str) -> None:
        """
        Saves array of points to the file. Ir replaces all None values to N/A and format floats
        :param points: 2-dimensional array. The 1st dimension is the number of x-axis points
        The 2nd - is the all y-points for a single  x-axis points. Each y-points has 3 numbers:
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

    # Retrieve the contents of the custom config file to over-ride
    # or augment settings defined by the default config file.
    # with open("./custom_line_plot.yaml", 'r') as stream:
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
        plot = EquivalenceTestingBounds(docs)
        plot.save_to_file()
        #plot.show_in_browser()
        plot.write_html()
        plot.write_output_file()
    except ValueError as val_er:
        print(val_er)


if __name__ == "__main__":
    main()
