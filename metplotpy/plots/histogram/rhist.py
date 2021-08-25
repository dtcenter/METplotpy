"""
Class Name: rhist.py
 """
__author__ = 'Tatiana Burek'

import re
import itertools

import yaml
import numpy as np
import pandas as pd

import plotly.graph_objects as go
from plotly.subplots import make_subplots
from plotly.graph_objects import Figure

from plots.constants import PLOTLY_AXIS_LINE_COLOR, PLOTLY_AXIS_LINE_WIDTH, PLOTLY_PAPER_BGCOOR
from plots.histogram.histogram_config import RHistogramConfig
from plots.histogram.rlhist_series import RhistSeries
from plots.base_plot import BasePlot
import plots.util as util
import metcalcpy.util.utils as utils
from metcalcpy.event_equalize import event_equalize


class Rhist(BasePlot):
    """  Generates a Plotly  Histograms of ensemble rank plot for 1 or more traces
    """

    def __init__(self, parameters: dict) -> None:
        """ Creates a Histograms of ensemble rank plot consisting of one or more traces, based on
            settings indicated by parameters.

            Args:
            @param parameters: dictionary containing user defined parameters

        """

        # init common layout
        super().__init__(parameters, "rhist_defaults.yaml")

        # instantiate a RHistogramConfig object, which holds all the necessary settings from the
        # config file that represents the BasePlot object (Rhist).
        self.config_obj = RHistogramConfig(self.parameters)

        # Check that we have all the necessary settings for each series
        is_config_consistent = self.config_obj._config_consistency_check()
        if not is_config_consistent:
            raise ValueError("The number of series defined by series_val_1 is"
                             " inconsistent with the number of settings"
                             " required for describing each series. Please check"
                             " the number of your configuration file's "
                             " plot_disp, series_order, user_legend,"
                             " colors settings.")

        # Read in input data, location specified in config file
        self.input_df = self._read_input_data()

        # Apply event equalization, if requested
        if self.config_obj.use_ee is True:
            self._perform_event_equalization()

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

        # add i_value
        fix_vals_keys.append('i_value')
        unique_i_value = self.input_df['i_value'].unique().tolist()
        fix_vals_permuted_list.append(unique_i_value)

        # do EE for the each series data
        if len(self.config_obj.series_val_names) > 0:
            input_df_ee = None
            all_fields_values_orig = self.config_obj.get_config_value('series_val_1').copy()
            all_fields_values = {}
            for field in reversed(list(all_fields_values_orig.keys())):
                all_fields_values[field] = all_fields_values_orig.get(field)

            for field_name, field_value in all_fields_values.items():
                for val in field_value:
                    all_filters = []
                    filter_list = val
                    if not isinstance(filter_list, str):
                        for i, filter_val in enumerate(filter_list):
                            if utils.is_string_integer(filter_val):
                                filter_list[i] = int(filter_val)
                    else:
                        filter_list = [filter_list]

                    all_filters.append((self.input_df[field_name].isin(filter_list)))

                    # use numpy to select the rows where any record evaluates to True
                    mask = np.array(all_filters).all(axis=0)
                    series_data_for_ee = self.input_df.loc[mask]
                    series_data_after_ee = event_equalize(series_data_for_ee, "fcst_valid_beg", {}, fix_vals_keys,
                                                          fix_vals_permuted_list, True, False)
                    if input_df_ee is None:
                        input_df_ee = series_data_after_ee
                    else:
                        input_df_ee = input_df_ee.append(series_data_after_ee).reindex()
        else:
            input_df_ee = event_equalize(self.input_df, "fcst_valid_beg", {}, fix_vals_keys,
                                         fix_vals_permuted_list, True, False)

        self.input_df = input_df_ee.drop('equalize', axis=1)

    def __repr__(self):
        """ Implement repr which can be useful for debugging this
            class.
        """

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

        # create series in teh correct order
        for i, name in enumerate(self.config_obj.get_series_y()):
            if not isinstance(name, list):
                name = [name]
            # get the actual index
            ind = i
            for order_index, order in enumerate(self.config_obj.series_ordering_zb):
                if order == i:
                    ind = order_index
                    break

            series_obj = RhistSeries(self.config_obj, ind, input_data, series_list, name)
            series_list.append(series_obj)

        if len(series_list) == 0:
            series_obj = RhistSeries(self.config_obj, 0, input_data, series_list, [])
            series_list.append(series_obj)
        else:
            # reorder series
            series_list = self.config_obj.create_list_by_series_ordering(series_list)

        return series_list

    def _create_figure(self):
        """
        Create a box plot from defaults and custom parameters
        """
        # create and draw the plot
        self.figure = self._create_layout()
        self._add_xaxis()
        self._add_yaxis()
        self._add_legend()

        # add series boxes
        for series in self.series_list:
            self._draw_series(series)

    def _draw_series(self, series: RhistSeries) -> None:
        """
        Draws the formatted Bar on the plot
        :param series: Bar series object with data and parameters
        """

        y_points = series.series_points
        x_points = sorted(series.series_data['i_value'].unique())

        # add the bar to plot
        self.figure.add_trace(
            go.Bar(
                x=x_points,
                y=y_points,
                showlegend=True,
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

        # create a layout without y2 axis
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
                                          'bordercolor': self.config_obj.legend_border_color,
                                          'borderwidth': self.config_obj.legend_border_width,
                                          'orientation': self.config_obj.legend_orientation,
                                          'font': {
                                              'size': self.config_obj.legend_size,
                                              'color': "black"
                                          }
                                          })

    def write_html(self) -> None:
        """
        Is needed - creates and saves the html representation of the plot WITHOUT Plotly.js
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
        saves box points to the file
        """

        # Open file, name it based on the stat_input config setting,
        # (the input data file) except replace the .data
        # extension with .points1 extension

        if self.config_obj.dump_points_1 is True:
            match = re.match(r'(.*)(.data)', self.config_obj.parameters['stat_input'])
            if match:
                filename = match.group(1)
            else:
                filename = 'points'
            filename = filename + '.points1'

            with open(filename, 'w') as file:
                for series in self.series_list:
                    file.writelines(
                        map('{}\t'.format,
                            [round(num, 6) for num in series.series_points]))
                    file.writelines('\n')
                file.close()


def main(config_filename=None):
    """
            Generates a sample, default, Rank histogram plot using the
            default and custom config files on sample data found in this directory.
            The location of the input data is defined in either the default or
            custom config file.
            Args:
                @param config_filename: default is None, the name of the custom config file to apply
        """

    # Retrieve the contents of the custom config file to over-ride
    # or augment settings defined by the default config file.
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
        plot = Rhist(docs)
        plot.save_to_file()
        # plot.show_in_browser()
        plot.write_html()
        plot.write_output_file()
    except ValueError as val_er:
        print(val_er)


if __name__ == "__main__":
    main()
