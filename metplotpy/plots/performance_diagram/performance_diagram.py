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
import collections
import metcalcpy
import pandas as pd
from plots.met_plot import MetPlot


class PerformanceDiagram(MetPlot):
    """  Generates a performance diagram (multi-line line plot)
         where each line represents a series of Success ratio vs POD
         A series represents a model paired with a vx_masking region.

         A setting is over-ridden in the default configuration file if
         it is defined in the custom configuration file.


        To use:
        >>> data = generate_sample_data()
        >>> perf_diag = PerformanceDiagram(None, data)

    """

    # Default values...
    DEFAULT_TITLE_FONT = 'sans-serif'
    DEFAULT_TITLE_COLOR = 'darkblue'
    DEFAULT_TITLE_FONTSIZE = 10
    AVAILABLE_MARKERS_LIST = ["o", "^", "s", "d", "H", "."]
    ACCEPTABLE_CI_VALS = ['NONE', 'BOOT', 'NORM']

    def __init__(self, parameters, data):
        """ Creates a line plot consisting of one or more lines (traces), based on
            settings indicated by parameters.

            Args:
            @param parameters: dictionary containing user defined parameters
            @param data:  input data containing datetime, model (or other identifying name),
                          statistics (PODY and FAR or normal or bootstrap upper and lower
                          confidence interval values of PODY and FAR) in XYZ format

        """

        default_conf_filename = "performance_diagram_defaults.yaml"

        # init common layout
        super().__init__(parameters, default_conf_filename)

        # Do not plot the legend for the equal lines of CSI (critical success index)
        self.plot_contour_legend = False
        self.output_image = self.get_config_value('plot_output')
        self.title_font = self.DEFAULT_TITLE_FONT
        self.title_color = self.DEFAULT_TITLE_COLOR
        self.xaxis = self._get_xaxis_title()
        self.yaxis = self._get_yaxis_title()
        self.title = self._get_title()
        self.plot_ci = self._get_plot_ci()
        self.plot_disp = self._get_plot_disp()
        self.series_ordering = self._get_series_order()
        self.colors_list = self._get_colors()
        self.marker_list = self._get_markers()
        self.linewidth_list = self._get_linewidths()
        self.linestyles_list = self._get_linestyles()
        self.symbols_list = self._get_series_symbols()
        self.user_legends = self._get_user_legends()
        self.series = self._create_series_objs()
        is_config_consistent = self._config_consistency_check()
        if not is_config_consistent:
            raise ValueError("The number of series defined by series_val is inconsistent with the number of settings"
                             " required for describing each series. Please check"
                             " the number of your configuration file's plot_i, plot_disp, series_order, user_legend,"
                             " colors, and series_symbols settings.")

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

    def _get_xaxis_title(self):
        """ Override the method in the parent class, MetPlot, as this is located
            in a different location in the config file.
        """

        return self.parameters['xaxis']

    def _get_yaxis_title(self):
        """ Override the method in the parent class, MetPlot, as this is located
            in a different location in the config file.
        """

        return self.parameters['yaxis']

    def _get_title(self):
        """Creates a  title dictionary with values from users and default parameters
        If users parameters dictionary doesn't have needed values - use defaults

        Args:

        Returns:
            - the title
        """
        current_title = self.get_config_value('title')
        return current_title

    def _get_plot_ci(self):
        """

            Args:

            Returns:
                list of values to indicate whether or not to plot the confidence interval for
                a particular series, and which confidence iterval (bootstrap or normal).

        """
        plot_ci_list = self.parameters['plot_ci']
        ci_settings_list = [ci.upper() for ci in plot_ci_list]

        # Do some checking to make sure that the values are valid (case-insensitive): None, boot, or norm
        for ci in ci_settings_list:
            if ci not in self.ACCEPTABLE_CI_VALS:
                raise ValueError("A plot_ci value is set to an invalid value. Accepted values are (case insensitive): "
                                 "None, norm, or boot. Please check your config file.")

        return ci_settings_list

    def _get_plot_disp(self):
        """
            Retrieve the boolean values that determine whether to display a particular series

            Args:

            Returns:
                A list of boolean values indicating whether or not to display the corresponding series
        """

        plot_display_vals = self.parameters['plot_disp']
        plot_display_bools = [pd for pd in plot_display_vals]
        return plot_display_bools

    def _get_series_order(self):
        """
            Get the order number for each series

            Args:

            Returns:
            a list of unique values representing the ordinal value of the corresponding series

        """
        ordinals = self.parameters['series_order']
        series_order_list = [ord for ord in ordinals]
        return series_order_list

    def _get_colors(self):
        """
           Retrieves the colors used for lines and markers, from the config file (default or custom).
           Args:

           Returns:
               colors_list or colors_from_config: a list of the colors to be used for the lines (
               and their corresponding marker symbols)
        """

        colors_settings = self.parameters['colors']
        color_list = [color for color in colors_settings]
        return color_list

    def _get_markers(self):
        """
           Retrieve all the markers, the order and number correspond to the number of series_order, user_legends,
           and number of series.

           Args:

           Returns:
               markers: a list of the markers
        """
        markers = self.parameters['series_symbols']
        markers_list = [m for m in markers]
        return markers_list

    def _get_linewidths(self):
        """ Retrieve all the linewidths from the configuration file, if not specified in any config file, use
            the default values of 2

            Args:

            Returns:
                linewidth_list: a list of linewidths corresponding to each line (model)
        """
        linewidths = self.parameters['series_line_width']
        linewidths_list = [l for l in linewidths]
        return linewidths_list

    def _get_linestyles(self):
        """
            Retrieve all the linestyles from the config file.

            Args:

            Returns:
                list of line styles, each line style corresponds to a particular series
        """
        linestyles = self.parameters['series_line_style']
        linestyle_list = [l for l in linestyles]
        return linestyle_list

    def _get_series_symbols(self):
        """
           Retrieve all the symbols that represent each series

           Args:

           Returns:
               a list of all the symbols, order is preserved.  That is, the first symbol corresponds to the first
               symbol defined.

        """
        symbols = self.parameters['series_symbols']
        symbols_list = [symbol for symbol in symbols]
        return symbols_list

    def _get_user_legends(self):
        """
           Retrieve the text that is to be displayed in the legend at the bottom of the plot.
           Each entry corresponds to a series.

           Args:

           Returns:
               a list consisting of the series label to be displayed in the plot legend.

        """
        all_legends = self.parameters['user_legend']
        legends_list = [legend for legend in all_legends]
        return legends_list

    def _create_series_objs(self):
        """
            Generate series objects, where each series object is a named tuple of unique model and vx_mask
            combinations, color, marker, user_legend label, plot_display value (True/False), .

            Args:

            Returns:
                a list of named tuples that represent a series.
        """

        # Define the series object (named tuple)
        Series = collections.namedtuple('Series', 'model, vx_mask, color, marker, linewidth, linestyle, '
                                                  'user_legend, plot_disp_value, series_order, series_ci_value')
        series_values = self.get_config_value('series_val')

        # Separate the model from the vx_mask portion of the series object so we can create
        # these attributes of a series object
        all_models = series_values['model']
        all_vx_masks = series_values['vx_mask']
        series_combo = [s for s in itertools.product(all_models, all_vx_masks)]
        self.num_series = len(series_combo)
        series_obj_list = []

        # Create a named tuple that represents the series object which consists
        # of a unique pairing of model with vx_mask region, marker, linewidth, symbol,
        # series_order, user_legend, plot_display_val, color.
        for idx, single_series in enumerate(series_combo):
            model_val = single_series[0]
            vx_mask_val = single_series[1]
            series_obj = Series(model=model_val, vx_mask=vx_mask_val, color=self.colors_list[idx],
                                marker=self.marker_list[idx],linewidth=self.linewidth_list[idx],
                                linestyle=self.linestyles_list[idx],
                                user_legend=self.user_legends[idx], plot_disp_value=self.plot_disp[idx],
                                series_order=self.series_ordering[idx], series_ci_value=self.plot_ci[idx])
            series_obj_list.append(series_obj)

        return series_obj_list

    def _config_consistency_check(self):
        """
            Checks that the number of settings defined for plot_ci, plot_disp, series_order, user_legend
            colors, and series_symbols is consistent with the

            Args:

            Returns:
                True if the number of settings for each of the above settings is consistent with the number of
                series (as defined by the cross product of the model and vx_mask defined in the series_val setting)

        """

        # Numbers of values for other settings for series
        num_ci_settings = len(self.plot_ci)
        num_plot_disp = len(self.plot_disp)
        num_markers = len(self.marker_list)
        num_series_ord = len(self.series_ordering)
        num_colors = len(self.colors_list)
        num_symbols = len(self.symbols_list)
        num_legends = len(self.user_legends)
        num_line_widths = len(self.linewidth_list)
        num_linestyles = len(self.linestyles_list)

        if self.num_series == num_ci_settings == num_plot_disp == \
                num_markers == num_series_ord == num_colors == num_symbols\
                == num_legends == num_line_widths == num_linestyles:
            return True
        else:
            return False

    def _get_output_file(self):
        """
            Retrieve the name and path for the output file (output plot).

            Args:

            Returns:
                the path and filename of the output plot
        """
        return self.get_config_value('plot_output')

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

    def _create_figure(self, perf_data):
        """
        Generate the performance diagram of varying number of series with POD and 1-FAR (Success Rate)
        values.  Hard-coding of labels for CSI lines and bias lines, and contour colors for the CSI
        curves.


        Args:
            perf_data: A list of dictionaries, with keys=model, POD, SR (Success Rate) values=name of model/series,
            lists of POD and SR respectively

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
        plt.title(self.title, fontsize=self.DEFAULT_TITLE_FONTSIZE, color=self.DEFAULT_TITLE_COLOR, fontweight="bold", fontfamily=self.DEFAULT_TITLE_FONT)
        plt.text(0.48, 0.6, "Frequency Bias", fontdict=dict(fontsize=8, rotation=45), alpha=.3)

        #
        # PLOT THE STATISTICS DATA FOR EACH MODEL/SERIES (i.e. GENERATE THE LINES ON THE  the statistics data for each model/series
        #
        for idx, series in enumerate(self.series):
            data = perf_data[idx]
            sr_array = data['SUCCESS_RATIO']
            pod_array = data['POD']

            # Only display the points for the series of interest, as indicated by the plot_disp
            # setting in the configuration file.
            if self.series[idx].plot_disp_value:
                plt.plot(sr_array, pod_array, linestyle=self.series[idx].linestyle, linewidth=self.series[idx].linewidth,
                     marker=self.series[idx].marker, color=self.series[idx].color,
                     label=self.series[idx].user_legend, alpha=0.5)

                ax2.legend(bbox_to_anchor=(0, -.14, 1, -.14), loc='lower left', mode='expand', borderaxespad=0., ncol=5,
                       prop={'size': 6})
                ax1.xaxis.set_label_coords(0.5, -0.066)
                ax1.set_xlabel(xlabel, fontsize=9)
                ax1.set_ylabel(ylabel, fontsize=9)
        plt.savefig(self.get_config_value('plot_output'))
        plt.show()
        self.save_to_file()


    def save_to_file(self):
        """ Save plot as file in directory as specified in default or custom config file."""
        print(f"saving file as {self.output_image}")

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

    def _create_series_data(self, stat_data_list):
        """
            From the input data, create the series data for model-vx_mask pairings to be plotted on the
            performance diagram.

            Args:
                stat_data_list: The input data containing the model, vx-mask region, PODY and FAR statistics
                                values used in creating the performance diagram of interest.
            Returns:

        """

        models = self.parameters['series_val']['model']
        vx_masks = self.parameters['series_val']['vx_mask']
        series_data = [s for s in itertools.product(models, vx_masks)]

        return series_data


def generate_sample_data():
    """
         Args:
         Returns:
             model_stat_data: A list of dictionaries, where the keys are series name, SUCCESS_RATE, and POD
    """

    model_names = ['model1', 'model2', 'model 3', 'model 4', 'fifth model']
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
            pod_values = [x * .09 for x in pod]
        elif i % 4 == 0:
            pod_values = [x * .025 for x in pod]
        elif i % 3 == 0:
            pod_values = [x * .002 for x in pod]
        elif i % 2 == 0:
            pod_values = [x * 0.08 for x in pod]
        else:
            pod_values = [x * 0.001 for x in pod]

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
    # with open("./custom_performance_diagram.yaml", 'r') as stream:
    with open("../config/performance_diagram_defaults.yaml", 'r') as stream:
        try:
            docs = yaml.load(stream, Loader=yaml.FullLoader)
        except yaml.YAMLError as exc:
            print(exc)

    # Read in user's data, or generate dummy data
    sample_data = generate_sample_data()

    try:
        # create a performance diagram
        pd = PerformanceDiagram(docs, sample_data)

    except ValueError as ve:
        print(ve)


if __name__ == "__main__":

    main()
