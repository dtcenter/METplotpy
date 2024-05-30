# ============================*
# ** Copyright UCAR (c) 2024
# ** University Corporation for Atmospheric Research (UCAR)
# ** National Science Foundation National Center for Atmospheric Research (NSF NCAR)
# ** Research Applications Lab (RAL)
# ** P.O.Box 3000, Boulder, Colorado, 80307-3000, USA
# ============================*

"""
Class Name: ScatterConfig
 """
__author__ = 'Minna Win'

import itertools

from ..config import Config
from .. import constants
from .. import util

import metcalcpy.util.utils as utils
class ScatterConfig(Config):
    """
       Configuration object for the scatter plot.
    """

    def __init__(self, parameters):
        """
           Reads in the scatter plot settings from a YAML configuration file.
           This YAML configuration file is used in conjunction with a default
           configuration file: scatter_defaults.yaml

           Args:
               @param parameters: a dictionary containing the user-defined parameters for generating a scatter plot.

           Returns:


        """

        super().__init__(parameters)

        # Write (if dump_points_1 is True) output points file provided by the METplotpy YAML config file
        self.dump_points = self._get_bool('dump_points')
        if self.dump_points:
            self.points_path = self.get_config_value('points_path')

        # Corresponds to the "Fixed Values" in METviewer UI
        self.fixed_vars_vals = self._get_fixed_vars_vals()

        # The two columns to plot
        self.var_val_x_axis = self.get_config_value('var_val_x_axis')
        self.var_val_y_axis = self.get_config_value('var_val_y_axis')

        # Fcst variable of interest
        self.fcst_var = self.get_config_value('fcst_var')

        # Plot trend line, or not
        self.show_trend = self.get_config_value('show_trend_line')

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
        self.show_nstats = self._get_bool('show_nstats')
        self.indy_stagger = self._get_bool('indy_stagger')
        self.variance_inflation_factor = self._get_bool('variance_inflation_factor')
        self.dump_points_1 = self._get_bool('dump_points_1')
        self.dump_points_2 = self._get_bool('dump_points_2')
        self.xaxis_reverse = self._get_bool('xaxis_reverse')
        self.sync_yaxes = self._get_bool('sync_yaxes')
        self.create_html = self._get_bool('create_html')
        self.start_from_zero = self._get_bool('start_from_zero')

        ##############################################
        # caption parameters
        self.caption = self.get_config_value('plot_caption')
        mv_caption_weight = self.get_config_value('caption_weight')
        self.caption_color = self.get_config_value('caption_col')

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
        self.yaxis = self.get_config_value('yaxis')

        ##############################################
        # x-axis parameters
        self.x_title_font_size = self.parameters['xlab_size'] + constants.DEFAULT_TITLE_FONTSIZE
        self.x_tickangle = self.parameters['xtlab_orient']
        if self.x_tickangle in constants.XAXIS_ORIENTATION.keys():
            self.x_tickangle = constants.XAXIS_ORIENTATION[self.x_tickangle]
        self.x_tickfont_size = self.parameters['xtlab_size'] + constants.DEFAULT_TITLE_FONTSIZE
        self.xaxis = util.apply_weight_style(self.xaxis, self.parameters['xlab_weight'])


        ##############################################
        self.marker_symbol = self._get_marker()
        self.marker_color = self.get_config_value('marker_colormap')
        self.marker_size = self.get_config_value('marker_size')
        self.linewidth_list = self._get_linewidths()
        self.show_legend = self.get_config_value('show_legend')

        ##############################################
        # legend parameters
        self.show_user_legend = self.get_config_value('show_legend')
        self.user_legend =  self._get_user_legend()

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

        self.stat_input = self.get_config_value('stat_input')

        ##############################################
        # marker parameters

        # Color of the marker is based on the value
        self.variable_val_by_color = self.get_config_value('variable_val_by_color')
        self.colormap = self.get_config_value('colormap')

        ##############################################
        # Matplotlib specific "workarounds"

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

        # Need to use a combination of Matplotlib's font weight and font style to
        # re-create the METviewer caption weight. Use the
        # MV_TO_MPL_CAPTION_STYLE dictionary to map these caption styles to
        # what was requested in METviewer
        self.caption_weight = constants.MV_TO_MPL_CAPTION_STYLE[mv_caption_weight]

        # (0,0) in METviewer corresponds to (x=0.05,y=0.13) in Matplotlib
        # Adjust the caption up/down from x-axis.
        # METviewer default is set to 3, which corresponds to a y-value in Matplotlib
        # to .13
        mv_caption_offset = self.get_config_value('caption_offset')
        self.caption_offset = float(mv_caption_offset) - 2.87

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




        def _get_user_legend(self, legend_label_type: str = '') -> list:
            """
            Retrieve the text that is to be displayed in the legend at the bottom of the
            plot.


            Args:
                    @parm legend_label_type:  The legend label, such as 'Performance'
                    that indicates
                                              the type of series line. Used when the user
                                              hasn't
                                              indicated a legend.

            Returns:
                    a list consisting of the series label to be displayed in the plot
                    legend.

            """

            user_legend = list(self.get_config_value('user_legend'))

            if len(user_legend) == 0:
                # Use the variable by value as the colorbar legend
                self.get_config_value('variable_val_by_color')

            return user_legend


    def _get_fixed_vars_vals(self) -> dict:
        """
           Retrieve a list of the inner keys (name of the variables to hold 'fixed') to
           the fixed_vars_vals dictionary. These values correspond to the Fixed
           Values set in the METviewer user interface. In the YAML configuration file,
           the value(s) are set under the fixed_vars_vals_input setting:

           fixed_vars_vals_input:
              - fcst_lev:
                - 'Z0'
              - vx_mask:
                - 'CONUS'
                - 'WEST'
              - fcst_thresh:
                 - '>0.0'
                 - '>=5.1'

           Also supports the 'legacy' format (used by METviewer when R script was
           employed):

           fixed_vars_vals_input:
              - fcst_lev:
                 - fcst_lev_0:
                   - 'Z0'
              - vx_mask:
                 - vx_mask_1:
                   - 'CONUS'
                   - 'EAST'

            Generate a new dictionary where the value of the inner key is
            associated to the outer key.

            Mixing of the two formats is also supported.




           Args:

           Returns:
               updated_fixed_vars_vals_dict:
               a dictionary of the keys and values associated with the
               fixed_vars_vals_input setting in the configuration file (corresponds to
               the METviewer Fixed Variable setting(s) ).

        """

        fixed_vars_vals_dict = self.get_config_value('fixed_vars_vals_input')
        if len(fixed_vars_vals_dict) == 0:
            # If user hasn't specified anything in the fixed_var_vals_input setting,
            # return an empty dictionary.
            return {}
        else:
            # Use the outer dictionary key and the inner dictionary value
            # Retrieve all the inner keys, then their corresponding values and
            # associate those inner values with the outer key in a new dictionary.
            outer_keys = fixed_vars_vals_dict.keys()
            updated_fixed_vars_vals_dict = {}
            inner_exists = False
            for key in outer_keys:
                try:
                    inner_keys = fixed_vars_vals_dict[key].keys()
                except AttributeError:
                    # No inner dictionary, format looks like:
                    #
                    updated_fixed_vars_vals_dict[key] = fixed_vars_vals_dict[key]
                else:
                    # inner dictionary, assign the value corresponding to the
                    # inner dictionary to the key of the outer dictionary.
                    for inner_key in inner_keys:
                        updated_fixed_vars_vals_dict[key] = fixed_vars_vals_dict[
                            key][inner_key]


            return updated_fixed_vars_vals_dict


    def _get_marker(self) -> str:
        '''
           Retrieves the marker setting and checks if the symbol is supported.

           Args:

           Returns: A Matplotlib symbol
        '''

        marker_value = self.get_config_value('marker_symbol')
        if marker_value in constants.AVAILABLE_MARKERS_LIST:
            return marker_value
        else:
            self.logger.error(
                "Requested marker symbol is invalid, check the Matplotlib documentation for supported symbols")
