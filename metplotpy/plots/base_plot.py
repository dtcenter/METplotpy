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
import numpy as np
from matplotlib.font_manager import FontProperties
import yaml
from typing import Union
from metplotpy.plots.util import strtobool
from .config import Config
from . import constants

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

    # image formats supported by plotly
    IMAGE_FORMATS = ("png", "jpeg", "webp", "svg", "pdf", "eps")
    DEFAULT_IMAGE_FORMAT = 'png'

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

    def get_image_format(self):
        """Reads the image format type from user provided image name.
        Uses file extension as a type. If the file extension is not valid -
        returns 'png' as a default

        Args:

        Returns:
            - image format
        """

        # get image name from properties
        image_name = self.get_config_value('image_name')
        if image_name:

            # extract and validate the file extension
            strings = image_name.split('.')
            if strings and strings[-1] in self.IMAGE_FORMATS:
                return strings[-1]

        # print the message if invalid and return default
        print('Unrecognised image format. png will be used')
        return self.DEFAULT_IMAGE_FORMAT



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
           Set up the font properties for the plot title: style (regular, italic), size,  and
           weight (normal, bold) for the title, captions, x-axis label, and y-axis label.

           Returns:
              weights_size_styles: A dictionary  containing the font property information
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
        if self.config_obj.x2lab_weight:
            x2lab_property= FontProperties()
            x2lab_property.set_size(self.config_obj.x2_title_font_size)
            x2lab_style, x2lab_wt = self.config_obj.x2lab_weight
            x2lab_property.set_style(x2lab_style)
            x2lab_property.set_weight(x2lab_wt)
            weights_size_styles['x2lab'] = x2lab_property

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

    def save_to_file(self):
        """Saves the image to a file specified in the config file.
         Prints a message if fails

        Args:

        Returns:

        """
        image_name = self.get_config_value('plot_filename')

        # Suppress deprecation warnings from third-party packages that are not in our control.
        warnings.filterwarnings("ignore", category=DeprecationWarning)

        # Create the directory for the output plot if it doesn't already exist
        dirname = os.path.dirname(os.path.abspath(image_name))
        os.makedirs(dirname, exist_ok=True)
        if self.figure:
            try:
                self.figure.write_image(image_name)
            except FileNotFoundError:
                self.logger.error(f"FileNotFoundError: Cannot save to file"
                                  f" {image_name}")
                # print("Can't save to file " + image_name)
            except ResourceWarning:
                self.logger.warning(f"ResourceWarning: in _kaleido"
                                  f" {image_name}")

            except ValueError as ex:
                self.logger.error(f"ValueError: Could not save output file.")
        else:
            self.logger.error(f"The figure {dirname} cannot be saved.")
            print("Oops!  The figure was not created. Can't save.")

    def remove_file(self):
        """Removes previously made image file .
        """
        image_name = self.get_config_value('plot_filename')

        # remove the old file if it exist
        if image_name is not None and os.path.exists(image_name):
            os.remove(image_name)

# TODO Remove Plotly specific,  use add_horizontal_line() and  add_vertical_line() below
# Plotly-specific,
    def _add_lines(self, config_obj: Config, x_points_index: Union[list, None] = None) -> None:
        """ Adds custom horizontal and/or vertical line to the plot.
            All line's metadata is in the config_obj.lines
            Args:
                @config_obj - plot's configurations
                @x_points_index - list of x-values that are used to create a plot
            Returns:
        """
        if not hasattr(config_obj, 'lines') or config_obj.lines is None:
            return

        shapes = []
        for line in config_obj.lines:
            # draw horizontal line
            if line['type'] == 'horiz_line':
                shapes.append({
                    'type': 'line',
                    'yref': 'y', 'y0': line['position'], 'y1': line['position'],
                    'xref': 'paper', 'x0': 0, 'x1': 0.95,
                    'line': {
                        'color': line['color'],
                        'dash': line['line_style'],
                        'width': line['line_width'],
                    },
                })
            elif line['type'] == 'vert_line':
                # draw vertical line
                try:
                    if x_points_index is None:
                        val = line['position']
                    else:
                        ordered_indy_label = config_obj.create_list_by_plot_val_ordering(config_obj.indy_label)
                        index = ordered_indy_label.index(line['position'])
                        val = x_points_index[index]
                    shapes.append({
                        'type': 'line',
                        'yref': 'paper', 'y0': 0, 'y1': 1,
                        'xref': 'x', 'x0': val, 'x1': val,
                        'line': {
                            'color': line['color'],
                            'dash': line['line_style'],
                            'width': line['line_width'],
                        }
                    })
                except ValueError:
                    line_position = line["position"]
                    msg = f"Vertical line with position {line_position} cannot be created."
                    self.logger.warning(msg)
                    print(msg)
            # ignore everything else

            # draw lines
            self.figure.update_layout(shapes=shapes)

    def add_horizontal_line(plt,y: float, line_properties: dict) -> None:
        """Adds a horizontal line to the matplotlib plot

        @param plt: Matplotlib pyplot object
        @param y y value for the line
        @param line_properties dictionary with line properties like color, width, dash
        @returns None
        """
        plt.axhline(y=y, xmin=0, xmax=1, **line_properties)

    def add_vertical_line(plt, x: float, line_properties: dict) -> None:
        """Adds a vertical line to the matplotlib plot

        @param plt: Matplotlib pyplot object
        @param x x value for the line
        @param line_properties dictionary with line properties like color, width, dash
        @returns None
        """
        plt.axvline(x=x, ymin=0, ymax=1, **line_properties)

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

    def _add_title(self, ax, font_properties):
        ax.set_title(
            self.config_obj.title,
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
