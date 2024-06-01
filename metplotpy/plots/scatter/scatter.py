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
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.font_manager import FontProperties
import yaml
import pandas as pd
from metplotpy.plots.base_plot import BasePlot
from metplotpy.plots.scatter.scatter_config import ScatterConfig
from metplotpy.plots import util

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
        start = datetime.now()
        self.logger.info("Reading input data")
        input_datafile = self.config_obj.stat_input
        df = pd.read_csv(input_datafile, sep="\t")
        total_read = datetime.now() - start
        self.logger.info(f"Reading input data completed in {total_read} seconds")

        # Filter data by fixed_vars_vals_input setting
        self.logger.info("Begin filtering data by the fixed_vars_vals_input setting")
        num_orig_rows = df.shape[0]
        fixed_var_dict = parms['fixed_vars_vals_input']
        filtered = util.filter_by_fixed_vars(df, fixed_var_dict)
        num_filtered_by_fixed_vars = filtered.shape[0]
        self.logger.debug(f"Filtering by fixed vars reduces {num_orig_rows} rows to {num_filtered_by_fixed_vars} rows")

        # Filter by fcst variable of interest
        fcst_var_value = str(self.config_obj.fcst_var)
        self.logger.info(f"Begin filtering by the fcst var of interest: {fcst_var_value}")
        filtered = filtered.loc[filtered['fcst_var'] == fcst_var_value]
        num_final_filtered = filtered.shape[0]
        self.logger.debug(f"Further filtering by fcst variable reduces number of rows from {num_filtered_by_fixed_vars} to {num_final_filtered}")

        x_column_name:str = str(self.config_obj.var_val_x_axis)
        y_column_name:str = str(self.config_obj.var_val_y_axis)
        x_values = filtered[x_column_name].tolist()
        y_values = filtered[y_column_name].tolist()

        # Get z-values (the value will dictate the color of the points)
        z_values_df:pd.DataFrame = filtered.loc[filtered['fcst_var'] == fcst_var_value]
        column_to_color_by_value = self.config_obj.variable_val_by_color
        z_values:list = z_values_df[column_to_color_by_value].tolist()

        # Save the x,y, and z-values to a file
        if self.config_obj.dump_points:
            try:
                self.logger.info(f"Create the {self.config_obj.points_path} directory for plot_points.txt file")
                os.makedirs(self.config_obj.points_path, exist_ok=True)
            except (FileExistsError, OSError):
                # ignore error if dir already exists
                pass

            points_file = os.path.join(self.config_obj.points_path, 'plot_points.txt')
            x_header = 'x=' + self.config_obj.var_val_x_axis
            y_header = 'y=' + self.config_obj.var_val_y_axis
            z_header = 'z=' + self.config_obj.variable_val_by_color
            points_df = pd.DataFrame({x_header:x_values, y_header:y_values, z_header:z_values})
            points_df.to_csv(points_file, sep="\t", index=False, na_rep='NA')

        # Generate the scatter plot based on plot settings defined in the YAML config file
        colormap = self.config_obj.marker_color
        self.logger.debug(
            f"Using the '{colormap}' colormap to color scatter points by {self.config_obj.variable_val_by_color} value")
        marker_size = self.config_obj.marker_size
        plt.scatter(x_values, y_values, s=marker_size, c=z_values, cmap=colormap, label=column_to_color_by_value)

        # Add the title, x-label, y-label, and legend
        x_label = self.config_obj.xaxis
        plt.xlabel(x_label)
        y_label = self.config_obj.yaxis
        plt.ylabel(y_label)
        title = self.config_obj.title
        plt.title(title)

        color_bar = plt.colorbar()

        # Add the legend label if requested
        if self.config_obj.show_legend:
           color_bar.set_label(self.config_obj.user_legend)

        # Turn on grid lines if requested,
        # make the grid lines as faint as possible to avoid
        # interfering with the scatter points and trendline/regression line
        if self.config_obj.grid_on:
            plt.grid(visible=True, which='major', axis='both', linestyle='dotted', linewidth=.4)

        # Add the trendline (regression line) if it was requested, using a
        # Least-squares fit.
        if self.config_obj.show_trendline:
            x_array = np.array(x_values)
            y_array = np.array(y_values)
            z_trend = np.polyfit(x_array, y_array, 1)
            poly = np.poly1d(z_trend)

            plt.plot(x_array, poly(x_array), color=self.config_obj.trendline_color, linewidth=self.config_obj.trendline_width,
                     linestyle=self.config_obj.trendline_style)

            # Start the x-axis from y=0
            if self.config_obj.start_from_zero:
               # retrieve the current Matplotlib Axes to set the xlim
               ax = plt.gca()
               ax.set_xlim(xmin=0)

        # Add caption, if there is any text
        if self.config_obj.add_caption:
            self.logger.debug(f"Caption settings: caption_align={self.config_obj.caption_align}, "
                             f"caption_offset={self.config_obj.caption_offset}, "
                             f"font size = {self.config_obj.caption_size}")
            self.logger.info(
                f"Adding caption text '{self.config_obj.plot_caption}'")
            fontobj = FontProperties()
            font = fontobj.copy()
            font.set_size(self.config_obj.caption_size)
            style = self.config_obj.caption_weight[0]
            wt = self.config_obj.caption_weight[1]
            font.set_style(style)
            font.set_weight(wt)
            plt.figtext(self.config_obj.caption_align, self.config_obj.caption_offset, self.config_obj.plot_caption,
                    fontproperties=font, color=self.config_obj.caption_color)

        # Save the plot
        plot_filename = self.config_obj.plot_filename
        self.logger.info(f"Saving scatter plot as {plot_filename}")
        plt.savefig(plot_filename)
        time_to_plot = datetime.now() - start
        self.logger.info(f"Total time for generating the scatter plot: {time_to_plot} seconds")



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

