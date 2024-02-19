import os

from metplotpy.plots.tcmpr_plots.line.mean.tcmpr_series_line_mean import TcmprSeriesLineMean
from metplotpy.plots.tcmpr_plots.line.tcmpr_line import TcmprLine


class TcmprLineMean(TcmprLine):
    def __init__(self, config_obj, column_info, col, case_data, input_df, baseline_data, stat_name):
        super().__init__(config_obj, column_info, col, case_data, input_df, None, stat_name)
        print("--------------------------------------------------------")
        print(f"Plotting MEAN time series by {self.config_obj.series_val_names[0]}")

        self._adjust_titles(stat_name)
        self.series_list = self._create_series(self.input_df, stat_name)
        self.case_data = None
        self.cur_baseline = baseline_data['cur_baseline']
        self.cur_baseline_data = baseline_data['cur_baseline_data']
        self.baseline_lead_time = 'ind'
        self._init_hfip_baseline_for_plot()
        if self.config_obj.prefix is None or len(self.config_obj.prefix) == 0:
            # self.plot_filename = f"{self.config_obj.plot_dir}{os.path.sep}{self.config_obj.list_stat_1[0]}_{stat_name}_mean.png"
            self.plot_filename = f"{self.config_obj.plot_dir}{os.path.sep}{stat_name}_mean.png"
        else:
            self.plot_filename = f"{self.config_obj.plot_dir}{os.path.sep}{self.config_obj.prefix}_{stat_name}_mean.png"
        # remove the old file if it exist
        if os.path.exists(self.plot_filename):
            os.remove(self.plot_filename)
        self._create_figure(stat_name)

    def _adjust_titles(self, stat_name):
        if self.yaxis_1 is None or len(self.yaxis_1) == 0:
            # self.yaxis_1 = self.config_obj.list_stat_1[0] + '(' + self.col['units'] + ')'
            self.yaxis_1 = stat_name + '(' + self.col['units'] + ')'

        if self.title is None or len(self.title) == 0:
            self.title = 'Mean of ' + self.col['desc'] + ' by ' \
                         + self.column_info[self.column_info['COLUMN'] == self.config_obj.series_val_names[0]][
                             "DESCRIPTION"].tolist()[0]

    def _init_hfip_baseline_for_plot(self):
        if 'Water Only' in self.config_obj.title or self.cur_baseline == 'no':
            print("Plot HFIP Baseline:" + self.cur_baseline)
        else:
            self.cur_baseline_data = self.cur_baseline_data[(self.cur_baseline_data['TYPE'] == 'CONS')]
            print('Plot HFIP Baseline:' + self.cur_baseline.replace('Error ', ''))

    def _create_series(self, input_data, stat_name):
        """
           Generate all the series objects that are to be displayed as specified by the plot_disp
           setting in the config file.  The points are all ordered by datetime.  Each series object
           is represented by a line in the diagram, so they also contain information
           for  plot-related/appearance-related settings (which were defined in the config file).
           A series object is defined by the series_val_1 setting in the config file.

           Args:
               input_data:  The input data in the form of a Pandas dataframe.
                            This data will be subset to reflect the series data of interest.
               stat_name:   Corresponds to the current list_stat_1 value (e.g. TK_ERR, ABS(AMAX_WIND-BMAX_WIND), etc.)
                            in the config file.
           Returns:
               a list of series objects that are to be displayed


        """
        series_list = []

        # add series for y1 axis
        all_series = self.config_obj.get_series_y(1)

        # Limit the series to only the current statistic, list_stat_1 in config file
        series_by_stat = [cur for cur in all_series if stat_name in cur]

        num_series_y1 = len(series_by_stat)
        for i, name in enumerate(series_by_stat):
            if not isinstance(name, list):
                name = [name]

            series_obj = TcmprSeriesLineMean(self.config_obj, i, input_data, series_list, name)
            series_list.append(series_obj)

        # add derived for y1 axis
        for i, name in enumerate(self.config_obj.get_config_value('derived_series_1')):
            # add default operation value if it is not provided
            if len(name) == 2:
                name.append("DIFF")
            # include the series only if the name is valid
            if len(name) == 3:
                # add stat if needed
                oper = name[2]
                name[:] = [(s + ' ' + stat_name) if ' ' not in s else s for s in name[:2]]
                name.append(oper)

                series_obj = TcmprSeriesLineMean(self.config_obj, num_series_y1 + i, input_data, series_list, name)
                series_list.append(series_obj)

        # reorder series
        series_list = self.config_obj.create_list_by_series_ordering(series_list)

        return series_list
