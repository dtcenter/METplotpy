# ============================*
# ** Copyright UCAR (c) 2023
# ** University Corporation for Atmospheric Research (UCAR)
# ** National Center for Atmospheric Research (NCAR)
# ** Research Applications Lab (RAL)
# ** P.O.Box 3000, Boulder, Colorado, 80307-3000, USA
# ============================*


"""
Class Name: TcmprSeriesLineMean
 """

from typing import Union

import numpy as np

import metcalcpy.util.utils as utils
from metplotpy.plots.tcmpr_plots.tcmpr_series import TcmprSeries
from metplotpy.plots.tcmpr_plots.tcmpr_util import get_mean_ci


class TcmprSeriesLineMean(TcmprSeries):
    """
        Represents a TCMPR mean  series object
        of data points and their plotting style
        elements (line colors,  etc.)

    """

    def __init__(self, config, idx: int, input_data, series_list: list,
                 series_name: Union[list, tuple]):
        super().__init__(config, idx, input_data, series_list, series_name)

    def _create_series_points(self) -> dict:
        """
        Subset the data for the appropriate series.
        Calculate values for each point including CI

        Args:

        Returns:
               dictionary with CI ,point values and number of stats as keys
        """

        self._init_series_data()

        series_points_results = {'val': [], 'ncl': [], 'ncu': [], 'nstat': [], 'mean': []}

        # for each point calculate plot statistic
        for indy in self.config.indy_vals:
            if utils.is_string_integer(indy):
                indy = int(indy)
            elif utils.is_string_strictly_float(indy):
                indy = float(indy)
            point_data = self.series_data.loc[self.series_data['LEAD_HR'] == indy]
            point_data = point_data.sort_values(by=['CASE'])

            ci_data = get_mean_ci(point_data['PLOT'].tolist(), self.config.alpha, self.config.n_min)
            if ci_data['ncl'] is not None:
                dbl_lo_ci = ci_data['val'] - ci_data['ncl']
            else:
                dbl_lo_ci = ci_data['val']

            if ci_data['ncu'] is not None:
                dbl_up_ci = ci_data['ncu'] - ci_data['val']
            else:
                dbl_up_ci = ci_data['val']

            series_points_results['ncl'].append(dbl_lo_ci)
            series_points_results['val'].append(ci_data['val'])
            series_points_results['ncu'].append(dbl_up_ci)
            series_points_results['nstat'].append(len(point_data))
            if series_points_results['nstat'] == 0:
                series_points_results['mean'].append(None)
            else:
                series_points_results['mean'].append(np.nanmean(point_data['PLOT'].tolist()))

        return series_points_results
