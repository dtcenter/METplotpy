import matplotlib
#matplotlib.use('agg')
import matplotlib.pyplot as plt
import matplotlib.colors as colors
from pylab import *
import cmocean
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
import cartopy.crs as ccrs
from cartopy.util import add_cyclic_point
import numpy as np
import sys
sys.path.insert(0, "/glade/u/home/kalb/UIUC/METcalcpy/")
import metcalcpy.util.utils as util

def plot_elbow(K,d,mi,line,curve,plot_title,output_plotname):

    #lw = 2
    #rc('axes',linewidth=1.5)

    plt.plot(K[int(mi)],d[mi]*-1,'*k')
    plt.plot(K, np.array(curve), 'kx-')
    plt.plot(K, line, 'r')
    plt.plot(K, d*-1, 'b')
    plt.xlabel('k')
    plt.ylabel('Sum_of_squared_distances')
    plt.title(plot_title)

    fmt = 'png'
    full_output_plot = output_plotname + "." + fmt
    plt.savefig(full_output_plot,format=fmt,dpi=400, bbox_inches='tight')


def plot_K_means(inputi,wrnum,lon,lat,perc,output_plotname):

    lon,lonsort = util.convert_lons_indices(lon,-180,360)

    ### Plot the clusters
    middleIndex = int((len(lon) - 1)/2)
    lon0 = lon[middleIndex]

    r = np.arange(-80,81,10)#*2.0

    ii=np.arange(0,wrnum,1)
    remp = wrnum%2
    if remp==0:
        nrows = wrnum/2
    else:
        nrows = (wrnum+1)/2

    lon,lat = np.meshgrid(lon, lat)
    tran = ccrs.PlateCarree(central_longitude=lon0)
    proj = tran
    fig = plt.figure(figsize=(10,10))
    for g1 in np.arange(0,wrnum,1):
        g = ii[g1]
        ax1 = fig.add_subplot(nrows,2,g1+1,projection=proj)
        contourf(lon,lat,inputi[g],r,transform=ccrs.PlateCarree(),cmap = cmocean.cm.balance,extend="both")
        ax1.coastlines(resolution='50m', color='gray', linewidth=1.25)
        if (wrnum - g1) <= 2:
            plt.colorbar(orientation='horizontal', fraction=0.086, pad=0.05)
        fr = perc[g1]*100 #get_cluster_fraction(f,g) * 100
        plt.title('WR '+str(g1+1)+' ('+str(round(fr,1))+'%)')

    plt.tight_layout()
    fmt='png'
    full_output_plot = output_plotname + "." + fmt
    plt.savefig(full_output_plot,format=fmt,dpi=400, bbox_inches='tight')

    plt.show()
