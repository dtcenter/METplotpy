import matplotlib.pyplot as plt
import matplotlib.colors as colors
from pylab import *
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
import cartopy.crs as ccrs
import numpy as np
from metcalcpy.util.utils import convert_coords

def create_cbl_plot(lons, lats, mean_cbl, mmstd, month_str, output_plotname):
    """
        Create the map plot of the mean CBL values

        Args:
         @params lons: a numpy array of the longitude values under consideration
         @params lats: a numpy array of the latitude values under consideration
         @params mmstd:  a numpy array of the mean weight heights
         @params mean_cbl: a numpy array of the mean CBL values that correspond to the lons
         @params month_str:  indicates the months comprising this plot
         @params output_plotname: The full path and filename of the output plot file

        Returns:
             Generates an output file in pdf format, with name and location as specified in the
             output_plotname input argument.
    """

    # center the plot at 0 degrees longitude
    lon_center = 0
    tran = ccrs.PlateCarree(central_longitude=lon_center)
    proj = tran
    fig = plt.figure(figsize=[10, 4])
    ax = fig.add_subplot(1, 1, 1, projection=proj)

    ax = plt.axes(projection=proj)
    contourf(lons, lats, mmstd[:, :], np.arange(0, 71, 10), cmap=plt.cm.Reds, extend='max')
    ax.coastlines(resolution='50m', color='gray', linewidth=1.25)
    gl = ax.gridlines(crs=proj, draw_labels=True)
    ax.set_global()

    gl.xlabels_top = False
    gl.ylabels_right = True
    gl.xformatter = LONGITUDE_FORMATTER
    gl.yformatter = LATITUDE_FORMATTER

    # to place the title at top, y=1, to set it at bottom, y=0
    plt.title('' + str(month_str) + ' Mean High-Pass Z500 STD', y=1)
    # set orientation='vertical' if you want this along the x2 axis
    plt.colorbar(orientation='horizontal', fraction=0.086, pad=0.1)

    # Adjust the lons, extent for lons in Cartopy is from -180 to 180, but
    # lons in data are [0,360], but we need [-180,180] for the plot
    # calculate the new lon range using formula ((lons + 180.0)%360.0) - 180.0
    # new_lons = np.mod(lons + 180.0, 360.0) - 180.0
    new_lons = convert_coords(lons)
    minlon = min(new_lons)
    maxlon = max(new_lons)
    ax.set_extent([minlon, maxlon, 0, 90], ccrs.PlateCarree())
    plt.plot(new_lons, mean_cbl, 'k', linewidth=1.0)
    fmt = 'pdf'
    full_output_plot = output_plotname + "." + fmt
    # plt.savefig("./CBL_" + str(month_str) + "." + fmt, format=fmt, dpi=400, bbox_inches='tight')
    plt.savefig(full_output_plot, format=fmt, dpi=400, bbox_inches='tight')

    plt.show()
