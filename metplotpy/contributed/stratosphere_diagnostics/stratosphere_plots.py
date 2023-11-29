import xarray as xr  # http://xarray.pydata.org/
import numpy as np
import cmocean
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

def plot_zonal_u_bias(lats,levels,bias,obar,outfile):

    plt.figure(0)
    plt.contourf(lats,levels,np.transpose(bias),cmap= cmocean.cm.balance,levels = np.arange(-12,13,2))
    plt.colorbar(orientation='horizontal')
    CS = plt.contour(lats,levels,np.transpose(obar),levels=[0,10,20,30,40,50,60,70,80,90,100],colors='black')
    plt.clabel(CS, inline=True, fontsize=10)
    plt.gca().invert_yaxis()
    plt.gca().set_yscale('log')
    plt.gca().yaxis.set_major_formatter(mticker.ScalarFormatter())
    plt.xlabel('Latitude (degrees)')
    plt.ylabel('Pressure (hPa)')
    plt.suptitle('GFS 24h Forecast Zonal Mean Wind Bias (ME) 02/2018')
    plt.title('Black Contours: ERA Climatology')

    # Save plot
    plt.savefig(outfile)
