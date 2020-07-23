"""
Class Name: ROCDiagramSeries
 """
__author__ = 'Minna Win'
__email__ = 'met_help@ucar.edu'

import pandas as pd
import metcalcpy.util.ctc_statistics as cstats
import metcalcpy.util.pstd_statistics as pstats
from plots.series import Series

class ROCDiagramSeries(Series):
    """
        Represents a ROC diagram series object
        of data points and their plotting style
        elements (line colors, markers, linestyles, etc.)

    """
    def __init__(self, config, idx, input_data):
        super().__init__(config, idx, input_data)

    def _create_series_points(self):
        """
           Subset the data for the appropriate series.  Data input can
           originate from CTC linetype or PCT linetype.  The methodology
           will depend on the linetype.

           Args:

           Returns:
               tuple of three lists:
                                   pody (Probability of detection) and
                                   pofd (probability of false detection/
                                         false alarm rate)
                                   thresh (threshold value, used to annotate)


        """
        if self.config.linetype_ctc:
            df_roc = cstats.calculate_ctc_roc(self.input_data)
            pody = df_roc['pody']
            pody = pd.Series([1]).append(pody, ignore_index=True)
            pody = pody.append(pd.Series([0]), ignore_index=True)
            pofd = df_roc['pofd']
            pofd = pd.Series([1]).append(pofd, ignore_index=True)
            pofd = pofd.append(pd.Series([0]), ignore_index=True)
            thresh = df_roc['thresh']
            thresh = pd.Series(['']).append(thresh, ignore_index=True)
            thresh = thresh.append(pd.Series(['']), ignore_index=True)
            return pofd, pody, thresh


        elif self.config.linetype_pct:
            roc_df = pstats._calc_pct_roc(self.input_data)

            pody = roc_df['pody']
            pofd = roc_df['pofd']
            thresh = roc_df['thresh']
            return pofd, pody, thresh
        else:
            raise ValueError('error neither ctc or pct linetype ')
