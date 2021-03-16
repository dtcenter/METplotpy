#!/usr/bin/env python

import xarray as xr
import cartopy.crs as ccrs
import cartopy.feature as cfeat
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.gridspec as gridspec

# Stuff for making the colorbar height not extend past the plot box
from mpl_toolkits.axes_grid1 import make_axes_locatable

# For lat/lon grid lines
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
from cartopy.mpl.ticker import LongitudeFormatter, LatitudeFormatter

# For drawing polylines
import matplotlib.patches as patches
from matplotlib.path import Path

# Config options
ADDPTS = True
FCSTLEAD = 96

# Use gridspec
gs = gridspec.GridSpec(nrows=4,ncols=1,height_ratios=[1,1,1,1],hspace=0.20,wspace=0.0)

# New Figure
fig = plt.figure(1,figsize=(20,15))

# Coordinate reference system
crs = ccrs.PlateCarree(central_longitude=180.0)

#gl = ax.gridlines(crs=ccrs.PlateCarree(), draw_labels=True,
#                  linewidth=0.5, color='gray', alpha=0.4, linestyle='-')
#gl.xlabels_top = True
#gl.ylabels_left = True
#gl.xlines = True
#gl.ylines = True
#gl.xlocator = mticker.FixedLocator([0,30,60,90,120,150,180,-30,-60,-90,-120,-150,-180])
#gl.xformatter = LONGITUDE_FORMATTER
#gl.yformatter = LATITUDE_FORMATTER
#gl.xlabel_style = {'size': 15, 'color': 'gray'}
#gl.ylabel_style = {'size': 15, 'color': 'gray'}

# Function for common axis params
def setup_axis(ax):
    ax.coastlines(resolution='50m',color='black')
    #ax.set_global()
    #ax.set_extent([0,359,-40,40],crs=ccrs.PlateCarree())
    ax.set_ylim([-40,40])
    #ax.set_xticks([0, 60, 120, 180, 240, 300, 360], crs=ccrs.PlateCarree())
    ax.set_xticks([45, 90, 135, 180, 225, 270, 315], minor=False, crs=ccrs.PlateCarree())
    #ax.set_yticks([-90, -60, -30, 0, 30, 60, 90], crs=ccrs.PlateCarree())
    #ax.set_yticks([-45 -30, -15, 0, 15, 30, 45], crs=ccrs.PlateCarree())
    ax.set_yticks([-40, -30, -15, 0, 15, 30, 40], minor=False, crs=ccrs.PlateCarree())
    ax.xaxis.set_major_formatter(LongitudeFormatter(zero_direction_label=True))
    ax.yaxis.set_major_formatter(LatitudeFormatter())
    ax.tick_params(axis="x", bottom=True, top=False, labelbottom=True, labeltop=False)
    ax.tick_params(axis="y", left=True, right=True, labelleft=True, labelright=True)
    ax.set_ylabel('')
    ax.set_xlabel('')
    #ax.add_feature(cfeat.STATES.with_scale('50m'))
    #ax.set_extent([0.0,359.0,-45.0,45.0],crs=ccrs.PlateCarree())

def setup_gridlines(ax):
    ax.set_ylim([-40,40])
    ax.set_xticks(list(range(0,370,10)),minor=False,crs=ccrs.PlateCarree())
    ax.set_yticks(list(range(-40,50,10)),minor=False,crs=ccrs.PlateCarree())
    ax.xaxis.set_major_formatter(LongitudeFormatter(zero_direction_label=True))
    ax.yaxis.set_major_formatter(LatitudeFormatter())
    ax.tick_params(axis="x", bottom=False, top=False, labelbottom=False, labeltop=False,grid_color='b')
    ax.tick_params(axis="y", left=False, right=False, labelleft=False, labelright=False,grid_color='b')
    ax.set_ylabel('')
    ax.set_xlabel('')

def draw_grid(ax):
  lat_fwd = list(range(-40,50,10))
  lat_rev = list(range(50,-40,-10))
  lon_fwd = list(range(0,370,10))
  lon_rev = list(range(370,0,-10))
  lon_cnt = 0
  lat_cnt = 0
  codes = [Path.MOVETO,Path.LINETO,Path.CLOSEPOLY]
  # DRAW LAT LINES FIRST
  print("LATITUDE")
  while lat_cnt < len(lat_fwd):
    while lon_cnt < len(lon_fwd):
      verts = [(float(lon_fwd[lon_cnt]),float(lat_fwd[lat_cnt])),(float(lon_rev[lon_cnt]),float(lat_fwd[lat_cnt])),(float(lon_rev[lon_cnt]),float(lat_fwd[lat_cnt]))]
      #print(verts)
      path = Path(verts,codes)
      patch = patches.PathPatch(path, lw=0.5, transform=ccrs.PlateCarree())
      ax.add_patch(patch)
      lon_cnt = lon_cnt + 1
    lon_cnt = 0
    lat_cnt = lat_cnt + 1
  lon_cnt = 0
  lat_cnt = 0
  # NOW DRAW LON LINES
  print("LONGITUDE")
  while lon_cnt < len(lon_fwd):
    while lat_cnt < len(lat_fwd):
      verts = [(float(lon_fwd[lon_cnt]),float(lat_fwd[lat_cnt])),(float(lon_fwd[lon_cnt]),float(lat_rev[lat_cnt])),(float(lon_fwd[lon_cnt]),float(lat_rev[lat_cnt]))]
      print(verts)
      path = Path(verts,codes)
      patch = patches.PathPatch(path, lw=0.5, transform=ccrs.PlateCarree(), color='lightgray')
      ax.add_patch(patch)
      lat_cnt = lat_cnt + 1
    lat_cnt = 0
    lon_cnt = lon_cnt + 1

# TOP PANEL
ax1 = plt.subplot(gs[0,0],projection=crs)
setup_axis(ax1)
ax1.set_title('(a) BEST N=%04d' % (int(len(alons))),loc='left')
#levels = [0.5,1.5,2.5,3.5]
levels = list(range(0,41,5))
# create an axes on the right side of ax. The width of cax will be 5%
# of ax and the padding between cax and ax will be fixed at 0.05 inch.
# since cartopy uses a geo_axes, we need to specify the axes_class for the append_axes method
axdiv1 = make_axes_locatable(ax1)
#cbax = axdiv.append_axes("right", size="5%", pad=0.1, axes_class=plt.Axes)
cbax1 = axdiv1.append_axes("bottom", size="5%", pad=0.35, axes_class=plt.Axes)
con1 = anly_xr.where(anly_xr>0.0).plot.pcolormesh(ax=ax1,transform=ccrs.PlateCarree(),levels=levels,cmap=plt.cm.Oranges,cbar_kwargs={'cax':cbax1,'ax':ax1,'orientation':'horizontal'},extend='max',add_labels=False)
if ADDPTS:
  scat1 = ax1.scatter(alons,alats,transform=ccrs.PlateCarree(),s=1,c='cyan')
cbar1 = con1.colorbar
# Set tickmark locations for colorbar
cbar1.set_ticks(list(range(0,41,5)))
#cbar1.set_ticklabels([1,2,3,4])
#cbar1.set_label('TC Genesis 10 deg -1 yr -1 (2017-2018)', labelpad=0, y=1.05, rotation=0, size=20)

#ax1 = plt.subplot(gs[0,0],projection=crs)
#setup_axis(ax1)
#ax1.set_title('(a) Hits',loc='left')
#levels = [0.5,1.5,2.5,3.5]
#levels = [0,1,2,3,4,5]
# create an axes on the right side of ax. The width of cax will be 5%
# of ax and the padding between cax and ax will be fixed at 0.05 inch.
# since cartopy uses a geo_axes, we need to specify the axes_class for the append_axes method
#axdiv1 = make_axes_locatable(ax1)
#cbax = axdiv.append_axes("right", size="5%", pad=0.1, axes_class=plt.Axes)
#cbax1 = axdiv1.append_axes("bottom", size="5%", pad=0.35, axes_class=plt.Axes)
#con1 = hit_xr.where(hit_xr>0.0).plot.pcolormesh(ax=ax1,transform=ccrs.PlateCarree(),levels=levels,cmap=plt.cm.Oranges,cbar_kwargs={'cax':cbax1,'ax':ax1,'orientation':'horizontal'},extend='max',add_labels=False)
#cbar1 = con1.colorbar
# Set tickmark locations for colorbar
#cbar1.set_ticks([0,1,2,3,4])
#cbar1.set_ticklabels([1,2,3,4])
#cbar1.set_label('TC Genesis 10 deg -1 yr -1 (2017-2018)', labelpad=0, y=1.05, rotation=0, size=20)

# SECOND PANEL
ax2 = plt.subplot(gs[1,0],projection=crs)
setup_axis(ax2)
ax2.set_title(F'(a) Hits (FV3-GFS {FCSTLEAD}h lead) N=%04d' % (int(len(hlon))),loc='left')
#levels = [0.5,1.5,2.5,3.5]
#levels = [0.5,1.5,2.5,3.5,4.5,5.5,6.5,7.5,8.5,9.5]
levels = levels
# create an axes on the right side of ax. The width of cax will be 5%
# of ax and the padding between cax and ax will be fixed at 0.05 inch.
# since cartopy uses a geo_axes, we need to specify the axes_class for the append_axes method
axdiv2 = make_axes_locatable(ax2)
#cbax = axdiv.append_axes("right", size="5%", pad=0.1, axes_class=plt.Axes)
cbax2 = axdiv2.append_axes("bottom", size="5%", pad=0.35, axes_class=plt.Axes)
con2 = hit_xr.where(hit_xr>0.0).plot.pcolormesh(ax=ax2,transform=ccrs.PlateCarree(),levels=levels,cmap=plt.cm.Oranges,cbar_kwargs={'cax':cbax2,'ax':ax2,'orientation':'horizontal'},extend='max',add_labels=False)
if ADDPTS:
  scat2 = ax2.scatter(hlon,hlat,transform=ccrs.PlateCarree(),s=1,c='cyan')
cbar2 = con2.colorbar
# Set tickmark locations for colorbar
cbar2.set_ticks(list(range(0,41,5)))
#cbar1.set_ticklabels([1,2,3,4])
#cbar1.set_label('TC Genesis 10 deg -1 yr -1 (2017-2018)', labelpad=0, y=1.05, rotation=0, size=20)

#ax2 = plt.subplot(gs[1,0],projection=crs)
#setup_axis(ax2)
#ax2.set_title('(b) Early TCGs',loc='left')
#levels = levels
# create an axes on the right side of ax. The width of cax will be 5%
# of ax and the padding between cax and ax will be fixed at 0.05 inch.
# since cartopy uses a geo_axes, we need to specify the axes_class for the append_axes method
#axdiv2 = make_axes_locatable(ax2)
#cbax = axdiv.append_axes("right", size="5%", pad=0.1, axes_class=plt.Axes)
#cbax2 = axdiv2.append_axes("bottom", size="5%", pad=0.35, axes_class=plt.Axes)
#con2 = ear_xr.where(ear_xr>0.0).plot.pcolormesh(ax=ax2,transform=ccrs.PlateCarree(),levels=levels,cmap=plt.cm.Oranges,cbar_kwargs={'cax':cbax2,'ax':ax2,'orientation':'horizontal'},extend='max',add_labels=False)
#cbar2 = con2.colorbar
# Set tickmark locations for colorbar
#cbar2.set_ticks([0,1,2,3,4])
#cbar2.set_ticklabels([1,2,3,4])
#cbar2.set_label('TC Genesis 10 deg -1 yr -1 (2017-2018)', labelpad=0, y=1.05, rotation=0, size=20)

# THIRD PANEL
ax3 = plt.subplot(gs[2,0],projection=crs)
setup_axis(ax3)
ax3.set_title(F'(c) False TCGs (FV3-GFS {FCSTLEAD}h lead) N=%04d' % (int(len(flon))),loc='left')
levels = levels
# create an axes on the right side of ax. The width of cax will be 5%
# of ax and the padding between cax and ax will be fixed at 0.05 inch.
# since cartopy uses a geo_axes, we need to specify the axes_class for the append_axes method
axdiv3 = make_axes_locatable(ax3)
#cbax = axdiv.append_axes("right", size="5%", pad=0.1, axes_class=plt.Axes)
cbax3 = axdiv3.append_axes("bottom", size="5%", pad=0.35, axes_class=plt.Axes)
con3 = fam_xr.where(fam_xr>0.0).plot.pcolormesh(ax=ax3,transform=ccrs.PlateCarree(),levels=levels,cmap=plt.cm.Oranges,cbar_kwargs={'cax':cbax3,'ax':ax3,'orientation':'horizontal'},extend='max',add_labels=False)
if ADDPTS:
  scat3 = ax3.scatter(flon,flat,transform=ccrs.PlateCarree(),s=1,c='cyan')
cbar3 = con3.colorbar
# Set tickmark locations for colorbar
cbar3.set_ticks(list(range(0,41,5)))
#cbar4.set_ticklabels([1,2,3,4])
#cbar3.set_label('TC Genesis 10 deg -1 yr -1 (2015-2018)', labelpad=0, y=1.05, rotation=0, size=20)

#ax3 = plt.subplot(gs[2,0],projection=crs)
#setup_axis(ax3)
#ax3.set_title('(c) Late TCGs',loc='left')
#levels = levels
# create an axes on the right side of ax. The width of cax will be 5%
# of ax and the padding between cax and ax will be fixed at 0.05 inch.
# since cartopy uses a geo_axes, we need to specify the axes_class for the append_axes method
#axdiv3 = make_axes_locatable(ax3)
#cbax = axdiv.append_axes("right", size="5%", pad=0.1, axes_class=plt.Axes)
#cbax3 = axdiv3.append_axes("bottom", size="5%", pad=0.35, axes_class=plt.Axes)
#con3 = lat_xr.where(lat_xr>0.0).plot.pcolormesh(ax=ax3,transform=ccrs.PlateCarree(),levels=levels,cmap=plt.cm.Oranges,cbar_kwargs={'cax':cbax3,'ax':ax3,'orientation':'horizontal'},extend='max',add_labels=False)
#cbar3 = con3.colorbar
# Set tickmark locations for colorbar
#cbar3.set_ticks([0,1,2,3,4])
#cbar3.set_ticklabels([1,2,3,4])
#cbar3.set_label('TC Genesis 10 deg -1 yr -1 (2017-2018)', labelpad=0, y=1.05, rotation=0, size=20)

# FOURTH PANEL
tot_xr = hit_xr+fam_xr
ax4 = plt.subplot(gs[3,0],projection=crs)
setup_axis(ax4)
ax4.set_title(F'(d) Hit + False TCGs (FV3-GFS {FCSTLEAD}h lead) N=%04d' % (int(len(flon)+len(hlon))),loc='left')
levels = levels
# create an axes on the right side of ax. The width of cax will be 5%
# of ax and the padding between cax and ax will be fixed at 0.05 inch.
# since cartopy uses a geo_axes, we need to specify the axes_class for the append_axes method
axdiv4 = make_axes_locatable(ax4)
#cbax = axdiv.append_axes("right", size="5%", pad=0.1, axes_class=plt.Axes)
cbax4 = axdiv4.append_axes("bottom", size="5%", pad=0.35, axes_class=plt.Axes)
con4 = tot_xr.where(tot_xr>0.0).plot.pcolormesh(ax=ax4,transform=ccrs.PlateCarree(),levels=levels,cmap=plt.cm.Oranges,cbar_kwargs={'cax':cbax4,'ax':ax4,'orientation':'horizontal'},extend='max',add_labels=False)
if ADDPTS:
  scat4 = ax4.scatter(flon,flat,transform=ccrs.PlateCarree(),s=1,c='cyan')
cbar4 = con4.colorbar
# Set tickmark locations for colorbar
cbar4.set_ticks(list(range(0,41,5)))
#cbar4.set_ticklabels([1,2,3,4])
cbar4.set_label('TC Genesis 10 deg -1 yr -1 (2015-2018)', labelpad=0, y=1.05, rotation=0, size=20)

# Save off figure
#plt.show()
if ADDPTS:
  plt.savefig(F'gdf_cat_ufs_{FCSTLEAD}h_pts.png',bbox_inches='tight',pad_inches=0.25)
else:
  plt.savefig(F'gdf_cat_ufs_{FCSTLEAD}h.png',bbox_inches='tight',pad_inches=0.25)

