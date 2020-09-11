import matplotlib.pyplot as plt
import matplotlib.colors as colors
from pylab import *
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
import cartopy.crs as ccrs
import netCDF4 as netcdf
import numpy as np
import warnings
import metcalcpy.util.utils as utils

def create_cbl_plot(lons, lats, cblf, mhweight, month_str, output_plotname, do_averaging=True):
    """
        Create the map plot of the mean CBL values

        Args:
         @params lons: a numpy array of the longitude values under consideration
         @params lats: a numpy array of the latitude values under consideration
         @params mhweight:  a numpy array of the weighted max high-pass
         @params cblf: a numpy array of the CBLf values that correspond to the lons
         @params month_str:  indicates the months comprising this plot
         @params output_plotname: The full path and filename of the output plot file
         @params do_averaging: calculate the averages for cblf and mwhgt and plot these values

        Returns:
             Generates an output file in pdf format, with name and location as specified in the
             output_plotname input argument.
    """
    # Ignore the MatplotlibDeprecationWarning.  draw() isn't being used and is
    # unaffected by the deprecation in Matplotlib 3.3.  This code was
    # developed using Matplotlib 3.3.1
    warnings.filterwarnings("ignore",category=DeprecationWarning)

    # do averaging, by default
    if not do_averaging:
        mmstd = mhweight
        CBLm = cblf
    else:
        CBLm = np.mean(cblf, axis=0)
        mmstd = np.nanmean(mhweight,axis=0)



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
    # lons in data are [0,360]. We need [-180,180] for the plot
    # calculate the new lon range using formula ((lons + 180.0)%360.0) - 180.0
    # new_lons = np.mod(lons + 180.0, 360.0) - 180.0
    # and we also need to reorder the CBLm array to align with the
    # new lon grid points.
    new_lons = utils.convert_lon_360_to_180(lons)
    CBLm_beg = CBLm[180:]
    CBLm_end = CBLm[0:180]
    CBLm_reordered = np.concatenate((CBLm_beg, CBLm_end))
    minlon = min(new_lons)
    maxlon = max(new_lons)
    ax.set_extent([minlon, maxlon, 0, 90], ccrs.PlateCarree())
    plt.plot(new_lons, CBLm_reordered, 'k', linewidth=1.0)
    fmt = 'pdf'
    full_output_plot = output_plotname + "." + fmt
    # plt.savefig("./CBL_" + str(month_str) + "." + fmt, format=fmt, dpi=400, bbox_inches='tight')
    plt.savefig(full_output_plot, format=fmt, dpi=400, bbox_inches='tight')
    fmt2 = 'png'
    full_output_plot2 = output_plotname + "." + fmt2
    plt.savefig(full_output_plot2, format=fmt2, dpi=400, bbox_inches='tight')

    # plt.show()







