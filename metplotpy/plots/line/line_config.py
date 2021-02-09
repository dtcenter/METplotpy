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


class LineConfig(Config):
    """
    Prepares and organises Line plot parameters
    """

    def __init__(self, parameters: dict) -> None:
        """ Reads in the plot settings from a line plot config file.

            Args:
            @param parameters: dictionary containing user defined parameters

        """
        super().__init__(parameters)

        # plot parameters
        self.grid_on = self._get_bool('grid_on')
        self.plot_width = self.calculate_plot_dimension('plot_width', 'pixels')
        self.plot_height = self.calculate_plot_dimension('plot_height', 'pixels')
        self.plot_margins = dict(l=0,
                                 r=self.parameters['mar'][3] + 20,
                                 t=self.parameters['mar'][2] + 80,
                                 b=self.parameters['mar'][0] + 80,
                                 pad=5
                                 )
        self.blended_grid_col = util.alpha_blending(self.parameters['grid_col'], 0.5)
        self.plot_stat = self._get_plot_stat()
        self.show_nstats = self._get_bool('show_nstats')
        self.indy_stagger = self._get_bool('indy_stagger_1')
        self.variance_inflation_factor = self._get_bool('variance_inflation_factor')
        self.dump_points_1 = self._get_bool('dump_points_1')
        self.dump_points_2 = self._get_bool('dump_points_2')
        self.vert_plot = self._get_bool('vert_plot')
        self.xaxis_reverse = self._get_bool('xaxis_reverse')
        self.sync_yaxes = self._get_bool('sync_yaxes')
        self.create_html = self._get_bool('create_html')

        ##############################################
        # caption parameters
        self.caption_size = int(constants.DEFAULT_CAPTION_FONTSIZE
                                * self.get_config_value('caption_size'))
        self.caption_offset = self.parameters['caption_offset'] - 3.1

        ##############################################
        # title parameters
        self.title_font_size = self.parameters['title_size'] * constants.DEFAULT_TITLE_FONT_SIZE
        self.title_offset = self.parameters['title_offset'] * constants.DEFAULT_TITLE_OFFSET
        self.y_title_font_size = self.parameters['ylab_size'] + constants.DEFAULT_TITLE_FONTSIZE

        ##############################################
        # y-axis parameters
        self.y_tickangle = self.parameters['ytlab_orient']
        if self.y_tickangle in constants.YAXIS_ORIENTATION.keys():
            self.y_tickangle = constants.YAXIS_ORIENTATION[self.y_tickangle]
        self.y_tickfont_size = self.parameters['ytlab_size'] + constants.DEFAULT_TITLE_FONTSIZE

        ##############################################
        # y2-axis parameters
        self.y2_title_font_size = self.parameters['y2lab_size'] + constants.DEFAULT_TITLE_FONTSIZE
        self.y2_tickangle = self.parameters['y2tlab_orient']
        if self.y2_tickangle in constants.YAXIS_ORIENTATION.keys():
            self.y2_tickangle = constants.YAXIS_ORIENTATION[self.y2_tickangle]
        self.y2_tickfont_size = self.parameters['y2tlab_size'] + constants.DEFAULT_TITLE_FONTSIZE

        ##############################################
        # x-axis parameters
        self.x_title_font_size = self.parameters['xlab_size'] + constants.DEFAULT_TITLE_FONTSIZE
        self.x_tickangle = self.parameters['xtlab_orient']
        if self.x_tickangle in constants.XAXIS_ORIENTATION.keys():
            self.x_tickangle = constants.XAXIS_ORIENTATION[self.x_tickangle]
        self.x_tickfont_size = self.parameters['xtlab_size'] + constants.DEFAULT_TITLE_FONTSIZE
        self.xaxis = util.apply_weight_style(self.xaxis, self.parameters['xlab_weight'])

        ##############################################
        # x2-axis parameters
        self.x2_title_font_size = self.parameters['x2lab_size'] + constants.DEFAULT_TITLE_FONTSIZE
        self.x2_tickangle = self.parameters['x2tlab_orient']
        if self.x2_tickangle in constants.XAXIS_ORIENTATION.keys():
            self.x2_tickangle = constants.XAXIS_ORIENTATION[self.x2_tickangle]
        self.x2_tickfont_size = self.parameters['x2tlab_size'] + constants.DEFAULT_TITLE_FONTSIZE

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
        self.all_series_y1 = self._get_all_series_y(1)
        self.all_series_y2 = self._get_all_series_y(2)
        self.con_series = self._get_con_series()
        self.num_series = self.calculate_number_of_series()

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

    def _get_mode(self) -> list:
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
        return self.create_list_by_series_ordering(mode_list)

    def _get_linestyles(self) -> list:
        """
           Retrieve all the line styles. Convert line style names from
           the config file into plotly python's line style names.

           Args:

           Returns:
               line_styles: a list of the plotly line styles
        """
        line_styles = self.get_config_value('series_line_style')
        line_style_list = []
        for line_style in line_styles:
            if line_style in constants.LINE_STYLE_TO_PLOTLY_DASH.keys():
                line_style_list.append(constants.LINE_STYLE_TO_PLOTLY_DASH[line_style])
            else:
                line_style_list.append(None)
        return self.create_list_by_series_ordering(line_style_list)

    def _get_markers(self) -> list:
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
        return self.create_list_by_series_ordering(markers_list)

    def _get_markers_size(self) -> list:
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
            if marker in constants.AVAILABLE_PLOTLY_MARKERS_LIST:
                markers_size.append(marker)
            else:
                markers_size.append(constants.PCH_TO_PLOTLY_MARKER_SIZE[marker])

        return self.create_list_by_series_ordering(markers_size)

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

    def _config_consistency_check(self) -> bool:
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
        # None, boot, or norm
        for ci_setting in ci_settings_list:
            if ci_setting not in constants.ACCEPTABLE_CI_VALS:
                raise ValueError("A plot_ci value is set to an invalid value. "
                                 "Accepted values are (case insensitive): "
                                 "None, norm, or boot. Please check your config file.")

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

        # create legend list for y-axis series
        for idx, ser_components in enumerate(self.get_series_y(1)):
            if idx >= len(all_user_legends) or all_user_legends[idx].strip() == '':
                # user did not provide the legend - create it
                legend_list.append(' '.join(map(str, ser_components)))
            else:
                # user provided a legend - use it
                legend_list.append(all_user_legends[idx])

        # add to legend list  legends for y2-axis series
        num_series_y1 = len(self.get_series_y(1))
        for idx, ser_components in enumerate(self.get_series_y(2)):
            # index of the legend
            legend_idx = idx + num_series_y1

            if legend_idx >= len(all_user_legends) or all_user_legends[legend_idx].strip() == '':
                # user did not provide the legend - create it
                legend_list.append(' '.join(map(str, ser_components)))
            else:
                # user provided a legend - use it
                legend_list.append(all_user_legends[legend_idx])

        # add to legend list  legends for y-axis derived series
        num_series_y2 = len(self.get_series_y(2))

        for idx, ser_components in enumerate(self.get_config_value('derived_series_1')):
            # index of the legend
            legend_idx = idx + num_series_y1 + num_series_y2
            if legend_idx >= len(all_user_legends) or all_user_legends[legend_idx].strip() == '':
                # user did not provide the legend - create it
                legend_list.append(utils.get_derived_curve_name(ser_components))
            else:
                # user provided a legend - use it
                legend_list.append(all_user_legends[legend_idx])

        # add to legend list  legends for y2-axis derived series
        for idx, ser_components in enumerate(self.get_config_value('derived_series_2')):
            # index of the legend
            legend_idx = idx + num_series_y1 + num_series_y2 \
                         + len(self.get_config_value('derived_series_1'))
            if legend_idx >= len(all_user_legends) or all_user_legends[legend_idx].strip() == '':
                # user did not provide the legend - create it
                legend_list.append(utils.get_derived_curve_name(ser_components))
            else:
                # user provided a legend - use it
                legend_list.append(all_user_legends[legend_idx])

        return self.create_list_by_series_ordering(legend_list)

    def get_series_y(self, axis: int) -> list:
        """
        Creates an array of series components (excluding derived) tuples for the specified y-axis
        :param axis: y-axis (1 or 2)
        :return: an array of series components tuples
        """
        all_fields_values_orig = self.get_config_value('series_val_' + str(axis)).copy()
        all_fields_values = {}
        for x in reversed(list(all_fields_values_orig.keys())):
            all_fields_values[x] = all_fields_values_orig.get(x)

        if self._get_fcst_vars(axis):
            all_fields_values['fcst_var'] = list(self._get_fcst_vars(axis).keys())

        all_fields_values['stat_name'] = self.get_config_value('list_stat_' + str(axis))
        return utils.create_permutations_mv(all_fields_values, 0)

    def _get_all_series_y(self, axis: int) -> list:
        """
        Creates an array of all series (including derived) components tuples
        for the specified y-axis
        :param axis: y-axis (1 or 2)
        :return: an array of series components tuples
        """
        all_series = self.get_series_y(axis)

        # add derived series if exist
        if self.get_config_value('derived_series_' + str(axis)):
            all_series = all_series + self.get_config_value('derived_series_' + str(axis))

        return all_series

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
        if isinstance(self.fcst_var_val_1, list) is True:
            fcst_vals = self.fcst_var_val_1
        elif isinstance(self.fcst_var_val_1, dict) is True:
            fcst_vals = list(self.fcst_var_val_1.values())
        fcst_vals_flat = [item for sublist in fcst_vals for item in sublist]
        series_vals_list.append(fcst_vals_flat)

        # Utilize itertools' product() to create the cartesian product of all elements
        # in the lists to produce all permutations of the series_val values and the
        # fcst_var_val values.
        permutations = list(itertools.product(*series_vals_list))

        if self.series_vals_2:
            series_vals_list_2 = self.series_vals_2.copy()
            if isinstance(self.fcst_var_val_2, list) is True:
                fcst_vals_2 = self.fcst_var_val_2
            elif isinstance(self.fcst_var_val_2, dict) is True:
                fcst_vals_2 = list(self.fcst_var_val_2.values())
            fcst_vals_2_flat = [item for sublist in fcst_vals_2 for item in sublist]
            series_vals_list_2.append(fcst_vals_2_flat)
            permutations_2 = list(itertools.product(*series_vals_list_2))
            permutations.extend(permutations_2)

        total = len(permutations)
        # add derived
        total = total + len(self.get_config_value('derived_series_1'))
        total = total + len(self.get_config_value('derived_series_2'))

        return total
