"""
Class Name: ROCDiagramSeries
 """
__author__ = 'Minna Win'
__email__ = 'met_help@ucar.edu'

import metcalcpy.util.utils as cp_utils
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


        """
        if self.config.linetype_ctc:
            print('do stuff for ctc')


        elif self.config.linetype_pct:
            print('do stuff for pct')
        else:
            raise ValueError('error neither ctc or pct linetype ')
