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
import yaml
import itertools

import plotly.graph_objects as go

from metcalcpy.event_equalize import event_equalize
from metplotpy.plots.base_plot import BasePlot
from metplotpy.plots.constants import PLOTLY_AXIS_LINE_COLOR, PLOTLY_AXIS_LINE_WIDTH
from metplotpy.plots.eclv.eclv_config import EclvConfig
from metplotpy.plots.eclv.eclv_series import EclvSeries
from metplotpy.plots.line.line import Line
from metplotpy.plots import util
from metplotpy.plots.series import Series

import metcalcpy.util.utils as calc_util


class Eclv(Line):
    """  Generates a Plotly Economic Cost Loss Relative Value plot for 1 or more traces (lines)
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

        # instantiate a EclvConfig object, which holds all the necessary settings from the
        # config file that represents the BasePlot object (Eclv).
        self.config_obj = EclvConfig(self.parameters)

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
            fix_vals_permuted_list = []

            for key in self.config_obj.fixed_vars_vals_input:
                vals_permuted = list(itertools.product(*self.config_obj.fixed_vars_vals_input[key].values()))
                vals_permuted_list = [item for sublist in vals_permuted for item in sublist]
                fix_vals_permuted_list.append(vals_permuted_list)

            fix_vals_keys = list(self.config_obj.fixed_vars_vals_input.keys())

            self.input_df = event_equalize(self.input_df, self.ECLV_INDY_VAR,
                                self.parameters['series_val_1'],
                                fix_vals_keys,
                                fix_vals_permuted_list, True,True)

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

        return f'Eclv({self.parameters!r})'

    def _create_series(self, input_data):
        """
           Generate all the series objects that are to be displayed as specified by the plot_disp
           setting in the config file.  Each series object
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
        for i, name in enumerate(self.config_obj.get_series_y(1)):
            if isinstance(name, str):
                name = [name]
            series_obj = EclvSeries(self.config_obj, i, input_data, series_list, name)
            series_list.append(series_obj)

        # reorder series
        series_list = self.config_obj.create_list_by_series_ordering(series_list)

        return series_list

    def _create_figure(self):
        """
        Create a eclv plot from defaults and custom parameters
        """
        # create and draw the plot
        self.figure = self._create_layout()
        self._add_xaxis()
        self._add_yaxis()
        self._add_legend()

        # placeholder for the number of stats
        n_stats = [0] * len(self.series_list[0].series_points[0]['x_pnt'])

        # add series lines
        for series in self.series_list:

            # Don't generate the plot for this series if
            # it isn't requested (as set in the config file)
            if series.plot_disp:
                self._draw_series(series)

                # aggregate number of stats
                for series_points in series.series_points:
                    n_stats = list(map(add, n_stats, series_points['nstat']))

        # add custom lines
        if len(self.series_list) > 0:
            self._add_lines(self.config_obj)

        # apply y axis limits
        self._yaxis_limits()

        # some x points could be very close to each other and the x-axis  ticktext is bunched up
        # do not print the ticktext for the first points by creating the custom array of x values
        for ind, val in enumerate(self.series_list[0].series_points[0]['x_pnt']):
            var_round = round(val, 2)
            if ind != 0 and var_round < 0.06:
                self.x_axis_ticktext.append('')
            else:
                self.x_axis_ticktext.append(var_round)

        self.figure.update_layout(
            xaxis=dict(
                tickmode='array',
                tickvals=self.series_list[0].series_points[0]['x_pnt'],
                ticktext=self.x_axis_ticktext,
                tickangle=self.config_obj.x_tickangle
            ),
            yaxis=dict(
                zeroline=True,
                zerolinecolor=PLOTLY_AXIS_LINE_COLOR,
                zerolinewidth=PLOTLY_AXIS_LINE_WIDTH
            )
        )

        # add x2 axis
        self._add_x2axis(n_stats)

    def _add_x2axis(self, n_stats) -> None:
        """
        Creates x2axis based on the properties from the config file
        and attaches it to the initial Figure

        :param n_stats: - labels for the axis
        """

        if self.config_obj.show_nstats:
            x_points = []

            # create ticktext array simolar to x-axis ticktext
            for idx, val in enumerate(self.x_axis_ticktext):
                if val != '':
                    x_points.append(n_stats[idx])
                else:
                    x_points.append('')

            self.figure.update_layout(xaxis2={
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
                'tickmode': 'array',
                'tickvals': self.series_list[0].series_points[0]['x_pnt'],
                'ticktext': x_points,
                'tickangle': self.config_obj.x2_tickangle,
                'tickfont': {
                    'size': self.config_obj.x2_tickfont_size
                },
                'scaleanchor': 'x',
                'automargin': False,
                'matches': 'x',
            }
            )

            # need to add an invisible line with all values = None
            self.figure.add_trace(
                go.Scatter(y=[None] * len(self.series_list[0].series_points[0]['x_pnt']),
                           x=self.series_list[0].series_points[0]['x_pnt'],
                           xaxis='x2', showlegend=False)
            )

    def _draw_series(self, series: Series, x_points_index_adj: Union[list, None] = None) -> None:
        """
        Draws the formatted line with CIs if needed on the plot

        :param series: Eclv series object with data and parameters
        :param x_points_index_adj: values for adjusting x-values position
        """

        # pct series can have mote than one line
        for ind, series_points in enumerate(series.series_points):
            y_points = series_points['dbl_med']
            x_points = series_points['x_pnt']

            # show or not ci
            # see if any ci values in not 0
            no_ci_up = all(v == 0 for v in series_points['dbl_up_ci'])
            no_ci_lo = all(v == 0 for v in series_points['dbl_lo_ci'])
            error_y_visible = True
            if (no_ci_up is True and no_ci_lo is True) or self.config_obj.plot_ci[series.idx] == 'NONE':
                error_y_visible = False

            # add the plot
            self.figure.add_trace(
                go.Scatter(x=x_points,
                           y=y_points,
                           showlegend=ind == 0,
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
                                    'array': series_points['dbl_up_ci'],
                                    'arrayminus': series_points['dbl_lo_ci'],
                                    'visible': error_y_visible,
                                    'thickness': self.config_obj.linewidth_list[series.idx]},
                           hovertemplate="<br>".join([
                               "Cost/Lost Ratio: %{customdata}",
                               "Economic Value: %{y}"
                           ]),
                           customdata=x_points
                           ),
                secondary_y=False
            )

    def write_output_file(self) -> None:
        """
        saves series points to the files
        """

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

            with open(filename, 'w') as file:
                writer = csv.writer(file, delimiter='\t')
                for series in self.series_list:
                    for vals_ind, vals in enumerate(series.series_points):
                        keys = sorted(vals.keys())
                        if vals_ind == 0:
                            writer.writerow(keys)
                        else:
                            file.writelines('\n')
                        for ind, dbl_med in enumerate(vals['dbl_med']):
                            vals['dbl_lo_ci'][ind] = dbl_med - vals['dbl_lo_ci'][ind]
                            vals['dbl_up_ci'][ind] = dbl_med + vals['dbl_up_ci'][ind]
                        writer.writerows(zip(*[[round(num, 6) for num in vals[key]] for key in keys]))
                    file.writelines('\n')
                    file.writelines('\n')
                file.close()


def main(config_filename=None):
    """
            Generates a sample, default, eclv plot using the
            default and custom config files on sample data found in this directory.
            The location of the input data is defined in either the default or
            custom config file.
            Args:
                @param config_filename: default is None, the name of the custom config file to apply
        """

    # Retrieve the contents of the custom config file to over-ride
    # or augment settings defined by the default config file.
    # with open("./custom_eclv_plot.yaml", 'r') as stream:
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
        plot = Eclv(docs)
        plot.save_to_file()
        #plot.show_in_browser()
        plot.write_html()
        plot.write_output_file()
    except ValueError as val_er:
        print(val_er)


if __name__ == "__main__":
    main()
