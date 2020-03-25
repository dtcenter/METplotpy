"""
Class Name: performance_diagram.py
 """
__author__ = 'Minna Win'
__email__ = 'met_help@ucar.edu'
import matplotlib.pyplot as plt
import numpy as np
import yaml
import pandas as pd
from plots.met_plot import MetPlot


class PerformanceDiagram(MetPlot):
    """  Generates a performance diagram (multi line line plot)
             where each line
             A setting is over-ridden in the default configuration file if
             it is defined in the custom configuration file.

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

        # create figure
        # pylint:disable=assignment-from-no-return
        # Need to have a self.figure that we can pass along to
        # the methods in met_plot.py (MetPlot class methods) to
        # create binary versions of the plot.
        # self.figure = self._create_figure()

        self.plot_contour_legend = False
        self.output_file = "./performance_diagram.png"
        # NOTE:  Support for only 5 models/series
        self.marker_list = ['.', 'o', '*', '+', 's']
        self.color_list = ['deepskyblue', 'r', 'darkorange', 'g', 'b']

    def __repr__(self):
        """ Implement repr which can be useful for debugging this
            class.
        """

        return f'PerformanceDiagram({self.parameters!r})'

    def get_xaxis_title(self):
        """ Override the method in the parent class, MetPlot, as this is located
            in a different location in the config file.
        """

        return self.parameters['xaxis']['title']

    def get_yaxis_title(self):
        """ Override the method in the parent class, MetPlot, as this is located
            in a different location in the config file.
        """

        return self.parameters['yaxis']['title']

    def show_in_browser(self):
        """For implementation in plotly only:
           Creates a plot and opens it in the browser.

                 Args:

                 Returns:

                 """
        if self.figure:
            self.figure.show()
        else:
            print("Matplotlib implementation of this plot, therefore not viewable in browser.")

    def generate_diagram(self, perf_data):
        '''
        Generate the performance diagram of up to five models with POD and FAR
        values.  Hard-coding of labels for x-axis, y-axis, CSI lines and bias lines, contour colors for the CSI
        curves.


        Args:
            perf_data: A list of dictionaries, with keys=model, POD, SR (Success Rate) values=name of model/series, lists of POD and SR respectively

        Returns:
            Generates a performance diagram with equal lines of CSI (Critical Success Index) and equal lines
            of bias
        '''

        fig = plt.figure()

        #
        # plot the "template" that creates the equal lines of CSI and equal lines of Bias that
        # are characteristic of a performance diagram.
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

        # CSI lines are filled contour, so they won't be overwritten by the contour plot lines of the bias
        csi_contour = ax1.contourf(sr_g, pod_g, csi, np.arange(0.1, 1.1, 0.1), extend="max", cmap=csi_cmap, alpha=.25)

        # The b_contour plot will be plotted on top of the filled contour plot representing the equal lines of CSI
        b_contour = ax1.contour(sr_g, pod_g, bias, [0.3, 0.5, 0.8, 1, 1.3, 1.5, 2.0, 3.0, 5.0, 10.0], colors="k",
                                linestyles="dashed")

        # coordinate location of where to put the label for the equal bias contour lines, since we haven't
        # created a second x-axis (at the top of the plot)
        plt.clabel(b_contour, fmt="%1.1f", fontsize=6,
                   manual=[(0.9, 0.225), (0.97, 0.415), (0.9, 0.7), (0.7, 0.7), (0.6, 0.9), (0.7, 0.9), (0, 1.),
                           (0, 2.0),
                           (0., 5), (0.1, 10.)])

        #
        # Retrieve settings from the config file
        #
        title = self.get_title()['text']

        # Format the underlying performance diagram axes, labels, equal lines of CSI, equal lines of bias.
        xlabel = "Success Ratio (1-FAR)"
        ylabel = "Probability of Detection"
        # xlabel = self.get_x_axis_title()
        # ylabel = self.get_yaxis_title()

        #
        # Optional: plot the legend for the contour lines representing the
        # equal lines of CSI.
        #
        plot_contour_legend = self.plot_contour_legend
        if plot_contour_legend:
            cbar = plt.colorbar(csi_contour)
            cbar.set_label(csi_label, fontsize=9)
        else:
            ax2.set_ylabel(csi_label, fontsize=9)

        plt.xticks(ticks)
        plt.yticks(ticks)
        plt.title(title, fontsize=14, fontweight="bold")
        plt.text(0.48, 0.6, "Frequency Bias", fontdict=dict(fontsize=10, rotation=45), alpha=.5)

        #
        # plot the statistics data for each model/series
        #
        for idx, data in enumerate(perf_data):
            model = data['model']
            sr_array = data['SUCCESS_RATIO']
            pod_array = data['POD']

            # Select the marker and color based on the index of the
            plt.plot(sr_array, pod_array, linestyle='-', marker=self.marker_list[idx], color=self.color_list[idx],
                     label=model, alpha=0.5)
            ax2.legend(bbox_to_anchor=(0, -.14, 1, -.14), loc='lower left', mode='expand', borderaxespad=0., ncol=5,
                       prop={'size': 6})
            ax1.xaxis.set_label_coords(0.5, -0.066)
            ax1.set_xlabel(xlabel, fontsize=9)
            ax1.set_ylabel(ylabel, fontsize=9)
        plt.savefig(self.output_file)
        plt.show()


def generate_sample_data(n, model_names):
    '''


        Args:
            n:  The number of POD, Success ratio performance point "pairs"
            model_names:  A list of model names
        Returns:
            model_stat_data: A list of dictionaries, where the keys are model, SUCCESS_RATE, and POD
    '''

    model_stat_data_list = []
    model_stat_dict = {}

    for i, model in enumerate(model_names):
        # create a list of FAR and POD statistics, consisting of n-points.
        far = np.random.randint(size=n, low=1, high=8)
        np.random.seed(seed=234)
        pod = np.random.randint(size=n, low=1, high=8)

        # Realistic values are between 0 and 1.0 let's multiply each value by 0.1
        if i % 5 == 0:
            pod_values = [x * .05 for x in pod]
        elif i % 4 == 0:
            pod_values = [x * .04 for x in pod]
        elif i % 3 == 0:
            pod_values = [x * .03 for x in pod]
        elif i % 2 == 0:
            pod_values = [x * 0.2 for x in pod]
        else:
            pod_values = [x * 0.01 for x in pod]

        # success ratio, 1-FAR; multiply each FAR value by 0.1 then do arithmetic
        # to convert to the success ratio
        success_ratio = [1 - x * 0.1 for x in far]

        model_stat_dict['model'] = model
        model_stat_dict['SUCCESS_RATIO'] = success_ratio
        model_stat_dict['POD'] = pod_values
        model_stat_data_list.append(model_stat_dict)
        model_stat_dict = {}
    return model_stat_data_list


def main():
    """
            Generates a sample, default, two-trace line plot using a combination of
            default and custom config files on sample data found in this directory.
            The location of the input data is defined in either the default or
            custom config file.
        """

    # Retrieve the contents of the custom config file to over-ride
    # or augment settings defined by the default config file.
    with open("./custom_performance_diagram.yaml", 'r') as stream:
        try:
            docs = yaml.load(stream, Loader=yaml.FullLoader)
        except yaml.YAMLError as exc:
            print(exc)

    try:
        # number of POD, 1-FAR
        num_points = 7
        model_names = ['Model 1', 'Model 2', 'Model 3', 'Series for GFS', 'Series for HRRR']
        perf_dict = generate_sample_data(num_points, model_names)
        pd = PerformanceDiagram(docs)
        pd.generate_diagram(perf_dict)
        pd.save_to_file()
    except ValueError as ve:
        print(ve)


if __name__ == "__main__":
    main()
