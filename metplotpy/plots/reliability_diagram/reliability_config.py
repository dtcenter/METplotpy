# ============================*
 # ** Copyright UCAR (c) 2020
 # ** University Corporation for Atmospheric Research (UCAR)
 # ** National Center for Atmospheric Research (NCAR)
 # ** Research Applications Lab (RAL)
 # ** P.O.Box 3000, Boulder, Colorado, 80307-3000, USA
 # ============================*
 
 
 
"""
Class Name: reliability_config.py

Holds values set in the Line plot config file(s)
"""
__author__ = 'Tatiana Burek'

import itertools

from ..config import Config
from .. import constants
from .. import util


class ReliabilityConfig(Config):
    """
    Prepares and organises Reliability plot parameters
    """

    def __init__(self, parameters: dict) -> None:
        """ Reads in the plot settings from a Reliability plot config file.

            Args:
            @param parameters: dictionary containing user defined parameters

        """
        super().__init__(parameters)

        self.plot_stat = None

        # plot parameters
        self.grid_on = self._get_bool('grid_on')
        self.plot_width = self.calculate_plot_dimension('plot_width')
        self.plot_height = self.calculate_plot_dimension('plot_height')

        self.plot_margins = {
            'l': 0,
            'r': self.parameters['mar'][3] + 20,
            't': self.parameters['mar'][2] + 80,
            'b': self.parameters['mar'][0] + 80,
            'pad': 5,
        }
        self.indy_stagger = self._get_bool('indy_stagger_1')
        self.blended_grid_col = util.alpha_blending(self.parameters['grid_col'], 0.5)
        self.variance_inflation_factor = self._get_bool('variance_inflation_factor')
        self.dump_points_1 = self._get_bool('dump_points_1')
        # Optional setting, indicates *where* to save the dump_points_1 file
        # used by METviewer
        self.points_path = self.get_config_value('points_path')
        self.create_html = self._get_bool('create_html')
        self.add_noskill_line = self._get_bool('add_noskill_line')
        self.add_skill_line = self._get_bool('add_skill_line')
        self.add_reference_line = self._get_bool('add_reference_line')
        self.rely_event_hist = self._get_bool('rely_event_hist')
        self.inset_hist = self._get_bool('inset_hist')
        self.summary_curves = self.get_config_value('summary_curves')
        self.noskill_line_col = self.get_config_value('noskill_line_col')
        self.reference_line_col = self.get_config_value('reference_line_col')

        ##############################################
        # caption parameters
        self.caption_size = int(constants.DEFAULT_CAPTION_FONTSIZE
                                * self.get_config_value('caption_size'))
        self.caption_offset = self.parameters['caption_offset'] - 3.1

        ##############################################
        # title parameters
        self.title_font_size = self.parameters['title_size'] * constants.DEFAULT_TITLE_FONT_SIZE
        self.title_offset = 1.0 + abs(self.parameters['title_offset']) * constants.DEFAULT_TITLE_OFFSET
        self.y_title_font_size = self.parameters['ylab_size'] + constants.DEFAULT_TITLE_FONTSIZE

        ##############################################
        # y-axis parameters
        self.y_tickangle = self.parameters['ytlab_orient']
        if self.y_tickangle in constants.YAXIS_ORIENTATION.keys():
            self.y_tickangle = constants.YAXIS_ORIENTATION[self.y_tickangle]
        self.y_tickfont_size = self.parameters['ytlab_size'] + constants.DEFAULT_TITLE_FONTSIZE

        ##############################################
        # x-axis parameters
        self.x_title_font_size = self.parameters['xlab_size'] + constants.DEFAULT_TITLE_FONTSIZE
        self.x_tickangle = self.parameters['xtlab_orient']
        if self.x_tickangle in constants.XAXIS_ORIENTATION.keys():
            self.x_tickangle = constants.XAXIS_ORIENTATION[self.x_tickangle]
        self.x_tickfont_size = self.parameters['xtlab_size'] + constants.DEFAULT_TITLE_FONTSIZE

        ##############################################
        # series parameters
        self.series_ordering = self.get_config_value('series_order')
        # Make the series ordering zero-based
        self.series_ordering_zb = [sorder - 1 for sorder in self.series_ordering]
        self.plot_disp = self._get_plot_disp()
        self.colors_list = self._get_colors()
        self.marker_list = self._get_markers()
        self.marker_size = self._get_markers_size()
        self.mode = self._get_mode()
        self.linewidth_list = self._get_linewidths()
        self.linestyles_list = self._get_linestyles()
        self.plot_ci = self._get_plot_ci()
        self.all_series_y1 = self._get_all_series_y()
        self.con_series = self._get_con_series()
        self.num_series = self.calculate_number_of_series()
        self.show_legend = self._get_show_legend()
        if not self.indy_label:
            self.indy_label = self.indy_vals

        ##############################################
        # legend parameters
        self.user_legends = self._get_user_legends()
        self.bbox_x = 0.5 + self.parameters['legend_inset']['x']
        self.bbox_y = -0.12 + self.parameters['legend_inset']['y'] + 0.25
        self.legend_size = int(constants.DEFAULT_LEGEND_FONTSIZE * self.parameters['legend_size'])
        if self.parameters['legend_box'].lower() == 'n':
            self.legend_border_width = 0  # Don't draw a box around legend labels
        else:
            self.legend_border_width = 2  # Enclose legend labels in a box

        if self.parameters['legend_ncol'] == 1:
            self.legend_orientation = 'v'
        else:
            self.legend_orientation = 'h'
        self.legend_border_color = "black"

    def _get_plot_disp(self) -> list:
        """
        Retrieve the values that determine whether to display a particular series
        and convert them to bool if needed

        Args:

        Returns:
                A list of boolean values indicating whether or not to
                display the corresponding series
            """

        plot_display_config_vals = self.get_config_value('plot_disp')
        plot_display_bools = []
        for val in plot_display_config_vals:
            if isinstance(val, bool):
                plot_display_bools.append(val)

            if isinstance(val, str):
                plot_display_bools.append(val.upper() == 'TRUE')

        return self.create_list_by_series_ordering(plot_display_bools)

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
        fcst_var_val_dict = self.get_config_value('fcst_var_val_' + str(index))
        if not fcst_var_val_dict:
            fcst_var_val_dict = {}

        return fcst_var_val_dict

    def config_consistency_check(self) -> None:
        """Checks that the number of settings defined for
            plot_disp, series_ordering, colors_list, user_legends, and show_legend
           are consistent with number of series.

           @raises ValueError if any of settings are inconsistent with the
            number of series (as defined by the cross product of the model
            and vx_mask defined in the series_val_1 setting)
        """
        lists_to_check = {
            "plot_ci": self.plot_ci,
            "plot_disp": self.plot_disp,
            "marker_list": self.marker_list,
            "series_ordering": self.series_ordering,
            "colors_list": self.colors_list,
            "user_legends": self.user_legends,
            "linewidth_list": self.linewidth_list,
            "linestyles_list": self.linestyles_list,
            "show_legend": self.show_legend,
        }
        self._config_compare_lists_to_num_series(lists_to_check)

    def _get_plot_ci(self) -> list:
        """

            Args:

            Returns:
                list of values to indicate whether or not to plot the confidence interval for
                a particular series, and which confidence interval (bootstrap or normal).

        """
        plot_ci_list = self.get_config_value('plot_ci')
        ci_settings_list = [ci.upper() for ci in plot_ci_list]

        # Do some checking to make sure that the values are valid (case-insensitive):
        # None, boot, or met_prm
        for ci_setting in ci_settings_list:
            if ci_setting not in constants.ACCEPTABLE_CI_VALS:
                raise ValueError("A plot_ci value is set to an invalid value. "
                                 "Accepted values are (case insensitive): "
                                 "None, met_prm, or boot. Please check your config file.")

        return self.create_list_by_series_ordering(ci_settings_list)

    def _get_user_legends(self, legend_label_type: str = '') -> list:
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

        all_user_legends = self.get_config_value('user_legend')
        legend_list = []

        # create legend list for  series
        for idx, ser_components in enumerate(self.get_series_y()):
            if idx >= len(all_user_legends) or all_user_legends[idx].strip() == '':
                # user did not provide the legend - create it
                legend_list.append(' '.join(map(str, ser_components)) + ' Reliability Curve')
            else:
                # user provided a legend - use it
                legend_list.append(all_user_legends[idx])

            # add to legend list  legends  derived series

        for idx, ser_components in enumerate(self.summary_curves):
            # index of the legend
            legend_idx = idx + len(self.get_series_y())
            if legend_idx >= len(all_user_legends) or all_user_legends[legend_idx].strip() == '':
                # user did not provide the legend - create it
                legend_list.append(ser_components + ' Reliability Curve')
            else:
                # user provided a legend - use it
                legend_list.append(all_user_legends[legend_idx])

        return self.create_list_by_series_ordering(legend_list)

    def get_series_y(self) -> list:
        """
        Creates an array of series components (excluding derived) tuples
        :return: an array of series components tuples
        """
        all_fields_values = self.get_config_value('series_val_1').copy()
        return list(itertools.product(*all_fields_values.values()))

    def _get_all_series_y(self) -> list:
        """
        Creates an array of all series (including derived) components tuples
        :return: an array of series components tuples
        """

        return self.get_series_y()

    def calculate_number_of_series(self) -> int:
        """
           From the number of items in the permutation list,
           determine how many series "objects" are to be plotted.

           Args:

           Returns:
               the number of series

        """
        # Retrieve the lists from the series_val_1 dictionary
        series_vals_list = self.series_vals_1.copy()

        # Utilize itertools' product() to create the cartesian product of all elements
        # in the lists to produce all permutations of the series_val values and the
        # fcst_var_val values.
        permutations = list(itertools.product(*series_vals_list))

        # add derived
        total = len(permutations) + len(self.summary_curves)

        return total
