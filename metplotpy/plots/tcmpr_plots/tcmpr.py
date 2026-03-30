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
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import metcalcpy.util.utils as calc_util
from metcalcpy.event_equalize import event_equalize
from metplotpy.plots import util as util
from metplotpy.plots.base_plot import BasePlot
from metplotpy.plots.constants import DEFAULT_TITLE_FONT_SIZE, DEFAULT_TITLE_OFFSET
from metplotpy.plots.tcmpr_plots.tcmpr_config import TcmprConfig
from metplotpy.plots.tcmpr_plots.tcmpr_series import TcmprSeries
from metplotpy.plots.tcmpr_plots.tcmpr_util import init_hfip_baseline, common_member, get_dep_column

PLOTS_WITH_BASELINE = ['boxplot', 'point', 'mean', 'skill_mn']


class Tcmpr(BasePlot):
    """  Generates a Matplotlib plot for 1 or more traces
         where each box is represented by a text point data file.
    """

    def __init__(self, config_obj, column_info, col, case_data, input_df, stat_name):
        """ Creates a plot, based on
            settings indicated by parameters.

            Args:
            @param parameters: dictionary containing user defined parameters

        """

        # init common layout
        super().__init__(config_obj.parameters, "tcmpr_defaults.yaml")

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
        self.stat_name = stat_name
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

    def _add_hfip_baseline(self, ax):

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

            ax.scatter(baseline_x_values, baseline_y_values,
                       marker='d',
                       facecolors='none',
                       edgecolors='blue',
                       s=30,
                       label=self.cur_baseline)

    def _create_figure(self):
        """
        Create a box plot from defaults and custom parameters
        """
        # create and draw the plot
        self.fig, self.ax = plt.subplots(figsize=(self.config_obj.plot_width, self.config_obj.plot_height),
                                         )#layout="constrained")

        # for secondary y axis
        self.ax2 = self.ax.twinx() if any(s.y_axis != 1 for s in self.series_list) else None

        wts_size_styles = self.get_weights_size_styles()

        self._add_title(self.ax, wts_size_styles['title'])
        self._add_caption(plt, wts_size_styles['caption'])

    def _add_title(self, ax, fontproperties, title_override=None):
        super()._add_title(ax, fontproperties, title_override=self.title)

    def _add_xaxis(self, ax=None, fontproperties=None, label=None, grid_on=None) -> None:
        """
        Configures and adds x-axis to the plot
        """
        if ax is None:
            ax = self.ax
        wts_size_styles = self.get_weights_size_styles()
        super()._add_xaxis(ax, wts_size_styles['xlab'])

    def _add_yaxis(self, ax=None, fontproperties=None, label=None, grid_on=None) -> None:
        """
        Configures and adds y-axis to the plot
        """
        if ax is None:
            ax = self.ax
        wts_size_styles = self.get_weights_size_styles()
        super()._add_yaxis(ax, wts_size_styles['ylab'], label=self.yaxis_1)

    def _add_x2axis(self, ax=None, n_stats=None, fontproperties=None) -> None:
        """
        Creates x2axis based on the properties from the config file
        and attaches it to the initial Figure

        """
        if not self.config_obj.show_nstats:
            return

        if n_stats is None:
            n_stats = [''] * len(self.config_obj.indy_vals)

            for ind, val_for_indy in enumerate(n_stats):
                if self.config_obj.use_ee and len(self.series_list) > 0:
                    n_stats[ind] = str(self.series_list[0].series_points['nstat'][ind])
                else:
                    ns = []
                    for series in self.series_list:
                        ns.append(str(series.series_points['nstat'][ind]))
                    n_stats[ind] = "\n".join(ns)

        wts_size_styles = self.get_weights_size_styles()
        super()._add_x2axis(self.ax, n_stats, wts_size_styles['x2lab'])

    def _add_legend(self, ax=None, handles_and_labels=None) -> None:
        """
        Creates a plot legend based on the properties from the config file
        and attaches it to the initial Figure
        """
        if ax is None:
            ax = self.ax
        super()._add_legend(ax)

    def save_to_file(self, plot_filename: str = None, **kwargs):
        """Saves the image to a file specified in the config file.
         Prints a message if fails

        Args:

        Returns:

        """
        # TODO: consider setting bbox_inches='tight' for all plots to ensure nothing is cut off
        super().save_to_file(self.plot_filename, bbox_inches='tight', **kwargs)

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
        if 'val' in series.series_points and len(series.series_points['val']) > 0:
            all_values = series.series_points['val']
            if 'ncl' in series.series_points:
                all_values = all_values + series.series_points['ncl']
            if 'ncu' in series.series_points:
                all_values = all_values + series.series_points['ncu']
        else:
            all_values = series.series_data['PLOT'].tolist()

        # remove None/NaN
        all_values = [v for v in all_values if v is not None and not np.isnan(v)]

        if len(all_values) == 0:
            return yaxis_min, yaxis_max

        low_range = min(all_values)
        upper_range = max(all_values)

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
    docs = util.get_params(config_filename)

    # Determine location of the default YAML config files and then
    # read defaults stored in YAML formatted file into the dictionary
    if 'METPLOTPY_BASE' in os.environ:
        location = os.path.join(os.environ['METPLOTPY_BASE'], 'metplotpy/plots/config')
    else:
        location = os.path.realpath(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config'))

    defaults = util.get_params(os.path.join(location, "tcmpr_defaults.yaml"))

    # merge user defined parameters into defaults if they exist
    docs = {**defaults, **docs}

    config_obj = TcmprConfig(docs)

    # Create the requested plot(s)
    create_plot(config_obj)


def create_plot(config_obj) -> None:
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

    for plot_type in config_obj.plot_type_list:

        # Apply event equalization, if requested
        # Event equalization is different for the skill_mn and skill_md
        if config_obj.use_ee:
            is_skill = plot_type == 'skill_mn' or plot_type == 'skill_md'
            logger.info(f"Perform event equalization for {plot_type}: {datetime.now()}")
            output_result = perform_event_equalization(orig_input_df, is_skill, config_obj)
            input_df = output_result

        input_df.rename({'equalize': 'CASE'}, axis=1, inplace=True)
        # Sort the data by the CASE column
        input_df = input_df.sort_values(by=['CASE', 'AMODEL'])
        input_df.reset_index(drop=True, inplace=True)

        for cur_stat in config_obj.list_stat_1:
            logger.info(f"Statistic of interest: {cur_stat}")
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
                if common_case_data is None:
                    common_case_data = plot.case_data

            except ValueError as ve:
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
