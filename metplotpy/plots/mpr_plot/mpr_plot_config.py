"""
Class Name: wind_rose_config.py

Holds values set in the Wind Rose config file(s)
"""
from plots.config import Config


class MprPlotConfig(Config):
    """ Reads in the plot settings from a rose_wind config file
        Args:
            @param parameters: dictionary containing user defined parameters
        Returns:
    """

    def __init__(self, parameters):
        # init common layout
        super().__init__(parameters)

        self.wind_rose_breaks = self.get_config_value('wind_rose_breaks')
        self.wind_rose_angle = self.get_config_value('wind_rose_angle')
        self.wind_rose_marker_colors = self.get_config_value('wind_rose_marker_colors')

        if len(self.wind_rose_marker_colors) != len(self.wind_rose_breaks):
            raise ValueError('wind_rose_marker_colors must have the same size as wind_rose_breaks')

        self.angularaxis_tickvals = self.get_config_value('angularaxis_tickvals')
        self.angularaxis_ticktext = self.get_config_value('angularaxis_ticktext')
        self.stat_input = self.get_config_value('stat_input')
        self.plot_width = self.get_config_value('plot_width')
        self.plot_height = self.get_config_value('plot_height')
        self.wind_rose = self.get_config_value('wind_rose')
        self.plot_filename = self.get_config_value('plot_filename')
        self.mpr_file_list = self.get_config_value('mpr_file_list')
        self.width = self.get_config_value('width')
        self.height = self.get_config_value('height')
        self.marker_color = self.get_config_value('marker_color')
        self.show_in_browser = self.get_config_value('show_in_browser')
