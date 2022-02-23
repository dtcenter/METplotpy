"""
Class Name: ContourSeries
 """
__author__ = 'Tatiana Burek'

from typing import Union
import numpy as np

from ..series import Series


class ContourSeries(Series):
    """
        Represents a Contour plot series object
        of data points and their plotting style
        elements (linestyles, etc.)

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
        for field in reversed(list(all_fields_values_orig.keys())):
            all_fields_values[field] = all_fields_values_orig.get(field)

        if self.config._get_fcst_vars(1):
            all_fields_values['fcst_var'] = list(self.config._get_fcst_vars(1).keys())
        all_fields_values['stat_name'] = self.config.get_config_value('list_stat_1')
        all_fields_values_no_indy[1] = all_fields_values

        return all_fields_values_no_indy

    def _calc_point_stat(self, data: list) -> Union[float, None]:
        """
        Calculates the statistic specified in the config 'plot_stat' parameter
        using input data list
        :param data: list os numbers
        :return:  mean, median or sum of the values from the input list or
            None if the statistic parameter is invalid
        """
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
        Subset the data for the appropriate series.
        Calculate values for each point

        Args:

        Returns:
               dictionary with x, y and z point values
        """

        y_real = self.config.indy_vals.copy()
        if self.config.reverse_x is True:
            y_real.reverse()

        x_real = self.config.series_vals_1[0].copy()
        if self.config.reverse_y is True:
            x_real.reverse()

        z = [[None for i in range(len(y_real))] for j in range(len(x_real))]
        for ind_y, y in enumerate(y_real):
            for ind_x, x in enumerate(x_real):
                all_filters = [self.input_data[self.config.indy_var].isin([y]),
                               self.input_data[self.config.series_val_names[0]].isin([x])]
                mask = np.array(all_filters).all(axis=0)
                data = self.input_data.loc[mask]
                z[ind_x][ind_y] = self._calc_point_stat(data['stat_value'])

        return {'x': y_real, 'y': x_real, 'z': z}
