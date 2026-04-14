# ============================*
 # ** Copyright UCAR (c) 2020
 # ** University Corporation for Atmospheric Research (UCAR)
 # ** National Center for Atmospheric Research (NCAR)
 # ** Research Applications Lab (RAL)
 # ** P.O.Box 3000, Boulder, Colorado, 80307-3000, USA
 # ============================*
 
 
 
"""
Class Name: roc_diagram_config.py

Holds values set in the ROC config file(s)
"""
__author__ = 'Minna Win'

from ..config import Config
from .. import util
from .. import constants

class ROCDiagramConfig(Config):
    def __init__(self, parameters):
        """ Reads in the plot settings from a ROC config file

            Args:
            @param parameters: dictionary containing user defined parameters

            Returns:

        """

        # init common layout
        super().__init__(parameters)

        # Boolean value to indicate whether to make the METviewer plot interactive
        self.create_html = self._get_bool('create_html')

        # Write (or not write) output points file provided by METviewer
        self.dump_points_1 = self._get_bool('dump_points_1')

        # Optional setting, indicates *where* to save the dump_points_1 file
        # used by METviewer
        self.points_path = self.get_config_value('points_path')

        # use this setting to determine the ordering of colors, lines, and markers
        self.series_ordering = self._get_series_order()

        # self.plot_ci = self._get_plot_ci()
        self.plot_disp = self._get_plot_disp()

        # Make the series ordering zero-based to be consistent with Python's zero-based
        # counting/numbering
        self.series_ordering_zb = [sorder - 1 for sorder in self.series_ordering]

        # settings that are unique to ROC diagrams
        self.series_inner_dict1 = self._get_series_inner_dict(1)
        self.series_inner_dict2 = self._get_series_inner_dict(2)
        self.stat_input = self.get_config_value('stat_input')
        # Contingency table count line type
        self.linetype_ctc = self.get_config_value('roc_ctc')
        # Probability contingency table count line type
        self.linetype_pct = self.get_config_value('roc_pct')
        # TODO: it looks like both roc_ctc and roc_pct cannot be set - add error check?
        # Supported values for stat_curve are none, mean, and median
        self.plot_stat = self.get_config_value('stat_curve')
        self.plot_width = self.calculate_plot_dimension('plot_width')
        self.plot_height = self.calculate_plot_dimension('plot_height')
        self.plot_resolution = self._get_plot_resolution()
        reverse_ctc_connection = str(self.get_config_value('reverse_connection_order'))
        if reverse_ctc_connection.upper() == "FALSE":
            self.ctc_ascending = False
        else:
            self.ctc_ascending = True

        # title parameters
        self.title_font_size = self.parameters['title_size'] * constants.DEFAULT_TITLE_FONT_SIZE
        self.title_offset = 1.0 + abs(self.parameters['title_offset']) * constants.DEFAULT_TITLE_OFFSET
        self.y_title_font_size = self.parameters['ylab_size'] + constants.DEFAULT_TITLE_FONTSIZE

        # Caption settings
        self.caption = self.get_config_value('plot_caption')
        self.caption_color = self.get_config_value('caption_col')
        # caption size is a magnification value
        self.caption_size = float(self.get_config_value('caption_size')) * constants.DEFAULT_CAPTION_FONTSIZE
        self.caption_offset = self.get_config_value('caption_offset') * constants.DEFAULT_CAPTION_Y_OFFSET
        self.caption_align = self.get_config_value('caption_align')
        self.caption = self.get_config_value('plot_caption')

        self.colors_list = self._get_colors()
        self.marker_list = self._get_markers()
        self.marker_open_list = self._get_markers_open()
        self.linewidth_list = self._get_linewidths()
        self.linestyles_list = self._get_linestyles()
        self.user_legends = self._get_user_legends("ROC Curve")
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
        self.legend_orientation = 'v' # TODO: should this be always vertical?
        legend_box = self.get_config_value('legend_box').lower()
        if legend_box == 'n':
            # Don't draw a box around legend labels
            self.draw_box = False
            self.legend_border_width = 0
        else:
            # Other choice is 'o'
            # Enclose legend labels in a box
            self.draw_box = True
            self.legend_border_width = 2

        # x-axis parameters
        self.x_title_font_size = self.parameters['xlab_size'] * constants.DEFAULT_TITLE_FONT_SIZE
        self.x_tickangle = self.parameters['xtlab_orient']
        if self.x_tickangle in constants.XAXIS_ORIENTATION.keys():
            self.x_tickangle = constants.XAXIS_ORIENTATION[self.x_tickangle]
        self.x_tickfont_size = self.parameters['xtlab_size'] * constants.DEFAULT_TITLE_FONT_SIZE

        # y-axis parameters
        self.y_tickangle = self.parameters['ytlab_orient']
        if self.y_tickangle in constants.YAXIS_ORIENTATION.keys():
            self.y_tickangle = constants.YAXIS_ORIENTATION[self.y_tickangle]
        self.y_tickfont_size = self.parameters['ytlab_size'] * constants.DEFAULT_TITLE_FONT_SIZE


        self.plot_width = self.calculate_plot_dimension('plot_width')
        self.plot_height = self.calculate_plot_dimension('plot_height')
        self.show_legend = self._get_show_legend()

        if 'summary_curve' in self.parameters.keys():
            self.summary_curve = self.parameters['summary_curve']
        else:
            self.summary_curve = 'none'


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

        for k,v in series_val_dict.items():
            # Sometimes the value consists of a list of more
            # than one item:
            for idx, val in enumerate(v):
                val_inner_dict[v[idx]] = k


        return val_inner_dict

    def _get_series_order(self):
        """
            Get the order number for each series

            Args:

            Returns:
            a list of unique values representing the ordinal value of the corresponding series

        """
        ordinals = self.get_config_value('series_order')
        series_order_list = list(ordinals)
        return series_order_list

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
        if str(self.get_config_value('add_point_thresholds')):
            response = str(self.get_config_value('add_point_thresholds')).lower()
            # Treat the value as a string, as this is what we
            # will get from METviewer
            if response == 'true':
                return True
            else:
                return False
