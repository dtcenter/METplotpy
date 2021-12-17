#!/usr/bin/python
# -*- coding: utf-8 -*-

################################################################################################
#ONE OF THE MAIN WRAPPER SCRIPTS TO AGGREGATE THE STATISTICS CREATED IN 
#ERO_verif_s_vday{1-3}.py USING STAT ANALYSIS AND CREATE A SERIES OF PLOTS. 
#20170705 - 20171210. MJE.
#UPDATE: MODIFIED TO GUNZIP PERMANENT FILES TO SAVE HARD DRIVE SPACE. 20180409. MJE.
#UPDATE: MODIFIED TO INCREASE EFFICIENCY. 20180510. MJE.
#UPDATE: FIX ERROR ASSOCIATED WITH DAY 1 00 UTC ISSUANCES. 20180718. MJE.
#UPDATE: TO ADD CSU-MLP TO VERIFICATION AND UPDATE MET VERSION TO 8.0. 20190507. MJE.
#UPDATE: ADD 2020 CSU-MLP, REMOVE ALL OLDER CSU VERSIONS BUT THE GEFS V2017. ADD
#ADDITIONAL VERIFICATION COMPARING CSU-MLP TO ERO. ADD ADDITIONAL VERIFICATION 
#OF CSU-MLP VERSIONS AND ERO TO PP. MJE. 20200510-15.
#UPDATE: MODIFIED CODE TO REFLECT MIDPOINT GRID_STAT BINNING, BSS INSTEAD OF BS, AND NEW PP TECHNIQUE. MJE. 20201113.
#UPDATE: UPDATED CODE TO PYTHON 3. MJE. 20210224.
#UPDATE: PLOTS THAT SAVED STATS FROM 202005-PRESENT HAVE BEEN UPDATED TO 202105-PRESENT. MJE. 20210608.
################################################################################################

import pygrib
import copy
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
import matplotlib as mpl
import glob
mpl.use('Agg') #So plots can be saved in cron
import matplotlib.pyplot as plt
from scipy.io import netcdf
from netCDF4 import Dataset
from scipy import ndimage
import importlib
import cartopy.crs as ccrs                   # import projections
import cartopy.feature as cf                 # import features
sys.path.append('/export/hpc-lw-dtbdev5/merickson/code/python/ERO')
import loadAllEROData
import Make2DPlot
import cartopy_maps
importlib.reload(loadAllEROData)
importlib.reload(Make2DPlot)
importlib.reload(cartopy_maps)
sys.path.append('/export/hpc-lw-dtbdev5/merickson/code/python/MET')
import METConFigGenV100
import py2netcdf
importlib.reload(METConFigGenV100)
importlib.reload(py2netcdf)

################################################################################
#########################1)MATRIX OF VARIABLES#################################
################################################################################
MET_PATH       = '/opt/MET/METPlus4_0/bin/'                                     #Location of MET software
CON_PATH       = '/export/hpc-lw-dtbdev5/wpc_cpgffh/METv6.0/'           #Location of MET config files
GRIB_PATH      = '/export/hpc-lw-dtbdev5/wpc_cpgffh/gribs/'             #Location of model GRIB files
FIG_PATH       = '/export/hpc-lw-dtbdev5/wpc_cpgffh/figures/ERO/'       #Location for figure generation
GRIB_PATH_DES  = 'ALL'                                                  #An appended string label for the temporary directory name
latlon_dims    = [-129.8,25.0,-65.0,49.8]                               #Latitude/longitude dimensions for plotting [WLON,SLAT,ELON,NLAT]
days_back      = 365                                                    #Total days backwards to include in verification
days_back_sh   = 59                                                     #Shorter window ERO statistics
days_offset    = 0                                                      #Most current date (e.g. end of verification window)
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

os.environ["LD_LIBRARY_PATH"] ='/opt/MET/METPlus4_0/external_libs/lib:/export-5/ncosrvnfs-cp/'+ \
    'nawips2/os/linux2.6.32_x86_64/lib:/lib:/usr/lib:/export-5/ncosrvnfs-cp/nawips3/'+ \
    'os/linux2.6.32_x86_64/lib:/export/hpc-lw-dtbdev5/'+ \
    'merickson/Canopy/appdata/canopy-1.7.2.3327.rh5-x86_64/lib:/usr/lib64/openmpi/lib/'
os.environ["LIBS"] = '/opt/MET/METPlus4_0/external_libs'

#Determine the smoothing radius width
width_smo     = int((smoth_filter * 2) / (111 * grid_delta))

#Calculate radius metadata info
dia_filter = int(np.ceil(neigh_filter/(grid_delta*111)))*2
if int(dia_filter) % 2 == 0:
    dia_filter = dia_filter - 1

#Create date specific directory
GRIB_PATH_EX = GRIB_PATH+'ERO_verif/ERO_verif_day'+str(validday)+'_'+GRIB_PATH_DES+'/'

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
with np.load('/export/hpc-lw-dtbdev5/wpc_cpgffh/gribs/ERO_verif/static/ALL_noMRGL_ST4gFFGmask_del'+str(grid_delta)+'.npz') as data:
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
PCT_data_ST4gFFG   = np.full([len(PCT_metadata)+1],np.nan)
PCT_data_ALL       = np.full([len(PCT_metadata)+1],np.nan)
if validday == 2 or validday == 3:
    PCT_data_CSUop2017 = np.full([len(PCT_metadata)+1],np.nan)
PCT_data_CSUop2020 = np.full([len(PCT_metadata)+1],np.nan)

####Create Stat Analysis configuration file and run stat_analysis for ERO Vs ST4gFFG
con_name_ST4gFFG      = METConFigGenV100.set_StatAnalysisConfigProb(CON_PATH,GRIB_PATH_DES,GRIB_PATH_EX,'ERO', \
    'Surface',ERO_probs_str,'ST4gFFG','Surface','>0','PCT',datetime_beg,datetime_end,gridpt_filter,'MAX_CIRCLE')   
stat_filename_ST4gFFG = GRIB_PATH_EX+GRIB_PATH_DES+'_ERO_Vs_ST4gFFG_s'+yrmondayhr_beg+'_e'+ \
    yrmondayhr_end+'_PCT'
#Gunzip/gzip needed files for stat_analysis
uni_month = np.unique([ '{:04d}'.format(pygrib.julian_to_datetime(i).year)+ \
    '{:02d}'.format(pygrib.julian_to_datetime(i).month) for i in np.arange(curdate-days_back,curdate)])
for month in uni_month:
    subprocess.call('gunzip '+GRIB_PATH_EX+'grid_stat_ST4gFFG_ERO_*'+month+'*.gz',stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'),shell=True)
subprocess.call(MET_PATH+'stat_analysis -lookin '+GRIB_PATH_EX+' -out '+stat_filename_ST4gFFG+' -config '+ \
    con_name_ST4gFFG,shell=True)
subprocess.call('gzip -f '+GRIB_PATH_EX+'grid_stat_ST4gFFG_ERO*.nc',stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'),shell=True)
subprocess.call('gzip -f '+GRIB_PATH_EX+'grid_stat_ST4gFFG_ERO*.stat',stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'),shell=True)

####Create Stat Analysis configuration file and run stat_analysis for ERO Vs ALL      
con_name_ALL      = METConFigGenV100.set_StatAnalysisConfigProb(CON_PATH,GRIB_PATH_DES,GRIB_PATH_EX,'ERO', \
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
subprocess.call('gzip -f '+GRIB_PATH_EX+'grid_stat_ALL_ERO*.nc',stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'),shell=True)
subprocess.call('gzip -f '+GRIB_PATH_EX+'grid_stat_ALL_ERO*.stat',stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'),shell=True)

###Create Stat Analysis configuration file and run stat_analysis for ERO Vs ALL 
if validday == 2 or validday == 3:
  
   #Read in CSUMLP operational GEFS from 2017
    con_name_CSUop2017      = METConFigGenV100.set_StatAnalysisConfigProb(CON_PATH,GRIB_PATH_DES,GRIB_PATH_EX,'CSUMLP_op_v2017', \
        'Surface',ERO_probs_str,'ALL','A365324','>0.0','PCT',datetime_beg,datetime_end,gridpt_filter,'MAX_CIRCLE')   
    stat_filename_CSUop2017 = GRIB_PATH_EX+GRIB_PATH_DES+'CSUMLP_op_v2017_s'+yrmondayhr_beg+'_e'+ \
        yrmondayhr_end+'_PCT'
    #Gunzip/gzip needed files for stat_analysis
    uni_month = np.unique([ '{:04d}'.format(pygrib.julian_to_datetime(i).year)+ \
        '{:02d}'.format(pygrib.julian_to_datetime(i).month) for i in np.arange(curdate-days_back,curdate)])
    for month in uni_month:
        subprocess.call('gunzip '+GRIB_PATH_EX+'grid_stat_ALL_CSUMLP_op_v2017_*'+month+'*.gz',stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'),shell=True)
    subprocess.call(MET_PATH+'stat_analysis -lookin '+GRIB_PATH_EX+' -out '+stat_filename_CSUop2017+' -config '+ \
        con_name_CSUop2017,shell=True)
    subprocess.call('gzip -f '+GRIB_PATH_EX+'grid_stat_ALL_CSUMLP_op_v2017*.nc',stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'),shell=True)
    subprocess.call('gzip -f '+GRIB_PATH_EX+'grid_stat_ALL_CSUMLP_op_v2017*.stat',stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'),shell=True)
        
#Read in CSUMLP operational GEFS from 2020
con_name_CSUop2020      = METConFigGenV100.set_StatAnalysisConfigProb(CON_PATH,GRIB_PATH_DES,GRIB_PATH_EX,'CSUMLP_op_v2020', \
    'Surface',ERO_probs_str,'ALL','A365324','>0.0','PCT',datetime_beg,datetime_end,gridpt_filter,'MAX_CIRCLE')
stat_filename_CSUop2020 = GRIB_PATH_EX+GRIB_PATH_DES+'CSUMLP_op_v2020_s'+yrmondayhr_beg+'_e'+ \
    yrmondayhr_end+'_PCT'
#Gunzip/gzip needed files for stat_analysis
uni_month = np.unique([ '{:04d}'.format(pygrib.julian_to_datetime(i).year)+ \
    '{:02d}'.format(pygrib.julian_to_datetime(i).month) for i in np.arange(curdate-days_back,curdate)])
for month in uni_month:
    subprocess.call('gunzip '+GRIB_PATH_EX+'grid_stat_ALL_CSUMLP_op_v2020_*'+month+'*.gz',stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'),shell=True)
subprocess.call(MET_PATH+'stat_analysis -lookin '+GRIB_PATH_EX+' -out '+stat_filename_CSUop2020+' -config '+ \
    con_name_CSUop2020,shell=True)
subprocess.call('gzip -f '+GRIB_PATH_EX+'grid_stat_ALL_CSUMLP_op_v2020*.nc',stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'),shell=True)
subprocess.call('gzip -f '+GRIB_PATH_EX+'grid_stat_ALL_CSUMLP_op_v2020*.stat',stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'),shell=True)

##Extract the data from the StatAnalysis file for ST4gFFG/ALL and CSU2017/2020
[PCT_data_ST4gFFG  , ERO_probs_str] = loadAllEROData.statAnalyisGatherLef(stat_filename_ST4gFFG    ,ERO_probs)
[PCT_data_ALL      , ERO_probs_str] = loadAllEROData.statAnalyisGatherLef(stat_filename_ALL        ,ERO_probs)
if validday == 2 or validday == 3:
    [PCT_data_CSUop2017, ERO_probs_str] = loadAllEROData.statAnalyisGatherLef(stat_filename_CSUop2017  ,ERO_probs)
[PCT_data_CSUop2020, ERO_probs_str] = loadAllEROData.statAnalyisGatherLef(stat_filename_CSUop2020  ,ERO_probs)

#Remove Stat Analysis files
output = subprocess.call('rm -rf '+stat_filename_ST4gFFG,stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'), shell=True)
output = subprocess.call('rm -rf '+stat_filename_ALL,stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'), shell=True)

############################################################################
#######LOAD VARIOUS ERO DATA COMPARED TO OBSERVATIONS (PROBABILISTIC)#######
############################################################################
  
###################Load BS/AuROC information from grid_stat output##########

(EvS_data,EvS_thre,EvS_yrmondayhr,EvS_vhr)    = loadAllEROData.statAnalyisSub_NEW(GRIB_PATH_EX, \
    'Surface','ERO','Surface','ST4gFFG','PSTD',['BSS','BRIER_NCL','BRIER_NCU','ROC_AUC'], \
    datetime_beg,datetime_end)
(EvA_data,EvA_thre,EvA_yrmondayhr,EvA_vhr)    = loadAllEROData.statAnalyisSub_NEW(GRIB_PATH_EX, \
    'Surface','ERO','A365324','ALL','PSTD',['BSS','BRIER_NCL','BRIER_NCU','ROC_AUC'], \
    datetime_beg,datetime_end)

#####Load short version of BS/AuROC from grid_stat output###################

(EvS_data_sh,EvS_thre_sh,EvS_yrmondayhr_sh,EvS_vhr_sh)    = loadAllEROData.statAnalyisSub_NEW(GRIB_PATH_EX, \
    'Surface','ERO','Surface','ST4gFFG','PSTD',['BSS','BRIER_NCL','BRIER_NCU','ROC_AUC'], \
    datetime.datetime(2021,5,1,0,0,0),datetime_end)
(EvA_data_sh,EvA_thre_sh,EvA_yrmondayhr_sh,EvA_vhr_sh)    = loadAllEROData.statAnalyisSub_NEW(GRIB_PATH_EX, \
    'Surface','ERO','A365324','ALL','PSTD',['BSS','BRIER_NCL','BRIER_NCU','ROC_AUC'], \
    datetime.datetime(2021,5,1,0,0,0),datetime_end)

#############################################################################
#####LOAD VARIOUS ERO DATA COMPARED TO PRACTICALLY PERFECT (DETERMINISTC)####
#############################################################################

###################Load CTC information from grid_stat output################

(EvPP_data,EvPP_thre,EvPP_yrmondayhr,EvPP_vhr)    = loadAllEROData.statAnalyisSub_NEW(GRIB_PATH_EX, \
    'Surface','ERO','Surface','PP_ALL','CTC',['TOTAL','FY_OY','FY_ON','FN_OY','FN_ON'],datetime.datetime(2021,5,1,0,0,0),datetime_end)

##############Process the CTC information from grid_stat output##############

#Isolate the thresholds associated with each element and the total unique threhsolds
thresh    = [float(i[2:]) for i in EvPP_thre[:,0]]
thresh_un = np.append(0.0,ERO_probs)
thresh_un = np.append(thresh_un,1.0)

#Initialize contingency table statistics
n          = np.zeros((len(thresh_un)))
a          = np.zeros((len(thresh_un)))
a_ref      = np.zeros((len(thresh_un)))
b          = np.zeros((len(thresh_un)))
c          = np.zeros((len(thresh_un)))
d          = np.zeros((len(thresh_un)))
hit_EvPP   = np.zeros((len(thresh_un)))
cbias_EvPP = np.zeros((len(thresh_un)))
far_EvPP   = np.zeros((len(thresh_un)))
csi_EvPP   = np.zeros((len(thresh_un)))
ets_EvPP   = np.zeros((len(thresh_un)))

#Loop through each event and threshold, properly separating contingency table metrics
for thr in range(0,len(thresh_un)): #through the unique thresholds
    for events in range(0,EvPP_data.shape[0]): #search all dates
        if thresh[events] == thresh_un[thr]:
            n[thr] = EvPP_data[events,0] + n[thr]
            a[thr] = EvPP_data[events,1] + a[thr]
            b[thr] = EvPP_data[events,2] + b[thr]
            c[thr] = EvPP_data[events,3] + c[thr]
            d[thr] = EvPP_data[events,4] + d[thr]

    #After summing the table stats, compute the metrics
    a_ref[thr] = (a[thr] + b[thr]) * (a[thr] + c[thr]) / n[thr]

    if (a[thr] + c[thr]) != 0:
        hit_EvPP[thr]   = a[thr] / (a[thr] + c[thr])
        cbias_EvPP[thr] = (a[thr] + b[thr]) / (a[thr] + c[thr])
    else:
        hit_EvPP[thr]   = np.NaN
        cbias_EvPP[thr] = np.NaN

    if (a[thr] + b[thr]) != 0:
        far_EvPP[thr] = b[thr] / (a[thr] + b[thr])
    else:
        far_EvPP[thr] = np.NaN

    if (a[thr] + b[thr] + c[thr]) != 0:
        csi_EvPP[thr] = a[thr] / (a[thr] + b[thr] + c[thr])
    else:
        csi_EvPP[thr] = np.NaN

    if (a[thr] - a_ref[thr] + b[thr] + c[thr]) != 0:
        ets_EvPP[thr] = (a[thr] - a_ref[thr]) / (a[thr] - a_ref[thr] + b[thr] + c[thr])
    else:
        ets_EvPP[thr] = np.NaN

del n
del a
del a_ref
del b
del c
del d
del EvPP_data
del EvPP_thre
del EvPP_yrmondayhr
del EvPP_vhr

############################################################################
######LOAD VARIOUS CSU COMPARED TO OBSERVATIONS (PROBABILISTIC)#############
############################################################################

##############Load the BS/AuROC information from grid_stat output###########

#CSUv2017 Operational ALL
if validday != 1:
    (C17opvA_data,C17opvA_thre,C17opvA_yrmondayhr,C17opvA_vhr)    = loadAllEROData.statAnalyisSub_NEW(GRIB_PATH_EX, \
        'Surface','CSUMLP_op_v2017','A365324','ALL','PSTD',['BSS','BRIER_NCL','BRIER_NCU','ROC_AUC'],datetime.datetime(2021,5,1,0,0,0),datetime_end)
else:
    C17opvA_data       = np.full((1,4),np.NaN) 
    C17opvA_thre       = np.full((1,4),np.NaN)
    C17opvA_yrmondayhr = np.full((1,4),np.NaN)
    C17opvA_vhr        = np.full((1,4),np.NaN)

#CSUv2020 Operational ALL
(C20opvA_data,C20opvA_thre,C20opvA_yrmondayhr,C20opvA_vhr)    = loadAllEROData.statAnalyisSub_NEW(GRIB_PATH_EX, \
    'Surface','CSUMLP_op_v2020','A365324','ALL','PSTD',['BSS','BRIER_NCL','BRIER_NCU','ROC_AUC'],datetime.datetime(2021,5,1,0,0,0),datetime_end)

#############################################################################
######LOAD VARIOUS CSU COMPARED TO PRACTICALLY PERFECT (DETERMINISTIC)#######
#############################################################################

#################Load the CTC information from grid_stat output##############
if validday != 1:
    (C17opvPP_data,C17opvPP_thre,C17opvPP_yrmondayhr,C17opvPP_vhr)    = loadAllEROData.statAnalyisSub_NEW(GRIB_PATH_EX, \
        'Surface','CSUMLP_op_v2017','Surface','PP_ALL','CTC',['TOTAL','FY_OY','FY_ON','FN_OY','FN_ON'],datetime.datetime(2021,5,1,0,0,0),datetime_end)
else:
    C17opvPP_data       = np.full((1,4),np.NaN)
    C17opvPP_thre       = np.full((1,4),np.NaN)
    C17opvPP_yrmondayhr = np.full((1,4),np.NaN)
    C17opvPP_vhr        = np.full((1,4),np.NaN)

#CSUv2020 Operational ALL
(C20opvPP_data,C20opvPP_thre,C20opvPP_yrmondayhr,C20opvPP_vhr)    = loadAllEROData.statAnalyisSub_NEW(GRIB_PATH_EX, \
    'Surface','CSUMLP_op_v2020','Surface','PP_ALL','CTC',['TOTAL','FY_OY','FY_ON','FN_OY','FN_ON'],datetime.datetime(2021,5,1,0,0,0),datetime_end)

#################Process the CTC information from grid_stat output###########

#Isolate the thresholds associated with each element and the total unique threhsolds
hit_C17opvPP   = np.zeros((len(thresh_un)))
cbias_C17opvPP = np.zeros((len(thresh_un)))
far_C17opvPP   = np.zeros((len(thresh_un)))
csi_C17opvPP   = np.zeros((len(thresh_un)))
ets_C17opvPP   = np.zeros((len(thresh_un)))

if validday != 1:

    #Convert all thresholds in the stat file to a float for comparison
    thresh         = [float(i[2:]) for i in C17opvPP_thre[:,0]]
 
    #Initialize contingency table statistics
    n              = np.zeros((len(thresh_un)))
    a              = np.zeros((len(thresh_un)))
    a_ref          = np.zeros((len(thresh_un)))
    b              = np.zeros((len(thresh_un)))
    c              = np.zeros((len(thresh_un)))
    d              = np.zeros((len(thresh_un)))

    #Loop through each event and threshold, properly separating contingency table metrics
    for thr in range(0,len(thresh_un)): #through the unique thresholds
        for events in range(0,C17opvPP_data.shape[0]): #search all dates
            if thresh[events] == thresh_un[thr]:
                n[thr] = C17opvPP_data[events,0] + n[thr]
                a[thr] = C17opvPP_data[events,1] + a[thr]
                b[thr] = C17opvPP_data[events,2] + b[thr]
                c[thr] = C17opvPP_data[events,3] + c[thr]
                d[thr] = C17opvPP_data[events,4] + d[thr]

        #After summing the table stats, compute the metrics
        a_ref[thr] = (a[thr] + b[thr]) * (a[thr] + c[thr]) / n[thr]    

        if (a[thr] + c[thr]) != 0:
            hit_C17opvPP[thr]   = a[thr] / (a[thr] + c[thr])
            cbias_C17opvPP[thr] = (a[thr] + b[thr]) / (a[thr] + c[thr])
        else:
            hit_C17opvPP[thr]   = np.NaN
            cbias_C17opvPP[thr] = np.NaN

        if (a[thr] + b[thr]) != 0:
            far_C17opvPP[thr] = b[thr] / (a[thr] + b[thr])
        else:
            far_C17opvPP[thr] = np.NaN

        if (a[thr] + b[thr] + c[thr]) != 0:
            csi_C17opvPP[thr] = a[thr] / (a[thr] + b[thr] + c[thr])
        else:
            csi_C17opvPP[thr] = np.NaN

        if (a[thr] - a_ref[thr] + b[thr] + c[thr]) != 0:
            ets_C17opvPP[thr] = (a[thr] - a_ref[thr]) / (a[thr] - a_ref[thr] + b[thr] + c[thr])
        else:
            ets_C17opvPP[thr] = np.NaN

    del n
    del a
    del a_ref
    del b
    del c
    del d
    del C17opvPP_data
    del C17opvPP_thre
    del C17opvPP_yrmondayhr
    del C17opvPP_vhr


#Isolate the thresholds associated with each element and the total unique threhsolds
thresh         = [float(i[2:]) for i in C20opvPP_thre[:,0]]

#Initialize contingency table statistics
n              = np.zeros((len(thresh_un)))
a              = np.zeros((len(thresh_un)))
a_ref          = np.zeros((len(thresh_un)))
b              = np.zeros((len(thresh_un)))
c              = np.zeros((len(thresh_un)))
d              = np.zeros((len(thresh_un)))
hit_C20opvPP   = np.zeros((len(thresh_un)))
cbias_C20opvPP = np.zeros((len(thresh_un)))
far_C20opvPP   = np.zeros((len(thresh_un)))
csi_C20opvPP   = np.zeros((len(thresh_un)))
ets_C20opvPP   = np.zeros((len(thresh_un)))

#Loop through each event and threshold, properly separating contingency table metrics
for thr in range(0,len(thresh_un)): #through the unique thresholds
    for events in range(0,C20opvPP_data.shape[0]): #search all dates
        if thresh[events] == thresh_un[thr]:
            n[thr] = C20opvPP_data[events,0] + n[thr]
            a[thr] = C20opvPP_data[events,1] + a[thr]
            b[thr] = C20opvPP_data[events,2] + b[thr]
            c[thr] = C20opvPP_data[events,3] + c[thr]
            d[thr] = C20opvPP_data[events,4] + d[thr]

    #After summing the table stats, compute the metrics
    a_ref[thr] = (a[thr] + b[thr]) * (a[thr] + c[thr]) / n[thr]

    if (a[thr] + c[thr]) != 0:
        hit_C20opvPP[thr]   = a[thr] / (a[thr] + c[thr])
        cbias_C20opvPP[thr] = (a[thr] + b[thr]) / (a[thr] + c[thr])
    else:
        hit_C20opvPP[thr]   = np.NaN
        cbias_C20opvPP[thr] = np.NaN

    if (a[thr] + b[thr]) != 0:
        far_C20opvPP[thr] = b[thr] / (a[thr] + b[thr])
    else:
        far_C20opvPP[thr] = np.NaN

    if (a[thr] + b[thr] + c[thr]) != 0:
        csi_C20opvPP[thr] = a[thr] / (a[thr] + b[thr] + c[thr])
    else:
        csi_C20opvPP[thr] = np.NaN

    if (a[thr] - a_ref[thr] + b[thr] + c[thr]) != 0:
        ets_C20opvPP[thr] = (a[thr] - a_ref[thr]) / (a[thr] - a_ref[thr] + b[thr] + c[thr])
    else:
        ets_C20opvPP[thr] = np.NaN

del n
del a
del a_ref
del b
del c
del d
del C20opvPP_data
del C20opvPP_thre
del C20opvPP_yrmondayhr
del C20opvPP_vhr

#Make2DPlot.Make2DPlot(lat,lon,'/export/hpc-lw-dtbdev5/merickson/ERO_verif/ERO_verif_day2_ALL//grid_stat_PP_ALL_ERO_s2020050412_e2020050512_vhr09_240000L_20200505_120000V_pairs.nc','OBS_PP_ALL_Surface_FULL','hpc@vm-lnx-rzdm06:/home/people/hpc/ftp/erickson/test6/','test1.png',[0.00,0.05,0.10,0.20,0.50,1.00])

####################################################################################################################
####LOAD/CALCULATE SPATIAL ERO FREQUENCY THROUGHOUT TOTAL PERIOD CONSIDERED USING MATRICES FROM statAnalyisSub######
####################################################################################################################

ERO_MRGL          = np.zeros((lat.shape[0],lat.shape[1]))
ERO_SLGT          = np.zeros((lat.shape[0],lat.shape[1]))
ERO_MDT           = np.zeros((lat.shape[0],lat.shape[1]))
ERO_HIGH          = np.zeros((lat.shape[0],lat.shape[1]))
ERO_MRGL_short    = np.zeros((lat.shape[0],lat.shape[1]))
ERO_SLGT_short    = np.zeros((lat.shape[0],lat.shape[1]))
ERO_MDT_short     = np.zeros((lat.shape[0],lat.shape[1]))
ERO_HIGH_short    = np.zeros((lat.shape[0],lat.shape[1]))
CSUop2017_MRGL    = np.zeros((lat.shape[0],lat.shape[1]))
CSUop2017_SLGT    = np.zeros((lat.shape[0],lat.shape[1]))
CSUop2017_MDT     = np.zeros((lat.shape[0],lat.shape[1]))
CSUop2017_HIGH    = np.zeros((lat.shape[0],lat.shape[1]))
CSUop2020_MRGL    = np.zeros((lat.shape[0],lat.shape[1]))
CSUop2020_SLGT    = np.zeros((lat.shape[0],lat.shape[1]))
CSUop2020_MDT     = np.zeros((lat.shape[0],lat.shape[1]))
CSUop2020_HIGH    = np.zeros((lat.shape[0],lat.shape[1]))

file_count        = 0
file_count_short  = 0
EvS_datestr       = []
EvS_datestr_short = []
#Do this for all ERO instances
for date in range(0,len(EvS_yrmondayhr)):
    for file_s in glob.glob(GRIB_PATH_EX+'grid_stat_ST4gFFG_ERO_s*'+'_e'+EvS_yrmondayhr[date]+'_vhr'+ \
        '{:02d}'.format(int(EvS_vhr[date]))+'*pairs.nc.gz'):

        print(file_s)

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
        ERO_MDT  = ERO_MDT  + temp

        temp     = (np.array(f.variables['FCST_ERO_Surface_FULL'][:])>=ERO_probs[3])*1
        temp[temp < 0] = 0
        ERO_HIGH = ERO_HIGH + temp
        
        EvS_datestr = np.append(EvS_datestr,EvS_yrmondayhr[date])
        f.close()
        
        file_count += 1 
       
#Do this for all ERO instances for a shorter time period starting 01 May 2021
EvS_yrmondayhr_short = [i for i in EvS_yrmondayhr if (not '2018' in i) and (not '2019' in i) and (not '2020' in i) and (not '202101' in i) and (not '202102' in i) and (not '202103' in i) and (not '202104' in i)]
for date in range(0,len(EvS_yrmondayhr_short)):
    for file_s in glob.glob(GRIB_PATH_EX+'grid_stat_ST4gFFG_ERO_s*'+'_e'+EvS_yrmondayhr_short[date]+'_vhr'+ \
        '{:02d}'.format(int(EvS_vhr[date]))+'*pairs.nc.gz'):

        print(file_s)

        subprocess.call('gunzip '+file_s,stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'),shell=True)
        f        = Dataset(file_s[0:-3], "a", format="NETCDF4")
        subprocess.call('gzip '+file_s[0:-3],stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'),shell=True)
        
        temp           = (np.array(f.variables['FCST_ERO_Surface_FULL'][:])>=ERO_probs[0])*1
        temp[temp < 0] = 0
        ERO_MRGL_short = ERO_MRGL_short + temp
        
        temp           = (np.array(f.variables['FCST_ERO_Surface_FULL'][:])>=ERO_probs[1])*1
        temp[temp < 0] = 0
        ERO_SLGT_short = ERO_SLGT_short + temp

        temp           = (np.array(f.variables['FCST_ERO_Surface_FULL'][:])>=ERO_probs[2])*1
        temp[temp < 0] = 0
        ERO_MDT_short  = ERO_MDT_short  + temp

        temp           = (np.array(f.variables['FCST_ERO_Surface_FULL'][:])>=ERO_probs[3])*1
        temp[temp < 0] = 0
        ERO_HIGH_short = ERO_HIGH_short + temp
        
        EvS_datestr_short = np.append(EvS_datestr_short,EvS_yrmondayhr_short[date])
        f.close()
        
        file_count_short += 1 


#Initialize matrices for CSU stuff
file_CSUop2017_count  = 0
file_CSUop2020_count  = 0
EvA_CSUop2017_datestr = []
EvA_CSUop2020_datestr = []

#for juldays in range(curdate-days_back-1,curdate,1):
for juldays in range(int(pygrib.datetime_to_julian(datetime.datetime(2021,5,1,0,0,0))),curdate,1):  
    datetime_CSU_beg = pygrib.julian_to_datetime(juldays)    
    yrmonday_CSU_beg = ''.join(['{:04d}'.format(datetime_CSU_beg.year),'{:02d}'.format(datetime_CSU_beg.month),'{:02d}'.format(datetime_CSU_beg.day)])   
    datetime_CSU_end = pygrib.julian_to_datetime(juldays+1)    
    yrmonday_CSU_end = ''.join(['{:04d}'.format(datetime_CSU_end.year),'{:02d}'.format(datetime_CSU_end.month),'{:02d}'.format(datetime_CSU_end.day)])   

    for vhr_CSU in ('00','12'):        
        if validday == 2 or validday == 3:    
            
            file_op_v2017 = GRIB_PATH_EX+'grid_stat_ALL_CSUMLP_op_v2017_s'+yrmonday_CSU_beg+'12_e'+yrmonday_CSU_end+'12_vhr'+ \
                vhr_CSU+'_240000L_'+yrmonday_CSU_end+'_120000V_pairs.nc.gz'

            try:
                #Do this for all CSU-MLP 2017 Operational instances
                subprocess.call('gunzip '+file_op_v2017,stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'),shell=True)
                f        = Dataset(file_op_v2017[0:-3], "a", format="NETCDF4")
                subprocess.call('gzip '+file_op_v2017[0:-3],stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'),shell=True)
                   
                temp     = (np.array(f.variables['FCST_CSUMLP_op_v2017_Surface_FULL'][:])>=ERO_probs[0])*1
                temp[temp < 0] = 0
                CSUop2017_MRGL = CSUop2017_MRGL + temp

                temp     = (np.array(f.variables['FCST_CSUMLP_op_v2017_Surface_FULL'][:])>=ERO_probs[1])*1
                temp[temp < 0] = 0
                CSUop2017_SLGT = CSUop2017_SLGT + temp
          
                temp     = (np.array(f.variables['FCST_CSUMLP_op_v2017_Surface_FULL'][:])>=ERO_probs[2])*1
                temp[temp < 0] = 0
                CSUop2017_MDT  = CSUop2017_MDT  + temp
            
                temp     = (np.array(f.variables['FCST_CSUMLP_op_v2017_Surface_FULL'][:])>=ERO_probs[3])*1
                temp[temp < 0] = 0
                CSUop2017_HIGH = CSUop2017_HIGH + temp
    
                EvA_CSUop2017_datestr = np.append(EvA_CSUop2017_datestr,vhr_CSU)
                f.close()
                    
                file_CSUop2017_count += 1 
            except IOError:
                pass

        if vhr_CSU == '00':                     
            try:

                if validday == 1:
                    file_op_v2020 = GRIB_PATH_EX+'grid_stat_ALL_CSUMLP_op_v2020_s'+yrmonday_CSU_beg+'12_e'+yrmonday_CSU_end+'12_vhr'+ \
                        '09_240000L_'+yrmonday_CSU_end+'_120000V_pairs.nc.gz'
                else:
                    file_op_v2020 = GRIB_PATH_EX+'grid_stat_ALL_CSUMLP_op_v2020_s'+yrmonday_CSU_beg+'12_e'+yrmonday_CSU_end+'12_vhr'+ \
                        '00_240000L_'+yrmonday_CSU_end+'_120000V_pairs.nc.gz'

                subprocess.call('gunzip '+file_op_v2020,stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'),shell=True)
                f        = Dataset(file_op_v2020[0:-3], "a", format="NETCDF4")
                subprocess.call('gzip '+file_op_v2020[0:-3],stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'),shell=True)
                    
                temp     = (np.array(f.variables['FCST_CSUMLP_op_v2020_Surface_FULL'][:])>=ERO_probs[0])*1
                temp[temp < 0] = 0
                CSUop2020_MRGL = CSUop2020_MRGL + temp
          
                temp     = (np.array(f.variables['FCST_CSUMLP_op_v2020_Surface_FULL'][:])>=ERO_probs[1])*1
                temp[temp < 0] = 0
                CSUop2020_SLGT = CSUop2020_SLGT + temp
            
                temp     = (np.array(f.variables['FCST_CSUMLP_op_v2020_Surface_FULL'][:])>=ERO_probs[2])*1
                temp[temp < 0] = 0
                CSUop2020_MDT  = CSUop2020_MDT  + temp
            
                temp     = (np.array(f.variables['FCST_CSUMLP_op_v2020_Surface_FULL'][:])>=ERO_probs[3])*1
                temp[temp < 0] = 0
                CSUop2020_HIGH = CSUop2020_HIGH + temp
    
                EvA_CSUop2020_datestr = np.append(EvA_CSUop2020_datestr,vhr_CSU)
                f.close()
                    
                file_CSUop2020_count += 1 
            except IOError:
                pass  
                    
################################################################################################
####CONSIDER SHORTER BS/AuROC PERIOD SUBSET ON DAYS WITH A SLGT OR GREATER######################
################################################################################################

EvS_isSLGT  = []
EvS_datestr = []
#Do this for all ERO instances
for date in range(0,len(EvS_yrmondayhr)):
    for file_s in glob.glob(GRIB_PATH_EX+'grid_stat_ST4gFFG_ERO_s*'+'_e'+EvS_yrmondayhr[date]+'_vhr'+ \
        '{:02d}'.format(int(EvS_vhr[date]))+'*pairs.nc.gz'):

        subprocess.call('gunzip '+file_s,stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'),shell=True)
        f        = Dataset(file_s[0:-3], "a", format="NETCDF4")
        subprocess.call('gzip '+file_s[0:-3],stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'),shell=True)
        
        temp     = (np.array(f.variables['FCST_ERO_Surface_FULL'][:])>=ERO_probs[1])*1
        temp[temp < 0] = 0

        #Check to see if any SLGT >= 10 points exists for given issuance
        if np.nansum(temp) < 10:
            EvS_isSLGT = np.append(EvS_isSLGT,0)
        else:
            EvS_isSLGT = np.append(EvS_isSLGT,1)

        EvS_datestr = np.append(EvS_datestr,EvS_yrmondayhr[date])

EvA_isSLGT  = []
EvA_datestr = []
#Repeat only for 09 UTC instances, so that this can be compared to EvA matrices
for date in range(0,len(EvA_yrmondayhr)):
    for file_s in glob.glob(GRIB_PATH_EX+'grid_stat_ST4gFFG_ERO_s*'+'_e'+EvA_yrmondayhr[date]+'_vhr'+ \
        '{:02d}'.format(int(EvA_vhr[date]))+'*pairs.nc.gz'):

        subprocess.call('gunzip '+file_s,stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'),shell=True)
        f        = Dataset(file_s[0:-3], "a", format="NETCDF4")
        subprocess.call('gzip '+file_s[0:-3],stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'),shell=True)
        
        temp     = (np.array(f.variables['FCST_ERO_Surface_FULL'][:])>=ERO_probs[1])*1
        temp[temp < 0] = 0

        #Check to see if any SLGT >= 500 points exists for given issuance
        if np.nansum(temp) < 10:
            EvA_isSLGT = np.append(EvA_isSLGT,0)
        else:
            EvA_isSLGT = np.append(EvA_isSLGT,1)

        EvA_datestr = np.append(EvA_datestr,EvA_yrmondayhr[date])

#For EvS, if one ERO issuance was dropped for a day, all are dropped since BS/AuROC exhibit signif. daily variability
for date_u in np.unique(EvS_datestr):

    indices = [i for i in range(0,len(EvS_datestr)) if date_u ==  EvS_datestr[i]]
    if np.isnan(np.mean(EvS_data[indices,3])) or np.mean(EvS_isSLGT[indices]) != 1:
        EvS_isSLGT[indices] = 0

#Subset the EvS and EvA data
EvS_isSLGT = [i for i in range(0,len(EvS_isSLGT)) if EvS_isSLGT[i] == 1]
EvA_isSLGT = [i for i in range(0,len(EvA_isSLGT)) if EvA_isSLGT[i] == 1]

#Eliminate all ERO days without at least a MRGL
EvS_data       = EvS_data[EvS_isSLGT,:]
EvS_yrmondayhr = EvS_yrmondayhr[EvS_isSLGT]
EvS_vhr        = EvS_vhr[EvS_isSLGT]
EvA_data       = EvA_data[EvA_isSLGT,:]
EvA_yrmondayhr = EvA_yrmondayhr[EvA_isSLGT]
EvA_vhr        = EvA_vhr[EvA_isSLGT]

#Find indices within ALL that match ST4gFFG (recall ALL can only use 24 hours of data)
EvAtoEVS_ind = np.full([EvA_yrmondayhr.shape[0]],np.nan)
for fcstA in range(0,len(EvA_yrmondayhr)):
    for fcstS in range(0,len(EvS_yrmondayhr)):
        if EvA_yrmondayhr[fcstA] == EvS_yrmondayhr[fcstS] and EvA_vhr[fcstA] == EvS_vhr[fcstS]:
            EvAtoEVS_ind[fcstA] = fcstS
            
#Collect data based on vhr to determine if forecast gets better closer to valid time
EvS_BS_byhr01    = []
EvS_BS_byhr09    = []
EvS_BS_byhr15    = []
EvS_BS_byhr21    = []
EvS_AuROC_byhr01 = []
EvS_AuROC_byhr09 = []
EvS_AuROC_byhr15 = []
EvS_AuROC_byhr21 = []
sep_days = np.where(EvS_vhr == 9)[0]

for days in range(0,len(sep_days)-1):
    
    #Subset data within the same day
    data_temp       = EvS_data[sep_days[days]:sep_days[days+1],:]
    vhr_temp        = EvS_vhr[sep_days[days]:sep_days[days+1]]
    
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
                
                #A bug was fixed in MET, resulting in proper number of grid points to be considered in metadata
                try:
                    ST4gFFG_last7[:,:,cnt_ALL]  = (np.array(f.variables['OBS_ST4gFFG_Surface_FULL_MAX_'+str(dia_filter**2)+''][:])*1)
                except:
                    ST4gFFG_last7[:,:,cnt_ALL]  = (np.array(f.variables['OBS_ST4gFFG_Surface_FULL_MAX_49'][:])*1)
                    
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

                #Due to cases of accidently zipping, unzip here but keep these files unzipped
                subprocess.call('gunzip '+filename_ST4gFFG,stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'),shell=True)
                subprocess.call('gunzip '+filename_ST4gARI,stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'),shell=True)

                #Apply practically perfect to ST4gFFG and ALL
                [lat,lon,PP_ALL_last7[:,:,cnt_ALL]]     = loadAllEROData.PracticallyPerfect_NEWEST(MET_PATH,GRIB_PATH_EX,latlon_dims,grid_delta,[1,1,1,0.8,0.8],width_smo, \
                    [filename_USGS,filename_LSRFLASH,filename_LSRREG,filename_ST4gFFG,filename_ST4gARI])
                [lat,lon,PP_ST4gFFG_last7[:,:,cnt_ALL]] = loadAllEROData.PracticallyPerfect_NEWEST(MET_PATH,GRIB_PATH_EX,latlon_dims,grid_delta,[1],width_smo, \
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

                fobj = open(filename_USGS, 'r')
                line_count = 0
                for line in fobj:
                    try:
                        if line_count > 0:
                            temp_lat = np.append(temp_lat,float(line[0:line.find('-')]))
                            temp_lon = np.append(temp_lon,float(line[line.find('-'):-1]))
                        line_count += 1
                    except ValueError: #There are rare spurious instances of no negative values
                        pass
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
                fobj = open(filename_LSRFLASH, 'r')
                line_count = 0
                for line in fobj:
                    try:
                        if line_count > 0:
                            temp_lat = np.append(temp_lat,float(line[0:line.find('-')]))
                            temp_lon = np.append(temp_lon,float(line[line.find('-'):-1]))
                        line_count += 1
                    except ValueError: #There are rare spurious instances of no negative values
                        pass
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
                fobj = open(filename_LSRREG, 'r')
                line_count = 0
                for line in fobj:
                    try:
                        if line_count > 0:
                            temp_lat = np.append(temp_lat,float(line[0:line.find('-')]))
                            temp_lon = np.append(temp_lon,float(line[line.find('-'):-1]))
                        line_count += 1
                    except ValueError: #There are rare spurious instances of no negative values
                        pass
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
                fobj = open(filename_MPING, 'r')
                line_count = 0
                for line in fobj:
                    try:
                        if line_count > 0:
                            temp_lat = np.append(temp_lat,float(line[0:line.find('-')]))
                            temp_lon = np.append(temp_lon,float(line[line.find('-'):-1]))
                        line_count += 1
                    except ValueError: #There are rare spurious instances of no negative values
                        pass
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

#BS AND AuROC AVERAGED BY ISSUANCE HOUR FOR ST4gFFG AND ALL             
fig = plt.figure(figsize=(8,8))
ax1 = fig.add_axes([0.1,0.1,0.8,0.8])
ax1.plot(range(0,len(EvS_BS_byhr)), EvS_BS_byhr,'-x',linewidth=2, label='walker position', color='blue')
ax1.set_xlabel('ERO Issuance Time',fontsize=14)
print([np.nanmin(EvS_BS_byhr),np.nanmax(EvS_BS_byhr)])
ax1.set_ylim(np.nanmin(EvS_BS_byhr)-0.1,np.nanmax(EvS_BS_byhr)+0.1)
# Make the y-axis label, ticks and tick labels match the line color.
ax1.set_ylabel('Brier Skill Score', color='b',fontsize=14)
#Second part of plotyy
ax2 = ax1.twinx()
ax2.plot(range(0,len(EvS_AuROC_byhr)), EvS_AuROC_byhr,'-x',linewidth=2, label='walker position', color='red')
ax2.set_ylabel('Area Under Relative Operating Characteristic', color='r',fontsize=14)
ax2.set_ylim(np.nanmin(EvS_AuROC_byhr)-0.005,np.nanmax(EvS_AuROC_byhr)+0.005)
if validday == 1:
    plt.xticks(np.linspace(0,2,3), ['09','15','01'],fontsize=11)
else:
    plt.xticks(np.linspace(0,1,2), ['09','21'],fontsize=11)
plt.show()
plt.title('BSS and AuROC by Issuance Time for WPC Day '+str(validday)+' ERO',fontsize=16)
#Set up the legend
line_label=[]
line_str=[];
leg_nam = ['BSS','AuROC']
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

#####CREATE BULK VERIFICATION STATISTICS BY THRESHOLD FOR VERIFICATION######
fig = plt.figure(figsize=(8,8))
ax = fig.add_axes([0.1,0.1,0.8,0.8])
if validday == 2 or validday == 3:
    plt.bar(np.arange(4)-0.1, (PCT_data_CSUop2017[6:-1:3]/(PCT_data_CSUop2017[6:-1:3]+PCT_data_CSUop2017[7:-1:3]))*100,align='center',width=0.2,color='#af7ac5')
plt.bar(np.arange(4)+0.1, (PCT_data_CSUop2020[6:-1:3]/(PCT_data_CSUop2020[6:-1:3]+PCT_data_CSUop2020[7:-1:3]))*100,align='center',width=0.2,color='#0c5eed')
#Pass line instances to a legend
line_label=[]
line_str=[];
leg_nam = ['2017 CSU-MLP','2020 CSU-MLP']
colorlist = ['#af7ac5','#0c5eed']  
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
#plt.title('Day '+str(int(validday))+' CSU-MLP Verification \n Valid Between '+yrmondayhr_beg[:-2]+' and '+yrmondayhr_end[:-2],fontsize=16)
plt.title('Day '+str(int(validday))+' CSU-MLP Verification \n Valid Between '+EvS_yrmondayhr_short[0][:-2]+' and '+yrmondayhr_end[:-2],fontsize=16)
plt.ylim((0,100))
plt.show()
plt.savefig(FIG_PATH+'/'+GRIB_PATH_DES+'_CSUMLP_bycat_vday'+str(int(validday))+'.png', bbox_inches='tight',dpi=200)
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
    [fig,ax] = cartopy_maps.plot_map(lat,lon)
    leg_mar = []
    leg_nam = []
    leg_col = []
    try:
        plt.scatter(lon[ARI_last7[:,:,days]==1], lat[ARI_last7[:,:,days]==1],color='red',marker='^',s=5,zorder=2,transform=ccrs.PlateCarree())  
        leg_mar = np.append(leg_mar,'^')
        leg_nam = np.append(leg_nam,'ST4 > ARI')
        leg_col = np.append(leg_col,'red')    
    except IndexError:
        pass
    try:
        plt.scatter(np.concatenate((USGS_lon_last7[days],USGS_lon_last7[days],USGS_lon_last7[days])), \
            np.concatenate((USGS_lat_last7[days],USGS_lat_last7[days],USGS_lat_last7[days])), \
            color='#9e42f4',marker='d',s=5,zorder=2,transform=ccrs.PlateCarree())
        leg_mar = np.append(leg_mar,'d')
        leg_nam = np.append(leg_nam,'USGS')
        leg_col = np.append(leg_col,'#9e42f4')
    except IndexError:
        pass
    try:
        plt.scatter(np.concatenate((LSRFLASH_lon_last7[days],LSRFLASH_lon_last7[days],LSRFLASH_lon_last7[days])), \
            np.concatenate((LSRFLASH_lat_last7[days],LSRFLASH_lat_last7[days],LSRFLASH_lat_last7[days])), \
            color='#38F9DA',marker='s',s=5,zorder=2,transform=ccrs.PlateCarree())
        leg_mar = np.append(leg_mar,'s')
        leg_nam = np.append(leg_nam,'LSR Flash')
        leg_col = np.append(leg_col,'#38F9DA')     
    except IndexError:
        pass
    try:
        plt.scatter(np.concatenate((LSRREG_lon_last7[days],LSRREG_lon_last7[days],LSRREG_lon_last7[days])), \
            np.concatenate((LSRREG_lat_last7[days],LSRREG_lat_last7[days],LSRREG_lat_last7[days])), \
            color='#0a95ab',marker='s',s=5,zorder=2,transform=ccrs.PlateCarree())
        leg_mar = np.append(leg_mar,'s')
        leg_nam = np.append(leg_nam,'LSR Regular')
        leg_col = np.append(leg_col,'#0a95ab')     
    except IndexError:
        pass
    try:
        plt.scatter(np.concatenate((MPING_lon_last7[days],MPING_lon_last7[days],MPING_lon_last7[days])), \
            np.concatenate((MPING_lat_last7[days],MPING_lat_last7[days],MPING_lat_last7[days])), \
            color='#6495ED',marker='*',s=5,zorder=2,transform=ccrs.PlateCarree())
        leg_mar = np.append(leg_mar,'*')
        leg_nam = np.append(leg_nam,'MPING')
        leg_col = np.append(leg_col,'#6495ED')   
    except IndexError:
        pass

    plt.contourf(lon, lat, ST4gFFG_last7[:,:,days], levels = [0,0.5,1], colors=('w','b'),zorder=1,transform=ccrs.PlateCarree())

    if np.sum(ERO_MRGL_last7[:,:,days] == 1) > 0:
        cs = plt.contour(lon, lat, ERO_MRGL_last7[:,:,days]==1, antialiased=False, colors='green',linewidths=0.8,transform=ccrs.PlateCarree())
    if np.sum(ERO_SLGT_last7[:,:,days] == 1) > 0:
        cs = plt.contour(lon, lat, ERO_SLGT_last7[:,:,days]==1, antialiased=False, colors='orange',linewidths=0.8,transform=ccrs.PlateCarree())
    if np.sum(ERO_MDT_last7 [:,:,days] == 1)  > 0:
        cs = plt.contour(lon, lat, ERO_MDT_last7[:,:,days] ==1, antialiased=False, colors='maroon',linewidths=0.8,transform=ccrs.PlateCarree())
    if np.sum(ERO_HIGH_last7[:,:,days] == 1) > 0:
        cs = plt.contour(lon, lat, ERO_HIGH_last7[:,:,days]==1, antialiased=False, colors='magenta',linewidths=0.8,transform=ccrs.PlateCarree())
        
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

    #ax.set_extent([np.nanmin(lon), np.nanmax(lon), np.nanmin(lat), np.nanmax(lat)], crs=ccrs.PlateCarree())
    plt.savefig(FIG_PATH+'/daybyday/'+GRIB_PATH_DES+'_EROwST4gFFG_'+vday_s+vhr_s+'_to_'+date_e_last7[days]+'_vday'+str(int(validday))+ \
        '_vhr'+vhr_s+'.png', bbox_inches='tight',dpi=200)
    plt.close() 
    #Transfer the day by day files to ftp site
    subprocess.call('scp '+FIG_PATH+'/daybyday/'+GRIB_PATH_DES+'_EROwST4gFFG_'+vday_s+vhr_s+'_to_'+date_e_last7[days]+'_vday'+str(int(validday))+ \
        '_vhr'+vhr_s+'.png hpc@vm-lnx-rzdm05:/home/people/hpc/www/htdocs/verification/ero_verif/images/daybyday/', \
        stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'), shell=True)

    print('scp '+FIG_PATH+'/daybyday/'+GRIB_PATH_DES+'_EROwST4gFFG_'+vday_s+vhr_s+'_to_'+date_e_last7[days]+'_vday'+str(int(validday))+ \
        '_vhr'+vhr_s+'.png')
        
    #Second plot only shows verification
    [fig,ax] = cartopy_maps.plot_map(lat,lon)
    leg_mar = []
    leg_nam = []
    leg_col = []
    try:
        plt.scatter(lon[ARI_last7[:,:,days]==1], lat[ARI_last7[:,:,days]==1],color='red',marker='^',s=5,zorder=2,transform=ccrs.PlateCarree())  
        leg_mar = np.append(leg_mar,'^')
        leg_nam = np.append(leg_nam,'ST4 > ARI')
        leg_col = np.append(leg_col,'red')    
    except IndexError:
        pass
    try:
        plt.scatter(np.concatenate((USGS_lon_last7[days],USGS_lon_last7[days],USGS_lon_last7[days])), \
            np.concatenate((USGS_lat_last7[days],USGS_lat_last7[days],USGS_lat_last7[days])), \
            color='#9e42f4',marker='d',s=5,zorder=2,transform=ccrs.PlateCarree())
        leg_mar = np.append(leg_mar,'d')
        leg_nam = np.append(leg_nam,'USGS')
        leg_col = np.append(leg_col,'#9e42f4')
    except IndexError:
        pass
    try:
        plt.scatter(np.concatenate((LSRFLASH_lon_last7[days],LSRFLASH_lon_last7[days],LSRFLASH_lon_last7[days])), \
            np.concatenate((LSRFLASH_lat_last7[days],LSRFLASH_lat_last7[days],LSRFLASH_lat_last7[days])), \
            color='#38F9DA',marker='s',s=5,zorder=2,transform=ccrs.PlateCarree())
        leg_mar = np.append(leg_mar,'s')
        leg_nam = np.append(leg_nam,'LSR Flash')
        leg_col = np.append(leg_col,'#38F9DA')     
    except IndexError:
        pass
    try:
        plt.scatter(np.concatenate((LSRREG_lon_last7[days],LSRREG_lon_last7[days],LSRREG_lon_last7[days])), \
            np.concatenate((LSRREG_lat_last7[days],LSRREG_lat_last7[days],LSRREG_lat_last7[days])), \
            color='#38F9DA',marker='x',s=5,zorder=2,transform=ccrs.PlateCarree())
        leg_mar = np.append(leg_mar,'x')
        leg_nam = np.append(leg_nam,'LSR Regular')
        leg_col = np.append(leg_col,'#38F9DA')     
    except IndexError:
        pass
    try:
        plt.scatter(np.concatenate((MPING_lon_last7[days],MPING_lon_last7[days],MPING_lon_last7[days])), \
            np.concatenate((MPING_lat_last7[days],MPING_lat_last7[days],MPING_lat_last7[days])), \
            color='#6495ED',marker='*',s=5,zorder=2,transform=ccrs.PlateCarree())
        leg_mar = np.append(leg_mar,'*')
        leg_nam = np.append(leg_nam,'MPING')
        leg_col = np.append(leg_col,'#6495ED')   
    except IndexError:
        pass

    plt.contourf(lon, lat, ST4gFFG_last7[:,:,days], levels = [0,0.5,1], colors=('w','b'),zorder=1,transform=ccrs.PlateCarree())

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
    #ax.set_extent([np.nanmin(lon), np.nanmax(lon), np.nanmin(lat), np.nanmax(lat)], crs=ccrs.PlateCarree())
    plt.savefig(FIG_PATH+'/daybyday/'+GRIB_PATH_DES+'_ST4gFFG_'+vday_s+vhr_s+'_to_'+date_e_last7[days]+'_vday'+str(int(validday))+ \
        '_vhr'+vhr_s+'.png', bbox_inches='tight',dpi=200)
    plt.close() 

    #Transfer the day by day files to ftp site
    subprocess.call('scp '+FIG_PATH+'/daybyday/'+GRIB_PATH_DES+'_ST4gFFG_'+vday_s+vhr_s+'_to_'+date_e_last7[days]+'_vday'+str(int(validday))+ \
        '_vhr'+vhr_s+'*.png hpc@vm-lnx-rzdm05:/home/people/hpc/www/htdocs/verification/ero_verif/images/daybyday/', \
        stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'), shell=True)

    #Create Practically Perfect plot with ST4gFFG compared to ERO forecast
    [fig,ax] = cartopy_maps.plot_map(lat,lon)
    cs = plt.contourf(lon, lat, PP_ST4gFFG_last7[:,:,days], levels = [0,5,10,20,50,100], colors=('w','#33fff3','#33beff','#337aff','#3c33ff'),vmin=0,vmax=100,transform=ccrs.PlateCarree())
    cb = plt.colorbar(cs,ax=ax)

    if np.sum(ERO_MRGL_last7[:,:,days] == 1) > 0:
        cs = plt.contour(lon, lat, ERO_MRGL_last7[:,:,days]==1, antialiased=False, colors='green',linewidths=0.8,transform=ccrs.PlateCarree())
    if np.sum(ERO_SLGT_last7[:,:,days] == 1) > 0:
        cs = plt.contour(lon, lat, ERO_SLGT_last7[:,:,days]==1, antialiased=False, colors='orange',linewidths=0.8,transform=ccrs.PlateCarree())
    if np.sum(ERO_MDT_last7 [:,:,days] == 1)  > 0:
        cs = plt.contour(lon, lat, ERO_MDT_last7[:,:,days] ==1, antialiased=False, colors='maroon',linewidths=0.8,transform=ccrs.PlateCarree())
    if np.sum(ERO_HIGH_last7[:,:,days] == 1) > 0:
        cs = plt.contour(lon, lat, ERO_HIGH_last7[:,:,days]==1, antialiased=False, colors='magenta',linewidths=0.8,transform=ccrs.PlateCarree())
        
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
    #ax.set_extent([np.nanmin(lon), np.nanmax(lon), np.nanmin(lat), np.nanmax(lat)], crs=ccrs.PlateCarree()) 

    plt.savefig(FIG_PATH+'/daybyday/'+GRIB_PATH_DES+'_EROwST4gFFG_PP_'+vday_s+vhr_s+'_to_'+date_e_last7[days]+'_vday'+str(int(validday))+ \
        '_vhr'+vhr_s+'.png', bbox_inches='tight',dpi=200)
    plt.close() 
    
    #Transfer the day by day files to ftp site
    subprocess.call('scp '+FIG_PATH+'/daybyday/'+GRIB_PATH_DES+'_EROwST4gFFG_PP_'+vday_s+vhr_s+'_to_'+date_e_last7[days]+'_vday'+str(int(validday))+ \
        '_vhr'+vhr_s+'.png hpc@vm-lnx-rzdm05:/home/people/hpc/www/htdocs/verification/ero_verif/images/daybyday/', \
        stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'), shell=True)
    
    print('scp '+FIG_PATH+'/daybyday/'+GRIB_PATH_DES+'_EROwST4gFFG_PP_'+vday_s+vhr_s+'_to_'+date_e_last7[days]+'_vday'+str(int(validday))+ \
        '_vhr'+vhr_s+'.png')
   
    #Create Practically Perfect plot with ALL compared to ERO forecast
    [fig,ax] = cartopy_maps.plot_map(lat,lon)
    cs = plt.contourf(lon, lat, PP_ALL_last7[:,:,days], levels = [0,5,10,20,50,100], colors=('w','#33fff3','#33beff','#337aff','#3c33ff'),vmin=0,vmax=100,transform=ccrs.PlateCarree())
    cb = plt.colorbar(cs,ax=ax)
    #cb = plt.colorbar(cs,"right", ticks=[0,5,10,20,50,100], size="5%", pad="2%", extend='both')

    if np.sum(ERO_MRGL_last7[:,:,days] == 1) > 0:
        cs = plt.contour(lon, lat, ERO_MRGL_last7[:,:,days]==1, antialiased=False, colors='green',linewidths=0.8,transform=ccrs.PlateCarree())
    if np.sum(ERO_SLGT_last7[:,:,days] == 1) > 0:
        cs = plt.contour(lon, lat, ERO_SLGT_last7[:,:,days]==1, antialiased=False, colors='orange',linewidths=0.8,transform=ccrs.PlateCarree())
    if np.sum(ERO_MDT_last7 [:,:,days] == 1)  > 0:
        cs = plt.contour(lon, lat, ERO_MDT_last7[:,:,days] ==1, antialiased=False, colors='maroon',linewidths=0.8,transform=ccrs.PlateCarree())
    if np.sum(ERO_HIGH_last7[:,:,days] == 1) > 0:
        cs = plt.contour(lon, lat, ERO_HIGH_last7[:,:,days]==1, antialiased=False, colors='magenta',linewidths=0.8,transform=ccrs.PlateCarree())
        
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
    #ax.set_extent([np.nanmin(lon), np.nanmax(lon), np.nanmin(lat), np.nanmax(lat)], crs=ccrs.PlateCarree()) 

    plt.savefig(FIG_PATH+'/daybyday/'+GRIB_PATH_DES+'_EROwALL_PP_'+vday_s+vhr_s+'_to_'+date_e_last7[days]+'_vday'+str(int(validday))+ \
        '_vhr'+vhr_s+'.png', bbox_inches='tight',dpi=200)

    #Transfer the day by day files to ftp site
    subprocess.call('scp '+FIG_PATH+'/daybyday/'+GRIB_PATH_DES+'_EROwALL_PP_'+vday_s+vhr_s+'_to_'+date_e_last7[days]+'_vday'+str(int(validday))+ \
        '_vhr'+vhr_s+'.png hpc@vm-lnx-rzdm05:/home/people/hpc/www/htdocs/verification/ero_verif/images/daybyday/', \
        stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'), shell=True)
    plt.close() 

    #For google sites, special condition to rename 12z issued most recent image with no datestring
    if days == len(date_s_last7)-1:

        #Identify the most recent daily ERO files to be displayed on the Google Site
        subprocess.call('cp  '+FIG_PATH+'/daybyday/'+GRIB_PATH_DES+'_EROwST4gFFG_'+vday_s+'12_to_'+date_e_last7[days]+'_vday'+ \
            str(int(validday))+'_vhr12.png '+FIG_PATH+'/'+GRIB_PATH_DES+'_EROwST4gFFG_last'+'_vday'+str(int(validday))+'.png', \
            stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'), shell=True)
        subprocess.call('cp  '+FIG_PATH+'/daybyday/'+GRIB_PATH_DES+'_ST4gFFG_'+vday_s+'12_to_'+date_e_last7[days]+'_vday'+ \
            str(int(validday))+'_vhr12.png '+FIG_PATH+'/'+GRIB_PATH_DES+'_ST4gFFG_last'+'_vday'+str(int(validday))+'.png', \
            stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'), shell=True)
        subprocess.call('cp  '+FIG_PATH+'/daybyday/'+GRIB_PATH_DES+'_EROwST4gFFG_PP_'+vday_s+'12_to_'+date_e_last7[days]+'_vday'+ \
            str(int(validday))+'_vhr12.png '+FIG_PATH+'/'+GRIB_PATH_DES+'_EROwST4gFFG_PP_last'+'_vday'+str(int(validday))+'.png', \
            stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'), shell=True)
        subprocess.call('cp  '+FIG_PATH+'/daybyday/'+GRIB_PATH_DES+'_EROwALL_PP_'+vday_s+'12_to_'+date_e_last7[days]+'_vday'+ \
            str(int(validday))+'_vhr12.png '+FIG_PATH+'/'+GRIB_PATH_DES+'_EROwALL_PP_last'+'_vday'+str(int(validday))+'.png', \
            stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'), shell=True)                                                                                                             
                                                                         
######PLOT THE MOST RECENT 12Z ISSUANCE FOR ALL CSU-MLP, CREATE VERIFICATION AND PRACTICALLY PERFECT PLOTS##########                                                                                                                                                            
datetime_CSU_beg = pygrib.julian_to_datetime(curdate-1)    
yrmonday_CSU_beg = ''.join(['{:04d}'.format(datetime_CSU_beg.year),'{:02d}'.format(datetime_CSU_beg.month),'{:02d}'.format(datetime_CSU_beg.day)])   
datetime_CSU_end = pygrib.julian_to_datetime(curdate)    
yrmonday_CSU_end = ''.join(['{:04d}'.format(datetime_CSU_end.year),'{:02d}'.format(datetime_CSU_end.month),'{:02d}'.format(datetime_CSU_end.day)])   
        
for vhr_CSU in ['00','12']:
    if validday == 2 or validday == 3:        

        file_op_v2017 = GRIB_PATH_EX+'grid_stat_ALL_CSUMLP_op_v2017_s'+yrmonday_CSU_beg+'12_e'+yrmonday_CSU_end+'12_vhr'+ \
            vhr_CSU+'_240000L_'+yrmonday_CSU_end+'_120000V_pairs.nc.gz'
            
        #Grab the latest daily files from all versions/reforecasts           
        try:
            subprocess.call('gunzip '+file_op_v2017,stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'),shell=True)
            f        = Dataset(file_op_v2017[0:-3], "a", format="NETCDF4")
            subprocess.call('gzip '+file_op_v2017[0:-3],stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'),shell=True)
            
            CSUMLP_CSUop2017 = np.array(f.variables['FCST_CSUMLP_op_v2017_Surface_FULL'][:])
            f.close()
            
        except IOError:
            CSUMLP_CSUop2017 = np.full(lat.shape,np.nan)

    if vhr_CSU == '00':
        if validday == 1:
            file_op_v2020 = GRIB_PATH_EX+'grid_stat_ALL_CSUMLP_op_v2020_s'+yrmonday_CSU_beg+'12_e'+yrmonday_CSU_end+'12_vhr'+ \
                '09_240000L_'+yrmonday_CSU_end+'_120000V_pairs.nc.gz'
        else:
            file_op_v2020 = GRIB_PATH_EX+'grid_stat_ALL_CSUMLP_op_v2020_s'+yrmonday_CSU_beg+'12_e'+yrmonday_CSU_end+'12_vhr'+ \
                '00_240000L_'+yrmonday_CSU_end+'_120000V_pairs.nc.gz'
            
        try:
            subprocess.call('gunzip '+file_op_v2020,stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'),shell=True)
            f        = Dataset(file_op_v2020[0:-3], "a", format="NETCDF4")
            subprocess.call('gzip '+file_op_v2020[0:-3],stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'),shell=True)
           
            CSUMLP_CSUop2020 = np.array(f.variables['FCST_CSUMLP_op_v2020_Surface_FULL'][:])
            f.close()
            
        except IOError:
            CSUMLP_CSUop2020 = np.full(lat.shape,np.nan)
            
#Plot CSUv2017 Operational 

for vhr_CSU in ['00','12']:
    if validday == 2 or validday == 3:

        [fig,ax] = cartopy_maps.plot_map(lat,lon)
    
        leg_mar = []
        leg_nam = []
        leg_col = []
        try:
            plt.scatter(lon[ARI_last7[:,:,-1]==1], lat[ARI_last7[:,:,-1]==1],color='red',marker='^',s=5,zorder=2,transform=ccrs.PlateCarree())  
            leg_mar = np.append(leg_mar,'^')
            leg_nam = np.append(leg_nam,'ST4 > ARI')
            leg_col = np.append(leg_col,'red')    
        except IndexError:
            pass
        try:
            plt.scatter(np.concatenate((USGS_lon_last7[-1],USGS_lon_last7[-1],USGS_lon_last7[-1])), \
                np.concatenate((USGS_lat_last7[-1],USGS_lat_last7[-1],USGS_lat_last7[-1])), \
                color='#9e42f4',marker='d',s=5,zorder=2,transform=ccrs.PlateCarree())
            leg_mar = np.append(leg_mar,'d')
            leg_nam = np.append(leg_nam,'USGS')
            leg_col = np.append(leg_col,'#9e42f4')
        except IndexError:
            pass
        try:
            plt.scatter(np.concatenate((LSRFLASH_lon_last7[-1],LSRFLASH_lon_last7[-1],LSRFLASH_lon_last7[-1])), \
                np.concatenate((LSRFLASH_lat_last7[-1],LSRFLASH_lat_last7[-1],LSRFLASH_lat_last7[-1])), \
                color='#38F9DA',marker='s',s=5,zorder=2,transform=ccrs.PlateCarree())
            leg_mar = np.append(leg_mar,'s')
            leg_nam = np.append(leg_nam,'LSR Flash')
            leg_col = np.append(leg_col,'#38F9DA')     
        except IndexError:
            pass
        try:
            plt.scatter(np.concatenate((LSRREG_lon_last7[-1],LSRREG_lon_last7[-1],LSRREG_lon_last7[-1])), \
                np.concatenate((LSRREG_lat_last7[-1],LSRREG_lat_last7[-1],LSRREG_lat_last7[-1])), \
                color='#0a95ab',marker='s',s=5,zorder=2,transform=ccrs.PlateCarree())
            leg_mar = np.append(leg_mar,'s')
            leg_nam = np.append(leg_nam,'LSR Regular')
            leg_col = np.append(leg_col,'#0a95ab')     
        except IndexError:
            pass
        try:
            plt.scatter(np.concatenate((MPING_lon_last7[-1],MPING_lon_last7[-1],MPING_lon_last7[-1])), \
                np.concatenate((MPING_lat_last7[-1],MPING_lat_last7[-1],MPING_lat_last7[-1])), \
                color='#6495ED',marker='*',s=5,zorder=2,transform=ccrs.PlateCarree())
            leg_mar = np.append(leg_mar,'*')
            leg_nam = np.append(leg_nam,'MPING')
            leg_col = np.append(leg_col,'#6495ED')   
        except IndexError:
            pass
    
        plt.contourf(lon, lat, ST4gFFG_last7[:,:,-1], levels = [0,0.5,1], colors=('w','b'),zorder=1)
    
        if np.sum(CSUMLP_CSUop2017 >= ERO_probs[0]) > 0:
            cs = plt.contour(lon, lat, CSUMLP_CSUop2017 >= ERO_probs[0], antialiased=False, colors='green',linewidths=0.8,transform=ccrs.PlateCarree())
        if np.sum(CSUMLP_CSUop2017 >= ERO_probs[1]) > 0:
            cs = plt.contour(lon, lat, CSUMLP_CSUop2017 >= ERO_probs[1], antialiased=False, colors='orange',linewidths=0.8,transform=ccrs.PlateCarree())
        if np.sum(CSUMLP_CSUop2017 >= ERO_probs[2])  > 0:
            cs = plt.contour(lon, lat, CSUMLP_CSUop2017 >= ERO_probs[2], antialiased=False, colors='maroon',linewidths=0.8,transform=ccrs.PlateCarree())
        if np.sum(CSUMLP_CSUop2017 >= ERO_probs[3]) > 0:
            cs = plt.contour(lon, lat, CSUMLP_CSUop2017 >= ERO_probs[3], antialiased=False, colors='magenta',linewidths=0.8,transform=ccrs.PlateCarree())
            
        #Pass line instances to a legend
        line_label=[]
        line_str=[]
        leg_mar = np.append(leg_mar,['o','_','_','_','_'])
        leg_nam = np.append(leg_nam,['ST4 > FFG','CSU-MLP Marginal','CSU-MLP Slight','CSU-MLP Moderate','CSU-MLP High'])
        leg_col = np.append(leg_col,['blue','green','orange','maroon','magenta'])
    
        for x in range(0,len(leg_nam)):
            line_label = np.hstack((line_label, mpl.lines.Line2D(range(1), range(1), color=leg_col[x], linestyle='None', marker=leg_mar[x], markersize=7)))
            line_str   = np.hstack((line_str, leg_nam[x]))
            
        first_legend=plt.legend(line_label, line_str, fontsize=6, numpoints=1, loc=3, framealpha=1)
        ax2 = plt.gca().add_artist(first_legend)
        
        #Create the title
        ax.set_title('WPC Day '+str(int(validday))+' CSU-MLP v2017 Operational GEFS With Verification: Issued 12 UTC \n Valid: 12 UTC on '+yrmonday_CSU_beg+' to '+ \
            '12 UTC on '+yrmonday_CSU_end,fontsize=14)
        #ax.set_extent([np.nanmin(lon), np.nanmax(lon), np.nanmin(lat), np.nanmax(lat)], crs=ccrs.PlateCarree())
 
        plt.savefig(FIG_PATH+'/daybyday/'+GRIB_PATH_DES+'_CSUopv2017wALL_'+yrmonday_CSU_beg+'12_to_'+yrmonday_CSU_end+'12_vday'+str(int(validday))+ \
            '_vhr'+vhr_CSU+'.png', bbox_inches='tight',dpi=200)
        plt.close() 
    
        #Transfer the day by day files to ftp site
        subprocess.call('scp '+FIG_PATH+'/daybyday/'+GRIB_PATH_DES+'_CSUopv2017wALL_'+yrmonday_CSU_beg+'12_to_'+yrmonday_CSU_end+'12_vday'+str(int(validday))+ \
            '_vhr'+vhr_CSU+'.png hpc@vm-lnx-rzdm05:/home/people/hpc/www/htdocs/verification/ero_verif/images/daybyday/', \
                    stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'), shell=True)                                                                                
        #Identify the 00z daily ERO files to be displayed on the Google Site
        subprocess.call('cp  '+FIG_PATH+'/daybyday/'+GRIB_PATH_DES+'_CSUopv2017wALL_'+yrmonday_CSU_beg+'12_to_'+yrmonday_CSU_end+ \
            '12_vday'+str(int(validday))+'_vhr00.png '+FIG_PATH+'/'+GRIB_PATH_DES+'_CSUopv2017_last'+'_vday'+ \
            str(int(validday))+'.png',stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'), shell=True)
                                                                                                                                                                                                             
    if vhr_CSU == '00':
            
        #Plot CSUv2020 Operational 
        [fig,ax] = cartopy_maps.plot_map(lat,lon)
 
        leg_mar = []
        leg_nam = []
        leg_col = []
        try:
            plt.scatter(lon[ARI_last7[:,:,-1]==1], lat[ARI_last7[:,:,-1]==1],color='red',marker='^',s=5,zorder=2,transform=ccrs.PlateCarree())  
            leg_mar = np.append(leg_mar,'^')
            leg_nam = np.append(leg_nam,'ST4 > ARI')
            leg_col = np.append(leg_col,'red')    
        except IndexError:
            pass
        try:
            plt.scatter(np.concatenate((USGS_lon_last7[-1],USGS_lon_last7[-1],USGS_lon_last7[-1])), \
                np.concatenate((USGS_lat_last7[-1],USGS_lat_last7[-1],USGS_lat_last7[-1])), \
                color='#9e42f4',marker='d',s=5,zorder=2,transform=ccrs.PlateCarree())
            leg_mar = np.append(leg_mar,'d')
            leg_nam = np.append(leg_nam,'USGS')
            leg_col = np.append(leg_col,'#9e42f4')
        except IndexError:
            pass
        try:
            plt.scatter(np.concatenate((LSRFLASH_lon_last7[-1],LSRFLASH_lon_last7[-1],LSRFLASH_lon_last7[-1])), \
                np.concatenate((LSRFLASH_lat_last7[-1],LSRFLASH_lat_last7[-1],LSRFLASH_lat_last7[-1])), \
                color='#38F9DA',marker='s',s=5,zorder=2,transform=ccrs.PlateCarree())
            leg_mar = np.append(leg_mar,'s')
            leg_nam = np.append(leg_nam,'LSR Flash')
            leg_col = np.append(leg_col,'#38F9DA')     
        except IndexError:
            pass
        try:
            plt.scatter(np.concatenate((LSRREG_lon_last7[-1],LSRREG_lon_last7[-1],LSRREG_lon_last7[-1])), \
                np.concatenate((LSRREG_lat_last7[-1],LSRREG_lat_last7[-1],LSRREG_lat_last7[-1])), \
            color='#0a95ab',marker='s',s=5,zorder=2,transform=ccrs.PlateCarree())
            leg_mar = np.append(leg_mar,'s')
            leg_nam = np.append(leg_nam,'LSR Regular')
            leg_col = np.append(leg_col,'#0a95ab')     
        except IndexError:
            pass
        try:
            plt.scatter(np.concatenate((MPING_lon_last7[-1],MPING_lon_last7[-1],MPING_lon_last7[-1])), \
                np.concatenate((MPING_lat_last7[-1],MPING_lat_last7[-1],MPING_lat_last7[-1])), \
                color='#6495ED',marker='*',s=5,zorder=2,transform=ccrs.PlateCarree())
            leg_mar = np.append(leg_mar,'*')
            leg_nam = np.append(leg_nam,'MPING')
            leg_col = np.append(leg_col,'#6495ED')   
        except IndexError:
            pass
        
        plt.contourf(lon, lat, ST4gFFG_last7[:,:,-1], levels = [0,0.5,1], colors=('w','b'),zorder=1,transform=ccrs.PlateCarree())
       
        if np.sum(CSUMLP_CSUop2020 >= ERO_probs[0]) > 0:
            cs = plt.contour(lon, lat, CSUMLP_CSUop2020 >= ERO_probs[0], antialiased=False, colors='green',linewidths=0.8,transform=ccrs.PlateCarree())
        if np.sum(CSUMLP_CSUop2020 >= ERO_probs[1]) > 0:
            cs = plt.contour(lon, lat, CSUMLP_CSUop2020 >= ERO_probs[1], antialiased=False, colors='orange',linewidths=0.8,transform=ccrs.PlateCarree())
        if np.sum(CSUMLP_CSUop2020 >= ERO_probs[2])  > 0:
            cs = plt.contour(lon, lat, CSUMLP_CSUop2020 >= ERO_probs[2], antialiased=False, colors='maroon',linewidths=0.8,transform=ccrs.PlateCarree())
        if np.sum(CSUMLP_CSUop2020 >= ERO_probs[3]) > 0:
            cs = plt.contour(lon, lat, CSUMLP_CSUop2020 >= ERO_probs[3], antialiased=False, colors='magenta',linewidths=0.8,transform=ccrs.PlateCarree())
                
        #Pass line instances to a legend
        line_label=[]
        line_str=[]
        leg_mar = np.append(leg_mar,['o','_','_','_','_'])
        leg_nam = np.append(leg_nam,['ST4 > FFG','CSU-MLP Marginal','CSU-MLP Slight','CSU-MLP Moderate','CSU-MLP High'])
        leg_col = np.append(leg_col,['blue','green','orange','maroon','magenta'])
        
        for x in range(0,len(leg_nam)):
            line_label = np.hstack((line_label, mpl.lines.Line2D(range(1), range(1), color=leg_col[x], linestyle='None', marker=leg_mar[x], markersize=7)))
            line_str   = np.hstack((line_str, leg_nam[x]))
                
        first_legend=plt.legend(line_label, line_str, fontsize=6, numpoints=1, loc=3, framealpha=1)
        ax2 = plt.gca().add_artist(first_legend)
            
        #Create the title
        ax.set_title('WPC Day '+str(int(validday))+' CSU-MLP v2020 Operational GEFS With Verification: Issued 12 UTC \n Valid: 12 UTC on '+yrmonday_CSU_beg+' to '+ \
            '12 UTC on '+yrmonday_CSU_end,fontsize=14)
        #ax.set_extent([np.nanmin(lon), np.nanmax(lon), np.nanmin(lat), np.nanmax(lat)], crs=ccrs.PlateCarree())
  
        plt.savefig(FIG_PATH+'/daybyday/'+GRIB_PATH_DES+'_CSUopv2020wALL_'+yrmonday_CSU_beg+'12_to_'+yrmonday_CSU_end+'12_vday'+str(int(validday))+ \
            '_vhr'+vhr_CSU+'.png', bbox_inches='tight',dpi=200)
        plt.close() 
        
        #Transfer the day by day files to ftp site
        subprocess.call('scp '+FIG_PATH+'/daybyday/'+GRIB_PATH_DES+'_CSUopv2020wALL_'+yrmonday_CSU_beg+'12_to_'+yrmonday_CSU_end+'12_vday'+str(int(validday))+ \
            '_vhr'+vhr_CSU+'.png hpc@vm-lnx-rzdm05:/home/people/hpc/www/htdocs/verification/ero_verif/images/daybyday/', \
            stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'), shell=True)                      
                        
        #Identify the 00z daily ERO files to be displayed on the Google Site
        subprocess.call('cp  '+FIG_PATH+'/daybyday/'+GRIB_PATH_DES+'_CSUopv2020wALL_'+yrmonday_CSU_beg+'12_to_'+yrmonday_CSU_end+ \
            '12_vday'+str(int(validday))+'_vhr00.png '+FIG_PATH+'/'+GRIB_PATH_DES+'_CSUopv2020_last'+'_vday'+ \
            str(int(validday))+'.png',stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'), shell=True) 

####Plot BSS/AuROC Bulk statistics for ERO/CSU versions########
fig = plt.figure(figsize=(8,8))
ax1 = fig.add_axes([0.1,0.1,0.8,0.8])
ax1.bar(0-0.15, [np.nanmedian(EvS_data_sh[:,0])],align='center',width=0.1,color='blue')
ax1.bar(0-0.05, [np.nanmedian(EvA_data_sh[:,0])],align='center',width=0.1,color='orange')
ax1.bar(0+0.05, [np.nanmedian(C17opvA_data[:,0])],align='center',width=0.1,color='#af7ac5')
ax1.bar(0+0.15, [np.nanmedian(C20opvA_data[:,0])],align='center',width=0.1,color='#fa30f7')
ax1.set_ylim(0,0.5)
ax1.set_ylabel('Brier Skill Score',color='k')
ax2 = ax1.twinx()  #create a second axes that shares the same x-axis
ax2.bar(1-0.15, [np.nanmedian(EvS_data_sh[:,3])],align='center',width=0.1,color='blue')
ax2.bar(1-0.05, [np.nanmedian(EvA_data_sh[:,3])],align='center',width=0.1,color='orange')
ax2.bar(1+0.05, [np.nanmedian(C17opvA_data[:,3])],align='center',width=0.1,color='#af7ac5')
ax2.bar(1+0.15, [np.nanmedian(C20opvA_data[:,3])],align='center',width=0.1,color='#fa30f7')
ax2.set_ylim(0,1.15)
ax2.set_ylabel('AuROC', color='k')  # we already handled the x-label with ax1
line_label=[]
line_str=[];
leg_nam = ['ERO Vs ST4gFFG','ERO Vs ALL','2017 CSU Vs ALL','2020 CSU Vs ALL']
colorlist = ['blue','orange','#af7ac5','#fa30f7']
for x in range(0,len(leg_nam)):
    line_label = np.hstack((line_label, mpl.lines.Line2D(range(1), range(1), color=colorlist[x], linestyle='None', marker='s', markersize=7)))
    line_str   = np.hstack((line_str, leg_nam[x]))
first_legend=plt.legend(line_label, line_str, fontsize=10, numpoints=1, loc=1, framealpha=1)
ax2 = plt.gca().add_artist(first_legend)
#Adjust axis and add labels
plt.xticks(np.arange(2),['BSS','AuROC'],fontsize=12)
plt.title('Day '+str(int(validday))+' Bulk Brier Skill Score and Area Under ROC \n Valid Between '+EvS_yrmondayhr_short[0][:-2]+' and '+yrmondayhr_end[:-2],fontsize=16)
plt.show()
plt.savefig(FIG_PATH+'/'+GRIB_PATH_DES+'_bulkBSaAuROC_vday'+str(int(validday))+'.png', bbox_inches='tight',dpi=200)
plt.close()

######Mke a plot of ERO/CSU Bias by Threshold#########
fig = plt.figure(figsize=(8,8))
ax = fig.add_axes([0.1,0.1,0.8,0.8])
plt.bar(np.arange(4)-0.2, cbias_EvPP[1:-1],align='center',width=0.2,color='orange')
plt.bar(np.arange(4)+0.00, cbias_C17opvPP[1:-1],align='center',width=0.2,color='#af7ac5')
plt.bar(np.arange(4)+0.2, cbias_C20opvPP[1:-1],align='center',width=0.2,color='#fa30f7')
plt.plot([-0.5,4.5],[1,1],'k',linewidth=3)
plt.xticks(np.arange(4), ERO_plotcat[0:],fontsize=14)
plt.xlim(-0.5,3.5)
plt.ylim(0,5)
line_label=[]
line_str=[];
leg_nam = ['ERO','2017 CSU','2020 CSU']
colorlist = ['orange','#af7ac5','#fa30f7']
for x in range(0,len(leg_nam)):
    line_label = np.hstack((line_label, mpl.lines.Line2D(range(1), range(1), color=colorlist[x], linestyle='None', marker='s', markersize=7)))
    line_str   = np.hstack((line_str, leg_nam[x]))
first_legend=plt.legend(line_label, line_str, fontsize=10, numpoints=1, loc=1, framealpha=1)
ax2 = plt.gca().add_artist(first_legend)
#Adjust axis and add labels
plt.ylabel('Contingency Bias',fontsize=14)
plt.title('Day '+str(int(validday))+' Contingency Bias Compared to Practically Perfect \n Valid Between '+EvS_yrmondayhr_short[0][:-2]+' and '+yrmondayhr_end[:-2],fontsize=16)
plt.show()
plt.savefig(FIG_PATH+'/'+GRIB_PATH_DES+'_CSUMLPaEROvsPP_CB_vday'+str(int(validday))+'.png', bbox_inches='tight',dpi=200)
plt.close()

######Make a plot of ERO/CSU CSI by Threshold#########
fig = plt.figure(figsize=(8,8))
ax = fig.add_axes([0.1,0.1,0.8,0.8])
plt.bar(np.arange(4)-0.2, csi_EvPP[1:-1],align='center',width=0.2,color='orange')
plt.bar(np.arange(4)+0.00, csi_C17opvPP[1:-1],align='center',width=0.2,color='#af7ac5')
plt.bar(np.arange(4)+0.2, csi_C20opvPP[1:-1],align='center',width=0.2,color='#fa30f7')
plt.plot([-0.5,4.5],[1,1],'k',linewidth=3)
plt.xticks(np.arange(4), ERO_plotcat[0:],fontsize=14)
plt.xlim(-0.5,3.5)
plt.ylim(0,1)
line_label=[]
line_str=[];
leg_nam = ['ERO','2017 CSU','2020 CSU']
colorlist = ['orange','#af7ac5','#fa30f7']
for x in range(0,len(leg_nam)):
    line_label = np.hstack((line_label, mpl.lines.Line2D(range(1), range(1), color=colorlist[x], linestyle='None', marker='s', markersize=7)))
    line_str   = np.hstack((line_str, leg_nam[x]))
first_legend=plt.legend(line_label, line_str, fontsize=10, numpoints=1, loc=1, framealpha=1)
ax2 = plt.gca().add_artist(first_legend)
#Adjust axis and add labels
plt.ylabel('Critical Success Index',fontsize=14)
plt.title('Day '+str(int(validday))+' CSI Compared to Practically Perfect \n Valid Between '+EvS_yrmondayhr_short[0][:-2]+' and '+yrmondayhr_end[:-2],fontsize=16)
plt.show()
plt.savefig(FIG_PATH+'/'+GRIB_PATH_DES+'_CSUMLPaEROvsPP_CSI_vday'+str(int(validday))+'.png', bbox_inches='tight',dpi=200)
plt.close()

######Make a plot of ERO/CSU Hit Rate by Threshold#########
fig = plt.figure(figsize=(8,8))
ax = fig.add_axes([0.1,0.1,0.8,0.8])
plt.bar(np.arange(4)-0.2, hit_EvPP[1:-1],align='center',width=0.2,color='orange')
plt.bar(np.arange(4)+0.00, hit_C17opvPP[1:-1],align='center',width=0.2,color='#af7ac5')
plt.bar(np.arange(4)+0.2, hit_C20opvPP[1:-1],align='center',width=0.2,color='#fa30f7')
plt.plot([-0.5,4.5],[1,1],'k',linewidth=3)
plt.xticks(np.arange(4), ERO_plotcat[0:],fontsize=14)
plt.xlim(-0.5,3.5)
plt.ylim(0,1)
line_label=[]
line_str=[];
leg_nam = ['ERO','2017 CSU','2020 CSU']
colorlist = ['orange','#af7ac5','#fa30f7']
for x in range(0,len(leg_nam)):
    line_label = np.hstack((line_label, mpl.lines.Line2D(range(1), range(1), color=colorlist[x], linestyle='None', marker='s', markersize=7)))
    line_str   = np.hstack((line_str, leg_nam[x]))
first_legend=plt.legend(line_label, line_str, fontsize=10, numpoints=1, loc=1, framealpha=1)
ax2 = plt.gca().add_artist(first_legend)
#Adjust axis and add labels
plt.ylabel('Hit Rate',fontsize=14)
plt.title('Day '+str(int(validday))+' HIT Compared to Practically Perfect \n Valid Between '+EvS_yrmondayhr_short[0][:-2]+' and '+yrmondayhr_end[:-2],fontsize=16)
plt.show()
plt.savefig(FIG_PATH+'/'+GRIB_PATH_DES+'_CSUMLPaEROvsPP_HIT_vday'+str(int(validday))+'.png', bbox_inches='tight',dpi=200)
plt.close()

######Make a plot of ERO/CSU FAR by Threshold#########
fig = plt.figure(figsize=(8,8))
ax = fig.add_axes([0.1,0.1,0.8,0.8])
plt.bar(np.arange(4)-0.2, far_EvPP[1:-1],align='center',width=0.2,color='orange')
plt.bar(np.arange(4)+0.00, far_C17opvPP[1:-1],align='center',width=0.2,color='#af7ac5')
plt.bar(np.arange(4)+0.2, far_C20opvPP[1:-1],align='center',width=0.2,color='#fa30f7')
plt.plot([-0.5,4.5],[1,1],'k',linewidth=3)
plt.xticks(np.arange(4), ERO_plotcat[0:],fontsize=14)
plt.xlim(-0.5,3.5)
plt.ylim(0,1.1)
line_label=[]
line_str=[];
leg_nam = ['ERO','2017 CSU','2020 CSU']
colorlist = ['orange','#af7ac5','#fa30f7']
for x in range(0,len(leg_nam)):
    line_label = np.hstack((line_label, mpl.lines.Line2D(range(1), range(1), color=colorlist[x], linestyle='None', marker='s', markersize=7)))
    line_str   = np.hstack((line_str, leg_nam[x]))
first_legend=plt.legend(line_label, line_str, fontsize=10, numpoints=1, loc=1, framealpha=1)
ax2 = plt.gca().add_artist(first_legend)
#Adjust axis and add labels
plt.ylabel('False Alarm Ratio',fontsize=14)
plt.title('Day '+str(int(validday))+' FAR Compared to Practically Perfect \n Valid Between '+EvS_yrmondayhr_short[0][:-2]+' and '+yrmondayhr_end[:-2],fontsize=16)
plt.show()
plt.savefig(FIG_PATH+'/'+GRIB_PATH_DES+'_CSUMLPaEROvsPP_FAR_vday'+str(int(validday))+'.png', bbox_inches='tight',dpi=200)
plt.close()

######CREATE AVERAGE PROBABILITY OF BEING WITHIN A ERO DRAWN CONTOUR THROUGHOUT THE PERIOD##########
max_bound = 20
my_cmap1 = copy.copy(mpl.cm.get_cmap('jet'))
my_cmap1.set_under('white')
values = np.linspace(0,max_bound,21)
[fig,ax] = cartopy_maps.plot_map(lat,lon)
cs = plt.contourf(lon, lat, (ERO_MRGL/file_count)*100, levels=values, extend='both', cmap=my_cmap1, vmin=0,vmax=max_bound,transform=ccrs.PlateCarree())
cb = plt.colorbar(cs,ax=ax)
#cb = plt.colorbar(cs,"right", ticks=values[0::4], size="5%", pad="2%", extend='both')
ax.set_title('Day '+str(validday)+' Probability of being in a Marginal ERO Contour \n Between '+yrmondayhr_beg[0:-2]+' and '+yrmondayhr_end[0:-2])
#ax.set_extent([np.nanmin(lon), np.nanmax(lon), np.nanmin(lat), np.nanmax(lat)], crs=ccrs.PlateCarree())
plt.savefig(FIG_PATH+'/'+GRIB_PATH_DES+'_ERO_spatprob_MRGL_vday'+str(int(validday))+'.png', bbox_inches='tight',dpi=200)
plt.close() 

max_bound = 40
my_cmap1 = copy.copy(mpl.cm.get_cmap('jet'))
my_cmap1.set_under('white')
values = np.linspace(0,max_bound,21)
[fig,ax] = cartopy_maps.plot_map(lat,lon)
cs = plt.contourf(lon, lat, (ERO_MRGL_short/file_count_short)*100, levels=values, extend='both', cmap=my_cmap1, vmin=0,vmax=max_bound,transform=ccrs.PlateCarree())
cb = plt.colorbar(cs,ax=ax)
#cb = plt.colorbar(cs,"right", ticks=values[0::4], size="5%", pad="2%", extend='both')
ax.set_title('Day '+str(validday)+' Probability of being in a Marginal ERO Contour \n Between '+EvS_yrmondayhr_short[0][0:-2]+' and '+yrmondayhr_end[0:-2])
#ax.set_extent([np.nanmin(lon), np.nanmax(lon), np.nanmin(lat), np.nanmax(lat)], crs=ccrs.PlateCarree())
plt.savefig(FIG_PATH+'/'+GRIB_PATH_DES+'_ERO_spatprob_MRGL_vday'+str(int(validday))+'_SHORT.png', bbox_inches='tight',dpi=200)
plt.close() 

max_bound = 10
my_cmap1 = copy.copy(mpl.cm.get_cmap('jet'))
my_cmap1.set_under('white')
values = np.linspace(0,max_bound,21)
[fig,ax] = cartopy_maps.plot_map(lat,lon)
cs = plt.contourf(lon, lat, (ERO_SLGT/file_count)*100, levels=values, extend='both', cmap=my_cmap1, vmin=0,vmax=max_bound,transform=ccrs.PlateCarree())
cb = plt.colorbar(cs,ax=ax)
#cb = plt.colorbar(cs,"right", ticks=values[0::4], size="5%", pad="2%", extend='both')
ax.set_title('Day '+str(validday)+' Probability of being in a Slight ERO Contour \n Between '+yrmondayhr_beg[0:-2]+' and '+yrmondayhr_end[0:-2])
#ax.set_extent([np.nanmin(lon), np.nanmax(lon), np.nanmin(lat), np.nanmax(lat)], crs=ccrs.PlateCarree())
plt.savefig(FIG_PATH+'/'+GRIB_PATH_DES+'_ERO_spatprob_SLGT_vday'+str(int(validday))+'.png', bbox_inches='tight',dpi=200)
plt.close() 

max_bound = 20
my_cmap1 =copy.copy(mpl.cm.get_cmap('jet'))
my_cmap1.set_under('white')
values = np.linspace(0,max_bound,21)
[fig,ax] = cartopy_maps.plot_map(lat,lon)
cs = plt.contourf(lon, lat, (ERO_SLGT_short/file_count_short)*100, levels=values, extend='both', cmap=my_cmap1, vmin=0,vmax=max_bound,transform=ccrs.PlateCarree())
cb = plt.colorbar(cs,ax=ax)
#cb = plt.colorbar(cs,"right", ticks=values[0::4], size="5%", pad="2%", extend='both')
ax.set_title('Day '+str(validday)+' Probability of being in a Slight ERO Contour \n Between '+EvS_yrmondayhr_short[0][0:-2]+' and '+yrmondayhr_end[0:-2])
#ax.set_extent([np.nanmin(lon), np.nanmax(lon), np.nanmin(lat), np.nanmax(lat)], crs=ccrs.PlateCarree())
plt.savefig(FIG_PATH+'/'+GRIB_PATH_DES+'_ERO_spatprob_SLGT_vday'+str(int(validday))+'_SHORT.png', bbox_inches='tight',dpi=200)
plt.close() 

max_bound = 4
my_cmap1 = copy.copy(mpl.cm.get_cmap('jet'))
my_cmap1.set_under('white')
values = np.linspace(0,max_bound,21)
[fig,ax] = cartopy_maps.plot_map(lat,lon)
cs = plt.contourf(lon, lat, (ERO_MDT/file_count)*100, levels=values, extend='both', cmap=my_cmap1, vmin=0,vmax=max_bound,transform=ccrs.PlateCarree())
cb = plt.colorbar(cs,ax=ax)
#cb = plt.colorbar(cs,"right", ticks=values[0::4], size="5%", pad="2%", extend='both')
ax.set_title('Day '+str(validday)+' Probability of being in a Moderate ERO Contour \n Between '+yrmondayhr_beg[0:-2]+' an '+yrmondayhr_end[0:-2])
#ax.set_extent([np.nanmin(lon), np.nanmax(lon), np.nanmin(lat), np.nanmax(lat)], crs=ccrs.PlateCarree())
plt.savefig(FIG_PATH+'/'+GRIB_PATH_DES+'_ERO_spatprob_MDT_vday'+str(int(validday))+'.png', bbox_inches='tight',dpi=200)
plt.close() 

max_bound = 8
my_cmap1 = copy.copy(mpl.cm.get_cmap('jet'))
my_cmap1.set_under('white')
values = np.linspace(0,max_bound,21)
[fig,ax] = cartopy_maps.plot_map(lat,lon)
cs = plt.contourf(lon, lat, (ERO_MDT_short/file_count_short)*100, levels=values, extend='both', cmap=my_cmap1, vmin=0,vmax=max_bound,transform=ccrs.PlateCarree())
cb = plt.colorbar(cs,ax=ax)
#cb = plt.colorbar(cs,"right", ticks=values[0::4], size="5%", pad="2%", extend='both')
ax.set_title('Day '+str(validday)+' Probability of being in a Moderate ERO Contour \n Between '+EvS_yrmondayhr_short[0][0:-2]+' an '+yrmondayhr_end[0:-2])
#ax.set_extent([np.nanmin(lon), np.nanmax(lon), np.nanmin(lat), np.nanmax(lat)], crs=ccrs.PlateCarree())
plt.savefig(FIG_PATH+'/'+GRIB_PATH_DES+'_ERO_spatprob_MDT_vday'+str(int(validday))+'_SHORT.png', bbox_inches='tight',dpi=200)
plt.close() 

max_bound = 1
my_cmap1 = copy.copy(mpl.cm.get_cmap('jet'))
my_cmap1.set_under('white')
values = np.linspace(0,max_bound,21)
[fig,ax] = cartopy_maps.plot_map(lat,lon)
cs = plt.contourf(lon, lat, (ERO_HIGH/file_count)*100, levels=values, extend='both', cmap=my_cmap1, vmin=0,vmax=max_bound,transform=ccrs.PlateCarree())
cb = plt.colorbar(cs,ax=ax)
#cb = m.colorbar(cs,"right", ticks=values[0::4], size="5%", pad="2%", extend='both')
ax.set_title('Day '+str(validday)+' Probability of being in a High ERO Contour \n Between '+yrmondayhr_beg[0:-2]+' and '+yrmondayhr_end[0:-2])
#ax.set_extent([np.nanmin(lon), np.nanmax(lon), np.nanmin(lat), np.nanmax(lat)], crs=ccrs.PlateCarree())
plt.savefig(FIG_PATH+'/'+GRIB_PATH_DES+'_ERO_spatprob_HIGH_vday'+str(int(validday))+'.png', bbox_inches='tight',dpi=200)
plt.close() 

max_bound = 2
my_cmap1 = copy.copy(mpl.cm.get_cmap('jet'))
my_cmap1.set_under('white')
values = np.linspace(0,max_bound,21)
[fig,ax] = cartopy_maps.plot_map(lat,lon)
cs = plt.contourf(lon, lat, (ERO_HIGH_short/file_count_short)*100, levels=values, extend='both', cmap=my_cmap1, vmin=0,vmax=max_bound,transform=ccrs.PlateCarree())
cb = plt.colorbar(cs,ax=ax)
#cb = m.colorbar(cs,"right", ticks=values[0::4], size="5%", pad="2%", extend='both')
ax.set_title('Day '+str(validday)+' Probability of being in a High ERO Contour \n Between '+EvS_yrmondayhr_short[0][0:-2]+' and '+yrmondayhr_end[0:-2])
#ax.set_extent([np.nanmin(lon), np.nanmax(lon), np.nanmin(lat), np.nanmax(lat)], crs=ccrs.PlateCarree())
plt.savefig(FIG_PATH+'/'+GRIB_PATH_DES+'_ERO_spatprob_HIGH_vday'+str(int(validday))+'_SHORT.png', bbox_inches='tight',dpi=200)
plt.close()

######CREATE AVERAGE PROBABILITY OF BEING WITHIN A CSUMLP 2017 REFORECASTS CONTOUR THROUGHOUT THE PERIOD##########
if validday == 2 or validday == 3:
    
    max_bound = 40
    my_cmap1 = copy.copy(mpl.cm.get_cmap('jet'))
    my_cmap1.set_under('white')
    values = np.linspace(0,max_bound,21)
    [fig,ax] = cartopy_maps.plot_map(lat,lon)
    cs = plt.contourf(lon, lat, (CSUop2017_MRGL/file_CSUop2017_count)*100, levels=values, extend='both', cmap=my_cmap1, vmin=0,vmax=max_bound,transform=ccrs.PlateCarree())
    cb = plt.colorbar(cs,ax=ax)
    #cb = m.colorbar(cs,"right", ticks=values[0::4], size="5%", pad="2%", extend='both')
    #ax.set_title('Day '+str(validday)+' Probability of being in a Marginal CSU v2017 Operational Contour \n Between '+yrmondayhr_beg[0:-2]+' and '+yrmondayhr_end[0:-2])
    ax.set_title('Day '+str(validday)+' Probability of being in a Marginal CSU v2017 Operational Contour \n Between '+EvS_yrmondayhr_short[0][0:-2]+' and '+yrmondayhr_end[0:-2])
    #ax.set_extent([np.nanmin(lon), np.nanmax(lon), np.nanmin(lat), np.nanmax(lat)], crs=ccrs.PlateCarree())
    plt.savefig(FIG_PATH+'/'+GRIB_PATH_DES+'_CSUopv2017_spatprob_MRGL_vday'+str(int(validday))+'.png', bbox_inches='tight',dpi=200)
    plt.close() 
    
    max_bound = 20
    my_cmap1 = copy.copy(mpl.cm.get_cmap('jet'))
    my_cmap1.set_under('white')
    values = np.linspace(0,max_bound,21)
    [fig,ax] = cartopy_maps.plot_map(lat,lon)
    cs = plt.contourf(lon, lat, (CSUop2017_SLGT/file_CSUop2017_count)*100, levels=values, extend='both', cmap=my_cmap1, vmin=0,vmax=max_bound,transform=ccrs.PlateCarree())
    cb = plt.colorbar(cs,ax=ax)
    #cb = m.colorbar(cs,"right", ticks=values[0::4], size="5%", pad="2%", extend='both')
    #ax.set_title('Day '+str(validday)+' Probability of being in a Slight CSU v2017 Operational Contour \n Between '+yrmondayhr_beg[0:-2]+' and '+yrmondayhr_end[0:-2])
    ax.set_title('Day '+str(validday)+' Probability of being in a Slight CSU v2017 Operational Contour \n Between '+EvS_yrmondayhr_short[0][0:-2]+' and '+yrmondayhr_end[0:-2])
    #ax.set_extent([np.nanmin(lon), np.nanmax(lon), np.nanmin(lat), np.nanmax(lat)], crs=ccrs.PlateCarree())
    plt.savefig(FIG_PATH+'/'+GRIB_PATH_DES+'_CSUopv2017_spatprob_SLGT_vday'+str(int(validday))+'.png', bbox_inches='tight',dpi=200)
    plt.close() 
    
    max_bound = 8
    my_cmap1 = copy.copy(mpl.cm.get_cmap('jet'))
    my_cmap1.set_under('white')
    values = np.linspace(0,max_bound,21)
    [fig,ax] = cartopy_maps.plot_map(lat,lon)
    cs = plt.contourf(lon, lat, (CSUop2017_MDT/file_CSUop2017_count)*100, levels=values, extend='both', cmap=my_cmap1, vmin=0,vmax=max_bound,transform=ccrs.PlateCarree())
    cb = plt.colorbar(cs,ax=ax)
    #cb = m.colorbar(cs,"right", ticks=values[0::4], size="5%", pad="2%", extend='both')
    #ax.set_title('Day '+str(validday)+' Probability of being in a Moderate CSU v2017 Operational Contour \n Between '+yrmondayhr_beg[0:-2]+' an '+yrmondayhr_end[0:-2])
    ax.set_title('Day '+str(validday)+' Probability of being in a Moderate CSU v2017 Operational Contour \n Between '+EvS_yrmondayhr_short[0][0:-2]+' an '+yrmondayhr_end[0:-2])
    #ax.set_extent([np.nanmin(lon), np.nanmax(lon), np.nanmin(lat), np.nanmax(lat)], crs=ccrs.PlateCarree())
    plt.savefig(FIG_PATH+'/'+GRIB_PATH_DES+'_CSUopv2017_spatprob_MDT_vday'+str(int(validday))+'.png', bbox_inches='tight',dpi=200)
    plt.close() 
    
    max_bound = 2
    my_cmap1 = copy.copy(mpl.cm.get_cmap('jet'))
    my_cmap1.set_under('white')
    values = np.linspace(0,max_bound,21)
    [fig,ax] = cartopy_maps.plot_map(lat,lon)
    cs = plt.contourf(lon, lat, (CSUop2017_HIGH/file_CSUop2017_count)*100, levels=values, extend='both', cmap=my_cmap1, vmin=0,vmax=max_bound,transform=ccrs.PlateCarree())
    cb = plt.colorbar(cs,ax=ax)
    #cb = m.colorbar(cs,"right", ticks=values[0::4], size="5%", pad="2%", extend='both')
    #ax.set_title('Day '+str(validday)+' Probability of being in a High CSU v2017 Operational Contour \n Between '+yrmondayhr_beg[0:-2]+' and '+yrmondayhr_end[0:-2])
    ax.set_title('Day '+str(validday)+' Probability of being in a High CSU v2017 Operational Contour \n Between '+EvS_yrmondayhr_short[0][0:-2]+' and '+yrmondayhr_end[0:-2])
    #ax.set_extent([np.nanmin(lon), np.nanmax(lon), np.nanmin(lat), np.nanmax(lat)], crs=ccrs.PlateCarree())
    plt.savefig(FIG_PATH+'/'+GRIB_PATH_DES+'_CSUopv2017_spatprob_HIGH_vday'+str(int(validday))+'.png', bbox_inches='tight',dpi=200)
    plt.close() 

######CREATE AVERAGE PROBABILITY OF BEING WITHIN A CSUMLP 2020 OPERATIONAL CONTOUR THROUGHOUT THE PERIOD##########
max_bound = 40
my_cmap1 = copy.copy(mpl.cm.get_cmap('jet'))
my_cmap1.set_under('white')
values = np.linspace(0,max_bound,21)
[fig,ax] = cartopy_maps.plot_map(lat,lon)
cs = plt.contourf(lon, lat, (CSUop2020_MRGL/file_CSUop2020_count)*100, levels=values, extend='both', cmap=my_cmap1, vmin=0,vmax=max_bound,transform=ccrs.PlateCarree())
cb = plt.colorbar(cs,ax=ax)
#cb = m.colorbar(cs,"right", ticks=values[0::4], size="5%", pad="2%", extend='both')
#ax.set_title('Day '+str(validday)+' Probability of being in a Marginal CSU v2020 Operational Contour \n Between '+yrmondayhr_beg[0:-2]+' and '+yrmondayhr_end[0:-2])
ax.set_title('Day '+str(validday)+' Probability of being in a Marginal CSU v2020 Operational Contour \n Between '+EvS_yrmondayhr_short[0][0:-2]+' and '+yrmondayhr_end[0:-2])
#ax.set_extent([np.nanmin(lon), np.nanmax(lon), np.nanmin(lat), np.nanmax(lat)], crs=ccrs.PlateCarree())
plt.savefig(FIG_PATH+'/'+GRIB_PATH_DES+'_CSUopv2020_spatprob_MRGL_vday'+str(int(validday))+'.png', bbox_inches='tight',dpi=200)
plt.close() 

max_bound = 20
my_cmap1 = copy.copy(mpl.cm.get_cmap('jet'))
my_cmap1.set_under('white')
values = np.linspace(0,max_bound,21)
[fig,ax] = cartopy_maps.plot_map(lat,lon)
cs = plt.contourf(lon, lat, (CSUop2020_SLGT/file_CSUop2020_count)*100, levels=values, extend='both', cmap=my_cmap1, vmin=0,vmax=max_bound,transform=ccrs.PlateCarree())
cb = plt.colorbar(cs,ax=ax)
#cb = m.colorbar(cs,"right", ticks=values[0::4], size="5%", pad="2%", extend='both')
#ax.set_title('Day '+str(validday)+' Probability of being in a Slight CSU v2020 Operational Contour \n Between '+yrmondayhr_beg[0:-2]+' and '+yrmondayhr_end[0:-2])
ax.set_title('Day '+str(validday)+' Probability of being in a Slight CSU v2020 Operational Contour \n Between '+EvS_yrmondayhr_short[0][0:-2]+' and '+yrmondayhr_end[0:-2])
#ax.set_extent([np.nanmin(lon), np.nanmax(lon), np.nanmin(lat), np.nanmax(lat)], crs=ccrs.PlateCarree())
plt.savefig(FIG_PATH+'/'+GRIB_PATH_DES+'_CSUopv2020_spatprob_SLGT_vday'+str(int(validday))+'.png', bbox_inches='tight',dpi=200)
plt.close() 

max_bound = 8
my_cmap1 = copy.copy(mpl.cm.get_cmap('jet'))
my_cmap1.set_under('white')
values = np.linspace(0,max_bound,21)
[fig,ax] = cartopy_maps.plot_map(lat,lon)
cs = plt.contourf(lon, lat, (CSUop2020_MDT/file_CSUop2020_count)*100, levels=values, extend='both', cmap=my_cmap1, vmin=0,vmax=max_bound,transform=ccrs.PlateCarree())
cb = plt.colorbar(cs,ax=ax)
#cb = m.colorbar(cs,"right", ticks=values[0::4], size="5%", pad="2%", extend='both')
#ax.set_title('Day '+str(validday)+' Probability of being in a Moderate CSU v2020 Operational Contour \n Between '+yrmondayhr_beg[0:-2]+' an '+yrmondayhr_end[0:-2])
ax.set_title('Day '+str(validday)+' Probability of being in a Moderate CSU v2020 Operational Contour \n Between '+EvS_yrmondayhr_short[0][0:-2]+' an '+yrmondayhr_end[0:-2])
#ax.set_extent([np.nanmin(lon), np.nanmax(lon), np.nanmin(lat), np.nanmax(lat)], crs=ccrs.PlateCarree())
plt.savefig(FIG_PATH+'/'+GRIB_PATH_DES+'_CSUopv2020_spatprob_MDT_vday'+str(int(validday))+'.png', bbox_inches='tight',dpi=200)
plt.close() 

max_bound = 2
my_cmap1 = copy.copy(mpl.cm.get_cmap('jet'))
my_cmap1.set_under('white')
values = np.linspace(0,max_bound,21)
[fig,ax] = cartopy_maps.plot_map(lat,lon)
cs = plt.contourf(lon, lat, (CSUop2020_HIGH/file_CSUop2020_count)*100, levels=values, extend='both', cmap=my_cmap1, vmin=0,vmax=max_bound,transform=ccrs.PlateCarree())
cb = plt.colorbar(cs,ax=ax)
#cb = m.colorbar(cs,"right", ticks=values[0::4], size="5%", pad="2%", extend='both')
#ax.set_title('Day '+str(validday)+' Probability of being in a High CSU v2020 Operational Contour \n Between '+yrmondayhr_beg[0:-2]+' and '+yrmondayhr_end[0:-2])
ax.set_title('Day '+str(validday)+' Probability of being in a High CSU v2020 Operational Contour \n Between '+EvS_yrmondayhr_short[0][0:-2]+' and '+yrmondayhr_end[0:-2])
#ax.set_extent([np.nanmin(lon), np.nanmax(lon), np.nanmin(lat), np.nanmax(lat)], crs=ccrs.PlateCarree())
plt.savefig(FIG_PATH+'/'+GRIB_PATH_DES+'_CSUopv2020_spatprob_HIGH_vday'+str(int(validday))+'.png', bbox_inches='tight',dpi=200)
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
#cs = plt.contourf(lon,lat,np.nanmean(ST4gFFG_last7[::-1,:],axis=2)*100, levels=values, extend='both', cmap=my_cmap1, vmin=0,vmax=max_bound)
#cb = plt.colorbar(cs,ax=ax)
#ax.set_title('Average Probability of ST4 > FFG Occurrences Between 20170514 and 20170822')
#ax.set_extent([np.nanmin(lon), np.nanmax(lon), np.nanmin(lat), np.nanmax(lat)], crs=ccrs.PlateCarree())
#plt.savefig('/export/hpc-lw-dtbdev5/wpc_cpgffh/figures/ERO/static/'+GRIB_PATH_DES+'_ST4gFFG_prob_vday'+str(int(validday))+'_NEW.png', bbox_inches='tight',dpi=200)
#plt.close()

#Copy all files to website folder at ftp://ftp.wpc.ncep.noaa.gov/erickson/ERO_verif/
subprocess.call('scp '+FIG_PATH+'*.* hpc@vm-lnx-rzdm05:/home/people/hpc/www/htdocs/verification/ero_verif/images', \
    stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'), shell=True)
