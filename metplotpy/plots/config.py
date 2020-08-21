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
        self.output_image = self.get_config_value('plot_filename')
        self.title_font = constants.DEFAULT_TITLE_FONT
        self.title_color = constants.DEFAULT_TITLE_COLOR
        self.xaxis = self.get_config_value('xaxis')
        self.yaxis_1 = self.get_config_value('yaxis_1')
        self.yaxis_2 = self.get_config_value('yaxis_2')
        self.title = self.get_config_value('title')
        self.use_ee = self.get_config_value('event_equalize')
        self.indy_vals = self.get_config_value('indy_vals')
        self.indy_var = self.get_config_value('indy_var')
        self.show_plot_in_browser = self.get_config_value('show_plot_in_browser')
        self.plot_width = self.get_config_value('plot_width')
        self.plot_height = self.get_config_value('plot_height')

        # legend style settings as defined in METviewer
        user_settings = self._get_legend_style()

        # list of the x, y, and loc values for the
        # bbox_to_anchor() setting used in determining
        # the location of the bounding box which defines
        # the legend.
        self.bbox_x = float(user_settings['bbox_x'])
        self.bbox_y = float(user_settings['bbox_y'])
        legend_magnification = user_settings['legend_size']
        self.legend_size = int(constants.DEFAULT_LEGEND_FONTSIZE * legend_magnification)
        self.legend_ncol = self.get_config_value('legend_ncol')
        legend_box = self.get_config_value('legend_box').lower()
        if legend_box == 'n':
            # Don't draw a box around legend labels
            self.draw_box = False
        else:
            # Other choice is 'o'
            # Enclose legend labels in a box
            self.draw_box = True

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
        elif index == 2:
            # evaluate series_val_2 setting
            series_val_dict = self.get_config_value('series_val_2')
        else:
            raise ValueError('Index value must be either 1 or 2.')

        # check for empty setting. If so, return an empty list
        if series_val_dict:
            val_dict_list = [*series_val_dict.values()]
        else:
            val_dict_list = []

        # Unpack and access the values corresponding to the inner keys
        # (series_var1, series_var2, ..., series_varn).
        return val_dict_list

    def _get_series_columns(self, index):
        ''' Retrieve the column name that corresponds to this '''

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
        if series_val_dict:
           return [*series_val_dict.keys()]
        else:
           return []

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
           Retrieve all the markers.

           Args:

           Returns:
               markers: a list of the markers
        """
        markers = self.get_config_value('series_symbols')
        markers_list = []
        for marker in markers:
            if marker in constants.AVAILABLE_MARKERS_LIST:
                # markers is the matplotlib symbol: .,o, ^, d, H, or s
                markers_list.append(marker)
            else:
                # markers are indicated by name: small circle, circle, triangle,
                # diamond, hexagon, square
                m = marker.lower()
                markers_list.append(constants.PCH_TO_MATPLOTLIB_MARKER[m])
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


    def _get_user_legends(self, legend_label_type):
        """
           Retrieve the text that is to be displayed in the legend at the bottom of the plot.
           Each entry corresponds to a series.

           Args:
               @parm legend_label_type:  The legend label, such as 'Performance' that indicates
                                    the type of series line. Used when the user hasn't
                                    indicated a legend.

           Returns:
               a list consisting of the series label to be displayed in the plot legend.

        """
        all_legends = self.get_config_value('user_legend')

        # for legend labels that aren't set (ie in conf file they are set to '')
        # create a legend label based on the permutation of the series names
        # appended by 'user_legend label'.  For example, for:
        #     series_val_1:
        #        model:
        #          - NoahMPv3.5.1_d01
        #        vx_mask:
        #          - CONUS
        # The constructed legend label will be "NoahMPv3.5.1_d01 CONUS Performance"


        # Check for empty list as setting in the config file
        legends_list = []

        # set a flag indicating when a legend label is specified
        legend_label_unspecified = True

        # Check if a stat curve was requested, if so, then the number
        # of series_val_1 values will be inconsistent with the number of
        # legend labels 'specified' (either with actual labels or whitespace)

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
                    legend_label_unspecified = False
                    legends_list.append(legend)

        ll_list = []
        series_list = self.all_series_vals

        # Some diagrams don't require a series_val1 value, hence
        # resulting in a zero-sized series_list.  In this case,
        # the legend label will just be the legend_label_type.
        if len(series_list) == 0 and legend_label_unspecified:
            return [legend_label_type]

        perms = utils.create_permutations(series_list)
        for idx,ll in enumerate(legends_list):
            if ll == ' ':
                if len(series_list) > 1:
                    label_parts = [perms[idx][0], ' ', perms[idx][1], ' ', legend_label_type]
                else:
                    label_parts = [perms[idx][0], ' ', legend_label_type]
                legend_label = ''.join(label_parts)
                ll_list.append(legend_label)
            else:
                ll_list.append(ll)

        legends_list_ordered = self.create_list_by_series_ordering(ll_list)
        return legends_list_ordered

    def _get_plot_resolution(self):
        """
            Retrieve the plot_res and plot_unit to determine the dpi
            setting in matplotlib.

            Args:

            Returns:
                plot resolution in units of dpi (dots per inch)

        """
        # Initialize to the default resolution
        # set by matplotlib
        dpi = 100

        # first check if plot_res is set in config file
        if self.get_config_value('plot_res'):
            resolution = self.get_config_value('plot_res')

            # check if the units value has been set in the config file
            if self.get_config_value('plot_units'):
                units = self.get_config_value('plot_units').lower()
                if units == 'in':
                    return resolution
                elif units == 'mm':
                    # convert mm to inches so we can
                    # set dpi value
                    return resolution * constants.MM_TO_INCHES
                else:
                    # units not supported, assume inches
                    return resolution
            else:
                # units not indicated, assume
                # we are dealing with inches
                return resolution
        else:
            # no plot_res value is set, return the default
            # dpi used by matplotlib
            return dpi


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


    def calculate_plot_dimension(self, config_value, output_units):
        '''
           To calculate the width or height that defines the size of the plot.
           Matplotlib defines these values in inches, Python plotly defines these
           in terms of pixels.  METviewer accepts units of inches or mm for width and
           height, so conversion from mm to inches or mm to pixels is necessary, depending
           on the requested output units, output_units.

           Args:
              @param config_value:  The plot dimension to convert, either a width or height, in inches or mm
              @param output_units: pixels or in (inches) to indicate which
                                   units to use to define plot size. Python plotly uses pixels and
                                   Matplotlib uses inches.
           Returns:
             converted_value : converted value from in/mm to pixels or mm to inches based on input values
        '''
        value2convert = self.get_config_value(config_value)
        resolution = self.get_config_value('plot_res')
        units = self.get_config_value('plot_units')

        # initialize converted_value to some small value
        converted_value = 0

        # convert to pixels
        # plotly uses pixels for setting plot size (width and height)
        if output_units.lower() == 'pixels':
            if units.lower() == 'in':
                # value in pixels
                converted_value = int(resolution * value2convert)
            elif units.lower() == 'mm':
                # Convert mm to pixels
                converted_value = int(resolution * value2convert * constants.MM_TO_INCHES)

        # Matplotlib uses inches (in) for setting plot size (width and height)
        elif output_units.lower() == 'in':
            if units.lower() == 'mm':
                # Convert mm to inches
                converted_value = value2convert * constants.MM_TO_INCHES
            else:
                converted_value = value2convert

        # plotly does not allow any value smaller than 10 pixels
        if output_units.lower() == 'pixels' and converted_value < 10:
            converted_value = 10

        return converted_value