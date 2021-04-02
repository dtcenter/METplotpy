
"""
This module/script generates static plots (png) from netcdf
output from performing a series by lead for all fhrs.  This
is the output from the METplus feature relative use case.
"""

import os, sys
import yaml
import errno
import warnings
from collections import namedtuple
import re
import matplotlib.pyplot as plt
from matplotlib import cm
import matplotlib.cbook
import cartopy.crs as ccrs
from cartopy.util import add_cyclic_point
#pylint: disable=import-error
sys.path.append("../..")
import metplotpy.plots.util as util

from netCDF4 import Dataset
# ignore the MatplotlibFutureDeprecation warning which does not affect this code
# since it was developed with matplotlib 3.3
warnings.simplefilter(action='ignore', category=matplotlib.cbook.mplDeprecation)

class PlotSeriesByLeadAll():
    def __init__(self, cfg):
        self.config = cfg

    # input_file, hour, variable_name, level_type, level, output_filename)
    def generate_plot(self, input_nc_filename, fhr, variable_name,
                      level_type, level, output_filename):
        '''


        :return:
        '''

        input_nc_file_dir = self.config['input_nc_file_dir']
        output_dir = self.config['output_dir']
        output_full_filename = os.path.join(output_dir, output_filename)
        background_on = self.config['background_on']

        # read in the netcdf file
        try:
            input_nc_file = os.path.join(input_nc_file_dir, input_nc_filename)
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

            # Uncomment to visually verify that these values are "reasonable" lat/lon values, etc.
            # print("lat : ", lats)
            # print("lon : ", lons)
            # print("FBAR: ", fbar)
            # print("OBAR: ", obar)

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
                    # Figure out the minimum and maximum values of the OBAR/FBAR temperature
                    # and use these values in the plt.Normalize() call.
                    minimum = obar.min()
                    maximum = obar.max()
                    # Allow the temperature values (OBAR, FBAR) and the longitude to cycle
                    # (encircle the globe)
                    # pylint: disable=unused-variable
                    obar_cyc, lon_cyc = add_cyclic_point(obar, coord=lons)
                else:
                    var_in_title = "FBAR"
                    # Figure out the minimum and maximum values of the OBAR/FBAR temperature
                    # and use these values in the plt.Normalize() call.
                    minimum = fbar.min()
                    maximum = fbar.max()
                    # Allow the temperature values (OBAR, FBAR) and the longitude to
                    # cycle (encircle the globe)
                    # pylint: disable=unused-variable
                    fbar_cyc, lon_cyc = add_cyclic_point(fbar, coord=lons)

                # Adding a legend from Stack Overflow.  Create your own mappable
                # object (scalar mappable) that can be passed to colorbar.
                # Normalize values are the min and max values normalized to
                # 0, 1 in the solution, here we use the minimum and maximum
                # values found in the FBAR/OBAR array.

                scalar_mappable = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(minimum, maximum))
                # pylint: disable=protected-access
                scalar_mappable._A = []
                plt.colorbar(scalar_mappable, ax=geo_ax)
                title = " series by init " + var_in_title + " for fhr " + fhr + " " + \
                        variable_name + " " + level_type + level
                plt.title(title)

                # output file will be saved as png
                if key == 'OBAR':
                    output_png_file = output_filename + "_obar.png"
                else:
                    output_png_file = output_filename + "_fbar.png"
                print("output filename: ", output_png_file)
                plt.savefig(output_png_file)

    def get_info(self, base_dir, output_base_dir):
        '''From the base_dir, where the series_F### subdirectories reside (and contain the
        netcdf output from the
           feature relative use case):
           1) get all the subdirectories
           2) from each subdirectory, get all the netcdf files
           3) from the netcdf file, extract the fhr, variable name, and level information
           4) Create the output filename, variable name, level, forecast hour to be used
           to create the title for the plot.

           :param base_dir  The base directory containing the series_F### subdirectories,
                            which in turn contain the netcdf
                            files created by running the METplus use cases
           :param output_base_dir The base directory where the plots are stored


           :return: file_info_list   A list of named tuples that contain the file info
                                     needed to generate the title of
                                     each plot and the output filename of each plot.
        '''

        # Get a list of all the subdirectories under the base_dir and create a list of named
        # tuples that contain the forecast hour, variable (TMP or HGT), level type
        # (ie P or Z) and level.
        FileInfo = namedtuple('FileInfo', 'fhr, variable_name,level_type, level, output_filename')

        # filename looks like the following: series_[fhr]_to_[fhr]_[variable]_[level].nc
        file_info_list = []

        # pylint: disable=unused-variable
        for root, dirs, files in os.walk(base_dir):
            for file in files:
                # match = re.search('series_F([0-9]{3})_(HGT|TMP)_(P|Z)([0-9]{3}).nc', file)
                match = re.search('series_F([0-9]{1,3})_to_F([0-9]{1,3})_(HGT|TMP)_(P|Z)([0-9]{1,3}).nc', file)
                if match:
                    fhr = match.group(1)
                    variable_name = match.group(3)
                    level_type = match.group(4)
                    level = match.group(5)
                    # Create the output filename (full path) but omit the extension
                    output_filename = 'series_F' + fhr + "_to_F" + fhr + "_" + variable_name + '_' + level_type + level
                    output_file_no_ext = os.path.join(output_base_dir, output_filename)
                    cur_file_info = FileInfo(fhr, variable_name, level_type, level, output_file_no_ext)
                    file_info_list.append(cur_file_info)

        return file_info_list


def main():
    """Generate plots for all the netcdf files found in the
    /d1/METplus_Plotting_Data/series_by_lead_all_fhrs:
    series_F000/, series_F006/, series_F012, and series_F018
    """

    config_file = util.read_config_from_command_line()

    with open(config_file, 'r') as stream:
        try:
            config = yaml.load(stream, Loader=yaml.FullLoader)
        except yaml.YAMLError as exc:
            print(exc)

    # Initialize a PlotSeriesByLeadAll instance
    psl = PlotSeriesByLeadAll(config)
    input_nc_file_dir = psl.config['input_nc_file_dir']
    output_dir = psl.config['output_dir']

    plot_on_setting = psl.config['background_on']
    if plot_on_setting.upper() == 'TRUE':
        plot_background_map = True
    else:
        plot_background_map = False

    # create the directory if it doesn't exist (equivalent of mkdir -p)
    try:
        os.makedirs(output_dir)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(output_dir):
            # directory already exists, proceed
            pass

    # Invoke the function that generates the plot
    file_info_list = psl.get_info(input_nc_file_dir, output_dir)

    for file_info in file_info_list:
        hour = file_info.fhr
        fhr = 'series_F' + hour
        input_dir = os.path.join(input_nc_file_dir, fhr)
        level_type = file_info.level_type
        level = file_info.level
        variable_name = file_info.variable_name
        input_filename = 'series_F' + hour + '_to_F' + hour + '_' + variable_name + '_' + level_type + \
                         level + '.nc'
        input_file = os.path.join(input_dir, input_filename)
        output_filename = file_info.output_filename

        psl.generate_plot(input_file, hour, variable_name, level_type, level, output_filename)


if __name__ == "__main__":
    main()
