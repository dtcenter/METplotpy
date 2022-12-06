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
import re

import numpy as np
import pandas as pd
from pandas import DataFrame

import metcalcpy.util.utils as utils
from ..series import Series


class BoxSeries(Series):
    """
        Represents a Box plot series object
        of data points and their plotting style
        elements (line colors,  etc.)

    """

    def __init__(self, config, idx: int, input_data, series_list: list,
                 series_name: Union[list, tuple], y_axis: int = 1):
        self.series_list = series_list
        self.series_name = series_name
        super().__init__(config, idx, input_data, y_axis)
        if list(self.config._get_fcst_vars(self.y_axis).keys())[0].startswith('REV_'):
            # calculate revision statistics for leg = 1 and add them to the series name
            stats = utils.calculate_mtd_revision_stats(self.series_data[['stat_value', 'revision_id']], 1)
            self.user_legends = f'{self.user_legends} (WW Runs Test:{stats.get("ww_run")},' \
                                f'Auto-Corr Test: p={stats.get("auto_cor_p")},' \
                                f'r={stats.get("auto_cor_r")})'

    def _create_all_fields_values_no_indy(self) -> dict:
        """
        Creates a dictionary with two keys that represents each axis
        values - dictionaries of field values pairs of all series variables (without indy variable)
        :return: dictionary with field-values pairs for each axis
        """
        all_fields_values_no_indy = {}

        all_fields_values_orig = self.config.get_config_value('series_val_1').copy()
        all_fields_values = {}
        for x in reversed(list(all_fields_values_orig.keys())):
            all_fields_values[x] = all_fields_values_orig.get(x)

        if self.config._get_fcst_vars(1):
            all_fields_values['fcst_var'] = list(self.config._get_fcst_vars(1).keys())
        all_fields_values['stat_name'] = self.config.get_config_value('list_stat_1')
        all_fields_values_no_indy[1] = all_fields_values

        if 'series_val_2' in self.config.parameters.keys():
            all_fields_values_orig = self.config.get_config_value('series_val_2').copy()
            all_fields_values = {}
            for x in reversed(list(all_fields_values_orig.keys())):
                all_fields_values[x] = all_fields_values_orig.get(x)

            if self.config._get_fcst_vars(2):
                all_fields_values['fcst_var'] = list(self.config._get_fcst_vars(2).keys())
            all_fields_values['stat_name'] = self.config.get_config_value('list_stat_2')
            all_fields_values_no_indy[2] = all_fields_values

        return all_fields_values_no_indy

    def _create_series_points(self) -> dict:
        """
        Subset the data for the appropriate series.
        Calculates values for each point including CI

        Args:

        Returns:
               dictionary with CI ,point values and number of stats as keys
        """

        series_data_1 = None
        series_data_2 = None

        # different ways to subset data for normal and derived series
        if self.series_name[-1] not in utils.OPERATION_TO_SIGN.keys():
            # this is a normal series
            all_filters = []

            # create a set of filters for this series
            for field_ind, field in enumerate(self.all_fields_values_no_indy[self.y_axis].keys()):
                filter_value = self.series_name[field_ind]
                if utils.GROUP_SEPARATOR in filter_value:
                    filter_list = re.findall(utils.DATE_TIME_REGEX, filter_value)
                    if len(filter_list) == 0:
                        filter_list = filter_value.split(utils.GROUP_SEPARATOR)
                    # add the original value
                    filter_list.append(filter_value)
                else:
                    filter_list = [filter_value]
                for i, filter_val in enumerate(filter_list):
                    if utils.is_string_integer(filter_val):
                        filter_list[i] = int(filter_val)
                    elif utils.is_string_strictly_float(filter_val):
                        filter_list[i] = float(filter_val)

                all_filters.append((self.input_data[field].isin(filter_list)))

            # filter by provided indy

            # Duck typing is different in Python 3.6 and Python 3.8, for
            # Python 3.8 and above, explicitly type cast the self.input_data[self.config.indy_var]
            # Panda Series object to 'str' if the list of indy_vals are of str type.
            # This will ensure we are doing str to str comparisons.
            if isinstance(self.config.indy_vals[0], str):
                indy_var_series = self.input_data[self.config.indy_var].astype(str)
            else:
                # The Panda series is as it was originally coded.
                indy_var_series = self.input_data[self.config.indy_var]

            all_filters.append(indy_var_series.isin(self.config.indy_vals))

            #use numpy to select the rows where any record evaluates to True
            mask = np.array(all_filters).all(axis=0)
            self.series_data = self.input_data.loc[mask]

            # sort data by date/time - needed for CI calculations
            if 'fcst_valid_beg' in self.series_data.columns:
                self.series_data = self.series_data.sort_values(['fcst_valid_beg', 'fcst_lead'])
            if 'fcst_valid' in self.series_data.columns:
                self.series_data = self.series_data.sort_values(['fcst_valid', 'fcst_lead'])
            if 'fcst_init_beg' in self.series_data.columns:
                self.series_data = self.series_data.sort_values(['fcst_init_beg', 'fcst_lead'])
            if 'fcst_init' in self.series_data.columns:
                self.series_data = self.series_data.sort_values(['fcst_init', 'fcst_lead'])

        else:
            # this is a derived series

            # the name of the 1st series
            series_name_1 = self.series_name[0].split()
            # the name of the 2nd series
            series_name_2 = self.series_name[1].split()
            # operation
            operation = self.series_name[2]

            # find original series data

            for series in self.series_list:
                if set(series_name_1) == set(series.series_name):
                    series_data_1 = series.series_data
                if set(series_name_2) == set(series.series_name):
                    series_data_2 = series.series_data

            # create a series name as a string
            series_name_str = utils.get_derived_curve_name([self.series_name[0],
                                                            self.series_name[1],
                                                            operation])
            # look for the data with the series name value in the input data frame
            # it could be there if agg or summary statistic logic was applied
            for field in self.all_fields_values_no_indy[self.y_axis]:
                self.series_data = self.input_data.loc[self.input_data[field] == series_name_str]
                if len(self.series_data) > 0:
                    break

            # check if the input frame already has derived series ( from calculation agg stats )
            if len(self.series_data) == 0:
                # no data with with the series name value was found
                # - calculate derived statistic for the each box
                self._calculate_derived_values(operation, series_data_1, series_data_2)

        # print a message if needed for inconsistent beta_values
        self._check_beta_value()

        series_points_results = {'nstat': []}

        # for each point calculate plot statistic
        for indy in self.config.indy_vals:
            if utils.is_string_integer(indy):
                indy = int(indy)
            elif utils.is_string_strictly_float(indy):
                indy = float(indy)

            point_data = self.series_data.loc[self.series_data[self.config.indy_var] == indy]
            series_points_results['nstat'].append(len(point_data['stat_value']))

        return series_points_results


    def _calculate_derived_values(self,
                                  operation: str,
                                  series_data_1: DataFrame,
                                  series_data_2: DataFrame) -> None:
        """
        Validates if both DataFrames have the same fcst_valid_beg values and if it is TRUE
        Calculates derived statistic for the each box based on data from the 1st
        and 2nd data frames
        For example, if the operation is 'DIFF' the diferensires between values from
        the 1st and the 2nd frames will be calculated
        This method also calculates CI(s)

        :param operation: statistic to calculate
        :param series_data_1: 1st data frame sorted  by fcst_init_beg
        :param series_data_2: 2nd data frame sorted  by fcst_init_beg
        """

        # for each independent value
        for indy in self.config.indy_vals:
            if utils.is_string_integer(indy):
                indy = int(indy)
            elif utils.is_string_strictly_float(indy):
                indy = float(indy)

            stats_indy_1 = \
                series_data_1.loc[series_data_1[self.config.indy_var] == indy]
            stats_indy_2 = \
                series_data_2.loc[series_data_2[self.config.indy_var] == indy]

            # validate data
            if 'fcst_valid_beg' in stats_indy_1.columns:
                unique_dates = \
                    stats_indy_1[['fcst_valid_beg', 'fcst_lead', 'stat_name']].drop_duplicates().shape[0]
            elif 'fcst_valid' in stats_indy_1.columns:
                unique_dates = \
                    stats_indy_1[['fcst_valid', 'fcst_lead', 'stat_name']].drop_duplicates().shape[0]
            elif 'fcst_init_beg' in stats_indy_1.columns:
                unique_dates = \
                    stats_indy_1[['fcst_init_beg', 'fcst_lead', 'stat_name']].drop_duplicates().shape[0]
            else:
                unique_dates = \
                    stats_indy_1[['fcst_init', 'fcst_lead', 'stat_name"']].drop_duplicates().shape[0]
            if stats_indy_1.shape[0] != unique_dates:
                raise ValueError(
                    'Derived curve can\'t be calculated. '
                    'Multiple values for one valid date/fcst_lead')

            # data should be sorted sorted  by fcst_init_beg !!!!!
            stats_values = utils.calc_derived_curve_value(stats_indy_1['stat_value'].tolist(),
                                                          stats_indy_2['stat_value'].tolist(),
                                                          operation)
            stats_indy_1 = stats_indy_1.drop(columns=['stat_value'])
            stats_indy_1['stat_value'] = stats_values

            if self.series_data is None:
                self.series_data = stats_indy_1
            else:
                self.series_data = pd.concat([self.series_data, (stats_indy_1)], sort=False)
