import plotly.graph_objects as go

from metplotpy.plots.tcmpr_plots.tcmpr import Tcmpr
from metplotpy.plots.tcmpr_plots.tcmpr_series import TcmprSeries


class TcmprLine(Tcmpr):
    def __init__(self, config_obj, column_info, col, case_data, input_df, baseline_data, stat_name):
        super().__init__(config_obj, column_info, col, case_data, input_df)

    def _create_figure(self, stat_name):
        """ Create a box plot from default and custom parameters"""

        self.figure = self._create_layout()
        self._add_xaxis()
        self._add_yaxis()
        self._add_legend()

        # placeholder for the min and max values for y-axis
        yaxis_min = None
        yaxis_max = None

        if self.config_obj.xaxis_reverse is True:
            self.series_list.reverse()
        # calculate stag adjustments
        stag_adjustments = self._calc_stag_adjustments()

        x_points_index = list(range(0, len(self.config_obj.indy_vals)))
        # add x ticks for line plots
        odered_indy_label = self.config_obj.create_list_by_plot_val_ordering(self.config_obj.indy_label)
        self.figure.update_layout(
            xaxis={
                'tickmode': 'array',
                'tickvals': x_points_index,
                'ticktext': odered_indy_label
            }
        )

        for series in self.series_list:
            # Don't generate the plot for this series if
            # it isn't requested (as set in the config file)
            if series.plot_disp:
                # collect min-max if we need to sync axis
                yaxis_min, yaxis_max = self.find_min_max(series, yaxis_min, yaxis_max)
                x_points_index_adj = x_points_index + stag_adjustments[series.idx]
                self._draw_series(series, x_points_index_adj)

        print(f'Range of {stat_name}: {yaxis_min}, {yaxis_max}')

        self._add_hfip_baseline()

        self.figure.update_layout(shapes=[dict(
            type='line',
            yref='y', y0=0, y1=0,
            xref='paper', x0=0, x1=0.95,
            line={'color': '#727273',
                  'dash': 'dot',
                  'width': 1},
        )])

        # add custom lines
        if len(self.series_list) > 0:
            self._add_lines(
                self.config_obj,
                sorted(self.series_list[0].series_data[self.config_obj.indy_var].unique())
            )
        # apply y axis limits
        self._yaxis_limits()

        # add x2 axis
        self._add_x2axis(list(range(0, len(self.config_obj.indy_vals))))

    def _draw_series(self, series: TcmprSeries, x_points_index_adj: list) -> None:
        """
        Draws the boxes on the plot

        :param series: Line series object with data and parameters
        """

        y_points = series.series_points['val']
        # show or not ci
        # see if any ci values in not 0
        no_ci_up = all(v == 0 for v in series.series_points['ncu'])
        no_ci_lo = all(v == 0 for v in series.series_points['ncl'])
        error_y_visible = True
        if (no_ci_up is True and no_ci_lo is True) or self.config_obj.series_ci[series.idx] == 'NONE' or \
                self.config_obj.series_ci[series.idx] is False:
            error_y_visible = False
        # create a trace
        self.figure.add_trace(
            go.Scatter(x=x_points_index_adj,
                       y=y_points,
                       showlegend=True,
                       mode='lines+markers',
                       textposition="top right",
                       name=self.config_obj.user_legends[series.idx],
                       line={'color': self.config_obj.colors_list[series.idx],
                             'width': self.config_obj.linewidth_list[series.idx],
                             'dash': self.config_obj.linestyles_list[series.idx]},
                       marker_symbol=self.config_obj.marker_list[series.idx],
                       marker_color=self.config_obj.colors_list[series.idx],
                       marker_line_color=self.config_obj.colors_list[series.idx],
                       marker_size=self.config_obj.marker_size[series.idx],
                       error_y={'type': 'data',
                                'symmetric': False,
                                'array': series.series_points['ncu'],
                                'arrayminus': series.series_points['ncl'],
                                'visible': error_y_visible,
                                'thickness': self.config_obj.linewidth_list[series.idx]}
                       ),
            secondary_y=series.y_axis != 1
        )
