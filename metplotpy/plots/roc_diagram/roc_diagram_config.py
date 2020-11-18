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
        self.series_inner_dict1 = self._get_series_inner_dict(1)
        self.series_inner_dict2 = self._get_series_inner_dict(2)
        self.stat_input = self.get_config_value('stat_input')
        # Contingency table count line type
        self.linetype_ctc = self.get_config_value('roc_ctc')
        # Probability contingency table count line type
        self.linetype_pct = self.get_config_value('roc_pct')
        # Supported values for stat_curve are none, mean, and median
        self.plot_stat = self.get_config_value('stat_curve')
        self.plot_width = self.calculate_plot_dimension('plot_width', 'pixels')
        self.plot_height = self.calculate_plot_dimension('plot_height', 'pixels')
        self.plot_resolution = self._get_plot_resolution()

        self.colors_list = self._get_colors()
        self.marker_list = self._get_markers()
        self.linewidth_list = self._get_linewidths()
        self.linestyles_list = self._get_linestyles()
        self.user_legends = self._get_user_legends("ROC Curve")
        self.add_point_thresholds = self._get_point_thresh()
        # legend style settings as defined in METviewer
        user_settings = self._get_legend_style()

        # caption parameters
        self.caption_weight = self.get_config_value('caption_weight')
        self.caption_color = self.get_config_value('caption_col')
        self.caption_align = self.get_config_value('caption_align')
        ##
        self.caption = self.get_config_value('plot_caption')
        self.caption_size = int(constants.DEFAULT_CAPTION_FONTSIZE
                                * self.get_config_value('caption_size'))
        self.caption_offset = self.parameters['caption_offset'] - 3.1

        # list of the x, y, and loc values for the
        # bbox_to_anchor() setting used in determining
        # the location of the bounding box which defines
        # the legend.
        self.bbox_x = float(user_settings['bbox_x'])
        # set legend box lower by .18 pixels of the default value
        # set in METviewer to prevent obstructing the x-axis.
        self.bbox_y = float(user_settings['bbox_y']) - 0.18
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

        plot_display_config_vals = self.get_config_value('plot_disp')
        plot_display_bools = []
        for p in plot_display_config_vals:
            if str(p).upper() == "TRUE":
                plot_display_bools.append(True)
            else:
                plot_display_bools.append(False)

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
        if str(self.get_config_value('add_point_thresholds')):
            response = str(self.get_config_value('add_point_thresholds')).lower()
            # Treat the value as a string, as this is what we
            # will get from METviewer
            if response == 'true':
                return True
            else:
                return False


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
        all_fcst_vars = []
        if index == 1:
            fcst_var_val_dict = self.get_config_value('fcst_var_val_1')
            if fcst_var_val_dict:
                all_fcst_vars = []
        elif index == 2:
            fcst_var_val_dict = self.get_config_value('fcst_var_val_2')
            if fcst_var_val_dict:
                all_fcst_vars = []
        else:
            all_fcst_vars = []

        return all_fcst_vars

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
                # markers are indicated by name: circle-open (for small circle),
                # circle, triangle-up,
                # diamond, hexagon, square
                m = marker.lower()
                markers_list.append(constants.PCH_TO_PLOTLY_MARKER[m])
        markers_list_ordered = self.create_list_by_series_ordering(markers_list)
        return markers_list_ordered

