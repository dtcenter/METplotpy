"""
Class Name: taylor_diagram.py
 """
__author__ = 'Minna Win'

import matplotlib.pyplot as plt
from matplotlib.projections import PolarAxes
import mpl_toolkits.axisartist.floating_axes as fa
import mpl_toolkits.axisartist.grid_finder as gf
import numpy as np
import yaml
import pandas as pd
import warnings
from plots.base_plot import BasePlot
import plots.util as util
from taylor_diagram_config import TaylorDiagramConfig

warnings.filterwarnings("ignore", category=DeprecationWarning)

class TaylorDiagram(BasePlot):
    """  Generates a Taylor diagram
         A setting is over-ridden in the default configuration file if
         it is defined in the custom configuration file.

    """

    def __init__(self, parameters:dict) -> None:
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

        # create figure
        # pylint:disable=assignment-from-no-return
        # Need to have a self.figure that we can pass along to
        # the methods in base_plot.py (BasePlot class methods) to
        # create binary versions of the plot.
        self.figure = self._create_figure()

    def _read_input_data(self) -> pd.DataFrame:
        """

            Args:

            Returns:
                 None
        """

        df_full = pd.read_csv(self.config_obj.stat_input, sep='\t', header='infer')

        # Remove any columns that are entirely 'NaN' this will be helpful
        # in determining whether we have aggregated statistics (stat_bcl and
        # stat_bcu columns with valid values), or not (stat_ncl and
        # stat_ncu with valid values).
        df = df_full.dropna(axis=1, how="all")
        return df

    def _create_figure(self) -> None:
        """
           Generate a Taylor diagram in Matplotlib, using the code created from
           Yannick Copin <yannick.copin@laposte.net>:
           https://gist.github.com/ycopin/3342888

           Args:

           Returns:

        """

        tr = PolarAxes.PolarTransform()

        # value of the reference standard deviation
        refstd = 1.0
        srange = (0, 1.5)

        # Correlation labels
        rlocs = np.array([0, 0.2, 0.4, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99, 1])

        # Create diagram of positive correlations
        pos_correlation_only = self.config_obj.values_of_corr
        if pos_correlation_only:
            tmax = np.pi/2
        else:
            # create diagram of positive and negative correlations
            tmax = np.pi
            rlocs = np.concatenate((-rlocs[:0:-1], rlocs))

        # Convert to polar angles
        tlocs = np.arccos(rlocs)
        gl1 = gf.FixedLocator(tlocs)
        tf1 = gf.DictFormatter(dict(zip(tlocs, map(str, rlocs))))

        # Standard deviation axis exent, in units of reference stddev
        smin = srange[0] * refstd
        smax = srange[1] * refstd

        ghelper = fa.GridHelperCurveLinear(
            tr,
            extremes=(0, tmax, smin, smax),
            grid_locator1=gl1, tick_formatter1=tf1)

        fig = plt.figure()
        rect = 111
        ax = fa.FloatingSubplot(fig, rect, grid_helper=ghelper)
        fig.add_subplot(ax)

        # Add a grid of the standard deviation arcs
        ax.grid(True, color='blue', ls=":")

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
            "bottom" if pos_correlation_only else "left")

        if smin:
            ax.axis["bottom"].toggle(ticklabels=False, label=False)
        else:
            # unused
            ax.axis["bottom"].set_visible(False)

        # Graphical axes, polar coordinates
        ax = ax.get_aux_axes(tr)

        # Add reference point and stddev contour
        l, = ax.plot([0], refstd, marker='o', color="black", markerfacecolor="none", markersize=5, ls=':', label='_')
        t = np.linspace(0, tmax)
        r = np.zeros_like(t) + refstd
        ax.plot(t, r, 'k--', label='_')

        # add contours
        rs, ts = np.meshgrid(np.linspace(smin, smax), np.linspace(0, tmax))

        # compute centered RMS difference
        rms = np.sqrt(refstd**2 + rs**2 - 2*refstd*rs*np.cos(ts))
        levels = 5
        contours = ax.contour(ts, rs, rms, levels, colors='darkgreen', linestyles=':', alpha=0.9)
        ax.clabel(contours, inline=True, fontsize=8, fmt='%.1f', colors='k')

        # standard deviation lines
        draw_gamma = self.config_obj.show_gamma
        if draw_gamma:
            # draw the standard deviation lines
            maxsd = 1.5


        plt.plot()
        plt.show()


def main(config_filename=None):
    """
            Generates a sample, default, line plot using a combination of
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
            docs = yaml.load(stream, Loader=yaml.FullLoader)
        except yaml.YAMLError as exc:
            print(exc)

    try:
        # create a performance diagram
        TaylorDiagram(docs)

    except ValueError as value_error:
        print(value_error)


if __name__ == "__main__":
    main()
