import matplotlib.pyplot as plt
import matplotlib.colors as colors
import numpy as np

def convert_lons_indices(exlons,minlon_in):

    origlons = np.asarray(exlons)
    minlon = abs(minlon_in)

    # Use formula
    newlons = np.mod((exlons + minlon), 360) - minlon
    lonsortlocs = np.argsort(newlons)
    reordered_lons = newlons[lonsortlocs]

    return reordered_lons,lonsortlocs

def plot_ibls(blonlong,lons,plot_title,output_plotname):

    #calculating long-term mean IBL for figure
    # Average across all days
    blonlongyr = np.mean(blonlong,axis=1) #[year, lon]
    blonlongmean = np.mean(blonlongyr,axis=0) #[lon]


    #Exchange longitude for better display
    lonplot,lonsortlocs = convert_lons_indices(lons,-89)
    a = blonlongmean[lonsortlocs]

    #Plot LTM IBL
    plt.figure()

    plt.plot(lonplot,a,linewidth = 2)
    plt.xlim([-90,270])
    plt.ylabel('IBL Frequency')
    plt.title(plot_title)
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


def plot_blocks(blockfreq,GIBL,ibl,lons,plot_title,output_plotname):

    lonplot,lonsortlocs = convert_lons_indices(lons,-90)

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
