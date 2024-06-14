# ============================*
 # ** Copyright UCAR (c) 2020
 # ** University Corporation for Atmospheric Research (UCAR)
 # ** National Center for Atmospheric Research (NCAR)
 # ** Research Applications Lab (RAL)
 # ** P.O.Box 3000, Boulder, Colorado, 80307-3000, USA
 # ============================*
 
 
 
"""
Class Name: prob_hist.py
 """
__author__ = 'Tatiana Burek'

from typing import Union
from datetime import datetime

from metplotpy.plots.histogram.hist import Hist
from metplotpy.plots.histogram.hist_series import HistSeries
from metplotpy.plots import util


class ProbHist(Hist):
    """  Generates a Plotly  Probability Histogram
        or Histograms of probability integral transform plot for 1 or more traces
    """
    LONG_NAME = 'probability histogram'
    config_obj_name = 'ProbHistogramConfig'
    series_obj = 'ProbHistSeries'

    def _get_x_points(self, series: HistSeries) -> list:
        x_points = []
        for ser in self.series_list:
            if len(x_points) > 0:
                break
            if len(ser.series_data) > 0:
                bin_size = ser.series_data['bin_size'][0]
                for i in range(1, int(1 / bin_size + 1)):
                    x_points.append(i * bin_size)
        return x_points

    def _get_dtick(self) -> Union[float, str]:
        bin_size = None
        for series in self.series_list:
            if bin_size is not None:
                break
            if len(series.series_data) > 0:
                bin_size = series.series_data['bin_size'][0]

        if bin_size is None:
            bin_size = 0.05
        return bin_size


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
    params = util.get_params(config_filename)
    try:
        plot = ProbHist(params)
        plot.save_to_file()
        # plot.show_in_browser()
        plot.write_html()
        plot.write_output_file()
        log_level = plot.get_config_value('log_level')
        log_filename = plot.get_config_value('log_filename')
        logger = util.get_common_logger(log_level, log_filename)
        logger.info(f"Finished probability histogram: {datetime.now()}")
    except ValueError as val_er:
        print(val_er)


if __name__ == "__main__":
    main()
