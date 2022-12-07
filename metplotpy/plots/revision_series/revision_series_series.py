# ============================*
# ** Copyright UCAR (c) 2022
# ** University Corporation for Atmospheric Research (UCAR)
# ** National Center for Atmospheric Research (NCAR)
# ** Research Applications Lab (RAL)
# ** P.O.Box 3000, Boulder, Colorado, 80307-3000, USA
# ============================*


"""
Class Name: RevisionSeriesSeries
 """

import math
import re
from datetime import datetime
import numpy as np
import pandas as pd

import metcalcpy.util.utils as utils
from metcalcpy.util.wald_wolfowitz_runs_test import runs_test
from metcalcpy.util.correlation import acf

from ..line.line_series import LineSeries


class RevisionSeriesSeries(LineSeries):
    """
        Represents a RevisionSeries plot series object
        of data points and their plotting style
        elements (line colors, markers, linestyles, etc.)

    """

    def _create_series_points(self) -> dict:
        """
        Subset the data for the appropriate series.
        Calculate values for each point

        Args:

        Returns:
               dictionary with point values and  stats as keys
        """
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

            # print a message if needed for inconsistent beta_values
            self._check_beta_value()

        # sort data by fcst_valid_beg ascending and fcst_lead descending
        self.series_data = self.series_data.sort_values(by=['fcst_valid_beg', 'fcst_lead'], ascending=[True, False])
        # get unique fcst_valid_beg
        unique_fcst_valid_beg = self.series_data.fcst_valid_beg.unique()

        labels_for_x = []
        result = None

        # suppress the warning by changing the default behavior
        pd.set_option('mode.chained_assignment', None)

        # for each fcst_valid_beg calculate the differences
        for valid in unique_fcst_valid_beg:
            data_for_valid = self.series_data.loc[self.series_data['fcst_valid_beg'] == valid]
            data_for_valid.reset_index(drop=True, inplace=True)
            # make sure that the data is valid
            # each valid date/time should have a unique list of lead times
            # if the list is not unique - throw an error
            fcst_leads = data_for_valid['fcst_lead'].tolist()
            if len(set(fcst_leads)) != len(fcst_leads):
                raise ValueError(
                    "Valid date " + valid + " for " + self.user_legends + " doesn't have unique lead times.")

            for i in range(len(data_for_valid)):
                if i < len(data_for_valid) - 1:
                    data_for_valid.loc[i, 'stat_value'] = data_for_valid.loc[i + 1, 'stat_value'] - data_for_valid.loc[
                        i, 'stat_value']
                    data_for_valid.loc[i, 'fcst_lead'] = ''
                else:
                    data_for_valid.loc[i, 'stat_value'] = None
                    datetime_object = datetime.fromisoformat(data_for_valid.loc[i, 'fcst_valid_beg'])
                    data_for_valid.loc[i, 'fcst_lead'] = datetime_object.strftime('%m-%d %H')
            labels_for_x.extend(data_for_valid['fcst_lead'].tolist())
            if result is None:
                result = data_for_valid
            else:
                result = pd.concat([result, data_for_valid])

        series_points_results = {
            'revision_run': None,
            'auto_cor_r': None,
            'auto_cor_p': None,
            'points': result}

        if self.config.revision_run:
            p_value = runs_test(result['stat_value'].tolist(), alternative="left.sided")['p_value']
            series_points_results['revision_run'] = p_value
            if p_value is not None and not pd.isna(p_value):
                p_value = str(utils.round_half_up(p_value, 2))
            else:
                p_value = 'N/A'
            self.user_legends = self.user_legends + '(WW Runs Test:' + p_value + ')'

        if self.config.revision_ac:
            acf_value = acf(result['stat_value'].tolist(), 'correlation')

            r_value = acf_value[1]
            p_value = 0.06270678 / math.sqrt(np.size(result['stat_value']))
            series_points_results['auto_cor_r'] = r_value
            series_points_results['auto_cor_p'] = p_value
            if p_value is not None and not pd.isna(p_value):
                p_value = str(utils.round_half_up(p_value, 2))
            else:
                p_value = 'N/A'
            if r_value is not None and not pd.isna(r_value):
                r_value = str(utils.round_half_up(r_value, 2))
            else:
                r_value = 'N/A'
            self.user_legends = self.user_legends + "(Auto-Corr Test: p=" + p_value + ",r=" + r_value + ")"

        return series_points_results
