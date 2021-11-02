"""
Class Name: PhistSeries
 """
__author__ = 'Tatiana Burek'

import numpy as np

import metcalcpy.util.utils as utils
from plots.histogram.rlhist_series import RhistSeries


class PhistSeries(RhistSeries):
    """
        Represents a Probability Histogram or Histograms of probability integral transform series object
        of data points and their plotting style
        elements

    """

    def _create_series_points(self) -> list:
        """
        Subset the data for the appropriate series.
        Calculates values for each box

        Args:

        Returns:
        """

        all_filters = []

        # create a set of filters for this series
        for field_ind, field in enumerate(self.all_fields_values_no_indy[self.y_axis].keys()):
            filter_value = self.series_name[field_ind]
            filter_list = [filter_value]
            for i, filter_val in enumerate(filter_list):
                if utils.is_string_integer(filter_val):
                    filter_list[i] = int(filter_val)

            all_filters.append((self.input_data[field].isin(filter_list)))

        # use numpy to select the rows where any record evaluates to True
        if len(all_filters) > 0:
            mask = np.array(all_filters).all(axis=0)
            self.series_data = self.input_data.loc[mask]
        else:
            self.series_data = self.input_data

        # group by i_value, series value, calculate sums of rank_i and store them as stat_value
        sum_by_columns = ['i_value', 'bin_size']
        sum_by_columns.extend(self.config.series_val_names)
        self.series_data = self.series_data.groupby(sum_by_columns).agg(
            stat_value=('bin_i', 'sum')
        ).reset_index()

        if self.config.normalized_histogram is True:
            total_stat = self.series_data['stat_value'].sum()
            series_points_results = self.series_data.loc[:, 'stat_value'].apply(lambda x: x / total_stat).tolist()
        else:
            series_points_results = self.series_data.loc[:, 'stat_value'].tolist()

        return series_points_results
