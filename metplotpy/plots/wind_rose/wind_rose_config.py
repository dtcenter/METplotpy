"""
Class Name: wind_rose_config.py

Holds values set in the Wind Rose config file(s)
"""
from ..config import Config


class WindRoseConfig(Config):
    def __init__(self, parameters):
        """ Reads in the plot settings from a rose_wind config file

            Args:
            @param parameters: dictionary containing user defined parameters

            Returns:

        """
        default_conf_filename = "wind_rose_defaults.yaml"
        # init common layout
        super().__init__(parameters)

        self.type = self.get_config_value('type')
        self.title = self.get_config_value('title')
        self.wind_rose_breaks = self.get_config_value('wind_rose_breaks')
        self.wind_rose_angle = self.get_config_value('wind_rose_angle')
        self.wind_rose_marker_colors = self.get_config_value('wind_rose_marker_colors')

        if len(self.wind_rose_marker_colors) != len(self.wind_rose_breaks) :
            raise ValueError('wind_rose_marker_colors must have the same size as wind_rose_breaks')

        self.create_figure = self.get_config_value('create_figure')
        self.show_legend = self.get_config_value('show_legend')
        self.angularaxis_tickvals = self.get_config_value('angularaxis_tickvals')
        self.angularaxis_ticktext = self.get_config_value('angularaxis_ticktext')
        self.stat_input = self.get_config_value('stat_input')
        self.plot_width = self.get_config_value('plot_width')
        self.plot_height = self.get_config_value('plot_height')
        self.dump_points = self.get_config_value('dump_points')
        # Optional setting, indicates *where* to save the dump_points_1 file
        # used by METviewer
        self.points_path = self.get_config_value('points_path')
        self.show_in_browser = self.get_config_value('show_in_browser')

