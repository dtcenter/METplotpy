"""
Class Name: roc_diagram.py
 """
__author__ = 'Minna Win'
__email__ = 'met_help@ucar.edu'

import os
import yaml
import pandas as pd
import matplotlib.pyplot as plt

import plots.util as util
from plots.met_plot import MetPlot
from roc_diagram_config import ROCDiagramConfig
from roc_diagram_series import ROCDiagramSeries

class ROCDiagram(MetPlot):
    """
        Creates a ROC diagram based on settings in a config file and
        either MET output data for the following line types:
            CTC (contingency table)
            PCT (probability contingency counts)

    """

    def __init__(self, parameters):
        """
            Instantiate a ROCDiagram object

            Args:
            @param parameters: dictionary containing user defined parameters

        """

        default_conf_filename = "roc_diagram_defaults.yaml"

        # init common layout
        super().__init__(parameters, default_conf_filename)

        # instantiate a PerformanceDiagramConfig object, which holds all the necessary settings from the
        # config file.
        self.config_obj = ROCDiagramConfig(parameters)

        # Read in input data, location specified in config file
        self.input_df = self._read_input_data()

        # Create a list of series objects.
        # Each series object contains all the necessary information for plotting,
        # such as line color, marker symbol,
        # line width, and criteria needed to subset the input dataframe.
        self.series_list = self._create_series(self.input_df)

        # create figure
        # pylint:disable=assignment-from-no-return
        # Need to have a self.figure that we can pass along to
        # the methods in met_plot.py (MetPlot class methods) to
        # create binary versions of the plot.
        # self.figure = self._create_figure()


    def _read_input_data(self):
        """
            Read the input data file (either CTC or PCT linetype)
            and store as a pandas dataframe so we can subset the
            data to represent each of the series defined by the
            series_val permutations.

            Args:

            Returns:

        """
        return pd.read_csv(self.config_obj.stat_input, sep='\t', header='infer')


    def _create_series(self, input_data):
        """
           Generate all the series objects that are to be displayed as specified by the plot_disp
           setting in the config file.  The points are all ordered by datetime.  Each series object
           is represented by a line in the performance diagram, so they also contain information
           for line width, line- and marker-colors, line style, and other plot-related/
           appearance-related settings (which were defined in the config file).

           Args:
               input_data:  The input data in the form of a Pandas dataframe.
                            This data will be subset to reflect the series data of interest.

           Returns:
               a list of series objects that are to be displayed


        """
        series_list = []

        # use the list of series ordering values to determine how many series objects we need.
        num_series = len(self.config_obj.series_ordering)

        for i, series in enumerate(range(num_series)):
            # Create a ROCDiagramSeries object
            series_obj = ROCDiagramSeries(self.config_obj, i, input_data)
            series_list.append(series_obj)
        return series_list


    def remove_file(self):
        """
           Removes previously made image file .  Invoked by the parent class before self.output_file
           attribute can be created, but overridden here.
        """

        image_name = self.get_config_value('plot_output')

        # remove the old file if it exist
        if os.path.exists(image_name):
            os.remove(image_name)


    def _create_figure(self):
        """
        Generate the performance diagram of varying number of series with POD and 1-FAR
        (Success Rate) values.  Hard-coding of labels for CSI lines and bias lines,
        and contour colors for the CSI curves.


        Args:


        Returns:
            Generates a performance diagram with equal lines of CSI (Critical Success Index)
            and equal lines of bias
        """

        # This creates a figure of height and width as specified by the user
        fig = plt.figure(figsize=[self.config_obj.plot_height, self.config_obj.plot_width])


def main():
    """
            Generates a sample, default, ROC diagram using the
            default and custom config files on sample data found in this directory.
            The location of the input data is defined in either the default or
            custom config file.
        """

    # Retrieve the contents of the custom config file to over-ride
    # or augment settings defined by the default config file.
    # with open("./custom_roc_diagram.yaml", 'r') as stream:
    config_file = util.read_config_from_command_line()
    with open(config_file, 'r') as stream:
        try:
            docs = yaml.load(stream, Loader=yaml.FullLoader)
        except yaml.YAMLError as exc:
            print(exc)

    try:
        # create a performance diagram
        ROCDiagram(docs)

    except ValueError as value_error:
        print(value_error)


if __name__ == "__main__":
    main()
