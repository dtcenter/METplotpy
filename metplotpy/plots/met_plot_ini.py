"""
Class Name: met_plot_ini.py
Base class for METplotpy plots that use INI config files.
 """
__author__ = 'Minna Win'
__email__ = 'met_help@ucar.edu'

from config_launcher import METplusLauncher



class MetPlotIni:
    """A class that provides methods for building Plotly plot's common features
        like title, axis, legend.

        To use:
           use as an abstract class for the common plot types
       """
    # image formats supported by plotly
    IMAGE_FORMATS = ("png", "jpeg", "webp", "svg", "pdf", "eps")
    DEFAULT_IMAGE_FORMAT = 'png'

    def __init__(self, parameters):
        """Inits MetPlot with user defined and default dictionaries.

        Args:
            parameters - dictionary representation of user defined parameters derived from
                         the INI style configuration file (parameters can be represented
                         by a configuration object).
            # defaults   - dictionary containing Metplotpy default parameters
        """
        self.parameters = parameters
        # self.defaults = defaults
        self.figure = None


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


    def get_title(self):
        """Creates a Plotly title dictionary with values from users and default parameters
        If users parameters dictionary doesn't have needed values - use defaults

        Args:

        Returns:
            - dictionary used by Plotly to build the title
        """
        current_title = dict(
            # How to get the title text from the yaml config file
            # text=self.get_config_value('title'),  # plot's title
            text = self.get_config_value('config', 'title'),
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
            # x-axis line color
            linecolor = self.get_config_value('xaxis', 'linecolor'),
            # whether or not a line bounding x-axis is drawn
            showline = self.get_config_value('xaxis', 'showline'),
            # width (in px) of x-axis line
            linewidth = self.get_config_value('xaxis', 'linewidth')
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
            # width (in px) of y-axis line
            linewidth = self.get_config_value('yaxis', 'linewidth'),
            # whether or not a line bounding y-axis is drawn
            showline = self.get_config_value('yaxis', 'showline'),
            # whether or not grid lines are drawn
            showgrid = self.get_config_value('yaxis', 'showgrid'),
            # whether ticks are drawn or not.
            ticks = self.get_config_value('yaxis', 'ticks'),
            # Sets the tick width (in px).
            tickwidth = self.get_config_value('yaxis', 'ticks_tickwidth'),
            # Sets the tick color.
            tickcolor=self.get_config_value('yaxis', 'tickcolor'),
            # the width (in px) of the grid lines
            gridwidth=self.get_config_value('yaxis', 'gridwidth'),
            # the color of the grid lines
            gridcolor=self.get_config_value('yaxis', 'gridcolor')
        )

        # Sets the range of the range slider. defaults to the full y-axis range
        y_range = self.get_config_value('yaxis', 'range')
        if y_range:
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
                size=self.get_config_value('xaxis_title', 'font_size'),
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
                size=self.get_config_value('yaxis_title', 'font_size'),
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
        all_items = self.parameters.items(section_of_interest)

        # Get a list of (option, value) tuple representing the key-value pairs found in the
        # section of interest.
        for item in all_items:
            if item[0] == item_of_interest:
                return item[1]
        else:
            # If we got here, we didn't find the item_of_interest in the configuration file
            raise Exception("The item of interest was not found in the configuration file.  Please check your configuration file.")


