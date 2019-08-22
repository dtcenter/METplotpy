#!/usr/bin/python
# -*- coding: utf-8 -*-

################################################################################################
#ONE OF THE MAIN WRAPPER SCRIPTS TO LOAD ERO/FFG/ST4 DATA, RUN THE DATA 
#THROUGH MET SOFTWARE, AND SAVE GRID_STAT OUTPUT. TO GATHER THE INITIAL
#LARGE DATA SAMPLE, THIS CODE WAS ITERATED THROUGH MANY PAST DAYS. 
#OPERATIONALLY THIS CODE ITERATES THROUGH THE MOST RECENT 7 DAYS TO 
#GRAB THE MOST UP-TO-DATE STAGE IV DATA. A SEPARATE SCRIPT IS USED
#TO AGGREGATE STATISTICS AND CREATE PLOTS. 20170501 - 20171210. MJE.
#
#MODIFIED TO INCLUDE MASKING OF SPURIOUS FFG DATA. 20180313. MJE.
#MODIFIED TO GUNZIP PERMANENT FILES TO SAVE HARD DRIVE SPACE. 20180409. MJE.
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
reload(METConFigGen)
reload(py2netcdf)

################################################################################
#########################1)MATRIX OF VARIABLES#################################
################################################################################
MET_PATH       = '/opt/MET6/met6.0/bin/'                                #Location of MET software
CON_PATH       = '/usr1/wpc_cpgffh/METv6.0/'                            #Location of MET config files
DATA_PATH      = '/usr1/wpc_cpgffh/gribs/'
GRIB_PATH      = '/export/hpc-lw-dtbdev5/merickson/'                    #Location of model GRIB files
GRIB_PATH_DES  = 'ALL'                                                  #An appended string label for the temporary directory name
latlon_dims    = [-129.8,25.0,-65.0,49.8]                               #Latitude/longitude dimensions for plotting [WLON,SLAT,ELON,NLAT]
ERO_probs      = [0.05,0.10,0.20,0.50]                                  #Declare the ERO probabilities for MRGL, SLGT, MDT, HIGH                                                                                                                   
days_back      = 7                                                      #Total days backwards to include in verification window
days_offset    = 1                                                      #Most current date (e.g. end of verification window)
validday       = 1                                                      #Valid days to be verified (single day)
validhr        = ['ALL']                                                #Valid hrs to be verified (specify 'ALL' for everything)
grid_delta     = 0.09                                                   #Grid resolution increment for interpolation (degrees lat/lon)
neigh_filter   = 40                                                     #Total neighborhoold filter (km)
################################################################################
######################2)PREPARE THE DATA FOR LOADING############################
################################################################################

#Create date specific directory
GRIB_PATH_EX = GRIB_PATH+'/ERO_verif/ERO_verif_day'+str(validday)+'_'+GRIB_PATH_DES+'/'
if not os.path.exists(GRIB_PATH_EX):
    os.makedirs(GRIB_PATH_EX)  
   
#Redo the ERO probabilities to proper strings for input to set_GridStatConfigProb
ERO_probs_str = ['>='+str(i) for i in np.append(np.append(0.0, ERO_probs), 1.0)]
ERO_probs_str = ', '.join(ERO_probs_str)   
 
#Static field of ERO categories
ERO_allcat=['ERO_MRGL','ERO_SLGT','ERO_MDT','ERO_HIGH']
               
#Generate current julian date, always starting at 12 UTC
curdate_init = datetime.datetime.now()-datetime.timedelta(days=days_offset)
curdate      = curdate_init.replace(hour=12)
curdate      = int(pygrib.datetime_to_julian(curdate))

#Load the CONUSmask and save the netCDF file
(CONUSmask,lat,lon) = loadAllEROData.readCONUSmask(DATA_PATH,latlon_dims,grid_delta)

#Load the ST4gFFG mask to mask out spurious points on FFG grid
with np.load('/usr1/wpc_cpgffh/gribs/ERO_verif/static/ALL_noMRGL_ST4gFFGmask_del'+str(grid_delta)+'.npz') as data:
    ST4gFFG_mask = data['ST4gFFG_mask']
CONUSmask[CONUSmask<0.1]  = np.NaN
CONUSmask[CONUSmask>=0.1] = 1
CONUSmask = CONUSmask * ST4gFFG_mask

#Load the ERO interpolation grid
(Fy,Fx,lat,lon) = loadAllEROData.createEROInterField(DATA_PATH,latlon_dims,grid_delta)

#Loop through the verification period
jday_count = 0
for juldays in range(curdate-days_back-1,curdate,1): #Keep verification period fixed and iterating backwards through vday

    ############################################################################
    ##########READ IN THE ERO DATA, CONVERT TO NP FORMAT########################
    ############################################################################
    
    #Create string/datetime elements to load ERO data for given day (verif. window is juldays to juldays+1)
    datetime_load_ERO = pygrib.julian_to_datetime(juldays-validday+1)    
    yrmonday_load_ERO = ''.join(['{:04d}'.format(pygrib.julian_to_datetime(juldays-validday+1).year),  \
        '{:02d}'.format(pygrib.julian_to_datetime(juldays-validday+1).month), \
        '{:02d}'.format(pygrib.julian_to_datetime(juldays-validday+1).day)])       

    #Determine the proper hours to load given inputs for each data set          
    vhr_ERO = []
    if os.path.isdir(DATA_PATH+'ERO/'+yrmonday_load_ERO):
        if 'ALL' in validhr:
            for file in os.listdir(DATA_PATH+'ERO/'+yrmonday_load_ERO):
                if '94e' in file and validday == 1:
                    vhr_ERO = np.append(vhr_ERO,float(file[12:14]))
                elif '98e' in file and validday == 2:
                    vhr_ERO = np.append(vhr_ERO,float(file[12:14]))
                elif '99e' in file and validday == 3:
                    vhr_ERO = np.append(vhr_ERO,float(file[12:14]))
        else:
            for data in range(0,len(validhr)):
                vhr_ERO = np.append(vhr_ERO,validhr[data])
    else:
        vhr_ERO = [0]
    vhr_ERO = np.sort(vhr_ERO)

    #Loop through all valid hours within a valid day
    for vhr in range(0,len(vhr_ERO)):

        #ERO Special condition: if 1 day ERO time stamp is before 09z, it is valid from the day before😴    
        if validday == 1 and vhr_ERO[vhr] < 9:
            if jday_count - 1 >= 0: #Cat onto previous day unless its the first day   
                
                #In this once case, change the date string between prevously loaded ERO data and to-be-saved data 
                yrmonday_end_ERO = ''.join(['{:04d}'.format(pygrib.julian_to_datetime(juldays).year),  \
                    '{:02d}'.format(pygrib.julian_to_datetime(juldays).month), \
                    '{:02d}'.format(pygrib.julian_to_datetime(juldays).day)])
                datetime_beg_ERO = pygrib.julian_to_datetime(juldays-1)
                datetime_end_ERO = pygrib.julian_to_datetime(juldays)
            else:
                continue
        else: #ERO fcst is fixed over verif. window (e.g. 2 day ERO issued 20160613, this would be 20160615)  

            #Date containing the last valid hour of the period to be analyzed
            yrmonday_end_ERO = ''.join(['{:04d}'.format(pygrib.julian_to_datetime(juldays+1).year),  \
                '{:02d}'.format(pygrib.julian_to_datetime(juldays+1).month), \
                '{:02d}'.format(pygrib.julian_to_datetime(juldays+1).day)]) 
            datetime_beg_ERO = pygrib.julian_to_datetime(juldays)
            datetime_end_ERO = pygrib.julian_to_datetime(juldays+1)

        #Read in the data
        (MRGL,ero_MRGL,SLGT,ero_SLGT,MDT,ero_MDT,HIGH,ero_HIGH) = \
            loadAllEROData.readERO(DATA_PATH+'ERO/',latlon_dims,grid_delta,datetime_load_ERO,vhr_ERO[vhr],validday,Fx,Fy)

        #Remove any ERO data falling outside CONUS
        ero_MRGL = ero_MRGL * CONUSmask
        ero_SLGT = ero_SLGT * CONUSmask
        ero_MDT  = ero_MDT  * CONUSmask
        ero_HIGH = ero_HIGH * CONUSmask

        #Combine all ERO information into one grid reflecting ERO probabilities
        ero_ALL = np.zeros((ero_MRGL.shape))
        ero_ALL = (((ero_MRGL > 0) & (ero_SLGT == 0) & (ero_MDT == 0) & (ero_HIGH == 0)) * ERO_probs[0]) + ero_ALL
        ero_ALL = (((ero_MRGL > 0) & (ero_SLGT > 0) & (ero_MDT == 0) & (ero_HIGH == 0)) * ERO_probs[1]) + ero_ALL
        ero_ALL = (((ero_MRGL > 0) & (ero_SLGT > 0) & (ero_MDT > 0) & (ero_HIGH == 0)) * ERO_probs[2]) + ero_ALL
        ero_ALL = (((ero_MRGL > 0) & (ero_SLGT > 0) & (ero_MDT > 0) & (ero_HIGH > 0)) * ERO_probs[3]) + ero_ALL
        
        #Save the ERO data
        vhr_rec = vhr_ERO[vhr]
        filename_ERO = py2netcdf.py2netcdf_ANALY(GRIB_PATH_EX,latlon_dims,grid_delta,datetime_beg_ERO, \
            datetime_end_ERO,vhr_rec,lat[::-1,0],lon[0,:],ero_ALL[::-1,:],'ERO','ERO Probability Grid')
     
    ############################################################################
    ########READ IN THE ST4gFFG DATA, CONVERT TO NP FORMAT######################
    ############################################################################

    #Determine the proper hours to load given inputs for each data set
    vhr_ST4 = np.linspace(13,36,24)+((validday-1)*24)
    
    #Create date info for start of ST4gFFG interval
    datetime_beg_FFG = pygrib.julian_to_datetime(juldays)
    datetime_end_FFG = pygrib.julian_to_datetime(juldays+1)
    yrmonday_ffg_beg = '{:04d}'.format(datetime_beg_FFG.year)+'{:02d}'.format(datetime_beg_FFG.month)+'{:02d}'.format(datetime_beg_FFG.day)
    yrmonday_ffg_end = '{:04d}'.format(datetime_end_FFG.year)+'{:02d}'.format(datetime_end_FFG.month)+'{:02d}'.format(datetime_end_FFG.day)
        
    #Initialize FFG matrices    
    ST4_01hr    = np.zeros((lat.shape[0], lat.shape[1], 24)) #[lat,lon,hours per day]
    ST4_06hr    = np.zeros((lat.shape[0], lat.shape[1], 4))  #[lat,lon,hours per day]
    FFG_01hr    = np.zeros((lat.shape[0], lat.shape[1], 24)) #[lat,lon,hours per day]
    FFG_03hr    = np.zeros((lat.shape[0], lat.shape[1], 8))  #[lat,lon,hours per day]
    FFG_06hr    = np.zeros((lat.shape[0], lat.shape[1], 4))  #[lat,lon,hours per day]
    
    vhr3_count = 0   
    vhr6_count = 0   
    for vhr in range(1,len(vhr_ST4)+1):
        #Read in 1/6 hour ST4
        (lat_t,lon_t,ST4_t_01hr) = loadAllEROData.readST4(MET_PATH,DATA_PATH+'ST4/',GRIB_PATH_EX,latlon_dims,grid_delta,datetime_beg_FFG,vhr,1)
        
        ST4_01hr[:,:,vhr-1] = ST4_t_01hr
        if (vhr % 6) == 0:
            (lat_t,lon_t,ST4_t_06hr) = loadAllEROData.readST4(MET_PATH,DATA_PATH+'ST4/',GRIB_PATH_EX,latlon_dims,grid_delta,datetime_beg_FFG,vhr,6)
            ST4_06hr[:,:,vhr6_count] = ST4_t_06hr
        
        #Read in 1 hour FFG available every 6 hours, duplicate so there are 24 points in a day
        if (vhr % 6) == 0:
            (lat_t,lon_t,FFG_t_01hr) = loadAllEROData.readFFG(MET_PATH,DATA_PATH+'FFG/',GRIB_PATH_EX,latlon_dims,grid_delta,datetime_beg_FFG,vhr-6,1)
            for vhr_b in range(1,7,1): #loop backwards, filling FFG hours
                FFG_01hr[:,:,vhr-vhr_b] = FFG_t_01hr
            
        #Read in 3 hour FFG available every 6 hours, duplicate so there are 8 points in a day
        if (vhr % 6) == 0:
            (lat_t,lon_t,FFG_t_03hr)   = loadAllEROData.readFFG(MET_PATH,DATA_PATH+'FFG/',GRIB_PATH_EX,latlon_dims,grid_delta,datetime_beg_FFG,vhr-6,3)
            for vhr_b in range(0,2,1): #loop backwards, filling FFG hours
                FFG_03hr[:,:,vhr3_count-vhr_b] = FFG_t_03hr
 
        #Read in 6 hour FFG
        if (vhr % 6) == 0:
            (lat_t,lon_t,FFG_t_06hr) = loadAllEROData.readFFG(MET_PATH,DATA_PATH+'FFG/',GRIB_PATH_EX,latlon_dims,grid_delta,datetime_beg_FFG,vhr-6,6)
            FFG_06hr[:,:,vhr6_count] = FFG_t_06hr
            
        if (vhr % 3) == 0:
            vhr3_count += 1
        if (vhr % 6) == 0:
            vhr6_count += 1
            
    #Delete all unnecessary FFG/ST4 data in folder
    subprocess.call('rm -rf '+GRIB_PATH_EX+'*ffg.grib2*', stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'), shell=True)
    subprocess.call('rm -rf '+GRIB_PATH_EX+'ST4.*', stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'), shell=True)
    
    #Calculate all possible flooding combinations for 3 and 6 hour intervals        
    (ST4gFFG) = loadAllEROData.calc_ST4gFFG(vhr_ST4,ST4_01hr,ST4_06hr,FFG_01hr,FFG_03hr,FFG_06hr)

    #Remove any observations falling outside CONUS
    ST4gFFG = ST4gFFG * np.transpose(np.tile(CONUSmask,(24,1,1)),(1,2,0))
    
    #Save the ST4gFFG data
    np.save(GRIB_PATH_EX+'ST4gFFG_ending'+yrmonday_end_ERO,ST4gFFG)

    ############################################################################
    #######READ IN THE ARI DATA USING MET, DETERMINE ST4gARI####################
    ############################################################################

    (lat,lon,ARI) = loadAllEROData.readARI(MET_PATH,DATA_PATH,GRIB_PATH_EX,latlon_dims,grid_delta,5)
    (ST4gARI)     = loadAllEROData.calc_ST4gARI(vhr_ST4,ST4_01hr,ST4_06hr,ARI)
    
    #Since ST4gARI applies a 24 hour window, only consider 24 hour periods
    ST4gARI = np.nansum(ST4gARI,axis=2) > 0
    ST4gARI = ST4gARI * CONUSmask
    
    #Save the ST4gARI data as netcdf
    filename_ST4gARI = py2netcdf.py2netcdf_ANALY(GRIB_PATH_EX,latlon_dims,grid_delta,datetime_beg_FFG, \
        datetime_end_FFG,12,lat[::-1,0],lon[0,:],ST4gARI[::-1,:],'ST4gARI','Binomial Occurrence of ST4 > ARI')
     
    #Save ST4gARI to text file, which will be handy in practically-perfect in plotting script
    filename_ST4gARI_txt = loadAllEROData.grid2txt(GRIB_PATH_EX,'ST4gARI',ST4gARI,lat,lon,yrmonday_ffg_beg+'12',yrmonday_ffg_end+'12')
                                                                             
    ############################################################################
    #######READ IN THE COSGROVE DATA USING MET, SAVE TO NETCDF##################
    ############################################################################
    
    datetime_beg_COS  = pygrib.julian_to_datetime(juldays)
    filename_USGS     = loadAllEROData.Cosgrove2txt(DATA_PATH,GRIB_PATH_EX,datetime_beg_COS,12,latlon_dims,grid_delta,'usgs')
    filename_LSRFLASH = loadAllEROData.Cosgrove2txt(DATA_PATH,GRIB_PATH_EX,datetime_beg_COS,12,latlon_dims,grid_delta,'lsrflash')
    filename_LSRREG   = loadAllEROData.Cosgrove2txt(DATA_PATH,GRIB_PATH_EX,datetime_beg_COS,12,latlon_dims,grid_delta,'lsrreg')
    filename_MPING    = loadAllEROData.Cosgrove2txt(DATA_PATH,GRIB_PATH_EX,datetime_beg_COS,12,latlon_dims,grid_delta,'mping')

    #Use gen_vx_mask to convert LSR/MPING/USGS obs to 1 km grid (neighborhood will be applied later)
    subprocess.call(MET_PATH+"gen_vx_mask -type box -height '1' "+GRIB_PATH_EX+"dummy_usgs.nc "+ \
        filename_USGS+" -name 'USGS' "+filename_USGS[:-3]+"nc", stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'), shell=True)
    subprocess.call(MET_PATH+"gen_vx_mask -type box -height '1' "+GRIB_PATH_EX+"dummy_lsrflash.nc "+ \
        filename_LSRFLASH+" -name 'LSRFLASH' "+filename_LSRFLASH[:-3]+"nc", stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'), shell=True)
    subprocess.call(MET_PATH+"gen_vx_mask -type box -height '1' "+GRIB_PATH_EX+"dummy_lsrreg.nc "+ \
        filename_LSRREG+" -name 'LSRREG' "+filename_LSRREG[:-3]+"nc", stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'), shell=True)
    subprocess.call(MET_PATH+"gen_vx_mask -type box -height '1' "+GRIB_PATH_EX+"dummy_mping.nc "+ \
        filename_MPING+" -name 'MPING' "+filename_MPING[:-3]+"nc", stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'), shell=True)  
    
    #Delete dummy.nc variable and text files from Cosgrove2txt
    subprocess.call('rm -rf '+GRIB_PATH_EX+'*dummy*.nc',stdout=open(os.devnull, 'wb'), stderr=open(os.devnull, 'wb'), shell=True)
    subprocess.call('rm -rf '+filename_USGS,stdout=open(os.devnull, 'wb'), stderr=open(os.devnull, 'wb'), shell=True)
    subprocess.call('rm -rf '+filename_LSRFLASH,stdout=open(os.devnull, 'wb'), stderr=open(os.devnull, 'wb'), shell=True)
    subprocess.call('rm -rf '+filename_LSRREG,stdout=open(os.devnull, 'wb'), stderr=open(os.devnull, 'wb'), shell=True)
    subprocess.call('rm -rf '+filename_MPING,stdout=open(os.devnull, 'wb'), stderr=open(os.devnull, 'wb'), shell=True)

    jday_count += 1    
           
############################################################################
##########CONVERT DATA TO NETCDF AND RUN MET GRID_STAT######################
############################################################################

for juldays in range(curdate-days_back-1,curdate,1): #Keep verification period fixed and iterating backwards through vday
    
    #Create date info for beginning/end of ST4gFFG interval
    datetime_beg_FFG = pygrib.julian_to_datetime(juldays)
    yrmonday_beg_FFG = ''.join(['{:04d}'.format(pygrib.julian_to_datetime(juldays).year),  \
        '{:02d}'.format(pygrib.julian_to_datetime(juldays).month), \
        '{:02d}'.format(pygrib.julian_to_datetime(juldays).day)])
    yrmonday_end_FFG = ''.join(['{:04d}'.format(pygrib.julian_to_datetime(juldays+1).year),  \
        '{:02d}'.format(pygrib.julian_to_datetime(juldays+1).month), \
        '{:02d}'.format(pygrib.julian_to_datetime(juldays+1).day)])
    
    #Recall the filename for USGS/LSR/MPING/ALL
    filename_USGS     = GRIB_PATH_EX+'USGS_s'+yrmonday_beg_FFG+'12_e'+yrmonday_end_FFG+'12.nc'
    filename_LSRFLASH = GRIB_PATH_EX+'LSRFLASH_s'+yrmonday_beg_FFG+'12_e'+yrmonday_end_FFG+'12.nc'
    filename_LSRREG   = GRIB_PATH_EX+'LSRREG_s'+yrmonday_beg_FFG+'12_e'+yrmonday_end_FFG+'12.nc'
    filename_MPING    = GRIB_PATH_EX+'MPING_s'+yrmonday_beg_FFG+'12_e'+yrmonday_end_FFG+'12.nc'
    filename_ARI      = GRIB_PATH_EX+'ST4gARI_s'+yrmonday_beg_FFG+'12_e'+yrmonday_end_FFG+'12_vhr12.nc'
    filename_ALL      = GRIB_PATH_EX+'ALL_s'+yrmonday_beg_FFG+'12_e'+yrmonday_end_FFG+'12.nc'
           
    for file in os.listdir(GRIB_PATH_EX):
        
        if 'ERO' in file and '.nc' in file and '_e'+str(yrmonday_end_FFG) in file and not 'grid_stat' in file:

            #Record the validhr for ERO
            vhr = float(file[file.find('_vhr')+4:file.find('_vhr')+6]) 
            
            #Load and properly subset the ST4gFFG data based on the vhr from ERO data
            try:
                ST4gFFG   = np.load(GRIB_PATH_EX+'ST4gFFG_ending'+yrmonday_end_FFG+'.npy')
            except IOError:
                ST4gFFG   = np.full([lat.shape[0],lat.shape[1],24],np.nan)
                
            #Subset the ST4gFFG data to match the ERO valid period, which may be less than 24 hours
            if validday == 1 and vhr > 12: #Data spans after 12z on day 1
                vhr_beg = vhr - 12
            elif validday == 1 and vhr < 9:  #Data spans after 00z (less than 12 hrs) on day 1
                vhr_beg = vhr + 12
            else:
                vhr_beg = 0
            ST4gFFG_sub = np.nansum(ST4gFFG[:,:,int(vhr_beg)::],axis=2) > 0
            
            #Date element specifying beginning/end of period for netCDF
            datetime_beg_NDF = datetime_beg_FFG + datetime.timedelta(hours=vhr_beg)
            datetime_end_NDF = datetime_beg_FFG + datetime.timedelta(hours=24)

            #Save the ST4gFFG netCDF for each ERO file
            filename_ST4gFFG = py2netcdf.py2netcdf_ANALY(GRIB_PATH_EX,latlon_dims,grid_delta,datetime_beg_NDF, \
                datetime_end_NDF,vhr,lat[::-1,0],lon[0,:],ST4gFFG_sub[::-1,:],'ST4gFFG','Binomial Occurrence of ST4 > FFG')
               
            #Create a text file of ST4gFFG points for practically perfect plotting later
            yrmonday_ffg_beg = '{:04d}'.format(datetime_beg_NDF.year)+'{:02d}'.format(datetime_beg_NDF.month)+'{:02d}'.format(datetime_beg_NDF.day)
            yrmonday_ffg_end = '{:04d}'.format(datetime_end_NDF.year)+'{:02d}'.format(datetime_end_NDF.month)+'{:02d}'.format(datetime_end_NDF.day)
            filename_ST4gFFG_txt = loadAllEROData.grid2txt(GRIB_PATH_EX,'ST4gFFG',ST4gFFG_sub,lat,lon,yrmonday_ffg_beg+'{:02d}'.format(int(vhr)),yrmonday_ffg_end+'12')

            #Use pcp_combine to sum up all flood observations
            subprocess.call(MET_PATH+"pcp_combine -add "+filename_ST4gFFG+" 'name=\"ST4gFFG\";level=\"R1\";' "+ \
                filename_USGS+" 'name=\"USGS\";level=\"R1\";' "+filename_LSRFLASH+" 'name=\"LSRFLASH\";level=\"R1\";' "+ \
                filename_LSRREG+" 'name=\"LSRREG\";level=\"R1\";' "+filename_MPING+" 'name=\"MPING\";level=\"R1\";' "+ \
                filename_ARI+" 'name=\"ST4gARI\";level=\"R1\";' "+filename_ALL+' -name ALL', \
                shell=True)

            #Convert ERO thresholds to netCDF, create met_stat config file, and run grid_stat
            con_name_ST4gFFG = [[] for i in range(0,len(ERO_allcat))]
            con_name_ALL = [[] for i in range(0,len(ERO_allcat))]
            
            #Generate config file for ALL and ST4gFFG for each unique date
            con_name_ST4gFFG = METConFigGen.set_GridStatConfigProb(CON_PATH,GRIB_PATH_DES,'ERO', \
                'Surface',ERO_probs_str,'TRUE','ST4gFFG','Surface','>0.0',file,neigh_filter,grid_delta)
            #Run grid_stat, compute single event statistics of ERO Vs ST4gFFG   
            subprocess.call(MET_PATH+'grid_stat '+GRIB_PATH_EX+file+' '+filename_ST4gFFG+' '+con_name_ST4gFFG+' -outdir '+ \
                GRIB_PATH_EX,shell=True)
                
            #grid_stat, compute single event statistics of ERO Vs ALL when verification period is 24 hours
            if not (validday == 1 and (vhr > 12 or vhr < 9)):
                con_name_ALL = METConFigGen.set_GridStatConfigProb(CON_PATH,GRIB_PATH_DES,'ERO', \
                    'Surface',ERO_probs_str,'TRUE','ALL','A394003','>0.0',file,neigh_filter,grid_delta)
                subprocess.call(MET_PATH+'grid_stat '+GRIB_PATH_EX+file+' '+filename_ALL+' '+con_name_ALL+' -outdir '+ \
                    GRIB_PATH_EX,shell=True)
                
            #Remove ERO netcdf file and ST4gFFG netcdf file
            subprocess.call('rm -rf '+GRIB_PATH_EX+file, stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'), shell=True)
            subprocess.call('rm -rf '+filename_ST4gFFG,  stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'), shell=True)

    #Remove ST4gFFG npy, cosgrove files and ARI files
    subprocess.call('rm -rf '+GRIB_PATH_EX+'ST4gFFG_ending'+yrmonday_end_FFG+'.npy',stdout=open(os.devnull, 'wb'), \
        stderr=open(os.devnull, 'wb'), shell=True)
    subprocess.call('rm -rf '+filename_USGS,stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'), shell=True)
    subprocess.call('rm -rf '+filename_LSRFLASH,stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'), shell=True)
    subprocess.call('rm -rf '+filename_LSRREG,stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'), shell=True)
    subprocess.call('rm -rf '+filename_MPING,stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'), shell=True)
    subprocess.call('rm -rf '+filename_ALL,stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'), shell=True)

#Make sure the directory exists
if not os.path.isdir(DATA_PATH+'/ERO_verif/ERO_verif_day'+str(validday)+'_'+GRIB_PATH_DES+'/'):
    os.makedirs(DATA_PATH+'/ERO_verif/ERO_verif_day'+str(validday)+'_'+GRIB_PATH_DES+'/')
      
#Move all grid-stat files to proper directory
subprocess.call('mv '+GRIB_PATH_EX+'* '+DATA_PATH+'/ERO_verif/ERO_verif_day'+str(validday)+'_'+GRIB_PATH_DES+'/', \
    stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'), shell=True)

#Gunzip the files
subprocess.call('gzip -f '+DATA_PATH+'/ERO_verif/ERO_verif_day'+str(validday)+'_'+GRIB_PATH_DES+'/*.nc',  stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'), shell=True) 
subprocess.call('gzip -f '+DATA_PATH+'/ERO_verif/ERO_verif_day'+str(validday)+'_'+GRIB_PATH_DES+'/*.stat',stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'), shell=True) 

#Remove the temporary directory
subprocess.call('rm -rf '+GRIB_PATH_EX,stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'), shell=True)  u
