# ============================*
 # ** Copyright UCAR (c) 2022
 # ** University Corporation for Atmospheric Research (UCAR)
 # ** National Center for Atmospheric Research (NCAR)
 # ** Research Applications Lab (RAL)
 # ** P.O.Box 3000, Boulder, Colorado, 80307-3000, USA
 # ============================*
 
 
 
#!/bin/env python
"""
Hank Fisher
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import norm
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import xarray as xr
import pandas as pd
from pyproj import Geod
import pyresample as pyr
from datetime import datetime, date
import PIL 
from PIL import Image
import io
import os, sys
import subprocess
import logging
import yaml


# something pandas needs
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()

"""
Import BasePlot class
"""
from plots.base_plot import BasePlot
#from ..base_plot import BasePlot


class PolarPlot(BasePlot):


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
    
    #--------------------------------------------------------
    def plot_polar(imageDir,hemisphere,
                  lon,lat,plot_data,plot_name):
        
        cmap='nipy_spectral'
    
        print('processing',hemisphere+'ern hemisphere')
        if hemisphere == 'north':
            crs=ccrs.NorthPolarStereo(central_longitude=-168.)
            bounding_lat=30.98
        else:
            crs=ccrs.SouthPolarStereo(central_longitude=-60.)
            bounding_lat=-39.23
    
        # separate the images by date
        if not os.path.isdir(imageDir):
            print("Making image directory "+imageDir)
            os.makedirs(imageDir)
    
        # trim to polar regions
        if hemisphere == 'north':
            plot_data=plot_data.where((plot_data.lat>=bounding_lat),drop=True) 
        else:
            plot_data=plot_data.where((plot_data.lat<=bounding_lat),drop=True) 
    
        lon,lat=np.meshgrid(lon,lat)  # shift from 1-d to 2-d arrays
        rice=obs_ice.to_masked_array()
    
        # pretty pictures
        print('plotting %s '%plot_name)
        plt.figure(dpi=150)
        ax=plt.axes(projection=crs)
        plt.pcolormesh(rlon,rlat,rice,cmap=cmap,
                       transform=ccrs.PlateCarree(),
                       vmin=0,vmax=1.0)
        plt.tick_params(labelsize='x-small')
        ax.add_feature(cfeature.LAND,zorder=1)
        ax.coastlines(zorder=1)
        ax.gridlines()
        cb=plt.colorbar()
        cb.ax.tick_params(labelsize='x-small')
    
        plt.title(plot_name,fontsize='small')
        print("Saving image to "+imageDir)
        saveImage(imageDir+'/'+plot_name+'.png',dpi=150)
        plt.close()
        
        return
