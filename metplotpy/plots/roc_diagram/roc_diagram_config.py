"""
Class Name: roc_diagram_config.py

Holds values set in the ROC config file(s)
"""
__author__ = 'Minna Win'
__email__ = 'met_help@ucar.edu'

from plots.config import Config
import plots.constants as constants

class ROCDiagramConfig(Config):
    def __init__(self, parameters):
        """ Reads in the plot settings from a ROC config file

            Args:
            @param parameters: dictionary containing user defined parameters

            Returns:

        """

        # init common layout
        super().__init__(parameters)

        # use this setting to determine the ordering of colors, lines, and markers
        self.series_ordering = self._get_series_order()

        # self.plot_ci = self._get_plot_ci()
        self.plot_disp = self._get_plot_disp()

        # Make the series ordering zero-based to be consistent with Python's zero-based
        # counting/numbering
        self.series_ordering_zb = [sorder - 1 for sorder in self.series_ordering]

        # settings that are unique to ROC diagrams
        self.stat_input = self.get_config_value('stat_input')
        # Contingency table count line type
        self.linetype_ctc = self.get_config_value('roc_ctc')
        # Probability contingency table count line type
        self.linetype_pct = self.get_config_value('roc_pct')
        # Supported values for stat_curve are none, mean, and median
        self.stat_curve = self.get_config_value('stat_curve')
        self.add_threshold_pts = self.get_config_value('add_pt_thresh')
        self.plot_width = self.get_config_value('plot_width')
        self.plot_height = self.get_config_value('plot_height')
        self.plot_resolution = self._get_plot_resolution()
        self.caption = self.get_config_value('plot_caption')
        self.caption_weight = self.get_config_value('caption_weight')
        self.caption_color = self.get_config_value('caption_color')
        self.caption_size = self.get_config_value('caption_size')
        self.caption_offset = self.get_config_value('caption_offset')
        self.caption_align = self.get_config_value('caption_align')
        self.plot_stat = self.stat_curve
        self.colors_list = self._get_colors()
        self.marker_list = self._get_markers()
        self.linewidth_list = self._get_linewidths()
        self.linestyles_list = self._get_linestyles()
        self.user_legends = self._get_user_legends()
        self.add_point_thresholds = self._get_point_thresh()
        # legend style settings as defined in METviewer
        user_settings = self._get_legend_style()

        # list of the x, y, and loc values for the
        # bbox_to_anchor() setting used in determining
        # the location of the bounding box which defines
        # the legend.
        self.bbox_x = float(user_settings['bbox_x'])
        self.bbox_y = float(user_settings['bbox_y'])
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


    def _get_point_thresh(self):
        """
            Retrieve the value (true/false) of the add_point_threshold
            setting in the config file.  This determines whether (or not)
            to label the corresponding threshold values.

            Args:

            Returns:
                True if add_point_thresholds is set to true
                False otherwise

        """
        if self.get_config_value('add_point_thresholds'):
            response = self.get_config_value('add_point_thresholds').lower()
            if response == "true":
                return True
            else:
                return False
