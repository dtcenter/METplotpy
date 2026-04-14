# ============================*
# ** Copyright UCAR (c) 2020
# ** University Corporation for Atmospheric Research (UCAR)
# ** National Center for Atmospheric Research (NCAR)
# ** Research Applications Lab (RAL)
# ** P.O.Box 3000, Boulder, Colorado, 80307-3000, USA
# ============================*


"""
Class Name: tcmpr.py
 """

import os

from metplotpy.plots.tcmpr_plots.scatter.tcmpr_series_scatter import TcmprSeriesScatter
from metplotpy.plots.tcmpr_plots.tcmpr import Tcmpr
from metplotpy.plots.tcmpr_plots.tcmpr_util import get_dep_column


class TcmprScatter(Tcmpr):
    """  Generates a Plotly box plot for 1 or more traces
         where each box is represented by a text point data file.
    """

    def __init__(self, config_obj, column_info, col, case_data, input_df, stat_name):
        """ Creates a box plot, based on
            settings indicated by parameters.

            Args:

        """

        # init common layout
        super().__init__(config_obj, column_info, col, case_data, input_df, stat_name)
        print("--------------------------------------------------------")
        print("Creating Scatter plot")
        print("Plot HFIP Baseline:" + self.cur_baseline)

        if not self.config_obj.scatter_x:
            raise ValueError("scatter_x values are not specified")

        if not self.config_obj.scatter_y:
            raise ValueError("scatter_y values are not specified")

        is_series_valid = len(self.config_obj.series_val_names) == 1 and self.config_obj.series_val_names[0] == 'LEAD'
        is_indy_valid = self.config_obj.indy_var == 'LEAD'

        if not is_series_valid and not is_indy_valid:
            raise ValueError("LEAD values are not specified")

        if not is_series_valid and is_indy_valid:
            self.config_obj.parameters['series_val_1'] = {}
            self.config_obj.parameters['series_val_1'][self.config_obj.indy_var] = self.config_obj.indy_vals
            self.config_obj.series_vals_1 = [self.config_obj.indy_vals]
            self.config_obj.all_series_vals = [self.config_obj.indy_vals]
            self.config_obj.series_val_names = [self.config_obj.indy_var]
            self.config_obj.indy_vals = []
            self.config_obj.indy_var = ''
            self.config_obj.list_stat_1 = []
            self.config_obj.all_series_y1 = self.config_obj._get_all_series_y(1)
            if len(self.config_obj.marker_list) != len(self.config_obj.all_series_y1):
                self.config_obj.marker_list = ['circle'] * len(self.config_obj.all_series_y1)
            if len(self.config_obj.linewidth_list) != len(self.config_obj.all_series_y1):
                self.config_obj.linewidth_list = [1] * len(self.config_obj.all_series_y1)
            if len(self.config_obj.linestyles_list) != len(self.config_obj.all_series_y1):
                self.config_obj.linestyles_list = [None] * len(self.config_obj.all_series_y1)
            if len(self.config_obj.user_legends) != len(self.config_obj.all_series_y1):
                self.config_obj.user_legends = [str(i) for i in self.config_obj.all_series_vals[0]]
            if len(self.config_obj.colors_list) != len(self.config_obj.all_series_y1):
                self.config_obj.colors_list = self.config_obj.colors_list[0: len(self.config_obj.all_series_y1)]
        elif is_series_valid:
            self.indy_vals = []
            self.indy_var = ''
            self.list_stat_1 = []
            self.all_series_y1 = self.config_obj._get_all_series_y(1)

        out_file_x = self.config_obj.scatter_x[-1].replace(')', '').replace('(', '_')
        out_file_y = self.config_obj.scatter_y[-1].replace(')', '').replace('(', '_')

        filename_prefix = self.config_obj.prefix if self.config_obj.prefix else f'{out_file_x}_vs_{out_file_y}'
        self.plot_filename = os.path.join(self.config_obj.plot_dir, f'{filename_prefix}_scatter.png')

        # remove the old file if it exist
        if os.path.exists(self.plot_filename):
            os.remove(self.plot_filename)

        self._adjust_titles()

        self.series_list = self._create_series(self.input_df)

        self._create_figure()

    def _adjust_titles(self):
        for ind, scatter_x_val in enumerate(self.config_obj.scatter_x):
            print("Processing scatter columns: " + scatter_x_val + " versus", self.config_obj.scatter_y[ind])
            # Get the data to be plotted
            col_x = get_dep_column(scatter_x_val, self.column_info, self.input_df)
            self.input_df['SCATTER_X'] = col_x['val']
            # Get the data to be plotted
            col_y = get_dep_column(self.config_obj.scatter_y[ind], self.column_info, self.input_df)
            self.input_df['SCATTER_Y'] = col_y['val']

            if not self.yaxis_1:
                self.yaxis_1 = self.config_obj.scatter_y[ind] + " (" + col_y['units'] + ')'

            if self.config_obj.xaxis == 'test x_label':
                self.config_obj.xaxis = scatter_x_val + " (" + col_x['units'] + ')'

            if not self.title:
                self.title = "Scatter plot of \n" + col_x['desc'] + '\nversus ' + col_y['desc']

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
        for i, name in enumerate(self.config_obj.get_series_y(1)):
            if not isinstance(name, list):
                name = [name]
            series_obj = TcmprSeriesScatter(self.config_obj, i, input_data, series_list, name)
            series_list.append(series_obj)

        # reorder series
        series_list = self.config_obj.create_list_by_series_ordering(series_list)

        # reverse series list if config is set to reverse x-axis
        if self.config_obj.xaxis_reverse:
            series_list.reverse()

        return series_list

    def _create_figure(self):
        """ Create a box plot from default and custom parameters"""

        super()._create_figure()

        for series in self.series_list:
            # Don't generate the plot for this series if
            # it isn't requested (as set in the config file)
            if not series.plot_disp:
                continue

            self._draw_series(series)

        values = [*self.input_df['SCATTER_X'], *self.input_df['SCATTER_Y']]
        # Draw a 1 to 1 reference line
        if (self.elements_with_string(self.config_obj.scatter_x, '_WIND_') > 0 and self.elements_with_string(
                self.config_obj.scatter_y, '_WIND_') > 0) \
                or (self.elements_with_string(self.config_obj.scatter_x, 'AMAX_WIND') > 0 and self.elements_with_string(self.config_obj.scatter_y, 'BMAX_WIND') > 0) \
                or (self.elements_with_string(self.config_obj.scatter_x, 'BMAX_WIND') > 0 and self.elements_with_string(self.config_obj.scatter_y, 'AMAX_WIND') > 0):

            xrange = [min(values) - 1, max(values) + 1]
            yrange = [min(values) - 1, max(values) + 1]

            self.ax.scatter(xrange, yrange,
                            color='#7b7d7d',
                            linestyle='--',
                            linewidth=1,
                            label='_No-Skill_',
                            )

        else:
            xrange = [min(self.input_df['SCATTER_X']) - 1, max(self.input_df['SCATTER_X']) + 1]
            yrange = [min(self.input_df['SCATTER_Y']) - 1, max(self.input_df['SCATTER_Y']) + 1]

            # Draw a reference line at 0
            self.add_horizontal_line(self.ax, yrange[0], {'line_width': 1, 'line_dash': "dash", 'line_color': "#7b7d7d"})

        # set x and y limits unless they are set in the config
        if not self.config_obj.parameters['xlim']:
            self.ax.set_xlim(xrange)
        if not self.config_obj.parameters['ylim']:
            self.ax.set_ylim(yrange)

        self._add_xaxis()
        self._add_yaxis()
        self._add_legend(self.ax)

    def _draw_series(self, series: TcmprSeriesScatter) -> None:
        # Create a point plot
        ax = self.ax if series.y_axis == 1 else self.ax2
        ax.scatter(series.series_data['SCATTER_X'], series.series_data['SCATTER_Y'],
                   size=self.config_obj.marker_size,
                   color=self.config_obj.colors_list[series.idx],
                   colormap=self.config_obj.marker_color,
                   label=self.config_obj.user_legends[series.idx],
                   )

    @staticmethod
    def elements_with_string(list_of_str, pattern):
        count = 0
        for s in list_of_str:
            if pattern in s:
                count = count + 1
        return count
