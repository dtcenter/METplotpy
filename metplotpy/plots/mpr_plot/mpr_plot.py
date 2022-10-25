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

import pandas as pd
import numpy as np
import yaml

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as pio

from metplotpy.plots.base_plot import BasePlot
from metplotpy.plots.constants import PLOTLY_AXIS_LINE_COLOR, PLOTLY_AXIS_LINE_WIDTH, PLOTLY_PAPER_BGCOOR

from metplotpy.plots.mpr_plot.mpr_plot_config import MprPlotConfig
from metplotpy.plots.wind_rose.wind_rose import WindRosePlot
from metplotpy.plots import util


class MprPlotInfo():
    """
    A placeholder for the  plot. Contains a plotly traces and the additional parameters
    """

    def __init__(self):
        # plotly traces for the plot
        self.traces = []

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
        self.input_df = None
        self.plot_info_list = []
        self.figure = self._create_figure()

    def _read_input_data(self) -> None:
        """
            Aggregates all MPR rows from all files to one DataFrame

            Args:

            Returns:

        """
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
                self.input_df = self.input_df.append(filtered)

    def _create_figure(self) -> go.Figure:
        """
            Initialise the figure and add Wnd roses traces

            Args:

            Returns:
                    Multipanel plot as Plotly figure
            """

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

        # each case has at least 2 rows (4 plots)
        n_rows = len(cases) * 2

        # Loop through each of the cases and create plots
        self._create_plots(cases)

        # Initialize figure with subplots
        subplot_titles = []
        specs = []
        for plot_info in self.plot_info_list:
            # collect titles
            subplot_titles.append(plot_info.title)

            # add additional specs for the wind rose
            if plot_info.col == 1:
                if isinstance(plot_info.traces[0], go.Barpolar):
                    n_rows = n_rows + 2
                    specs.append([{'type': 'polar', 'colspan': 2, 'rowspan': 2}, None])
                    specs.append([None, None])
                else:
                    specs.append([{}, {}])

        fig = make_subplots(rows=int(n_rows), cols=2,
                            subplot_titles=subplot_titles,
                            shared_yaxes=False, specs=specs)

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

        # add plots and traces to it's specified locations
        for plot_info in self.plot_info_list:
            if not isinstance(plot_info.traces[0], go.Barpolar):
                # for line plots
                for trace in plot_info.traces:
                    fig.add_trace(trace, row=plot_info.row, col=plot_info.col)

                fig.update_xaxes(title_text=plot_info.xaxes['title_text'],
                                 range=plot_info.xaxes['range'],
                                 row=plot_info.row, col=plot_info.col)
                fig.update_yaxes(title_text=plot_info.yaxes['title_text'],
                                 # range=plot_info.yaxes['range'],
                                 row=plot_info.row, col=plot_info.col)
            else:
                # for wind rose
                for trace in plot_info.traces:
                    fig.add_trace(trace, row=plot_info.row, col=plot_info.col)

        # additional setings for the wind rose plots
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

        # general settings
        fig.update_layout(
            showlegend=False,
            plot_bgcolor=PLOTLY_PAPER_BGCOOR,
            bargap=0,
            margin=dict(
                l=50,
                r=50,
                b=100,
                t=100,
                pad=4
            ),
            autosize=False,
            width=self.config_obj.width,
            height=self.config_obj.height,
        )
        return fig

    def _create_plots(self, cases: np.ndarray) -> None:
        """
        For the each case create a set of plots:
        - histogram for forecast
        - histogram for obs
        - scatter plot
        - Q-Q plot
        - wind rose plots for forecast, obs winds and wind error (if requested)
        Calculates the position and the title for each plot
        :param cases:  list of unique cases
        :return:
        """
        row_n = 1
        for case_ind, case in enumerate(cases):
            # Get the subset for this case
            case_subset = self.input_df[self.input_df['CASE'] == case]
            case_subset.reset_index(inplace=True, drop=True)
            case_name_1 = f"{case_subset['MODEL'][0]}: {case_subset['FCST_VAR'][0]} at {case_subset['FCST_LEV'][0]}"
            case_name_2 = f"{case_subset['OBTYPE'][0]}, {case_subset['VX_MASK'][0]}, {case_subset['INTERP_MTHD'][0]} ({case_subset['INTERP_PNTS'][0]})"
            case_title = f"{case_name_1}<br>{case_name_2}"
            wind_case_title = f"{case_name_1}, {case_name_2}"

            fcst_obs_data = pd.concat([case_subset['FCST'], case_subset['OBS']])
            number_of_intervals = len(np.histogram_bin_edges(fcst_obs_data, bins='sturges')) - 1
            n_bins = util.pretty(min(fcst_obs_data), max(fcst_obs_data), number_of_intervals)

            # histogram for forecast
            info_fcst = self._create_histogtam(case_title, case_subset, n_bins, 'FCST')
            if info_fcst:
                info_fcst.row = row_n
                self.plot_info_list.append(info_fcst)

            # histogram for obs
            info_obs = self._create_histogtam(case_title, case_subset, n_bins, 'OBS')
            if info_obs:
                info_obs.row = row_n
                self.plot_info_list.append(info_obs)

            row_n = row_n + 1
            # create trend line
            trend_line = self._create_trend_line(case_subset)

            # Create a scatter plot
            scatter = self._create_scatter_plot(case_title, case_subset, trend_line)
            scatter.row = row_n
            self.plot_info_list.append(scatter)

            # Create a Q-Q plot
            qq_plot = self._create_qq_plot(case_title, case_subset, trend_line)
            qq_plot.row = row_n
            self.plot_info_list.append(qq_plot)
            row_n = row_n + 1

            # Check for UGRD/VGRD vector pairs and plot wind rose
            if self.config_obj.wind_rose and case_subset['FCST_VAR'][0] == \
                    'UGRD' and case_subset['OBS_VAR'][0] == 'UGRD':
                # Store UGRD/VGRD indices
                vgrd_case = case.replace("UGRD", "VGRD")
                vind = self.input_df[self.input_df['CASE'] == vgrd_case]
                vind.reset_index(inplace=True, drop=True)

                # in Rscript:  sum(data$OBS_SID[uind] == data$OBS_SID[v_wind_data]) != sum(uind))
                if len(case_subset) == len(vind):

                    info = self._create_wind_rose_plot(case_subset, vind, wind_case_title, 'FCST')
                    info.row = row_n
                    self.plot_info_list.append(info)
                    row_n = row_n + 2

                    info = self._create_wind_rose_plot(case_subset, vind, wind_case_title, 'OBS')
                    info.row = row_n
                    self.plot_info_list.append(info)
                    row_n = row_n + 2

                    info = self._create_wind_rose_plot(case_subset, vind, wind_case_title, 'FCST-OBS')
                    info.row = row_n
                    self.plot_info_list.append(info)
                    row_n = row_n + 2
                else:
                    print("WARNING: UGRD/VGRD vectors do not exactly match")

    def _create_wind_rose_plot(self, u_wind_data: pd.DataFrame,
                               v_wind_data: pd.DataFrame, case_title: str,
                               data_type: str) -> MprPlotInfo:
        """
        Creates  MprPlotInfo for the wind rose plot
        :param u_wind_data: DataFrame with a requared column named 'FCST_VAR' with values 'UGRD'
            and  columns 'OBS' and 'FCST' with U data
        :param v_wind_data: DataFrame with a requared column named 'FCST_VAR' with values 'VGRD'
            and  columns 'OBS' and 'FCST' with V data
        :param case_title: title
        :param data_type: type of the wind rose.Indicates which data to use for the plot.
            Can be 'FCST', 'OBS' or 'FCST-OBS'
        :return: MprPlotInfo object with wind rose traces and title
        """

        if data_type == 'FCST-OBS':
            title = 'Wind Errors'
        elif data_type == 'FCST':
            title = 'Forecast'
        else:
            title = 'Observed'

        # init MprPlotInfo
        info = MprPlotInfo()
        info.col = 1
        info.title = f'{title} winds {len(u_wind_data)} points<br>{case_title}<br>    '

        # create custom parameters for the plot
        docs = {
            'create_figure': False,
            'show_legend': False,
            'type': data_type
        }
        # add main parameters
        docs.update(self.config_obj.parameters)

        # create a wind rose
        plot = WindRosePlot(docs, u_wind_data, v_wind_data)

        # record traces
        for trace in plot.traces:
            info.traces.append(trace)

        return info

    def _create_trend_line(self, case_subset: pd.DataFrame) -> go.Scatter:
        """
        Creates a trend line to use in a scatter and Q-Q plots
        It calculates the intercept and slope for the line using OBS and FCST data
        :param case_subset: DataFrame with data for this case
        :return: a trend line as a Plotly Scatter
        """

        fcst = case_subset['FCST']
        x_coords = np.array([fcst.min(), fcst.max()])

        # find intercept and slope for the regression line
        slope_intercept = np.polyfit(case_subset['FCST'], case_subset['OBS'], 1)
        slope = slope_intercept[0]
        intercept = slope_intercept[1]

        if intercept == 0 and slope == 0:
            x_coords = [-1, 1]
            y_coords = [-1, 1]
        else:
            y_coords = intercept + slope * x_coords

        trend_line = go.Scatter(x=x_coords,
                                y=y_coords,
                                line={'color': 'black',
                                      'width': 1,
                                      'dash': 'dash'},
                                showlegend=False,
                                mode='lines',
                                name='Trend Line'
                                )
        return trend_line

    def _create_qq_plot(self, case_title: str, case_subset: pd.DataFrame,
                        trend_line: go.Scatter) -> MprPlotInfo:
        """
        MprPlotInfo for the Q-Q plot
        :param case_title: plot title
        :param case_subset:  DataFrame with FCST and OBS data
        :param trend_line: Scatter for the trend line
        :return: MprPlotInfo object with Q-Q plot traces and title
        """

        # subset and sort data
        qq_fcst = case_subset['FCST'].tolist()
        qq_fcst.sort()

        qq_obs = case_subset['OBS'].tolist()
        qq_obs.sort()

        # create the plot
        qq_plot = go.Scatter(
            x=qq_fcst,
            y=qq_obs,
            mode='markers',
            name='Q-Q Plot',
            marker=dict(
                color=self.config_obj.marker_color,
                line=dict(
                    color='rgb(174,167,250)'
                )
            )
        )

        # init MprPlotInfo
        info = MprPlotInfo()
        info.col = 2
        info.traces.append(qq_plot)
        info.traces.append(trend_line)
        info.title = f"Q-Q Plot of {len(case_subset)} points<br>{case_title}"
        info.xaxes['title_text'] = 'Forecast'
        info.yaxes['title_text'] = 'Observation'
        return info

    def _create_scatter_plot(self, case_title: str, case_subset: pd.DataFrame,
                             trend_line: go.Scatter) -> MprPlotInfo:
        """
        MprPlotInfo for the Scatter plot
        :param case_title: plot title
        :param case_subset: DataFrame with FCST and OBS data
        :param trend_line: Scatter for the trend line
        :return: MprPlotInfo object with Scatter plot traces and title
        """

        # create the plot
        scatter = go.Scatter(
            x=case_subset['FCST'],
            y=case_subset['OBS'],
            mode='markers',
            name='Scatter Plot',
            marker=dict(
                color=self.config_obj.marker_color,
                line=dict(
                    color='rgb(174,167,250)'
                )
            )
        )

        # init MprPlotInfo
        info = MprPlotInfo()
        info.col = 1
        info.traces.append(scatter)
        info.traces.append(trend_line)
        info.title = f"Scatter Plot of {len(case_subset)} points<br>{case_title}"
        info.xaxes['title_text'] = 'Forecast'
        info.yaxes['title_text'] = 'Observation'
        return info

    def _create_histogtam(self, case_title: str, case_subset: pd.DataFrame,
                          n_bins: np.ndarray, data_type: str) -> MprPlotInfo:
        """
        Creates  MprPlotInfo for the histogtam
        :param case_title: plot title
        :param case_subset: DataFrame with FCST and OBS data
        :param n_bins: data bins
        :param data_type: type for 'FCST' or 'OBS' histogtam
        :return: MprPlotInfo object with Scatter plot traces and title
        """


        info = MprPlotInfo()
        if data_type == 'FCST':
            title = 'Forecast'
            info.col = 1
        else:
            title = 'Observation'
            info.col = 2

        # calculate histogram data and bins
        hist_kwargs = dict()
        hist_kwargs['range'] = (min(case_subset[data_type]), max(case_subset[data_type]))
        hist_counts, hist_bins = \
            np.histogram(case_subset[data_type], n_bins, weights=None, **hist_kwargs)

        hist_bins = 0.5 * (hist_bins[:-1] + hist_bins[1:])

        # create plot
        histogram = go.Bar(
            x=hist_bins,
            y=hist_counts,
            name=f"{title} Histogram",
            marker=dict(
                color='#ffffff',
                line=dict(
                    color='rgb(1, 1, 1)',
                    width=1
                )
            )
        )

        # init MprPlotInfo
        info.traces.append(histogram)
        info.title = f"{title} Histogram of {len(case_subset)} points<br>{case_title}"
        info.xaxes['title_text'] = title
        info.xaxes['range'] = [0, n_bins[-1]]
        info.yaxes['title_text'] = 'Frequency'
        return info

    def save_to_file(self) -> None:
        """Saves the image to a file specified in the config file.
         Prints a message if fails

        Args:

        Returns:

        """
        image_name = self.get_config_value('plot_filename')
        pio.kaleido.scope.default_format = "png"
        pio.kaleido.scope.default_height = self.config_obj.height
        pio.kaleido.scope.default_width = self.config_obj.width
        if self.figure:
            try:
                self.figure.write_image(image_name)
            except FileNotFoundError:
                print("Can't save to file " + image_name)
            except ValueError as ex:
                print(ex)
        else:
            print("Oops!  The figure was not created. Can't save.")


def main(config_filename=None):
    """
        Generates a sample, default, line plot using the
        default and custom config files on sample data found in this directory.
        The location of the input data is defined in either the default or
        custom config file.
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
        plot = MprPlot(docs)
        plot.save_to_file()
        if plot.config_obj.show_in_browser:
            plot.show_in_browser()
    except ValueError as ve:
        print(ve)


if __name__ == "__main__":
    main()
