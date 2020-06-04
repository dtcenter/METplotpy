"""
Class Name: roc_diagram_config.py

Holds values set in the ROC config file(s)
"""
__author__ = 'Minna Win'
__email__ = 'met_help@ucar.edu'

from plots.config import Config
import plots.constants as constants

class ROCDiagramConfig(Config):
    def __init__(self, parameters):
        """ Reads in the plot settings from a ROC config file

            Args:
            @param parameters: dictionary containing user defined parameters

            Returns:

        """

        # init common layout
        super().__init__(parameters)

        # use this setting to determine the ordering of colors, lines, and markers
        self.series_ordering = self._get_series_order()

        # self.plot_ci = self._get_plot_ci()
        self.plot_disp = self._get_plot_disp()

        # Make the series ordering zero-based to be consistent with Python's zero-based
        # counting/numbering
        self.series_ordering_zb = [sorder - 1 for sorder in self.series_ordering]

        # settings that are unique to ROC diagrams
        self.stat_input = self.get_config_value('stat_input')
        # Contingency table count line type
        self.linetype_ctc = self.get_config_value('roc_ctc')
        # Probability contingency table count line type
        self.linetype_pct = self.get_config_value('roc_pct')
        # Supported values for stat_curve are none, mean, and median
        self.stat_curve = self.get_config_value('stat_curve')
        self.add_threshold_pts = self.get_config_value('add_pt_thresh')
        self.plot_width = self.get_config_value('plot_width')
        self.plot_height = self.get_config_value('plot_height')
        self.plot_resolution = self.get_config_value('plot_res')
        self.plot_units = self.get_config_value('plot_units')
        self.caption = self.get_config_value('plot_caption')
        self.caption_weight = self.get_config_value('caption_weight')
        self.caption_color = self.get_config_value('caption_color')
        self.caption_size = self.get_config_value('caption_size')
        self.caption_offset = self.get_config_value('caption_offset')
        self.caption_align = self.get_config_value('caption_align')
        self.plot_stat = self.stat_curve
        self.colors_list = self._get_colors()
        self.marker_list = self._get_markers()
        self.linewidth_list = self._get_linewidths()
        self.linestyles_list = self._get_linestyles()
        self.symbols_list = self._get_series_symbols()
        self.user_legends = self._get_user_legends()

    # def _get_fcst_vars(self):
    #     """
    #         Override the parent's implementation.  The ROC diagram config file
    #         currently does not require a fcst_var setting.
    #
    #       Args:
    #            return an empty list if no fcst_var setting was found
    #     """
    #
    #     fcst_var_val_dict = self.get_config_value('fcst_var_vals')
    #     if not fcst_var_val_dict:
    #         return []
    #     else:
    #         return [*fcst_var_val_dict.keys()]

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

    # def _get_plot_ci(self):
    #     """
    #
    #         Args:
    #
    #         Returns:
    #             list of values to indicate whether or not to plot the confidence interval for
    #             a particular series, and which confidence interval (bootstrap or normal).
    #
    #     """
    #     plot_ci_list = self.get_config_value('plot_ci')
    #     num_series = len(self.series_ordering_zb)
    #     ordered_ci_settings_list =[]
    #     if not plot_ci_list:
    #         for series in num_series:
    #             ordered_ci_settings_list.append(" ")
    #     ci_settings_list = [ci.upper() for ci in plot_ci_list]
    #
    #     # Do some checking to make sure that the values are valid (case-insensitive):
    #     # None, boot, or norm
    #     for ci_setting in ci_settings_list:
    #         if ci_setting not in constants.ACCEPTABLE_CI_VALS:
    #             raise ValueError("A plot_ci value is set to an invalid value. "
    #                              "Accepted values are (case insensitive): "
    #                              "None, norm, or boot. Please check your config file.")
    #
    #     # order the ci list according to the series_order setting (e.g. 1 2 3, 2 1 3,..., etc.)
    #     ordered_ci_settings_list = self.create_list_by_series_ordering(ci_settings_list)
    #
    #     return ordered_ci_settings_list


    # def create_list_by_series_ordering(self, setting_to_order):
    #     """
    #         Generate a list of series plotting settings based on what is set
    #         in series_order in the config file.
    #         If the series_order is specified:
    #            series_order:
    #             -3
    #             -1
    #             -2
    #
    #             and color is set:
    #            color:
    #             -red
    #             -blue
    #             -green
    #
    #            and the line widths are:
    #            line_width:
    #               -1
    #               -3
    #               -2
    #            then the first series has a line width=3,
    #            the second series has a line width=2,
    #            and the third series has a line width=1
    #
    #         Then the following is expected:
    #           the first series' color is 'blue'
    #           the second series' color is 'green'
    #           the third series' color is 'red'
    #
    #         This allows the user the flexibility to change marker symbols, colors, and
    #         other line qualities between the series (lines) without having to re-order
    #         *all* the values.
    #
    #         Args:
    #
    #             setting_to_order:  the name of the setting (eg line_width) to be
    #                                ordered based on the order indicated
    #                                in the config file under the series_order setting.
    #
    #         Returns:
    #             a list reflecting the order that is consistent with what was set in series_order
    #
    #     """
    #
    #     # order the ci list according to the series_order setting
    #     ordered_settings_list = []
    #
    #     # Make the series ordering list zero-based to sync with Python's zero-based counting
    #     series_ordered_zb = [sorder - 1 for sorder in self.series_ordering]
    #     for idx in range(len(setting_to_order)):
    #         # find the current index's value in the zero-based series_ordering list
    #         loc = series_ordered_zb.index(idx)
    #         ordered_settings_list.append(setting_to_order[loc])
    #
    #     return ordered_settings_list

    def _get_plot_disp(self):
        """
            Retrieve the boolean values that determine whether to display a particular series

            Args:

            Returns:
                A list of boolean values indicating whether or not to
                display the corresponding series
        """

        plot_display_vals = self.get_config_value('plot_disp')
        plot_display_bools = [pd for pd in plot_display_vals]
        plot_display_bools_ordered = self.create_list_by_series_ordering(plot_display_bools)
        return plot_display_bools_ordered

