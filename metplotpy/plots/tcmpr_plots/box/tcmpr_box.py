import os
from datetime import datetime

import plotly.graph_objects as go

from metplotpy.plots.tcmpr_plots.box.tcmpr_box_point import TcmprBoxPoint
from metplotpy.plots.tcmpr_plots.tcmpr_series import TcmprSeries
import metplotpy.plots.util as util
import pandas as pd
from scipy import stats



class TcmprBox(TcmprBoxPoint):
    def __init__(self, config_obj, column_info, col, case_data, input_df, baseline_data, stat_name):
        super().__init__(config_obj, column_info, col, case_data, input_df, baseline_data, stat_name)

        # Set up Logging
        self.box_logger = util.get_common_logger(self.config_obj.log_level, self.config_obj.log_filename)

        self.box_logger.info(f"--------------------------------------------------------\n")
        self.box_logger.info(f"Plotting BOXPLOT time series by {self.config_obj.series_val_names[0]}")
        self._adjust_titles(stat_name)
        self.series_list = self._create_series(self.input_df, stat_name)
        self.case_data = None
        self.cur_baseline = baseline_data['cur_baseline']
        self.cur_baseline_data = baseline_data['cur_baseline_data']
        self._init_hfip_baseline_for_plot()

        # a list of dataframes, used for collecting outlier data
        self.outliers:list[pd.DataFrame] = []

        if self.config_obj.prefix is None or len(self.config_obj.prefix) == 0:
            self.plot_filename = f"{self.config_obj.plot_dir}{os.path.sep}{stat_name}_boxplot.png"
            self.outlier_filename = f"{self.config_obj.plot_dir}{os.path.sep}{stat_name}_boxplot_outliers.txt"
        else:
            self.plot_filename = f"{self.config_obj.plot_dir}{os.path.sep}{self.config_obj.prefix}_{stat_name}_boxplot.png"
            self.outlier_filename = f"{self.config_obj.plot_dir}{os.path.sep}{self.config_obj.prefix}_{stat_name}_boxplot_outliers.txt"

        self.box_logger.info(f"Plot will be saved as {self.plot_filename}")
        self.box_logger.info(f"Outlier file will be saved as {self.outlier_filename}")

        # remove the old file if it exists
        if os.path.exists(self.plot_filename):
            os.remove(self.plot_filename)

        self._create_figure()

        # Concatenate all the outlier dataframes and save to a file
        final_outlier:pd.DataFrame = pd.concat(self.outliers)
        final_outlier.to_csv(self.outlier_filename, sep="\t", index=False)


    def _adjust_titles(self, stat_name):
        if self.yaxis_1 is None or len(self.yaxis_1) == 0:
            self.yaxis_1 = stat_name + '(' + self.col['units'] + ')'

        if self.title is None or len(self.title) == 0:
            self.title = 'Boxplots of ' + self.col['desc'] + ' by ' \
                         + self.column_info[self.column_info['COLUMN'] == self.config_obj.series_val_names[0]][
                             "DESCRIPTION"].tolist()[0]

    def _draw_series(self, series: TcmprSeries) -> None:
        """
        Draws the boxes on the plot

        :param series: Line series object with data and parameters
        """

        start_time = datetime.now()
        # defaults markers and colors for the regular box plot
        line_color = dict(color='rgb(0,0,0)')
        marker_color = series.color
        marker_line_color = series.color

        if len([x for x in series.series_data['PLOT'].tolist() if x is not None]) < self.config_obj.n_min:
            line_color = dict(color='rgba(0,0,0,0)')
            fillcolor = 'rgba(0,0,0,0)'
            marker_symbol = 'circle'
        else:
            if series.color == 'rgb(0,0,0)' or series.color == 'black' or series.color == '#000000':
                fillcolor = '#ffffff'
            else:
                fillcolor = series.color
            marker_symbol = 'circle-open'

        # Retrieve the outlier points and collect them into a list of dataframes (based
        # on lead hour), which will then be saved into a text file (for all series and
        # all lead hours).
        # Employ the IQR method to identify outliers.
        unique_lead_hrs = series.series_data['LEAD_HR'].unique()
        working = series.series_data.copy(deep=True)
        for cur_lead in unique_lead_hrs:
            wip = working[['LEAD_HR', 'PLOT']]
            df_cur_lead = wip.loc[wip['LEAD_HR'] == cur_lead]
            data = df_cur_lead[['PLOT']]
            q1 = data.quantile(q=0.25)
            q3 = data.quantile(q=0.75)
            iqr = data.apply(stats.iqr)
            iqr_1p5 = 1.5 * iqr

            # find the outliers for this lead hour
            data_outliers:pd.DataFrame = data[((data < (q1-iqr_1p5))|(data > (q3+iqr_1p5))).any(axis=1)]
            outlier_idx = data_outliers.index

            # Get the entire row of data from the "original" data (series.series_data)
            # and add them to a list of dataframes that will be merged after the
            # plotting is complete.
            outlier_df = self.input_df.iloc[outlier_idx]
            self.outliers.append(outlier_df)


        # create a trace

        self.figure.add_trace(
            go.Box(x=series.series_data['LEAD_HR'],
                   y=series.series_data['PLOT'],
                   mean=series.series_points['mean'],
                   notched=self.config_obj.box_notch,
                   line=line_color,
                   fillcolor=fillcolor,
                   name=series.user_legends,
                   showlegend=True,
                   # quartilemethod='linear', #"exclusive", "inclusive", or "linear"
                   boxmean=self.config_obj.box_avg,
                   boxpoints='outliers',  # outliers, all, False
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
                   ),
            secondary_y=series.y_axis != 1
        )

        end_time = datetime.now()
        total_time = end_time - start_time
        self.box_logger.debug(f"Drawing series points took {total_time} millisecs")
