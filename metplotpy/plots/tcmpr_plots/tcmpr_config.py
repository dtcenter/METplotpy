# ============================*
# ** Copyright UCAR (c) 2020
# ** University Corporation for Atmospheric Research (UCAR)
# ** National Center for Atmospheric Research (NCAR)
# ** Research Applications Lab (RAL)
# ** P.O.Box 3000, Boulder, Colorado, 80307-3000, USA
# ============================*


"""
Class Name: tcmpr_config.py

Holds values set in the box plot config file(s)
"""

import warnings
import itertools

import metcalcpy.util.utils as utils
from .. import constants
from .. import util
from ..config import Config
import metplotpy.plots.util as util


class TcmprConfig(Config):
    """
    Prepares and organises Line plot parameters
    """
    SUPPORTED_PLOT_TYPES = ['boxplot', 'point', 'mean', 'median', 'relperf', 'rank', 'skill_mn', 'skill_md']
    def __init__(self, parameters: dict) -> None:
        """ Reads in the plot settings from a box plot config file.

            Args:
            @param parameters: dictionary containing user defined parameters

        """
        super().__init__(parameters)

        # Logging
        self.log_filename = self.get_config_value('log_filename')
        self.log_level = self.get_config_value('log_level')
        self.logger = util.get_common_logger(self.log_level, self.log_filename)

        ##############################################
        self.plot_type_list = self._get_plot()
        self.tcst_files = self._get_tcst_files()
        self.tcst_dir = self._get_tcst_dir()
        self.rp_diff = self._get_rp_diff()
        self.hfip_bsln = self._get_hfip_bsln()
        self.footnote_flag = self._get_bool('footnote_flag')
        self.n_min = self.get_config_value('n_min')
        self.scatter_x = self.get_config_value('scatter_x')
        self.scatter_y = self.get_config_value('scatter_y')
        self.demo_yr = self.get_config_value('demo_yr')  # not used in Rscript. not sure if we need it
        self.alpha = self.get_config_value('alpha')

        # Check the relative scatter settings
        if len(self.scatter_x) != len(self.scatter_y):
            raise ValueError("ERROR: The number of scatter_x and scatter_y variables specified must match each other")
        self.skill_ref = self.get_config_value('skill_ref')

        ##############################################

        # plot parameters
        self.grid_on = self._get_bool('grid_on')
        self.plot_width = self.calculate_plot_dimension('plot_width', 'pixels')
        self.plot_height = self.calculate_plot_dimension('plot_height', 'pixels')
        self.plot_margins = self.parameters['mar']
        self.blended_grid_col = util.alpha_blending(self.parameters['grid_col'], 0.5)
        self.plot_stat = self._get_plot_stat()
        self.show_nstats = self._get_bool('show_nstats')
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
        self.series_ci = self._get_series_ci()
        self.colors_list = self._get_colors()
        self.all_series_y1 = self._get_all_series_y(1)
        self.num_series = self.calculate_number_of_series()
        self.linewidth_list = self._get_linewidths()
        self.linestyles_list = self._get_linestyles()
        self.marker_list = self._get_markers()
        self.marker_size = self._get_markers_size()

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

        self.box_avg = self._get_bool('box_avg')
        self.box_notch = self._get_bool('box_notch')

        self.plot_dir = self.parameters['plot_dir']
        self.prefix = self.parameters['prefix']
        self.subtitle = self._get_subtitle()
        self.baseline_file = self.parameters['baseline_file']
        self.column_info_file = self.parameters['column_info_file']

    # TODO validate list_stat_1. It should have only one element for now
    # TODO validate series_vals_1. It should have only one key element for now

    def _get_subtitle(self):
        if self.parameters['subtitle'] is not None and len(self.parameters['subtitle']) > 0:
            return self.parameters['subtitle']
        else:
            filter_str = ''
            for key, value in self.parameters['series_val_1'].items():
                csv = ','.join(value)
                filter_str = f'{filter_str} -{key} {csv}'
            for key, value in self.parameters['fixed_vars_vals_input'].items():
                csv = ','.join(value)
                filter_str = f'{filter_str} -{key} {csv}'
            return filter_str

    def _get_tcst_dir(self):
        return self.get_config_value('tcst_dir')

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
        markers_size = self.get_config_value('series_symbols_size')
        return self.create_list_by_series_ordering(markers_size)

    def _get_plot(self) -> list:
        plot_type_list = self.get_config_value('plot_type_list')
        for cur_plot_type in plot_type_list:
            if cur_plot_type not in self.SUPPORTED_PLOT_TYPES:
                raise ValueError("Requesting an unsupported plot type. Supported types: boxplot, "
                             "point, mean, median, relperf, rank, skill_mn, and skill_md ")
        return plot_type_list

    def _get_tcst_files(self) -> list:
        tcst_files = self.get_config_value('tcst_files')
        return tcst_files

    def _get_rp_diff(self) -> list:
        rp_diff = self.get_config_value('rp_diff')
        # TODO validate rp_diff
        if len(rp_diff) == 1:
            rp_diff = [rp_diff[0]] * len(self.indy_vals)
        return rp_diff

    def _get_hfip_bsln(self) -> str:
        """
           Expect hfip_bsln value to be 'no', 0, 5, or 10

        """

        hfip_bsln = str(self.get_config_value('hfip_bsln'))
        hfip_bsln = hfip_bsln.lower()

        # Validate that hfip_bsln is one of the following; (no, 0, 5, 10 year goal)
        supported_bsln = ['no', '0', '5', '10']
        if hfip_bsln not in supported_bsln:
            raise ValueError(f"Error: Valid hfip_bsln values are: {supported_bsln}. ")

        return hfip_bsln

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

    def _get_series_ci(self) -> list:
        """
        Retrieve the values that determine whether to display a particular series
        and convert them to bool if needed

        Args:

        Returns:
                A list of boolean values indicating whether or not to
                display the corresponding series
            """

        series_ci_config_vals = self.get_config_value('series_ci')
        series_ci_bools = []
        for val in series_ci_config_vals:
            if isinstance(val, bool):
                series_ci_bools.append(val)

            if isinstance(val, str):
                series_ci_bools.append(val.upper() == 'TRUE')

        return self.create_list_by_series_ordering(series_ci_bools)

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
            raise ValueError(
                "An unsupported statistic was set for the plot_stat setting.  Supported values are sum, mean, and median.")
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
        num_plot_disp = len(self.plot_disp)
        num_series_ord = len(self.series_ordering)
        num_colors = len(self.colors_list)
        num_legends = len(self.user_legends)
        status = False

        if self.num_series == num_plot_disp == \
                num_series_ord == num_colors \
                == num_legends:
            status = True
        return status

    def _get_user_legends(self, legend_label_type: str = '') -> list:
        """
        Retrieve the text that is to be displayed in the legend at the bottom of the plot.
        Each entry corresponds to a series.

        Args:
                @parm legend_label_type:  The legend label, such as 'Performance' that indicates
                                          the type of series box. Used when the user hasn't
                                          indicated a legend.

        Returns:
                a list consisting of the series label to be displayed in the plot legend.

        """

        all_user_legends = self.get_config_value('user_legend')
        legend_list = []

        # create legend list for y-axis series

        series = self.get_series_y(1)
        for idx, ser_components in enumerate(series):
            if idx >= len(all_user_legends) or all_user_legends[idx].strip() == '':
                # user did not provide the legend - create it
                legend_list.append(ser_components[0])
            else:
                # user provided a legend - use it
                legend_list.append(all_user_legends[idx])

        # add to legend list  legends for y2-axis series
        num_series_y1 = len(self.get_series_y(1))

        for idx, ser_components in enumerate(self.get_config_value('derived_series_1')):
            # index of the legend
            legend_idx = idx + num_series_y1
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

        all_fields_values['fcst_var'] = self.list_stat_1

        return utils.create_permutations_mv(all_fields_values, 0)

    def get_series_y_relperf(self, axis: int) -> list:
        """
        Creates an array of series components (excluding derived) tuples for the specified y-axis
        :param axis: y-axis (1 or 2)
        :return: an array of series components tuples
        """
        all_fields_values_orig = self.get_config_value('series_val_' + str(axis)).copy()
        all_fields_values = {}
        for x in reversed(list(all_fields_values_orig.keys())):
            all_fields_values[x] = all_fields_values_orig.get(x)

        all_fields_values['fcst_var'] = ['Better']

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
        else:
            fcst_vals = list()
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
            else:
                fcst_vals_2 = list()
            fcst_vals_2_flat = [item for sublist in fcst_vals_2 for item in sublist]
            series_vals_list_2.append(fcst_vals_2_flat)
            permutations_2 = list(itertools.product(*series_vals_list_2))
            permutations.extend(permutations_2)

        total = len(permutations)
        # add derived
        total = total + len(self.get_config_value('derived_series_1'))

        return total
