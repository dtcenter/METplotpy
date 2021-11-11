"""
Class Name: rel_hist.py
 """
__author__ = 'Tatiana Burek'

import yaml

import plots.util as util
from plots.histogram.hist import Hist

from plots.histogram.hist_series import HistSeries


class RelHist(Hist):
    """  Generates a Plotly  Relative Histogram or Histograms of relative position plot
        for 1 or more traces
    """

    config_obj_name='RelHistogramConfig'
    series_obj='RelHistSeries'

    def _get_x_points(self, series: HistSeries) -> list:
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

    # Retrieve the contents of the custom config file to over-ride
    # or augment settings defined by the default config file.
    if not config_filename:
        config_file = util.read_config_from_command_line()
    else:
        config_file = config_filename
    with open(config_file, 'r') as stream:
        try:
            docs = yaml.load(stream, Loader=yaml.FullLoader)
        except yaml.YAMLError as exc:
            print(exc)

    try:
        plot = RelHist(docs)
        plot.save_to_file()
        # plot.show_in_browser()
        plot.write_html()
        plot.write_output_file()
    except ValueError as val_er:
        print(val_er)


if __name__ == "__main__":
    main()
