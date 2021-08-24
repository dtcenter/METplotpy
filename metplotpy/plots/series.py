"""
Class Name: series.py
 """
__author__ = 'Minna Win'


class Series:
    """
        Represents a series object of data points and their plotting style
        elements (line colors, markers, linestyles, etc.)
        Each series is depicted by a single line in the performance diagram.

    """

    def __init__(self, config, idx: int, input_data, y_axis: int = 1):
        self.config = config
        self.idx = idx
        self.input_data = input_data
        self.y_axis = y_axis
        self.plot_disp = config.plot_disp[idx]
        self.plot_stat = config.plot_stat
        self.color = config.colors_list[idx]
        self.series_data = None
        if hasattr(config, 'marker_list'):
            self.marker = config.marker_list[idx]
        if hasattr(config, 'linewidth_list'):
            self.linewidth = config.linewidth_list[idx]
        if hasattr(config, 'linestyles_list'):
            self.linestyle = config.linestyles_list[idx]

        self.user_legends = config.user_legends[idx]
        self.series_order = config.series_ordering_zb[idx]

        # Variables used for subsetting the input dataframe
        # series variable names defined in the series_val_1 setting
        self.series_vals_1 = config.series_vals_1
        self.series_vals_2 = config.series_vals_2
        self.all_series_vals = self.series_vals_1 + self.series_vals_2

        # Forecast variable names defined in the fcst_var_val setting
        # Renamed fcst_vars_1 and fcst_vars_2 in config file
        # self.fcst_vars_1 = config.fcst_vars_1
        # self.fcst_vars_2 = config.fcst_vars_2
        # to this:
        self.fcst_vars_1 = config.fcst_var_val_1
        self.fcst_vars_2 = config.fcst_var_val_2

        # Column names corresponding to the series variable names
        self.series_val_names = config.series_val_names

        self.all_fields_values_no_indy = self._create_all_fields_values_no_indy()

        # Subset the data for this series object
        self.series_points = self._create_series_points()

    def _create_series_points(self):
        """
        Abstract method that create series points.

        """
        raise NotImplementedError

    def _create_all_fields_values_no_indy(self) -> dict:
        """
        Creates a dictionary with two keys that represents each axis
        values - dictionaries of field values pairs of all series variables (without indy variable)
        :return: dictionary with field-values pairs for each axis
        """
        return {}

    def _check_beta_value(self) -> None:
        """
        Checks if the current statistic is 'DMAP_GBETA' and prints a warning message
        if the corresponding BETA_VALUE values changes
        :return:
        """
        # get the stat
        if 'stat_name' in self.all_fields_values_no_indy[self.y_axis].keys():
            stat_value = self.all_fields_values_no_indy[self.y_axis]['stat_name'][0]
        else:
            stat_value = None

        # get the series name
        if hasattr(self, 'series_name') and self.series_name is not None:
            name = self.series_name
        else:
            name = ''

        # check and print the warning
        if stat_value is not None \
                and self.series_data is not None \
                and stat_value == 'DMAP_GBETA' \
                and 'beta_value' in self.series_data.columns:
            unique_beta_value = self.series_data['beta_value'].unique()
            if len(unique_beta_value) > 1:
                print(f'WARNING: note that beta_value differs for one or more GBETA values for {name} '
                      f'so that comparisons across cases may not be comparable.')
