# ============================*
 # ** Copyright UCAR (c) 2022
 # ** University Corporation for Atmospheric Research (UCAR)
 # ** National Center for Atmospheric Research (NCAR)
 # ** Research Applications Lab (RAL)
 # ** P.O.Box 3000, Boulder, Colorado, 80307-3000, USA
 # ============================*
 
 
 
"""
Class Name: contour_config.py

Holds values set in the Contour plot config file(s)
"""
__author__ = 'Tatiana Burek'

from ..config import Config
from .. import constants
from .. import util

import metcalcpy.util.utils as utils


class ContourConfig(Config):
    """
    Prepares and organises Contour plot parameters
    """

    def __init__(self, parameters: dict) -> None:
        """ Reads in the plot settings from a Contour plot config file.

            Args:
            @param parameters: dictionary containing user defined parameters

        """
        super().__init__(parameters)

        # Optional setting, indicates *where* to save the dump_points_1 file
        # used by METviewer
        self.points_path = self.get_config_value('points_path')

        # Logging
        self.log_level = self.get_config_value('log_level')
        self.log_filename = self.get_config_value('log_filename')

        # plot parameters
        self.plot_width = self.calculate_plot_dimension('plot_width')
        self.plot_height = self.calculate_plot_dimension('plot_height')
        self.plot_margins = {
            'l': 0,
            'r': self.parameters['mar'][3] + 20,
            't': self.parameters['mar'][2] + 80,
            'b': self.parameters['mar'][0] + 80,
            'pad': 5,
        }
        self.dump_points_1 = self._get_bool('dump_points_1')
        self.plot_stat = self._get_plot_stat()

        ##############################################
        # caption parameters
        self.caption_size = int(constants.DEFAULT_CAPTION_FONTSIZE
                                * self.get_config_value('caption_size'))
        self.caption_offset = self.parameters['caption_offset'] - 3.1

        ##############################################
        # title parameters
        self.title_font_size = self.parameters['title_size'] * constants.DEFAULT_TITLE_FONT_SIZE
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
        self.all_series_y1 = self._get_all_series_y()
        self.num_series = 1
        self.linewidth_list = self._get_linewidths()
        self.linestyles_list = self._get_linestyles()
        self.colors_list = self._get_colors()

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
        self.points_path = self.get_config_value('points_path')

        ##############################################
        self.contour_intervals = self.get_config_value('contour_intervals')
        self.color_palette = self._get_colorscale()
        if self.contour_intervals != len(self.color_palette) - 1:
            print(f"WARNING: Number of contour intervals ({self.contour_intervals}) "
                  f"doesn't match the number of colors in the color palette ({len(self.color_palette)})."
                  f" Setting contour intervals to {len(self.color_palette) - 1}")
            self.contour_intervals = len(self.color_palette) - 1
        self.add_color_bar = self._get_bool('add_color_bar')
        self.xaxis_reverse = self._get_bool('reverse_x') or self._get_bool('xaxis_reverse')
        self.yaxis_reverse = self._get_bool('reverse_y') or self._get_bool('yaxis_reverse')
        self.add_contour_overlay = self._get_bool('add_contour_overlay')

    def _get_colorscale(self):
        """
        Retrieve the pallet name from the config file and
        returns corresponding to the pallet's name colors.
        If the pale name is invalid - return colors for the default pallet 'green_red'

        Returns: the list of colors
        """
        color_palette = self.get_config_value('color_palette')
        if color_palette not in util.COLORSCALES.keys():
            print(f"WARNING: Color pallet {color_palette} doesn't supported. Using default pallet")
            color_palette = 'green_red'
        return util.COLORSCALES[color_palette]

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
            if not fcst_var_val_dict:
                fcst_var_val_dict = {}
        elif index == 2:
            fcst_var_val_dict = self.get_config_value('fcst_var_val_2')
            if not fcst_var_val_dict:
                fcst_var_val_dict = {}
        else:
            fcst_var_val_dict = {}

        return fcst_var_val_dict

    def config_consistency_check(self) -> None:
        """Checks that the number of settings are consistent with number of series.

           @raises ValueError if any of settings are inconsistent with the
            number of series (as defined by the cross product of the model
            and vx_mask defined in the series_val_1 setting)
        """
        lists_to_check = {
            "plot_disp": self.plot_disp,
            "series_ordering": self.series_ordering,
            "colors_list": self.colors_list,
            "user_legends": self.user_legends,
            "linewidth_list": self.linewidth_list,
            "linestyles_list": self.linestyles_list,
        }
        self._config_compare_lists_to_num_series(lists_to_check)

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

        # create legend list for y-axis series
        for idx, ser_components in enumerate(self.get_series_y()):
            if idx >= len(all_user_legends) or all_user_legends[idx].strip() == '':
                # user did not provide the legend - create it
                legend_list.append(' '.join(map(str, ser_components)))
            else:
                # user provided a legend - use it
                legend_list.append(all_user_legends[idx])

        return self.create_list_by_series_ordering(legend_list)

    def get_series_y(self) -> list:
        """
            Creates an array of series components tuples for the specified y-axis
            :return: an array of series components tuples
            """

        all_fields_values = {}
        if self.get_fcst_vars_keys(1):
            all_fields_values['fcst_var'] = self.get_fcst_vars_keys(1)

        stat_name = self.get_config_value('list_stat_1')
        if stat_name is not None:
            all_fields_values['stat_name'] = stat_name
        return utils.create_permutations_mv(all_fields_values, 0)

    def _get_all_series_y(self) -> list:
        """
        Creates an array of all series components tuples
        for the specified y-axis
        :return: an array of series components tuples
        """
        return self.get_series_y()

    def _get_plot_stat(self) -> str:
        """
            Retrieves the plot_stat setting from the config file.
            There will be many statistics values
            (ie stat_name=PODY or stat_name=FAR in data file) that
            correspond to a specific time (init or valid, as specified
            in the config file), for a combination of
            model, vx_mask, fcst_var,etc.  We require a single value
            to represent this combination. Acceptable values are sum, mean, and median.

            Returns:
                 stat_to_plot: one of the following values for the plot_stat: MEAN, MEDIAN, or SUM
        """

        accepted_stats = ['MEAN', 'MEDIAN', 'SUM']
        stat_to_plot = self.get_config_value('plot_stat').upper()

        if stat_to_plot not in accepted_stats:
            raise ValueError("An unsupported statistic was set for the plot_stat setting. "
                             " Supported values are sum, mean, and median.")
        return stat_to_plot
