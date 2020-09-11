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

    def __init__(self, config, idx: int, input_data, y_axis: int = 1):
        super().__init__(config, idx, input_data, y_axis)

    def _create_series_points(self):
        """
           Subset the data for the appropriate series.  Data input can
           originate from CTC linetype or PCT linetype.  The methodology
           will depend on the linetype.

           Args:

           Returns:
               tuple of three lists:
                                   pody (Probability of detection) and
                                   pofd (probability of false detection/
                                         false alarm rate)
                                   thresh (threshold value, used to annotate)


        """
        # Subset data based on self.all_series_vals that we acquired from the
        # config file

        all_fields_values = self.config.get_config_value('series_val_' + str(self.y_axis)).copy()

        if self.config._get_fcst_vars(self.y_axis):
            all_fields_values['fcst_var'] = list(self.config._get_fcst_vars(self.y_axis).keys())

        all_fields_values['stat_name'] = self.config.get_config_value('list_stat_' + str(self.y_axis))

        if self.config.indy_vals:
            all_fields_values[self.config.indy_var] = self.config.indy_vals

        all_points = list(itertools.product(*all_fields_values.values()))

        # calculate index adjustment for y2 axis
        y2_ind_adjust = 0
        if self.y_axis == 2:
            y2_ind_adjust = len(self.config.all_series_y1)

        start_index = (self.idx-y2_ind_adjust) * len(self.config.indy_vals)
        end_index = start_index + len(self.config.indy_vals)
        series_points = all_points[start_index: end_index]

        series_points_results = {'dbl_lo_ci': [], 'dbl_med': [], 'dbl_up_ci': [], 'nstat': []}
        # for each point
        for point_ind, point in enumerate(series_points):
            all_filters = []
            for field_ind, field in enumerate(all_fields_values.keys()):
                filter_value = point[field_ind]
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
            point_data = self.input_data.loc[mask]

            # sort data by date/time - needed for CI calculations
            if 'fcst_valid_beg' in point_data.columns:
                point_data = point_data.sort_values(['fcst_valid_beg', 'fcst_lead'])
            elif 'fcst_valid' in point_data.columns:
                point_data = point_data.sort_values(['fcst_valid', 'fcst_lead'])

            # calculate point stat
            if self.config.plot_stat == 'MEAN':
                point_stat = np.nanmean(point_data['stat_value'])
            elif self.config.plot_stat == 'MEDIAN':
                point_stat = np.nanmedian(point_data['stat_value'])
            elif self.config.plot_stat == 'SUM':
                point_stat = np.nansum(point_data['stat_value'])
            else:
                point_stat = None

            series_ci = self.config.plot_ci[self.idx]
            dbl_lo_ci = 0
            dbl_up_ci = 0

            if 'STD' == series_ci and len(point_data) > 0:
                std_err_vals = None
                if self.config.plot_stat == 'MEAN':
                    std_err_vals = utils.compute_std_err_from_mean(point_data['stat_value'].tolist())

                elif self.config.plot_stat == 'MEDIAN':
                    if  self.config.variance_inflation_factor is True:
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

            series_points_results['dbl_lo_ci'].append(dbl_lo_ci)
            series_points_results['dbl_med'].append(point_stat)
            series_points_results['dbl_up_ci'].append(dbl_up_ci)
            series_points_results['nstat'].append(len(point_data['stat_value']))

        return series_points_results
