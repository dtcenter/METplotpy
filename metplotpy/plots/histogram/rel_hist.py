# ============================*
 # ** Copyright UCAR (c) 2020
 # ** University Corporation for Atmospheric Research (UCAR)
 # ** National Center for Atmospheric Research (NCAR)
 # ** Research Applications Lab (RAL)
 # ** P.O.Box 3000, Boulder, Colorado, 80307-3000, USA
 # ============================*
 
 
 
"""
Class Name: rel_hist.py
 """
__author__ = 'Tatiana Burek'

import yaml
from datetime import datetime

from metplotpy.plots import util
from metplotpy.plots.histogram.hist import Hist
from metplotpy.plots.histogram.hist_series import HistSeries


class RelHist(Hist):
    """  Generates a Plotly  Relative Histogram or Histograms of relative position plot
        for 1 or more traces
    """
    LONG_NAME = 'relative frequency histogram'
    config_obj_name='RelHistogramConfig'
    series_obj='RelHistSeries'

    def _get_x_points(self, series: HistSeries) -> list:
        self.logger.info(f"Retrieving x points for {self.LONG_NAME}: {datetime.now()}")
        return sorted(series.series_data['i_value'].unique())


def main(config_filename=None):
    """
            Generates a sample, default, Probability Histogram or
            Histograms of probability integral transform
            plot using the default and custom config files on sample data found in this directory.
            The location of the input data is defined in either the default or
            custom config file.
            Args:
                @param config_filename: default is None, the name of the custom config file to apply
        """
    util.make_plot(config_filename, RelHist)


if __name__ == "__main__":
    main()
