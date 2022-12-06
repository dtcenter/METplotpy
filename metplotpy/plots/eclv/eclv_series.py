# ============================*
 # ** Copyright UCAR (c) 2022
 # ** University Corporation for Atmospheric Research (UCAR)
 # ** National Center for Atmospheric Research (NCAR)
 # ** Research Applications Lab (RAL)
 # ** P.O.Box 3000, Boulder, Colorado, 80307-3000, USA
 # ============================*
 
 
 
"""
Class Name: EclvSeries
 """
__author__ = 'Tatiana Burek'

import math

import numpy as np
from scipy.stats import norm

import metcalcpy.util.utils as utils
from ..line.line_series import LineSeries


class EclvSeries(LineSeries):
    """
        Represents a Economic Cost Loss Relative Value plot series object
        of data points and their plotting style
        elements (line colors, markers, linestyles, etc.)

    """

    def _create_series_points(self) -> list:
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

        # init the list of thresholds
        if 'thresh_i' in self.series_data.columns:
            list_thresh = self.series_data['thresh_i'].unique().tolist()
        else:
            list_thresh = [0]

        series_points_results = []

        dbl_alpha = self.config.parameters['alpha']
        dbl_z = norm.ppf(1 - (dbl_alpha / 2))
        dbl_z_val = (dbl_z + dbl_z / math.sqrt(2)) / 2

        for thresh in list_thresh:
            series_points_for_thresh = {'dbl_lo_ci': [], 'dbl_med': [], 'dbl_up_ci': [], 'nstat': [], 'x_pnt': []}
            if 'thresh_i' in self.series_data.columns:
                thresh_series_data = self.series_data.loc[self.series_data['thresh_i'] == thresh]
            else:
                thresh_series_data = self.series_data

            if 'stat_bcl' in self.series_data.columns:
                unique_x_pnt_i = thresh_series_data['x_pnt_i'].tolist()
            else:
                unique_x_pnt_i = thresh_series_data['x_pnt_i'].unique().tolist()
            unique_x_pnt_i.sort()

            #for each x_pnt_i calculate statistic and CIs
            for ind_x_pnt_i, x_pnt_i in enumerate(unique_x_pnt_i):
                if 'stat_bcl' in self.series_data.columns:
                    point_data = thresh_series_data[ind_x_pnt_i]
                else:
                    point_data = thresh_series_data.loc[thresh_series_data['x_pnt_i'] == x_pnt_i]

                if len(point_data) > 0:
                    # calculate point stat
                    point_stat = self._calc_point_stat(point_data['y_pnt_i'].tolist())

                    # calculate CI
                    dbl_lo_ci = 0
                    dbl_up_ci = 0
                    series_ci = self.config.get_config_value('plot_ci')[self.idx].upper()

                    # count al values that are not non and more than 0
                    nansum = 0
                    for val in point_data['y_pnt_i'].tolist():
                        if not np.isnan(val) and val != 0.0:
                            nansum = nansum + 1

                    if series_ci == 'STD' and nansum > 0:
                        std_err_vals = None
                        if self.config.plot_stat == 'MEAN':
                            std_err_vals = utils.compute_std_err_from_mean(point_data['y_pnt_i'].tolist())

                        elif self.config.plot_stat == 'MEDIAN':
                            std_err_vals = utils.compute_std_err_from_median_no_variance_inflation_factor(
                                point_data['y_pnt_i'].tolist())

                        elif self.config.plot_stat == 'SUM':
                            std_err_vals = utils.compute_std_err_from_sum(point_data['y_pnt_i'].tolist())

                        if std_err_vals is not None and std_err_vals[1] == 0:
                            dbl_std_err = dbl_z_val * std_err_vals[0]
                            dbl_lo_ci = dbl_std_err
                            dbl_up_ci = dbl_std_err

                    elif series_ci == 'BOOT':
                        stat_btcu = 0
                        stat_btcl = 0
                        if 'stat_btcu' in point_data.head() and 'stat_btcl' in point_data.head():
                            stat_btcu = self._calc_point_stat(point_data['stat_btcu'].tolist())
                            stat_btcl = self._calc_point_stat(point_data['stat_btcl'].tolist())
                            if stat_btcu == -9999:
                                stat_btcu = 0
                            if stat_btcl == -9999:
                                stat_btcl = 0

                        dbl_lo_ci = point_stat - stat_btcl
                        dbl_up_ci = stat_btcu - point_stat

                    elif series_ci == 'MET_BOOT':
                        stat_bcu = 0
                        stat_bcl = 0
                        if 'stat_bcu' in point_data.head() and 'stat_bcl' in point_data.head():
                            stat_bcu = self._calc_point_stat(point_data['stat_bcu'].tolist())
                            stat_bcl = self._calc_point_stat(point_data['stat_bcl'].tolist())
                            if stat_bcu == -9999:
                                stat_bcu = 0
                            if stat_bcl == -9999:
                                stat_bcl = 0

                        dbl_lo_ci = point_stat - stat_bcl
                        dbl_up_ci = stat_bcu - point_stat

                    elif series_ci == 'MET_PRM':
                        stat_ncu = 0
                        stat_ncl = 0
                        if 'stat_ncu' in point_data.head() and 'stat_ncl' in point_data.head():
                            stat_ncu = self._calc_point_stat(point_data['stat_ncu'].tolist())
                            stat_ncl = self._calc_point_stat(point_data['stat_ncl'].tolist())
                            if stat_ncu == -9999:
                                stat_ncu = 0
                            if stat_ncl == -9999:
                                stat_ncl = 0

                        dbl_lo_ci = point_stat - stat_ncl
                        dbl_up_ci = stat_ncu - point_stat

                else:
                    dbl_lo_ci = None
                    point_stat = None
                    dbl_up_ci = None

                series_points_for_thresh['dbl_lo_ci'].append(dbl_lo_ci)
                series_points_for_thresh['dbl_med'].append(point_stat)
                series_points_for_thresh['dbl_up_ci'].append(dbl_up_ci)
                series_points_for_thresh['x_pnt'].append(x_pnt_i)

                # calculate the number of records for thresh
                if 'nstats' in self.series_data.columns:
                    total = sum(point_data['nstats'].tolist())
                else:
                    total = sum(x is not None or np.isnan(x) is False for x in point_data['y_pnt_i'])

                # add number of records for thresh to the number of records for series
                if ind_x_pnt_i < len(series_points_for_thresh['nstat']):
                    series_points_for_thresh['nstat'][ind_x_pnt_i] = total + series_points_for_thresh['nstat'][ind_x_pnt_i]
                else:
                    series_points_for_thresh['nstat'].append(total)
            series_points_results.append(series_points_for_thresh)

        return series_points_results

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
