import os
from datetime import datetime
import numpy as np

from metplotpy.plots.tcmpr_plots.box.tcmpr_box_point import TcmprBoxPoint
from metplotpy.plots.tcmpr_plots.tcmpr_series import TcmprSeries
import metplotpy.plots.util as util


class TcmprBox(TcmprBoxPoint):
    def __init__(self, config_obj, column_info, col, case_data, input_df, baseline_data, stat_name):
        super().__init__(config_obj, column_info, col, case_data, input_df, baseline_data, stat_name)

        # Set up Logging
        self.box_logger = util.get_common_logger(self.config_obj.log_level, self.config_obj.log_filename)

        self.box_logger.info("--------------------------------------------------------\n")
        self.box_logger.info(f"Plotting BOXPLOT time series by {self.config_obj.series_val_names[0]}")
        self._adjust_titles(stat_name)
        self.series_list = self._create_series(self.input_df, stat_name)
        self.case_data = None
        self.cur_baseline = baseline_data['cur_baseline']
        self.cur_baseline_data = baseline_data['cur_baseline_data']
        self._init_hfip_baseline_for_plot()

        if self.config_obj.prefix is None or len(self.config_obj.prefix) == 0:
            self.plot_filename = f"{self.config_obj.plot_dir}{os.path.sep}{stat_name}_boxplot.png"
        else:
            self.plot_filename = f"{self.config_obj.plot_dir}{os.path.sep}{self.config_obj.prefix}_{stat_name}_boxplot.png"

        self.box_logger.info(f"Plot will be saved as {self.plot_filename}")

        # remove the old file if it exists
        if os.path.exists(self.plot_filename):
            os.remove(self.plot_filename)
        self._create_figure()

    def _adjust_titles(self, stat_name):
        if not self.yaxis_1:
            self.yaxis_1 = stat_name + '(' + self.col['units'] + ')'

        if self.title:
            return

        self.title = (
            f"Boxplots of\n{self.col['desc']}\nby "
            f"{self.column_info[self.column_info['COLUMN'] == self.config_obj.series_val_names[0]]["DESCRIPTION"].tolist()[0]}"
        )

    def _draw_series(self, series: TcmprSeries):
        """
        Draws the boxes on the plot

        :param series: Line series object with data and parameters
        """
        start_time = datetime.now()

        # Calculate positions for grouping
        x_points = self.config_obj.indy_vals
        x_locs, width = self._get_x_locs_and_width(x_points, series.idx)

        # Prepare data for boxplot
        data_to_plot = []
        for x in x_points:
            point_data = series.series_data.loc[series.series_data['LEAD_HR'] == x, 'PLOT'].tolist()
            # remove None/NaN
            data_to_plot.append([v for v in point_data if v is not None and not np.isnan(v)])

        if series.color == 'rgb(0,0,0)' or series.color == 'black' or series.color == '#000000':
            fillcolor = '#ffffff'
        else:
            fillcolor = series.color

        ax = self.ax if series.y_axis == 1 else self.ax2

        # Define properties for median and mean lines
        median_props = {
            'color': 'black',
            'linewidth': 1,
        }
        mean_props = {
            'linestyle': ':',
            'color': 'black',
            'linewidth': 1,
        }

        if len([x for x in series.series_data['PLOT'].tolist() if x is not None]) < self.config_obj.n_min:
            return None

        boxplot = ax.boxplot(data_to_plot, positions=x_locs, widths=width,
                        patch_artist=True,
                        label=self.config_obj.user_legends[series.idx],
                        notch=self.config_obj.box_notch,
                        showmeans=self.config_obj.box_avg,
                        meanline=self.config_obj.box_avg,
                        medianprops=median_props,
                        meanprops=mean_props,
                        flierprops={'markeredgecolor': series.color},
                        )

        for patch in boxplot['boxes']:
            patch.set_facecolor(fillcolor)
            patch.set_edgecolor('black')

        # add a proxy for legend
        #ax.plot([], [], color=fillcolor, label=series.user_legends, marker='s', linestyle='None')

        end_time = datetime.now()
        total_time = end_time - start_time
        self.box_logger.debug(f"Drawing series points took {total_time} millisecs")
        return boxplot['boxes'][0]
