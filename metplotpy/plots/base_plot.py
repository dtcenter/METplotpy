# !/usr/bin/env conda run -n blenny_363 python
"""
Class Name: base_plot.py
 """
__author__ = 'Tatiana Burek'

import os
import numpy as np
import yaml
from typing import Union

from config import Config


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
            location = os.path.join(os.environ['METPLOTPY_BASE'], 'plots/config')
        else:
            location = os.path.realpath(os.path.join(os.getcwd(), '../config'))

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

    def get_legend(self):
        """Creates a Plotly legend dictionary with values from users and default parameters
        If users parameters dictionary doesn't have needed values - use defaults

        Args:

        Returns:
            - dictionary used by Plotly to build the legend
        """

        current_legend = dict(
            x=self.get_config_value('legend', 'x'),  # x-position
            y=self.get_config_value('legend', 'y'),  # y-position
            font=dict(
                family=self.get_config_value('legend', 'font', 'family'),  # font family
                size=self.get_config_value('legend', 'font', 'size'),  # font size
                color=self.get_config_value('legend', 'font', 'color'),  # font color
            ),
            bgcolor=self.get_config_value('legend', 'bgcolor'),  # background color
            bordercolor=self.get_config_value('legend', 'bordercolor'),  # border color
            borderwidth=self.get_config_value('legend', 'borderwidth'),  # border width
            xanchor=self.get_config_value('legend', 'xanchor'),  # horizontal position anchor
            yanchor=self.get_config_value('legend', 'yanchor')  # vertical position anchor
        )
        return current_legend

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
        legend_settings = dict(border_width=borderwidth,
                               orientation=legend_orientation,
                               legend_inset=dict(x=legend_inset['x'],
                                                 y=legend_inset['y']),
                               legend_size=legend_size)

        return legend_settings

    def get_title(self):
        """Creates a Plotly title dictionary with values from users and default parameters
        If users parameters dictionary doesn't have needed values - use defaults

        Args:

        Returns:
            - dictionary used by Plotly to build the title
        """
        current_title = dict(
            text=self.get_config_value('title'),  # plot's title
            # Sets the container `x` refers to. "container" spans the entire `width` of the plot.
            # "paper" refers to the width of the plotting area only.
            xref="paper",
            x=0.5  # x position with respect to `xref`
        )
        return current_title

    def get_xaxis(self):
        """Creates a Plotly x-axis dictionary with values from users and default parameters
        If users parameters dictionary doesn't have needed values - use defaults

        Args:

        Returns:
            - dictionary used by Plotly to build the x-axis
        """
        current_xaxis = dict(
            linecolor=self.get_config_value('xaxis', 'linecolor'),  # x-axis line color
            # whether or not a line bounding x-axis is drawn
            showline=self.get_config_value('xaxis', 'showline'),
            linewidth=self.get_config_value('xaxis', 'linewidth')  # width (in px) of x-axis line
        )
        return current_xaxis

    def get_yaxis(self):
        """Creates a Plotly y-axis dictionary with values from users and default parameters
        If users parameters dictionary doesn't have needed values - use defaults

        Args:

        Returns:
            - dictionary used by Plotly to build the y-axis
        """
        current_yaxis = dict(
            linecolor=self.get_config_value('yaxis', 'linecolor'),  # y-axis line color
            linewidth=self.get_config_value('yaxis', 'linewidth'),  # width (in px) of y-axis line
            # whether or not a line bounding y-axis is drawn
            showline=self.get_config_value('yaxis', 'showline'),
            # whether or not grid lines are drawn
            showgrid=self.get_config_value('yaxis', 'showgrid'),
            ticks=self.get_config_value('yaxis', 'ticks'),  # whether ticks are drawn or not.
            tickwidth=self.get_config_value('yaxis', 'tickwidth'),  # Sets the tick width (in px).
            tickcolor=self.get_config_value('yaxis', 'tickcolor'),  # Sets the tick color.
            # the width (in px) of the grid lines
            gridwidth=self.get_config_value('yaxis', 'gridwidth'),
            gridcolor=self.get_config_value('yaxis', 'gridcolor')  # the color of the grid lines
        )

        # Sets the range of the range slider. defaults to the full y-axis range
        y_range = self.get_config_value('yaxis', 'range')
        if y_range is not None:
            current_yaxis['range'] = y_range
        return current_yaxis

    def get_xaxis_title(self):
        """Creates a Plotly x-axis label title dictionary with values
        from users and default parameters.
        If users parameters dictionary doesn't have needed values - use defaults

        Args:

        Returns:
            - dictionary used by Plotly to build the x-axis label title as annotation
        """
        x_axis_label = dict(
            x=self.get_config_value('xaxis', 'x'),  # x-position of label
            y=self.get_config_value('xaxis', 'y'),  # y-position of label
            showarrow=False,
            text=self.get_config_value('xaxis', 'title', 'text'),
            xref="paper",  # the annotation's x coordinate axis
            yref="paper",  # the annotation's y coordinate axis
            font=dict(
                family=self.get_config_value('xaxis', 'title', 'font', 'family'),
                size=self.get_config_value('xaxis', 'title', 'font', 'size'),
                color=self.get_config_value('xaxis', 'title', 'font', 'color'),
            )
        )
        return x_axis_label

    def get_yaxis_title(self):
        """Creates a Plotly y-axis label title dictionary with values
         from users and default parameters
        If users parameters dictionary doesn't have needed values - use defaults

        Args:

        Returns:
            - dictionary used by Plotly to build the y-axis label title as annotation
        """
        y_axis_label = dict(
            x=self.get_config_value('yaxis', 'x'),  # x-position of label
            y=self.get_config_value('yaxis', 'y'),  # y-position of label
            showarrow=False,
            text=self.get_config_value('yaxis', 'title', 'text'),
            textangle=-90,  # the angle at which the `text` is drawn with respect to the horizontal
            xref="paper",  # the annotation's x coordinate axis
            yref="paper",  # the annotation's y coordinate axis
            font=dict(
                family=self.get_config_value('xaxis', 'title', 'font', 'family'),
                size=self.get_config_value('xaxis', 'title', 'font', 'size'),
                color=self.get_config_value('xaxis', 'title', 'font', 'color'),
            )
        )
        return y_axis_label

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
        if self.figure:
            try:
                self.figure.write_image(image_name)
            except FileNotFoundError:
                print("Can't save to file " + image_name)
            except ValueError as ex:
                print(ex)
        else:
            print("Oops!  The figure was not created. Can't save.")

    def remove_file(self):
        """Removes previously made image file .
        """
        image_name = self.get_config_value('plot_filename')

        # remove the old file if it exist
        if os.path.exists(image_name):
            os.remove(image_name)

    def show_in_browser(self):
        """Creates a plot and opens it in the browser.

         Args:

         Returns:

         """
        if self.figure:
            self.figure.show()
        else:
            print("Oops!  The figure was not created. Can't show")

    def _add_lines(self, config_obj: Config, x_points_index: Union[list, None] = None) -> None:
        """ Adds custom horizontal and/or vertical line to the plot.
            All line's metadata is in the config_obj.lines
            Args:
                @config_obj - plot's configurations
                @x_points_index - list of x-values that are used to create a plot
            Returns:
        """
        if hasattr(config_obj, 'lines') and config_obj.lines is not None:
            shapes = []
            for line in config_obj.lines:
                # draw horizontal line
                if line['type'] == 'horiz_line':
                    shapes.append(dict(
                        type='line',
                        yref='y', y0=line['position'], y1=line['position'],
                        xref='paper', x0=0, x1=0.95,
                        line={'color': line['color'],
                              'dash': line['line_style'],
                              'width': line['line_width']},
                    ))
                elif line['type'] == 'vert_line':
                    # draw vertical line
                    try:
                        if x_points_index is None:
                            val = line['position']
                        else:
                            ordered_indy_label = config_obj.create_list_by_plot_val_ordering(config_obj.indy_label)
                            index = ordered_indy_label.index(line['position'])
                            val = x_points_index[index]
                        shapes.append(dict(
                            type='line',
                            yref='paper', y0=0, y1=1,
                            xref='x', x0=val, x1=val,
                            line={'color': line['color'],
                                  'dash': line['line_style'],
                                  'width': line['line_width']},
                        ))
                    except ValueError:
                        print(f'WARNING: vertical line with position {line["position"]} can\'t be created')
                # ignore everything else

            # draw lines
            self.figure.update_layout(shapes=shapes)

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
