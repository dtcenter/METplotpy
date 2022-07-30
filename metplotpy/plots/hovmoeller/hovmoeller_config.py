# ============================*
# ** Copyright UCAR (c) 2020
# ** University Corporation for Atmospheric Research (UCAR)
# ** National Center for Atmospheric Research (NCAR)
# ** Research Applications Lab (RAL)
# ** P.O.Box 3000, Boulder, Colorado, 80307-3000, USA
# ============================*


"""
Class Name: hovmoeller_config.py

Holds values set in the hovmoeller config file(s)
"""
__author__ = 'Minna Win'

from ..config import Config
from .. import util
from .. import constants

class HovmoellerConfig(Config):
    def __init__(self, parameters):
        """ Reads in the plot settings from the hovmoeller config files

            Args:
            @param parameters: dictionary containing user defined parameters

            Returns:

        """

        # init common layout
        super().__init__(parameters)

        self.data_dir = self.get_config_value('input_data_dir')
        self.input_data_file = self.get_config_value('input_data_file')
        self.log_level = str(self.get_config_value('log_level')).upper()
        self.xy_label_fontsize = self.get_config_value('xy_label_font_size')
        self.title_size = self.get_config_value('title_size')
        self.date_start = self.get_config_value('date_start')
        self.date_end = self.get_config_value('date_end')
        self.lat_min = self.get_config_value('lat_min')
        self.lat_max = self.get_config_value('lat_max')
        self.var_name = self.get_config_value('var_name')
        self.var_units = self.get_config_value('var_units')
        self.unit_conversion = self.get_config_value('unit_conversion')
        self.contour_min = self.get_config_value('contour_min')
        self.contour_max = self.get_config_value('contour_max')
        self.contour_del = self.get_config_value('contour_del')
        self.colorscale = self.get_config_value('colorscale')
        self.xaxis = self.get_config_value('xaxis')
        self.yaxis = self.get_config_value('yaxis')








