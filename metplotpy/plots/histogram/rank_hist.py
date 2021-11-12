"""
Class Name: rank_hist.py
 """
__author__ = 'Tatiana Burek'

import yaml

from plots.histogram.hist import Hist
import plots.util as util
from plots.histogram.hist_series import HistSeries


class RankHist(Hist):
    """  Generates a Plotly  Histograms of ensemble rank plot for 1 or more traces
    """

    config_obj_name='RankHistogramConfig'
    series_obj='RankHistSeries'

    def _get_x_points(self, series: HistSeries) -> list:
        return sorted(series.series_data['i_value'].unique())


def main(config_filename=None):
    """
            Generates a sample, default, Rank histogram plot using the
            default and custom config files on sample data found in this directory.
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
        plot = RankHist(docs)
        plot.save_to_file()
        # plot.show_in_browser()
        plot.write_html()
        plot.write_output_file()
    except ValueError as val_er:
        print(val_er)


if __name__ == "__main__":
    main()
