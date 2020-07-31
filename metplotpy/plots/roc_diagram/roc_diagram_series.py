"""
Class Name: ROCDiagramSeries
 """
__author__ = 'Minna Win'
__email__ = 'met_help@ucar.edu'

import pandas as pd
import metcalcpy.util.ctc_statistics as cstats
import metcalcpy.util.pstd_statistics as pstats
import metcalcpy.util.utils as utils
from plots.series import Series

class ROCDiagramSeries(Series):
    """
        Represents a ROC diagram series object
        of data points and their plotting style
        elements (line colors, markers, linestyles, etc.)

    """
    def __init__(self, config, idx, input_data):
        super().__init__(config, idx, input_data)

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
        input_df = self.input_data
        series_num = self.series_order
        perm = utils.create_permutations(self.all_series_vals)
        if len(self.all_series_vals) > 0 :
            cur_perm = perm[series_num]
            subset_df = self._subset_data(input_df, cur_perm)
        else:
            # no subsetting of data required, no series_val_1 values
            # were specified in the config file.
            subset_df = input_df.copy()
        if self.config.linetype_ctc:
            df_roc = cstats.calculate_ctc_roc(subset_df)
            pody = df_roc['pody']
            pody = pd.Series([1]).append(pody, ignore_index=True)
            pody = pody.append(pd.Series([0]), ignore_index=True)
            pofd = df_roc['pofd']
            pofd = pd.Series([1]).append(pofd, ignore_index=True)
            pofd = pofd.append(pd.Series([0]), ignore_index=True)
            thresh = df_roc['thresh']
            thresh = pd.Series(['']).append(thresh, ignore_index=True)
            thresh = thresh.append(pd.Series(['']), ignore_index=True)
            return pofd, pody, thresh

        elif self.config.linetype_pct:
            roc_df = pstats._calc_pct_roc(subset_df)
            pody = roc_df['pody']
            pody = pd.Series([1]).append(pody, ignore_index=True)
            pody = pody.append(pd.Series([0]), ignore_index=True)
            pofd = roc_df['pofd']
            pofd = pd.Series([1]).append(pofd, ignore_index=True)
            pofd = pofd.append(pd.Series([0]), ignore_index=True)
            thresh = roc_df['thresh']
            thresh = pd.Series(['']).append(thresh, ignore_index=True)
            thresh = thresh.append(pd.Series(['']), ignore_index=True)
            return pofd, pody, thresh
        else:
            raise ValueError('error neither ctc or pct linetype ')

    def _subset_data(self, df_full, permutation):
        '''
            Subset the input dataframe, iterating over the column and rows of interest

            Args:
               @param df_full:          The pandas dataframe representation of the full
                                        input data.

               @param permutation:      A list representing a permutation/series of
                                        interest (e.g. ['model', 'vx_mask'],
                                        which represent the series values of interest
                                        that are specified in the config file.

            Returns:
                df_subset:  The portion of the full dataset that corresponds to the column header(s)
                            and rows of interest.
        '''


        df_subset = df_full.copy()

        # only supporting series_val_1 for ROC diagrams, so we are
        # only interested in the series_inner_dict1
        inner_dict = self.config.series_inner_dict1

        for perm in permutation:
            for k,v in self.config.series_inner_dict1.items():
                if perm == k:
                    column_header = v
                    row_of_interest = perm

            df_subset = df_subset[df_subset[column_header] == row_of_interest]



        return df_subset