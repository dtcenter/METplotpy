"""
Class Name: taylor_diagram.py
 """
__author__ = 'Minna Win'

import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.font_manager import FontProperties
import numpy as np
import yaml
import pandas as pd
import warnings
from plots.base_plot import BasePlot

warnings.filterwarnings("ignore", category=DeprecationWarning)

class TaylorDiagram(BasePlot):
    """  Generates a performance diagram (multi-line line plot)
         where each line represents a series of Success ratio vs POD
         A series represents a model paired with a vx_masking region.

         A setting is over-ridden in the default configuration file if
         it is defined in the custom configuration file.

    """

    def __init__(self, parameters:dict) -> None:
        """ Creates a line plot consisting of one or more lines (traces), based on
            settings indicated by parameters.

            Args:
            @param parameters: dictionary containing user defined parameters

        """

        default_conf_filename = "taylor_diagram_defaults.yaml"


