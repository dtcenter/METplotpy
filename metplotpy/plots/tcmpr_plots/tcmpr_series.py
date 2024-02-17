# ============================*
# ** Copyright UCAR (c) 2020
# ** University Corporation for Atmospheric Research (UCAR)
# ** National Center for Atmospheric Research (NCAR)
# ** Research Applications Lab (RAL)
# ** P.O.Box 3000, Boulder, Colorado, 80307-3000, USA
# ============================*


"""
Class Name: TcmprSeries
 """

import re
from typing import Union

import numpy as np
import pandas as pd
from pandas import DataFrame

import metcalcpy.util.utils as utils
from .tcmpr_util import get_prop_ci
from ..series import Series


class TcmprSeries(Series):
    """
        Represents a tcmpr plot series object
        of data points and their plotting style
        elements (line colors,  etc.)

    """

    def __init__(self, config, idx: int, input_data, series_list: list,
                 series_name: Union[list, tuple], skill_ref_data: DataFrame = None):
        self.series_list = series_list
        self.series_name = series_name
        self.rank_min_val = []
        # self.series_len = len(config.get_series_y(1)) + len(config.get_config_value('derived_series_1'))
        self.series_len = len(self.series_list) + len(config.get_config_value('derived_series_1'))
        self.skill_ref_data = skill_ref_data
        if idx >= self.series_len:
            super().__init__(config, 0, input_data, 1)
        else:
            super().__init__(config, idx, input_data, 1)
        self.idx = idx

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
        all_fields_values_no_indy[1] = all_fields_values

        return all_fields_values_no_indy

    def _create_series_points(self) -> dict:
        """
        Subset the data for the appropriate series.
        Calculate values for each point including CI

        Args:

        Returns:
               dictionary with CI ,point values and number of stats as keys
        """

        self._init_series_data()

        series_points_results = {'val': [], 'ncl': [], 'ncu': [], 'nstat': [], 'mean': []}

        # for each point calculate plot statistic
        for indy in self.config.indy_vals:
            if utils.is_string_integer(indy):
                indy = int(indy)
            elif utils.is_string_strictly_float(indy):
                indy = float(indy)
            point_data = self.series_data.loc[
                (self.series_data["LEAD_HR"] == indy)]
            point_data = point_data.sort_values(by=['CASE'])

            series_points_results['nstat'].append(len(point_data.index))
            if len(point_data) == 0:
                series_points_results['mean'].append(None)
            else:
                series_points_results['mean'].append(np.nanmean(point_data['PLOT'].tolist()))

        return series_points_results

    def _init_series_data(self):
        # different ways to subset data for normal and derived series

        if len(self.series_name) == 1 or self.series_name[-1] not in utils.OPERATION_TO_SIGN.keys():
            # this is a normal series
            all_filters = []

            # create a set of filters for this series
            for field_ind, field in enumerate(self.all_fields_values_no_indy[self.y_axis].keys()):
                filter_value = self.series_name[field_ind]
                if isinstance(filter_value, str) and utils.GROUP_SEPARATOR in filter_value:
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

            # use numpy to select the rows where any record evaluates to True
            mask = np.array(all_filters).all(axis=0)
            self.series_data = self.input_data.loc[mask]

            # sort data by date/time/storm - needed for CI calculations
            self.series_data = self.series_data.sort_values(['VALID', 'LEAD', 'STORM_ID'])

        else:
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

            self._calculate_derived_values(operation, series_data_1, series_data_2)

    def create_relperf_points(self, case_data):
        print('Case_data size =' + str(len(case_data.index)))
        for indy in self.config.indy_vals:

            if utils.is_string_integer(indy):
                indy = int(indy)
            elif utils.is_string_strictly_float(indy):
                indy = float(indy)
                print("indy float =" + str(indy))
            if self.idx >= self.series_len:
                series_val = self.series_name[0]
            else:
                series_val = self.config.series_vals_1[0][self.idx]
            case_data_indy = case_data[case_data['LEAD_HR'] == indy]
            # Get counts
            n_cur = len(case_data_indy[case_data_indy['PLOT'] == series_val])
            n_tot = len(case_data_indy)
            # Compute the current relative performance and CI
            s = get_prop_ci(n_cur, n_tot, self.config.n_min, self.config.alpha)
            self.series_points['ncl'].append(s['ncl'])
            self.series_points['val'].append(s['val'])
            self.series_points['ncu'].append(s['ncu'])

    def create_rank_points(self, case_data):
        for indy in self.config.indy_vals:
            if utils.is_string_integer(indy):
                indy = int(indy)
            elif utils.is_string_strictly_float(indy):
                indy = float(indy)
            case_data_indy = case_data[case_data['LEAD_HR'] == indy]
            case_data_indy = case_data_indy.dropna(subset=['RANK_RANDOM'], how='all')
            # Get counts
            n_cur = len(case_data_indy[case_data_indy['RANK_RANDOM'] == self.idx + 1])
            n_tot = len(case_data_indy)
            # Compute the current relative performance and CI
            s = get_prop_ci(n_cur, n_tot, self.config.n_min, self.config.alpha)
            ci_data = s['val']

            self.series_points['ncl'].append(s['ncl'])
            self.series_points['val'].append(ci_data)
            self.series_points['ncu'].append(s['ncu'])

            if self.idx == 0 or len(self.config.all_series_y1) == self.idx + 1:
                case_data_indy = case_data[case_data['LEAD_HR'] == indy]
                case_data_indy = case_data_indy.dropna(subset=['RANK_MIN'], how='all')
                n_cur = len(case_data_indy[case_data_indy['RANK_MIN'] == self.idx + 1])
                n_tot = len(case_data_indy)
                rank_min = 100 * n_cur / n_tot
                self.rank_min_val.append(rank_min)

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
                series_data_1.loc[series_data_1['LEAD_HR'] == indy]
            stats_indy_2 = \
                series_data_2.loc[series_data_2['LEAD_HR'] == indy]

            # validate data

            unique_dates = \
                stats_indy_1[['VALID', 'LEAD_HR', 'BMODEL', 'STORM_ID']].drop_duplicates().shape[0]

            if stats_indy_1.shape[0] != unique_dates:
                raise ValueError(
                    'Derived curve can\'t be calculated. '
                    'Multiple values for one valid date/LEAD_HR')

            # data should be sorted   by fcst_init_beg !!!!!
            stats_values = utils.calc_derived_curve_value(stats_indy_1['PLOT'].tolist(),
                                                          stats_indy_2['PLOT'].tolist(),
                                                          operation)

            stats_indy_1['PLOT'] = stats_values

            if self.series_data is None:
                self.series_data = stats_indy_1
            else:
                self.series_data = pd.concat([self.series_data, stats_indy_1], sort=False)
