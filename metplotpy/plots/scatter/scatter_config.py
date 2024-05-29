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

        # Plot is NOT interactive, set the value appropriately
        self.create_html = False

        # Write (if dump_points_1 is True) output points file provided by the METplotpy YAML config file
        self.dump_points_1 = self._get_bool('dump_points_1')
        if self.dump_points_1:
            self.points_path = self.get_config_value('points_path')



