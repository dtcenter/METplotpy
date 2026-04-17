# ============================*
 # ** Copyright UCAR (c) 2021
 # ** University Corporation for Atmospheric Research (UCAR)
 # ** National Center for Atmospheric Research (NCAR)
 # ** Research Applications Lab (RAL)
 # ** P.O.Box 3000, Boulder, Colorado, 80307-3000, USA
 # ============================*
 
 
 
"""
Class Name: mpr_plot.py
 """
__author__ = 'Tatiana Burek'

import os
from datetime import datetime
import pandas as pd
import numpy as np
import yaml

from matplotlib import pyplot as plt
from matplotlib.gridspec import GridSpec

from metplotpy.plots.base_plot import BasePlot

from metplotpy.plots.mpr_plot.mpr_plot_config import MprPlotConfig
from metplotpy.plots.wind_rose.wind_rose import WindRosePlot
from metplotpy.plots import util


class MprPlotInfo():
    """
    A placeholder for the plot. Contains additional parameters
    """

    def __init__(self):
        # plot't title
        self.title = None

        # plot's row number
        self.row = None

        # plot's column number
        self.col = None

        # xaxis parameters
        self.xaxes = dict(
            title_text='',
            range=None,
        )

        # yaxis parameters
        self.yaxes = dict(
            title_text='',
            range=None,
        )



class MprPlot(BasePlot):
    """
       Creates a set of graphics based on settings in a config file from MPR line type data.
       These are the plot types that get generated:
       - forecast and observation histograms
       -scatter plot
       -Q-Q plot
       -forecast and observation and wind errors wind rose (optional)
       This class is based on plot_mpr.R implemented by John Halley Gotway

       This class works with MET v.9.1+ output
    """

    def __init__(self, parameters: dict) -> None:
        default_conf_filename = "mpr_plot_defaults.yaml"

        # init common layout
        super().__init__(parameters, default_conf_filename)

        # instantiate a MprPlotConfig object, which holds all the necessary settings from the
        # config file that represents the BasePlot object.
        self.config_obj = MprPlotConfig(self.parameters)
        self.logger = util.get_common_logger(self.config_obj.log_level,
                                             self.config_obj.log_filename)
        self.logger.info(f"Begin matched pair plotting: {datetime.now()}")
        self.input_df = None
        self.plot_info_list = []
        self.figure = self._create_figure()

    def _read_input_data(self) -> None:
        """
            Aggregates all MPR rows from all files to one DataFrame

            Args:

            Returns:

        """
        self.logger.info(f"Reading input data: {datetime.now()}")
        dtypes = {"VERSION": 'str', 'MODEL': 'str', 'DESC': 'str', 'FCST_LEAD': int}

        # for each file
        for mpr_file in self.config_obj.mpr_file_list:
            # read data to the DataFrame
            input_data = pd.read_csv(mpr_file, delimiter=r"\s+",
                                     header='infer', float_precision='round_trip',
                                     dtype=dtypes)
            # filter MPR data
            filtered = input_data[input_data['LINE_TYPE'] == 'MPR']

            # append to the main DataFrame
            if not self.input_df:
                self.input_df = filtered
            else:
                self.input_df = pd.concat([self.input_df, filtered])

        self.logger.info(f"Finished reading input data: {datetime.now()}")

    def _create_figure(self) -> plt.Figure:
        """
            Initialise the figure and add subplots

            Returns:
                    Multipanel plot as Matplotlib figure
            """
        self.logger.info(f"Begin creating the figure: {datetime.now()}")

        # read data
        self._read_input_data()

        # Build a list of cases
        self.input_df['CASE'] = self.input_df.loc[:, 'MODEL'].astype(str) \
                                + ' ' + self.input_df.loc[:, 'FCST_VAR'].astype(str) \
                                + ' ' + self.input_df.loc[:, 'FCST_LEV'].astype(str) \
                                + ' ' + self.input_df.loc[:, 'OBS_VAR'].astype(str) \
                                + ' ' + self.input_df.loc[:, 'OBS_LEV'].astype(str) \
                                + ' ' + self.input_df.loc[:, 'OBTYPE'].astype(str) \
                                + ' ' + self.input_df.loc[:, 'VX_MASK'].astype(str) \
                                + ' ' + self.input_df.loc[:, 'INTERP_MTHD'].astype(str) \
                                + ' ' + self.input_df.loc[:, 'INTERP_PNTS'].astype(str)
        # find unique cases
        cases = self.input_df['CASE'].unique()

        # Calculate total rows
        n_rows = 0
        for case in cases:
            n_rows += 2  # for histograms and scatter/qq
            if self.config_obj.wind_rose:
                case_subset = self.input_df[self.input_df['CASE'] == case]
                if case_subset['FCST_VAR'].iloc[0] == 'UGRD':
                    n_rows += 6  # 3 wind roses * 2 rows each

        fig = plt.figure(figsize=(self.config_obj.width / 100, self.config_obj.height / 100))
        gs = GridSpec(n_rows, 2, figure=fig)

        # Loop through each of the cases and create plots
        curr_row = 0
        for case in cases:
            # Get the subset for this case
            case_subset = self.input_df[self.input_df['CASE'] == case]
            case_subset.reset_index(inplace=True, drop=True)
            case_name_1 = f"{case_subset['MODEL'][0]}: {case_subset['FCST_VAR'][0]} at {case_subset['FCST_LEV'][0]}"
            case_name_2 = f"{case_subset['OBTYPE'][0]}, {case_subset['VX_MASK'][0]}, {case_subset['INTERP_MTHD'][0]} ({case_subset['INTERP_PNTS'][0]})"
            case_title = f"{case_name_1}\n{case_name_2}"
            wind_case_title = f"{case_name_1}, {case_name_2}"

            fcst_obs_data = pd.concat([case_subset['FCST'], case_subset['OBS']])
            number_of_intervals = len(np.histogram_bin_edges(fcst_obs_data, bins='sturges')) - 1
            n_bins = util.pretty(min(fcst_obs_data), max(fcst_obs_data), number_of_intervals)

            # histogram for forecast
            ax_fcst = fig.add_subplot(gs[curr_row, 0])
            self._create_histogram(ax_fcst, case_title, case_subset, n_bins, 'FCST')

            # histogram for obs
            ax_obs = fig.add_subplot(gs[curr_row, 1])
            self._create_histogram(ax_obs, case_title, case_subset, n_bins, 'OBS')

            curr_row += 1

            # create trend line coords
            x_trend, y_trend = self._create_trend_line(case_subset)

            # Create a scatter plot
            ax_scatter = fig.add_subplot(gs[curr_row, 0])
            self._create_scatter_plot(ax_scatter, case_title, case_subset, x_trend, y_trend)

            # Create a Q-Q plot
            ax_qq = fig.add_subplot(gs[curr_row, 1])
            self._create_qq_plot(ax_qq, case_title, case_subset, x_trend, y_trend)

            curr_row += 1

            # Check for UGRD/VGRD vector pairs and plot wind rose
            if self.config_obj.wind_rose and case_subset['FCST_VAR'][0] == \
                    'UGRD' and case_subset['OBS_VAR'][0] == 'UGRD':
                # Store UGRD/VGRD indices
                vgrd_case = case.replace("UGRD", "VGRD")
                vind = self.input_df[self.input_df['CASE'] == vgrd_case]
                vind.reset_index(inplace=True, drop=True)

                if len(case_subset) == len(vind):
                    for data_type in ['FCST', 'OBS', 'FCST-OBS']:
                        ax_wr = fig.add_subplot(gs[curr_row:curr_row+2, :], projection='polar')
                        self._create_wind_rose_plot(ax_wr, case_subset, vind, wind_case_title, data_type)
                        curr_row += 2
                else:
                    self.logger.warning(" WARNING:: UGRD/VGRD vectors do not exactly match ")

        plt.tight_layout()
        self.logger.info(f"Finished creating the figure: {datetime.now()}")
        return fig

    def _create_wind_rose_plot(self, ax: plt.Axes, u_wind_data: pd.DataFrame,
                               v_wind_data: pd.DataFrame, case_title: str,
                               data_type: str) -> None:
        """
        Creates  wind rose plot on the provided axes
        :param ax: axes to plot on
        :param u_wind_data: DataFrame with U wind data
        :param v_wind_data: DataFrame with V wind data
        :param case_title: title
        :param data_type: type of the wind rose ('FCST', 'OBS', or 'FCST-OBS')
        """

        self.logger.info(f"Begin creating a wind rose plot for {data_type}")
        if data_type == 'FCST-OBS':
            title = 'Wind Errors'
        elif data_type == 'FCST':
            title = 'Forecast'
        else:
            title = 'Observed'

        # create custom parameters for the plot
        docs = {
            'show_legend': False,
            'type': data_type,
            'title': f'{title} winds {len(u_wind_data)} points\n{case_title}'
        }
        # add main parameters
        docs.update(self.config_obj.parameters)

        # create a wind rose on the provided axis
        WindRosePlot(docs, u_wind_data, v_wind_data, ax=ax)
        self.logger.info(f"Finished creating wind rose: {datetime.now()} ")

    def _create_trend_line(self, case_subset: pd.DataFrame) -> tuple:
        """
        Creates coordinates for a trend line to use in a scatter and Q-Q plots
        It calculates the intercept and slope for the line using OBS and FCST data
        :param case_subset: DataFrame with data for this case
        :return: x and y coordinates for the trend line
        """

        fcst = case_subset['FCST']
        x_coords = np.array([fcst.min(), fcst.max()])

        # find intercept and slope for the regression line
        slope_intercept = np.polyfit(case_subset['FCST'], case_subset['OBS'], 1)
        slope = slope_intercept[0]
        intercept = slope_intercept[1]

        if intercept == 0 and slope == 0:
            x_coords = np.array([-1, 1])
            y_coords = np.array([-1, 1])
        else:
            y_coords = intercept + slope * x_coords

        return x_coords, y_coords

    def _create_qq_plot(self, ax: plt.Axes, case_title: str, case_subset: pd.DataFrame,
                        x_trend: np.ndarray, y_trend: np.ndarray) -> None:
        """
        Plots the Q-Q plot on the provided axes
        :param ax: axes to plot on
        :param case_title: plot title
        :param case_subset:  DataFrame with FCST and OBS data
        :param x_trend: x coordinates for the trend line
        :param y_trend: y coordinates for the trend line
        """

        self.logger.info(f"Begin creating qq plot: {datetime.now()}")
        # subset and sort data
        qq_fcst = np.sort(case_subset['FCST'])
        qq_obs = np.sort(case_subset['OBS'])

        # create the plot
        ax.scatter(qq_fcst, qq_obs, color=self.config_obj.marker_color, edgecolors='blue', alpha=0.7)
        ax.plot(x_trend, y_trend, color='black', linestyle='--', linewidth=1)

        ax.set_title(f"Q-Q Plot of {len(case_subset)} points\n{case_title}")
        ax.set_xlabel('Forecast')
        ax.set_ylabel('Observation')
        self.logger.info(f"Finished creating qq plot: {datetime.now()}")

    def _create_scatter_plot(self, ax: plt.Axes, case_title: str, case_subset: pd.DataFrame,
                             x_trend: np.ndarray, y_trend: np.ndarray) -> None:
        """
        Plots the Scatter plot on the provided axes
        :param ax: axes to plot on
        :param case_title: plot title
        :param case_subset: DataFrame with FCST and OBS data
        :param x_trend: x coordinates for the trend line
        :param y_trend: y coordinates for the trend line
        """

        self.logger.info(f"Begin creating scatter plot: {datetime.now()}")
        # create the plot
        ax.scatter(case_subset['FCST'], case_subset['OBS'], color=self.config_obj.marker_color, edgecolors='blue', alpha=0.7)
        ax.plot(x_trend, y_trend, color='black', linestyle='--', linewidth=1)

        ax.set_title(f"Scatter Plot of {len(case_subset)} points\n{case_title}")
        ax.set_xlabel('Forecast')
        ax.set_ylabel('Observation')
        self.logger.info(f"Finished creating scatter plot: {datetime.now()}")

    def _create_histogram(self, ax: plt.Axes, case_title: str, case_subset: pd.DataFrame,
                          n_bins: np.ndarray, data_type: str) -> None:
        """
        Plots the histogram on the provided axes
        :param ax: axes to plot on
        :param case_title: plot title
        :param case_subset: DataFrame with FCST and OBS data
        :param n_bins: data bins
        :param data_type: type for 'FCST' or 'OBS' histogram
        """

        self.logger.info(f"Begin creating the histogram for {data_type}: {datetime.now()}")
        title = 'Forecast' if data_type == 'FCST' else 'Observation'

        # create plot
        ax.hist(case_subset[data_type], bins=n_bins, color='white', edgecolor='black', alpha=0.75)

        ax.set_title(f"{title} Histogram of {len(case_subset)} points\n{case_title}")
        ax.set_xlabel(title)
        ax.set_ylabel('Frequency')
        self.logger.info(f"Finished creating histogram: {datetime.now()}")


def main(config_filename=None):
    """
        Generates a mpr plot using the
        default and custom config files on sample data.
    """
    util.make_plot(config_filename, MprPlot)


if __name__ == "__main__":
    main()
