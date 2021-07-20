import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt
import matplotlib.colors as colors
from pylab import *
import cmocean
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from cartopy.util import add_cyclic_point
import numpy as np
import metcalcpy.util.utils as util

def plot_elbow(K,d,mi,line,curve,plot_title,output_plotname):

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


def plot_eof(eof,wrnum,variance_fractions,lons,lats,output_plotname,plevels):

    print(output_plotname)
    middleIndex = int((len(lons) - 1)/2)
    lon0 = lons[middleIndex]

    remp = wrnum%2
    if remp==0:
        nrows = wrnum/2
    else:
        nrows = (wrnum+1)/2

    #Plot leading 6 modes
    tran = ccrs.PlateCarree(central_longitude=lon0)
    proj = tran
    fig = plt.figure(figsize=(10,10))
    for i in np.arange(0,wrnum,1):
        corr = eof[i]
        ax1 = fig.add_subplot(int(nrows),2,i+1,projection=proj)
        contourf(lons,lats,corr,plevels,transform=ccrs.PlateCarree(),cmap = cmocean.cm.balance,extend='both')
        if (wrnum - i) <= 2:
            plt.colorbar(orientation ='horizontal',pad=0.01)  #.set_label(label='m',size=15)
        ax1.add_feature(cfeature.BORDERS)
        ax1.add_feature(cfeature.STATES)
        ax1.add_feature(cfeature.COASTLINE)
        plt.title('EOF '+str(i+1)+' ('+str(round(variance_fractions[i],2))+' %)')

    plt.tight_layout()
    fmt='png'
    full_output_plot = output_plotname + "." + fmt
    plt.savefig(full_output_plot,format=fmt,dpi=400, bbox_inches='tight')


def plot_K_means(inputi,wrnum,lons,lats,perc,output_plotname,plevels):

    lons,lonsort = util.convert_lons_indices(lons,-180,360)

    ### Plot the clusters
    middleIndex = int((len(lons) - 1)/2)
    lon0 = lons[middleIndex]

    ii=np.arange(0,wrnum,1)
    remp = wrnum%2
    if remp==0:
        nrows = wrnum/2
    else:
        nrows = (wrnum+1)/2

    lons,lats = np.meshgrid(lons, lats)
    tran = ccrs.PlateCarree(central_longitude=lon0)
    proj = tran
    fig = plt.figure(figsize=(10,10))
    for g1 in np.arange(0,wrnum,1):
        g = ii[g1]
        ax1 = fig.add_subplot(int(nrows),2,g1+1,projection=proj)
        if plevels:
            contourf(lons,lats,inputi[g],plevels,transform=ccrs.PlateCarree(),cmap = cmocean.cm.balance,extend="both")
        else:
            contourf(lons,lats,inputi[g],transform=ccrs.PlateCarree(),cmap = cmocean.cm.balance,extend="both")
        ax1.coastlines(resolution='50m', color='gray', linewidth=1.25)
        if (wrnum - g1) <= 2:
            plt.colorbar(orientation='horizontal', fraction=0.086, pad=0.05).set_label(label='m',size=15)
        fr = perc[g1]*100 #get_cluster_fraction(f,g) * 100
        plt.title('Weather Regime '+str(g1+1)+' ('+str(round(fr,1))+'%)')

    plt.tight_layout()
    fmt='png'
    full_output_plot = output_plotname + "." + fmt
    plt.savefig(full_output_plot,format=fmt,dpi=400, bbox_inches='tight')


def plot_wr_frequency(WRmean,wrnum,dlen,plot_title,output_plotname):

    days = np.arange(1,dlen+1)
    plt.figure(figsize=(10,5))

    for ww in np.arange(np.int(wrnum)):
        plt.plot(days,WRmean[ww],label='WR'+str(ww+1)+'')

    plt.ylabel('Number of WR days per week')
    plt.xlabel('Week of DJF')
    plt.title(plot_title)
    plt.legend()
    plt.xlim([1,dlen+1])

    fmt='png'
    full_output_plot = output_plotname + "." + fmt
    plt.savefig(full_output_plot,format=fmt,dpi=400, bbox_inches='tight')
