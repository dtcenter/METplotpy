# ============================*
# ** Copyright UCAR (c) 2023
# ** University Corporation for Atmospheric Research (UCAR)
# ** National Center for Atmospheric Research (NCAR)
# ** Research Applications Lab (RAL)
# ** P.O.Box 3000, Boulder, Colorado, 80307-3000, USA
# ============================*


"""
Class Name: TcmprSeriesScatter
 """

import re
from typing import Union

import numpy as np

import metcalcpy.util.utils as utils
from metplotpy.plots.series import Series


class TcmprSeriesScatter(Series):
    """
        Represents a Box plot series object
        of data points and their plotting style
        elements (line colors,  etc.)

    """

    def __init__(self, config, idx: int, input_data, series_list: list,
                 series_name: Union[list, tuple]):
        self.series_list = series_list
        self.series_name = series_name
        super().__init__(config, idx, input_data, 1)

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

        # different ways to subset data for normal and derived series
        # this is a normal series
        all_filters = []

        # create a set of filters for this series
        for field_ind, field in enumerate(self.all_fields_values_no_indy[self.y_axis].keys()):
            if field == 'LEAD':
                field = 'LEAD_HR'
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

        mask = np.array(all_filters).all(axis=0)
        self.series_data = self.input_data.loc[mask]

        # sort data by date/time/storm - needed for CI calculations
        self.series_data = self.series_data.sort_values(['VALID', 'LEAD', 'STORM_ID'])

        series_points_results = {'val': [], 'ncl': [], 'ncu': [], 'nstat': []}
        return series_points_results
