"""
Class Name: reliability.py
 """
__author__ = 'Tatiana Burek'
__email__ = 'met_help@ucar.edu'

import os
import re
import csv
from typing import Union

import yaml
import numpy as np
import pandas as pd

import plotly.graph_objects as go
from plotly.subplots import make_subplots
from plotly.graph_objects import Figure

from plots.constants import PLOTLY_AXIS_LINE_COLOR, PLOTLY_AXIS_LINE_WIDTH, PLOTLY_PAPER_BGCOOR
from plots.base_plot import BasePlot
import plots.util as util
from plots.reliability_diagram.reliability_config import ReliabilityConfig
from plots.reliability_diagram.reliability_series import ReliabilitySeries


def abline(x_value: float, intercept: float, slope: float) -> float:
    """
    Calculates y coordinate based on x-value, intercept and slope
    :param x_value: x coordinate
    :param intercept:  intercept
    :param slope: slope
    :return: y value
    """
    return slope * x_value + intercept


class Reliability(BasePlot):
    """  Generates a Plotly line plot for 1 or more traces (lines)
         where each line is represented by a text point data file.
    """

    def __init__(self, parameters: dict) -> None:
        """ Creates a line plot consisting of one or more lines (traces), based on
            settings indicated by parameters.

            Args:
            @param parameters: dictionary containing user defined parameters

        """

        # init common layout
        super().__init__(parameters, "reliability_defaults.yaml")

        # instantiate a LineConfig object, which holds all the necessary settings from the
        # config file that represents the BasePlot object (Line).
        self.config_obj = ReliabilityConfig(self.parameters)

        # Check that we have all the necessary settings for each series
        is_config_consistent = self.config_obj._config_consistency_check()
        if not is_config_consistent:
            raise ValueError("The number of series defined by series_val_1 "
                             " inconsistent with the number of settings"
                             " required for describing each series. Please check"
                             " the number of your configuration file's plot_i,"
                             " plot_disp, series_order, user_legend,"
                             " colors, and series_symbols settings.")

        # Read in input data, location specified in config file
        self.input_df = self._read_input_data()

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

    def __repr__(self):
        """ Implement repr which can be useful for debugging this
            class.
        """

        return f'Reliability({self.parameters!r})'

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
        series_list = []
        # add series for y1 axis
        for i, name in enumerate(self.config_obj.get_series_y()):
            series_obj = ReliabilitySeries(self.config_obj, i, input_data, series_list, name)
            series_list.append(series_obj)

        # add derived
        for i, name in enumerate(self.config_obj.summary_curves):
            series_obj = ReliabilitySeries(self.config_obj, len(self.config_obj.get_series_y()) + i,
                                           input_data, series_list, name)
            series_list.append(series_obj)

        # reorder series
        series_list = self.config_obj.create_list_by_series_ordering(series_list)

        return series_list

    def _create_figure(self):
        """
        Create a line plot from defaults and custom parameters
        """
        # create and draw the plot

        self.figure = self._create_layout()
        self._add_xaxis()
        self._add_yaxis()
        self._add_y2axis()

        self._add_legend()

        # calculate stag adjustments
        stag_adjustments = self._calc_stag_adjustments()

        x_points_index = self.series_list[-1].series_points['thresh_i'].tolist()

        # add series lines
        for series in self.series_list:
            # apply staggering offset if applicable
            if stag_adjustments[series.idx] == 0:
                x_points_index_adj = x_points_index
            else:
                x_points_index_adj = x_points_index + stag_adjustments[series.idx]

            # Don't generate the plot for this series if
            # it isn't requested (as set in the config file)
            if series.plot_disp:
                self._draw_series(series, x_points_index_adj)

    def _draw_series(self, series: ReliabilitySeries, x_points_index_adj: list) -> None:
        """
        Draws the formatted line with CIs if needed on the plot

        :param series: Line series object with data and parameters
        :param x_points_index_adj: values for adjusting x-values position
        """

        if series.idx == 0:
            self._add_noskill_polygon(series.series_points['stat_value'][0])

        if self.config_obj.rely_event_hist is True and 'n_i' in series.series_points:
            x_axis = 'x1'
            if self.config_obj.inset_hist is True:
                x_axis = 'x2'

            bar_trace = go.Bar(
                x=x_points_index_adj,
                y=series.series_points['n_i'].tolist(),
                name="Absolute_cases",
                marker_color=self.config_obj.colors_list[series.idx],
                marker_line_color=self.config_obj.colors_list[series.idx],
                opacity=1,
                showlegend=False,
                xaxis=x_axis,
                yaxis='y2'
            )
            if self.config_obj.inset_hist is True:
                self.figure.add_trace(bar_trace)
            else:
                self.figure.add_trace(bar_trace, secondary_y=True)

        self._add_noskill_line(series.series_points['stat_value'][0])
        self._add_perfect_reliability_line()
        self._add_noresolution_line(series.series_points['stat_value'][0])

        y_points = series.series_points['stat_value'].tolist()
        stat_bcu = all(v == 0 for v in series.series_points['stat_btcu'])
        stat_bcl = all(v == 0 for v in series.series_points['stat_btcl'])

        error_y_visible = True

        if (stat_bcu is True and stat_bcl is True) or self.config_obj.plot_ci[series.idx] == 'NONE':
            error_y_visible = False

        # add the plot
        line_trace = go.Scatter(x=x_points_index_adj,
                                y=y_points,
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
                                error_y={'type': 'data',
                                         'symmetric': False,
                                         'array': series.series_points['stat_btcu'],
                                         'arrayminus': series.series_points['stat_btcl'],
                                         'visible': error_y_visible,
                                         'thickness': self.config_obj.linewidth_list[series.idx]}

                                )

        if self.config_obj.inset_hist is True:
            self.figure.add_trace(line_trace)
        else:
            self.figure.add_trace(line_trace, secondary_y=False)

    def _add_y2axis(self) -> None:
        """
        Adds y2-axis if needed
        """

        if self.config_obj.rely_event_hist is True and self.config_obj.inset_hist is False:
            self.figure.update_yaxes(title_text='',
                                     secondary_y=True,
                                     linecolor=PLOTLY_AXIS_LINE_COLOR,
                                     linewidth=PLOTLY_AXIS_LINE_WIDTH,
                                     showgrid=False,
                                     zeroline=False,
                                     ticks="inside",
                                     tickangle=self.config_obj.y_tickangle,
                                     tickfont={'size': self.config_obj.y_tickfont_size}
                                     )

    def _add_noskill_polygon(self, o_bar: Union[float, None]) -> None:
        """
        Adds no-skill polygon to the graph if needed and o_bar is not None
        :param o_bar: o_bar value or None
        """
        if self.config_obj.add_noskill_line is True:
            if o_bar and o_bar is not None:
                self.figure.add_trace(
                    go.Scatter(x=[o_bar, o_bar, 1, 1, o_bar, 0, 0],
                               y=[0, 1, 1, (1 - o_bar) / 2 + o_bar, o_bar, o_bar, 0],
                               fill='toself',
                               fillcolor='#ededed',
                               line={'color': '#ededed'},
                               showlegend=False,
                               name='No-Skill poly',
                               hoverinfo='skip',
                               opacity=0.5
                               )
                )
            else:
                print(' WARNING: no-skill polygon can\'t be created for the series')

    def _add_noskill_line(self, o_bar: Union[float, None]) -> None:
        """
        Adds no-skill line to the graph if needed and o_bar is not None
        :param o_bar: o_bar value or None
        """
        if self.config_obj.add_noskill_line is True:
            if o_bar and o_bar is not None:
                # create a line
                intercept = 0.5 * o_bar
                self.figure.add_trace(
                    go.Scatter(x=[0, 1],
                               y=[abline(0, intercept, 0.5), abline(1, intercept, 0.5)],
                               line={'color': 'red',
                                     'dash': 'dash',
                                     'width': 1},
                               showlegend=False,
                               mode='lines',
                               name='No-Skill'
                               )
                )
                # create annotation
                self.figure.add_annotation(
                    x=1,
                    y=abline(1, intercept, 0.5),
                    xref="x",
                    yref="y",
                    text="No-Skill",
                    showarrow=True,
                    font={
                        'color': '#636363',
                        'size': self.config_obj.x_tickfont_size
                    },
                    align="left",
                    ax=10,
                    ay=0,
                    textangle=90
                )
            else:
                print(' WARNING: no-skill line can\'t be created for the series')

    def _add_perfect_reliability_line(self) -> None:
        """
         Adds perfect reliability line to the graph if needed
        :return:
        """
        if self.config_obj.add_skill_line is True:
            self.figure.add_trace(
                go.Scatter(x=[0, 1],
                           y=[abline(0, 0, 1), abline(1, 0, 1)],
                           line={'color': 'grey',
                                 'width': 1},
                           showlegend=False,
                           mode='lines',
                           name='Perfect reliability'
                           )
            )
            self.figure.add_annotation(
                x=1,
                y=abline(1, 0, 1),
                xref="x",
                yref="y",
                text="Perfect reliability",
                font={
                    'color': '#636363',
                    'size': self.config_obj.x_tickfont_size
                },
                showarrow=True,
                align="left",
                ax=10,
                ay=0,
                textangle=90
            )

    def _add_noresolution_line(self, o_bar: Union[float, None]) -> None:
        """
        Adds no-resolution line to the graph if needed and o_bar is not None
        :param o_bar: o_bar value or None
        """
        if self.config_obj.add_reference_line is True:
            if o_bar and o_bar is not None:
                self.figure.add_trace(
                    go.Scatter(x=[0, 1],
                               y=[abline(0, o_bar, 0), abline(1, o_bar, 0)],
                               line={'color': 'red',
                                     'dash': 'dash',
                                     'width': 1},
                               showlegend=False,
                               mode='lines',
                               name='No-resolution'
                               )
                )
                self.figure.add_trace(
                    go.Scatter(x=[abline(0, o_bar, 0), abline(1, o_bar, 0)],
                               y=[0, 1],
                               line={'color': 'red',
                                     'dash': 'dash',
                                     'width': 1},
                               showlegend=False,
                               mode='lines',
                               name='No-resolution'
                               )
                )
                self.figure.add_annotation(
                    x=1,
                    y=abline(1, o_bar, 0),
                    xref="x",
                    yref="y",
                    text="No-resolution",
                    showarrow=True,
                    font={
                        'color': '#636363',
                        'size': self.config_obj.x_tickfont_size
                    },
                    align="left",
                    ax=10,
                    ay=0,
                    textangle=90
                )
            else:
                print(' WARNING: no-resolution line can\'t be created for the series')

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
        if self.config_obj.rely_event_hist is True and self.config_obj.inset_hist is True:
            # us go.Layout and  go.Figure to create a figure because of the inset
            layout = go.Layout(
                yaxis=dict(
                    range=[0, 1],
                    tickvals=[x / 10.0 for x in range(0, 11, 1)],
                    ticktext=[x / 10.0 for x in range(0, 11, 1)],
                    showgrid=False,
                    title_text=
                    util.apply_weight_style(self.config_obj.yaxis_1,
                                            self.config_obj.parameters['ylab_weight']),
                    title_standoff=abs(self.config_obj.parameters['ylab_offset']) + 10,

                ),
                xaxis2=dict(
                    domain=[0.08, 0.55],
                    anchor='y2'
                ),
                yaxis2=dict(
                    domain=[0.7, 0.98],
                    anchor='x2',
                    title_text='# Forecasts',
                    showgrid=True,
                    title_standoff=0
                )
            )
            fig = go.Figure(layout=layout)
        else:
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
                                 showgrid=False,
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
                                 tickfont={'size': self.config_obj.x_tickfont_size},
                                 tickmode='array',
                                 tickvals=[x / 10.0 for x in range(0, 11, 1)],
                                 ticktext=[x / 10.0 for x in range(0, 11, 1)],
                                 range=[0, 1]
                                 )

    def _add_yaxis(self) -> None:
        """
        Configures and adds y-axis to the plot
        """

        self.figure.update_yaxes(
            linecolor=PLOTLY_AXIS_LINE_COLOR,
            linewidth=PLOTLY_AXIS_LINE_WIDTH,

            zeroline=False,
            ticks="inside",
            gridwidth=self.config_obj.parameters['grid_lwd'],
            gridcolor=self.config_obj.blended_grid_col,
            automargin=True,
            title_font={
                'size': self.config_obj.y_title_font_size
            },
            tickangle=self.config_obj.y_tickangle,
            tickfont={'size': self.config_obj.y_tickfont_size},

        )
        # adjustments for the inset
        if self.config_obj.rely_event_hist is False or self.config_obj.inset_hist is False:
            self.figure.update_yaxes(secondary_y=False,
                                     showgrid=False,
                                     range=[0, 1],
                                     tickvals=[x / 10.0 for x in range(0, 11, 1)],
                                     ticktext=[x / 10.0 for x in range(0, 11, 1)],
                                     title_standoff=
                                     abs(self.config_obj.parameters['ylab_offset']) + 10,
                                     title_text=
                                     util.apply_weight_style(self.config_obj.yaxis_1,
                                                             self.config_obj.parameters['ylab_weight'])
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
        Formats series point data to the 2-dim array and saves it to the files
        """

        # Open file, name it based on the stat_input config setting,
        # (the input data file) except replace the .data
        # extension with .points1 extension

        if self.config_obj.dump_points_1 is True:

            # create an array for y1 points
            all_points_1 = []

            # get points from each series
            for series in self.series_list:
                series.series_points['stat_btcl'] \
                    = series.series_points['stat_value'] - series.series_points['stat_btcl']
                series.series_points['stat_btcu'] \
                    = series.series_points['stat_value'] + series.series_points['stat_btcu']
                columns_for_print \
                    = series.series_points[["thresh_i", "stat_value", 'stat_btcl', 'stat_btcu']]
                all_points_1.append(columns_for_print.head().values.tolist())

            all_points_1 = [item for sublist in all_points_1 for item in sublist]

            # create a file name from stat_input parameter
            match = re.match(r'(.*)(.data)', self.config_obj.parameters['stat_input'])
            if match:
                filename_only = match.group(1)
            else:
                filename_only = 'points'

            # save points
            if self.config_obj.dump_points_1 is True:
                self._save_points(all_points_1, filename_only + ".points1")

    def _calc_stag_adjustments(self) -> list:
        """
        Calculates the x-axis adjustment for each point if requested.
        It needed so hte points and CIs for each x-axis values don't be placed on top of each other

        :return: the list of the adjustment values
        """

        # get the total number of series
        num_stag = len(self.config_obj.all_series_y1) + len(self.config_obj.summary_curves)

        # init the result with 0
        stag_vals = [0] * num_stag

        # calculate staggering values
        if self.config_obj.indy_stagger is True:
            dbl_adj_scale = (self.series_list[-1].series_points['thresh_i'].tolist()[-1] -
                             self.series_list[-1].series_points['thresh_i'].tolist()[0]) / 150
            stag_vals = np.linspace(-(num_stag / 2) * dbl_adj_scale,
                                    (num_stag / 2) * dbl_adj_scale,
                                    num_stag,
                                    True)
            stag_vals = stag_vals + dbl_adj_scale / 2
        return stag_vals

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
            my_csv.close()

        except TypeError:
            print('Can\'t save points to a file')


def main(config_filename=None):
    """
            Generates a sample, default, line plot using the
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
        plot = Reliability(docs)
        plot.save_to_file()
        #plot.show_in_browser()
        plot.write_html()
        plot.write_output_file()
    except ValueError as val_er:
        print(val_er)


if __name__ == "__main__":
    main()
