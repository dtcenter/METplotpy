# ============================*
# ** Copyright UCAR (c) 2025
# ** University Corporation for Atmospheric Research (UCAR)
# ** National Science Foundation National Center for Atmospheric Research (NSF NCAR)
# ** Research Applications Lab (RAL)
# ** P.O.Box 3000, Boulder, Colorado, 80307-3000, USA
# ============================*

"""
  Class name: plot_gradient.py

  Plotting the gradient for  a Model, Observation, and a Difference
  The three plots are displayed in one figure.
"""

import sys
import os
import yaml
from datetime import datetime
import matplotlib

matplotlib.use('agg')
import matplotlib.pyplot as plt
import matplotlib.colors as colors
from pylab import contourf
import cartopy.crs as ccrs
import numpy as np
import netCDF4 as nc
from metcalcpy.util import read_env_vars_in_config as readconfig
from metplotpy.plots import util


class PlotGradient():

    def __init__(self, config_file):

        # Retrieve the
        with open(config_file, 'r') as _:
            try:
                input_config_file = os.getenv("PLOTTING_YAML_CONFIG_NAME", config_file)
                settings = readconfig.parse_config(input_config_file)
            except yaml.YAMLError:
                sys.exit(1)

        now = datetime.now()
        log_dir = settings['log_directory']
        os.makedirs(log_dir, exist_ok=True)
        logname = "plot_log_" + str(datetime.timestamp(now)) + ".txt"
        log_filename = os.path.join(log_dir, logname)
        self.logger = util.get_common_logger(settings['log_level'], log_filename)
        self.logger.info("log output located at " + log_filename)

        self.output_filename = settings['output_filename']
        self.output_directory = settings['output_directory']
        os.makedirs(self.output_directory, exist_ok=True)

        # Read input file and access variables and attributes
        input_dir = settings['input_dir']
        input_filename = settings['input_filename']
        input_file = os.path.join(input_dir, input_filename)
        input_data = nc.Dataset(input_file)
        self.lat = input_data.variables['lat'][:]
        self.lon = input_data.variables['lon'][:]
        self.fcst_tec = input_data.variables['FCST_gradient_FULL'][:]
        self.obs_tec = input_data.variables['OBS_gradient_FULL'][:]
        self.diff = input_data.variables['DIFF_gradient_FULL'][:]

        # Figure settings/customizations
        self.figure_width = settings['figure_width']
        self.figure_height = settings['figure_height']
        if settings['annotation'] is None:
            self.annotation = ''
        else:
            self.annotation = settings['annotation']

        # Model plot settings
        self.model_colormap = settings['model_colormap']
        self.model_coastline_resolution = settings['model_coastline_resolution']
        self.model_coastline_color = settings['model_coastline_color']
        self.model_coastline_linewidth = settings['model_coastline_linewidth']
        self.model_gridline_color = settings['model_gridline_color']
        self.model_gridline_linestyle = settings['model_gridline_linestyle']
        self.model_gridline_draw_labels = settings['model_gridline_draw_labels']
        self.model_gridline_top_labels = settings['model_gridline_top_labels']
        self.model_gridline_right_labels = settings['model_gridline_right_labels']
        self.model_colorbar_shrink = settings['model_resize_colorbar_factor']
        self.model_plot_title = settings['model_plot_title']

        # Observation plot settings
        self.obs_colormap = settings['obs_colormap']
        self.obs_coastline_resolution = settings['obs_coastline_resolution']
        self.obs_coastline_color = settings['obs_coastline_color']
        self.obs_coastline_linewidth = settings['obs_coastline_linewidth']
        self.obs_gridline_color = settings['obs_gridline_color']
        self.obs_gridline_linestyle = settings['obs_gridline_linestyle']
        self.obs_gridline_draw_labels = settings['obs_gridline_draw_labels']
        self.obs_gridline_top_labels = settings['obs_gridline_top_labels']
        self.obs_gridline_right_labels = settings['obs_gridline_right_labels']
        self.obs_colorbar_shrink = settings['obs_resize_colorbar_factor']
        self.obs_plot_title = settings['obs_plot_title']

        # Difference plot settings
        self.diff_colormap = settings['diff_colormap']
        self.diff_coastline_resolution = settings['diff_coastline_resolution']
        self.diff_coastline_color = settings['diff_coastline_color']
        self.diff_coastline_linewidth = settings['diff_coastline_linewidth']
        self.diff_gridline_color = settings['diff_gridline_color']
        self.diff_gridline_linestyle = settings['diff_gridline_linestyle']
        self.diff_gridline_draw_labels = settings['diff_gridline_draw_labels']
        self.diff_gridline_top_labels = settings['diff_gridline_top_labels']
        self.diff_gridline_right_labels = settings['diff_gridline_right_labels']
        self.diff_colorbar_shrink = settings['diff_resize_colorbar_factor']
        self.diff_plot_title = settings['diff_plot_title']


        # Get Valid Time and Units to plot
        self.valid_time_original = getattr(input_data.variables['FCST_gradient_FULL'], 'valid_time')
        self.valid_time = self.valid_time_original.replace('_', ' ')
        self.var_units = getattr(input_data.variables['FCST_gradient_FULL'], 'units')

        # Close input file
        message = "Initialization complete"
        self.logger.info(message)
        input_data.close()


    def make_plot(self):
        """
        Generate the Model TEC Magnitude, Observation TEC Magnitude, and
        Difference plots

        Args:
            None

        Returns:
            None, saves a figure with three plots as a .png file

        """

        # Setup plot transform, projections, etc.
        self.logger.info("Setting up figure")
        transform = ccrs.Robinson()
        projection= ccrs.PlateCarree()
        fig = plt.figure(figsize=(self.figure_width, self.figure_width))

        #
        # MODEL plot
        #
        self.logger.info("Setting up MODEL plotting")
        ax1 = fig.add_subplot(2, 2, 1, projection=transform)
        contourf(self.lon, self.lat, self.fcst_tec, cmap=self.model_colormap, transform=projection, extend='max')
        ax1.coastlines(resolution=self.model_coastline_resolution, color=self.model_coastline_color,
                       linewidth=self.model_coastline_linewidth)
        gl = ax1.gridlines(draw_labels=self.model_gridline_draw_labels, color=self.model_gridline_color,
                           linestyle=self.model_gridline_linestyle)
        gl.top_labels = self.model_gridline_top_labels
        gl.right_labels = self.model_gridline_right_labels
        plt.colorbar(shrink=self.model_colorbar_shrink, label=self.var_units)
        plt.title(self.model_plot_title)

        #
        # OBS plot
        #
        self.logger.info("Setting up OBS plotting")
        ax1 = fig.add_subplot(2, 2, 2, projection=transform)
        contourf(self.lon, self.lat, self.obs_tec, cmap=self.obs_colormap, transform=ccrs.PlateCarree(), extend='max')
        ax1.coastlines(resolution=self.obs_coastline_resolution, color=self.obs_coastline_color)
        gl = ax1.gridlines(draw_labels=self.obs_gridline_draw_labels, color=self.obs_gridline_color,
                           linestyle=self.obs_gridline_linestyle)
        gl.top_labels = self.obs_gridline_top_labels
        gl.right_labels = self.obs_gridline_right_labels
        plt.colorbar(shrink=self.obs_colorbar_shrink, label=self.var_units)
        plt.title(self.obs_plot_title)

        # Add Valid time label in empty plot spot
        self.logger.info("Filling in the valid time in the empty plot space")
        ax1 = fig.add_subplot(2, 2, 3)
        ax1.axis('off')
        if len(self.annotation) > 0:
            ax1.annotate(self.annotation, (0.1, 0.5), xycoords='axes fraction', va='center')
        else:
            ax1.annotate('Valid Time:  ' + self.valid_time + ' UTC', (0.1, 0.5), xycoords='axes fraction', va='center')

        #
        # DIFF plot
        #

        self.logger.info("Setting up DIFF plotting")
        # First get the data range to center the colorbar on 0
        cbar_max = np.max([np.min(self.diff), np.max(self.diff)])
        cbar_min = -cbar_max
        norm = colors.CenteredNorm()

        ax1 = fig.add_subplot(2, 2, 4, projection=transform)
        contourf(self.lon, self.lat, self.diff, cmap=self.diff_colormap, transform=ccrs.PlateCarree(), extend='max',
                 vmin=cbar_min,
                 vmax=cbar_max, norm=norm)
        ax1.coastlines(resolution=self.diff_coastline_resolution, color=self.diff_coastline_color)
        gl = ax1.gridlines(draw_labels=self.diff_gridline_draw_labels, color=self.diff_gridline_color,
                           linestyle=self.diff_gridline_linestyle)
        gl.top_labels = self.diff_gridline_top_labels
        gl.right_labels = self.diff_gridline_right_labels
        plt.colorbar(shrink=self.diff_colorbar_shrink, label=self.var_units)
        plt.title(self.diff_plot_title)

        # Save the  final plot as a png file
        plt.tight_layout()
        plotname = self.output_filename + str(self.valid_time_original) + ".png"
        final_plot = os.path.join(self.output_directory, plotname)
        plt.savefig(final_plot)
        self.logger.info(f"Plotting complete, plot saved to  {final_plot}")

def main():
    """
       Get the configuration file and invoke appropriate methods
       to generate gradient plots.

       Args:
            None

       Returns:
           None: Generates three plots in one figure saved to output file specified
                     in the configuration file.

    """

config_file: str = util.read_config_from_command_line()
try:
    plot = PlotGradient(config_file)
    plot.make_plot()

except ValueError:
    sys.exit(1)

if __name__ == "__main__":
    main()
