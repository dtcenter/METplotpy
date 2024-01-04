import xarray as xr  # http://xarray.pydata.org/
import numpy as np
import cmocean
import matplotlib
from matplotlib import cm
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker


def plot_zonal_bias(lats,levels,bias,obar,outfile,ptitle,plevs):

    plt.figure(0)
    plt.contourf(lats,levels,np.transpose(bias),cmap= cmocean.cm.balance,levels = range(-12,14,2))
    plt.colorbar(orientation='horizontal')
    CS = plt.contour(lats,levels,np.transpose(obar),levels=plevs,colors='black',linewidths=0.5)
    plt.clabel(CS, inline=True, fontsize=10)
    plt.gca().invert_yaxis()
    plt.gca().set_yscale('log')
    plt.gca().yaxis.set_major_formatter(mticker.ScalarFormatter())
    plt.xlabel('Latitude (degrees)')
    plt.ylabel('Pressure (hPa)')
    plt.suptitle(ptitle)
    plt.title('Black Contours: Obs Climatology')

    # Save plot
    plt.savefig(outfile)
    plt.close()


def plot_polar_bias(leads,levels,pdata,outfile,ptitle,plevs):

    ctable = cmocean.cm.balance
    plot_polar_contour(leads,levels,pdata,outfile,ptitle,plevs,ctable)


def plot_polar_rmse(leads,levels,pdata,outfile,ptitle,plevs):

    ctable = cm.viridis
    plot_polar_contour(leads,levels,pdata,outfile,ptitle,plevs,ctable)


def plot_polar_contour(leads,levels,pdata,outfile,ptitle,plevs,ctable):

    plt.figure(0)
    plt.contourf(leads,levels,pdata,cmap=ctable,levels = plevs)
    plt.colorbar(orientation='horizontal')
    plt.gca().invert_yaxis()
    plt.gca().set_yscale('log')
    plt.gca().yaxis.set_major_formatter(mticker.ScalarFormatter())
    plt.xlabel('Lead Time (hours)')
    plt.ylabel('Pressure (hPa)')
    plt.suptitle(ptitle)

    # Save plot
    plt.savefig(outfile)
    plt.close()

