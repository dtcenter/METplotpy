# ============================*
# ** Copyright UCAR (c) 2022
# ** University Corporation for Atmospheric Research (UCAR)
# ** National Center for Atmospheric Research (NCAR)
# ** Research Applications Lab (RAL)
# ** P.O.Box 3000, Boulder, Colorado, 80307-3000, USA
# ============================*


"""
Class Name: revision_box_config.py

Holds values set in the RevisionBox plot config file(s)
"""
import itertools

from ..box.box_config import BoxConfig
from .. import constants as constants
from .. import util

import metcalcpy.util.utils as utils


class RevisionBoxConfig(BoxConfig):
    def __init__(self, parameters: dict) -> None:
        """ Reads in the plot settings from a revision box plot config file.

           Args:
           @param parameters: dictionary containing user defined parameters

       """

        super().__init__(parameters)

        # override values set in BoxConfig that are not used by revision box
        self.plot_stat = None
        self.show_nstats = None
        self.dump_points_2 = None
        self.vert_plot = None
        self.xaxis_reverse = None
        self.sync_yaxes = None

        self.all_series_y2 = None

        # set values specific to RevisionBox not set in BoxConfig
        self.revision_ac = self._get_bool('revision_ac')
        self.revision_run = self._get_bool('revision_run')
        self.indy_stagger = self._get_bool('indy_stagger_1')

    def _get_user_legends(self, legend_label_type: str = '') -> list:
        """
        Retrieve the text that is to be displayed in the legend at the bottom of the plot.
        Each entry corresponds to a series.

        Args:
                @parm legend_label_type:  The legend label, such as 'Performance' that indicates
                                          the type of series line. Used when the user hasn't
                                          indicated a legend.

        Returns:
                a list consisting of the series label to be displayed in the plot legend.

        """

        all_user_legends = self.get_config_value('user_legend')
        legend_list = []

        # create legend list for y-axis series
        for idx, ser_components in enumerate(self.get_series_y(1)):
            if idx >= len(all_user_legends) or all_user_legends[idx].strip() == '':
                # user did not provide the legend - create it
                legend_list.append(' '.join(map(str, ser_components)))
            else:
                # user provided a legend - use it
                legend_list.append(all_user_legends[idx])

        return self.create_list_by_series_ordering(legend_list)
