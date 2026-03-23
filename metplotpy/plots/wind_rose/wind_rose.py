# ============================*
 # ** Copyright UCAR (c) 2021
 # ** University Corporation for Atmospheric Research (UCAR)
 # ** National Center for Atmospheric Research (NCAR)
 # ** Research Applications Lab (RAL)
 # ** P.O.Box 3000, Boulder, Colorado, 80307-3000, USA
 # ============================*
 
 
 

"""
Class Name: wind_rose.py
 """
__author__ = 'Tatiana Burek'

import os
import math
from datetime import datetime
from typing import Union
import pandas as pd
import numpy as np
import re

from matplotlib import pyplot as plt
import matplotlib.ticker as mtick

from metplotpy.plots.base_plot import BasePlot
from metplotpy.plots.wind_rose.wind_rose_config import WindRoseConfig
from metplotpy.plots import util


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

        self.logger = self.config_obj.logger
        self.logger.info(f"Begin Wind Rose: {datetime.now()}")

        # if u or v DataFrames is not provided - read data from the MET stat file
        if u_wind_data is None or v_wind_data is None:
            # Read in input data, location specified in config file
            self.logger.info("Reading input data specified in config file.")
            self._read_input_data()
        else:
            self.logger.info("Reading input data from MET stat file.")
            self.u_wind_data = u_wind_data
            self.v_wind_data = v_wind_data

        self._create_figure()

    def _read_input_data(self):
        """
            Read the input data file ( UGRD and UGRD forecast vars)
            and store as a pandas dataframes.

            Args:

            Returns:

        """
        input_df = pd.read_csv(self.config_obj.stat_input, sep='\\s+', header='infer')
        self.u_wind_data = input_df[input_df['FCST_VAR'] == 'UGRD']
        self.v_wind_data = input_df[input_df['FCST_VAR'] == 'VGRD']

    def _create_figure(self):
        """
        Initialise the figure and add Wnd roses traces

        Args:


        Returns:
             Wind rose plot as Plotly figure
        """
        self.logger.info(f"Creating figure: {datetime.now()}")
        _, ax = plt.subplots(subplot_kw={'projection': 'polar'},
                               figsize=(self.config_obj.plot_width, self.config_obj.plot_height))

        wts_size_styles = self.get_weights_size_styles()
        self._add_title(ax, wts_size_styles['title'])

        self._add_title(ax, wts_size_styles['title'])
        self._add_caption(plt, wts_size_styles['caption'])

        # create wind rose traces
        self._create_traces(ax)

        # set north = 0 degrees
        ax.set_theta_zero_location('N')

        # clockwise
        ax.set_theta_direction(-1)

        # add hole in center of plot
        ax.set_rorigin(-1)

        # set location of radial labels (northwest)
        ax.set_rlabel_position(-45)

        # add % symbol to radial labels
        ax.yaxis.set_major_formatter(mtick.FormatStrFormatter('%g%%'))

        # add angular axis ticks and labels, (N, E, S, W)
        ax.set_xticks(np.deg2rad(self.config_obj.angularaxis_tickvals))
        ax.set_xticklabels(self.config_obj.angularaxis_ticktext, rotation=45, ha='right')

        if self.config_obj.radialaxis_range is not None:
            ax.set_ylim(self.config_obj.radialaxis_range)
            start, stop = self.config_obj.radialaxis_range
            step = self.config_obj.radialaxis_step
            ax.set_yticks(np.arange(start, stop + step, step))

        # turn off outermost circle (spine)
        ax.spines['polar'].set_visible(False)

        self._add_legend(ax, loc='upper left')

    def _create_traces(self, ax):
        """
        Creates wind rose traces based on the u and v data.
        Number of traces is equal to the length of wind_rose_breaks
        and has it's own color from wind_rose_marker_colors.
        Each trace's data is based on the frequency of the wind speed in the break

        Args:
        Returns:
        """
        self.logger.info(f"Creating wind rose traces: {datetime.now()}")
        self.traces = []
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
        self.logger.info("Calculating the wind speed.")
        wind_speed = [
            math.sqrt(u_wind_data[i] * u_wind_data[i] + v_wind_data[i] * v_wind_data[i])
            for i in range(len(v_wind_data))
        ]

        # calculate the wind dir in degrees for each row and bin it to angles
        self.logger.info("Calculating the wind direction.")
        wind_dir_deg = self._get_wind_dir_deg(u_wind_data, v_wind_data, wind_speed)

        # join wind_speed and wind_dir in one array
        wind_speed_dir = np.vstack((wind_speed, wind_dir_deg)).T

        # create list of angles
        angles = np.arange(0, 360, self.config_obj.wind_rose_angle)

        # distance between the centre of the bin and its edge
        step = (angles[1] - angles[0]) / 2

        # remove rows where wind direction is None
        # and converting data between 348.75 and 360 to negative
        wind_speed_dir_processed = self._process_wind_speed_dir(wind_speed_dir, angles, step)

        # determining the direction bins
        bin_edges_dir = np.append(angles - step, [angles[-1] + step])

        frequencies = np.array([])
        number_of_records = len(wind_speed_dir)
        speed_bins = []

        # If the last break is > max wind speed, omit the last break and
        # use the Mean error (me) max wind speed as the last breaks value.
        breaks = self.config_obj.wind_rose_breaks.copy()
        last_break_idx = len(breaks) - 1

        if max(wind_speed) > breaks[last_break_idx]:
            # append the max wind speed to the list of break values
            breaks.append(max(wind_speed))
        else:
            # replace the last break value with the max windspeed
            breaks = breaks[:-1]
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

        theta = np.deg2rad(angles)
        width = (2 * np.pi) / len(angles)

        bottom = np.zeros(len(angles))

        # create traces
        for i, speed_bin in enumerate(speed_bins):
            r_values = frequencies_df.loc[speed_bin, 'frequency'].values

            ax.bar(
                theta,
                r_values,
                width=width,
                bottom=bottom,
                color=self.config_obj.wind_rose_marker_colors[i],
                label=f"Wind {speed_bin}",
                linewidth=0.5,
                zorder=3,  # above the grid lines
            )

            bottom += r_values

        self.logger.info(f"Finished creating traces: {datetime.now()}")

    def _get_wind_dir_deg(self, u_wind_data, v_wind_data, wind_speed):
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

        return wind_dir_deg

    @staticmethod
    def _process_wind_speed_dir(wind_speed_dir, angles, step):
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

        return wind_speed_dir_processed

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


        # if points_path parameter doesn't exist,
        # open file, name it based on the stat_input config setting,
        # (the input data file) except replace the .data
        # extension with .points1 extension
        # otherwise use points_path path
        points = {}
        for trace in self.traces:
            points[trace.name] = trace.r

        match = re.match(r'(.*)(.txt)', self.config_obj.parameters['stat_input'])
        if self.config_obj.dump_points is True and match:
            filename = match.group(1)
            # replace the default path with the custom
            if self.config_obj.points_path is not None:
                # get the file name
                path = filename.split(os.path.sep)
                if len(path) > 0:
                    filename = path[-1]
                else:
                    filename = '.' + os.path.sep
                os.makedirs(self.config_obj.points_path, exist_ok=True)
                filename = self.config_obj.points_path + os.path.sep + filename

            # save points
            filename = filename + '.points1'
            self._save_points(points, filename)


    @staticmethod
    def _save_points(points: dict, output_file: str) -> None:
        """
        Saves dictionary of points to the file.
        :param points: dictionary of the trace's name and ist frequencies
        :param output_file: the name of the output file
        """
        try:
            all_points_formatted = {}
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
            print("Can't save points to a file")


def main(config_filename=None):
    """
            Generates a sample, default, Wind rose plot using the
            default and custom config files on sample data found in this directory.
            The location of the input data is defined in either the default or
            custom config file.
        """
    util.make_plot(config_filename, WindRosePlot)


if __name__ == "__main__":
    main()
