"""
Class Name: met_plot_ini.py
Base class for METplotpy plots that use INI config files.
 """
__author__ = "Minna Win adapted from Tatiana Burek's met_plot.py"
__email__ = 'met_help@ucar.edu'



import os

class MetPlotIni:
    """A class that provides methods for building Plotly plot's common features
        like title, axis, legend.

     To use:
        use as a abstract class for the common plot types
    """

    # image formats supported by plotly
    IMAGE_FORMATS = ("png", "jpeg", "webp", "svg", "pdf", "eps")
    DEFAULT_IMAGE_FORMAT = 'png'

    def __init__(self, parameters, defaults):
        """Inits MetPlot with user defined and default dictionaries.
           Removes the old image it it exists

        Args:
            parameters - dictionary containing default and user defined parameters
            defaults   - dictionary containing Metplotpy default parameters

        """

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
        image_name = self.get_config_value('config','image_name')
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
            x=float(self.get_config_value('legend', 'x')),  # x-position
            y=float(self.get_config_value('legend', 'y')),  # y-position
            font=dict(
                family=self.get_config_value('legend', 'font_family'),  # font family
                size=int(self.get_config_value('legend', 'font_size')),  # font size
                color=self.get_config_value('legend', 'font_color'),  # font color
            ),
            bgcolor=self.get_config_value('legend', 'bgcolor'),  # background color
            bordercolor=self.get_config_value('legend', 'border_color'),  # border color
            borderwidth=int(self.get_config_value('legend', 'border_width')),  # border width
            xanchor=self.get_config_value('legend', 'xanchor'),  # horizontal position anchor
            yanchor=self.get_config_value('legend', 'yanchor')  # vertical position anchor
        )
        return current_legend

    def get_title(self):
        """Creates a Plotly title dictionary with values from users and default parameters
        If users parameters dictionary doesn't have needed values - use defaults

        Args:

        Returns:
            - dictionary used by Plotly to build the title
        """
        current_title = dict(
            text=self.get_config_value('config', 'title'),  # plot's title
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
            linecolor = self.get_config_value('xaxis', 'linecolor'),  # x-axis line color
            # whether or not a line bounding x-axis is drawn
            showline = self.convert_str_to_bool(self.get_config_value('xaxis', 'showline')),
            # width (in px) of x-axis line, convert to int
            linewidth = int(self.get_config_value('xaxis', 'linewidth'))
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
            # y-axis line color
            linecolor = self.get_config_value('yaxis', 'linecolor'),
            # width (in px) of y-axis line, convert to int
            linewidth = int(self.get_config_value('yaxis', 'linewidth')),
            # whether or not a line bounding y-axis is drawn, convert from string to bool value
            showline = self.convert_str_to_bool(self.get_config_value('yaxis', 'showline')),
            # whether or not grid lines are drawn, convert to bool
            showgrid = self.convert_str_to_bool(self.get_config_value('yaxis', 'showgrid')),
            # whether ticks are drawn or not.
            ticks = self.get_config_value('yaxis', 'ticks'),
            # ticks = self.convert_str_to_bool(self.get_config_value('yaxis', 'ticks')),
            # Sets the tick width (in px).
            tickwidth = int(self.get_config_value('yaxis', 'ticks_tickwidth')),
            # Sets the tick color.
            tickcolor=self.get_config_value('yaxis', 'tickcolor'),
            # the width (in px) of the grid lines
            gridwidth=int(self.get_config_value('yaxis', 'gridwidth')),
            # the color of the grid lines
            gridcolor=self.get_config_value('yaxis', 'gridcolor')
        )

        # Sets the range of the range slider. defaults to the full y-axis range
        y_range_start = self.get_config_value('yaxis', 'range_start')
        y_range_end = self.get_config_value('yaxis', 'range_end')
        y_range = [y_range_start, y_range_end]
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
            text=self.get_config_value('xaxis_title', 'text'),
            xref="paper",  # the annotation's x coordinate axis
            yref="paper",  # the annotation's y coordinate axis
            font=dict(
                family=self.get_config_value('xaxis_title', 'font_family'),
                size=int(self.get_config_value('xaxis_title', 'font_size')),
                color=self.get_config_value('xaxis_title', 'font_color'),
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
            text=self.get_config_value('yaxis_title', 'text'),
            textangle=-90,  # the angle at which the `text` is drawn with respect to the horizontal
            xref="paper",  # the annotation's x coordinate axis
            yref="paper",  # the annotation's y coordinate axis
            font=dict(
                family=self.get_config_value('yaxis_title', 'font_family'),
                size=int(self.get_config_value('yaxis_title', 'font_size')),
                color=self.get_config_value('yaxis_title', 'font_color'),
            )
        )
        return y_axis_label

    def get_config_value(self, section_of_interest, item_of_interest):
        """
        This method provides support for reading in and parsing the INI style of configuration
        file by utilizing the produtil and METplus wrapper modules.

        Get the value for a key (item of interest). i.e. the value to a key-value pairing
        from a specific section (section_of_interest).


        Input:

            @param section_of_interest:   The section (in an INI config file) where the
                                          item of interest is found. Sections are defined by
                                          square brackets: []
            @param item_of_interest:   The item of interest (where item of interest
                                       is the key in a key-value pairing in the INI config file)

        Returns:
           The value of the item_of_interest, i.e. the value corresponding to the key in the key-value
           pair, where the key corresponds to the item_of_interest.
        """

        config = self.parameters
        all_items = self.parameters.items()

        # Get a list of (option, value) tuple representing the key-value pairs found in the
        # section of interest.
        for item in all_items:
            if item[0] == section_of_interest:
                # Retrieve the keys for this section
                keys = config[item[0]].keys()
                for key in keys:
                    if key == item_of_interest:
                        return config[item[0]][key]
        else:
            # If we got here, we didn't find the item_of_interest in the configuration file
            # set the value to None so that the default value will be used instead.
            config[section_of_interest][item_of_interest] = None


    def _get_nested(self, data, args):
        """Recursive function that uses the tuple with keys to find a value
        in multidimensional dictionary.

        Args:
            data - dictionary for the lookup
            args  - a tuple with keys

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
        image_name = self.get_config_value('config', 'image_name')
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
        """Removes previously made  image file .
        """
        image_name = self.get_config_value('config', 'image_name')

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

    def convert_str_to_bool(self, str):
        """ Converts a string value of true/True/etc and false/False/etc to the corresponding
            boolean values.  All values in the INI config file are read in as strings.  Some
            of these values need to be converted to boolean.

            Input:
                @param str:  The input string to convert to it's corresponding boolean value

            Return:
               a boolean value: True or False
        """
        if str.upper() == 'TRUE':
            return True
        elif str.upper() == 'FALSE':
            return False
        else:
            raise ValueError("True or False expected but not set, please check configuration file.")

    def is_conf_missing_section(self, section_of_interest):
        """ Checks if the configuration file is missing the section of interest.
            If the section of interest is missing, we will get an error because the
            configuration is a dictionary, and the section of interest is the outer key in
            the configuration dictionary.

            Input:
            @param section_of_interest:  The section (outer key) of a dictionary representation of a configuration
                                         file.

            Returns:
            boolean value True if the section of interest is missing, False otherwise

        """

