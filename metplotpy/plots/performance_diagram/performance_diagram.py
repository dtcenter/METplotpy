"""
Class Name: performance_diagram.py
 """
__author__ = 'Minna Win'
__email__ = 'met_help@ucar.edu'
import matplotlib.pyplot as plt
import numpy as np
import itertools
import yaml
import os
import pandas as pd
from plots.met_plot import MetPlot
from config import Config
from series import Series



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

        # instantiate a Config object, which holds all the necessary settings from the
        # config file.
        self.config_obj = Config(parameters)

        # Read in input data, location specified in config file
        self.input_df = self.read_input_data()

        # Create a list of series objects.
        # Each series object contains all the necessary information for plotting, such as line color, marker symbol,
        # line width, and criteria needed to subset the input dataframe.
        self.series_list = self._create_series(self.input_df)

        # create figure
        # pylint:disable=assignment-from-no-return
        # Need to have a self.figure that we can pass along to
        # the methods in met_plot.py (MetPlot class methods) to
        # create binary versions of the plot.
        self.figure = self._create_figure()

    def __repr__(self):
        """ Implement repr which can be useful for debugging this
            class.
        """

        return f'PerformanceDiagram({self.parameters!r})'


    def _get_indy_variable(self):
        """
           Retrieve the independent variable of interest such as fcst_valid_beg or fcst_init_beg


           Returns:
               value of the indy_var
        """
        return self.get_config_value('indy_var')

    def _get_fcst_vars(self):
        """
           Retrieve the independent and dependent statistics variables (ie statistic for x-axis, and statistic
           for the y-axis).  In this case, this should be PODY for dependent statistic variable, and FAR as the
           independent statistic variable, which is used to calculate the Success Ratio (1-FAR).

           Returns:
               stat_var_indy and stat_var_dep: the independent statistics variable (x-axis) and the
                                               dependent statistics variable (y-axis)
        """

        # retrieve the independent and dependent variables set in the configuration file under the fcst_var_val key.
        fcst_var_dict = self.parameters['fcst_var_val']
        fcst_vars = list(fcst_var_dict.values())
        # We retrieve the first key of the fctst_var_val dictionary, since we don't know the name of the key
        indy_var = fcst_vars[0][0]
        dep_var = fcst_vars[0][1]

        return indy_var, dep_var

    def _get_indy_values(self):
        """
           Retrieve the list of datetimes (independent values) that are used to create the series data

           Args:

           Returns:
                a list of the datetimes of interest as strings
        """
        return self.parameters['indy_vals']

    def _get_output_file(self):
        """
            Retrieve the name and path for the output file (output plot).

            Args:

            Returns:
                the path and filename of the output plot
        """
        return self.get_config_value('plot_output')

    def read_input_data(self):
        """
            Read in the input data as set in the config file as stat_input as a pandas dataframe.

            Args:

            Return:
                 the pandas dataframe representation of the input data file

        """
        return pd.read_csv(self.config_obj.stat_input, sep='\t', header='infer')

    def _create_series(self, input_data):
        """
           Generate all the series objects that are to be displayed as specified by the plot_disp setting in the config
           file.  The points are all ordered by datetime.  Each series object is represented by a line in the
           performance diagram, so they also contain information for line width, line- and marker-colors,
           line style, and other plot-related/appearance-related settings (which were defined in the config file).

           Args:
               input_data:  The input data in the form of a Pandas dataframe.  This data will be subset to
                          reflect the series data of interest.

           Returns:
               a list of series objects that are to be displayed


        """
        series_list = []

        # use the list of series ordering values to determine how many series objects we need.
        num_series = len(self.config_obj.series_ordering)

        for i, series in enumerate(range(num_series)):
            # Check if this series is to be displayed (i.e. plot_disp is set to True)
            if self.config_obj.plot_disp[series]:
                # Create a Series object
                # idx = self.config_obj.series_ordering_zb[i]
                series_obj = Series(self.config_obj, i, input_data)
                series_list.append(series_obj)
        return series_list

    def save_to_file(self):
        """
          This is the matplotlib-friendly implementation, which overrides the parent class'
          version (which is a Python Plotly implementation).

        """
        plt.savefig(self.output_file)

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
           In a plotly implrmentation, this creates a plot and opens it in the browser.

                 Args:

                 Returns:

                 """
        if self.figure:
            self.figure.show()
        else:
            #
            print("Matplotlib implementation of this plot, this plot won't be visable in browser.")

    def _create_figure(self):
        """
        Generate the performance diagram of varying number of series with POD and 1-FAR (Success Rate)
        values.  Hard-coding of labels for CSI lines and bias lines, and contour colors for the CSI
        curves.


        Args:


        Returns:
            Generates a performance diagram with equal lines of CSI (Critical Success Index) and equal lines
            of bias
        """

        fig = plt.figure()

        #
        # PLOT THE "TEMPLATE" THAT CREATES THE EQUAL LINES OF CSI AND EQUAL LINES OF BIAS
        # THAT COMPRISE THE PERFORMANCE DIAGRAM
        #

        # add an extra y-axis to indicate tick marks for the equal lines of CSI
        ax1 = fig.add_subplot(111)
        ax2 = ax1.twinx()

        # Use the numpy meshgrid to assist in generating the equal lines of BIAS and CSI, based on
        # David John Gagne's approach: https://gist.github.com/djgagne/64516e3ea268ec31fb34
        ticks = np.arange(0.1, 1.1, 0.1)

        # use a grayscale color map for the filled contour
        csi_cmap = "binary"

        # set the start value to a miniscule, non-zero number to avoid the runtime divide-by-zero error
        grid_ticks = np.arange(0.000001, 1.01, 0.01)

        sr_g, pod_g = np.meshgrid(grid_ticks, grid_ticks)
        bias = pod_g / sr_g
        csi = 1.0 / (1.0 / sr_g + 1.0 / pod_g - 1.0)
        csi_label = "Critical Success Index"

        # CSI lines are filled contour lines
        csi_contour = ax1.contourf(sr_g, pod_g, csi, np.arange(0.1, 1.1, 0.1), extend="max", cmap=csi_cmap, alpha=.25)

        # The equal lines of CSI are represented by ordinary contour lines
        bias_contour = ax1.contour(sr_g, pod_g, bias, [0.3, 0.5, 0.8, 1, 1.3, 1.5, 2.0, 3.0, 5.0, 10.0], colors="k",
                                linestyles="dashed")

        # coordinate location of where to put the label for the equal bias contour lines, since we haven't
        # created a second x-axis (at the top of the plot)
        plt.clabel(bias_contour, fmt="%1.1f", fontsize=6,
                   manual=[(0.9, 0.225), (0.97, 0.415), (0.9, 0.7), (0.7, 0.7), (0.6, 0.9), (0.7, 0.9), (0, 1.),
                           (0, 2.0),
                           (0., 5), (0.1, 10.)])

        #
        # RETRIEVE SETTINGS FROM THE CONFIG FILE
        #

        # Format the underlying performance diagram axes, labels, equal lines of CSI, equal lines of bias.
        # xlabel = "Success Ratio (1-FAR)"
        # ylabel = "Probability of Detection"
        xlabel = self.config_obj.xaxis
        ylabel = self.config_obj.yaxis

        #
        # Optional: plot the legend for the contour lines representing the
        # equal lines of CSI.
        #
        plot_contour_legend = self.config_obj.plot_contour_legend
        if plot_contour_legend:
            cbar = plt.colorbar(csi_contour)
            cbar.set_label(csi_label, fontsize=9)
        else:
            ax2.set_ylabel(csi_label, fontsize=9)

        plt.xticks(ticks)
        plt.yticks(ticks)
        plt.title(self.config_obj.title, fontsize=self.config_obj.DEFAULT_TITLE_FONTSIZE, color=self.config_obj.DEFAULT_TITLE_COLOR, fontweight="bold", fontfamily=self.config_obj.DEFAULT_TITLE_FONT)
        # plt.text(0.48, 0.6, "Frequency Bias", fontdict=dict(fontsize=8, rotation=45), alpha=.3)

        #
        # PLOT THE STATISTICS DATA FOR EACH line/SERIES (i.e. GENERATE THE LINES ON THE  the statistics data for each model/series
        #
        for idx, series in enumerate(self.series_list):
            pody_points = series.series_points[1]
            sr_points = series.series_points[0]
            # plt.plot(sr_points, pody_points, linestyle=series.linestyle, linewidth=series.linewidth, marker=series.marker,
            #          color=series.color, label=series.user_legends, alpha=0.5)
            plt.plot(sr_points, pody_points, linestyle=series.linestyle, linewidth=series.linewidth,
                     color=series.color, label=series.user_legends, alpha=0.5)
            plt.plot(sr_points, pody_points, marker=series.marker,
                      color=series.color)

            # Annotate the points with their PODY (i.e. dependent variable value)
            if self.config_obj.anno_var == 'y':
                for idx, pody in enumerate(pody_points):
                    plt.annotate(str(pody) + self.config_obj.anno_units, (sr_points[idx], pody_points[idx]), fontsize=10)
            elif self.config_obj.anno_var == 'x':
                for idx, sr in enumerate(sr_points):
                    plt.annotate(str(sr) + self.config_obj.anno_units, (sr_points[idx], pody_points[idx]), fontsize=10)



            ax2.legend(bbox_to_anchor=(0, -.14, 1, -.14), loc='lower left', mode='expand', borderaxespad=0., ncol=5,
                       prop={'size': 6})
            ax1.xaxis.set_label_coords(0.5, -0.066)
            ax1.set_xlabel(xlabel, fontsize=9)
            ax1.set_ylabel(ylabel, fontsize=9)
            # print(f"****Number of series: {(data['POD'][0])}")
        ax2.legend(bbox_to_anchor=(0, -.14, 1, -.14), loc='lower left', mode='expand', borderaxespad=0., ncol=5,
                                  prop={'size': 6})
        ax1.xaxis.set_label_coords(0.5, -0.066)
        ax1.set_xlabel(xlabel, fontsize=9)
        ax1.set_ylabel(ylabel, fontsize=9)
        plt.savefig(self.get_config_value('plot_output'))
        plt.show()
        # self.save_to_file()


    def save_to_file(self):
        """ Save plot as file in directory as specified in default or custom config file."""
        print(f"saving file as {self.output_image}")






def main():
    """
            Generates a sample, default, two-trace line plot using a combination of
            default and custom config files on sample data found in this directory.
            The location of the input data is defined in either the default or
            custom config file.
        """

    # Retrieve the contents of the custom config file to over-ride
    # or augment settings defined by the default config file.
    # with open("./custom_performance_diagram.yaml", 'r') as stream:
    with open("../config/performance_diagram_defaults.yaml", 'r') as stream:
        try:
            docs = yaml.load(stream, Loader=yaml.FullLoader)
        except yaml.YAMLError as exc:
            print(exc)


    try:
        # create a performance diagram
        pd = PerformanceDiagram(docs)

    except ValueError as ve:
        print(ve)



if __name__ == "__main__":

    main()
