import xarray as xr  # http://xarray.pydata.org/
import numpy as np
import pandas as pd
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


def plot_qbo_phase_circuits(inits,periods,rean_qbo_pcs,rfcst_qbo_pcs,outfile):

    fig = plt.figure(1)

    for i,init in enumerate(inits):

        dates = pd.date_range(init, periods=periods, freq="1D")
        #Remove leap days
        dates = dates[(dates.month != 2) | (dates.day != 29)] 
        ax = fig.add_subplot(4,7,i+1)

        # plot the QBO phase space time series
        plt_handles = []

        # green/red dots are the start/end of the fcst period
        plt.plot(rfcst_qbo_pcs.sel(mode=0, time=dates),
             rfcst_qbo_pcs.sel(mode=1, time=dates), linewidth=1.5)
        plt.plot(rfcst_qbo_pcs.sel(mode=0, time=dates[0]),
             rfcst_qbo_pcs.sel(mode=1, time=dates[0]), marker="o", color="green")
        plt.plot(rfcst_qbo_pcs.sel(mode=0, time=dates[-1]),
             rfcst_qbo_pcs.sel(mode=1, time=dates[-1]), marker="o", color="red")

        # plot same thing from reanalysis in black
        plt.plot(rean_qbo_pcs.sel(mode=0, time=dates),
             rean_qbo_pcs.sel(mode=1, time=dates), color='black', linewidth=1.5)
        plt.plot(rean_qbo_pcs.sel(mode=0, time=dates[0]),
             rean_qbo_pcs.sel(mode=1, time=dates[0]), marker="o", color="green")
        plt.plot(rean_qbo_pcs.sel(mode=0, time=dates[-1]),
             rean_qbo_pcs.sel(mode=1, time=dates[-1]), marker="o", color="red")
        plt.xlim((-2.5,2.5))
        plt.ylim((-2.5,2.5))
        plt.gca().set_aspect('equal')
        plt.title('Start: '+init.strftime('%Y-%m-%d'), fontsize=22)

        # plot the QBO phase lines
        amp = 2.5
        ax.plot([-amp,amp],[-amp,amp], linewidth=0.5, linestyle='--', color='k', zorder=0)
        ax.plot([-amp,amp],[amp,-amp], linewidth=0.5, linestyle='--', color='k', zorder=0)
        ax.plot([-amp,amp],[0,0], linewidth=0.5, linestyle='--', color='k', zorder=0)
        ax.plot([0,0],[-amp,amp], linewidth=0.5, linestyle='--', color='k', zorder=0)
        ax.set_xticks(np.arange(-2.,2.1,1))
        ax.set_yticks(np.arange(-2.,2.1,1))


    fig.set_size_inches(24,16)
    fig.subplots_adjust(hspace = 0.25, left=0.07, right=0.92, top=0.92, bottom=0.07)
    plt.savefig(outfile, dpi=150, facecolor='white', bbox_inches="tight")



def plot_qbo_phase_space(rean_qbo_pcs,eofs,plot_title,outfile):

    from mpl_toolkits.axes_grid1.inset_locator import (inset_axes, InsetPosition, mark_inset)

    fig = plt.figure(4)

    ax = fig.add_subplot(1,1,1)
    ax.plot(rean_qbo_pcs.sel(mode=0), rean_qbo_pcs.sel(mode=1), alpha=0.75, linewidth=0.6)
    ax.set_xlim((-2.5,2.5))
    ax.set_ylim((-2.5,2.5))
    ax.set_aspect('equal')

    amp = 2.5
    ax.plot([-amp,amp],[-amp,amp], linewidth=0.65, linestyle='--', color='k', zorder=0)
    ax.plot([-amp,amp],[amp,-amp], linewidth=0.65, linestyle='--', color='k', zorder=0)
    ax.plot([-amp,amp],[0,0], linewidth=0.65, linestyle='--', color='k', zorder=0)
    ax.plot([0,0],[-amp,amp], linewidth=0.65, linestyle='--', color='k', zorder=0)
    ax.set_xticks(np.arange(-2.,2.1,1))
    ax.set_yticks(np.arange(-2.,2.1,1))

    ax.set_xlabel('EOF1', fontsize=20)
    ax.set_ylabel('EOF2', fontsize=20)
    ax.tick_params(which='major', axis='both', length=7, labelsize=18)
    ax.grid(True,alpha=0.5)

    ## Plot idealized zonal wind profiles for different combinations of
    ## EOF values
    inset_axes = []
    axi = ax.inset_axes([2,-0.25,0.5,0.5], transform=ax.transData)
    axi.plot(eofs.sel(mode=0), eofs.pres, linewidth=1.5)
    inset_axes.append(axi)

    axi = ax.inset_axes([np.sqrt(2)+0.2, np.sqrt(2)+0.2, 0.5, 0.5], transform=ax.transData)
    axi.plot(eofs.sel(mode=0)+eofs.sel(mode=1), eofs.pres, linewidth=1.5)
    inset_axes.append(axi)

    axi = ax.inset_axes([-0.25,2, 0.5, 0.5], transform=ax.transData)
    axi.plot(eofs.sel(mode=1), eofs.pres, linewidth=1.5)
    inset_axes.append(axi)

    axi = ax.inset_axes([-np.sqrt(2)-0.2-0.5, np.sqrt(2)+0.2, 0.5, 0.5], transform=ax.transData)
    axi.plot(-1*eofs.sel(mode=0)+eofs.sel(mode=1), eofs.pres, linewidth=1.5)
    inset_axes.append(axi)

    axi = ax.inset_axes([-2.5,-0.25, 0.5, 0.5], transform=ax.transData)
    axi.plot(-1*eofs.sel(mode=0), eofs.pres, linewidth=1.5)
    inset_axes.append(axi)

    axi = ax.inset_axes([-np.sqrt(2)-0.2-0.5, -np.sqrt(2)-0.2-0.5, 0.5, 0.5], transform=ax.transData)
    axi.plot(-1*eofs.sel(mode=0)-eofs.sel(mode=1), eofs.pres, linewidth=1.5)
    inset_axes.append(axi)

    axi = ax.inset_axes([-0.25,-2.5, 0.5, 0.5], transform=ax.transData)
    axi.plot(-1*eofs.sel(mode=1), eofs.pres, linewidth=1.5)
    inset_axes.append(axi)

    axi = ax.inset_axes([np.sqrt(2)+0.2, -np.sqrt(2)-0.2-0.5, 0.5, 0.5], transform=ax.transData)
    axi.plot(eofs.sel(mode=0)-eofs.sel(mode=1), eofs.pres, linewidth=1.5)
    inset_axes.append(axi)

    for axi in inset_axes:
        axi.invert_yaxis()
        axi.set_yscale('log')
        axi.set_yticks([])
        axi.set_xticks([])
        axi.minorticks_off()
        axi.set_xlim(-1.1,1.1)
        axi.axvline(0, color='black')
        axi.set_facecolor('lightgrey')

    ax.set_title(plot_title, fontsize=24, fontweight='semibold')
    fig.set_size_inches(10,10)

    plt.savefig(outfile, dpi=150, facecolor='white')
