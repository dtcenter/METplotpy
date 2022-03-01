# ============================*
 # ** Copyright UCAR (c) 2020
 # ** University Corporation for Atmospheric Research (UCAR)
 # ** National Center for Atmospheric Research (NCAR)
 # ** Research Applications Lab (RAL)
 # ** P.O.Box 3000, Boulder, Colorado, 80307-3000, USA
 # ** University of Illinois, Urbana-Champaign
 # ============================*
 
 
 
import matplotlib.pyplot as plt
import matplotlib.colors as colors
from matplotlib import MatplotlibDeprecationWarning
from pylab import *
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
import cartopy.crs as ccrs
from cartopy.util import add_cyclic_point
import numpy as np
import warnings
import metcalcpy.util.utils as utils

def create_cbl_plot(lons, lats, cblf, mhweight, month_str, output_plotname, do_averaging=True, lon_0_to_360=True):
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
         @params lon_0_to_360: True by default. If false, assumes longitude grid points span from
                                -180 to 180. If true, make the necessary conversion to -180 to 180 in
                                the longitude and reorder the corresponding CBLm numpy array.

        Returns:
             Generates an output file in pdf format, with name and location as specified in the
             output_plotname input argument.
    """
    # Ignore the MatplotlibDeprecationWarning.  draw() isn't being used and is
    # unaffected by the deprecation in Matplotlib 3.3.  This code was
    # developed using Matplotlib 3.3.1
    warnings.filterwarnings("ignore",category=MatplotlibDeprecationWarning)
    # To filter the cartopy mpl gridliner deprecation warning
    warnings.filterwarnings("ignore",category=UserWarning)

    # do averaging, by default
    if not do_averaging:
        mmstd = mhweight
        CBLm = cblf
    else:
        CBLm = np.mean(cblf, axis=0)
        mmstd = np.nanmean(mhweight,axis=0)


    mmstd, lonsm = add_cyclic_point(mmstd, lons)

    # center the plot at 0 degrees longitude
    lon_center = 0
    tran = ccrs.PlateCarree(central_longitude=lon_center)
    proj = tran
    fig = plt.figure(figsize=[10, 4])
    ax = fig.add_subplot(1, 1, 1, projection=proj)

    ax = plt.axes(projection=proj)
    contourf(lonsm, lats, mmstd[:, :], np.arange(0, 71, 10), cmap=plt.cm.Reds, extend='max')
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

    if lon_0_to_360:
        # Convert lon grid to -180 to 180 and reorder the CBLm values to
        # correspond to these changes.
        lons = utils.convert_lon_360_to_180(lons)
        CBLm_beg = CBLm[180:]
        CBLm_end = CBLm[0:180]
        CBLm = np.concatenate((CBLm_beg, CBLm_end))

    CBLm, lons = add_cyclic_point(CBLm, coord=lons)
    minlon = min(lons)
    maxlon = max(lons)
    ax.set_extent([minlon, maxlon, 0, 90], ccrs.PlateCarree())
    plt.plot(lons, CBLm, 'k', linewidth=1.0)
    fmt = 'pdf'
    full_output_plot = output_plotname + "." + fmt
    # plt.savefig("./CBL_" + str(month_str) + "." + fmt, format=fmt, dpi=400, bbox_inches='tight')
    plt.savefig(full_output_plot, format=fmt, dpi=400, bbox_inches='tight')
    plt.pause(1e-13)
    fmt2 = 'png'
    full_output_plot2 = output_plotname + "." + fmt2
    plt.savefig(full_output_plot2, format=fmt2, dpi=400, bbox_inches='tight')

    # plt.show()







