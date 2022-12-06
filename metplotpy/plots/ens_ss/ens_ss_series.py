# ============================*
 # ** Copyright UCAR (c) 2022
 # ** University Corporation for Atmospheric Research (UCAR)
 # ** National Center for Atmospheric Research (NCAR)
 # ** Research Applications Lab (RAL)
 # ** P.O.Box 3000, Boulder, Colorado, 80307-3000, USA
 # ============================*
 
 
 
"""
Class Name: EnsSsSeries
 """
__author__ = 'Tatiana Burek'

from typing import Union
import pandas as pd

import numpy as np

import metcalcpy.util.utils as utils
from .. import GROUP_SEPARATOR

from ..series import Series


class EnsSsSeries(Series):
    """
        Represents a ens_ss plot series object
        of data points and their plotting style
        elements (ens_ss colors, markers, linestyles, etc.)

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
        all_fields_values_no_indy[1] = all_fields_values

        return all_fields_values_no_indy

    def _create_series_points(self) -> dict:
        """
        Subset the data for the appropriate series.
        Calculates values for each point including CI

        Args:

        Returns:
               dictionary with CI ,point values and number of stats as keys
        """

        # different ways to subset data for normal and derived series
        # this is a normal series
        all_filters = []

        # create a set of filters for this series
        for field_ind, field in enumerate(self.all_fields_values_no_indy[self.y_axis].keys()):
            filter_value = self.series_name[field_ind]
            if utils.GROUP_SEPARATOR in filter_value:
                filter_list = filter_value.split(GROUP_SEPARATOR)
                # add the original value
                filter_list.append(filter_value)
            elif ";" in filter_value:
                filter_list = filter_value.split(';')
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
        if len(self.config.indy_var) > 0:
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

        agg_bin_n = self.series_data[['bin_n', 'var_min']].groupby('var_min').agg('sum')['bin_n'].tolist()

        # aggregate the bins with matching variance limits
        aggregates = pd.DataFrame(list(zip(agg_bin_n,
                                          self._aggregate_column('var_mean', agg_bin_n),
                                          self._aggregate_column('fbar', agg_bin_n),
                                          self._aggregate_column('obar', agg_bin_n),
                                          self._aggregate_column('fobar', agg_bin_n),
                                          self._aggregate_column('ffbar', agg_bin_n),
                                          self._aggregate_column('oobar', agg_bin_n)
                                          )),
                                 columns=['bin_n', 'var_mean', 'fbar', 'obar', 'fobar', 'ffbar', 'oobar'])

        # if the number of binned points is not specified, use a default
        binned_points = self.config.ensss_pts
        if binned_points < 1:
            num_pts = sum(aggregates['bin_n'])
            if num_pts > 10:
                binned_points = num_pts / 10
            else:
                binned_points = 1
        # initialize storage
        spread_skill_values = []
        mse_values = []
        pts_values = []
        current_bins = None

        # build bins with roughly equals amounts of points
        for index, row in aggregates.iterrows():
            # if the bin is large enough, calculate a spread/skill point
            if (current_bins is not None) and (binned_points < sum(current_bins['bin_n']) or index == len(aggregates.index) - 1):
                scale = 1 / sum(current_bins['bin_n'])
                spread_skill = scale * sum(current_bins['bin_n'] * current_bins['var_mean'])
                mse = scale * (sum(current_bins['bin_n'] * current_bins['ffbar']) - 2 * sum(current_bins['bin_n'] * current_bins['fobar']) + sum(
                    current_bins['bin_n'] * current_bins['oobar']))
                spread_skill_values.append(spread_skill)
                mse_values.append(mse)
                pts_values.append(sum(current_bins['bin_n']))
                current_bins = None
            # add a new row to the current bin
            if current_bins is None:
                current_bins = pd.DataFrame([row])
            else:
                # current_bins = current_bins.append(pd.DataFrame([row]))
                current_bins = pd.concat([current_bins, pd.DataFrame([row])])

        series_points_results = {'spread_skill': spread_skill_values, 'mse': mse_values, 'pts': pts_values}

        return series_points_results

    def _aggregate_column(self, column_name: str, agg_bin_n: list) -> list:
        a = self.series_data[['bin_n', 'var_min', column_name]]
        a['bin_n'] = a['bin_n'] * a[column_name]
        agg_list = a[['bin_n', 'var_min']].groupby('var_min').agg('sum')['bin_n'].tolist()
        return [i / j for i, j in zip(agg_list, agg_bin_n)]
