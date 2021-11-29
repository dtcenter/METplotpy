"""
Class Name: HistogramConfig

Holds values set in the histograms plot config file(s)
"""

import itertools

from plots.config import Config
import plots.constants as constants
import plots.util as util

import metcalcpy.util.utils as utils


class HistogramConfig(Config):
    """
    Prepares and organises histogram plot parameters
    """

    def __init__(self, parameters: dict) -> None:
        """ Reads in the plot settings from a histogram plot config file.

            Args:
            @param parameters: dictionary containing user defined parameters

        """
        super().__init__(parameters)

        # plot parameters
        self.grid_on = self._get_bool('grid_on')
        self.plot_width = self.calculate_plot_dimension('plot_width', 'pixels')
        self.plot_height = self.calculate_plot_dimension('plot_height', 'pixels')
        self.plot_margins = dict(l=0,
                                 r=self.parameters['mar'][3] + 20,
                                 t=self.parameters['mar'][2] + 80,
                                 b=self.parameters['mar'][0] + 80,
                                 pad=5
                                 )
        self.blended_grid_col = util.alpha_blending(self.parameters['grid_col'], 0.5)
        self.dump_points_1 = self._get_bool('dump_points_1')
        self.create_html = self._get_bool('create_html')

        ##############################################
        # caption parameters
        self.caption_size = int(constants.DEFAULT_CAPTION_FONTSIZE
                                * self.get_config_value('caption_size'))
        self.caption_offset = self.parameters['caption_offset'] - 3.1

        ##############################################
        # title parameters
        self.title_font_size = self.parameters['title_size'] * constants.DEFAULT_TITLE_FONT_SIZE
        self.title_offset = self.parameters['title_offset'] * constants.DEFAULT_TITLE_OFFSET
        self.y_title_font_size = self.parameters['ylab_size'] + constants.DEFAULT_TITLE_FONTSIZE

        ##############################################
        # y-axis parameters
        self.y_tickangle = self.parameters['ytlab_orient']
        if self.y_tickangle in constants.YAXIS_ORIENTATION.keys():
            self.y_tickangle = constants.YAXIS_ORIENTATION[self.y_tickangle]
        self.y_tickfont_size = self.parameters['ytlab_size'] + constants.DEFAULT_TITLE_FONTSIZE

        ##############################################
        # x-axis parameters
        self.x_title_font_size = self.parameters['xlab_size'] + constants.DEFAULT_TITLE_FONTSIZE
        self.x_tickangle = self.parameters['xtlab_orient']
        if self.x_tickangle in constants.XAXIS_ORIENTATION.keys():
            self.x_tickangle = constants.XAXIS_ORIENTATION[self.x_tickangle]
        self.x_tickfont_size = self.parameters['xtlab_size'] + constants.DEFAULT_TITLE_FONTSIZE
        self.xaxis = util.apply_weight_style(self.xaxis, self.parameters['xlab_weight'])

        ##############################################
        # ser parameters
        self.series_ordering = self.get_config_value('series_order')
        # Make the ser ordering zero-based
        self.series_ordering_zb = [sorder - 1 for sorder in self.series_ordering]
        self.plot_disp = self._get_plot_disp()
        self.colors_list = self._get_colors()
        self.all_series_y1 = self.get_series_y()
        self.num_series = self.calculate_number_of_series()

        ##############################################
        # legend parameters

        self.bbox_x = 0.5 + self.parameters['legend_inset']['x']
        self.bbox_y = -0.12 + self.parameters['legend_inset']['y'] + 0.25
        self.legend_size = int(constants.DEFAULT_LEGEND_FONTSIZE * self.parameters['legend_size'])
        if self.parameters['legend_box'].lower() == 'n':
            self.legend_border_width = 0  # Don't draw a box around legend labels
        else:
            self.legend_border_width = 2  # Enclose legend labels in a box

        if self.parameters['legend_ncol'] == 1:
            self.legend_orientation = 'v'
        else:
            self.legend_orientation = 'h'
        self.legend_border_color = "black"

        self.normalized_histogram = self._get_bool('normalized_histogram')
        self.fixed_vars_vals_input = self.parameters['fixed_vars_vals_input']

        self.points_path = self.get_config_value('points_path')

    def _get_plot_disp(self) -> list:
        """
        Retrieve the values that determine whether to display a particular ser
        and convert them to bool if needed

        Args:

        Returns:
                A list of boolean values indicating whether or not to
                display the corresponding ser
            """

        plot_display_config_vals = self.get_config_value('plot_disp')
        plot_display_bools = []
        for val in plot_display_config_vals:
            if isinstance(val, bool):
                plot_display_bools.append(val)

            if isinstance(val, str):
                plot_display_bools.append(val.upper() == 'TRUE')

        return self.create_list_by_series_ordering(plot_display_bools)

    def _config_consistency_check(self) -> bool:
        """
            Checks that the number of settings defined for plot_ci,
            plot_disp, series_order, user_legend colors, and series_symbols
            are consistent.

            Args:

            Returns:
                True if the number of settings for each of the above
                settings is consistent with the number of
                ser (as defined by the cross product of the model
                and vx_mask defined in the series_val_1 setting)

        """
        # Determine the number of ser based on the number of
        # permutations from the series_var setting in the
        # config file

        # Numbers of values for other settings for ser
        num_plot_disp = len(self.plot_disp)
        num_series_ord = len(self.series_ordering)
        num_colors = len(self.colors_list)
        num_legends = len(self.user_legends)
        status = False

        if self.num_series == num_plot_disp == \
                num_series_ord == num_colors \
                == num_legends:
            status = True
        return status

    def get_series_y(self) -> list:
        """
        Creates an array of ser components (excluding derived) tuples for the specified y-axis
        :param axis: y-axis (1 or 2)
        :return: an array of ser components tuples
        """
        all_fields_values_orig = self.get_config_value('series_val_1').copy()
        all_fields_values = {}
        for x in reversed(list(all_fields_values_orig.keys())):
            all_fields_values[x] = all_fields_values_orig.get(x)

        return utils.create_permutations_mv(all_fields_values, 0)

    def calculate_number_of_series(self) -> int:
        """
           From the number of items in the permutation list,
           determine how many ser "objects" are to be plotted.

           Args:

           Returns:
               the number of ser

        """
        # Retrieve the lists from the series_val_1 dictionary
        series_vals_list = self.series_vals_1.copy()

        # Utilize itertools' product() to create the cartesian product of all elements
        # in the lists to produce all permutations of the series_val values and the
        # fcst_var_val values.
        permutations = list(itertools.product(*series_vals_list))

        return len(permutations)

    def _get_user_legends(self, legend_label_type: str = '') -> list:
        """
        Retrieve the text that is to be displayed in the legend at the bottom of the plot.
        Each entry corresponds to a ser.

        Args:
                @parm legend_label_type:  The legend label. Used when the user hasn't
                                          indicated a legend.

        Returns:
                a list consisting of the ser label to be displayed in the plot legend.

        """

        all_user_legends = self.get_config_value('user_legend')
        legend_list = []

        # create legend list for y-axis ser
        for idx, ser_components in enumerate(self.get_series_y()):
            if idx >= len(all_user_legends) or all_user_legends[idx].strip() == '':
                # user did not provide the legend - create it
                if isinstance(ser_components, str):
                    legend_list.append(ser_components + '  ' + legend_label_type)
                else:
                    ser_components.append(legend_label_type)
                    legend_list.append(' '.join(map(str, ser_components)))
            else:
                # user provided a legend - use it
                legend_list.append(all_user_legends[idx])

        # if there is no ser variables
        if len(legend_list) == 0:
            if len(all_user_legends) > 0:
                legend_list.append(all_user_legends[0])
            else:
                legend_list.append(legend_label_type)

        return self.create_list_by_series_ordering(legend_list)


class RankHistogramConfig(HistogramConfig):
    """
        Prepares and organises rank histogram plot parameters
    """

    def __init__(self, parameters: dict) -> None:
        """ Reads in the plot settings from a Rank histogram plot config file.

            Args:
            @param parameters: dictionary containing user defined parameters

        """
        super().__init__(parameters)
        self.user_legends = self._get_user_legends('Rank Histogram')


class ProbHistogramConfig(HistogramConfig):
    """
        Prepares and organises Probability Histogram  plot parameters
    """

    def __init__(self, parameters: dict) -> None:
        """ Reads in the plot settings from a Probability histogram plot config file.

            Args:
            @param parameters: dictionary containing user defined parameters

        """
        super().__init__(parameters)
        self.user_legends = self._get_user_legends('Probability Histogram')


class RelHistogramConfig(HistogramConfig):
    """
        Prepares and organises Relative Histogram plot parameters
    """

    def __init__(self, parameters: dict) -> None:
        """ Reads in the plot settings from a Relative Histogram or Histograms
            of relative position plot config file.

            Args:
            @param parameters: dictionary containing user defined parameters

        """
        super().__init__(parameters)
        self.user_legends = self._get_user_legends('Relative Histogram')
