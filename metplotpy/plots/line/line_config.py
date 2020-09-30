"""
Class Name: line_config.py

Holds values set in the Line plot config file(s)
"""
__author__ = 'Minna Win, Hank Fisher'
__email__ = 'met_help@ucar.edu'

import re
import itertools

from plots.config import Config
import plots.constants as constants

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

        # use this setting to determine the ordering of colors, lines, and markers
        self.series_ordering = self._get_series_order()

        self.plot_disp = self._get_plot_disp()

        # Make the series ordering zero-based to be consistent with Python's zero-based
        # counting/numbering
        self.series_ordering_zb = [sorder - 1 for sorder in self.series_ordering]

        self.stat_input = self.get_config_value('stat_input')

        self.series_inner_dict1 = self._get_series_inner_dict(1)
        self.series_inner_dict2 = self._get_series_inner_dict(2)

        # Supported values for stat_curve are none, mean, and median
        self.plot_stat = self.get_config_value('stat_curve')
        self.plot_width = self.calculate_plot_dimension('plot_width', 'pixels')
        self.plot_height = self.calculate_plot_dimension('plot_height', 'pixels')
        self.plot_margins = dict(l=self.parameters['mar'][1]+80,
                                 r=self.parameters['mar'][3]+80,
                                 t=self.parameters['mar'][2]+100 + 10,
                                 b=self.parameters['mar'][0]+80,
                                 pad= 5
                                 )
        self.plot_resolution = self._get_plot_resolution()
        self.caption = self.get_config_value('plot_caption')
        self.caption_weight = self.get_config_value('caption_weight')
        self.caption_color = self.get_config_value('caption_color')
        self.caption_size = self.get_config_value('caption_size')
        self.caption_offset = self.get_config_value('caption_offset')
        self.caption_align = self.get_config_value('caption_align')
        self.colors_list = self._get_colors()
        self.marker_list = self._get_markers()
        self.marker_size = self._get_markers_size()
        self.mode = self._get_mode()
        self.linewidth_list = self._get_linewidths()
        self.linestyles_list = self._get_linestyles()
        self.plot_ci = self._get_plot_ci()

        # legend style settings as defined in METviewer
        user_settings = self._get_legend_style()

        # list of the x, y, and loc values for the
        # bbox_to_anchor() setting used in determining
        # the location of the bounding box which defines
        # the legend.
        self.bbox_x = 0.5 + float(user_settings['bbox_x'])
        # set legend box lower by .18 pixels of the default value
        # set in METviewer to prevent obstructing the x-axis.
        self.bbox_y = -0.12 + float(user_settings['bbox_y']) + 0.25
        legend_magnification = user_settings['legend_size']
        caption_magnification = self.get_config_value('caption_size')
        self.legend_size = int(constants.DEFAULT_LEGEND_FONTSIZE * legend_magnification)
        self.caption_size = int(constants.DEFAULT_CAPTION_FONTSIZE * caption_magnification)
        self.legend_ncol = self.get_config_value('legend_ncol')
        legend_box = self.get_config_value('legend_box').lower()
        if legend_box == 'n':
            # Don't draw a box around legend labels
            self.draw_box = False
        else:
            # Other choice is 'o'
            # Enclose legend labels in a box
            self.draw_box = True
        self.plot_stat = self._get_plot_stat()
        self.show_nstats = self.get_config_value('show_nstats')
        if self.show_nstats == 'True':
            self.show_nstats = True
        elif self.show_nstats == 'False':
            self.show_nstats = False

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

    def _get_series_inner_dict(self, index):

        """
            Get a dictionary containing the inner key-value pairs. This information
            will be used to subset the PCT or CTC data (represented by a
            pandas dataframe) for the ROC diagram.

            The value of this inner dictionary corresponds to the column name of the
            dataframe, and is saved as the key in this new dictionary.  The key of the
            inner dictionary corresponds to the row of interest, and is saved as the
            value in the new dictionary.

            For example:
            series_val_1:
               model:
                  - GFS
                  - WRF
               vx_mask:
                  - FULL

            The inner dictionary (from the above configuration file entry)
            looks like this: {'model': ['GFS', 'WRF'], 'vx_mask':'FULL'}
            and we want to subset the data where (model == GFS and vx_mask == FULL) for one
            permutation/series and (model == WRF and vx_mask == FULL)
            for the second permutation/series
            (i.e. key = row value of interest and value = corresponding column header).

            Our new dictionary looks like this:

            {'GFS':'model', 'WRF':'model','FULL':'vx_mask'}

            now we can readily determine which row value of interest corresponds to a column header.


            We also need to support this (and other) scenario(s):
            series_val_1:
                model:
                   - GFS
                   - GALWEM

            where the inner dictionary looks like: {'model': ['GFS', 'GALWEM']} and our
            new dictionary looks like:
            {'GFS':'model', 'GALWEM':'model'}


            Args:
                index:  The number defining which of series_vals_1 or series_vals_2 to consider

            Returns:
                val_inner_dict: the inner dictionary
                                of the series_vals dictionary re-organized,
                                where the key is the row value of interest
                                and the value corresponds to the column header

        """
        val_inner_dict = {}

        if index == 1:
            # evaluate series_val_1 setting
            series_val_dict = self.get_config_value('series_val_1')
        elif index == 2:
            # evaluate series_val_2 setting
            series_val_dict = self.get_config_value('series_val_2')
        else:
            raise ValueError('Index value must be either 1 or 2')

        # return empty dictionary if series_val_dict is empty
        if not series_val_dict:
            return {}

        for field, values in series_val_dict.items():
            # Sometimes the value consists of a list of more
            # than one item:
            for idx, val in enumerate(values):
                val_inner_dict[values[idx]] = field

        return val_inner_dict

    def _get_series_order(self):
        """
            Get the order number for each series

            Args:

            Returns:
            a list of unique values representing the ordinal value of the corresponding series

        """
        return self.get_config_value('series_order')

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
                fcst_var_val_dict = []
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
        num_series = self.calculate_number_of_series()

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

        if num_series == num_plot_disp == \
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

    def _get_user_legends(self, legend_label_type):

        all_legends = self.get_config_value('user_legend')
        legend_list = []
        for idx, ser_components in enumerate(self._get_all_series()):
            if idx >= len(all_legends) or all_legends[idx].strip() == '':
                if len(ser_components) == 3 and ser_components[2] in OPERATION_TO_SIGN.keys():
                    # this is a derived series
                    legend_list.append(utils.get_derived_curve_name(ser_components))
                else:
                    legend_list.append(' '.join(map(str, ser_components)))
            else:
                legend_list.append(all_legends[idx])

        legends_list_ordered = self.create_list_by_series_ordering(legend_list)
        return legends_list_ordered

    def _get_all_series(self):
        all_series = self.all_series_y1.copy()
        if self.all_series_y2:
            all_series.extend(self.all_series_y2)

        return all_series

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

    def get_show_signif(self):
        """ Retrieve all the show_signif from the configuration file, if not
            specified in any config file, use the default values of False

            Args:

            Returns:
                show_signif_list: a list of show_signif corresponding to each line
        """
        show_signif = self.get_config_value('show_signif')
        show_signif_list = []
        for val in show_signif:
            if isinstance(val, str):
                show_signif_list.append(val == 'True')
        show_signif_list_ordered = self.create_list_by_series_ordering(show_signif_list)
        return show_signif_list_ordered
