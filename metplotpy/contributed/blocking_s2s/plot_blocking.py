# ============================*
 # ** Copyright UCAR (c) 2020
 # ** University Corporation for Atmospheric Research (UCAR)
 # ** National Center for Atmospheric Research (NCAR)
 # ** Research Applications Lab (RAL)
 # ** P.O.Box 3000, Boulder, Colorado, 80307-3000, USA
 # ** University of Illinois, Urbana-Champaign
 # ============================*
 
 
 
import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import numpy as np
import sys
sys.path.insert(0, "/glade/u/home/kalb/UIUC/METcalcpy/")
import metcalcpy.util.utils as util
import warnings

warnings.filterwarnings("ignore",category=UserWarning)

def plot_ibls(blonlong,lons,plot_title,output_plotname,**kwargs):

    # Get extra arguments
    data2 = kwargs.get('data2',None)
    lon2 = kwargs.get('lon2',None)
    label1 = kwargs.get('label1',None)
    label2 = kwargs.get('label2',None)

    #calculating long-term mean IBL for figure
    # Average across all days
    blonlongyr = np.mean(blonlong,axis=1) #[year, lon]
    blonlongmean = np.mean(blonlongyr,axis=0) #[lon]

    #Exchange longitude for better display
    lonplot,lonsortlocs = util.convert_lons_indices(lons,-89,360)
    a = blonlongmean[lonsortlocs]

    #Plot LTM IBL
    plt.figure()

    plt.plot(lonplot,a,linewidth = 2,label=label1)

    #Check for an additional dataset
    print('Plotting')
    if data2 is not None:
        blon2longyr = np.mean(data2,axis=1) #[year, lon]
        blon2longmean = np.mean(blon2longyr,axis=0) #[lon]
        if lon2 is not None:
            lon2plot,lon2sortlocs = util.convert_lons_indices(lon2,-89,360)
        else:
            lon2plot = lonplot
            lon2sortlocs = lonsortlocs
        a2 = blon2longmean[lon2sortlocs]
        plotmax = np.nanmax([np.nanmax(a),np.nanmax(a2)])
        plt.plot(lon2plot,a2,linewidth = 2,label=label2)
    else:
        plotmax=np.nanmax(a)
    plt.xlim([-90,270])
    #plt.ylim([0,plotmax])
    plt.ylabel('IBL Frequency')
    plt.title(plot_title)
    ax=plt.gca()
    ax.minorticks_on()
    ax.tick_params(axis='both',width=1.5,length=5)
    ax.tick_params(which='minor',width=1.5,length=2.5)
    ax.grid(True, which='both',axis='x')
    ax.grid(True, which='major',axis='y',linewidth=1.5)
    ax.grid(True, which='major',axis='x',linewidth=1.5)
    if label1:
        plt.legend()

    fmt = 'pdf'
    full_output_plot = output_plotname + "." + fmt
    plt.savefig(full_output_plot,format=fmt,dpi=400, bbox_inches='tight')
    plt.pause(1e-13)
    fmt2 = 'png'
    full_output_plot2 = output_plotname + "." + fmt2
    plt.savefig(full_output_plot2,format=fmt2,dpi=400, bbox_inches='tight')


def plot_blocks(blockfreq,GIBL,ibl,lons,plot_title,output_plotname):

    lonplot,lonsortlocs = util.convert_lons_indices(lons,-90,360)

    gibl_mean = np.mean(GIBL,axis=(1,0))
    gibl_mean = gibl_mean[lonsortlocs]
    
    blockfreq_mean = np.nanmean(blockfreq,axis=(1,0))
    blockfreq_mean = blockfreq_mean[lonsortlocs]
    ibl_mean = np.mean(ibl,axis=(1,0))
    ibl_mean = ibl_mean[lonsortlocs]

    plt.figure()

    lw = 2
    plt.plot(lonplot,ibl_mean,'k',linewidth = lw)
    plt.plot(lonplot,gibl_mean,'b',linewidth=lw)
    plt.plot(lonplot,blockfreq_mean,'r',linewidth = lw)

    plt.xlim([-90,270])
    plt.ylabel('Blocking Frequency')
    plt.xlabel('Longitude')
    plt.title(plot_title)
    plt.legend(['IBL','GIBL','Blocked Events'],loc=1,ncol=1,prop={'size':14})
    ax=plt.gca()
    ax.minorticks_on()
    ax.tick_params(axis='both',width=1.5,length=5)
    ax.tick_params(which='minor',width=1.5,length=2.5)
    ax.grid(True, which='both',axis='x')
    ax.grid(True, which='major',axis='y',linewidth=1.5)
    ax.grid(True, which='major',axis='x',linewidth=1.5)

    fmt = 'pdf'
    full_output_plot = output_plotname + "." + fmt
    plt.savefig(full_output_plot,format=fmt,dpi=400, bbox_inches='tight')
    plt.pause(1e-13)
    fmt2 = 'png'
    full_output_plot2 = output_plotname + "." + fmt2
    plt.savefig(full_output_plot2,format=fmt2,dpi=400, bbox_inches='tight')
