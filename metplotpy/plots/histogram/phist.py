"""
Class Name: phist.py
 """
__author__ = 'Tatiana Burek'

import yaml
import plotly.graph_objects as go

from plots.constants import PLOTLY_AXIS_LINE_COLOR, PLOTLY_AXIS_LINE_WIDTH
from plots.histogram.plhist_series import PhistSeries
import plots.util as util

from plots.histogram.rhist import Rhist


class Phist(Rhist):
    """  Generates a Plotly  Probability Histogram
        or Histograms of probability integral transform plot for 1 or more traces
    """

    def _create_series(self, input_data):
        """
           Generate all the series objects that are to be displayed as specified by the plot_disp
           setting in the config file.  The points are all ordered by datetime.  Each series object
           is represented by a line in the diagram, so they also contain information
           for line width, line- and marker-colors, line style, and other plot-related/
           appearance-related settings (which were defined in the config file).

           Args:
               input_data:  The input data in the form of a Pandas dataframe.
                            This data will be subset to reflect the series data of interest.

           Returns:
               a list of series objects that are to be displayed


        """
        series_list = []

        # create series in teh correct order
        for i, name in enumerate(self.config_obj.get_series_y()):
            if not isinstance(name, list):
                name = [name]
            # get the actual index
            ind = i
            for order_index, order in enumerate(self.config_obj.series_ordering_zb):
                if order == i:
                    ind = order_index
                    break

            series_obj = PhistSeries(self.config_obj, ind, input_data, series_list, name)
            series_list.append(series_obj)

        if len(series_list) == 0:
            series_obj = PhistSeries(self.config_obj, 0, input_data, series_list, [])
            series_list.append(series_obj)
        else:
            # reorder series
            series_list = self.config_obj.create_list_by_series_ordering(series_list)

        self.x_points = []
        self.bin_size = 0.05
        for series in series_list:
            if len(self.x_points) > 0:
                break
            if len(series.series_data) > 0:
                self.bin_size = series.series_data['bin_size'][0]
                for i in range(1, int(1 / self.bin_size + 1)):
                    self.x_points.append(i * self.bin_size)

        return series_list

    def _draw_series(self, series: PhistSeries) -> None:
        """
        Draws the formatted Bar on the plot
        :param series: Bar series object with data and parameters
        """

        y_points = series.series_points

        # add the bar to plot
        self.figure.add_trace(
            go.Bar(
                x=self.x_points,
                y=y_points,
                showlegend=True,
                name=self.config_obj.user_legends[series.idx],
                marker_color=self.config_obj.colors_list[series.idx],
                marker_line_color=self.config_obj.colors_list[series.idx]
            )
        )

    def _add_xaxis(self) -> None:
        """
        Configures and adds x-axis to the plot
        """
        self.figure.update_xaxes(title_text=self.config_obj.xaxis,
                                 linecolor=PLOTLY_AXIS_LINE_COLOR,
                                 linewidth=PLOTLY_AXIS_LINE_WIDTH,
                                 zeroline=False,
                                 gridwidth=self.config_obj.parameters['grid_lwd'],
                                 gridcolor=self.config_obj.blended_grid_col,
                                 automargin=True,
                                 title_font={
                                     'size': self.config_obj.x_title_font_size
                                 },
                                 title_standoff=abs(self.config_obj.parameters['xlab_offset']),
                                 tickangle=self.config_obj.x_tickangle,
                                 tickfont={'size': self.config_obj.x_tickfont_size},
                                 dtick=self.bin_size,
                                 showgrid=False
                                 )


def main(config_filename=None):
    """
            Generates a sample, default, Probability Histogram or Histograms of probability integral transform
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
        plot = Phist(docs)
        plot.save_to_file()
        plot.show_in_browser()
        plot.write_html()
        plot.write_output_file()
    except ValueError as val_er:
        print(val_er)


if __name__ == "__main__":
    main()
