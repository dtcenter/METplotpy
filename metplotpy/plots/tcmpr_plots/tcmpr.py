# ============================*
# ** Copyright UCAR (c) 2020
# ** University Corporation for Atmospheric Research (UCAR)
# ** National Center for Atmospheric Research (NCAR)
# ** Research Applications Lab (RAL)
# ** P.O.Box 3000, Boulder, Colorado, 80307-3000, USA
# ============================*


"""
Class Name: tcmpr.py
 """
import copy
import glob
import os
import sys
from datetime import datetime
from typing import Union
# Ignore DeprecationWarning for pyarrow in Pandas3 for now
import warnings
warnings.filterwarnings('ignore')
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import yaml
from plotly.graph_objects import Figure
from plotly.subplots import make_subplots

import metcalcpy.util.utils as calc_util
from metcalcpy.event_equalize import event_equalize
from metplotpy.plots import util
from metplotpy.plots.base_plot import BasePlot
from metplotpy.plots.constants import PLOTLY_AXIS_LINE_COLOR, PLOTLY_AXIS_LINE_WIDTH, PLOTLY_PAPER_BGCOOR
from metplotpy.plots.tcmpr_plots.tcmpr_config import TcmprConfig
from metplotpy.plots.tcmpr_plots.tcmpr_series import TcmprSeries
from metplotpy.plots.tcmpr_plots.tcmpr_util import init_hfip_baseline, common_member, get_dep_column

PLOTS_WITH_BASELINE = ['boxplot', 'point', 'mean', 'skill_mn']


class Tcmpr(BasePlot):
    """  Generates a Plotly  plot for 1 or more traces
         where each box is represented by a text point data file.
    """

    def __init__(self, config_obj, column_info, col, case_data, input_df, stat_name):
        """ Creates a plot, based on
            settings indicated by parameters.

            Args:
            @param parameters: dictionary containing user defined parameters

        """

        # init common layout
        super().__init__(None, "tcmpr_defaults.yaml")

        # Set up Logging
        self.logger = util.get_common_logger(config_obj.log_level, config_obj.log_filename)

        self.series_list = []

        # instantiate a BoxConfig object, which holds all the necessary settings from the
        # config file that represents the BasePlot object (Box).
        self.config_obj = config_obj

        # Read in input data, location specified in config file
        self.input_df = input_df

        # Read the TCMPR column information from a data file.
        self.column_info = column_info

        self.cur_baseline = "no"
        self.cur_baseline_data = None

        self.case_data = case_data

        self.col = col
        self.title = self.config_obj.title
        self.baseline_lead_time = 'lead'
        self.yaxis_1 = self.config_obj.yaxis_1

        self.plot_filename = f"{self.config_obj.plot_dir}{os.path.sep}{self.config_obj.list_stat_1[0]}_{self.config_obj.plot_type_list}.png"
        # Check that we have all the necessary settings for each series
        # TODO  implement the consistency check if no series values were specified
        # is_config_consistent = self.config_obj._config_consistency_check()
        # if not is_config_consistent:
        #     raise ValueError("The number of series defined by series_val_1/2 and derived curves is"
        #                      " inconsistent with the number of settings"
        #                      " required for describing each series. Please check"
        #                      " the number of your configuration file's plot_i,"
        #                      " plot_disp, series_order, user_legend,"
        #                      " colors, and series_symbols settings.")

        # if series and indy_vals were not provided - use all values from the file
        if len(self.config_obj.indy_vals) == 0 and self.config_obj.indy_var != '':
            self.config_obj.indy_vals = sorted(self.input_df[self.config_obj.indy_var].unique())

    def _create_series(self, input_data, stat_name):
        """
           Generate all the series objects that are to be displayed as specified by the plot_disp
           setting in the config file.  The points are all ordered by datetime.  Each series object
           is represented by a box in the diagram, so they also contain information
           for  plot-related/appearance-related settings (which were defined in the config file).

           Args:
               input_data:  The input data in the form of a Pandas dataframe.
                            This data will be subset to reflect the series data of interest.
               stat_name:   The name of the current 'statistic', as specified as the list_stat_1
                            list of values in the configuration file (e.g. TK_ERR, ABS(AMAX_WIND-BMAX_WIND), etc.)
                            Default is None.

           Returns:
               a list of series objects that are to be displayed


        """
        self.logger.info(f"Creating series for {stat_name}: {datetime.now()}")
        series_list = []

        # add series for y1 axis

        # Determine the series list based on the current
        # list_stat_1 value (e.g. TK_ERR, ABS(AMAX_WIND-BMAX_WIND), etc.) under consideration.
        all_series = self.config_obj.get_series_y(1)

        # Limit the series to only the current statistic, list_stat_1 in config file
        series_by_stat = [cur for cur in all_series if stat_name in cur]
        num_series_y1 = len(series_by_stat)
        for i, name in enumerate(series_by_stat):
             if not isinstance(name, list):
                 name = [name]
             # cur_plot_type = self.config_obj.get_config_value('plot_type_list')
             series_obj = TcmprSeries(self.config_obj, i, input_data, series_list,
                                      name, stat_name)
             series_list.append(series_obj)

        # add derived for y1 axis
        for i, name in enumerate(self.config_obj.get_config_value('derived_series_1')):
            # add default operation value if it is not provided
            if len(name) == 2:
                name.append("DIFF")
            # include the series only if the name is valid
            if len(name) == 3:
                # add stat if needed
                oper = name[2]
                name[:] = [(s + ' ' + stat_name) if ' ' not in s else s for s in name[:2]]
                name.append(oper)
                series_obj = TcmprSeries(self.config_obj, num_series_y1 + i, input_data, series_list, name, stat_name)
                series_list.append(series_obj)

        # reorder series
        series_list = self.config_obj.create_list_by_series_ordering(series_list)
        self.logger.info(f"Series list created: {datetime.now()}")
        return series_list

    def _calc_stag_adjustments(self) -> list:
        """
        Calculates the x-axis adjustment for each point if requested.
        It needed so the points and CIs for each x-axis values don't be placed on top of each other

        :return: the list of the adjustment values
        """

        # get the total number of series
        num_stag = len(self.config_obj.all_series_y1)

        # calculate staggering values

        dbl_adj_scale = (len(self.config_obj.indy_vals) - 1) / 100
        stag_vals = np.linspace(-(num_stag / 2) * dbl_adj_scale,
                                (num_stag / 2) * dbl_adj_scale,
                                num_stag,
                                True)
        stag_vals = stag_vals + dbl_adj_scale / 2
        return stag_vals

    def _add_hfip_baseline(self):

        self.logger.info(f"Adding the hfip baseline: {datetime.now()}")
        # Add  baseline for each lead time
        if self.cur_baseline_data is not None:
            baseline_x_values = []
            baseline_y_values = []
            lead_times = self.config_obj.indy_vals
            lead_times.sort()
            for ind, lead in enumerate(lead_times):
                # Get data for the current lead time
                baseline_lead = self.cur_baseline_data[(self.cur_baseline_data['LEAD_HR'] == lead)][
                    'VALUE'].tolist()
                if self.baseline_lead_time == 'ind':
                    current_leads = [ind] * len(baseline_lead)
                else:
                    current_leads = [lead] * len(baseline_lead)

                baseline_x_values.extend(current_leads)
                baseline_y_values.extend(baseline_lead)

            self.figure.add_trace(
                go.Scatter(x=baseline_x_values,
                           y=baseline_y_values,
                           showlegend=True,
                           mode='markers',
                           textposition="top right",
                           name=self.cur_baseline,
                           marker=dict(size=8,
                                       color='rgb(0,0,255)',
                                       line=dict(
                                           width=1,
                                           color='rgb(0,0,255)'
                                       ),
                                       symbol='diamond-cross-open',
                                       )
                           )
            )

    def _yaxis_limits(self) -> None:
        """
        Apply limits on y2 axis if needed
        """
        if len(self.config_obj.parameters['ylim']) > 0:
            self.figure.update_layout(yaxis={'range': [self.config_obj.parameters['ylim'][0],
                                                       self.config_obj.parameters['ylim'][1]],
                                             'autorange': False})

    def _create_layout(self) -> Figure:
        """
        Creates a new layout based on the properties from the config file
        including plots size, annotation and title

        :return: Figure object
        """
        # create annotation
        annotation_caption = {'text': util.apply_weight_style(self.config_obj.parameters['plot_caption'],
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
                              }
        annotation_subtitle = {'text': util.apply_weight_style(self.config_obj.subtitle,
                                                               1),
                               'align': 'center',
                               'showarrow': False,
                               'xref': 'paper',
                               'yref': 'paper',
                               'x': 0.5,
                               'y': -0.26,
                               'font': {
                                   'size': self.config_obj.caption_size,
                                   'color': self.config_obj.parameters['caption_col']
                               }
                               }

        # create title
        title = {'text': util.apply_weight_style(self.title,
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

        # create a layout and allow y2 axis
        fig = make_subplots(specs=[[{"secondary_y": True}]])

        # add size, annotation, title
        fig.update_layout(
            width=self.config_obj.plot_width,
            height=self.config_obj.plot_height,
            margin=self.config_obj.plot_margins,
            paper_bgcolor=PLOTLY_PAPER_BGCOOR,
            annotations=[annotation_caption, annotation_subtitle],
            title=title,
            plot_bgcolor=PLOTLY_PAPER_BGCOOR
        )

        return fig

    def _add_xaxis(self) -> None:
        """
        Configures and adds x-axis to the plot
        """
        self.figure.update_xaxes(title_text=self.config_obj.xaxis,
                                 linecolor=PLOTLY_AXIS_LINE_COLOR,
                                 linewidth=PLOTLY_AXIS_LINE_WIDTH,
                                 showgrid=self.config_obj.grid_on,
                                 ticks="outside",
                                 zeroline=False,
                                 gridwidth=self.config_obj.parameters['grid_lwd'],
                                 gridcolor=self.config_obj.blended_grid_col,
                                 automargin=True,
                                 title_font={
                                     'size': self.config_obj.x_title_font_size
                                 },
                                 title_standoff=abs(self.config_obj.parameters['xlab_offset']),
                                 tickangle=self.config_obj.x_tickangle,
                                 tickfont={'size': self.config_obj.x_tickfont_size},
                                 tickformat='d'
                                 )
        # reverse xaxis if needed
        if hasattr(self.config_obj, 'xaxis_reverse') and self.config_obj.xaxis_reverse is True:
            self.figure.update_xaxes(autorange="reversed")

    def _add_yaxis(self) -> None:
        """
        Configures and adds y-axis to the plot
        """
        self.figure.update_yaxes(title_text=
                                 util.apply_weight_style(self.yaxis_1,
                                                         self.config_obj.parameters['ylab_weight']),
                                 secondary_y=False,
                                 linecolor=PLOTLY_AXIS_LINE_COLOR,
                                 linewidth=PLOTLY_AXIS_LINE_WIDTH,
                                 showgrid=self.config_obj.grid_on,
                                 zeroline=False,
                                 ticks="inside",
                                 gridwidth=self.config_obj.parameters['grid_lwd'],
                                 gridcolor=self.config_obj.blended_grid_col,
                                 automargin=True,
                                 title_font={
                                     'size': self.config_obj.y_title_font_size
                                 },
                                 title_standoff=self.config_obj.parameters['ylab_offset'],
                                 tickangle=self.config_obj.y_tickangle,
                                 tickfont={'size': self.config_obj.y_tickfont_size},
                                 exponentformat='none'
                                 )

    def _add_x2axis(self, vals) -> None:
        """
        Creates x2axis based on the properties from the config file
        and attaches it to the initial Figure

        """
        if self.config_obj.show_nstats:
            # new_list = ['<span style="color:blue;">' +str(x) +'</span>'+'<br>AAA' for x in n_stats

            n_stats = [''] * len(self.config_obj.indy_vals)

            for ind, val_for_indy in enumerate(n_stats):
                if self.config_obj.use_ee is True and len(self.series_list) > 0:
                    n_stats[ind] = n_stats[ind] + '<span style="color:black;">' + str(
                        self.series_list[0].series_points['nstat'][ind]) + '</span><br>'
                else:
                    for series in self.series_list:
                        n_stats[ind] = n_stats[ind] + '<span style="color:' + series.color + ';">' + str(
                            series.series_points['nstat'][ind]) + '</span><br>'

            self.figure.update_layout(xaxis2={'title_text': util.apply_weight_style('',
                                                                                    self.config_obj.parameters[
                                                                                        'x2lab_weight']
                                                                                    ),
                                              'linecolor': PLOTLY_AXIS_LINE_COLOR,
                                              'linewidth': PLOTLY_AXIS_LINE_WIDTH,
                                              'overlaying': 'x',
                                              'side': 'top',
                                              'showgrid': False,
                                              'zeroline': False,
                                              'title_font': {'size': self.config_obj.x2_title_font_size},
                                              'title_standoff': abs(self.config_obj.parameters['x2lab_offset']),
                                              'tickmode': 'array',
                                              'tickvals': vals,
                                              'ticktext': n_stats,
                                              'tickangle': self.config_obj.x2_tickangle,
                                              'tickfont': {'size': self.config_obj.x2_tickfont_size},
                                              'scaleanchor': 'x'
                                              }
                                      )
            # reverse x2axis if needed
            if self.config_obj.xaxis_reverse is True:
                self.figure.update_layout(xaxis2={'autorange': "reversed"})

            # need to add an invisible line with all values = None
            self.figure.add_trace(
                go.Scatter(y=[None] * len(vals), x=vals,
                           xaxis='x2', showlegend=False)
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
                                          },
                                          'traceorder': 'normal'
                                          })
        if hasattr(self.config_obj, 'xaxis_reverse') and self.config_obj.xaxis_reverse is True:
            self.figure.update_layout(legend={'traceorder': 'reversed'})

    def save_to_file(self):
        """Saves the image to a file specified in the config file.
         Prints a message if fails

        Args:

        Returns:

        """

        # Create the directory for the output plot if it doesn't already exist
        dirname = os.path.dirname(os.path.abspath(self.plot_filename))
        try:
           os.makedirs(dirname, exist_ok=True)
        except FileExistsError:
            pass

        self.logger.info(f'Saving the image file: {self.plot_filename}')
        if self.figure:
            try:
                self.figure.write_image(file=self.plot_filename, format='png',
                                        width=self.config_obj.plot_width,
                                        height=self.config_obj.plot_height,
                                        scale=2)
            except FileNotFoundError:
                self.logger.error(f"Cannot save to file {self.plot_filename}")
            except ValueError as ex:
                print(ex)
        else:
            self.logger.error(f"The figure wasn't created.  Nothing to save")

    @staticmethod
    def find_min_max(series: TcmprSeries, yaxis_min: Union[float, None],
                     yaxis_max: Union[float, None]) -> tuple:
        """
        Finds min and max value between provided min and max and y-axis CI values of this series
        if yaxis_min or yaxis_max is None - min/max value of the series is returned

        :param series: series to use for calculations
        :param yaxis_min: previously calculated min value
        :param yaxis_max: previously calculated max value
        :return: a tuple with calculated min/max
        """
        # calculate series upper and lower limits of CIs

        # Skip lead times for which no data is found
        if len(series.series_data) == 0:
            return yaxis_min, yaxis_max

        # Get the values to be plotted for this lead times
        all_values = series.series_points['val']

        if 'ncl' in series.series_points:
            all_values = all_values + series.series_points['ncl']
        if 'ncu' in series.series_points:
            all_values = all_values + series.series_points['ncu']

        if len(all_values) == 0:
            return yaxis_min, yaxis_max

        low_range = min([v for v in all_values if v is not None])
        upper_range = max([v for v in all_values if v is not None])

        # find min max
        if yaxis_min is None or yaxis_max is None:
            return low_range, upper_range

        return min(yaxis_min, low_range), max(yaxis_max, upper_range)

def perform_event_equalization(input_df:pd.DataFrame, is_skill:bool, config_obj:dict) -> pd.DataFrame:
    '''
       Performs event equalization.  The skill_mn and skill_md plots require the skill_ref value to be included.

    Args:
       @param input_df: The original input data, comprised of all the specified data files.

       @param is_skill: Boolean value to indicate whether the plot type is skill_mn or skill_md.

       @param config_obj: A dictionary representation of the settings and values in the yaml config file.

    Returns:
        output_data: pd.Dataframe containing the results

    '''


    logger = util.get_common_logger(config_obj.log_level, config_obj.log_filename)
    logger.info(f"Performing requested event equalization: {datetime.now()}")
    output_data = pd.DataFrame()
    series = copy.deepcopy(config_obj.parameters['series_val_1'])
    if is_skill:
        series['AMODEL'].extend(config_obj.skill_ref)

    for series_var, series_var_vals in series.items():
        series_data = input_df[input_df[series_var].isin(series_var_vals)]

        # Run event_equalize as a process to capture the stdout to the logfile
        series_data = event_equalize(series_data, '', config_obj.parameters['series_val_1'], [], [], True, False)
        if output_data.empty:
            output_data = series_data
        else:
            output_data.append(series_data)

    return output_data


def main(config_filename=None):
    """
        Generates a sample, default, TCMPR plot using a combination of
        default and custom config files on sample data found in this directory.
        The location of the input data is defined in either the default or
        custom config file.
        Args:
                @param config_filename: default is None, the name of the custom config file to apply
    """

    # Retrieve the contents of the custom config file to over-ride
    # or augment settings defined by the default config file.
    if not config_filename:
        config_file = util.read_config_from_command_line()
    else:
        config_file = config_filename
    with open(config_file, 'r') as stream:
        try:
            docs = yaml.load(stream, Loader=yaml.FullLoader)
        except yaml.YAMLError as exc:
            print(exc)

    # Determine location of the default YAML config files and then
    # read defaults stored in YAML formatted file into the dictionary
    if 'METPLOTPY_BASE' in os.environ:
        location = os.path.join(os.environ['METPLOTPY_BASE'], 'metplotpy/plots/config')
    else:
        location = os.path.realpath(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config'))

    with open(os.path.join(location, "tcmpr_defaults.yaml"), 'r') as stream:
        try:
            defaults = yaml.load(stream, Loader=yaml.FullLoader)
        except yaml.YAMLError as exc:
            print(exc)

    # merge user defined parameters into defaults if they exist
    docs = {**defaults, **docs}

    config_obj = TcmprConfig(docs)

    # Create the requested plot(s)
    create_plot(config_obj)


def create_plot(config_obj: dict) -> None:
    """
        One or more TCMPR plots is generated. Event equalization is performed if
        it was requested by a setting in the yaml configuration file.

        Args:
           @param config_obj:  The config object containing all the necessary information obtained
                               from the yaml configuration file.

        Returns: None, creates one or more plots as specified in the yaml config file
    """

    # Find input files, they must have the .tcst extension and filename must have
    # the prefix "tc_pairs" (e.g. tc_pairs_gfso_20220401.tcst)
    tcst_files = []
    # list all .tcst files in tcst_dir
    if config_obj.tcst_dir is not None and len(config_obj.tcst_dir) > 0 and os.path.exists(config_obj.tcst_dir):
        tcst_files = glob.glob(config_obj.tcst_dir + 'tc_pairs*.tcst')
    # add specific files
    for file in config_obj.tcst_files:
        if file not in tcst_files:
            tcst_files.append(file)

    orig_input_df = read_tcst_files(config_obj, tcst_files)
    input_df = orig_input_df.copy(deep=True)

    # Define a demo and retro column

    # Note: Currently not supported, leave commented out for now.

    # input_df = orig_input_df.copy(deep=True)
    # if config_obj.demo_yr is not None and config_obj.demo_yr != 'NA':
    #     demo_yr_obj = datetime.strptime(str(config_obj.demo_yr), '%Y')
    #     input_df.loc[input_df['VALID_TIME'] >= demo_yr_obj, "TYPE"] = "DEMO"
    #     input_df.loc[input_df['VALID_TIME'] < demo_yr_obj, "TYPE"] = "RETRO"

    # Read the TCMPR column information from a data file.
    column_info = pd.read_csv(os.path.join(sys.path[0], config_obj.column_info_file),
                              sep=r'\s+', header='infer',
                              quotechar='"', skipinitialspace=True, encoding='utf-8')

    logger = util.get_common_logger(config_obj.log_level, config_obj.log_filename)
\
    for plot_type in config_obj.plot_type_list:

        # Apply event equalization, if requested
        # Event equalization is different for the skill_mn and skill_md
        is_skill = False
        if config_obj.use_ee:
            if plot_type == 'skill_mn' or plot_type == 'skill_md':
                is_skill = True
                # perform event equalization on the skill_mn|skill_md plot type
                logger.info(f"Perform event equalization for {plot_type}: {datetime.now()}")
                output_result = perform_event_equalization(orig_input_df, is_skill, config_obj)
                input_df = output_result
            else:
                logger.info(f"Perform event equalization for {plot_type}: {datetime.now()}")
                output_result = perform_event_equalization(orig_input_df, is_skill, config_obj)
                input_df = output_result

        input_df.rename({'equalize': 'CASE'}, axis=1, inplace=True)
        # Sort the data by the CASE column
        input_df = input_df.sort_values(by=['CASE', 'AMODEL'])
        input_df.reset_index(drop=True, inplace=True)

        for cur_stat in config_obj.list_stat_1:
            logger.info(f"Statistic of interest: {cur_stat}")
            # col_to_plot = get_dep_column(config_obj.list_stat_1[0], column_info, input_df)
            col_to_plot = get_dep_column(cur_stat, column_info, input_df)
            input_df['PLOT'] = col_to_plot['val']

            baseline_data = None
            if common_member(config_obj.plot_type_list, PLOTS_WITH_BASELINE):
                baseline_data = init_hfip_baseline(config_obj, config_obj.baseline_file, input_df)

            plot = None
            common_case_data = None
            try:
                if plot_type == 'boxplot':
                    from metplotpy.plots.tcmpr_plots.box.tcmpr_box import TcmprBox
                    plot = TcmprBox(config_obj, column_info, col_to_plot, common_case_data, input_df, baseline_data,
                                    cur_stat)
                elif plot_type == 'point':
                    from metplotpy.plots.tcmpr_plots.box.tcmpr_point import TcmprPoint
                    plot = TcmprPoint(config_obj, column_info, col_to_plot, common_case_data, input_df, baseline_data,
                                      cur_stat)
                elif plot_type == 'mean':
                    from metplotpy.plots.tcmpr_plots.line.mean.tcmpr_line_mean import TcmprLineMean
                    plot = TcmprLineMean(config_obj, column_info, col_to_plot, common_case_data, input_df,
                                         baseline_data, cur_stat)
                elif plot_type == 'median':
                    from metplotpy.plots.tcmpr_plots.line.median.tcmpr_line_median import TcmprLineMedian
                    plot = TcmprLineMedian(config_obj, column_info, col_to_plot, common_case_data, input_df, cur_stat)
                elif plot_type == 'relperf':
                    from metplotpy.plots.tcmpr_plots.relperf.tcmpr_relperf import TcmprRelPerf
                    plot = TcmprRelPerf(config_obj, column_info, col_to_plot, common_case_data, input_df, cur_stat)
                elif plot_type == 'rank':
                    from metplotpy.plots.tcmpr_plots.rank.tcmpr_rank import TcmprRank
                    plot = TcmprRank(config_obj, column_info, col_to_plot, common_case_data, input_df, cur_stat)
                elif plot_type == 'scatter':
                    from metplotpy.plots.tcmpr_plots.scatter.tcmpr_scatter import TcmprScatter
                    plot = TcmprScatter(config_obj, column_info, col_to_plot, common_case_data, input_df, cur_stat)
                elif plot_type == 'skill_mn':
                    from metplotpy.plots.tcmpr_plots.skill.mean.tcmpr_skill_mean import TcmprSkillMean
                    plot = TcmprSkillMean(config_obj, column_info, col_to_plot, common_case_data, input_df,
                                          cur_stat, baseline_data)
                elif plot_type == 'skill_md':
                    from metplotpy.plots.tcmpr_plots.skill.median.tcmpr_skill_median import TcmprSkillMedian
                    plot = TcmprSkillMedian(config_obj, column_info, col_to_plot, common_case_data, input_df, cur_stat)

                plot.save_to_file()
                # plot.show_in_browser()
                if common_case_data is None:
                    common_case_data = plot.case_data

            except (ValueError, Exception) as ve:
                print(ve)


def print_data_info(input_df, series):
    # Print information about the dataset.
    info_list = ["AMODEL", "BMODEL", "BASIN", "CYCLONE",
                 "STORM_NAME", "LEAD_HR", "LEVEL", "WATCH_WARN"]
    for info in info_list:
        uniq_list = input_df[info].unique()
        if pd.isna(uniq_list).any():
            vals = 'NA'
        else:
            vals = ','.join(map(str, uniq_list))
        print(f'Found {len(uniq_list)} unique entries for {info}: {vals}')
    # Get the unique series entries from the data
    series_uniq = input_df[series].unique()

    # List unique series entries
    print(
        f'Found {len(series_uniq)} unique value(s) for the {series} series: {",".join(map(str, series_uniq))}')


def read_tcst_files(config_obj, tcst_files):
    all_fields_values = copy.deepcopy(config_obj.parameters['series_val_1'])
    all_fields_values.update(config_obj.parameters['fixed_vars_vals_input'])
    if 'skill_mn' in config_obj.plot_type_list or 'skill_md' in config_obj.plot_type_list:
        all_fields_values['AMODEL'].extend(config_obj.skill_ref)
    input_df = None
    for file in tcst_files:
        if os.path.exists(file):
            print(f'Reading track data:{file}')
            if config_obj.is_tcdiag:
                file_df = pd.read_csv(file, sep='\t')
            else:
                file_df = pd.read_csv(file, sep=r'\s+|;|:', header='infer', engine="python")
            file_df['LEAD_HR'] = file_df['LEAD'] / 10000
            file_df['LEAD_HR'] = file_df['LEAD_HR'].astype('int')
            all_filters = []
            # create a set of filters

            for field, value in all_fields_values.items():
                filter_list = value
                for i, filter_val in enumerate(filter_list):
                    if calc_util.is_string_integer(filter_val):
                        filter_list[i] = int(filter_val)
                    elif calc_util.is_string_strictly_float(filter_val):
                        filter_list[i] = float(filter_val)

                all_filters.append(file_df[field].isin(filter_list))

            all_filters.append(file_df['LEAD_HR'].isin(config_obj.parameters['indy_vals']))

            # use numpy to select the rows where any record evaluates to True
            mask = np.array(all_filters).all(axis=0)

            if config_obj.is_tcdiag:
                file_df['VALID_TIME'] = file_df['VALID']
            else:
                file_df['VALID_TIME'] = pd.to_datetime(file_df['VALID'], format='%Y%m%d_%H%M%S')  # 20170417_060000
            # Define a case column
            file_df['equalize'] = file_df.loc[:, 'BMODEL'].astype(str) \
                                  + ':' + file_df.loc[:, 'STORM_ID'].astype(str) \
                                  + ':' + file_df.loc[:, 'INIT'].astype(str) \
                                  + ':' + file_df.loc[:, 'LEAD_HR'].astype(str) \
                                  + ':' + file_df.loc[:, 'VALID'].astype(str)
            if input_df is None:
                input_df = file_df.loc[mask]
            else:
                input_df = pd.concat([input_df, file_df.loc[mask]])
    return input_df


if __name__ == "__main__":
    main()
