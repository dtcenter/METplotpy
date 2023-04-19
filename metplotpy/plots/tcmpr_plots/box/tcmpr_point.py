import os

import plotly.graph_objects as go

from metplotpy.plots.tcmpr_plots.box.tcmpr_box_point import TcmprBoxPoint
from metplotpy.plots.tcmpr_plots.tcmpr_series import TcmprSeries


class TcmprPoint(TcmprBoxPoint):
    def __init__(self, config_obj, column_info, col, case_data, input_df, baseline_data):
        super().__init__(config_obj, column_info, col, case_data, input_df, baseline_data)
        print("--------------------------------------------------------")
        print(f"Plotting POINT time series by {self.config_obj.series_val_names[0]}")

        self._adjust_titles()
        self.series_list = self._create_series(self.input_df)
        self.case_data = None
        self.cur_baseline = baseline_data['cur_baseline']
        self.cur_baseline_data = baseline_data['cur_baseline_data']
        self._init_hfip_baseline_for_plot()

        if self.config_obj.prefix is None or len(self.config_obj.prefix) == 0:
            self.plot_filename = f"{self.config_obj.plot_dir}{os.path.sep}{self.config_obj.list_stat_1[0]}_pointplot.png"
        else:
            self.plot_filename = f"{self.config_obj.plot_dir}{os.path.sep}{self.config_obj.prefix}.png"

        # remove the old file if it exist
        if os.path.exists(self.plot_filename):
            os.remove(self.plot_filename)
        self._create_figure()

    def _adjust_titles(self):
        if self.yaxis_1 is None or len(self.yaxis_1) == 0:
            self.yaxis_1 = self.config_obj.list_stat_1[0] + '(' + self.col['units'] + ')'

        if self.title is None or len(self.title) == 0:
            self.title = 'Point Plots  of ' + self.col['desc'] + ' by ' \
                         + self.column_info[self.column_info['COLUMN'] == self.config_obj.series_val_names[0]][
                             "DESCRIPTION"].tolist()[0]

    def _draw_series(self, series: TcmprSeries) -> None:
        """
        Draws the boxes on the plot

        :param series: Line series object with data and parameters
        """

        # defaults markers and colors for the regular box plot
        marker_color = series.color
        marker_line_color = series.color

        # Point plot

        line_color = dict(color='rgba(0,0,0,0)')
        fillcolor = 'rgba(0,0,0,0)'
        marker_symbol = 'circle'
        boxpoints = 'all'

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
                   boxpoints=boxpoints,  # outliers, all, False
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
