# ============================*
 # ** Copyright UCAR (c) 2020
 # ** University Corporation for Atmospheric Research (UCAR)
 # ** National Center for Atmospheric Research (NCAR)
 # ** Research Applications Lab (RAL)
 # ** P.O.Box 3000, Boulder, Colorado, 80307-3000, USA
 # ============================*
 
 
 
"""
Creates static graphics plots (png) reading in the netcdf files that are the output from running the
grid-to-grid use case with the anom.conf file.
"""
import os, sys
import re
import errno, warnings
import yaml
from matplotlib import cm
import matplotlib.cbook
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
from cartopy.util import add_cyclic_point
#pylint: disable=import-error
from netCDF4 import Dataset
sys.path.append("../..")
import metplotpy.plots.util as util
# ignore the MatplotlibFutureDeprecation warning which does not affect this code
# since changes must be made in Cartopy code
warnings.simplefilter(action='ignore', category=matplotlib.cbook.mplDeprecation)

class PlotGridToGrid():
    def __init__(self,cfg):
        self.config = cfg

    def create_plots(self,input_dir, variable_name, nc_var_name, title, nc_flag_type, output_dir,
                     background_on=False):
        """
        Creates plots of output from grid_to_grid METplus wrapper use case,
        where the nc_pair_flags raw and diff are
        set to TRUE to generate the output for the raw variables for fcst and obs,
        and their corresponding difference.

        :param input_dir:
        :param variable_name: The variable of interest: tmp, ugrd, hgt, etc
        :param nc_var_name: The variable name as described in the netcdf file
        :param title:  The title for this plot
        :param nc_flag_type:  Corresponds *somewhat* to the nc_pairs_flag: FCST&OBS correspond to raw,
                              DIFF corresponds to diff
        :param output_dir:  The directory where the png files will be saved.
        :param background_on: default is False to turn off plotting coastlines/underlying map
        :return:
        """

        # Set the type to all upper case, and variable_names to lower case

        # Get all the netcdf output files in the input directory
        all_nc_filenames = []

        # pylint: disable=unused-variable
        for root, dirs, files in os.walk(input_dir):
            for file in files:
                match = re.match(r'(.*).nc', file)
                if match:
                    all_nc_filenames.append(file)

        # For each netcdf file, open the file, and
        # retrieve the fields from the netcdf file
        for nc_file in all_nc_filenames:
            try:
                file_handle = Dataset(os.path.join(input_dir, nc_file), mode='r')
            except FileNotFoundError:
                print("File ", nc_file, " does not exist.")
            else:
                # Retrieve variables of interest
                lons = file_handle.variables['lon'][:]
                lats = file_handle.variables['lat'][:]
                variable = file_handle.variables[nc_var_name][:]

                # Finished acquiring variables, no longer need the file_handle.
                file_handle.close()

            # print("netcdf file: ", nc_file)
            # print(nc_var_name, ': ', variable)
            # print('lon: ', lons)
            # print('lat: ', lats)
            #
            # print("======================\n\n")

            # Use the reversed Spectral colormap to reflect temperatures.
            cmap = cm.get_cmap('Spectral_r')

            # generate a contour map of the variable of interest
            plt.figure(figsize=(13, 6.2))
            geo_ax = plt.axes(projection=ccrs.PlateCarree())

            # Only plot the coastlines if the background map is requested
            if background_on:
                geo_ax.coastlines()

            # Figure out the minimum and maximum values of the OBAR/FBAR temperature
            # and use these values in the
            # plt.Normalize() call.
            minimum = variable.min()
            maximum = variable.max()
            # print(variable)

            #  Allow the variable and the longitude to cycle (encircle the globe)
            # pylint: disable=unused-variable
            variable_cyc, lon_cyc = add_cyclic_point(variable, coord=lons)
            # print("variable cyc: ", variable_cyc)
            # print("lon cyc: ", lon_cyc)

            # set number of contour levels to 65, higher number results in more smoothing.
            plt.contourf(lons, lats, variable, 65, transform=ccrs.PlateCarree(), cmap=cmap)

            # Adding a legend from Stack Overflow.  Create your own mappable object
            # (scalar mappable) that can be passed to colorbar.  Normalize values
            # are the min and max values normalized to 0, 1 in the
            # solution, here we use the minimum and maximum values found in the FBAR/OBAR array.

            scalar_mappable = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(minimum, maximum))
            # pylint: disable=protected-access
            scalar_mappable._A = []
            plt.colorbar(scalar_mappable, ax=geo_ax)
            plt.title(title)

            # output file will be saved as png
            output_png_file = variable_name + "_" + nc_flag_type + "_" + \
                              os.path.splitext(nc_file)[0] + ".png"
            plt.savefig(os.path.join(output_dir, output_png_file))


def main():
    """
    Set up the input variables needed to generate the plots by parsing the yaml config file, then invoke
    the plotting
    :return:
    """
    config_file = util.read_config_from_command_line()

    with open(config_file, 'r') as stream:
        try:
            config = yaml.load(stream, Loader=yaml.FullLoader)
        except yaml.YAMLError as exc:
            print(exc)

    pgg = PlotGridToGrid(config)



    # generate the plots of all the raw fields and diffs for the grid_to_grid use
    # case results generated by running
    # the anom.conf file.

    # The directory where the grid stat netcdf output files are located.
    input_dir = pgg.config['input_dir']

    # The directory where you wish to save the plots
    output_dir = pgg.config['output_dir']

    # create the directory if it doesn't exist (equivalent of mkdir -p)
    try:
        os.makedirs(output_dir)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(output_dir):
            pass

    # Indicate the fcst and obs raw fields of interest and the corresponding diff field
    # e.g. nc_fcst_var = FCST_TMP_P850_FULL
    #      nc_obs_var = OBS_TMP_P850_FULL
    #      nc_diff_var = DIFF_TMP_P850_FULL
    #      which are obtained by performing an 'ncdump' on the netcdf file and
    #      and assigning the variable names exactly as they are displayed in the ncdump output.
    # The 'var' is set to the variable name ie. TMP, UGRD, VGRD, HGT, etc...
    # and is used as a prefix to the output file
    # name to differentiate it from the plots of other variables.
    var = 'TMP'
    nc_fcst_var = pgg.config['nc_fcst_var']
    nc_fcst_title = pgg.config['nc_fcst_title']
    nc_obs_var = pgg.config['nc_obs_var']
    nc_obs_title = pgg.config['nc_obs_title']
    nc_diff_var = pgg.config['nc_diff_var']
    nc_diff_title = pgg.config['nc_diff_title']

    # set to True if you want to draw the coastlines on the plot
    background_on = True

    # nc_flag_type corresponds to the nc_flag in the MET grid-stat config file:
    # ie  FCST or OBS corresponds to raw=TRUE,
    # and DIFF corresponds to diff=TRUE
    nc_flag_type = "FCST"
    pgg.create_plots(input_dir, var, nc_fcst_var, nc_fcst_title, nc_flag_type,
                 output_dir, background_on)
    nc_flag_type = "OBS"
    pgg.create_plots(input_dir, var, nc_obs_var, nc_obs_title, nc_flag_type,
                     output_dir, background_on)
    nc_flag_type = "DIFF"
    pgg.create_plots(input_dir, var, nc_diff_var, nc_diff_title, nc_flag_type,
                 output_dir, background_on)


if __name__ == "__main__":

    main()
