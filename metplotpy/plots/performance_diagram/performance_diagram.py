"""
Class Name: performance_diagram.py
 """
__author__ = 'Minna Win'
__email__ = 'met_help@ucar.edu'
import os
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm
from matplotlib.colors import LinearSegmentedColormap
import numpy as np
import yaml
import pandas as pd
from plots.met_plot import MetPlot
import metcalcpy.util.utils as calc_util
from performance_diagram_config import PerformanceDiagramConfig
from performance_diagram_series import PerformanceDiagramSeries
import plots.util as util
import plots.constants as constants


class PerformanceDiagram(MetPlot):
    """  Generates a performance diagram (multi-line line plot)
         where each line represents a series of Success ratio vs POD
         A series represents a model paired with a vx_masking region.

         A setting is over-ridden in the default configuration file if
         it is defined in the custom configuration file.


        To use:
        >>>
        >>> perf_diag = PerformanceDiagram(None)

    """

    def __init__(self, parameters):
        """ Creates a line plot consisting of one or more lines (traces), based on
            settings indicated by parameters.

            Args:
            @param parameters: dictionary containing user defined parameters

        """

        default_conf_filename = "performance_diagram_defaults.yaml"

        # init common layout
        super().__init__(parameters, default_conf_filename)

        # instantiate a PerformanceDiagramConfig object, which holds all the necessary settings from the
        # config file.
        self.config_obj = PerformanceDiagramConfig(self.parameters)

        # Read in input data, location specified in config file
        self.input_df = self._read_input_data()

        # Apply event equalization, if requested
        if self.config_obj.use_ee:
            self.input_df = calc_util.perform_event_equalization(self.parameters, self.input_df)

        # Create a list of series objects.
        # Each series object contains all the necessary information for plotting,
        # such as line color, marker symbol,
        # line width, and criteria needed to subset the input dataframe.
        self.series_list = self._create_series(self.input_df)

        # create figure
        # pylint:disable=assignment-from-no-return
        # Need to have a self.figure that we can pass along to
        # the methods in met_plot.py (MetPlot class methods) to
        # create binary versions of the plot.
        self.figure = self._create_figure()


    def _read_input_data(self):
        """
            Read in the input data as set in the config file as stat_input as a pandas dataframe.

            Args:

            Return:
                 the pandas dataframe representation of the input data file

        """
        return pd.read_csv(self.config_obj.stat_input, sep='\t', header='infer')

    def _create_series(self, input_data):
        """
           Generate all the series objects that are to be displayed as specified by the plot_disp
           setting in the config file.  The points are all ordered by datetime.  Each series object
           is represented by a line in the performance diagram, so they also contain information
           for line width, line- and marker-colors, line style, and other plot-related/
           appearance-related settings (which were defined in the config file).

           Args:
               input_data:  The input data in the form of a Pandas dataframe.
                            This data will be subset to reflect the series data of interest.

           Returns:
               a list of series objects that are to be displayed


        """
        series_list = []

        # use the list of series ordering values to determine how many series objects we need.
        num_series = len(self.config_obj.series_ordering)

        for i, series in enumerate(range(num_series)):
            # Create a PerformanceDiagramSeries object
            series_obj = PerformanceDiagramSeries(self.config_obj, i, input_data)
            series_list.append(series_obj)
        return series_list

    def save_to_file(self):
        """
          This is the matplotlib-friendly implementation, which overrides the parent class'
          version (which is a Python Plotly implementation).

        """
        plt.savefig(self.config_obj.output_image)

    def remove_file(self):
        """
           Removes previously made image file .  Invoked by the parent class before self.output_file
           attribute can be created.
        """

        image_name = self.get_config_value('plot_output')

        # remove the old file if it exist
        if os.path.exists(image_name):
            os.remove(image_name)

    def show_in_browser(self):
        """***NOTE***: This method is required for implementation in plotly.
           In a plotly implementation, this creates a plot and opens it in the browser.

                 Args:

                 Returns:

                 """
        if self.figure:
            self.figure.show()
        else:
            print("Matplotlib implementation of this plot, this plot won't be visible in browser.")

    def _create_figure(self):
        """
        Generate the performance diagram of varying number of series with POD and 1-FAR
        (Success Rate) values.  Hard-coding of labels for CSI lines and bias lines,
        and contour colors for the CSI curves.


        Args:


        Returns:
            Generates a performance diagram with equal lines of CSI (Critical Success Index)
            and equal lines of bias
        """

        # This creates a figure size that is of a "reasonable" size
        fig = plt.figure(figsize=[8.5, 8])

        #
        # PLOT THE "TEMPLATE" THAT CREATES THE EQUAL LINES OF CSI AND EQUAL LINES OF BIAS
        # THAT COMPRISE THE PERFORMANCE DIAGRAM
        #

        # add an extra y-axis to indicate tick marks for the equal lines of CSI
        ax1 = fig.add_subplot(111)
        ax2 = ax1.twinx()
        ax1.set_xlim([0, 1])
        ax1.set_ylim([0, 1])
        ax2.set_xlim([0, 1])
        ax2.set_ylim([0, 1])

        # Using Logan Dawson's template for the performance diagram, which is
        # easier to read and maintain than the previous implementation.
        x_axis = y_axis = np.arange(0.01, 1.01, 0.01)
        x_mesh, y_mesh = np.meshgrid(x_axis, y_axis)
        bounds = np.arange(0, 1.10, 0.10)
        BoundaryNorm(bounds, len(bounds))
        colors = ['#ffffff', '#f0f0f0', '#e3e3e3', '#d6d6d6', '#c9c9c9', '#bdbdbd', '#b0b0b0',
                  '#a3a3a3', '#969696', '#8a8a8a']
        colormap = LinearSegmentedColormap.from_list('percentdiff_cbar', colors, N=len(bounds))

        csi = ((1 / x_mesh) + (1 / y_mesh) - 1) ** -1
        cs_var = ax1.contourf(x_mesh, y_mesh, csi, np.arange(0.0, 1.1, 0.1), cmap=colormap)
        csi_label = "Critical Success Index"

        biases = [0.1, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 4.0, 10.0]
        bias_loc_x = [0.94, 0.935, 0.94, 0.935, 0.9, 0.58, 0.42, 0.18, 0.03]
        bias_loc_y = [0.12, 0.2625, 0.5, 0.74, 0.95, 0.95, 0.95, 0.95, 0.95]

        bias = y_mesh / x_mesh
        ax1.contour(x_mesh, y_mesh, bias, biases, colors='black', linestyles='--')

        for i, j in enumerate(biases):
            ax1.annotate(j, (bias_loc_x[i], bias_loc_y[i]), fontsize=12)

        # Format the underlying performance diagram axes, labels, equal lines of CSI,
        # equal lines of bias.
        xlabel = self.config_obj.xaxis
        ylabel = self.config_obj.yaxis_1

        # From original implementation, replace this with Logan's for now
        # Optional: plot the legend for the contour lines representing the
        # equal lines of CSI.
        #
        plot_contour_legend = self.config_obj.plot_contour_legend
        if plot_contour_legend:
            cbar = plt.colorbar(cs_var)
            cbar.set_label(csi_label, fontsize=9)

        plt.title(self.config_obj.title, fontsize=constants.DEFAULT_TITLE_FONTSIZE,
                  color=constants.DEFAULT_TITLE_COLOR, fontweight="bold",
                  fontfamily=constants.DEFAULT_TITLE_FONT)

        #
        # PLOT THE STATISTICS DATA FOR EACH line/SERIES (i.e. GENERATE THE LINES ON THE
        # the statistics data for each model/series
        #
        for i, series in enumerate(self.series_list):
            # Don't generate the plot for this series if
            # it isn't requested (as set in the config file)
            if series.plot_disp:
                pody_points = series.series_points[1]
                sr_points = series.series_points[0]
                plt.plot(sr_points, pody_points, linestyle=series.linestyle,
                         linewidth=series.linewidth,
                         color=series.color, marker=series.marker,
                         label=series.user_legends,
                         alpha=0.5, ms=3)

                # Annotate the points with their PODY (i.e. dependent variable value)
                if not self.config_obj.anno_var :
                    pass
                elif self.config_obj.anno_var == 'y':
                    for idx, pody in enumerate(pody_points):
                        plt.annotate(str(pody) + self.config_obj.anno_units,
                                    (sr_points[idx], pody_points[idx]), fontsize=9)
                elif self.config_obj.anno_var == 'x':
                    for idx, succ_ratio in enumerate(sr_points):
                        plt.annotate(str(succ_ratio) + self.config_obj.anno_units,
                                    (sr_points[idx], pody_points[idx]), fontsize=9)

                # Plot error bars if they were requested:
                if self.config_obj.plot_ci[i] != "NONE":
                    pody_errs = series.series_points[2]
                    plt.errorbar(sr_points, pody_points, yerr=pody_errs,
                                 color=series.color, ecolor="black", ms=1, capsize=2)

        # example settings, legend is outside of plot along the bottom
        # ax2.legend(bbox_to_anchor=(0, -.14, 1, -.14), loc='lower left', mode='expand',
        #            borderaxespad=0., ncol=5, prop={'size': 6}, fancybox=True)

        # Legend based on the style settings in the config file.
        ax2.legend(bbox_to_anchor=(self.config_obj.bbox_x, self.config_obj.bbox_y), loc='lower left',
                               ncol=self.config_obj.legend_ncol,
                   prop={'size': self.config_obj.legend_size})
        ax1.xaxis.set_label_coords(0.5, -0.066)
        ax1.set_xlabel(xlabel, fontsize=9)
        ax1.set_ylabel(ylabel, fontsize=9)
        if self.config_obj.yaxis_2:
            ax2.set_ylabel(self.config_obj.yaxis_2, fontsize=9)

        plt.savefig(self.get_config_value('plot_output'))
        # plt.show()
        self.save_to_file()


def main():
    """
            Generates a sample, default, line plot using a combination of
            default and custom config files on sample data found in this directory.
            The location of the input data is defined in either the default or
            custom config file.
    """

    # Retrieve the contents of the custom config file to over-ride
    # or augment settings defined by the default config file.
    # with open("./custom_performance_diagram.yaml", 'r') as stream:
    config_file = util.read_config_from_command_line()
    with open(config_file, 'r') as stream:
        try:
            docs = yaml.load(stream, Loader=yaml.FullLoader)
        except yaml.YAMLError as exc:
            print(exc)

    try:
        # create a performance diagram
        PerformanceDiagram(docs)

    except ValueError as value_error:
        print(value_error)


if __name__ == "__main__":
    main()
