import datetime

from metplotpy.plots.tcmpr_plots.tcmpr import Tcmpr
from metplotpy.plots.tcmpr_plots.tcmpr_series import TcmprSeries
import metplotpy.plots.util as util

class TcmprBoxPoint(Tcmpr):
    def __init__(self, config_obj, column_info, col, case_data, input_df,  baseline_data, stat_name):
        super().__init__(config_obj, column_info, col, case_data, input_df, stat_name)
        # Set up Logging
        self.box_point_logger = util.get_common_logger(self.config_obj.log_level, self.config_obj.log_filename)
        self.series_len = len(config_obj.get_series_y(1)) + len(config_obj.get_config_value('derived_series_1'))


    def _init_hfip_baseline_for_plot(self):
        if 'Water Only' in self.config_obj.title or self.cur_baseline == 'no':
            self.box_point_logger.info(f"Plot HFIP Baseline: {self.cur_baseline}")
        else:
            self.cur_baseline_data = self.cur_baseline_data[(self.cur_baseline_data['TYPE'] == 'CONS')]
            self.box_point_logger.info(f"Plot HFIP Baseline: {self.cur_baseline.replace('Error ', '')}")

    def _draw_series(self, series: TcmprSeries) -> None:
        pass

    def _create_figure(self):
        """ Create a box plot from default and custom parameters"""
        start_time = datetime.datetime.now()
        self.figure = self._create_layout()
        self._add_xaxis()
        self._add_yaxis()
        self._add_legend()

        # placeholder for the min and max values for y-axis
        yaxis_min = None
        yaxis_max = None

        if self.config_obj.xaxis_reverse is True:
            self.series_list.reverse()

        # add x ticks for line plots
        self.figure.update_layout(
            xaxis={
                'tickmode': 'array',
                'tickvals': self.config_obj.indy_vals,
                'ticktext': self.config_obj.indy_label
            }
        )

        for series in self.series_list:
            # Don't generate the plot for this series if
            # it isn't requested (as set in the config file)
            if series.plot_disp:
                # collect min-max if we need to sync axis
                yaxis_min, yaxis_max = self.find_min_max(series, yaxis_min, yaxis_max)
                self._draw_series(series)

        self.box_point_logger.info(f'Range of {self.config_obj.list_stat_1[0]}: {yaxis_min}, {yaxis_max}')
        self._add_hfip_baseline()

        self.figure.update_layout(shapes=[dict(
            type='line',
            yref='y', y0=0, y1=0,
            xref='paper', x0=0, x1=0.95,
            line={'color': '#727273',
                  'dash': 'dot',
                  'width': 1},
        )])

        self.figure.update_layout(boxmode='group')

        # add custom lines
        if len(self.series_list) > 0:
            self._add_lines(
                self.config_obj,
                sorted(self.series_list[0].series_data[self.config_obj.indy_var].unique())
            )
        # apply y axis limits
        self._yaxis_limits()

        # add x2 axis
        self._add_x2axis(self.config_obj.indy_vals)
        end_time = datetime.datetime.now()
        total_time = end_time - start_time
        self.box_point_logger.info(f"Took {total_time} millisecs to create a boxplot")

