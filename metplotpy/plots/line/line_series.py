"""
Class Name: ROCDiagramSeries
 """
__author__ = 'Tatiana Burek'
__email__ = 'met_help@ucar.edu'

import numpy as np
import itertools
import math

import metcalcpy.util.utils as utils
from plots.series import Series
from scipy.stats import norm


class LineSeries(Series):
    """
        Represents a ROC diagram series object
        of data points and their plotting style
        elements (line colors, markers, linestyles, etc.)

    """

    def __init__(self, config, idx: int, input_data, series_list: list, y_axis: int = 1):
        self.series_list = series_list
        self.series_name = ''
        self.series_data = None
        super().__init__(config, idx, input_data, y_axis)

    def _calc_point_stat(self, data: list) -> float:
        # calculate point stat
        if self.config.plot_stat == 'MEAN':
            point_stat = np.nanmean(data)
        elif self.config.plot_stat == 'MEDIAN':
            point_stat = np.nanmedian(data)
        elif self.config.plot_stat == 'SUM':
            point_stat = np.nansum(data)
        else:
            point_stat = None
        return point_stat

    def _create_series_points(self) -> dict:
        """

        """
        # Subset data based on self.all_series_vals that we acquired from the
        # config file

        all_fields_values = self.config.get_config_value('series_val_' + str(self.y_axis)).copy()

        if self.config._get_fcst_vars(self.y_axis):
            all_fields_values['fcst_var'] = list(self.config._get_fcst_vars(self.y_axis).keys())

        all_fields_values['stat_name'] = self.config.get_config_value('list_stat_' + str(self.y_axis))

        list_of_series_names = list(itertools.product(*all_fields_values.values()))
        all_fields_values_no_indy = all_fields_values.copy()

        if self.idx < len(list_of_series_names):
            # this is a normal series
            self.series_name = list_of_series_names[self.idx]
            all_filters = []
            for field_ind, field in enumerate(all_fields_values_no_indy.keys()):
                filter_value = self.series_name[field_ind]
                if "," in filter_value:
                    filter_list = filter_value.split(',')
                elif ";" in filter_value:
                    filter_list = filter_value.split(';')
                else:
                    filter_list = [filter_value]
                for i, filter_val in enumerate(filter_list):
                    if utils.is_string_integer(filter_val):
                        filter_list[i] = int(filter_val)

                all_filters.append((self.input_data[field].isin(filter_list)))
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

            # TODO  check if the input frame already has diff series ( from calculation agg stats )

            derived_series_index = self.idx - len(self.config.get_series_y(self.y_axis))

            self.series_name = self.config.get_config_value('derived_series_' + str(self.y_axis))[
                derived_series_index]
            series_name_1 = self.series_name[0].split()
            series_name_2 = self.series_name[1].split()
            operation = self.series_name[2]

            # find original series
            for series in self.series_list:
                if set(series_name_1) == set(series.series_name):
                    series_1 = series
                if set(series_name_2) == set(series.series_name):
                    series_2 = series
            name = utils.get_derived_curve_name([self.series_name[0], self.series_name[1], operation])
            for field in all_fields_values_no_indy:
                self.series_data = self.input_data.loc[self.input_data[field] == name]
                if len(self.series_data) > 0:
                    break

            # check if the input frame already has diff series ( from calculation agg stats )
            if len(self.series_data) == 0:

                for indy in self.config.indy_vals:
                    if utils.is_string_integer(indy):
                        indy = int(indy)

                    # check if the input frame already has diff series ( from calculation agg stats )

                    stats_indy_1 = series_1.series_data.loc[series_1.series_data[self.config.indy_var] == indy]
                    stats_indy_2 = series_2.series_data.loc[series_2.series_data[self.config.indy_var] == indy]

                    # validate data
                    if 'fcst_valid_beg' in stats_indy_1.columns:
                        unique_dates = \
                        stats_indy_1[['fcst_valid_beg', 'fcst_lead', 'stat_name']].drop_duplicates().shape[0]
                    elif 'fcst_valid' in stats_indy_1.columns:
                        unique_dates = stats_indy_1[['fcst_valid', 'fcst_lead', 'stat_name']].drop_duplicates().shape[0]
                    elif 'fcst_init_beg' in stats_indy_1.columns:
                        unique_dates = \
                        stats_indy_1[['fcst_init_beg', 'fcst_lead', 'stat_name']].drop_duplicates().shape[0]
                    else:
                        unique_dates = stats_indy_1[['fcst_init', 'fcst_lead', 'stat_name"']].drop_duplicates().shape[0]
                    if stats_indy_1.shape[0] != unique_dates:
                        raise ValueError(
                            'Derived curve can\'t be calculated. Multiple values for one valid date/fcst_lead')

                    # data should be sorted

                    stats_values = utils.calc_derived_curve_value(stats_indy_1['stat_value'].tolist(),
                                                                  stats_indy_2['stat_value'].tolist(),
                                                                  operation)
                    stats_indy_1 = stats_indy_1.drop(columns=['stat_value'])
                    stats_indy_1['stat_value'] = stats_values

                    if 'stat_bcl' in stats_indy_1.columns:
                        stats_values = utils.calc_derived_curve_value(stats_indy_1['stat_bcl'].tolist(),
                                                                      stats_indy_2['stat_bcl'].tolist(),
                                                                      operation)
                        stats_indy_1 = stats_indy_1.drop(columns=['stat_bcl'])
                        stats_indy_1['stat_bcl'] = stats_values

                    if 'stat_bcu' in stats_indy_1.columns:
                        stats_values = utils.calc_derived_curve_value(stats_indy_1['stat_bcu'].tolist(),
                                                                      stats_indy_2['stat_bcu'].tolist(),
                                                                      operation)
                        stats_indy_1 = stats_indy_1.drop(columns=['stat_bcu'])
                        stats_indy_1['stat_bcu'] = stats_values

                    if self.series_data is None:
                        self.series_data = stats_indy_1
                    else:
                        self.series_data = self.series_data.append(stats_indy_1)

        series_points_results = {'dbl_lo_ci': [], 'dbl_med': [], 'dbl_up_ci': [], 'nstat': []}
        # for each point
        for point_ind, indy in enumerate(self.config.indy_vals):
            if utils.is_string_integer(indy):
                indy = int(indy)

            point_data = self.series_data.loc[self.series_data[self.config.indy_var] == indy]

            if len(point_data) > 0:

                # calculate point stat
                point_stat = self._calc_point_stat(point_data['stat_value'].tolist())

                series_ci = self.config.get_config_value('plot_ci')[self.idx].upper()
                dbl_lo_ci = 0
                dbl_up_ci = 0

                if 'STD' == series_ci:
                    std_err_vals = None
                    if self.config.plot_stat == 'MEAN':
                        std_err_vals = utils.compute_std_err_from_mean(point_data['stat_value'].tolist())

                    elif self.config.plot_stat == 'MEDIAN':
                        if self.config.variance_inflation_factor is True:
                            std_err_vals = utils.compute_std_err_from_median_variance_inflation_factor(
                                point_data['stat_value'].tolist())
                        else:
                            std_err_vals = utils.compute_std_err_from_median_no_variance_inflation_factor(
                                point_data['stat_value'].tolist())

                    elif self.config.plot_stat == 'SUM':
                        std_err_vals = utils.compute_std_err_from_sum(point_data['stat_value'].tolist())

                    if std_err_vals is not None and std_err_vals[1] == 0:
                        dbl_alpha = self.config.parameters['alpha']
                        dbl_z = norm.ppf(1 - (dbl_alpha / 2))
                        dbl_z_val = (dbl_z + dbl_z / math.sqrt(2)) / 2
                        dbl_std_err = dbl_z_val * std_err_vals[0]
                        dbl_lo_ci = dbl_std_err
                        dbl_up_ci = dbl_std_err
                elif 'BOOT' == series_ci:
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

                elif 'NORM' == series_ci:
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

            series_points_results['dbl_lo_ci'].append(dbl_lo_ci)
            series_points_results['dbl_med'].append(point_stat)
            series_points_results['dbl_up_ci'].append(dbl_up_ci)
            series_points_results['nstat'].append(len(point_data['stat_value']))

        return series_points_results
