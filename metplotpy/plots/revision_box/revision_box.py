# ============================*
# ** Copyright UCAR (c) 2022
# ** University Corporation for Atmospheric Research (UCAR)
# ** National Center for Atmospheric Research (NCAR)
# ** Research Applications Lab (RAL)
# ** P.O.Box 3000, Boulder, Colorado, 80307-3000, USA
# ============================*


"""
Class Name: revision_box.py
 """
import os
import re
from datetime import datetime
import plotly.graph_objects as go

from metplotpy.plots.base_plot import BasePlot

from metplotpy.plots.box.box import Box
from metplotpy.plots import util

import metcalcpy.util.utils as calc_util
from metplotpy.plots.constants import PLOTLY_AXIS_LINE_COLOR, PLOTLY_AXIS_LINE_WIDTH
from metplotpy.plots.revision_box.revision_box_config import RevisionBoxConfig
from metplotpy.plots.revision_box.revision_box_series import RevisionBoxSeries


class RevisionBox(Box):
    """  Generates a Plotly Revision box plot for 1 or more boxes.
    """
    LONG_NAME = 'revision box'
    defaults_name = 'revision_box_defaults.yaml'

    def __init__(self, parameters: dict) -> None:
        """ Creates a Revision Box plot consisting of one or more boxes, based on
            settings indicated by parameters.

            Args:
            @param parameters: dictionary containing user defined parameters

        """

        # init common layout
        BasePlot.__init__(self, parameters, self.defaults_name)

        # instantiate a RevisionBoxConfig object, which holds all the necessary settings from the
        # config file that represents the BasePlot object (RevisionBox).
        self.config_obj = RevisionBoxConfig(self.parameters)
        self.logger = self.config_obj.logger
        self.logger.info(f"Begin revision box plotting: {datetime.now()}")

        # Check that we have all the necessary settings for each series
        is_config_consistent = self.config_obj._config_consistency_check()
        if not is_config_consistent:
            raise ValueError("The number of series defined by series_val_1  is"
                             " inconsistent with the number of settings"
                             " required for describing each series. Please check"
                             " the number of your configuration file's plot_i,"
                             " plot_disp, series_order, user_legend,"
                             " colors, show_legend and series_symbols settings.")

        # Read in input data, location specified in config file
        self.input_df = self._read_input_data()

        # Apply event equalization, if requested
        if self.config_obj.use_ee is True:
            self.logger.info("Applying event equalization")
            self.input_df = calc_util.perform_event_equalization(self.parameters, self.input_df)

        # Create a list of series objects.
        # Each series object contains all the necessary information for plotting,
        # such as  color and criteria needed to subset the input dataframe.
        self.series_list = self._create_series(self.input_df)

        # create figure
        # pylint:disable=assignment-from-no-return
        # Need to have a self.figure that we can pass along to
        # the methods in base_plot.py (BasePlot class methods) to
        # create binary versions of the plot.
        self._create_figure()

    def __repr__(self):
        """ Implement repr which can be useful for debugging this
            class.
        """

        return f'RevisionBox({self.parameters!r})'

    def _create_series(self, input_data):
        """
               Generate all the series objects that are to be displayed as specified by the plot_disp
               setting in the config file. Each series object
               is represented by a box in the diagram, so they also contain information
               for  plot-related/appearance-related settings (which were defined in the config file).

               Args:
                   input_data:  The input data in the form of a Pandas dataframe.
                                This data will be subset to reflect the series data of interest.

               Returns:
                   a list of series objects that are to be displayed


        """
        self.logger.info(f"Begin creating series points: {datetime.now()}")
        series_list = []

        # add series for y1 axis
        for i, name in enumerate(self.config_obj.get_series_y()):
            series_obj = RevisionBoxSeries(self.config_obj, i, input_data, series_list, name)
            series_list.append(series_obj)

        # reorder series
        series_list = self.config_obj.create_list_by_series_ordering(series_list)
        self.logger.info(f"Finished creating series points: {datetime.now()}")

        return series_list

    def _create_figure(self):
        """ Create a box plot from default and custom parameters"""

        self.logger.info(f"Begin creating the figure: {datetime.now()}")
        self.figure = self._create_layout()
        self._add_xaxis()
        self._add_yaxis()
        self._add_legend()

        annotation_text_all = ''
        for inx, series in enumerate(self.series_list):
            # Don't generate the plot for this series if
            # it isn't requested (as set in the config file)
            if series.plot_disp:
                self._draw_series(series)
                # construct annotation text
                annotation_text = series.user_legends + ': '
                if self.config_obj.revision_run:
                    annotation_text = annotation_text + 'WW Runs Test:' + series.series_points['revision_run'] + ' '

                if self.config_obj.revision_ac:
                    annotation_text = annotation_text + "Auto-Corr Test: p=" \
                                      + series.series_points['auto_cor_p'] \
                                      + ", r=" + series.series_points['auto_cor_r']

                annotation_text_all = annotation_text_all + annotation_text
                if inx < len(self.series_list) - 1:
                    annotation_text_all = annotation_text_all + '<br>'

        # add custom lines
        if len(self.series_list) > 0:
            self._add_lines(
                self.config_obj,
                sorted(self.series_list[0].series_data[self.config_obj.indy_var].unique())
            )

        # apply y axis limits
        self._yaxis_limits()

        # add Auto-Corr Test and/or WW Runs Test results if needed
        if self.config_obj.revision_run or self.config_obj.revision_ac:
            self.figure.add_annotation(text=annotation_text_all,
                                       align='left',
                                       showarrow=False,
                                       xref='paper',
                                       yref='paper',
                                       x=0,
                                       yanchor='bottom',
                                       xanchor='left',
                                       y=1,
                                       font={
                                           'size': self.config_obj.legend_size,
                                           'color': "black"
                                       },
                                       bordercolor=self.config_obj.legend_border_color,
                                       borderwidth=0
                                       )

            self.logger.info(f"Finished creating figure: {datetime.now()}")

    def _draw_series(self, series: RevisionBoxSeries) -> None:
        """
        Draws the boxes on the plot

        :param series: RevisionBoxSeries object with data and parameters
        """

        self.logger.info(f"Begin drawing series: {datetime.now()}")
        # defaults markers and colors for the regular box plot
        line_color = dict(color='rgb(0,0,0)')
        fillcolor = series.color
        marker_color = 'rgb(0,0,0)'
        marker_line_color = 'rgb(0,0,0)'
        marker_symbol = 'circle-open'

        # markers and colors for points only  plot
        if self.config_obj.box_pts:
            line_color = dict(color='rgba(0,0,0,0)')
            fillcolor = 'rgba(0,0,0,0)'
            marker_color = series.color
            marker_symbol = 'circle'
            marker_line_color = series.color

        # create a trace
        self.figure.add_trace(
            go.Box(  # x=[series.idx],
                y=series.series_points['points']['stat_value'].tolist(),
                notched=self.config_obj.box_notch,
                line=line_color,
                fillcolor=fillcolor,
                name=series.user_legends,
                showlegend=self.config_obj.show_legend[series.idx] == 1,
                boxmean=self.config_obj.box_avg,
                boxpoints=self.config_obj.boxpoints,  # outliers, all, False
                pointpos=0,
                marker=dict(size=4,
                            color=marker_color,
                            line=dict(
                                width=1,
                                color=marker_line_color
                            ),
                            symbol=marker_symbol,
                            ),
                jitter=0
            )
        )

        self.logger.info(f"Finished drawing series:{datetime.now()}")

    def _add_xaxis(self) -> None:
        """
        Configures and adds x-axis to the plot
        """
        self.figure.update_xaxes(title_text=self.config_obj.xaxis,
                                 linecolor=PLOTLY_AXIS_LINE_COLOR,
                                 linewidth=PLOTLY_AXIS_LINE_WIDTH,
                                 title_font={
                                     'size': self.config_obj.x_title_font_size
                                 },
                                 title_standoff=abs(self.config_obj.parameters['xlab_offset']),
                                 tickangle=self.config_obj.x_tickangle,
                                 tickfont={'size': self.config_obj.x_tickfont_size},
                                 tickmode='linear'
                                 )

    def write_output_file(self) -> None:
        """
        Formats series values and dumps it into the file
        """

        # open file, name it based on the stat_input config setting,
        # (the input data file) except replace the .data
        # extension with .points1 extension
        # otherwise use points_path path

        self.logger.info("Writing output file.")

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

            filename = filename + '.points1'
            if os.path.exists(filename):
                os.remove(filename)
            for series in self.series_list:
                file_object = open(filename, 'a')
                file_object.write('\n')
                file_object.write(series.user_legends)
                file_object.write('\n')
                annotation_text = ''
                if self.config_obj.revision_run:
                    annotation_text = annotation_text + 'WW Runs Test:' + series.series_points['revision_run'] + ' '

                if self.config_obj.revision_ac:
                    annotation_text = annotation_text + "Auto-Corr Test: p=" \
                                      + series.series_points['auto_cor_p'] \
                                      + ", r=" + series.series_points['auto_cor_r']
                if len(annotation_text) > 0:
                    file_object.write(annotation_text)
                    file_object.write('\n')
                file_object.close()
                quantile_data = series.series_points['points']['stat_value'].quantile([0, 0.25, 0.5, 0.75, 1]).iloc[
                                ::-1]
                quantile_data.to_csv(filename, header=False, index=None, sep=' ', mode='a')
                file_object.close()


def main(config_filename=None):
    """
        Generates a sample, default, revision box plot using a combination of
        default and custom config files on sample data found in this directory.
        The location of the input data is defined in either the default or
        custom config file.
        Args:
                @param config_filename: default is None, the name of the custom config file to apply
    """
    util.make_plot(config_filename, RevisionBox)


if __name__ == "__main__":
    main()
