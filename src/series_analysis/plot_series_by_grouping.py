import os
from netCDF4 import Dataset
import re
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
from cartopy.util import add_cyclic_point
from matplotlib import cm
import errno


def create_plot(input_nc_file_dir, output_dir, background_on):
    '''

    :param input_dir:   The input directory where the netcdf files are located.
    :param output_dir:  The output directory where the png files will be saved
    :param background_on: Boolean value to indicate whether to draw coastlines on the plot.
    :return:
    '''
    # Get the netcdf files in each subdirectory, sorted by grouping name so that
    # Day1 preceeds Day2, and Day2 preceeds Day3, etc.
    nc_files = get_nc_files(input_nc_file_dir)
    # print(nc_files)

    # For each nc_file, read in the necessary values from the netcdf file
    for nc_file in nc_files:
        print("current nc file: ", nc_file)
        match = re.match(r'.*/(.*).nc', nc_file)
        if match:
            filename_only = match.group(1)
        else:
            raise ValueError("The netcdf filename doesn't match the expected format.")

        # Create the output directory if it doesn't already exist
        # create the output directory if it doesn't exist (equivalent of mkdir -p)
        try:
            os.makedirs(output_dir)
        except OSError as exc:
            if exc.errno == errno.EEXIST and os.path.isdir(output_dir):
                pass
        output_filename = os.path.join(output_dir, filename_only)

        # extract the variable_name and level from the output_filename
        var_level_match = re.match(r'series_F[0-9]{3}_to_F[0-9]{3}_([A-Z]{3})_(P|Z)([0-9]{1,3}).*', filename_only)
        if var_level_match:
            variable_name = var_level_match.group(1)
            level_type = var_level_match.group(2)
            level_name = var_level_match.group(3)
            level = level_type + level_name
        else:
            raise ValueError("The variable and level couldn't be extracted from the netcdf filename.")

        try:
            input_nc_file = os.path.join(input_nc_file_dir, nc_file)
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
            print("===============\n\n")

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
                # Figure out the minimum and maximum values of the OBAR/FBAR temperature and use these values in the
                # plt.Normalize() call.
                minimum = obar.min()
                maximum = obar.max()
                # Allow the temperature values (OBAR, FBAR) and the longitude to cycle (encircle the globe)
                obar_cyc, lon_cyc = add_cyclic_point(obar, coord=lons)
            else:
                var_in_title = "FBAR"
                # Figure out the minimum and maximum values of the OBAR/FBAR temperature and use these values in the
                # plt.Normalize() call.
                minimum = fbar.min()
                maximum = fbar.max()
                # Allow the temperature values (OBAR, FBAR) and the longitude to cycle (encircle the globe)
                fbar_cyc, lon_cyc = add_cyclic_point(fbar, coord=lons)

            # Adding a legend from Stack Overflow.  Create your own mappable object (scalar mappable) that can be
            # passed to colorbar.  Normalize values are the min and max values normalized to 0, 1 in the
            # solution, here we use the minimum and maximum values found in the FBAR/OBAR array.

            sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(minimum, maximum))
            sm._A = []
            plt.colorbar(sm, ax=geo_ax)
            title = var_in_title + " from series by init for " + variable_name + " " + level
            plt.title(title)

            # output file will be saved as png
            if key == 'OBAR':
                output_png_file = output_filename + "_obar.png"
            else:
                output_png_file = output_filename + "_fbar.png"
            print("output filename: ", output_png_file)
            plt.savefig(output_png_file)


def get_nc_files(input_dir_base):
    '''
        Generate a sorted list (by ascending alphanumeric name) of the netcdf files that will be read in to be
        used for generating plots.
        :param input_dir_base: the base directory where all the input netcdf files are located
        :return: sorted_nc_files:  A sorted list of the full filepath of the netcdf files to be used for plotting
    '''
    nc_files = []
    for root, dirs, files in os.walk(input_dir_base):
        for file in files:
            nc_files.append(os.path.join(root, file))

    # sort files by full path in ascending order so Day1 preceeds Day2, and
    # Day3 preceeds Day4...
    sorted_nc_files = sorted(nc_files)
    return sorted_nc_files


if __name__ == "__main__":
    input_dir = '/d1/METplus_Plotting_Data/series_by_lead_grouping'
    output_dir = '/d1/METplus_Plotting_Data/series_by_lead_grouping/plots'
    background_on = True
    create_plot(input_dir, output_dir, background_on)
