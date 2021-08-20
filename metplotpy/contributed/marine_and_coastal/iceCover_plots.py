#!/bin/env python
"""
Global RTOFS Ice Concentration Metrics
Version 1.0
Todd Spindler
NOAA/NWS/NCEP/EMC

Changes
25 July 2019 -- ported to Phase 3 (Mars)
26 Aug 2020 -- ported to Hera
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
#import matplotlib.mlab as mlab
from scipy.stats import norm
from sklearn.metrics import mean_squared_error
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import xarray as xr
import pandas as pd
from pyproj import Geod
import pyresample as pyr
from datetime import datetime, date
from PIL import Image
import io
import sqlite3
import os, sys
import subprocess
from mmab_toolkit import MidpointNormalize, add_mmab_logos
#import ipdb; ipdb.set_trace()

# something pandas needs
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()

PLOT_STATS=True
UPDATE_DB=True
UPLOAD_TO_POLAR=False
MAKE_MOVIE=False

# initialize the database
def init_db(dbfile):
    
    # connect to db file
    conn = sqlite3.connect(dbfile,detect_types=sqlite3.PARSE_DECLTYPES,timeout=30.0)
    c = conn.cursor()    
    
    # Create table
    c.execute('CREATE TABLE IF NOT EXISTS ice (date timestamp,' +
                                              'hemisphere string,' +
                                              'diff_avg real,' +
                                              'diff_std real,' + 
                                              'diff_bias real,' + 
                                              'diff_rms real,' + 
                                              'diff_cc real,' + 
                                              'diff_si real,' + 
                                              'ncep_extent real,' + 
                                              'rtofs_extent real,' +
                                              'ncep_area real,' + 
                                              'rtofs_area real,' +
                                              'unique(date,hemisphere))')
                                  
    # Save (commit) the changes
    conn.commit()
                 
    # close the connection
    conn.close()    
    return

# initialize the database
def update_db(dbfile,date,hemisphere,mu,sigma,bias,rms,cc,si,ncep_extent,rtofs_extent,ncep_area,rtofs_area):
    
    if not os.path.isfile(dbfile):
        init_db(dbfile)
        
    # connect to db file
    conn = sqlite3.connect(dbfile,detect_types=sqlite3.PARSE_DECLTYPES,timeout=30.0)
    c = conn.cursor()    
    
    # Larger example that inserts many records at a time
    
    y,m,d=int(date[0:4]),int(date[4:6]),int(date[6:8])
    thedate=datetime(y,m,d)
    
    update = (thedate,hemisphere,mu,sigma,bias,rms,cc,si,ncep_extent,rtofs_extent,ncep_area,rtofs_area)
    
    c.execute('REPLACE INTO ice VALUES (?,?,?,?,?,?,?,?,?,?,?,?)', update)
    
    # Save (commit) the changes
    conn.commit()
                 
    # close the connection
    conn.close()    

#-------------------------------------
# read the database back in
#-------------------------------------
def read_db(dbfile):
    
    conn=sqlite3.connect(dbfile,detect_types=sqlite3.PARSE_DECLTYPES,timeout=30.0)
    results=pd.read_sql('SELECT DISTINCT * FROM ice',conn)
    conn.close()
    
    return results
#-------------------------------------
# figure optimization and compression 
#-------------------------------------
def saveImage(imagefile,**kwargs):
    ram = io.BytesIO()
    plt.gcf().savefig(ram,**kwargs)
    ram.seek(0)
    im=Image.open(ram)
    im2 = im.convert('RGB').convert('P', palette=Image.WEB)
    im.save(imagefile, format='PNG',optimize=True)
    ram.close()
    return
#--------------------------------------
# compute stats with weighted averages 
#--------------------------------------
def calc_stats(obs,model,area):
    diff=model-obs
    bias = np.ma.average(diff,weights=area)
    obs_sdev=obs.std()
    model_sdev=model.std()
    rmse=mean_squared_error(obs,model,sample_weight=area)**0.5
    cc=np.ma.corrcoef(obs.flatten(),model.flatten())[0,1]
    si=100.0*((np.ma.average(diff**2,weights=area))**0.5 - bias**2)/np.ma.average(obs,weights=area)
    
    return bias, rmse, cc, si

#-------------------------------------
def iceArea(lon1,lat1,ice1):
    """
    Compute the cell side dimensions (Vincenty) and the cell surface areas.
    This assumes the ice has already been masked and subsampled as needed    
    returns ice_extent, ice_area, surface_area = iceArea(lon,lat,ice)
    surface_area is the computed grid areas in km**2)
    """
    lon=lon1.copy()
    lat=lat1.copy()
    ice=ice1.copy()
    g=Geod(ellps='WGS84')
    _,_,xdist=g.inv(lon,lat,np.roll(lon,-1,axis=1),np.roll(lat,-1,axis=1))
    _,_,ydist=g.inv(lon,lat,np.roll(lon,-1,axis=0),np.roll(lat,-1,axis=0))
    xdist=np.ma.array(xdist,mask=ice.mask)/1000.
    ydist=np.ma.array(ydist,mask=ice.mask)/1000.
    xdist=xdist[:-1,:-1]
    ydist=ydist[:-1,:-1]
    ice=ice[:-1,:-1]     # just to match the roll
    extent=xdist*ydist   # extent is surface area only
    area=xdist*ydist*ice # ice area is actual ice cover (area * concentration)
    return extent.flatten().sum(), area.flatten().sum(), extent

#--------------------------------------------------------
def make_maps(imageDir,hemisphere,theDate,
              nlon,nlat,nice,rlon,rlat,rice,
              diff,crs,ncep_area,rtofs_area,mu,sigma,bias,rms,cc,si):
    
    cmap='nipy_spectral'

    # pretty pictures
    print('plotting rtofs ice')
    plt.figure(dpi=150)
    ax=plt.axes(projection=crs)
    plt.pcolormesh(rlon,rlat,rice,cmap=cmap,
                   transform=ccrs.PlateCarree(),
                   vmin=0,vmax=1.0)
    plt.tick_params(labelsize='x-small')
    ax.add_feature(cfeature.LAND,zorder=1)
    ax.coastlines(zorder=1)
    ax.gridlines()
    add_mmab_logos()
    cb=plt.colorbar()
    cb.ax.tick_params(labelsize='x-small')
    plt.title('Global RTOFS sea ice concentration '+theDate+'\n(area='+'%10.3e'%rtofs_area+' km$^2$)',fontsize='small')
    saveImage(imageDir+'/rtofs_ice_'+hemisphere+'.png',dpi=150)
    plt.close()
    
    print('plotting OSTIA ice')
    plt.figure(dpi=150)
    ax=plt.axes(projection=crs)
    plt.pcolormesh(nlon,nlat,nice,cmap=cmap,
                   transform=ccrs.PlateCarree(),
                   vmin=0,vmax=1.0)
    plt.tick_params(labelsize='x-small')
    ax.add_feature(cfeature.LAND,zorder=1)
    ax.coastlines(zorder=1)
    ax.gridlines()
    add_mmab_logos()
    cb=plt.colorbar()
    cb.ax.tick_params(labelsize='x-small')
    plt.title('OSTIA sea ice concentration '+theDate+'\n(area='+'%10.3e'%ncep_area+' km$^2$)',fontsize='small')
    saveImage(imageDir+'/ncep_ice_'+hemisphere+'.png',dpi=150)
    plt.close()
    
    print('plotting difference')
    plt.figure(dpi=150)
    #ax1=plt.axes([.1,.3,.8,.6],projection=crs)
    ax1 = plt.subplot2grid((4,1),(0,0),rowspan=3,projection=crs)
    #plt.pcolormesh(nlon,nlat,diff,cmap='bwr',transform=ccrs.PlateCarree(),
    #               norm=MidpointNormalize(midpoint=0.,vmin=diff.min(),vmax=diff.max()))
    plt.pcolormesh(nlon,nlat,diff,cmap='bwr',transform=ccrs.PlateCarree(),
                   norm=MidpointNormalize(midpoint=0.,vmin=-0.5,vmax=0.5))
    plt.tick_params(labelsize='x-small')
    ax1.add_feature(cfeature.LAND,zorder=1)    
    ax1.coastlines(zorder=1)
    ax1.gridlines()
    add_mmab_logos()
    cb=plt.colorbar()
    cb.ax.tick_params(labelsize='x-small')
    plt.title('RTOFS minus OSTIA sea ice concentration for ' + theDate,fontsize='small')
    
    #ax2=plt.axes([.22,.05,.6,.15])
    ax2 = plt.subplot2grid((6,4),(5,1),colspan=2)
    # match the width of the axis above
    #bb1=ax1.get_position(original=False)
    bb2=ax2.get_position(original=False)
    ax2.set_position([bb2.x0,bb2.y0+.05,bb2.x1-bb2.x0,bb2.y1-bb2.y0])
    # set number of bins to 100
    n,bins,patches=plt.hist(diff.compressed(),100,density=True,alpha=0.5)
    #y=mlab.normpdf(bins,mu,sigma)
    y=norm.pdf(bins,mu,sigma)
    plt.plot(bins,y,'r-')
    plt.xlim((-0.5,0.5))
    plt.tick_params(labelsize='x-small')
    plt.grid()
    plt.title('Difference distribution',fontsize='x-small')
    plt.text(1.5,1.0,'weighted avg={:3.3f}\nstd dev={:3.3f}\nbias={:3.3f}\nrmse={:3.3f}\ncorr coeff={:3.3f}\nscatter index={:3.3f}'.format(mu,sigma,bias,rms,cc,si),
             transform=ax2.transAxes,horizontalalignment='right',
             verticalalignment='top',fontsize='x-small')
    
    saveImage(imageDir+'/ice_diff_'+hemisphere+'.png',dpi=150)

    return

#---------------------------------------------------------------
def plot_stats(imageDir,hemisphere,theDate,dbfile,lookback='180 d'):
    """
    Plot accumulated statistics with a 6-month lookback
    """

    results=read_db(dbfile)
    results=results[results.hemisphere==hemisphere]
    results.index=results.date
    
    minDate=pd.to_datetime(theDate)-pd.Timedelta(lookback)
    results=results[minDate:theDate]

    # diff plot
    plt.figure(dpi=150)
    ax=plt.axes()
    plt.fill_between(results.index,results.diff_avg+results.diff_std,
                     results.diff_avg-results.diff_std,color='lightgrey',
                     label='Std Dev')
    results.diff_avg.plot(ax=ax,label='Area-weighted Average',fontsize='small')
    plt.grid()
    plt.legend(fontsize='small')
    plt.ylabel('Sea Ice Concentration Difference',fontsize='small')
    plt.xlabel('Date',fontsize='small')
    plt.title('RTOFS minus OSTIA Sea Ice Concentration\n'+hemisphere.capitalize()+'ern Hemisphere '+theDate,fontsize='small')
    add_mmab_logos()
    saveImage(imageDir+'/ice_stats_'+hemisphere+'.png',dpi=150)
    plt.close()

    # stats plots
    params={'diff_bias':'Bias','diff_rms':'RMSE','diff_cc':'Corr Coeff','diff_si':'Scatter Index'}
    for param,name in params.items():
        plt.figure(dpi=150)
        ax=plt.axes()
        results[param].plot(ax=ax,label=name,fontsize='small')
        plt.grid()
        plt.legend(fontsize='small')
        plt.xlabel('Date',fontsize='small')
        plt.title(name+' for RTOFS minus OSTIA Sea Ice Concentration\n'+hemisphere.capitalize()+'ern Hemisphere '+theDate,fontsize='small')
        add_mmab_logos()
        saveImage(imageDir+'/ice_stats_'+param+'_'+hemisphere+'.png',dpi=150)
        plt.close()

    # accumulated extent plot
    plt.figure(dpi=150)
    ax=plt.axes()
    results['ncep_extent']=results.ncep_extent/1e6
    results['rtofs_extent']=results.rtofs_extent/1e6
    results['ncep_area']=results.ncep_area/1e6
    results['rtofs_area']=results.rtofs_area/1e6
    results.ncep_extent.plot(ax=ax,linestyle='-',color='C0',label='NCEP Ice Extent',fontsize='small')
    results.rtofs_extent.plot(ax=ax,linestyle='-',color='C1',label='RTOFS Ice Extent',fontsize='small')
    results.ncep_area.plot(ax=ax,linestyle='--',color='C0',label='NCEP Ice Area',fontsize='small')
    results.rtofs_area.plot(ax=ax,linestyle='--',color='C1',label='RTOFS Ice Area',fontsize='small')
    plt.legend(fontsize='small')
    plt.grid()
    plt.ylabel('Sea Ice Extent and Area $x10^6 (km^2)$',fontsize='small')
    plt.xlabel('Date',fontsize='small')
    plt.title(hemisphere.capitalize()+'ern Hemisphere Ice Extent and Area '+theDate,fontsize='small')
    add_mmab_logos()
    saveImage(imageDir+'/ice_extent_area_'+hemisphere+'.png',dpi=150)
    plt.close()
    return

#-------------------------------------------------------
def process_one_day(theDate,hemisphere):
    
    print('processing',hemisphere+'ern hemisphere')
    if hemisphere == 'north':
        crs=ccrs.NorthPolarStereo(central_longitude=-168.)
        bounding_lat=30.98
    else:
        crs=ccrs.SouthPolarStereo(central_longitude=-60.)
        bounding_lat=-39.23
        
    imageDir='/scratch2/NCEPDEV/stmp1/Todd.Spindler/images/ice/'+theDate
    rtofsfile='/scratch2/NCEPDEV/marine/Todd.Spindler/noscrub/Global/archive/'+theDate+'/rtofs_glo_2ds_n024_ice.nc'
    icefile='/scratch2/NCEPDEV/marine/Todd.Spindler/noscrub/OSTIA/OSTIA-UKMO-L4-GLOB-v2.0_'+theDate+'.nc'
    dbfile='/scratch2/NCEPDEV/marine/Todd.Spindler/save/VPPPG/Global_RTOFS/EMC_ocean-verification/ice/fix/global_ice.db'
        
    # separate the images by date
    if not os.path.isdir(imageDir):
        os.makedirs(imageDir)

    # load rtofs data and subset to hemisphere of interest and ice cover min value
    print('reading rtofs ice')
    if not os.path.exists(rtofsfile):
        print('missing rtofs file',rtofsfile)
        return
    rtofs=xr.open_dataset(rtofsfile,decode_times=True)
    rtofs=rtofs.ice_coverage[0,:-1,]
    #rtofs=rtofs[::-1,] # flip it to match ncep ice
            
    # load ice data
    print('reading ncep ice')
    if not os.path.exists(icefile):
        print('missing ncep ice file',icefile)
        return

    ncep=xr.open_dataset(icefile,decode_times=True)
    ncep=ncep.rename({'lon':'Longitude','lat':'Latitude'})
    ncep=ncep.sea_ice_fraction.squeeze()
    
    # trim to polar regions
    if hemisphere == 'north':
        rtofs=rtofs.where((rtofs.Latitude>=bounding_lat),drop=True) 
        ncep=ncep.where((ncep.Latitude>=bounding_lat),drop=True) 
    else:
        rtofs=rtofs.where((rtofs.Latitude<=bounding_lat),drop=True) 
        ncep=ncep.where((ncep.Latitude<=bounding_lat),drop=True) 
    
    # now it's back to masked arrays
    rlon=rtofs.Longitude.values
    rlat=rtofs.Latitude.values
    rice=rtofs.to_masked_array()

    nlon=ncep.Longitude.values%360. # shift from -180 - 180 to 0-360
    nlat=ncep.Latitude.values
    nlon,nlat=np.meshgrid(nlon,nlat)  # shift from 1-d to 2-d arrays
    nice=ncep.to_masked_array()
    
    # mask out values below 15%
    rice.mask=np.ma.mask_or(rice.mask,rice<0.15)
    nice.mask=np.ma.mask_or(nice.mask,nice<0.15)

    # compute ice area on original grids
    print('computing ice area')
    ncep_extent,ncep_area,ncep_surface_area=iceArea(nlon,nlat,nice)
    rtofs_extent,rtofs_area,rtofs_surface_area=iceArea(rlon,rlat,rice)
    
    # interpolate rtofs to ncep grid
    print('interpolating rtofs to OSTIA grid')            
    
    # pyresample gausssian-weighted kd-tree interp
    rlon1=pyr.utils.wrap_longitudes(rlon)
    rlat1=rlat.copy()
    nlon1=pyr.utils.wrap_longitudes(nlon)
    nlat1=nlat.copy()
    # define the grids
    orig_def = pyr.geometry.GridDefinition(lons=rlon1,lats=rlat1)
    targ_def = pyr.geometry.GridDefinition(lons=nlon1,lats=nlat1)
    radius=50000
    sigmas=25000    
    rice2=pyr.kd_tree.resample_gauss(orig_def,rice,targ_def,
                                     radius_of_influence=radius,
                                     sigmas=sigmas,
                                     nprocs=8,
                                     neighbours=8,
                                     fill_value=None)
            
    print('creating combined mask')
    combined_mask=np.logical_and(nice.mask,rice2.mask)
    nice2=nice.filled(fill_value=0.0)
    rice2=rice2.filled(fill_value=0.0)
    nice2=np.ma.array(nice2,mask=combined_mask)
    rice2=np.ma.array(rice2,mask=combined_mask)

    # compute various statistics
    print('computing statistics')
    diff=rice2-nice2
    bins=100
    # weighted average with grid surface area as weight              
    # trim off the bottom and right side to match the SA from iceArea
    mu = np.average(diff[:-1,:-1],weights=ncep_surface_area)
    sigma=diff.std()
    bias,rms,cc,si=calc_stats(nice2[:-1,:-1],rice2[:-1,:-1],ncep_surface_area)

    # draw pictures
    make_maps(imageDir,hemisphere,theDate,
              nlon1,nlat1,nice2,nlon1,nlat1,rice2,
              diff,crs,ncep_area,rtofs_area,mu,sigma,bias,rms,cc,si)
    
    # update the dbase
    if UPDATE_DB:
        update_db(dbfile,theDate,hemisphere,mu,sigma,bias,rms,cc,si,ncep_extent,rtofs_extent,ncep_area,rtofs_area)

    # plot ice stats
    if PLOT_STATS:
        plot_stats(imageDir,hemisphere,theDate,dbfile)

    #upload to web server
    if UPLOAD_TO_POLAR:
        print('starting upload at',datetime.now())
        remoteID='tspindler@140.90.100.206'
        remoteDir='/home/www/polar/global/ice/archive/images/'+theDate
        localDir='/scratch2/NCEPDEV/stmp1/Todd.Spindler/images/ice/'+theDate
        archDir='/scratch2/NCEPDEV/marine/Todd.Spindler/noscrub/Class-4/ice/images/'+theDate
        os.system('ssh -o "BatchMode yes" '+remoteID+' mkdir -p '+remoteDir)
        os.system('scp -o "BatchMode yes" '+localDir+'/*.png '+remoteID+':'+remoteDir+'/.')
        os.system('mkdir -p '+archDir)
        os.system('cp '+localDir+'/*.png '+archDir+'/.')
        os.system('rm -rf '+localDir)
        if MAKE_MOVIE:
            os.system('/scratch2/NCEPDEV/marine/Todd.Spindler/VPPPG/Global_RTOFS/EMC_ocean-verification/ice/scripts/make_ice_movies.sh '+theDate)
        
    return

#-----------------------------------------------------------------

if __name__ == '__main__':

    theDate=sys.argv[1]

    if len(sys.argv)<2:
        theDate=datetime.now().strftime('%Y%m%d')

    print('Starting Ice Concentration V&V at',datetime.now(),'for',theDate)
    
    for hemi in ['north','south']:
        process_one_day(theDate,hemi)

    print('completed ice at',datetime.now())
