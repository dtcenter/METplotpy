# ============================*
 # ** Copyright UCAR (c) 2022
 # ** University Corporation for Atmospheric Research (UCAR)
 # ** National Center for Atmospheric Research (NCAR)
 # ** Research Applications Lab (RAL)
 # ** P.O.Box 3000, Boulder, Colorado, 80307-3000, USA
 # ============================*
 
 
 
"""
Class Name: eclv_config.py

Holds values set in the ECLV plot config file(s)
"""
__author__ = 'Tatiana Burek'

import itertools
from ..line.line_config import LineConfig


class EclvConfig(LineConfig):
    """
    Prepares and organises Economic Cost Loss Relative Value plot parameters
    """

    def __init__(self, parameters: dict) -> None:
        LineConfig.__init__(self, parameters)
        self.fixed_vars_vals_input = self.parameters['fixed_vars_vals_input']

    def _get_user_legends(self, legend_label_type: str = '') -> list:
        """
        Retrieve the text that is to be displayed in the legend at the bottom of the plot.
        Each entry corresponds to a series.

        Args:
                @parm legend_label_type:  The legend label, such as 'Economic value' that indicates
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
                if isinstance(ser_components, str):
                    legend_list.append(ser_components + ' Economic value')
                else:
                    legend_list.append(' '.join(map(str, ser_components)) + ' Economic value')
            else:
                # user provided a legend - use it
                legend_list.append(all_user_legends[idx])

        return self.create_list_by_series_ordering(legend_list)

    def config_consistency_check(self):
        """Checks that the number of settings are consistent with number of series.

           @raises ValueError if any of settings are inconsistent with the
            number of series (as defined by the cross product of the model
            and vx_mask defined in the series_val_1 setting)
        """

        lists_to_check = {
            "plot_ci": self.plot_ci,
            "plot_disp": self.plot_disp,
            "marker_list": self.marker_list,
            "series_ordering": self.series_ordering,
            "colors_list": self.colors_list,
            "user_legends": self.user_legends,
            "linewidth_list": self.linewidth_list,
            "linestyles_list": self.linestyles_list,
            "show_legend": self.show_legend,
        }
        self._config_compare_lists_to_num_series(lists_to_check)

    def calculate_number_of_series(self) -> int:
        """
           From the number of items in the permutation list,
           determine how many series "objects" are to be plotted.

           Args:

           Returns:
               the number of series

        """
        # Retrieve the lists from the series_val_1 dictionary
        series_vals_list = self.series_vals_1.copy()

        # Utilize itertools' product() to create the cartesian product of all elements
        # in the lists to produce all permutations of the series_val values and the
        # fcst_var_val values.
        permutations = list(itertools.product(*series_vals_list))
        return len(permutations)
