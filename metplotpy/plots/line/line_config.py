"""
Class Name: line_config.py

Holds values set in the Line plot config file(s)
"""
__author__ = 'Minna Win, Hank Fisher'
__email__ = 'met_help@ucar.edu'

import itertools

from plots.config import Config
import plots.constants as constants
import plots.util as util

import metcalcpy.util.utils as utils
from metcalcpy.util.utils import OPERATION_TO_SIGN


class LineConfig(Config):

    def __init__(self, parameters):
        """ Reads in the plot settings from a line plot config file.

            Args:
            @param parameters: dictionary containing user defined parameters

        """

        #
        # Configuration settings that apply to each series (line)
        #

        # init common layout
        super().__init__(parameters)

        self.paper_bgcolor = "white"
        self.line_color = "#c2c2c2"
        self.line_width = 2

        self.title_font_size = self.parameters['title_size'] * constants.DEFAULT_TITLE_FONT_SIZE
        self.title_offset = self.parameters['title_offset'] * constants.DEFAULT_TITLE_OFFSET

        self.y_title_font_size = self.parameters['ylab_size'] + constants.DEFAULT_TITLE_FONTSIZE
        self.y_tickangle = self.parameters['ytlab_orient']
        if self.y_tickangle in constants.YAXIS_ORIENTATION.keys():
            self.y_tickangle = constants.YAXIS_ORIENTATION[self.y_tickangle]
        self.y_tickfont_size = self.parameters['ytlab_size'] + constants.DEFAULT_TITLE_FONTSIZE

        self.y2_title_font_size = self.parameters['y2lab_size'] + constants.DEFAULT_TITLE_FONTSIZE
        self.y2_tickangle = self.parameters['y2tlab_orient']
        if self.y2_tickangle in constants.YAXIS_ORIENTATION.keys():
            self.y2_tickangle = constants.YAXIS_ORIENTATION[self.y2_tickangle]
        self.y2_tickfont_size = self.parameters['y2tlab_size'] + constants.DEFAULT_TITLE_FONTSIZE

        self.x_title_font_size = self.parameters['xlab_size'] + constants.DEFAULT_TITLE_FONTSIZE
        self.x_tickangle = self.parameters['xtlab_orient']
        if self.x_tickangle in constants.XAXIS_ORIENTATION.keys():
            self.x_tickangle = constants.XAXIS_ORIENTATION[self.x_tickangle]
        self.x_tickfont_size = self.parameters['xtlab_size'] + constants.DEFAULT_TITLE_FONTSIZE

        self.x2_title_font_size = self.parameters['x2lab_size'] + constants.DEFAULT_TITLE_FONTSIZE
        self.x2_tickangle = self.parameters['x2tlab_orient']
        if self.x2_tickangle in constants.XAXIS_ORIENTATION.keys():
            self.x2_tickangle = constants.XAXIS_ORIENTATION[self.x2_tickangle]
        self.x2_tickfont_size = self.parameters['x2tlab_size'] + constants.DEFAULT_TITLE_FONTSIZE

        # use alpha blending for the grid lines
        self.blended_grid_col = util.alpha_blending(self.parameters['grid_col'], 0.5)

        self.xaxis = util.apply_weight_style(self.xaxis, self.parameters['xlab_weight'])
        self.series_ordering = self.get_config_value('series_order')

        self.plot_disp = self._get_plot_disp()

        # Make the series ordering zero-based to be consistent with Python's zero-based
        # counting/numbering
        self.series_ordering_zb = [sorder - 1 for sorder in self.series_ordering]

        self.plot_width = self.calculate_plot_dimension('plot_width', 'pixels')
        self.plot_height = self.calculate_plot_dimension('plot_height', 'pixels')
        self.plot_margins = dict(l=0,
                                 r=self.parameters['mar'][3] + 20,
                                 t=self.parameters['mar'][2] + 80,
                                 b=self.parameters['mar'][0] + 80,
                                 pad=5
                                 )
        self.caption_size = int(constants.DEFAULT_CAPTION_FONTSIZE * self.get_config_value('caption_size'))
        self.caption_offset = self.parameters['caption_offset'] - 3.1
        self.colors_list = self._get_colors()
        self.marker_list = self._get_markers()
        self.marker_size = self._get_markers_size()
        self.mode = self._get_mode()
        self.linewidth_list = self._get_linewidths()
        self.linestyles_list = self._get_linestyles()
        self.plot_ci = self._get_plot_ci()

        # list of the x, y, and loc values for the
        # bbox_to_anchor() setting used in determining
        # the location of the bounding box which defines
        # the legend.
        self.bbox_x = 0.5 + self.parameters['legend_inset']['x']
        # set legend box lower by .18 pixels of the default value
        # set in METviewer to prevent obstructing the x-axis.
        self.bbox_y = -0.12 + self.parameters['legend_inset']['y'] + 0.25
        self.legend_size = int(constants.DEFAULT_LEGEND_FONTSIZE * self.parameters['legend_size'])

        if self.parameters['legend_box'].lower() == 'n':
            # Don't draw a box around legend labels
            self.legend_border_width = 0
        else:
            # Other choice is 'o'
            # Enclose legend labels in a box
            self.legend_border_width = 2

        if self.parameters['legend_ncol'] == 1:
            self.legend_orientation = 'v'
        else:
            self.legend_orientation = 'h'
        self.legend_border_color = "black"

        self.plot_stat = self._get_plot_stat()
        self.show_nstats = self._get_bool('show_nstats')

        self.all_series_y1 = self._get_all_series_y(1)
        self.all_series_y2 = self._get_all_series_y(2)
        self.user_legends = self._get_user_legends("")
        self.indy_stagger = self._get_bool('indy_stagger_1')
        self.variance_inflation_factor = self._get_bool('variance_inflation_factor')
        self.dump_points_1 = self._get_bool('dump_points_1')
        self.dump_points_2 = self._get_bool('dump_points_2')
        self.vert_plot = self._get_bool('vert_plot')
        self.xaxis_reverse = self._get_bool('xaxis_reverse')
        self.sync_yaxes = self._get_bool('sync_yaxes')
        self.grid_on = self._get_bool('grid_on')
        self.con_series = self._get_con_series()
        self.num_series = self.calculate_number_of_series()
        self.create_html = self._get_bool('create_html')

    def _get_plot_disp(self):
        """
                Retrieve the boolean values that determine whether to display a particular series

                Args:

                Returns:
                    A list of boolean values indicating whether or not to
                    display the corresponding series
            """

        plot_display_config_vals = self.get_config_value('plot_disp')
        plot_display_bools = []
        for val in plot_display_config_vals:
            if str(val).upper() == "TRUE":
                plot_display_bools.append(True)
            else:
                plot_display_bools.append(False)

        plot_display_bools_ordered = self.create_list_by_series_ordering(plot_display_bools)
        return plot_display_bools_ordered

    def get_fcst_vars(self, index):
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

    def _get_mode(self):
        """
           Retrieve all the modes. Convert mode names from
           the config file into plotly python's mode names.

           Args:

           Returns:
               markers: a list of the plotly markers
        """
        modes = self.get_config_value('series_type')
        mode_list = []
        for mode in modes:
            if mode in constants.TYPE_TO_PLOTLY_MODE.keys():
                # the recognized plotly marker names:
                # circle-open (for small circle), circle, triangle-up,
                # square, diamond, or hexagon
                mode_list.append(constants.TYPE_TO_PLOTLY_MODE[mode])
            else:
                mode_list.append('lines+markers')
        mode_list_ordered = self.create_list_by_series_ordering(mode_list)
        return mode_list_ordered

    def _get_linestyles(self):
        """
           Retrieve all the markers. Convert marker names from
           the config file into plotly python's marker names.

           Args:

           Returns:
               markers: a list of the plotly markers
        """
        line_styles = self.get_config_value('series_line_style')
        line_style_list = []
        for line_style in line_styles:
            if line_style in constants.LINE_STYLE_TO_PLOTLY_DASH.keys():
                # the recognized plotly marker names:
                # circle-open (for small circle), circle, triangle-up,
                # square, diamond, or hexagon
                line_style_list.append(constants.LINE_STYLE_TO_PLOTLY_DASH[line_style])
            else:
                line_style_list.append(None)
        line_style_list_ordered = self.create_list_by_series_ordering(line_style_list)
        return line_style_list_ordered

    def _get_markers(self):
        """
           Retrieve all the markers. Convert marker names from
           the config file into plotly python's marker names.

           Args:

           Returns:
               markers: a list of the plotly markers
        """
        markers = self.get_config_value('series_symbols')
        markers_list = []
        for marker in markers:
            if marker in constants.AVAILABLE_PLOTLY_MARKERS_LIST:
                # the recognized plotly marker names:
                # circle-open (for small circle), circle, triangle-up,
                # square, diamond, or hexagon
                markers_list.append(marker)
            else:
                markers_list.append(constants.PCH_TO_PLOTLY_MARKER[marker])
        markers_list_ordered = self.create_list_by_series_ordering(markers_list)
        return markers_list_ordered

    def _get_markers_size(self):
        """
           Retrieve all the markers. Convert marker names from
           the config file into plotly python's marker names.

           Args:

           Returns:
               markers: a list of the plotly markers
        """
        markers = self.get_config_value('series_symbols')
        markers_size = []
        for marker in markers:
            markers_size.append(constants.PCH_TO_PLOTLY_MARKER_SIZE[marker])

        markers_size_ordered = self.create_list_by_series_ordering(markers_size)
        return markers_size_ordered

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
            Checks that the number of settings defined for plot_ci,
            plot_disp, series_order, user_legend colors, and series_symbols
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

        # Numbers of values for other settings for series
        num_ci_settings = len(self.plot_ci)
        num_plot_disp = len(self.plot_disp)
        num_markers = len(self.marker_list)
        num_series_ord = len(self.series_ordering)
        num_colors = len(self.colors_list)
        num_legends = len(self.user_legends)
        num_line_widths = len(self.linewidth_list)
        num_linestyles = len(self.linestyles_list)
        status = False

        if self.num_series == num_plot_disp == \
                num_markers == num_series_ord == num_colors \
                == num_legends == num_line_widths == num_linestyles == num_ci_settings:
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

    def _get_user_legends(self, legend_label_type):

        all_legends = self.get_config_value('user_legend')
        legend_list = []
        num_series_y1 = len(self.get_series_y(1))
        for idx, ser_components in enumerate(self.get_series_y(1)):
            if idx >= len(all_legends) or all_legends[idx].strip() == '':
                if len(ser_components) == 3 and ser_components[2] in OPERATION_TO_SIGN.keys():
                    # this is a derived series
                    legend_list.append(utils.get_derived_curve_name(ser_components))
                else:
                    legend_list.append(' '.join(map(str, ser_components)))
            else:
                legend_list.append(all_legends[idx])

        num_series_y2 = len(self.get_series_y(2))
        for idx, ser_components in enumerate(self.get_series_y(2)):
            if idx + num_series_y1 >= len(all_legends) or all_legends[idx + num_series_y1].strip() == '':
                if len(ser_components) == 3 and ser_components[2] in OPERATION_TO_SIGN.keys():
                    # this is a derived series
                    legend_list.append(utils.get_derived_curve_name(ser_components))
                else:
                    legend_list.append(' '.join(map(str, ser_components)))
            else:
                legend_list.append(all_legends[idx + num_series_y1])

        num_series_y1_d = len(self.get_config_value('derived_series_1'))
        for idx, ser_components in enumerate(self.get_config_value('derived_series_1')):
            if idx + num_series_y1 + num_series_y2 >= len(all_legends) or all_legends[
                idx + num_series_y1 + num_series_y2].strip() == '':
                if len(ser_components) == 3 and ser_components[2] in OPERATION_TO_SIGN.keys():
                    # this is a derived series
                    legend_list.append(utils.get_derived_curve_name(ser_components))
                else:
                    legend_list.append(' '.join(map(str, ser_components)))
            else:
                legend_list.append(all_legends[idx + num_series_y1 + num_series_y2])

        for idx, ser_components in enumerate(self.get_config_value('derived_series_2')):
            if idx + num_series_y1 + num_series_y2 + num_series_y1_d >= len(all_legends) or all_legends[
                idx + num_series_y1 + num_series_y2 + num_series_y1_d].strip() == '':
                if len(ser_components) == 3 and ser_components[2] in OPERATION_TO_SIGN.keys():
                    # this is a derived series
                    legend_list.append(utils.get_derived_curve_name(ser_components))
                else:
                    legend_list.append(' '.join(map(str, ser_components)))
            else:
                legend_list.append(all_legends[idx + num_series_y1 + num_series_y2 + num_series_y1_d])

        legends_list_ordered = self.create_list_by_series_ordering(legend_list)
        return legends_list_ordered

    def get_series_y(self, axis):
        all_fields_values = self.get_config_value('series_val_' + str(axis)).copy()
        if self.get_fcst_vars(axis):
            all_fields_values['fcst_var'] = list(self.get_fcst_vars(axis).keys())

        all_fields_values['stat_name'] = self.get_config_value('list_stat_' + str(axis))
        return list(itertools.product(*all_fields_values.values()))

    def _get_all_series_y(self, axis):
        all_series = self.get_series_y(axis)

        # add derived series if exist
        if self.get_config_value('derived_series_' + str(axis)):
            all_series = all_series + self.get_config_value('derived_series_' + str(axis))

        return all_series
