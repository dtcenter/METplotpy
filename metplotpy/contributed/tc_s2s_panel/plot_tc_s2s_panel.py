#!/usr/bin/env python

import xarray as xr
import cartopy.crs as ccrs
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import os

# Stuff for making the colorbar height not extend past the plot box
from mpl_toolkits.axes_grid1 import make_axes_locatable

# For lat/lon axes
from cartopy.mpl.ticker import LongitudeFormatter, LatitudeFormatter

# Config options
ADDPTS = False
PANELTITLELOC = 'left'

# Set some variables
lead_step = int(str(os.environ.get('TCGEN_INIT_FREQ')))
shortest_lead = int(str(os.environ.get('TCGEN_MIN_LEAD')))
longest_lead = int(str(os.environ.get('TCGEN_MAX_LEAD')))
LEAD_WINDOW_STR = f"{shortest_lead:d} - {longest_lead:d}"

# Strings for plots
count_string = f'TC genesis counts per 10x10 degrees per year'
days_string = f'TC days per 10x10 degrees per year'

# Function for common axis params
def setup_axis(ax):

    # What environment variables will we need here?
    # None, just leave this stuff fixed for the use case

    # Add coastlines
    ax.coastlines(resolution='50m',color='black')

    # Set the latitude window limit (y-axis)
    ax.set_ylim([-40,40])

    # Define the tickmark locations for the x-axis (longitude)
    ax.set_xticks([45, 90, 135, 180, 225, 270, 315], minor=False, crs=ccrs.PlateCarree())

    # Define the tickmark locations for the y-axis (latitude)
    ax.set_yticks([-40, -30, -15, 0, 15, 30, 40], minor=False, crs=ccrs.PlateCarree())

    # Set tickmark formatting for x and y axes
    ax.xaxis.set_major_formatter(LongitudeFormatter(zero_direction_label=True))
    ax.yaxis.set_major_formatter(LatitudeFormatter())

    # Control which sides of the panel tickmarks appear on
    ax.tick_params(axis="x", bottom=True, top=False, labelbottom=True, labeltop=False)
    ax.tick_params(axis="y", left=True, right=True, labelleft=True, labelright=True)
   
    # Turn off axis titles
    ax.set_ylabel('')
    ax.set_xlabel('')

# Panels go 1,2,3 top to bottom
def plot_gdf(gdf_data):

  # Use gridspec
  gs_gdf = gridspec.GridSpec(nrows=4,ncols=1,height_ratios=[1,1,1,1],hspace=0.20,wspace=0.0)

  # New Figure
  fig_gdf = plt.figure(1,figsize=(20,15))

  # Coordinate reference system
  crs_gdf = ccrs.PlateCarree(central_longitude=180.0)

  ####### PANEL 1
  ax1 = plt.subplot(gs_gdf[0,0],projection=crs_gdf)
  setup_axis(ax1)
  ax1.set_title('(a) BEST Genesis Event Density',loc=PANELTITLELOC)
  levels = [0.5,1.0,1.5,2.0,2.5,3.0,3.5,4.0]

  # create an axis on the bottom of ax. The width of cax will be 5%
  # of ax and the padding between cax and ax will be fixed at 0.35 inch.
  # since cartopy uses a geo_axes, we need to specify the axes_class for the append_axes method
  # Use this axis for the colorbar
  axdiv1 = make_axes_locatable(ax1)
  cbax1 = axdiv1.append_axes("bottom", size="5%", pad=0.35, axes_class=plt.Axes)

  # Contour the data
  con1 = gdf_data['OBS_DENS'].where(gdf_data['OBS_DENS']>0.0).plot.pcolormesh(ax=ax1,transform=ccrs.PlateCarree(),levels=levels,cmap=plt.cm.Reds,cbar_kwargs={'cax':cbax1,'ax':ax1,'orientation':'horizontal'},extend='max',add_labels=False)

  # Add scatter points if requested
  if ADDPTS:
    scat1 = ax1.scatter(alons,alats,transform=ccrs.PlateCarree(),s=1,c='cyan')

  # Add the colorbar and set the tickmarks on it
  cbar1 = con1.colorbar
  cbar1.set_ticks(levels)

  ######## PANEL 2
  ax2 = plt.subplot(gs_gdf[1,0],projection=crs_gdf)
  setup_axis(ax2)
  ax2.set_title(f'(b) Forecast Genesis Event Density ({LEAD_WINDOW_STR}h)',loc=PANELTITLELOC)
  levels = levels

  # create an axis on the bottom of ax. The width of cax will be 5%
  # of ax and the padding between cax and ax will be fixed at 0.35 inch.
  # since cartopy uses a geo_axes, we need to specify the axes_class for the append_axes method
  # Use this axis for the colorbar
  axdiv2 = make_axes_locatable(ax2)
  cbax2 = axdiv2.append_axes("bottom", size="5%", pad=0.35, axes_class=plt.Axes)

  # Contour the data
  con2 = gdf_data['FCST_DENS'].where(gdf_data['FCST_DENS']>0.0).plot.pcolormesh(ax=ax2,transform=ccrs.PlateCarree(),levels=levels,cmap=plt.cm.Reds,cbar_kwargs={'cax':cbax2,'ax':ax2,'orientation':'horizontal'},extend='max',add_labels=False)

  # Add scatter points if requested
  if ADDPTS:
    scat2 = ax2.scatter(hlon,hlat,transform=ccrs.PlateCarree(),s=1,c='cyan')

  # Add the colorbar and set the tickmarks on it
  cbar2 = con2.colorbar
  cbar2.set_ticks(levels)

  ######## PANEL 3
  fminuso = gdf_data['FCST_DENS']-gdf_data['OBS_DENS'] 
  ax3 = plt.subplot(gs_gdf[2,0],projection=crs_gdf)
  setup_axis(ax3)
  ax3.set_title(f'(c) (b) minus (a)',loc=PANELTITLELOC)
  levels = [-2.7,-2.1,-1.5,-0.9,-0.3,0.3,0.9,1.5,2.1,2.7]

  # create an axis on the bottom of ax. The width of cax will be 5%
  # of ax and the padding between cax and ax will be fixed at 0.35 inch.
  # since cartopy uses a geo_axes, we need to specify the axes_class for the append_axes method
  # Use this axis for the colorbar
  axdiv3 = make_axes_locatable(ax3)
  cbax3 = axdiv3.append_axes("bottom", size="5%", pad=0.35, axes_class=plt.Axes)

  # Contour the data
  con3 = fminuso.where((fminuso>0.3) | (fminuso<-0.3)).plot.pcolormesh(ax=ax3,transform=ccrs.PlateCarree(),levels=levels,cmap=plt.cm.coolwarm,cbar_kwargs={'cax':cbax3,'ax':ax3,'orientation':'horizontal'},extend='both',add_labels=False)

  # Add scatter points if requested
  if ADDPTS:
    scat3 = ax3.scatter(flon,flat,transform=ccrs.PlateCarree(),s=1,c='cyan')

  # Add the colorbar and set the tickmarks on it
  cbar3 = con3.colorbar
  cbar3.set_ticks(levels)
  cbar3.set_label(count_string,labelpad=0,y=1.05,rotation=0,size=20)

  ######## PANEL 4
  ax4 = plt.subplot(gs_gdf[3,0],projection=crs_gdf)
  ax4.axis('off')

  # Save off figure
  #plt.show()
  if ADDPTS:
     plt.savefig('GDF.png')
  else:
    plt.savefig('GDF.png',bbox_inches='tight',pad_inches=0.25)

  # Cleanup
  del(fig_gdf,gs_gdf)

# Panels go 1,2,3,4 top to bottom
def plot_gdf_ufs(gdf_data):
  
  # Use gridspec
  gs_gdf = gridspec.GridSpec(nrows=4,ncols=1,height_ratios=[1,1,1,1],hspace=0.20,wspace=0.0)

  # New Figure
  fig_gdf = plt.figure(1,figsize=(20,15))
  
  # Coordinate reference system
  crs_gdf = ccrs.PlateCarree(central_longitude=180.0)

  ####### PANEL 1
  ax1 = plt.subplot(gs_gdf[0,0],projection=crs_gdf)
  setup_axis(ax1)
  ax1.set_title('(a) BEST Genesis Event Density',loc=PANELTITLELOC)
  levels = [0.0,0.05,0.1,0.2,0.3,0.4,0.5,0.8,1.1,1.4]

  # create an axis on the bottom of ax. The width of cax will be 5%
  # of ax and the padding between cax and ax will be fixed at 0.35 inch.
  # since cartopy uses a geo_axes, we need to specify the axes_class for the append_axes method
  # Use this axis for the colorbar
  axdiv1 = make_axes_locatable(ax1)
  cbax1 = axdiv1.append_axes("bottom", size="5%", pad=0.35, axes_class=plt.Axes)

  # Contour the data
  con1 = gdf_data['OBS_DENS'].where(gdf_data['OBS_DENS']>0.0).plot.pcolormesh(ax=ax1,transform=ccrs.PlateCarree(),levels=levels,cmap=plt.cm.Reds,cbar_kwargs={'cax':cbax1,'ax':ax1,'orientation':'horizontal'},extend='max',add_labels=False)

  # Add scatter points if requested
  if ADDPTS:
    scat1 = ax1.scatter(alons,alats,transform=ccrs.PlateCarree(),s=1,c='cyan')

  # Add the colorbar and set the tickmarks on it
  cbar1 = con1.colorbar
  cbar1.set_ticks(levels)

  ######## PANEL 2
  ax2 = plt.subplot(gs_gdf[1,0],projection=crs_gdf)
  setup_axis(ax2)
  ax2.set_title('(b) Hits (Forecast Yes/Observation Yes)',loc=PANELTITLELOC)
  levels = levels

  # create an axis on the bottom of ax. The width of cax will be 5%
  # of ax and the padding between cax and ax will be fixed at 0.35 inch.
  # since cartopy uses a geo_axes, we need to specify the axes_class for the append_axes method
  # Use this axis for the colorbar
  axdiv2 = make_axes_locatable(ax2)
  cbax2 = axdiv2.append_axes("bottom", size="5%", pad=0.35, axes_class=plt.Axes)

  # Contour the data
  con2 = gdf_data['FYOY_DENS'].where(gdf_data['FYOY_DENS']>0.0).plot.pcolormesh(ax=ax2,transform=ccrs.PlateCarree(),levels=levels,cmap=plt.cm.Reds,cbar_kwargs={'cax':cbax2,'ax':ax2,'orientation':'horizontal'},extend='max',add_labels=False)

  # Add scatter points if requested
  if ADDPTS:
    scat2 = ax2.scatter(hlon,hlat,transform=ccrs.PlateCarree(),s=1,c='cyan')

  # Add the colorbar and set the tickmarks on it
  cbar2 = con2.colorbar
  cbar2.set_ticks(levels)

  ######## PANEL 3
  ax3 = plt.subplot(gs_gdf[2,0],projection=crs_gdf)
  setup_axis(ax3)
  ax3.set_title('(c) False Alarms (Forecast Yes/Observation No)',loc=PANELTITLELOC)
  levels = levels

  # create an axis on the bottom of ax. The width of cax will be 5%
  # of ax and the padding between cax and ax will be fixed at 0.35 inch.
  # since cartopy uses a geo_axes, we need to specify the axes_class for the append_axes method
  # Use this axis for the colorbar
  axdiv3 = make_axes_locatable(ax3)
  cbax3 = axdiv3.append_axes("bottom", size="5%", pad=0.35, axes_class=plt.Axes)

  # Contour the data
  con3 = gdf_data['FYON_DENS'].where(gdf_data['FYON_DENS']>0.0).plot.pcolormesh(ax=ax3,transform=ccrs.PlateCarree(),levels=levels,cmap=plt.cm.Reds,cbar_kwargs={'cax':cbax3,'ax':ax3,'orientation':'horizontal'},extend='max',add_labels=False)

  # Add scatter points if requested
  if ADDPTS:
    scat3 = ax3.scatter(flon,flat,transform=ccrs.PlateCarree(),s=1,c='cyan')

  # Add the colorbar and set the tickmarks on it
  cbar3 = con3.colorbar
  cbar3.set_ticks(levels)

  ######## PANEL 4
  hitfalse = gdf_data['FYOY_DENS']+gdf_data['FYON_DENS']
  ax4 = plt.subplot(gs_gdf[3,0],projection=crs_gdf)
  setup_axis(ax4)
  ax4.set_title('(d) Hits + False Alarms',loc=PANELTITLELOC)
  
  # create an axes on the bottom of ax. The width of cax will be 5%
  # of ax and the padding between cax and ax will be fixed at 0.35 inch.
  # since cartopy uses a geo_axes, we need to specify the axes_class for the append_axes method
  # Use this axis for the colorbar
  axdiv4 = make_axes_locatable(ax4)
  cbax4 = axdiv4.append_axes("bottom", size="5%", pad=0.35, axes_class=plt.Axes)

  # Contour the data
  con4 = hitfalse.where(hitfalse>0.0).plot.pcolormesh(ax=ax4,transform=ccrs.PlateCarree(),levels=levels,cmap=plt.cm.Reds,cbar_kwargs={'cax':cbax4,'ax':ax4,'orientation':'horizontal'},extend='max',add_labels=False)

  # Add scatter points if requested
  if ADDPTS:
    scat4 = ax4.scatter(flon,flat,transform=ccrs.PlateCarree(),s=1,c='cyan')

  # Add the colorbar and set the tickmarks on it
  # Since this is the bottom panel also add a title
  cbar4 = con4.colorbar
  cbar4.set_ticks(levels)
  cbar4.set_label(count_string,labelpad=0,y=1.05,rotation=0,size=20)

  # Save off figure
  #plt.show()
  if ADDPTS:
     plt.savefig('GDF_UFS.png')
  else:
    plt.savefig('GDF_UFS.png',bbox_inches='tight',pad_inches=0.25)

  # Cleanup
  del(gs_gdf,fig_gdf)

# Panels go 1,2,3,4 top to bottom
def plot_gdf_cat(gdf_data):

  # Use gridspec
  gs_gdf = gridspec.GridSpec(nrows=4,ncols=1,height_ratios=[1,1,1,1],hspace=0.20,wspace=0.0)

  # New Figure
  fig_gdf = plt.figure(1,figsize=(20,15))

  # Coordinate reference system
  crs_gdf = ccrs.PlateCarree(central_longitude=180.0)

  ####### PANEL 1
  ax1 = plt.subplot(gs_gdf[0,0],projection=crs_gdf)
  setup_axis(ax1)
  ax1.set_title('(a) Hits (Forecast Yes/Observation Yes)',loc=PANELTITLELOC)
  levels = [0.0,0.05,0.1,0.2,0.3,0.4,0.5,0.8,1.1,1.4]

  # create an axis on the bottom of ax. The width of cax will be 5%
  # of ax and the padding between cax and ax will be fixed at 0.35 inch.
  # since cartopy uses a geo_axes, we need to specify the axes_class for the append_axes method
  # Use this axis for the colorbar
  axdiv1 = make_axes_locatable(ax1)
  cbax1 = axdiv1.append_axes("bottom", size="5%", pad=0.35, axes_class=plt.Axes)

  # Contour the data
  con1 = gdf_data['FYOY_DENS'].where(gdf_data['FYOY_DENS']>0.0).plot.pcolormesh(ax=ax1,transform=ccrs.PlateCarree(),levels=levels,cmap=plt.cm.Reds,cbar_kwargs={'cax':cbax1,'ax':ax1,'orientation':'horizontal'},extend='max',add_labels=False)

  # Add scatter points if requested
  if ADDPTS:
    scat1 = ax1.scatter(alons,alats,transform=ccrs.PlateCarree(),s=1,c='cyan')

  # Add the colorbar and set the tickmarks on it
  cbar1 = con1.colorbar
  cbar1.set_ticks(levels)

  ######## PANEL 2
  ax2 = plt.subplot(gs_gdf[1,0],projection=crs_gdf)
  setup_axis(ax2)
  ax2.set_title('(b) Early Hits',loc=PANELTITLELOC)
  levels = levels

  # create an axis on the bottom of ax. The width of cax will be 5%
  # of ax and the padding between cax and ax will be fixed at 0.35 inch.
  # since cartopy uses a geo_axes, we need to specify the axes_class for the append_axes method
  # Use this axis for the colorbar
  axdiv2 = make_axes_locatable(ax2)
  cbax2 = axdiv2.append_axes("bottom", size="5%", pad=0.35, axes_class=plt.Axes)

  # Contour the data
  con2 = gdf_data['EHIT_DENS'].where(gdf_data['EHIT_DENS']>0.0).plot.pcolormesh(ax=ax2,transform=ccrs.PlateCarree(),levels=levels,cmap=plt.cm.Reds,cbar_kwargs={'cax':cbax2,'ax':ax2,'orientation':'horizontal'},extend='max',add_labels=False)

  # Add scatter points if requested
  if ADDPTS:
    scat2 = ax2.scatter(hlon,hlat,transform=ccrs.PlateCarree(),s=1,c='cyan')

  # Add the colorbar and set the tickmarks on it
  cbar2 = con2.colorbar
  cbar2.set_ticks(levels)

  ######## PANEL 3
  ax3 = plt.subplot(gs_gdf[2,0],projection=crs_gdf)
  setup_axis(ax3)
  ax3.set_title('(c) Late Hits',loc=PANELTITLELOC)
  levels = levels

  # create an axis on the bottom of ax. The width of cax will be 5%
  # of ax and the padding between cax and ax will be fixed at 0.35 inch.
  # since cartopy uses a geo_axes, we need to specify the axes_class for the append_axes method
  # Use this axis for the colorbar
  axdiv3 = make_axes_locatable(ax3)
  cbax3 = axdiv3.append_axes("bottom", size="5%", pad=0.35, axes_class=plt.Axes)

  # Contour the data
  con3 = gdf_data['LHIT_DENS'].where(gdf_data['LHIT_DENS']>0.0).plot.pcolormesh(ax=ax3,transform=ccrs.PlateCarree(),levels=levels,cmap=plt.cm.Reds,cbar_kwargs={'cax':cbax3,'ax':ax3,'orientation':'horizontal'},extend='max',add_labels=False)

  # Add scatter points if requested
  if ADDPTS:
    scat3 = ax3.scatter(flon,flat,transform=ccrs.PlateCarree(),s=1,c='cyan')

  # Add the colorbar and set the tickmarks on it
  cbar3 = con3.colorbar
  cbar3.set_ticks(levels)

  ######## PANEL 4
  #tot_xr = hit_xr+fam_xr
  ax4 = plt.subplot(gs_gdf[3,0],projection=crs_gdf)
  setup_axis(ax4)
  ax4.set_title('(d) False Alarms (Forecast Yes/Observation No)',loc=PANELTITLELOC)
  levels = levels

  # create an axes on the bottom of ax. The width of cax will be 5%
  # of ax and the padding between cax and ax will be fixed at 0.35 inch.
  # since cartopy uses a geo_axes, we need to specify the axes_class for the append_axes method
  # Use this axis for the colorbar
  axdiv4 = make_axes_locatable(ax4)
  cbax4 = axdiv4.append_axes("bottom", size="5%", pad=0.35, axes_class=plt.Axes)

  # Contour the data
  con4 = gdf_data['FYON_DENS'].where(gdf_data['FYON_DENS']>0.0).plot.pcolormesh(ax=ax4,transform=ccrs.PlateCarree(),levels=levels,cmap=plt.cm.Reds,cbar_kwargs={'cax':cbax4,'ax':ax4,'orientation':'horizontal'},extend='max',add_labels=False)

  # Add scatter points if requested
  if ADDPTS:
    scat4 = ax4.scatter(flon,flat,transform=ccrs.PlateCarree(),s=1,c='cyan')

  # Add the colorbar and set the tickmarks on it
  # Since this is the bottom panel also add a title
  cbar4 = con4.colorbar
  cbar4.set_ticks(levels)
  cbar4.set_label(count_string,labelpad=0,y=1.05,rotation=0,size=20)

  # Save off figure
  #plt.show()
  if ADDPTS:
     plt.savefig('GDF_CAT.png')
  else:
    plt.savefig('GDF_CAT.png',bbox_inches='tight',pad_inches=0.25)

  # Cleanup
  del(gs_gdf,fig_gdf)

# Panels go 1,2,3,4 top to bottom
def plot_tdf(tdf_data):

  # Use gridspec
  gs_tdf = gridspec.GridSpec(nrows=4,ncols=1,height_ratios=[1,1,1,1],hspace=0.20,wspace=0.0)

  # New Figure
  fig_tdf = plt.figure(1,figsize=(20,15))

  # Coordinate reference system
  crs_tdf = ccrs.PlateCarree(central_longitude=180.0)

  ####### PANEL 1
  ax1 = plt.subplot(gs_tdf[0,0],projection=crs_tdf)
  setup_axis(ax1)
  ax1.set_title('(a) BEST Genesis Track Density',loc=PANELTITLELOC)
  levels = [3.0,6.0,9.0,12.0,15.0,18.0,21.0,24.0]

  # create an axis on the bottom of ax. The width of cax will be 5%
  # of ax and the padding between cax and ax will be fixed at 0.35 inch.
  # since cartopy uses a geo_axes, we need to specify the axes_class for the append_axes method
  # Use this axis for the colorbar
  axdiv1 = make_axes_locatable(ax1)
  cbax1 = axdiv1.append_axes("bottom", size="5%", pad=0.35, axes_class=plt.Axes)

  # Contour the data
  con1 = tdf_data['OTRK_DENS'].where(tdf_data['OTRK_DENS']>0.0).plot.pcolormesh(ax=ax1,transform=ccrs.PlateCarree(),levels=levels,cmap=plt.cm.Reds,cbar_kwargs={'cax':cbax1,'ax':ax1,'orientation':'horizontal'},extend='max',add_labels=False)

  # Add scatter points if requested
  if ADDPTS:
    scat1 = ax1.scatter(alons,alats,transform=ccrs.PlateCarree(),s=1,c='cyan')

  # Add the colorbar and set the tickmarks on it
  cbar1 = con1.colorbar
  cbar1.set_ticks(levels)

  ######## PANEL 2
  ax2 = plt.subplot(gs_tdf[1,0],projection=crs_tdf)
  setup_axis(ax2)
  ax2.set_title(f'(b) Forecast Genesis Track Density ({LEAD_WINDOW_STR}h)',loc=PANELTITLELOC)
  levels = levels

  # create an axis on the bottom of ax. The width of cax will be 5%
  # of ax and the padding between cax and ax will be fixed at 0.35 inch.
  # since cartopy uses a geo_axes, we need to specify the axes_class for the append_axes method
  # Use this axis for the colorbar
  axdiv2 = make_axes_locatable(ax2)
  cbax2 = axdiv2.append_axes("bottom", size="5%", pad=0.35, axes_class=plt.Axes)

  # Contour the data
  con2 = tdf_data['FTRK_DENS'].where(tdf_data['FTRK_DENS']>0.0).plot.pcolormesh(ax=ax2,transform=ccrs.PlateCarree(),levels=levels,cmap=plt.cm.Reds,cbar_kwargs={'cax':cbax2,'ax':ax2,'orientation':'horizontal'},extend='max',add_labels=False)

  # Add scatter points if requested
  if ADDPTS:
    scat2 = ax2.scatter(hlon,hlat,transform=ccrs.PlateCarree(),s=1,c='cyan')

  # Add the colorbar and set the tickmarks on it
  cbar2 = con2.colorbar
  cbar2.set_ticks(levels)

  ######## PANEL 3
  fminuso = tdf_data['FTRK_DENS']-tdf_data['OTRK_DENS']
  ax3 = plt.subplot(gs_tdf[2,0],projection=crs_tdf)
  setup_axis(ax3)
  ax3.set_title('(c) (b) minus (a)',loc=PANELTITLELOC)
  levels = [-11.0,-9.0,-7.0,-5.0,-3.0,-1.0,1.0,3.0,5.0,7.0,9.0]
  
  # create an axis on the bottom of ax. The width of cax will be 5%
  # of ax and the padding between cax and ax will be fixed at 0.35 inch.
  # since cartopy uses a geo_axes, we need to specify the axes_class for the append_axes method
  # Use this axis for the colorbar
  axdiv3 = make_axes_locatable(ax3)
  cbax3 = axdiv3.append_axes("bottom", size="5%", pad=0.35, axes_class=plt.Axes)

  # Contour the data
  con3 = fminuso.where((fminuso>1.0) | (fminuso<-1.0)).plot.pcolormesh(ax=ax3,transform=ccrs.PlateCarree(),levels=levels,cmap=plt.cm.coolwarm,cbar_kwargs={'cax':cbax3,'ax':ax3,'orientation':'horizontal'},extend='both',add_labels=False)

  # Add scatter points if requested
  if ADDPTS:
    scat3 = ax3.scatter(flon,flat,transform=ccrs.PlateCarree(),s=1,c='cyan')

  # Add the colorbar and set the tickmarks on it
  cbar3 = con3.colorbar
  cbar3.set_ticks(levels)
  cbar3.set_label(days_string,labelpad=0,y=1.05,rotation=0,size=20)

  ######## PANEL 4
  ax4 = plt.subplot(gs_tdf[3,0],projection=crs_tdf)
  ax4.axis('off') 

  # Save off figure
  #plt.show()
  if ADDPTS:
     plt.savefig('TDF.png')
  else:
    plt.savefig('TDF.png',bbox_inches='tight',pad_inches=0.25)

  # Cleanup
  del(gs_tdf,fig_tdf)
