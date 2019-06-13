import os
from netCDF4 import Dataset
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
from cartopy.util import add_cyclic_point
from cmocean import cm as cmo
from matplotlib import cm


def create_plot(input_nc_file_dir, input_nc_filename, variable_name, level, storm_number, output_filename,
                background_on=False):
    '''
        Reads the input netcdf file and gathers the lat, lon, FBAR and OBAR values into numpy arrays
    :param input_nc_file_dir The directory where the netcdf input file resides
    :param input_nc_file:  The name of the netcdf input file containing the variable of interest
    :param variable_name:   The name of the variable of interest, e.g. TEMP.
    :pararm level:          The level corresponding to the variable of interest, e.g. Z2, L1, P500, etc.
    :param storm_number    The storm number, used in the title of the plot.
    :param output_filename The "base" output filename to be used for FBAR and OBAR plots.
    :param backgroung_on:  Background map with coastlines are by default turned "off".
    :return:

    '''

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
            title = var_in_title + " from series by init for " + variable_name + " " + level + " Storm " \
                    + storm_number
            plt.title(title)

            # output file will be saved as png
            if key == 'OBAR':
                output_png_file = output_filename + "_obar.png"
            else:
                output_png_file = output_filename + "_fbar.png"
            print("output filename: ", output_png_file)
            plt.savefig(output_png_file)


if __name__ == "__main__":
    #
    # series by init
    #

    # The storm number of interest
    storm_number = 'ML1200972014'
    # The input directory where the netcdf files created by the series analysis (by initialization times) are saved
    nc_input_dir = \
        '/d1/METplus_Plotting_Data/series_by_init/20141214_00/' + storm_number

    # The name of the netccdf file of interest
    nc_input_filename = 'series_TMP_Z2.nc'
    variable_name = 'TMP'
    level = 'Z2'
    # The output file name (full path)
    obar_fbar_output = '/d1/METplus_Plotting_Data/series_by_init/20141214_00/' + storm_number + '/TMP_Z2'

    # By default, this is set to False, set to True if you want the coastlines plotted.
    include_background = True
    # Invoke the function that generates the plot
    create_plot(nc_input_dir, nc_input_filename, variable_name, level, storm_number, obar_fbar_output,
                include_background)
