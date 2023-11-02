# ============================*
 # ** Copyright UCAR (c) 2022
 # ** University Corporation for Atmospheric Research (UCAR)
 # ** National Center for Atmospheric Research (NCAR)
 # ** Research Applications Lab (RAL)
 # ** P.O.Box 3000, Boulder, Colorado, 80307-3000, USA
 # ============================*
 
 
 
"""
Class Name: contour.py
 """
__author__ = 'Tatiana Burek'

import os
from datetime import datetime
import re
import csv

import yaml
import pandas as pd

import plotly.graph_objects as go
from plotly.subplots import make_subplots
from plotly.graph_objects import Figure

from metplotpy.plots.constants import PLOTLY_PAPER_BGCOOR
from metplotpy.plots.base_plot import BasePlot
from metplotpy.plots import util
from metplotpy.plots.contour.contour_config import ContourConfig
from metplotpy.plots.contour.contour_series import ContourSeries
from metplotpy.plots.series import Series

import metcalcpy.util.utils as calc_util


class Contour(BasePlot):
    """  Generates a Plotly contour plot
    """

    defaults_name = 'contour_defaults.yaml'

    def __init__(self, parameters: dict) -> None:
        """ Creates a contour plot based on
            settings indicated by parameters.

            Args:
            @param parameters: dictionary containing user defined parameters

        """

        # init common layout
        super().__init__(parameters, self.defaults_name)

        self.allow_secondary_y = False

        # instantiate a ContourConfig object, which holds all the necessary settings from the
        # config file that represents the BasePlot object (Line).
        self.config_obj = ContourConfig(self.parameters)


        self.contour_logger = self.config_obj.logger
        self.contour_logger.info(f"Start contour plot: {datetime.now()}")

        # Check that we have all the necessary settings for each series
        self.contour_logger.info("Consistency checking of config settings for colors,legends, etc.")
        is_config_consistent = self.config_obj._config_consistency_check()
        if not is_config_consistent:
            self.contour_logger.error("ValueError: The number of series defined by "
                                 "series_val_1 is inconsistent with the number of "
                                 "settings required for describing each series. "
                                 "Please check  the number of your configuration"
                                 " file's  plot_disp, series_order, user_legend,"
                                 " colors settings. ")
            raise ValueError("The number of series defined by series_val_1 is"
                             " inconsistent with the number of settings"
                             " required for describing each series. Please check"
                             " the number of your configuration file's "
                             " plot_disp, series_order, user_legend,"
                             " colors settings.")

        # Read in input data, location specified in config file
        self.contour_logger.info(f"Begin reading input data: {datetime.now()}")
        self.input_df = self._read_input_data()

        # Apply event equalization, if requested

        if self.config_obj.use_ee is True:
            self.contour_logger.info(f"Begin event equalization: {datetime.now()} ")
            self.input_df = calc_util.perform_event_equalization(self.parameters, self.input_df)
            self.contour_logger.info(f"Event equalization complete: {datetime.now()}")

        # Create a list of series objects.
        # Each series object contains all the necessary information for plotting,
        # such as
        # line width, and criteria needed to subset the input dataframe.
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

        return f'Counture({self.parameters!r})'

    def _read_input_data(self):
        """
            Read the input data file
            and store as a pandas dataframe.

            Args:

            Returns:

        """
        return pd.read_csv(self.config_obj.parameters['stat_input'], sep='\t',
                           header='infer', float_precision='round_trip')

    def _create_series(self, input_data):
        """
           Generate all the series objects that are to be displayed as specified by the plot_disp
           setting in the config file.  The points are all ordered by datetime.

           Args:
               input_data:  The input data in the form of a Pandas dataframe.
                            This data will be subset to reflect the series data of interest.

           Returns:
               a list of series objects that are to be displayed


        """
        series_list = []

        self.contour_logger.info(f"Generating series objects: {datetime.now()}")
        # add series for y1 axis
        num_series_y1 = len(self.config_obj.get_series_y())
        for i, name in enumerate(self.config_obj.get_series_y()):
            series_obj = ContourSeries(self.config_obj, i, input_data, series_list, name)
            series_list.append(series_obj)

        # reorder series
        series_list = self.config_obj.create_list_by_series_ordering(series_list)

        self.contour_logger.info(f"Finished creating series objects: {datetime.now()}")
        return series_list

    def _create_figure(self):
        """
        Create a Contour plot from defaults and custom parameters
        """

        self.contour_logger.info(f"Creating the figure: {datetime.now()}")
        # create and draw the plot
        self.figure = self._create_layout()
        self._add_xaxis()
        self._add_yaxis()
        self._add_legend()

        for series in self.series_list:

            # Don't generate the plot for this series if
            # it isn't requested (as set in the config file)
            if series.plot_disp:
                self._draw_series(series)

        x_points_index = list(range(0, len(self.config_obj.indy_vals)))
        ordered_indy_label = self.config_obj.create_list_by_plot_val_ordering(self.config_obj.indy_label)

        # display only 5 tick labels on teh x-axis if
        # - it is a date and
        # - the size of labels is more than 5 and
        # - user did not provide custom  labels (the x values and labels array are the same)

        if self.config_obj.reverse_x is True:
            ordered_indy_label.reverse()

        if self.config_obj.indy_var in ['fcst_init_beg', 'fcst_valid_beg'] \
                and len(self.config_obj.indy_vals) > 5 \
                and ordered_indy_label == self.series_list[0].series_points['x']:
            step = int(len(self.config_obj.indy_vals) / 5)
            ordered_indy_label_new = [''] * len(self.config_obj.indy_vals)
            for i in range(0, len(ordered_indy_label), step):
                ordered_indy_label_new[i] = ordered_indy_label[i]
            ordered_indy_label = ordered_indy_label_new

        self.figure.update_layout(
            xaxis={
                'tickmode': 'array',
                'tickvals': x_points_index,
                'ticktext': ordered_indy_label,
                'type': 'category',
                'ticks': "outside"
            }
        )
        self.contour_logger.info(f"Figure creating complete: {datetime.now()}")

    def _draw_series(self, series: Series) -> None:
        """
        Draws the data

        :param series: Contour series object with data and parameters
        """
        self.contour_logger.info(f"Drawing the data: {datetime.now()}")
        line_width = self.config_obj.linewidth_list[series.idx]
        if self.config_obj.add_contour_overlay is False:
            line_width = 0

        # apply y axis limits
        if len(self.config_obj.parameters['ylim']) > 0:
            zmin = self.config_obj.parameters['ylim'][0]
            zmax = self.config_obj.parameters['ylim'][1]
            zauto = False
        else:
            zmin = None
            zmax = None
            zauto = True

        self.figure.add_trace(
            go.Contour(
                z=series.series_points['z'],
                x=series.series_points['x'],
                y=series.series_points['y'],
                showscale=self.config_obj.add_color_bar,
                ncontours=self.config_obj.contour_intervals,
                line={'color': self.config_obj.colors_list[series.idx],
                      'width': line_width,
                      'dash': self.config_obj.linestyles_list[series.idx],
                      'smoothing': 0},
                contours={
                    # 'size': 10,
                    'showlabels': True,
                    'labelfont': {  # label font properties
                        'size': 10,
                        'color': self.config_obj.colors_list[series.idx]
                    }
                },
                colorscale=self.config_obj.color_palette,
                zmin=zmin,
                zmax=zmax,
                zauto=zauto
            )
        )
        self.contour_logger.info(f"Finished drawing data: {datetime.now()}")

    def _create_layout(self) -> Figure:
        """
        Creates a new layout based on the properties from the config file
        including plots size, annotation and title

        :return: Figure object
        """
        # create annotation
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
        # create title
        title = {'text': util.apply_weight_style(self.config_obj.title,
                                                 self.config_obj.parameters['title_weight']),
                 'font': {
                     'size': self.config_obj.title_font_size,
                 },
                 'y': self.config_obj.title_offset,
                 'x': self.config_obj.parameters['title_align'],
                 'xanchor': 'center',
                 'xref': 'paper'
                 }

        # create a layout and allow y2 axis
        fig = make_subplots(specs=[[{"secondary_y": self.allow_secondary_y}]])

        # add size, annotation, title
        fig.update_layout(
            width=self.config_obj.plot_width,
            height=self.config_obj.plot_height,
            margin=self.config_obj.plot_margins,
            paper_bgcolor=PLOTLY_PAPER_BGCOOR,
            annotations=annotation,
            title=title,
            plot_bgcolor=PLOTLY_PAPER_BGCOOR
        )
        return fig

    def _add_xaxis(self) -> None:
        """
        Configures and adds x-axis to the plot
        """
        self.figure.update_xaxes(title_text=self.config_obj.xaxis,
                                 showgrid=False,
                                 zeroline=False,
                                 automargin=True,
                                 title_font={
                                     'size': self.config_obj.x_title_font_size
                                 },
                                 title_standoff=abs(self.config_obj.parameters['xlab_offset']),
                                 tickangle=self.config_obj.x_tickangle,
                                 tickfont={'size': self.config_obj.x_tickfont_size}
                                 )

    def _add_yaxis(self) -> None:
        """
        Configures and adds y-axis to the plot
        """
        self.figure.update_yaxes(title_text=
                                 util.apply_weight_style(self.config_obj.yaxis_1,
                                                         self.config_obj.parameters['ylab_weight']),
                                 secondary_y=False,
                                 showgrid=False,
                                 zeroline=False,
                                 automargin=True,
                                 title_font={
                                     'size': self.config_obj.y_title_font_size
                                 },
                                 title_standoff=abs(self.config_obj.parameters['ylab_offset']),
                                 tickangle=self.config_obj.y_tickangle,
                                 tickfont={'size': self.config_obj.y_tickfont_size}
                                 )

    def _add_legend(self) -> None:
        """
        Creates a plot legend based on the properties from the config file
        and attaches it to the initial Figure
        """
        self.figure.update_layout(legend={'x': self.config_obj.bbox_x,
                                          'y': self.config_obj.bbox_y,
                                          'xanchor': 'center',
                                          'yanchor': 'top',
                                          'bordercolor': self.config_obj.legend_border_color,
                                          'borderwidth': self.config_obj.legend_border_width,
                                          'orientation': self.config_obj.legend_orientation,
                                          'font': {
                                              'size': self.config_obj.legend_size,
                                              'color': "black"
                                          }
                                          })

    def remove_file(self):
        """
           Removes previously made image file .  Invoked by the parent class before self.output_file
           attribute can be created, but overridden here.
        """

        super().remove_file()
        self._remove_html()

    def _remove_html(self) -> None:
        """
        Removes previously made HTML file.
        """

        name_arr = self.get_config_value('plot_filename').split('.')
        html_name = name_arr[0] + ".html"
        # remove the old file if it exist
        if os.path.exists(html_name):
            os.remove(html_name)

    def write_html(self) -> None:
        """
        Is needed - creates and saves the html representation of the plot WITHOUT Plotly.js
        """
        if self.config_obj.create_html is True:
            # construct the file name from plot_filename
            name_arr = self.get_config_value('plot_filename').split('.')
            name_arr[-1] = 'html'
            html_name = ".".join(name_arr)

            # save html
            self.figure.write_html(html_name, include_plotlyjs=False)

    def write_output_file(self) -> None:
        """
        saves series points to the files
        """
        self.contour_logger.info(f"Writing output file: {datetime.now()}")

        # Open file, name it based on the stat_input config setting,
        # (the input data file) except replace the .data
        # extension with .points1 extension
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

            with open(filename, 'w') as file:
                writer = csv.writer(file, delimiter='\t')
                for series in self.series_list:
                    writer.writerow(['X values:'])
                    writer.writerow(series.series_points['x'])
                    file.writelines('\n')
                    writer.writerow(['Y values:'])
                    writer.writerow(series.series_points['y'])
                    file.writelines('\n')
                    writer.writerow(['Z values (X,Y):'])
                    writer.writerows(series.series_points['z'])
                    file.writelines('\n')
                    file.writelines('\n')
                file.close()
        self.contour_logger.info(f"Finished writing output file: {datetime.now()}")


def main(config_filename=None):
    """
            Generates a sample, default, Contour plot using the
            default and custom config files on sample data found in this directory.
            The location of the input data is defined in either the default or
            custom config file.
            Args:
                @param config_filename: default is None, the name of the custom config file to apply
        """

    # Retrieve the contents of the custom config file to over-ride
    # or augment settings defined by the default config file.
    # with open("./custom_line_plot.yaml", 'r') as stream:
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
        plot = Contour(docs)
        plot.save_to_file()
        # plot.show_in_browser()
        plot.write_html()
        plot.write_output_file()
        plot.contour_logger.info(f"Finished contour plot at {datetime.now()}")
    except ValueError as val_er:
        print(val_er)


if __name__ == "__main__":
    main()
