"""
Class Name: roc_diagram.py
 """
__author__ = 'Minna Win'
__email__ = 'met_help@ucar.edu'

import os
import yaml
import re
import pandas as pd
import plotly
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import plots.util as util
import plots.constants as constants
from plots.base_plot import BasePlot
from roc_diagram_config import ROCDiagramConfig
from roc_diagram_series import ROCDiagramSeries
import metcalcpy.util.utils as calc_util


class ROCDiagram(BasePlot):
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

        # instantiate a ROCDiagramConfig object, which holds all the necessary settings from the
        # config file that represents the BasePlot object (ROC diagram).
        self.config_obj = ROCDiagramConfig(self.parameters)

        # Read in input data, location specified in config file
        self.input_df = self._read_input_data()

        # Apply event equalization, if requested
        if self.config_obj.use_ee:

            # Initialize the fix variable lists that will be needed by the
            # event_equalize() method in the METcalcpy module.
            list_fix_vars = []
            list_fix_var_vals = []

            # for both PCT and CTC linetypes, the indy_val is fcst_valid_beg,
            # as verified by looking at the METviewer GUI for ROC diagram
            self.parameters['indy_vals'] = 'fcst_valid_beg'

            if self.config_obj.linetype_pct:
                # add thresh_i
                input_df = self.input_df
                unique_i_thresh = input_df['thresh_i'].unique()
                # Create a dataframe to act like the matrix with
                # n rows and 1 column in roc.R script.
                matPermVal_df = pd.DataFrame(unique_i_thresh)

                # Assign values to list_fix_vars and list_fix_var_vals which
                # are used in the event_equalize() code.
                if list_fix_vars is None:
                    list_fix_vars.append("thresh_i")
                    list_fix_var_vals[0] = matPermVal_df[:,1]
                else:
                    list_fix_vars.append('thresh_i')
                    list_fix_var_vals[len(list_fix_var_vals) + 1] = matPermVal_df[:,1]

            self.input_df = calc_util.perform_event_equalization(self.config_obj.parameters, self.input_df)

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
           is represented by a line in the diagram, so they also contain information
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

        image_name = self.get_config_value('plot_filename')

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

        fig = make_subplots(specs=[[{"secondary_y": True}]])


        # Set plot height and width in pixel value
        width = self.config_obj.plot_width
        height = self.config_obj.plot_height
        # fig.update_layout(width=width, height=height, paper_bgcolor="white")
        fig.update_layout(width=width, height=height)

        # Add figure title
        # fig.update_layout(
        #     title={'text': self.config_obj.title,
        #            'y': 0.95,
        #            'x': 0.5,
        #            'xanchor': "center",
        #            'yanchor': "top"},
        #     plot_bgcolor="#FFF"
        #
        # )

        # create title
        title = {'text': util.apply_weight_style(self.config_obj.title,
                                                 self.config_obj.parameters['title_weight']),
                 'font': {
                     'size': self.config_obj.title_font_size,
                 },
                 'y': self.config_obj.title_offset,
                 'x': self.config_obj.parameters['title_align'],
                 'xanchor': 'center',
                 'yanchor':'top',
                 'xref': 'paper'
                 }
        fig.update_layout(title=title, plot_bgcolor="#FFF")


        # fig.update_xaxes(title_text=self.config_obj.xaxis, linecolor="black", linewidth=2, showgrid=False,
        #                  range=[0.0, 1.0], dtick=0.1)

        # Set y-axes titles
        # fig.update_yaxes(title_text="<b>primary</b> yaxis title", secondary_y=False)
        fig.update_yaxes(title_text=self.config_obj.yaxis_1, secondary_y=False, linecolor="black", linewidth=2,
                         showgrid=False, zeroline=False, range=[0.0, 1.0],dtick=0.1)
        # fig.update_yaxes(title_text=self.config_obj.yaxis_2, secondary_y=True, linecolor="black", linewidth=2,
        #                  showgrid=False, zeroline=False, range=[0.0, 1.0], dtick=0.1)

        # set the range of the x-axis and y-axis to range from 0 to 1
        fig.update_layout(xaxis=dict(range=[0., 1.]))
        fig.update_layout(yaxis=dict(range=[0., 1.]))

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

        # caption styling
        annotation = [
            {'text': util.apply_weight_style(self.config_obj.parameters['plot_caption'],
                                             self.config_obj.parameters['caption_weight']),
             'align': 'left',
             'showarrow': False,
             'xref': 'paper',
             'yref': 'paper',
             'x': self.config_obj.parameters['caption_align'],
             'y': self.config_obj.caption_offset,
             'font': {
                 'size': self.config_obj.caption_size,
                 'color': self.config_obj.parameters['caption_col']
             }
             }]

        # Set x-axis title
        # fig.update_xaxes(title_text=self.config_obj.xaxis, linecolor="black", linewidth=2, showgrid=False,
        #                  dtick=0.1, tickmode='linear', tick0=0.0)
        fig.update_xaxes(title_text=self.config_obj.xaxis,
                                 linecolor=constants.PLOTLY_AXIS_LINE_COLOR,
                                 linewidth=constants.PLOTLY_AXIS_LINE_WIDTH,
                                 showgrid=False,
                                 dtick=0.1,
                                 tick0=0.0,
                                 tickmode='linear',
                                 zeroline=False,
                                 title_font={
                                     'size': self.config_obj.x_title_font_size
                                 },
                                 ticks="inside",
                                 title_standoff=abs(self.config_obj.parameters['xlab_offset']),
                                 tickangle=self.config_obj.x_tickangle,
                                 tickfont={'size': self.config_obj.x_tickfont_size}
                                 )
        fig.update_yaxes(title_text=
                                 util.apply_weight_style(self.config_obj.yaxis_1,
                                                         self.config_obj.parameters['ylab_weight']),
                                 secondary_y=False,
                                 linecolor=constants.PLOTLY_AXIS_LINE_COLOR,
                                 linewidth=constants.PLOTLY_AXIS_LINE_WIDTH,
                                 zeroline=False,
                                 title_font={
                                     'size': self.config_obj.y_title_font_size
                                 },
                                 ticks="inside",
                                 title_standoff=abs(self.config_obj.parameters['ylab_offset']),
                                 tickangle=self.config_obj.y_tickangle,
                                 tickfont={'size': self.config_obj.y_tickfont_size}
                                 )

        fig.update_layout(annotations=annotation)

        thresh_list = []

        # "Dump" False Detection Rate (POFD) and PODY points to an output
        # file based on the output image filename (useful in debugging)
        self.write_output_file()

        for idx, series in enumerate(self.series_list):
            for i, thresh_val in enumerate(series.series_points[2]):
                thresh_list.append(str(thresh_val))

            # Don't generate the plot for this series if
            # it isn't requested (as set in the config file)
            if series.plot_disp:
                pofd_points = series.series_points[0]
                pody_points = series.series_points[1]
                legend_label = self.config_obj.user_legends[idx]

                # add the plot
                fig.add_trace(
                    go.Scatter(mode="lines+markers",x=pofd_points, y=pody_points, showlegend=True,
                               text=thresh_list, textposition="top right", name=legend_label,
                               line=dict(color=self.config_obj.colors_list[idx],
                                         width=self.config_obj.linewidth_list[idx]),
                               marker_symbol=self.config_obj.marker_list[idx]),
                    secondary_y=False
                )


            def add_trace_copy(trace):
                """Adds separate traces for markers and a legend.
                   This is a fix for not printing 'Aa' in the legend
                    Args:
                    Returns:
                """
                fig.add_traces(trace)
                new_trace = fig.data[-1]
                # if self.config_obj.add_point_thresholds:
                #     new_trace.update(textfont_color=trace.marker.color, textposition='top center',
                #                  mode="text", showlegend=False)
                new_trace.update(textfont_color=trace.marker.color, textposition='top center',
                                         mode="text", showlegend=False)
                trace.update(mode="lines+markers")
            if self.config_obj.add_point_thresholds:
                fig.for_each_trace(add_trace_copy)
        return fig

    def save_to_file(self):
        """Saves the image to a file specified in the config file.
         Prints a message if fails

        Args:

        Returns:

        """
        image_name = self.get_config_value('plot_filename')
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

    def write_html(self) -> None:
        """
        Is needed - creates and saves the html representation of the plot WITHOUT Plotly.js
        """
        if self.config_obj.create_html is True:
            # construct the fle name from plot_filename
            name_arr = self.get_config_value('plot_filename').split('.')
            html_name = name_arr[0] + ".html"

            # save html
            self.figure.write_html(html_name, include_plotlyjs=False)


def main(config_filename=None):
    """
            Generates a sample, default, ROC diagram using the
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
        r = ROCDiagram(docs)
        r.save_to_file()
        r.write_html()
        r.write_output_file()
        # r.show_in_browser()
    except ValueError as ve:
        print(ve)


if __name__ == "__main__":
    main()
