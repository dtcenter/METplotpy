"""
Class Name: performance_diagram.py
 """
__author__ = 'Minna Win'
__email__ = 'met_help@ucar.edu'
import matplotlib.pyplot as plt
import numpy as np
import yaml
import metcalcpy
from plots.met_plot import MetPlot


class PerformanceDiagram(MetPlot):
    """  Generates a performance diagram (multi-line line plot)
         where each line represents a model/time series of Success ratio vs POD
         A setting is over-ridden in the default configuration file if
         it is defined in the custom configuration file.


        To use:
        >>> data = generate_sample_data()
        >>> perf_diag = PerformanceDiagram(None, data)

    """

    # Default marker symbols and line colors. Colors can be chosen in config files.  For now, markers are hard-coded.
    # Currently support maximum of five models (lines) in diagram.
    DEFAULT_MARKER_LIST = ['.', 'o', '*', '+', 's']
    DEFAULT_COLOR_LIST = ['deepskyblue', 'red', 'darkorange', 'green', 'blue']
    DEFAULT_LINE_WIDTH = [2,2,2,2,2]
    DEFAULT_TITLE_FONT = 'sans-serif'
    DEFAULT_TITLE_COLOR = 'blue'
    DEFAULT_TITLE_FONTSIZE = 10

    def __init__(self, parameters, data):
        """ Creates a line plot consisting of one or more lines (traces), based on
            settings indicated by parameters.

            Args:
            @param parameters: dictionary containing user defined parameters

        """

        default_conf_filename = "performance_diagram_defaults.yaml"
        # init common layout
        super().__init__(parameters, default_conf_filename)

        self.plot_contour_legend = False
        self.output_file = "./performance_diagram.png"
        self.xaxis = self.get_xaxis_title()
        self.yaxis = self.get_yaxis_title()
        self.title = self.get_title()['text']
        self.title_font = self.DEFAULT_TITLE_FONT
        self.title_color = self.DEFAULT_TITLE_COLOR
        self.model_list = self._get_all_models()
        self.colors_list = self._get_all_colors()
        self.marker_list = self.DEFAULT_MARKER_LIST
        self.linewidth_list = self._get_all_linewidths()

        # create figure
        # pylint:disable=assignment-from-no-return
        # Need to have a self.figure that we can pass along to
        # the methods in met_plot.py (MetPlot class methods) to
        # create binary versions of the plot.
        self.figure = self._create_figure(data)

    def __repr__(self):
        """ Implement repr which can be useful for debugging this
            class.
        """

        return f'PerformanceDiagram({self.parameters!r})'

    def get_data(self):
        """
            Invokes the appropriate file reader from the metcalcpy package.
            Args:
                input_filename:  The name of the input filename to be read

            Return:
                plotting_data:  A list of dictionaries that have keys corresponding to the model/series name, init time, valid time,
                                forecast lead, probability of detection (POD), and false alarm rate (FAR)
        """
        # Invoke method from metcalcpy package to assist in retrieving data
        return []

    def _get_title_font(self):
        """
           Retrieve the font family from a configuration file (either default or custom config file).

           Args:

           Returns:
               title_font:  The name of the font family (string) to be applied to the title

        """
        return self.parameters['title']['font']

    def _get_title_color(self):
        """
           Retrieve the text color for the title from a configuration file (either default or custom config file).

           Args:

           Returns:
               title_color:  The name of the font color (string) to be applied to the title

        """
        return self.parameters['title']['color']


    def _get_all_colors(self):

        """
           Retrieves the colors for lines and markers, from the config file or use the defaults if undefined in config.
           Args:

           Returns:
               colors_list or colors_from_config: a list of the colors to be used for the lines (
               and their corresponding marker symbols)
        """

        lines = self.parameters['lines']
        color_list = []
        for line in lines:
            color_list.append(line['color'])
        if len(color_list) != len(lines) or color_list is None:
            # Not all lines have color (no way to guess what the user intended)
            # or no colors are specified in the config file, use default values
            return self.DEFAULT_COLOR_LIST
        else:
            return color_list


    def _get_all_models(self):
        """
            Get a list of the models specified in the configuration file.

            Args:

            Returns:
                a list of models specified in the default or custom config file.
        """

        lines = self.parameters['lines']
        model_list = []
        for line in lines:
            model_list.append(line['name'])

        return model_list

    def _get_all_linewidths(self):
        """ Retrieve all the linewidths from the configuration file, if not specified in any config file, use
            the default values of 2

            Args:

            Returns:
                linewidth_list: a list of linewidths corresponding to each line (model)
        """

        linewidths_list = []
        lines = self.parameters['lines']
        for line in lines:
            linewidth = line['width']
            linewidths_list.append(linewidth)
        return linewidths_list


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

    def save_to_file(self, plt_obj):
        """
          This is the matplotlib-friendly implementation, which overrides the parent class'
          version (which is a Python Plotly implementation).

        """
        plt_obj.savefig(self.output_file)


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

    def _create_figure(self, perf_data):
        '''
        Generate the performance diagram of up to five models with POD and 1-FAR (Success Rate)
        values.  Hard-coding of labels for CSI lines and bias lines, and contour colors for the CSI
        curves.


        Args:
            perf_data: A list of dictionaries, with keys=model, POD, SR (Success Rate) values=name of model/series, lists of POD and SR respectively

        Returns:
            Generates a performance diagram with equal lines of CSI (Critical Success Index) and equal lines
            of bias
        '''

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
        xlabel = self.xaxis
        ylabel = self.yaxis

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
        plt.title(self.title, fontsize=11, fontweight="bold", fontfamily=self.DEFAULT_TITLE_FONT)
        plt.text(0.48, 0.6, "Frequency Bias", fontdict=dict(fontsize=8, rotation=45), alpha=.3)

        #
        # PLOT THE STATISTICS DATA FOR EACH MODEL/SERIES (i.e. GENERATE THE LINES ON THE  the statistics data for each model/series
        #
        for idx, data in enumerate(perf_data):
            # model = data['model']
            sr_array = data['SUCCESS_RATIO']
            pod_array = data['POD']

            # Select the marker and color based on the index of the
            # plt.plot(sr_array, pod_array, linestyle='-', marker=self.marker_list[idx], color=self.color_list[idx],
            #          label=model, alpha=0.5)
            plt.plot(sr_array, pod_array, linestyle='-', linewidth=self.linewidth_list[idx], marker=self.marker_list[idx], color=self.colors_list[idx],
                     label=self.model_list[idx], alpha=0.5)
            ax2.legend(bbox_to_anchor=(0, -.14, 1, -.14), loc='lower left', mode='expand', borderaxespad=0., ncol=5,
                       prop={'size': 6})
            ax1.xaxis.set_label_coords(0.5, -0.066)
            ax1.set_xlabel(xlabel, fontsize=9)
            ax1.set_ylabel(ylabel, fontsize=9)
        plt.savefig(self.output_file)
        plt.show()
        self.save_to_file(plt)

    def read_input_data(self):
        """
            Based on the input filename, invoke method from the metcalcpy package to
            open and create a list of dictionaries containing the following keys: model, fcst_valid_beg, fcst_lead, vx_mask,
             stat_name, stat_value.  The value for stat_value is a list of statistics (either PODY or FAR values) for
             each model-vx_mask combination.

            Args:

            Return:

        """

        stat_data_list = []

        return stat_data_list

    def create_series_data(self, stat_data_list):
        """
            From the input data, create the series data for model-vx_mask pairings to be plotted on the
            performance diagram.

            Args:
                stat_data_list: The input data containing the model, vx-mask region, PODY and FAR statistics
                                values used in creating the performance diagram of interest.
            Returns:

        """

        series_data = []

        return series_data



def generate_sample_data(params):
    '''
        Args:
            params:  Input parameters read in from the custom configuration file.
        Returns:
            model_stat_data: A list of dictionaries, where the keys are model, SUCCESS_RATE, and POD
    '''

    all_lines = params['lines']
    model_names = []
    for line in all_lines:
        model_names.append(line['name'])

    num_points = 7

    # Test invocation of metcalcpy package's method
    # if metcalcpy.represents_int(num_points):
    #     print(f"metcalcpy's event equalization function works")

    model_stat_data_list = []
    model_stat_dict = {}

    for i, model in enumerate(model_names):
        # create a list of FAR and POD statistics, consisting of n-points.
        far = np.random.randint(size=num_points, low=1, high=9)
        np.random.seed(seed=234)
        pod = np.random.randint(size=num_points, low=1, high=9)

        # Realistic values are between 0 and 1.0 let's multiply each value by 0.1
        if i % 5 == 0:
            pod_values = [x * .125 for x in pod]
        elif i % 4 == 0:
            pod_values = [x * .12 for x in pod]
        elif i % 3 == 0:
            pod_values = [x * .115 for x in pod]
        elif i % 2 == 0:
            pod_values = [x * 0.11 for x in pod]
        else:
            pod_values = [x * 0.1 for x in pod]

        # pod_values = [x * 0.1 for x in pod]
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
        sample_data = generate_sample_data(docs)
        # alternatively, read in data from a text file
        # via one or more methods in the metcalcpy package
        # input_filename = 'path/to/input_filename'
        # sample_data = metcalcpy.read_model_stat_data(input_filename)
        pd = PerformanceDiagram(docs, sample_data)


    except ValueError as ve:
        print(ve)


if __name__ == "__main__":
    main()
