"""
Class Name: LineSeries
 """
__author__ = 'Tatiana Burek'

from typing import Union
import re
import math

import numpy as np
from pandas import DataFrame
from statistics import mean, median
from itertools import groupby
from scipy.stats import norm

import metcalcpy.util.utils as utils
from plots.series import Series


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

                all_filters.append((self.input_data[field].isin(filter_list)))

            # filter by provided indy
            all_filters.append((self.input_data[self.config.indy_var].isin(self.config.indy_vals)))
            # use numpy to select the rows where any record evaluates to True
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

            point_data = self.series_data.loc[self.series_data[self.config.indy_var] == indy]
            if list(self.config._get_fcst_vars(self.y_axis).keys())[0].startswith('REV_'):
                stats = self._calculate_mtd_revision_stats()

            series_points_results['nstat'].append(len(point_data['stat_value']))

        return series_points_results

    def _calculate_mtd_revision_stats(self):
        subset = self.series_data[['stat_value', 'revision_id']]
        unique_ids = subset.revision_id.unique()
        data_for_stats = []
        for id in unique_ids:
            data_for_id = subset[subset['revision_id'] == id]['stat_value'].tolist()
            data_for_stats.extend(data_for_id)
            data_for_stats.extend([None])
        if len(data_for_stats) > 0:
            data_for_stats.pop()

        mean_val = mean(elem for elem in data_for_stats if elem is not None)

        def func(a):
            if a is not None:
                return a - mean_val
            else:
                return None

        data_for_stats = list(map(func, data_for_stats))
        acf_value = self.acf(data_for_stats, 'correlation', 2)
        r = acf_value[1]
        # qnorm((1 + 0.05)/2) = 0.06270678
        p_value = 0.06270678 / math.sqrt(np.size(data_for_stats))
        ww_run = self.run_test(data_for_stats, 'left.sided', 'median')['p_value']
        if ww_run is None:
            ww_run = None
        else:
            ww_run = round(ww_run, 2)
        if p_value is None:
            p_value = None
        else:
            p_value = round(p_value, 2)
        if r is None:
            r = None
        else:
            r = round(r, 2)
        return {
            'ww_run': ww_run,
            'auto_cor_p' : p_value,
            'auto_cor_r' : r
        }

    def run_test(self, x, alternative="two.sided", threshold='median') -> Union[None, dict]:
        '''
        Wald-Wolfowitz Runs Test.
        Performs the Wald-Wolfowitz runs test of randomness for continuous data.
        Mimicks runs.test Rscript function

        :param x: a numeric vector containing the observations
        :param alternative: a character string with the alternative hypothesis.
            Must be one of "two.sided" (default), "left.sided" or "right.sided".
        :param threshold: the cut-point to transform the data into a dichotomous vector
            Must be one of "median" (default) or "mean".
        :return: Wald-Wolfowitz Runs Test results as a dictionary
        '''
        if alternative != "two.sided" and alternative != "left.sided" and alternative != "right.sided":
            print("must give a valid alternative")
        x = [elem for elem in x if elem is not None]
        if threshold == 'median':
            x_threshold = median(x)
        elif threshold == "mean":
            x_threshold = mean(x)
        else:
            print('ERROR  incorrect threshold')
            x_threshold = None
        x = [elem for elem in x if elem != x_threshold]
        res = [i - x_threshold for i in x]
        s = np.sign(res)
        n1 = 0
        n2 = 0
        for num in s:
            if num > 0:
                n1 += 1
            elif num < 0:
                n2 += 1
        runs = [(k, sum(1 for i in g)) for k, g in groupby(s)]
        r1 = 0
        r2 = 0
        for run in runs:
            if run[0] == 1:
                r1 += 1
            elif run[0] == -1:
                r2 += 1
        n = n1 + n2
        mu = 1 + 2 * n1 * n2 / (n1 + n2)
        vr = 2 * n1 * n2 * (2 * n1 * n2 - n1 - n2) / (n * n * (n - 1))
        rr = r1 + r2
        pv = 0
        # pvalue == "normal"
        pv0 = norm.cdf((rr - mu) / math.sqrt(vr))
        if alternative == "two.sided":
            pv = 2 * min(pv0, 1 - pv0)
        if alternative == "left.sided":
            pv = pv0
        if alternative == "right.sided":
            pv = 1 - pv0

        return {
            'statistic': (rr - mu) / math.sqrt(vr),
            'p_value': pv,
            'runs': rr,
            'mu': mu,
            'var': vr
        }

    def acf(self, x, acf_type='correlation', lag_max=None) -> Union[list, None]:
        '''
        The function acf computes estimates of the autocovariance or autocorrelation function.
        Args:
            x - numeric array.
            acf_type - character string giving the type of acf to be computed.
                Allowed values are "correlation" (the default), "covariance".
            lag_max - maximum lag at which to calculate the acf.
                Default is 10*log10(N/m) where N is the number of observations and m the number of series.
                Will be automatically limited to one less than the number of observations in the series.


        :return:
        '''
        if acf_type not in ['covariance', 'correlation']:
            print('ERROR  incorrect acf_type')
            return None

        acf_result = []
        size = np.size(x)
        mean_val = mean(elem for elem in x if elem is not None)
        if lag_max is None:
            lag_max = math.floor(10 * (math.log10(size) - math.log10(1)))
        lag_max = int(min(lag_max, size - 1))
        cov_0 = self._autocovariance(x, size, 0, mean_val)
        for i in range(lag_max):
            cov = self._autocovariance(x, size, i, mean_val)
            if acf_type == 'covariance':
                acf_result.append(cov)
            elif acf_type == 'correlation':
                acf_result.append(cov / cov_0)

        return acf_result

    def _autocovariance(self, Xi, N, k, Xs):
        autoCov = 0
        total = 0
        for i in np.arange(0, N - k):
            if Xi[i + k] is not None and Xi[i] is not None:
                autoCov += ((Xi[i + k]) - Xs) * (Xi[i] - Xs)
                total = total + 1
        return (1 / (total + k)) * autoCov

    def _shift(self, x, b):
        if (b <= 0):
            return x
        d = np.array(x)
        d1 = d
        d1[b:] = d[:-b]
        d1[0:b] = 0
        return d1

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
                self.series_data = self.series_data.append(stats_indy_1, sort=False)
