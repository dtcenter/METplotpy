# ============================*
 # ** Copyright UCAR (c) 2026
 # ** University Corporation for Atmospheric Research (UCAR)
 # ** National Science Foundation National Center for Atmospheric Research (NSF NCAR)
 # ** Research Applications Lab (RAL)
 # ** P.O.Box 3000, Boulder, Colorado, 80307-3000, USA
 # ============================*
 
 
 
"""
Class Name: base_plot.py
 """
__author__ = 'Tatiana Burek'

import os
import logging
import warnings
from datetime import datetime
import numpy as np
from matplotlib.font_manager import FontProperties

from matplotlib import pyplot as plt

import yaml
from typing import Union
from operator import add
from metplotpy.plots.util import strtobool
from .config import Config
from . import constants


###
# Global matplotlib default setting overrides
###

# set default for dashed and dotted lines to be longer and wider spaced
plt.rcParams['lines.dashed_pattern'] = [10, 10]
plt.rcParams['lines.dotted_pattern'] = [5, 5]

# Turn off spines globally
plt.rcParams['axes.spines.top'] = False
plt.rcParams['axes.spines.right'] = False

turn_on_logging = strtobool('LOG_BASE_PLOT')
# Log when Chrome is downloaded at runtime
if turn_on_logging:
   log = logging.getLogger("base_plot")
   log.setLevel(logging.INFO)

   formatter = logging.Formatter("%(asctime)s [%(levelname)s] | %(name)s | %(message)s")

   # set the WRITE_LOG env var to True to save the log message to a
   # separate log file
   write_log = strtobool('WRITE_LOG')
   if write_log:
      file_handler = logging.FileHandler("./base_plot.log")
      file_handler.setFormatter(formatter)
      log.addHandler(file_handler)


class BasePlot:
    """A class that provides methods for building Plotly plot's common features
     like title, axis, legend.

     To use:
        use as an abstract class for the common plot types
    """

    def __init__(self, parameters, default_conf_filename):
        """Inits BasePlot with user defined and default dictionaries.
           Removes the old image if it exists

        Args:
            @param parameters - dictionary containing user defined parameters
            @param default_conf_filename - the name of the default config file
                                     for the plot type that is a subclass.


        """

        # Determine location of the default YAML config files and then
        # read defaults stored in YAML formatted file into the dictionary
        if 'METPLOTPY_BASE' in os.environ:
            location = os.path.join(os.environ['METPLOTPY_BASE'], 'metplotpy/plots/config')
        else:
            location = os.path.realpath(os.path.join(os.path.dirname(__file__), 'config'))

        with open(os.path.join(location, default_conf_filename), 'r') as stream:
            try:
                defaults = yaml.load(stream, Loader=yaml.FullLoader)
            except yaml.YAMLError as exc:
                print(exc)

        # merge user defined parameters into defaults if they exist
        if parameters:
            self.parameters = {**defaults, **parameters}
        else:
            self.parameters = defaults

        self.figure = None
        self.remove_file()
        self.config_obj = Config(self.parameters)

    def get_legend_style(self):
        """
            Retrieve the legend style settings that are set
            in the METviewer tool

            Args:

            Returns:
                - a dictionary that holds the legend settings that
                  are set in METviewer
        """
        legend_box = self.get_config_value('legend_box').lower()
        borderwidth = 0
        if legend_box == 'o':
            # Draws a box around the legend
            borderwidth = 1
        elif legend_box == 'n':
            # Do not draw border around the legend labels.
            borderwidth = 0

        legend_ncol = self.get_config_value('legend_ncol')
        if legend_ncol > 1:
            legend_orientation = "h"
        else:
            legend_orientation = "v"
        legend_inset = self.get_config_value('legend_inset')
        legend_size = self.get_config_value('legend_size')
        legend_settings = {
            "border_width": borderwidth,
            "orientation": legend_orientation,
            "legend_inset": {
                'x': legend_inset['x'],
                'y': legend_inset['y'],
            },
            'legend_size': legend_size,
        }

        return legend_settings

    def get_weights_size_styles(self):
        """
           Set up the font properties for the plot title: style (regular, italic), size, and
           weight (normal, bold) for the title, captions, x-axis label, and y-axis label.

           Returns:
              weights_size_styles: A dictionary containing the font property information
                                             for the title, captions, x-axis label, and y-axis label
        """
        weights_size_styles = {}

        # For title
        title_property= FontProperties()
        title_property.set_size(self.config_obj.title_size)
        style = self.config_obj.title_weight[0]
        wt = self.config_obj.title_weight[1]
        title_property.set_style(style)
        title_property.set_weight(wt)
        weights_size_styles['title'] = title_property

        # For caption
        caption_property = FontProperties()
        caption_property.set_size(self.config_obj.caption_size)
        cap_style = self.config_obj.caption_weight[0]
        cap_wt = self.config_obj.caption_weight[1]
        caption_property.set_style(cap_style)
        caption_property.set_weight(cap_wt)
        weights_size_styles['caption'] = caption_property

        # For xaxis label
        xlab_property= FontProperties()
        xlab_property.set_size(self.config_obj.x_title_font_size)
        xlab_style = self.config_obj.xlab_weight[0]
        xlab_wt = self.config_obj.xlab_weight[1]
        xlab_property.set_style(xlab_style)
        xlab_property.set_weight(xlab_wt)
        weights_size_styles['xlab'] = xlab_property

        # For yaxis label
        ylab_property = FontProperties()
        ylab_property.set_size(self.config_obj.y_title_font_size)
        ylab_style = self.config_obj.ylab_weight[0]
        ylab_wt = self.config_obj.ylab_weight[1]
        ylab_property.set_style(ylab_style)
        ylab_property.set_weight(ylab_wt)
        weights_size_styles['ylab'] = ylab_property

        # For x2axis label if set
        if (hasattr(self.config_obj, 'x2lab_weight')
                and self.config_obj.x2lab_weight is not None
                and hasattr(self.config_obj, 'x2_title_font_size')
                and self.config_obj.x2_title_font_size is not None):
            x2lab_property= FontProperties()
            x2lab_property.set_size(self.config_obj.x2_title_font_size)
            x2lab_style, x2lab_wt = self.config_obj.x2lab_weight
            x2lab_property.set_style(x2lab_style)
            x2lab_property.set_weight(x2lab_wt)
            weights_size_styles['x2lab'] = x2lab_property


        # For y2axis label if set
        if (hasattr(self.config_obj, 'y2lab_weight')
                and self.config_obj.y2lab_weight is not None
                and hasattr(self.config_obj, 'y2_title_font_size')
                and self.config_obj.y2_title_font_size is not None):
            y2lab_property= FontProperties()
            y2lab_property.set_size(self.config_obj.y2_title_font_size)
            y2lab_style, y2lab_wt = self.config_obj.y2lab_weight
            y2lab_property.set_style(y2lab_style)
            y2lab_property.set_weight(y2lab_wt)
            weights_size_styles['y2lab'] = y2lab_property

        return weights_size_styles


    def get_config_value(self, *args):
        """Gets the value of a configuration parameter.
        Looks for parameter in the user parameter dictionary

        Args:
            @ param args - chain of keys that defines a key to the parameter

        Returns:
            - a value for the parameter of None
        """

        return self._get_nested(self.parameters, args)

    def _get_nested(self, data, args):
        """Recursive function that uses the tuple with keys to find a value
        in multidimensional dictionary.

        Args:
            @data - dictionary for the lookup
            @args  - a tuple with keys

        Returns:
            - a value for the parameter of None
        """

        if args and data:

            # get value for the first key
            element = args[0]
            if element:
                value = data.get(element)

                # if the size of key tuple is 1 - the search is over
                if len(args) == 1:
                    return value

                # if the size of key tuple is > 1 - search using other keys
                return self._get_nested(value, args[1:])
        return None

    def get_img_bytes(self):
        """Returns an image as a bytes object in a format specified in the config file

        Args:

        Returns:
            - an image as a bytes object
        """
        if self.figure:
            return self.figure.to_image(format=self.get_config_value('image_format'),
                                        width=self.get_config_value('width'),
                                        height=self.get_config_value('height'),
                                        scale=self.get_config_value('scale'))

        return None

    def save_to_file(self, plot_filename=None, **kwargs) -> None:
        """!Saves the plot to a file.
        Add any arguments passed to the function directly to plt.savefig."""
        image_name = plot_filename if plot_filename else self.get_config_value('plot_filename')

        self.logger.info(f"Saving to file: {image_name} : {datetime.now()}")
        os.makedirs(os.path.dirname(image_name), exist_ok=True)
        plot_obj = plt if not self.figure else self.figure
        try:
            plot_obj.savefig(image_name, dpi=self.get_config_value('plot_res'), **kwargs)
            self.logger.info(f"Finished saving plot {datetime.now()}")
        except Exception as ex:
            self.logger.error(f"Failed to save plot to file: {ex}")
        finally:
            plt.close('all')

    def remove_file(self):
        """Removes previously made image file .
        """
        image_name = self.get_config_value('plot_filename')

        # remove the old file if it exist
        if image_name is not None and os.path.exists(image_name):
            os.remove(image_name)

    @staticmethod
    def add_horizontal_line(ax: plt.Axes, y: float, line_properties: dict) -> None:
        """Adds a horizontal line to the matplotlib plot

        @param ax: Matplotlib Axes object
        @param y y value for the line
        @param line_properties dictionary with line properties like color, width, dash
        @returns None
        """
        ax.axhline(y=y, xmin=0, xmax=1, **line_properties)

    @staticmethod
    def add_vertical_line(ax: plt.Axes, x: float, line_properties: dict) -> None:
        """Adds a vertical line to the matplotlib plot

        @param ax: Matplotlib Axes object
        @param x x value for the line
        @param line_properties dictionary with line properties like color, width, dash
        @returns None
        """
        ax.axvline(x=x, ymin=0, ymax=1, **line_properties)

    @staticmethod
    def get_array_dimensions(data):
        """Returns the dimension of the array

        Args:
            @param data - input array
        Returns:
            - an integer representing the array's dimension or None
        """
        if data is None:
            return None

        np_array = np.array(data)
        return len(np_array.shape)

    def _add_title(self, ax, font_properties, title_override=None):
        title = title_override if title_override else self.config_obj.title
        ax.set_title(
            title.replace('<br>', '\n'),
            fontproperties=font_properties,
            color=constants.DEFAULT_TITLE_COLOR,
            pad=28,
            x=self.config_obj.parameters['title_align'],
            y=self.config_obj.title_offset,
        )

    def _add_caption(self, plt, font_properties):
        y_pos = max(0.01, self.config_obj.caption_offset)
        plt.figtext(
            self.config_obj.caption_align, y_pos,
            self.config_obj.plot_caption,
            fontproperties=font_properties,
            color=self.config_obj.parameters['caption_col'],
        )

    def _add_legend(self, ax: plt.Axes, handles_and_labels=None, loc='upper center') -> None:
        """Creates a plot legend based on the properties from the config file.
        Note: This should be called after adding the series, because the plot
        labels need to be created before including them in the legend.
        """
        orientation = "horizontal" if self.config_obj.legend_orientation == 'h' else "vertical"

        handles, labels = ax.get_legend_handles_labels()
        if handles_and_labels:
            handles = [item[0] for item in handles_and_labels]
            labels = [item[1] for item in handles_and_labels]

        if not handles:
            print("Warning: No labels found. Use ax.plot(..., label='name')")

        # handle plots that only have a single boolean for show legend
        show_legend = self.config_obj.show_legend
        if isinstance(show_legend, bool):
            show_legend = [show_legend] * len(handles)

        # only show legend entries that have show_legend set to True
        filtered_handles = [h for h, show in zip(handles, show_legend) if show == 1]
        filtered_labels = [l for l, show in zip(labels, show_legend) if show == 1]

        legend = ax.legend(
            handles=filtered_handles,
            labels=filtered_labels,
            bbox_to_anchor=(self.config_obj.bbox_x, self.config_obj.bbox_y),
            loc=loc,
            edgecolor=self.config_obj.legend_border_color,
            frameon=self.config_obj.draw_box,
            ncol=max(1, len(handles)) if orientation == "horizontal" else 1,
            fontsize=self.config_obj.legend_size,
            labelcolor="black"
        )
        if legend:
            frame = legend.get_frame()
            frame.set_linewidth(self.config_obj.legend_border_width)

    def _add_xaxis(self, ax: plt.Axes, fontproperties: FontProperties, label=None, grid_on=None) -> None:
        """
        Configures and adds x-axis to the plot. Handles vertical plot by switching x and y axis.
        """
        is_vert = getattr(self.config_obj, 'vert_plot', False)
        if label is None:
            label = self.config_obj.xaxis if not is_vert else self.config_obj.yaxis_1

        if grid_on is None:
            grid_on = self.config_obj.grid_on

        ax.set_xlabel(label, fontproperties=fontproperties,
                      labelpad=abs(self.config_obj.parameters['xlab_offset']) * constants.PIXELS_TO_POINTS)

        if self.config_obj.indy_label and not is_vert:
            xtick_locs = self._get_xtick_locs()
            ax.set_xticks(xtick_locs, self.config_obj.indy_label)

        ax.tick_params(axis="x", direction="in", which="both", labelrotation=self.config_obj.x_tickangle)
        if grid_on:
            ax.grid(True, which='major', axis='x', color=self.config_obj.blended_grid_col,
                    linestyle='-', linewidth=self.config_obj.parameters['grid_lwd'])
            ax.set_axisbelow(True)

        if not is_vert:
            if len(self.config_obj.parameters.get('xlim', [])) > 0:
                # TODO: support xlim_step? only used for line plots
                ax.set_xlim(self.config_obj.parameters['xlim'])
            elif getattr(self.config_obj, 'start_from_zero', False):
                xtick_locs = self._get_xtick_locs()
                if len(xtick_locs) > 0:
                    ax.set_xlim(min(xtick_locs), max(xtick_locs))

            if self.config_obj.xaxis_reverse:
                ax.invert_xaxis()
        else:
            if len(self.config_obj.parameters['ylim']) > 0:
                ax.set_xlim(self.config_obj.parameters['ylim'])

            if self.config_obj.yaxis_reverse:
                ax.invert_xaxis()

    def _add_yaxis(self, ax: plt.Axes, fontproperties: FontProperties, label=None, grid_on=None) -> None:
        """
        Configures and adds y-axis to the plot. Handles vertical plot by switching x and y axis.
        """
        is_vert = getattr(self.config_obj, 'vert_plot', False)
        if label is None:
            label = self.config_obj.yaxis_1 if not is_vert else self.config_obj.xaxis

        if grid_on is None:
            grid_on = self.config_obj.grid_on

        ax.set_ylabel(label, fontproperties=fontproperties,
                      labelpad=abs(self.config_obj.parameters['ylab_offset']) * constants.PIXELS_TO_POINTS)
        ax.tick_params(axis="y", direction="in", which="both", labelrotation=self.config_obj.y_tickangle)

        # add grid lines if requested
        if grid_on:
            ax.grid(True, which='major', axis='y', color=self.config_obj.blended_grid_col, linestyle='-', linewidth=self.config_obj.parameters['grid_lwd'])
            ax.set_axisbelow(True)

        if not is_vert:
            # set y limits if min/max are defined in config
            if len(self.config_obj.parameters['ylim']) > 0:
                ax.set_ylim(self.config_obj.parameters['ylim'])

            if self.config_obj.yaxis_reverse:
                ax.invert_yaxis()
        else:
            if self.config_obj.indy_label:
                xtick_locs = self._get_xtick_locs()
                ax.set_yticks(xtick_locs, self.config_obj.indy_label)

                if getattr(self.config_obj, 'start_from_zero', False):
                    if len(xtick_locs) > 0:
                        ax.set_ylim(min(xtick_locs), max(xtick_locs))

            if self.config_obj.xaxis_reverse:
                ax.invert_yaxis()

    def _get_xtick_locs(self):
        # use the indices as tick locations
        xtick_locs = np.arange(len(self.config_obj.indy_label))
        if self.config_obj.indy_vals:
            # Use the actual numeric values from indy_vals as tick locations
            try:
                xtick_locs = [float(i) for i in self.config_obj.indy_vals]
            # if they are not numeric, revert to using the indices
            except ValueError:
                pass

        return xtick_locs


    def _get_nstats(self) -> list:
        """
        Calculates n_stats for the x2 axis.
        Default implementation sums nstat across all active series.
        """
        n_stats = [0] * len(self.config_obj.indy_vals)
        for series in self.series_list:
            if series.plot_disp:
                # aggregate number of stats
                n_stats = list(map(add, n_stats, series.series_points.get('nstat', [])))

        return n_stats

    def _add_x2axis(self, ax, n_stats, fontproperties: FontProperties) -> None:
        """
        Creates x2axis based on the properties from the config file.

        Note: This function is based on logic from individual plots that show number of stats (n_stats)
        on the top x-axis. This will need to be modified if other plots display a 2nd x-axis
        with other information.

        Note: this function may need to be called after adding the series, because some
        plots add ticks that will conflict with the explicit x ticks set in this function.
        Calliing this after will override the ticks and prevent a conflict.

        :param n_stats labels for the axis
        """
        if not self.config_obj.show_nstats:
            return

        num_lines = 1
        if n_stats and isinstance(n_stats, list) and len(n_stats) > 0 and isinstance(n_stats[0], list):
            num_lines = len(n_stats[0])

        # Adjust labelpad based on number of n_stats lines to avoid overlap
        # Each line takes approximately fontsize points + some spacing
        extra_pad = 0
        if num_lines > 1:
            extra_pad = num_lines * self.config_obj.x2_tickfont_size * 1.2

        label_args = {
            'fontproperties': fontproperties,
            'labelpad': (abs(self.config_obj.parameters['x2lab_offset']) * constants.PIXELS_TO_POINTS) + extra_pad,
        }

        if not self.config_obj.vert_plot:
            ax_top = ax.secondary_xaxis('top')
            ax_top.set_xlabel('NStats', **label_args)
            self._set_nstat_ticks(ax, ax_top, n_stats, is_vertical=False)

            # adjust title padding if x2 axis is shown on top
            if num_lines > 1:
                ax.set_title(ax.get_title(),
                             fontproperties=ax.title.get_fontproperties(),
                             color=ax.title.get_color(),
                             pad=extra_pad + 15,
                             x=self.config_obj.parameters['title_align'],
                             y=self.config_obj.title_offset)

        else:
            ax_right = ax.secondary_yaxis('right')
            ax_right.set_ylabel('NStats', **label_args)
            self._set_nstat_ticks(ax, ax_right, n_stats, is_vertical=True)

    def _set_nstat_ticks(self, ax, ax_secondary, n_stats, is_vertical=False):
        if not n_stats:
            return

        if is_vertical:
            current_locs = ax.get_yticks()
        else:
            current_locs = ax.get_xticks()

        # handle single value, single color n_stat (list of strings or ints)
        if not isinstance(n_stats[0], list):
            if is_vertical:
                ax_secondary.set_yticks(current_locs, labels=n_stats, size=self.config_obj.x2_tickfont_size)
            else:
                ax_secondary.set_xticks(current_locs, labels=n_stats, size=self.config_obj.x2_tickfont_size)
            return

        # handle n_stat for multiple series that are color coded
        if is_vertical:
            ax_secondary.set_yticks(current_locs)
            ax_secondary.set_yticklabels([])
            transform = ax.get_yaxis_transform()  # X=axes coords, Y=data coords
        else:
            ax_secondary.set_xticks(current_locs)
            ax_secondary.set_xticklabels([])
            transform = ax.get_xaxis_transform()  # X=data coords, Y=axes coords

        for i, loc in enumerate(current_locs):
            # Avoid IndexError if current_locs has more ticks than n_stats
            if i >= len(n_stats):
                break
            for j, stat_info in enumerate(n_stats[i]):
                # Offset position for each series to mimic newlines
                # Using offset points ensures consistent spacing regardless of plot size
                if is_vertical:
                    x, y = 1.0, loc
                    offset_x = (j * self.config_obj.x2_tickfont_size * 1.2) + 2
                    offset_y = 0
                    ha, va = 'left', 'center'
                else:
                    x, y = loc, 1.0
                    offset_x = 0
                    offset_y = (j * self.config_obj.x2_tickfont_size * 1.2) + 2
                    ha, va = 'center', 'bottom'

                # Use the main axes 'ax' to add the text with offset points
                ax.annotate(stat_info['val'],
                            xy=(x, y),
                            xycoords=transform,
                            xytext=(offset_x, offset_y),
                            textcoords='offset points',
                            color=stat_info['color'],
                            ha=ha, va=va,
                            fontsize=self.config_obj.x2_tickfont_size)

    def _add_y2axis(self, ax: plt.Axes, fontproperties: Union[FontProperties, None]):
        """
        Adds y2-axis if needed
        """
        ax_right = ax.twinx()
        ax_right.spines['right'].set_visible(True)
        ax_right.set_ylabel(self.config_obj.yaxis_2, fontproperties=fontproperties,
                            labelpad=abs(self.config_obj.parameters['y2lab_offset']) * constants.PIXELS_TO_POINTS)

        # set y2 limits if defined in config
        if len(self.config_obj.parameters['y2lim']) > 0:
            ax_right.set_ylim(self.config_obj.parameters['y2lim'])

        return ax_right

    def _sync_yaxes(self, ax, ax2, yaxis_min: Union[float, None], yaxis_max: Union[float, None]):
        if not self.config_obj.sync_yaxes or self.config_obj.vert_plot:
            return

        # set y limits if defined in config or if min/max are provided
        if len(self.config_obj.parameters['ylim']) > 0:
            yaxis_min = self.config_obj.parameters['ylim'][0]
            yaxis_max = self.config_obj.parameters['ylim'][1]

        if yaxis_min is not None and yaxis_max is not None:
            ax.set_ylim(yaxis_min, yaxis_max)
            ax2.set_ylim(yaxis_min, yaxis_max)

    def _add_lines(self, ax: plt.Axes, config_obj: Config, x_points_index: Union[list, None] = None) -> None:
        """Adds custom horizontal and/or vertical line to the plot.
           All line's metadata is in the config_obj.lines
            Args:
                @param ax - matplotlib Axes object
                @param config_obj plot configuration object
                @param x_points_index optional list of x-values that are used to create vertical line
        """
        if not hasattr(config_obj, 'lines') or config_obj.lines is None:
            return

        for line in config_obj.lines:

            # format line properties in format that matplotlib expects
            line_properties = {
                'color': line['color'],
                'linewidth': line['line_width'],
                'linestyle': line['line_style'],
            }

            # draw horizontal line
            if line['type'] == 'horiz_line':

                y_position = line['position']
                self.add_horizontal_line(ax, y_position, line_properties)

            elif line['type'] == 'vert_line':

                # draw vertical line
                x_position = line['position']
                try:
                    if x_points_index is not None:
                        ordered_indy_label = config_obj.create_list_by_plot_val_ordering(
                            config_obj.indy_label)
                        index = ordered_indy_label.index(line['position'])
                        x_position = x_points_index[index]

                    self.add_vertical_line(ax, x_position, line_properties)

                except ValueError:
                    msg = f"Vertical line with position {x_position} cannot be created."
                    self.logger.warning(msg)
                    print(f"WARNING: {msg}")

    def _get_x_locs_and_width(self, x_points, index, stagger_scale=None):
        if stagger_scale is None:
            stagger_scale = constants.MPL_DEFAULT_BAR_WIDTH

        try:
            # Attempt to convert x_points to floats (handles numeric indy_vals)
            # Threshold values (e.g., ">5.0") will raise a ValueError/TypeError
            base = np.array([float(x) for x in x_points])

            if len(base) > 1:
                # Calculate the minimum spacing between numeric x-points
                # to determine an appropriate bar width.
                sorted_base = np.sort(base)
                spacing = np.diff(sorted_base)
                min_spacing = np.min(spacing)
                # Ensure spacing is positive to avoid zero-width bars
                if min_spacing <= 0:
                    min_spacing = 1.0
            else:
                min_spacing = 1.0
        except (ValueError, TypeError):
            # Fallback to integer indices for non-numeric data (e.g., thresholds)
            base = np.arange(len(x_points))
            min_spacing = 1.0

        n_visible_series = sum(1 for s in self.series_list if s.plot_disp)
        n = max(n_visible_series, 1)

        # Scale width and offset by min_spacing to ensure bars fit within the numeric gaps
        width = (min_spacing * stagger_scale) / n
        offset = (index - (n - 1) / 2.0) * width
        x_locs = base + offset
        return x_locs, width

    def write_output_file(self) -> None:
        """To be implemented by child class"""
        pass
