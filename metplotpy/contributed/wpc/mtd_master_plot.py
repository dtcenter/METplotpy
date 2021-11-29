#!/usr/bin/python

################################################################################################
#USING THE OUTPUT FROM 'mtd_master.save,' THIS SCRIPT LOADS THE MTD RESULTS SAVED IN THE LAST
#FUNCTION, COLLECTS, AGGREGATES, AND PLOTS THE DATA IN MANY DIFFERENT FORMATS. NOTE THIS CODE
#CAN BE RUN IN FIVE MODES, DETERMINED BY 'subset_data': 1) 'SIMP' TO PLOT SIMPLE OBJECTS 
#2) 'PAIR' PAIRED OBJECTS 3) 'PAIRinit' INITIATION OF PAIRED OBJECTS, 4) 'PAIRdisp' DISSIPATION 
#OF PAIRED OBJECTS 5) POYgPMY (PROBABILITY OF OBSERVATION 'YES' GIVEN MODEL OCCURS).
#NOTE THAT THIS FUNCTION CAN LOAD MULTIPLE MODELS/MEMBERS THROUGH 'load_model'
#AS LONG AS THEY ARE IN THE SAME DIRECTORY SPECIFIED BY 'GRIB_PATH_DES.' CREATED: 20171107 - 20171124. MJE.
#
# UPDATE: MODIFIED TO FIX BUGS, ADD SUBSET BY FORECAST HOUR, AND STATISTICAL SIGNIFICANCE. 20171205. MJE
# UPDATE: FIXED MINOR PLOTTING BUGS AND ADDED FLEXIBILITY WITH WoFS SUBHOURLY DATA. 20191114. MJE.
# UPDATE: ADDED ADDITIONAL PLOTTING CAPABILITIES, REORGANIZED CODE, AND ADDED POYgPMY. 20210202. MJE.
# Update: Addition to code to allow saving of simple operational objects for bias look-up tables
# and improving functionality to the way data is loaded. MJE. 20210323.
# Update: Added seasonal subset capability to dates loaded. MJE. 20210324.
################################################################################################

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
import copy
import cartopy.feature as cf
import cartopy.crs as ccrs
import importlib
import matplotlib as mpl
mpl.use('Agg') #So plots can be saved in cron
import matplotlib.pyplot as plt
from windrose import WindroseAxes
import matplotlib.cm as cm
from scipy.io import netcdf
from netCDF4 import Dataset
from scipy import ndimage
from scipy import stats
from scipy import interpolate
from mpl_toolkits.axes_grid1 import make_axes_locatable
from scipy.ndimage.filters import gaussian_filter

#Load predefined functions
sys.path.append('/export/hpc-lw-dtbdev5/merickson/code/python/MET')
import METConFigGenV100
import METLoadEnsemble
import METPlotEnsemble
import haversine
import METConFigGen
importlib.reload(METConFigGenV100)
importlib.reload(METLoadEnsemble)
importlib.reload(METPlotEnsemble)
sys.path.append('/export/hpc-lw-dtbdev5/merickson/code/python/ERO')
import loadAllEROData
import cartopy_maps
importlib.reload(loadAllEROData)

################################################################################
#########################1)MATRIX OF VARIABLES#################################
################################################################################
GRIB_PATH      = '/export/hpc-lw-dtbdev5/wpc_cpgffh/gribs/'              #Location of model GRIB files
FIG_PATH       = '/export/hpc-lw-dtbdev5/wpc_cpgffh/figures/MET/RETRO/'  #Location for figure generation
TRACK_PATH     = '/export/hpc-lw-dtbdev5/wpc_cpgffh/tracks/'             #Location for saving track files
beg_date       = datetime.datetime(2019,11,14,0,0,0)                       #Beginning time of retrospective runs (datetime element)
end_date       = datetime.datetime(2019,11,15,18,0,0)                      #Ending time of retrospective runs (datetime element)
init_inc       = 1                                                       #Initialization increment (hours; e.g. total hours between model init. cycles)
season_sub     = [5,6,7,8]                                               #Seasonally subset the data by month (array of months to keep)
latlon_dims    = [-126,23,-65,50]                                        #Latitude/longitude dimensions for plotting [WLON,SLAT,ELON,NLAT]
subset_data    = 'PAIR'                                                  #'SIMP'=simple,'PAIR'=paired,'PAIRdisp'=diss,'PAIRinit'=init,'POYgPMY' = Prob Obs Yes Given Prob Mod Yes
pre_acc        = 1.0                                                     #Precipitation accumulation total
total_fcst_hrs = 18.0                                                    #Last forecast hour to be considered
start_hrs      = 0.0                                                     #Skip hours ahead before running MET                                                 
thres          = 0.1                                                     #Precip. threshold for defining objects (inches) (specifiy single value)
pctile         = 80                                                      #Range percentile in some plots to convey uncertainity
grid_res_nat   = []                                                       #Grid resolution (degrees) of the native grid. If =[], everything is aggregated spatially
grid_res_agg   = []                                                       #Grid resolution (degrees) of the aggregated grid. If =[], everything is aggregated spatially
stat_size      = 1                                                       #Minimum number of observations per grid point to plot statistics
stat_tvalue    = 0.01                                                    #Minimum p-value to plot statistical significance
subset_dhours   = [np.arange(0,24,pre_acc)]
subset_fhours   = []                                                     #Create plots for specific forecast hours in array (e.g. f12-f18; NOTE CAN ONLY SPECIFY fhours OR dhours)
#subset_dhours   = []
#subset_fhours   = [np.arange(7,13,pre_acc),np.arange(13,19,pre_acc)]
GRIB_PATH_DES  = 'MTD_RETRO_HRRRv4_t'+str(thres)                         #An appended string label for the temporary directory name
load_model     = ['HRRRv4_lag00']                                        #An array of the model to be loaded, or for ensembles, one or multiple members
os.environ["LIBS"] = "/opt/MET/METPlus4_0/external_libs"
os.environ["LD_LIBRARY_PATH"] ="/opt/MET/METPlus4_0/external_libs/lib:/export-5/ncosrvnfs-cp/nawips2/os/linux2.6.32_x86_64/lib:/lib:/usr/lib:/export-5/ncosrvnfs-cp/nawips3/os/linux2.6.32_x86_64/lib:/export/hpc-lw-dtbdev5/merickson/Canopy/appdata/canopy-1.7.2.3327.rh5-x86_64/lib:/usr/lib64/openmpi/lib/"
################################################################################
######################2)PREPARE THE DATA FOR LOADING############################
################################################################################

#Adjust beginning and end dates to proper ranges given 'init_inc'
beg_date = beg_date + datetime.timedelta(hours = (init_inc-beg_date.hour%init_inc)*(beg_date.hour%init_inc>0))
end_date = end_date - datetime.timedelta(hours = end_date.hour%init_inc)

#Throw an error if 'end_date' is before 'beg_date'
if (end_date - beg_date).days < 0:
    raise ValueError("'end_date' is before 'beg_date'")

#Check for errors in the code
if len(subset_fhours) != 0 and len(subset_dhours) != 0:
    raise ValueError('Only \'subset_fhours\' or \'subset_dhours\' contain data, but not both. The other must be specified as blank')

#If either the aggregated or native grid resolution is blank, they are both blank and everything is aggregated throughout the domain
if grid_res_nat == [] or grid_res_agg == []:
    grid_res_nat = []
    grid_res_agg = []

#If the aggregation search radius is less than the native resolution grid, set them as equal
if grid_res_agg < grid_res_nat:
    grid_res_agg = grid_res_nat
    
subset_hours = []
plot_str     = []
lab_str      = []
#For plotting, specify forecast or diurnal hours in figure name and identify proper index for extracting hourly data in data pull
if subset_fhours != []:
    hour_index   = 0
    if grid_res_agg != []:
        subset_hours = subset_fhours
        for hrs in range(0,len(subset_fhours)):
            plot_str     = np.append(plot_str,'F'+str(subset_fhours[hrs][0])+'toF'+str(subset_fhours[hrs][-1]))
            lab_str      = np.append(lab_str,'Forecast Hour')
    elif grid_res_agg == []:
        for sublist in subset_fhours:
            for item in sublist:
                subset_hours = np.append(subset_hours,item)
        plot_str     = np.append(plot_str,'F'+str(subset_hours[0])+'toF'+str(subset_hours[-1]))
        lab_str      = np.append(lab_str,'Forecast Hour')
        
if subset_dhours != []:
    hour_index   = 1
    if grid_res_agg != [] :
        subset_hours = subset_dhours
        for hrs in range(0,len(subset_dhours)):
            plot_str     = np.append(plot_str,'D'+str(subset_dhours[hrs][0])+'toD'+str(subset_dhours[hrs][-1]))
            lab_str      = np.append(lab_str,'Diurnal Hour')
    elif grid_res_agg == [] and subset_dhours != []:
        for sublist in subset_dhours:
            for item in sublist:
                subset_hours = np.append(subset_hours,item)
        plot_str     = np.append(plot_str,'D'+str(subset_hours[0])+'toD'+str(subset_hours[-1]))
        lab_str      = np.append(lab_str,'Diurnal Hour')

#Create string for grid resolution
if grid_res_agg == []:
    grid_res_agg_str = 'ALL'
else:
    grid_res_agg_str = str(grid_res_agg)
 
#If grid domain is specified create grid/CONUSmask
if grid_res_nat != []:
    [lon_nat,lat_nat] = np.meshgrid(np.linspace(latlon_dims[0],latlon_dims[2],int(np.round((latlon_dims[2]-latlon_dims[0])/grid_res_nat,2)+1)), \
        np.linspace(latlon_dims[3],latlon_dims[1],int(np.round((latlon_dims[3]-latlon_dims[1])/grid_res_nat,2)+1)))   
    (CONUSmask,lat,lon) = loadAllEROData.readCONUSmask(GRIB_PATH,latlon_dims,grid_res_nat)
    CONUSmask[np.isnan(CONUSmask)] = 0
    #Interpolate mask to new grid since they are 1 degree off from each other and smooth to capture the slightly offshore regions
    CONUSmask = interpolate.griddata(np.stack((lon.flatten(),lat.flatten()),axis=1),CONUSmask.flatten(),(lon-grid_res_nat/2,lat+grid_res_nat/2),method='nearest')
    CONUSmask = gaussian_filter(CONUSmask,0.5) >= 0.10
else: #Create a grid where everything is spatially aggregated to one point
    lon_nat=np.array([[latlon_dims[0],latlon_dims[2]],[latlon_dims[0],latlon_dims[2]]])
    lat_nat=np.array([[latlon_dims[3],latlon_dims[3]],[latlon_dims[1],latlon_dims[1]]])
    CONUSmask = np.ones((lat_nat.shape))

#Create start/end date strings
beg_date_str_sh = '{:04d}'.format(beg_date.year)+ \
    '{:02d}'.format(beg_date.month)+'{:02d}'.format(beg_date.day)
end_date_str_sh = '{:04d}'.format(end_date.year)+ \
    '{:02d}'.format(end_date.month)+'{:02d}'.format(end_date.day)
beg_date_str_lo = '{:02d}'.format(beg_date.hour)+' UTC '+'{:04d}'.format(beg_date.year)+ \
    '{:02d}'.format(beg_date.month)+'{:02d}'.format(beg_date.day)
end_date_str_lo = '{:02d}'.format(end_date.hour)+' UTC '+'{:04d}'.format(end_date.year)+ \
    '{:02d}'.format(end_date.month)+'{:02d}'.format(end_date.day)

#Create datetime list of all model initializations to be loaded
delta = end_date - beg_date
total_incs = int(((delta.days * 24) + (delta.seconds / 3600) - 1) / init_inc)
list_date = []
for i in range(total_incs+1):
    if (beg_date + datetime.timedelta(hours = i * init_inc)).month in season_sub:
        list_date = np.append(list_date,beg_date + datetime.timedelta(hours = i * init_inc))

################################################################################
##########3) LOAD DATA NEEDED FOR PROCESSING####################################
################################################################################
if 'SIMP' in subset_data:
    [grid_obs_sing,grid_mod_sing,simp_prop_count,data_exist_sum] = METLoadEnsemble.load_simp_prop(TRACK_PATH,GRIB_PATH_DES,load_model,list_date, \
        start_hrs,total_fcst_hrs,pre_acc,thres,lat_nat,lon_nat,grid_res_agg)
elif 'PAIR' in subset_data:
    [grid_pair,grid_init,grid_disp,pair_prop_count,data_exist_sum] = METLoadEnsemble.load_pair_prop(TRACK_PATH,GRIB_PATH_DES,load_model,list_date, \
        start_hrs,total_fcst_hrs,pre_acc,thres,lat_nat,lon_nat,grid_res_agg)      
elif 'POYgPMY'.lower() in subset_data.lower():
    [grid_POYgPMY,simp_prop_count,data_exist_sum] = METLoadEnsemble.load_pair_POYgPMY(TRACK_PATH,GRIB_PATH_DES,load_model,list_date, \
        start_hrs,total_fcst_hrs,pre_acc,thres,lat_nat,lon_nat,grid_res_agg)

################################################################################
###########4) AGGREGATE ALL SPATIAL STATISTICS TO A COARSER GRID FOR PLOTTING###
################################################################################

if subset_data == 'SIMP':   
    
    #Aggregate for unpaired objects
    grid_mod_int10mean  = np.full([lat_nat.shape[0], lon_nat.shape[1], len(subset_hours)],np.nan)
    grid_mod_int50mean  = np.full([lat_nat.shape[0], lon_nat.shape[1], len(subset_hours)],np.nan)
    grid_mod_int90mean  = np.full([lat_nat.shape[0], lon_nat.shape[1], len(subset_hours)],np.nan)
    grid_mod_areamean   = np.full([lat_nat.shape[0], lon_nat.shape[1], len(subset_hours)],np.nan)
    grid_mod_angmean    = np.full([lat_nat.shape[0], lon_nat.shape[1], len(subset_hours)],np.nan)
    grid_mod_count      = np.full([lat_nat.shape[0], lon_nat.shape[1], len(subset_hours)],np.nan)
    grid_obs_int10mean  = np.full([lat_nat.shape[0], lon_nat.shape[1], len(subset_hours)],np.nan)
    grid_obs_int50mean  = np.full([lat_nat.shape[0], lon_nat.shape[1], len(subset_hours)],np.nan)
    grid_obs_int90mean  = np.full([lat_nat.shape[0], lon_nat.shape[1], len(subset_hours)],np.nan)
    grid_obs_areamean   = np.full([lat_nat.shape[0], lon_nat.shape[1], len(subset_hours)],np.nan)
    grid_obs_angmean    = np.full([lat_nat.shape[0], lon_nat.shape[1], len(subset_hours)],np.nan)
    grid_obs_count      = np.full([lat_nat.shape[0], lon_nat.shape[1], len(subset_hours)],np.nan)
    grid_diff_int10mean = np.full([lat_nat.shape[0], lon_nat.shape[1], len(subset_hours)],np.nan)
    grid_diff_int50mean = np.full([lat_nat.shape[0], lon_nat.shape[1], len(subset_hours)],np.nan)
    grid_diff_int90mean = np.full([lat_nat.shape[0], lon_nat.shape[1], len(subset_hours)],np.nan)
    grid_diff_areamean  = np.full([lat_nat.shape[0], lon_nat.shape[1], len(subset_hours)],np.nan)
    grid_diff_angmean   = np.full([lat_nat.shape[0], lon_nat.shape[1], len(subset_hours)],np.nan)
    grid_diff_count     = np.full([lat_nat.shape[0], lon_nat.shape[1], len(subset_hours)],np.nan)

    grid_mod_int10std   = np.full([lat_nat.shape[0], lon_nat.shape[1], len(subset_hours), 2],np.nan)
    grid_mod_int50std   = np.full([lat_nat.shape[0], lon_nat.shape[1], len(subset_hours), 2],np.nan)
    grid_mod_int90std   = np.full([lat_nat.shape[0], lon_nat.shape[1], len(subset_hours), 2],np.nan)
    grid_mod_areastd    = np.full([lat_nat.shape[0], lon_nat.shape[1], len(subset_hours), 2],np.nan)
    grid_mod_angstd     = np.full([lat_nat.shape[0], lon_nat.shape[1], len(subset_hours), 2],np.nan)
    grid_obs_int10std   = np.full([lat_nat.shape[0], lon_nat.shape[1], len(subset_hours), 2],np.nan)
    grid_obs_int50std   = np.full([lat_nat.shape[0], lon_nat.shape[1], len(subset_hours), 2],np.nan)
    grid_obs_int90std   = np.full([lat_nat.shape[0], lon_nat.shape[1], len(subset_hours), 2],np.nan)
    grid_obs_areastd    = np.full([lat_nat.shape[0], lon_nat.shape[1], len(subset_hours), 2],np.nan)
    grid_obs_angstd     = np.full([lat_nat.shape[0], lon_nat.shape[1], len(subset_hours), 2],np.nan)
    grid_diff_int10std  = np.full([lat_nat.shape[0], lon_nat.shape[1], len(subset_hours), 2],np.nan)
    grid_diff_int50std  = np.full([lat_nat.shape[0], lon_nat.shape[1], len(subset_hours), 2],np.nan)
    grid_diff_int90std  = np.full([lat_nat.shape[0], lon_nat.shape[1], len(subset_hours), 2],np.nan)
    grid_diff_areastd   = np.full([lat_nat.shape[0], lon_nat.shape[1], len(subset_hours), 2],np.nan)
    grid_diff_angstd    = np.full([lat_nat.shape[0], lon_nat.shape[1], len(subset_hours), 2],np.nan)

    for yloc in range(0,lat_nat.shape[0]):
        for xloc in range(0,lat_nat.shape[1]):
            for hr_p in range(0,len(subset_hours)): #For each hour increment to be considered

                if len(grid_mod_sing[yloc][xloc]) > 0:
                    
                    #Extract all elements and conditionalize by hour
                    hr_mod      = np.array([i[5+hour_index] for i in grid_mod_sing[yloc][xloc]])
                    int10_mod   = np.array([i[0] for i in grid_mod_sing[yloc][xloc]])
                    int50_mod   = np.array([i[1] for i in grid_mod_sing[yloc][xloc]])
                    int90_mod   = np.array([i[2] for i in grid_mod_sing[yloc][xloc]])
                    area_mod    = np.array([i[3] for i in grid_mod_sing[yloc][xloc]])
                    ang_mod     = np.array([i[4] for i in grid_mod_sing[yloc][xloc]])

                    #Fine if element of 1st array is present in 2nd.
                    #NEWER python use isin
                    subset_hr = np.in1d(hr_mod,subset_hours[hr_p])
                    
                    #Subset hour in new data
                    hr_mod      = hr_mod[subset_hr]
                    int10_mod = int10_mod[subset_hr]
                    int50_mod = int50_mod[subset_hr]
                    int90_mod = int90_mod[subset_hr]
                    area_mod  = area_mod[subset_hr]
                    ang_mod   = ang_mod[subset_hr]
                    
                    #Subset the data and compute median
                    grid_mod_int10mean[yloc,xloc,hr_p] = np.nanmedian(int10_mod)
                    grid_mod_int50mean[yloc,xloc,hr_p] = np.nanmedian(int50_mod)
                    grid_mod_int90mean[yloc,xloc,hr_p] = np.nanmedian(int90_mod)
                    grid_mod_areamean[yloc,xloc,hr_p]  = np.nanmedian(area_mod)
                    grid_mod_angmean[yloc,xloc,hr_p]   = np.nanmedian(ang_mod)
                    
                    grid_mod_int10std[yloc,xloc,hr_p,0]  = np.nanpercentile(int10_mod,100-pctile)
                    grid_mod_int10std[yloc,xloc,hr_p,1]  = np.nanpercentile(int10_mod,pctile)
                    grid_mod_int50std[yloc,xloc,hr_p,0]  = np.nanpercentile(int50_mod,100-pctile)
                    grid_mod_int50std[yloc,xloc,hr_p,1]  = np.nanpercentile(int50_mod,pctile)
                    grid_mod_int90std[yloc,xloc,hr_p,0]  = np.nanpercentile(int90_mod,100-pctile)
                    grid_mod_int90std[yloc,xloc,hr_p,1]  = np.nanpercentile(int90_mod,pctile)
                    grid_mod_areastd[yloc,xloc,hr_p,0]   = np.nanpercentile(area_mod,100-pctile)
                    grid_mod_areastd[yloc,xloc,hr_p,1]   = np.nanpercentile(area_mod,pctile)
                    grid_mod_angstd[yloc,xloc,hr_p,0]    = np.nanpercentile(ang_mod,100-pctile)
                    grid_mod_angstd[yloc,xloc,hr_p,1]    = np.nanpercentile(ang_mod,pctile)
                    
                    grid_mod_count[yloc,xloc,hr_p] = len(ang_mod)
                else:
                    hr_mod = []
                    
                if len(grid_obs_sing[yloc][xloc]) > 0:
                    
                    #Extract all elements and conditionalize by hour
                    hr_obs    = np.array([i[5+hour_index] for i in grid_obs_sing[yloc][xloc]])
                    int10_obs = np.array([i[0] for i in grid_obs_sing[yloc][xloc]])
                    int50_obs = np.array([i[1] for i in grid_obs_sing[yloc][xloc]])
                    int90_obs = np.array([i[2] for i in grid_obs_sing[yloc][xloc]])
                    area_obs  = np.array([i[3] for i in grid_obs_sing[yloc][xloc]])
                    ang_obs   = np.array([i[4] for i in grid_obs_sing[yloc][xloc]])

                    #Fine if element of 1st array is present in 2nd.
                    #NEWER python use isin
                    subset_hr = np.in1d(hr_obs,subset_hours[hr_p]) 
                    
                    #Subset hour in new data
                    hr_obs    = hr_obs[subset_hr]
                    int10_obs = int10_obs[subset_hr]
                    int50_obs = int50_obs[subset_hr]
                    int90_obs = int90_obs[subset_hr]
                    area_obs  = area_obs[subset_hr]
                    ang_obs   = ang_obs[subset_hr]
                    
                    #Subset the data and compute median
                    grid_obs_int10mean[yloc,xloc,hr_p] = np.nanmedian(int10_obs)
                    grid_obs_int50mean[yloc,xloc,hr_p] = np.nanmedian(int50_obs)
                    grid_obs_int90mean[yloc,xloc,hr_p] = np.nanmedian(int90_obs)
                    grid_obs_areamean[yloc,xloc,hr_p]  = np.nanmedian(area_obs)
                    grid_obs_angmean[yloc,xloc,hr_p]   = np.nanmedian(ang_obs)


                    grid_obs_int10std[yloc,xloc,hr_p,0] = np.nanpercentile(int10_obs,100-pctile)
                    grid_obs_int10std[yloc,xloc,hr_p,1] = np.nanpercentile(int10_obs,pctile)
                    grid_obs_int50std[yloc,xloc,hr_p,0] = np.nanpercentile(int50_obs,100-pctile)
                    grid_obs_int50std[yloc,xloc,hr_p,1] = np.nanpercentile(int50_obs,pctile)
                    grid_obs_int90std[yloc,xloc,hr_p,0] = np.nanpercentile(int90_obs,100-pctile)
                    grid_obs_int90std[yloc,xloc,hr_p,1] = np.nanpercentile(int90_obs,pctile)
                    grid_obs_areastd[yloc,xloc,hr_p,0]  = np.nanpercentile(area_obs,100-pctile)
                    grid_obs_areastd[yloc,xloc,hr_p,1]  = np.nanpercentile(area_obs,pctile)
                    grid_obs_angstd[yloc,xloc,hr_p,0]   = np.nanpercentile(ang_obs,100-pctile)
                    grid_obs_angstd[yloc,xloc,hr_p,1]   = np.nanpercentile(ang_obs,pctile)
                    
                    grid_obs_count[yloc,xloc,hr_p]     = len(ang_obs)
                    
                else:
                    hr_obs = []
                    
                #Perform a 2-sided t-test for the difference between two means
                if (len(hr_mod) > 1) & (len(hr_obs) > 1):

                    if stats.ttest_ind(int10_mod,int10_obs).pvalue < stat_tvalue or grid_res_nat == []:
                        grid_diff_int10mean[yloc,xloc,hr_p] = np.nanmedian(int10_mod) - np.nanmedian(int10_obs)
                    if stats.ttest_ind(int50_mod,int50_obs).pvalue < stat_tvalue or grid_res_nat == []:
                        grid_diff_int50mean[yloc,xloc,hr_p] = np.nanmedian(int50_mod) - np.nanmedian(int50_obs)
                    if stats.ttest_ind(int90_mod,int90_obs).pvalue < stat_tvalue or grid_res_nat == []:
                        grid_diff_int90mean[yloc,xloc,hr_p] = np.nanmedian(int90_mod) - np.nanmedian(int90_obs)
                    if stats.ttest_ind(area_mod,area_obs).pvalue < stat_tvalue or grid_res_nat == []:
                        grid_diff_areamean[yloc,xloc,hr_p]    = np.nanmedian(area_mod) - np.nanmedian(area_obs)
                    if stats.ttest_ind(ang_mod,ang_obs).pvalue < stat_tvalue or grid_res_nat == []:
                        grid_diff_angmean[yloc,xloc,hr_p]     = np.nanmedian(ang_mod) - np.nanmedian(ang_obs)
                        
                    grid_diff_count[yloc,xloc,hr_p]       = len(ang_mod) - len(ang_obs)

    #Apply CONUS mask
    for hr_p in range(0,grid_mod_int90mean.shape[2]):
        grid_mod_int10mean[:,:,hr_p]  = grid_mod_int10mean[:,:,hr_p] * CONUSmask
        grid_mod_int50mean[:,:,hr_p]  = grid_mod_int50mean[:,:,hr_p] * CONUSmask
        grid_mod_int90mean[:,:,hr_p]  = grid_mod_int90mean[:,:,hr_p] * CONUSmask
        grid_obs_int10mean[:,:,hr_p]  = grid_obs_int10mean[:,:,hr_p] * CONUSmask
        grid_obs_int50mean[:,:,hr_p]  = grid_obs_int50mean[:,:,hr_p] * CONUSmask
        grid_obs_int90mean[:,:,hr_p]  = grid_obs_int90mean[:,:,hr_p] * CONUSmask
        grid_mod_areamean[:,:,hr_p]   = grid_mod_areamean[:,:,hr_p] * CONUSmask
        grid_obs_areamean[:,:,hr_p]   = grid_obs_areamean[:,:,hr_p]* CONUSmask
        grid_mod_angmean[:,:,hr_p]    = grid_mod_angmean[:,:,hr_p] * CONUSmask
        grid_obs_angmean[:,:,hr_p]    = grid_obs_angmean[:,:,hr_p] * CONUSmask
        grid_mod_count[:,:,hr_p]      = grid_mod_count[:,:,hr_p] * CONUSmask
        grid_obs_count[:,:,hr_p]      = grid_obs_count[:,:,hr_p] * CONUSmask
        grid_diff_int10mean[:,:,hr_p] = grid_diff_int10mean[:,:,hr_p] * CONUSmask
        grid_diff_int50mean[:,:,hr_p] = grid_diff_int50mean[:,:,hr_p] * CONUSmask
        grid_diff_int90mean[:,:,hr_p] = grid_diff_int90mean[:,:,hr_p] * CONUSmask
        grid_diff_areamean[:,:,hr_p]  = grid_diff_areamean[:,:,hr_p] * CONUSmask
        grid_diff_angmean[:,:,hr_p]   = grid_diff_angmean[:,:,hr_p] * CONUSmask
        grid_diff_count[:,:,hr_p]     = grid_diff_count[:,:,hr_p] * CONUSmask
        
        grid_mod_int10std[:,:,hr_p,0]   = grid_mod_int10std[:,:,hr_p,0] * CONUSmask
        grid_mod_int10std[:,:,hr_p,1]   = grid_mod_int10std[:,:,hr_p,1] * CONUSmask
        grid_mod_int50std[:,:,hr_p,0]   = grid_mod_int50std[:,:,hr_p,0] * CONUSmask
        grid_mod_int50std[:,:,hr_p,1]   = grid_mod_int50std[:,:,hr_p,1] * CONUSmask
        grid_mod_int90std[:,:,hr_p,0]   = grid_mod_int90std[:,:,hr_p,0] * CONUSmask
        grid_mod_int90std[:,:,hr_p,1]   = grid_mod_int90std[:,:,hr_p,1] * CONUSmask
        grid_obs_int10std[:,:,hr_p,0]   = grid_obs_int10std[:,:,hr_p,0] * CONUSmask
        grid_obs_int10std[:,:,hr_p,1]   = grid_obs_int10std[:,:,hr_p,1] * CONUSmask
        grid_obs_int50std[:,:,hr_p,0]   = grid_obs_int50std[:,:,hr_p,0] * CONUSmask
        grid_obs_int50std[:,:,hr_p,1]   = grid_obs_int50std[:,:,hr_p,1] * CONUSmask
        grid_obs_int90std[:,:,hr_p,0]   = grid_obs_int90std[:,:,hr_p,0] * CONUSmask
        grid_obs_int90std[:,:,hr_p,1]   = grid_obs_int90std[:,:,hr_p,1] * CONUSmask
        grid_mod_areastd[:,:,hr_p,0]    = grid_mod_areastd[:,:,hr_p,0] * CONUSmask
        grid_mod_areastd[:,:,hr_p,1]    = grid_mod_areastd[:,:,hr_p,1] * CONUSmask
        grid_obs_areastd[:,:,hr_p,0]    = grid_obs_areastd[:,:,hr_p,0]* CONUSmask
        grid_obs_areastd[:,:,hr_p,1]    = grid_obs_areastd[:,:,hr_p,1]* CONUSmask
        grid_mod_angstd[:,:,hr_p,0]     = grid_mod_angstd[:,:,hr_p,0] * CONUSmask
        grid_mod_angstd[:,:,hr_p,1]     = grid_mod_angstd[:,:,hr_p,1] * CONUSmask
        grid_obs_angstd[:,:,hr_p,0]     = grid_obs_angstd[:,:,hr_p,0] * CONUSmask
        grid_obs_angstd[:,:,hr_p,1]     = grid_obs_angstd[:,:,hr_p,1] * CONUSmask
        grid_diff_int10std[:,:,hr_p,0]  = grid_diff_int10std[:,:,hr_p,0] * CONUSmask
        grid_diff_int10std[:,:,hr_p,1]  = grid_diff_int10std[:,:,hr_p,1] * CONUSmask
        grid_diff_int50std[:,:,hr_p,0]  = grid_diff_int50std[:,:,hr_p,0] * CONUSmask
        grid_diff_int50std[:,:,hr_p,1]  = grid_diff_int50std[:,:,hr_p,1] * CONUSmask
        grid_diff_int90std[:,:,hr_p,0]  = grid_diff_int90std[:,:,hr_p,0] * CONUSmask
        grid_diff_int90std[:,:,hr_p,1]  = grid_diff_int90std[:,:,hr_p,1] * CONUSmask
        grid_diff_areastd[:,:,hr_p,0]   = grid_diff_areastd[:,:,hr_p,0] * CONUSmask
        grid_diff_areastd[:,:,hr_p,1]   = grid_diff_areastd[:,:,hr_p,1] * CONUSmask
        grid_diff_angstd[:,:,hr_p,0]    = grid_diff_angstd[:,:,hr_p,0] * CONUSmask
        grid_diff_angstd[:,:,hr_p,1]    = grid_diff_angstd[:,:,hr_p,1] * CONUSmask

elif subset_data == 'PAIR':

    ##Aggregate for paired objects
    grid_pair_ymean        = np.full([lat_nat.shape[0], lon_nat.shape[1], len(subset_hours)],np.nan)
    grid_pair_ystd         = np.full([lat_nat.shape[0], lon_nat.shape[1], len(subset_hours), 2],np.nan)
    grid_pair_xmean        = np.full([lat_nat.shape[0], lon_nat.shape[1], len(subset_hours)],np.nan)
    grid_pair_xstd         = np.full([lat_nat.shape[0], lon_nat.shape[1], len(subset_hours), 2],np.nan)
    grid_pair_int10mean    = np.full([lat_nat.shape[0], lon_nat.shape[1], len(subset_hours)],np.nan)
    grid_pair_int10mean_ns = np.full([lat_nat.shape[0], lon_nat.shape[1], len(subset_hours)],np.nan)
    grid_pair_int10std     = np.full([lat_nat.shape[0], lon_nat.shape[1], len(subset_hours), 2],np.nan)
    grid_pair_int50mean    = np.full([lat_nat.shape[0], lon_nat.shape[1], len(subset_hours)],np.nan)
    grid_pair_int50mean_ns = np.full([lat_nat.shape[0], lon_nat.shape[1], len(subset_hours)],np.nan)
    grid_pair_int50std     = np.full([lat_nat.shape[0], lon_nat.shape[1], len(subset_hours), 2],np.nan)
    grid_pair_int90mean    = np.full([lat_nat.shape[0], lon_nat.shape[1], len(subset_hours)],np.nan)
    grid_pair_int90mean_ns = np.full([lat_nat.shape[0], lon_nat.shape[1], len(subset_hours)],np.nan)
    grid_pair_int90std     = np.full([lat_nat.shape[0], lon_nat.shape[1], len(subset_hours), 2],np.nan)
    grid_pair_areamean     = np.full([lat_nat.shape[0], lon_nat.shape[1], len(subset_hours)],np.nan)
    grid_pair_areastd      = np.full([lat_nat.shape[0], lon_nat.shape[1], len(subset_hours), 2],np.nan)
    grid_pair_angmean      = np.full([lat_nat.shape[0], lon_nat.shape[1], len(subset_hours)],np.nan)
    grid_pair_angstd       = np.full([lat_nat.shape[0], lon_nat.shape[1], len(subset_hours), 2],np.nan)
    grid_pair_count        = np.full([lat_nat.shape[0], lon_nat.shape[1], len(subset_hours)],np.nan)
    grid_pair_magnitude    = [[[] for i in range(0,lat_nat.shape[1])] for j in range(0,lat_nat.shape[0])] 
    grid_pair_angle        = [[[] for i in range(0,lat_nat.shape[1])] for j in range(0,lat_nat.shape[0])] 
        
    for yloc in range(0,lat_nat.shape[0]):
        for xloc in range(0,lat_nat.shape[1]):
            for hr_p in range(0,len(subset_hours)): #For each hour increment to be considered   
                
                temp_data = []    
                #Check for paired objects within the proper time range
                if np.sum([len(t) for t in grid_pair[yloc][xloc]]) > 0:
                    element_count = 0
                    for t in grid_pair[yloc][xloc]:
                        if t[7+hour_index] in np.array(subset_hours[hr_p]): #Check for proper hour range
                            if element_count == 0:
                                temp_data = np.full([1, 9], np.nan)
    
                            #Extract ydiff,xdiff,intdiff_10,intdiff_50,intdiff_90,areadiff,angdiff,fhour,dhour
                            temp_data = np.vstack((temp_data,np.array([t[0],t[1],t[2],t[3],t[4],t[5],t[6],t[7],t[8]]))) 
                            element_count += 1
                
                #Retain statistically significant spatial biases
                if len(temp_data) > 0:    
                    #Retain only if statistically sigificant
                    if stats.ttest_1samp(temp_data[1:,0],0.0).pvalue < stat_tvalue or stats.ttest_1samp(temp_data[1:,1],0.0).pvalue < stat_tvalue or grid_res_nat == []:
                        grid_pair_ymean[yloc,xloc,hr_p]       = np.nanmedian(temp_data[:,0])
                        grid_pair_ystd[yloc,xloc,hr_p,0]      = np.nanpercentile(temp_data[:,0],100-pctile)   
                        grid_pair_ystd[yloc,xloc,hr_p,1]      = np.nanpercentile(temp_data[:,0],pctile)
                        grid_pair_xmean[yloc,xloc,hr_p]       = np.nanmedian(temp_data[:,1])
                        grid_pair_xstd[yloc,xloc,hr_p,0]      = np.nanpercentile(temp_data[:,1],100-pctile) 
                        grid_pair_xstd[yloc,xloc,hr_p,1]      = np.nanpercentile(temp_data[:,1],pctile)
                    grid_pair_int10mean_ns[yloc,xloc,hr_p]    = np.nanmedian(temp_data[:,2])
                    if stats.ttest_1samp(temp_data[1:,2],0.0).pvalue < stat_tvalue or grid_res_nat == []:
                        grid_pair_int10mean[yloc,xloc,hr_p]   = np.nanmedian(temp_data[:,2])
                        grid_pair_int10std[yloc,xloc,hr_p,0]  = np.nanpercentile(temp_data[:,2],100-pctile)
                        grid_pair_int10std[yloc,xloc,hr_p,1]  = np.nanpercentile(temp_data[:,2],pctile)
                    grid_pair_int50mean_ns[yloc,xloc,hr_p]    = np.nanmedian(temp_data[:,3])
                    if stats.ttest_1samp(temp_data[1:,3],0.0).pvalue < stat_tvalue or grid_res_nat == []:
                        grid_pair_int50mean[yloc,xloc,hr_p]   = np.nanmedian(temp_data[:,3])
                        grid_pair_int50std[yloc,xloc,hr_p,0]  = np.nanpercentile(temp_data[:,3],100-pctile)
                        grid_pair_int50std[yloc,xloc,hr_p,1]  = np.nanpercentile(temp_data[:,3],pctile)
                    grid_pair_int90mean_ns[yloc,xloc,hr_p]    = np.nanmedian(temp_data[:,4])
                    if stats.ttest_1samp(temp_data[1:,4],0.0).pvalue < stat_tvalue or grid_res_nat == []:
                        grid_pair_int90mean[yloc,xloc,hr_p]   = np.nanmedian(temp_data[:,4])
                        grid_pair_int90std[yloc,xloc,hr_p,0]  = np.nanpercentile(temp_data[:,4],100-pctile) 
                        grid_pair_int90std[yloc,xloc,hr_p,1]  = np.nanpercentile(temp_data[:,4],pctile)
                    if stats.ttest_1samp(temp_data[1:,5],0.0).pvalue < stat_tvalue or grid_res_nat == []:
                        grid_pair_areamean[yloc,xloc,hr_p]    = np.nanmedian(temp_data[:,5])
                        grid_pair_areastd[yloc,xloc,hr_p,0]   = np.nanpercentile(temp_data[:,5],100-pctile) 
                        grid_pair_areastd[yloc,xloc,hr_p,1]   = np.nanpercentile(temp_data[:,5],pctile)
                    if stats.ttest_1samp(temp_data[1:,6],0.0).pvalue < stat_tvalue or grid_res_nat == []:
                        grid_pair_angmean[yloc,xloc,hr_p]     = np.nanmedian(temp_data[:,6])
                        grid_pair_angstd[yloc,xloc,hr_p,0]    = np.nanpercentile(temp_data[:,6],100-pctile)           
                        grid_pair_angstd[yloc,xloc,hr_p,1]    = np.nanpercentile(temp_data[:,6],pctile)
                    grid_pair_count[yloc,xloc,hr_p]           = np.sum(np.isnan(temp_data[:,1])==0)
                    
                #Calculate individual angle/magnitude values to create rose plots
                if grid_res_nat == [] and len(temp_data) > 0:
                    grid_pair_magnitude[yloc][xloc] = np.append(grid_pair_magnitude[yloc][xloc],np.sqrt(temp_data[:,0]**2 + temp_data[:,1]**2))
                    for pt in range(0,len(temp_data[:,0])):
                        temp_deg = (math.atan2(temp_data[pt,1],temp_data[pt,0])/math.pi*180)+180
                        grid_pair_angle[yloc][xloc] = np.append(grid_pair_angle[yloc][xloc],temp_deg)
                        print(grid_pair_angle[yloc][xloc]) 

    #Apply CONUS mask
    for hr_p in range(0,grid_pair_int90mean.shape[2]):
        grid_pair_ymean[:,:,hr_p]         = grid_pair_ymean[:,:,hr_p] * CONUSmask
        grid_pair_ystd[:,:,hr_p,0]        = grid_pair_ystd[:,:,hr_p,0] * CONUSmask
        grid_pair_ystd[:,:,hr_p,1]        = grid_pair_ystd[:,:,hr_p,1] * CONUSmask
        grid_pair_xmean[:,:,hr_p]         = grid_pair_xmean[:,:,hr_p] * CONUSmask
        grid_pair_xstd[:,:,hr_p,0]        = grid_pair_xstd[:,:,hr_p,0] * CONUSmask
        grid_pair_xstd[:,:,hr_p,1]        = grid_pair_xstd[:,:,hr_p,1] * CONUSmask
        grid_pair_int10mean[:,:,hr_p]     = grid_pair_int10mean[:,:,hr_p] * CONUSmask
        grid_pair_int10mean_ns[:,:,hr_p]  = grid_pair_int10mean_ns[:,:,hr_p] * CONUSmask
        grid_pair_int10std[:,:,hr_p,0]    = grid_pair_int10std[:,:,hr_p,0] * CONUSmask
        grid_pair_int10std[:,:,hr_p,1]    = grid_pair_int10std[:,:,hr_p,1] * CONUSmask
        grid_pair_int50mean[:,:,hr_p]     = grid_pair_int50mean[:,:,hr_p] * CONUSmask
        grid_pair_int50mean_ns[:,:,hr_p]  = grid_pair_int50mean_ns[:,:,hr_p] * CONUSmask
        grid_pair_int50std[:,:,hr_p,0]    = grid_pair_int50std[:,:,hr_p,0] * CONUSmask
        grid_pair_int50std[:,:,hr_p,1]    = grid_pair_int50std[:,:,hr_p,1] * CONUSmask
        grid_pair_int90mean[:,:,hr_p]     = grid_pair_int90mean[:,:,hr_p] * CONUSmask
        grid_pair_int90mean_ns[:,:,hr_p]  = grid_pair_int90mean_ns[:,:,hr_p] * CONUSmask
        grid_pair_int90std[:,:,hr_p,0]    = grid_pair_int90std[:,:,hr_p,0] * CONUSmask
        grid_pair_int90std[:,:,hr_p,1]    = grid_pair_int90std[:,:,hr_p,1] * CONUSmask
        grid_pair_areamean[:,:,hr_p]      = grid_pair_areamean[:,:,hr_p] * CONUSmask
        grid_pair_areastd[:,:,hr_p,0]     = grid_pair_areastd[:,:,hr_p,0] * CONUSmask
        grid_pair_areastd[:,:,hr_p,1]     = grid_pair_areastd[:,:,hr_p,1] * CONUSmask
        grid_pair_angmean[:,:,hr_p]       = grid_pair_angmean[:,:,hr_p] * CONUSmask
        grid_pair_angstd[:,:,hr_p,0]      = grid_pair_angstd[:,:,hr_p,0] * CONUSmask
        grid_pair_angstd[:,:,hr_p,1]      = grid_pair_angstd[:,:,hr_p,1] * CONUSmask
        grid_pair_count[:,:,hr_p]         = grid_pair_count[:,:,hr_p] * CONUSmask
    
elif subset_data == 'PAIRinit':
    
    ##Aggregate for paired dissipation objects
    grid_init_ymean        = np.full([lat_nat.shape[0], lon_nat.shape[1], len(subset_hours)],np.nan)
    grid_init_ystd         = np.full([lat_nat.shape[0], lon_nat.shape[1], len(subset_hours), 2],np.nan)
    grid_init_xmean        = np.full([lat_nat.shape[0], lon_nat.shape[1], len(subset_hours)],np.nan)
    grid_init_xstd         = np.full([lat_nat.shape[0], lon_nat.shape[1], len(subset_hours), 2],np.nan)
    grid_init_int10mean    = np.full([lat_nat.shape[0], lon_nat.shape[1], len(subset_hours)],np.nan)
    grid_init_int10mean_ns = np.full([lat_nat.shape[0], lon_nat.shape[1], len(subset_hours)],np.nan)
    grid_init_int10std     = np.full([lat_nat.shape[0], lon_nat.shape[1], len(subset_hours), 2],np.nan)
    grid_init_int50mean    = np.full([lat_nat.shape[0], lon_nat.shape[1], len(subset_hours)],np.nan)
    grid_init_int50mean_ns = np.full([lat_nat.shape[0], lon_nat.shape[1], len(subset_hours)],np.nan)
    grid_init_int50std     = np.full([lat_nat.shape[0], lon_nat.shape[1], len(subset_hours), 2],np.nan)
    grid_init_int90mean    = np.full([lat_nat.shape[0], lon_nat.shape[1], len(subset_hours)],np.nan)
    grid_init_int90mean_ns = np.full([lat_nat.shape[0], lon_nat.shape[1], len(subset_hours)],np.nan)
    grid_init_int90std     = np.full([lat_nat.shape[0], lon_nat.shape[1], len(subset_hours), 2],np.nan)
    grid_init_areamean     = np.full([lat_nat.shape[0], lon_nat.shape[1], len(subset_hours)],np.nan)
    grid_init_areastd      = np.full([lat_nat.shape[0], lon_nat.shape[1], len(subset_hours), 2],np.nan)
    grid_init_angmean      = np.full([lat_nat.shape[0], lon_nat.shape[1], len(subset_hours)],np.nan)
    grid_init_angstd       = np.full([lat_nat.shape[0], lon_nat.shape[1], len(subset_hours), 2],np.nan)
    grid_init_timemean     = np.full([lat_nat.shape[0], lon_nat.shape[1], len(subset_hours)],np.nan)
    grid_init_timestd      = np.full([lat_nat.shape[0], lon_nat.shape[1], len(subset_hours), 2],np.nan)
    grid_init_count        = np.full([lat_nat.shape[0], lon_nat.shape[1], len(subset_hours)],np.nan)
    grid_init_magnitude    = [[[] for i in range(0,lat_nat.shape[1])] for j in range(0,lat_nat.shape[0])] 
    grid_init_angle        = [[[] for i in range(0,lat_nat.shape[1])] for j in range(0,lat_nat.shape[0])] 
    
    for yloc in range(0,lat_nat.shape[0]):
        for xloc in range(0,lat_nat.shape[1]):
            for hr_p in range(0,len(subset_hours)): #For each hour increment to be considered 
                
                temp_data = []    
                #Check for paired objects within the proper time range
                if np.sum([len(t) for t in grid_init[yloc][xloc]]) > 0:
                    element_count = 0
                    for t in grid_init[yloc][xloc]:
                        if t[8+hour_index] in np.array(subset_hours[hr_p]): #Check for proper hour range
                            if element_count == 0:
                                temp_data = np.full([1, 10], np.nan)
    
                            #Extract [ydiff,xdiff,intdiff_10,intdiff_50,intdiff_90,areadiff,angdiff,timediff,fhour_first_obs,dhour_first_obs]
                            temp_data = np.vstack((temp_data,np.array([t[0],t[1],t[2],t[3],t[4],t[5],t[6],t[7],t[8],t[9]]))) 
                            element_count += 1                                                                                                   
                                                                                                       
                #Retain statistically significant spatial biases
                if len(temp_data) > 0:

                    if stats.ttest_1samp(temp_data[1:,0],0.0).pvalue < stat_tvalue or stats.ttest_1samp(temp_data[1:,1],0.0).pvalue < stat_tvalue or grid_res_nat == []:            
                        grid_init_ymean[yloc,xloc,hr_p]      = np.nanmedian(temp_data[:,0])
                        grid_init_ystd[yloc,xloc,hr_p,0]     = np.nanpercentile(temp_data[:,0],100-pctile) 
                        grid_init_ystd[yloc,xloc,hr_p,1]     = np.nanpercentile(temp_data[:,0],pctile)
                        grid_init_xmean[yloc,xloc,hr_p]      = np.nanmedian(temp_data[:,1])
                        grid_init_xstd[yloc,xloc,hr_p,0]     = np.nanpercentile(temp_data[:,1],100-pctile) 
                        grid_init_xstd[yloc,xloc,hr_p,1]     = np.nanpercentile(temp_data[:,1],pctile)
                    grid_init_int10mean_ns[yloc,xloc,hr_p]   = np.nanmedian(temp_data[:,2])
                    if stats.ttest_1samp(temp_data[1:,2],0.0).pvalue < stat_tvalue or grid_res_nat == []:
                        grid_init_int10mean[yloc,xloc,hr_p]  = np.nanmedian(temp_data[:,2])
                        grid_init_int10std[yloc,xloc,hr_p,0] = np.nanpercentile(temp_data[:,2],100-pctile) 
                        grid_init_int10std[yloc,xloc,hr_p,1] = np.nanpercentile(temp_data[:,2],pctile)
                    grid_init_int50mean_ns[yloc,xloc,hr_p]   = np.nanmedian(temp_data[:,3])
                    if stats.ttest_1samp(temp_data[1:,3],0.0).pvalue < stat_tvalue or grid_res_nat == []:
                        grid_init_int50mean[yloc,xloc,hr_p]  = np.nanmedian(temp_data[:,3])
                        grid_init_int50std[yloc,xloc,hr_p,0] = np.nanpercentile(temp_data[:,3],100-pctile) 
                        grid_init_int50std[yloc,xloc,hr_p,1] = np.nanpercentile(temp_data[:,3],pctile)
                    grid_init_int90mean_ns[yloc,xloc,hr_p]   = np.nanmedian(temp_data[:,4])
                    if stats.ttest_1samp(temp_data[1:,4],0.0).pvalue < stat_tvalue or grid_res_nat == []:
                        grid_init_int90mean[yloc,xloc,hr_p]  = np.nanmedian(temp_data[:,4])
                        grid_init_int90std[yloc,xloc,hr_p,0] = np.nanpercentile(temp_data[:,4],100-pctile) 
                        grid_init_int90std[yloc,xloc,hr_p,1] = np.nanpercentile(temp_data[:,4],pctile)
                    if stats.ttest_1samp(temp_data[1:,5],0.0).pvalue < stat_tvalue or grid_res_nat == []:
                        grid_init_areamean[yloc,xloc,hr_p]   = np.nanmedian(temp_data[:,5])
                        grid_init_areastd[yloc,xloc,hr_p,0]  = np.nanpercentile(temp_data[:,5],100-pctile) 
                        grid_init_areastd[yloc,xloc,hr_p,1]  = np.nanpercentile(temp_data[:,5],pctile)
                    if stats.ttest_1samp(temp_data[1:,6],0.0).pvalue < stat_tvalue or grid_res_nat == []:
                        grid_init_angmean[yloc,xloc,hr_p]    = np.nanmedian(temp_data[:,6])
                        grid_init_angstd[yloc,xloc,hr_p,0]   = np.nanpercentile(temp_data[:,6],100-pctile) 
                        grid_init_angstd[yloc,xloc,hr_p,1]   = np.nanpercentile(temp_data[:,6],pctile)
                    if stats.ttest_1samp(temp_data[1:,7],0.0).pvalue < stat_tvalue or grid_res_nat == []:
                        grid_init_timemean[yloc,xloc,hr_p]   = np.nanmedian(temp_data[:,7])
                        grid_init_timestd[yloc,xloc,hr_p,0]  = np.nanpercentile(temp_data[:,7],100-pctile)     
                        grid_init_timestd[yloc,xloc,hr_p,1]  = np.nanpercentile(temp_data[:,7],pctile)
                    grid_init_count[yloc,xloc,hr_p]          = np.sum(np.isnan(temp_data[:,1])==0)

                #Calculate individual angle/magnitude values to create rose plots
                if grid_res_nat == [] and len(temp_data) > 0:
                    grid_init_magnitude[yloc][xloc] = np.append(grid_init_magnitude[yloc][xloc],np.sqrt(temp_data[:,0]**2 + temp_data[:,1]**2))
                    for pt in range(0,len(temp_data[:,0])):
                        temp_deg = (math.atan2(temp_data[pt,1],temp_data[pt,0])/math.pi*180)+180
                        grid_init_angle[yloc][xloc] = np.append(grid_init_angle[yloc][xloc],temp_deg)   

    #Apply CONUS mask
    for hr_p in range(0,grid_init_int90mean.shape[2]):
        grid_init_ymean[:,:,hr_p]        = grid_init_ymean[:,:,hr_p] * CONUSmask
        grid_init_ystd[:,:,hr_p,0]       = grid_init_ystd[:,:,hr_p,0] * CONUSmask
        grid_init_ystd[:,:,hr_p,1]       = grid_init_ystd[:,:,hr_p,1] * CONUSmask
        grid_init_xmean[:,:,hr_p]        = grid_init_xmean[:,:,hr_p] * CONUSmask
        grid_init_xstd[:,:,hr_p,0]       = grid_init_xstd[:,:,hr_p,0] * CONUSmask
        grid_init_xstd[:,:,hr_p,1]       = grid_init_xstd[:,:,hr_p,1] * CONUSmask
        grid_init_int10mean[:,:,hr_p]    = grid_init_int10mean[:,:,hr_p] * CONUSmask
        grid_init_int10mean_ns[:,:,hr_p] = grid_init_int10mean_ns[:,:,hr_p] * CONUSmask
        grid_init_int10std[:,:,hr_p,0]   = grid_init_int10std[:,:,hr_p,0] * CONUSmask
        grid_init_int10std[:,:,hr_p,1]   = grid_init_int10std[:,:,hr_p,1] * CONUSmask
        grid_init_int50mean[:,:,hr_p]    = grid_init_int50mean[:,:,hr_p] * CONUSmask
        grid_init_int50mean_ns[:,:,hr_p] = grid_init_int50mean_ns[:,:,hr_p] * CONUSmask
        grid_init_int50std[:,:,hr_p,0]   = grid_init_int50std[:,:,hr_p,0] * CONUSmask
        grid_init_int50std[:,:,hr_p,1]   = grid_init_int50std[:,:,hr_p,1] * CONUSmask
        grid_init_int90mean[:,:,hr_p]    = grid_init_int90mean[:,:,hr_p] * CONUSmask
        grid_init_int90mean_ns[:,:,hr_p] = grid_init_int90mean_ns[:,:,hr_p] * CONUSmask
        grid_init_int90std[:,:,hr_p,0]   = grid_init_int90std[:,:,hr_p,0] * CONUSmask
        grid_init_int90std[:,:,hr_p,1]   = grid_init_int90std[:,:,hr_p,1] * CONUSmask
        grid_init_areamean[:,:,hr_p]     = grid_init_areamean[:,:,hr_p] * CONUSmask
        grid_init_areastd[:,:,hr_p,0]    = grid_init_areastd[:,:,hr_p,0] * CONUSmask
        grid_init_areastd[:,:,hr_p,1]    = grid_init_areastd[:,:,hr_p,1] * CONUSmask
        grid_init_angmean[:,:,hr_p]      = grid_init_angmean[:,:,hr_p] * CONUSmask
        grid_init_angstd[:,:,hr_p,0]     = grid_init_angstd[:,:,hr_p,0] * CONUSmask
        grid_init_angstd[:,:,hr_p,1]     = grid_init_angstd[:,:,hr_p,1] * CONUSmask
        grid_init_timemean[:,:,hr_p]     = grid_init_timemean[:,:,hr_p] * CONUSmask
        grid_init_timestd[:,:,hr_p,0]    = grid_init_timestd[:,:,hr_p,0] * CONUSmask
        grid_init_timestd[:,:,hr_p,1]    = grid_init_timestd[:,:,hr_p,1] * CONUSmask
        grid_init_count[:,:,hr_p]        = grid_init_count[:,:,hr_p] * CONUSmask

elif subset_data == 'PAIRdisp':
    
    ##Aggregate for paired dissipation objects
    grid_disp_ymean        = np.full([lat_nat.shape[0], lon_nat.shape[1], len(subset_hours)],np.nan)
    grid_disp_ystd         = np.full([lat_nat.shape[0], lon_nat.shape[1], len(subset_hours), 2],np.nan)
    grid_disp_xmean        = np.full([lat_nat.shape[0], lon_nat.shape[1], len(subset_hours)],np.nan)
    grid_disp_xstd         = np.full([lat_nat.shape[0], lon_nat.shape[1], len(subset_hours), 2],np.nan)
    grid_disp_int10mean    = np.full([lat_nat.shape[0], lon_nat.shape[1], len(subset_hours)],np.nan)
    grid_disp_int10mean_ns = np.full([lat_nat.shape[0], lon_nat.shape[1], len(subset_hours)],np.nan)
    grid_disp_int10std     = np.full([lat_nat.shape[0], lon_nat.shape[1], len(subset_hours), 2],np.nan)
    grid_disp_int50mean    = np.full([lat_nat.shape[0], lon_nat.shape[1], len(subset_hours)],np.nan)
    grid_disp_int50mean_ns = np.full([lat_nat.shape[0], lon_nat.shape[1], len(subset_hours)],np.nan)
    grid_disp_int50std     = np.full([lat_nat.shape[0], lon_nat.shape[1], len(subset_hours), 2],np.nan)
    grid_disp_int90mean    = np.full([lat_nat.shape[0], lon_nat.shape[1], len(subset_hours)],np.nan)
    grid_disp_int90mean_ns = np.full([lat_nat.shape[0], lon_nat.shape[1], len(subset_hours)],np.nan)
    grid_disp_int90std     = np.full([lat_nat.shape[0], lon_nat.shape[1], len(subset_hours), 2],np.nan)
    grid_disp_areamean     = np.full([lat_nat.shape[0], lon_nat.shape[1], len(subset_hours)],np.nan)
    grid_disp_areastd      = np.full([lat_nat.shape[0], lon_nat.shape[1], len(subset_hours), 2],np.nan)
    grid_disp_angmean      = np.full([lat_nat.shape[0], lon_nat.shape[1], len(subset_hours)],np.nan)
    grid_disp_angstd       = np.full([lat_nat.shape[0], lon_nat.shape[1], len(subset_hours), 2],np.nan)
    grid_disp_timemean     = np.full([lat_nat.shape[0], lon_nat.shape[1], len(subset_hours)],np.nan)
    grid_disp_timestd      = np.full([lat_nat.shape[0], lon_nat.shape[1], len(subset_hours), 2],np.nan)
    grid_disp_count        = np.full([lat_nat.shape[0], lon_nat.shape[1], len(subset_hours)],np.nan)
    grid_disp_magnitude    = [[[] for i in range(0,lat_nat.shape[1])] for j in range(0,lat_nat.shape[0])] 
    grid_disp_angle        = [[[] for i in range(0,lat_nat.shape[1])] for j in range(0,lat_nat.shape[0])] 
    
    for yloc in range(0,lat_nat.shape[0]):
        for xloc in range(0,lat_nat.shape[1]):
            for hr_p in range(0,len(subset_hours)): #For each hour increment to be considered 
                
                temp_data = []    
                #Check for paired objects within the proper time range
                if np.sum([len(t) for t in grid_disp[yloc][xloc]]) > 0:
                    element_count = 0
                    for t in grid_disp[yloc][xloc]:
                        if t[8+hour_index] in np.array(subset_hours[hr_p]): #Check for proper hour range
                            if element_count == 0:
                                temp_data = np.full([1, 10], np.nan)
    
                            #Extract [ydiff,xdiff,intdiff_10,intdiff_50,intdiff_90,areadiff,angdiff,timediff,fhour_first_obs,dhour_first_obs]
                            temp_data = np.vstack((temp_data,np.array([t[0],t[1],t[2],t[3],t[4],t[5],t[6],t[7],t[8],t[9]]))) 
                            element_count += 1                                                                                                   
                                                                                                                   
                #Retain statistically significant spatial biases
                if len(temp_data) > 0:      

                    if stats.ttest_1samp(temp_data[1:,0],0.0).pvalue < stat_tvalue or stats.ttest_1samp(temp_data[1:,1],0.0).pvalue < stat_tvalue or grid_res_nat == []:            
                        grid_disp_ymean[yloc,xloc,hr_p]       = np.nanmedian(temp_data[:,0])
                        grid_disp_ystd[yloc,xloc,hr_p,0]      = np.nanpercentile(temp_data[:,0],100-pctile) 
                        grid_disp_ystd[yloc,xloc,hr_p,1]      = np.nanpercentile(temp_data[:,0],pctile)
                        grid_disp_xmean[yloc,xloc,hr_p]       = np.nanmedian(temp_data[:,1])
                        grid_disp_xstd[yloc,xloc,hr_p,0]      = np.nanpercentile(temp_data[:,1],100-pctile) 
                        grid_disp_xstd[yloc,xloc,hr_p,1]      = np.nanpercentile(temp_data[:,1],pctile)
                    grid_disp_int10mean_ns[yloc,xloc,hr_p]    = np.nanmedian(temp_data[:,2])
                    if stats.ttest_1samp(temp_data[1:,2],0.0).pvalue < stat_tvalue or grid_res_nat == []:
                        grid_disp_int10mean[yloc,xloc,hr_p]   = np.nanmedian(temp_data[:,2])
                        grid_disp_int10std[yloc,xloc,hr_p,0]  = np.nanpercentile(temp_data[:,2],100-pctile) 
                        grid_disp_int10std[yloc,xloc,hr_p,1]  = np.nanpercentile(temp_data[:,2],pctile)
                    grid_disp_int50mean_ns[yloc,xloc,hr_p]    = np.nanmedian(temp_data[:,3])
                    if stats.ttest_1samp(temp_data[1:,3],0.0).pvalue < stat_tvalue or grid_res_nat == []:
                        grid_disp_int50mean[yloc,xloc,hr_p]   = np.nanmedian(temp_data[:,3])
                        grid_disp_int50std[yloc,xloc,hr_p,0]  = np.nanpercentile(temp_data[:,3],100-pctile) 
                        grid_disp_int50std[yloc,xloc,hr_p,1]  = np.nanpercentile(temp_data[:,3],pctile)
                    grid_disp_int90mean_ns[yloc,xloc,hr_p]    = np.nanmedian(temp_data[:,4])
                    if stats.ttest_1samp(temp_data[1:,4],0.0).pvalue < stat_tvalue or grid_res_nat == []:
                        grid_disp_int90mean[yloc,xloc,hr_p]   = np.nanmedian(temp_data[:,4])
                        grid_disp_int90std[yloc,xloc,hr_p,0]  = np.nanpercentile(temp_data[:,4],100-pctile) 
                        grid_disp_int90std[yloc,xloc,hr_p,1]  = np.nanpercentile(temp_data[:,4],pctile)
                    if stats.ttest_1samp(temp_data[1:,5],0.0).pvalue < stat_tvalue or grid_res_nat == []:
                        grid_disp_areamean[yloc,xloc,hr_p]    = np.nanmedian(temp_data[:,5])
                        grid_disp_areastd[yloc,xloc,hr_p,0]   = np.nanpercentile(temp_data[:,5],100-pctile) 
                        grid_disp_areastd[yloc,xloc,hr_p,1]   = np.nanpercentile(temp_data[:,5],pctile)
                    if stats.ttest_1samp(temp_data[1:,6],0.0).pvalue < stat_tvalue or grid_res_nat == []:
                        grid_disp_angmean[yloc,xloc,hr_p]     = np.nanmedian(temp_data[:,6])
                        grid_disp_angstd[yloc,xloc,hr_p,0]    = np.nanpercentile(temp_data[:,6],100-pctile) 
                        grid_disp_angstd[yloc,xloc,hr_p,1]    = np.nanpercentile(temp_data[:,6],pctile)
                    if stats.ttest_1samp(temp_data[1:,7],0.0).pvalue < stat_tvalue or grid_res_nat == []:
                        grid_disp_timemean[yloc,xloc,hr_p]    = np.nanmedian(temp_data[:,7])
                        grid_disp_timestd[yloc,xloc,hr_p,0]   = np.nanpercentile(temp_data[:,7],100-pctile)     
                        grid_disp_timestd[yloc,xloc,hr_p,1]   = np.nanpercentile(temp_data[:,7],pctile)
                    grid_disp_count[yloc,xloc,hr_p]           = np.sum(np.isnan(temp_data[:,1])==0)

                #Calculate individual angle/magnitude values to create rose plots
                if grid_res_nat == [] and len(temp_data) > 0:
                    grid_disp_magnitude[yloc][xloc] = np.append(grid_disp_magnitude[yloc][xloc],np.sqrt(temp_data[:,0]**2 + temp_data[:,1]**2))
                    for pt in range(0,len(temp_data[:,0])):
                        temp_deg = (math.atan2(temp_data[pt,1],temp_data[pt,0])/math.pi*180)+180
                        grid_disp_angle[yloc][xloc] = np.append(grid_disp_angle[yloc][xloc],temp_deg)   
                        
    #Apply CONUS mask
    for hr_p in range(0,grid_disp_int90mean.shape[2]):
        grid_disp_ymean[:,:,hr_p]        = grid_disp_ymean[:,:,hr_p] * CONUSmask
        grid_disp_ystd[:,:,hr_p,0]       = grid_disp_ystd[:,:,hr_p,0] * CONUSmask
        grid_disp_ystd[:,:,hr_p,1]       = grid_disp_ystd[:,:,hr_p,1] * CONUSmask
        grid_disp_xmean[:,:,hr_p]        = grid_disp_xmean[:,:,hr_p] * CONUSmask
        grid_disp_xstd[:,:,hr_p,0]       = grid_disp_xstd[:,:,hr_p,0] * CONUSmask
        grid_disp_xstd[:,:,hr_p,1]       = grid_disp_xstd[:,:,hr_p,1] * CONUSmask
        grid_disp_int10mean[:,:,hr_p]    = grid_disp_int10mean[:,:,hr_p] * CONUSmask
        grid_disp_int10mean_ns[:,:,hr_p] = grid_disp_int10mean_ns[:,:,hr_p] * CONUSmask
        grid_disp_int10std[:,:,hr_p,0]   = grid_disp_int10std[:,:,hr_p,0] * CONUSmask
        grid_disp_int10std[:,:,hr_p,1]   = grid_disp_int10std[:,:,hr_p,1] * CONUSmask
        grid_disp_int50mean[:,:,hr_p]    = grid_disp_int50mean[:,:,hr_p] * CONUSmask
        grid_disp_int50mean_ns[:,:,hr_p] = grid_disp_int50mean_ns[:,:,hr_p] * CONUSmask
        grid_disp_int50std[:,:,hr_p,0]   = grid_disp_int50std[:,:,hr_p,0] * CONUSmask
        grid_disp_int50std[:,:,hr_p,1]   = grid_disp_int50std[:,:,hr_p,1] * CONUSmask
        grid_disp_int90mean[:,:,hr_p]    = grid_disp_int90mean[:,:,hr_p] * CONUSmask
        grid_disp_int90mean_ns[:,:,hr_p] = grid_disp_int90mean_ns[:,:,hr_p] * CONUSmask
        grid_disp_int90std[:,:,hr_p,0]   = grid_disp_int90std[:,:,hr_p,0] * CONUSmask
        grid_disp_int90std[:,:,hr_p,1]   = grid_disp_int90std[:,:,hr_p,1] * CONUSmask
        grid_disp_areamean[:,:,hr_p]     = grid_disp_areamean[:,:,hr_p] * CONUSmask
        grid_disp_areastd[:,:,hr_p,0]    = grid_disp_areastd[:,:,hr_p,0] * CONUSmask
        grid_disp_areastd[:,:,hr_p,1]    = grid_disp_areastd[:,:,hr_p,1] * CONUSmask
        grid_disp_angmean[:,:,hr_p]      = grid_disp_angmean[:,:,hr_p] * CONUSmask
        grid_disp_angstd[:,:,hr_p,0]     = grid_disp_angstd[:,:,hr_p,0] * CONUSmask
        grid_disp_angstd[:,:,hr_p,1]     = grid_disp_angstd[:,:,hr_p,1] * CONUSmask
        grid_disp_timemean[:,:,hr_p]     = grid_disp_timemean[:,:,hr_p] * CONUSmask
        grid_disp_timestd[:,:,hr_p,0]    = grid_disp_timestd[:,:,hr_p,0] * CONUSmask
        grid_disp_timestd[:,:,hr_p,1]    = grid_disp_timestd[:,:,hr_p,1] * CONUSmask
        grid_disp_count[:,:,hr_p]        = grid_disp_count[:,:,hr_p] * CONUSmask

elif subset_data == 'POYgPMY':

    CONUSmask2 = CONUSmask * 1.0
    CONUSmask2[CONUSmask2==0]  = np.NaN
    grid_POYgPMY = grid_POYgPMY * CONUSmask2

########################################################                                                                
##############PLOT THE DATA SPATIALLY###################  

#Plot the paired statistics   
if subset_data == 'PAIR':
    
    if grid_res_nat == []: #If everything is aggregated along the time dimension only
        
        #Subset magnitude/angle differences and then create wind rose plot
        angle_temp = grid_pair_angle[1][1]
        mag_temp   = grid_pair_magnitude[1][1]
        angle_temp = angle_temp[~np.isnan(angle_temp)]
        mag_temp   = mag_temp[~np.isnan(mag_temp)]
        
        ax = WindroseAxes.from_ax()
        ax.bar(angle_temp, mag_temp, bins=[0,10,20,50,75,100,125,150,200,400,500],blowto=True)
        ax.set_legend()
        plt.title('Paired Model Displacement (km) - Area Precip. >= '+str(thres)+'" Per '+'{0:.2f}'.format(pre_acc)+' Hour\n '+ \
            'From '+beg_date_str_lo+' to '+end_date_str_lo,fontsize=14) 
        plt.savefig(FIG_PATH+'/'+GRIB_PATH_DES+'_pair_prop_rose_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[0]+ \
            '_t'+str(thres)+'_r'+grid_res_agg_str+'_d'+'_'.join([str(i) for i in latlon_dims])+'.png', bbox_inches='tight',dpi=200)
        plt.close()
        os.system('scp '+FIG_PATH+'/'+GRIB_PATH_DES+'_pair_prop_rose_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[0]+ \
            '_t'+str(thres)+'_r'+grid_res_agg_str+'_d'+'_'.join([str(i) for i in latlon_dims])+'.png hpc@vm-lnx-rzdm06:/home/people/hpc/ftp/erickson/test2')
        
        #Plot showing the x displacement/std and y displacement/std
        fig = plt.figure(figsize=(8,8))
        ax1 = fig.add_axes([0.1,0.1,0.8,0.8])
        ax1.errorbar(subset_hours-0.1,grid_pair_xmean[1,1],yerr=[grid_pair_xmean[1,1]-grid_pair_xstd[1,1,:,0],grid_pair_xstd[1,1,:,1]-grid_pair_xmean[1,1]],color='b',fmt='-x',capthick=2)
        ax1.plot(subset_hours, np.zeros(len(subset_hours)),linewidth=3,color='black')
        ax1.set_xlabel(lab_str[0],fontsize=14)
        ax1.set_ylabel('East-West Average Displacement (km)', color='b',fontsize=14)
        ax1.set_ylim(-thres*3000,thres*3000)
        #Second part of plotyy
        ax2 = ax1.twinx()
        ax2.errorbar(subset_hours+0.1,grid_pair_ymean[1,1],yerr=[grid_pair_ymean[1,1]-grid_pair_ystd[1,1,:,0],grid_pair_ystd[1,1,:,1]-grid_pair_ymean[1,1]],color='r',fmt='-x',capthick=2)
        ax2.set_ylabel('North-South Average Displacement (km)', color='r',fontsize=14)
        ax2.set_ylim(-thres*3000,thres*3000)
        plt.title('Average Displacement - Area Precip. >= '+str(thres)+'" Per '+'{0:.2f}'.format(pre_acc)+' Hour\n '+ \
            'From '+beg_date_str_lo+' to '+end_date_str_lo,fontsize=14) 
        #Set up the legend
        line_label=[]
        line_str=[]
        leg_nam = ['East-West Displacement','North-South Displacement']
        colorlist = ['blue','red']
        markerlist = ['x','x']   
        linelist = ['-','-']
        for x in range(0,len(leg_nam)):
            line_label = np.hstack((line_label, mpl.lines.Line2D(range(1), range(1), color=colorlist[x], linestyle=linelist[x], marker=markerlist[x], markersize=7)))
            line_str   = np.hstack((line_str, leg_nam[x]))
        first_legend=plt.legend(line_label, line_str, fontsize=12, numpoints=1, loc=0, framealpha=1)
        ax2 = plt.gca().add_artist(first_legend)
        plt.savefig(FIG_PATH+'/'+GRIB_PATH_DES+'_pair_prop_xydisp_byhour_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[0]+ \
            '_t'+str(thres)+'_r'+grid_res_agg_str+'_d'+'_'.join([str(i) for i in latlon_dims])+'.png', bbox_inches='tight',dpi=200)
        plt.close()
        os.system('scp '+FIG_PATH+'/'+GRIB_PATH_DES+'_pair_prop_xydisp_byhour_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[0]+ \
            '_t'+str(thres)+'_r'+grid_res_agg_str+'_d'+'_'.join([str(i) for i in latlon_dims])+'.png hpc@vm-lnx-rzdm06:/home/people/hpc/ftp/erickson/test2')
        
        #Plot showing the 10/50/90th percentile of intensity/std and 
        fig = plt.figure(figsize=(8,8))
        ax = fig.add_axes([0.1,0.1,0.8,0.8])
        plt.errorbar(subset_hours-0.15,grid_pair_int10mean[1,1],yerr=[grid_pair_int10mean[1,1]-grid_pair_int10std[1,1,:,0],grid_pair_int10std[1,1,:,1]-grid_pair_int10mean[1,1]],color='b',fmt='-x',capthick=2)
        plt.errorbar(subset_hours-0.00,grid_pair_int50mean[1,1],yerr=[grid_pair_int50mean[1,1]-grid_pair_int50std[1,1,:,0],grid_pair_int50std[1,1,:,1]-grid_pair_int50mean[1,1]],color='g',fmt='-x',capthick=2)
        plt.errorbar(subset_hours+0.15,grid_pair_int90mean[1,1],yerr=[grid_pair_int90mean[1,1]-grid_pair_int90std[1,1,:,0],grid_pair_int90std[1,1,:,1]-grid_pair_int90mean[1,1]],color='r',fmt='-x',capthick=2)
        plt.plot(subset_hours, np.zeros(len(subset_hours)),linewidth=3,color='black')
        plt.xlabel(lab_str[0],fontsize=14)
        plt.ylabel('Mean Object Intensity Difference (Inches)',fontsize=14)
        plt.ylim((-thres*2,thres*2.5))
        plt.title('Paired Intensity Difference - Area Precip. >= '+str(thres)+'" Per '+'{0:.2f}'.format(pre_acc)+' Hour\n '+ \
            'From '+beg_date_str_lo+' to '+end_date_str_lo,fontsize=14) 
        #Set up the legend
        line_label=[]
        line_str=[];
        leg_nam = ['10th Object Intensity Difference','50th Object Intensity Difference','90th Object Intensity Difference']
        colorlist  = ['blue','green','red',]
        markerlist = ['x','x','x']
        linelist   = ['-','-','-']
        for x in range(0,len(leg_nam)):
            line_label = np.hstack((line_label, mpl.lines.Line2D(range(1), range(1), color=colorlist[x], linestyle=linelist[x], marker=markerlist[x], markersize=7)))
            line_str   = np.hstack((line_str, leg_nam[x]))
        first_legend=plt.legend(line_label, line_str, fontsize=10, numpoints=1, loc=0, framealpha=1)
        plt.savefig(FIG_PATH+'/'+GRIB_PATH_DES+'_pair_prop_inten_byhour_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[0]+ \
            '_t'+str(thres)+'_r'+grid_res_agg_str+'_d'+'_'.join([str(i) for i in latlon_dims])+'.png', bbox_inches='tight',dpi=200)
        plt.close()
        os.system('scp '+FIG_PATH+'/'+GRIB_PATH_DES+'_pair_prop_inten_byhour_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[0]+ \
            '_t'+str(thres)+'_r'+grid_res_agg_str+'_d'+'_'.join([str(i) for i in latlon_dims])+'.png hpc@vm-lnx-rzdm06:/home/people/hpc/ftp/erickson/test2')
 
        #Plot showing mean object area/std and object count
        fig = plt.figure(figsize=(8,8))
        ax1 = fig.add_axes([0.1,0.1,0.8,0.8])
        ax1.plot(subset_hours, grid_pair_count[1,1],'-x',linewidth=1, label='walker position', color='blue')
        ax1.set_xlabel(lab_str[0],fontsize=14)
        ax1.set_ylabel('Total Object Count', color='b',fontsize=14)
        ax1.set_ylim(0,np.nanmax(grid_pair_count[1,1])*1.25)
        #Second part of plotyy
        ax2 = ax1.twinx()        
        ax2.errorbar(subset_hours,grid_pair_areamean[1,1],yerr=[grid_pair_areamean[1,1]-grid_pair_areastd[1,1,:,0],grid_pair_areastd[1,1,:,1]-grid_pair_areamean[1,1]],color='r',fmt='-x',capthick=2)
        ax2.plot(subset_hours, np.zeros(len(subset_hours)),linewidth=3,color='black')
        ax2.set_ylabel('Mean Object Area Difference (Grid Squares)', color='r',fontsize=14)
        ax2.set_ylim(-thres*5000,thres*5000)
        plt.title('Paired Object Count/Area Difference - Area Precip. >= '+str(thres)+'" Per '+'{0:.2f}'.format(pre_acc)+' Hour\n '+ \
            'From '+beg_date_str_lo+' to '+end_date_str_lo,fontsize=14) 
        #Set up the legend
        line_label=[]
        line_str=[];
        colorlist  = ['blue','red']
        leg_nam    = ['Total Object Count','Object Area Difference']
        markerlist = ['x','x'] 
        linelist   = ['-','-']
        for x in range(0,len(leg_nam)):
            line_label = np.hstack((line_label, mpl.lines.Line2D(range(1), range(1), color=colorlist[x], linestyle=linelist[x], marker=markerlist[x], markersize=7)))
            line_str   = np.hstack((line_str, leg_nam[x]))
        first_legend=plt.legend(line_label, line_str, fontsize=12, numpoints=1, loc=0, framealpha=1)
        plt.savefig(FIG_PATH+'/'+GRIB_PATH_DES+'_pair_prop_countarea_byhour_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[0]+ \
            '_t'+str(thres)+'_r'+grid_res_agg_str+'_d'+'_'.join([str(i) for i in latlon_dims])+'.png', bbox_inches='tight',dpi=200)
        plt.close()
        os.system('scp '+FIG_PATH+'/'+GRIB_PATH_DES+'_pair_prop_countarea_byhour_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[0]+ \
            '_t'+str(thres)+'_r'+grid_res_agg_str+'_d'+'_'.join([str(i) for i in latlon_dims])+'.png hpc@vm-lnx-rzdm06:/home/people/hpc/ftp/erickson/test2')

    elif grid_res_nat != []: 

        for hrs in range(0,len(subset_hours)): #loop through different hour subsets  
            
            ###############Plot Total Count###############
            #Create first colorlist
            my_cmap1 = copy.copy(mpl.cm.get_cmap('jet'))
            my_cmap1.set_under('white')
            [fig,ax] = cartopy_maps.plot_map(lat,lon)     
            #im = plt.imshow(grid_obs_count, interpolation='nearest', values=values, cmap=my_cmap1, norm=norm)
            cs = plt.pcolormesh(lon_nat-(grid_res_nat/2.0),lat_nat+(grid_res_nat/2.0),grid_pair_count[:,:,hrs],cmap=my_cmap1,vmin=0.01,vmax=np.nanmax(grid_pair_count)*1.05,transform=ccrs.PlateCarree())
            cs.cmap.set_under('white')
            cb = plt.colorbar(cs,ax=ax,extend='min')
            ax.set_title('Paired Object Total Count - '+'{0:.2f}'.format(pre_acc)+' Hour Precip. > '+str(thres)+'"\n'+ \
                'From '+beg_date_str_lo+' to '+end_date_str_lo,fontsize=13)
            plt.savefig(FIG_PATH+'/'+GRIB_PATH_DES+'_pair_prop_count_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[hrs]+ \
                '_t'+str(thres)+'_r'+grid_res_agg_str+'.png', bbox_inches='tight',dpi=200)
            plt.close()
            os.system('scp '+FIG_PATH+'/'+GRIB_PATH_DES+'_pair_prop_count_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[hrs]+ \
                '_t'+str(thres)+'_r'+grid_res_agg_str+'.png hpc@vm-lnx-rzdm06:/home/people/hpc/ftp/erickson/test2')

            ###############Plot Displacement and intensity simultaneously###############
            #Create first colorlist
            my_cmap1 = copy.copy(mpl.cm.get_cmap('RdYlGn'))
            
            #Determine max limit of colorbar
            if thres == 0.1:
                vmax = 0.05
            elif thres == 0.25:
                vmax = 0.1
            elif thres == 0.5:
                vmax = 0.2

            [fig,ax] = cartopy_maps.plot_map(lat,lon)
            im = plt.quiver(lon_nat-(grid_res_nat/2.0),lat_nat+(grid_res_nat/2.0),grid_pair_xmean[:,:,hrs]*((grid_pair_xmean[:,:,hrs]!=0*1) | (grid_pair_ymean[:,:,hrs]!=0*1)), \
                grid_pair_ymean[:,:,hrs]*((grid_pair_xmean[:,:,hrs]!=0*1) | (grid_pair_ymean[:,:,hrs]!=0*1)),grid_pair_int10mean_ns[:,:,hrs]*((grid_pair_xmean[:,:,hrs]!=0*1) \
                | (grid_pair_ymean[:,:,hrs]!=0*1)), cmap=my_cmap1,clim=(-vmax, vmax),units='inches',angles='xy',scale_units='inches', scale = 300, width = 0.03,linewidths=0.2, \
                edgecolors='k',transform=ccrs.PlateCarree())
            cs = plt.quiverkey(im, 0.68, 0.28, 100, '100 km', labelpos='E',coordinates='figure',transform=ccrs.PlateCarree())                
            cb = plt.colorbar(im,ax=ax,extend='min')
            ax.set_title('Paired Object Displacement and 10th Pctile of Intensity - '+'{0:.2f}'.format(pre_acc)+' Hour Precip. > '+str(thres)+'"\n'+ \
                'From '+beg_date_str_lo+' to '+end_date_str_lo,fontsize=13)
            plt.savefig(FIG_PATH+'/'+GRIB_PATH_DES+'_pair_prop_inten10Adisp_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[hrs]+ \
                '_t'+str(thres)+'_r'+grid_res_agg_str+'.png', bbox_inches='tight',dpi=200)   
            plt.close()
            os.system('scp '+FIG_PATH+'/'+GRIB_PATH_DES+'_pair_prop_inten10Adisp_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[hrs]+ \
                '_t'+str(thres)+'_r'+grid_res_agg_str+'.png hpc@vm-lnx-rzdm06:/home/people/hpc/ftp/erickson/test2')

            #Determine max limit of colorbar
            if thres == 0.1:
                vmax = 0.1
            elif thres == 0.25:
                vmax = 0.2
            elif thres == 0.5:
                vmax = 0.4

            [fig,ax] = cartopy_maps.plot_map(lat,lon)
            im = plt.quiver(lon_nat-(grid_res_nat/2.0),lat_nat+(grid_res_nat/2.0),grid_pair_xmean[:,:,hrs]*((grid_pair_xmean[:,:,hrs]!=0*1) | (grid_pair_ymean[:,:,hrs]!=0*1)), \
                grid_pair_ymean[:,:,hrs]*((grid_pair_xmean[:,:,hrs]!=0*1) | (grid_pair_ymean[:,:,hrs]!=0*1)),grid_pair_int50mean_ns[:,:,hrs]*((grid_pair_xmean[:,:,hrs]!=0*1) \
                | (grid_pair_ymean[:,:,hrs]!=0*1)), cmap=my_cmap1,clim=(-vmax, vmax),units='inches',angles='xy',scale_units='inches', scale = 300, width = 0.03, \
                linewidths=0.2,edgecolors='k',transform=ccrs.PlateCarree())
            cs = plt.quiverkey(im, 0.68, 0.28, 100, '100 km', labelpos='E',coordinates='figure',transform=ccrs.PlateCarree())                
            cb = plt.colorbar(im,ax=ax,extend='min')
            ax.set_title('Paired Object Displacement and 50th Pctile of Intensity - '+'{0:.2f}'.format(pre_acc)+' Hour Precip. > '+str(thres)+'"\n'+ \
                'From '+beg_date_str_lo+' to '+end_date_str_lo,fontsize=13)
            plt.savefig(FIG_PATH+'/'+GRIB_PATH_DES+'_pair_prop_inten50Adisp_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[hrs]+ \
                '_t'+str(thres)+'_r'+grid_res_agg_str+'.png', bbox_inches='tight',dpi=200)   
            plt.close()  
            os.system('scp '+FIG_PATH+'/'+GRIB_PATH_DES+'_pair_prop_inten50Adisp_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[hrs]+ \
                '_t'+str(thres)+'_r'+grid_res_agg_str+'.png hpc@vm-lnx-rzdm06:/home/people/hpc/ftp/erickson/test2')
            
            #Determine max limit of colorbar
            if thres == 0.1:
                vmax = 0.2
            elif thres == 0.25:
                vmax = 0.4
            elif thres == 0.5:
                vmax = 0.6

            [fig,ax] = cartopy_maps.plot_map(lat,lon)
            im = plt.quiver(lon_nat-(grid_res_nat/2.0),lat_nat+(grid_res_nat/2.0),grid_pair_xmean[:,:,hrs]*((grid_pair_xmean[:,:,hrs]!=0*1) | (grid_pair_ymean[:,:,hrs]!=0*1)), \
                grid_pair_ymean[:,:,hrs]*((grid_pair_xmean[:,:,hrs]!=0*1) | (grid_pair_ymean[:,:,hrs]!=0*1)),grid_pair_int90mean_ns[:,:,hrs]*((grid_pair_xmean[:,:,hrs]!=0*1) | \
                (grid_pair_ymean[:,:,hrs]!=0*1)), cmap=my_cmap1,clim=(-vmax, vmax),units='inches',angles='xy',scale_units='inches', scale = 300, width = 0.03,linewidths=0.2, \
                edgecolors='k',transform=ccrs.PlateCarree())
            cs = plt.quiverkey(im, 0.68, 0.28, 100, '100 km', labelpos='E',coordinates='figure',transform=ccrs.PlateCarree())                
            cb = plt.colorbar(im,ax=ax,extend='min')
            ax.set_title('Paired Object Displacement and 90th Pctile of Intensity - '+'{0:.2f}'.format(pre_acc)+' Hour Precip. > '+str(thres)+'"\n'+ \
                'From '+beg_date_str_lo+' to '+end_date_str_lo,fontsize=13)
            plt.savefig(FIG_PATH+'/'+GRIB_PATH_DES+'_pair_prop_inten90Adisp_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[hrs]+ \
                '_t'+str(thres)+'_r'+grid_res_agg_str+'.png', bbox_inches='tight',dpi=200)   
            plt.close()     
            os.system('scp '+FIG_PATH+'/'+GRIB_PATH_DES+'_pair_prop_inten90Adisp_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[hrs]+ \
                '_t'+str(thres)+'_r'+grid_res_agg_str+'.png hpc@vm-lnx-rzdm06:/home/people/hpc/ftp/erickson/test2')
             
            ###############Plot Model Intensity Mean Error###############

            #Create first colorlist
            my_cmap1 = copy.copy(mpl.cm.get_cmap('RdYlGn'))
            #Determine max limit of colorbar
            if thres == 0.1:
                vmax = 0.05
            elif thres == 0.25:
                vmax = 0.1
            elif thres == 0.5:
                vmax = 0.2

            [fig,ax] = cartopy_maps.plot_map(lat,lon)
            cs = plt.pcolormesh(lon_nat-(grid_res_nat/2.0),lat_nat+(grid_res_nat/2.0),grid_pair_int10mean[:,:,hrs],cmap=my_cmap1,vmin=-vmax,vmax=vmax,transform=ccrs.PlateCarree())
            cs.cmap.set_under('white')
            cb = plt.colorbar(cs,ax=ax)
            ax.set_title('Paired Object 10th Pctile of Intensity Mean Error - '+'{0:.2f}'.format(pre_acc)+' Hour Precip. > '+str(thres)+'"\n'+ \
                'From '+beg_date_str_lo+' to '+end_date_str_lo,fontsize=13)
            plt.savefig(FIG_PATH+'/'+GRIB_PATH_DES+'_pair_prop_inten10_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[hrs]+ \
                '_t'+str(thres)+'_r'+grid_res_agg_str+'.png', bbox_inches='tight',dpi=200)
            plt.close()
            os.system('scp '+FIG_PATH+'/'+GRIB_PATH_DES+'_pair_prop_inten10_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[hrs]+ \
                '_t'+str(thres)+'_r'+grid_res_agg_str+'.png hpc@vm-lnx-rzdm06:/home/people/hpc/ftp/erickson/test2')

            #Create first colorlist
            my_cmap1 = copy.copy(mpl.cm.get_cmap('RdYlGn'))
            #Determine max limit of colorbar
            if thres == 0.1:
                vmax = 0.1
            elif thres == 0.25:
                vmax = 0.2
            elif thres == 0.5:
                vmax = 0.4

            [fig,ax] = cartopy_maps.plot_map(lat,lon)
            #im = plt.imshow(grid_obs_count, interpolation='nearest', values=values, cmap=my_cmap1, norm=norm)
            cs = plt.pcolormesh(lon_nat-(grid_res_nat/2.0),lat_nat+(grid_res_nat/2.0),grid_pair_int50mean[:,:,hrs],cmap=my_cmap1,vmin=-vmax,vmax=vmax,transform=ccrs.PlateCarree())
            cs.cmap.set_under('white')
            cb = plt.colorbar(cs,ax=ax)
            ax.set_title('Paired Object 50th Pctile of Intensity Mean Error - '+'{0:.2f}'.format(pre_acc)+' Hour Precip. > '+str(thres)+'"\n'+ \
                'From '+beg_date_str_lo+' to '+end_date_str_lo,fontsize=13)
            plt.savefig(FIG_PATH+'/'+GRIB_PATH_DES+'_pair_prop_inten50_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[hrs]+ \
                '_t'+str(thres)+'_r'+grid_res_agg_str+'.png', bbox_inches='tight',dpi=200)
            plt.close()
            os.system('scp '+FIG_PATH+'/'+GRIB_PATH_DES+'_pair_prop_inten50_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[hrs]+ \
                '_t'+str(thres)+'_r'+grid_res_agg_str+'.png hpc@vm-lnx-rzdm06:/home/people/hpc/ftp/erickson/test2')

            #Create first colorlist
            my_cmap1 = copy.copy(mpl.cm.get_cmap('RdYlGn'))
            #Determine max limit of colorbar
            if thres == 0.1:
                vmax = 0.2
            elif thres == 0.25:
                vmax = 0.4
            elif thres == 0.5:
                vmax = 0.6
            
            [fig,ax] = cartopy_maps.plot_map(lat,lon)
            cs = plt.pcolormesh(lon_nat-(grid_res_nat/2.0),lat_nat+(grid_res_nat/2.0),grid_pair_int90mean[:,:,hrs],cmap=my_cmap1,vmin=-vmax,vmax=vmax,transform=ccrs.PlateCarree())
            cs.cmap.set_under('white')
            cb = plt.colorbar(cs,ax=ax)
            ax.set_title('Paired Object 90th Pctile of Intensity Mean Error - '+'{0:.2f}'.format(pre_acc)+' Hour Precip. > '+str(thres)+'"\n'+ \
                'From '+beg_date_str_lo+' to '+end_date_str_lo,fontsize=13)
            plt.savefig(FIG_PATH+'/'+GRIB_PATH_DES+'_pair_prop_inten90_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[hrs]+ \
                '_t'+str(thres)+'_r'+grid_res_agg_str+'.png', bbox_inches='tight',dpi=200)
            plt.close()
            os.system('scp '+FIG_PATH+'/'+GRIB_PATH_DES+'_pair_prop_inten90_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[hrs]+ \
                '_t'+str(thres)+'_r'+grid_res_agg_str+'.png hpc@vm-lnx-rzdm06:/home/people/hpc/ftp/erickson/test2')            
            ###############Plot Model Area Mean Error###############                                                                                                                                                                                                                                                                                                                                                                                              
            #Create first colorlist
            my_cmap1 = copy.copy(mpl.cm.get_cmap('coolwarm')) 
            
            #Determine max limit of colorbar
            vmax = 600

            [fig,ax] = cartopy_maps.plot_map(lat,lon)
            #im = plt.imshow(grid_obs_count, interpolation='nearest', values=values, cmap=my_cmap1, norm=norm)
            cs = plt.pcolormesh(lon_nat-(grid_res_nat/2.0),lat_nat+(grid_res_nat/2.0),grid_pair_areamean[:,:,hrs],cmap=my_cmap1,vmin=-vmax,vmax=vmax,transform=ccrs.PlateCarree())
            cs.cmap.set_under('white')
            cb = plt.colorbar(cs,ax=ax)
            ax.set_title('Paired Object Area Mean Error- '+'{0:.2f}'.format(pre_acc)+' Hour Precip. > '+str(thres)+'"\n'+ \
                'From '+beg_date_str_lo+' to '+end_date_str_lo,fontsize=13)
            plt.savefig(FIG_PATH+'/'+GRIB_PATH_DES+'_pair_prop_area_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[hrs]+ \
                '_t'+str(thres)+'_r'+grid_res_agg_str+'.png', bbox_inches='tight',dpi=200)  
            plt.close()
            os.system('scp '+FIG_PATH+'/'+GRIB_PATH_DES+'_pair_prop_area_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[hrs]+ \
                '_t'+str(thres)+'_r'+grid_res_agg_str+'.png hpc@vm-lnx-rzdm06:/home/people/hpc/ftp/erickson/test2')
 
            ###############Plot Model Angle Mean Error###############                                                                                                                                                                                                                                                                                                                                                                                              
            #Create first colorlist
            my_cmap1 = copy.copy(mpl.cm.get_cmap('coolwarm')) 
            
            #Determine max limit of colorbar
            vmax = 180

            [fig,ax] = cartopy_maps.plot_map(lat,lon)
            cs = plt.pcolormesh(lon_nat-(grid_res_nat/2.0),lat_nat+(grid_res_nat/2.0),grid_pair_angmean[:,:,hrs],cmap=my_cmap1,vmin=-vmax,vmax=vmax,transform=ccrs.PlateCarree())
            cs.cmap.set_under('white')
            cb = plt.colorbar(cs,ax=ax)
            ax.set_title('Paired Object Angle Mean Error- '+'{0:.2f}'.format(pre_acc)+' Hour Precip. > '+str(thres)+'"\n'+ \
                'From '+beg_date_str_lo+' to '+end_date_str_lo,fontsize=13) 
            plt.savefig(FIG_PATH+'/'+GRIB_PATH_DES+'_pair_prop_angle_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[hrs]+ \
                '_t'+str(thres)+'_r'+grid_res_agg_str+'.png', bbox_inches='tight',dpi=200)  
            plt.close()
            os.system('scp '+FIG_PATH+'/'+GRIB_PATH_DES+'_pair_prop_angle_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[hrs]+ \
                '_t'+str(thres)+'_r'+grid_res_agg_str+'.png hpc@vm-lnx-rzdm06:/home/people/hpc/ftp/erickson/test2')

elif subset_data == 'PAIRinit':

    if grid_res_nat == []: #If everything is aggregated along the time dimension only
        
        #Subset magnitude/angle differences and then create wind rose plot
        angle_temp = grid_init_angle[1][1]
        mag_temp   = grid_init_magnitude[1][1]
        angle_temp = angle_temp[~np.isnan(angle_temp)]
        mag_temp   = mag_temp[~np.isnan(mag_temp)]

        ax = WindroseAxes.from_ax()
        ax.bar(angle_temp, mag_temp, bins=[0,10,20,50,75,100,125,150,200,400,500],blowto=True)
        ax.set_legend()
        plt.title('Paired Model Displacement (km) at Init. - Area Precip. >= '+str(thres)+'" Per '+'{0:.2f}'.format(pre_acc)+' Hour\n '+ \
            'From '+beg_date_str_lo+' to '+end_date_str_lo,fontsize=14) 
        plt.savefig(FIG_PATH+'/'+GRIB_PATH_DES+'_pair_init_rose_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[0]+ \
            '_t'+str(thres)+'_r'+grid_res_agg_str+'_d'+'_'.join([str(i) for i in latlon_dims])+'.png', bbox_inches='tight',dpi=200)
        plt.close()
        os.system('scp '+FIG_PATH+'/'+GRIB_PATH_DES+'_pair_init_rose_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[0]+ \
            '_t'+str(thres)+'_r'+grid_res_agg_str+'_d'+'_'.join([str(i) for i in latlon_dims])+'.png hpc@vm-lnx-rzdm06:/home/people/hpc/ftp/erickson/test2')

        #Plot showing the x displacement/std and y displacement/std
        fig = plt.figure(figsize=(8,8))
        ax1 = fig.add_axes([0.1,0.1,0.8,0.8])
        ax1.errorbar(subset_hours+0.1,grid_init_xmean[1,1],yerr=[grid_init_xmean[1,1]-grid_init_xstd[1,1,:,0],grid_init_xstd[1,1,:,1]-grid_init_xmean[1,1]],color='b',fmt='-x',capthick=2)
        ax1.plot(subset_hours, np.zeros(len(subset_hours)),linewidth=3,color='black')
        ax1.set_xlabel(lab_str[0],fontsize=14)
        ax1.set_ylabel('East-West Average Displacement (km)', color='b',fontsize=14)
        ax1.set_ylim(-thres*3000,thres*3000)
        #Second part of plotyy
        ax2 = ax1.twinx()
        ax1.errorbar(subset_hours-0.1,grid_init_ymean[1,1],yerr=[grid_init_ymean[1,1]-grid_init_ystd[1,1,:,0],grid_init_ystd[1,1,:,1]-grid_init_ymean[1,1]],color='r',fmt='-x',capthick=2)
        ax2.set_ylabel('North-South Average Displacement (km)', color='r',fontsize=14)
        ax2.set_ylim(-thres*3000,thres*3000)
        plt.title('Average Displacement at Init. - Area Precip. >= '+str(thres)+'" Per '+'{0:.2f}'.format(pre_acc)+' Hour\n '+ \
            'From '+beg_date_str_lo+' to '+end_date_str_lo,fontsize=14) 
        #Set up the legend
        line_label=[]
        line_str=[]
        leg_nam = ['East-West Displacement','North-South Displacement']
        colorlist = ['blue','red']
        markerlist = ['x','x']   
        linelist = ['-','-']
        for x in range(0,len(leg_nam)):
            line_label = np.hstack((line_label, mpl.lines.Line2D(range(1), range(1), color=colorlist[x], linestyle=linelist[x], marker=markerlist[x], markersize=7)))
            line_str   = np.hstack((line_str, leg_nam[x]))
        first_legend=plt.legend(line_label, line_str, fontsize=12, numpoints=1, loc=0, framealpha=1)
        ax2 = plt.gca().add_artist(first_legend)
        plt.savefig(FIG_PATH+'/'+GRIB_PATH_DES+'_pair_init_xydisp_byhour_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[0]+ \
            '_t'+str(thres)+'_r'+grid_res_agg_str+'_d'+'_'.join([str(i) for i in latlon_dims])+'.png', bbox_inches='tight',dpi=200)
        plt.close()
        os.system('scp '+FIG_PATH+'/'+GRIB_PATH_DES+'_pair_init_xydisp_byhour_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[0]+ \
            '_t'+str(thres)+'_r'+grid_res_agg_str+'_d'+'_'.join([str(i) for i in latlon_dims])+'.png hpc@vm-lnx-rzdm06:/home/people/hpc/ftp/erickson/test2')
        
        #Plot showing the 10/50/90th percentile of intensity/std and 
        fig = plt.figure(figsize=(8,8))
        ax = fig.add_axes([0.1,0.1,0.8,0.8])
        ax.errorbar(subset_hours-0.15,grid_init_int10mean[1,1],yerr=[grid_init_int10mean[1,1]-grid_init_int10std[1,1,:,0],grid_init_int10std[1,1,:,1]-grid_init_int10mean[1,1]],color='b',fmt='-x',capthick=2)
        ax.errorbar(subset_hours+0.00,grid_init_int50mean[1,1],yerr=[grid_init_int50mean[1,1]-grid_init_int50std[1,1,:,0],grid_init_int50std[1,1,:,1]-grid_init_int90mean[1,1]],color='g',fmt='-x',capthick=2)
        ax.errorbar(subset_hours+0.15,grid_init_int90mean[1,1],yerr=[grid_init_int90mean[1,1]-grid_init_int90std[1,1,:,0],grid_init_int90std[1,1,:,1]-grid_init_int90mean[1,1]],color='r',fmt='-x',capthick=2)
        plt.plot(subset_hours, np.zeros(len(subset_hours)),linewidth=3,color='black')
        plt.xlabel(lab_str[0],fontsize=14)
        plt.ylabel('Mean Object Intensity Difference (Inches)',fontsize=14)
        plt.ylim((-thres*3.5,thres*3.5))
        plt.title('Paired Intensity Difference at Init. - Area Precip. >= '+str(thres)+'" Per '+'{0:.2f}'.format(pre_acc)+' Hour\n '+ \
            'From '+beg_date_str_lo+' to '+end_date_str_lo,fontsize=14) 
        #Set up the legend
        line_label=[]
        line_str=[];
        leg_nam = ['10th Object Intensity Difference','50th Object Intensity Difference','90th Object Intensity Difference']
        colorlist  = ['blue','green','red']
        markerlist = ['x','x','x'] 
        linelist   = ['-','-','-']
        for x in range(0,len(leg_nam)):
            line_label = np.hstack((line_label, mpl.lines.Line2D(range(1), range(1), color=colorlist[x], linestyle=linelist[x], marker=markerlist[x], markersize=7)))
            line_str   = np.hstack((line_str, leg_nam[x]))
        first_legend=plt.legend(line_label, line_str, fontsize=10, numpoints=1, loc=0, framealpha=1)
        plt.savefig(FIG_PATH+'/'+GRIB_PATH_DES+'_pair_init_inten_byhour_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[0]+ \
            '_t'+str(thres)+'_r'+grid_res_agg_str+'_d'+'_'.join([str(i) for i in latlon_dims])+'.png', bbox_inches='tight',dpi=200)
        plt.close()
        os.system('scp '+FIG_PATH+'/'+GRIB_PATH_DES+'_pair_init_inten_byhour_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[0]+ \
            '_t'+str(thres)+'_r'+grid_res_agg_str+'_d'+'_'.join([str(i) for i in latlon_dims])+'.png hpc@vm-lnx-rzdm06:/home/people/hpc/ftp/erickson/test2')
        
        #Plot showing mean object area/std and object count
        fig = plt.figure(figsize=(8,8))
        ax1 = fig.add_axes([0.1,0.1,0.8,0.8])
        ax1.plot(subset_hours, grid_init_count[1,1],'-x',linewidth=1, label='walker position', color='blue')
        ax1.set_xlabel(lab_str[0],fontsize=14)
        ax1.set_ylabel('Total Object Count', color='b',fontsize=14)
        ax1.set_ylim(0,np.nanmax(grid_init_count[1,1])*1.25)
        #Second part of plotyy
        ax2 = ax1.twinx()
        ax2.errorbar(subset_hours,grid_init_areamean[1,1],yerr=[grid_init_areamean[1,1]-grid_init_areastd[1,1,:,0],grid_init_areastd[1,1,:,1]-grid_init_areamean[1,1]],color='r',fmt='-x',capthick=2)
        ax2.plot(subset_hours, np.zeros(len(subset_hours)),linewidth=3,color='black')
        ax2.set_ylabel('Mean Object Area Difference (Grid Squares)', color='r',fontsize=14)
        ax2.set_ylim(-thres*5000,thres*5000)
        plt.title('Paired Object Count/Area Difference at Init. - Area Precip. >= '+str(thres)+'" Per '+'{0:.2f}'.format(pre_acc)+' Hour\n '+ \
            'From '+beg_date_str_lo+' to '+end_date_str_lo,fontsize=14) 
        #Set up the legend
        line_label=[]
        line_str=[];
        colorlist  = ['blue','red']
        leg_nam    = ['Total Object Count','Object Area Difference']
        markerlist = ['x','x']   
        linelist   = ['-','-']
        for x in range(0,len(leg_nam)):
            line_label = np.hstack((line_label, mpl.lines.Line2D(range(1), range(1), color=colorlist[x], linestyle=linelist[x], marker=markerlist[x], markersize=7)))
            line_str   = np.hstack((line_str, leg_nam[x]))
        first_legend=plt.legend(line_label, line_str, fontsize=12, numpoints=1, loc=0, framealpha=1)
        plt.savefig(FIG_PATH+'/'+GRIB_PATH_DES+'_pair_init_countarea_byhour_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[0]+ \
            '_t'+str(thres)+'_r'+grid_res_agg_str+'_d'+'_'.join([str(i) for i in latlon_dims])+'.png', bbox_inches='tight',dpi=200)
        plt.close()
        os.system('scp '+FIG_PATH+'/'+GRIB_PATH_DES+'_pair_init_countarea_byhour_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[0]+ \
            '_t'+str(thres)+'_r'+grid_res_agg_str+'_d'+'_'.join([str(i) for i in latlon_dims])+'.png hpc@vm-lnx-rzdm06:/home/people/hpc/ftp/erickson/test2')

        #Plot showing time mean/std
        fig = plt.figure(figsize=(8,8))
        ax = fig.add_axes([0.1,0.1,0.8,0.8])
        plt.errorbar(subset_hours,grid_init_timemean[1,1],yerr=[grid_init_timemean[1,1]-grid_init_timestd[1,1,:,0],grid_init_timestd[1,1,:,1]-grid_init_timemean[1,1]],color='b',fmt='-x',capthick=2)
        plt.plot(subset_hours, np.zeros(len(subset_hours)),linewidth=3,color='black')
        plt.xlabel(lab_str[0],fontsize=14)
        plt.ylabel('Mean Object Time Difference (Increments)',fontsize=14)
        plt.ylim((-15,15))
        plt.title('Paired Object Time Difference at Init. - Area Precip. >= '+str(thres)+'" Per '+'{0:.2f}'.format(pre_acc)+' Hour\n '+ \
            'From '+beg_date_str_lo+' to '+end_date_str_lo,fontsize=14) 
        #Set up the legend
        line_label=[]
        line_str=[];
        leg_nam = ['Object Time Difference']
        colorlist  = ['blue']
        markerlist = ['x']  
        linelist   = ['-']
        for x in range(0,len(leg_nam)):
            line_label = np.hstack((line_label, mpl.lines.Line2D(range(1), range(1), color=colorlist[x], linestyle=linelist[x], marker=markerlist[x], markersize=7)))
            line_str   = np.hstack((line_str, leg_nam[x]))
        first_legend=plt.legend(line_label, line_str, fontsize=10, numpoints=1, loc=0, framealpha=1)
        plt.savefig(FIG_PATH+'/'+GRIB_PATH_DES+'_pair_init_time_byhour_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[0]+ \
            '_t'+str(thres)+'_r'+grid_res_agg_str+'_d'+'_'.join([str(i) for i in latlon_dims])+'.png', bbox_inches='tight',dpi=200)
        plt.close()
        os.system('scp '+FIG_PATH+'/'+GRIB_PATH_DES+'_pair_init_time_byhour_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[0]+ \
            '_t'+str(thres)+'_r'+grid_res_agg_str+'_d'+'_'.join([str(i) for i in latlon_dims])+'.png hpc@vm-lnx-rzdm06:/home/people/hpc/ftp/erickson/test2')
        
    elif grid_res_nat != []: 
        
        for hrs in range(0,len(subset_hours)): #loop through different hour subsets  
            
            ###############Plot Total Count###############                                                                                                                                                                                                                                                                                                                                                                                              
            #Create first colorlist
            my_cmap1 = copy.copy(mpl.cm.get_cmap('jet'))
            my_cmap1.set_under('white')

            [fig,ax] = cartopy_maps.plot_map(lat,lon)
            cs = plt.pcolormesh(lon_nat-(grid_res_nat/2.0),lat_nat+(grid_res_nat/2.0),grid_init_count[:,:,hrs],cmap=my_cmap1,vmin=0.01,vmax=np.nanmax(grid_init_count)*1.05,transform=ccrs.PlateCarree())
            cs.cmap.set_under('white')
            cb = plt.colorbar(cs,ax=ax,extend='min')
            ax.set_title('Object Initiation Total Count - '+'{0:.2f}'.format(pre_acc)+' Hour Precip. > '+str(thres)+'"\n'+ \
                'From '+beg_date_str_lo+' to '+end_date_str_lo,fontsize=13)
            plt.savefig(FIG_PATH+'/'+GRIB_PATH_DES+'_prop_init_count_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[hrs]+ \
                '_t'+str(thres)+'_r'+grid_res_agg_str+'.png', bbox_inches='tight',dpi=200)      
            plt.close()
            os.system('scp '+FIG_PATH+'/'+GRIB_PATH_DES+'_prop_init_count_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[hrs]+ \
                '_t'+str(thres)+'_r'+grid_res_agg_str+'.png hpc@vm-lnx-rzdm06:/home/people/hpc/ftp/erickson/test2')
                
            ###############Plot Displacement and intensity simultaneously###############
            #Create first colorlist
            my_cmap1 = copy.copy(mpl.cm.get_cmap('RdYlGn'))
            
            #Determine max limit of colorbar
            if thres == 0.1:
                vmax = 0.05
            elif thres == 0.25:
                vmax = 0.1
            elif thres == 0.5:
                vmax = 0.2

            [fig,ax] = cartopy_maps.plot_map(lat,lon)
            im = plt.quiver(lon_nat-(grid_res_nat/2.0),lat_nat+(grid_res_nat/2.0),grid_init_xmean[:,:,hrs]*((grid_init_xmean[:,:,hrs]!=0*1) | (grid_init_ymean[:,:,hrs]!=0*1)), \
                grid_init_ymean[:,:,hrs]*((grid_init_xmean[:,:,hrs]!=0*1) | (grid_init_ymean[:,:,hrs]!=0*1)),grid_init_int10mean_ns[:,:,hrs]*((grid_init_xmean[:,:,hrs]!=0*1) | \
                (grid_init_ymean[:,:,hrs]!=0*1)),cmap=my_cmap1,clim=(-vmax, vmax),units='inches',angles='xy',scale_units='inches', scale = 300, width = 0.03,linewidths=0.2, \
                edgecolors='k',transform=ccrs.PlateCarree())
            cs = plt.quiverkey(im, 0.68, 0.28, 100, '100 km', labelpos='E',coordinates='figure',transform=ccrs.PlateCarree())                
            cb = plt.colorbar(im,ax=ax,extend='min')
            ax.set_title('Object Initiation Displacement and 10th Pctile of Intensity - '+'{0:.2f}'.format(pre_acc)+' Hour Precip. > '+str(thres)+'"\n'+ \
                'From '+beg_date_str_lo+' to '+end_date_str_lo,fontsize=13)
            plt.savefig(FIG_PATH+'/'+GRIB_PATH_DES+'_prop_init_inten10Adisp_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[hrs]+ \
                '_t'+str(thres)+'_r'+grid_res_agg_str+'.png', bbox_inches='tight',dpi=200)     
            plt.close()
            os.system('scp '+FIG_PATH+'/'+GRIB_PATH_DES+'_prop_init_inten10Adisp_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[hrs]+ \
                '_t'+str(thres)+'_r'+grid_res_agg_str+'.png hpc@vm-lnx-rzdm06:/home/people/hpc/ftp/erickson/test2')
 
            #Determine max limit of colorbar
            if thres == 0.1:
                vmax = 0.1
            elif thres == 0.25:
                vmax = 0.2
            elif thres == 0.5:
                vmax = 0.4

            [fig,ax] = cartopy_maps.plot_map(lat,lon)
            im = plt.quiver(lon_nat-(grid_res_nat/2.0),lat_nat+(grid_res_nat/2.0),grid_init_xmean[:,:,hrs]*((grid_init_xmean[:,:,hrs]!=0*1) | (grid_init_ymean[:,:,hrs]!=0*1)), \
                grid_init_ymean[:,:,hrs]*((grid_init_xmean[:,:,hrs]!=0*1) | (grid_init_ymean[:,:,hrs]!=0*1)),grid_init_int50mean_ns[:,:,hrs]*((grid_init_xmean[:,:,hrs]!=0*1) | \
                (grid_init_ymean[:,:,hrs]!=0*1)),cmap=my_cmap1,clim=(-vmax, vmax),units='inches',angles='xy',scale_units='inches', scale = 300, width = 0.03,linewidths=0.2, \
                edgecolors='k',transform=ccrs.PlateCarree())
            cs = plt.quiverkey(im, 0.68, 0.28, 100, '100 km', labelpos='E',coordinates='figure')                
            cb = plt.colorbar(im,ax=ax,extend='min')
            ax.set_title('Object Initiation Displacement and 50th Pctile of Intensity - '+'{0:.2f}'.format(pre_acc)+' Hour Precip. > '+str(thres)+'"\n'+ \
                'From '+beg_date_str_lo+' to '+end_date_str_lo,fontsize=13)
            plt.savefig(FIG_PATH+'/'+GRIB_PATH_DES+'_prop_init_inten50Adisp_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[hrs]+ \
                '_t'+str(thres)+'_r'+grid_res_agg_str+'.png', bbox_inches='tight',dpi=200)     
            plt.close()
            os.system('scp '+FIG_PATH+'/'+GRIB_PATH_DES+'_prop_init_inten50Adisp_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[hrs]+ \
                '_t'+str(thres)+'_r'+grid_res_agg_str+'.png hpc@vm-lnx-rzdm06:/home/people/hpc/ftp/erickson/test2')
                  
            #Determine max limit of colorbar
            if thres == 0.1:
                vmax = 0.2
            elif thres == 0.25:
                vmax = 0.4
            elif thres == 0.5:
                vmax = 0.6

            [fig,ax] = cartopy_maps.plot_map(lat,lon)
            im = plt.quiver(lon_nat-(grid_res_nat/2.0),lat_nat+(grid_res_nat/2.0),grid_init_xmean[:,:,hrs]*((grid_init_xmean[:,:,hrs]!=0*1) | (grid_init_ymean[:,:,hrs]!=0*1)), \
                grid_init_ymean[:,:,hrs]*((grid_init_xmean[:,:,hrs]!=0*1) | (grid_init_ymean[:,:,hrs]!=0*1)),grid_init_int90mean_ns[:,:,hrs]*((grid_init_xmean[:,:,hrs]!=0*1) \
                | (grid_init_ymean[:,:,hrs]!=0*1)), cmap=my_cmap1,clim=(-vmax, vmax),units='inches', angles='xy',scale_units='inches', scale = 300, width = 0.03,linewidths=0.2, \
                edgecolors='k',transform=ccrs.PlateCarree())
            cs = plt.quiverkey(im, 0.68, 0.28, 100, '100 km', labelpos='E',coordinates='figure',transform=ccrs.PlateCarree())                
            cb = plt.colorbar(im,ax=ax,extend='min')
            ax.set_title('Object Initiation Displacement and 90th Pctile of Intensity - '+'{0:.2f}'.format(pre_acc)+' Hour Precip. > '+str(thres)+'"\n'+ \
                'From '+beg_date_str_lo+' to '+end_date_str_lo,fontsize=13)
            plt.savefig(FIG_PATH+'/'+GRIB_PATH_DES+'_prop_init_inten90Adisp_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[hrs]+ \
                '_t'+str(thres)+'_r'+grid_res_agg_str+'.png', bbox_inches='tight',dpi=200)     
            plt.close()
            os.system('scp '+FIG_PATH+'/'+GRIB_PATH_DES+'_prop_init_inten90Adisp_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[hrs]+ \
                '_t'+str(thres)+'_r'+grid_res_agg_str+'.png hpc@vm-lnx-rzdm06:/home/people/hpc/ftp/erickson/test2')
                      
            ###############Plot Model Intensity Mean Error###############

            #Create first colorlist
            my_cmap1 = copy.copy(mpl.cm.get_cmap('RdYlGn'))
            
            #Determine max limit of colorbar
            if thres == 0.1:
                vmax = 0.05
            elif thres == 0.25:
                vmax = 0.1
            elif thres == 0.5:
                vmax = 0.2
                
            [fig,ax] = cartopy_maps.plot_map(lat,lon)
            cs = plt.pcolormesh(lon_nat-(grid_res_nat/2.0),lat_nat+(grid_res_nat/2.0),grid_init_int10mean[:,:,hrs],cmap=my_cmap1,vmin=-vmax,vmax=vmax,transform=ccrs.PlateCarree())
            cs.cmap.set_under('white')
            cb = plt.colorbar(cs,ax=ax)
            ax.set_title('Object Initiation 10 Pctile of Intensity Mean Error - '+'{0:.2f}'.format(pre_acc)+' Hour Precip. > '+str(thres)+'"\n'+ \
                'From '+beg_date_str_lo+' to '+end_date_str_lo,fontsize=13)
            plt.savefig(FIG_PATH+'/'+GRIB_PATH_DES+'_prop_init_inten10_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[hrs]+ \
                '_t'+str(thres)+'_r'+grid_res_agg_str+'.png', bbox_inches='tight',dpi=200)
            plt.close()
            os.system('scp '+FIG_PATH+'/'+GRIB_PATH_DES+'_prop_init_inten10_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[hrs]+ \
                '_t'+str(thres)+'_r'+grid_res_agg_str+'.png hpc@vm-lnx-rzdm06:/home/people/hpc/ftp/erickson/test2')

            #Determine max limit of colorbar
            if thres == 0.1:
                vmax = 0.1
            elif thres == 0.25:
                vmax = 0.2
            elif thres == 0.5:
                vmax = 0.4
            
            [fig,ax] = cartopy_maps.plot_map(lat,lon)
            cs = plt.pcolormesh(lon_nat-(grid_res_nat/2.0),lat_nat+(grid_res_nat/2.0),grid_init_int50mean[:,:,hrs],cmap=my_cmap1,vmin=-vmax,vmax=vmax,transform=ccrs.PlateCarree())
            cs.cmap.set_under('white')
            cb = plt.colorbar(cs,ax=ax)
            ax.set_title('Object Initiation 50 Pctile of Intensity Mean Error - '+'{0:.2f}'.format(pre_acc)+' Hour Precip. > '+str(thres)+'"\n'+ \
                'From '+beg_date_str_lo+' to '+end_date_str_lo,fontsize=13)
            plt.savefig(FIG_PATH+'/'+GRIB_PATH_DES+'_prop_init_inten50_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[hrs]+ \
                '_t'+str(thres)+'_r'+grid_res_agg_str+'.png', bbox_inches='tight',dpi=200)
            plt.close() 
            os.system('scp '+FIG_PATH+'/'+GRIB_PATH_DES+'_prop_init_inten50_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[hrs]+ \
                '_t'+str(thres)+'_r'+grid_res_agg_str+'.png hpc@vm-lnx-rzdm06:/home/people/hpc/ftp/erickson/test2')
              
            #Determine max limit of colorbar
            if thres == 0.1:
                vmax = 0.2
            elif thres == 0.25:
                vmax = 0.4
            elif thres == 0.5:
                vmax = 0.6

            [fig,ax] = cartopy_maps.plot_map(lat,lon)
            cs = plt.pcolormesh(lon_nat-(grid_res_nat/2.0),lat_nat+(grid_res_nat/2.0),grid_init_int90mean[:,:,hrs],cmap=my_cmap1,vmin=-vmax,vmax=vmax,transform=ccrs.PlateCarree())
            cs.cmap.set_under('white')
            cb = plt.colorbar(cs,ax=ax)
            ax.set_title('Object Initiation 90 Pctile of Intensity Mean Error - '+'{0:.2f}'.format(pre_acc)+' Hour Precip. > '+str(thres)+'"\n'+ \
                'From '+beg_date_str_lo+' to '+end_date_str_lo,fontsize=13)
            plt.savefig(FIG_PATH+'/'+GRIB_PATH_DES+'_prop_init_inten90_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[hrs]+ \
                '_t'+str(thres)+'_r'+grid_res_agg_str+'.png', bbox_inches='tight',dpi=200)
            plt.close() 
            os.system('scp '+FIG_PATH+'/'+GRIB_PATH_DES+'_prop_init_inten90_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[hrs]+ \
                '_t'+str(thres)+'_r'+grid_res_agg_str+'.png hpc@vm-lnx-rzdm06:/home/people/hpc/ftp/erickson/test2')
                           
            ###############Plot Mean Error in Time###############

            #Create first colorlist
            my_cmap1 = copy.copy(mpl.cm.get_cmap('RdYlGn'))
            
            #Determine max limit of colorbar
            vmax = 3

            [fig,ax] = cartopy_maps.plot_map(lat,lon)
            cs = plt.pcolormesh(lon_nat-(grid_res_nat/2.0),lat_nat+(grid_res_nat/2.0),grid_init_timemean[:,:,hrs],cmap=my_cmap1,vmin=-vmax,vmax=vmax,transform=ccrs.PlateCarree())
            cs.cmap.set_under('white')
            cb = plt.colorbar(cs,ax=ax)
            ax.set_title('Object Initiation Time Mean Error - '+'{0:.2f}'.format(pre_acc)+' Hour Precip. > '+str(thres)+'"\n'+ \
                'From '+beg_date_str_lo+' to '+end_date_str_lo,fontsize=13)
            plt.savefig(FIG_PATH+'/'+GRIB_PATH_DES+'_prop_init_time_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[hrs]+ \
                '_t'+str(thres)+'_r'+grid_res_agg_str+'.png', bbox_inches='tight',dpi=200)
            plt.close()
            os.system('scp '+FIG_PATH+'/'+GRIB_PATH_DES+'_prop_init_time_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[hrs]+ \
                '_t'+str(thres)+'_r'+grid_res_agg_str+'.png hpc@vm-lnx-rzdm06:/home/people/hpc/ftp/erickson/test2')
            
            ###############Plot Model Area Mean Error###############

            #Create first colorlist
            my_cmap1 = copy.copy(mpl.cm.get_cmap('coolwarm')) 
            
            #Determine max limit of colorbar
            vmax = 600
            [fig,ax] = cartopy_maps.plot_map(lat,lon)
            cs = plt.pcolormesh(lon_nat-(grid_res_nat/2.0),lat_nat+(grid_res_nat/2.0),grid_init_areamean[:,:,hrs],cmap=my_cmap1,vmin=-vmax,vmax=vmax,transform=ccrs.PlateCarree())
            cs.cmap.set_under('white')
            cb = plt.colorbar(cs,ax=ax)
            ax.set_title('Object Initiation Area Mean Error- '+'{0:.2f}'.format(pre_acc)+' Hour Precip. > '+str(thres)+'"\n'+ \
                'From '+beg_date_str_lo+' to '+end_date_str_lo,fontsize=13)
            plt.savefig(FIG_PATH+'/'+GRIB_PATH_DES+'_prop_init_area_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[hrs]+ \
                '_t'+str(thres)+'_r'+grid_res_agg_str+'.png', bbox_inches='tight',dpi=200)  
            plt.close()
            os.system('scp '+FIG_PATH+'/'+GRIB_PATH_DES+'_prop_init_area_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[hrs]+ \
                '_t'+str(thres)+'_r'+grid_res_agg_str+'.png hpc@vm-lnx-rzdm06:/home/people/hpc/ftp/erickson/test2')
 
            ###############Plot Model Angle Mean Error###############

            #Create first colorlist
            my_cmap1 = copy.copy(mpl.cm.get_cmap('coolwarm')) 
            
            #Determine max limit of colorbar
            vmax = 180
            [fig,ax] = cartopy_maps.plot_map(lat,lon)
            cs = plt.pcolormesh(lon_nat-(grid_res_nat/2.0),lat_nat+(grid_res_nat/2.0),grid_init_angmean[:,:,hrs],cmap=my_cmap1,vmin=-vmax,vmax=vmax,transform=ccrs.PlateCarree())
            cs.cmap.set_under('white')
            cb = plt.colorbar(cs,ax=ax)
            ax.set_title('Object Initiation Angle Mean Error- '+'{0:.2f}'.format(pre_acc)+' Hour Precip. > '+str(thres)+'"\n'+ \
                'From '+beg_date_str_lo+' to '+end_date_str_lo,fontsize=13)
            plt.savefig(FIG_PATH+'/'+GRIB_PATH_DES+'_prop_init_angle_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[hrs]+ \
                '_t'+str(thres)+'_r'+grid_res_agg_str+'.png', bbox_inches='tight',dpi=200)  
            plt.close()    
            os.system('scp '+FIG_PATH+'/'+GRIB_PATH_DES+'_prop_init_angle_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[hrs]+ \
                '_t'+str(thres)+'_r'+grid_res_agg_str+'.png hpc@vm-lnx-rzdm06:/home/people/hpc/ftp/erickson/test2')
        
elif subset_data == 'PAIRdisp':
         
    if grid_res_nat == []: #If everything is aggregated along the time dimension only

        #Subset magnitude/angle differences and then create wind rose plot
        angle_temp = grid_disp_angle[1][1]
        mag_temp   = grid_disp_magnitude[1][1]
        angle_temp = angle_temp[~np.isnan(angle_temp)]
        mag_temp   = mag_temp[~np.isnan(mag_temp)]

        ax = WindroseAxes.from_ax()
        ax.bar(angle_temp, mag_temp, bins=[0,10,20,50,75,100,125,150,200,400,500],blowto=True)
        ax.set_legend()
        plt.title('Paired Model Displacement (km) at Disp. - Area Precip. >= '+str(thres)+'" Per '+'{0:.2f}'.format(pre_acc)+' Hour\n '+ \
            'From '+beg_date_str_lo+' to '+end_date_str_lo,fontsize=14) 
        plt.savefig(FIG_PATH+'/'+GRIB_PATH_DES+'_pair_disp_rose_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[0]+ \
            '_t'+str(thres)+'_r'+grid_res_agg_str+'_d'+'_'.join([str(i) for i in latlon_dims])+'.png', bbox_inches='tight',dpi=200)
        plt.close()   
        os.system('scp '+FIG_PATH+'/'+GRIB_PATH_DES+'_pair_disp_rose_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[0]+ \
            '_t'+str(thres)+'_r'+grid_res_agg_str+'_d'+'_'.join([str(i) for i in latlon_dims])+'.png hpc@vm-lnx-rzdm06:/home/people/hpc/ftp/erickson/test2')
        
        #Plot showing the x displacement/std and y displacement/std
        fig = plt.figure(figsize=(8,8))
        ax1 = fig.add_axes([0.1,0.1,0.8,0.8])
        ax1.errorbar(subset_hours-0.1,grid_disp_xmean[1,1],yerr=[grid_disp_xmean[1,1]-grid_disp_xstd[1,1,:,0],grid_disp_xstd[1,1,:,1]-grid_disp_xmean[1,1]],color='b',fmt='-x',capthick=2)
        ax1.plot(subset_hours, np.zeros(len(subset_hours)),linewidth=3,color='black')
        ax1.set_xlabel(lab_str[0],fontsize=14)
        ax1.set_ylabel('East-West Average Displacement (km)', color='b',fontsize=14)
        ax1.set_ylim(-thres*3000,thres*3000)
        #Second part of plotyy
        ax2 = ax1.twinx()
        ax2.errorbar(subset_hours+0.1,grid_disp_ymean[1,1],yerr=[grid_disp_ymean[1,1]-grid_disp_ystd[1,1,:,0],grid_disp_ystd[1,1,:,1]-grid_disp_ymean[1,1]],color='r',fmt='-x',capthick=2)
        ax2.set_ylabel('North-South Average Displacement (km)', color='r',fontsize=14)
        ax2.set_ylim(-thres*3000,thres*3000)
        plt.title('Average Displacement at Disp. - Area Precip. >= '+str(thres)+'" Per '+'{0:.2f}'.format(pre_acc)+' Hour\n '+ \
            'From '+beg_date_str_lo+' to '+end_date_str_lo,fontsize=14) 
        #Set up the legend
        line_label=[]
        line_str=[]
        leg_nam = ['East-West Displacement','North-South Displacement']
        colorlist = ['blue','red']
        markerlist = ['x','x']
        linelist = ['-','-']
        for x in range(0,len(leg_nam)):
            line_label = np.hstack((line_label, mpl.lines.Line2D(range(1), range(1), color=colorlist[x], linestyle=linelist[x], marker=markerlist[x], markersize=7)))
            line_str   = np.hstack((line_str, leg_nam[x]))
        first_legend=plt.legend(line_label, line_str, fontsize=12, numpoints=1, loc=0, framealpha=1)
        ax2 = plt.gca().add_artist(first_legend)
        plt.savefig(FIG_PATH+'/'+GRIB_PATH_DES+'_pair_disp_xydisp_byhour_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[0]+ \
            '_t'+str(thres)+'_r'+grid_res_agg_str+'_d'+'_'.join([str(i) for i in latlon_dims])+'.png', bbox_inches='tight',dpi=200)
        plt.close()
        os.system('scp '+FIG_PATH+'/'+GRIB_PATH_DES+'_pair_disp_xydisp_byhour_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[0]+ \
            '_t'+str(thres)+'_r'+grid_res_agg_str+'_d'+'_'.join([str(i) for i in latlon_dims])+'.png hpc@vm-lnx-rzdm06:/home/people/hpc/ftp/erickson/test2')

        #Plot showing the 10/50/90th percentile of intensity/std and 
        fig = plt.figure(figsize=(8,8))
        ax = fig.add_axes([0.1,0.1,0.8,0.8])
        plt.errorbar(subset_hours-0.15,grid_disp_int10mean[1,1],yerr=[grid_disp_int10mean[1,1]-grid_disp_int10std[1,1,:,0],grid_disp_int10std[1,1,:,1]-grid_disp_int10mean[1,1]],color='b',fmt='-x',capthick=2)
        plt.errorbar(subset_hours+0.00,grid_disp_int50mean[1,1],yerr=[grid_disp_int50mean[1,1]-grid_disp_int50std[1,1,:,0],grid_disp_int50std[1,1,:,1]-grid_disp_int50mean[1,1]],color='g',fmt='-x',capthick=2)
        plt.errorbar(subset_hours+0.15,grid_disp_int90mean[1,1],yerr=[grid_disp_int90mean[1,1]-grid_disp_int90std[1,1,:,0],grid_disp_int90std[1,1,:,1]-grid_disp_int90mean[1,1]],color='r',fmt='-x',capthick=2)
        plt.plot(subset_hours, np.zeros(len(subset_hours)),linewidth=3,color='black')
        plt.xlabel(lab_str[0],fontsize=14)
        plt.ylabel('Mean Object Intensity Difference (Inches)',fontsize=14)
        plt.ylim((-thres*3.5,thres*3.5))
        plt.title('Paired Intensity Difference at Disp. - Area Precip. >= '+str(thres)+'" Per '+'{0:.2f}'.format(pre_acc)+' Hour\n '+ \
            'From '+beg_date_str_lo+' to '+end_date_str_lo,fontsize=14) 
        #Set up the legend
        line_label=[]
        line_str=[];
        leg_nam = ['10th Object Intensity Difference','50th Object Intensity Difference','90th Object Intensity Difference']
        colorlist  = ['blue','green','red']
        markerlist = ['x','x','x']
        linelist   = ['-','-','-']
        for x in range(0,len(leg_nam)):
            line_label = np.hstack((line_label, mpl.lines.Line2D(range(1), range(1), color=colorlist[x], linestyle=linelist[x], marker=markerlist[x], markersize=7)))
            line_str   = np.hstack((line_str, leg_nam[x]))
        first_legend=plt.legend(line_label, line_str, fontsize=10, numpoints=1, loc=0, framealpha=1)
        plt.savefig(FIG_PATH+'/'+GRIB_PATH_DES+'_pair_disp_inten_byhour_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[0]+ \
            '_t'+str(thres)+'_r'+grid_res_agg_str+'_d'+'_'.join([str(i) for i in latlon_dims])+'.png', bbox_inches='tight',dpi=200)
        plt.close()
        os.system('scp '+FIG_PATH+'/'+GRIB_PATH_DES+'_pair_disp_inten_byhour_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[0]+ \
            '_t'+str(thres)+'_r'+grid_res_agg_str+'_d'+'_'.join([str(i) for i in latlon_dims])+'.png hpc@vm-lnx-rzdm06:/home/people/hpc/ftp/erickson/test2')

        #Plot showing mean object area/std and object count
        fig = plt.figure(figsize=(8,8))
        ax1 = fig.add_axes([0.1,0.1,0.8,0.8])
        ax1.plot(subset_hours, grid_disp_count[1,1],'-x',linewidth=1, label='walker position', color='blue')
        ax1.set_xlabel(lab_str[0],fontsize=14)
        ax1.set_ylabel('Total Object Count', color='b',fontsize=14)
        ax1.set_ylim(0,np.nanmax(grid_disp_count[1,1])*1.25)
        #Second part of plotyy
        ax2 = ax1.twinx()
        ax2.errorbar(subset_hours+0.1,grid_disp_areamean[1,1],yerr=[grid_disp_areamean[1,1]-grid_disp_areastd[1,1,:,0],grid_disp_areastd[1,1,:,1]-grid_disp_areamean[1,1]],color='r',fmt='-x',capthick=2)
        ax2.plot(subset_hours, np.zeros(len(subset_hours)),linewidth=3,color='black')
        ax2.set_ylabel('Mean Object Area Difference (Grid Squares)', color='r',fontsize=14)
        ax2.set_ylim(-thres*5000,thres*5000)
        plt.title('Paired Object Count/Area Difference at Disp. - Area Precip. >= '+str(thres)+'" Per '+'{0:.2f}'.format(pre_acc)+' Hour\n '+ \
            'From '+beg_date_str_lo+' to '+end_date_str_lo,fontsize=14) 
        #Set up the legend
        line_label=[]
        line_str=[];
        colorlist  = ['blue','red']
        leg_nam    = ['Total Object Count','Object Area Difference']
        markerlist = ['x','x']   
        linelist   = ['-','-']
        for x in range(0,len(leg_nam)):
            line_label = np.hstack((line_label, mpl.lines.Line2D(range(1), range(1), color=colorlist[x], linestyle=linelist[x], marker=markerlist[x], markersize=7)))
            line_str   = np.hstack((line_str, leg_nam[x]))
        first_legend=plt.legend(line_label, line_str, fontsize=12, numpoints=1, loc=0, framealpha=1)
        plt.savefig(FIG_PATH+'/'+GRIB_PATH_DES+'_pair_disp_countarea_byhour_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[0]+ \
            '_t'+str(thres)+'_r'+grid_res_agg_str+'_d'+'_'.join([str(i) for i in latlon_dims])+'.png', bbox_inches='tight',dpi=200)
        plt.close()
        os.system('scp '+FIG_PATH+'/'+GRIB_PATH_DES+'_pair_disp_countarea_byhour_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[0]+ \
            '_t'+str(thres)+'_r'+grid_res_agg_str+'_d'+'_'.join([str(i) for i in latlon_dims])+'.png hpc@vm-lnx-rzdm06:/home/people/hpc/ftp/erickson/test2')

        #Plot showing time mean/std
        fig = plt.figure(figsize=(8,8))
        ax = fig.add_axes([0.1,0.1,0.8,0.8])
        plt.errorbar(subset_hours,grid_disp_timemean[1,1],yerr=[grid_disp_timemean[1,1]-grid_disp_timestd[1,1,:,0],grid_disp_timestd[1,1,:,1]-grid_disp_timemean[1,1]],color='b',fmt='-x',capthick=2)
        plt.plot(subset_hours, np.zeros(len(subset_hours)),linewidth=3,color='black')
        plt.xlabel(lab_str[0],fontsize=14)
        plt.ylabel('Mean Object Time Difference (Increments)',fontsize=14)
        plt.ylim((-15,15))
        plt.title('Paired Object Time Difference at Disp. - Area Precip. >= '+str(thres)+'" Per '+'{0:.2f}'.format(pre_acc)+' Hour\n '+ \
            'From '+beg_date_str_lo+' to '+end_date_str_lo,fontsize=14) 
        #Set up the legend
        line_label=[]
        line_str=[];
        leg_nam = ['Object Time Difference']
        colorlist  = ['blue']
        markerlist = ['x']  
        linelist   = ['-']
        for x in range(0,len(leg_nam)):
            line_label = np.hstack((line_label, mpl.lines.Line2D(range(1), range(1), color=colorlist[x], linestyle=linelist[x], marker=markerlist[x], markersize=7)))
            line_str   = np.hstack((line_str, leg_nam[x]))
        first_legend=plt.legend(line_label, line_str, fontsize=10, numpoints=1, loc=0, framealpha=1)
        plt.savefig(FIG_PATH+'/'+GRIB_PATH_DES+'_pair_disp_time_byhour_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[0]+ \
            '_t'+str(thres)+'_r'+grid_res_agg_str+'_d'+'_'.join([str(i) for i in latlon_dims])+'.png', bbox_inches='tight',dpi=200)
        plt.close()
        os.system('scp '+FIG_PATH+'/'+GRIB_PATH_DES+'_pair_disp_time_byhour_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[0]+ \
            '_t'+str(thres)+'_r'+grid_res_agg_str+'_d'+'_'.join([str(i) for i in latlon_dims])+'.png hpc@vm-lnx-rzdm06:/home/people/hpc/ftp/erickson/test2')

    elif grid_res_nat != []:       
        
        for hrs in range(0,len(subset_hours)): #loop through different hour subsets                  

            ###############Plot Total Count###############

            #Create first colorlist
            my_cmap1 = copy.copy(mpl.cm.get_cmap('jet'))
            my_cmap1.set_under('white')

            [fig,ax] = cartopy_maps.plot_map(lat,lon)
            cs = plt.pcolormesh(lon_nat-(grid_res_nat/2.0),lat_nat+(grid_res_nat/2.0),grid_disp_count[:,:,hrs],cmap=my_cmap1,vmin=0.01,vmax=np.nanmax(grid_disp_count)*1.05,transform=ccrs.PlateCarree())
            cs.cmap.set_under('white')
            cb = plt.colorbar(cs,ax=ax,extend='min')
            ax.set_title('Object Dissipation Total Count - '+'{0:.2f}'.format(pre_acc)+' Hour Precip. > '+str(thres)+'"\n'+ \
                'From '+beg_date_str_lo+' to '+end_date_str_lo,fontsize=13)
            plt.savefig(FIG_PATH+'/'+GRIB_PATH_DES+'_prop_disp_count_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[hrs]+ \
                '_t'+str(thres)+'_r'+grid_res_agg_str+'.png', bbox_inches='tight',dpi=200)      
            plt.close()
            os.system('scp '+FIG_PATH+'/'+GRIB_PATH_DES+'_prop_disp_count_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[hrs]+ \
                '_t'+str(thres)+'_r'+grid_res_agg_str+'.png hpc@vm-lnx-rzdm06:/home/people/hpc/ftp/erickson/test2')
                
            ###############Plot Displacement and intensity simultaneously###############
            #Create first colorlist
            my_cmap1 = copy.copy(mpl.cm.get_cmap('RdYlGn'))
            
            #Determine max limit of colorbar
            if thres == 0.1:
                vmax = 0.05
            elif thres == 0.25:
                vmax = 0.1
            elif thres == 0.5:
                vmax = 0.2

            [fig,ax] = cartopy_maps.plot_map(lat,lon)                
            im = plt.quiver(lon_nat-(grid_res_nat/2.0),lat_nat+(grid_res_nat/2.0),grid_disp_xmean[:,:,hrs]*((grid_disp_xmean[:,:,hrs]!=0*1) & (grid_disp_ymean[:,:,hrs]!=0*1)), \
                grid_disp_ymean[:,:,hrs]*((grid_disp_xmean[:,:,hrs]!=0*1) & (grid_disp_ymean[:,:,hrs]!=0*1)),grid_disp_int10mean_ns[:,:,hrs]*((grid_disp_xmean[:,:,hrs]!=0*1) & \
                (grid_disp_ymean[:,:,hrs]!=0*1)), cmap=my_cmap1,clim=(-vmax, vmax),units='inches',angles='xy',scale_units='inches', scale = 300, width = 0.03,linewidths=0.2, \
                edgecolors='k',transform=ccrs.PlateCarree())
            cs = plt.quiverkey(im, 0.68, 0.28, 100, '100 km', labelpos='E',coordinates='figure',transform=ccrs.PlateCarree())                
            cb = plt.colorbar(im,ax=ax,extend='min')
            ax.set_title('Object Dissipation Displacement and 10th Pctile of Intensity - '+'{0:.2f}'.format(pre_acc)+' Hour Precip. > '+str(thres)+'"\n'+ \
                'From '+beg_date_str_lo+' to '+end_date_str_lo,fontsize=13)
            plt.savefig(FIG_PATH+'/'+GRIB_PATH_DES+'_prop_disp_inten10Adisp_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[hrs]+ \
                '_t'+str(thres)+'_r'+grid_res_agg_str+'.png', bbox_inches='tight',dpi=200)     
            plt.close()
            os.system('scp '+FIG_PATH+'/'+GRIB_PATH_DES+'_prop_disp_inten10Adisp_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[hrs]+ \
                '_t'+str(thres)+'_r'+grid_res_agg_str+'.png hpc@vm-lnx-rzdm06:/home/people/hpc/ftp/erickson/test2')
            
            #Determine max limit of colorbar
            if thres == 0.1:
                vmax = 0.1
            elif thres == 0.25:
                vmax = 0.2
            elif thres == 0.5:
                vmax = 0.4

            [fig,ax] = cartopy_maps.plot_map(lat,lon)                
            im = plt.quiver(lon_nat-(grid_res_nat/2.0),lat_nat+(grid_res_nat/2.0),grid_disp_xmean[:,:,hrs]*((grid_disp_xmean[:,:,hrs]!=0*1) & (grid_disp_ymean[:,:,hrs]!=0*1)), \
                grid_disp_ymean[:,:,hrs]*((grid_disp_xmean[:,:,hrs]!=0*1) & (grid_disp_ymean[:,:,hrs]!=0*1)),grid_disp_int50mean_ns[:,:,hrs]*((grid_disp_xmean[:,:,hrs]!=0*1) & \
                (grid_disp_ymean[:,:,hrs]!=0*1)),cmap=my_cmap1,clim=(-vmax, vmax),units='inches',angles='xy',scale_units='inches', scale = 300, width = 0.03,linewidths=0.2, \
                edgecolors='k',transform=ccrs.PlateCarree())
            cs = plt.quiverkey(im, 0.68, 0.28, 100, '100 km', labelpos='E',coordinates='figure',transform=ccrs.PlateCarree())                
            cb = plt.colorbar(im,ax=ax,extend='min')
            ax.set_title('Object Dissipation Displacement and 50th Pctile of Intensity - '+'{0:.2f}'.format(pre_acc)+' Hour Precip. > '+str(thres)+'"\n'+ \
                'From '+beg_date_str_lo+' to '+end_date_str_lo,fontsize=13)
            plt.savefig(FIG_PATH+'/'+GRIB_PATH_DES+'_prop_disp_inten50Adisp_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[hrs]+ \
                '_t'+str(thres)+'_r'+grid_res_agg_str+'.png', bbox_inches='tight',dpi=200)     
            plt.close()
            os.system('scp '+FIG_PATH+'/'+GRIB_PATH_DES+'_prop_disp_inten50Adisp_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[hrs]+ \
                '_t'+str(thres)+'_r'+grid_res_agg_str+'.png hpc@vm-lnx-rzdm06:/home/people/hpc/ftp/erickson/test2')
            
            #Determine max limit of colorbar
            if thres == 0.1:
                vmax = 0.2
            elif thres == 0.25:
                vmax = 0.4
            elif thres == 0.5:
                vmax = 0.6

            [fig,ax] = cartopy_maps.plot_map(lat,lon)                
            im = plt.quiver(lon_nat-(grid_res_nat/2.0),lat_nat+(grid_res_nat/2.0),grid_disp_xmean[:,:,hrs]*((grid_disp_xmean[:,:,hrs]!=0*1) & (grid_disp_ymean[:,:,hrs]!=0*1)), \
                grid_disp_ymean[:,:,hrs]*((grid_disp_xmean[:,:,hrs]!=0*1) & (grid_disp_ymean[:,:,hrs]!=0*1)),grid_disp_int90mean_ns[:,:,hrs]*((grid_disp_xmean[:,:,hrs]!=0*1) \
                & (grid_disp_ymean[:,:,hrs]!=0*1)), cmap=my_cmap1,clim=(-vmax, vmax),units='inches',angles='xy',scale_units='inches', scale = 300, width = 0.03,linewidths=0.2, \
                edgecolors='k',transform=ccrs.PlateCarree())
            cs = plt.quiverkey(im, 0.68, 0.28, 100, '100 km', labelpos='E',coordinates='figure',transform=ccrs.PlateCarree())                
            cb = plt.colorbar(im,ax=ax,extend='min')
            ax.set_title('Object Dissipation Displacement and 90th Pctile of Intensity - '+'{0:.2f}'.format(pre_acc)+' Hour Precip. > '+str(thres)+'"\n'+ \
                'From '+beg_date_str_lo+' to '+end_date_str_lo,fontsize=13)
            plt.savefig(FIG_PATH+'/'+GRIB_PATH_DES+'_prop_disp_inten90Adisp_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[hrs]+ \
                '_t'+str(thres)+'_r'+grid_res_agg_str+'.png', bbox_inches='tight',dpi=200)     
            plt.close()
            os.system('scp '+FIG_PATH+'/'+GRIB_PATH_DES+'_prop_disp_inten90Adisp_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[hrs]+ \
                '_t'+str(thres)+'_r'+grid_res_agg_str+'.png hpc@vm-lnx-rzdm06:/home/people/hpc/ftp/erickson/test2')
                                
            ###############Plot Model Intensity Mean Error###############

            #Create first colorlist
            my_cmap1 = copy.copy(mpl.cm.get_cmap('RdYlGn'))
            
            #Determine max limit of colorbar
            if thres == 0.1:
                vmax = 0.05
            elif thres == 0.25:
                vmax = 0.1
            elif thres == 0.5:
                vmax = 0.2

            [fig,ax] = cartopy_maps.plot_map(lat,lon)                
            #im = plt.imshow(grid_obs_count, interpolation='nearest', values=values, cmap=my_cmap1, norm=norm)
            cs = plt.pcolormesh(lon_nat-(grid_res_nat/2.0),lat_nat+(grid_res_nat/2.0),grid_disp_int10mean[:,:,hrs],cmap=my_cmap1,vmin=-vmax,vmax=vmax,transform=ccrs.PlateCarree())
            cs.cmap.set_under('white')
            cb = plt.colorbar(cs,ax=ax)
            ax.set_title('Object Dissipation 10th Pctile of Intensity Mean Error - '+'{0:.2f}'.format(pre_acc)+' Hour Precip. > '+str(thres)+'"\n'+ \
                'From '+beg_date_str_lo+' to '+end_date_str_lo,fontsize=13)
            plt.savefig(FIG_PATH+'/'+GRIB_PATH_DES+'_prop_disp_inten10_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[hrs]+ \
                '_t'+str(thres)+'_r'+grid_res_agg_str+'.png', bbox_inches='tight',dpi=200) 
            plt.close()
            os.system('scp '+FIG_PATH+'/'+GRIB_PATH_DES+'_prop_disp_inten10_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[hrs]+ \
                '_t'+str(thres)+'_r'+grid_res_agg_str+'.png hpc@vm-lnx-rzdm06:/home/people/hpc/ftp/erickson/test2')

            #Determine max limit of colorbar
            if thres == 0.1:
                vmax = 0.1
            elif thres == 0.25:
                vmax = 0.2
            elif thres == 0.5:
                vmax = 0.4

            [fig,ax] = cartopy_maps.plot_map(lat,lon)                
            cs = plt.pcolormesh(lon_nat-(grid_res_nat/2.0),lat_nat+(grid_res_nat/2.0),grid_disp_int50mean[:,:,hrs],cmap=my_cmap1,vmin=-vmax,vmax=vmax,transform=ccrs.PlateCarree())
            cs.cmap.set_under('white')
            cb = plt.colorbar(cs,ax=ax)
            ax.set_title('Object Dissipation 50th Pctile of Intensity Mean Error - '+'{0:.2f}'.format(pre_acc)+' Hour Precip. > '+str(thres)+'"\n'+ \
                'From '+beg_date_str_lo+' to '+end_date_str_lo,fontsize=13)
            plt.savefig(FIG_PATH+'/'+GRIB_PATH_DES+'_prop_disp_inten50_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[hrs]+ \
                '_t'+str(thres)+'_r'+grid_res_agg_str+'.png', bbox_inches='tight',dpi=200)
            plt.close()
            os.system('scp '+FIG_PATH+'/'+GRIB_PATH_DES+'_prop_disp_inten50_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[hrs]+ \
                '_t'+str(thres)+'_r'+grid_res_agg_str+'.png hpc@vm-lnx-rzdm06:/home/people/hpc/ftp/erickson/test2')

            #Determine max limit of colorbar
            if thres == 0.1:
                vmax = 0.2
            elif thres == 0.25:
                vmax = 0.4
            elif thres == 0.5:
                vmax = 0.6

            [fig,ax] = cartopy_maps.plot_map(lat,lon)                
            cs = plt.pcolormesh(lon_nat-(grid_res_nat/2.0),lat_nat+(grid_res_nat/2.0),grid_disp_int90mean[:,:,hrs],cmap=my_cmap1,vmin=-vmax,vmax=vmax,transform=ccrs.PlateCarree())
            cs.cmap.set_under('white')
            cb = plt.colorbar(cs,ax=ax)
            ax.set_title('Object Dissipation 90th Pctile of Intensity Mean Error - '+'{0:.2f}'.format(pre_acc)+' Hour Precip. > '+str(thres)+'"\n'+ \
                'From '+beg_date_str_lo+' to '+end_date_str_lo,fontsize=13)
            plt.savefig(FIG_PATH+'/'+GRIB_PATH_DES+'_prop_disp_inten90_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[hrs]+ \
                '_t'+str(thres)+'_r'+grid_res_agg_str+'.png', bbox_inches='tight',dpi=200)
            plt.close()
            os.system('scp '+FIG_PATH+'/'+GRIB_PATH_DES+'_prop_disp_inten90_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[hrs]+ \
                '_t'+str(thres)+'_r'+grid_res_agg_str+'.png hpc@vm-lnx-rzdm06:/home/people/hpc/ftp/erickson/test2')                          

            ###############Plot Mean Error in Time###############

            #Create first colorlist
            my_cmap1 = copy.copy(mpl.cm.get_cmap('RdYlGn'))
            
            #Determine max limit of colorbar
            vmax = 3

            [fig,ax] = cartopy_maps.plot_map(lat,lon)                
            cs = plt.pcolormesh(lon_nat-(grid_res_nat/2.0),lat_nat+(grid_res_nat/2.0),grid_disp_timemean[:,:,hrs],cmap=my_cmap1,vmin=-vmax,vmax=vmax,transform=ccrs.PlateCarree())
            cs.cmap.set_under('white')
            cb = plt.colorbar(cs,ax=ax)
            ax.set_title('Object Dissipation Time Mean Error - '+'{0:.2f}'.format(pre_acc)+' Hour Precip. > '+str(thres)+'"\n'+ \
                'From '+beg_date_str_lo+' to '+end_date_str_lo,fontsize=13)
            plt.savefig(FIG_PATH+'/'+GRIB_PATH_DES+'_prop_disp_time_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[hrs]+ \
                '_t'+str(thres)+'_r'+grid_res_agg_str+'.png', bbox_inches='tight',dpi=200)
            plt.close()
            os.system('scp '+FIG_PATH+'/'+GRIB_PATH_DES+'_prop_disp_time_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[hrs]+ \
                '_t'+str(thres)+'_r'+grid_res_agg_str+'.png hpc@vm-lnx-rzdm06:/home/people/hpc/ftp/erickson/test2')

            ###############Plot Model Area Mean Error###############

            #Create first colorlist
            my_cmap1 = copy.copy(mpl.cm.get_cmap('coolwarm')) 
            
            #Determine max limit of colorbar
            vmax = 600

            [fig,ax] = cartopy_maps.plot_map(lat,lon)                
            cs = plt.pcolormesh(lon_nat-(grid_res_nat/2.0),lat_nat+(grid_res_nat/2.0),grid_disp_areamean[:,:,hrs],cmap=my_cmap1,vmin=-vmax,vmax=vmax,transform=ccrs.PlateCarree())
            cs.cmap.set_under('white')
            cb = plt.colorbar(cs,ax=ax)
            ax.set_title('Object Dissipation Area Mean Error- '+'{0:.2f}'.format(pre_acc)+' Hour Precip. > '+str(thres)+'"\n'+ \
                'From '+beg_date_str_lo+' to '+end_date_str_lo,fontsize=13)
            plt.savefig(FIG_PATH+'/'+GRIB_PATH_DES+'_prop_disp_area_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[hrs]+ \
                '_t'+str(thres)+'_r'+grid_res_agg_str+'.png', bbox_inches='tight',dpi=200)  
            plt.close()
            os.system('scp '+FIG_PATH+'/'+GRIB_PATH_DES+'_prop_disp_area_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[hrs]+ \
                '_t'+str(thres)+'_r'+grid_res_agg_str+'.png hpc@vm-lnx-rzdm06:/home/people/hpc/ftp/erickson/test2')
            
            ###############Plot Model Angle Mean Error###############

            #Create first colorlist
            my_cmap1 = copy.copy(mpl.cm.get_cmap('coolwarm')) 
            
            #Determine max limit of colorbar
            vmax = 180
            [fig,ax] = cartopy_maps.plot_map(lat,lon)                
            cs = plt.pcolormesh(lon_nat-(grid_res_nat/2.0),lat_nat+(grid_res_nat/2.0),grid_disp_angmean[:,:,hrs],cmap=my_cmap1,vmin=-vmax,vmax=vmax,transform=ccrs.PlateCarree())
            cs.cmap.set_under('white')
            cb = plt.colorbar(cs,ax=ax)
            ax.set_title('Object Dissipation Angle Mean Error- '+'{0:.2f}'.format(pre_acc)+' Hour Precip. > '+str(thres)+'"\n'+ \
                'From '+beg_date_str_lo+' to '+end_date_str_lo,fontsize=13)
            plt.savefig(FIG_PATH+'/'+GRIB_PATH_DES+'_prop_disp_angle_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[hrs]+ \
                '_t'+str(thres)+'_r'+grid_res_agg_str+'.png', bbox_inches='tight',dpi=200)  
            plt.close()
            os.system('scp '+FIG_PATH+'/'+GRIB_PATH_DES+'_prop_disp_angle_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[hrs]+ \
                '_t'+str(thres)+'_r'+grid_res_agg_str+'.png hpc@vm-lnx-rzdm06:/home/people/hpc/ftp/erickson/test2')

###Plot the paired statistics
elif subset_data == 'SIMP':

    if grid_res_nat == []: #If everything is aggregated along the time dimension only

        #Plot intensity by hour
        fig = plt.figure(figsize=(8,8))
        ax1 = fig.add_axes([0.1,0.1,0.8,0.8])
        ax1.errorbar(subset_hours-0.1,grid_obs_int10mean[1,1],yerr=[grid_obs_int10mean[1,1]-grid_obs_int10std[1,1,:,0],grid_obs_int10std[1,1,:,1]-grid_obs_int10mean[1,1]],color='g',fmt='-s',capthick=2,linewidth=3)
        ax1.errorbar(subset_hours+0.1,grid_mod_int10mean[1,1],yerr=[grid_mod_int10mean[1,1]-grid_mod_int10std[1,1,:,0],grid_mod_int10std[1,1,:,1]-grid_mod_int10mean[1,1]],color='b',fmt='-s',capthick=2,linewidth=3)
        ax1.errorbar(subset_hours-0.1,grid_obs_int50mean[1,1],yerr=[grid_obs_int50mean[1,1]-grid_obs_int50std[1,1,:,0],grid_obs_int50std[1,1,:,1]-grid_obs_int50mean[1,1]],color='g',fmt='--x',capthick=2,linewidth=3)
        ax1.errorbar(subset_hours+0.1,grid_mod_int50mean[1,1],yerr=[grid_mod_int50mean[1,1]-grid_mod_int50std[1,1,:,0],grid_mod_int50std[1,1,:,1]-grid_mod_int50mean[1,1]],color='b',fmt='--x',capthick=2,linewidth=3)
        ax1.errorbar(subset_hours-0.1,grid_obs_int90mean[1,1],yerr=[grid_obs_int90mean[1,1]-grid_obs_int90std[1,1,:,0],grid_obs_int90std[1,1,:,1]-grid_obs_int90mean[1,1]],color='g',fmt='-.o',capthick=2,linewidth=3)
        ax1.errorbar(subset_hours+0.1,grid_mod_int90mean[1,1],yerr=[grid_mod_int90mean[1,1]-grid_mod_int90std[1,1,:,0],grid_mod_int90std[1,1,:,1]-grid_mod_int90mean[1,1]],color='b',fmt='-.o',capthick=2,linewidth=3)
        ax1.set_xlabel(lab_str[0],fontsize=14)
        ax1.set_ylabel('Mean Object Intensity',fontsize=14)
        plt.title('Unpaired Object Intensity Precip. >= '+str(thres)+'" Per '+'{0:.2f}'.format(pre_acc)+' Hour\n '+ \
            'From '+beg_date_str_lo+' to '+end_date_str_lo,fontsize=14)     
        plt.ylim([0,thres*10.0])
        #Set up the legend
        line_label=[]
        line_str=[];
        leg_nam = ['10th Percentile Obs.','10th Percentile Model','50th Percentile Obs.','50th Percentile Model', \
            '90th Percentile Obs.','90th Percentile Model']
        colorlist = ['green','blue','green','blue','green','blue'] 
        markerlist = ['s','s','x','x','o','o']   
        for x in range(0,len(leg_nam)):
            line_label = np.hstack((line_label, mpl.lines.Line2D(range(1), range(1), color=colorlist[x], linestyle='None', marker=markerlist[x], markersize=7)))
            line_str   = np.hstack((line_str, leg_nam[x]))
        first_legend=plt.legend(line_label, line_str, fontsize=12, numpoints=1, loc=0, framealpha=1)
        ax1 = plt.gca().add_artist(first_legend)
        plt.savefig(FIG_PATH+'/'+GRIB_PATH_DES+'_simp_prop_inten_byhour_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[0]+ \
            '_t'+str(thres)+'_r'+grid_res_agg_str+'_d'+'_'.join([str(i) for i in latlon_dims])+'.png', bbox_inches='tight',dpi=200)
        plt.close()
        os.system('scp '+FIG_PATH+'/'+GRIB_PATH_DES+'_simp_prop_inten_byhour_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[0]+ \
            '_t'+str(thres)+'_r'+grid_res_agg_str+'_d'+'_'.join([str(i) for i in latlon_dims])+'.png hpc@vm-lnx-rzdm06:/home/people/hpc/ftp/erickson/test2')

        #Plot area by hour
        fig = plt.figure(figsize=(8,8))
        ax1 = fig.add_axes([0.1,0.1,0.8,0.8]) 
        ax1.errorbar(subset_hours-0.1,grid_obs_areamean[1,1],yerr=[grid_obs_areamean[1,1]-grid_obs_areastd[1,1,:,0],grid_obs_areastd[1,1,:,1]-grid_obs_areamean[1,1]],color='g',fmt='-s',capthick=2,linewidth=3)
        ax1.errorbar(subset_hours+0.1,grid_mod_areamean[1,1],yerr=[grid_mod_areamean[1,1]-grid_mod_areastd[1,1,:,0],grid_mod_areastd[1,1,:,1]-grid_mod_areamean[1,1]],color='b',fmt='-s',capthick=2,linewidth=3)

        ax1.set_xlabel(lab_str[0],fontsize=14)
        ax1.set_ylabel('Median Object Area (Grid Points)',fontsize=14)
        plt.ylim(0, 1000)
        plt.title('Unpaired Object Area Precip. >= '+str(thres)+'" Per '+'{0:.2f}'.format(pre_acc)+' Hour\n '+ \
            'From '+beg_date_str_lo+' to '+end_date_str_lo,fontsize=14) 
        #Set up the legend
        line_label=[]
        line_str=[];
        leg_nam = ['Observation','Model']
        colorlist = ['green','blue'] 
        markerlist = ['.','.']   
        for x in range(0,len(leg_nam)):
            line_label = np.hstack((line_label, mpl.lines.Line2D(range(1), range(1), color=colorlist[x], linestyle='None', marker=markerlist[x], markersize=7)))
            line_str   = np.hstack((line_str, leg_nam[x]))
        first_legend=plt.legend(line_label, line_str, fontsize=16, numpoints=1, loc=0, framealpha=1)
        ax1 = plt.gca().add_artist(first_legend)
        plt.savefig(FIG_PATH+'/'+GRIB_PATH_DES+'_simp_prop_area_byhour_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[0]+ \
            '_t'+str(thres)+'_r'+grid_res_agg_str+'_d'+'_'.join([str(i) for i in latlon_dims])+'.png', bbox_inches='tight',dpi=200)
        plt.close()   
        os.system('scp '+FIG_PATH+'/'+GRIB_PATH_DES+'_simp_prop_area_byhour_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[0]+ \
            '_t'+str(thres)+'_r'+grid_res_agg_str+'_d'+'_'.join([str(i) for i in latlon_dims])+'.png hpc@vm-lnx-rzdm06:/home/people/hpc/ftp/erickson/test2')

        #Plot angle by hour
        fig = plt.figure(figsize=(8,8))
        ax1 = fig.add_axes([0.1,0.1,0.8,0.8])
        ax1.errorbar(subset_hours-0.1,grid_obs_angmean[1,1],yerr=[grid_obs_angmean[1,1]-grid_obs_angstd[1,1,:,0],grid_obs_angstd[1,1,:,1]-grid_obs_angmean[1,1]],color='g',fmt='-x',capthick=2,linewidth=3)
        ax1.errorbar(subset_hours+0.1,grid_mod_angmean[1,1],yerr=[grid_mod_angmean[1,1]-grid_mod_angstd[1,1,:,0],grid_mod_angstd[1,1,:,1]-grid_mod_angmean[1,1]],color='b',fmt='-x',capthick=2,linewidth=3)
        ax1.set_xlabel(lab_str[0],fontsize=14)
        ax1.set_ylabel('Median Object Angle',fontsize=14)
        plt.title('Unpaired Object Angle Precip. >= '+str(thres)+'" Per '+'{0:.2f}'.format(pre_acc)+' Hour\n '+ \
            'From '+beg_date_str_lo+' to '+end_date_str_lo,fontsize=14)   
        #Set up the legend
        line_label=[]
        line_str=[];
        leg_nam = ['Observation','Model']
        colorlist = ['green','blue'] 
        markerlist = ['.','.']   
        for x in range(0,len(leg_nam)):
            line_label = np.hstack((line_label, mpl.lines.Line2D(range(1), range(1), color=colorlist[x], linestyle='None', marker=markerlist[x], markersize=7)))
            line_str   = np.hstack((line_str, leg_nam[x]))
        first_legend=plt.legend(line_label, line_str, fontsize=16, numpoints=1, loc=0, framealpha=1)
        ax1 = plt.gca().add_artist(first_legend)
        plt.savefig(FIG_PATH+'/'+GRIB_PATH_DES+'_simp_prop_angle_byhour_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[0]+ \
            '_t'+str(thres)+'_r'+grid_res_agg_str+'_d'+'_'.join([str(i) for i in latlon_dims])+'.png', bbox_inches='tight',dpi=200)
        plt.close()
        os.system('scp '+FIG_PATH+'/'+GRIB_PATH_DES+'_simp_prop_angle_byhour_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[0]+ \
            '_t'+str(thres)+'_r'+grid_res_agg_str+'_d'+'_'.join([str(i) for i in latlon_dims])+'.png hpc@vm-lnx-rzdm06:/home/people/hpc/ftp/erickson/test2')
        
        #Plot aggregated count by hour
        fig = plt.figure(figsize=(8,8))
        ax1 = fig.add_axes([0.1,0.1,0.8,0.8])
        plt.plot(subset_hours,grid_obs_count[1,1],color='green',marker = 's', linewidth=3)
        plt.plot(subset_hours,grid_mod_count[1,1],color='blue' ,marker = 's', linewidth=3)
        ax1.set_xlabel(lab_str[0],fontsize=14)
        ax1.set_ylabel('Summed Object Count',fontsize=14)
        plt.title('Unpaired Object Count Precip. >= '+str(thres)+'" Per '+'{0:.2f}'.format(pre_acc)+' Hour\n '+ \
            'From '+beg_date_str_lo+' to '+end_date_str_lo,fontsize=14)   
        #Set up the legend
        line_label=[]
        line_str=[];
        leg_nam = ['Observation','Model']
        colorlist = ['green','blue'] 
        markerlist = ['.','.']   
        for x in range(0,len(leg_nam)):
            line_label = np.hstack((line_label, mpl.lines.Line2D(range(1), range(1), color=colorlist[x], linestyle='None', marker=markerlist[x], markersize=7)))
            line_str   = np.hstack((line_str, leg_nam[x]))
        first_legend=plt.legend(line_label, line_str, fontsize=16, numpoints=1, loc=0, framealpha=1)
        ax1 = plt.gca().add_artist(first_legend)
        plt.savefig(FIG_PATH+'/'+GRIB_PATH_DES+'_simp_prop_count_byhour_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[0]+ \
            '_t'+str(thres)+'_r'+grid_res_agg_str+'_d'+'_'.join([str(i) for i in latlon_dims])+'.png', bbox_inches='tight',dpi=200)
        plt.close()
        os.system('scp '+FIG_PATH+'/'+GRIB_PATH_DES+'_simp_prop_count_byhour_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[0]+ \
            '_t'+str(thres)+'_r'+grid_res_agg_str+'_d'+'_'.join([str(i) for i in latlon_dims])+'.png hpc@vm-lnx-rzdm06:/home/people/hpc/ftp/erickson/test2')
        
    elif grid_res_nat != []: 

        for hrs in range(0,len(subset_hours)): #loop through different hour subsets

            ################Plot Model Intensity###############

            #Create first colorlist
            my_cmap1 = copy.copy(mpl.cm.get_cmap('jet'))
            my_cmap1.set_under('white')
                
            #Determine max limit of colorbar
            try:
                vmax = np.round(np.percentile(grid_obs_int90mean[grid_obs_int90mean>0],99),2)
            except IndexError:
                vmax = 0

            [fig,ax] = cartopy_maps.plot_map(lat,lon)                
            cs = plt.pcolormesh(lon_nat-(grid_res_nat/2.0),lat_nat+(grid_res_nat/2.0),grid_mod_int90mean[:,:,hrs],cmap=my_cmap1,vmin=0.01,vmax=vmax,transform=ccrs.PlateCarree())
            cs.cmap.set_under('white')
            cb = plt.colorbar(cs,ax=ax,extend='min')
            ax.set_title('Unpaired Model Object Intensity - '+'Precip. >= '+str(thres)+'" Per '+'{0:.2f}'.format(pre_acc)+' Hour\n '+ \
                'From '+beg_date_str_lo+' to '+end_date_str_lo,fontsize=13)     
            plt.savefig(FIG_PATH+'/'+GRIB_PATH_DES+'_simp_prop_inten_mod_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[hrs]+ \
                '_t'+str(thres)+'_r'+grid_res_agg_str+'.png', bbox_inches='tight',dpi=200)
            plt.close()
            os.system('scp '+FIG_PATH+'/'+GRIB_PATH_DES+'_simp_prop_inten_mod_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[hrs]+ \
                '_t'+str(thres)+'_r'+grid_res_agg_str+'.png hpc@vm-lnx-rzdm06:/home/people/hpc/ftp/erickson/test2')

            ###############Plot Observed Intensity###############
            [fig,ax] = cartopy_maps.plot_map(lat,lon)
            cs = plt.pcolormesh(lon_nat-(grid_res_nat/2.0),lat_nat+(grid_res_nat/2.0),grid_obs_int90mean[:,:,hrs],cmap=my_cmap1,vmin=0.01,vmax=vmax,transform=ccrs.PlateCarree())
            cs.cmap.set_under('white')
            cb = plt.colorbar(cs,ax=ax,extend='min')
            ax.set_title('Unpaired Stave IV Object Intensity Precip. >= '+str(thres)+'" Per '+'{0:.2f}'.format(pre_acc)+' Hour\n '+ \
                'From '+beg_date_str_lo+' to '+end_date_str_lo,fontsize=13)
            plt.savefig(FIG_PATH+'/'+GRIB_PATH_DES+'_simp_prop_inten_obs_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[hrs]+ \
                '_t'+str(thres)+'_r'+grid_res_agg_str+'.png', bbox_inches='tight',dpi=200)
            plt.close()  
            os.system('scp '+FIG_PATH+'/'+GRIB_PATH_DES+'_simp_prop_inten_obs_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[hrs]+ \
                '_t'+str(thres)+'_r'+grid_res_agg_str+'.png hpc@vm-lnx-rzdm06:/home/people/hpc/ftp/erickson/test2')
        
            ###############Plot Difference in Intensity###############
            NaN_matrix = ((grid_mod_int90mean > 0) & (grid_obs_int90mean > 0))*1.0
            
            #Create first colorlist
            my_cmap1 = copy.copy(mpl.cm.get_cmap('RdYlGn'))
            
            #Determine max limit of colorbar
            if thres == 0.1:
                vmax = 0.2
            elif thres == 0.25:
                vmax = 0.4
            elif thres == 0.5:
                vmax = 0.6

            [fig,ax] = cartopy_maps.plot_map(lat,lon)                
            cs = plt.pcolormesh(lon_nat-(grid_res_nat/2.0),lat_nat+(grid_res_nat/2.0),grid_diff_int90mean[:,:,hrs]*NaN_matrix[:,:,hrs],cmap=my_cmap1,vmin=-vmax,vmax=vmax,transform=ccrs.PlateCarree())
            cs.cmap.set_under('white')
            cb = plt.colorbar(cs,ax=ax,extend='min')
            ax.set_title('Unpaired Object Intensity Difference Precip. >= '+str(thres)+'" Per '+'{0:.2f}'.format(pre_acc)+' Hour\n '+ \
                'From '+beg_date_str_lo+' to '+end_date_str_lo,fontsize=13) 
            plt.savefig(FIG_PATH+'/'+GRIB_PATH_DES+'_simp_prop_inten_diff_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[hrs]+ \
                '_t'+str(thres)+'_r'+grid_res_agg_str+'.png', bbox_inches='tight',dpi=200)
            plt.close()  
            os.system('scp '+FIG_PATH+'/'+GRIB_PATH_DES+'_simp_prop_inten_diff_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[hrs]+ \
                '_t'+str(thres)+'_r'+grid_res_agg_str+'.png hpc@vm-lnx-rzdm06:/home/people/hpc/ftp/erickson/test2')
            
            ###############Plot Model Area###############
            #Determine max limit of colorbar
            try:
                vmax = np.round(np.percentile(grid_obs_areamean[grid_obs_areamean>0],95),2)
            except IndexError:
                vmax = 0

            [fig,ax] = cartopy_maps.plot_map(lat,lon)               
            cs = plt.pcolormesh(lon_nat-(grid_res_nat/2.0),lat_nat+(grid_res_nat/2.0),grid_mod_areamean[:,:,hrs],cmap=my_cmap1,vmin=0.01,vmax=vmax,transform=ccrs.PlateCarree())
            cs.cmap.set_under('white')
            cb = plt.colorbar(cs,ax=ax)
            ax.set_title('Unpaired Model Object Area Precip. >= '+str(thres)+'" Per '+'{0:.2f}'.format(pre_acc)+' Hour\n '+ \
                'From '+beg_date_str_lo+' to '+end_date_str_lo,fontsize=13)
            plt.savefig(FIG_PATH+'/'+GRIB_PATH_DES+'_simp_prop_area_mod_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[hrs]+ \
                '_t'+str(thres)+'_r'+grid_res_agg_str+'.png', bbox_inches='tight',dpi=200)
            plt.close()  
            os.system('scp '+FIG_PATH+'/'+GRIB_PATH_DES+'_simp_prop_area_mod_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[hrs]+ \
                '_t'+str(thres)+'_r'+grid_res_agg_str+'.png hpc@vm-lnx-rzdm06:/home/people/hpc/ftp/erickson/test2')
            
            ###############Plot Observed Area###############
            [fig,ax] = cartopy_maps.plot_map(lat,lon)
            cs = plt.pcolormesh(lon_nat-(grid_res_nat/2.0),lat_nat+(grid_res_nat/2.0),grid_obs_areamean[:,:,hrs],cmap=my_cmap1,vmin=0.01,vmax=vmax,transform=ccrs.PlateCarree())
            cs.cmap.set_under('white')
            cb = plt.colorbar(cs,ax=ax)
            ax.set_title('Unpaired Stage IV Object Area Precip. >= '+str(thres)+'" Per '+'{0:.2f}'.format(pre_acc)+' Hour\n '+ \
                'From '+beg_date_str_lo+' to '+end_date_str_lo,fontsize=13)
            plt.savefig(FIG_PATH+'/'+GRIB_PATH_DES+'_simp_prop_area_obs_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[hrs]+ \
                '_t'+str(thres)+'_r'+grid_res_agg_str+'.png', bbox_inches='tight',dpi=200)
            plt.close()   
            os.system('scp '+FIG_PATH+'/'+GRIB_PATH_DES+'_simp_prop_area_obs_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[hrs]+ \
                '_t'+str(thres)+'_r'+grid_res_agg_str+'.png hpc@vm-lnx-rzdm06:/home/people/hpc/ftp/erickson/test2')
        
            ###############Plot Difference in Area###############
            NaN_matrix = ((grid_mod_areamean > 0) & (grid_obs_areamean > 0))*1.0
            
            #Create first colorlist
            my_cmap1 = copy.copy(mpl.cm.get_cmap('coolwarm'))
            
            #Determine max limit of colorbar
            vmax = 600
            [fig,ax] = cartopy_maps.plot_map(lat,lon)
            cs = plt.pcolormesh(lon_nat-(grid_res_nat/2.0),lat_nat+(grid_res_nat/2.0),grid_diff_areamean[:,:,hrs]*NaN_matrix[:,:,hrs],cmap=my_cmap1,vmin=-vmax,vmax=vmax,transform=ccrs.PlateCarree())
            cs.cmap.set_under('white')
            cb = plt.colorbar(cs,ax=ax)
            ax.set_title('Unpaired Object Area Difference Precip. >= '+str(thres)+'" Per '+'{0:.2f}'.format(pre_acc)+' Hour\n '+ \
                'From '+beg_date_str_lo+' to '+end_date_str_lo,fontsize=13) 
            plt.savefig(FIG_PATH+'/'+GRIB_PATH_DES+'_simp_prop_area_diff_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[hrs]+ \
                '_t'+str(thres)+'_r'+grid_res_agg_str+'.png', bbox_inches='tight',dpi=200)
            plt.close()  
            os.system('scp '+FIG_PATH+'/'+GRIB_PATH_DES+'_simp_prop_area_diff_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[hrs]+ \
                '_t'+str(thres)+'_r'+grid_res_agg_str+'.png hpc@vm-lnx-rzdm06:/home/people/hpc/ftp/erickson/test2')
            
            ###############Plot Modeled Angle###############
            #Determine max limit of colorbar
            vmax = 180
            [fig,ax] = cartopy_maps.plot_map(lat,lon)
            cs = plt.pcolormesh(lon_nat-(grid_res_nat/2.0),lat_nat+(grid_res_nat/2.0),grid_mod_angmean[:,:,hrs],cmap=my_cmap1,vmin=0.01,vmax=vmax,transform=ccrs.PlateCarree())
            cs.cmap.set_under('white')
            cb = plt.colorbar(cs,ax=ax,extend='min')
            ax.set_title('Unpaired Model Object Angle Precip. >= '+str(thres)+'" Per '+'{0:.2f}'.format(pre_acc)+' Hour\n '+ \
                'From '+beg_date_str_lo+' to '+end_date_str_lo,fontsize=13)
            plt.savefig(FIG_PATH+'/'+GRIB_PATH_DES+'_simp_prop_ang_mod_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[hrs]+ \
                '_t'+str(thres)+'_r'+grid_res_agg_str+'.png', bbox_inches='tight',dpi=200)
            plt.close()
            os.system('scp '+FIG_PATH+'/'+GRIB_PATH_DES+'_simp_prop_ang_mod_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[hrs]+ \
                '_t'+str(thres)+'_r'+grid_res_agg_str+'.png hpc@vm-lnx-rzdm06:/home/people/hpc/ftp/erickson/test2')
                
            ###############Plot Observed Angle###############
            
            #Determine max limit of colorbar
            vmax = 180
            [fig,ax] = cartopy_maps.plot_map(lat,lon)
            cs = plt.pcolormesh(lon_nat-(grid_res_nat/2.0),lat_nat+(grid_res_nat/2.0),grid_obs_angmean[:,:,hrs],cmap=my_cmap1,vmin=0.01,vmax=vmax,transform=ccrs.PlateCarree())
            cs.cmap.set_under('white')
            cb = plt.colorbar(cs,ax=ax,extend='min')
            ax.set_title('Unpaired Stage IV Object Angle Precip. >= '+str(thres)+'" Per '+'{0:.2f}'.format(pre_acc)+' Hour\n '+ \
                'From '+beg_date_str_lo+' to '+end_date_str_lo,fontsize=13)
            plt.savefig(FIG_PATH+'/'+GRIB_PATH_DES+'_simp_prop_ang_obs_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[hrs]+ \
                '_t'+str(thres)+'_r'+grid_res_agg_str+'.png', bbox_inches='tight',dpi=200)
            plt.close()
            os.system('scp '+FIG_PATH+'/'+GRIB_PATH_DES+'_simp_prop_ang_obs_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[hrs]+ \
                '_t'+str(thres)+'_r'+grid_res_agg_str+'.png hpc@vm-lnx-rzdm06:/home/people/hpc/ftp/erickson/test2')

            ###############Plot Difference in Angle###############
            NaN_matrix = (grid_diff_angmean > 0)*1.0
            
            #Create first colorlist
            my_cmap1 = copy.copy(mpl.cm.get_cmap('coolwarm')) 
            
            #Determine max limit of colorbar
            vmax = 180
            [fig,ax] = cartopy_maps.plot_map(lat,lon)
            cs = plt.pcolormesh(lon_nat-(grid_res_nat/2.0),lat_nat+(grid_res_nat/2.0),grid_diff_angmean[:,:,hrs]*NaN_matrix[:,:,hrs],cmap=my_cmap1,vmin=-vmax,vmax=vmax,transform=ccrs.PlateCarree())
            cs.cmap.set_under('white')
            cb = plt.colorbar(cs,ax=ax,extend='min')
            ax.set_title('Unpaired Object Angle Difference Precip. >= '+str(thres)+'" Per '+'{0:.2f}'.format(pre_acc)+' Hour\n '+ \
                'From '+beg_date_str_lo+' to '+end_date_str_lo,fontsize=13)
            plt.savefig(FIG_PATH+'/'+GRIB_PATH_DES+'_simp_prop_ang_diff_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[hrs]+ \
                '_t'+str(thres)+'_r'+grid_res_agg_str+'.png', bbox_inches='tight',dpi=200)
            plt.close()
            os.system('scp '+FIG_PATH+'/'+GRIB_PATH_DES+'_simp_prop_ang_diff_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[hrs]+ \
                '_t'+str(thres)+'_r'+grid_res_agg_str+'.png hpc@vm-lnx-rzdm06:/home/people/hpc/ftp/erickson/test2')
            
            ###############Plot Modeled Storm Track Count###############
            #Determine max limit of colorbar
            try:
                vmax = np.round(np.nanpercentile(grid_obs_count/simp_prop_count,99.5),2)  
            except IndexError:
                vmax = 0
            [fig,ax] = cartopy_maps.plot_map(lat,lon)
            cs = plt.pcolormesh(lon_nat-(grid_res_nat/2.0),lat_nat+(grid_res_nat/2.0),grid_mod_count[:,:,hrs]/simp_prop_count,cmap=my_cmap1,vmin=0.01,vmax=vmax,transform=ccrs.PlateCarree())
            cs.cmap.set_under('white')
            cb = plt.colorbar(cs,ax=ax,extend='min')
            ax.set_title('Unpaired Model Object Track Frequency Precip. >= '+str(thres)+'" Per '+'{0:.2f}'.format(pre_acc)+' Hour\n '+ \
                'From '+beg_date_str_lo+' to '+end_date_str_lo,fontsize=13)
            plt.savefig(FIG_PATH+'/'+GRIB_PATH_DES+'_simp_prop_count_mod_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[hrs]+ \
                '_t'+str(thres)+'_r'+grid_res_agg_str+'.png', bbox_inches='tight',dpi=200)
            plt.close()   
            os.system('scp '+FIG_PATH+'/'+GRIB_PATH_DES+'_simp_prop_count_mod_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[hrs]+ \
                '_t'+str(thres)+'_r'+grid_res_agg_str+'.png hpc@vm-lnx-rzdm06:/home/people/hpc/ftp/erickson/test2')
            
            ###############Plot Observed Storm Track Count###############
            [fig,ax] = cartopy_maps.plot_map(lat,lon)
            cs = plt.pcolormesh(lon_nat-(grid_res_nat/2.0),lat_nat+(grid_res_nat/2.0),grid_obs_count[:,:,hrs]/simp_prop_count,cmap=my_cmap1,vmin=0.01,vmax=vmax,transform=ccrs.PlateCarree())
            cs.cmap.set_under('white')
            cb = plt.colorbar(cs,ax=ax,extend='min')
            ax.set_title('Unpaired Stage IV Track Frequency Precip. >= '+str(thres)+'" Per '+'{0:.2f}'.format(pre_acc)+' Hour\n '+ \
                'From '+beg_date_str_lo+' to '+end_date_str_lo,fontsize=13)
            plt.savefig(FIG_PATH+'/'+GRIB_PATH_DES+'_simp_prop_count_obs_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[hrs]+ \
                '_t'+str(thres)+'_r'+grid_res_agg_str+'.png', bbox_inches='tight',dpi=200)
            plt.close()
            os.system('scp '+FIG_PATH+'/'+GRIB_PATH_DES+'_simp_prop_count_obs_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[hrs]+ \
                '_t'+str(thres)+'_r'+grid_res_agg_str+'.png hpc@vm-lnx-rzdm06:/home/people/hpc/ftp/erickson/test2')
            
            ###############Plot Difference in Track Count###############
            NaN_matrix = ((grid_diff_count > 0))*1.0
            
            #Create first colorlist
            my_cmap1 = copy.copy(mpl.cm.get_cmap('coolwarm')) 
            [fig,ax] = cartopy_maps.plot_map(lat,lon)
            cs = plt.pcolormesh(lon_nat-(grid_res_nat/2.0),lat_nat+(grid_res_nat/2.0),grid_diff_count[:,:,hrs],cmap=my_cmap1,vmin=-np.nanmax(grid_diff_count)*1.05,vmax=np.nanmax(grid_diff_count)*1.05,transform=ccrs.PlateCarree())
            cs.cmap.set_under('white')
            cb = plt.colorbar(cs,ax=ax,extend='min')
            ax.set_title('Unpaired Track Frequency Difference Precip. >= '+str(thres)+'" Per '+'{0:.2f}'.format(pre_acc)+' Hour\n '+ \
                'From '+beg_date_str_lo+' to '+end_date_str_lo,fontsize=13)
            plt.savefig(FIG_PATH+'/'+GRIB_PATH_DES+'_simp_prop_count_diff_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[hrs]+ \
                '_t'+str(thres)+'_r'+grid_res_agg_str+'.png', bbox_inches='tight',dpi=200)
            plt.close()
            os.system('scp '+FIG_PATH+'/'+GRIB_PATH_DES+'_simp_prop_count_diff_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[hrs]+ \
                '_t'+str(thres)+'_r'+grid_res_agg_str+'.png hpc@vm-lnx-rzdm06:/home/people/hpc/ftp/erickson/test2')            

elif subset_data == 'POYgPMY':

    if grid_res_nat == []: #If everything is aggregated along the time dimension only
        print ('Nothing to plot here, but average POYgPMY is '+str(np.nanmean(grid_POYgPMY)))
    elif grid_res_nat != []:

        #Create first colorlist
        my_cmap1 = copy.copy(mpl.cm.get_cmap('jet'))
        my_cmap1.set_under('white')
        [fig,ax] = cartopy_maps.plot_map(lat,lon)
        cs = plt.pcolormesh(lon_nat-(grid_res_nat/2.0),lat_nat+(grid_res_nat/2.0),grid_POYgPMY,cmap=my_cmap1,vmin=0,vmax=100,transform=ccrs.PlateCarree())
        cb = plt.colorbar(cs,ax=ax,extend='min')
        ax.set_title('Probability that Observation Exists Given Model Forecasts an Object - '+'{0:.2f}'.format(pre_acc)+' Hour Precip. > '+str(thres)+'"\n'+ \
            'From '+beg_date_str_lo+' to '+end_date_str_lo,fontsize=13)
        plt.savefig(FIG_PATH+'/'+GRIB_PATH_DES+'_POYgPMY_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[hrs]+ \
           '_t'+str(thres)+'_r'+grid_res_agg_str+'.png', bbox_inches='tight',dpi=200)
        plt.close()
        os.system('scp '+FIG_PATH+'/'+GRIB_PATH_DES+'_POYgPMY_s'+beg_date_str_sh+'_e'+end_date_str_sh+'_'+plot_str[hrs]+ \
           '_t'+str(thres)+'_r'+grid_res_agg_str+'.png hpc@vm-lnx-rzdm06:/home/people/hpc/ftp/erickson/test2')
 
