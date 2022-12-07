# ============================*
 # ** Copyright UCAR (c) 2020
 # ** University Corporation for Atmospheric Research (UCAR)
 # ** National Center for Atmospheric Research (NCAR)
 # ** Research Applications Lab (RAL)
 # ** P.O.Box 3000, Boulder, Colorado, 80307-3000, USA
 # ============================*
 
 
 
"""
Class Name: LineSeries
 """
__author__ = 'Tatiana Burek'

from typing import Union
import numpy as np
import warnings

import metcalcpy.util.utils as utils
from .. import GROUP_SEPARATOR
from ..series import Series


class ReliabilitySeries(Series):
    """
        Represents a Reliability plot series object
        of data points and their plotting style
        elements (line colors, markers, linestyles, etc.)

    """

    def __init__(self, config, idx: int, input_data, series_list: list,
                 series_name: Union[list, tuple], y_axis: int = 1):
        self.series_list = series_list
        self.series_name = series_name
        super().__init__(config, idx, input_data, y_axis)

    def _create_all_fields_values_no_indy(self) -> dict:
        """
        Creates a dictionary with two keys that represents each axis
        values - dictionaries of field values pairs of all series variables (without indy variable)
        :return: dictionary with field-values pairs for each axis
        """
        all_fields_values_no_indy = {}
        all_fields_values = self.config.get_config_value('series_val_1').copy()
        if self.config._get_fcst_vars(1):
            all_fields_values['fcst_var'] = list(self.config._get_fcst_vars(1).keys())
        all_fields_values['stat_name'] = self.config.get_config_value('list_stat_1')
        all_fields_values_no_indy[1] = all_fields_values

        all_fields_values = self.config.get_config_value('series_val_2').copy()
        if self.config._get_fcst_vars(2):
            all_fields_values['fcst_var'] = list(self.config._get_fcst_vars(2).keys())
        all_fields_values['stat_name'] = self.config.get_config_value('list_stat_2')
        all_fields_values_no_indy[2] = all_fields_values

        return all_fields_values_no_indy

    def _calc_point_stat(self, data: list) -> Union[float, None]:
        """
        Calculates the statistic specified in the config 'plot_stat' parameter
        using input data list
        :param data: list os numbers
        :return:  mean, median or sum of the values from the input list or
            None if the statistic parameter is invalid
        """
        # calculate point stat
        if self.config.plot_stat == 'MEAN':
            with warnings.catch_warnings():
                warnings.filterwarnings(action='ignore', message='All-NaN slice encountered')
                point_stat = np.nanmean(data)
        elif self.config.plot_stat == 'MEDIAN':
            with warnings.catch_warnings():
                warnings.filterwarnings(action='ignore', message='All-NaN slice encountered')
                point_stat = np.nanmedian(data)
        elif self.config.plot_stat == 'SUM':
            with warnings.catch_warnings():
                warnings.filterwarnings(action='ignore', message='All-NaN slice encountered')
                point_stat = np.nansum(data)
        else:
            point_stat = None
        return point_stat

    def _create_series_points(self) -> dict:
        """
        Subset the data for the appropriate series.
        Calculates values for each point including CI

        Args:

        Returns:
               dictionary with CI ,point values and number of stats as keys
        """

        # different ways to subset data for normal and derived series
        if self.series_name not in ['median', 'mean']:
            # this is a normal series
            all_filters = []

            # create a set of filters for this series
            for field_ind, field in enumerate(self.config.get_config_value('series_val_1').keys()):
                filter_value = self.series_name[field_ind]
                if utils.GROUP_SEPARATOR in filter_value:
                    filter_list = filter_value.split(GROUP_SEPARATOR)
                elif ";" in filter_value:
                    filter_list = filter_value.split(';')
                else:
                    filter_list = [filter_value]
                for i, filter_val in enumerate(filter_list):
                    if utils.is_string_integer(filter_val):
                        filter_list[i] = int(filter_val)
                    elif utils.is_string_strictly_float(filter_val):
                        filter_list[i] = float(filter_val)

                all_filters.append((self.input_data[field].isin(filter_list)))
            # use numpy to select the rows where any record evaluates to True
            if all_filters:
                mask = np.array(all_filters).all(axis=0)
                self.series_data = self.input_data.loc[mask]
            else:
                self.series_data = self.input_data

            # sort data by date/time - needed for CI calculations
            if 'fcst_lead' in self.series_data.columns:
                if 'fcst_valid_beg' in self.series_data.columns:
                    self.series_data = self.series_data.sort_values(['fcst_valid_beg', 'fcst_lead'])
                if 'fcst_valid' in self.series_data.columns:
                    self.series_data = self.series_data.sort_values(['fcst_valid', 'fcst_lead'])
                if 'fcst_init_beg' in self.series_data.columns:
                    self.series_data = self.series_data.sort_values(['fcst_init_beg', 'fcst_lead'])
                if 'fcst_init' in self.series_data.columns:
                    self.series_data = self.series_data.sort_values(['fcst_init', 'fcst_lead'])
            else:
                if 'fcst_valid_beg' in self.series_data.columns:
                    self.series_data = self.series_data.sort_values(['fcst_valid_beg'])
                if 'fcst_valid' in self.series_data.columns:
                    self.series_data = self.series_data.sort_values(['fcst_valid'])
                if 'fcst_init_beg' in self.series_data.columns:
                    self.series_data = self.series_data.sort_values(['fcst_init_beg'])
                if 'fcst_init' in self.series_data.columns:
                    self.series_data = self.series_data.sort_values(['fcst_init'])

            obar_data = self.series_data.loc[lambda df: df['stat_name'] == 'PSTD_BASER', :]
            calibration_data = self.series_data.loc[lambda df: df['stat_name'] == 'PSTD_CALIBRATION', :]
            n_i_data = self.series_data.loc[lambda df: df['stat_name'] == 'PSTD_NI', :]

            series_points_results = calibration_data.copy()
            series_points_results['thresh_ii'] = series_points_results['thresh_i'].tolist()
            series_points_results['n_i'] = n_i_data['stat_value'].tolist()
            series_points_results.reset_index(drop=True, inplace=True)

            for i in range(1, len(series_points_results)):
                series_points_results.loc[i - 1, 'thresh_i'] = 0.5 * (
                        series_points_results.loc[i, 'thresh_ii']
                        + series_points_results.loc[i - 1, 'thresh_ii']
                )

            series_points_results.loc[len(series_points_results) - 1, 'thresh_i'] = 0.5 * (
                    1 + series_points_results.loc[len(series_points_results) - 1, 'thresh_ii'])
            series_points_results['no_skill'] = \
                [0.5 * (a + b) for a, b in zip(series_points_results['thresh_i'],
                                               obar_data['stat_value'])]
            series_points_results = series_points_results.drop(columns=['stat_name'])

            series_points_results['stat_btcl'] = \
                series_points_results['stat_value'] - series_points_results['stat_btcl']
            series_points_results['stat_btcu'] = \
                series_points_results['stat_btcu'] - series_points_results['stat_value']

        else:
            # this is a derived series
            calibration_data = \
                self.input_data.loc[lambda df: df['stat_name'] == 'PSTD_CALIBRATION', :]
            if self.series_name == 'median':
                series_points_results = calibration_data.groupby('thresh_i')[[
                    'stat_value', 'stat_btcl', 'stat_btcu']].median().reset_index()
            elif self.series_name == 'mean':
                series_points_results = calibration_data.groupby('thresh_i')[[
                    'stat_value', 'stat_btcl', 'stat_btcu']].mean().reset_index()
            else:
                series_points_results = calibration_data.copy()
                series_points_results['stat_name'] = None
                series_points_results['stat_btcl'] = None
                series_points_results['stat_btcu'] = None

            series_points_results['stat_btcl'] = \
                series_points_results['stat_value'] - series_points_results['stat_btcl']
            series_points_results['stat_btcu'] = \
                series_points_results['stat_btcu'] - series_points_results['stat_value']
            series_points_results['thresh_ii'] = series_points_results['thresh_i'].copy()

            for i in range(1, len(series_points_results)):
                series_points_results.loc[i - 1, 'thresh_i'] = \
                    0.5 * (series_points_results.loc[i, 'thresh_ii']
                           + series_points_results.loc[i - 1, 'thresh_ii'])

            series_points_results.loc[len(series_points_results) - 1, 'thresh_i'] = 0.5 * (
                    1 + series_points_results.loc[len(series_points_results) - 1, 'thresh_ii'])

        return series_points_results
