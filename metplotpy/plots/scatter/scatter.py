# ============================*
# ** Copyright UCAR (c) 2024
# ** University Corporation for Atmospheric Research (UCAR)
# ** National Science Foundation National Center for Atmospheric Research (NSF NCAR)
# ** Research Applications Lab (RAL)
# ** P.O.Box 3000, Boulder, Colorado, 80307-3000, USA
# ============================*

"""
Class Name: Scatter
 """
__author__ = 'Minna Win'

import os
from datetime import datetime
import re
import matplotlib.pyplot as plt
import yaml
import pandas as pd
from metplotpy.plots.base_plot import BasePlot
import metcalcpy.util.utils as calc_util
from metplotpy.plots.scatter.scatter_config import ScatterConfig
from metplotpy.plots import util
from metplotpy.plots import constants

class Scatter(BasePlot):
    """
       Generate a scatter plot using Matplotlib and MPR linetyp output from the MET point-stat tool.

       PRE-CONDITION:  The MET .stat output data MUST be reformatted for the scatter plot, where all column headers
                       are present AND there are additional columns for stat_name, stat_value, stat_ncl, stat_ncu,
                       stat_bcu, and stat_bcl.


    """

    defaults_name = 'scatter_defaults.yaml'

    def __init__(self, parameters: dict) -> None:
        """
           Create a scatter plot from data where all columns are labelled.
           The marker color is based on the value, where the colors are determined by the
           colormap specified in the configuration file.  Requires a configuration file to be used
           in conjunction with the default configuration file.

           Args:
               @param parameters: a dictionary representation of the settings in the YAML configuration file
           Returns:
               None

        """

        super().__init__(parameters, self.defaults_name)

        # instantiate a ScatterConfig object that contains all the settings
        self.config_obj = ScatterConfig(self.parameters)

        # use the logger set up in the METplotpy util module
        self.logger = self.config_obj.logger

        # create a ScatterConfig object that contains all the settings in the YAML config file.
        self.config_obj = ScatterConfig(self.parameters)

    def create_figure(self, parms) -> None:
        """ Generate the scatter plot

           Args:
                 @param parms: The dictionary representation of the settings and associated values in the
                               YAML config file
           Returns: None
                Generates a scatter plot and saves it.
        """
        self.logger.info(f"Creating the scatter plot figure: {datetime.now()}")

        # Read input data
        start_read = datetime.now()
        self.logger.info("Reading input data")
        input_datafile = self.config_obj.stat_input
        df = pd.read_csv(input_datafile, sep="\t")
        total_read = datetime.now() - start_read
        self.logger.info(f"Reading input data completed in {total_read} seconds")

        # Filter data by fixed_vars_vals_input setting
        self.logger.info("Begin filtering data by the fixed_vars_vals_input setting")
        num_orig_rows = df.shape[0]
        fixed_var_dict = parms['fixed_vars_vals_input']
        filtered = util.filter_by_fixed_vars(df, fixed_var_dict)
        num_filtered_by_fixed_vars = filtered.shape[0]
        self.logger.info(f"Filtering by fixed vars reduces {num_orig_rows} rows to {num_filtered_by_fixed_vars} rows")

        # Filter by fcst variable of interest
        fcst_var_value = str(self.config_obj.fcst_var)
        self.logger.info(f"Begin filtering by the fcst var of interest: {fcst_var_value}")
        filtered = filtered.loc[filtered['fcst_var'] == fcst_var_value]
        num_final_filtered = filtered.shape[0]
        self.logger.info(f"Further filtering by fcst variable reduces number of rows from {num_filtered_by_fixed_vars} to {num_final_filtered}")

        x_column_name:str = str(self.config_obj.var_val_x_axis)
        y_column_name:str = str(self.config_obj.var_val_y_axis)
        x_values = filtered[x_column_name].tolist()
        y_values = filtered[y_column_name].tolist()

        # Get z-values
        z_var_name = str(self.config_obj.variable_val_by_color)

        z_values_df = filtered.loc[filtered['fcst_var'] == fcst_var_value]
        column_to_color_by_value = self.config_obj.variable_val_by_color
        z_values = z_values_df[column_to_color_by_value].tolist()

        # Generate the scatter plot based on plot settings defined in the YAML config file
        cmap = self.config_obj.colormap
        marker_size = self.config_obj.marker_size
        plt.scatter(x_values, y_values, s=marker_size, c=z_values, cmap=cmap, label=column_to_color_by_value)


        # Add the title, x-label, y-label, and legend
        x_label = self.config_obj.xaxis
        plt.xlabel(x_label)
        y_label = self.config_obj.yaxis
        plt.ylabel(y_label)
        title = self.config_obj.title
        plt.title(title)

        color_bar = plt.colorbar()
        color_bar.set_label(column_to_color_by_value)
        plt.show()

        # Save the plot
        user_legend = self.config_obj.user_legend
        plt.savefig("./scatter_plot.png")






def main(config_filename=None):
    """
       Read in the YAML configuration file and create a scatter object.

       Args:


       Returns: None
    """

    if not config_filename:
        config_file = util.read_config_from_command_line()
    else:
        config_file = config_filename
    with open(config_file, 'r') as stream:
        try:
            docs = yaml.load(stream, Loader=yaml.FullLoader)
        except yaml.YAMLError as exc:
            print(exc)

    try:
        plot = Scatter(docs)
        plot.create_figure(docs)
        plot.logger.info(f"Finished generating scatter plot: {datetime.now()}")
    except ValueError as ve:
        print(ve)

if __name__ == "__main__":
    main()

