"""
Class Name: roc_diagram.py
 """
__author__ = 'Minna Win'
__email__ = 'met_help@ucar.edu'

import os
import yaml
import re
import pandas as pd
import numpy as np
import plotly
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import constants

import plots.util as util
from plots.met_plot import MetPlot
from roc_diagram_config import ROCDiagramConfig
from roc_diagram_series import ROCDiagramSeries


class ROCDiagram(MetPlot):
    """
        Creates a ROC diagram based on settings in a config file and
        either MET output data for the following line types:
            CTC (contingency table)
            PCT (probability contingency counts)

    """

    def __init__(self, parameters):
        """
            Instantiate a ROCDiagram object

            Args:
            @param parameters: dictionary containing user defined parameters

        """

        default_conf_filename = "roc_diagram_defaults.yaml"

        # init common layout
        super().__init__(parameters, default_conf_filename)

        # instantiate a PerformanceDiagramConfig object, which holds all the necessary settings from the
        # config file.
        self.config_obj = ROCDiagramConfig(parameters)

        # Read in input data, location specified in config file
        self.input_df = self._read_input_data()

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
            Read the input data file (either CTC or PCT linetype)
            and store as a pandas dataframe so we can subset the
            data to represent each of the series defined by the
            series_val permutations.

            Args:

            Returns:

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
            # Create a ROCDiagramSeries object
            series_obj = ROCDiagramSeries(self.config_obj, i, input_data)
            series_list.append(series_obj)
        return series_list

    def remove_file(self):
        """
           Removes previously made image file .  Invoked by the parent class before self.output_file
           attribute can be created, but overridden here.
        """

        image_name = self.get_config_value('plot_output')

        # remove the old file if it exist
        if os.path.exists(image_name):
            os.remove(image_name)

    def _create_figure(self):
        """
        Generate the performance diagram of varying number of series with POD and 1-FAR
        (Success Rate) values.  Hard-coding of labels for CSI lines and bias lines,
        and contour colors for the CSI curves.


        Args:


        Returns:
             ROC diagram
        """

        # This creates a figure of height and width as specified by the user
        # fig = plt.figure(figsize=[self.config_obj.plot_height, self.config_obj.plot_width],
        #                  dpi=self.config_obj.plot_resolution)
        #
        # ax1 = fig.add_subplot()
        # ax2 = ax1.twinx()
        # ax1.set_ylim(0.0, 1.0)
        # ax2.set_ylim(0.0, 1.0)
        # ax1.set_xlim(0.0, 1.0)
        # plt.title(self.config_obj.title, fontsize=constants.DEFAULT_TITLE_FONTSIZE,
        #           color=constants.DEFAULT_TITLE_COLOR, fontweight="bold",
        #           fontfamily=constants.DEFAULT_TITLE_FONT)
        # ax1.set_xlabel(self.config_obj.xaxis)
        # ax1.set_ylabel(self.config_obj.yaxis_1)
        # ax2.set_ylabel(self.config_obj.yaxis_2)
        #

        fig = make_subplots(specs=[[{"secondary_y": True}]])

        # Add figure title
        fig.update_layout(
            title={'text': self.config_obj.title,
                   'y': 0.95,
                   'x': 0.5,
                   'xanchor': "center",
                   'yanchor': "top"},
            plot_bgcolor="#FFF"

        )
        # Set x-axis title
        fig.update_xaxes(title_text=self.config_obj.xaxis, linecolor="black", linewidth=2, showgrid=False,
                         range=[0.0, 1.0])
        fig.update_xaxes(title_text=self.config_obj.xaxis, linecolor="black", linewidth=2, showgrid=False,
                         range=[0.0, 1.0])

        # Set y-axes titles
        # fig.update_yaxes(title_text="<b>primary</b> yaxis title", secondary_y=False)
        fig.update_yaxes(title_text=self.config_obj.yaxis_1, secondary_y=False, linecolor="black", linewidth=2,
                         showgrid=False, zeroline=False, range=[0.0, 1.0])
        fig.update_yaxes(title_text=self.config_obj.yaxis_2, secondary_y=True, linecolor="black", linewidth=2,
                         showgrid=False, zeroline=False, range=[0.0, 1.0])

        # plot the no-skill line
        x = [0., 1.]
        y = [0., 1.]
        fig.add_trace(go.Scatter(x=x, y=y, line=dict(color='grey',
                                                     width=1.2,
                                                     dash='dash'
                                                     ),
                                 name='no skill line',
                                 showlegend=False
                                 ))

        # style the legend box
        if self.config_obj.draw_box:
            fig.update_layout(legend=dict(x=self.config_obj.bbox_x,
                                          y=self.config_obj.bbox_y,
                                          bordercolor="black",
                                          borderwidth=2
                                          ))

        else:
            fig.update_layout(legend=dict(x=self.config_obj.bbox_x,
                                          y=self.config_obj.bbox_y
                                          ))

        # can't support number of columns in legend, can only choose
        # between horizontal or vertical alignment of legend labels
        # so only support vertical legends (ie num columns = 1)
        fig.update_layout(legend=dict(x=self.config_obj.bbox_x,
                                      y=self.config_obj.bbox_y,
                                      bordercolor="black",
                                      borderwidth=2
                                      ))
        thresh_list = []

        for idx, series in enumerate(self.series_list):
            for i, thresh_val in enumerate(series.series_points[2]):
                thresh_list.append(str(thresh_val))

            # Don't generate the plot for this series if
            # it isn't requested (as set in the config file)
            if series.plot_disp:
                pofd_points = series.series_points[0]
                pody_points = series.series_points[1]
                legend_label = self.config_obj.user_legends[idx]
                fig.add_trace(
                    go.Scatter(x=pofd_points, y=pody_points, mode="lines+markers+text", showlegend=True,
                               text=thresh_list, textposition="top right", name=legend_label),
                    secondary_y=False
                )

            return fig

    def save_to_file(self):
        """Saves the image to a file specified in the config file.
         Prints a message if fails

        Args:

        Returns:

        """
        image_name = self.get_config_value('plot_output')
        if self.figure:
            try:
                self.figure.write_image(image_name)
            except FileNotFoundError:
                print("Can't save to file " + image_name)
            except ValueError as ex:
                print(ex)
        else:
            print("Oops!  The figure was not created. Can't save.")

    def write_output_file(self):
        """
            Writes the POFD (False alarm ratio) and PODY data points that are
            being plotted

        """

        # Open file, name it based on the stat_input config setting,
        # (the input data file) except replace the .data
        # extension with .points1 extension
        input_filename = self.config_obj.stat_input
        match = re.match(r'(.*)(.data)', input_filename)
        if match:
            filename_only = match.group(1)
            output_file = filename_only + ".points1"

            # make sure this file doesn't already
            # exit, delete it if it does
            try:
                if os.stat(output_file).st_size == 0:
                    fileobj = open(output_file, 'a')
                else:
                    os.remove(output_file)
            except FileNotFoundError as fnfe:
                # OK if no file was found
                pass

            fileobj = open(output_file, 'a')
            header_str = "pofd\t pody\n"
            fileobj.write(header_str)
            all_pody = []
            all_pofd = []
            for series in self.series_list:
                pody_points = series.series_points[1]
                pofd_points = series.series_points[0]
                all_pody.extend(pody_points)
                all_pofd.extend(pofd_points)

            all_points = zip(all_pofd, all_pody)
            for idx, pts in enumerate(all_points):
                data_str = str(pts[0]) + "\t" + str(pts[1]) + "\n"
                fileobj.write(data_str)

            fileobj.close()


def main():
    """
            Generates a sample, default, ROC diagram using the
            default and custom config files on sample data found in this directory.
            The location of the input data is defined in either the default or
            custom config file.
        """

    # Retrieve the contents of the custom config file to over-ride
    # or augment settings defined by the default config file.
    # with open("./custom_roc_diagram.yaml", 'r') as stream:
    config_file = util.read_config_from_command_line()
    with open(config_file, 'r') as stream:
        try:
            docs = yaml.load(stream, Loader=yaml.FullLoader)
        except yaml.YAMLError as exc:
            print(exc)

    try:
        r = ROCDiagram(docs)
        r.save_to_file()
        r.show_in_browser()
    except ValueError as ve:
        print(ve)


if __name__ == "__main__":
    main()
