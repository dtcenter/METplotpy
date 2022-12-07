# ============================*
 # ** Copyright UCAR (c) 2020
 # ** University Corporation for Atmospheric Research (UCAR)
 # ** National Center for Atmospheric Research (NCAR)
 # ** Research Applications Lab (RAL)
 # ** P.O.Box 3000, Boulder, Colorado, 80307-3000, USA
 # ============================*
 
 
 
"""
Class Name: ROCDiagramSeries
 """
__author__ = 'Minna Win'

import sys

import pandas as pd
import re
import metcalcpy.util.ctc_statistics as cstats
import metcalcpy.util.pstd_statistics as pstats
import metcalcpy.util.utils as utils
from ..series import Series


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

        # Event equalization can sometimes create an empty data frame.  Check for
        # an empty data frame and return a tuple of empty lists if this is the case.
        if input_df.empty:
            print(f"INFO: No points to plot (most likely as a result of event equalization).  ")
            return [],[],[]

        series_num = self.series_order
        perm = utils.create_permutations(self.all_series_vals)
        if len(self.all_series_vals) > 0:
            cur_perm = perm[series_num]
            subset_df = self._subset_data(input_df, cur_perm)
        else:
            # no subsetting of data required, no series_val_1 values
            # were specified in the config file.
            subset_df = input_df.copy()
        if self.config.linetype_ctc:
            subset_df = self._add_ctc_columns(subset_df)
            df_roc = cstats.calculate_ctc_roc(subset_df, ascending=self.config.ctc_ascending)
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
            for k, v in self.config.series_inner_dict1.items():
                if perm == k:
                    column_header = v
                    row_of_interest = perm

            df_subset = df_subset[df_subset[column_header] == row_of_interest]

        return df_subset

    def _add_ctc_columns(self, df_input):
        '''
        Create two new columns in the data frame from the fcst_thresh
        column of the CTC linetype data. This will be useful in sorting
        based on the fcst_thresh values.

        Args:
        @param df_input:  the dataframe containing all the CTC data

        Returns:
        @param thresh_sorted:  a new dataframe that is sorted based on
                               the threshold value and threshold operator
                               that comprise the fcst_thresh column.
                               If two or more threshold values are identical,
                               use the threshold operator (<,<=,==, >=,>)
                               to determine the order.
        '''

        # If the df_input dataframe is empty (most likely as a result of event equalization),
        # return the df_input data frame.
        if df_input.empty:
            return df_input

        # From the fcst_thresh column, create two new columns, thresh_values and
        # op_wts that we can then sort using Pandas' multi-column sorting
        # capability.
        operators = []
        values = []
        thresholds = df_input['fcst_thresh']
        # Assign weights to the operators, 1 for the <, 5 for the > so that
        # > supercedes all other operators.
        wt_maps = {'<': 1, '<=': 2, '==': 3, '>=': 4, '>': 5}
        wts = []
        for thrsh in thresholds:
            # treat the fcst_thresh as two groups, one for
            # the operator and the other for the value (which
            # can be a negative value).
            match = re.match(r'(\<|\<=|\==|\>=|\>)*((-)*([0-9])(.)*)', thrsh)
            match_text = re.match(r'(\<|\<=|\==|\>=|\>)*(.*)', thrsh)
            if match:
                operators.append(match.group(1))
                value = float(match.group(2))
                values.append(value)
            elif match_text:
                operators.append(match_text.group(1))
                value = match_text.group(2)
                values.append(value)
            else:
                raise ValueError("fcst_thresh has a value that doesn't conform to "
                                 "the expected format")

        for operator in operators:
            # if no operator precedes the number in fcst_thresh,
            # then assume this is the same as == and assign a weight of 3
            if operator is None:
                wts.append(3)
            else:
                wts.append(wt_maps[operator])

        # Add these columns to the input dataframe
        df_input['thresh_values'] = values
        df_input['op_wts'] = wts

        # return the input dataframe with two additional columns if
        # everything worked as expected
        return df_input
