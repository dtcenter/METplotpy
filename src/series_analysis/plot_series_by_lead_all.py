import os
from netCDF4 import Dataset
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
from cartopy.util import add_cyclic_point
from matplotlib import cm

def generate_plot(input_nc_file_dir, input_nc_filename, variable_name, level, output_filename,
                background_on=False):
    '''

    :param input_file:
    :param input_nc_filename
    :param variable_name
    :param output_filename
    :return:
    '''

    #read in the netcdf file
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
            title = var_in_title + " from series by init for " + variable_name + " " + level
            plt.title(title)

            # output file will be saved as png
            if key == 'OBAR':
                output_png_file = output_filename + "_obar.png"
            else:
                output_png_file = output_filename + "_fbar.png"
            print("output filename: ", output_png_file)
            plt.savefig(output_png_file)

if __name__ == "__main__":
    input_dir = "/d1/METplus_Plotting_Data/series_by_lead_all_fhrs/series_F000"
    input_file = "series_F000_TMP_P850.nc"
    output_filename = '/d1/METplus_Plotting_Data/series_by_lead_all_fhrs/series_F000/series_by_lead'
    variable_name = 'TMP'
    level = 'P850'
    plot_background_map = True
    generate_plot(input_dir, input_file, variable_name, level, output_filename, plot_background_map )