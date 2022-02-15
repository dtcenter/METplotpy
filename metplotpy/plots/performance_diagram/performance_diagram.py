"""
Class Name: performance_diagram.py
 """
__author__ = 'Minna Win'

import os
import re
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.font_manager import FontProperties
import numpy as np
import yaml
import pandas as pd
from ..base_plot import BasePlot
import metcalcpy.util.utils as calc_util
from .performance_diagram_config import PerformanceDiagramConfig
from .performance_diagram_series import PerformanceDiagramSeries
from .. import util
from .. import constants
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)


class PerformanceDiagram(BasePlot):
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
        # the methods in base_plot.py (BasePlot class methods) to
        # create binary versions of the plot.
        self.figure = self._create_figure()

    def _read_input_data(self):
        """
            Read in the input data as set in the config file as stat_input as a pandas dataframe.

            Args:

            Return:
                 the pandas dataframe representation of the input data file

        """
        df_full = pd.read_csv(self.config_obj.stat_input, sep='\t', header='infer')

        # Remove any columns that are entirely 'NaN' this will be helpful
        # in determining whether we have aggregated statistics (stat_btcl and
        # stat_btu columns with valid values)
        df = df_full.dropna(axis=1, how="all")
        return df

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
        num_series = self.config_obj.calculate_number_of_series()

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
           Removes previously made image file.  Invoked by the parent class before self.output_file
           attribute can be created.
        """

        image_name = self.get_config_value('plot_filename')

        # remove the old file if it exists
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

        # This creates a figure size that is of a "reasonable" size, in inches
        fig = plt.figure(figsize=(self.config_obj.plot_width, self.config_obj.plot_height))

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

        # use FontProperties to re-create the weights set in METviewer
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
                # plt.figtext(self.config_obj.caption_align, self.config_obj.caption_offset, self.config_obj.plot_caption,
        #             size=self.config_obj.caption_size, color=self.config_obj.caption_color)

        plt.figtext(self.config_obj.caption_align, self.config_obj.caption_offset, self.config_obj.plot_caption,
                    fontproperties=font,color=self.config_obj.caption_color)

        #
        # PLOT THE STATISTICS DATA FOR EACH line/SERIES (i.e. GENERATE THE LINES ON THE
        # the statistics data for each model/series
        #

        # "Dump" success ratio and PODY points to an output
        # file based on the output image filename (useful in debugging)
        if self.config_obj.dump_points_1 is True:
            # needed by METviewer
            self.write_output_file()

        for i, series in enumerate(self.series_list):
            # Don't generate the plot for this series if
            # it isn't requested (as set in the config file)

            if series.plot_disp:
                pody_points = series.series_points[1]
                sr_points = series.series_points[0]

                # turn on/off connecting line. 'NA' in config file turns off
                # connecting line
                if series.linewidth == 'NA':
                    linewidth = 0
                else:
                    linewidth = series.linewidth

                # small circle and circle symbols render very small
                # increase the marker size for these two.

                if series.marker == '.' or series.marker == 'o':
                    plt.plot(sr_points, pody_points, linestyle=series.linestyle,
                             linewidth=linewidth,
                             color=self.config_obj.colors_list[i], marker=series.marker,
                             label=series.user_legends,
                             alpha=0.5, ms=9)
                else:
                    plt.plot(sr_points, pody_points, linestyle=series.linestyle,
                             linewidth=linewidth,
                             color=self.config_obj.colors_list[i], marker=series.marker,
                             label=series.user_legends,
                             alpha=0.5, ms=6)

                # Annotate the points with their PODY (i.e. dependent variable value)
                if not self.config_obj.anno_var:
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
                    # ecolor=None uses the same line color used to connect
                    # the markers
                    # elinewidth explicitly set it to the current linewidth of this
                    # series line
                    plt.errorbar(sr_points, pody_points, yerr=pody_errs,
                                 color=self.config_obj.colors_list[i], ecolor=None, ms=1, capsize=2,
                                 elinewidth=self.config_obj.linewidth_list[i])

        # example settings, legend is outside of plot along the bottom
        # ax2.legend(bbox_to_anchor=(0, -.14, 1, -.14), loc='lower left', mode='expand',
        #            borderaxespad=0., ncol=5, prop={'size': 6}, fancybox=True)

        # Legend based on the style settings in the config file.
        ax2.legend(bbox_to_anchor=(self.config_obj.bbox_x, self.config_obj.bbox_y), loc='best',
                   ncol=self.config_obj.legend_ncol,
                   prop={'size': self.config_obj.legend_size},
                   frameon=self.config_obj.draw_box)

        # Use the fontmanager to set the weight for the x-axis label/title using the same
        # method employed above for the caption text weight
        font_x = fontobj.copy()
        font_x.set_size(self.config_obj.x_title_font_size)
        style_x = self.config_obj.xlab_weight[0]
        wt_x = self.config_obj.xlab_weight[1]
        font_x.set_style(style_x)
        font_x.set_weight(wt_x)
        ax1.xaxis.set_label_coords(self.config_obj.x_title_offset, self.config_obj.x_title_align)
        ax1.set_xlabel(xlabel, fontsize=self.config_obj.x_title_font_size, fontproperties=font_x)

        # repeat with another fontmanager for the y-axis label/title
        font_y = fontobj.copy()
        font_y.set_size(self.config_obj.y_title_font_size)
        style_y = self.config_obj.ylab_weight[0]
        wt_y = self.config_obj.ylab_weight[1]
        font_y.set_style(style_y)
        font_y.set_weight(wt_y)
        ax1.yaxis.set_label_coords(self.config_obj.y_title_align, self.config_obj.y_title_offset)
        ax1.set_ylabel(ylabel, fontsize=self.config_obj.y_title_font_size,fontproperties=font_y)

        # xtick labels and ytick labels
        plt.xticks(visible=False)
        plt.setp(ax1.get_xticklabels(), fontsize=self.config_obj.x_tickfont_size, rotation=self.config_obj.x_tickangle)
        plt.setp(ax1.get_yticklabels(), fontsize=self.config_obj.y_tickfont_size, rotation=self.config_obj.y_tickangle)

        if self.config_obj.yaxis_2:
            ax2.set_ylabel(self.config_obj.yaxis_2, fontsize=9)

        # use plt.tight_layout() to prevent label box from scrolling off the figure
        plt.tight_layout()
        plt.savefig(self.get_config_value('plot_filename'))
        self.save_to_file()

    def write_output_file(self):
        """
            Writes the 1-FAR and PODY data points that are
            being plotted. Saves the points1 file to either a default location
            (ie where the input data is stored) or to a location specified in
            the custom config file under the optional points_path config setting.

        """


        # if points_path parameter doesn't exist,
        # open file, name it based on the stat_input config setting,
        # (the input data file) except replace the .data
        # extension with .points1 extension
        # otherwise use points_path path
        match = re.match(r'(.*)(.data)', self.config_obj.parameters['stat_input'])
        if self.config_obj.dump_points_1 is True and match:
            filename = match.group(1)
            # replace the default path with the custom
            if self.config_obj.points_path is not None:
                # get the file name
                path = filename.split(os.path.sep)
                if len(path) > 0:
                    filename = path[-1]
                else:
                    filename = '.' + os.path.sep
                filename = self.config_obj.points_path + os.path.sep + filename

            output_file = filename + '.points1'

            # make sure this file doesn't already
            # exist, delete it if it does
            try:
                if os.stat(output_file).st_size == 0:
                    fileobj = open(output_file, 'a')
                else:
                    os.remove(output_file)
            except FileNotFoundError as fnfe:
                # OK if no file was found
                pass

            fileobj = open(output_file, 'a')
            header_str = "1-far\t pody\n"
            fileobj.write(header_str)
            all_pody = []
            all_sr = []
            for series in self.series_list:
                pody_points = series.series_points[1]
                sr_points = series.series_points[0]
                all_pody.extend(pody_points)
                all_sr.extend(sr_points)

            all_points = zip(all_sr, all_pody)
            for idx, pts in enumerate(all_points):
                data_str = str(pts[0]) + "\t" + str(pts[1]) + "\n"
                fileobj.write(data_str)

            fileobj.close()


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
    # with open("./custom_performance_diagram.yaml", 'r') as stream:
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
        PerformanceDiagram(docs)

    except ValueError as value_error:
        print(value_error)


if __name__ == "__main__":
    main()
