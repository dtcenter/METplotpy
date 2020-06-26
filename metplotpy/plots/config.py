"""
Class Name: config.py

Holds values set in the config file(s)
"""
__author__ = 'Minna Win'
__email__ = 'met_help@ucar.edu'

import itertools
import metcalcpy.util.utils as utils
import plots.constants as constants

class Config:
    """
       Handles reading in and organizing configuration settings in the yaml configuration file.
    """

    def __init__(self, parameters):

        self.parameters = parameters

        #
        # Configuration settings that apply to the plot
        #
        self.output_image = self.get_config_value('plot_output')
        self.title_font = constants.DEFAULT_TITLE_FONT
        self.title_color = constants.DEFAULT_TITLE_COLOR
        self.xaxis = self.get_config_value('xaxis')
        self.yaxis_1 = self.get_config_value('yaxis_1')
        self.yaxis_2 = self.get_config_value('yaxis_2')
        self.title = self.get_config_value('title')
        self.use_ee = self.get_config_value('event_equalize')
        self.indy_vals = self.get_config_value('indy_vals')
        self.indy_var = self.get_config_value('indy_var')


        # These are the inner keys to the series_val setting, and
        # they represent the series variables of
        # interest.  The keys correspond to the column names
        # in the input dataframe.
        self.series_vals_1 = self._get_series_vals(1)
        self.series_vals_2 = self._get_series_vals(2)
        self.all_series_vals = self.series_vals_1 + self.series_vals_2

        # Represent the names of the forecast variables (inner keys) to the fcst_var_val setting.
        # These are the names of the columns in the input dataframe.
        self.fcst_vars_1 = self._get_fcst_vars(1)
        self.fcst_vars_2 = self._get_fcst_vars(2)

        # Get the list of the statistics of interest
        self.list_stat_1 = self.get_config_value('list_stat_1')
        self.list_stat_2 = self.get_config_value('list_stat_2')

        # These are the inner values to the series_val setting (these correspond to the
        # keys returned in self.series_vals above).  These are the specific variable values to
        # be used in subsetting the input dataframe (e.g. for key='model', and value='SH_CMORPH',
        # we want to subset data where column name is 'model', with coincident rows of 'SH_CMORPH'.
        self.series_val_names = self._get_series_val_names()


    def get_config_value(self, *args):
        """Gets the value of a configuration parameter.
        Looks for parameter in the user parameter dictionary

        Args:
            @ param args - chain of keys that defines a key to the parameter

        Returns:
            - a value for the parameter of None
        """

        return self._get_nested(self.parameters, args)


    def _get_nested(self, data, args):
        """Recursive function that uses the tuple with keys to find a value
        in multidimensional dictionary.

        Args:
            @data - dictionary for the lookup
            @args  - a tuple with keys

        Returns:
            - a value for the parameter of None
        """

        if args and data:

            # get value for the first key
            element = args[0]
            if element:
                value = data.get(element)

                # if the size of key tuple is 1 - the search is over
                if len(args) == 1:
                    return value

                # if the size of key tuple is > 1 - search using other keys
                return self._get_nested(value, args[1:])
        return None

    def _get_legend_style(self):
        """
            Retrieve the legend style settings that are set
            in the METviewer tool

            Args:

            Returns:
                - a dictionary that holds the legend settings that
                  are set in METviewer
        """
        legend_box = self.get_config_value('legend_box').lower()
        legend_ncol = self.get_config_value('legend_ncol')
        legend_inset = self.get_config_value('legend_inset')
        legend_bbox_x = legend_inset['x']
        legend_bbox_y = legend_inset['y']
        legend_size = self.get_config_value('legend_size')
        legend_settings = dict(bbox_x=legend_bbox_x,
                               bbox_y=legend_bbox_y,
                               legend_size=legend_size,
                               legend_ncol=legend_ncol,
                               legend_box=legend_box)

        return legend_settings

    def _get_series_vals(self, index):
        """
            Get a tuple of lists of all the variable values that correspond to the inner
            key of the series_val dictionaries (series_val_1 and series_val_2).
            These values will be used with lists of other config values to
            create filtering criteria.  This is useful to subset the input data
            to assist in identifying the data points for this series.

            Args:
                index:  The number defining which of series_vals_1 or series_vals_2 to consider

            Returns:
                lists of *all* the values of the inner dictionary
                of the series_vals dictionaries

        """

        if index == 1:
            # evaluate series_val_1 setting
            series_val_dict = self.get_config_value('series_val_1')
            val_dict_list = [*series_val_dict.values()]
        elif index == 2:
            # evaluate series_val_2 setting
            # check for empty setting. If so, return an empty list
            series_val_dict_2 = self.get_config_value('series_val_2')
            if series_val_dict_2:
                val_dict_list = [*series_val_dict_2.values()]
            else:
                val_dict_list = []

        # Unpack and access the values corresponding to the inner keys
        # (series_var1, series_var2, ..., series_varn).
        return val_dict_list

    def _get_fcst_vars(self, index):
        """
           Retrieve a list of the inner keys (fcst_vars) to the fcst_var_val dictionary.

           Args:
              index: identifier used to differentiate between fcst_var_val_1 and
                     fcst_var_val_2 config settings
           Returns:
               a list containing all the fcst variables requested in the
               fcst_var_val setting in the config file.  This will be
               used to subset the input data that corresponds to a particular series.

        """
        if index == 1:
            fcst_var_val_dict = self.get_config_value('fcst_var_val_1')
            if fcst_var_val_dict:
                all_fcst_vars = [*fcst_var_val_dict.keys()]
            else:
                all_fcst_vars = []
        elif index == 2:
            fcst_var_val_dict = self.get_config_value('fcst_var_val_2')
            if fcst_var_val_dict:
                all_fcst_vars = [*fcst_var_val_dict.keys()]
            else:
                all_fcst_vars = []
        else:
            all_fcst_vars = []

        return all_fcst_vars

    def _get_series_val_names(self):
        """
            Get a list of all the variable value names (i.e. inner key of the
            series_val dictionary). These values will be used with lists of
            other config values to create filtering criteria.  This is useful
            to subset the input data to assist in identifying the data points
            for this series.

            Args:

            Returns:
                a "list of lists" of *all* the keys to the inner dictionary of
                the series_val dictionary

        """


        series_val_dict = self.get_config_value('series_val_1')

        # Unpack and access the values corresponding to the inner keys
        # (series_var1, series_var2, ..., series_varn).
        return [*series_val_dict.keys()]

    def calculate_number_of_series(self):
        """
           From the number of items in the permutation list,
           determine how many series "objects" are to be plotted.

           Args:

           Returns:
               the number of series

        """

        # Retrieve the lists from the series_val_1 dictionary
        series_vals_list = self.series_vals_1

        # Utilize itertools' product() to create the cartesian product of all elements
        # in the lists to produce all permutations of the series_val values and the
        # fcst_var_val values.
        permutations = [p for p in itertools.product(*series_vals_list)]

        return len(permutations)

    def _get_colors(self):
        """
           Retrieves the colors used for lines and markers, from the
           config file (default or custom).
           Args:

           Returns:
               colors_list or colors_from_config: a list of the colors to be used for the lines
               (and their corresponding marker symbols)
        """

        colors_settings = self.get_config_value('colors')
        color_list = [color for color in colors_settings]
        color_list_ordered = self.create_list_by_series_ordering(color_list)
        return color_list_ordered

    def _get_markers(self):
        """
           Retrieve all the markers, the order and number correspond to the number
           of series_order, user_legends, and number of series.

           Args:

           Returns:
               markers: a list of the markers
        """
        markers = self.get_config_value('series_symbols')
        markers_list = [m for m in markers]
        markers_list_ordered = self.create_list_by_series_ordering(markers_list)
        return markers_list_ordered

    def _get_linewidths(self):
        """ Retrieve all the linewidths from the configuration file, if not
            specified in any config file, use the default values of 2

            Args:

            Returns:
                linewidth_list: a list of linewidths corresponding to each line (model)
        """
        linewidths = self.get_config_value('series_line_width')
        linewidths_list = [l for l in linewidths]
        linewidths_list_ordered = self.create_list_by_series_ordering(linewidths_list)
        return linewidths_list_ordered

    def _get_linestyles(self):
        """
            Retrieve all the linestyles from the config file.

            Args:

            Returns:
                list of line styles, each line style corresponds to a particular series
        """
        linestyles = self.get_config_value('series_line_style')
        linestyle_list = [l for l in linestyles]
        linestyle_list_ordered = self.create_list_by_series_ordering(linestyle_list)
        return linestyle_list_ordered


    def _get_user_legends(self):
        """
           Retrieve the text that is to be displayed in the legend at the bottom of the plot.
           Each entry corresponds to a series.

           Args:

           Returns:
               a list consisting of the series label to be displayed in the plot legend.

        """
        all_legends = self.get_config_value('user_legend')

        # for legend labels that aren't set (ie in conf file they are set to '')
        # create a legend label based on the permutation of the series names
        # appended by 'Performance'.  For example, for:
        #     series_val_1:
        #        model:
        #          - NoahMPv3.5.1_d01
        #        vx_mask:
        #          - CONUS
        # The constructed legend label will be "NoahMPv3.5.1_d01 CONUS Performance"

        # Check for empty list as setting in the config file
        legends_list = []
        num_series = self.calculate_number_of_series()
        if len(all_legends) == 0:
            for i in range(num_series):
                legends_list.append(' ')
        else:
            for legend in all_legends:
                if len(legend) == 0:
                    legend = ' '
                    legends_list.append(legend)
                else:
                    legends_list.append(legend)

        ll_list = []
        series_list = self.all_series_vals
        perms = utils.create_permutations(series_list)
        for idx,ll in enumerate(legends_list):
            if ll == ' ':
                if len(series_list) > 1:
                    label_parts = [perms[idx][0], ' ', perms[idx][1], " Performance"]
                else:
                    label_parts = [perms[idx][0], ' Performance']
                legend_label = ''.join(label_parts)

                ll_list.append(legend_label)
            else:
                ll_list.append(ll)

        legends_list_ordered = self.create_list_by_series_ordering(ll_list)
        return legends_list_ordered

    def create_list_by_series_ordering(self, setting_to_order):
        """
            Generate a list of series plotting settings based on what is set
            in series_order in the config file.
            If the series_order is specified:
               series_order:
                -3
                -1
                -2

                and color is set:
               color:
                -red
                -blue
                -green

               and the line widths are:
               line_width:
                  -1
                  -3
                  -2
               then the first series has a line width=3,
               the second series has a line width=2,
               and the third series has a line width=1

            Then the following is expected:
              the first series' color is 'blue'
              the second series' color is 'green'
              the third series' color is 'red'

            This allows the user the flexibility to change marker symbols, colors, and
            other line qualities between the series (lines) without having to re-order
            *all* the values.

            Args:

                setting_to_order:  the name of the setting (eg line_width) to be
                                   ordered based on the order indicated
                                   in the config file under the series_order setting.

            Returns:
                a list reflecting the order that is consistent with what was set in series_order

        """

        # order the ci list according to the series_order setting
        ordered_settings_list = []

        # Make the series ordering list zero-based to sync with Python's zero-based counting
        series_ordered_zb = [sorder - 1 for sorder in self.series_ordering]
        for idx in range(len(setting_to_order)):
            # find the current index's value in the zero-based series_ordering list
            loc = series_ordered_zb.index(idx)
            ordered_settings_list.append(setting_to_order[loc])

        return ordered_settings_list
