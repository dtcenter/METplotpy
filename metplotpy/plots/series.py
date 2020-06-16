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
    def __init__(self, config, idx, input_data):
        self.config = config
        self.idx = idx
        self.input_data = input_data
        self.plot_disp = config.plot_disp[idx]
        self.plot_stat = config.plot_stat[idx]
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

        # Subset the data for this series object
        self.series_points = self._create_series_points()


