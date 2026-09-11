# ============================*
# ** Copyright UCAR (c) 2026
# ** University Corporation for Atmospheric Research (UCAR)
# ** National Science Foundation National Center for Atmospheric Research (NSF NCAR)
# ** Research Applications Lab (RAL)
# ** P.O.Box 3000, Boulder, Colorado, 80307-3000, USA
# ============================*

"""
Class Name: ModeFieldPlotConfig

Handles configuration settings for plotting the Mode fields

Default configuration file settings are overridden by a mandatory, user-specified
configuration file.

"""
__author__ = 'Minna Win'

import os
from .. import util


class ModeFieldPlotConfig():

    def __init__(self, parameters: dict):

        self.params = parameters

        log_level: str = self.get_config_value('log_level')
        log_filename = self.get_config_value('log_filename')
        self.logger = util.get_common_logger(log_level, log_filename)

        input_dir = self.get_config_value('input_dir')
        input_data = self.get_config_value('mode_obj_file')
        self.input_file = os.path.join(input_dir, input_data)
        self.field_to_plot: str = self.get_config_value('field_to_plot')

        output_dir = self.get_config_value('output_dir')
        output_fname = self.get_config_value('output_filename')
        self.output_filename = os.path.join(output_dir, output_fname)

        self.download_shapefile: bool = self.get_config_value('download_natural_earth_shapefile')

        if self.get_config_value('plot_filename') is None or self.get_config_value('plot_filename') == ' ':
            if self.field_to_plot.lower() == 'raw':
                plot_name = "mode_raw.png"
            else:
                # name the objects field plot
                self.plot_filename = "mode_objects.png"
        else:
            # user-defined plot filename
            self.plot_filename = self.get_config_value('plot_filename')

        # Plot settings
        self.plot_width = self.get_config_value('plot_width')
        self.plot_height = self.get_config_value('plot_height')
        self.padding: float = self.get_config_value('bbox_padding_degrees')
        self.resolution_dpi: float = self.get_config_value('resolution_dpi')
        self.auto_space: bool = self.get_config_value('automatic_vert_horiz_spacing')
        self.labels_on: bool = self.get_config_value('show_obj_id_labels')
        # colormap settings
        self.cmap: str = self.get_config_value('colormap_name')
        self.vmin: float = self.get_config_value('vmin')
        self.vmax: float = self.get_config_value('vmax')
        self.vmax_pctile: float = self.get_config_value('vmax_pctile')

        self.colorbar_label: str = self.get_config_value('colorbar_label')
        self.colorbar_label_fontsize: int = self.get_config_value('colorbar_label_fontsize')
        self.colorbar_max: float = self.get_config_value('colorbar_max')

        self.title_space: float = self.get_config_value('title_space')
        self.top_bottom_margin: float = self.get_config_value('top_bottom_margin')
        self.super_title_text = self.get_config_value('super_title')
        self.super_title_font_size = self.get_config_value('super_title_font_size')

        self.subplot_adjust_top = self.get_config_value('subplot_top')
        self.subplot_adjust_bottom = self.get_config_value('subplot_bottom')
        self.subplot_adjust_left = self.get_config_value('subplot_left')
        self.subplot_adjust_right = self.get_config_value('subplot_right')
        self.vert_spacing = self.get_config_value('vert_spacing')


    def get_config_value(self, *args: str | int | float):
        """
        Gets the value of a configuration parameter.
        Looks for parameter in the user's parameter dictionary

        Args:
            @ param args - chain of keys that defines a key to the parameter

        Returns:
            - a value for the parameter of None
       """

        if args and self.params:

            # get value for the first key
            element = args[0]
            if element:
                value = self.params.get(element)

                # if the size of key tuple is 1 - the search is over
                if len(args) == 1:
                    return value

                # if the size of key tuple is > 1 - search using other keys
                return self._get_nested(value, args[1:])
        return None
