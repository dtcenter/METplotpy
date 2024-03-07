import os
from datetime import datetime

import numpy as np
import plotly.graph_objects as go

from metcalcpy.util import utils
from metplotpy.plots.tcmpr_plots.skill.mean.tcmpr_series_skill_mean import TcmprSeriesSkillMean
from metplotpy.plots.tcmpr_plots.skill.tcmpr_skill import TcmprSkill
import metplotpy.plots.util as util


class TcmprSkillMean(TcmprSkill):
    def __init__(self, config_obj, column_info, col, case_data, input_df, stat_name,  baseline_data):
        super().__init__(config_obj, column_info, col, case_data, input_df, baseline_data, stat_name)

        # Set up Logging
        self.skill_logger = util.get_common_logger(self.config_obj.log_level, self.config_obj.log_filename)

        self.skill_logger.info("--------------------------------------------------------")
        self.skill_logger.info(f"Plotting SKILL_MN time series by {self.config_obj.series_val_names[0]}")

        self._adjust_titles(stat_name)
        self.cur_baseline = baseline_data['cur_baseline']
        self.cur_baseline_data = baseline_data['cur_baseline_data']
        self._init_hfip_baseline_for_plot()
        self.series_list = self._create_series(self.input_df, stat_name)
        self.case_data = None
        if self.config_obj.prefix is None or len(self.config_obj.prefix) == 0:
            self.plot_filename = f"{self.config_obj.plot_dir}{os.path.sep}{stat_name}_skill_mn.png"
        else:
            self.plot_filename = f"{self.config_obj.plot_dir}{os.path.sep}{self.config_obj.prefix}_{stat_name}_skill_mn.png"

        # remove the old file if it exists
        if os.path.exists(self.plot_filename):
            os.remove(self.plot_filename)
        self._create_figure(stat_name)

    def _adjust_titles(self, stat_name):
        if self.yaxis_1 is None or len(self.yaxis_1) == 0:
            self.yaxis_1 = 'Skill for ' + stat_name + ' (' + self.col['units'] + ')'

        if self.title is None or len(self.title) == 0:
            self.title = 'Mean Skill Scores of ' + self.col['desc'] + ' by ' \
                         + self.column_info[self.column_info['COLUMN'] == self.config_obj.series_val_names[0]][
                             "DESCRIPTION"].tolist()[0]

    def _init_hfip_baseline_for_plot(self):
        if 'Water Only' in self.title:
            self.skill_logge.info(f"Plot HFIP Baseline: {self.cur_baseline}")
        else:
            self.cur_baseline = self.cur_baseline.replace('Error', 'Skill')
            self.cur_baseline = self.cur_baseline.replace('HFIP Baseline ', 'HFIP Skill Baseline')
        self.skill_logger.info(f"Plot HFIP Baseline:  {self.cur_baseline.replace('Error ', '')}")

    def _add_hfip_baseline(self):
        # Add HFIP baseline for each lead time
        if self.cur_baseline_data is not None:
            self.skill_logger.info(f"Adding HFIP baseline: {datetime.now()}")
            baseline_x_values = []
            baseline_y_values = []
            lead_times = np.unique(self.series_list[0].series_data[self.config_obj.indy_var].tolist())
            lead_times.sort()
            for ind, lead in enumerate(lead_times):
                if lead != 0:
                    ocd5_data = self.cur_baseline_data.loc[
                        (self.cur_baseline_data['LEAD'] == lead) & (self.cur_baseline_data['TYPE'] == "OCD5")][
                        'VALUE'].tolist()
                    ocd5_data = ocd5_data[0]
                    cons_data = self.cur_baseline_data.loc[
                        (self.cur_baseline_data['LEAD'] == lead) & (self.cur_baseline_data['TYPE'] == "CONS")][
                        'VALUE'].tolist()
                    if len(cons_data) > 1:
                        raise ValueError(
                            f"ERROR: Can't create HFIP baseline for lead time {lead} : too many values of CONS in .dat file")
                    cons_data = cons_data[0]

                    baseline_lead = utils.round_half_up(100 * (ocd5_data - cons_data) / ocd5_data, 1)
                    baseline_x_values.append(ind)
                    baseline_y_values.append(baseline_lead)

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

    def _create_series(self, input_data, stat_name):
        """
           Generate all the series objects that are to be displayed as specified by the plot_disp
           setting in the config file.  The points are all ordered by datetime.  Each series object
           is represented by a box in the diagram, so they also contain information
           for  plot-related/appearance-related settings (which were defined in the config file).

           Args:
               input_data:  The input data in the form of a Pandas dataframe.
                            This data will be subset to reflect the series data of interest.
               stat_name:  The current value of the list_stat_1 specified in the configuration file. This represents
                           type of plot (e.g. TK_ERR, ABS(AMAX_WIND-BMAX-WIND), etc.).

           Returns:
               a list of series objects that are to be displayed


        """

        start_time = datetime.now()
        all_fields_values = {'AMODEL': [utils.GROUP_SEPARATOR.join(self.config_obj.skill_ref)],
                             'fcst_var': self.config_obj.list_stat_1}
        permutations = utils.create_permutations_mv(all_fields_values, 0)
        ref_model_data_series = TcmprSeriesSkillMean(self.config_obj, 0,
                                                     input_data, [], permutations[0], stat_name,  None)
        ref_model_data = ref_model_data_series.series_data

        series_list = []

        # add series for y1 axis
        unique_series = []
        for cur in self.config_obj.get_series_y(1):
            if cur[0] not in unique_series:
                unique_series.append(cur[0])

        num_series_y1 = len(unique_series)
        # num_series_y1 = len(self.config_obj.get_series_y(1))
        # for i, name in enumerate(self.config_obj.get_series_y(1)):
        for i, name in enumerate(unique_series):
            if not isinstance(name, list):
                name = [name]

            series_obj = TcmprSeriesSkillMean(self.config_obj, i, input_data, series_list, name, stat_name, ref_model_data)
            series_list.append(series_obj)

        # add derived for y1 axis
        for i, name in enumerate(self.config_obj.get_config_value('derived_series_1')):
            # add default operation value if it is not provided
            if len(name) == 2:
                name.append("DIFF")
            # include the series only if the name is valid
            if len(name) == 3:
                series_obj = TcmprSeriesSkillMean(self.config_obj, num_series_y1 + i, input_data, series_list, name, stat_name)
                series_list.append(series_obj)

        # reorder series
        series_list = self.config_obj.create_list_by_series_ordering(series_list)

        end_time = datetime.now()
        total_time = end_time - start_time
        self.skill_logger.info(f"Total time to create series list for {stat_name}: {total_time} milliseconds ")
        return series_list
