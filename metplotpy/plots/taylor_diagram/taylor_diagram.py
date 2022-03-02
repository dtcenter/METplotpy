# ============================*
 # ** Copyright UCAR (c) 2022
 # ** University Corporation for Atmospheric Research (UCAR)
 # ** National Center for Atmospheric Research (NCAR)
 # ** Research Applications Lab (RAL)
 # ** P.O.Box 3000, Boulder, Colorado, 80307-3000, USA
 # ============================*
 
 
 
"""
Class Name: taylor_diagram.py

Generates a Taylor diagram using the Matplotlib code from
Yannick Copin <yannick.copin@laposte.net>
(with some slight modifications) for creating the axis and plot's look-and-feel.
Incorporated to support the functionality originally provided by the R implementation used by
METviewer.
 """
__author__ = 'Minna Win'

import warnings
import logging
import matplotlib.pyplot as plt
import numpy
import pandas
from matplotlib.font_manager import FontProperties
from matplotlib.projections import PolarAxes
import mpl_toolkits.axisartist.floating_axes as fa
import mpl_toolkits.axisartist.grid_finder as gf
import numpy as np
import yaml
import pandas as pd
from metplotpy.plots import constants
from metplotpy.plots.base_plot import BasePlot
from metplotpy.plots import util
from metplotpy.plots.taylor_diagram.taylor_diagram_config import TaylorDiagramConfig
from metplotpy.plots.taylor_diagram.taylor_diagram_series import TaylorDiagramSeries

warnings.filterwarnings("ignore", category=DeprecationWarning)


class TaylorDiagram(BasePlot):
    """  Generates a Taylor diagram
         A setting is over-ridden in the default configuration file if
         that same setting is defined in the custom configuration file.

    """

    def __init__(self, parameters: dict) -> None:
        """ Creates a Taylor diagram

            Args:
            @param parameters: dictionary containing user defined parameters

        """

        default_conf_filename = "taylor_diagram_defaults.yaml"

        # init common layout
        super().__init__(parameters, default_conf_filename)

        # instantiate a TaylorDiagramConfig object, which holds all
        # the settings from the config files.
        self.config_obj = TaylorDiagramConfig(self.parameters)

        # Read in the input data that is specified in the config file.
        self.input_df = self._read_input_data()

        # Create a list of series objects.
        # Each series object contains all the necessary information for plotting,
        # such as the criteria needed to subset the input dataframe.
        try:
            self.series_list = self._create_series(self.input_df)
        except AttributeError as ae:
            print("Attribute Error encountered while creating a Taylor series object")

        # create figure
        # pylint:disable=assignment-from-no-return
        # Need to have a self.figure that we can pass along to
        # the methods in base_plot.py (BasePlot class methods) to
        # create binary versions of the plot.
        try:
            self.figure = self._create_figure()
        except AttributeError as ae:
            print("Attribute Error encountered when creating figure.")
        except ValueError:
            print("Value Error encountered when creating figure.")


    def _read_input_data(self) -> pd.DataFrame:
        """

            Args:

            Returns:
                 pandas dataframe representation of the data generated by the MET stat tool.
        """

        df_full: pd.DataFrame = \
            pd.read_csv(self.config_obj.stat_input, sep='\t', header='infer')

        # Remove any columns that are entirely 'NaN'/'NA' this will be helpful
        # in determining whether we have aggregated statistics (stat_btcl and
        # stat_btcu columns with valid values), or not (stat_ncl and
        # stat_ncu with valid values).
        df = df_full.dropna(axis=1, how="all")
        return df


    def _create_series(self, input_df: pandas.DataFrame) -> list:
        """
           Generate all the series objects that are to be plotted.  Each series corresponds to
           a permutation of all the series_val_1 variables.

           Args:

               @param input_df:  pandas dataframe representation of the input data that was created
                                 by MET.

           Returns:
               a list of series objects (as named tuples) that represent the values to be plotted.


        """
        series_list = []

        # use the list of series ordering values to determine how many series objects we need.
        num_series = self.config_obj.calculate_number_of_series()

        for i, series in enumerate(range(num_series)):
            # Create a TaylorDiagramSeries object
            series_obj = TaylorDiagramSeries(self.config_obj, i, self.input_df)
            series_list.append(series_obj)
        return series_list

    def _create_figure(self) -> None:
        """
           Generate a Taylor diagram in Matplotlib, using the code from
           Yannick Copin <yannick.copin@laposte.net>:
           https://gist.github.com/ycopin/3342888

           Plot the normalized OSTDEV and PR_CORR values from output created by MET.

           Args:

           Returns:

        """

        # value of the reference standard deviation,etc.
        # use these values as we are normalizing the standard deviation.
        refstd = 1.0
        stdev_min = 0
        radmax = 1.5
        stdev_max = radmax * refstd
        # stdev_range = (stdev_min, stdev_max)

        fig = plt.figure(figsize=(self.config_obj.plot_width, self.config_obj.plot_height))

        tr = PolarAxes.PolarTransform()

        # Correlation labels
        rlocs = np.array([0, 0.2, 0.4, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99, 1])

        # Create diagram of positive correlations
        pos_correlation_only = self.config_obj.values_of_corr
        if pos_correlation_only:
            # positive correlation only
            tick_max = np.pi / 2
        else:
            # create diagram of positive and negative correlations
            tick_max = np.pi
            rlocs = np.concatenate((-rlocs[:0:-1], rlocs))

        # Convert to polar angles
        tick_locations: numpy.array = np.arccos(rlocs)
        # positions
        gl1 = gf.FixedLocator(tick_locations)
        tf1 = gf.DictFormatter(dict(zip(tick_locations, map(str, rlocs))))

        # Standard deviation axis exent, in units of reference stddev

        # DEBUG
        # stdev_min: float = stdev_range[0] * refstd
        # stdev_max: float = stdev_range[1] * refstd
        stdev_min: float = stdev_min * refstd
        stdev_max: float = stdev_max* refstd

        ghelper = fa.GridHelperCurveLinear(
            tr,
            extremes=(0, tick_max, stdev_min, stdev_max),
            grid_locator1=gl1, tick_formatter1=tf1)

        rect = 111
        ax = fa.FloatingSubplot(fig, rect, grid_helper=ghelper)
        fig.add_subplot(ax)

        #
        # Adjust axes
        #

        # Angle axis
        ax.axis["top"].set_axis_direction("bottom")
        ax.axis["top"].toggle(ticklabels=True, label=True)
        ax.axis["top"].major_ticklabels.set_axis_direction("top")
        ax.axis["top"].label.set_axis_direction("top")
        ax.axis["top"].label.set_text("Correlation")

        # X axis
        ax.axis["left"].set_axis_direction("bottom")
        ax.axis["left"].label.set_text("Standard deviation")

        # Y axis
        ax.axis["right"].set_axis_direction("top")
        ax.axis["right"].toggle(ticklabels=True)
        ax.axis["right"].major_ticklabels.set_axis_direction(
            "bottom")
        ax.axis["right"].label.set_text("Standard deviation")
        ax.axis["bottom"].toggle(ticklabels=False, label=False)

        # Graphical axes
        self._ax = ax
        # Polar coordinates
        self.ax = ax.get_aux_axes(tr)

        # Add a grid of the standard deviation rays
        self._ax.grid(True, color='blue', ls=":")

        # Add reference point and stddev contour
        l, = self.ax.plot([0], refstd, marker='o', color="black", markerfacecolor="none", markersize=5, ls=':', label='_')
        t = np.linspace(0, tick_max)
        r = np.zeros_like(t) + refstd
        self.ax.plot(t, r, 'k--', label='_')

        # add RMSE contours
        rs, ts = np.meshgrid(np.linspace(stdev_min, stdev_max), np.linspace(0, tick_max))

        # compute centered RMS difference
        rms = np.sqrt(refstd ** 2 + rs ** 2 - 2 * refstd * rs * np.cos(ts))
        levels = 5

        if self.config_obj.show_gamma:
            contours = self.ax.contour(ts, rs, rms, levels, colors="#cccccc", linestyles='-', alpha=0.9)
            self.ax.clabel(contours, inline=True, fontsize=8, fmt='%.1f', colors='k')

        for i, series in enumerate(self.series_list):

            # normalize the OSTDEV: ostdev/fstdev
            stdev = series.series_points.fstdev / series.series_points.ostdev
            correlation = series.series_points.pr_corr
            marker = self.config_obj.marker_list[i]
            marker_colors = self.config_obj.colors_list[i]

            # Only plot this series if plot_disp setting is True
            legend = self.config_obj.user_legends[i]
            if self.config_obj.plot_disp[i]:
                self.ax.plot(np.arccos(correlation), stdev, marker=marker, ms=10, ls='',
                             color=marker_colors, label=legend)

        # use FontProperties to re-create the weights used in METviewer
        fontobj = FontProperties()
        font_title = fontobj.copy()
        font_title.set_size(self.config_obj.title_size)
        style = self.config_obj.title_weight[0]
        wt = self.config_obj.title_weight[1]
        font_title.set_style(style)
        font_title.set_weight(wt)

        plt.title(self.config_obj.title,
                      fontproperties=font_title,
                      color=constants.DEFAULT_TITLE_COLOR,
                      pad=28)

        # Plot the caption, leverage FontProperties to re-create the 'weights' menu in
        # METviewer (i.e. use a combination of style and weight to create the bold italic
        # caption weight in METviewer)
        fontobj = FontProperties()
        font = fontobj.copy()
        font.set_size(self.config_obj.caption_size)
        style = self.config_obj.caption_weight[0]
        wt = self.config_obj.caption_weight[1]
        font.set_style(style)
        font.set_weight(wt)
        plt.figtext(self.config_obj.caption_align, self.config_obj.caption_offset, self.config_obj.plot_caption,
                    fontproperties=font, color=self.config_obj.caption_color)

        # Add a figure legend

        # Make some adjustments to the legend box for METviewer default settings when show_gamma is set to
        # False and only positive correlations are to be shown.
        # The default in METviewer for the y-offset of the bbox is y=-0.25 and when y=-.1,
        # the legend box remains in the plot. An adjustment was alread made: y = default y_offset + 0.15
        # in the taylor_diagram_config.py script.  Add another 0.2 to get the bbox y offset value to .1
        if self.config_obj.values_of_corr is False:
            bbox_y = self.config_obj.bbox_y + 0.2
        else:
            bbox_y = self.config_obj.bbox_y
        fig.legend(bbox_to_anchor=(self.config_obj.bbox_x, bbox_y), loc='upper center',
                   ncol=self.config_obj.legend_ncol,
                   prop={'size': self.config_obj.legend_size},
                   frameon=self.config_obj.draw_box)

        plt.tight_layout()
        plt.plot()

        # Save the figure, based on whether we are displaying only positive correlations or all
        # correlations.
        if pos_correlation_only:
            # Setting the bbox_inches keeps the legend box always within the plot boundaries.  This *may* result
            # in a distorted plot.
            plt.savefig(self.config_obj.output_image, dpi=self.config_obj.plot_resolution, bbox_inches="tight")
        else:
            # setting bbox_inches causes a loss in the title, especially when there are numerous legend
            # items.  The legend inset 'y' value will likely need to
            # be modified to keep all legend items on the plot.
            plt.savefig(self.config_obj.output_image, dpi=self.config_obj.plot_resolution)


def main(config_filename=None):
    """
            Generates a sample, default plot using a combination of
            default and custom config files on sample data found in this directory.
            The location of the input data is defined in either the default or
            custom config file.

            Args:
                @param config_filename: default is None, the name of the custom config file to apply
            Returns:

    """

    # Retrieve the contents of the custom config file to over-ride
    # or augment settings defined by the default config file.
    # with open("./custom_taylor_diagram.yaml", 'r') as stream:
    if not config_filename:
        config_file = util.read_config_from_command_line()
    else:
        config_file = config_filename
    with open(config_file, 'r') as stream:
        try:
            docs: dict = yaml.load(stream, Loader=yaml.FullLoader)
        except yaml.YAMLError as exc:
            print(exc)

    try:
        TaylorDiagram(docs)

    except ValueError as value_error:
        print(value_error)


if __name__ == "__main__":
    main()
