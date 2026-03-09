# ============================*
 # ** Copyright UCAR (c) 2020
 # ** University Corporation for Atmospheric Research (UCAR)
 # ** National Center for Atmospheric Research (NCAR)
 # ** Research Applications Lab (RAL)
 # ** P.O.Box 3000, Boulder, Colorado, 80307-3000, USA
 # ============================*
 
 
 
"""
Class Name: config.py

Holds values set in the config file(s)
"""
__author__ = 'Minna Win'

import itertools
from typing import Union
from datetime import datetime

import metcalcpy.util.utils as utils
import metplotpy.plots.util
from . import constants


class Config:
    """
       Handles reading in and organizing configuration settings in the yaml configuration file.
    """

    def __init__(self, parameters):

        self.parameters = parameters

        # Logging
        self.log_filename = self.get_config_value('log_filename')
        self.log_level = self.get_config_value('log_level')
        self.logger = metplotpy.plots.util.get_common_logger(self.log_level,
                                                             self.log_filename)

        #
        # Configuration settings that apply to the plot
        #
        self.output_image = self.get_config_value('plot_filename')
        self.title_font = constants.DEFAULT_TITLE_FONT
        self.title_color = constants.DEFAULT_TITLE_COLOR
        self.xaxis = self.get_config_value('xaxis')
        self.xaxis_reverse = False
        self.yaxis_1 = self.get_config_value('yaxis_1')
        self.yaxis_2 = self.get_config_value('yaxis_2')
        self.sync_yaxes = False
        self.title = self.get_config_value('title')
        self.use_ee = self._get_bool('event_equal')
        self.indy_vals = self.get_config_value('indy_vals')
        self.indy_label = self._get_indy_label()
        self.indy_var = self.get_config_value('indy_var')
        self.show_plot_in_browser = self.get_config_value('show_plot_in_browser')

        # Plot figure dimensions should be in inches
        self.plot_width = self.calculate_plot_dimension('plot_width')
        self.plot_height = self.calculate_plot_dimension('plot_height' )
        self.plot_caption = self.get_config_value('plot_caption')
        # plain text, bold, italic, bold italic are choices in METviewer UI
        self.caption_weight = constants.MV_TO_MPL_CAPTION_STYLE[self.get_config_value('caption_weight')]
        self.caption_color = self.get_config_value('caption_col')
        # relative magnification
        self.caption_size = self.get_config_value('caption_size')

        # up-down location relative to the x-axis line
        self.caption_offset = self.get_config_value('caption_offset')
        # left-right position
        self.caption_align = self.get_config_value('caption_align')

        # legend style settings as defined in METviewer
        user_settings = self._get_legend_style()

        # list of the x, y
        # bbox_to_anchor() setting used in determining
        # the location of the bounding box which defines
        # the legend.

        bbox_x = user_settings.get('bbox_x')
        if bbox_x is not None:
            self.bbox_x = float(user_settings['bbox_x'])

        bbox_y = user_settings.get('bbox_y')
        if bbox_y is not None:
            self.bbox_y = float(user_settings['bbox_y'])

        legend_magnification = user_settings.get('legend_size')
        if legend_magnification is not None:
            self.legend_size = int(constants.DEFAULT_LEGEND_FONTSIZE * legend_magnification)

        self.legend_ncol = self.get_config_value('legend_ncol')
        legend_box = self.get_config_value('legend_box')
        self.draw_box = False
        if legend_box is not None:
            legend_box = legend_box.lower()
            if legend_box == 'o':
                # Don't draw a box around legend labels
                self.draw_box = True


        # some settings used by some but not all plot types

        # Plotly plots often require offsets to the margins
        self.plot_margins = self.get_config_value('mar')
        self.grid_on = self._get_bool('grid_on')
        if self.get_config_value('mar_offset'):
            self.plot_margins = {
                'l': 0,
                'r': self.parameters['mar'][3] + 20,
                't': self.parameters['mar'][2] + 80,
                'b': self.parameters['mar'][0] + 80,
                'pad': 5,
            }

        self.grid_col = self.get_config_value('grid_col')
        if self.grid_col:
            self.blended_grid_col = metplotpy.plots.util.alpha_blending(self.grid_col, 0.5)
        self.show_nstats = self._get_bool('show_nstats')
        self.indy_stagger = self._get_bool('indy_stagger')

        # Some of the plot types use Matplotlib, these settings are only relevant
        # for plots implemented with Matplotlib.

        # left-right location of x-axis label/title relative to the y-axis line
        # make adjustments between METviewer default and Matplotlib's center
        # METviewer default value of 2 corresponds to Matplotlib value of .5
        #
        mv_x_title_offset = self.get_config_value('xlab_offset')
        if mv_x_title_offset:
          self.x_title_offset = float(mv_x_title_offset) - 1.5


        # up-down of x-axis label/title position
        # make adjustments between METviewer default and Matplotlib's center
        # METviewer default is .5, Matplotlib center is 0.05, so subtract 0.55 from the
        # METviewer setting to get the correct Matplotlib y-value (up/down)
        # for the x-title position
        mv_x_title_align = self.get_config_value('xlab_align')
        if mv_x_title_align:
           self.x_title_align = float(mv_x_title_align) - .55

        # Need to use a combination of Matplotlib's font weight and font style to

        # re-create the METviewer xlab_weight. Use the
        # MV_TO_MPL_CAPTION_STYLE dictionary to map these caption styles to
        # what was requested in METviewer
        self.xlab_weight = constants.MV_TO_MPL_CAPTION_STYLE[self.get_config_value('xlab_weight')]
        self.x2lab_weight = self.get_config_value('x2lab_weight')
        if self.x2lab_weight:
            self.x2lab_weight = constants.MV_TO_MPL_CAPTION_STYLE[self.x2lab_weight]

        self.x_tickangle = self.parameters['xtlab_orient']
        if self.x_tickangle in constants.XAXIS_ORIENTATION.keys():
            self.x_tickangle = constants.XAXIS_ORIENTATION[self.x_tickangle]
        self.x_tickfont_size = self.parameters['xtlab_size'] * constants.MPL_FONT_SIZE_DEFAULT

        # y-axis labels and y-axis ticks
        self.y_title_font_size = self.parameters['ylab_size'] * constants.DEFAULT_CAPTION_FONTSIZE
        self.y_tickangle = self.parameters['ytlab_orient']
        if self.y_tickangle in constants.YAXIS_ORIENTATION.keys():
            self.y_tickangle = constants.YAXIS_ORIENTATION[self.y_tickangle]
        self.y_tickfont_size = self.parameters['ytlab_size'] * constants.MPL_FONT_SIZE_DEFAULT

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
        self.y2lab_weight = self.get_config_value('y2lab_weight')
        if self.y2lab_weight:
            self.y2lab_weight = constants.MV_TO_MPL_CAPTION_STYLE[self.y2lab_weight]

        # Adjust the caption left/right relative to the y-axis
        # METviewer default is set to 0, corresponds to y=0.05 in Matplotlib
        mv_caption_align = self.get_config_value('caption_align')
        self.caption_align = float(mv_caption_align) + 0.13

        # The plot's title size, title weight, and positioning in left-right and up-down directions
        mv_title_size = self.get_config_value('title_size')
        self.title_size = mv_title_size * constants.MPL_FONT_SIZE_DEFAULT

        mv_title_weight = self.get_config_value('title_weight')
        # use the same constants dictionary as used for captions
        self.title_weight = constants.MV_TO_MPL_CAPTION_STYLE[mv_title_weight]

        # These values can't be used as-is, the only choice for aligning in Matplotlib
        # are center (default), left, and right
        mv_title_align = self.get_config_value('title_align')
        self.title_align = float(mv_title_align)

        # does nothing because the vertical position in Matplotlib is
        # automatically chosen to avoid labels and ticks on the topmost
        # x-axis
        mv_title_offset = self.get_config_value('title_offset')
        self.title_offset = float(mv_title_offset)

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
        self.bbox_y = mv_bbox_y + .15
        legend_magnification = user_settings['legend_size']
        self.legend_size = int(constants.DEFAULT_LEGEND_FONTSIZE * legend_magnification)
        self.legend_ncol = self.get_config_value('legend_ncol')

        # Don't draw a box around legend labels unless an 'o' is set
        legend_box = self.get_config_value('legend_box').lower()
        self.draw_box = legend_box == 'o'

        # These are the inner keys to the series_val setting, and
        # they represent the series variables of
        # interest.  The keys correspond to the column names
        # in the input dataframe.
        self.series_vals_1 = self._get_series_vals(1)
        self.series_vals_2 = self._get_series_vals(2)
        self.all_series_vals = self.series_vals_1.copy()
        if self.series_vals_2:
            self.all_series_vals.extend(self.series_vals_2)

        # Represent the names of the forecast variables (inner keys) to the fcst_var_val setting.
        # These are the names of the columns in the input dataframe.
        self.fcst_var_val_1 = self._get_fcst_vars(1)
        self.fcst_var_val_2 = self._get_fcst_vars(2)

        # Get the list of the statistics of interest
        self.list_stat_1 = self.get_config_value('list_stat_1')
        self.list_stat_2 = self.get_config_value('list_stat_2')

        # These are the inner values to the series_val setting (these correspond to the
        # keys returned in self.series_vals above).  These are the specific variable values to
        # be used in subsetting the input dataframe (e.g. for key='model', and value='SH_CMORPH',
        # we want to subset data where column name is 'model', with coincident rows of 'SH_CMORPH'.
        self.series_val_names = self._get_series_val_names()
        self.series_ordering = None
        self.indy_plot_val = self.get_config_value('indy_plot_val')
        self.lines = self._get_lines()


    def get_config_value(self, *args:Union[str,int,float]):
        """Gets the value of a configuration parameter.
        Looks for parameter in the user parameter dictionary

        Args:
            @ param args - chain of keys that defines a key to the parameter

        Returns:
            - a value for the parameter of None
        """

        return self._get_nested(self.parameters, args)

    def _get_nested(self, data:dict, args:tuple):
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

    def _get_legend_style(self) -> dict:
        """
            Retrieve the legend style settings that are set
            in the METviewer tool

            Args:

            Returns:
                - a dictionary that holds the legend settings that
                  are set in METviewer
        """
        legend_box = self.get_config_value('legend_box')
        if legend_box:
            legend_box = legend_box.lower()

        legend_ncol = self.get_config_value('legend_ncol')
        legend_inset = self.get_config_value('legend_inset')
        if legend_inset:
            legend_bbox_x = legend_inset['x']
            legend_bbox_y = legend_inset['y']
            legend_size = self.get_config_value('legend_size')
            legend_settings = {
                'bbox_x': legend_bbox_x,
                'bbox_y': legend_bbox_y,
                'legend_size': legend_size,
                'legend_ncol': legend_ncol,
                'legend_box': legend_box,
            }
        else:
            legend_settings = {}

        return legend_settings

    def _get_series_vals(self, index:int) -> list:
        """
            Get a tuple of lists of all the variable values that correspond to the inner
            key of the series_val dictionaries (series_val_1 and series_val_2).
            These values will be used with lists of other config values to
            create filtering criteria.  This is useful to subset the input data
            to assist in identifying the data points for this series.

            Args:
                index:  The number defining which of series_vals_1 or series_vals_2 to consider

            Returns:
                lists of *all* the values of the inner dictionary
                of the series_vals dictionaries

        """

        if index == 1:
            # evaluate series_val_1 setting
            series_val_dict = self.get_config_value('series_val_1')
        elif index == 2:
            # evaluate series_val_2 setting
            series_val_dict = self.get_config_value('series_val_2')
        else:
            raise ValueError('Index value must be either 1 or 2.')

        # check for empty setting. If so, return an empty list
        if series_val_dict:
            val_dict_list = [*series_val_dict.values()]
        else:
            val_dict_list = []

        # Unpack and access the values corresponding to the inner keys
        # (series_var1, series_var2, ..., series_varn).
        return val_dict_list

    def _get_series_columns(self, index):
        ''' Retrieve the column name that corresponds to this '''

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
        if index == 1:
            fcst_var_val_dict = self.get_config_value('fcst_var_val_1')
            if fcst_var_val_dict:
                all_fcst_vars = [*fcst_var_val_dict.keys()]
            else:
                all_fcst_vars = []
        elif index == 2:
            fcst_var_val_dict = self.get_config_value('fcst_var_val_2')
            if fcst_var_val_dict:
                all_fcst_vars = [*fcst_var_val_dict.keys()]
            else:
                all_fcst_vars = []
        else:
            all_fcst_vars = []

        return all_fcst_vars

    def get_fcst_vars_dict(self, index: int) -> dict:
        """Retrieve a dictionary of the fcst_var_val_{index} variable from the config.

           Args:
              index: identifier used to differentiate between fcst_var_val_1 and
                     fcst_var_val_2 config settings
           Returns:
               a list containing all the fcst variables requested in the
               fcst_var_val setting in the config file.  This will be
               used to subset the input data that corresponds to a particular series.

        """
        if index not in (1, 2):
            return {}

        fcst_dict = self.get_config_value(f'fcst_var_val_{index}')
        if fcst_dict is None:
            return {}
        return fcst_dict

    def get_fcst_vars_keys(self, index: int) -> list:
        """Retrieve a list of keys from the fcst_var_val_{index} variable from the config.

           Args:
              index: identifier used to differentiate between fcst_var_val_1 and
                     fcst_var_val_2 config settings
           Returns:
               a list containing all the fcst variables requested in the
               fcst_var_val setting in the config file.  This will be
               used to subset the input data that corresponds to a particular series.

        """
        fcst_vars_dict = self.get_fcst_vars_dict(index)
        if fcst_vars_dict is None:
            return []
        return list(fcst_vars_dict.keys())

    def _get_series_val_names(self) -> list:
        """
            Get a list of all the variable value names (i.e. inner key of the
            series_val dictionary). These values will be used with lists of
            other config values to create filtering criteria.  This is useful
            to subset the input data to assist in identifying the data points
            for this series.

            Args:

            Returns:
                a "list of lists" of *all* the keys to the inner dictionary of
                the series_val dictionary

        """

        series_val_dict = self.get_config_value('series_val_1')

        # Unpack and access the values corresponding to the inner keys
        # (series_var1, series_var2, ..., series_varn).
        if series_val_dict:
            return [*series_val_dict.keys()]
        return []

    def calculate_number_of_series(self) -> int:
        """
           From the number of items in the permutation list,
           determine how many series "objects" are to be plotted.

           Args:

           Returns:
               the number of series

        """

        # Retrieve the lists from the series_val_1 dictionary
        series_vals_list = self.series_vals_1

        # Utilize itertools' product() to create the cartesian product of all elements
        # in the lists to produce all permutations of the series_val values and the
        # fcst_var_val values.
        permutations = list(itertools.product(*series_vals_list))

        return len(permutations)

    def _get_colors(self) -> list:
        """
           Retrieves the colors used for lines and markers, from the
           config file (default or custom).
           Args:

           Returns:
               colors_list or colors_from_config: a list of the colors to be used for the lines
               (and their corresponding marker symbols)
        """

        colors_settings = self.get_config_value('colors')
        return self.create_list_by_series_ordering(list(colors_settings))

    def _get_con_series(self) -> list:
        """
           Retrieves the 'connect across NA' values used for lines and markers, from the
           config file (default or custom).
           Args:

           Returns:
               con_series_list or con_series_from_config: a list of 1 and/or 0 to
               be used for the lines
        """
        con_series_settings = self.get_config_value('con_series')
        return self.create_list_by_series_ordering(list(con_series_settings))

    def _get_show_legend(self) -> list:
        """
           Retrieves the 'show_legend' values used for displaying or
           not the legend of a trace in the legend box, from the
           config file. If 'show_legend' is not provided - throws an error
           Args:

           Returns:
               show_legend_list or show_legend_from_config: a list of 1 and/or 0 to
               be used for the traces
        """
        show_legend_settings = self.get_config_value('show_legend')

        if show_legend_settings is None:
            raise ValueError("ERROR: show_legend parameter is not provided.")

        # Support all variations of setting the show_legend: '1', 1, "true" (any combination of cases), True (boolean)
        updated_show_legend_settings = []
        for legend_setting in show_legend_settings:
            legend_setting = str(legend_setting).lower()
            if legend_setting == '1' or legend_setting == 'true' or legend_setting == 1 or legend_setting is True:
                updated_show_legend_settings.append(int(1))
            else:
                updated_show_legend_settings.append(int(0))

        return self.create_list_by_series_ordering(list(updated_show_legend_settings))

    def _get_markers(self):
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

    def _get_linewidths(self) -> Union[list, None]:
        """ Retrieve all the linewidths from the configuration file, if not
            specified in any config file, use the default values of 2

            Args:

            Returns:
                linewidth_list: a list of linewidths corresponding to each line (model)
        """
        linewidths = self.get_config_value('series_line_width')
        if linewidths is not None:
            return self.create_list_by_series_ordering(list(linewidths))
        else:
            return None

    def _get_linestyles(self) -> list:
        """
            Retrieve all the linestyles from the config file.

            Args:

            Returns:
                list of line styles, each line style corresponds to a particular series
        """
        linestyles = self.get_config_value('series_line_style')
        linestyle_list_ordered = self.create_list_by_series_ordering(list(linestyles))
        return linestyle_list_ordered


    def _get_user_legends(self, legend_label_type: str ) -> list:
        """
           Retrieve the text that is to be displayed in the legend at the bottom of the plot.
           Each entry corresponds to a series.

         For legend labels that aren't set (ie in conf file they are set to '')
         create a legend label based on the permutation of the series names
         appended by 'user_legend label'.  For example, for:
             series_val_1:
                model:
                  - NoahMPv3.5.1_d01
                vx_mask:
                  - CONUS
         The constructed legend label will be "NoahMPv3.5.1_d01 CONUS Performance"

           Args:
               @parm legend_label_type:  The legend label, such as 'Performance',
                                         used when the user hasn't indicated a legend in the
                                         configuration file.

           Returns:
               a list consisting of the series label to be displayed in the plot legend.

        """
        legends_list, legend_label_unspecified = self._get_legends_list()

        ll_list = []
        series_list = self.all_series_vals

        # Some diagrams don't require a series_val1 value, hence
        # resulting in a zero-sized series_list.  In this case,
        # the legend label will just be the legend_label_type.
        if len(series_list) == 0 and legend_label_unspecified:
            # check if summary_curve is present
            if 'summary_curve' in self.parameters.keys() and self.parameters['summary_curve'] != 'none':
                return [legend_label_type, self.parameters['summary_curve'] + ' ' + legend_label_type]
            return [legend_label_type]

        perms = utils.create_permutations(series_list)
        for idx,ll in enumerate(legends_list):
            if ll == ' ':
                if len(series_list) > 1:
                    label_parts = [perms[idx][0], ' ', perms[idx][1], ' ', legend_label_type]
                else:
                    label_parts = [perms[idx][0], ' ', legend_label_type]
                legend_label = ''.join(label_parts)
                ll_list.append(legend_label)
            else:
                ll_list.append(ll)
        if 'summary_curve' in self.parameters.keys() and self.parameters['summary_curve'] != 'none':
            ll_list.append(self.parameters['summary_curve'] + ' ' + legend_label_type)

        legends_list_ordered = self.create_list_by_series_ordering(ll_list)
        return legends_list_ordered

    def _get_legends_list(self):
        all_legends = self.get_config_value('user_legend')

        # Check for empty list as setting in the config file
        legends_list = []

        # set a flag indicating when a legend label is specified
        legend_label_unspecified = True

        # Check if a stat curve was requested, if so, then the number
        # of series_val_1 values will be inconsistent with the number of
        # legend labels 'specified' (either with actual labels or whitespace)

        num_series = self.calculate_number_of_series()
        if len(all_legends) == 0:
            for _ in range(num_series):
                legends_list.append(' ')
        else:
            for legend in all_legends:
                if len(legend) == 0:
                    legend = ' '
                    legends_list.append(legend)
                else:
                    legend_label_unspecified = False
                    legends_list.append(legend)

        return legends_list, legend_label_unspecified


    def _get_plot_resolution(self) -> int:
        """
            Retrieve the plot_res and plot_unit to determine the dpi
            setting in matplotlib.

            Args:

            Returns:
                plot resolution in units of dpi (dots per inch)

        """
        # Initialize to the default resolution
        # set by matplotlib
        dpi = 100

        # first check if plot_res is set in config file
        if self.get_config_value('plot_res'):
            resolution = self.get_config_value('plot_res')

            # check if the units value has been set in the config file
            if self.get_config_value('plot_units'):
                return self._convert_units_to_inches(resolution, self.get_config_value('plot_units'))

            # units not indicated, assume
            # we are dealing with inches
            return resolution

        # no plot_res value is set, return the default
        # dpi used by matplotlib
        return dpi

    def _convert_units_to_inches(self, value, units):
        units_lower = units.lower()
        if units_lower == 'mm':
            return value * constants.MM_TO_INCHES
        if units_lower == 'cm':
            return value * constants.CM_TO_INCHES

        # if unsupported units are specified, log a warning but assume inches
        if units_lower != 'in':
            self.logger.warning(f"Invalid units specified: {units}. Expected in, mm, or cm. Assuming inches.")

        return value

    def create_list_by_series_ordering(self, setting_to_order) -> list:
        """
            Generate a list of series plotting settings based on what is set
            in series_order in the config file.
            If the series_order is specified:
               series_order:
                -3
                -1
                -2

                and color is set:
               color:
                -red
                -blue
                -green


            Then the following is expected:
              the first series' color is 'blue'
              the second series' color is 'green'
              the third series' color is 'red'

            This allows the user the flexibility to change marker symbols, colors, and
            other line qualities between the series (lines) without having to re-order
            *all* the values.

            Args:

                setting_to_order:  the name of the setting (eg axis_line_width) to be
                                   ordered based on the order indicated
                                   in the config file under the series_order setting.

            Returns:
                a list reflecting the order that is consistent with what was set in series_order

        """

        # create a natural order if series_ordering is missing
        if self.series_ordering is None:
            self.series_ordering = list(range(1, len(setting_to_order) + 1))

        # Make the series ordering list zero-based to sync with Python's zero-based counting
        series_ordered_zb = [sorder - 1 for sorder in self.series_ordering]

        if len(setting_to_order) == len(series_ordered_zb):
            # Reorder the settings according to the zero based series order.
            settings_reordered = [setting_to_order[i] for i in series_ordered_zb]
            return settings_reordered

        return setting_to_order


    def create_list_by_plot_val_ordering(self, setting_to_order: str) -> list:
        """
        Generate a list of indy parameters settings based on what is set
        in indy_plot_val in the config file.
        If the  is specified:
        -3
        -1
        -2

        and indy_vals is set:
        indy_vals:
        -120000
        -150000
        -180000

        Then the following is expected:
        the first indy_val  is 1850000
        the second indy_val is 120000
        the third indy_val is 150000


        Args:

            setting_to_order:  the name of the setting (eg indy_vals) to be
                                        ordered based on the order indicated
                                        in the config file under the indy_plot_val setting.

        Returns:
            a list reflecting the order that is consistent with what was set in indy_plot_val
        """

        # order the input list according to the series_order setting
        ordered_settings_list = []
        # create a natural order if series_ordering is missing
        if self.indy_plot_val is None or len(self.indy_plot_val) == 0:
            self.indy_plot_val = list(range(1, len(setting_to_order) + 1))

        # Make the series ordering list zero-based to sync with Python's zero-based counting
        indy_ordered_zb = [sorder - 1 for sorder in self.indy_plot_val]
        for idx, indy in enumerate(indy_ordered_zb):
            ordered_settings_list.insert(indy, setting_to_order[idx])

        return ordered_settings_list


    def calculate_plot_dimension(self, config_value: str) -> int:
        '''
           To calculate the width or height that defines the size of the plot.
           Matplotlib defines these values in inches.  METviewer accepts units of inches or mm for width and
           height, so conversion from mm to inches or mm to pixels is necessary, depending
           on the requested output units, output_units.

           Args:
              @param config_value:  The plot dimension to convert, either a width or height,
                    in inches or mm
              @param output_units: pixels or in (inches) to indicate which
                                   units to use to define plot size.    Matplotlib uses inches.
           Returns:
             converted_value : converted value from in/mm to pixels or mm to inches based
                                    on input values
        '''
   
        value2convert = self.get_config_value(config_value)
        units = self.get_config_value('plot_units')

        # Matplotlib uses inches (in) for setting plot size (width and height)
        return self._convert_units_to_inches(value2convert, units)


    def _get_bool(self, param: str) -> Union[bool, None]:
        """
        Validates the value of the parameter and returns a boolean
        Args:
            :param param: name of the parameter
        Returns:
            :return: boolean value or None
        """

        param_val = self.get_config_value(param)
        if isinstance(param_val, bool):
            return param_val

        if isinstance(param_val, str):
            return param_val.upper() == 'TRUE'

        return None

    def _get_indy_label(self):
        if 'indy_label' in self.parameters.keys():
            return self.get_config_value('indy_label')
        return self.indy_vals

    def _get_lines(self) -> Union[list, None]:
        """
         Initialises the custom lines properties and returns a validated list
         Args:

         Returns:
             :return: list of lines properties or None
         """

        # get property value from the parameters
        lines = self.get_config_value('lines')
        if lines is None:
            return None

        # if the property exists - proceed
        # validate data and replace the values
        for line in lines:

            # validate line_type
            if line['type'] not in ('horiz_line', 'vert_line') :
                print(f'WARNING: custom line type {line["type"]} is not supported')
                line['type'] = None
                continue

            # convert position to float if line_type=horiz_line
            if line['type'] == 'horiz_line':
                try:
                    line['position'] = float(line['position'])
                except ValueError:
                    print(f'WARNING: custom line position {line["position"]} is invalid')
                    line['type'] = None
            else:
                # convert position to string if line_type=vert_line
                line['position'] = str(line['position'])

            # convert line_width to float
            try:
                line['line_width'] = float(line['line_width'])
            except ValueError:
                print(f'WARNING: custom line width {line["line_width"]} is invalid')
                line['type'] = None

            # convert line style to matplotlib format if necessary
            if line['line_style'] in constants.LINESTYLE_BY_NAMES:
                line['line_style'] = constants.LINESTYLE_BY_NAMES[line['line_style']]

        return lines

    def config_consistency_check(self) -> None:
        """Checks that the number of settings defined for
            plot_disp, series_ordering, colors_list, user_legends, and show_legend
           are consistent with number of series.

           @raises ValueError if any of settings are inconsistent with the
            number of series (as defined by the cross product of the model
            and vx_mask defined in the series_val_1 setting)
        """
        lists_to_check = {
            "plot_disp": self.plot_disp,
            "series_ordering": self.series_ordering,
            "colors_list": self.colors_list,
            "user_legends": self.user_legends,
            "show_legend": self.show_legend,
        }
        self._config_compare_lists_to_num_series(lists_to_check)

    def _config_compare_lists_to_num_series(self, lists_to_check: dict) -> list:
        """
            Checks that the number of settings defined for lists are consistent
            with the number of series to plot.

            Args:
                @param lists_to_check: dictionary with name of list as key and
                actual list to check as value.

            @raises ValueError if any settings are inconsistent with the number of series
        """
        self.logger.info(f"Checking consistency of config settings relative to number of series {datetime.now()}")

        # Determine the number of series based on the number of
        # permutations from the series_var setting in the config file
        error_messages = []
        for name, list_to_check in lists_to_check.items():

            if len(list_to_check) == self.num_series:
                continue

            error_messages.append(f"{name} ({len(list_to_check)}) does not match number of series ({self.num_series})")

        if error_messages:
            msg = (
                "The number of series defined by series_val_1/2 and derived curves is "
                "inconsistent with the number of settings required for describing each series."
            )
            msg += "\n" + "\n".join(error_messages)
            self.logger.error(msg)
            raise ValueError(msg)

        self.logger.info(f"Config consistency check completed successfully: {datetime.now()}")
