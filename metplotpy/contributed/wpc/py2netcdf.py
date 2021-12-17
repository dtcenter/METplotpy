#!/usr/bin/python

###################################################################################
#This function was originailly designed to convert python flash flood guidance and
#stage IV data to netCDF, so that it can be read into various MET tools. As a result
#several of the metadata variables are static, but can be adapted to be more flexible.
#
#Created by MJE. 20170623.
###################################################################################

import pygrib
import os
import subprocess
from netCDF4 import Dataset
import datetime
import numpy as np

##################################################################################
#py2netcdf_ANALY creates a netCDF file from python data. Note the method of netCDF
#creation here is crude. Based on the input data, time metadata is specified 
#between the beginning input time stamp and ending input time stamp to the 
#nearest minute. The metadata mimics MET created netCDF files, and 
#some of the descriptions are static. NetCDF file consists of lat, lon and one
#2-D variable only. 
#
#NOTE: THIS CODE IS FOR ANALYSIS DATA ONLY. USE py2netcdf_FCST to specify
#the proper init and valid times for forecast data. 20170610 - 20170705. MJE.
#
#Modified to consider minute/second data. 20190221.
#####################INPUT FILES FOR py2netcdf_ANALY#############################
# GRIB_PATH_TEMP = directory where data is stored
# latlon_dims    = latitude/longitude dimensions for plotting [WLON,SLAT,ELON,NLAT]
# grid_delta     = grid resolution increment for interpolation (degrees lat/lon)
# datetime_beg   = datetime element for beginning of time window
# datetime_end   = datetime element for end of time window
# vhr            = valid hour of forecast issuance
# lat            = array of latitude points (must be dx/dy)
# lon            = array of longitude points (must be dx/dy)
# data           = grid of data to be saved
# var_name       = string specifying netCDF name in file
# var_name_long  = string specifying netCDF long name description
####################OUTPUT FILES FOR py2netcdf_ANALY#############################
# filesave       = name of file created by py2netcdf_ANALY
###################################################################################

def py2netcdf_ANALY(GRIB_PATH_TEMP,latlon_dims,grid_delta,datetime_beg,datetime_end,vhr,lat,lon,data,var_name,var_name_long):
    
##################COMMENT OUT WHEN IN FUNCTION MODE#################################
#datetime_beg = datetime_ffg_beg
#datetime_end = datetime_ffg_end
#vhr          = 12
#lat          = lat[::-1,0]
#lon          = lon[0,:] 
#data         = flood_obs_sub[::-1,:]
#var_name     = 'ST4gFFG'
####################################################################################

    #Static metadata
    var_level     = 'Surface'
    var_units     = 'None'
    var_FillValue = '-9999.f'
    
    #Convert datetime to a string
    yrmonday_beg = ''.join(['{:04d}'.format(datetime_beg.year),'{:02d}'.format(datetime_beg.month), \
        '{:02d}'.format(datetime_beg.day)])
    hr_beg       = '{:02d}'.format(datetime_beg.hour)
    min_beg      = '{:02d}'.format(datetime_beg.minute)
    sec_beg      = '{:02d}'.format(datetime_beg.second)
    yrmonday_end = ''.join(['{:04d}'.format(datetime_end.year),'{:02d}'.format(datetime_end.month), \
        '{:02d}'.format(datetime_end.day)])
    hr_end       = '{:02d}'.format(datetime_end.hour)
    min_end      = '{:02d}'.format(datetime_end.minute)
    sec_end      = '{:02d}'.format(datetime_end.second)
    
    #Determine distance beteween start and end dates in seconds
    time_delta_totsec = datetime_end - datetime_beg 
    time_delta_totsec = (time_delta_totsec.days*24*60*60)+time_delta_totsec.seconds
    
    #Determine total hour/min/sec length
    time_delta_hr  = '{:02d}'.format(time_delta_totsec/(60*60))
    time_delta_min = '{:02d}'.format((time_delta_totsec/60) - int(time_delta_hr)*60)
    time_delta_sec = '{:02d}'.format(((time_delta_totsec) - int(time_delta_hr)*60*60 - int(time_delta_min)*60))
    
    #############Convert Data to netCDF4##################
    filesave = GRIB_PATH_TEMP+var_name+'_s'+yrmonday_beg+hr_beg+'_e'+yrmonday_end+hr_end+'_vhr'+'{:02d}'.format(int(vhr))+'.nc'
    
    subprocess.call('rm -rf '+filesave,stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'), shell=True)
    fid = Dataset(filesave, 'w', format='NETCDF4_CLASSIC')
    
    lats  = fid.createDimension('lat', int(lat.shape[0]))
    lons  = fid.createDimension('lon', int(lon.shape[0]))
    
    lats  = fid.createVariable('lat', 'f8', ('lat'))
    lons  = fid.createVariable('lon', 'f8', ('lon'))    
    datas = fid.createVariable(var_name, 'f8', ('lat','lon'))
    
    #Create variable attributes
    lats.long_name = "latitude"
    lats.units = "degrees_north"
    lats.standard_name = "latitude"
    lons.long_name = "longitude"
    lons.units = "degrees_east"
    lons.standard_name = "longitude"
    
    now = datetime.datetime.now()
    nowtime = now.strftime("%Y%m%d_%H%M%S")
    
    #fid._NCProperties = "version=1|netcdflibversion=4.4.1.1|hdf5libversion=1.10.0"
    fid.FileOrigins = "File "+filesave+" generated "+nowtime+" UTC via Python"
    fid.MET_version = "V6.0"
    fid.MET_tool = "None"
    #fid.RunCommand = "Regrid from Projection: Stereographic Nx: 1121 Ny: 881 IsNorthHemisphere: true Lon_orient: 105.000 Bx: 399.440 By: 1599.329 Alpha: 2496.0783 to Projection: Lat/Lon Nx: 248 Ny: 648 lat_ll: 25.100 lon_ll: 131.100 delta_lat: 0.100 delta_lon: 0.100"
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
    datas[:]   = data

    #Further specify metdata
    datas.FillValue = var_FillValue
    datas.long_name = var_name_long
    datas.level = var_level
    datas.units = var_units
    datas.init_time = yrmonday_beg+'_'+hr_beg+min_beg+sec_beg
    #datas.init_time_ut = str(int((((pygrib.datetime_to_julian(datetime_beg)) \
    #    -pygrib.datetime_to_julian(datetime.datetime(1970,1,1,0,0,0)))*24*60*60)+3600))
    datas.init_time_ut = str(int(np.round((((pygrib.datetime_to_julian(datetime_beg)) \
        -pygrib.datetime_to_julian(datetime.datetime(1970,1,1,0,0,0)))*24*60*60)))) 
    #datas.valid_time = yrmonday_beg+'_'+hr_end+'0000'
    datas.valid_time = yrmonday_end+'_'+hr_end+min_end+sec_end
    
    #datas.valid_time_ut = str(int((((pygrib.datetime_to_julian(datetime_beg))-pygrib.datetime_to_julian(datetime.datetime(1970,1,1,0,0,0)))*24*60*60)))
    datas.valid_time_ut = str(int(np.round((((pygrib.datetime_to_julian(datetime_beg+datetime.timedelta(seconds = int(time_delta_totsec)))) \
        -pygrib.datetime_to_julian(datetime.datetime(1970,1,1,0,0,0)))*24*60*60))))
    datas.accum_time = time_delta_hr+time_delta_min+time_delta_sec
    datas.accum_time_sec = int(time_delta_totsec)
    
    #Close the file
    fid.close()
    
    return(filesave)

##################################################################################
#py2netcdf_FCST creates a netCDF file from python data. Note the method of netCDF
#creation here is crude. This file uses 'datetime_init' to create an initialization
#time, 'datetime_valid' to create a valid date time, and 'pre_acc' to fill in the
#accumulation interval to the nearest minute. This is different from py2netcdf_ANALY
#in treating differently analysis data (same init and valid time) and forecast
#data (different init and valid time). The metadata mimics MET created 
#netCDF files, and some of the descriptions are static. NetCDF file consists 
#of lat, lon and one 2-D variable only. 20190201-20190307. MJE.
#
#Modified to consider minute/second data. 20190221.
#####################INPUT FILES FOR py2netcdf_FCST#############################
# GRIB_PATH_TEMP = directory where data is stored
# latlon_dims    = latitude/longitude dimensions for plotting [WLON,SLAT,ELON,NLAT]
# grid_delta     = grid resolution increment for interpolation (degrees lat/lon)
# datetime_beg   = datetime element for beginning of time window
# datetime_end   = datetime element for end of time window
# vhr            = valid hour of forecast issuance
# lat            = array of latitude points (must be dx/dy)
# lon            = array of longitude points (must be dx/dy)
# data           = grid of data to be saved
# var_name       = string specifying netCDF name in file
# var_name_long  = string specifying netCDF long name description
####################OUTPUT FILES FOR py2netcdf_FCST#############################
# filesave       = name of file created by py2netcdf_FCST
###################################################################################

def py2netcdf_FCST(GRIB_PATH_TEMP,latlon_dims,grid_delta,datetime_init,datetime_end,pre_acc,vhr,lat,lon,data,var_name,var_name_long):

##################COMMENT OUT WHEN IN FUNCTION MODE#################################
#datetime_init= datetime_ffg_init
#datetime_end = datetime_ffg_end
#vhr          = 12
#lat          = lat[::-1,0]
#lon          = lon[0,:] 
#data         = flood_obs_sub[::-1,:]
#var_name     = 'ST4gFFG'
####################################################################################

    #Static metadata
    var_level     = 'Surface'
    var_units     = 'None'
    var_FillValue = '-9999.f'

    #Calculate accumulation interval in seconds
    pre_acc_sec = int(pre_acc[0:2])*60*60+int(pre_acc[2:4])*60+int(pre_acc[4:6])
    
    #Convert datetime to a string for initialization time
    yrmonday_init = ''.join(['{:04d}'.format(datetime_init.year),'{:02d}'.format(datetime_init.month), \
        '{:02d}'.format(datetime_init.day)])
    hr_init       = '{:02d}'.format(datetime_init.hour)
    min_init      = '{:02d}'.format(datetime_init.minute)
    sec_init      = '{:02d}'.format(datetime_init.second)
    
    #Convert datetime to a string for beginning of accumulation interval
    datetime_beg = datetime_end - datetime.timedelta(seconds = pre_acc_sec)
    yrmonday_beg = ''.join(['{:04d}'.format(datetime_beg.year),'{:02d}'.format(datetime_beg.month), \
        '{:02d}'.format(datetime_beg.day)])
    hr_beg       = '{:02d}'.format(datetime_beg.hour)
    min_beg      = '{:02d}'.format(datetime_beg.minute)
    sec_beg      = '{:02d}'.format(datetime_beg.second)
    
    #Convert datetime to a string for end of accumulation interval
    yrmonday_end = ''.join(['{:04d}'.format(datetime_end.year),'{:02d}'.format(datetime_end.month), \
        '{:02d}'.format(datetime_end.day)])
    hr_end       = '{:02d}'.format(datetime_end.hour)
    min_end      = '{:02d}'.format(datetime_end.minute)
    sec_end      = '{:02d}'.format(datetime_end.second)
    

    
    #Determine distance beteween start and end dates in seconds
    time_delta_totsec = datetime_end - datetime_beg 
    time_delta_totsec = (time_delta_totsec.days*24*60*60)+time_delta_totsec.seconds
    
    #Determine total hour/min/sec length
    time_delta_hr  = '{:02d}'.format(time_delta_totsec/(60*60))
    time_delta_min = '{:02d}'.format((time_delta_totsec/60) - int(time_delta_hr)*60)
    time_delta_sec = '{:02d}'.format(((time_delta_totsec) - int(time_delta_hr)*60*60 - int(time_delta_min)*60))
    
    #############Convert Data to netCDF4##################
    filesave = GRIB_PATH_TEMP+var_name+'_s'+yrmonday_beg+hr_beg+'_e'+yrmonday_end+hr_end+'_vhr'+'{:02d}'.format(int(vhr))+'.nc'
    
    subprocess.call('rm -rf '+filesave,stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'), shell=True)
    fid = Dataset(filesave, 'w', format='NETCDF4_CLASSIC')
    
    lats  = fid.createDimension('lat', int(lat.shape[0]))
    lons  = fid.createDimension('lon', int(lon.shape[0]))
    
    lats  = fid.createVariable('lat', 'f8', ('lat'))
    lons  = fid.createVariable('lon', 'f8', ('lon'))    
    datas = fid.createVariable(var_name, 'f8', ('lat','lon'))
    
    #Create variable attributes
    lats.long_name = "latitude"
    lats.units = "degrees_north"
    lats.standard_name = "latitude"
    lons.long_name = "longitude"
    lons.units = "degrees_east"
    lons.standard_name = "longitude"
    
    now = datetime.datetime.now()
    nowtime = now.strftime("%Y%m%d_%H%M%S")
    
    #fid._NCProperties = "version=1|netcdflibversion=4.4.1.1|hdf5libversion=1.10.0"
    fid.FileOrigins = "File "+filesave+" generated "+nowtime+" UTC via Python"
    fid.MET_version = "V6.0"
    fid.MET_tool = "None"
    #fid.RunCommand = "Regrid from Projection: Stereographic Nx: 1121 Ny: 881 IsNorthHemisphere: true Lon_orient: 105.000 Bx: 399.440 By: 1599.329 Alpha: 2496.0783 to Projection: Lat/Lon Nx: 248 Ny: 648 lat_ll: 25.100 lon_ll: 131.100 delta_lat: 0.100 delta_lon: 0.100"
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
    datas[:]   = data

    #Further specify metdata
    datas.FillValue = var_FillValue
    datas.long_name = var_name_long
    datas.level = var_level
    datas.units = var_units
    datas.init_time = yrmonday_init+'_'+hr_init+min_init+sec_init
    #datas.init_time_ut = str(int((((pygrib.datetime_to_julian(datetime_beg)) \
    #    -pygrib.datetime_to_julian(datetime.datetime(1970,1,1,0,0,0)))*24*60*60)+3600))
    datas.init_time_ut = str(int(np.round((((pygrib.datetime_to_julian(datetime_init)) \
        -pygrib.datetime_to_julian(datetime.datetime(1970,1,1,0,0,0)))*24*60*60)))) 
    #datas.valid_time = yrmonday_beg+'_'+hr_end+'0000'
    datas.valid_time = yrmonday_end+'_'+hr_end+min_end+sec_end
    
    #datas.valid_time_ut = str(int((((pygrib.datetime_to_julian(datetime_beg))-pygrib.datetime_to_julian(datetime.datetime(1970,1,1,0,0,0)))*24*60*60)))
    datas.valid_time_ut = str(int(np.round((((pygrib.datetime_to_julian(datetime_end)) \
        -pygrib.datetime_to_julian(datetime.datetime(1970,1,1,0,0,0)))*24*60*60))))
    datas.accum_time = time_delta_hr+time_delta_min+time_delta_sec
    datas.accum_time_sec = int(time_delta_totsec)
    
    #Close the file
    fid.close()
    
    return(filesave)
