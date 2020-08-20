#!/usr/bin/python

###################################################################################
#These series of functions are designed to load all of the necessary data for the
#WPC ERO verification.
#
#Created by MJE. 20170515.
###################################################################################

import pygrib
import sys
import subprocess
import string
import gzip
import time
import os
import numpy as np
import datetime
import time
import math
from mpl_toolkits.basemap import Basemap, cm
import matplotlib as mpl
mpl.use('Agg') #So plots can be saved in cron
import matplotlib.pyplot as plt
from matplotlib.mlab import griddata
from matplotlib.path import Path
from scipy.io import netcdf
from scipy.ndimage.filters import gaussian_filter
from netCDF4 import Dataset
from scipy import ndimage
from scipy import interpolate

##################################################################################
#readCONUSmask reads an ASCII CONUS mask originally created in MATLAB, along with
#the latitude-longitude grid coordinates, and interpolates the data to a new grid. 
#MJE. 20170517.
#
#Update of domain subsettting added 20170612 and 20170619. MJE.
#
#####################INPUT FILES FOR readCONUSmask#############################
# GRIB_PATH     = directory where data is stored
# latlon_dims   = latitude/longitude dimensions for plotting [WLON,SLAT,ELON,NLAT]
# grid_delta    = grid resolution increment for interpolation (degrees lat/lon)
####################OUTPUT FILES FOR setupData#############################
# CONUSmask     = data containing the CONUSmask (0 = not CONUS) 
# lat_new       = latitude corresponding to CONUS data
# lon_new       = longitude corresponding to CONUS data
###################################################################################

def readCONUSmask(GRIB_PATH,latlon_dims,grid_delta):
    
    #Error if specified lat/lon dims are outside CONUS (-129.8 to -60.2 W and 20.2 to 49.8 N)
    if latlon_dims[0] < -129.8 or latlon_dims[2] > -60.2 or latlon_dims[1] < 20.2 or latlon_dims[3] > 49.8:
        raise ValueError('User Specified lat/lon outside of boundary')

    lat_count = 0  
    fobj = open(GRIB_PATH+'/ERO/static/CONUS_lat.txt', 'r')
    for line in fobj:
        if lat_count == 0:
            lat = map(float,line.split())
        else:
            lat = np.vstack((lat,map(float,line.split())))
        lat_count += 1
        
    lon_count = 0  
    fobj = open(GRIB_PATH+'/ERO/static/CONUS_lon.txt', 'r')
    for line in fobj:
        if lon_count == 0:
            lon = map(float,line.split())
        else:
            lon = np.vstack((lon,map(float,line.split())))
        lon_count += 1
        
    mask_count = 0  
    fobj = open(GRIB_PATH+'/ERO/static/CONUSmask.txt', 'r')
    for line in fobj:
        if mask_count == 0:
            CONUSmask = map(float,line.split())
        else:
            CONUSmask = np.vstack((CONUSmask,map(float,line.split())))
        mask_count += 1
    
    #Create new grid from user specified boundaries and resolution
    [lon_new,lat_new] = np.meshgrid(np.linspace(latlon_dims[0],latlon_dims[2],np.round((latlon_dims[2]-latlon_dims[0])/grid_delta,2)+1), \
        np.linspace(latlon_dims[3],latlon_dims[1],np.round((latlon_dims[3]-latlon_dims[1])/grid_delta,2)+1))
        
    #Interpolate delx and dely from static grid to user specified grid
    CONUSmask = interpolate.griddata(np.stack((lon.flatten(),lat.flatten()),axis=1),CONUSmask.flatten(),(lon_new,lat_new))
    
    #If grid_delta = 0.09, load a make-shift mask that filters out excessive coastal ST4>FFG regions
    if grid_delta == 0.09:
        f         = Dataset('/usr1/wpc_cpgffh/gribs/ERO_verif/static/ST4gFFG_s2017072212_e2017082212_vhr12.nc', "a", format="NETCDF4")
        temp      = (np.array(f.variables['ST4gFFG'][:])<=0.20)*1
        lat       = np.array(f.variables['lat'][:])*1
        lon       = np.array(f.variables['lon'][:])*1
        lat       = np.tile(lat,(len(lon),1)).T
        lon       = np.tile(lon,(len(lat),1))
        f.close()
        
        temp      = interpolate.griddata(np.stack((lon.flatten(),lat.flatten()),axis=1),temp.flatten(),(lon_new,lat_new))
        
        CONUSmask = CONUSmask * temp
     
    return(CONUSmask,lat_new,lon_new)

##################################################################################
#createEROInterField reads in the static elevation del interpolation field created 
#in MATLAB that is used to extend unclosed ERO contours further offshore. This code
#then interpolates the del_x and del_y fields to the user specified grid, which is
#used in readERO. MJE. 20170619.
#
#####################INPUT FILES FOR createEROInterField##########################
# GRIB_PATH     = directory where data is stored
# latlon_dims   = latitude/longitude dimensions for plotting [WLON,SLAT,ELON,NLAT]
# grid_delta    = grid resolution increment for interpolation (degrees lat/lon)
####################OUTPUT FILES FOR setupData#############################
# Fy            = del y elevation grid interpolated to user specifications (read into readERO)
# Fx            = del x elevation grid interpolated to user specifications (read into readERO)
# lat           = latitude corresponding to CONUS data
# lon           = longitude corresponding to CONUS data
##################################################################################

def createEROInterField(GRIB_PATH,latlon_dims,grid_delta):
    
    ##LOAD AN INVERTED DEL FUNCTION OF CONUS TO EXTEND OPEN ERO CONTOURS AWAY FROM THE MAINLAND######
    delx_count = 0  
    fobj = open(GRIB_PATH+'ERO/static/CONUS_delx.txt', 'r')
    for line in fobj:
        if delx_count == 0:
            delx = map(float,line.split())
        else:
            delx = np.vstack((delx,map(float,line.split())))
        delx_count += 1
    
    dely = []
    dely_count = 0  
    fobj = open(GRIB_PATH+'ERO/static/CONUS_dely.txt', 'r')
    for line in fobj:
        if dely_count == 0:
            dely = map(float,line.split())
        else:
            dely = np.vstack((dely,map(float,line.split())))
        dely_count += 1
        
    lat = []
    lat_count = 0  
    fobj = open(GRIB_PATH+'ERO/static/CONUS_lat.txt', 'r')
    for line in fobj:
        if lat_count == 0:
            lat = map(float,line.split())
        else:
            lat = np.vstack((lat,map(float,line.split())))
        lat_count += 1
        
    lon = []
    lon_count = 0  
    fobj = open(GRIB_PATH+'ERO/static/CONUS_lon.txt', 'r')
    for line in fobj:
        if lon_count == 0:
            lon = map(float,line.split())
        else:
            lon = np.vstack((lon,map(float,line.split())))
        lon_count += 1  

    #Create new grid from user specified boundaries and resolution
    [lon_new,lat_new] = np.meshgrid(np.linspace(latlon_dims[0],latlon_dims[2],np.round((latlon_dims[2]-latlon_dims[0])/grid_delta,2)+1), \
        np.linspace(latlon_dims[3],latlon_dims[1],np.round((latlon_dims[3]-latlon_dims[1])/grid_delta,2)+1))
        
    #Interpolate delx and dely from static grid to user specified grid
    delx = interpolate.griddata(np.stack((lon.flatten(),lat.flatten()),axis=1),delx.flatten(),(lon_new,lat_new))
    dely = interpolate.griddata(np.stack((lon.flatten(),lat.flatten()),axis=1),dely.flatten(),(lon_new,lat_new))

    #Create interpolation field once for ERO forecast points
    Fx = interpolate.interp2d(lon_new[0,:], lat_new[:,0], delx, kind='cubic')
    Fy = interpolate.interp2d(lon_new[0,:], lat_new[:,0], dely, kind='cubic')
        
    return(Fy,Fx,lat_new,lon_new)
        
##################################################################################
#readERO reads in days 1 - 3 WPC EROs. Specifically the ERO for MRGL, SLGT,
#MDT, and HIGH are output as an ASCII list and a boolean grid for each contour,
#individually. Can also subset the domain.
#
#Note that the original code attempted to group all objects with the same group
#number, but different objects can share the same group number (EX: 15 UTC 20160804)
#and the same object can share different group numbers (EX: 15 UTC 20160805). Hence,
#the header between contours, rather than the group numbers, are used to separate 
#objects.
#
#Originally coded in MATLAB.        MJE. 20170307-20170322.
#Adapted to python and streamlined. MJE. 20170515-20170619.
#
#####################INPUT FILES FOR setupData#############################
# GRIB_PATH     = directory where ERO data is stored
# latlon_dims   = latitude/longitude dimensions for plotting [WLON,SLAT,ELON,NLAT]
# grid_delta    = grid resolution increment for interpolation (degrees lat/lon)
# datetime_ERO  = datetime element
# inithr        = a number; hour to be loaded
# validday      = valid day for ERO (number; 1,2 or 3)
# Fx            = del x elevation grid interpolated to user specifications (created in createEROInterField)
# Fy            = del y elevation grid interpolated to user specifications (created in createEROInterField)
####################OUTPUT FILES FOR setupData#############################
# MRGL          = ERO lat/lon list of MRGL points
# ero_MRGL      = ERO MRGL data in gridded form (0 = not MRGL, 1 = MRGL)
# SLGT          = ERO lat/lon list of SLGT points
# ero_SLGT      = ERO SLGT data in gridded form (0 = not SLGT, 1 = SLGT)
# MDT           = ERO lat/lon list of MDT points
# ero_MDT       = ERO MDT data in gridded form  (0 = not MDT,  1 = MDT)
# HIGH         	= ERO lat/lon list of HIGH points
# ero_HIGH      = ERO HIGH data in gridded form (0 = not HIGH, 1 = HIGH)
###################################################################################

def readERO(GRIB_PATH,latlon_dims,grid_delta,datetime_ERO,inithr,validday,Fx,Fy):

##################COMMENT OUT WHEN IN FUNCTION MODE#################################
#inithr        = 9
#grid_delta    = 0.1
#GRIB_PATH     = '/usr1/wpc_cpgffh/gribs/ERO/' 
#datetime_ERO  = datetime.datetime(2017, 6, 17, 12, 0)
#validday      = 1
####################################################################################

    #Error if specified lat/lon dims are outside CONUS (-129.8 to -60.2 W and 20.2 to 49.8 N)
    if latlon_dims[0] < -129.8 or latlon_dims[2] > -60.2 or latlon_dims[1] < 20.2 or latlon_dims[3] > 49.8:
        raise ValueError('User Specified lat/lon outside of boundary')
        
    #Convert datetime to a string
    yrmonday = ''.join(['{:04d}'.format(datetime_ERO.year),'{:02d}'.format(datetime_ERO.month), \
        '{:02d}'.format(datetime_ERO.day)])
        
    #Convert inithr to a string
    inithr = '{:02d}'.format(int(inithr))
           
    #Create grid from user specifications
    [lon,lat] = np.meshgrid(np.linspace(latlon_dims[0],latlon_dims[2],np.round((latlon_dims[2]-latlon_dims[0])/grid_delta,2)+1), \
        np.linspace(latlon_dims[3],latlon_dims[1],np.round((latlon_dims[3]-latlon_dims[1])/grid_delta,2)+1))
        
    ###############INITIALIZE AND SET UP VARIABLES PROPERLY############################
    MRGL       = [[] for i in range(0,40)]
    MRGL_meta  = [[] for i in range(0,40)]
    MRGL_count = 0
    SLGT       = [[] for i in range(0,40)]
    SLGT_meta  = [[] for i in range(0,40)]
    SLGT_count = 0
    MDT        = [[] for i in range(0,40)]
    MDT_meta   = [[] for i in range(0,40)]
    MDT_count = 0
    HIGH       = [[] for i in range(0,40)]
    HIGH_meta  = [[] for i in range(0,40)]
    HIGH_count = 0

    #Load proper valid ERO day
    if validday == 1:
        day_str = '94e'
    elif validday == 2:
        day_str = '98e' 
    elif validday == 3:
        day_str = '99e'
    
    #Proper syntax for loading data
    filename = GRIB_PATH+yrmonday+'/'+day_str+'_'+yrmonday+inithr+'.txt'
    
    #########LOAD THE ERO DATA AND SEPARATE EACH CONTOUR############################
    
    #Attempt to load the data
    try:
        file = gzip.open(filename+'.gz', 'rb')
        line_content = file.readline()
        
        while line_content:  #Iterate through file     
            
            #Read in metadata describing group number and closed/not closed
            if 'CLOSED' in line_content:
                meta = [float(line_content[line_content.find('CLOSED')+7]), float(line_content[line_content.find('GRPNUM')+7])]
                
                #Read in next line to determine MRGL, SLGT, MDT, or HIGH
                line_content = file.readline()
    
            #Find and archive marginal content
            if 'MRGL' in line_content:
                
                #Skip the header
                line_content = file.readline()
                
                #Read data in line by line 
                for line_content in file:
    
                    #Determine if we are at the end of the file
                    if 'VG_TYPE' not in line_content:
                        if len(MRGL[MRGL_count]) == 0:
                            MRGL[MRGL_count]      = [float(line_content[0:6]),float(line_content[6:14])]
                            MRGL_meta[MRGL_count] = meta
                        else:
                            MRGL[MRGL_count]      = np.vstack((MRGL[MRGL_count], [float(line_content[0:6]),float(line_content[6:14])]))
                    else:
                        MRGL_count += 1
                        break
            elif 'SLGT' in line_content:
                
                #Skip the header
                line_content = file.readline()
                
                #Read data in line by line 
                for line_content in file:
    
                    #Determine if we are at the end of the file
                    if 'VG_TYPE' not in line_content:
                        if len(SLGT[SLGT_count]) == 0:
                            SLGT[SLGT_count]      = [float(line_content[0:6]),float(line_content[6:14])]
                            SLGT_meta[SLGT_count] = meta
                        else:
                            SLGT[SLGT_count]      = np.vstack((SLGT[SLGT_count], [float(line_content[0:6]),float(line_content[6:14])]))
                    else:
                        SLGT_count += 1
                        break
            elif 'MDT' in line_content:
                
                #Skip the header
                line_content = file.readline()
                
                #Read data in line by line 
                for line_content in file:
    
                    #Determine if we are at the end of the file
                    if 'VG_TYPE' not in line_content:
                        if len(MDT[MDT_count]) == 0:
                            MDT[MDT_count]      = [float(line_content[0:6]),float(line_content[6:14])]
                            MDT_meta[MDT_count] = meta
                        else:
                            MDT[MDT_count]      = np.vstack((MDT[MDT_count], [float(line_content[0:6]),float(line_content[6:14])]))
                    else:
                        MDT_count += 1
                        break
            elif 'HIGH' in line_content:
                
                #Skip the header
                line_content = file.readline()
                
                #Read data in line by line 
                for line_content in file:
    
                    #Determine if we are at the end of the file
                    if 'VG_TYPE' not in line_content:
                        if len(HIGH[HIGH_count]) == 0:
                            HIGH[HIGH_count]      = [float(line_content[0:6]),float(line_content[6:14])]
                            HIGH_meta[HIGH_count] = meta
                        else:
                            HIGH[HIGH_count]      = np.vstack((HIGH[HIGH_count], [float(line_content[0:6]),float(line_content[6:14])]))
                    else:
                        HIGH_count += 1
                        break
            else:
                line_content = file.readline()
        print('Day '+str(validday)+' ERO File Loaded - Issued on '+yrmonday+' at '+inithr+' UTC')

        #Remove empty categories
        MRGL      = [i for i in MRGL if len(i) != 0]
        SLGT      = [i for i in SLGT if len(i) != 0]
        MDT       = [i for i in MDT  if len(i) != 0]
        HIGH      = [i for i in HIGH if len(i) != 0]   
        MRGL_meta = [i for i in MRGL_meta if len(i) != 0]
        SLGT_meta = [i for i in SLGT_meta if len(i) != 0]
        MDT_meta  = [i for i in MDT_meta  if len(i) != 0]
        HIGH_meta = [i for i in HIGH_meta if len(i) != 0]   
        
        #######APPLY DEL FUNCTION WHEN APPLICABLE, CREATE 2D POLYGON GRID MASK FROM ARRAY OF ERO CATEGORIES##########
        #Initialize needed matrices
        ero_MRGL = np.zeros((lat.shape))
        ero_SLGT = np.zeros((lat.shape))
        ero_MDT  = np.zeros((lat.shape))
        ero_HIGH = np.zeros((lat.shape))
        
        #Loop through each category, create a gridded version to compare to obs   
        if len(MRGL) > 0:
            for ca in range(0,len(MRGL)):
                if len(MRGL[ca]) > 2: #Need more than 2 points to form a shape
                    
                    #If ERO not closed, use del CONUS grid to determine direction to extend objects off the coast (eliminate missing gaps)
                    if MRGL_meta[ca][0] == 0:
                        
                        #Use the interpolate function to interpolate to specific points
                        vector_x = [Fx(MRGL[ca][0,1],MRGL[ca][0,0]),Fx(MRGL[ca][-1,1],MRGL[ca][-1,0])]
                        vector_y = [Fy(MRGL[ca][0,1],MRGL[ca][0,0]),Fy(MRGL[ca][-1,1],MRGL[ca][-1,0])]
                        
                        #Given del function, construct temporary array 
                        MRGL_lat_temp = np.concatenate((MRGL[ca][0,0]+vector_y[0],MRGL[ca][:,0],MRGL[ca][-1,0]+vector_y[1]),axis=0)
                        MRGL_lon_temp = np.concatenate(([MRGL[ca][0,1]+vector_x[0], MRGL[ca][:,1], MRGL[ca][-1,1]+vector_x[1]]),axis=0)
                        
                        #Finally, given the polygon, interpolate to binomial grid shape
                        path = Path(np.vstack((MRGL_lon_temp,MRGL_lat_temp)).T)
                        grid = path.contains_points(np.vstack((lon.flatten(),lat.flatten())).T)
                        grid = grid.reshape(lon.shape)
                        ero_MRGL = ero_MRGL + grid
                        
                    else:
                            
                        #Given the polygon, interpolate to binomial grid shape
                        path = Path(np.vstack((MRGL[ca][:,1],MRGL[ca][:,0])).T)
                        grid = path.contains_points(np.vstack((lon.flatten(),lat.flatten())).T)
                        grid = grid.reshape(lon.shape)
                        ero_MRGL = ero_MRGL + grid
        
        if len(SLGT) > 0:
            for ca in range(0,len(SLGT)):
                if len(SLGT[0]) > 2: #Need more than 2 points to form a shape
                    
                    #If ERO not closed, use del CONUS grid to determine direction to extend objects off the coast (eliminate missing gaps)
                    if SLGT_meta[ca][0] == 0:
                        
                        #Use the interpolate function to interpolate to specific points
                        vector_x = [Fx(SLGT[ca][0,1],SLGT[ca][0,0]),Fx(SLGT[ca][-1,1],SLGT[ca][-1,0])]
                        vector_y = [Fy(SLGT[ca][0,1],SLGT[ca][0,0]),Fy(SLGT[ca][-1,1],SLGT[ca][-1,0])]
                        
                        #Given del function, construct temporary array 
                        SLGT_lat_temp = np.concatenate((SLGT[ca][0,0]+vector_y[0],SLGT[ca][:,0],SLGT[ca][-1,0]+vector_y[1]),axis=0)
                        SLGT_lon_temp = np.concatenate(([SLGT[ca][0,1]+vector_x[0], SLGT[ca][:,1], SLGT[ca][-1,1]+vector_x[1]]),axis=0)
                        
                        #Finally, given the polygon, interpolate to binomial grid shape
                        path = Path(np.vstack((SLGT_lon_temp,SLGT_lat_temp)).T)
                        grid = path.contains_points(np.vstack((lon.flatten(),lat.flatten())).T)
                        grid = grid.reshape(lon.shape)
                        ero_SLGT = ero_SLGT + grid
                        
                    else:
                            
                        #Given the polygon, interpolate to binomial grid shape
                        path = Path(np.vstack((SLGT[ca][:,1],SLGT[ca][:,0])).T)
                        grid = path.contains_points(np.vstack((lon.flatten(),lat.flatten())).T)
                        grid = grid.reshape(lon.shape)
                        ero_SLGT = ero_SLGT + grid
                        
        if len(MDT) > 0:
            for ca in range(0,len(MDT)):
                if len(MDT[0]) > 2: #Need more than 2 points to form a shape
                    
                    #If ERO not closed, use del CONUS grid to determine direction to extend objects off the coast (eliminate missing gaps)
                    if MDT_meta[ca][0] == 0:
                        
                        #Use the interpolate function to interpolate to specific points
                        vector_x = [Fx(MDT[ca][0,1],MDT[ca][0,0]),Fx(MDT[ca][-1,1],MDT[ca][-1,0])]
                        vector_y = [Fy(MDT[ca][0,1],MDT[ca][0,0]),Fy(MDT[ca][-1,1],MDT[ca][-1,0])]
                        
                        #Given del function, construct temporary array 
                        MDT_lat_temp = np.concatenate((MDT[ca][0,0]+vector_y[0],MDT[ca][:,0],MDT[ca][-1,0]+vector_y[1]),axis=0)
                        MDT_lon_temp = np.concatenate(([MDT[ca][0,1]+vector_x[0], MDT[ca][:,1], MDT[ca][-1,1]+vector_x[1]]),axis=0)
                        
                        #Finally, given the polygon, interpolate to binomial grid shape
                        path = Path(np.vstack((MDT_lon_temp,MDT_lat_temp)).T)
                        grid = path.contains_points(np.vstack((lon.flatten(),lat.flatten())).T)
                        grid = grid.reshape(lon.shape)
                        ero_MDT = ero_MDT + grid
                        
                    else:
                            
                        #Given the polygon, interpolate to binomial grid shape
                        path = Path(np.vstack((MDT[ca][:,1],MDT[ca][:,0])).T)
                        grid = path.contains_points(np.vstack((lon.flatten(),lat.flatten())).T)
                        grid = grid.reshape(lon.shape)
                        ero_MDT = ero_MDT + grid
        
        if len(HIGH) > 0:
            for ca in range(0,len(HIGH)):
                if len(HIGH[0]) > 2: #Need more than 2 points to form a shape
                    
                    #If ERO not closed, use del CONUS grid to determine direction to extend objects off the coast (eliminate missing gaps)
                    if HIGH_meta[ca][0] == 0:
                        
                        #Use the interpolate function to interpolate to specific points
                        vector_x = [Fx(HIGH[ca][0,1],HIGH[ca][0,0]),Fx(HIGH[ca][-1,1],HIGH[ca][-1,0])]
                        vector_y = [Fy(HIGH[ca][0,1],HIGH[ca][0,0]),Fy(HIGH[ca][-1,1],HIGH[ca][-1,0])]
                        
                        #Given del function, construct temporary array 
                        HIGH_lat_temp = np.concatenate((HIGH[ca][0,0]+vector_y[0],HIGH[ca][:,0],HIGH[ca][-1,0]+vector_y[1]),axis=0)
                        HIGH_lon_temp = np.concatenate(([HIGH[ca][0,1]+vector_x[0], HIGH[ca][:,1], HIGH[ca][-1,1]+vector_x[1]]),axis=0)
                        
                        #Finally, given the polygon, interpolate to binomial grid shape
                        path = Path(np.vstack((HIGH_lon_temp,HIGH_lat_temp)).T)
                        grid = path.contains_points(np.vstack((lon.flatten(),lat.flatten())).T)
                        grid = grid.reshape(lon.shape)
                        ero_HIGH = ero_HIGH + grid
                        
                    else:
                            
                        #Given the polygon, interpolate to binomial grid shape
                        path = Path(np.vstack((HIGH[ca][:,1],HIGH[ca][:,0])).T)
                        grid = path.contains_points(np.vstack((lon.flatten(),lat.flatten())).T)
                        grid = grid.reshape(lon.shape)
                        ero_HIGH = ero_HIGH + grid

        #Round the lat/lon data to eliminate roundoff errors
        lat=np.round(lat,2)
        lon=np.round(lon,2)
             
    except IOError or OSError:
        
        MRGL     = np.NaN
        ero_MRGL = np.NaN
        SLGT     = np.NaN
        ero_SLGT = np.NaN
        MDT      = np.NaN
        ero_MDT  = np.NaN
        HIGH     = np.NaN
        ero_HIGH = np.NaN
        
        print('Day '+str(validday)+' ERO File Not Found - Issued on '+yrmonday+' at '+inithr+' UTC')
                    
    return(MRGL,ero_MRGL,SLGT,ero_SLGT,MDT,ero_MDT,HIGH,ero_HIGH)

#########################################################################################
#portWPCQPF uses Bruce V's script to simultaneously convert the 6-hr GEMPAK WPC QPF 
#forecast data to 24-hour GRIB2 data. This only needs to run once. MJE. 20180301.
#
#####################INPUT FILES FOR portWPCQPF###########################################
#DATA_PATH      = Location of permanent model GRIB files
#datetime_wpc   = datetime element of data to be coverted
#validday       = valid hour (number) to be read in
#####################OUTPUT FILES FOR portWPCQPF#############################
#
#########################################################################################

def portWPCQPF(DATA_PATH,datetime_wpc,validday):

    ###################COMMENT OUT WHEN IN FUNCTION MODE#################################
    #DATA_PATH     = '/usr1/wpc_cpgffh/gribs/' 
    #datetime_wpc  = datetime.datetime(2017, 7, 19, 12, 0)
    #validday      = 3 
    #####################################################################################

    #Change directories so Bruce's function works
    os.chdir(DATA_PATH+'WPCQPF/')
    
    #Create datetime element for day being loaded 
    yrmonday_wpc = '{:04d}'.format(datetime_wpc.year)+'{:02d}'.format(datetime_wpc.month)+'{:02d}'.format(datetime_wpc.day)
    
    #Save the data in 6 hour increments
    for fcst_hr in range((24 * validday)-18,(24 * validday)+6,6):
        
        #Define the forecast projection in hours
        fcst_hr_str = '{:03d}'.format(fcst_hr)
        
        #Define filename
        filename = yrmonday_wpc+'12_f'+fcst_hr_str+'_wpcqpf.grb2'
        
        #Remove older files
        subprocess.call('rm -rf '+filename+'*',stdout=open(os.devnull, 'wb'), \
            stderr=open(os.devnull, 'wb'),shell=True)
            
        #Convert 6-hour GEMPAK to 24-hour grib2
        subprocess.call('/export/hpc-lw-dtbdev5/merickson/code/gempak/prep_qpf /export-2/hpcnfs/data/hpcqpf/5km/p06i_YYYYMMDDHHfFFF.grd '+ \
            yrmonday_wpc+'12 '+fcst_hr_str+' p06i ./'+filename+' -format grib2 -grid 2p5km',stdout=open(os.devnull, 'wb'), \
            stderr=open(os.devnull, 'wb'), shell=True)
        
        #Gunzip the files
        subprocess.call('gzip '+DATA_PATH+'WPCQPF/'+filename,stdout=open(os.devnull, 'wb'), \
            stderr=open(os.devnull, 'wb'),shell=True)
        
    return()

##################################################################################
#readffair2017ERO reads in days 1 - 3 WPC Experimental EROs issued during FFAIR. 
#Specifically the ERO for MRGL, SLGT, MDT, and HIGH are output as an ASCII 
#list and a boolean grid for each contour, individually. Can also subset the domain.
#
#Adapted from readERO. MJE. 20170803.
#
#####################INPUT FILES FOR readffair2017ERO#############################
# GRIB_PATH     = directory where ERO data is stored
# latlon_dims   = latitude/longitude dimensions for plotting [WLON,SLAT,ELON,NLAT]
# grid_delta    = grid resolution increment for interpolation (degrees lat/lon)
# datetime_ERO  = datetime element
# inithr        = a number; hour to be loaded
# validday      = valid day for ERO (number; 1,2 or 3)
# Fx            = del x elevation grid interpolated to user specifications (created in createEROInterField)
# Fy            = del y elevation grid interpolated to user specifications (created in createEROInterField)
####################OUTPUT FILES FOR setupData#############################
# MRGL          = ERO lat/lon list of MRGL points
# ero_MRGL      = ERO MRGL data in gridded form (0 = not MRGL, 1 = MRGL)
# SLGT          = ERO lat/lon list of SLGT points
# ero_SLGT      = ERO SLGT data in gridded form (0 = not SLGT, 1 = SLGT)
# MDT           = ERO lat/lon list of MDT points
# ero_MDT       = ERO MDT data in gridded form  (0 = not MDT,  1 = MDT)
# HIGH         	= ERO lat/lon list of HIGH points
# ero_HIGH      = ERO HIGH data in gridded form (0 = not HIGH, 1 = HIGH)
###################################################################################
        
def readffair2017ERO(GRIB_PATH,latlon_dims,grid_delta,datetime_ERO,inithr,validday,Fx,Fy):

##################COMMENT OUT WHEN IN FUNCTION MODE#################################
#inithr        = 12
#grid_delta    = 0.1
#GRIB_PATH     = '/usr1/wpc_cpgffh/gribs/ERO/FFAIR_2017/' 
#datetime_ERO  = datetime.datetime(2017, 6, 22, 12, 0)
#validday      = 2
####################################################################################

    #Error if specified lat/lon dims are outside CONUS (-129.8 to -60.2 W and 20.2 to 49.8 N)
    if latlon_dims[0] < -129.8 or latlon_dims[2] > -60.2 or latlon_dims[1] < 20.2 or latlon_dims[3] > 49.8:
        raise ValueError('User Specified lat/lon outside of boundary')
        
    #Convert datetime to a string
    yrmonday = ''.join(['{:04d}'.format(datetime_ERO.year),'{:02d}'.format(datetime_ERO.month), \
        '{:02d}'.format(datetime_ERO.day)])
        
    #Convert inithr to a string
    inithr = '{:02d}'.format(int(inithr))
           
    #Create grid from user specifications
    [lon,lat] = np.meshgrid(np.linspace(latlon_dims[0],latlon_dims[2],np.round((latlon_dims[2]-latlon_dims[0])/grid_delta,2)+1), \
        np.linspace(latlon_dims[3],latlon_dims[1],np.round((latlon_dims[3]-latlon_dims[1])/grid_delta,2)+1))
        
    ###############INITIALIZE AND SET UP VARIABLES PROPERLY############################
    MRGL       = [[] for i in range(0,40)]
    MRGL_meta  = [[] for i in range(0,40)]
    MRGL_count = 0
    SLGT       = [[] for i in range(0,40)]
    SLGT_meta  = [[] for i in range(0,40)]
    SLGT_count = 0
    MDT        = [[] for i in range(0,40)]
    MDT_meta   = [[] for i in range(0,40)]
    MDT_count = 0
    HIGH       = [[] for i in range(0,40)]
    HIGH_meta  = [[] for i in range(0,40)]
    HIGH_count = 0
    
    #Proper syntax for loading data
    filename = GRIB_PATH+'/ffair_ero'+str(int(validday))+'_'+yrmonday+'12f0'+str(int(24*(validday)))+'.txt'
    
    #########LOAD THE ERO DATA AND SEPARATE EACH CONTOUR############################
    
    #Attempt to load the data
    try:
    
        file = gzip.open(filename+'.gz', 'rb')
        line_content = file.readline()
        
        while line_content:  #Iterate through file     
  
            #Read in metadata describing group number and closed/not closed
            if 'CLOSED' in line_content:
                meta = [float(line_content[line_content.find('CLOSED')+7]), float(line_content[line_content.find('GRPNUM')+7])]
                
                #Read in next line to determine MRGL, SLGT, MDT, or HIGH
                line_content = file.readline()
    
            #Find and archive marginal content
            if '<GROUPED TEXT>5' in line_content and '<GROUPED TEXT>50' not in line_content:
                
                #Skip the header
                line_content = file.readline()
                
                #Read data in line by line 
                for line_content in file:
    
                    #Determine if we are at the end of the file
                    if 'VG_TYPE' not in line_content:
                        if len(MRGL[MRGL_count]) == 0:
                            MRGL[MRGL_count]      = [float(line_content[0:6]),float(line_content[6:14])]
                            MRGL_meta[MRGL_count] = meta
                        else:
                            MRGL[MRGL_count]      = np.vstack((MRGL[MRGL_count], [float(line_content[0:6]),float(line_content[6:14])]))
                    else:
                        MRGL_count += 1
                        break
            elif '<GROUPED TEXT>15' in line_content:
                
                #Skip the header
                line_content = file.readline()
                
                #Read data in line by line 
                for line_content in file:
    
                    #Determine if we are at the end of the file
                    if 'VG_TYPE' not in line_content:
                        if len(SLGT[SLGT_count]) == 0:
                            SLGT[SLGT_count]      = [float(line_content[0:6]),float(line_content[6:14])]
                            SLGT_meta[SLGT_count] = meta
                        else:
                            SLGT[SLGT_count]      = np.vstack((SLGT[SLGT_count], [float(line_content[0:6]),float(line_content[6:14])]))
                    else:
                        SLGT_count += 1
                        break
            elif '<GROUPED TEXT>30' in line_content:
                
                #Skip the header
                line_content = file.readline()
                
                #Read data in line by line 
                for line_content in file:
    
                    #Determine if we are at the end of the file
                    if 'VG_TYPE' not in line_content:
                        if len(MDT[MDT_count]) == 0:
                            MDT[MDT_count]      = [float(line_content[0:6]),float(line_content[6:14])]
                            MDT_meta[MDT_count] = meta
                        else:
                            MDT[MDT_count]      = np.vstack((MDT[MDT_count], [float(line_content[0:6]),float(line_content[6:14])]))
                    else:
                        MDT_count += 1
                        break
            elif '<GROUPED TEXT>50' in line_content:
                
                #Skip the header
                line_content = file.readline()
                
                #Read data in line by line 
                for line_content in file:
    
                    #Determine if we are at the end of the file
                    if 'VG_TYPE' not in line_content:
                        if len(HIGH[HIGH_count]) == 0:
                            HIGH[HIGH_count]      = [float(line_content[0:6]),float(line_content[6:14])]
                            HIGH_meta[HIGH_count] = meta
                        else:
                            HIGH[HIGH_count]      = np.vstack((HIGH[HIGH_count], [float(line_content[0:6]),float(line_content[6:14])]))
                    else:
                        HIGH_count += 1
                        break
            else:
                line_content = file.readline()
        print('Day '+str(validday)+' ERO File Loaded - Issused on '+yrmonday+' at '+inithr+' UTC')

        #Remove empty categories
        MRGL      = [i for i in MRGL if len(i) != 0]
        SLGT      = [i for i in SLGT if len(i) != 0]
        MDT       = [i for i in MDT  if len(i) != 0]
        HIGH      = [i for i in HIGH if len(i) != 0]   
        MRGL_meta = [i for i in MRGL_meta if len(i) != 0]
        SLGT_meta = [i for i in SLGT_meta if len(i) != 0]
        MDT_meta  = [i for i in MDT_meta  if len(i) != 0]
        HIGH_meta = [i for i in HIGH_meta if len(i) != 0]   
        
        #######APPLY DEL FUNCTION WHEN APPLICABLE, CREATE 2D POLYGON GRID MASK FROM ARRAY OF ERO CATEGORIES##########
        #Initialize needed matrices
        ero_MRGL = np.zeros((lat.shape))
        ero_SLGT = np.zeros((lat.shape))
        ero_MDT  = np.zeros((lat.shape))
        ero_HIGH = np.zeros((lat.shape))
        
        #Loop through each category, create a gridded version to compare to obs   
        if len(MRGL) > 0:
            for ca in range(0,len(MRGL)):
                if len(MRGL[ca]) > 2: #Need more than 2 points to form a shape
                    
                    #If ERO not closed, use del CONUS grid to determine direction to extend objects off the coast (eliminate missing gaps)
                    if MRGL_meta[ca][0] == 0:
                        
                        #Use the interpolate function to interpolate to specific points
                        vector_x = [Fx(MRGL[ca][0,1],MRGL[ca][0,0]),Fx(MRGL[ca][-1,1],MRGL[ca][-1,0])]
                        vector_y = [Fy(MRGL[ca][0,1],MRGL[ca][0,0]),Fy(MRGL[ca][-1,1],MRGL[ca][-1,0])]
                        
                        #Given del function, construct temporary array 
                        MRGL_lat_temp = np.concatenate((MRGL[ca][0,0]+vector_y[0],MRGL[ca][:,0],MRGL[ca][-1,0]+vector_y[1]),axis=0)
                        MRGL_lon_temp = np.concatenate(([MRGL[ca][0,1]+vector_x[0], MRGL[ca][:,1], MRGL[ca][-1,1]+vector_x[1]]),axis=0)
                        
                        #Finally, given the polygon, interpolate to binomial grid shape
                        path = Path(np.vstack((MRGL_lon_temp,MRGL_lat_temp)).T)
                        grid = path.contains_points(np.vstack((lon.flatten(),lat.flatten())).T)
                        grid = grid.reshape(lon.shape)
                        ero_MRGL = ero_MRGL + grid
                        
                    else:
                            
                        #Given the polygon, interpolate to binomial grid shape
                        path = Path(np.vstack((MRGL[ca][:,1],MRGL[ca][:,0])).T)
                        grid = path.contains_points(np.vstack((lon.flatten(),lat.flatten())).T)
                        grid = grid.reshape(lon.shape)
                        ero_MRGL = ero_MRGL + grid
        
        if len(SLGT) > 0:
            for ca in range(0,len(SLGT)):
                if len(SLGT[0]) > 2: #Need more than 2 points to form a shape
                    
                    #If ERO not closed, use del CONUS grid to determine direction to extend objects off the coast (eliminate missing gaps)
                    if SLGT_meta[ca][0] == 0:
                        
                        #Use the interpolate function to interpolate to specific points
                        vector_x = [Fx(SLGT[ca][0,1],SLGT[ca][0,0]),Fx(SLGT[ca][-1,1],SLGT[ca][-1,0])]
                        vector_y = [Fy(SLGT[ca][0,1],SLGT[ca][0,0]),Fy(SLGT[ca][-1,1],SLGT[ca][-1,0])]
                        
                        #Given del function, construct temporary array 
                        SLGT_lat_temp = np.concatenate((SLGT[ca][0,0]+vector_y[0],SLGT[ca][:,0],SLGT[ca][-1,0]+vector_y[1]),axis=0)
                        SLGT_lon_temp = np.concatenate(([SLGT[ca][0,1]+vector_x[0], SLGT[ca][:,1], SLGT[ca][-1,1]+vector_x[1]]),axis=0)
                        
                        #Finally, given the polygon, interpolate to binomial grid shape
                        path = Path(np.vstack((SLGT_lon_temp,SLGT_lat_temp)).T)
                        grid = path.contains_points(np.vstack((lon.flatten(),lat.flatten())).T)
                        grid = grid.reshape(lon.shape)
                        ero_SLGT = ero_SLGT + grid
                        
                    else:
                            
                        #Given the polygon, interpolate to binomial grid shape
                        path = Path(np.vstack((SLGT[ca][:,1],SLGT[ca][:,0])).T)
                        grid = path.contains_points(np.vstack((lon.flatten(),lat.flatten())).T)
                        grid = grid.reshape(lon.shape)
                        ero_SLGT = ero_SLGT + grid
                        
        if len(MDT) > 0:
            for ca in range(0,len(MDT)):
                if len(MDT[0]) > 2: #Need more than 2 points to form a shape
                    
                    #If ERO not closed, use del CONUS grid to determine direction to extend objects off the coast (eliminate missing gaps)
                    if MDT_meta[ca][0] == 0:
                        
                        #Use the interpolate function to interpolate to specific points
                        vector_x = [Fx(MDT[ca][0,1],MDT[ca][0,0]),Fx(MDT[ca][-1,1],MDT[ca][-1,0])]
                        vector_y = [Fy(MDT[ca][0,1],MDT[ca][0,0]),Fy(MDT[ca][-1,1],MDT[ca][-1,0])]
                        
                        #Given del function, construct temporary array 
                        MDT_lat_temp = np.concatenate((MDT[ca][0,0]+vector_y[0],MDT[ca][:,0],MDT[ca][-1,0]+vector_y[1]),axis=0)
                        MDT_lon_temp = np.concatenate(([MDT[ca][0,1]+vector_x[0], MDT[ca][:,1], MDT[ca][-1,1]+vector_x[1]]),axis=0)
                        
                        #Finally, given the polygon, interpolate to binomial grid shape
                        path = Path(np.vstack((MDT_lon_temp,MDT_lat_temp)).T)
                        grid = path.contains_points(np.vstack((lon.flatten(),lat.flatten())).T)
                        grid = grid.reshape(lon.shape)
                        ero_MDT = ero_MDT + grid
                        
                    else:
                            
                        #Given the polygon, interpolate to binomial grid shape
                        path = Path(np.vstack((MDT[ca][:,1],MDT[ca][:,0])).T)
                        grid = path.contains_points(np.vstack((lon.flatten(),lat.flatten())).T)
                        grid = grid.reshape(lon.shape)
                        ero_MDT = ero_MDT + grid
        
        if len(HIGH) > 0:
            for ca in range(0,len(HIGH)):
                if len(HIGH[0]) > 2: #Need more than 2 points to form a shape
                    
                    #If ERO not closed, use del CONUS grid to determine direction to extend objects off the coast (eliminate missing gaps)
                    if HIGH_meta[ca][0] == 0:
                        
                        #Use the interpolate function to interpolate to specific points
                        vector_x = [Fx(HIGH[ca][0,1],HIGH[ca][0,0]),Fx(HIGH[ca][-1,1],HIGH[ca][-1,0])]
                        vector_y = [Fy(HIGH[ca][0,1],HIGH[ca][0,0]),Fy(HIGH[ca][-1,1],HIGH[ca][-1,0])]
                        
                        #Given del function, construct temporary array 
                        HIGH_lat_temp = np.concatenate((HIGH[ca][0,0]+vector_y[0],HIGH[ca][:,0],HIGH[ca][-1,0]+vector_y[1]),axis=0)
                        HIGH_lon_temp = np.concatenate(([HIGH[ca][0,1]+vector_x[0], HIGH[ca][:,1], HIGH[ca][-1,1]+vector_x[1]]),axis=0)
                        
                        #Finally, given the polygon, interpolate to binomial grid shape
                        path = Path(np.vstack((HIGH_lon_temp,HIGH_lat_temp)).T)
                        grid = path.contains_points(np.vstack((lon.flatten(),lat.flatten())).T)
                        grid = grid.reshape(lon.shape)
                        ero_HIGH = ero_HIGH + grid
                        
                    else:
                            
                        #Given the polygon, interpolate to binomial grid shape
                        path = Path(np.vstack((HIGH[ca][:,1],HIGH[ca][:,0])).T)
                        grid = path.contains_points(np.vstack((lon.flatten(),lat.flatten())).T)
                        grid = grid.reshape(lon.shape)
                        ero_HIGH = ero_HIGH + grid

        #Round the lat/lon data to eliminate roundoff errors
        lat=np.round(lat,2)
        lon=np.round(lon,2)
             
    except IOError or OSError:
        
        MRGL     = np.NaN
        ero_MRGL = np.NaN
        SLGT     = np.NaN
        ero_SLGT = np.NaN
        MDT      = np.NaN
        ero_MDT  = np.NaN
        HIGH     = np.NaN
        ero_HIGH = np.NaN
        
        print('Day '+str(validday)+' ERO File Not Found - Issused on '+yrmonday+' at '+inithr+' UTC')
                    
    return(MRGL,ero_MRGL,SLGT,ero_SLGT,MDT,ero_MDT,HIGH,ero_HIGH)
               
#########################################################################################
#readST4 reads in the specified ST4 data and uses MET tools to interpolate ST4 data 
#to a common 0.1 degree Lat/Lon grid.  MJE. 20170518-20170613.
#
#####################INPUT FILES FOR setupData###########################################
#MET_PATH       = Directory for MET executibles
#GRIB_PATH      = Directory where ST4 data is stored
#GRIB_PATH_TEMP = Temporary directory where new data is created/transferred
#latlon_dims    = latitude/longitude dimensions for plotting [WLON,SLAT,ELON,NLAT]
#grid_delta     = grid resolution increment for interpolation (degrees lat/lon)
#datetime_ST4   = datetime element
#vhr            = valid hour (number) to be read in
#pre_acc        = accumulation interval (number; 1, 6, or 24 hours)
####################OUTPUT FILES FOR setupData#############################
#lat            = grid of latitude from netcdf MODE output
#lon            = grid of longitude from netcdf MODE output
#ST4            = grid of ST4 values
#########################################################################################

def readST4(MET_PATH,GRIB_PATH,GRIB_PATH_TEMP,latlon_dims,grid_delta,datetime_ST4,vhr,pre_acc):

    ###################COMMENT OUT WHEN IN FUNCTION MODE#################################
    #MET_PATH       = '/opt/MET6/met6.0/bin/' 
    #GRIB_PATH      = '/usr1/wpc_cpgffh/gribs/ST4/' 
    #GRIB_PATH_TEMP = '/usr1/wpc_cpgffh/gribs/temp/ERO_20170608/'
    #datetime_ST4   = datetime.datetime(2016, 8, 13, 12, 0, 0)
    #grid_delta     = 0.1
    #vhr            = 13
    #pre_acc        = 1
    #####################################################################################
    
    #Error if specified lat/lon dims are outside CONUS (-129.8 to -60.2 W and 20.2 to 49.8 N)
    if latlon_dims[0] < -129.8 or latlon_dims[2] > -60.2 or latlon_dims[1] < 20.2 or latlon_dims[3] > 49.8:
        raise ValueError('User Specified lat/lon outside of boundary')
        
    #Convert datetime to julian day
    julday_ST4 = pygrib.datetime_to_julian(datetime_ST4)
    
    #Convert inithr to a string
    vhr = '{:02d}'.format(int(vhr))
        
    #Datetime and proper strings for each hour to be loaded
    datetime_ST4 = pygrib.julian_to_datetime(julday_ST4 + ((float(vhr)+0.01)/24))
    yrmonday_ST4 = '{:04d}'.format(datetime_ST4.year)+'{:02d}'.format(datetime_ST4.month)+\
        '{:02d}'.format(datetime_ST4.day)
    hour_ST4     = '{:02d}'.format(datetime_ST4.hour)

    #Filename for each hour to be loaded
    filename = 'ST4.'+yrmonday_ST4+hour_ST4+'.'+'{:02d}'.format(pre_acc)+'h'

    #Copy the ST4 data to a temporary directory
    output = subprocess.call('cp  '+GRIB_PATH+yrmonday_ST4+'/'+filename+'.gz '+GRIB_PATH_TEMP+filename+'.gz', \
        stdout=open(os.devnull, 'wb'), stderr=open(os.devnull, 'wb'), shell=True)
    
    #Gunzip the data
    output = subprocess.call('gunzip '+GRIB_PATH_TEMP+filename+'.gz', stdout=open(os.devnull, 'wb'), \
        stderr=open(os.devnull, 'wb'), shell=True)

    #Interpolate to a common grid (del function grid) using MET's regrid_data_plane
    xpts = len(np.linspace(latlon_dims[0],latlon_dims[2],np.round((latlon_dims[2]-latlon_dims[0])/grid_delta,2)+1))
    ypts = len(np.linspace(latlon_dims[3],latlon_dims[1],np.round((latlon_dims[3]-latlon_dims[1])/grid_delta,2)+1))
    
    output = subprocess.call(MET_PATH+'regrid_data_plane '+GRIB_PATH_TEMP+filename+ \
        ' \'latlon '+str(xpts)+' '+str(ypts)+' '+str(latlon_dims[1])+' '+str(latlon_dims[0])+ \
        ' '+str(grid_delta)+' '+str(grid_delta)+'\' '+GRIB_PATH_TEMP+filename+'.nc'+ \
        ' -field \'name="APCP"; level="A'+str(pre_acc)+'";\'', stdout=open(os.devnull, 'wb'), \
        stderr=open(os.devnull, 'wb'), shell=True)

    #Load static data file and initialize needed variables for later
    try:
        f   = Dataset(GRIB_PATH_TEMP+filename+'.nc', "a", format="NETCDF4")
        lat = f.variables['lat'][:]
        lon = f.variables['lon'][:]
        #lat = np.linspace(20,50,301)
        #lon = np.linspace(-130,-60,701)
        lon = np.flipud(np.tile(lon,(lat.shape[0],1)))
        lat = np.flipud(np.transpose(np.tile(lat,(lon.shape[1],1))))
        ST4 = np.flipud(f.variables["APCP_"+'{:02d}'.format(int(pre_acc))][:])
        f.close()
        
        #Round the lat/lon data to eliminate roundoff errors
        lat=np.round(lat,2)
        lon=np.round(lon,2)

        ST4[ST4<0] = np.NaN
        
        print('ST4 File Loaded for '+str(int(pre_acc))+' hr Acc. on '+yrmonday_ST4+' at '+hour_ST4+' UTC')
    
    except (IOError):
        
        lat=np.NaN
        lon=np.NaN
        ST4=np.NaN
        
        print('ST4 File Not Found for '+str(int(pre_acc))+' hr Acc. on '+yrmonday_ST4+' at '+hour_ST4+' UTC')
        
    return(lat,lon,ST4)

#########################################################################################
#readFFG reads in the specified FFG data using MET tools and interpolates FFG data 
#to a common grid 0.1 degree LAT/LON grid. MJE. 20170613-20170801.
#
#####################INPUT FILES FOR setupData###########################################
#MET_PATH       = Directory for MET executibles
#GRIB_PATH      = Directory where FFG data is stored
#GRIB_PATH_TEMP = Temporary directory where new data is created/transferred
#latlon_dims    = latitude/longitude dimensions for plotting [WLON,SLAT,ELON,NLAT]
#grid_delta     = grid resolution increment for interpolation (degrees lat/lon)
#datetime_FFG   = datetime element
#vhr            = valid hour (number) to be read in
#pre_acc        = accumulation interval (number; 1, 3, or 6 hours)
####################OUTPUT FILES FOR setupData#############################
#lat            = grid of latitude from netcdf MODE output
#lon            = grid of longitude from netcdf MODE output
#FFG            = grid of FFG values
#########################################################################################

def readFFG(MET_PATH,GRIB_PATH,GRIB_PATH_TEMP,latlon_dims,grid_delta,datetime_FFG,vhr,pre_acc):

    ###################COMMENT OUT WHEN IN FUNCTION MODE#################################
    #MET_PATH       = '/opt/MET6/met6.0/bin/' 
    #GRIB_PATH      = '/usr1/wpc_cpgffh/gribs/FFG/' 
    #GRIB_PATH_TEMP = '/usr1/wpc_cpgffh/gribs//WPCQPF/WPCQPF_verif_day1_ALL/'
    #datetime_FFG   = datetime.datetime(2018, 3, 1, 12, 0)
    #grid_delta     = 0.03
    #vhr            = 12
    #pre_acc        = 6
    #####################################################################################
    
    #Error if specified lat/lon dims are outside CONUS (-129.8 to -60.2 W and 20.2 to 49.8 N)
    if latlon_dims[0] < -129.8 or latlon_dims[2] > -60.2 or latlon_dims[1] < 20.2 or latlon_dims[3] > 49.8:
        raise ValueError('User Specified lat/lon outside of boundary')
        
    #Convert datetime to julian day
    julday_FFG = pygrib.datetime_to_julian(datetime_FFG)
    
    #Convert inithr to a string
    vhr = '{:02d}'.format(int(vhr))
        
    #Datetime and proper strings for each hour to be loaded
    datetime_FFG = pygrib.julian_to_datetime(julday_FFG + ((float(vhr)+0.01)/24))
    yrmonday_FFG = '{:04d}'.format(datetime_FFG.year)+'{:02d}'.format(datetime_FFG.month)+\
        '{:02d}'.format(datetime_FFG.day)
    hour_FFG     = '{:02d}'.format(datetime_FFG.hour)

    #Filename for each hour to be loaded
    filename = yrmonday_FFG+hour_FFG+'_acc'+'{:02d}'.format(pre_acc)+'_ffg.grib2'

    #Copy the WPCQPF data directory
    if not os.path.isdir(GRIB_PATH_TEMP):
        os.mkdir(GRIB_PATH_TEMP)
        
    output = subprocess.call('cp  '+GRIB_PATH+yrmonday_FFG+'/'+filename+'.gz '+GRIB_PATH_TEMP+filename+'.gz', \
        stdout=open(os.devnull, 'wb'), stderr=open(os.devnull, 'wb'), shell=True)
    
    #Gunzip the data
    output = subprocess.call('gunzip '+GRIB_PATH_TEMP+filename+'.gz', stdout=open(os.devnull, 'wb'), \
        stderr=open(os.devnull, 'wb'), shell=True)

    #Interpolate to a common grid (del function grid) using MET's regrid_data_plane
    xpts = len(np.linspace(latlon_dims[0],latlon_dims[2],np.round((latlon_dims[2]-latlon_dims[0])/grid_delta,2)+1))
    ypts = len(np.linspace(latlon_dims[3],latlon_dims[1],np.round((latlon_dims[3]-latlon_dims[1])/grid_delta,2)+1))
        
    output = subprocess.call(MET_PATH+'regrid_data_plane '+GRIB_PATH_TEMP+filename+ \
        ' \'latlon '+str(xpts)+' '+str(ypts)+' '+str(latlon_dims[1])+' '+str(latlon_dims[0])+ \
        ' '+str(grid_delta)+' '+str(grid_delta)+'\' '+GRIB_PATH_TEMP+filename+'.nc'+ \
        ' -field \'name="FFLDG"; level="R1";\'', stdout=open(os.devnull, 'wb'), \
        stderr=open(os.devnull, 'wb'), shell=True)

    #Load static data file and initialize needed variables for later
    try:
        f   = Dataset(GRIB_PATH_TEMP+filename+'.nc', "a", format="NETCDF4")
        lat = f.variables['lat'][:]
        lon = f.variables['lon'][:]
        lon = np.flipud(np.tile(lon,(lat.shape[0],1)))
        lat = np.flipud(np.transpose(np.tile(lat,(lon.shape[1],1))))
        FFG = np.flipud(f.variables["FFLDG_R1"][:])
        f.close()
        
        #Round the lat/lon data to eliminate roundoff errors
        lat=np.round(lat,2)
        lon=np.round(lon,2)

        FFG[FFG<0] = np.NaN
         
        print('FFG File Loaded for '+str(int(pre_acc))+' hr Acc. on '+yrmonday_FFG+' at '+hour_FFG+' UTC')
        
    except (IOError):
        
        lat=np.NaN
        lon=np.NaN
        FFG=np.NaN
        
        print('FFG File Not Found for '+str(int(pre_acc))+' hr Acc. on '+yrmonday_FFG+' at '+hour_FFG+' UTC')
        
    return(lat,lon,FFG)    
                        
#########################################################################################
#readWPCQPF converts the WPC QPF 6-hour GEMPAK data to grib2 using Bruce V's function and
#copies it to /usr1/wpc_cpgffh. This function only needs to be run once. MJE. 20180305.
#
#####################INPUT FILES FOR convertWPCQPF#######################################
#GRIB_PATH       = Directory where WPC QPF data is stored
#datetime_WPCQPF = datetime element
#vhr             = hours forward from datetime_WPCQPF
####################OUTPUT FILES FOR convertWPCQPF#######################################
#
#########################################################################################

def convertWPCQPF(GRIB_PATH,datetime_WPCQPF,hour):

    ###################COMMENT OUT WHEN IN FUNCTION MODE#################################
    #GRIB_PATH       = DATA_PATH 
    #datetime_WPCQPF = datetime_wpc
    #hour            = vhr
    #####################################################################################                                   
    #CD to proper directory
    os.chdir(GRIB_PATH+'WPCQPF/')

    #Change datetime element to a string
    yrmondayhr_wpc = '{:04d}'.format(datetime_WPCQPF.year)+'{:02d}'.format(datetime_WPCQPF.month)+ \
        '{:02d}'.format(datetime_WPCQPF.day)+'{:02d}'.format(datetime_WPCQPF.hour)
        
    #Change datetime element to a julian date
    juldate_wpc = pygrib.datetime_to_julian(datetime_WPCQPF)
    
    #Define the forecast projection in hours
    fcst_hr = '{:03d}'.format(hour)
    #fcst_hr = '{:03d}'.format((24 * (validday - 1) + hour))

    #Define the filename
    filename_sh = yrmondayhr_wpc+'_wpcqpf_f'+fcst_hr
    filename_lo = GRIB_PATH+'WPCQPF/'+filename_sh
    
    #Remove older files
    output = subprocess.call('rm -rf '+filename_lo+'*',stdout=open(os.devnull, 'wb'), \
        stderr=open(os.devnull, 'wb'),shell=True)

    #print '/export/hpc-lw-dtbdev5/merickson/code/gempak/prep_qpf /export-2/hpcnfs/data/hpcqpf/5km/p06i_YYYYMMDDHHfFFF.grd '+ \
    #    yrmondayhr_wpc+' '+fcst_hr+' p06i ./'+filename_sh+'.grb2'+' -format grib2 -grid 2p5km'
    #Convert and gunzip the files
    if juldate_wpc >= pygrib.datetime_to_julian(datetime.datetime(2015, 10, 13, 0, 0)): #5 km WPC QPF grid
        output = subprocess.call('/export/hpc-lw-dtbdev5/merickson/code/gempak/prep_qpf /export-2/hpcnfs/data/hpcqpf/5km/p06i_YYYYMMDDHHfFFF.grd '+ \
            yrmondayhr_wpc+' '+fcst_hr+' p06i ./'+filename_sh+'.grb2'+' -format grib2 -grid 2p5km', stdout=open(os.devnull, 'wb'), \
            stderr=open(os.devnull, 'wb'), shell=True)
        
        if os.path.exists('./'+filename_sh+'.grb2'):
            print('WPC QPF File Converted - Issued on '+fcst_hr+' hr Acc. on '+yrmondayhr_wpc)
        else:
            print('WPC QPF File Not Converted - Issued on '+fcst_hr+' hr Acc. on '+yrmondayhr_wpc)
    else: #20 km WPC QPF grid
        output = subprocess.call('/export/hpc-lw-dtbdev5/merickson/code/gempak/prep_qpf /export-2/hpcnfs/data/hpcqpf/YYYYMMDDHH_hpcqpf.grd '+ \
            yrmondayhr_wpc+' '+fcst_hr+' p06i ./'+filename_sh+'.grb2'+' -format grib2 -grid 2p5km', stdout=open(os.devnull, 'wb'), \
            stderr=open(os.devnull, 'wb'), shell=True)
        
        if os.path.exists('./'+filename_sh+'.grb2'):
            print('WPC QPF File Converted - Issued on '+fcst_hr+' hr Acc. on '+yrmondayhr_wpc)
        else:
            print('WPC QPF File Not Converted - Issued on '+fcst_hr+' hr Acc. on '+yrmondayhr_wpc)
        
    output = subprocess.call('gzip '+filename_lo+'.grb2',stdout=open(os.devnull, 'wb'), \
        stderr=open(os.devnull, 'wb'),shell=True)
               
#########################################################################################
#readWPCQPF reads in the WPC QPF 6-hour GRIB2 data (created from convertWPCQPF) and
#regrids the data to a specified grid using MET tools. MJE. 20180305.
#
#Minor modification to simplify process. MJE. 20180222.
#####################INPUT FILES FOR readWPCQPF#########################################
#MET_PATH        = Directory for MET executibles
#GRIB_PATH       = Directory where WPC QPF data is stored
#GRIB_PATH_EX    = Directory where WPC MET verification is performed
#latlon_dims     = latitude/longitude dimensions for plotting [WLON,SLAT,ELON,NLAT]
#grid_delta      = grid resolution increment for interpolation (degrees lat/lon)
#datetime_WPCQPF = datetime element
#vhr             = hour of forecast
####################OUTPUT FILES FOR readWPCQPF##########################################
#lat             = grid of latitude from netcdf MODE output
#lon             = grid of longitude from netcdf MODE output
#WPCQPF          = grid of WPCQPF data
#########################################################################################

def readWPCQPF(MET_PATH,GRIB_PATH,GRIB_PATH_EX,latlon_dims,grid_delta,datetime_WPCQPF,hour):

    ###################COMMENT OUT WHEN IN FUNCTION MODE#################################
    #GRIB_PATH       = '/usr1/wpc_cpgffh/gribs/WPCQPF/' 
    #GRIB_PATH_EX    = '/usr1/wpc_cpgffh/gribs//WPCQPF/WPCQPF_verif_day3_ALL/'
    #datetime_WPCQPF = datetime.datetime(2017, 7, 21, 12, 0)
    #grid_delta      = 0.03
    #hour            = 6
    #####################################################################################                             

    #Change datetime element to a string
    yrmondayhr_wpc = '{:04d}'.format(datetime_WPCQPF.year)+'{:02d}'.format(datetime_WPCQPF.month)+ \
        '{:02d}'.format(datetime_WPCQPF.day)+'{:02d}'.format(datetime_WPCQPF.hour)
    
    #Determine common grid everything will be interpolated to
    xpts = len(np.linspace(latlon_dims[0],latlon_dims[2],np.round((latlon_dims[2]-latlon_dims[0])/grid_delta,2)+1))
    ypts = len(np.linspace(latlon_dims[3],latlon_dims[1],np.round((latlon_dims[3]-latlon_dims[1])/grid_delta,2)+1))

    #Define the forecast projection in hours
    fcst_hr = '{:03d}'.format(hour)
    #fcst_hr = '{:03d}'.format((24 * (validday - 1) + hour))

    #Define the filename
    filename_sh = yrmondayhr_wpc+'_wpcqpf_f'+fcst_hr
    filename_lo = GRIB_PATH+filename_sh
    
    #Gunzip, regrid the file, and rezip the file
    subprocess.call('gunzip '+filename_lo+'.grb2.gz', stdout=open(os.devnull, 'wb'), stderr=open(os.devnull, 'wb'), shell=True)
    output = subprocess.call(MET_PATH+'regrid_data_plane '+filename_lo+'.grb2'+ \
        ' \'latlon '+str(xpts)+' '+str(ypts)+' '+str(latlon_dims[1])+' '+str(latlon_dims[0])+ \
        ' '+str(grid_delta)+' '+str(grid_delta)+'\' '+GRIB_PATH_EX+filename_sh+'.nc'+ \
        ' -field \'name="FFLDG"; level="R1";\'',stdout=open(os.devnull, 'wb'), \
        stderr=open(os.devnull, 'wb'),shell=True)
        
    #Gunzip and regrid the file
    subprocess.call('gzip '+filename_lo+'.grb2',stdout=open(os.devnull, 'wb'), \
        stderr=open(os.devnull, 'wb'), shell=True)
        
    #Open file into python workspace
    try:
        f      = Dataset(GRIB_PATH_EX+filename_sh+'.nc', "a", format="NETCDF4")
        lat    = f.variables['lat'][:]
        lon    = f.variables['lon'][:]
        WPCQPF = (np.flipud(f.variables['FFLDG_R1'][:])/25.4).data
        WPCQPF[WPCQPF < 0] = np.NaN
        f.close()        
    
        #Round the lat/lon data to eliminate roundoff errors
        lat=np.round(lat,2)
        lon=np.round(lon,2)
    
        print('WPC QPF File Loaded - Issued on '+fcst_hr+' hr Acc. on '+yrmondayhr_wpc)
    
        subprocess.call(GRIB_PATH_EX+filename_sh+'.nc', stdout=open(os.devnull, 'wb'), \
            stderr=open(os.devnull, 'wb'), shell=True)

    except (IOError):
        
        lat = np.NaN
        lon = np.NaN
        WPCQPF = np.NaN
        
        print('WPC QPF File Not Found - Issued on '+fcst_hr+' hr Acc. on '+yrmondayhr_wpc)

    return(lat,lon,WPCQPF)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   
                                    
#########################################################################################
#readCSU reads in the specified CSU data using MET tools and interpolates CSU data 
#to a common grid 0.1 degree LAT/LON grid. MJE. 20180105.
#
#####################INPUT FILES FOR setupData###########################################
#MET_PATH       = Directory for MET executibles
#GRIB_PATH      = Directory where ERO data is stored
#GRIB_PATH_TEMP = Temporary directory where new data is created/transferred
#latlon_dims    = latitude/longitude dimensions for plotting [WLON,SLAT,ELON,NLAT]
#grid_delta     = grid resolution increment for interpolation (degrees lat/lon)
#datetime_CSU   = datetime element
#fhr            = ending forecast hour (number) for data to be read in
####################OUTPUT FILES FOR setupData#############################
#lat            = grid of latitude from netcdf MODE output
#lon            = grid of longitude from netcdf MODE output
#CSU            = grid of CSU values
#########################################################################################

def readCSU(MET_PATH,GRIB_PATH,GRIB_PATH_TEMP,latlon_dims,grid_delta,datetime_CSU,fhr):

    ######################COMMENT OUT WHEN IN FUNCTION MODE#################################
    #MET_PATH       = '/opt/MET6/met6.0/bin/' 
    #GRIB_PATH      = '/usr1/wpc_cpgffh/gribs/CSU_MLP_FFaIR/' 
    #GRIB_PATH_TEMP = GRIB_PATH_EX
    #datetime_CSU   = datetime_endval
    #grid_delta     = 0.09
    #fhr            = 60
    ########################################################################################
    
    #Fields in the grib2 files
    fields = ['ARID21Y','ARID31Y','ARID210Y','ARID310Y']
    
    if fhr == 60:  #when analyzing day 2 data, only look at first two fields
        field_ind = [0,2]
    elif fhr == 84:
        field_ind = [1,3]
        
    #Error if specified lat/lon dims are outside CONUS (-129.8 to -60.2 W and 20.2 to 49.8 N)
    if latlon_dims[0] < -129.8 or latlon_dims[2] > -60.2 or latlon_dims[1] < 20.2 or latlon_dims[3] > 49.8:
        raise ValueError('User Specified lat/lon outside of boundary')
        
    #Grab initial time of CSU file from final forecast hour
    datetime_CSU   = datetime_CSU-datetime.timedelta(hours=fhr)
    yrmondayhr_CSU = '{:04d}'.format(datetime_CSU.year)+'{:02d}'.format(datetime_CSU.month)+\
        '{:02d}'.format(datetime_CSU.day)+'{:02d}'.format(datetime_CSU.hour)

    #Filename for each hour to be loaded exqpf_2017062200.grb2
    filename_in = 'exqpf_'+yrmondayhr_CSU+'.grb2'

    #Copy the CSU data to a temporary directory
    output = subprocess.call('cp  '+GRIB_PATH+filename_in+'.gz '+GRIB_PATH_TEMP+filename_in+'.gz', \
        stdout=open(os.devnull, 'wb'), stderr=open(os.devnull, 'wb'), shell=True)
    
    #Gunzip the data
    output = subprocess.call('gunzip '+GRIB_PATH_TEMP+filename_in+'.gz', stdout=open(os.devnull, 'wb'), \
        stderr=open(os.devnull, 'wb'), shell=True)

    #Interpolate to a common grid (del function grid) using MET's regrid_data_plane
    xpts = len(np.linspace(latlon_dims[0],latlon_dims[2],np.round((latlon_dims[2]-latlon_dims[0])/grid_delta,2)+1))
    ypts = len(np.linspace(latlon_dims[3],latlon_dims[1],np.round((latlon_dims[3]-latlon_dims[1])/grid_delta,2)+1))
    
    #Initialize CSU data matrix
    CSU = np.full([ypts,xpts,len(field_ind)],np.nan)
    
    #Loop through the specified fields in the grib files (ARID21Y;ARID31Y;ARID210Y;ARID310Y)
    data_count = 0
    for data in field_ind:
        
        subprocess.call(MET_PATH+'regrid_data_plane '+GRIB_PATH_TEMP+filename_in+ \
            ' \'latlon '+str(xpts)+' '+str(ypts)+' '+str(latlon_dims[1])+' '+str(latlon_dims[0])+ \
            ' '+str(grid_delta)+' '+str(grid_delta)+'\' '+GRIB_PATH_TEMP+filename_in+'.nc'+ \
            ' -field \'name="FFLDG"; level="R'+str(data+1)+'";\'', stdout=open(os.devnull, 'wb'), \
            stderr=open(os.devnull, 'wb'), shell=True)

        #Load static data file and initialize needed variables for later
        try:
            
            f   = Dataset(GRIB_PATH_TEMP+filename_in+'.nc', "a", format="NETCDF4")
            
            #Retrieve variable name
            for var_str in f.variables:
                if 'FFLDG' in var_str:
                    var_name = var_str
                
            lat = f.variables['lat'][:]
            lon = f.variables['lon'][:]
            lon = np.flipud(np.tile(lon,(lat.shape[0],1)))
            lat = np.flipud(np.transpose(np.tile(lat,(lon.shape[1],1))))
            CSU[:,:,data_count] = np.flipud(f.variables[var_name][:]).data
            f.close()
            
            #Round the lat/lon data to eliminate roundoff errors
            lat=np.round(lat,2)
            lon=np.round(lon,2)

            print('CSU File Loaded - Issued on '+fields[data]+' hr Acc. on '+yrmondayhr_CSU)
        
        except (IOError):
            
            lat = np.NaN
            lon = np.NaN
            CSU[:,:,data_count] = np.NaN
            
            print('CSU File Not Found - Issued on '+fields[data]+' hr Acc. on '+yrmondayhr_CSU)
        
        subprocess.call('rm -rf '+GRIB_PATH_TEMP+filename_in+'.nc', stdout=open(os.devnull, 'wb'), \
            stderr=open(os.devnull, 'wb'), shell=True)
        
        data_count += 1
    
    subprocess.call('rm -rf '+GRIB_PATH_TEMP+filename_in+'.nc', stdout=open(os.devnull, 'wb'), \
        stderr=open(os.devnull, 'wb'), shell=True)
                    
    if np.mean(np.isnan(CSU)) < 1:
        CSU[CSU < 0] = np.NaN
           
    return(lat,lon,CSU)    
                             
#########################################################################################
#readARI reads in the specified ARI data using MET tools and interpolates ARI data 
#to a common grid X degree LAT/LON grid. MJE. 20170719.
#
#####################INPUT FILES FOR readARI###########################################
#MET_PATH       = Directory for MET executibles
#GRIB_PATH      = Directory where ERO data is stored
#GRIB_PATH_TEMP = Temporary directory where new data is created/transferred
#latlon_dims    = latitude/longitude dimensions for plotting [WLON,SLAT,ELON,NLAT]
#grid_delta     = grid resolution increment for interpolation (degrees lat/lon)
#ARI_recur      = ARI recurrence interval (in years) to be loaded
####################OUTPUT FILES FOR setupData#############################
#lat            = grid of latitude from netcdf MODE output
#lon            = grid of longitude from netcdf MODE output
#ARI            = grid of ST4 values (lat,lon,ARI_recur)
#########################################################################################

def readARI(MET_PATH,GRIB_PATH,GRIB_PATH_EX,latlon_dims,grid_delta,ARI_recur):

    ####################COMMENT OUT WHEN IN FUNCTION MODE#################################
    #ARI_recur     = 5.0
    #GRIB_PATH    = '/usr1/wpc_cpgffh/gribs/'
    #GRIB_PATH_EX = '/usr1/wpc_cpgffh/gribs//ERO_verif/ERO_verif_day1_ALL/'
    #latlon_dims  = [-129.8,25.0,-65.0,49.8]
    #grid_delta   = 0.1
    #####################################################################################

    #Error if specified lat/lon dims are outside CONUS (-129.8 to -60.2 W and 20.2 to 49.8 N)
    if latlon_dims[0] < -129.8 or latlon_dims[2] > -60.2 or latlon_dims[1] < 20.2 or latlon_dims[3] > 49.8:
        raise ValueError('User Specified lat/lon outside of boundary')

    #Total number of hours to be loaded
    ARI_hrs = [1,3,6,12,24]

    #Interpolate to a common grid (del function grid) using MET's regrid_data_plane
    xpts = len(np.linspace(latlon_dims[0],latlon_dims[2],np.round((latlon_dims[2]-latlon_dims[0])/grid_delta,2)+1))
    ypts = len(np.linspace(latlon_dims[3],latlon_dims[1],np.round((latlon_dims[3]-latlon_dims[1])/grid_delta,2)+1))

    #Initialize variables
    ARI = np.ones((ypts,xpts,len(ARI_hrs)))
       
    for hrs in range(0,len(ARI_hrs)):
        
        #Filename for each interval to be loaded
        filename = str(ARI_hrs[hrs])+'h_'+str(int(ARI_recur))+'yr.grib'

        #Copy the ST4 data to a temporary directory
        output = subprocess.call('cp  '+GRIB_PATH+'ARI/'+filename+'.gz '+GRIB_PATH_EX+filename+'2.gz', \
            stdout=open(os.devnull, 'wb'), stderr=open(os.devnull, 'wb'), shell=True)
        
        #Gunzip the data
        output = subprocess.call('gunzip '+GRIB_PATH_EX+filename+'2.gz', stdout=open(os.devnull, 'wb'), \
            stderr=open(os.devnull, 'wb'), shell=True)

        output = subprocess.call(MET_PATH+'regrid_data_plane '+GRIB_PATH_EX+filename+'2'+ \
            ' \'latlon '+str(xpts)+' '+str(ypts)+' '+str(latlon_dims[1])+' '+str(latlon_dims[0])+ \
            ' '+str(grid_delta)+' '+str(grid_delta)+'\' '+GRIB_PATH_EX+filename+'2.nc'+ \
            ' -field \'name="REFZC"; level="R1";\'', stdout=open(os.devnull, 'wb'), \
            stderr=open(os.devnull, 'wb'), shell=True)

        #Load ARI data
        f            = Dataset(GRIB_PATH_EX+filename+'2.nc', "a", format="NETCDF4")
        lat          = f.variables['lat'][:]
        lon          = f.variables['lon'][:]
        lon          = np.flipud(np.tile(lon,(lat.shape[0],1)))
        lat          = np.flipud(np.transpose(np.tile(lat,(lon.shape[1],1))))
        ARI[:,:,hrs] = np.flipud(f.variables['REFZC_R1'][:])
        f.close()
        
        subprocess.call('rm -rf '+GRIB_PATH_EX+filename+'2.gz', stdout=open(os.devnull, 'wb'), \
            stderr=open(os.devnull, 'wb'), shell=True)
        subprocess.call('rm -rf '+GRIB_PATH_EX+filename+'2.nc', stdout=open(os.devnull, 'wb'), \
            stderr=open(os.devnull, 'wb'), shell=True)
        subprocess.call('rm -rf '+GRIB_PATH_EX+filename+'2', stdout=open(os.devnull, 'wb'), \
            stderr=open(os.devnull, 'wb'), shell=True)
        
        print('ARI File Loaded for '+str(int(ARI_hrs[hrs]))+' accumulated hours')
        
    #Round the lat/lon data to eliminate roundoff errors
    lat=np.round(lat,2)
    lon=np.round(lon,2)

    ARI[ARI<0] = np.NaN
    
    #Adjustment factor to convert ARI from milli-inches to millimeters
    ARI = (ARI / float(1000)) * 25.4
        
    return(lat,lon,ARI)
     
#########################################################################################
#Cosgrove2txt serves a specific purpose; from the archived Cosgrove tbl database, 
#extract the lat/lon information for the specified data type (USGS, LSRFLASH, LSRREG, or MPING) 
#and save that data as a text file readable by MET. MJE. 20170718.
#
#Update: Include LSR regular flooding events. MJE. 20180427.
#Update: Include 6 hour increments: vhr =  0 means  6-hr reports between 18-00z
#                                   vhr =  6 means  6-hr reports between 00-06z
#                                   vhr = 24 means 24-hr reports between 12-12z 
#                                   MJE. 20180816.
#
#####################INPUT FILES FOR Cosgrove2txt#######################################
#GRIB_PATH        = Directory where grib data is stored
#GRIB_PATH_EX     = Directory where text file and new netCDF file is to be saved
#datetime_beg_COS = Datetime element of data to be loaded
#vhr              = Starting hour of validation period
#latlon_dims      = latitude/longitude dimensions for plotting [WLON,SLAT,ELON,NLAT]
#grid_delta       = grid resolution increment for interpolation (degrees lat/lon)
#data_type        = Data type to be loaded (USGS, LSRREG, LSRFLASH, or MPING)
####################OUTPUT FILES FOR Cosgrove2txt#######################################
#filename_s       = Name of created text file
#########################################################################################

def Cosgrove2txt(GRIB_PATH,GRIB_PATH_EX,datetime_beg_COS,vhr,latlon_dims,grid_delta,data_type):
    
    ###################COMMENT OUT WHEN IN FUNCTION MODE#################################
    #GRIB_PATH          = '/usr1/wpc_cpgffh/gribs/' 
    #GRIB_PATH_EX       = '/usr1/wpc_cpgffh/gribs//ERO_verif/ERO_verif_day1_FFGonly/'
    #datetime_beg_COS   = datetime.datetime(2017, 7, 16, 12, 0, 0)
    #data_type          = 'usgs'
    #latlon_dims        = [-129.8,25.0,-65.0,49.8]
    #grid_delta         = 0.1
    #####################################################################################
    
    #Cosgrove date on original file reflects end time.
    datetime_end_COS = datetime_beg_COS + datetime.timedelta(days=1)
    yrmonday_beg_COS = ''.join(['{:04d}'.format(datetime_beg_COS.year),  \
        '{:02d}'.format(datetime_beg_COS.month),'{:02d}'.format(datetime_beg_COS.day)])
    yrmonday_end_COS = ''.join(['{:04d}'.format(datetime_end_COS.year),  \
        '{:02d}'.format(datetime_end_COS.month),'{:02d}'.format(datetime_end_COS.day)])

    #Create new grid from user specified boundaries and resolution
    [lon,lat] = np.meshgrid(np.linspace(latlon_dims[0],latlon_dims[2],np.round((latlon_dims[2]-latlon_dims[0])/grid_delta,2)+1), \
        np.linspace(latlon_dims[3],latlon_dims[1],np.round((latlon_dims[3]-latlon_dims[1])/grid_delta,2)+1))
    lat = np.round(lat[::-1,0],decimals=2)
    lon = np.round(lon[0,:],   decimals=2)
    fid = Dataset(GRIB_PATH_EX+'dummy_'+data_type.lower()+'.nc', 'w', format='NETCDF4_CLASSIC')
    lats  = fid.createDimension('lat', int(lat.shape[0]))
    lons  = fid.createDimension('lon', int(lon.shape[0]))
    lats  = fid.createVariable('lat', 'f8', ('lat'))
    lons  = fid.createVariable('lon', 'f8', ('lon'))    
    #Create variable attributes
    lats.long_name = "latitude"
    lats.units = "degrees_north"
    lats.standard_name = "latitude"
    lons.long_name = "longitude"
    lons.units = "degrees_east"
    lons.standard_name = "longitude"
    fid.FileOrigins = "Dummy File to Provide Gridded Lat/Lon Information"
    fid.MET_version = "V6.0"
    fid.MET_tool = "None"
    fid.RunCommand = "Regrid from Projection: Stereographic Nx: 1121 Ny: 881 IsNorthHemisphere: true Lon_orient: 105.000 Bx: 399.440 By: 1599.329 Alpha: 2496.0783 to Projection: Lat/Lon Nx: 248 Ny: 648 lat_ll: 25.100 lon_ll: 131.100 delta_lat: 0.100 delta_lon: 0.100"
    fid.Projection = "LatLon"
    fid.lat_ll = str(latlon_dims[1])+" degrees_north"
    fid.lon_ll = str(latlon_dims[0])+" degrees_east"
    fid.delta_lat = str(grid_delta)+" degrees"
    fid.delta_lon = str(grid_delta)+" degrees"
    fid.Nlat = str(lat.shape[0])+" grid_points"
    fid.Nlon = str(lon.shape[0])+" grid_points"
    #Writting data to file
    lats[:]    = lat
    lons[:]    = lon
    #Close the file
    fid.close()
    
    #Proper hour datestring given start hour of validation period
    if vhr == 0:     #06-hour reports from 18 - 00z
        vhr_str = '00'
        filename_s = GRIB_PATH_EX+data_type.upper()+'_s'+yrmonday_beg_COS+'18_e'+yrmonday_end_COS+'00.txt'
    elif vhr == 6:   #06-hour reports from 00 - 06z
        vhr_str = '06'
        filename_s = GRIB_PATH_EX+data_type.upper()+'_s'+yrmonday_end_COS+'00_e'+yrmonday_end_COS+'06.txt'
    else:            #24-hour reports from 12 - 02z
        vhr_str = '12'
        filename_s = GRIB_PATH_EX+data_type.upper()+'_s'+yrmonday_beg_COS+'12_e'+yrmonday_end_COS+'12.txt'    
                                                                                
    #Read Cosgrove data, extract lat/lon data, create new text file readable by gen_vx_mask 
    if 'lsrflash' in data_type.lower():
        filename = GRIB_PATH+'COSGROVE/'+data_type.upper()+'/'+yrmonday_end_COS+ \
            '.'+vhr_str+'00.final.flashflood_lsr.station.nophan.tbl.gz'
        if not os.path.isfile(filename):
            filename = GRIB_PATH+'COSGROVE/'+data_type.upper()+'/'+yrmonday_end_COS+ \
                '.'+vhr_str+'00.prelim.flashflood_lsr.station.nophan.tbl.gz'
    if 'lsrreg' in data_type.lower():
        filename = GRIB_PATH+'COSGROVE/'+data_type.upper()+'/'+yrmonday_end_COS+ \
            '.'+vhr_str+'00.final.flood_lsr.station.nophan.tbl.gz'
        if not os.path.isfile(filename):
            filename = GRIB_PATH+'COSGROVE/'+data_type.upper()+'/'+yrmonday_end_COS+ \
                '.'+vhr_str+'00.prelim.flood_lsr.station.nophan.tbl.gz'
    elif 'usgs' in data_type.lower():
        filename = GRIB_PATH+'COSGROVE/'+data_type.upper()+'/'+yrmonday_end_COS+ \
            '.'+vhr_str+'00.flashflood_'+data_type.lower()+'.station.nophan.tbl.gz'
    elif 'mping' in data_type.lower():
        filename = GRIB_PATH+'COSGROVE/'+data_type.upper()+'/'+yrmonday_end_COS+ \
            '.'+vhr_str+'00.flood_'+data_type.lower()+'.station.nophan.tbl.gz'
            
    temp_lat = []
    temp_lon = []
    try:
        
        fobj = gzip.open(filename, 'rb')
        
        #Round lat/lon data
        for line in fobj:
            temp_lat = np.append(temp_lat,float(line[54:61])/100)
            temp_lon = np.append(temp_lon,float(line[61:68])/100)
            
        fobj.close()
        
    except IOError: #Rare condition file was not written
        
        #Write lat/lon as zeros to avoid blank file
        temp_lat = [0.0]
        temp_lon = [0.0]

    fobj = open(filename_s, 'wb')
    fobj.write(data_type.upper()+'\n')
    for line in range(0,len(temp_lat)):
        fobj.write(str(np.round(temp_lat[line],decimals=1))+''+str(np.round(temp_lon[line],decimals=1))+'\n')
        
    fobj.close()

    return(filename_s)

#########################################################################################
#grid2txt serves a specific purpose; from a gridded binomial 2-D field, 
#create a text file of all points where WPC exceeds FFG. MJE. 20180411.
#
#UPDATE: Modified to include any 2-d field and vhr start/end. MJE. 20180423.
#
#####################INPUT FILES FOR grid2txt#######################################
#GRIB_PATH_EX         = Directory where text file and new netCDF file is to be saved
#GridName             = String name for grid
#Grid                 = Binomial 2-D grid of ST4 exceeding FFG
#lat                  = 2-D lat grid
#lon                  = 2-D lon grid
#yrmondayhr_beg       = beginning yrmondayhr string 
#yrmondayhr_end       = ending yrmondayhr string
####################OUTPUT FILES FOR grid2txt#######################################
#filename_Grid_txt = Name of created text file
#########################################################################################

def grid2txt(GRIB_PATH_EX,GridName,Grid,lat,lon,yrmondayhr_beg,yrmondayhr_end):
    
    ###################COMMENT OUT WHEN IN FUNCTION MODE#################################
    #GRIB_PATH_EX       = '/usr1/wpc_cpgffh/gribs//WPCQPF/WPCQPF_verif_day1_ALL/' 
    #GridName           = 'WPCQPF'
    #yrmonday_end       = '20180228'
    #yrmonday_beg       = '20180301'
    #####################################################################################
    
    filename_Grid_txt = GRIB_PATH_EX+GridName+'_s'+yrmondayhr_beg+'_e'+yrmondayhr_end+'.txt'
    if np.sum(Grid == True) > 0:
        Grid_lat = lat[Grid == 1]
        Grid_lon = lon[Grid == 1]
    else:
        Grid_lat = []
        Grid_lon = []
    
    fobj = open(filename_Grid_txt, 'wb')
    fobj.write(GridName+'\n')
    for line in range(0,len(Grid_lat)):
        fobj.write(str(np.round(Grid_lat[line],decimals=1))+''+str(np.round(Grid_lon[line],decimals=1))+'\n')
        
    fobj.close()

    return(filename_Grid_txt)

#########################################################################################
#calc_ST4gFFG serves a specific purpose; given 1,3,6 hour ST4 and 3,6 hour FFG, 
#compute all possible combinations of flooding within each 1, 3, and 6 hour windows for all 
#data within the valid hours window specified. Output is a daily grid of FFG > ST4. 
#MJE. 20170622-20170719.
#
#####################INPUT FILES FOR calc_ST4gFFG###########################################
#vhr_ST4       = Valid hours to be considered; dimension (vhr)
#ST4_01hr      = ST4 1-hour accumulated precipitation; dimension (lat,lon,vhr)
#ST4_06hr      = ST4 6-hour accumulated precipitation; dimension (lat,lon,vhr/6)
#FFG_01hr      = FFG 1-hour accumulated precipitation; dimension (lat,lon,vhr)
#FFG_03hr      = FFG 3-hour accumulated precipitation; dimension (lat,lon,vhr/3)
#FFG_06hr      = FFG 6-hour accumulated precipitation; dimension (lat,lon,vhr/6)
####################OUTPUT FILES FOR calc_ST4gFFG###########################################
#flood_obs     = Daily flood obs grid representing all possible combinations of ST4 > FFG
############################################################################################

def calc_ST4gFFG(vhr_ST4,ST4_01hr,ST4_06hr,FFG_01hr,FFG_03hr,FFG_06hr):
    
    #Find all ST4 >= FFG 1,3,6 hour combinations
    vhr3_count = 0
    vhr6_count = 0
    flood_3hr = np.zeros(([ST4_01hr.shape[0],ST4_01hr.shape[1], 5,8]))
    flood_6hr = np.zeros(([ST4_01hr.shape[0],ST4_01hr.shape[1],11,4]))
    
    for vhr in range(0,len(vhr_ST4)):

        #Find and consider all 6 hour increments as long as 1 hr is in the 6 hr window
        if (vhr + 1) % 6 == 0:   #find focus hour
            vhr6_count_ext = 0
            for int_6hr in range(vhr-10,vhr+1,1): #look backwards from focus hr (i.e. hr 12 spans 7-12, first window is 2-7, last window is 12-17)
                
                #In this case remove negative indices since they are not meant to wrap around
                if int_6hr < 0:
                    int_6hr_use = 0
                else:
                    int_6hr_use = int_6hr
                        
                if np.sum(np.linspace(int_6hr,int_6hr+6,7) > 0) > 0:
                    
                    flood_6hr[:,:,vhr6_count_ext,vhr6_count] = np.sum(ST4_01hr[:,:,int_6hr_use:int_6hr+6], \
                        axis=2) > FFG_06hr[:,:,vhr6_count]
                    vhr6_count_ext += 1

            vhr6_count += 1

        #Find and consider all 3 hour increments as long as 1 hr is in the 3 hr window
        if (vhr + 1) % 3 == 0:   #find focus hour
            vhr3_count_ext = 0
            for int_3hr in range(vhr-4,vhr+1,1): #look backwards from focus hr
                
                #In this case remove negative indices since they are not meant to wrap around
                if int_3hr < 0:
                    int_3hr_use = 0
                else:
                    int_3hr_use = int_3hr
                    
                if np.sum(np.linspace(int_3hr,int_3hr+3,4) > 0) > 0:
                    
                    flood_3hr[:,:,vhr3_count_ext,vhr3_count]=np.sum(ST4_01hr[:,:,int_3hr_use:int_3hr+3], \
                        axis=2) > FFG_03hr[:,:,vhr3_count]
                    vhr3_count_ext += 1
                    
            vhr3_count += 1
                          
    #Remove NaNs from data, replace with zeros
    NaN_01hr=np.isnan(ST4_01hr) | np.isnan(FFG_01hr)
    NaN_06hr=np.isnan(ST4_06hr) | np.isnan(FFG_06hr)
    ST4_01hr[NaN_01hr] = 0
    ST4_06hr[NaN_06hr] = 0
    FFG_01hr[NaN_01hr] = 0
    FFG_03hr[np.isnan(FFG_03hr)] = 0
    FFG_06hr[NaN_06hr] = 0
    
    #Condense all 1,3,6 hour instances and combine
    flood_1hr=ST4_01hr > FFG_01hr
    flood_3hr=np.nansum(flood_3hr,axis=2) > 0
    flood_6hr=((ST4_06hr > FFG_06hr) + np.nansum(flood_6hr,axis=2)) > 0
    
    #Duplicate 3/6 hour so it can be more easily folded into a 24 hour day
    flood_3hr_dup = np.zeros((ST4_01hr.shape[0],ST4_01hr.shape[1],flood_1hr.shape[2]))
    flood_6hr_dup = np.zeros((ST4_01hr.shape[0],ST4_01hr.shape[1],flood_1hr.shape[2]))
    vhr3_count = 0
    vhr6_count = 0

    for vhr in range(0,flood_1hr.shape[2],1):
        
        if vhr % 3 == 0 and vhr != 0:
            vhr3_count += 1
        
        if vhr % 6 == 0 and vhr != 0:
            vhr6_count += 1
        
        flood_3hr_dup[:,:,vhr] = flood_3hr[:,:,vhr3_count]
        flood_6hr_dup[:,:,vhr] = flood_6hr[:,:,vhr6_count]
            
    #Combine all flooding info
    flood_obs=((flood_1hr + flood_3hr_dup + flood_6hr_dup) > 0)

    return flood_obs

#########################################################################################
#calc_ST4gARI serves a specific purpose; given 1,3,6 hour ST4 and 1,3,6,12,24 hour ARI, 
#compute all possible combinations of flooding within all of the hourly windows possible. 
#Output is an hourly binomial grid of ARI > ST4, however note that every hour includes the
#24 hour threshold and hence this should only be applied over the full 24 hours.
#MJE. 20170718-20170721.
#
#####################INPUT FILES FOR calc_ST4gARI########################################
#vhr_ST4       = Valid hours to be considered; dimension (vhr)
#ST4_01hr      = ST4 1-hour accumulated precipitation; dimension (lat,lon,vhr)
#ST4_06hr      = ST4 6-hour accumulated precipitation; dimension (lat,lon,vhr/6)
#ARI           = ARI precipitation values (lat,lon,thresholds for 1/3/6/12/24 hour windows)
####################OUTPUT FILES FOR calc_ST4gARI#############################
#flood_obs     = Daily flood obs grid representing all possible combinations of ST4 > ARI
#########################################################################################

def calc_ST4gARI(vhr_ST4,ST4_01hr,ST4_06hr,ARI):
    
    #Split ARI into 1,3,6,12, and 24 hour variables
    ARI_01hr  = ARI[:,:,0]
    ARI_03hr  = ARI[:,:,1]
    ARI_06hr  = ARI[:,:,2]
    ARI_12hr  = ARI[:,:,3]
    ARI_24hr  = ARI[:,:,4]

    #Create ST4 24 hour precipitation
    ST4_24hr = np.sum(ST4_06hr, axis = 2)
    
    #Find all ST4 >= ARI 1,3,6 hour combinations
    vhr03_count = 0
    vhr06_count = 0
    vhr12_count = 0
    flood_03hr  = np.zeros(([ST4_01hr.shape[0],ST4_01hr.shape[1], 5,len(vhr_ST4)/3]))
    flood_06hr  = np.zeros(([ST4_01hr.shape[0],ST4_01hr.shape[1],11,len(vhr_ST4)/6]))
    flood_12hr  = np.zeros(([ST4_01hr.shape[0],ST4_01hr.shape[1],23,len(vhr_ST4)/12]))
    
    for vhr in range(0,len(vhr_ST4)):

        #Find and consider all 3 hour increments as long as 1 hr is in the 3 hr window
        if (vhr + 1) % 3 == 0:   #find focus hour
            vhr03_count_ext = 0
            for int_03hr in range(vhr-4,vhr+1,1): #look backwards from focus hr

                #In this case remove negative indices since they are not meant to wrap around
                if int_03hr < 0:
                    int_03hr_use = 0
                else:
                    int_03hr_use = int_03hr
                    
                if np.sum(np.linspace(int_03hr,int_03hr+3,4) > 0) > 0:
                    
                    flood_03hr[:,:,vhr03_count_ext,vhr03_count]=np.sum(ST4_01hr[:,:,int_03hr_use:int_03hr+3], \
                        axis=2) > ARI_03hr
                    vhr03_count_ext += 1
                    
            vhr03_count += 1
            
        #Find and consider all 6 hour increments as long as 1 hr is in the 6 hr window
        if (vhr + 1) % 6 == 0:   #find focus hour
            vhr06_count_ext = 0
            for int_06hr in range(vhr-10,vhr+1,1): #look backwards from focus hr (i.e. hr 12 spans 7-12, first window is 2-7, last window is 12-17)
                
                #In this case remove negative indices since they are not meant to wrap around
                if int_06hr < 0:
                    int_06hr_use = 0
                else:
                    int_06hr_use = int_06hr
                        
                if np.sum(np.linspace(int_06hr,int_06hr+6,7) > 0) > 0:
                    
                    flood_06hr[:,:,vhr06_count_ext,vhr06_count] = np.sum(ST4_01hr[:,:,int_06hr_use:int_06hr+6], \
                        axis=2) > ARI_06hr
                    vhr06_count_ext += 1

            vhr06_count += 1

        #Find and consider all 12 hour increments as long as 1 hr is in the 3 hr window
        if (vhr + 1) % 12 == 0:   #find focus hour
            vhr12_count_ext = 0
            for int_12hr in range(vhr-22,vhr+1,1): #look backwards from focus hr
                
                #In this case remove negative indices since they are not meant to wrap around
                if int_12hr < 0:
                    int_12hr_use = 0
                else:
                    int_12hr_use = int_12hr
                    
                if np.sum(np.linspace(int_12hr,int_12hr+12,13) > 0) > 0:
                    flood_12hr[:,:,vhr12_count_ext,vhr12_count]=np.sum(ST4_01hr[:,:,int_12hr_use:int_12hr+12], \
                        axis=2) > ARI_12hr
                    vhr12_count_ext += 1
                    
            vhr12_count += 1

    #Sum flood observation windows of all possible combinations
    flood_03hr = np.nansum(flood_03hr,axis=2) > 0
    flood_06hr = np.nansum(flood_06hr,axis=2) > 0
    flood_12hr = np.nansum(flood_12hr,axis=2) > 0
    
    #Duplicate 3,6,12,24 hour flood increments to match 24 hour day
    flood_03hr_dup = np.zeros((ST4_01hr.shape[0],ST4_01hr.shape[1],len(vhr_ST4)))
    flood_06hr_dup = np.zeros((ST4_01hr.shape[0],ST4_01hr.shape[1],len(vhr_ST4)))
    flood_12hr_dup = np.zeros((ST4_01hr.shape[0],ST4_01hr.shape[1],len(vhr_ST4)))
    ST4_06hr_dup   = np.zeros((ST4_01hr.shape[0],ST4_01hr.shape[1],len(vhr_ST4)))
    
    #Check to see if verification window is shorter than 3,6,12 hour windows
    if flood_03hr.shape[2] == 0:
        flood_03hr = np.zeros((flood_03hr.shape[0],flood_03hr.shape[1],1))
    if flood_06hr.shape[2] == 0:
        flood_06hr = np.zeros((flood_06hr.shape[0],flood_06hr.shape[1],1))
    if flood_12hr.shape[2] == 0:
        flood_12hr = np.zeros((flood_12hr.shape[0],flood_12hr.shape[1],1))

    vhr03_count = 0
    vhr06_count = 0
    vhr12_count = 0
    for vhr in range(0,len(vhr_ST4),1):
        
        if vhr % 3 == 0 and vhr != 0:
            vhr03_count += 1
        if vhr % 6 == 0 and vhr != 0:
            vhr06_count += 1
        if vhr % 12 == 0 and vhr != 0:
            vhr12_count += 1
        
        ST4_06hr_dup[:,:,vhr]   = ST4_06hr[:,:,vhr06_count]
        flood_03hr_dup[:,:,vhr] = flood_03hr[:,:,vhr03_count]
        flood_06hr_dup[:,:,vhr] = flood_06hr[:,:,vhr06_count]
        flood_12hr_dup[:,:,vhr] = flood_12hr[:,:,vhr12_count]

    flood_03hr = flood_03hr_dup
    flood_06hr = flood_06hr_dup
    flood_12hr = flood_12hr_dup
    ST4_06hr   = ST4_06hr_dup
    ST4_24hr   = np.transpose(np.tile(ST4_24hr,(len(vhr_ST4),1,1)),(1,2,0))
    
    #Duplicate all ARI fields to match len(vhr_ST4) hour intervals
    ARI_01hr = np.transpose(np.tile(ARI_01hr,(len(vhr_ST4),1,1)),(1,2,0))
    ARI_03hr = np.transpose(np.tile(ARI_03hr,(len(vhr_ST4),1,1)),(1,2,0))
    ARI_06hr = np.transpose(np.tile(ARI_06hr,(len(vhr_ST4),1,1)),(1,2,0))
    ARI_12hr = np.transpose(np.tile(ARI_12hr,(len(vhr_ST4),1,1)),(1,2,0))
    ARI_24hr = np.transpose(np.tile(ARI_24hr,(len(vhr_ST4),1,1)),(1,2,0))
    
    #Remove NaNs from data, replace with zeros
    NaN_01hr=np.isnan(ST4_01hr) | np.isnan(ARI_01hr) 
    NaN_03hr=np.isnan(ARI_03hr) | np.isnan(flood_03hr)
    NaN_06hr=np.isnan(ST4_06hr) | np.isnan(ARI_06hr) | np.isnan(flood_06hr)
    NaN_12hr=np.isnan(ARI_12hr) | np.isnan(flood_12hr) 
    NaN_24hr=np.isnan(ST4_24hr) | np.isnan(ARI_24hr)
    ST4_01hr[NaN_01hr] = 0
    ARI_01hr[NaN_01hr] = 0
    ST4_06hr[NaN_06hr] = 0
    ARI_06hr[NaN_06hr] = 0
    ST4_24hr[NaN_24hr] = 0
    ARI_24hr[NaN_24hr] = 0
    
    #Condense all 1,3,6,12 hour running window instances
    flood_01hr = ST4_01hr > ARI_01hr
    flood_06hr = ((ST4_06hr > ARI_06hr) + flood_06hr) > 0
    flood_24hr = ST4_24hr > ARI_24hr
    
    #Combine all flooding info 
    flood_obs=((flood_01hr + flood_03hr + flood_06hr + flood_12hr + flood_24hr) > 0)

    return flood_obs
    
#########################################################################################
#statAnalyisSub is a substitute for running statAnalysis. Specifically, it reads in the grid_stat 
#STAT output files for the ERO verification and collects the data specified in the input.
#Use this version for the operational ERO figure generation. MJE. 20170828 - 20170915
#
#UPDATE: Reorganized code to improve efficency. MJE. 20180502.
#
#####################INPUT FILES FOR statAnalyisSub########################################
#GRIB_PATH_EX  = Directory where data is located
#fcst_lev      = Forecast level specified in grid_stat file
#fcst_var      = Forecast variable specified in grid_stat file
#obs_lev       = Observation level specified in grid_stat file
#obs_var       = Observation variable specified in grid_stat file
#line_type     = Statistic type being extracted in the 'line_type' location
#var_type      = Within the data of the 'line_type' statistics, the specific values requested
#datetime_beg  = Beginning time for extracting grid_stat data
#datetime_end  = Ending time for extracting grid_stat data
####################OUTPUT FILES FOR statAnalyisSub#############################
#f_data        = Data extracted from grid_stat STAT file
#f_yrmondayhr  = Year, month, day, and hour information of the file
#f_vhr         = Issuance hour of ERO forecast
#########################################################################################

def statAnalyisSub(GRIB_PATH_EX,fcst_lev,fcst_var,obs_lev,obs_var,line_type,var_type,datetime_beg,datetime_end):

    #######################COMMENT OUT WHEN IN FUNCTION MODE##################################
    #GRIB_PATH_EX = GRIB_PATH_EX_noMRGL
    #fcst_lev  = 'Surface'
    #fcst_var  = 'ERO'
    #obs_lev   = 'A365324'
    #obs_var   = 'ALL'
    #line_type = 'PSTD'
    #var_type  = ['BRIER','BRIER_NCL','BRIER_NCU','ROC_AUC']
    #datetime_beg = datetime_beg
    #datetime_end = datetime_end
    ##########################################################################################

    #Convert datetime elements to Julian day
    julian_beg = pygrib.datetime_to_julian(datetime_beg)
    julian_end = pygrib.datetime_to_julian(datetime_end)
    
    #Metadata list corresponding to the master header in the file                                                             
    metadata_list_header  = ['VERSION','MODEL','DESC','FCST_LEAD','FCST_VALID_BEG','FCST_VALID_END','OBS_LEAD', \
        'OBS_VALID_BEG','OBS_VALID_END','FCST_VAR','FCST_LEV','OBS_VAR','OBS_LEV','OBTYPE','VX_MASK','INTERP_MTHD', \
        'INTERP_PNTS','FCST_THRESH','OBS_THRESH','COV_THRESH','ALPHA','LINE_TYPE']   
        
    #Depending on line_type, read in metadata specific to that data type
    if line_type == 'PSTD':
        metadata_list_read = ['PTSD','TOTAL','N_THRESH','BASER','BASER_NCL','BASER_NCU','RELIABILITY','RESOLUTION', \
            'UNCERTAINTY','ROC_AUC','BRIER','BRIER_NCL','BRIER_NCU','BRIERCL','BRIERCL_NCL','BRIERCL_NCU','BSS','THRESH_i']
        
        #Find the proper index within the data
        var_ind = []
        for type in var_type:    
            var_ind = np.append(var_ind,metadata_list_read.index(type))
    
    #Initialize variables and run through files
    f_data       = []    
    f_yrmondayhr = [] 
    f_vhr        = []
    for file_s in os.listdir(GRIB_PATH_EX):
        
        #Find proper file format       
        if '_'+fcst_var+'_' in file_s and '_'+obs_var+'_' in file_s and 'V.stat' in file_s:

            #Find files within the specified date range
            datetime_temp = datetime.datetime(int(file_s[file_s.find('_e')+2:file_s.find('_e')+6]), \
                int(file_s[file_s.find('_e')+6:file_s.find('_e')+8]), \
                int(file_s[file_s.find('_e')+8:file_s.find('_e')+10]), \
                int(file_s[file_s.find('_e')+10:file_s.find('_e')+12]), 0, 0)
            julian_temp = pygrib.datetime_to_julian(datetime_temp)

            if julian_temp >= julian_beg and julian_temp <= julian_end:

                #Initialize starting index location of data
                list_ind = []
                
                #Read the file
                subprocess.call('gunzip '+GRIB_PATH_EX+file_s,stdout=open(os.devnull, 'wb'), stderr=open(os.devnull, 'wb'),shell=True)
                file   = open(GRIB_PATH_EX+file_s[0:-3], 'rb')
                subprocess.call('gzip '+GRIB_PATH_EX+file_s[0:-3],stdout=open(os.devnull, 'wb'), stderr=open(os.devnull, 'wb'),shell=True)
                lin    = file.readline()
                
                #Find the metadata structure
                for list in metadata_list_header:
                    list_ind = np.append(list_ind,lin.find(list))
                
                while lin:  #Iterate f_yrmondayhrthrough file     
                    lin = file.readline()
                    
                    #Check fcst/obs level/variable and line_type specifications and flooding proxy is yes
                    if fcst_var == lin[int(list_ind[9]):int(list_ind[10])].strip() and \
                        fcst_lev == lin[int(list_ind[10]):int(list_ind[11])].strip() and \
                        obs_var  == lin[int(list_ind[11]):int(list_ind[12])].strip() and \
                        obs_lev in lin[int(list_ind[12]):int(list_ind[13])].strip() and \
                        line_type in lin[int(list_ind[21]):]: #and MRGL_issued > 0:
    
                            #Extract metadata from file
                            f_yrmondayhr = np.append(f_yrmondayhr,file_s[file_s.find('_e')+2:file_s.find('_e')+12])
                            f_vhr        = np.append(f_vhr,int(file_s[file_s.find('_vhr')+4:file_s.find('_vhr')+6]))
                            lin_temp     = lin[int(list_ind[21]):].split()

                            #Extract the proper data specified in 'var_type'
                            f_data_temp = np.full([len(var_ind)],np.nan)
                            for values in range(0,len(var_ind)):
                                try:
                                    f_data_temp[values] = float(lin_temp[int(var_ind[values])])
                                except ValueError:
                                    pass
                            
                            #Concatenate the data into a permanent data source
                            if len(f_data) == 0:
                                f_data = np.concatenate((f_data,f_data_temp), axis = 0)
                            else: 
                                f_data = np.vstack((f_data,f_data_temp))
                file.close()
                
    #Sort the data by date
    sort_ind        = np.argsort(f_yrmondayhr)
    f_yrmondayhr    = f_yrmondayhr[sort_ind]
    f_vhr           = f_vhr[sort_ind]
    f_data          = f_data[sort_ind,:]
    
    #Sort data by hour by isolating date and sorting hour within each specific day
    f_yrmondayhr_temp  = [int(i) for i in f_yrmondayhr]
    f_index            = np.append(0,np.where(np.diff(f_yrmondayhr_temp)>0)[0]+1)
    f_index            = np.append(f_index,len(f_yrmondayhr_temp))
    
    f_vhr_arr_tot = []
    for date in range(0,len(f_index)-1):
    
        f_vhr_temp = f_vhr[f_index[date]:f_index[date+1]]
        f_vhr_arr  = np.argsort(f_vhr_temp)
        
        #The 01 UTC issuance is later than other. Rearrange to end of array.
        if f_vhr_temp[f_vhr_arr[0]] == 1:
            f_vhr_arr = np.append(f_vhr_arr[1::],f_vhr_arr[0])
        
        #Concat rearranged array
        f_vhr_arr_tot = np.append(f_vhr_arr_tot,f_vhr_arr+f_index[date])

    #Convert to integer
    f_vhr_arr_tot = [int(i) for i in f_vhr_arr_tot]
    
    #Use indces to rearrange data
    f_yrmondayhr    = f_yrmondayhr[f_vhr_arr_tot]
    f_vhr           = f_vhr[f_vhr_arr_tot]
    f_data          = f_data[f_vhr_arr_tot,:]
    
    return(f_data,f_yrmondayhr,f_vhr)
    
#########################################################################################
#statAnalyisSubFFAIR is a substitute for running statAnalysis. Specifically, it reads in the grid_stat 
#STAT output files for the ERO verification and collects the data specified in the input.
#Use this version for FFAIR which considers reading in data by valid day. 
#THIS FUNCTION IS EVOLVING. MJE. 20170828 - ????
#
#####################INPUT FILES FOR statAnalyisSubFFAIR########################################
#GRIB_PATH_EX  = Directory where data is located
#fcst_lev      = Forecast level specified in grid_stat file
#fcst_var      = Forecast variable specified in grid_stat file
#obs_lev       = Observation level specified in grid_stat file
#obs_var       = Observation variable specified in grid_stat file
#line_type     = Statistic type being extracted in the 'line_type' location
#var_type      = Within the data of the 'line_type' statistics, the specific values requested
#datetime_beg  = Beginning time for extracting grid_stat data
#datetime_end  = Ending time for extracting grid_stat data
#vday          = Valid day to be analyzed
#vhr           = Valid hour to be analyzed
####################OUTPUT FILES FOR statAnalyisSubFFAIR#############################
#f_data        = Data extracted from grid_stat STAT file
#f_vday        = The verification day from the file
#f_yrmondayhr  = year, month, day, and hour information of the file
#########################################################################################

def statAnalyisSubFFAIR(GRIB_PATH_EX,fcst_lev,fcst_var,obs_lev,obs_var,line_type,var_type,datetime_beg,datetime_end,vday,vhr):

#######################COMMENT OUT WHEN IN FUNCTION MODE##################################
#GRIB_PATH_EX = '/usr1/wpc_cpgffh/gribs//ERO_verif/ERO_verif_FFaIR2018/'
#fcst_lev  = 'Surface'
#fcst_var  = 'ERO'
#obs_lev   = 'Surface'
#obs_var   = 'ST4gFFG'
#line_type = 'PSTD'
#var_type  = ['BRIER','BRIER_NCL','BRIER_NCU']
#datetime_beg = datetime.datetime(2017,6,20,0,0,0)
#datetime_end = datetime.datetime(2017,7,25,0,0,0)
#vday         = 1
##########################################################################################

    #Convert datetime elements to Julian day
    julian_beg = pygrib.datetime_to_julian(datetime_beg)
    julian_end = pygrib.datetime_to_julian(datetime_end)
    
    #Metadata list corresponding to the master header in the file                                                             
    metadata_list_header  = ['VERSION','MODEL','DESC','FCST_LEAD','FCST_VALID_BEG','FCST_VALID_END','OBS_LEAD', \
        'OBS_VALID_BEG','OBS_VALID_END','FCST_VAR','FCST_LEV','OBS_VAR','OBS_LEV','OBTYPE','VX_MASK','INTERP_MTHD', \
        'INTERP_PNTS','FCST_THRESH','OBS_THRESH','COV_THRESH','ALPHA','LINE_TYPE']   
        
    #Depending on line_type, read in metadata specific to that data type
    if line_type == 'PSTD':
        metadata_list_read = ['PTSD','TOTAL','N_THRESH','BASER','BASER_NCL','BASER_NCU','RELIABILITY','RESOLUTION', \
            'UNCERTAINTY','ROC_AUC','BRIER','BRIER_NCL','BRIER_NCU','BRIERCL','BRIERCL_NCL','BRIERCL_NCU','BSS','THRESH_i']
        
        #Find the proper index within the data
        var_ind = []
        for type in var_type:    
            var_ind = np.append(var_ind,metadata_list_read.index(type))
    
    #Initialize variables and run through files
    f_data       = []  
    f_vday       = []    
    f_yrmondayhr = [] 
    for file_s in os.listdir(GRIB_PATH_EX):

        if '_'+fcst_var+'_' in file_s and '_'+obs_var+'_' in file_s and 'V.stat' in file_s and 'vday'+str(vday) in file_s and 'vhr'+'{:02d}'.format(int(vhr)) in file_s:

            print file_s
            
            #Initialize starting index location of data
            list_ind = []
            
            #Read the file
            file   = open(GRIB_PATH_EX+file_s, 'rb')
            lin    = file.readline()
            
            #Find the metadata structure
            for list in metadata_list_header:
                list_ind = np.append(list_ind,lin.find(list))
            
            while lin:  #Iterate f_yrmondayhrthrough file     
                lin = file.readline()
                
                #Check fcst/obs level/variable and line_type specifications
                if fcst_var == lin[int(list_ind[9]):int(list_ind[10])].strip() and \
                    fcst_lev == lin[int(list_ind[10]):int(list_ind[11])].strip() and \
                    obs_var  == lin[int(list_ind[11]):int(list_ind[12])].strip() and \
                    obs_lev  == lin[int(list_ind[12]):int(list_ind[13])].strip() and \
                    line_type  in lin[int(list_ind[21]):]:
                        
                        #Final check to see if file falls within the date bounds specified
                        datetime_temp = datetime.datetime(int(file_s[file_s.find('_e')+2:file_s.find('_e')+6]), \
                            int(file_s[file_s.find('_e')+6:file_s.find('_e')+8]), \
                            int(file_s[file_s.find('_e')+8:file_s.find('_e')+10]), \
                            int(file_s[file_s.find('_e')+10:file_s.find('_e')+12]), 0, 0)
                        julian_temp = pygrib.datetime_to_julian(datetime_temp)
                        
                        if julian_temp >= julian_beg and julian_temp <= julian_end:
                            
                            #Extract metadata from file
                            f_vday       = np.append(f_vday,float(file_s[file_s.find('vday')+4:file_s.find('vday')+5]))
                            f_yrmondayhr = np.append(f_yrmondayhr,file_s[file_s.find('_e')+2:file_s.find('_e')+12])
                            lin_temp     = lin[int(list_ind[21]):].split()
                            
                            #Extract the proper data specified in 'var_type'
                            f_data_temp = np.full([len(var_ind)],np.nan)
                            for values in range(0,len(var_ind)):
                                try:
                                    f_data_temp[values] = float(lin_temp[int(var_ind[values])])
                                except ValueError:
                                    pass
                            
                            #Concatenate the data into a permanent data source
                            if len(f_data) == 0:
                                f_data = np.concatenate((f_data,f_data_temp), axis = 0)
                            else: 
                                f_data = np.vstack((f_data,f_data_temp))
            file.close()
            
    #Sort the data by date
    sort_ind        = np.argsort(f_yrmondayhr)
    f_yrmondayhr    = f_yrmondayhr[sort_ind]
    f_vday          = f_vday[sort_ind]
    f_data          = f_data[sort_ind]

    return(f_data,f_vday,f_yrmondayhr)
    
#########################################################################################
#PracticallyPerfect creates a practically perfect grid of flooding probabilities from a 
#text file of flooding observations or proxies. This involves 2 steps: 1) Using the text 
#file, a dummy grid is created so that the flooding points can be interpolated to the grid
#using a specified neighborhood radius and 2) a smoothing is applied to the binomial field
#to create probabilities. If multiple text files are used as input, they are concatenated 
#and considered all at once. This function is designed to serve as a verification to the 
#ERO forecast probabilities. 
#
#NOTE: This function needs a dummy 2D grid to interpolate the points to. This dummy file 
#is created in the Cosgrove2txt definition. MJE. 20180411.
#
#####################INPUT FILES FOR PracticallyPerfect#######################################
#MET_PATH             = Directory for MET executibles
#GRIB_PATH_EX         = Directory where text files, dummy 2-D grid, and P-P data is to be saved
#latlon_dims          = latitude/longitude dimensions for 2-D grid [WLON,SLAT,ELON,NLAT]
#grid_delta           = grid resolution increment for 2-D grid (degrees lat/lon)    
#neigh_filter         = Radius for neighborhood technique (in km) during interpolation (array for multiple files)
#width_smo            = Sigma value for smoother (radius of smoothing in grid points) (1 value, constant for all files)
#filenames            = Array of filenames containing flooding observations/proxies
####################OUTPUT FILES FOR PracticallyPerfect#######################################
#lat                  = 2-D lat grid
#lon                  = 2-D lon grid
#DATA_SMO             = Practically perfect 2-D field
#########################################################################################

def PracticallyPerfect(MET_PATH,GRIB_PATH_EX,latlon_dims,grid_delta,neigh_filter,width_smo,filenames):

    ####################COMMENT OUT WHEN IN FUNCTION MODE#################################
    #filenames       = ['/usr1/wpc_cpgffh/gribs//WPCQPF/WPCQPF_verif_day3_ALL/WPCQPF_s2018041412_e2018041512.txt']
    #GRIB_PATH_EX    = '/usr1/wpc_cpgffh/gribs//WPCQPF/WPCQPF_verif_day3_ALL/' 
    #latlon_dims     = [-129.8,25.0,-65.0,49.8]
    #grid_delta      = 0.09
    #neigh_filter    = [5]
    #width_smo       = 18
    #####################################################################################
                    
    #Create new grid from user specifications so text file can be interpolated to it
    [lon,lat] = np.meshgrid(np.linspace(latlon_dims[0],latlon_dims[2],np.round((latlon_dims[2]-latlon_dims[0])/grid_delta,2)+1), \
        np.linspace(latlon_dims[3],latlon_dims[1],np.round((latlon_dims[3]-latlon_dims[1])/grid_delta,2)+1))
    lat = np.round(lat[::-1,0],decimals=2)
    lon = np.round(lon[0,:],   decimals=2)
    fid = Dataset(GRIB_PATH_EX+'dummy_SAMPLE.nc', 'w', format='NETCDF4_CLASSIC')
    lats  = fid.createDimension('lat', int(lat.shape[0]))
    lons  = fid.createDimension('lon', int(lon.shape[0]))
    lats  = fid.createVariable('lat', 'f8', ('lat'))
    lons  = fid.createVariable('lon', 'f8', ('lon'))    
    #Create variable attributes
    lats.long_name = "latitude"
    lats.units = "degrees_north"
    lats.standard_name = "latitude"
    lons.long_name = "longitude"
    lons.units = "degrees_east"
    lons.standard_name = "longitude"
    fid.FileOrigins = "Dummy File to Provide Gridded Lat/Lon Information"
    fid.MET_version = "V6.0"
    fid.MET_tool = "None"
    fid.RunCommand = "Regrid from Projection: Stereographic Nx: 1121 Ny: 881 IsNorthHemisphere: true Lon_orient: 105.000 Bx: 399.440 By: 1599.329 Alpha: 2496.0783 to Projection: Lat/Lon Nx: 248 Ny: 648 lat_ll: 25.100 lon_ll: 131.100 delta_lat: 0.100 delta_lon: 0.100"
    fid.Projection = "LatLon"
    fid.lat_ll = str(latlon_dims[1])+" degrees_north"
    fid.lon_ll = str(latlon_dims[0])+" degrees_east"
    fid.delta_lat = str(grid_delta)+" degrees"
    fid.delta_lon = str(grid_delta)+" degrees"
    fid.Nlat = str(lat.shape[0])+" grid_points"
    fid.Nlon = str(lon.shape[0])+" grid_points"
    #Writting data to file
    lats[:]    = lat
    lons[:]    = lon
    #Close the file
    fid.close()
                    
    #Loop through each text file creating a unique binomial grid from a unique neighborhood radius
    files_count = 0
    file_sum_txt    = []
    for files in filenames:
    
        #Use gen_vx_mask to convert text tiles to a binomial grid of flood = TRUE within x KM of a point
        subprocess.call(MET_PATH+"gen_vx_mask -type circle -thresh '<="+str(int(neigh_filter[files_count]))+"' "+GRIB_PATH_EX+"dummy_SAMPLE.nc "+ \
            files+" -name 'DATA' "+files[:-4]+".nc", stdout=open(os.devnull, 'wb'), stderr=open(os.devnull, 'wb'), shell=True)
        file_sum_txt = np.append(file_sum_txt,files[:-4]+".nc"+" 'name=\"DATA\";level=\"R1\";' ")
        files_count += 1
    
    #Invoke pcp_combine to sum all the data
    subprocess.call(MET_PATH+"pcp_combine -add "+' '.join(file_sum_txt)+" "+GRIB_PATH_EX+"combined_file.nc"+" -name ALL", \
        stdout=open(os.devnull, 'wb'), stderr=open(os.devnull, 'wb'), shell=True)

    #Load data and apply the Python Gaussian filter (no MET equivalent)
    try:
        f           = Dataset(GRIB_PATH_EX+'combined_file.nc', "a", format="NETCDF4") 
        lat         = np.tile(f.variables['lat'][:], (f.variables['lon'][:].shape[0],1)).T
        lon         = np.tile(f.variables['lon'][:], (f.variables['lat'][:].shape[0],1))
        DATA        = (f.variables['ALL'][:] > 0)*100
        DATA_SMO = gaussian_filter(DATA,width_smo/2)
        f.close()
    except:
        lat         = np.full((lat.shape[0],lon.shape[0]),np.nan)
        lon         = np.full((lat.shape[0],lon.shape[0]),np.nan)
        DATA_SMO    = np.full((lat.shape[0],lon.shape[1]),np.nan)
    #Remove unneeded files
    subprocess.call('rm -rf '+GRIB_PATH_EX+'dummy_SAMPLE.nc', stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'), shell=True)
    subprocess.call('rm -rf '+GRIB_PATH_EX+'combined_file.nc', stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'), shell=True)
    file_count = 0
    for files in filenames:
        subprocess.call('rm -rf '+file_sum_txt[file_count][0:file_sum_txt[file_count].find('.nc')+3], stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'), shell=True)
        file_count += 1

    return(lat,lon,DATA_SMO)
    
##################################################################################################
#PracticallyPerfect_NEW creates a practically perfect grid of flooding probabilities from a 
#text file of flooding observations or proxies. This involves 2 steps: 1) Using the text 
#file, a dummy grid is created so that the flooding points can be interpolated to the grid
#using a specified neighborhood radius and 2) a smoothing is applied to the binomial field
#to create probabilities. If multiple text files are used as input, P-P is computed 
#separately for each file (except for observed observations, which are summed) and averaged 
#together. This is different than PracticallyPerfect, where all data is combined and then 
#P-P is computed.
#
#NOTE: This function needs a dummy 2D grid to interpolate the points to. This dummy file 
#is created in the Cosgrove2txt definition. MJE. 20181017.
#
#####################INPUT FILES FOR PracticallyPerfect_NEW#######################################
#MET_PATH             = Directory for MET executibles
#GRIB_PATH_EX         = Directory where text files, dummy 2-D grid, and P-P data is to be saved
#latlon_dims          = latitude/longitude dimensions for 2-D grid [WLON,SLAT,ELON,NLAT]
#grid_delta           = grid resolution increment for 2-D grid (degrees lat/lon)    
#neigh_filter         = Radius for neighborhood technique (in km) during interpolation (array for multiple files)
#width_smo            = Sigma value for smoother (radius of smoothing in grid points) (1 value, constant for all files)
#filenames            = Array of filenames containing flooding observations/proxies
####################OUTPUT FILES FOR PracticallyPerfect_NEW#######################################
#lat                  = 2-D lat grid
#lon                  = 2-D lon grid
#DATA_SMO             = Practically perfect 2-D field
#########################################################################################

def PracticallyPerfect_NEW(MET_PATH,GRIB_PATH_EX,latlon_dims,grid_delta,neigh_filter,width_smo,filenames):

    ####################COMMENT OUT WHEN IN FUNCTION MODE#################################
    #filenames       = [filename_USGS,filename_LSRFLASH,filename_LSRREG,filename_WPCgFFG_txt,filename_WPCgARI_txt]
    #GRIB_PATH_EX    = '/usr1/wpc_cpgffh/gribs//WPCQPF/WPCQPF_verif_day3_ALL/' 
    #latlon_dims     = [-129.8,25.0,-65.0,49.8]
    #grid_delta      = 0.09
    #neigh_filter    = [40,40,40,10,10]
    #width_smo       = 21
    ######################################################################################
                    
    #Create new grid from user specifications so text file can be interpolated to it
    [lon,lat] = np.meshgrid(np.linspace(latlon_dims[0],latlon_dims[2],np.round((latlon_dims[2]-latlon_dims[0])/grid_delta,2)+1), \
        np.linspace(latlon_dims[3],latlon_dims[1],np.round((latlon_dims[3]-latlon_dims[1])/grid_delta,2)+1))
    lat = np.round(lat[::-1,0],decimals=2)
    lon = np.round(lon[0,:],   decimals=2)
    fid = Dataset(GRIB_PATH_EX+'dummy_SAMPLE.nc', 'w', format='NETCDF4_CLASSIC')
    lats  = fid.createDimension('lat', int(lat.shape[0]))
    lons  = fid.createDimension('lon', int(lon.shape[0]))
    lats  = fid.createVariable('lat', 'f8', ('lat'))
    lons  = fid.createVariable('lon', 'f8', ('lon'))    
    #Create variable attributes
    lats.long_name = "latitude"
    lats.units = "degrees_north"
    lats.standard_name = "latitude"
    lons.long_name = "longitude"
    lons.units = "degrees_east"
    lons.standard_name = "longitude"
    fid.FileOrigins = "Dummy File to Provide Gridded Lat/Lon Information"
    fid.MET_version = "V6.0"
    fid.MET_tool = "None"
    fid.RunCommand = "Regrid from Projection: Stereographic Nx: 1121 Ny: 881 IsNorthHemisphere: true Lon_orient: 105.000 Bx: 399.440 By: 1599.329 Alpha: 2496.0783 to Projection: Lat/Lon Nx: 248 Ny: 648 lat_ll: 25.100 lon_ll: 131.100 delta_lat: 0.100 delta_lon: 0.100"
    fid.Projection = "LatLon"
    fid.lat_ll = str(latlon_dims[1])+" degrees_north"
    fid.lon_ll = str(latlon_dims[0])+" degrees_east"
    fid.delta_lat = str(grid_delta)+" degrees"
    fid.delta_lon = str(grid_delta)+" degrees"
    fid.Nlat = str(lat.shape[0])+" grid_points"
    fid.Nlon = str(lon.shape[0])+" grid_points"
    #Writting data to file
    lats[:]    = lat
    lons[:]    = lon
    #Close the file
    fid.close()
    
    #Loop through each text file applying a neighborhood technique
    files_count = 0
    file_long_txt    = []
    for files in filenames:
        #Use gen_vx_mask to convert text tiles to a binomial grid of flood = TRUE within x KM of a point
        subprocess.call(MET_PATH+"gen_vx_mask -type circle -thresh '<="+str(int(neigh_filter[files_count]))+"' "+GRIB_PATH_EX+"dummy_SAMPLE.nc "+ \
            files+" -name 'DATA' "+files[:-4]+".nc", stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'), shell=True)
        file_long_txt = np.append(file_long_txt,files[:-4]+".nc"+" 'name=\"DATA\";level=\"R1\";' ")
        files_count += 1
        
    #Determine the files to sum and the files to mean
    sum_files     = [filenames[i] for i in range(0,len(filenames)) if 'LSR' in filenames[i] or 'USGS' in filenames[i]]
    sum_files_txt = [file_long_txt[i] for i in range(0,len(filenames)) if 'LSR' in filenames[i] or 'USGS' in filenames[i]]
    mean_files    = [filenames[i] for i in range(0,len(filenames)) if not 'LSR' in filenames[i] and not 'USGS' in filenames[i]]
    
    #Sum the observed observations together
    subprocess.call(MET_PATH+"pcp_combine -add "+' '.join(sum_files_txt)+" "+GRIB_PATH_EX+"combined_file.nc"+" -name ALL", \
            stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'), shell=True)
    
    #Initialize data matrix        
    [lon,lat] = np.meshgrid(np.linspace(latlon_dims[0],latlon_dims[2],np.round((latlon_dims[2]-latlon_dims[0])/grid_delta,2)+1), \
        np.linspace(latlon_dims[3],latlon_dims[1],np.round((latlon_dims[3]-latlon_dims[1])/grid_delta,2)+1))     
    DATA = np.full((lat.shape[0],lat.shape[1],len(mean_files)+len(sum_files)),np.NaN)
    
    #Load data and apply the Python Gaussian filter to the meaned data (no MET equivalent)
    files_count = 0
    for files in mean_files:
        
        f                     = Dataset(files[:-4]+".nc", "a", format="NETCDF4") 
        lat                   = np.tile(f.variables['lat'][:], (f.variables['lon'][:].shape[0],1)).T
        lon                   = np.tile(f.variables['lon'][:], (f.variables['lat'][:].shape[0],1))
        DATA_temp             = (f.variables['DATA'][:] > 0)*100
        f.close()
        DATA[:,:,files_count] = gaussian_filter(DATA_temp,width_smo/2)
        
        files_count += 1
        
    #Load the data that was summed (the obs) and combine with other data for averaging (no MET equivalent)
    try:
        f             = Dataset(GRIB_PATH_EX+"combined_file.nc", "a", format="NETCDF4")
        lat           = np.tile(f.variables['lat'][:], (f.variables['lon'][:].shape[0],1)).T
        lon           = np.tile(f.variables['lon'][:], (f.variables['lat'][:].shape[0],1))
        DATA_temp     = (f.variables['ALL'][:] > 0)*100
        f.close()
        DATA[:,:,-1]  = gaussian_filter(DATA_temp,width_smo/2)
    except IOError:
        pass
    
    DATA_SMO = np.nanmean(DATA,axis = 2)

    #Remove unneeded files
    subprocess.call('rm -rf '+GRIB_PATH_EX+'dummy_SAMPLE.nc', stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'), shell=True)
    subprocess.call('rm -rf '+GRIB_PATH_EX+'combined_file.nc', stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'), shell=True)
    file_count = 0
    for files in filenames:
        subprocess.call('rm -rf '+file_long_txt[file_count][0:file_long_txt[file_count].find('.nc')+3], stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'), shell=True)
        file_count += 1

    return(lat,lon,DATA_SMO)
