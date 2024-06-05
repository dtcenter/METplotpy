import os
from datetime import datetime

from metcalcpy.util import utils
from metplotpy.plots.tcmpr_plots.skill.median.tcmpr_series_skill_median import TcmprSeriesSkillMedian
from metplotpy.plots.tcmpr_plots.skill.tcmpr_skill import TcmprSkill
import metplotpy.plots.util as util


class TcmprSkillMedian(TcmprSkill):
    def __init__(self, config_obj, column_info, col, case_data, input_df, stat_name):
        super().__init__(config_obj, column_info, col, case_data, input_df, stat_name, None)

        # Set up Logging
        self.skillmd_logger = util.get_common_logger(self.config_obj.log_level, self.config_obj.log_filename)

        self.skillmd_logger.info("--------------------------------------------------------")
        self.skillmd_logger.info(f"Plotting SKILL_MD time series by {self.config_obj.series_val_names[0]}")

        self.skillmd_logger.info("Plot HFIP Baseline:" + self.cur_baseline)

        self._adjust_titles(stat_name)
        self.series_list = self._create_series(self.input_df, stat_name)
        self.case_data = None

        if self.config_obj.prefix is None or len(self.config_obj.prefix) == 0:
            self.plot_filename = f"{self.config_obj.plot_dir}{os.path.sep}{stat_name}_skill_md.png"
        else:
            self.plot_filename = f"{self.config_obj.plot_dir}{os.path.sep}{self.config_obj.prefix}_{stat_name}_skill_md.png"

        # remove the old file if it exists
        if os.path.exists(self.plot_filename):
            os.remove(self.plot_filename)
        self._create_figure(stat_name)

    def _adjust_titles(self, stat_name):
        if self.yaxis_1 is None or len(self.yaxis_1) == 0:
            self.yaxis_1 =  'Skill  for ' + stat_name + ' (' + self.col['units'] + ')'

        if self.title is None or len(self.title) == 0:
            self.title = 'Median Skill Scores of ' + self.col['desc'] + ' by ' \
                         + self.column_info[self.column_info['COLUMN'] == self.config_obj.series_val_names[0]][
                             "DESCRIPTION"].tolist()[0]

    def _create_series(self, input_data, stat_name):
        """
           Generate all the series objects that are to be displayed as specified by the plot_disp
           setting in the config file.  The points are all ordered by datetime.  Each series object
           is represented by a box in the diagram, so they also contain information
           for  plot-related/appearance-related settings (which were defined in the config file).

           Args:
               input_data:  The input data in the form of a Pandas dataframe.
                            This data will be subset to reflect the series data of interest.

               stat_name:   The current name of the "statistic" specified in list_stat_1 of the config file

           Returns:
               a list of series objects that are to be displayed


        """

        start_time = datetime.now()

        all_fields_values = {'AMODEL': [utils.GROUP_SEPARATOR.join(self.config_obj.skill_ref)],
                             'fcst_var': self.config_obj.list_stat_1}
        permutations = utils.create_permutations_mv(all_fields_values, 0)
        ref_model_data_series = TcmprSeriesSkillMedian(self.config_obj, 0,
                                                       input_data, [], permutations[0], stat_name)
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
            series_obj = TcmprSeriesSkillMedian(self.config_obj, i, input_data, series_list, name, stat_name, ref_model_data)
            series_list.append(series_obj)

        # add derived for y1 axis
        for i, name in enumerate(self.config_obj.get_config_value('derived_series_1')):
            # add default operation value if it is not provided
            if len(name) == 2:
                name.append("DIFF")
            # include the series only if the name is valid
            if len(name) == 3:
                series_obj = TcmprSeriesSkillMedian(self.config_obj, num_series_y1 + i, input_data, series_list, name, stat_name)
                series_list.append(series_obj)

        # reorder series
        series_list = self.config_obj.create_list_by_series_ordering(series_list)
        end_time = datetime.now()
        total_time = end_time - start_time
        self.skillmd_logger.info(f"Took {total_time} milliseconds to create series for {stat_name}")

        return series_list
