"""
Class Name: PerformanceDiagramSeries
 """
__author__ = 'Minna Win'
__email__ = 'met_help@ucar.edu'

import metcalcpy.util.utils as utils
from plots.series import Series
import numpy as np

print(np.__version__)
'x' in np.arange(5)

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

    def _create_series_points(self):
        """
           Subset the data for the appropriate series

           Args:

           Returns:
               a tuple of lists that represent the (SuccessRatio, PODY) values,
               where SuccessRatio = 1-FAR

        """

        input_df = self.input_data

        # Calculate the cartesian product of all series_val values as
        # defined in the config file.  These will be used to subset the pandas
        # dataframe input data.  Each permutation corresponds to a series.
        # This permutation corresponds to this series instance.
        perm = self._create_permutations()

        # We know that for performance diagrams, we are interested in the
        # fcst_var column of the input data.
        fcst_var_colname = 'fcst_var'

        # subset input data based on the forecast variables set in the config file
        for fcst_var in self.fcst_vars_1:
            subset_fcst_var = input_df[input_df[fcst_var_colname] == fcst_var]

        # subset based on the permutation of series_val values set in the config file.
        for i, series_val_name in enumerate(self.series_val_names):
            subset_series = subset_fcst_var[subset_fcst_var[series_val_name] == perm[i]]

        # subset based on the stat
        pody_df = subset_series[subset_series['stat_name'] == 'PODY']
        far_df = subset_series[subset_series['stat_name'] == 'FAR']

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
            pody_indy = pody_df[pody_df[self.config.indy_var] == indy_val_str]
            far_indy = far_df[far_df[self.config.indy_var] == indy_val_str]

            if not pody_indy.empty and not far_indy.empty:
                # For this time step, use either the sum, mean, or median to
                # represent the singular value for the
                # statistic of interest.
                if self.config.plot_stat == 'MEDIAN':
                    pody_val = pody_indy['stat_value'].median()
                    sr_val = 1 - far_indy['stat_value'].median()
                    pody_ncl = pody_indy['stat_ncl'].median()
                    pody_ncu = pody_indy['stat_ncu'].median()

                elif self.config.plot_stat == 'MEAN':
                    pody_val = pody_indy['stat_value'].mean()
                    sr_val = 1 - far_indy['stat_value'].mean()
                    pody_ncl = pody_indy['stat_ncl'].mean()
                    pody_ncu = pody_indy['stat_ncu'].mean()

                elif self.config.plot_stat == 'SUM':
                    pody_val = pody_indy['stat_value'].sum()
                    sr_val = 1 - far_indy['stat_value'].sum()
                    pody_ncl = pody_indy['stat_ncl'].sum()
                    pody_ncu = pody_indy['stat_ncu'].sum()


                # Calculate the yerr list needed by matplotlib.pyplot's
                # errorbar() method. These values are the lengths of the error bars,
                # given by:
                # pody_err = pody_ncu - pody_ncl
                pody_err = pody_ncu - pody_ncl

                # Round final PODY and Success ratio values to 2-sig figs
                # pody_val_2sig = round(pody_val, 2)
                pody_val_2sig = utils.round_half_up(pody_val, 2)
                # sr_val_2sig = round(sr_val, 2)
                sr_val_2sig = utils.round_half_up(sr_val, 2)
                pody_list.append(pody_val_2sig)
                sr_list.append(sr_val_2sig)
                pody_err_list.append(pody_err)

        return sr_list, pody_list, pody_err_list