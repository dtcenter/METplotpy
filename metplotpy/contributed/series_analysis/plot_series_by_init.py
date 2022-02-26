# ============================*
 # ** Copyright UCAR (c) 2020
 # ** University Corporation for Atmospheric Research (UCAR)
 # ** National Center for Atmospheric Research (NCAR)
 # ** Research Applications Lab (RAL)
 # ** P.O.Box 3000, Boulder, Colorado, 80307-3000, USA
 # ============================*
 
 
 
"""
Generates static plots (png) from netcdf output from performing series analysis by init times.
"""

import os
import sys
import yaml
import errno
import warnings
import matplotlib.pyplot as plt
import matplotlib.cbook
from matplotlib import cm
import cartopy.crs as ccrs
from cartopy.util import add_cyclic_point
#pylint: disable=import-error
from netCDF4 import Dataset
sys.path.append("../..")
import metplotpy.plots.util as util
# ignore the MatplotlibFutureDeprecation warning which does not affect this code
# since changes must be made in Cartopy code
warnings.simplefilter(action='ignore', category=matplotlib.cbook.mplDeprecation)

class PlotSeriesByInit():
    def __init__(self, cfg:dict) -> None:
        self.config = cfg

    def create_plot(self) -> dict:
        '''
            Generates the plots (png) for each var-level-stat combination created
            by the series analysis by init.
            Reads the input netcdf file and gathers the lat, lon, FBAR and OBAR
            values into numpy arrays

        :param
        :return:
        :raises errno.EEXIST, FileNotFoundError

        '''

        # Retrieve the settings indicating the storm, variables, levels, etc of interest from the yaml config file,
        # series_init.yaml
        config = self.config
        input_nc_filename = config['input_nc_file']
        input_nc_file_dir = config['input_nc_file_dir']
        variable_name = config['variable_name']
        level = config['level']
        storm_number = config['storm_number']
        output_filename_base = config['output_filename_base']
        output_dir = config['output_dir']
        background_on_setting = config['background_on']

        if background_on_setting.upper() == 'TRUE':
            background_on = True
        else:
            background_on = False

        # create the output directory if it doesn't exist
        try:
            os.makedirs(output_dir)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

        try:
            input_nc_file_storm_dir = os.path.join(input_nc_file_dir, storm_number)
            input_nc_file = os.path.join(input_nc_file_storm_dir, input_nc_filename)
            file_handle = Dataset(input_nc_file, mode='r')
        except FileNotFoundError:
            print("File ", input_nc_file, " does not exist.")
        else:

            # Retrieve variables of interest
            lons = file_handle.variables['lon'][:]
            lats = file_handle.variables['lat'][:]
            fbar = file_handle.variables['series_cnt_FBAR'][:]
            obar = file_handle.variables['series_cnt_OBAR'][:]

            # close the file handle now that we are finished retrieving what we need
            file_handle.close()

            # Verify that these values are consistent with lat, lon values, etc.
            print("lat : ", lats)
            print("lon : ", lons)
            print("FBAR: ", fbar)
            print("OBAR: ", obar)

            # Use the reversed Spectral colormap to reflect temperatures.
            cmap = cm.get_cmap('Spectral_r')

            vars_dict = {'FBAR': fbar, 'OBAR': obar}
            for key, value in vars_dict.items():
                # generate a contour map of OBAR/FBAR values
                plt.figure(figsize=(13, 6.2))
                geo_ax = plt.axes(projection=ccrs.PlateCarree())

                # set number of contour levels to 65, higher number results in more smoothing.
                plt.contourf(lons, lats, value, 65, transform=ccrs.PlateCarree(), cmap=cmap)

                # Only plot the coastlines if the background map is requested
                if background_on:
                    geo_ax.coastlines()

                if key == 'OBAR':
                    var_in_title = "OBAR"
                    # Figure out the minimum and maximum values of the OBAR/FBAR
                    # temperature and use these values in the
                    # plt.Normalize() call.
                    minimum = obar.min()
                    maximum = obar.max()
                    # Allow the temperature values (OBAR, FBAR) and the longitude
                    # to cycle (encircle the globe)

                    # pylint: disable=unused-variable
                    obar_cyc, lon_cyc = add_cyclic_point(obar, coord=lons)
                else:
                    var_in_title = "FBAR"
                    # Figure out the minimum and maximum values of the OBAR/FBAR
                    # temperature and use these values in the
                    # plt.Normalize() call.
                    minimum = fbar.min()
                    maximum = fbar.max()
                    # Allow the temperature values (OBAR, FBAR) and the longitude
                    # to cycle (encircle the globe)
                    # pylint: disable=unused-variable
                    fbar_cyc, lon_cyc = add_cyclic_point(fbar, coord=lons)

                # Adding a legend from Stack Overflow.  Create your own mappable object
                # (scalar mappable) that can be passed to colorbar.  Normalize values
                # are the min and max values normalized to 0, 1 in the
                # solution, here we use the minimum and maximum values found in the FBAR/OBAR
                # array.

                scalar_mappable = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(minimum, maximum))
                # pylint: disable=protected-access
                scalar_mappable._A = []
                plt.colorbar(scalar_mappable, ax=geo_ax)
                title = var_in_title + " from series by init for " + variable_name + \
                        " " + level + " Storm " \
                        + storm_number
                plt.title(title)

                # output file will be saved as png
                if key == 'OBAR':

                    output_png_filename = output_filename_base + "_obar.png"
                    # output_png_file = output_dir + "/" + output_png_filename
                    output_png_file = os.path.join(output_dir, output_png_filename)


                else:

                    output_png_filename = output_filename_base + "_fbar.png"
                    output_png_file = os.path.join(output_dir, output_png_filename)

                print("output filename: ", output_png_file)
                plt.savefig(output_png_file)


def main():
    """
       Invoke create_plot() to generate png OBAR and FBAR plots for specified storm, level, variable of the
       METplus series analysis output.

    :return:
    """

    config_file = util.read_config_from_command_line()

    with open(config_file, 'r') as stream:
        try:
            config = yaml.load(stream, Loader=yaml.FullLoader)
        except yaml.YAMLError as exc:
            print(exc)

    # Invoke the function that generates the plot
    psbi = PlotSeriesByInit(config)
    psbi.create_plot()


if __name__ == "__main__":
    main()
