# ============================*
 # ** Copyright UCAR (c) 2020
 # ** University Corporation for Atmospheric Research (UCAR)
 # ** National Center for Atmospheric Research (NCAR)
 # ** Research Applications Lab (RAL)
 # ** P.O.Box 3000, Boulder, Colorado, 80307-3000, USA
 # ============================*



"""
Class Name: roc_diagram.py
 """
__author__ = 'Minna Win'

import os
from datetime import datetime
import re
import warnings
# with warnings.catch_warnings():
#     warnings.simplefilter("ignore", category="DeprecationWarning")
#     warnings.simplefilter("ignore", category="ResourceWarning")

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from metplotpy.plots import util
from metplotpy.plots import constants
from metplotpy.plots.base_plot import BasePlot
from metplotpy.plots.roc_diagram.roc_diagram_config import ROCDiagramConfig
from metplotpy.plots.roc_diagram.roc_diagram_series import ROCDiagramSeries
import metcalcpy.util.utils as calc_util
from metplotpy.plots.util import prepare_pct_roc, prepare_ctc_roc


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
        self.logger = self.config_obj.logger
        self.logger.info(f"Begin ROC diagram: {datetime.now()}")

        # Read in input data, location specified in config file
        self.input_df = self._read_input_data()

        # Apply event equalization, if requested

        if self.config_obj.use_ee:
            self.logger.info("Applying event equalization")
            #
            # for both PCT and CTC linetypes, the indy_var is fcst_valid_beg,
            # as verified by looking at the METviewer GUI for ROC diagram
            self.parameters['indy_var'] = 'fcst_valid_beg'

            if self.config_obj.linetype_pct:
                # add thresh_i to fixed_vars

                # initialise and sort thresh_i
                unique_i_thresh = self.input_df['thresh_i'].unique().tolist()
                unique_i_thresh.sort()

                # create a sub-dictionary
                thresh_i_0 = {'thresh_i_0': unique_i_thresh}

                # add sub-dictionary to fixed_vars_vals_input
                self.parameters['fixed_vars_vals_input']['thresh_i'] = thresh_i_0

            self.input_df = calc_util.perform_event_equalization(self.parameters, self.input_df)
            self.logger.info("Finished performing event equalization.")

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

        # add custom lines
        if len(self.series_list) > 0:
            self._add_lines(self.config_obj)

    def _read_input_data(self) -> pd.DataFrame:
        """
            Read the input data file (either CTC or PCT linetype)
            and store as a pandas dataframe so we can subset the
            data to represent each of the series defined by the
            series_val permutations.

            Args:

            Returns: input_df the dataframe representation of the input data

        """
        self.logger.info("Reading input data.")
        # If self.config_obj.lineype_ctc is True, check for the presence of the fy_oy column.
        # If present, proceed as usual, otherwise extract the fcst_thresh, fy_oy, fy_on, fn_on, and fn_oy data
        # from the stat_name and stat_value columns (long to wide).
        input_df = pd.read_csv(self.config_obj.stat_input, sep='\t', header='infer')
        if self.config_obj.linetype_ctc:
            # Check if there is a column name 'fy_oy'.  If it is missing, then this data has been reformatted by
            # the METdataio reformatter.
            input_columns = input_df.columns.to_list()
            if 'fy_oy' in input_columns:
                # This data has been created from the METviewer database
                return input_df

            else:
                # This data was created by the METdataio reformatter and needs to be modified from long to wide format.
                wide_input_df = self.ctc_long_to_wide(input_df)
                return wide_input_df
        else:
            # PCT data
            return input_df

    def ctc_long_to_wide(self, input_df: pd.DataFrame) -> pd.DataFrame:
        """
          Convert the dataframe representation of the CTC linetype data (that was reformatted by METdataio) from long
          to wide format.  The fcst_thresh, fy_oy, fy_on, fn_oy, and fn_on will be in separate columns,
          rather than residing under the stat_name and stat_value.

          Args:
              @param input_df:  The input dataframe that represents the CTC data reformatted by METdataio.

          Returns:  ctc_df: a dataframe that has the additional columns: fy_oy, fy_on, fn_on, fn_oy, and
                    fcst_thresh extracted from the stat_name and stat_values columns
        """


        # Use all the columns (except the stat_name, stat_value,stat_bcl, stat_bcu, stat_ncl, stat_ncu,
        # and Idx column) as the pivot index
        col_index = input_df.columns.to_list()
        ignore_cols = ['Idx', 'stat_name', 'stat_value', 'stat_bcl', 'stat_bcu', 'stat_ncl', 'stat_ncu']
        for cur in ignore_cols:
            if cur in col_index:
               col_index.remove(cur)
        df_wide = input_df.pivot(index=col_index, columns='stat_name', values='stat_value')

        # reset the index
        reset_df_wide = df_wide.reset_index()

        # Convert all the header names (column labels) to all lower case
        reset_df_wide.columns = [x.lower() for x in reset_df_wide.columns]

        return reset_df_wide

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
        self.logger.info("Creating series object.")
        series_list = []

        # use the list of series ordering values to determine how many series objects we need.
        num_series = len(self.config_obj.series_ordering)
        if self.config_obj.summary_curve != 'none':
            num_series = num_series -1

        for i, series in enumerate(range(num_series)):
            # Create a ROCDiagramSeries object
            series_obj = ROCDiagramSeries(self.config_obj, i, input_data)
            series_list.append(series_obj)

        if self.config_obj.summary_curve != 'none':
            # add Summary Curve bassd on teh summary dataframes of each ROCDiagramSeries
            df_sum_main = None
            for idx, series in enumerate(series_list):
                # create a main summary frame from series summary frames
                if self.config_obj.linetype_ctc:
                    if df_sum_main is None:
                        df_sum_main = pd.DataFrame(columns=['fcst_thresh', 'fy_oy', 'fy_on', 'fn_oy', 'fn_on'])
                elif self.config_obj.linetype_pct:
                    if df_sum_main is None:
                        df_sum_main = pd.DataFrame(columns=['thresh_i', 'i_value', 'on_i', 'oy_i'])

                df_sum_main = pd.concat([df_sum_main, series.series_points[3]], axis=0)

            if self.config_obj.linetype_ctc:
                df_summary_curve = pd.DataFrame(columns=['fcst_thresh', 'fy_oy', 'fy_on', 'fn_oy', 'fn_on'])
                fcst_thresh_list = df_sum_main['fcst_thresh'].unique()
                for thresh in fcst_thresh_list:
                    if self.config_obj.summary_curve == 'median':
                        group_stats_fy_oy = df_sum_main['fy_oy'][df_sum_main['fcst_thresh'] == thresh].median()
                        group_stats_fn_oy = df_sum_main['fn_oy'][df_sum_main['fcst_thresh'] == thresh].median()
                        group_stats_fy_on = df_sum_main['fy_on'][df_sum_main['fcst_thresh'] == thresh].median()
                        group_stats_fn_on = df_sum_main['fn_on'][df_sum_main['fcst_thresh'] == thresh].median()
                    else:
                        group_stats_fy_oy = df_sum_main['fy_oy'][df_sum_main['fcst_thresh'] == thresh].mean()
                        group_stats_fn_oy = df_sum_main['fn_oy'][df_sum_main['fcst_thresh'] == thresh].mean()
                        group_stats_fy_on = df_sum_main['fy_on'][df_sum_main['fcst_thresh'] == thresh].mean()
                        group_stats_fn_on = df_sum_main['fn_on'][df_sum_main['fcst_thresh'] == thresh].mean()
                    df_summary_curve.loc[len(df_summary_curve)] = {'fcst_thresh': thresh,
                                                                   'fy_oy': group_stats_fy_oy,
                                                                   'fn_oy': group_stats_fn_oy,
                                                                   'fy_on': group_stats_fy_on,
                                                                   'fn_on': group_stats_fn_on,
                                                                   }
                df_summary_curve.reset_index()
                pody, pofd, thresh = prepare_ctc_roc(df_summary_curve,self.config_obj.ctc_ascending)
            else:
                df_summary_curve = pd.DataFrame(columns=['thresh_i', 'on_i', 'oy_i'])
                thresh_i_list = df_sum_main['thresh_i'].unique()
                for index, thresh in enumerate(thresh_i_list):
                    if self.config_obj.summary_curve == 'median':
                        on_i_sum = df_sum_main['on_i'][df_sum_main['thresh_i'] == thresh].median()
                        oy_i_sum = df_sum_main['oy_i'][df_sum_main['thresh_i'] == thresh].median()
                    else:
                        on_i_sum = df_sum_main['on_i'][df_sum_main['thresh_i'] == thresh].mean()
                        oy_i_sum = df_sum_main['oy_i'][df_sum_main['thresh_i'] == thresh].mean()
                    df_summary_curve.loc[len(df_summary_curve)] = {'thresh_i': thresh, 'on_i': on_i_sum,
                                                                   'oy_i': oy_i_sum, }
                df_summary_curve.reset_index()
                pody, pofd, thresh = prepare_pct_roc(df_summary_curve)

            series_obj = ROCDiagramSeries(self.config_obj, num_series -1, None)
            series_obj.series_points = (pofd, pody, thresh, None)

            series_list.append(series_obj)

        return series_list

    def remove_file(self):
        """
           Removes previously made image file .  Invoked by the parent class before self.output_file
           attribute can be created, but overridden here.
        """

        image_name = self.get_config_value('plot_filename')
        warnings.filterwarnings("ignore", category=DeprecationWarning)

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

        self.logger.info(f"Begin creating figure: {datetime.now()}")
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
                 'yanchor': 'top',
                 'xref': 'paper'
                 }
        fig.update_layout(title=title, plot_bgcolor="#FFF")

        # fig.update_xaxes(title_text=self.config_obj.xaxis, linecolor="black", linewidth=2, showgrid=False,
        #                  range=[0.0, 1.0], dtick=0.1)

        # Set y-axes titles
        # fig.update_yaxes(title_text="<b>primary</b> yaxis title", secondary_y=False)
        fig.update_yaxes(title_text=self.config_obj.yaxis_1, secondary_y=False, linecolor="black", linewidth=2,
                         showgrid=False, zeroline=False, range=[0.0, 1.0], dtick=0.1)
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
        # This output file is used by METviewer and not necessary for other uses.
        if self.config_obj.dump_points_1 == True :
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
                self.logger.info("Adding traces for markers and legend.")
                fig.add_trace(
                    go.Scatter(mode="lines+markers", x=pofd_points, y=pody_points,
                               showlegend=self.config_obj.show_legend[series.idx] == 1,
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

        self.logger.info(f"Finished creating figure: {datetime.now()}")

        return fig



    def write_output_file(self):
        """
            Writes the POFD (False alarm ratio) and PODY data points that are
            being plotted

        """

        self.logger.info("Writing output file")
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

        self.logger.info("Writing HTML file")
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
    params = util.get_params(config_filename)
    try:
        r = ROCDiagram(params)
        r.save_to_file()

        r.write_html()
        r.logger.info(f"Finished ROC diagram: {datetime.now()}")

        #r.show_in_browser()
    except ValueError as ve:
        print(ve)


if __name__ == "__main__":
    main()
