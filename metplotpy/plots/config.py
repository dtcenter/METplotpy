"""
Class Name: config.py

Holds values set in the config file(s)
"""
__author__ = 'Minna Win'
__email__ = 'met_help@ucar.edu'


class Config:
    """
       Handles reading in and organizing configuration settings in the yaml configuration file.
    """
    # Default values...
    DEFAULT_TITLE_FONT = 'sans-serif'
    DEFAULT_TITLE_COLOR = 'darkblue'
    DEFAULT_TITLE_FONTSIZE = 10
    AVAILABLE_MARKERS_LIST = ["o", "^", "s", "d", "H", "."]

    def __init__(self, parameters):

        self.parameters = parameters

        #
        # Configuration settings that apply to the plot
        #
        self.output_image = self.get_config_value('plot_output')
        self.title_font = self.DEFAULT_TITLE_FONT
        self.title_color = self.DEFAULT_TITLE_COLOR
        self.xaxis = self.get_config_value('xaxis')
        self.yaxis = self.get_config_value('yaxis')
        self.title = self.get_config_value('title')

        # employ event equalization if requested
        self.use_ee = self.get_config_value('event_equalization')

        #for now, we will print out a message indicating that event equalization is requested
        if self.use_ee:
            print("Event equalization requested")
        else:
            print("Event equalization turned off.")

        self.indy_vals = self.get_config_value('indy_vals')
        self.indy_var = self.get_config_value('indy_var')

        # These are the inner keys to the series_val setting, and
        # they represent the series variables of
        # interest.  The keys correspond to the column names
        # in the input dataframe.
        self.series_vals = self._get_series_vals()

        # Represent the names of the forecast variables (inner keys) to the fcst_var_val setting.
        # These are the names of the columns in the input dataframe.
        self.fcst_vars = self._get_fcst_vars()

        # These are the inner values to the series_val setting (these correspond to the
        # keys returned in self.series_vals above).  These are the specific variable values to
        # be used in subsetting the input dataframe (e.g. for key='model', and value='SH_CMORPH',
        # we want to subset data where column name is 'model', with coincident rows of 'SH_CMORPH'.
        self.series_val_names = self._get_series_val_names()


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


    def _get_series_vals(self):
        """
            Get a list of all the variable values that correspond to the inner
            key of the series_val dictionary.
            These values will be used with lists of other config values to
            create filtering criteria.  This is useful to subset the input data
            to assist in identifying the data points for this series.

            Args:

            Returns:
                a "list of lists" of *all* the values of the inner dictionary
                of the series_val dictionary

        """


        series_val_dict = self.get_config_value('series_val')

        # Unpack and access the values corresponding to the inner keys
        # (series_var1, series_var2, ..., series_varn).
        return [*series_val_dict.values()]

    def _get_fcst_vars(self):
        """
           Retrieve a list of the inner keys (fcst_vars) to the fcst_var_val dictionary.

           Args:

           Returns:
               a list containing all the fcst variables requested in the
               fcst_var_val setting in the config file.  This will be
               used to subset the input data that corresponds to a particular series.

        """
        fcst_var_val_dict = self.get_config_value('fcst_var_val')
        all_fcst_vars = [*fcst_var_val_dict.keys()]
        return all_fcst_vars

    def _get_series_val_names(self):
        """
            Get a list of all the variable value names (i.e. inner key of the
            series_val dictionary). These values will be used with lists of
            other config values to create filtering criteria.  This is useful
            to subset the input data to assist in identifying the data points
            for this series.

            Args:

            Returns:
                a "list of lists" of *all* the keys to the inner dictionary of
                the series_val dictionary

        """


        series_val_dict = self.get_config_value('series_val')

        # Unpack and access the values corresponding to the inner keys
        # (series_var1, series_var2, ..., series_varn).
        return [*series_val_dict.keys()]
