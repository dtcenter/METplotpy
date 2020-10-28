
#!/usr/bin/env conda run -n blenny_363 python
"""
Class Name: performance_diagram_config.py

Holds values set in the Performance Diagram config file(s)
"""
__author__ = 'Minna Win'
__email__ = 'met_help@ucar.edu'

import re
from plots.config import Config
import plots.constants as constants

class PerformanceDiagramConfig(Config):

    def __init__(self, parameters):
        """ Reads in the plot settings from a performance diagram config file.

            Args:
            @param parameters: dictionary containing user defined parameters

        """

        #
        # Configuration settings that apply to each series (line)
        #

        # init common layout
        super().__init__(parameters)

        # use this setting to determine the ordering of colors, lines, and markers
        self.series_ordering = self._get_series_order()

        # captions
        self.plot_caption = self.get_config_value('plot_caption')
        # plain text, bold, italic, bold italic are choices in METviewer UI
        self.caption_weight = self.get_config_value('caption_weight')
        self.caption_color = self.get_config_value('caption_color')
        # relative magnification
        self.caption_size = self.get_config_value('caption_size')
        # up-down location relative to the x-axis line
        self.caption_offset = self.get_config_value('caption_offset')
        # left-right position
        self.caption_align = self.get_config_value('caption_align')

        # Make the series ordering zero-based to be consistent with Python's zero-based
        # counting/numbering
        self.series_ordering_zb = [sorder - 1 for sorder in self.series_ordering]
        self.plot_contour_legend = self.get_config_value('plot_contour_legend')
        self.stat_input = self.get_config_value('stat_input')
        self.plot_ci = self._get_plot_ci()
        self.plot_stat = self._get_plot_stat()
        self.plot_disp = self._get_plot_disp()
        self.colors_list = self._get_colors()
        self.marker_list = self._get_markers()
        self.linewidth_list = self._get_linewidths()
        self.linestyles_list = self._get_linestyles()
        self.user_legends = self._get_user_legends("Performance")
        self.plot_width = self.calculate_plot_dimension('plot_width', 'in')
        self.plot_height = self.calculate_plot_dimension('plot_height', 'in')

        # x-axis labels and x-axis ticks
        self.x_title_font_size = self.parameters['xlab_size'] + constants.DEFAULT_TITLE_FONTSIZE
        self.x_tickangle = self.parameters['xtlab_orient']
        if self.x_tickangle in constants.XAXIS_ORIENTATION.keys():
            self.x_tickangle = constants.XAXIS_ORIENTATION[self.x_tickangle]
        self.x_tickfont_size = self.parameters['xtlab_size'] + constants.DEFAULT_TITLE_FONTSIZE


        # y-axis labels and y-axis ticks
        self.y_title_font_size = self.parameters['ylab_size'] + constants.DEFAULT_TITLE_FONTSIZE
        self.y_tickangle = self.parameters['ytlab_orient']
        if self.y_tickangle in constants.YAXIS_ORIENTATION.keys():
            self.y_tickangle = constants.YAXIS_ORIENTATION[self.y_tickangle]
        self.y_tickfont_size = self.parameters['ytlab_size'] + constants.DEFAULT_TITLE_FONTSIZE

        # Caption settings
        self.caption = self.get_config_value('plot_caption')
        mv_caption_weight = self.get_config_value('caption_weight')
        self.caption_color = self.get_config_value('caption_color')

        # Only oblique, italic, and normal are supported in Matplotlib, use the
        # MV_TO_MPL_CATPTION_STYLE dictionary to map these caption styles to
        # what was requested in METviewer
        self.caption_weight = constants.MV_TO_MPL_CAPTION_STYLE[mv_caption_weight]


        # Make necessary adjustments from values set in METviewer to
        # corresponding values in Matplotlib.
        requested_caption_size = self.get_config_value('caption_size')
        self.caption_size = self.calculate_caption_size(requested_caption_size)

        # METviewer default set to 0, which corresponds to a y-value in Matplotlib
        # to .13
        mv_caption_offset = self.get_config_value('caption_offset')
        self.caption_offset = mv_caption_offset + 0.13

        # METviewer default is set to 3, which corresponds to an x-value in Matplotlib
        # to 0.05
        mv_caption_align = self.get_config_value('caption_align')
        self.caption_align = mv_caption_align - 2.95



        # legend style settings as defined in METviewer
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
        self.bbox_y = mv_bbox_y +.15
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

        self.anno_var, self.anno_units = self._get_annotation_template()

        # Check that the config file has all the settings for each series
        is_config_consistent = self._config_consistency_check()
        if not is_config_consistent:
            raise ValueError("The number of series defined by series_val_1 is"
                             " inconsistent with the number of settings"
                             " required for describing each series. Please check"
                             " the number of your configuration file's plot_i,"
                             " plot_disp, series_order, user_legend,"
                             " colors, and series_symbols settings.")


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


    def _get_plot_stat(self):
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


    def _config_consistency_check(self):
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
        num_line_widths = len(self.linewidth_list)
        num_linestyles = len(self.linestyles_list)
        status = False

        if num_series == num_plot_disp == \
                    num_markers == num_series_ord == num_colors  \
                    == num_line_widths == num_linestyles:
            status = True
        return status


    def _get_plot_ci(self):
        """

            Args:

            Returns:
                list of values to indicate whether or not to plot the confidence interval for
                a particular series, and which confidence interval (bootstrap or normal).

        """
        plot_ci_list = self.get_config_value('plot_ci')
        ci_settings_list = [ci.upper() for ci in plot_ci_list]

        # Do some checking to make sure that the values are valid (case-insensitive):
        # None, boot, or norm
        for ci_setting in ci_settings_list:
            if ci_setting not in constants.ACCEPTABLE_CI_VALS:
                raise ValueError("A plot_ci value is set to an invalid value. "
                                 "Accepted values are (case insensitive): "
                                 "None, norm, or boot. Please check your config file.")

        # order the ci list according to the series_order setting (e.g. 1 2 3, 2 1 3,..., etc.)
        ordered_ci_settings_list = self.create_list_by_series_ordering(ci_settings_list)

        return ordered_ci_settings_list


    def _get_annotation_template(self):
        """ Retrieve the annotation template, and then extract the units and the variable

        """
        anno_tmpl = self.get_config_value('annotation_template')
        if not anno_tmpl:
            return None, None
        match = re.match(r'^%([a-z|A-Z])(.*)', anno_tmpl)
        if match:
            anno_var = match.group(1)
            anno_units = match.group(2)
        else:
            raise ValueError("Non-conforming annotation template specified in "
                             "config file.  Expecting format of %y <units> or %x <units>")
        return anno_var, anno_units

    def calculate_caption_size(self, requested_caption_size):
        '''
            Calculate the actual caption_size. Override this for Matplotlib and Pyplot implementations.
            The caption size in METviewer is a percent value of magnification.  Make the
            appropriate calculations

            Args:
                @param requested_caption_size: The caption size specified in the config file

            Returns:
                actual_caption_size:  The size that will be applied to the caption
        '''
        # by default, the caption will be located on the lower right side
        # of the plot, below the x-axis.  METviewer has default value of
        # 0.8 (80% magnification)  For this implementation (Matplotlib), set the
        # base caption size to 12, and calculate the font size (in pointsize/pixel)

        caption_size = float(requested_caption_size)
        matplotlib_default_size = 12.0
        actual_caption_size = caption_size * matplotlib_default_size
        return actual_caption_size


