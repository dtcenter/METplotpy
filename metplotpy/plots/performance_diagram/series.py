"""
Class Name: series.py
 """
__author__ = 'Minna Win'
__email__ = 'met_help@ucar.edu'
import itertools
from datetime import datetime

class Series:
    """
        Represents a series object of data points and their plotting style
        elements (line colors, markers, linestyles, etc.)
        Each series is depicted by a single line in the performance diagram.

    """
    def __init__(self, config, idx, input_data):
        self.config = config
        self.idx = idx
        self.input_data = input_data
        self.plot_ci = config.plot_ci[idx]
        self.plot_disp = config.plot_disp[idx]
        self.plot_stat = config.plot_stat[idx]
        self.color = config.colors_list[idx]
        self.marker = config.marker_list[idx]
        self.linewidth = config.linewidth_list[idx]
        self.linestyle = config.linestyles_list[idx]
        self.symbol = config.symbols_list[idx]
        self.user_legends = config.user_legends[idx]
        self.series_order = config.series_ordering_zb[idx]

        # Variables used for subsetting the input dataframe
        # series variable names defined in the series_val setting
        self.series_vals = config.series_vals
        # forecast variable names defined in the fcst_var_val setting
        self.fcst_vars = config.fcst_vars

        # Column names corresponding to the series variable names
        self.series_val_names = config.series_val_names

        # Subset the data for this series object
        self.series_points = self._create_series_points()

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
        for fcst_var in self.fcst_vars:
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

            # Convert the datetimes in the indy_val list (from the config file)
            # to strings so we can compare them to the string representation of
            # the datetimes in the data file
            indy_val_str = datetime.strftime(indy_val, "%Y-%m-%d %H:%M:%S")

            # Now we can subset based on the current datetime in the list of
            # indy_vals specified in the config file.
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

                # Round final values to 2-sig figs
                pody_val_2sig = round(pody_val, 2)
                sr_val_2sig = round(sr_val, 2)
                pody_list.append(pody_val_2sig)
                sr_list.append(sr_val_2sig)
                pody_err_2sig = round(pody_err, 2)
                pody_err_list.append(pody_err_2sig)

        return sr_list, pody_list, pody_err_list


    def _create_permutations(self):
        """
           Create all permutations (ie cartesian products) between the
           elements in the lists of dictionaries under the series_val
           dictionary (representing the columns in the input data upon which to
           subset the datetime data of interest):

           for example:

           series_val:
              model:
                - GFS_0p25_G193
              vx_mask:
                - NH_CMORPH_G193
                - SH_CMORPH_G193
                - TROP_CMORPH_G193


            So for the above case, we have two lists in the series_val dictionary,
            one for model and another for vx_mask:
            model_list = ["GFS_0p25_G193"]
            vx_mask_list = ["NH_CMORPH_G193", "SH_CMORPH_G193", "TROP_CMORPH_G193"]

            and a cartesian product representing all permutations of the lists
            above results in the following:

           ("GFS_0p25_G193", "NH_CMORPH_G193")
           ("GFS_0p25_G193", "SH_CMORPH_G193")
           ("GFS_0p25_G193", "TROP_CMORPH_G193")

           This is useful for subsetting the input data to retrieve the FAR and PODY
           stat values that represent each datetime.
           *********
           **NOTE**
           ********
             There is no a priori knowledge of what or how many "values" of series_var
             variables (e.g. model, vx_mask, xyz, etc.) Therefore we use the following
             nomenclature:

             fcst_var_val:
                 fcst_var1:
                     -indy_fcst_stat
                     -dep_fcst_stat
                 fcst_var2:
                     -indy_fcst_stat
                     -dep_fcst_stat
            *Since we are only supporting one x-axis (independent vars) vs y-axis
            (dependent vars), we will always expect
             the indy_fcst_stat (independent stat value) and
             dep_fcst_stat (dependent stat value) to be the same for all
             fcst_var values selected.

             series_val:
                series_var1:
                   -series_var1_val1
                series_var2:
                   -series_var2_val1
                   -series_var2_val2
                   -series_var2_val3
                series_var3:
                   -series_var3_val1
                   -series_var3_val2

           Args:

           Returns:
               permutation: a list of tuples that represent the possible
               permutations of column names that correspond
               to this series instance. There is one permutation per series.
        """

        # Retrieve the lists from the series_val dictionary
        series_vals_list = self.series_vals

        # Utilize itertools' product() to create the cartesian product of all elements
        # in the lists to produce all permutations of the series_val values and the
        # fcst_var_val values.
        permutations = [p for p in itertools.product(*series_vals_list)]

        # order the permutations so they are consistent with the ordering defined
        # in the series_order config setting
        ordered_permutations = self.config.create_list_by_series_ordering(permutations)

        # return the permutation for this series
        return ordered_permutations[self.idx]
