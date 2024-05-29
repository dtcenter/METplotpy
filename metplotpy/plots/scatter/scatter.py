# ============================*
# ** Copyright UCAR (c) 2024
# ** University Corporation for Atmospheric Research (UCAR)
# ** National Science Foundation National Center for Atmospheric Research (NSF NCAR)
# ** Research Applications Lab (RAL)
# ** P.O.Box 3000, Boulder, Colorado, 80307-3000, USA
# ============================*

"""
Class Name: Scatter
 """
__author__ = 'Minna Win'

import os
from datetime import datetime
import re
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.font_manager import FontProperties
import numpy as np
import yaml
import pandas as pd
from metplotpy.plots.base_plot import BasePlot
import metcalcpy.util.utils as calc_util
from metplotpy.plots.scatter.scatter_config import ScatterConfig
# from metplotpy.plots.performance_diagram.performance_diagram_series import PerformanceDiagramSeries
from metplotpy.plots import util
from metplotpy.plots import constants

class Scatter(BasePlot):
    """
       Generate a scatter plot using Matplotlib and MPR linetyp output from the MET point-stat tool.

       PRE-CONDITION:  The MET .stat output data MUST be reformatted for the scatter plot, where all column headers
                       are present AND there are additional columns for stat_name, stat_value, stat_ncl, stat_ncu,
                       stat_bcu, and stat_bcl.


    """

    defaults_name = 'scatter_defaults.yaml'

    def __init__(self, parameters: dict) -> None:
        """
           Create a scatter plot of one or two 'lines', with marker color of the variable
           of interest varies based on values.  The colors are determined by the colormap
           specified in the configuration file.  Requires a configuration file to be used
           in conjunction with the default configuration file.

           Args:
               @param parameters: a dictionary representation of the settings in the YAML configuration file
           Returns:
               None

        """

        super().__init__(parameters, self.defaults_name)

        # instantiate a ScatterConfig object that contains all the settings
        self.config_obj = ScatterConfig(self.parameters)

        # use the logger set up in the METplotpy util module
        self.logger = self.config_obj.logger