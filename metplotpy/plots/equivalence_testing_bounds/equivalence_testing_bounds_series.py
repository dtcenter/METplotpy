# ============================*
 # ** Copyright UCAR (c) 2022
 # ** University Corporation for Atmospheric Research (UCAR)
 # ** National Center for Atmospheric Research (NCAR)
 # ** Research Applications Lab (RAL)
 # ** P.O.Box 3000, Boulder, Colorado, 80307-3000, USA
 # ============================*
 
 
 
"""
Class Name: EquivalenceTestingBoundSeries
 """
__author__ = 'Tatiana Burek'

from typing import Union
import statistics
import math

import numpy as np
import pandas as pd
from pandas import DataFrame
import metcalcpy.util.correlation as pg

import metcalcpy.util.utils as utils
from metcalcpy.sum_stat import calculate_statistic
from .. import GROUP_SEPARATOR
from ..line.line_series import LineSeries


class EquivalenceTestingBoundsSeries(LineSeries):
    """
        Represents a Line plot series object
        of data points and their plotting style
        elements (line colors, markers, linestyles, etc.)

    """

    def __init__(self, config, idx: int, input_data, series_list: list,
                 series_name: Union[list, tuple], y_axis: int = 1):

        super().__init__(config, idx, input_data, series_list, series_name, y_axis)

    def _create_series_points(self) -> dict:
        """
        Subset the data for the appropriate series.
        Calculates values for each point including CI

        Args:

        Returns:
               dictionary with CI ,point values and number of stats as keys
        """

        # different ways to subset data for normal and derived series
        if self.series_name[-1] not in utils.OPERATION_TO_SIGN.keys():
            # this is a normal series
            all_filters = []

            # create a set of filters for this series
            for field_ind, field in enumerate(self.all_fields_values_no_indy[self.y_axis].keys()):
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
            mask = np.array(all_filters).all(axis=0)
            self.series_data = self.input_data.loc[mask]
            return dict()

        # this is a derived series

        # the name of the 1st series
        series_name_1 = self.series_name[0].split()
        # the name of the 2nd series
        series_name_2 = self.series_name[1].split()
        # operation
        operation = self.series_name[2]

        # find original series data
        series_data_1 = None
        series_data_2 = None
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
            # convert  'stat_value' column of ints to floats
            series_data_1['stat_value'] = pd.to_numeric(series_data_1['stat_value'],
                                                        downcast='float')
            series_data_2['stat_value'] = pd.to_numeric(series_data_2['stat_value'],
                                                        downcast='float')

            # no data with with the series name value was found -
            # calculate derived statistic for the each line
            self._calculate_tost_paired(series_data_1.reset_index(drop=True),
                                        series_data_2.reset_index(drop=True))

        return self.series_data

    def _calculate_tost_paired(self, series_data_1: DataFrame, series_data_2: DataFrame) -> None:
        """
        Validates if both DataFrames have the same fcst_valid_beg values and if it is TRUE
        Calculates derived statistic for the each line based on data from thr 1st and
        2nd data frames. For example, if the operation is 'DIFF' the differences between
        values from the 1st and the 2nd frames will be calculated
        This method also calculates CI(s)

        :param series_data_1: 1st data frame sorted  by fcst_init_beg
        :param series_data_2: 2nd data frame sorted  by fcst_init_beg
        """

        all_zero_1 = all(elem is None or math.isnan(elem)
                         for elem in series_data_1['stat_value'].tolist())
        all_zero_2 = all(elem is None or math.isnan(elem)
                         for elem in series_data_2['stat_value'].tolist())

        if all_zero_1 is True and all_zero_2 is True:
            # calculate stat values
            for index, row in series_data_1.iterrows():
                row_array = np.expand_dims(row.to_numpy(), axis=0)
                stat_value = calculate_statistic(row_array, series_data_1.columns,
                                                 series_data_1["stat_name"][0].lower())
                # save the value to the 'stat_value' column
                series_data_1.at[index, 'stat_value'] = stat_value
            for index, row in series_data_2.iterrows():
                row_array = np.expand_dims(row.to_numpy(), axis=0)
                stat_value = calculate_statistic(row_array, series_data_2.columns,
                                                 series_data_2["stat_name"][0].lower())
                # save the value to the 'stat_value' column
                series_data_2.at[index, 'stat_value'] = stat_value

        corr = pg.corr(x=series_data_1['stat_value'],
                       y=series_data_2['stat_value'])['r'].tolist()[0]
        low_eqbound = self.config.get_config_value('low_eqbound')
        if not low_eqbound:
            low_eqbound = -0.001
        high_eqbound = self.config.get_config_value('high_eqbound')
        if not high_eqbound:
            high_eqbound = 0.001

        self.series_data = utils.tost_paired(len(series_data_1['stat_value']),
                                             statistics.mean(series_data_1['stat_value']),
                                             statistics.mean(series_data_2['stat_value']),
                                             statistics.stdev(series_data_1['stat_value']),
                                             statistics.stdev(series_data_2['stat_value']),
                                             corr,
                                             low_eqbound, high_eqbound,
                                             self.config.get_config_value('alpha')
                                             )
