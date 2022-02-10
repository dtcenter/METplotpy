
"""
Class Name: taylor_diagram_config.py

Holds values set in the Taylor Diagram configuration files
"""

__author__ = "Minna Win"

from plots.config import Config
import plots.constants as constants

class TaylorDiagramConfig(Config):
    """
       Parse and organize any Taylor Diagram plot parameters from the
       default and custom configuration files.

    """

    def __init__(self, parameters: dict) -> None:
        """
             Read in the settings from the config file.

             Args:
                 @param parameters:  A dictionary containing user-defined settings for the
                                     plot.
            Returns: None
        """
        super().__init__(parameters)

        # Write/don't write intermediate output points
        self.dump_points_1 = self._get_bool('dump_points_1')
        self.points_path = self.get_config_value('points_path')

        # settings for determining ordering of colors, lines, markers, etc.
        self.series_ordering = self._get_series_order()

        # Make series ordering zero-based to achieve consistency with Python,
        # which is zero-based.
        self.series_ordering_zb = [sorder -1 for sorder in self.series_ordering]
        self.stat_input = self.get_config_value('stat_input')
        self.plot_disp = self._get_plot_disp()
        self.colors_list = self._get_colors()
        self.marker_list = self._get_markers()
        # self.linewidth_list = self._get_linewidths()
        # self.linestyles_list = self._get_linestyles()
        self.user_legends = self._get_user_legends("")
        self.plot_units = self.get_config_value('plot_units')
        self.plot_resolution = self.get_config_value('plot_res')
        self.show_gamma = self._get_bool('taylor_show_gamma')
        self.values_of_corr = self._get_bool('taylor_voc')


        # Convert the plot height and width to inches if units aren't in
        # inches.
        if self.plot_units.lower() != 'in':
            self.plot_width = self.calculate_plot_dimension('plot_width', 'in')
            self.plot_height = self.calculate_plot_dimension('plot_height', 'in')

        # x-axis labels, x-axis ticks
        self.x_title_font_size = self.parameters['xlab_size'] * constants.DEFAULT_CAPTION_FONTSIZE

        # y-axis labels and y-axis ticks
        self.y_title_font_size = self.parameters['ylab_size'] * constants.DEFAULT_CAPTION_FONTSIZE
        self.y_tickangle = self.parameters['ytlab_orient']
        if self.y_tickangle in constants.YAXIS_ORIENTATION.keys():
            self.y_tickangle = constants.YAXIS_ORIENTATION[self.y_tickangle]
        self.y_tickfont_size = self.parameters['ytlab_size'] * constants.MPL_FONT_SIZE_DEFAULT

        # legend style settings as defined in METviewer:
        # legend box, ncol, inset
        user_settings = self._get_legend_style()

        # list of the x, y, and loc values for the
        # bbox_to_anchor() setting used in determining
        # the location of the bounding box which defines
        # the legend.

        # adjust METviewer values to be consistent with the Matplotlib scale
        # The METviewer x default is set to 0, which corresponds to a Matplotlib
        # x-value of 0.5 (roughly centered with respect to the x-axis)
        mv_bbox_x = float(user_settings['bbox_x'])
        self.bbox_x = mv_bbox_x + 0.5

        # METviewer legend box y-value is set to -.25 by default, which corresponds
        # to a Matplotlib y-value of -.1
        mv_bbox_y = float(user_settings['bbox_y'])
        self.bbox_y = mv_bbox_y + .15
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

        # left-right location of x-axis label/title relative to the y-axis line
        # make adjustments between METviewer default and Matplotlib's center
        # METviewer default value of 2 corresponds to Matplotlib value of .5
        #
        mv_x_title_offset = self.get_config_value('xlab_offset')
        self.x_title_offset = float(mv_x_title_offset) - 1.5

        # up-down of x-axis label/title position
        # make adjustments between METviewer default and Matplotlib's center
        # METviewer default is .5, Matplotlib center is 0.05, so subtract 0.55 from the
        # METviewer setting to get the correct Matplotlib y-value (up/down)
        # for the x-title position
        mv_x_title_align = self.get_config_value('xlab_align')
        self.x_title_align = float(mv_x_title_align) - .55

        # left-right position of y-axis label/title position
        # make adjustments between METviewer default and Matplotlib's center
        # METviewer default is .5, Matplotlib center is -0.05
        mv_y_title_align = self.get_config_value('ylab_align')
        self.y_title_align = float(mv_y_title_align) - 0.55

        # up-down location of y-axis label/title relative to the x-axis line
        # make adjustments between METviewer default and Matplotlib's center
        # METviewer default value of -2 corresponds to Matplotlib value of 0.4
        #
        mv_y_title_offset = self.get_config_value('ylab_offset')
        self.y_title_offset = float(mv_y_title_offset) + 2.4

        # Need to use a combination of Matplotlib's font weight and font style to
        # re-create the METviewer ylab_weight. Use the
        # MV_TO_MPL_CAPTION_STYLE dictionary to map these caption styles to
        # what was requested in METviewer
        mv_ylab_weight = self.get_config_value('ylab_weight')
        self.ylab_weight = constants.MV_TO_MPL_CAPTION_STYLE[mv_ylab_weight]

        # The plot's title size, title weight, and positioning in left-right and up-down directions
        mv_title_size = self.get_config_value('title_size')
        self.title_size = mv_title_size * constants.MPL_FONT_SIZE_DEFAULT

        mv_title_weight = self.get_config_value('title_weight')
        # use the same constants dictionary as used for captions
        self.title_weight = constants.MV_TO_MPL_CAPTION_STYLE[mv_title_weight]

        # does nothing because the vertical position in Matplotlib is
        # automatically chosen to avoid labels and ticks on the topmost
        # x-axis
        mv_title_offset = self.get_config_value('title_offset')
        offset_val = float(mv_title_offset)
        self.offset_val = offset_val

        # These values can't be used as-is, the only choice for aligning in Matplotlib
        # are center (default), left, and right
        mv_title_align = self.get_config_value('title_align')
        title_align_val = float(mv_title_align)
        # set to center, left, or right based on the numerical value in the
        # config file: 1.5- right, -1.5 - left, 0.5 and other values - center
        if title_align_val == 1.5:
            self.title_align = 'right'
        elif title_align_val == -1.5:
            self.title_align = 'left'
        else:
            # the default setting
            self.title_align = 'center'

        # Need to use a combination of Matplotlib's font weight and font style to
        # re-create the METviewer xlab_weight. Use the
        # MV_TO_MPL_CAPTION_STYLE dictionary to map these caption styles to
        # what was requested in METviewer
        mv_xlab_weight = self.get_config_value('xlab_weight')
        self.xlab_weight = constants.MV_TO_MPL_CAPTION_STYLE[mv_xlab_weight]

        self.x_tickangle = self.parameters['xtlab_orient']
        if self.x_tickangle in constants.XAXIS_ORIENTATION.keys():
            self.x_tickangle = constants.XAXIS_ORIENTATION[self.x_tickangle]
        self.x_tickfont_size = self.parameters['xtlab_size'] * constants.MPL_FONT_SIZE_DEFAULT

        # Check that the config file has all the settings for each series
        is_config_consistent = self._config_consistency_check()
        if not is_config_consistent:
            raise ValueError("The number of series defined by series_val_1 is"
                             " inconsistent with the number of settings"
                             " required for describing each series. Please check"
                             " the number of your configuration file's plot_i,"
                             " plot_disp, series_order, user_legend,"
                             " colors, and series_symbols settings.")


        # Taylor diagram grid lines, etc.
        self.grid_linestyle = self.get_config_value('grid_lty')
        self.grid_color = self.get_config_value('grid_col')
        self.grid_linewidth = self.get_config_value('grid_linewidth')

        # use this setting to determine the ordering of colors, lines, and markers
        self.series_ordering = self._get_series_order()

        # Caption settings
        self.caption = self.get_config_value('plot_caption')
        mv_caption_weight = self.get_config_value('caption_weight')
        self.caption_color = self.get_config_value('caption_col')
        self.plot_caption = self.get_config_value('plot_caption')

        # Need to use a combination of Matplotlib's font weight and font style to
        # re-create the METviewer caption weight. Use the
        # MV_TO_MPL_CAPTION_STYLE dictionary to map these caption styles to
        # what was requested in METviewer
        self.caption_weight = constants.MV_TO_MPL_CAPTION_STYLE[mv_caption_weight]


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

    def _get_plot_disp(self) -> list:
        """
            Retrieve the boolean values that determine whether to display a particular series

            Args:

            Returns:
                A list of boolean values indicating whether or not to
                display the corresponding series
        """

        plot_display_vals = self.get_config_value('plot_disp')

        # Convert these string values to the boolean values they represent to avoid
        # inconsistent results.
        plot_display_bools = []
        for cur_pd in plot_display_vals:
            if cur_pd.lower() == 'true':
                plot_display_bools.append(True)
            else:
                plot_display_bools.append(False)

        plot_display_bools_ordered = self.create_list_by_series_ordering(plot_display_bools)

        return plot_display_bools_ordered

    def _get_markers(self) -> list:
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
                markers_list.append(constants.PCH_TO_MATPLOTLIB_MARKER[marker.lower()])
        markers_list_ordered = self.create_list_by_series_ordering(list(markers_list))
        return markers_list_ordered

    def _config_consistency_check(self) -> bool:
        """
            Checks that the number of settings defined for
            plot_disp, series_order, colors, and series_symbols
            are consistent.

            Args:

            Returns:
                True if the number of settings for each of the above
                settings is consistent with the number of
                series (as defined by the cross product of the model
                and vx_mask defined in the series_val_1 setting)

        """
        # Determine the number of series based on the number of
        # permutations from the series_var setting in the
        # config file
        num_series = self.calculate_number_of_series()

        # Numbers of values for other settings for series
        num_plot_disp = len(self.plot_disp)
        num_markers = len(self.marker_list)
        num_series_ord = len(self.series_ordering)
        num_colors = len(self.colors_list)
        # num_line_widths = len(self.linewidth_list)
        # num_linestyles = len(self.linestyles_list)
        status = False

        if num_series == num_plot_disp == \
                    num_markers == num_series_ord == num_colors:
            status = True
        return status

    def _get_fcst_vars(self, index: int) -> list:
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

