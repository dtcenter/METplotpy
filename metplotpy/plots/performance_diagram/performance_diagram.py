
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

    def __repr__(self):
        """ Implement repr which can be useful for debugging this
            class.
        """

        return f'PerformanceDiagram({self.parameters!r})'

    def generate_diagram(self, perf_data):
        '''
        Generate the performance diagram of up to five models with POD and FAR
        values.  Hard-coding of labels for x-axis, y-axis, CSI lines and bias lines, contour colors for the CSI
        curves.


        Args:
            perf_data: A dictionary, keys= POD, SR (Success Rate) values=lists of POD and SR respectively

        Returns:
            Generates a performance diagram with equal lines of CSI (Critical Success Index) and equal lines
            of bias
        '''

        figsize = (9, 8)
        markers = ['.', '*']

        colors = ['r', 'k']
        fig = plt.figure()
        ax1 = fig.add_subplot(111)
        ax2 = ax1.twinx()

        xlabel = "Success Ratio"
        ylabel = "Probability of Detection"

        ticks = np.arange(0.1, 1.1, 0.1)
        dpi = 300
        # csi_cmap = "Blues"
        csi_cmap = "binary"
        csi_label = "Critical Success Index"


        # Retrieve settings from the config file
        title = p.get_title()['text']
        # set the start value to a non-zero number to avoid the runtime divide-by-zero error
        grid_ticks = np.arange(0.000001, 1.01, 0.01)
        sr_g, pod_g = np.meshgrid(grid_ticks, grid_ticks)
        bias = pod_g / sr_g
        csi = 1.0 / (1.0 / sr_g + 1.0 / pod_g - 1.0)
        # CSI lines are filled contour, so that they aren't overwritten by the contour plot lines of the bias
        csi_contour = plt.contourf(sr_g, pod_g, csi, np.arange(0.1, 1.1, 0.1), extend="max", cmap=csi_cmap, alpha=.25)

        # This will get overwritten by the b_contour plot, that's why we need to create a filled contour plot of the CSI
        # lines
        b_contour = plt.contour(sr_g, pod_g, bias, [0.3, 0.5, 0.8, 1, 1.3, 1.5, 2.0, 3.0, 5.0, 10.0], colors="k",
                            linestyles="dashed")

        # original 4 contour lines used by John David Gagne
        # b_contour = plt.contour(sr_g, pod_g, bias, [0.5, 1, 1.5, 2, 4], colors="k", linestyles="dashed")

        # coordinate location of where to put the label for the equal bias contour lines
        plt.clabel(b_contour, fmt="%1.1f",fontsize=6,
                   manual=[(0.9, 0.225), (0.97, 0.415), (0.9, 0.7), (0.7, 0.7), (0.6, 0.9), (0.7, 0.9), (0, 1.), (0, 2.0),
                           (0., 5), (0.1, 10.)])

        # Original locations used by John David Gagne
        # plt.clabel(b_contour, fmt="%1.1f", manual=[(0.2, 0.9), (0.4, 0.9), (0.6, 0.9), (0.7, 0.7)])

        # Optional: plot the legend for the contour lines representing the
        # equal lines of CSI.
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
        legend_params = dict(loc=4, fontsize=7, framealpha=.8, frameon=True)
        plt.legend(**legend_params)
        # plt.figure(figsize=figsize)
        sr_array = perf_data['SR']
        pod_array = perf_data['POD']

        plt.plot(sr_array, pod_array, linestyle = '--', marker=".", color='r', label="Model A", alpha=0.5)
        # ax2.legend(bbox_to_anchor=(0., -.12, 1., -.12), loc='lower left', mode='expand',  borderaxespad=0., ncol=5)
        ax2.legend(bbox_to_anchor=(0, -.14, 1,-.14), loc='lower left', mode='expand',  borderaxespad=0., ncol=5)
        ax1.xaxis.set_label_coords(-0.01, -0.02)
        ax1.set_xlabel(xlabel, fontsize=9)
        ax1.set_ylabel(ylabel, fontsize=9)
        plt.savefig(self.output_file)
        plt.show()

def generate_random_data(n):
    ''' return a list of dictionaries containing the Performance data:
        perf_data[i] = {'SUCCESS_RATIO': .xyz, 'POD': .lmn}
        Where the success ratio=1- FAR

        Args:
            n:  The number of POD, Success ratio performance point "pairs"
        Returns:
            perf_data: A list of POD and FAR values represented as a dictionary
    '''

    sr_data = []
    pod_data = []
    # create n-sets of POD, FAR dataset
    far = np.random.randint(size=n, low=1, high=9)
    np.random.seed(seed=234)
    pod = np.random.randint(size=n, low=1, high=9)

    # Realistic values are between 0 and 1.0 let's multiply each value by 0.1
    pod_values = [x*.01 for x in pod]

    # success ratio, 1-FAR; multiply each FAR value by 0.1 then do arithmetic
    # to convert to the success ratio
    success_ratio = [1-x*0.1 for x in far]

    perf_data = {}
    for i in range(n):

        pod_data.append(pod_values[i])
        sr_data.append(success_ratio[i])

    perf_data['SR'] = sr_data
    perf_data['POD'] = pod_data
    return perf_data

def get_parameters():
    ''' Temporary function to return parameters (configuration values)
        needed to generate the performance diagram.

        Args:

        Returns:
            params:  a dictionary that contains the keywords and their corresponding values
                     representing the user's settings for the performance diagram
    '''

    params = {}
    params['title'] = "Example performance diagram"

    return params

if __name__ == "__main__":

    # number of POD, 1-FAR
    num = 5
    perf_dict = generate_random_data(num)

    # Retrieve the contents of the custom config file to over-ride
    # or augment settings defined by the default config file.
    with open("./custom_performance_diagram.yaml", 'r') as stream:
        try:
            docs = yaml.load(stream, Loader=yaml.FullLoader)
        except yaml.YAMLError as exc:
            print(exc)

    try:
      p = PerformanceDiagram(docs)
      p.generate_diagram(perf_dict)
    except ValueError as ve:
        print(ve)

