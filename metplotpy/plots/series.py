"""
Class Name: series.py
 """
__author__ = 'Minna Win'
__email__ = 'met_help@ucar.edu'

import itertools
import metcalcpy.util.utils as utils


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
        self.marker = config.marker_list[idx]
        self.linewidth = config.linewidth_list[idx]
        self.linestyle = config.linestyles_list[idx]
        self.user_legends = config.user_legends[idx]
        self.series_order = config.series_ordering_zb[idx]

        # Variables used for subsetting the input dataframe
        # series variable names defined in the series_val_1 setting
        self.series_vals_1 = config.series_vals_1
        self.series_vals_2 = config.series_vals_2
        self.all_series_vals = self.series_vals_1 + self.series_vals_2

        # forecast variable names defined in the fcst_var_val setting
        self.fcst_vars_1 = config.fcst_vars_1
        self.fcst_vars_2 = config.fcst_vars_2

        # Column names corresponding to the series variable names
        self.series_val_names = config.series_val_names

        self.all_fields_values_no_indy = {}
        all_fields_values = self.config.get_config_value('series_val_1').copy()
        if self.config.get_fcst_vars(1):
            all_fields_values['fcst_var'] = list(self.config.get_fcst_vars(1).keys())
        all_fields_values['stat_name'] = self.config.get_config_value('list_stat_1')
        self.all_fields_values_no_indy[1] = all_fields_values

        all_fields_values = self.config.get_config_value('series_val_2').copy()
        if self.config.get_fcst_vars(2):
            all_fields_values['fcst_var'] = list(self.config.get_fcst_vars(2).keys())
        all_fields_values['stat_name'] = self.config.get_config_value('list_stat_2')
        self.all_fields_values_no_indy[2] = all_fields_values

        # Subset the data for this series object
        self.series_points = self._create_series_points()

    def _create_series_points(self):
        """
        Abstract method that create series points.

        """
        raise NotImplementedError
