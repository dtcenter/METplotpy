# ============================*
# ** Copyright UCAR (c) 2023
# ** University Corporation for Atmospheric Research (UCAR)
# ** National Center for Atmospheric Research (NCAR)
# ** Research Applications Lab (RAL)
# ** P.O.Box 3000, Boulder, Colorado, 80307-3000, USA
# ============================*


"""
Class Name: TcmprSeriesSkill
 """

from typing import Union

import numpy as np
from pandas import DataFrame

import metcalcpy.util.utils as utils
from plots.tcmpr_plots.tcmpr_series import TcmprSeries


class TcmprSeriesSkillMedian(TcmprSeries):
    """
        Represents a Box plot series object
        of data points and their plotting style
        elements (line colors,  etc.)

    """

    def __init__(self, config, idx: int, input_data, series_list: list,
                 series_name: Union[list, tuple], skill_ref_data: DataFrame = None):
        super().__init__(config, idx, input_data, series_list, series_name, skill_ref_data)

    def _create_series_points(self) -> dict:
        """
        Subset the data for the appropriate series.
        Calculate values for each point including CI

        Args:

        Returns:
               dictionary with CI ,point values and number of stats as keys
        """

        self._init_series_data()
        result_size = len(self.config.indy_vals)
        series_points_results = {'val': [None] * result_size,
                                 'nstat': [None] * result_size}
        # for each point calculate plot statistic
        for i in range(0, result_size):
            indy = self.config.indy_vals[i]
            if utils.is_string_integer(indy):
                indy = int(indy)
            elif utils.is_string_strictly_float(indy):
                indy = float(indy)
            point_data = self.series_data.loc[
                (self.series_data['LEAD_HR'] == indy)]

            # Skip lead times for which no data is found

            if len(point_data) > 0 and self.skill_ref_data is not None and len(self.skill_ref_data) > 0:
                point_data = point_data.sort_values(by=['CASE'])
                data_ref = self.skill_ref_data.loc[(self.skill_ref_data['LEAD_HR'] == indy)]

                # Get the values to be plotted for this lead time
                val = None
                if i != 0 and data_ref is not None:
                    cur = np.nanmedian(point_data['PLOT'].tolist())
                    ref = np.nanmedian(data_ref['PLOT'].tolist())

                    if ref is not None and cur is not None:
                        val = utils.round_half_up(100 * (ref - cur) / ref, 0)

                    series_points_results['val'][i] = val

            series_points_results['nstat'][i] = len(point_data)

        return series_points_results
