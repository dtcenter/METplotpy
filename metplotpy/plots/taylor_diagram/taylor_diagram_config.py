
"""
Class Name: taylor_diagram_config.py

Holds values set in the Taylor Diagram configuration files
"""

__author__ = "Minna Win"

import re
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
        self.series_ordering = self._get_series_order('series_order')

        # Make series ordering zero-based to achieve consistency with Python,
        # which is zero-based.
        self.series_ordering_zb = [sorder -1 for sorder in self.series_ordering]
        self.stat_input = self.get_config_value('stat_input')
        self.plot_disp = self._get_plot_disp()
        self.colors_list = self._get_colors()
        self.marker_list = self._get_markers()
        self.linewidth_list = self._get_linewidths()
        self.linestyles_list = self._get_linestyles()
        self.user_legends = self._get_user_legends("Taylor Diagram")
        self.plot_units = self.get_config_value('plot_units')
        self.plot_resolution = self.get_config_value('plot_res')

        # Convert the plot height and width to inches if units aren't in
        # inches.
        if self.plot_units.lower() != 'in':
            self.plot_width = self.calculate_plot_dimension('plot_width', 'in')
            self.plot_height = self.calculate_plot_dimension('plot_height', 'in')

        # x-axis labels, x-axis ticks
        self.x_title_font_size = self.parameters['xlab_size'] * constants.DEFAULT_CAPTION_FONTSIZE

        # legend style settings as defined in METviewer:
        # legend box, ncol, inset
        user_settings = self._get_legend_style()

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

    def _get_plot_disp(self) -> list:
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