"""
Class Name: TaylorDiagramSeries
"""
__author__ = 'Minna Win'

import collections
from collections import namedtuple
import pandas

from plots.series import Series
import metcalcpy.util.utils as calcpy_utils



class TaylorDiagramSeries(Series):
    """
       Represents a Taylor Diagram series object of data points:
       standard deviation, correlation coefficient from
       MET output file.
    """

    def __init__(self, config, idx, input_data):
        # idx is the index number of the series (i.e. a permutation of all
        # possible series values).
        super().__init__(config, idx, input_data)

    def _subset_data(self, input_df) -> pandas.DataFrame:
        """
            Args:
              :param input_df: The pandas dataframe representation of the full data to be subset.
            Returns:
                subsetted_df:  The portion of the full dataset that corresponds to the column header(s)
                            and rows of interest.

        """

        # Work on a copy of the original dataframe so we can subset the
        # original dataframe based on the columns we need.
        df_by_columns = input_df.copy(deep=True)

        # For Taylor Diagrams we need the stat_name column that contains the
        # OSTDEV, FSTDEV, RMSE, and PR_CORR labels and the
        # column stat_value, which has the corresponding values that are needed for plotting.
        # We also need the names of the series_val_1 names (i.e. model, vx_mask, etc.)
        columns_of_interest = [columns_of_interest for columns_of_interest in self.series_val_names]
        relevant_columns = columns_of_interest

        # These columns are required for getting the statistics values to plot, add
        # these to the list of columns of interest.
        required_columns = ['stat_name', 'fcst_var', 'stat_value']
        for required in required_columns:
            relevant_columns.append(required)

        df_by_columns = df_by_columns[relevant_columns]

        # only one fcst var value allowed for Taylor diagram, first subset
        # based on this to simplify the query string for subsetting based on
        # the series val names and variable permutations.
        fcst_var_val = self.fcst_vars_1
        subsetted_df = df_by_columns[df_by_columns['fcst_var'] == str(fcst_var_val[0])]

        return subsetted_df

    def _create_series_points(self) -> collections.namedtuple:
        """
           Subset the MET output data into an individual series consisting of values of standard
           deviation and correlation coefficient

           Args:
            Returns:
               a named tuple that represent the standard deviations (max between the reference and forecast stdev),
               RMSE, and Pearson correlation coefficient.

        """

        # Subset the initial dataframe (i.e. the one that contains *all* the
        # input data and columns from the MET input file).
        permutations_list = calcpy_utils.create_permutations(self.all_series_vals)
        self.subsetted_df = self._subset_data(self.input_data)

        # Determine which series this corresponds to.
        cur_perm = permutations_list[self.idx]

        qstr = self.series_val_names[0] + "==" + '"' + cur_perm[0] + '"' + " & " + self.series_val_names[
            1] + "==" + '"' + cur_perm[1] + '"'

        # retrieve the row of data corresponding to this current permutation/series
        fstdev_query = qstr + " & " + 'stat_name == "FSTDEV"'
        ostdev_query = qstr + " & " + 'stat_name == "OSTDEV"'
        corr_query = qstr + " & " + 'stat_name == "PR_CORR"'

        fstdev_results = self.subsetted_df.query(fstdev_query)['stat_value'].values[0]
        ostdev_results = self.subsetted_df.query(ostdev_query)['stat_value'].values[0]

        # for the stdev, pick the max value between fstdev and ostdev
        stdev_results = max(fstdev_results, ostdev_results)
        corr_results = self.subsetted_df.query(corr_query)['stat_value'].values[0]

        # Create a named tuple to return
        TaylorStats = namedtuple('TaylorStats', ['fstdev', 'ostdev', 'pr_corr'])
        series_stats = TaylorStats(fstdev=fstdev_results, ostdev=ostdev_results, pr_corr=corr_results)

        return series_stats
