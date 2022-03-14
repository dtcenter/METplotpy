# ============================*
 # ** Copyright UCAR (c) 2020
 # ** University Corporation for Atmospheric Research (UCAR)
 # ** National Center for Atmospheric Research (NCAR)
 # ** Research Applications Lab (RAL)
 # ** P.O.Box 3000, Boulder, Colorado, 80307-3000, USA
 # ============================*
 
 
 
"""
Class Name: PerformanceDiagramSeries
 """
__author__ = 'Minna Win'

import warnings
import re
import metcalcpy.util.utils as utils
from ..series import Series


# To suppress FutureWarning raised by pandas due to
# standoff between numpy and Python with respect to
# comparing a string to scalar.  Note, this is also
# an issue observed in Scikit, matplotlib, and TensorFlow.
# Workaround solution from Stack Overflow:
# https://stackoverflow.com/questions/40659212/
# futurewarning-elementwise-comparison-failed-
# returning-scalar-but-in-the-futur#46721064
# and GitHub issue in numpy repo:
# https://github.com/numpy/numpy/issues/6784
# warnings.simplefilter(action='ignore', category=FutureWarning)
# Instead, use pandas' astype to convert what you are comparing
# to a string, otherwise, you might end up with an empty
# dataframe and then an empty plot.

class PerformanceDiagramSeries(Series):
    """
        Represents a performance diagram series object
        of data points and their plotting style
        elements (line colors, markers, linestyles, etc.)
        Each series is depicted by a single line in the
        performance diagram.

    """

    def __init__(self, config, idx, input_data):
        super().__init__(config, idx, input_data)
        self.plot_ci = config.plot_ci[idx]

    def _create_series_points(self):
        """
           Subset the data for the appropriate series

           Args:

           Returns:
               a tuple of lists that represent the (SuccessRatio, PODY) values,
               where SuccessRatio = 1-FAR

        """

        input_df = self.input_data
        series_num = self.series_order

        # Assume we do have confidence data (either
        # stat_ncl/stat_ncu or stat_bcl/stat_bcu values)
        # that are NOT 'NaN'.
        no_confidence_data = False

        # Calculate the cartesian product of all series_val values as
        # defined in the config file.  These will be used to subset the pandas
        # dataframe input data.  Each permutation corresponds to a series.
        # This permutation corresponds to this series instance.
        perm = utils.create_permutations(self.all_series_vals)

        # Check that we have all the necessary settings for each series
        is_config_consistent = self.config._config_consistency_check()
        if not is_config_consistent:
            raise ValueError("The number of series defined by series_val_1 is"
                             " inconsistent with the number of settings"
                             " required for describing each series. Please check"
                             " the number of your configuration file's plot_i,"
                             " plot_disp, series_order, user_legend,"
                             " colors, and series_symbols settings.")

        cur_perm = perm[series_num]

        # We know that for performance diagrams, we are interested in the
        # fcst_var column of the input data.
        fcst_var_colname = 'fcst_var'

        # subset input data based on the forecast variables set in the config file
        for fcst_var in self.fcst_vars_1:
            subset_fcst_var = input_df[input_df[fcst_var_colname] == fcst_var]

        # subset based on the permutation of series_val values set in the config file.
        # work on a copy of the dataframe
        subsetted = subset_fcst_var.copy()

        # same number of items in tuple, so sufficient to get
        # the number of the items in the first tuple.
        for i, svn in enumerate(self.series_val_names):
            # match the series value name to
            # its corresponding permutation value
            col_str = svn

            # If we have more than one item in the series_val1, treat this
            # differently than if there is only one item
            if len(self.series_val_names) > 1:
                series_var_val_str = cur_perm[i]
            else:
                series_var_val_str = cur_perm[0]
            if i == 0:
                query_str = col_str + " == " + '"' + series_var_val_str + '"'
            else:
                query_str = query_str + " and " + col_str + " == " + '"' + series_var_val_str + '"'

        subset_series = subsetted.query(query_str)

        # subset based on the stat, since we are generating a performance diagram,
        # the only two stats we are interested in are PODY and FAR (or NBR_PODY and
        # NBR_FAR if neighborhood contingency table data is available instead).
        list_stat = self.config.list_stat_1
        for i, cur_stat in enumerate(list_stat):
            # Subset by PODY/NBR_PODY and FAR/NBR_FAR
            pody_stat_match = re.match(r'.*PODY',cur_stat )
            far_stat_match = re.match(r'.*FAR', cur_stat)
            if pody_stat_match:
                pody_stat = pody_stat_match.group(0)
                pody_df = subset_series[subset_series['stat_name'] == pody_stat]
            if far_stat_match:
                far_stat = far_stat_match.group(0)
                far_df = subset_series[subset_series['stat_name'] == far_stat]

        # pody_df = subset_series[subset_series['stat_name'] == 'PODY']
        # far_df = subset_series[subset_series['stat_name'] == 'FAR']

        # for Normal Confidence intervals, get the upper and lower confidence
        # interval values and use these to calculate a list of error values to
        # be used by matplotlib's pyplot errorbar() method.

        # now extract the PODY and FAR points for the specified datetimes.
        # Store the PODY points into a list.
        # Calculate the success ratio, which is 1 - FAR and
        # store those values in a list.
        pody_list = []
        sr_list = []
        pody_err_list = []

        for indy_val in self.config.indy_vals:
            # Now we can subset based on the current independent
            # variable in the list of indy_vals specified
            # in the config file.
            indy_val_str = str(indy_val)

            # Convert the indy var values into strings using pandas astype()
            pody_df_copy = pody_df.copy()
            far_df_copy = far_df.copy()
            pody_df_copy[self.config.indy_var] = pody_df_copy[self.config.indy_var].astype(str)
            far_df_copy[self.config.indy_var] = far_df_copy[self.config.indy_var].astype(str)
            pody_indy = pody_df_copy[pody_df_copy[self.config.indy_var] == indy_val_str]
            far_indy = far_df_copy[far_df_copy[self.config.indy_var] == indy_val_str]

            # Determine whether we are using aggregated statistics data,
            # which have stat_bcl and stat_bcu columns, rather than
            # stat_ncl and stat_ncu columns.
            # Check for the presence of the stat_bcl column in the
            # dataframe. If it exists, then we have aggregated
            # statistics data and we use the stat_bcl and stat_bcu
            # columns.  Otherwise, we use stat_ncl and stat_ncu
            # column data.
            if 'stat_bcl' in subsetted:
                # aggregated statistics
                cl_varname = 'stat_bcl'
                cu_varname = 'stat_bcu'
            else:
                cl_varname = 'stat_ncl'
                cu_varname = 'stat_ncu'

            # Check if we are missing the stat_bcl and stat_ncl
            # columns.  These will be missing if all values
            # in these columns are NaN.
            if ('stat_bcl' not in pody_indy) and ('stat_ncl' not in pody_indy):
                no_confidence_data = True

            # the stat_value column can consist of some NA values.
            # drop the rows that have NA so they don't get treated
            # as NaN's by python.
            pody_indy = pody_indy.dropna(axis=0, how='any')
            far_indy = far_indy.dropna(axis=0, how='any')
            if not pody_indy.empty and not far_indy.empty:
                # For this time step, use either the sum, mean, or median to
                # represent the singular value for the
                # statistic of interest.

                if self.config.plot_stat == 'MEDIAN':
                    pody_val = pody_indy['stat_value'].median()
                    sr_val = 1 - far_indy['stat_value'].median()
                    if no_confidence_data:
                        pody_ncl = pody_ncu = 0.
                        print("No available confidence level data")
                    else:
                        pody_ncl = pody_indy[cl_varname].median()
                        pody_ncu = pody_indy[cu_varname].median()


                elif self.config.plot_stat == 'MEAN':
                    pody_val = pody_indy['stat_value'].mean()
                    sr_val = 1 - far_indy['stat_value'].mean()
                    if no_confidence_data:
                        pody_ncl = pody_ncu = 0.
                        print("No available confidence level data")
                    else:
                        pody_ncl = pody_indy[cl_varname].mean()
                        pody_ncu = pody_indy[cu_varname].mean()

                elif self.config.plot_stat == 'SUM':
                    pody_val = pody_indy['stat_value'].sum()
                    sr_val = 1 - far_indy['stat_value'].sum()
                    if no_confidence_data:
                        pody_ncl = pody_ncu = 0.
                        print("No available confidence level data")
                    else:
                        pody_ncl = pody_indy[cl_varname].sum()
                        pody_ncu = pody_indy[cu_varname].sum()

                # Calculate the yerr list needed by matplotlib.pyplot's
                # errorbar() method. These values are the lengths of the error bars,
                # given by:
                # pody_err = pody_ncu - pody_ncl
                pody_err = pody_ncu - pody_ncl

                # Round final PODY and Success ratio values to 2-sig figs
                # pody_val_2sig = round(pody_val, 2)
                pody_val_2sig = utils.round_half_up(pody_val, 4)
                # sr_val_2sig = round(sr_val, 2)
                sr_val_2sig = utils.round_half_up(sr_val, 4)
                pody_list.append(pody_val_2sig)
                sr_list.append(sr_val_2sig)
                pody_err_list.append(pody_err)

        return sr_list, pody_list, pody_err_list
