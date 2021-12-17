#!/usr/bin/python
# -*- coding: utf-8 -*-

################################################################################################
#ONE OF THE MAIN WRAPPER SCRIPTS TO AGGREGATE THE STATISTICS CREATED IN 
#ERO_verif_s_vday{1-3}.py USING STAT ANALYSIS AND CREATE A SERIES OF PLOTS. 
#20170705 - 20171210. MJE.
#
#UPDATE: MODIFIED TO GUNZIP PERMANENT FILES TO SAVE HARD DRIVE SPACE. 20180409. MJE.
#UPDATE: MODIFIED TO INCREASE EFFICIENCY. 20180510. MJE.
#UPDATE: FIX ERROR ASSOCIATED WITH DAY 1 00 UTC ISSUANCES. 20180718. MJE.
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
from mpl_toolkits.basemap import Basemap, cm
import matplotlib as mpl
mpl.use('Agg') #So plots can be saved in cron
import matplotlib.pyplot as plt
from matplotlib.mlab import griddata
from scipy.io import netcdf
from netCDF4 import Dataset
from scipy import ndimage
import loadAllEROData
reload(loadAllEROData)
sys.path.append('/export/hpc-lw-dtbdev5/merickson/code/python/MET')
import METConFigGen
import py2netcdf
import glob
reload(METConFigGen)
reload(py2netcdf)
from mpl_toolkits.axes_grid1 import make_axes_locatable

################################################################################
#########################1)MATRIX OF VARIABLES#################################
################################################################################
MET_PATH       = '/opt/MET6/met6.0/bin/'                                #Location of MET software
CON_PATH       = '/usr1/wpc_cpgffh/METv6.0/'                            #Location of MET config files
GRIB_PATH      = '/usr1/wpc_cpgffh/gribs/'                              #Location of model GRIB files
FIG_PATH       = '/usr1/wpc_cpgffh/figures/ERO/'                        #Location for figure generation
GRIB_PATH_DES  = 'ALL'                                                  #An appended string label for the temporary directory name
latlon_dims    = [-129.8,25.0,-65.0,49.8]                               #Latitude/longitude dimensions for plotting [WLON,SLAT,ELON,NLAT]                                                                                                                    
days_back      = 365                                                    #Total days backwards to include in verification
days_back_sh   = 60                                                     #Shorter window ERO statistics
days_offset    = 1                                                      #Most current date (e.g. end of verification window)
validday       = 1                                                      #Valid days to be verified (single day)
grid_delta     = 0.09                                                   #Grid resolution increment for interpolation (degrees lat/lon)
neigh_filter   = 40                                                     #Total neighborhoold filter (km)
gridpt_filter  = 49                                                     #Input into stat_analysis. Total pts in circle
smoth_filter   = 105                                                    #Total neighborhood smoother (radius in km)
ERO_probs      = [0.05,0.10,0.20,0.50]                                  #Declare the ERO probabilities for MRGL, SLGT, MDT, HIGH 
ERO_plotcat    = ['Marginal','Slight','Moderate','High']                #Declare plotting strings for all ERO thresholds
################################################################################
######################PREPARE THE DATA FOR LOADING##############################
################################################################################

#Determine the smoothing radius width
width_smo     = int((smoth_filter * 2) / (111 * grid_delta))

#Calculate radius metadata info
dia_filter = int(np.ceil(neigh_filter/(grid_delta*111)))*2
if int(dia_filter) % 2 == 0:
    dia_filter = dia_filter - 1

#Create date specific directory
GRIB_PATH_EX = GRIB_PATH+'/ERO_verif/ERO_verif_day'+str(validday)+'_'+GRIB_PATH_DES+'/'

#Redo the ERO probabilities to proper strings for input to set_GridStatConfigProb
ERO_probs_str = ['>='+str(i) for i in np.append(np.append(0.0, ERO_probs), 1.0)]
ERO_probs_str = ', '.join(ERO_probs_str)   
            
#Meta-data for PCT stat analysis generated file and ERO thresholds
PCT_metadata = ['TOTAL','N_THRESH']
for i in range(0,len(ERO_probs)+1): 
    for j in range(0,3):
        ele = []
        if j == 0:
            ele = 'THRES_'+str(i+1)
        elif j == 1:
            ele = 'OY_'+str(i+1)
        elif j == 2:
            ele = 'ON_'+str(i+1)
        
        PCT_metadata = np.append(PCT_metadata,ele)
      
#Generate current julian date, always starting at 12 UTC
curdate_init = datetime.datetime.now()-datetime.timedelta(days=days_offset)
curdate      = curdate_init.replace(hour=12)
curdate      = int(pygrib.datetime_to_julian(curdate))

#Load the CONUSmask and save the netCDF file
(CONUSmask,lat,lon) = loadAllEROData.readCONUSmask(GRIB_PATH,latlon_dims,grid_delta)

#Load the ST4gFFG mask to mask out spurious points on FFG grid
with np.load('/usr1/wpc_cpgffh/gribs/ERO_verif/static/ALL_noMRGL_ST4gFFGmask_del'+str(grid_delta)+'.npz') as data:
    ST4gFFG_mask = data['ST4gFFG_mask']
CONUSmask[CONUSmask<0.1]  = np.NaN
CONUSmask[CONUSmask>=0.1] = 1
CONUSmask = CONUSmask * ST4gFFG_mask

############################################################################
########AGGREGATE ALL GRID STAT RESULTS USING STAT_ANALYSIS#################
############################################################################

#Create strings for start/end valid dates (note metadata has a valid time as the end of the data)
datetime_beg = pygrib.julian_to_datetime(curdate-days_back)
datetime_end = pygrib.julian_to_datetime(curdate)

yrmondayhr_beg = ''.join(['{:04d}'.format(datetime_beg.year),'{:02d}'.format(datetime_beg.month), \
    '{:02d}'.format(datetime_beg.day),'{:02d}'.format(datetime_beg.hour)])
yrmondayhr_end = ''.join(['{:04d}'.format(datetime_end.year),'{:02d}'.format(datetime_end.month), \
    '{:02d}'.format(datetime_end.day),'{:02d}'.format(datetime_end.hour)])
    
jultime_alldates =  range(curdate-days_back,curdate,1)

#Initialize needed variables
PCT_data_ST4gFFG  = np.full([len(PCT_metadata)+1],np.nan)
PCT_data_ALL      = np.full([len(PCT_metadata)+1],np.nan)

####Create Stat Analysis configuration file and run stat_analysis for ST4gFFG
con_name_ST4gFFG      = METConFigGen.set_StatAnalysisConfigProb(CON_PATH,GRIB_PATH_DES,GRIB_PATH_EX,'ERO', \
    'Surface',ERO_probs_str,'ST4gFFG','Surface','>0','PCT',datetime_beg,datetime_end,gridpt_filter,'MAX_CIRCLE')   
stat_filename_ST4gFFG = GRIB_PATH_EX+GRIB_PATH_DES+'_ERO_Vs_ST4gFFG_s'+yrmondayhr_beg+'_e'+ \
    yrmondayhr_end+'_PCT'
#Gunzip/gzip needed files for stat_analysis
uni_month = np.unique([ '{:04d}'.format(pygrib.julian_to_datetime(i).year)+ \
    '{:02d}'.format(pygrib.julian_to_datetime(i).month) for i in np.arange(curdate-days_back,curdate)])
for month in uni_month:
    subprocess.call('gunzip '+GRIB_PATH_EX+'grid_stat_ST4gFFG_ERO_*'+month+'*.gz',stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'),shell=True)
subprocess.call(MET_PATH+'stat_analysis -lookin '+GRIB_PATH_EX+' -out '+stat_filename_ST4gFFG+' -config '+ \
    con_name_ST4gFFG,stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'),shell=True)
for month in uni_month:
    subprocess.call('gzip -f '+GRIB_PATH_EX+'grid_stat_ST4gFFG_ERO_*'+month+'*',stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'),shell=True)
       
####Create Stat Analysis configuration file and run stat_analysis for ALL      
con_name_ALL      = METConFigGen.set_StatAnalysisConfigProb(CON_PATH,GRIB_PATH_DES,GRIB_PATH_EX,'ERO', \
    'Surface',ERO_probs_str,'ALL','A365324','>0','PCT',datetime_beg,datetime_end,gridpt_filter,'MAX_CIRCLE')  
stat_filename_ALL = GRIB_PATH_EX+GRIB_PATH_DES+'_ERO_Vs_ALL_s'+yrmondayhr_beg+'_e'+ \
    yrmondayhr_end+'_PCT'
#Gunzip/gzip needed files for stat_analysis
uni_month = np.unique([ '{:04d}'.format(pygrib.julian_to_datetime(i).year)+ \
    '{:02d}'.format(pygrib.julian_to_datetime(i).month) for i in np.arange(curdate-days_back,curdate)])
for month in uni_month:
    subprocess.call('gunzip '+GRIB_PATH_EX+'grid_stat_ALL_ERO_*'+month+'*.gz',stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'),shell=True)
subprocess.call(MET_PATH+'stat_analysis -lookin '+GRIB_PATH_EX+' -out '+stat_filename_ALL+' -config '+ \
    con_name_ALL,stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'),shell=True)
for month in uni_month:
    subprocess.call('gzip -f '+GRIB_PATH_EX+'grid_stat_ALL_ERO_*'+month+'*',stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'),shell=True)
      
#Extract the data from the StatAnalysis file for ST4gFFG
file = open(stat_filename_ST4gFFG, 'rb')
lin = file.readline()
while lin:  #Iterate through file     
    #Read in next line to determine MRGL, SLGT, MDT, or HIGH
    lin = file.readline()
    if 'PCT:' in lin:
        #Array of white-space index elements that delineates new columns of data
        lin_empty = np.array([i for i in range(0,len(lin)) if lin[i] == ' '])
        lin_empty = lin_empty[lin_empty >= lin.find(':')+1]
        lin_empty = lin_empty[np.diff(np.insert(lin_empty,0,0)) != 1]
        #Loop through non-white space elements to identify components
        for ind in range(0,len(lin_empty)):
            if ind == len(lin_empty)-1:
                PCT_data_ST4gFFG[ind] = float(lin[lin_empty[ind]:-1])
            else:
                PCT_data_ST4gFFG[ind] = float(lin[lin_empty[ind]:lin_empty[ind+1]])

#Extract the data from the StatAnalysis file for ALL
file = open(stat_filename_ALL, 'rb')
lin = file.readline()
while lin:  #Iterate through file     
    #Read in next line to determine MRGL, SLGT, MDT, or HIGH
    lin = file.readline()
    if 'PCT:' in lin:
        #Array of white-space index elements that delineates new columns of data
        lin_empty = np.array([i for i in range(0,len(lin)) if lin[i] == ' '])
        lin_empty = lin_empty[lin_empty >= lin.find(':')+1]
        lin_empty = lin_empty[np.diff(np.insert(lin_empty,0,0)) != 1]
        #Loop through non-white space elements to identify components
        for ind in range(0,len(lin_empty)):
            if ind == len(lin_empty)-1:
                PCT_data_ALL[ind] = float(lin[lin_empty[ind]:-1])
            else:
                PCT_data_ALL[ind] = float(lin[lin_empty[ind]:lin_empty[ind+1]])

#Remove Stat Analysis files
output = subprocess.call('rm -rf '+stat_filename_ST4gFFG,stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'), shell=True)
output = subprocess.call('rm -rf '+stat_filename_ALL,stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'), shell=True)

############################################################################
######USE SELF-CREATED FUNCTIONS TO EXTRACT DATA FROM GRID_STAT#############
############################################################################
  
#Load BS/AuROC information from grid_stat output
(EvS_data,EvS_yrmondayhr,EvS_vhr)    = loadAllEROData.statAnalyisSub(GRIB_PATH_EX, \
    'Surface','ERO','Surface','ST4gFFG','PSTD',['BRIER','BRIER_NCL','BRIER_NCU','ROC_AUC'], \
    datetime_beg,datetime_end)
(EvA_data,EvA_yrmondayhr,EvA_vhr)    = loadAllEROData.statAnalyisSub(GRIB_PATH_EX, \
    'Surface','ERO','A365324','ALL','PSTD',['BRIER','BRIER_NCL','BRIER_NCU','ROC_AUC'], \
    datetime_beg,datetime_end)

#Load short version of BS/AuROC for plotting time series and issuance time data
(EvS_data_sh,EvS_yrmondayhr_sh,EvS_vhr_sh)    = loadAllEROData.statAnalyisSub(GRIB_PATH_EX, \
    'Surface','ERO','Surface','ST4gFFG','PSTD',['BRIER','BRIER_NCL','BRIER_NCU','ROC_AUC'], \
    datetime_end-datetime.timedelta(days=days_back_sh),datetime_end)
(EvA_data_sh,EvA_yrmondayhr_sh,EvA_vhr_sh)    = loadAllEROData.statAnalyisSub(GRIB_PATH_EX, \
    'Surface','ERO','A365324','ALL','PSTD',['BRIER','BRIER_NCL','BRIER_NCU','ROC_AUC'], \
    datetime_end-datetime.timedelta(days=days_back_sh),datetime_end)
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       
####################################################################################################################
####LOAD/CALCULATE SPATIAL ERO FREQUENCY THROUGHOUT TOTAL PERIOD CONSIDERED USING MATRICES FROM statAnalyisSub######
####################################################################################################################

ERO_MRGL    = np.zeros((lat.shape[0],lat.shape[1]))
ERO_SLGT    = np.zeros((lat.shape[0],lat.shape[1]))
ERO_MDT     = np.zeros((lat.shape[0],lat.shape[1]))
ERO_HIGH    = np.zeros((lat.shape[0],lat.shape[1]))
file_count  = 0
EvS_datestr = []

#Do this for all ERO instances
for date in range(0,len(EvS_yrmondayhr)):
    for file_s in glob.glob(GRIB_PATH_EX+'grid_stat_ST4gFFG_ERO_s*'+'_e'+EvS_yrmondayhr[date]+'_vhr'+ \
        '{:02d}'.format(int(EvS_vhr[date]))+'*pairs.nc.gz'):
        
        subprocess.call('gunzip '+file_s,stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'),shell=True)
        f        = Dataset(file_s[0:-3], "a", format="NETCDF4")
        subprocess.call('gzip '+file_s[0:-3],stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'),shell=True)
        
        temp     = (np.array(f.variables['FCST_ERO_Surface_FULL'][:])>=ERO_probs[0])*1
        temp[temp < 0] = 0
        ERO_MRGL = ERO_MRGL + temp
        
        temp     = (np.array(f.variables['FCST_ERO_Surface_FULL'][:])>=ERO_probs[1])*1
        temp[temp < 0] = 0
        ERO_SLGT = ERO_SLGT + temp

        temp     = (np.array(f.variables['FCST_ERO_Surface_FULL'][:])>=ERO_probs[2])*1
        temp[temp < 0] = 0
        ERO_MDT = ERO_MDT + temp

        temp     = (np.array(f.variables['FCST_ERO_Surface_FULL'][:])>=ERO_probs[3])*1
        temp[temp < 0] = 0
        ERO_HIGH = ERO_HIGH + temp
        
        EvS_datestr = np.append(EvS_datestr,EvS_yrmondayhr[date])
        file_count += 1 

################################################################################################
####CONSIDER SHORTER BS/AuROC PERIOD SUBSET ON DAYS WITH A SLGT OR GREATER######################
################################################################################################

EvS_isSLGT_sh  = []
EvS_datestr_sh = []
#Do this for all ERO instances
for date in range(0,len(EvS_yrmondayhr_sh)):
    for file_s in glob.glob(GRIB_PATH_EX+'grid_stat_ST4gFFG_ERO_s*'+'_e'+EvS_yrmondayhr_sh[date]+'_vhr'+ \
        '{:02d}'.format(int(EvS_vhr_sh[date]))+'*pairs.nc.gz'):

        subprocess.call('gunzip '+file_s,stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'),shell=True)
        f        = Dataset(file_s[0:-3], "a", format="NETCDF4")
        subprocess.call('gzip '+file_s[0:-3],stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'),shell=True)
        
        temp     = (np.array(f.variables['FCST_ERO_Surface_FULL'][:])>=ERO_probs[1])*1
        temp[temp < 0] = 0

        #Check to see if any SLGT >= 10 points exists for given issuance
        if np.nansum(temp) < 10:
            EvS_isSLGT_sh = np.append(EvS_isSLGT_sh,0)
        else:
            EvS_isSLGT_sh = np.append(EvS_isSLGT_sh,1)

        EvS_datestr_sh = np.append(EvS_datestr_sh,EvS_yrmondayhr_sh[date])

EvA_isSLGT_sh  = []
EvA_datestr_sh = []
#Repeat only for 09 UTC instances, so that this can be compared to EvA matrices
for date in range(0,len(EvA_yrmondayhr_sh)):
    for file_s in glob.glob(GRIB_PATH_EX+'grid_stat_ST4gFFG_ERO_s*'+'_e'+EvA_yrmondayhr_sh[date]+'_vhr'+ \
        '{:02d}'.format(int(EvA_vhr_sh[date]))+'*pairs.nc.gz'):

        subprocess.call('gunzip '+file_s,stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'),shell=True)
        f        = Dataset(file_s[0:-3], "a", format="NETCDF4")
        subprocess.call('gzip '+file_s[0:-3],stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'),shell=True)
        
        temp     = (np.array(f.variables['FCST_ERO_Surface_FULL'][:])>=ERO_probs[1])*1
        temp[temp < 0] = 0

        #Check to see if any SLGT >= 500 points exists for given issuance
        if np.nansum(temp) < 10:
            EvA_isSLGT_sh = np.append(EvA_isSLGT_sh,0)
        else:
            EvA_isSLGT_sh = np.append(EvA_isSLGT_sh,1)

        EvA_datestr_sh = np.append(EvA_datestr_sh,EvA_yrmondayhr_sh[date])

#For EvS, if one ERO issuance was dropped for a day, all are dropped since BS/AuROC exhibit signif. daily variability
for date_u in np.unique(EvS_datestr_sh):

    indices = [i for i in range(0,len(EvS_datestr_sh)) if date_u ==  EvS_datestr_sh[i]]
    if np.isnan(np.mean(EvS_data_sh[indices,3])) or np.mean(EvS_isSLGT_sh[indices]) != 1:
        EvS_isSLGT_sh[indices] = 0

#Subset the EvS and EvA data
EvS_isSLGT_sh = [i for i in range(0,len(EvS_isSLGT_sh)) if EvS_isSLGT_sh[i] == 1]
EvA_isSLGT_sh = [i for i in range(0,len(EvA_isSLGT_sh)) if EvA_isSLGT_sh[i] == 1]

#Eliminate all ERO days without at least a MRGL
EvS_data_sh       = EvS_data_sh[EvS_isSLGT_sh,:]
EvS_yrmondayhr_sh = EvS_yrmondayhr_sh[EvS_isSLGT_sh]
EvS_vhr_sh        = EvS_vhr_sh[EvS_isSLGT_sh]
EvA_data_sh       = EvA_data_sh[EvA_isSLGT_sh,:]
EvA_yrmondayhr_sh = EvA_yrmondayhr_sh[EvA_isSLGT_sh]
EvA_vhr_sh        = EvA_vhr_sh[EvA_isSLGT_sh]

#Find indices within ALL that match ST4gFFG (recall ALL can only use 24 hours of data)
EvAtoEVS_ind_sh = np.full([EvA_yrmondayhr_sh.shape[0]],np.nan)
for fcstA in range(0,len(EvA_yrmondayhr_sh)):
    for fcstS in range(0,len(EvS_yrmondayhr_sh)):
        if EvA_yrmondayhr_sh[fcstA] == EvS_yrmondayhr_sh[fcstS] and EvA_vhr_sh[fcstA] == EvS_vhr_sh[fcstS]:
            EvAtoEVS_ind_sh[fcstA] = fcstS
            
#Collect data based on vhr to determine if forecast gets better closer to valid time
EvS_BS_byhr01    = []
EvS_BS_byhr09    = []
EvS_BS_byhr15    = []
EvS_BS_byhr21    = []
EvS_AuROC_byhr01 = []
EvS_AuROC_byhr09 = []
EvS_AuROC_byhr15 = []
EvS_AuROC_byhr21 = []
sep_days = np.where(EvS_vhr_sh == 9)[0]

for days in range(0,len(sep_days)-1):
    
    #Subset data within the same day
    data_temp       = EvS_data_sh[sep_days[days]:sep_days[days+1],:]
    vhr_temp        = EvS_vhr_sh[sep_days[days]:sep_days[days+1]]
    
    for hours in range(0,len(vhr_temp)):
        
        if validday == 1:
            if vhr_temp[hours] >= 0 and vhr_temp[hours] <= 6:
                EvS_BS_byhr01    = np.append(EvS_BS_byhr01,   data_temp[hours,0])
                EvS_AuROC_byhr01 = np.append(EvS_AuROC_byhr01,data_temp[hours,3])
            elif vhr_temp[hours] >= 6 and vhr_temp[hours] <= 12:
                EvS_BS_byhr09    = np.append(EvS_BS_byhr09,   data_temp[hours,0])
                EvS_AuROC_byhr09 = np.append(EvS_AuROC_byhr09,data_temp[hours,3])
            elif vhr_temp[hours] >= 12 and vhr_temp[hours] <= 18:
                EvS_BS_byhr15    = np.append(EvS_BS_byhr15,   data_temp[hours,0])
                EvS_AuROC_byhr15 = np.append(EvS_AuROC_byhr15,data_temp[hours,3])       
        else:
            if vhr_temp[hours] >= 0 and vhr_temp[hours] <= 12:
                EvS_BS_byhr09    = np.append(EvS_BS_byhr09,   data_temp[hours,0])
                EvS_AuROC_byhr09 = np.append(EvS_AuROC_byhr09,data_temp[hours,3])
            elif vhr_temp[hours] >= 12:
                EvS_BS_byhr21    = np.append(EvS_BS_byhr21,   data_temp[hours,0])
                EvS_AuROC_byhr21 = np.append(EvS_AuROC_byhr21,data_temp[hours,3])
               
#Aggregate all the data together and average
if validday == 1:
    EvS_BS_byhr    = [np.nanmedian(EvS_BS_byhr09),np.nanmedian(EvS_BS_byhr15),np.nanmedian(EvS_BS_byhr01)]
    EvS_AuROC_byhr = [np.nanmedian(EvS_AuROC_byhr09),np.nanmedian(EvS_AuROC_byhr15),np.nanmedian(EvS_AuROC_byhr01)]  
else:        
    EvS_BS_byhr    = [np.nanmedian(EvS_BS_byhr09),np.nanmedian(EvS_BS_byhr21)]
    EvS_AuROC_byhr = [np.nanmedian(EvS_AuROC_byhr09),np.nanmedian(EvS_AuROC_byhr21)]  

#######################################################################################################
###FOR RECENT 7 DAY WINDOW, LOAD DATA TO CREATE NEW VERIF. SPAT. PLOTS (SINCE ST4 MAY UPDATE)##########
#######################################################################################################

jultime_end = int(pygrib.datetime_to_julian(datetime_end))

#Initilize needed matrices
cnt_ALL  = 0
ST4gFFG_last7      = np.full([lat.shape[0],lat.shape[1],100],np.nan)
ARI_last7          = np.full([lat.shape[0],lat.shape[1],100],np.nan)
ERO_MRGL_last7     = np.full([lat.shape[0],lat.shape[1],100],np.nan)
ERO_SLGT_last7     = np.full([lat.shape[0],lat.shape[1],100],np.nan)
ERO_MDT_last7      = np.full([lat.shape[0],lat.shape[1],100],np.nan)
ERO_HIGH_last7     = np.full([lat.shape[0],lat.shape[1],100],np.nan)
PP_ALL_last7       = np.full([lat.shape[0],lat.shape[1],100],np.nan)
PP_ST4gFFG_last7   = np.full([lat.shape[0],lat.shape[1],100],np.nan)
vhr_last7          = []
date_s_last7       = []
date_e_last7       = []
USGS_lat_last7     = [[] for i in range(0,100)]
USGS_lon_last7     = [[] for i in range(0,100)]
LSRFLASH_lat_last7 = [[] for i in range(0,100)]
LSRFLASH_lon_last7 = [[] for i in range(0,100)]
LSRREG_lat_last7   = [[] for i in range(0,100)]
LSRREG_lon_last7   = [[] for i in range(0,100)]
MPING_lat_last7    = [[] for i in range(0,100)]
MPING_lon_last7    = [[] for i in range(0,100)]

#Loop through all files, find file with specific date string, separate ERO category for plotting
for days in range(jultime_end-7,jultime_end+1):
    #Create proper string to seek out data
    datetime_cur = pygrib.julian_to_datetime(days)
    yrmonday_cur = ''.join(['{:04d}'.format(datetime_cur.year),'{:02d}'.format(datetime_cur.month), \
        '{:02d}'.format(datetime_cur.day)])
    datetime_ahd = pygrib.julian_to_datetime(days+1)
    yrmonday_ahd = ''.join(['{:04d}'.format(datetime_ahd.year),'{:02d}'.format(datetime_ahd.month), \
        '{:02d}'.format(datetime_ahd.day)])
    datetime_bhd = pygrib.julian_to_datetime(days-1)
    yrmonday_bhd = ''.join(['{:04d}'.format(datetime_bhd.year),'{:02d}'.format(datetime_bhd.month), \
        '{:02d}'.format(datetime_bhd.day)])
    
    filename_ARI   = GRIB_PATH_EX+'ST4gARI_s'+yrmonday_bhd+'12_e'+yrmonday_cur+'12_vhr12.nc.gz'
    
    #Recreate text files for MPING/LSR/USGS   
    filename_USGS      = loadAllEROData.Cosgrove2txt(GRIB_PATH,GRIB_PATH_EX,datetime_bhd,12,latlon_dims,grid_delta,'usgs')
    filename_LSRFLASH  = loadAllEROData.Cosgrove2txt(GRIB_PATH,GRIB_PATH_EX,datetime_bhd,12,latlon_dims,grid_delta,'lsrflash')
    filename_LSRREG    = loadAllEROData.Cosgrove2txt(GRIB_PATH,GRIB_PATH_EX,datetime_bhd,12,latlon_dims,grid_delta,'lsrreg')
    filename_MPING     = loadAllEROData.Cosgrove2txt(GRIB_PATH,GRIB_PATH_EX,datetime_bhd,12,latlon_dims,grid_delta,'mping')
    
    for files in os.listdir(GRIB_PATH_EX):
        if '_e'+yrmonday_cur in files and '.nc' in files and 'grid_stat_ST4gFFG' in files:
            if '_ERO_' in files:

                date_s_last7                = np.append(date_s_last7,files[files.find('_ERO_')+6:files.find('_ERO_')+16])
                date_e_last7                = np.append(date_e_last7,files[files.find('_ERO_')+18:files.find('_ERO_')+28])
                vhr_last7                   = np.append(vhr_last7,files[files.find('_vhr')+4:files.find('_vhr')+6])

                subprocess.call('gunzip '+GRIB_PATH_EX+files,stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'),shell=True)
                f        = Dataset(GRIB_PATH_EX+files[0:-3], "a", format="NETCDF4")
                subprocess.call('gzip '+GRIB_PATH_EX+files[0:-3],stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'),shell=True)
                
                ST4gFFG_last7[:,:,cnt_ALL]  = (np.array(f.variables['OBS_ST4gFFG_Surface_FULL_MAX_'+str(dia_filter**2)+''][:])*1)
                ERO_MRGL_last7[:,:,cnt_ALL] = (np.array(f.variables['FCST_ERO_Surface_FULL'][:])==ERO_probs[0])*1
                ERO_SLGT_last7[:,:,cnt_ALL] = (np.array(f.variables['FCST_ERO_Surface_FULL'][:]==ERO_probs[1])*1)
                ERO_MDT_last7[:,:,cnt_ALL]  = (np.array(f.variables['FCST_ERO_Surface_FULL'][:]==ERO_probs[2])*1)
                ERO_HIGH_last7[:,:,cnt_ALL] = (np.array(f.variables['FCST_ERO_Surface_FULL'][:]==ERO_probs[3])*1)
                f.close()
                
                #Code identify ST4gFFG and ST4gARI txt files
                if validday == 1 and int(vhr_last7[cnt_ALL]) >= 0 and int(vhr_last7[cnt_ALL]) < 9:
                    filename_ST4gFFG = GRIB_PATH_EX+'ST4gFFG_s'+date_e_last7[cnt_ALL][0:-2]+'{:02d}'.format(int(vhr_last7[cnt_ALL]))+ \
                        '_e'+date_e_last7[cnt_ALL][0:-2]+'12.txt'
                else:
                    filename_ST4gFFG = GRIB_PATH_EX+'ST4gFFG_s'+date_s_last7[cnt_ALL][0:-2]+'{:02d}'.format(int(vhr_last7[cnt_ALL]))+ \
                        '_e'+date_e_last7[cnt_ALL][0:-2]+'12.txt'
                filename_ST4gARI = GRIB_PATH_EX+'ST4gARI_s'+date_s_last7[cnt_ALL][0:-2]+'12'+'_e'+date_e_last7[cnt_ALL][0:-2]+'12.txt'

                #Apply practically perfect to ST4gFFG and ALL
                [lat,lon,PP_ALL_last7[:,:,cnt_ALL]]     = loadAllEROData.PracticallyPerfect_NEW(MET_PATH,GRIB_PATH_EX,latlon_dims,grid_delta,[40,40,40,25,25],width_smo, \
                    [filename_USGS,filename_LSRFLASH,filename_LSRREG,filename_ST4gFFG,filename_ST4gARI])
                [lat,lon,PP_ST4gFFG_last7[:,:,cnt_ALL]] = loadAllEROData.PracticallyPerfect_NEW(MET_PATH,GRIB_PATH_EX,latlon_dims,grid_delta,[25],width_smo, \
                    [filename_ST4gFFG])

                #Load ARI/USGS/LSR/MPING and match dimensions of ST4gFFG data        
                #Read in ARI
                subprocess.call('gunzip '+filename_ARI,stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'),shell=True)
                f                           = Dataset(filename_ARI[0:-3], "a", format="NETCDF4")
                subprocess.call('gzip '+filename_ARI[0:-3],stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'),shell=True)
                
                ARI_last7[:,:,cnt_ALL]      = f.variables['ST4gARI'][:]    
                
                #Read in USGS
                temp_lat = []
                temp_lon = []

                fobj = open(filename_USGS, 'rb')
                line_count = 0
                for line in fobj:
                    if line_count > 0:
                        temp_lat = np.append(temp_lat,float(line[0:4]))
                        temp_lon = np.append(temp_lon,float(line[4:-1]))
                    line_count += 1
                fobj.close()
                if len(temp_lat) == 0:
                    USGS_lat_last7[cnt_ALL] = [0]
                    USGS_lon_last7[cnt_ALL] = [0]
                else:
                    USGS_lat_last7[cnt_ALL] = temp_lat
                    USGS_lon_last7[cnt_ALL] = temp_lon
                
                #Read in LSRFLASH
                temp_lat = []
                temp_lon = []
                fobj = open(filename_LSRFLASH, 'rb')
                line_count = 0
                for line in fobj:
                    if line_count > 0:
                        temp_lat = np.append(temp_lat,float(line[0:4]))
                        temp_lon = np.append(temp_lon,float(line[4:-1]))
                    line_count += 1
                fobj.close()
                if len(temp_lat) == 0:
                    LSRFLASH_lat_last7[cnt_ALL] = [0]
                    LSRFLASH_lon_last7[cnt_ALL] = [0]
                else:
                    LSRFLASH_lat_last7[cnt_ALL] = temp_lat
                    LSRFLASH_lon_last7[cnt_ALL] = temp_lon
                    
                #Read in LSRREG
                temp_lat = []
                temp_lon = []
                fobj = open(filename_LSRREG, 'rb')
                line_count = 0
                for line in fobj:
                    if line_count > 0:
                        temp_lat = np.append(temp_lat,float(line[0:4]))
                        temp_lon = np.append(temp_lon,float(line[4:-1]))
                    line_count += 1
                fobj.close()
                if len(temp_lat) == 0:
                    LSRREG_lat_last7[cnt_ALL] = [0]
                    LSRREG_lon_last7[cnt_ALL] = [0]
                else:
                    LSRREG_lat_last7[cnt_ALL] = temp_lat
                    LSRREG_lon_last7[cnt_ALL] = temp_lon
                    
                #Read in MPING
                temp_lat = []
                temp_lon = []
                fobj = open(filename_MPING, 'rb')
                line_count = 0
                for line in fobj:
                    if line_count > 0:
                        temp_lat = np.append(temp_lat,float(line[0:4]))
                        temp_lon = np.append(temp_lon,float(line[4:-1]))
                    line_count += 1
                fobj.close()
                if len(temp_lat) == 0:
                    MPING_lat_last7[cnt_ALL] = [0]
                    MPING_lon_last7[cnt_ALL] = [0]
                else:
                    MPING_lat_last7[cnt_ALL] = temp_lat
                    MPING_lon_last7[cnt_ALL] = temp_lon
                    
                cnt_ALL += 1
          
#Remove NaN dimension
remove_nans        = np.mean(np.mean(np.isnan(ERO_HIGH_last7),axis=0),axis=0)       
ERO_MRGL_last7     = ERO_MRGL_last7[:,:,remove_nans==0]
ERO_SLGT_last7     = ERO_SLGT_last7[:,:,remove_nans==0]  
ERO_MDT_last7      = ERO_MDT_last7[:,:,remove_nans==0]  
ERO_HIGH_last7     = ERO_HIGH_last7[:,:,remove_nans==0]
ST4gFFG_last7      = ST4gFFG_last7[:,:,remove_nans==0]
PP_ST4gFFG_last7   = PP_ST4gFFG_last7[:,:,remove_nans==0]
PP_ALL_last7       = PP_ALL_last7[:,:,remove_nans==0]
ARI_last7          = ARI_last7[:,:,remove_nans==0]
USGS_lat_last7     = [i for i in USGS_lat_last7 if len(i) > 0]
USGS_lon_last7     = [i for i in USGS_lon_last7 if len(i) > 0]
LSRFLASH_lat_last7 = [i for i in LSRFLASH_lat_last7 if len(i) > 0]
LSRFLASH_lon_last7 = [i for i in LSRFLASH_lon_last7 if len(i) > 0]
LSRREG_lat_last7   = [i for i in LSRREG_lat_last7 if len(i) > 0]
LSRREG_lon_last7   = [i for i in LSRREG_lon_last7 if len(i) > 0]
MPING_lat_last7    = [i for i in MPING_lat_last7 if len(i) > 0]
MPING_lon_last7    = [i for i in MPING_lon_last7 if len(i) > 0]

############################################################################
##################PLOTTIN TIME FOR ALL DATA GENERATED#######################
############################################################################
#CREATE TIME SERIES OF BS AND AuROC FOR ST4gFFG AND ALL, BUT ONLY FOR DAYS WITH MRGL > 500 POINTS
fig = plt.figure(figsize=(8,8))
ax1 = fig.add_axes([0.1,0.1,0.8,0.8])
ax1.plot(range(0,EvS_data_sh.shape[0]), EvS_data_sh[:,0],'-x',linewidth=1, label='walker position', color='blue')
ax1.plot(EvAtoEVS_ind_sh, EvA_data_sh[:,0], 'o', linewidth=1, label='walker position', color='blue')
ax1.set_xlabel('ERO Valid Ending Time',fontSize=14)
ax1.set_ylim(-0.011,np.nanmax(EvA_data_sh[:,0]*2))
# Make the y-axis label, ticks and tick labels match the line color.
ax1.set_ylabel('Brier Score', color='b',fontSize=14)
ax1.annotate('BS - Lower is Better', xy=(EvS_data_sh.shape[0]-(EvS_data_sh.shape[0]/10), -0.006), xytext=(EvS_data_sh.shape[0]-(EvS_data_sh.shape[0]/10), 0), \
    arrowprops=dict(facecolor='blue', edgecolor='blue'),horizontalalignment='center', verticalalignment='top',color='blue')
#Second part of plotyy
ax2 = ax1.twinx()
ax2.plot(range(0,EvS_data_sh.shape[0]), EvS_data_sh[:,3], '-x',linewidth=1, label='walker position', color='red')
ax2.plot(EvAtoEVS_ind_sh, EvA_data_sh[:,3], 'o',linewidth=1, label='walker position', color='red')
ax2.set_ylabel('Area Under Relative Operating Characteristic', color='r',fontSize=14)
xtick_pts = np.arange(0,len(EvS_yrmondayhr_sh),(len(EvS_yrmondayhr_sh)/6)+1)
plt.xticks(xtick_pts, EvS_yrmondayhr_sh[xtick_pts],fontsize=4)
ax2.set_ylim(-0.011,1.1)
ax2.annotate('AuROC - Higher is Better', xy=(EvS_data_sh.shape[0]-(EvS_data_sh.shape[0]/10), 1.1), xytext=(EvS_data_sh.shape[0]-(EvS_data_sh.shape[0]/10), 1.04), \
    arrowprops=dict(facecolor='red', edgecolor='red'),horizontalalignment='center', verticalalignment='top',color='red')
plt.show()
plt.title('Time Series of BS and AuROC for WPC Day '+str(validday)+' ERO',fontsize=16)
#Set up the legend
line_label=[]
line_str=[];
leg_nam = ['BS - FFG Only','BS - ALL', 'AuROC - FFG Only', 'AuROC - ALL']
colorlist = ["blue","blue","red","red"] 
markerlist = ['x','o','x','o']   
for x in range(0,len(leg_nam)):
    line_label = np.hstack((line_label, mpl.lines.Line2D(range(1), range(1), color=colorlist[x], linestyle='None', marker=markerlist[x], markersize=7)))
    line_str   = np.hstack((line_str, leg_nam[x]))
first_legend=plt.legend(line_label, line_str, fontsize=10, numpoints=1, loc=3, framealpha=1)
ax2 = plt.gca().add_artist(first_legend)
plt.savefig(FIG_PATH+'/'+GRIB_PATH_DES+'_timeseries_BSandAuROC_vday'+str(int(validday))+'.png', bbox_inches='tight',dpi=200)
plt.close()                                                                                                                                                                                                                                                                                                                                                                                                                                                       
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                
#BS AND AuROC AVERAGED BY ISSUANCE HOUR FOR ST4gFFG AND ALL                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             #CREATE TIME SERIES OF BS AND AuROC FOR ST4GFFG AND ALL
fig = plt.figure(figsize=(8,8))
ax1 = fig.add_axes([0.1,0.1,0.8,0.8])
ax1.plot(range(0,len(EvS_BS_byhr)), EvS_BS_byhr,'-x',linewidth=2, label='walker position', color='blue')
ax1.set_xlabel('ERO Issuance Time',fontSize=14)
ax1.set_ylim(np.nanmin(EvS_BS_byhr)-0.0001,np.nanmax(EvS_BS_byhr)+0.0001)
# Make the y-axis label, ticks and tick labels match the line color.
ax1.set_ylabel('Brier Score', color='b',fontSize=14)
ax1.annotate('BS - Lower is Better', xy=(len(EvS_BS_byhr)-(float(len(EvS_BS_byhr))/10)-1, np.nanmin(EvS_BS_byhr)-0.0001), xytext=(len(EvS_BS_byhr)-(float(len(EvS_BS_byhr))/10)-1, np.nanmin(EvS_BS_byhr)-0.00005), \
    arrowprops=dict(facecolor='blue', edgecolor='blue'),horizontalalignment='center', verticalalignment='top',color='blue')
#Second part of plotyy
ax2 = ax1.twinx()
ax2.plot(range(0,len(EvS_AuROC_byhr)), EvS_AuROC_byhr,'-x',linewidth=2, label='walker position', color='red')
ax2.set_ylabel('Area Under Relative Operating Characteristic', color='r',fontSize=14)
ax2.set_ylim(np.nanmin(EvS_AuROC_byhr)-0.005,np.nanmax(EvS_AuROC_byhr)+0.005)
ax2.annotate('AuROC - Higher is Better', xy=(len(EvS_BS_byhr)-(float(len(EvS_BS_byhr))/10)-1, np.nanmax(EvS_AuROC_byhr)+0.0045), \
    xytext=(len(EvS_BS_byhr)-(float(len(EvS_BS_byhr))/10)-1, np.nanmax(EvS_AuROC_byhr)+0.0025), arrowprops=dict(facecolor='red', \
    edgecolor='red'),horizontalalignment='center', verticalalignment='top',color='red')
if validday == 1:
    plt.xticks(np.linspace(0,2,3), ['09','15','01'],fontsize=11)
else:
    plt.xticks(np.linspace(0,1,2), ['09','21'],fontsize=11)
plt.show()
plt.title('BS and AuROC by Issuance Time for WPC Day '+str(validday)+' ERO',fontsize=16)
#Set up the legend
line_label=[]
line_str=[];
leg_nam = ['BS','AuROC']
colorlist = ["blue","red"] 
markerlist = ['x','x']   
for x in range(0,len(leg_nam)):
    line_label = np.hstack((line_label, mpl.lines.Line2D(range(1), range(1), color=colorlist[x], linestyle='None', marker=markerlist[x], markersize=7)))
    line_str   = np.hstack((line_str, leg_nam[x]))
first_legend=plt.legend(line_label, line_str, fontsize=12, numpoints=1, loc=2, framealpha=1)
ax2 = plt.gca().add_artist(first_legend)
plt.savefig(FIG_PATH+'/'+GRIB_PATH_DES+'_issuancetime_BSandAuROC_vday'+str(int(validday))+'.png', bbox_inches='tight',dpi=200)
plt.close()     
        
#####CREATE BULK VERIFICATION STATISTICS BY THRESHOLD FOR VERIFICATION######
fig = plt.figure(figsize=(8,8))
ax = fig.add_axes([0.1,0.1,0.8,0.8])
plt.bar(np.arange(4)-0.15,(PCT_data_ST4gFFG[6:-1:3]/(PCT_data_ST4gFFG[6:-1:3]+PCT_data_ST4gFFG[7:-1:3]))*100,align='center',width=0.3,color='blue')
plt.bar(np.arange(4)+0.15,(PCT_data_ALL[6:-1:3]/(PCT_data_ALL[6:-1:3]+PCT_data_ALL[7:-1:3]))*100,align='center',width=0.3,color='orange')
#Pass line instances to a legend
line_label=[]
line_str=[];
leg_nam = ['FFG Only','FFG, ARI, USGS, MPING, and LSRs']
colorlist = ["blue","orange"]    
for x in range(0,len(leg_nam)):
    line_label = np.hstack((line_label, mpl.lines.Line2D(range(1), range(1), color=colorlist[x], linestyle='None', marker='s', markersize=7)))
    line_str   = np.hstack((line_str, leg_nam[x]))
first_legend=plt.legend(line_label, line_str, fontsize=12, numpoints=1, loc=2, framealpha=1)
ax2 = plt.gca().add_artist(first_legend)
#Plot remainder of figure
plt.plot([-0.4,0.4],[5,5],'g',linewidth=3)
plt.plot([-0.4,0.4],[10,10],'r',linewidth=3)
plt.plot([0.6,1.4],[10,10],'g',linewidth=3)
plt.plot([0.6,1.4],[20,20],'r',linewidth=3)
plt.plot([1.6,2.4],[20,20],'g',linewidth=3)
plt.plot([1.6,2.4],[50,50],'r',linewidth=3)
plt.plot([2.6,3.4],[50,50],'g',linewidth=3)
plt.plot([2.6,3.4],[99.7,99.7],'r',linewidth=3)
plt.xticks(np.arange(4), ERO_plotcat[0:],fontsize=14)
plt.ylabel('ERO Category',fontsize=14)
plt.ylabel('Average Probability (%)',fontsize=14)
plt.title('Day '+str(int(validday))+' ERO Verification \n Valid Between '+yrmondayhr_beg[:-2]+' and '+yrmondayhr_end[:-2],fontsize=16)
plt.ylim((0,100))
plt.show()
plt.savefig(FIG_PATH+'/'+GRIB_PATH_DES+'_ERO_bycat_vday'+str(int(validday))+'.png', bbox_inches='tight',dpi=200)
plt.close() 

######FOR THE MOST RECENT 7 DAYS, CREATE VERIFICATION AND PRACTICALLY PERFECT PLOTS##########
for days in range(0,len(date_s_last7)):
    
    if validday == 1 and float(vhr_last7[days]) > 12:
        vhr_s = vhr_last7[days]
        vday_s = date_s_last7[days][0:-2]
    elif validday == 1 and float(vhr_last7[days]) < 9:
        vhr_s = vhr_last7[days]
        vday_s = date_e_last7[days][0:-2]
    else:
        vhr_s = '12'
        vday_s = date_s_last7[days][0:-2]
    
    #First plot includes ERO and verification    
    fig = plt.figure(figsize=(8,8))
    ax = fig.add_axes([0.1,0.1,0.8,0.8])
    m = Basemap(llcrnrlon=latlon_dims[0], llcrnrlat=latlon_dims[1], urcrnrlon=latlon_dims[2],urcrnrlat=latlon_dims[3],resolution='l',projection='merc')
    # draw coastlines, state and country boundaries, edge of map.
    m.drawcoastlines(linewidth=0.5)
    m.drawstates(linewidth=0.5)
    m.drawcountries(linewidth=0.5)
    # draw parallels and meridians
    m.drawparallels(np.arange(0,90,5),labels=[1,0,0,0],fontsize=12,linewidth=0.5)#labels=[left,right,top,bottom]
    m.drawmeridians(np.arange(-180,0,10),labels=[0,0,0,1],fontsize=12,linewidth=0.5) #labels=[left,right,top,bottom]
    props = dict(boxstyle='round', facecolor='wheat', alpha=1)

    leg_mar = []
    leg_nam = []
    leg_col = []
    try:
        m.scatter(lon[ARI_last7[:,:,days]==1], lat[ARI_last7[:,:,days]==1],color='red',marker='^',s=5,latlon=True,zorder=2)  
        leg_mar = np.append(leg_mar,'^')
        leg_nam = np.append(leg_nam,'ST4 > ARI')
        leg_col = np.append(leg_col,'red')    
    except IndexError:
        pass
    try:
        m.scatter(np.concatenate((USGS_lon_last7[days],USGS_lon_last7[days],USGS_lon_last7[days])), \
            np.concatenate((USGS_lat_last7[days],USGS_lat_last7[days],USGS_lat_last7[days])), \
            color='#9e42f4',marker='d',s=5,latlon=True,zorder=2)
        leg_mar = np.append(leg_mar,'d')
        leg_nam = np.append(leg_nam,'USGS')
        leg_col = np.append(leg_col,'#9e42f4')
    except IndexError:
        pass
    try:
        m.scatter(np.concatenate((LSRFLASH_lon_last7[days],LSRFLASH_lon_last7[days],LSRFLASH_lon_last7[days])), \
            np.concatenate((LSRFLASH_lat_last7[days],LSRFLASH_lat_last7[days],LSRFLASH_lat_last7[days])), \
            color='#38F9DA',marker='s',s=5,latlon=True,zorder=2)
        leg_mar = np.append(leg_mar,'s')
        leg_nam = np.append(leg_nam,'LSR Flash')
        leg_col = np.append(leg_col,'#38F9DA')     
    except IndexError:
        pass
    try:
        m.scatter(np.concatenate((LSRREG_lon_last7[days],LSRREG_lon_last7[days],LSRREG_lon_last7[days])), \
            np.concatenate((LSRREG_lat_last7[days],LSRREG_lat_last7[days],LSRREG_lat_last7[days])), \
            color='#0a95ab',marker='s',s=5,latlon=True,zorder=2)
        leg_mar = np.append(leg_mar,'s')
        leg_nam = np.append(leg_nam,'LSR Regular')
        leg_col = np.append(leg_col,'#0a95ab')     
    except IndexError:
        pass
    try:
        m.scatter(np.concatenate((MPING_lon_last7[days],MPING_lon_last7[days],MPING_lon_last7[days])), \
            np.concatenate((MPING_lat_last7[days],MPING_lat_last7[days],MPING_lat_last7[days])), \
            color='#6495ED',marker='*',s=5,latlon=True,zorder=2)
        leg_mar = np.append(leg_mar,'*')
        leg_nam = np.append(leg_nam,'MPING')
        leg_col = np.append(leg_col,'#6495ED')   
    except IndexError:
        pass

    m.contourf(lon, lat, ST4gFFG_last7[:,:,days], latlon=True, levels = [0,0.5,1], colors=('w','b'),zorder=1)

    if np.sum(ERO_MRGL_last7[:,:,days] == 1) > 0:
        cs = m.contour(lon, lat, ERO_MRGL_last7[:,:,days]==1, latlon=True, antialiased=False, colors='green',linewidths=0.8)
    if np.sum(ERO_SLGT_last7[:,:,days] == 1) > 0:
        cs = m.contour(lon, lat, ERO_SLGT_last7[:,:,days]==1, latlon=True, antialiased=False, colors='orange',linewidths=0.8)
    if np.sum(ERO_MDT_last7 [:,:,days] == 1)  > 0:
        cs = m.contour(lon, lat, ERO_MDT_last7[:,:,days] ==1, latlon=True, antialiased=False, colors='maroon',linewidths=0.8)
    if np.sum(ERO_HIGH_last7[:,:,days] == 1) > 0:
        cs = m.contour(lon, lat, ERO_HIGH_last7[:,:,days]==1, latlon=True, antialiased=False, colors='magenta',linewidths=0.8)
        
    #Pass line instances to a legend
    line_label=[]
    line_str=[]
    leg_mar = np.append(leg_mar,['o','_','_','_','_'])
    leg_nam = np.append(leg_nam,['ST4 > FFG','Marginal','Slight','Moderate','High'])
    leg_col = np.append(leg_col,['blue','green','orange','maroon','magenta'])

    for x in range(0,len(leg_nam)):
        line_label = np.hstack((line_label, mpl.lines.Line2D(range(1), range(1), color=leg_col[x], linestyle='None', marker=leg_mar[x], markersize=7)))
        line_str   = np.hstack((line_str, leg_nam[x]))
        
    first_legend=plt.legend(line_label, line_str, fontsize=6, numpoints=1, loc=3, framealpha=1)
    ax2 = plt.gca().add_artist(first_legend)
    
    #Create the title
    ax.set_title('WPC Day '+str(int(validday))+' ERO With ST4 > FFG Verification: Issued '+vhr_last7[days]+' UTC \n Valid: '+vhr_s+' UTC on '+vday_s+' to '+ \
        date_e_last7[days][-2:]+' UTC on '+date_e_last7[days][0:-2],fontsize=14)
    
    plt.savefig(FIG_PATH+'/daybyday/'+GRIB_PATH_DES+'_EROwST4gFFG_'+vday_s+vhr_s+'_to_'+date_e_last7[days]+'_vday'+str(int(validday))+ \
        '_vhr'+vhr_s+'.png', bbox_inches='tight',dpi=200)
    plt.close() 

    #Transfer the day by day files to ftp site
    subprocess.call('scp '+FIG_PATH+'/daybyday/'+GRIB_PATH_DES+'_EROwST4gFFG_'+vday_s+vhr_s+'_to_'+date_e_last7[days]+'_vday'+str(int(validday))+ \
        '_vhr'+vhr_s+'.png hpc@vm-lnx-rzdm05:/home/people/hpc/www/htdocs/verification/ero_verif/images/daybyday/', \
        stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'), shell=True)
        
    #Second plot only shows verification
    fig = plt.figure(figsize=(8,8))
    ax = fig.add_axes([0.1,0.1,0.8,0.8])
    m = Basemap(llcrnrlon=latlon_dims[0], llcrnrlat=latlon_dims[1], urcrnrlon=latlon_dims[2],urcrnrlat=latlon_dims[3],resolution='l',projection='merc')
    # draw coastlines, state and country boundaries, edge of map.
    m.drawcoastlines(linewidth=0.5)
    m.drawstates(linewidth=0.5)
    m.drawcountries(linewidth=0.5)
    # draw parallels and meridians
    m.drawparallels(np.arange(0,90,5),labels=[1,0,0,0],fontsize=12,linewidth=0.5)#labels=[left,right,top,bottom]
    m.drawmeridians(np.arange(-180,0,10),labels=[0,0,0,1],fontsize=12,linewidth=0.5) #labels=[left,right,top,bottom]
    props = dict(boxstyle='round', facecolor='wheat', alpha=1)

    leg_mar = []
    leg_nam = []
    leg_col = []
    try:
        m.scatter(lon[ARI_last7[:,:,days]==1], lat[ARI_last7[:,:,days]==1],color='red',marker='^',s=5,latlon=True,zorder=2)  
        leg_mar = np.append(leg_mar,'^')
        leg_nam = np.append(leg_nam,'ST4 > ARI')
        leg_col = np.append(leg_col,'red')    
    except IndexError:
        pass
    try:
        m.scatter(np.concatenate((USGS_lon_last7[days],USGS_lon_last7[days],USGS_lon_last7[days])), \
            np.concatenate((USGS_lat_last7[days],USGS_lat_last7[days],USGS_lat_last7[days])), \
            color='#9e42f4',marker='d',s=5,latlon=True,zorder=2)
        leg_mar = np.append(leg_mar,'d')
        leg_nam = np.append(leg_nam,'USGS')
        leg_col = np.append(leg_col,'#9e42f4')
    except IndexError:
        pass
    try:
        m.scatter(np.concatenate((LSRFLASH_lon_last7[days],LSRFLASH_lon_last7[days],LSRFLASH_lon_last7[days])), \
            np.concatenate((LSRFLASH_lat_last7[days],LSRFLASH_lat_last7[days],LSRFLASH_lat_last7[days])), \
            color='#38F9DA',marker='s',s=5,latlon=True,zorder=2)
        leg_mar = np.append(leg_mar,'s')
        leg_nam = np.append(leg_nam,'LSR Flash')
        leg_col = np.append(leg_col,'#38F9DA')     
    except IndexError:
        pass
    try:
        m.scatter(np.concatenate((LSRREG_lon_last7[days],LSRREG_lon_last7[days],LSRREG_lon_last7[days])), \
            np.concatenate((LSRREG_lat_last7[days],LSRREG_lat_last7[days],LSRREG_lat_last7[days])), \
            color='#38F9DA',marker='x',s=5,latlon=True,zorder=2)
        leg_mar = np.append(leg_mar,'x')
        leg_nam = np.append(leg_nam,'LSR Regular')
        leg_col = np.append(leg_col,'#38F9DA')     
    except IndexError:
        pass
    try:
        m.scatter(np.concatenate((MPING_lon_last7[days],MPING_lon_last7[days],MPING_lon_last7[days])), \
            np.concatenate((MPING_lat_last7[days],MPING_lat_last7[days],MPING_lat_last7[days])), \
            color='#6495ED',marker='*',s=5,latlon=True,zorder=2)
        leg_mar = np.append(leg_mar,'*')
        leg_nam = np.append(leg_nam,'MPING')
        leg_col = np.append(leg_col,'#6495ED')   
    except IndexError:
        pass

    m.contourf(lon, lat, ST4gFFG_last7[:,:,days], latlon=True, levels = [0,0.5,1], colors=('w','b'),zorder=1)

    #Pass line instances to a legend
    line_label=[]
    line_str=[]
    leg_mar = np.append(leg_mar,['o'])
    leg_nam = np.append(leg_nam,['ST4 > FFG'])
    leg_col = np.append(leg_col,['blue'])

    for x in range(0,len(leg_nam)):
        line_label = np.hstack((line_label, mpl.lines.Line2D(range(1), range(1), color=leg_col[x], linestyle='None', marker=leg_mar[x], markersize=7)))
        line_str   = np.hstack((line_str, leg_nam[x]))
        
    first_legend=plt.legend(line_label, line_str, fontsize=6, numpoints=1, loc=3, framealpha=1)
    ax2 = plt.gca().add_artist(first_legend)
    
    #Create the title
    ax.set_title('WPC Day '+str(int(validday))+' Verification Only \n Valid: '+vhr_s+' UTC on '+vday_s+' to '+ \
        date_e_last7[days][-2:]+' UTC on '+date_e_last7[days][0:-2],fontsize=14)
        
    plt.savefig(FIG_PATH+'/daybyday/'+GRIB_PATH_DES+'_ST4gFFG_'+vday_s+vhr_s+'_to_'+date_e_last7[days]+'_vday'+str(int(validday))+ \
        '_vhr'+vhr_s+'.png', bbox_inches='tight',dpi=200)
    plt.close() 

    #Transfer the day by day files to ftp site
    subprocess.call('scp '+FIG_PATH+'/daybyday/'+GRIB_PATH_DES+'_ST4gFFG_'+vday_s+vhr_s+'_to_'+date_e_last7[days]+'_vday'+str(int(validday))+ \
        '_vhr'+vhr_s+'.png hpc@vm-lnx-rzdm05:/home/people/hpc/www/htdocs/verification/ero_verif/images/daybyday/', \
        stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'), shell=True)
        
    #Create Practically Perfect plot with ST4gFFG compared to ERO forecast
    fig = plt.figure(figsize=(8,8))
    ax = fig.add_axes([0.1,0.1,0.8,0.8])
    m = Basemap(llcrnrlon=latlon_dims[0], llcrnrlat=latlon_dims[1], urcrnrlon=latlon_dims[2],urcrnrlat=latlon_dims[3],resolution='l',projection='merc')
    # draw coastlines, state and country boundaries, edge of map.
    m.drawcoastlines(linewidth=0.5)
    m.drawstates(linewidth=0.5)
    m.drawcountries(linewidth=0.5)
    # draw parallels and meridians
    m.drawparallels(np.arange(0,90,5),labels=[1,0,0,0],fontsize=12,linewidth=0.5)#labels=[left,right,top,bottom]
    m.drawmeridians(np.arange(-180,0,10),labels=[0,0,0,1],fontsize=12,linewidth=0.5) #labels=[left,right,top,bottom]
    cs = m.contourf(lon, lat, PP_ST4gFFG_last7[:,:,days], latlon=True, levels = [0,5,10,20,50,100], colors=('w','#33fff3','#33beff','#337aff','#3c33ff'),vmin=0,vmax=100)
    cb = m.colorbar(cs,"right", ticks=[0,5,10,20,50,100], size="5%", pad="2%", extend='both')

    if np.sum(ERO_MRGL_last7[:,:,days] == 1) > 0:
        cs = m.contour(lon, lat, ERO_MRGL_last7[:,:,days]==1, latlon=True, antialiased=False, colors='green',linewidths=0.8)
    if np.sum(ERO_SLGT_last7[:,:,days] == 1) > 0:
        cs = m.contour(lon, lat, ERO_SLGT_last7[:,:,days]==1, latlon=True, antialiased=False, colors='orange',linewidths=0.8)
    if np.sum(ERO_MDT_last7 [:,:,days] == 1)  > 0:
        cs = m.contour(lon, lat, ERO_MDT_last7[:,:,days] ==1, latlon=True, antialiased=False, colors='maroon',linewidths=0.8)
    if np.sum(ERO_HIGH_last7[:,:,days] == 1) > 0:
        cs = m.contour(lon, lat, ERO_HIGH_last7[:,:,days]==1, latlon=True, antialiased=False, colors='magenta',linewidths=0.8)
        
    #Pass line instances to a legend
    line_label=[]
    line_str=[]
    leg_mar = []
    leg_nam = []
    leg_col = []
    leg_mar = np.append(leg_mar,['_','_','_','_'])
    leg_nam = np.append(leg_nam,['Marginal','Slight','Moderate','High'])
    leg_col = np.append(leg_col,['green','orange','maroon','magenta'])

    for x in range(0,len(leg_nam)):
        line_label = np.hstack((line_label, mpl.lines.Line2D(range(1), range(1), color=leg_col[x], linestyle='None', marker=leg_mar[x], markersize=7)))
        line_str   = np.hstack((line_str, leg_nam[x]))
        
    first_legend=plt.legend(line_label, line_str, fontsize=6, numpoints=1, loc=3, framealpha=1)
    ax2 = plt.gca().add_artist(first_legend)
    
    #Create the title
    ax.set_title('WPC Day '+str(int(validday))+' ERO With ST4 > FFG Based Practically Perfect: Issued '+vhr_last7[days]+' UTC \n Valid: '+vhr_s+' UTC on '+vday_s+' to '+ \
        date_e_last7[days][-2:]+' UTC on '+date_e_last7[days][0:-2],fontsize=14)
    
    plt.savefig(FIG_PATH+'/daybyday/'+GRIB_PATH_DES+'_EROwST4gFFG_PP_'+vday_s+vhr_s+'_to_'+date_e_last7[days]+'_vday'+str(int(validday))+ \
        '_vhr'+vhr_s+'.png', bbox_inches='tight',dpi=200)
    plt.close() 

    #Transfer the day by day files to ftp site
    subprocess.call('scp '+FIG_PATH+'/daybyday/'+GRIB_PATH_DES+'_EROwST4gFFG_PP_'+vday_s+vhr_s+'_to_'+date_e_last7[days]+'_vday'+str(int(validday))+ \
        '_vhr'+vhr_s+'.png hpc@vm-lnx-rzdm05:/home/people/hpc/www/htdocs/verification/ero_verif/images/daybyday/', \
        stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'), shell=True)
        
    #Create Practically Perfect plot with ALL compared to ERO forecast
    fig = plt.figure(figsize=(8,8))
    ax = fig.add_axes([0.1,0.1,0.8,0.8])
    m = Basemap(llcrnrlon=latlon_dims[0], llcrnrlat=latlon_dims[1], urcrnrlon=latlon_dims[2],urcrnrlat=latlon_dims[3],resolution='l',projection='merc')
    # draw coastlines, state and country boundaries, edge of map.
    m.drawcoastlines(linewidth=0.5)
    m.drawstates(linewidth=0.5)
    m.drawcountries(linewidth=0.5)
    # draw parallels and meridians
    m.drawparallels(np.arange(0,90,5),labels=[1,0,0,0],fontsize=12,linewidth=0.5)#labels=[left,right,top,bottom]
    m.drawmeridians(np.arange(-180,0,10),labels=[0,0,0,1],fontsize=12,linewidth=0.5) #labels=[left,right,top,bottom]
    cs = m.contourf(lon, lat, PP_ALL_last7[:,:,days], latlon=True, levels = [0,5,10,20,50,100], colors=('w','#33fff3','#33beff','#337aff','#3c33ff'),vmin=0,vmax=100)
    cb = m.colorbar(cs,"right", ticks=[0,5,10,20,50,100], size="5%", pad="2%", extend='both')

    if np.sum(ERO_MRGL_last7[:,:,days] == 1) > 0:
        cs = m.contour(lon, lat, ERO_MRGL_last7[:,:,days]==1, latlon=True, antialiased=False, colors='green',linewidths=0.8)
    if np.sum(ERO_SLGT_last7[:,:,days] == 1) > 0:
        cs = m.contour(lon, lat, ERO_SLGT_last7[:,:,days]==1, latlon=True, antialiased=False, colors='orange',linewidths=0.8)
    if np.sum(ERO_MDT_last7 [:,:,days] == 1)  > 0:
        cs = m.contour(lon, lat, ERO_MDT_last7[:,:,days] ==1, latlon=True, antialiased=False, colors='maroon',linewidths=0.8)
    if np.sum(ERO_HIGH_last7[:,:,days] == 1) > 0:
        cs = m.contour(lon, lat, ERO_HIGH_last7[:,:,days]==1, latlon=True, antialiased=False, colors='magenta',linewidths=0.8)
        
    #Pass line instances to a legend
    line_label=[]
    line_str=[]
    leg_mar = []
    leg_nam = []
    leg_col = []
    leg_mar = np.append(leg_mar,['_','_','_','_'])
    leg_nam = np.append(leg_nam,['Marginal','Slight','Moderate','High'])
    leg_col = np.append(leg_col,['green','orange','maroon','magenta'])

    for x in range(0,len(leg_nam)):
        line_label = np.hstack((line_label, mpl.lines.Line2D(range(1), range(1), color=leg_col[x], linestyle='None', marker=leg_mar[x], markersize=7)))
        line_str   = np.hstack((line_str, leg_nam[x]))
        
    first_legend=plt.legend(line_label, line_str, fontsize=6, numpoints=1, loc=3, framealpha=1)
    ax2 = plt.gca().add_artist(first_legend)
    
    #Create the title
    ax.set_title('WPC Day '+str(int(validday))+' ERO With ALL Practically Perfect: Issued '+vhr_last7[days]+' UTC \n Valid: '+vhr_s+' UTC on '+vday_s+' to '+ \
        date_e_last7[days][-2:]+' UTC on '+date_e_last7[days][0:-2],fontsize=14)
    
    plt.savefig(FIG_PATH+'/daybyday/'+GRIB_PATH_DES+'_EROwALL_PP_'+vday_s+vhr_s+'_to_'+date_e_last7[days]+'_vday'+str(int(validday))+ \
        '_vhr'+vhr_s+'.png', bbox_inches='tight',dpi=200)

    #Transfer the day by day files to ftp site
    subprocess.call('scp '+FIG_PATH+'/daybyday/'+GRIB_PATH_DES+'_EROwALL_PP_'+vday_s+vhr_s+'_to_'+date_e_last7[days]+'_vday'+str(int(validday))+ \
        '_vhr'+vhr_s+'.png hpc@vm-lnx-rzdm05:/home/people/hpc/www/htdocs/verification/ero_verif/images/daybyday/', \
        stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'), shell=True)
    plt.close() 

    #For google sites, special condition to rename most recent image with no datestring
    if days == len(date_s_last7)-1:

        #Identify the most recent daily ERO files to be displayed on the Google Site
        subprocess.call('cp  '+FIG_PATH+'/daybyday/'+GRIB_PATH_DES+'_EROwST4gFFG_'+vday_s+vhr_s+'_to_'+date_e_last7[days]+'_vday'+ \
            str(int(validday))+'_vhr'+vhr_s+'.png '+FIG_PATH+'/'+GRIB_PATH_DES+'_EROwST4gFFG_last'+'_vday'+str(int(validday))+'.png', \
            stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'), shell=True)
        subprocess.call('cp  '+FIG_PATH+'/daybyday/'+GRIB_PATH_DES+'_ST4gFFG_'+vday_s+vhr_s+'_to_'+date_e_last7[days]+'_vday'+ \
            str(int(validday))+'_vhr'+vhr_s+'.png '+FIG_PATH+'/'+GRIB_PATH_DES+'_ST4gFFG_last'+'_vday'+str(int(validday))+'.png', \
            stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'), shell=True)
        subprocess.call('cp  '+FIG_PATH+'/daybyday/'+GRIB_PATH_DES+'_EROwST4gFFG_PP_'+vday_s+vhr_s+'_to_'+date_e_last7[days]+'_vday'+ \
            str(int(validday))+'_vhr'+vhr_s+'.png '+FIG_PATH+'/'+GRIB_PATH_DES+'_EROwST4gFFG_PP_last'+'_vday'+str(int(validday))+'.png', \
            stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'), shell=True)
        subprocess.call('cp  '+FIG_PATH+'/daybyday/'+GRIB_PATH_DES+'_EROwALL_PP_'+vday_s+vhr_s+'_to_'+date_e_last7[days]+'_vday'+ \
            str(int(validday))+'_vhr'+vhr_s+'.png '+FIG_PATH+'/'+GRIB_PATH_DES+'_EROwALL_PP_last'+'_vday'+str(int(validday))+'.png', \
            stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'), shell=True)
             
######CREATE AVERAGE PROBABILITY OF BEING WITHIN A ERO DRAWN CONTOUR THROUGHOUT THE PERIOD##########
max_bound = 15
my_cmap1 = mpl.cm.get_cmap('jet')
my_cmap1.set_under('white')
values = np.linspace(0,max_bound,21)
fig = plt.figure(figsize=(8,8))
ax = fig.add_axes([0.1,0.1,0.8,0.8])
m = Basemap(llcrnrlon=latlon_dims[0], llcrnrlat=latlon_dims[1], urcrnrlon=latlon_dims[2],urcrnrlat=latlon_dims[3],resolution='l',projection='merc')
# draw coastlines, state and country boundaries, edge of map.
m.drawcoastlines(linewidth=0.5)
m.drawstates(linewidth=0.5)
m.drawcountries(linewidth=0.5)
# draw parallels and meridians
m.drawparallels(np.arange(0,90,5),labels=[1,0,0,0],fontsize=12,linewidth=0.5)#labels=[left,right,top,bottom]
m.drawmeridians(np.arange(-180,0,10),labels=[0,0,0,1],fontsize=12,linewidth=0.5) #labels=[left,right,top,bottom]
props = dict(boxstyle='round', facecolor='wheat', alpha=1)
cs = m.contourf(lon, lat, (ERO_MRGL/file_count)*100, latlon=True, levels=values, extend='both', cmap=my_cmap1, vmin=0,vmax=max_bound)
cb = m.colorbar(cs,"right", ticks=values[0::4], size="5%", pad="2%", extend='both')
ax.set_title('Day '+str(validday)+' Probability of being in a Marginal ERO Contour \n Between '+yrmondayhr_beg[0:-2]+' and '+yrmondayhr_end[0:-2])
plt.savefig(FIG_PATH+'/'+GRIB_PATH_DES+'_ERO_spatprob_MRGL_vday'+str(int(validday))+'.png', bbox_inches='tight',dpi=200)
plt.close() 

max_bound = 8
my_cmap1 = mpl.cm.get_cmap('jet')
my_cmap1.set_under('white')
values = np.linspace(0,max_bound,21)
fig = plt.figure(figsize=(8,8))
ax = fig.add_axes([0.1,0.1,0.8,0.8])
m = Basemap(llcrnrlon=latlon_dims[0], llcrnrlat=latlon_dims[1], urcrnrlon=latlon_dims[2],urcrnrlat=latlon_dims[3],resolution='l',projection='merc')
# draw coastlines, state and country boundaries, edge of map.
m.drawcoastlines(linewidth=0.5)
m.drawstates(linewidth=0.5)
m.drawcountries(linewidth=0.5)
# draw parallels and meridians
m.drawparallels(np.arange(0,90,5),labels=[1,0,0,0],fontsize=12,linewidth=0.5)#labels=[left,right,top,bottom]
m.drawmeridians(np.arange(-180,0,10),labels=[0,0,0,1],fontsize=12,linewidth=0.5) #labels=[left,right,top,bottom]
props = dict(boxstyle='round', facecolor='wheat', alpha=1)
cs = m.contourf(lon, lat, (ERO_SLGT/file_count)*100, latlon=True, levels=values, extend='both', cmap=my_cmap1, vmin=0,vmax=max_bound)
cb = m.colorbar(cs,"right", ticks=values[0::4], size="5%", pad="2%", extend='both')
ax.set_title('Day '+str(validday)+' Probability of being in a Slight ERO Contour \n Between '+yrmondayhr_beg[0:-2]+' and '+yrmondayhr_end[0:-2])
plt.savefig(FIG_PATH+'/'+GRIB_PATH_DES+'_ERO_spatprob_SLGT_vday'+str(int(validday))+'.png', bbox_inches='tight',dpi=200)
plt.close() 

max_bound = 4
my_cmap1 = mpl.cm.get_cmap('jet')
my_cmap1.set_under('white')
values = np.linspace(0,max_bound,21)
fig = plt.figure(figsize=(8,8))
ax = fig.add_axes([0.1,0.1,0.8,0.8])
m = Basemap(llcrnrlon=latlon_dims[0], llcrnrlat=latlon_dims[1], urcrnrlon=latlon_dims[2],urcrnrlat=latlon_dims[3],resolution='l',projection='merc')
# draw coastlines, state and country boundaries, edge of map.
m.drawcoastlines(linewidth=0.5)
m.drawstates(linewidth=0.5)
m.drawcountries(linewidth=0.5)
# draw parallels and meridians
m.drawparallels(np.arange(0,90,5),labels=[1,0,0,0],fontsize=12,linewidth=0.5)#labels=[left,right,top,bottom]
m.drawmeridians(np.arange(-180,0,10),labels=[0,0,0,1],fontsize=12,linewidth=0.5) #labels=[left,right,top,bottom]
props = dict(boxstyle='round', facecolor='wheat', alpha=1)
cs = m.contourf(lon, lat, (ERO_MDT/file_count)*100, latlon=True, levels=values, extend='both', cmap=my_cmap1, vmin=0,vmax=max_bound)
cb = m.colorbar(cs,"right", ticks=values[0::4], size="5%", pad="2%", extend='both')
ax.set_title('Day '+str(validday)+' Probability of being in a Moderate ERO Contour \n Between '+yrmondayhr_beg[0:-2]+' an '+yrmondayhr_end[0:-2])
plt.savefig(FIG_PATH+'/'+GRIB_PATH_DES+'_ERO_spatprob_MDT_vday'+str(int(validday))+'.png', bbox_inches='tight',dpi=200)
plt.close() 

max_bound = 1
my_cmap1 = mpl.cm.get_cmap('jet')
my_cmap1.set_under('white')
values = np.linspace(0,max_bound,21)
fig = plt.figure(figsize=(8,8))
ax = fig.add_axes([0.1,0.1,0.8,0.8])
m = Basemap(llcrnrlon=latlon_dims[0], llcrnrlat=latlon_dims[1], urcrnrlon=latlon_dims[2],urcrnrlat=latlon_dims[3],resolution='l',projection='merc')
# draw coastlines, state and country boundaries, edge of map.
m.drawcoastlines(linewidth=0.5)
m.drawstates(linewidth=0.5)
m.drawcountries(linewidth=0.5)
# draw parallels and meridians
m.drawparallels(np.arange(0,90,5),labels=[1,0,0,0],fontsize=12,linewidth=0.5)#labels=[left,right,top,bottom]
m.drawmeridians(np.arange(-180,0,10),labels=[0,0,0,1],fontsize=12,linewidth=0.5) #labels=[left,right,top,bottom]
props = dict(boxstyle='round', facecolor='wheat', alpha=1)
cs = m.contourf(lon, lat, (ERO_HIGH/file_count)*100, latlon=True, levels=values, extend='both', cmap=my_cmap1, vmin=0,vmax=max_bound)
cb = m.colorbar(cs,"right", ticks=values[0::4], size="5%", pad="2%", extend='both')
ax.set_title('Day '+str(validday)+' Probability of being in a High ERO Contour \n Between '+yrmondayhr_beg[0:-2]+' and '+yrmondayhr_end[0:-2])
plt.savefig(FIG_PATH+'/'+GRIB_PATH_DES+'_ERO_spatprob_HIGH_vday'+str(int(validday))+'.png', bbox_inches='tight',dpi=200)
plt.close() 

##One-off dummy plot displaying the frequency of ST4>FFG
#max_bound = 50
#my_cmap1 = mpl.cm.get_cmap('jet')
#my_cmap1.set_under('white')
#values = np.linspace(0,max_bound,21)
#fig = plt.figure(figsize=(8,8))
#ax = fig.add_axes([0.1,0.1,0.8,0.8])
#m = Basemap(llcrnrlon=latlon_dims[0], llcrnrlat=latlon_dims[1], urcrnrlon=latlon_dims[2],urcrnrlat=latlon_dims[3],resolution='l',projection='merc')
## draw coastlines, state and country boundaries, edge of map.
#m.drawcoastlines(linewidth=0.5)
#m.drawstates(linewidth=0.5)
#m.drawcountries(linewidth=0.5)
## draw parallels and meridians
#m.drawparallels(np.arange(0,90,5),labels=[1,0,0,0],fontsize=12,linewidth=0.5)#labels=[left,right,top,bottom]
#m.drawmeridians(np.arange(-180,0,10),labels=[0,0,0,1],fontsize=12,linewidth=0.5) #labels=[left,right,top,bottom]
#props = dict(boxstyle='round', facecolor='wheat', alpha=1)
#cs = m.contourf(lon,lat,np.nanmean(ST4gFFG_last7[::-1,:],axis=2)*100,latlon=True, levels=values, extend='both', cmap=my_cmap1, vmin=0,vmax=max_bound)
#cb = m.colorbar(cs,"right", ticks=values[0::4], size="5%", pad="2%", extend='both') 
#ax.set_title('Average Probability of ST4 > FFG Occurrences Between 20170514 and 20170822')
#plt.savefig('/usr1/wpc_cpgffh/figures/ERO/static/'+GRIB_PATH_DES+'_ST4gFFG_prob_vday'+str(int(validday))+'_NEW.png', bbox_inches='tight',dpi=200)
#plt.close()

#Copy all files to website folder at ftp://ftp.wpc.ncep.noaa.gov/erickson/ERO_verif/
subprocess.call('scp '+FIG_PATH+'*.* hpc@vm-lnx-rzdm05:/home/people/hpc/www/htdocs/verification/ero_verif/images', \
    stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'), shell=True)