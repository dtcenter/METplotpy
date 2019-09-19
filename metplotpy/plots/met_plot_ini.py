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
        image_name = self.get_item_value('config','image_name')
        if image_name:

            # extract and validate the file extension
            strings = image_name.split('.')
            if strings and strings[-1] in self.IMAGE_FORMATS:
                return strings[-1]

        # print the message if invalid and return default
        print('Unrecognised image format. png will be used')
        return self.DEFAULT_IMAGE_FORMAT


    def get_item_value(self, section_of_interest, item_of_interest):
        """
        Get the value for a key (item of interest). i.e. the value to a key-value pairing
        from a specific section (section_of_interest)


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


