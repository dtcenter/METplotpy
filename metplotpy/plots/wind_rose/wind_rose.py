
"""
Class Name: wind_rose.py
 """
__author__ = 'Tatiana Burek'

import math
from typing import Union
import pandas as pd
import numpy as np
import yaml
import re
from pathlib import Path

import plotly.graph_objects as go
from plotly.subplots import make_subplots

from plots.base_plot import BasePlot
from plots.wind_rose.wind_rose_config import WindRoseConfig
from plots.constants import PLOTLY_AXIS_LINE_COLOR, PLOTLY_AXIS_LINE_WIDTH, PLOTLY_PAPER_BGCOOR
import plots.util as util


class WindRosePlot(BasePlot):
    """
            Creates a Wind rose plot based on settings in a config file and
            either MET output data for the MPR line type.
            The data can be extracted from the provided files or provided
            as DataFrames for U and V wind components.
            DataFrame requirements:
             - should have a column named 'FCST_VAR' with values 'UGRD' for u_wind_data and/or 'VGRD' for v_wind_data
             - should contain columns 'OBS' and 'FCST'
            (see point_stat_mpr.txt)
            Based on 'type' parameter the Wind rose would be built from OBS or FCST or FCST-OBS data
            This class works with MET v.9.1+ output
            """
    def __init__(self, parameters: dict, u_wind_data: Union[pd.DataFrame, None] = None,
                 v_wind_data: Union[pd.DataFrame, None] = None):

        default_conf_filename = "wind_rose_defaults.yaml"

        # init common layout
        super().__init__(parameters, default_conf_filename)

        # instantiate a WindRoseConfig object, which holds all the necessary settings from the
        # config file that represents the BasePlot object (WindRosePlot).
        self.config_obj = WindRoseConfig(self.parameters)

        # if u or v DataFrames is not provided - read data from the MET stat file
        if u_wind_data is None or v_wind_data is None:
            # Read in input data, location specified in config file
            self._read_input_data()
        else:
            self.u_wind_data = u_wind_data
            self.v_wind_data = v_wind_data

        # wind rose traces
        self.traces = []

        # create wind rose traces
        self._create_traces()

        # create figure if needed
        # pylint:disable=assignment-from-no-return
        # Need to have a self.figure that we can pass along to
        # the methods in base_plot.py (BasePlot class methods) to
        # create binary versions of the plot.
        if self.config_obj.create_figure:
            self.figure = self._create_figure()

    def _read_input_data(self):
        """
            Read the input data file ( UGRD and UGRD forecast vars)
            and store as a pandas dataframes.

            Args:

            Returns:

        """
        input_df = pd.read_csv(self.config_obj.stat_input, delim_whitespace=True, header='infer')
        self.u_wind_data = input_df[input_df['FCST_VAR'] == 'UGRD']
        self.v_wind_data = input_df[input_df['FCST_VAR'] == 'VGRD']

    def _create_figure(self):
        """
        Initialise the figure and add Wnd roses traces

        Args:


        Returns:
             Wind rose plot as Plotly figure
        """

        fig = make_subplots(specs=[[{"secondary_y": False}]])

        # Set plot height and width in pixel value
        fig.update_layout(width=self.config_obj.plot_width, height=self.config_obj.plot_height)

        # Add figure title
        fig.update_layout(
            title={'text': self.config_obj.title,
                   'y': 0.95,
                   'x': 0.5,
                   'xanchor': "center",
                   'yanchor': "top"},
            plot_bgcolor="#FFF"

        )

        fig.update_xaxes(
            linecolor=PLOTLY_AXIS_LINE_COLOR,
            linewidth=PLOTLY_AXIS_LINE_WIDTH,
            showgrid=False,
            ticks="outside",
            zeroline=False,
            automargin=True
        )

        fig.update_yaxes(
            secondary_y=False,
            linecolor=PLOTLY_AXIS_LINE_COLOR,
            linewidth=PLOTLY_AXIS_LINE_WIDTH,
            showgrid=False,
            zeroline=False,
            ticks="outside",
            automargin=True
        )

        fig.update_polars(
            bgcolor=PLOTLY_PAPER_BGCOOR,
            hole=0.08,
            angularaxis_thetaunit="degrees",
            angularaxis_rotation=90,
            angularaxis_direction='clockwise',
            angularaxis_gridcolor=PLOTLY_AXIS_LINE_COLOR,
            angularaxis_tickvals=self.config_obj.angularaxis_tickvals,
            angularaxis_ticktext=self.config_obj.angularaxis_ticktext,
            angularaxis_tickmode='array',
            radialaxis_angle=135,
            radialaxis_tickmode='linear',
            radialaxis_tickangle=100,
            radialaxis_tick0=5,
            radialaxis_dtick=5,
            radialaxis_gridcolor=PLOTLY_AXIS_LINE_COLOR,
            radialaxis_showticklabels=True,
            radialaxis_ticksuffix='%'
        )

        fig.update_layout(
            showlegend=self.config_obj.show_legend,
            plot_bgcolor=PLOTLY_PAPER_BGCOOR,
        )

        # add traces
        for trace in self.traces:
            fig.add_trace(trace)

        return fig

    def _create_traces(self):
        """
        Creates wind rose traces based on the u and v data.
        Number of traces is equal to the length of wind_rose_breaks
        and has it's own color from wind_rose_marker_colors.
        Each trace's data is based on the frequency of the wind speed in the break

        Args:
        Returns:
        """

        # init data based on type
        if self.config_obj.type == 'FCST-OBS':
            u_wind_data = (self.u_wind_data['FCST'] - self.u_wind_data['OBS']).tolist()
            v_wind_data = (self.v_wind_data['FCST'] - self.v_wind_data['OBS']).tolist()
        elif self.config_obj.type == 'FCST':
            u_wind_data = self.u_wind_data['FCST'].tolist()
            v_wind_data = self.v_wind_data['FCST'].tolist()
        else:
            u_wind_data = self.u_wind_data['OBS'].tolist()
            v_wind_data = self.v_wind_data['OBS'].tolist()

        # calculate the wind speed
        wind_speed = [
            math.sqrt(u_wind_data[i] * u_wind_data[i] + v_wind_data[i] * v_wind_data[i])
            for i in range(len(v_wind_data))
        ]

        # calculate the wind dir in degrees for each row and bin it to angles
        wind_dir_deg = []
        for i, v_wind in enumerate(v_wind_data):
            if wind_speed[i] == 0:
                wind_dir_deg.append(None)
            else:
                # calculate the wind dir
                wd = math.atan2(u_wind_data[i] / wind_speed[i], v_wind / wind_speed[i]) * 180 / math.pi
                if wd < 0:
                    wind_dir_deg.append(None)
                else:
                    wind_dir_deg.append(
                        self.config_obj.wind_rose_angle * math.ceil(wd / self.config_obj.wind_rose_angle - 0.5))

        # join wind_speed and wind_dir in one array
        wind_speed_dir = np.vstack((wind_speed, wind_dir_deg)).T

        # create list of angles
        angles = np.arange(0, 360, self.config_obj.wind_rose_angle)

        # distance between the centre of the bin and its edge
        step = (angles[1] - angles[0]) / 2

        # remove rows where wind direction is None
        # and converting data between 348.75 and 360 to negative
        wind_speed_dir_processed = np.empty((0, 2), float)
        for i, wspd in enumerate(wind_speed_dir):
            if wspd[1] is not None:
                if angles[-1] + step <= wspd[1] and wspd[1] < 360:
                    wind_speed_dir_processed = np.append(wind_speed_dir_processed, np.array(
                        [[wspd[0], wspd[1] - 360, ]]), axis=0)
                else:
                    wind_speed_dir_processed = np.append(wind_speed_dir_processed,
                                                         np.array([[wspd[0], wspd[1], ]]),
                                                         axis=0)

        # determining the direction bins
        bin_edges_dir = np.append(angles - step, [angles[-1] + step])

        frequencies = np.array([])
        number_of_records = len(wind_speed_dir)
        speed_bins = []

        # add me max wind speed as the last breaks
        breaks = self.config_obj.wind_rose_breaks.copy()
        breaks.append(max(wind_speed))

        # loop selecting given bins and calculate frequencies
        for i in range(len(breaks) - 1):
            # initialise speed bins strings
            speed_bins.append(f'{int(breaks[i])}-{int(breaks[i + 1])} m/s')

            for j in range(len(bin_edges_dir) - 1):
                # filter data
                bin_contents = self._boundary_filter(breaks[i], breaks[i + 1],
                                                     bin_edges_dir[j], bin_edges_dir[j + 1],
                                                     wind_speed_dir_processed)

                # applying the filtering function for every bin
                # and checking the number of measurements
                frequency = len(bin_contents) / number_of_records

                # obtaining the final frequencies of bin
                frequencies = np.append(frequencies, frequency)

        # create all permutations of speed_bins and angles
        perm_speedbins_angles = pd.MultiIndex.from_product(
            [speed_bins, angles],
            names=['wind_speed_bins', 'wind_direction_bins']
        )
        # create a data frame from permutations of speed_bins
        # and angles with the additional  'frequency' column
        frequencies_df = pd.DataFrame(0, perm_speedbins_angles, ['frequency'])

        # updating the frequencies in the dataframe
        frequencies_df.frequency = frequencies * 100  # [%]

        # create traces
        for i, speed_bin in enumerate(speed_bins):
            trace = go.Barpolar(
                r=frequencies_df.loc[(speed_bin), 'frequency'],
                name=f'Wind {speed_bin}',
                marker_color=self.config_obj.wind_rose_marker_colors[i]
            )
            self.traces.append(trace)

    def save_to_file(self) -> None:
        """ Saves the image to a file specified in the config file.
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

    @staticmethod
    def _boundary_filter(boundary_lower_speed: float,
                         boundary_higher_speed: float,
                         boundary_lower_direction: float,
                         boundary_higher_direction: float,
                         wind_rose_data: np.ndarray) -> np.ndarray:
        """
        This method  filters the wind rose data based on the boundary wind speed and direction

        :param boundary_lower_speed: lowest speed
        :param boundary_higher_speed: highest speed
        :param boundary_lower_direction: lowest direction
        :param boundary_higher_direction: highest direction
        :param wind_rose_data: 2-dim array with wind speed as a 1st column and wind dir as a 2nd column
        :return: 2-dim array with wind speed as a 1st column and wind dir
                as a 2nd column that conform to the boundaries
        """

        # mask for wind speed column
        log_mask_speed = (wind_rose_data[:, 0] > boundary_lower_speed) \
                         & (wind_rose_data[:, 0] <= boundary_higher_speed)
        # mask for wind direction
        log_mask_direction = (wind_rose_data[:, 1] > boundary_lower_direction) \
                             & (wind_rose_data[:, 1] <= boundary_higher_direction)

        # application of the filter on the wind_rose_data array
        return wind_rose_data[log_mask_speed & log_mask_direction]

    def write_output_file(self) -> None:
        """
        Formats series point data to the 2-dim array and saves it to the files
        """

        # Open file, name it based on the stat_input config setting,
        # (the input data file) except replace the .data
        # extension with .points1 extension

        if self.config_obj.dump_points is True:

            points = dict()
            for trace in self.traces:
                points[trace.name] = trace.r

            # create a file name from stat_input parameter
            match = re.match(r'(.*)(.data)', self.config_obj.parameters['stat_input'])
            if match:
                filename_only = match.group(1)
            else:
                filename_only = 'wind_rose'

            # save points
            self._save_points(points, filename_only + ".points")

    @staticmethod
    def _save_points(points: dict, output_file: str) -> None:
        """
        Saves dictionary of points to the file.
        :param points: dictionary of the trace's name and ist frequencies
        :param output_file: the name of the output file
        """
        try:
            all_points_formatted = dict()
            for key, value in points.items():
                data_formatted = ''
                for val in value:
                    if val is None:
                        data_formatted += " N/A"
                    else:
                        data_formatted += (" %.6f" % val)
                all_points_formatted[key] = data_formatted

            with open(output_file, "w+") as f:
                for key, value in all_points_formatted.items():
                    f.write('%s:%s\n' % (key, value))

        except TypeError:
            print('Can\'t save points to a file')


def main(config_filename=None):
    """
            Generates a sample, default, Wind rose plot using the
            default and custom config files on sample data found in this directory.
            The location of the input data is defined in either the default or
            custom config file.
        """

    # Retrieve the contents of the custom config file to over-ride
    # or augment settings defined by the default config file.
    # with open("./mpr_plot_custom.yaml", 'r') as stream:
    if not config_filename:
        config_file = util.read_config_from_command_line()
    else:
        config_file = config_filename
    with open(config_file, 'r') as stream:
        try:
            docs = yaml.load(stream, Loader=yaml.FullLoader)
        except yaml.YAMLError as exc:
            print(exc)
    # point to data file in the test dir
    if  'stat_input' not in docs:
        docs['stat_input'] = str(Path(__file__).parent.parent.parent.parent)  + '/test/wind_rose/point_stat_mpr.txt'

    try:
        plot = WindRosePlot(docs)
        plot.save_to_file()
        if plot.config_obj.show_in_browser:
            plot.show_in_browser()
        plot.write_output_file()

    except ValueError as ve:
        print(ve)


if __name__ == "__main__":
    main()
