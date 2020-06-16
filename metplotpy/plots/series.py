"""
Class Name: series.py
 """
__author__ = 'Minna Win'
__email__ = 'met_help@ucar.edu'
import itertools
import metcalcpy.util.utils as utils

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
        self.plot_disp = config.plot_disp[idx]
        self.plot_stat = config.plot_stat[idx]
        self.color = config.colors_list[idx]
        self.marker = config.marker_list[idx]
        self.linewidth = config.linewidth_list[idx]
        self.linestyle = config.linestyles_list[idx]
        self.user_legends = config.user_legends[idx]
        self.series_order = config.series_ordering_zb[idx]

        # Variables used for subsetting the input dataframe
        # series variable names defined in the series_val_1 setting
        self.series_vals_1 = config.series_vals_1
        self.series_vals_2 = config.series_vals_2
        self.all_series_vals = self.series_vals_1 + self.series_vals_2

        # forecast variable names defined in the fcst_var_val setting
        self.fcst_vars_1 = config.fcst_vars_1
        self.fcst_vars_2 = config.fcst_vars_2

        # Column names corresponding to the series variable names
        self.series_val_names = config.series_val_names

        # Subset the data for this series object
        self.series_points = self._create_series_points()


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
        series_vals_list = self.series_vals_1
        series_vals_list = self.all_series_vals

        # Utilize itertools' product() to create the cartesian product of all elements
        # in the lists to produce all permutations of the series_val values and the
        # fcst_var_val values.
        permutations = [p for p in itertools.product(*series_vals_list)]

        # order the permutations so they are consistent with the ordering defined
        # in the series_order config setting
        ordered_permutations = self.config.create_list_by_series_ordering(permutations)

        # return the permutation for this series
        return ordered_permutations[self.idx]
