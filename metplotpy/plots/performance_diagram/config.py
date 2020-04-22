"""
Class Name: config.py

Holds values set in the config file(s)
"""
__author__ = 'Minna Win'
__email__ = 'met_help@ucar.edu'

class Config:
    # Default values...
    DEFAULT_TITLE_FONT = 'sans-serif'
    DEFAULT_TITLE_COLOR = 'darkblue'
    DEFAULT_TITLE_FONTSIZE = 10
    AVAILABLE_MARKERS_LIST = ["o", "^", "s", "d", "H", "."]
    ACCEPTABLE_CI_VALS = ['NONE', 'BOOT', 'NORM']

    def __init__(self, parameters):

        self.parameters = parameters

        #
        # Configuration settings that apply to the plot
        #

        # Do not plot the legend for the equal lines of CSI (critical success index)
        self.plot_contour_legend = False
        self.output_image = self.parameters['plot_output']
        self.title_font = self.DEFAULT_TITLE_FONT
        self.title_color = self.DEFAULT_TITLE_COLOR
        self.xaxis = self._get_xaxis_title()
        self.yaxis = self._get_yaxis_title()
        self.title = self._get_title()

        #
        # Configuration settings that apply to each series (line)
        #
        self.stat_input = self._get_stat_input()
        self.plot_ci = self._get_plot_ci()
        self.plot_stat = self._get_plot_stat()
        self.plot_disp = self._get_plot_disp()
        self.series_ordering = self._get_series_order()
        self.colors_list = self._get_colors()
        self.marker_list = self._get_markers()
        self.linewidth_list = self._get_linewidths()
        self.linestyles_list = self._get_linestyles()
        self.symbols_list = self._get_series_symbols()
        self.user_legends = self._get_user_legends()
        is_config_consistent = self._config_consistency_check()
        if not is_config_consistent:
            raise ValueError("The number of series defined by series_val is inconsistent with the number of settings"
                             " required for describing each series. Please check"
                             " the number of your configuration file's plot_i, plot_disp, series_order, user_legend,"
                             " colors, and series_symbols settings.")


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

    def _get_stat_input(self):
        """
            Retrieve the input data file containing the statistics of interest.

            Returns:
                location and name of the input data file with statistics of interest.

        """
        return self.get_config_value('stat_input')

    def _get_xaxis_title(self):
        """
            The label for the xaxis
        """

        return self.get_config_value('xaxis')

    def _get_yaxis_title(self):
        """
            The label for the y-axis
        """

        return self.get_config_value('yaxis')

    def _get_title(self):
        """Creates a  title dictionary with values from users and default parameters
        If users parameters dictionary doesn't have needed values - use defaults

        Args:

        Returns:
            - the title
        """
        current_title = self.get_config_value('title')
        return current_title

    def _get_plot_ci(self):
        """

            Args:

            Returns:
                list of values to indicate whether or not to plot the confidence interval for
                a particular series, and which confidence iterval (bootstrap or normal).

        """
        plot_ci_list = self.get_config_value('plot_ci')
        ci_settings_list = [ci.upper() for ci in plot_ci_list]

        # Do some checking to make sure that the values are valid (case-insensitive): None, boot, or norm
        for ci in ci_settings_list:
            if ci not in self.ACCEPTABLE_CI_VALS:
                raise ValueError("A plot_ci value is set to an invalid value. Accepted values are (case insensitive): "
                                 "None, norm, or boot. Please check your config file.")

        return ci_settings_list

    def _get_plot_stat(self):
        """
            Retrieves the plot_stat setting from the config file.  There will be many statistics values
            (ie stat_name=PODY or stat_name=FAR in data file) that correspond to a specific time
            (init or valid, as specified in the config file), for a combination of
            model, vx_mask, fcst_var,etc.  We require a single value to represent this combination.
            Acceptable values are sum, mean, and median.

            Returns:
                 stat_to_plot: one of the following values for the plot_stat: MEAN, MEDIAN, or SUM
        """

        accepted_stats = ['MEAN', 'MEDIAN', 'SUM']
        stat_to_plot = self.get_config_value('plot_stat').upper()

        if stat_to_plot not in accepted_stats:
            raise ValueError("An unsupported statistic was set for the plot_stat setting. "
                             " Supported values are sum, mean, and median.")
        return stat_to_plot

    def _get_plot_disp(self):
        """
            Retrieve the boolean values that determine whether to display a particular series

            Args:

            Returns:
                A list of boolean values indicating whether or not to display the corresponding series
        """

        plot_display_vals = self.get_config_value('plot_disp')
        plot_display_bools = [pd for pd in plot_display_vals]
        return plot_display_bools

    def _get_series_order(self):
        """
            Get the order number for each series

            Args:

            Returns:
            a list of unique values representing the ordinal value of the corresponding series

        """
        ordinals = self.get_config_value('series_order')
        series_order_list = [ord for ord in ordinals]
        return series_order_list

    def _get_colors(self):
        """
           Retrieves the colors used for lines and markers, from the config file (default or custom).
           Args:

           Returns:
               colors_list or colors_from_config: a list of the colors to be used for the lines (
               and their corresponding marker symbols)
        """

        colors_settings = self.get_config_value('colors')
        color_list = [color for color in colors_settings]
        return color_list

    def _get_markers(self):
        """
           Retrieve all the markers, the order and number correspond to the number of series_order, user_legends,
           and number of series.

           Args:

           Returns:
               markers: a list of the markers
        """
        markers = self.get_config_value('series_symbols')
        markers_list = [m for m in markers]
        return markers_list

    def _get_linewidths(self):
        """ Retrieve all the linewidths from the configuration file, if not specified in any config file, use
            the default values of 2

            Args:

            Returns:
                linewidth_list: a list of linewidths corresponding to each line (model)
        """
        linewidths = self.get_config_value('series_line_width')
        linewidths_list = [l for l in linewidths]
        return linewidths_list

    def _get_linestyles(self):
        """
            Retrieve all the linestyles from the config file.

            Args:

            Returns:
                list of line styles, each line style corresponds to a particular series
        """
        linestyles = self.get_config_value('series_line_style')
        linestyle_list = [l for l in linestyles]
        return linestyle_list

    def _get_series_symbols(self):
        """
           Retrieve all the symbols that represent each series

           Args:

           Returns:
               a list of all the symbols, order is preserved.  That is, the first symbol corresponds to the first
               symbol defined.

        """
        symbols = self.get_config_value('series_symbols')
        symbols_list = [symbol for symbol in symbols]
        return symbols_list

    def _get_user_legends(self):
        """
           Retrieve the text that is to be displayed in the legend at the bottom of the plot.
           Each entry corresponds to a series.

           Args:

           Returns:
               a list consisting of the series label to be displayed in the plot legend.

        """
        all_legends = self.get_config_value('user_legend')
        legends_list = [legend for legend in all_legends]
        return legends_list

    # def _get_event_equalization_value(self):
    #     """
    #         Retrieve the boolean value from the config file which determines whether or
    #         not event equalization should be used.
    #
    #         Args:
    #
    #         Returns:
    #             True or False
    #
    #     """
    #     ee_val = self.parameters.getattribute('event_equalization').upper()
    #
    #     if ee_val == 'TRUE':
    #         return True
    #     else:
    #         return False

    def _config_consistency_check(self):
        """
            Checks that the number of settings defined for plot_ci, plot_disp, series_order, user_legend
            colors, and series_symbols is consistent with the

            Args:

            Returns:
                True if the number of settings for each of the above settings is consistent with the number of
                series (as defined by the cross product of the model and vx_mask defined in the series_val setting)

        """

        # Numbers of values for other settings for series
        # num_ci_settings = len(self.plot_ci)
        num_plot_disp = len(self.plot_disp)
        num_markers = len(self.marker_list)
        num_series_ord = len(self.series_ordering)
        num_colors = len(self.colors_list)
        num_symbols = len(self.symbols_list)
        num_legends = len(self.user_legends)
        num_line_widths = len(self.linewidth_list)
        num_linestyles = len(self.linestyles_list)

        # if self.num_series == num_ci_settings == num_plot_disp == \
        #         num_markers == num_series_ord == num_colors == num_symbols\
        #         == num_legends == num_line_widths == num_linestyles:
        if  num_plot_disp == \
                    num_markers == num_series_ord == num_colors == num_symbols \
                    == num_legends == num_line_widths == num_linestyles:
            return True
        else:
            return False
