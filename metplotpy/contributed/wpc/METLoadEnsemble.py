#!/usr/bin/python

################################################################################################
#CONTAINS A SERIES OF PLATFORM SPECIFIC FUNCTIONS TO SET THE STAGE FOR LOADING MET. 
#Created 20161202-20170504. MJE.
#UPDATE: Added new features/update MET version. 20190606. MJE.
#UPDATE: Update from Python2 to Python3. MJE. 20210303.
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
import haversine
import matplotlib as mpl
import matplotlib.pyplot as plt
from netCDF4 import Dataset
from scipy import ndimage

###################################################################################
#setupData is a pre-processing step to load the CAM model data and/or ST4 obs located 
#at /export/hpc-lw-dtbdev5/wpc_cpgffh/gribs on hpc-lw-dtbdev5. Since most CAM data is initialized at 
#different intervals, this function does most of the grunt work to load the proper 
#strings, variables, and create the proper folders. Thereafter, run METLoadEnsemble.loadDataStr 
#to create the absolute path string to load model/obs data. Run this function outside of any for loop.
#
#When adding another ensemble member, take the following steps:
#1) Ensure the new model string name matches a partial string name in 'model_default,'
#if not then add a partial string to model_default
#2) Add the frequency of initalizations in UTC to 'run_times' and 'acc_int'
#
#Created by MJE. 20161206 - 20161215. 
#Update: Remove unnecessary variables, rename variables for clarification. 20170315. MJE
#Update: Add NEWSe. 20181026. MJE
#Update: Add MRMS 15-min. 20181206. MJE
#Update: Add NEWSe 1-hour. 20190417. MJE.
#Update: Add FV3FLAM 1-hour. 20201204. MJE.
#Update: Add HRRR 15-min. 20201207. MJE.
#
#####################INPUT FILES FOR setupData#############################
#GRIB_PATH         = Location of model GRIB files
#FIG_PATH          = Location for figure generation
#GRIB_PATH_DES     = An appended string label for the temporary directory name 
#load_data         = User specified string list of data to be loaded
#pre_acc           = Precipitation accumulation total
#total_fcst_hrs    = Last forecast hour to be considered
#latlon_dims       = latitude/longitude dimensions for plotting [WLON,SLAT,ELON,NLAT]
#curdate           = contains datetime information
#thres             = threshold analyzed
####################OUTPUT FILES FOR setupData#############################
#GRIB_PATH_TEMP    = temporary path where files are copied and MET is applied
#FIG_PATH_s        = directory for saving image files
#curdate           = current data array
#init_yrmondayhr   = model dependent string of year, month, day, and hour
#hrs               = string of forecast hours to load
#offset_fcsthr     = model dependent offset, in hours, from default initialization time
#load_data_nc      = model dependent string for the netcdf converted model name (only models to be loaded)
#acc_int           = model dependent accumulation interval (depends on temporal resolution of model
#lat               = Subset grid of latitude data
#lon               = Subset grid of longitude data
###################################################################################

def setupData(GRIB_PATH,FIG_PATH,GRIB_PATH_DES,load_data,pre_acc,total_fcst_hrs,latlon_dims,curdate,thres):

    #Create an array of partial strings to match the load data array specified by the user
    model_default=['ST4','MRMS15min','MRMS2min','NAM','HIRESW','HRRR','NSSL-OP','NSSL-ARW','NSSL-NMB','HRAM','NEWSe5min','NEWSe60min', \
        'HRRRe60min','FV3LAM','HRRRv415min']

    #Convert numbers to strings of proper length
    yrmondayhr=curdate.strftime('%Y%m%d%H')
    
    #Use list comprehension to cat on '.nc' to model list
    load_data_nc = [x + '.nc' for x in load_data]
    
    #Given the initalization hour, choose the most recent run for each model, archive initialization times
    offset_fcsthr=[]
    init_yrmondayhr=[]
    acc_int=[]
    for model in range(len(load_data)): #Through the models
        if model_default[0] in load_data[model]:          #ST4 (Depends on specified acc. interval)
            if (pre_acc == 6 or pre_acc == 12 or pre_acc == 18 or pre_acc == 24): # 6 hour acc. (24 hr acc. takes to long operationally)
                run_times=np.linspace(0,24,5) #Time in UTC data is available
                acc_int=np.append(acc_int,6)  #Hourly interval of data
            else:                                         #1 hour acc.
                run_times=np.linspace(0,24,25)
                acc_int=np.append(acc_int,1)
        elif model_default[1]  in load_data[model]:       #MRMS available in 15 min output
            run_times=np.linspace(0,24,4*24+1)
            acc_int=np.append(acc_int,15.0/60.0)
        elif model_default[2]  in load_data[model]:       #MRMS available in 2 min output
            run_times=np.linspace(0,24,30*24+1)
            acc_int=np.append(acc_int,2.0/60.0)
        elif model_default[3]  in load_data[model]:       #NAMNEST AND NAMNESTP
            run_times=np.linspace(0,24,5)
            #Accumulation interval depends on date for NAM and also user specificed precipitation interval
            if pygrib.datetime_to_julian(curdate) >= pygrib.datetime_to_julian(datetime.datetime(2017,3,21,6,0)):
                acc_int=np.append(acc_int,1)
            else:
                #If desired interval (pre_acc) is one but we are using earlier NAM data, throw error
                raise ValueError('Specified Interval of 1 Hour Impossible with NAM before 2017032106')
        elif model_default[4]  in load_data[model]:       #HIRES ARW/FV3
            run_times=np.linspace(0,24,3)
            acc_int=np.append(acc_int,1)
        elif model_default[5]  in load_data[model] and \
            '15min' not in load_data[model]:              #HRRR or HRRRp
            run_times=np.linspace(0,24,25)
            acc_int=np.append(acc_int,1)
        elif model_default[6]  in load_data[model]:       #NSSL Operational
            run_times=np.linspace(0,24,3)
            acc_int=np.append(acc_int,1)
        elif model_default[7]  in load_data[model] \
            or model_default[8]  in load_data[model]:     #NSSL Ensemble
            run_times=np.linspace(0,24,2)
            acc_int=np.append(acc_int,1)
        elif model_default[10]  in load_data[model]:      #NEWSe5min (NEWSe at 5 minute output)
            run_times=np.linspace(0,24,25)
            acc_int=np.append(acc_int,1.0/12.0)
        elif model_default[11]  in load_data[model]:      #NEWSe60min (NEWSe at 60 minute output)
            run_times=np.linspace(0,24,25)
            acc_int=np.append(acc_int,1)
        elif model_default[12]  in load_data[model]:      #HRRRe60min (HRRRe at 60 minute output)
            run_times=np.linspace(0,24,3)
            acc_int=np.append(acc_int,1)
        elif model_default[13]  in load_data[model]:      #FV3LAM (FV3LAM at 60 minute output)
            run_times=np.linspace(0,24,25)
            acc_int=np.append(acc_int,1)
        elif model_default[14]  in load_data[model]:      #HRRR15min (HRRR at 15 minute output)
            run_times=np.linspace(0,24,25)
            acc_int=np.append(acc_int,1.0/4.0)
    
        #Calculate lag from user specified string
        lag = float(load_data[model][load_data[model].index("lag")+3::])
        
        #Check to see if lag makes sense given frequency of initialization, and calculate strings
        if lag%(24.0 / (float(len(run_times))-1)) == 0: 
            #Determine the most recent model initialization offset
            init_offset = curdate.hour - run_times[np.argmax(run_times>curdate.hour)-1]
            #Combine the lag and offset to determine total offset
            offset_fcsthr=np.append(offset_fcsthr,init_offset+lag)
            #Determine yrmondayhr string from above information
            curdate_temp=curdate-datetime.timedelta(hours=int(offset_fcsthr[model]))
            init_yrmondayhr=np.append(init_yrmondayhr,curdate_temp.strftime('%Y%m%d%H'))
        else: #If lag is misspecified, compute with no lag
            lag = 0
            init_offset = curdate.hour - run_times[np.argmax(run_times>curdate.hour)-1]
            offset_fcsthr=np.append(offset_fcsthr,init_offset+lag)
            curdate_temp=curdate-datetime.timedelta(hours=int(offset_fcsthr[model]))
            init_yrmondayhr=np.append(init_yrmondayhr,curdate_temp.strftime('%Y%m%d%H'))
    
    #Create temporary directory
    GRIB_PATH_TEMP='/export/hpc-lw-dtbdev5/merickson/temp/'+yrmondayhr+'_p_'+str(pre_acc)+'_t'+str(thres)+'_'+GRIB_PATH_DES

    try:
        #os.system('rm -rf '+GRIB_PATH_TEMP)
        os.mkdir(GRIB_PATH_TEMP)
    except OSError:
        pass
    
    #Remove old files from temp directory
    output=os.system("rm -rf "+GRIB_PATH_TEMP+"/*.nc")
    output=os.system("rm -rf "+GRIB_PATH_TEMP+"/*.ps")
    output=os.system("rm -rf "+GRIB_PATH_TEMP+"/*.txt")
    output=os.system("rm -rf "+GRIB_PATH_TEMP+"/*grib2*")
    output=os.system("rm -rf "+GRIB_PATH_TEMP+"/*mod2*")
    
    #Set the proper forecast hours load depending on the initialization
    hrs = np.arange(0.0,total_fcst_hrs+0.01,pre_acc)
    
    #Remove partial accumulation periods
    hrs = hrs[hrs > 0]
    
    #Create directory for saving figures
    FIG_PATH_s=FIG_PATH+yrmondayhr
    try:
        os.mkdir(FIG_PATH_s)
    except OSError:
        pass
        
    #Load static data file and initialize needed variables for later
    f = Dataset(GRIB_PATH+'static/STATIC.nc', "a", format="NETCDF4")
    lat=f.variables['lat'][:]
    lon=f.variables['lon'][:]
    f.close()
    #Remove gridded data not in the lat/lon grid specifications
    data_subset=(lat >= latlon_dims[1]-3) & (lat < latlon_dims[3]+3) & (lon >= latlon_dims[0]-3) & (lon < latlon_dims[2]+3)*1
    x_elements_beg=np.argmax(np.diff(data_subset,axis=1)==1, axis=1)
    x_elements_end=np.argmax(np.diff(data_subset,axis=1)==-1, axis=1)
    y_elements_beg=np.argmax(np.diff(data_subset,axis=0)==1, axis=0)
    y_elements_end=np.argmax(np.diff(data_subset,axis=0)==-1, axis=0)
    x_elements_beg=x_elements_beg[x_elements_beg > 0]
    x_elements_end=x_elements_end[x_elements_end > 0]
    y_elements_beg=y_elements_beg[y_elements_beg > 0]
    y_elements_end=y_elements_end[y_elements_end > 0]
    x_beg=np.min(x_elements_beg)
    x_end=np.max(x_elements_end)
    y_beg=np.min(y_elements_beg)
    y_end=np.max(y_elements_end)
    
    lat=lat[y_beg:y_end,x_beg:x_end]
    lon=lon[y_beg:y_end,x_beg:x_end]
      
    return(GRIB_PATH_TEMP,FIG_PATH_s,curdate,init_yrmondayhr,hrs,offset_fcsthr,load_data_nc,acc_int,lat,lon)

###################################################################################
#loadDataStr creates the absolute path string necessary to load model data, given 
#a variety of inputs (i.e. model type and forecast hour). It is best to use 
#setupData before this function to optimize performance.
#
#When adding another ensemble member, take the following steps:
#1) Add the string to 'data_default'
#2) Add the model syntax information to the if statement specifying 'data_str'
#
#Created by MJE. 20161205-20161215.
#Update: Remove unnecessary variables, rename variables for clarification. 20170315. MJE
#Update: Add ARW member 2, which is part of the HREFv2. 20170425. MJE
#Update: Add forecast minute string to handle sub-hourly data. 20181108. MJE
#Update: Added MRMS/NEWSe strings. 20181206. MJE
#Update: Added more NEWSe details. 20190305. MJE
#Update: Added HRRRe. 20190417. MJE
#Update: Added FV3LAM. 20201204. MJE.
#Update: Add HRRRv4 15-min. 20201207. MJE.
#Update: Replace NMB with FV3 due to HREFv3 upgrade. 20210511. MJE.
#
#####################INPUT FILES FOR loadDataStr####################################
#GRIB_PATH          = Location of model GRIB files
#load_data          = String of model name
#init_yrmondayhr    = model dependent string of year, month, day and hour
#acc_int            = model dependent accumulation interval
#fcst_hr_str        = current forecast hour
#fcst_min_str       = current forecast minute
####################OUTPUT FILES FOR loadDataStr####################################
#data_str           = absolute path of model to be loaded
###################################################################################
def loadDataStr(GRIB_PATH, load_data, init_yrmondayhr, acc_int, fcst_hr_str, fcst_min_str):

#####Comment out when not testing function#################
#load_data       = load_data[0]
#init_yrmondayhr = init_yrmondayhr[0]
#acc_int         = acc_int[0]
###########################################################

    #Default list of model strings
    data_default=['ST4'     ,'MRMS2min'    ,'MRMS15min'       ,'HIRESNAM'          ,'HIRESNAMP'          ,'HIRESWARW'         , \
        'HIRESWARW2'        ,'HIRESWFV3'   ,'HRRRv2'          ,'HRRRv3'            ,'HRRRv4'             ,'NSSL-OP'           , \
        'NSSL-ARW-CTL'      ,'NSSL-ARW-N1' ,'NSSL-ARW-P1'     ,'NSSL-ARW-P2'       ,'NSSL-NMB-CTL'       ,'NSSL-NMB-N1'       , \
        'NSSL-NMB-P1'       ,'NSSL-NMB-P2' ,'HRAM3E'          ,'HRAM3G'            ,'NEWSe5min'          ,'NEWSe60min'        , \
        'HRRRe60min'        ,'FV3LAM'      ,'HRRRv415min']  #Array of total model strings

    #Create proper string for loading of model data
    if data_default[0] in load_data[:-2]: #Observation/analysis for ST4
        #ST4 is treated a bit differently, since the analysis time changes, hence the date and folder
        acc_int_str = '{:02d}'.format(int(acc_int))
        newtime= datetime.datetime(int(init_yrmondayhr[0:4]),int(init_yrmondayhr[4:6]),int(init_yrmondayhr[6:8]))+ \
            datetime.timedelta(hours=int(fcst_hr_str)+int(init_yrmondayhr[-2:]))
        data_str = [GRIB_PATH+'/ST4/'+newtime.strftime('%Y%m%d')+'/ST4.'+newtime.strftime('%Y%m%d')+ \
            newtime.strftime('%H')+'.'+acc_int_str+'h']
    elif data_default[1] in load_data[:-2]: #Observation/analysis for MRMS 2-min data
        #MRMS is treated a bit differently, since the analysis time changes, hence the date and folder
        newtime= datetime.datetime(int(init_yrmondayhr[0:4]),int(init_yrmondayhr[4:6]),int(init_yrmondayhr[6:8]))+ \
            datetime.timedelta(hours=int(fcst_hr_str)+float(fcst_min_str)/60+int(init_yrmondayhr[-2:]))
        data_str = [GRIB_PATH+'/MRMS/'+newtime.strftime('%Y%m%d')+'/MRMS_PrecipRate_00.00_'+newtime.strftime('%Y%m%d')+ \
            '-'+newtime.strftime('%H')+newtime.strftime('%M')+'00.grib2']
    elif data_default[2] in load_data[:-2]: #Observation/analysis for MRMS 15-min data
        #MRMS is treated a bit differently, since the analysis time changes, hence the date and folder
        newtime= datetime.datetime(int(init_yrmondayhr[0:4]),int(init_yrmondayhr[4:6]),int(init_yrmondayhr[6:8]))+ \
            datetime.timedelta(hours=int(fcst_hr_str)+float(fcst_min_str)/60+int(init_yrmondayhr[-2:]))
        data_str = [GRIB_PATH+'/MRMS/'+newtime.strftime('%Y%m%d')+'/'+newtime.strftime('%Y%m%d')+'-'+newtime.strftime('%H')+ \
            newtime.strftime('%M')+'00.netcdf']
    elif data_default[3] in load_data[:-2] and not data_default[2] in load_data[:-2]:   #NAM NEST
        data_str = [GRIB_PATH+'/HIRESNAM/'+init_yrmondayhr[:-2]+'/nam.t'+init_yrmondayhr[-2:]+'z.conusnest.hiresf'+fcst_hr_str+'.tm00.grib2.mod']
    elif data_default[4] in load_data[:-2]: #NAM NEST PARALLEL
        data_str = [GRIB_PATH+'/HIRESNAMP/'+init_yrmondayhr[:-2]+'/nam_conusnest_'+init_yrmondayhr[:-2]+init_yrmondayhr[-2:]+'f0'+fcst_hr_str+'.grib2']
    elif data_default[5] in load_data[:-2] and '2' not in load_data[:-2]: #ARW CONUS
        data_str = [GRIB_PATH+'/HIRESW/'+init_yrmondayhr[:-2]+'/hiresw.t'+init_yrmondayhr[-2:]+'z.arw_5km.f'+fcst_hr_str+'.conus.grib2.mod']
    elif data_default[6] in load_data[:-2]: #ARW CONUS Member 2
        data_str = [GRIB_PATH+'/HIRESW/'+init_yrmondayhr[:-2]+'/hiresw.t'+init_yrmondayhr[-2:]+'z.arw_5km.f'+fcst_hr_str+'.conusmem2.grib2.mod']
    elif data_default[7] in load_data[:-2]: #FV3 CONUS
        data_str = [GRIB_PATH+'/HIRESW/'+init_yrmondayhr[:-2]+'/hiresw.t'+init_yrmondayhr[-2:]+'z.fv3_5km.f'+fcst_hr_str+'.conus.grib2.mod']
    elif data_default[8] in load_data[:-2]: #HRRRv2
        data_str = [GRIB_PATH+'/HRRRv2/'+init_yrmondayhr[:-2]+'/hrrr.t'+init_yrmondayhr[-2:]+'z.wrfsfcf'+fcst_hr_str+'.grib2.mod']
    elif data_default[9] in load_data[:-2]: #HRRRv3
        data_str = [GRIB_PATH+'/HRRRv3/'+init_yrmondayhr[:-2]+'/hrrr_2d_'+init_yrmondayhr[:-2]+init_yrmondayhr[-2:]+fcst_hr_str+'.grib2']
    elif data_default[10] in load_data[:-2] and not '15min' in load_data[:-2]: #HRRRv4
        data_str = [GRIB_PATH+'/HRRRv4/'+init_yrmondayhr[:-2]+'/hrrr_2d_'+init_yrmondayhr[:-2]+init_yrmondayhr[-2:]+fcst_hr_str+'.grib2']  
    elif data_default[11] in load_data[:-2]: #NSSL CONTROL
        data_str = [GRIB_PATH+'/NSSL/'+init_yrmondayhr[:-2]+'/wrf4nssl_'+init_yrmondayhr[:-2]+init_yrmondayhr[-2:]+'.f'+fcst_hr_str+'.mod2']
    elif data_default[12] in load_data[:-2]: #NSSL ARW CTL
        data_str = [GRIB_PATH+'/NSSL/'+init_yrmondayhr[:-2]+'/wrf4nssl_arw_ctl_'+init_yrmondayhr[:-2]+init_yrmondayhr[-2:]+'.f'+fcst_hr_str+'.mod2']
    elif data_default[13] in load_data[:-2]: #NSSL ARW N1
        data_str = [GRIB_PATH+'/NSSL/'+init_yrmondayhr[:-2]+'/wrf4nssl_arw_n1_'+init_yrmondayhr[:-2]+init_yrmondayhr[-2:]+'.f'+fcst_hr_str+'.mod2']
    elif data_default[14] in load_data[:-2]: #NSSL ARW P1
        data_str = [GRIB_PATH+'/NSSL/'+init_yrmondayhr[:-2]+'/wrf4nssl_arw_p1_'+init_yrmondayhr[:-2]+init_yrmondayhr[-2:]+'.f'+fcst_hr_str+'.mod2']
    elif data_default[15] in load_data[:-2]: #NSSL ARW P2
        data_str = [GRIB_PATH+'/NSSL/'+init_yrmondayhr[:-2]+'/wrf4nssl_arw_p2_'+init_yrmondayhr[:-2]+init_yrmondayhr[-2:]+'.f'+fcst_hr_str+'.mod2']
    elif data_default[16] in load_data[:-2]: #NSSL NMB CTL
        data_str = [GRIB_PATH+'/NSSL/'+init_yrmondayhr[:-2]+'/wrf4nssl_nmb_ctl_'+init_yrmondayhr[:-2]+init_yrmondayhr[-2:]+'.f'+fcst_hr_str+'.mod2']
    elif data_default[17] in load_data[:-2]: #NSSL NMB N1
        data_str = [GRIB_PATH+'/NSSL/'+init_yrmondayhr[:-2]+'/wrf4nssl_nmb_n1_'+init_yrmondayhr[:-2]+init_yrmondayhr[-2:]+'.f'+fcst_hr_str+'.mod2']
    elif data_default[18] in load_data[:-2]: #NSSL NMB P1
        data_str = [GRIB_PATH+'/NSSL/'+init_yrmondayhr[:-2]+'/wrf4nssl_nmb_p1_'+init_yrmondayhr[:-2]+init_yrmondayhr[-2:]+'.f'+fcst_hr_str+'.mod2']
    elif data_default[19] in load_data: #NSSL NMB P2
        data_str = [GRIB_PATH+'/NSSL/'+init_yrmondayhr[:-2]+'/wrf4nssl_nmb_p2_'+init_yrmondayhr[:-2]+init_yrmondayhr[-2:]+'.f'+fcst_hr_str+'.mod2']
    elif data_default[20] in load_data[:-2]: #HRAM3E
        data_str = [GRIB_PATH+'/WWE2017/'+init_yrmondayhr[:-2]+'/hram3e_'+init_yrmondayhr[:-2]+init_yrmondayhr[-2:]+'f0'+fcst_hr_str+'.grib2']
    elif data_default[21] in load_data[:-2]: #HRAM3G
        data_str = [GRIB_PATH+'/WWE2017/'+init_yrmondayhr[:-2]+'/hram3g_'+init_yrmondayhr[:-2]+init_yrmondayhr[-2:]+'f0'+fcst_hr_str+'.grib2']
    elif data_default[22] in load_data[:-2]: #NEWSe5min
        initime = datetime.datetime(int(init_yrmondayhr[0:4]),int(init_yrmondayhr[4:6]),int(init_yrmondayhr[6:8]),int(init_yrmondayhr[8::]))
        newtime = datetime.datetime(int(init_yrmondayhr[0:4]),int(init_yrmondayhr[4:6]),int(init_yrmondayhr[6:8]))+ \
            datetime.timedelta(hours=int(fcst_hr_str)+float(fcst_min_str)/60+int(init_yrmondayhr[-2:]))

        if int(load_data[load_data.find('mem')+3:load_data.find('mem')+5]) < 10:
            ens_mem = load_data[load_data.find('mem')+4:load_data.find('mem')+5]
        else:
            ens_mem = load_data[load_data.find('mem')+3:load_data.find('mem')+5]

        data_str = [GRIB_PATH+'/NEWSe/NEWSe_Min/'+initime.strftime('%Y%m%d')+'/NEWSe_'+initime.strftime('%Y%m%d')+ \
            '_i'+initime.strftime('%H')+initime.strftime('%M')+'_m'+ens_mem+'_f'+newtime.strftime('%H')+newtime.strftime('%M')+ \
            '.nc']
    elif data_default[23] in load_data[:-2]: #NEWSe60min
        if int(load_data[load_data.find('mem')+3:load_data.find('mem')+5]) < 10:
            ens_mem = load_data[load_data.find('mem')+4:load_data.find('mem')+5]
        else:
            ens_mem = load_data[load_data.find('mem')+3:load_data.find('mem')+5]
        data_str = [GRIB_PATH+'/NEWSe/NEWSe_Hour/'+init_yrmondayhr[:-2]+'/NEWSe_'+init_yrmondayhr[:-2]+'_i'+init_yrmondayhr[-2:]+'_m'+ens_mem+'_f'+fcst_hr_str+'.grb2']
    elif data_default[24] in load_data[:-2]: #HRRRe60min
        ens_mem = load_data[load_data.find('mem')+3:load_data.find('mem')+5]
        data_str = [GRIB_PATH+'/HRRRe/'+init_yrmondayhr[:-2]+'/mem'+ens_mem+'_hrrr_ens_'+init_yrmondayhr+fcst_hr_str+'.grib2']
    elif data_default[25] in load_data[:-2]: #FV3LAM
        if load_data[0:load_data.find('_')] == 'FV3LAM':
            data_str = [GRIB_PATH+'/FV3LAM/'+init_yrmondayhr[:-2]+'/fv3lam.t'+init_yrmondayhr[-2:]+'z.conus.testbed.f'+fcst_hr_str+'.grib2.mod']
        elif load_data[0:load_data.find('_')] == 'FV3LAMx':
            data_str = [GRIB_PATH+'/FV3LAMx/'+init_yrmondayhr[:-2]+'/fv3lamx.t'+init_yrmondayhr[-2:]+'z.conus.testbed.f'+fcst_hr_str+'.grib2.mod']
        elif load_data[0:load_data.find('_')] == 'FV3LAMda':
            data_str = [GRIB_PATH+'/FV3LAMda/'+init_yrmondayhr[:-2]+'/fv3lamda.t'+init_yrmondayhr[-2:]+'z.conus.testbed.f'+fcst_hr_str+'.grib2.mod']
    elif data_default[26] in load_data[:-2]: #HRRRv415min
        data_str = [GRIB_PATH+'/HRRRv4_SubHourly/'+init_yrmondayhr[:-2]+'/hrrr_2d_'+init_yrmondayhr+fcst_hr_str+fcst_min_str+'.grib2']

    return data_str
 
###################################################################################
#loadDataMODE loads MODE object data. This includes the *_obj.nc and *_obj.txt file. 

#Created by MJE. 20161207.
#Update: Remove unnecessary variables, rename variables for clarification. 20170315. MJE
#
#####################INPUT FILES FOR loadDataMODE#############################
#GRIB_PATH_TEMP    = temporary path where files are copied and MET is applied
#MODEfile_new      = QPE string for the netcdf converted data name
#latlon_dims       = latitude/longitude dimensions for plotting [WLON,SLAT,ELON,NLAT]
####################OUTPUT FILES FOR loadDataMODE#############################
#lat               = grid of latitude from netcdf MODE output
#lon               = grid of longitude from netcdf latlon_dimsMODE output
#grid              = grid of raw forecast or observation values
#simp_bin          = binary grid of simple information
#clus_bin          = binary grid of cluster information
#simp_prop         = simple centroid info of lat,lon,90th percentile
#clus_prop         = cluster info of comp_obs_id,comp_mod_id,comp_cent_dist,
#                    comp_bound_dist,comp_convex_hull_dist,comp_angle_diff,
#                    comp_area_ratio,comp_inter_area,comp_union_area,comp_symm_diff,
#                    comp_inter_over_area,comp_complex_ratio comp_pctle_inten_ratio,
#                    comp_interest
#data_success      = file successfully loaded if equals zero
###################################################################################
#Note: "Simple" means unmatched while "cluster" refers to merged objects.
#"Single" refers to unmatched objects while "pair" refers to matched objects.

def loadDataMODE(GRIB_PATH_TEMP, MODEfile_new, latlon_dims):

    #MODEfile_new=MODEfile_new[fcst_hr_count][model][thres_count]
    
    #Matrix of header strings to seek out and length of data
    head_str_obj    = ['OBJECT_ID'] 
    head_len_obj    = [11]
    head_str_simp   = ['OBJECT_ID','CENTROID_LAT','CENTROID_LON','INTENSITY_90']
    head_len_simp   = [11,13,12,12]    
    head_str_clus   = ['OBJECT_CAT','OBJECT_CAT','CENTROID_DIST','BOUNDARY_DIST','CONVEX_HULL_DIST', \
        'ANGLE_DIFF','AREA_RATIO','INTERSECTION_AREA','UNION_AREA','SYMMETRIC_DIFF',   \
        'INTERSECTION_OVER_AREA','COMPLEXITY_RATIO','PERCENTILE_INTENSITY_RATIO','INTEREST']
    head_len_clus   = [11,11,13,13,16,10,10,17,10,14,22,16,26,8]

    simp_prop = np.ones((4,150))*-999
    clus_prop = np.ones((14,150))*-999

    #Check to see if file exists
    if os.path.isfile(GRIB_PATH_TEMP+'/'+MODEfile_new+'_obj.nc'): 

        #####1) First read in the 2d text file to gather centroid intensity and location
        #Open file and read through it
        target = open(GRIB_PATH_TEMP+'/'+MODEfile_new+'_obj.txt','r')
        data = target.readlines()
        target.close()

        #Loop through each line and gather the needed info
        f_count = 0
        f_simp_count = 0
        f_clus_count = 0
        
        for line in data:
            
            #Find location of data in each file usimp header information
            if f_count == 0:
                line1 = line
                array_obj = [line1.find(head_str_obj[0]),line1.find(head_str_obj[0])+head_len_obj[0]]
            
            if f_count > 0:
                
                #Isolate simple cluster model/obs objects, gather stats comparing mod to obs in the form:
                #[object ID, centroid lat, centroid lon, centroid 90th percentile]
                
                for header in range(0,len(head_str_simp)):
                    
                    #Gather data grabbing arrays; special conditions for getting OBJECT_ID
                    if header == 0:
                        array_simp = [line1.find(head_str_simp[header])+8,line1.find(head_str_simp[header])+head_len_simp[header]]
                    else:
                        array_simp = [line1.find(head_str_simp[header]),line1.find(head_str_simp[header])+head_len_simp[header]]
                        
                    if ('CF' in line[array_obj[0]:array_obj[-1]]) and ('_' not in line[array_obj[0]:array_obj[-1]]):
                        simp_prop[header,f_simp_count] = float(line[array_simp[0]:array_simp[-1]])
                        if header == len(head_str_simp)-1:
                            f_simp_count += 1
                            
                    elif ('CO' in line[array_obj[0]:array_obj[-1]]) and ('_' not in line[array_obj[0]:array_obj[-1]]):
                        #Make observation ID's negative to differentiate from model
                        if head_str_simp[header] == 'OBJECT_ID':
                            simp_prop[header,f_simp_count] = -float(line[array_simp[0]:array_simp[-1]])
                        else:
                            simp_prop[header,f_simp_count] = float(line[array_simp[0]:array_simp[-1]])    
                        
                        if header == len(head_str_simp)-1:
                            f_simp_count += 1

                #Isolate cluster cluster model/obs objects, gather stats comparing mod to obs in the form:
                #[comp_obs_id,comp_mod_id,comp_cent_dist,comp_bound_dist,comp_convex_hull_dist,comp_angle_diff,
                # comp_area_ratio,comp_inter_area,comp_union_area,comp_symm_diff,comp_inter_over_area,comp_complex_ratio
                # comp_pctle_inten_ratio,comp_interest]
                
                for header in range(0,len(head_str_clus)):
                    
                    #Gather data grabbing arrays; special conditions for getting OBJECT_CAT ID
                    if header == 0:
                        array_clus = [line1.find(head_str_clus[header])+8,line1.find(head_str_clus[header])+11]
                    elif header == 1:
                        array_clus = [line1.find(head_str_clus[header])+2,line1.find(head_str_clus[header])+5]
                    else:
                        array_clus = [line1.find(head_str_clus[header]),line1.find(head_str_clus[header])+head_len_clus[header]]
                    
                    if ('CF' in (line[array_obj[0]:array_obj[-1]]) and 'CO' in (line[array_obj[0]:array_obj[-1]])):
                        if header == 0: #Observations denoted as negative
                            clus_prop[header,f_clus_count] = -float(line[array_clus[0]:array_clus[-1]]) 
                        else:
                            clus_prop[header,f_clus_count] = float(line[array_clus[0]:array_clus[-1]]) 

                        if header == len(head_str_clus)-1:
                            f_clus_count += 1

            f_count += 1
            
        #Remove unpopulated dimensions
        simp_prop = simp_prop[:, np.nanmean(simp_prop == -999, axis=0) == 0]  
        clus_prop = clus_prop[:, np.nanmean(clus_prop == -999, axis=0) == 0]  
        
        #Redo as NaN if objects are blank
        if simp_prop.shape[1] == 0:
            simp_prop = np.nan
        if clus_prop.shape[1] == 0:
            clus_prop = np.nan              
        
        #####2) Next read in the centroid shape data from the netcdf file
        f = Dataset(GRIB_PATH_TEMP+'/'+MODEfile_new+'_obj.nc', "a", format="NETCDF4")
        lat=f.variables['lat'][:]
        lon=f.variables['lon'][:]
        
        #Initialize matrices
        simp_bin   = np.zeros(lat.shape)
        clus_bin   = np.zeros(lat.shape)

        #Consider difference in string between model and observation
        if 'ST4' in MODEfile_new:
            #First do simple object data
            simp_bin=f.variables['obs_obj_id']
            simp_bin=simp_bin[:]
            simp_bin[simp_bin < 0] = 0
            #Next do cluster data and raw field
            clus_bin=f.variables['obs_clus_id']
            clus_bin=clus_bin[:]
            clus_bin[clus_bin < 0] = 0
            #Finally raw data
            grid=f.variables['obs_raw'][:]/25.4
        else:
            #First do simple object data
            simp_bin=f.variables['fcst_obj_id']
            simp_bin=simp_bin[:]
            simp_bin[simp_bin < 0] = 0
            #Next do cluster data and raw field
            clus_bin=f.variables['fcst_clus_id']
            clus_bin=clus_bin[:]
            clus_bin[clus_bin < 0] = 0
            #Finally raw data
            grid=f.variables['fcst_raw'][:]/25.4
        
        #Replace missing elements with NaN
        grid[grid < 0] = np.nan
        
        #Convert to boolean matrix
        simp_bin = simp_bin > 0
        clus_bin = clus_bin > 0
        
        #Remove gridded data not in the lat/lon grid specifications
        data_subset=(lat >= latlon_dims[1]-3) & (lat < latlon_dims[3]+3) & (lon >= latlon_dims[0]-3) & (lon < latlon_dims[2]+3)*1
        x_elements_beg=np.argmax(np.diff(data_subset,axis=1)==1, axis=1)
        x_elements_end=np.argmax(np.diff(data_subset,axis=1)==-1, axis=1)
        y_elements_beg=np.argmax(np.diff(data_subset,axis=0)==1, axis=0)
        y_elements_end=np.argmax(np.diff(data_subset,axis=0)==-1, axis=0)
        x_elements_beg=x_elements_beg[x_elements_beg > 0]
        x_elements_end=x_elements_end[x_elements_end > 0]
        y_elements_beg=y_elements_beg[y_elements_beg > 0]
        y_elements_end=y_elements_end[y_elements_end > 0]
        x_beg=np.min(x_elements_beg)
        x_end=np.max(x_elements_end)
        y_beg=np.min(y_elements_beg)
        y_end=np.max(y_elements_end)

        lat=lat[y_beg:y_end,x_beg:x_end]
        lon=lon[y_beg:y_end,x_beg:x_end]
        grid=grid[y_beg:y_end,x_beg:x_end]
        simp_bin=simp_bin[y_beg:y_end,x_beg:x_end]
        clus_bin=clus_bin[y_beg:y_end,x_beg:x_end]
        
        #Remove cluster information not in the lat/lon grid specifications. 
        #First find IDs for simple clusters that are not in the domain. Since
        #cluster clusters do not have lat/lon information, they are removed
        #if any simple clusters are removed.
        if 'ST4' not in MODEfile_new and not np.isnan(np.mean(simp_prop)):
            data_subset = (simp_prop[1,:] >= latlon_dims[1]) & (simp_prop[1,:] < latlon_dims[3]) & \
                (simp_prop[2,:] >= latlon_dims[0]) & (simp_prop[2,:] < latlon_dims[2])
            simp_prop=simp_prop[:,data_subset]
            #Remember obs/model simple clusters to apply to cluster clusters
            clus_ID = simp_prop[0,:]

            #Loop through existing cluster IDs in the clusters
            keep_ID_mod = np.zeros((len(clus_prop[0],)),dtype = np.int)
            keep_ID_obs = np.zeros((len(clus_prop[0],)),dtype = np.int)
            for clusters in range(0,len(clus_ID)):
                if clus_ID[clusters] >= 0:  #model clusters
                    keep_ID_mod=keep_ID_mod+(clus_ID[clusters]==clus_prop[1,:])*1
                elif clus_ID[clusters] < 0: #obs clusters
                    keep_ID_obs=keep_ID_obs+(clus_ID[clusters]==clus_prop[0,:])*1
            
            #If model or obs simple cluster ID exists in the cluster, keep it
            keep_ID = (keep_ID_mod + keep_ID_obs) > 0
            clus_prop = clus_prop[:,keep_ID]      

        data_success = 0 #Success
        f.close() 
        
    else: #If statement, file does not exist
    
        lat  = np.nan
        lon  = np.nan
        grid = np.nan

        simp_bin  = np.nan
        clus_bin  = np.nan

        simp_prop = np.nan
        clus_prop = np.nan
        
        #Model should exist, but doesnt
        data_success = 1 #Failure
    #END if statement to check for file existance

    return(lat, lon, grid, simp_bin, clus_bin, simp_prop, clus_prop, data_success)


###################################################################################
#loadDataMTDV90 loads MTD object data. This includes gridded simple and cluster binary
#data(simp_bin,clus_bin), which separately considers model/observation. Since
#the object attribute property data (e.g. simp_prop/pair_prop) includes both model
#and observation data (if obs exists), the same is true here. Hence, if both model
#and observation are requested, this function will load both to include both in
#object attribute files, but keeps model/obs separate in binary files.
#
#NOTE: The current 2d.txt MTD file includes simple-single and cluster-pairs, but they are
#not well labeled. The first lines start with simple-single forecast objects (e.g. OBJECT_ID=F_1),
#and show how they are merged into clusters (e.g. OBJECT_CAT=CF_1). Observations are then shown
#in the same format. Thereafter, forecast data is shown again for OBJECT_ID and OBJECT_CAT.
#At this point, the data is cluster-pairs for forecast data, with the cluster ID matching the
#observation cluster ID. The forecast cluster ID will match the earlier forecast cluster ID
#if that cluster did not involve multiple mergers, otherwise it is the centroid of the mergers.
#This code will gather the first round of forecast/obs into 'simp_prop' and the second into
#'pair_prop.'
#
#Created 20170310-20170321. MJE.
#Update: Modified code for METv6.0, added cluster object attributes. 20170428-20170503. MJE.
#Update: Added 10th and 50th percentile to simp_prop and pair_prop. 20180911. MJE.
#Update: Modified code to read in METv7.0 changes. 20190313. MJE.
#Update: Round pair_prop and simp_prop to nearest thousandth rather than hundredth. 20200123. MJE.
#Update: Code modified to work with METv9.0. 20201104. MJE
#Update: Increase initialized dimensions for 'simp_prop' and pair_prop' 20201231. MJE
#Update: Fixed minor bug with 'pair_prop' 20210419. MJE.
#
#####################INPUT FILES FOR loadDataMTDV90#############################
#GRIB_PATH_TEMP    = temporary path where files are copied and MET is applied
#MTDfile_new       = QPE string for the netcdf converted data (must point to model, not ST4. ST4 data is in model)
#ismodel           = boolean value, load model data if 1 otherwise load obs data if 0
#latlon_dims       = latitude/longitude dimensions for plotting [WLON,SLAT,ELON,NLAT]
####################OUTPUT FILES FOR loadDataMTDV90#############################
#lat               = grid of latitude from netcdf MODE output
#lon               = grid of longitude from netcdf MODE output
#grid_mod          = grid of raw forecast values
#grid_obs          = grid of raw observation values
#simp_bin          = binary grid of simple information
#clus_bin          = binary grid of cluster information
#simp_prop         = simple centroid info of OBJECT_ID','OBJECT_CAT','TIME_INDEX','AREA','CENTROID_LAT','CENTROID_LON','AXIS_ANG','10TH INTEN PERC','50TH INTEN PERC','90TH INTEN PERC'
#pair_prop         = paired centroid info of OBJECT_ID','OBJECT_CAT','TIME_INDEX','AREA','CENTROID_LAT','CENTROID_LON','AXIS_ANG','10TH INTEN PERC','50TH INTEN PERC','90TH INTEN PERC'
#data_success      = file successfully loaded if equals zero
###################################################################################
#Note: "Simple" means unmerged while "cluster" refers to merged
#"Single" refers to unmatched objects while "pair" refers to matched objects.
#There are 5 MTD ascii files: 1) 2d spatial attributes for single simple objects,
#2) 3d single-simple (ss) objects, 3) 3d single-cluster (sc) objects,
#4) 3d pair-single (ps), and 5) 3d pair-cluster (pc) objects. There is also a netcdf file.

def loadDataMTDV90(GRIB_PATH_TEMP, MTDfile_new, ismodel, latlon_dims):

    #MTDfile_new=MTDfile_new[mod_loc]
    #ismodel=ismodel[mod_loc]

    #Note: OBJECT_CAT formerly called CLUSTER_ID

    head_str_obj    = ['OBJECT_ID']
    head_len_obj    = [11]
    head_str_simp   = ['OBJECT_ID','OBJECT_CAT','TIME_INDEX','AREA','CENTROID_LAT','CENTROID_LON','AXIS_ANG']
    head_len_simp   = [11,            12,           12,         6,       14,           14,            8]

    simp_prop = np.ones((9,10000))*-999
    pair_prop = np.ones((9,10000))*-999

    print(GRIB_PATH_TEMP+'/'+MTDfile_new+'_obj.nc')
    print(GRIB_PATH_TEMP+'/'+MTDfile_new+'_2d.txt')

    #Check to see if file exists
    if os.path.isfile(GRIB_PATH_TEMP+'/'+MTDfile_new+'_obj.nc'):

        #If file exists, try to open it up
        try:

            #####1) First read in the 2d text file to gather centroid intensity and location
            #Open file and read through it
            target = open(GRIB_PATH_TEMP+'/'+MTDfile_new+'_2d.txt','r')
            data = target.readlines()
            target.close()

            #Loop through each line and gather the needed info
            f_count         = 0       #counter by line in file
            f_simp_count    = 0       #counter by each simple attribute ('OBJECT_ID','TIME_INDEX',etc)
            f_pair_count    = 0       #counter by each pair attribute ('OBJECT_ID','TIME_INDEX',etc)
            line_prev       = []      #load the previous line
            pair_load       = False   #reaching paired data line in data files

            for line in data:
                
                #Find location of data in each file using header information
                if f_count == 0:
                    line1 = line
                    array_obj = [line1.find(head_str_obj[0]),line1.find(head_str_obj[0])+head_len_obj[0]]

                if f_count > 0:
                    #Determine if paired objects exist (when objects go from obs back to fcst)
                    if 'F' in line[line1.find(head_str_simp[0])+5:line1.find(head_str_simp[0])+8] and \
                        'O' in line_prev[line1.find(head_str_simp[0])+5:line1.find(head_str_simp[0])+8]: #THIS INSTANCE ONLY HAPPENS ONCE!
                        pair_load = 'TRUE'

                    #Isolate simple cluster model/obs objects, gather stats comparing mod to obs in the form:
                    #[object ID, object cat, time index, area of object, centroid lat, centroid lon, axis angle]

                    for header in range(0,len(head_str_simp)):

                        #Gather data grabbing arrays; special conditions for getting OBJECT_ID/OBJECT_CAT
                        if header == 0 or header == 1:
                            array_simp = [line1.find(head_str_simp[header])+4,line1.find(head_str_simp[header])+head_len_simp[header]]
                        else:
                            array_simp = [line1.find(head_str_simp[header]),line1.find(head_str_simp[header])+head_len_simp[header]]

                        if pair_load: #Paired data saved to 'pair_prop'

                            if ('F' in line[array_obj[0]:array_obj[-1]]): # and 'ST4' not in MTDfile_new:

                                #Special consideration for cluster data
                                if head_str_simp[header] == 'OBJECT_ID': #object ID
                                    temp_d = line[array_simp[0]:array_simp[-1]]
                                    temp_d = temp_d.replace('CF','')
                                    pair_prop[header,f_pair_count] = float(temp_d)
                                elif head_str_simp[header] == 'OBJECT_CAT': #Cluster ID
                                    if 'NA' in line[array_simp[0]:array_simp[-1]]:
                                        pair_prop[header,f_pair_count] = np.NaN
                                    else:
                                        temp_d = line[array_simp[0]+4:array_simp[-1]]
                                        temp_d = temp_d.replace('F','')
                                        pair_prop[header,f_pair_count] = float(temp_d)
                                else:
                                    pair_prop[header,f_pair_count] = float(line[array_simp[0]:array_simp[-1]])

                                if header == len(head_str_simp)-1:
                                    f_pair_count += 1

                            elif ('O' in line[array_obj[0]:array_obj[-1]]): # and 'ST4' in MTDfile_new:

                                #Make observation ID's negative to differentiate from model
                                if head_str_simp[header] == 'OBJECT_ID': #object ID
                                    temp_d = line[array_simp[0]:array_simp[-1]]
                                    temp_d = temp_d.replace('CO','')
                                    pair_prop[header,f_pair_count] = -float(temp_d)
                                elif head_str_simp[header] == 'OBJECT_CAT': #Cluster ID
                                    if 'NA' in line[array_simp[0]:array_simp[-1]]:
                                        pair_prop[header,f_pair_count] = np.NaN
                                    else:
                                        temp_d = line[array_simp[0]+4:array_simp[-1]]
                                        temp_d = temp_d.replace('O','')
                                        pair_prop[header,f_pair_count] = -float(temp_d)
                                else:
                                    pair_prop[header,f_pair_count] = float(line[array_simp[0]:array_simp[-1]])

                                if header == len(head_str_simp)-1:
                                    f_pair_count += 1

                        else: #non-paired data saved to 'simp_prop'

                            if ('F' in line[array_obj[0]:array_obj[-1]]): # and 'ST4' not in MTDfile_new:

                                #Special consideration for cluster data
                                if head_str_simp[header] == 'OBJECT_ID': #object ID
                                    temp_d = line[array_simp[0]:array_simp[-1]]
                                    temp_d = temp_d.replace('F','')
                                    simp_prop[header,f_simp_count] = float(temp_d)
                                elif head_str_simp[header] == 'OBJECT_CAT': #Cluster ID
                                    if 'NA' in line[array_simp[0]:array_simp[-1]]:
                                        simp_prop[header,f_simp_count] = np.NaN
                                    else:
                                        temp_d = line[array_simp[0]+4:array_simp[-1]]
                                        temp_d = temp_d.replace('F','')
                                        simp_prop[header,f_simp_count] = float(temp_d)
                                else:
                                    simp_prop[header,f_simp_count] = float(line[array_simp[0]:array_simp[-1]])

                                if header == len(head_str_simp)-1:
                                    f_simp_count += 1

                            elif ('O' in line[array_obj[0]:array_obj[-1]]): # and 'ST4' in MTDfile_new:

                                #Make observation ID's negative to differentiate from model
                                if head_str_simp[header] == 'OBJECT_ID': #object ID
                                    temp_d = line[array_simp[0]:array_simp[-1]]
                                    temp_d = temp_d.replace('O','')
                                    simp_prop[header,f_simp_count] = -float(temp_d)
                                elif head_str_simp[header] == 'OBJECT_CAT': #Cluster ID
                                    if 'NA' in line[array_simp[0]:array_simp[-1]]:
                                        simp_prop[header,f_simp_count] = np.NaN
                                    else:
                                        temp_d = line[array_simp[0]+4:array_simp[-1]]
                                        temp_d = temp_d.replace('O','')
                                        simp_prop[header,f_simp_count] = -float(temp_d)
                                else:
                                    simp_prop[header,f_simp_count] = float(line[array_simp[0]:array_simp[-1]])

                                if header == len(head_str_simp)-1:
                                    f_simp_count += 1

                line_prev = line
                f_count += 1

            #Create obj. intensity since METv6.0 doesnt output it directly. First initialize additional row
            simp_prop = np.concatenate((simp_prop,np.full((1,simp_prop.shape[1]),np.NaN)),axis=0)
            pair_prop = np.concatenate((pair_prop,np.full((1,pair_prop.shape[1]),np.NaN)),axis=0)

            #Remove unpopulated dimensions
            simp_prop = simp_prop[:, np.nanmean(simp_prop[0:7,:] == -999, axis=0) == 0]
            pair_prop = pair_prop[:, np.nanmean(pair_prop[0:7,:] == -999, axis=0) == 0]

            #####2) Next read in the centroid shape data from the netcdf file
            f = Dataset(GRIB_PATH_TEMP+'/'+MTDfile_new+'_obj.nc', "a", format="NETCDF4")
            lat=f.variables['lat'][:]
            lon=f.variables['lon'][:]

            #Try loading gridded obs to match data in 'simp_prop'
            try:
                simp_bin_obs = f.variables['obs_object_id']
                simp_bin_obs = simp_bin_obs[:]
                simp_bin_obs[simp_bin_obs < 0] = 0

                #Cluster object data
                try: #May not always have clusters
                    clus_bin_obs = f.variables['obs_cluster_id']
                    clus_bin_obs = clus_bin_obs[:]
                    clus_bin_obs[clus_bin_obs < 0] = 0
                except KeyError:
                    clus_bin_obs  = np.zeros((simp_bin_obs.shape))

                #Rraw data
                grid_obs = f.variables['obs_raw'][:]/25.4
                grid_obs[grid_obs < 0] = np.nan
            except:
                 grid_obs = []

            #There is always gridded forecast object data to load
            simp_bin_mod = f.variables['fcst_object_id']
            simp_bin_mod = simp_bin_mod[:]
            simp_bin_mod[simp_bin_mod < 0] = 0

            #Cluster object data
            try: #May not always have clusters
                clus_bin_mod = f.variables['fcst_cluster_id']
                clus_bin_mod = clus_bin_mod[:]
                clus_bin_mod[clus_bin_mod < 0] = 0
            except KeyError:
                clus_bin_mod = np.zeros((simp_bin_mod.shape))

            #Raw data
            grid_mod = f.variables['fcst_raw'][:]/25.4
            grid_mod[grid_mod < 0] = np.nan

            #Loop through each line of 'simp_prop' and determine obj. 10,50,90th prctile
            #['OBJECT_ID','OBJECT_CAT','TIME_INDEX','AREA','CENTROID_LAT','CENTROID_LON','AXIS_ANG','INTENSITY_10','INTENSITY_50','INTENSITY_90']

            for line_c in range(0,simp_prop.shape[1]):

                #Determine object ID
                obj_id = int(simp_prop[0][line_c])
                #Determine the forecast hour
                try:
                    fcst_hr = int(simp_prop[2][line_c])
                except ValueError:
                    fcst_hr = -999 #data missing

                if fcst_hr != -999: #data exists                                                                                                                                                                                                                                                                                                                                                                                                                                          
                    if obj_id < 0: #Load obs data
                        simp_prop[7,line_c] = np.round(np.nanpercentile(grid_obs[fcst_hr,simp_bin_obs[fcst_hr,:,:] == np.abs(obj_id)], 10),3)
                        simp_prop[8,line_c] = np.round(np.nanpercentile(grid_obs[fcst_hr,simp_bin_obs[fcst_hr,:,:] == np.abs(obj_id)], 50),3)
                        simp_prop[9,line_c] = np.round(np.percentile(grid_obs[fcst_hr,simp_bin_obs[fcst_hr,:,:] == np.abs(obj_id)], 90),3)
                    else:          #Load model data
                        simp_prop[7,line_c] = np.round(np.nanpercentile(grid_mod[fcst_hr,simp_bin_mod[fcst_hr,:,:] == np.abs(obj_id)], 10),3)
                        simp_prop[8,line_c] = np.round(np.nanpercentile(grid_mod[fcst_hr,simp_bin_mod[fcst_hr,:,:] == np.abs(obj_id)], 50),3)
                        simp_prop[9,line_c] = np.round(np.nanpercentile(grid_mod[fcst_hr,simp_bin_mod[fcst_hr,:,:] == np.abs(obj_id)], 90),3)
                else: #data missing
                    if obj_id < 0: #Load obs data
                        simp_prop[7,line_c] = np.NaN
                        simp_prop[8,line_c] = np.NaN
                        simp_prop[9,line_c] = np.NaN
                    else:          #Load model data
                        simp_prop[7,line_c] = np.NaN
                        simp_prop[8,line_c] = np.NaN
                        simp_prop[9,line_c] = np.NaN

            #Loop through each line of 'pair_prop' and determine obj. 10,50,90th prctile
            #['OBJECT_ID','TIME_INDEX','AREA','CENTROID_LAT','CENTROID_LON','AXIS_ANG','INTENSITY_10','INTENSITY_50','INTENSITY_90']
            for line_c in range(0,pair_prop.shape[1]):

                #Determine object ID
                obj_id = int(pair_prop[0][line_c])
                #Determine the forecast hour
                try:
                    fcst_hr = int(pair_prop[2][line_c])
                except ValueError:
                    fcst_hr = -999 #data missing

                if fcst_hr != 999: #data exists                                                                                                                                                                                                                                                                                                                                                                                                                                           
                    if obj_id < 0: #Load obs data
                        try:
                            pair_prop[7,line_c] = np.round(np.nanpercentile(grid_obs[fcst_hr,clus_bin_obs[fcst_hr,:,:] == np.abs(obj_id)], 10),3)
                            pair_prop[8,line_c] = np.round(np.nanpercentile(grid_obs[fcst_hr,clus_bin_obs[fcst_hr,:,:] == np.abs(obj_id)], 50),3)
                            pair_prop[9,line_c] = np.round(np.nanpercentile(grid_obs[fcst_hr,clus_bin_obs[fcst_hr,:,:] == np.abs(obj_id)], 90),3)
                        except ValueError:
                            pair_prop[7,line_c] = np.NaN
                            pair_prop[8,line_c] = np.NaN
                            pair_prop[9,line_c] = np.NaN

                    else:          #Load model data
                        try:
                            pair_prop[7,line_c] = np.round(np.nanpercentile(grid_mod[fcst_hr,clus_bin_mod[fcst_hr,:,:] == np.abs(obj_id)], 10),3)
                            pair_prop[8,line_c] = np.round(np.nanpercentile(grid_mod[fcst_hr,clus_bin_mod[fcst_hr,:,:] == np.abs(obj_id)], 50),3)
                            pair_prop[9,line_c] = np.round(np.nanpercentile(grid_mod[fcst_hr,clus_bin_mod[fcst_hr,:,:] == np.abs(obj_id)], 90),3)
                        except ValueError:
                            pair_prop[7,line_c] = np.NaN
                            pair_prop[8,line_c] = np.NaN
                            pair_prop[9,line_c] = np.NaN

                else: #data missing
                    if obj_id < 0: #Load obs data
                        pair_prop[7,line_c] = np.NaN
                        pair_prop[8,line_c] = np.NaN
                        pair_prop[9,line_c] = np.NaN
                    else:          #Load model data
                        pair_prop[7,line_c] = np.NaN
                        pair_prop[8,line_c] = np.NaN
                        pair_prop[9,line_c] = np.NaN

            #Output only mod or obs in 'bin' matrices, convert to boolean
            if ismodel == 0:
               simp_bin = simp_bin_obs
               clus_bin = clus_bin_obs
            else:
               simp_bin = simp_bin_mod
               clus_bin = clus_bin_mod

            #Remove gridded data not in the lat/lon grid specifications
            data_subset=(lat >= latlon_dims[1]-3) & (lat < latlon_dims[3]+3) & (lon >= latlon_dims[0]-3) & (lon < latlon_dims[2]+3)*1
            x_elements_beg=np.argmax(np.diff(data_subset,axis=1)==1, axis=1)
            x_elements_end=np.argmax(np.diff(data_subset,axis=1)==-1, axis=1)
            y_elements_beg=np.argmax(np.diff(data_subset,axis=0)==1, axis=0)
            y_elements_end=np.argmax(np.diff(data_subset,axis=0)==-1, axis=0)
            x_elements_beg=x_elements_beg[x_elements_beg > 0]
            x_elements_end=x_elements_end[x_elements_end > 0]
            y_elements_beg=y_elements_beg[y_elements_beg > 0]
            y_elements_end=y_elements_end[y_elements_end > 0]
            x_beg=np.min(x_elements_beg)
            x_end=np.max(x_elements_end)
            y_beg=np.min(y_elements_beg)
            y_end=np.max(y_elements_end)
            lat      = lat[y_beg:y_end,x_beg:x_end]
            lon      = lon[y_beg:y_end,x_beg:x_end]
            try:
                grid_obs = np.transpose(grid_obs[:,y_beg:y_end,x_beg:x_end],(1, 2, 0))
            except TypeError:
                pass
            grid_mod = np.transpose(grid_mod[:,y_beg:y_end,x_beg:x_end],(1, 2, 0))
            simp_bin = np.transpose(simp_bin[:,y_beg:y_end,x_beg:x_end],(1, 2, 0))
            clus_bin = np.transpose(clus_bin[:,y_beg:y_end,x_beg:x_end],(1, 2, 0))

            #Remove cluster information not in the lat/lon grid specifications.
            #First find IDs for simple clusters that are not in the domain. Since
            #cluster clusters do not have lat/lon information, they are removed
            #if any simple clusters are removed.
            data_subset = (simp_prop[4,:] >= latlon_dims[1]) & (simp_prop[4,:] < latlon_dims[3]) & \
                (simp_prop[5,:] >= latlon_dims[0]) & (simp_prop[5,:] < latlon_dims[2])
            simp_prop=simp_prop[:,data_subset]

            data_subset = (pair_prop[4,:] >= latlon_dims[1]) & (pair_prop[4,:] < latlon_dims[3]) & \
                (pair_prop[5,:] >= latlon_dims[0]) & (pair_prop[5,:] < latlon_dims[2])
            pair_prop=pair_prop[:,data_subset]

            data_success = np.zeros((clus_bin.shape[2])) #Success
            f.close()
        except (RuntimeError, TypeError, NameError, ValueError, KeyError): #File exists but has no clusters

            lat = f.variables['lat'][:]
            lon = f.variables['lon'][:]

            try:
                grid_obs = f.variables['obs_raw'][:]/25.4
            except KeyError:
                grid_obs = []

            grid_mod = f.variables['fcst_raw'][:]/25.4

            simp_bin  = np.zeros((grid_mod.shape[0], grid_mod.shape[1], grid_mod.shape[2]),dtype=np.bool)
            clus_bin  = np.zeros((grid_mod.shape[0], grid_mod.shape[1], grid_mod.shape[2]),dtype=np.bool)

            simp_prop = np.nan
            pair_prop = np.nan

            #Model should exist and does
            data_success = np.zeros((clus_bin.shape[2])) #Success
            f.close()
        #END try statement

    else: #If statement, file does not exist

        lat          = np.nan
        lon          = np.nan
        grid_mod     = np.nan
        grid_obs     = np.nan

        simp_bin     = np.nan
        clus_bin     = np.nan

        simp_prop    = np.nan
        pair_prop    = np.nan

        #Model should exist, but doesnt
        data_success = 1 #Failure
    #END if statement to check for file existance

    return(lat, lon, grid_mod, grid_obs, simp_bin, clus_bin, simp_prop, pair_prop, data_success)
    
###################################################################################
#loadDataMTD loads MTD object data. This includes gridded simple and cluster binary
#data(simp_bin,clus_bin), which separately considers model/observation. Since 
#the object attribute property data (e.g. simp_prop/pair_prop) includes both model 
#and observation data (if obs exists), the same is true here. Hence, if both model 
#and observation are requested, this function will load both to include both in 
#object attribute files, but keeps model/obs separate in binary files.
#
#NOTE: The current 2d.txt MTD file includes simple-single and cluster-pairs, but they are
#not well labeled. The first lines start with simple-single forecast objects (e.g. OBJECT_ID=F_1), 
#and show how they are merged into clusters (e.g. OBJECT_CAT=CF_1). Observations are then shown
#in the same format. Thereafter, forecast data is shown again for OBJECT_ID and OBJECT_CAT.
#At this point, the data is cluster-pairs for forecast data, with the cluster ID matching the
#observation cluster ID. The forecast cluster ID will match the earlier forecast cluster ID
#if that cluster did not involve multiple mergers, otherwise it is the centroid of the mergers.
#This code will gather the first round of forecast/obs into 'simp_prop' and the second into
#'pair_prop.'
#
#Created 20170310-20170321. MJE.
#Update: Modified code for METv6.0, added cluster object attributes. 20170428-20170503. MJE.
#Update: Added 10th and 50th percentile to simp_prop and pair_prop. 20180911. MJE.
#Update: Modified code to read in METv7.0 changes. 20190313. MJE.
#Update: Round pair_prop and simp_prop to nearest thousandth rather than hundredth. 20200123. MJE.
#
#####################INPUT FILES FOR loadDataMODE#############################
#GRIB_PATH_TEMP    = temporary path where files are copied and MET is applied
#MTDfile_new       = QPE string for the netcdf converted data (must point to model, not ST4. ST4 data is in model)
#ismodel           = boolean value, load model data if 1 otherwise load obs data if 0
#latlon_dims       = latitude/longitude dimensions for plotting [WLON,SLAT,ELON,NLAT]
####################OUTPUT FILES FOR loadDataMODE#############################
#lat               = grid of latitude from netcdf MODE output
#lon               = grid of longitude from netcdf MODE output
#grid_mod          = grid of raw forecast values
#grid_obs          = grid of raw observation values
#simp_bin          = binary grid of simple information
#clus_bin          = binary grid of cluster information
#simp_prop         = simple centroid info of OBJECT_ID','OBJECT_CAT','TIME_INDEX','AREA','CENTROID_LAT','CENTROID_LON','AXIS_ANG','10TH INTEN PERC','50TH INTEN PERC','90TH INTEN PERC'
#pair_prop         = paired centroid info of OBJECT_ID','OBJECT_CAT','TIME_INDEX','AREA','CENTROID_LAT','CENTROID_LON','AXIS_ANG','10TH INTEN PERC','50TH INTEN PERC','90TH INTEN PERC'
#data_success      = file successfully loaded if equals zero
###################################################################################
#Note: "Simple" means unmerged while "cluster" refers to merged
#"Single" refers to unmatched objects while "pair" refers to matched objects.
#There are 5 MTD ascii files: 1) 2d spatial attributes for single simple objects,
#2) 3d single-simple (ss) objects, 3) 3d single-cluster (sc) objects,
#4) 3d pair-single (ps), and 5) 3d pair-cluster (pc) objects. There is also a netcdf file.

def loadDataMTD(GRIB_PATH_TEMP, MTDfile_new, ismodel, latlon_dims):

    #MTDfile_new=MTDfile_new[mod_loc]
    #ismodel=ismodel[mod_loc]
    
    #Note: OBJECT_CAT formerly called CLUSTER_ID
    
    head_str_obj    = ['OBJECT_ID'] 
    head_len_obj    = [11]
    head_str_simp   = ['OBJECT_ID','OBJECT_CAT','TIME_INDEX','AREA','CENTROID_LAT','CENTROID_LON','AXIS_ANG']
    head_len_simp   = [11,            12,           12,         6,       14,           14,            8]    
    
    simp_prop = np.ones((9,10000))*-999
    pair_prop = np.ones((9,10000))*-999

    #Check to see if file exists
    if os.path.isfile(GRIB_PATH_TEMP+'/'+MTDfile_new+'_obj.nc'): 
        
        #If file exists, try to open it up
        try:
    
            
            #####1) First read in the 2d text file to gather centroid intensity and location
            #Open file and read through it
            target = open(GRIB_PATH_TEMP+'/'+MTDfile_new+'_2d.txt','r')
            data = target.readlines()
            target.close()

            #Loop through each line and gather the needed info
            f_count         = 0       #counter by line in file
            f_simp_count    = 0       #counter by each simple attribute ('OBJECT_ID','TIME_INDEX',etc)
            f_pair_count    = 0       #counter by each pair attribute ('OBJECT_ID','TIME_INDEX',etc)
            line_prev       = []      #load the previous line
            pair_load       = False   #reaching paired data line in data files

            for line in data:
                #Find location of data in each file using header information
                if f_count == 0:
                    line1 = line
                    array_obj = [line1.find(head_str_obj[0]),line1.find(head_str_obj[0])+head_len_obj[0]]
                
                if f_count > 0:
                    #Determine if paired objects exist (when objects go from obs back to fcst)
                    if 'F' in line[line1.find(head_str_simp[0])+5:line1.find(head_str_simp[0])+8] and \
                        'O' in line_prev[line1.find(head_str_simp[0])+5:line1.find(head_str_simp[0])+8]: #THIS INSTANCE ONLY HAPPENS ONCE!
                        pair_load = 'TRUE'
                        
                    #Isolate simple cluster model/obs objects, gather stats comparing mod to obs in the form:
                    #[object ID, object cat, time index, area of object, centroid lat, centroid lon, axis angle]
                    
                    for header in range(0,len(head_str_simp)):
                    
                        #Gather data grabbing arrays; special conditions for getting OBJECT_ID/OBJECT_CAT
                        if header == 0 or header == 1:
                            array_simp = [line1.find(head_str_simp[header])+4,line1.find(head_str_simp[header])+head_len_simp[header]]
                        else:
                            array_simp = [line1.find(head_str_simp[header]),line1.find(head_str_simp[header])+head_len_simp[header]]
                        
                        if pair_load: #Paired data saved to 'pair_prop'

                            if ('F' in line[array_obj[0]:array_obj[-1]]): # and 'ST4' not in MTDfile_new:
                                
                                #Special consideration for cluster data
                                if head_str_simp[header] == 'OBJECT_ID': #object ID
                                    temp_d = line[array_simp[0]:array_simp[-1]]
                                    temp_d = temp_d.replace('F','')
                                    pair_prop[header,f_pair_count] = float(temp_d)
                                elif head_str_simp[header] == 'OBJECT_CAT': #Cluster ID
                                    if 'NA' in line[array_simp[0]:array_simp[-1]]:
                                        pair_prop[header,f_pair_count] = np.NaN
                                    else:
                                        temp_d = line[array_simp[0]+4:array_simp[-1]]
                                        temp_d = temp_d.replace('F','')
                                        pair_prop[header,f_pair_count] = float(temp_d)
                                else:
                                    pair_prop[header,f_pair_count] = float(line[array_simp[0]:array_simp[-1]])
                                
                                if header == len(head_str_simp)-1:
                                    f_pair_count += 1
                                    
                            elif ('O' in line[array_obj[0]:array_obj[-1]]): # and 'ST4' in MTDfile_new:
                                
                                #Make observation ID's negative to differentiate from model
                                if head_str_simp[header] == 'OBJECT_ID': #object ID
                                    temp_d = line[array_simp[0]:array_simp[-1]]
                                    temp_d = temp_d.replace('O','')
                                    pair_prop[header,f_pair_count] = -float(temp_d)
                                elif head_str_simp[header] == 'OBJECT_CAT': #Cluster ID
                                    if 'NA' in line[array_simp[0]:array_simp[-1]]:
                                        pair_prop[header,f_pair_count] = np.NaN
                                    else:
                                        temp_d = line[array_simp[0]+4:array_simp[-1]]
                                        temp_d = temp_d.replace('O','')
                                        pair_prop[header,f_pair_count] = -float(temp_d)
                                else:
                                    pair_prop[header,f_pair_count] = float(line[array_simp[0]:array_simp[-1]])    
                                
                                if header == len(head_str_simp)-1:
                                    f_pair_count += 1
                                                                                          
                        else: #non-paired data saved to 'simp_prop'

                            if ('F' in line[array_obj[0]:array_obj[-1]]): # and 'ST4' not in MTDfile_new:
                                
                                #Special consideration for cluster data
                                if head_str_simp[header] == 'OBJECT_ID': #object ID
                                    temp_d = line[array_simp[0]:array_simp[-1]]
                                    temp_d = temp_d.replace('F','')
                                    simp_prop[header,f_simp_count] = float(temp_d)
                                elif head_str_simp[header] == 'OBJECT_CAT': #Cluster ID
                                    if 'NA' in line[array_simp[0]:array_simp[-1]]:
                                        simp_prop[header,f_simp_count] = np.NaN
                                    else:
                                        temp_d = line[array_simp[0]+4:array_simp[-1]]
                                        temp_d = temp_d.replace('F','')
                                        simp_prop[header,f_simp_count] = float(temp_d)
                                else:
                                    simp_prop[header,f_simp_count] = float(line[array_simp[0]:array_simp[-1]])  
                                
                                if header == len(head_str_simp)-1:
                                    f_simp_count += 1
                                    
                            elif ('O' in line[array_obj[0]:array_obj[-1]]): # and 'ST4' in MTDfile_new:
                                
                                #Make observation ID's negative to differentiate from model
                                if head_str_simp[header] == 'OBJECT_ID': #object ID
                                    temp_d = line[array_simp[0]:array_simp[-1]]
                                    temp_d = temp_d.replace('O','')
                                    simp_prop[header,f_simp_count] = -float(temp_d)
                                elif head_str_simp[header] == 'OBJECT_CAT': #Cluster ID
                                    if 'NA' in line[array_simp[0]:array_simp[-1]]:
                                        simp_prop[header,f_simp_count] = np.NaN
                                    else:
                                        temp_d = line[array_simp[0]+4:array_simp[-1]]
                                        temp_d = temp_d.replace('O','')
                                        simp_prop[header,f_simp_count] = -float(temp_d)
                                else:
                                    simp_prop[header,f_simp_count] = float(line[array_simp[0]:array_simp[-1]])    
                                
                                if header == len(head_str_simp)-1:
                                    f_simp_count += 1
                                
                line_prev = line
                f_count += 1

            #Create obj. intensity since METv6.0 doesnt output it directly. First initialize additional row
            simp_prop = np.concatenate((simp_prop,np.full((1,simp_prop.shape[1]),np.NaN)),axis=0)
            pair_prop = np.concatenate((pair_prop,np.full((1,pair_prop.shape[1]),np.NaN)),axis=0)
            
            #Remove unpopulated dimensions
            simp_prop = simp_prop[:, np.nanmean(simp_prop[0:7,:] == -999, axis=0) == 0]
            pair_prop = pair_prop[:, np.nanmean(pair_prop[0:7,:] == -999, axis=0) == 0]

            #####2) Next read in the centroid shape data from the netcdf file
            f = Dataset(GRIB_PATH_TEMP+'/'+MTDfile_new+'_obj.nc', "a", format="NETCDF4")
            lat=f.variables['lat'][:]
            lon=f.variables['lon'][:]

            #Try loading gridded obs to match data in 'simp_prop'
            try:
                simp_bin_obs = f.variables['obs_object_id']
                simp_bin_obs = simp_bin_obs[:]
                simp_bin_obs[simp_bin_obs < 0] = 0

                #Cluster object data
                try: #May not always have clusters
                    clus_bin_obs = f.variables['obs_cluster_id']
                    clus_bin_obs = clus_bin_obs[:]
                    clus_bin_obs[clus_bin_obs < 0] = 0
                except KeyError:
                    clus_bin_obs  = np.zeros((simp_bin_obs.shape))

                #Rraw data
                grid_obs = f.variables['obs_raw'][:]/25.4
                grid_obs[grid_obs < 0] = np.nan
            except:
                 grid_obs = []

            #There is always gridded forecast object data to load
            simp_bin_mod = f.variables['fcst_object_id']
            simp_bin_mod = simp_bin_mod[:]
            simp_bin_mod[simp_bin_mod < 0] = 0

            #Cluster object data
            try: #May not always have clusters
                clus_bin_mod = f.variables['fcst_cluster_id']
                clus_bin_mod = clus_bin_mod[:]
                clus_bin_mod[clus_bin_mod < 0] = 0
            except KeyError:
                clus_bin_mod = np.zeros((simp_bin_mod.shape))

            #Raw data
            grid_mod = f.variables['fcst_raw'][:]/25.4
            grid_mod[grid_mod < 0] = np.nan

            #Loop through each line of 'simp_prop' and determine obj. 10,50,90th prctile 
            #['OBJECT_ID','OBJECT_CAT','TIME_INDEX','AREA','CENTROID_LAT','CENTROID_LON','AXIS_ANG','INTENSITY_10','INTENSITY_50','INTENSITY_90'] 
            for line_c in range(0,simp_prop.shape[1]):

                #Determine object ID
                obj_id = int(simp_prop[0][line_c])
                #Determine the forecast hour
                try:
                    fcst_hr = int(simp_prop[2][line_c])
                except ValueError:
                    fcst_hr = -999 #data missing

                if fcst_hr != -999: #data exists                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     
                    if obj_id < 0: #Load obs data
                        simp_prop[7,line_c] = np.round(np.nanpercentile(grid_obs[fcst_hr,simp_bin_obs[fcst_hr,:,:] == np.abs(obj_id)], 10),3)
                        simp_prop[8,line_c] = np.round(np.nanpercentile(grid_obs[fcst_hr,simp_bin_obs[fcst_hr,:,:] == np.abs(obj_id)], 50),3)
                        simp_prop[9,line_c] = np.round(np.percentile(grid_obs[fcst_hr,simp_bin_obs[fcst_hr,:,:] == np.abs(obj_id)], 90),3)
                    else:          #Load model data
                        simp_prop[7,line_c] = np.round(np.nanpercentile(grid_mod[fcst_hr,simp_bin_mod[fcst_hr,:,:] == np.abs(obj_id)], 10),3)
                        simp_prop[8,line_c] = np.round(np.nanpercentile(grid_mod[fcst_hr,simp_bin_mod[fcst_hr,:,:] == np.abs(obj_id)], 50),3)
                        simp_prop[9,line_c] = np.round(np.nanpercentile(grid_mod[fcst_hr,simp_bin_mod[fcst_hr,:,:] == np.abs(obj_id)], 90),3)
                else: #data missing
                    if obj_id < 0: #Load obs data
                        simp_prop[7,line_c] = np.NaN
                        simp_prop[8,line_c] = np.NaN
                        simp_prop[9,line_c] = np.NaN
                    else:          #Load model data
                        simp_prop[7,line_c] = np.NaN
                        simp_prop[8,line_c] = np.NaN 
                        simp_prop[9,line_c] = np.NaN  

            #Loop through each line of 'pair_prop' and determine obj. 10,50,90th prctile 
            #['OBJECT_ID','TIME_INDEX','AREA','CENTROID_LAT','CENTROID_LON','AXIS_ANG','INTENSITY_10','INTENSITY_50','INTENSITY_90']  
            for line_c in range(0,pair_prop.shape[1]):

                #Determine object ID
                obj_id = int(pair_prop[0][line_c])
                #Determine the forecast hour
                try:
                    fcst_hr = int(pair_prop[2][line_c])
                except ValueError:
                    fcst_hr = -999 #data missing

                if fcst_hr != 999: #data exists                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     
                    if obj_id < 0: #Load obs data
                        pair_prop[7,line_c] = np.round(np.nanpercentile(grid_obs[fcst_hr,clus_bin_obs[fcst_hr,:,:] == np.abs(obj_id)], 10),3)
                        pair_prop[8,line_c] = np.round(np.nanpercentile(grid_obs[fcst_hr,clus_bin_obs[fcst_hr,:,:] == np.abs(obj_id)], 50),3)
                        pair_prop[9,line_c] = np.round(np.nanpercentile(grid_obs[fcst_hr,clus_bin_obs[fcst_hr,:,:] == np.abs(obj_id)], 90),3)
                    else:          #Load model data
                        pair_prop[7,line_c] = np.round(np.nanpercentile(grid_mod[fcst_hr,clus_bin_mod[fcst_hr,:,:] == np.abs(obj_id)], 10),3)
                        pair_prop[8,line_c] = np.round(np.nanpercentile(grid_mod[fcst_hr,clus_bin_mod[fcst_hr,:,:] == np.abs(obj_id)], 50),3)
                        pair_prop[9,line_c] = np.round(np.nanpercentile(grid_mod[fcst_hr,clus_bin_mod[fcst_hr,:,:] == np.abs(obj_id)], 90),3)
                else: #data missing
                    if obj_id < 0: #Load obs data
                        pair_prop[7,line_c] = np.NaN
                        pair_prop[8,line_c] = np.NaN
                        pair_prop[9,line_c] = np.NaN
                    else:          #Load model data
                        pair_prop[7,line_c] = np.NaN
                        pair_prop[8,line_c] = np.NaN
                        pair_prop[9,line_c] = np.NaN


            #Output only mod or obs in 'bin' matrices, convert to boolean
            if ismodel == 0:
               simp_bin = simp_bin_obs
               clus_bin = clus_bin_obs
            else:
               simp_bin = simp_bin_mod
               clus_bin = clus_bin_mod
          
            #Remove gridded data not in the lat/lon grid specifications
            data_subset=(lat >= latlon_dims[1]-3) & (lat < latlon_dims[3]+3) & (lon >= latlon_dims[0]-3) & (lon < latlon_dims[2]+3)*1
            x_elements_beg=np.argmax(np.diff(data_subset,axis=1)==1, axis=1)
            x_elements_end=np.argmax(np.diff(data_subset,axis=1)==-1, axis=1)
            y_elements_beg=np.argmax(np.diff(data_subset,axis=0)==1, axis=0)
            y_elements_end=np.argmax(np.diff(data_subset,axis=0)==-1, axis=0)
            x_elements_beg=x_elements_beg[x_elements_beg > 0]
            x_elements_end=x_elements_end[x_elements_end > 0]
            y_elements_beg=y_elements_beg[y_elements_beg > 0]
            y_elements_end=y_elements_end[y_elements_end > 0]
            x_beg=np.min(x_elements_beg)
            x_end=np.max(x_elements_end)
            y_beg=np.min(y_elements_beg)
            y_end=np.max(y_elements_end)

            lat      = lat[y_beg:y_end,x_beg:x_end]
            lon      = lon[y_beg:y_end,x_beg:x_end]
            try:
                grid_obs = np.transpose(grid_obs[:,y_beg:y_end,x_beg:x_end],(1, 2, 0))
            except TypeError:
                pass
            grid_mod = np.transpose(grid_mod[:,y_beg:y_end,x_beg:x_end],(1, 2, 0))
            simp_bin = np.transpose(simp_bin[:,y_beg:y_end,x_beg:x_end],(1, 2, 0))
            clus_bin = np.transpose(clus_bin[:,y_beg:y_end,x_beg:x_end],(1, 2, 0))
               
            #Remove cluster information not in the lat/lon grid specifications. 
            #First find IDs for simple clusters that are not in the domain. Since
            #cluster clusters do not have lat/lon information, they are removed
            #if any simple clusters are removed.
            data_subset = (simp_prop[4,:] >= latlon_dims[1]) & (simp_prop[4,:] < latlon_dims[3]) & \
                (simp_prop[5,:] >= latlon_dims[0]) & (simp_prop[5,:] < latlon_dims[2])
            simp_prop=simp_prop[:,data_subset]
            
            data_subset = (pair_prop[4,:] >= latlon_dims[1]) & (pair_prop[4,:] < latlon_dims[3]) & \
                (pair_prop[5,:] >= latlon_dims[0]) & (pair_prop[5,:] < latlon_dims[2])
            pair_prop=pair_prop[:,data_subset]

            data_success = np.zeros((clus_bin.shape[2])) #Success
            f.close() 
        except (RuntimeError, TypeError, NameError, ValueError, KeyError): #File exists but has no clusters
                        
            lat = f.variables['lat'][:]
            lon = f.variables['lon'][:]

            try:
                grid_obs = f.variables['obs_raw'][:]/25.4    
            except KeyError:
                grid_obs = []
            
            grid_mod = f.variables['fcst_raw'][:]/25.4  
   
            simp_bin  = np.zeros((grid_mod.shape[0], grid_mod.shape[1], grid_mod.shape[2]),dtype=np.bool)
            clus_bin  = np.zeros((grid_mod.shape[0], grid_mod.shape[1], grid_mod.shape[2]),dtype=np.bool)
            
            simp_prop = np.nan
            pair_prop = np.nan

            #Model should exist and does
            data_success = np.zeros((clus_bin.shape[2])) #Success
            f.close() 
        #END try statement
        
    else: #If statement, file does not exist
    
        lat          = np.nan
        lon          = np.nan
        grid_mod     = np.nan
        grid_obs     = np.nan
        
        simp_bin     = np.nan
        clus_bin     = np.nan
        
        simp_prop    = np.nan
        pair_prop    = np.nan

        #Model should exist, but doesnt
        data_success = 1 #Failure
    #END if statement to check for file existance

    return(lat, lon, grid_mod, grid_obs, simp_bin, clus_bin, simp_prop, pair_prop, data_success)
    
###################################################################################
#THIS FUNCTION LOADS THE PAIRED OBJECTS CREATED RETROSPECTIVELY USING 
#'mtd_retroruns_save.py.' ALL OF THE DATES ARE LOADED INSIDE OF THIS FUNCTION
#AND THE STATISTICS ARE AGGREGATED SPATIALLY. THERE IS A FILTERING OPTION BY 
#FORECAST HOUR, DIURNAL HOUR, AND SPATIALLY. THIS FUNCTION ALSO CALCULATES 
#DIFFERENCES IN PAIRED OBJECT INITIATION AND DISSIPATION. THIS NEW VERSION 
#ALLOWS FOR SPATIAL AGGREGATION OF DATA ON A DIFFERENT DOMAIN RESOLUTION THAN 
#THE NATIVE DOMAIN.
#
#Created 20171101-20171120. MJE.
#Updated: 20171205 to subset by forecast hour and fix bugs
#Updated: Correct minor bugs. MJE. 20191106.
#Updated: Add forecast/diurnal hour information to output and remove option to subset hours. MJE 20200106.
#Updated: Add 10,50,90th percentile outputs. MJE. 20200128.
#Updated: Fixed bug for computing spatially aggregated data. MJE. 20200204-06.
#Updated: Option for spatial aggregation of data on a different resolution than native domain. MJE 20200306.
#Updated: Fixed bug for aggregation option. MJE. 20200319
#Updated: Adjusted code for a list of days to allow for nonconsecutive days, rather than start/end date. MJE. 20210324.

#####################INPUT FILES FOR load_pair_prop###############################
#TRACK_PATH        = path to track data
#GRIB_PATH_DES     = unique string ID for MET run
#load_model        = a string list of model data to be loaded
#list_date         = list of dates (datetime element)
#start_hrs         = start hour for MTD run (usually zero)
#total_fcst_hrs    = total forecast hours
#pre_acc           = precipitation accumulation interval
#thres             = thrshold for precipitation data
#lat_nat           = latitude native grid
#lon_nat           = longitude native grid
#grid_res_agg      = grid resolution to aggregate statistics (e.g. search radius)
####################OUTPUT FILES FOR load_pair_prop################################
#grid_pair         = grid showing model/obs differences of paired object attributes
#grid_init         = grid showing model/obs differences of initiation object attributes
#grid_disp         = grid showing model/obs differences of disipation object attributes
#pair_prop_count   = total sample size of data
##data_exist_sum   = total sample size of data by grid point
###################################################################################

def load_pair_prop(TRACK_PATH,GRIB_PATH_DES,load_model,list_date,start_hrs,total_fcst_hrs,pre_acc,thres,lat_nat,lon_nat,grid_res_agg):

    #Determine the total number of possible forecast hours
    fcst_hrs_all = np.arange(start_hrs,total_fcst_hrs,pre_acc)

    #Calculate native grid resolution
    grid_res_nat = np.unique(np.round(np.diff(lon_nat),1))
    
    #Calculate search radius out for aggregate statistics in grid points
    if grid_res_agg == []:
        search_radius = 0
    else:
        search_radius = np.floor(grid_res_agg / grid_res_nat ) - 1
    
    #Initialize the paired attributes matrices and other temporary variables
    grid_pair       = [[[] for i in range(0,lat_nat.shape[1])] for j in range(0,lat_nat.shape[0])]         
    grid_init       = [[[] for i in range(0,lat_nat.shape[1])] for j in range(0,lat_nat.shape[0])]   
    grid_disp       = [[[] for i in range(0,lat_nat.shape[1])] for j in range(0,lat_nat.shape[0])] 
    xloc_u = []
    yloc_u = []
    pair_prop_count = 0
    data_sum_count  = 0
   
    #Determine if there is one or several datetime elements
    try:
        temps = list_date.shape
    except AttributeError:
        list_date = [list_date]
 
    #Loop through and aggregate data
    for datetime_curdate in list_date: #through the dates
            print(datetime_curdate)

            for model in load_model: #through the members

                #Load paired model/obs track files here
                try:
    
                    #Isolate member number if there are multiple members
                    if 'mem' in model:
                        mem = model[model.find('mem')+3:model.find('mem')+5]
                        filename_load = TRACK_PATH+GRIB_PATH_DES+'_m'+mem+'_'+'{:04d}'.format(datetime_curdate.year)+ \
                            '{:02d}'.format(datetime_curdate.month)+'{:02d}'.format(datetime_curdate.day)+'{:02d}'.format(datetime_curdate.hour)+\
                            '_pair_prop'+'_s'+str(int(start_hrs))+'_e'+str(int(start_hrs+total_fcst_hrs))+'_h'+'{0:.2f}'.format(pre_acc)+'_t'+str(thres)+'.npz'
                    else:
                        filename_load = TRACK_PATH+GRIB_PATH_DES+'_'+'{:04d}'.format(datetime_curdate.year)+ \
                            '{:02d}'.format(datetime_curdate.month)+'{:02d}'.format(datetime_curdate.day)+'{:02d}'.format(datetime_curdate.hour)+\
                            '_pair_prop'+'_s'+str(int(start_hrs))+'_e'+str(int(start_hrs+total_fcst_hrs))+'_h'+'{0:.2f}'.format(pre_acc)+'_t'+str(thres)+'.npz'
                    
                    #Unzip the file, load the data, and rezip the original file
                    output = os.system('gunzip '+filename_load+'.gz')
                    data   = np.load(filename_load)
                    output = os.system('gzip '+filename_load)
                    
                    #Initialize grid to sum total number of missing points
                    if data_sum_count == 0:
                        data_exist_sum = np.zeros((data['data_exist'].shape))
                        data_sum_count += 1
                    
                    pair_prop_k     = data['pair_prop_k']
                    data_exist_sum  = data_exist_sum + data['data_exist']
                    
                except IOError:
                    print(filename_load+' Not Found')
                    pair_prop_k = np.nan

                #UNCOMMENT to print out information on object information        
                #for ind in np.unique(pair_prop_k[0]):
                #    print 'Index is '+str(ind)
                #    print pair_prop_k[2][pair_prop_k[0]==ind]
                #    print pair_prop_k[4][pair_prop_k[0]==ind]
                #    print pair_prop_k[5][pair_prop_k[0]==ind]
                
                ##FIRST LOOP THROUGH pair_prop_k, GATHERING 1) INSTANCES WHERE MOD/OBS MATCHED/MERGED OBJECTS EXIST 
                ##AT THE SAME TIME AND CALCULATE DIFFERENCES AND 2) INSTANCES WHERE MATCHED/MERGED MOD/OBS INITIATE 
                ##OR DISSIPATE AND CALCULATE DIFFERENCES PERTAINING TO THAT.
                
                if np.mean(np.isnan(pair_prop_k)) < 1 and np.mean(pair_prop_k) == 0: #Model exists, but with no data
                    pair_prop_count += 1
                    
                elif np.mean(np.isnan(pair_prop_k)) < 1 and np.mean(pair_prop_k) != 0: #Model exists with data

                    for obs_num in np.unique(pair_prop_k[0][pair_prop_k[0]<0]): #Each unique "storm" track
                        
                        #Isolate model/obs and find all common time indices to both
                        obs_use  = np.where(pair_prop_k[0] ==  obs_num)[0]
                        mod_use  = np.where(pair_prop_k[0] == -obs_num)[0]
                        time_use = np.union1d(pair_prop_k[2][obs_use],pair_prop_k[2][mod_use])

                        #Append a spurious +1 to the end of 'time_use' so the end time is always properly captured
                        time_use = np.hstack((time_use,time_use[-1]+1))

                        ##Subset times based on user specification
                        #time_use = np.intersect1d(time_use,subset_hours)
            
                        #Binomial variables to determine 1) at start, mod or obs first and 2) at end, mod or obs last
                        first_obs = 0
                        final_obs = 0 
                        first_mod = 0
                        final_mod = 0
                        tloc_first_obs = 0
                        tloc_first_mod = 0
                        tloc_final_obs = len(fcst_hrs_all)-1
                        tloc_final_mod = len(fcst_hrs_all)-1
                           
                        #Loop through all data within each specific paired object
                        for time_val in time_use: #Each element within the "storm" tracks
                            
                            #Find matching obs/model index location
                            obs_ind = np.where((pair_prop_k[1][:] ==  obs_num) & (pair_prop_k[2][:] == time_val))[0]
                            mod_ind = np.where((pair_prop_k[1][:] == -obs_num) & (pair_prop_k[2][:] == time_val))[0]
                            
                            #Check that values is within domain boundaries (using observation data)
                            if not (pair_prop_k[4][obs_ind] < np.nanmin(lat_nat) or pair_prop_k[4][obs_ind] > np.nanmax(lat_nat) or \
                                pair_prop_k[5][obs_ind] < np.nanmin(lon_nat) or pair_prop_k[5][obs_ind] > np.nanmax(lon_nat)):

                                #1) FIND ALL INSTANCES OF MOD/OBS INITIATION/DISSIPATION. THIS ALLOWS FOR THE
                                #COMPARISON OF MOD AND OBS AT DIFFERENT TIMES. 
                
                                #Find first instance of obs
                                if len(obs_ind) > 0 and first_obs == 0:
                                      
                                    #Index location of data to be stored in archived matrix
                                    yloc_first_obs  = int(np.argmax(np.diff([lat_nat[:,1]>pair_prop_k[4][obs_ind][0]]))+1)
                                    xloc_first_obs  = int(np.argmax(np.diff([lon_nat[1,:]<pair_prop_k[5][obs_ind][0]]))+1)
                                    tloc_first_obs  = int(time_val)
                                    
                                    #Value of data to be stored in archived matrix
                                    lat_first_obs    = pair_prop_k[4][obs_ind][0]
                                    lon_first_obs    = pair_prop_k[5][obs_ind][0]
                                    ang_first_obs    = pair_prop_k[6][obs_ind][0]
                                    int_first_obs_10 = pair_prop_k[7][obs_ind][0]
                                    int_first_obs_50 = pair_prop_k[8][obs_ind][0]
                                    int_first_obs_90 = pair_prop_k[9][obs_ind][0]
                                    area_first_obs   = pair_prop_k[3][obs_ind][0]
                                    fhour_first_obs  = (pair_prop_k[2][obs_ind][0] + 1) * pre_acc
                                    dhour_first_obs  = (((pair_prop_k[2][obs_ind][0]+ 1) * pre_acc) + datetime_curdate.hour) - \
                                        24 * ((((pair_prop_k[2][obs_ind][0] + 1) * pre_acc) + datetime_curdate.hour) >= 24) * 1
                                    
                                    first_obs = 1
                                
                                #Find last instance of obs (note we grab the data from the previous index)
                                elif len(obs_ind) == 0 and first_obs == 1 and final_obs == 0: 

                                    #Index location of data to be stored in archived matrix
                                    yloc_final_obs = int(np.argmax(np.diff([lat_nat[:,1]>pair_prop_k[4][obs_ind_prev][0]]))+1)
                                    xloc_final_obs = int(np.argmax(np.diff([lon_nat[1,:]<pair_prop_k[5][obs_ind_prev][0]]))+1)
                                    tloc_final_obs = int(time_val - 1)
                                    
                                    #Value of data to be stored in archived matrix
                                    lat_final_obs    = pair_prop_k[4][obs_ind_prev][0]
                                    lon_final_obs    = pair_prop_k[5][obs_ind_prev][0]
                                    ang_final_obs    = pair_prop_k[6][obs_ind_prev][0]
                                    int_final_obs_10 = pair_prop_k[7][obs_ind_prev][0]
                                    int_final_obs_50 = pair_prop_k[8][obs_ind_prev][0]
                                    int_final_obs_90 = pair_prop_k[9][obs_ind_prev][0]
                                    area_final_obs   = pair_prop_k[3][obs_ind_prev][0]
                                    fhour_final_obs  = (pair_prop_k[2][obs_ind_prev][0] + 1) * pre_acc
                                    dhour_final_obs  = (((pair_prop_k[2][obs_ind_prev][0]+ 1) * pre_acc) + datetime_curdate.hour) - \
                                        24 * ((((pair_prop_k[2][obs_ind_prev][0] + 1) * pre_acc) + datetime_curdate.hour) >= 24) * 1
                                    
                                    final_obs = 1
                                    
                                #Find first instance of mod
                                if len(mod_ind) > 0 and first_mod == 0:
                                    
                                    #Index location of data to be stored in archived matrix
                                    yloc_first_mod = int(np.argmax(np.diff([lat_nat[:,1]>pair_prop_k[4][mod_ind][0]]))+1)
                                    xloc_first_mod = int(np.argmax(np.diff([lon_nat[1,:]<pair_prop_k[5][mod_ind][0]]))+1)
                                    tloc_first_mod = int(time_val)

                                    #Value of data to be stored in archived matrix
                                    lat_first_mod    = pair_prop_k[4][mod_ind][0]
                                    lon_first_mod    = pair_prop_k[5][mod_ind][0]
                                    ang_first_mod    = pair_prop_k[6][mod_ind][0]
                                    int_first_mod_10 = pair_prop_k[7][mod_ind][0]
                                    int_first_mod_50 = pair_prop_k[8][mod_ind][0]
                                    int_first_mod_90 = pair_prop_k[9][mod_ind][0]
                                    area_first_mod   = pair_prop_k[3][mod_ind][0]
                                    fhour_first_mod  = (pair_prop_k[2][mod_ind][0] + 1) * pre_acc
                                    dhour_first_mod  = (((pair_prop_k[2][mod_ind][0]+ 1) * pre_acc) + datetime_curdate.hour) - \
                                        24 * ((((pair_prop_k[2][mod_ind][0] + 1) * pre_acc) + datetime_curdate.hour) >= 24) * 1
                                    first_mod = 1
                                    
                                #Find last instance of mod (note we grab the data from the previous index)
                                elif len(mod_ind) == 0 and first_mod == 1 and final_mod == 0: 
            
                                    #Index location of data to be stored in archived matrix
                                    yloc_final_mod = int(np.argmax(np.diff([lat_nat[:,1]>pair_prop_k[4][mod_ind_prev][0]]))+1)
                                    xloc_final_mod = int(np.argmax(np.diff([lon_nat[1,:]<pair_prop_k[5][mod_ind_prev][0]]))+1)
                                    tloc_final_mod = int(time_val - 1)
                                    
                                    #Value of data to be stored in archived matrix
                                    lat_final_mod    = pair_prop_k[4][mod_ind_prev][0]
                                    lon_final_mod    = pair_prop_k[5][mod_ind_prev][0]
                                    ang_final_mod    = pair_prop_k[6][mod_ind_prev][0]
                                    int_final_mod_10 = pair_prop_k[7][mod_ind_prev][0]
                                    int_final_mod_50 = pair_prop_k[8][mod_ind_prev][0]
                                    int_final_mod_90 = pair_prop_k[9][mod_ind_prev][0]
                                    area_final_mod   = pair_prop_k[3][mod_ind_prev][0]
                                    fhour_final_mod  = (pair_prop_k[2][mod_ind_prev][0] + 1) * pre_acc
                                    dhour_final_mod  = (((pair_prop_k[2][mod_ind_prev][0]+ 1) * pre_acc) + datetime_curdate.hour) - \
                                        24 * ((((pair_prop_k[2][mod_ind_prev][0] + 1) * pre_acc) + datetime_curdate.hour) >= 24) * 1
                                    
                                    final_mod = 1
                                    
                                #2) FIND AND RECORD ALL INSTANCES OF MOD AND OBS AT A FIXED TIME. 
                                #NOTE BOTH MOD AND OBS MUST EXIST FOR THE TIME PERIOD ANALYZED.
                
                                #Collect Statistics when mod/obs both exist
                                if len(mod_ind) > 0 and len(obs_ind) > 0: 
 
                                    #Find y,x,t location on the archived paired attributes grid
                                    #Note: anything from -95.9999 to -94 is put into -94 longitude; anything from 37.999 to 36 is put into 36 latitude
                                    yloc = int(np.argmax(np.diff([lat_nat[:,1]>pair_prop_k[4][obs_ind][0]]))+1)
                                    xloc = int(np.argmax(np.diff([lon_nat[1,:]<pair_prop_k[5][obs_ind][0]]))+1)
                                    #tloc = int(time_val)
                                                            
                                    #Latitude model displacement (model south is negative)
                                    if pair_prop_k[4][mod_ind][0] > pair_prop_k[4][obs_ind][0]:
                                        ysign = 1
                                    else:
                                        ysign = -1
                                    
                                    #longitude model displacement (model west is negative)
                                    if pair_prop_k[5][mod_ind][0] > pair_prop_k[5][obs_ind][0]:
                                        xsign = 1
                                    else:
                                        xsign = -1
                                        
                                    #Calculate x and y vector distance separately
                                    #ydiff  = pair_prop_k[4][mod_ind][0] - pair_prop_k[4][obs_ind][0]
                                    #xdiff  = pair_prop_k[5][mod_ind][0] - pair_prop_k[5][obs_ind][0]
                                    ydiff = ysign * (haversine.distance((pair_prop_k[4][mod_ind][0], pair_prop_k[5][mod_ind][0]), \
                                        (pair_prop_k[4][obs_ind][0], pair_prop_k[5][mod_ind][0])))
                                    xdiff = xsign * (haversine.distance((pair_prop_k[4][mod_ind][0], pair_prop_k[5][mod_ind][0]), \
                                        (pair_prop_k[4][mod_ind][0], pair_prop_k[5][obs_ind][0])))
                
                                    #Calculate intensity, area, and angle differences (model - obs)
                                    intdiff_10 = pair_prop_k[7][mod_ind][0] - pair_prop_k[7][obs_ind][0]
                                    intdiff_50 = pair_prop_k[8][mod_ind][0] - pair_prop_k[8][obs_ind][0]
                                    intdiff_90 = pair_prop_k[9][mod_ind][0] - pair_prop_k[9][obs_ind][0]
                                    areadiff   = pair_prop_k[3][mod_ind][0] - pair_prop_k[3][obs_ind][0]
                                    angdiff    = pair_prop_k[6][mod_ind][0] - pair_prop_k[6][obs_ind][0]
                                    fhour      = (pair_prop_k[2][obs_ind][0] + 1) * pre_acc
                                    dhour      = (((pair_prop_k[2][obs_ind][0]+ 1) * pre_acc) + datetime_curdate.hour) - \
                                        24 * ((((pair_prop_k[2][obs_ind][0] + 1) * pre_acc) + datetime_curdate.hour) >= 24) * 1 #diurnal hour increment
                                    
                                    #Define search radius on aggregate grid, considering grid domains
                                    xsearch = np.arange(xloc-search_radius,xloc+search_radius+1,1)
                                    xsearch = xsearch[(xsearch >= 0) & (xsearch < lon_nat.shape[1])]
                                    xsearch = xsearch.astype(int)
                                    ysearch = np.arange(yloc-search_radius,yloc+search_radius+1,1)
                                    ysearch = ysearch[(ysearch >= 0) & (ysearch < lat_nat.shape[0])]
                                    ysearch = ysearch.astype(int)
                                    
                                    #Aggregate statistics to native grid using aggregate grid search radius            
                                    for xloc_l in xsearch: #through xloc points
                                        for yloc_l in ysearch: #through yloc points    
        
                                            #Append data to paired attribute list [ydiff,xdiff,int_diff,area_diff,ang_diff]
                                            if len(grid_pair[yloc_l][xloc_l]) == 0:
                                                grid_pair[yloc_l][xloc_l] = [[ydiff,xdiff,intdiff_10,intdiff_50,intdiff_90,areadiff,angdiff,fhour,dhour]]
                                                xloc_u = np.append(xloc_u,xloc_l)
                                                yloc_u = np.append(yloc_u,yloc_l)
                                            else:
                                                grid_pair[yloc_l][xloc_l] = np.vstack((grid_pair[yloc_l][xloc_l],[ydiff,xdiff,intdiff_10,intdiff_50,intdiff_90,areadiff,angdiff,fhour,dhour]))
                                                xloc_u = np.append(xloc_u,xloc_l)
                                                yloc_u = np.append(yloc_u,yloc_l)
                                
                                #print('Paired obs mapped to '+str([yloc,xloc,tloc])+ 'with values of '+str([ydiff,xdiff,intdiff,areadiff,angdiff]))
                                #END model/obs check
                                
                                #Recall previous indices for model and observation
                                obs_ind_prev = obs_ind
                                mod_ind_prev = mod_ind
                                
                            #END domain check    
                        #END through time_val
                        
                        #3) RECORD ALL INSTANCES OF MOD/OBS INITIATION AND CALCULATE DIFFERENCES.
                        #DISREGARD ALL INSTANCES WHERE OBJ EXISTED AT TIME ZERO.
            
                        if tloc_first_obs != 0 and tloc_first_mod != 0:
            
                            #Latitude model displacement (model south is negative)
                            if lat_first_mod > lat_first_obs:
                                ysign = 1
                            else:
                                ysign = -1
                            
                            #longitude model displacement (model west is negative)
                            if lon_first_mod > lon_first_obs:
                                xsign = 1
                            else:
                                xsign = -1
                                
                            #Calculate y and x distance with x and y, respectively, constant between mod/obs object !!!!!!!!!!!1START HERE!!!!!!!!!!!!
                            ydiff = ysign * (haversine.distance((lat_first_mod, lon_first_mod),(lat_first_obs, lon_first_mod)))
                            xdiff = xsign * (haversine.distance((lat_first_mod, lon_first_mod),(lat_first_mod, lon_first_obs)))
            
                            #Calculate intensity, area, and angle differences (model - obs)
                            intdiff_10 = int_first_mod_10  - int_first_obs_10
                            intdiff_50 = int_first_mod_50  - int_first_obs_50
                            intdiff_90 = int_first_mod_90  - int_first_obs_90
                            areadiff   = area_first_mod    - area_first_obs
                            angdiff    = ang_first_mod     - ang_first_obs
                            timediff   = tloc_first_mod    - tloc_first_obs
                            
                            #Define search radius on aggregate grid, considering grid domains
                            xsearch = np.arange(xloc_first_obs-search_radius,xloc_first_obs+search_radius+1,1)
                            xsearch = xsearch[(xsearch >= 0) & (xsearch < lon_nat.shape[1])]
                            xsearch = xsearch.astype(int)
                            ysearch = np.arange(yloc_first_obs-search_radius,yloc_first_obs+search_radius+1,1)
                            ysearch = ysearch[(ysearch >= 0) & (ysearch < lat_nat.shape[0])]
                            ysearch = ysearch.astype(int)
  
                            #Aggregate statistics to native grid using aggregate grid search radius            
                            for xloc_l in xsearch: #through xloc points
                                for yloc_l in ysearch: #through yloc points    
    
                                    #Append data to init attribute list mapped to obs location [ydiff,xdiff,intdiff_10,intdiff_50,intdiff_90,areadiff,angdiff,timediff,fhour_first_obs,dhour_first_obs]
                                    if len(grid_init[yloc_l][xloc_l]) == 0:
                                        grid_init[yloc_l][xloc_l] = [[ydiff,xdiff,intdiff_10,intdiff_50,intdiff_90,areadiff,angdiff,timediff,fhour_first_obs,dhour_first_obs]]
                                    else:
                                        grid_init[yloc_l][xloc_l] = np.vstack((grid_init[yloc_l][xloc_l], \
                                            [ydiff,xdiff,intdiff_10,intdiff_50,intdiff_90,areadiff,angdiff,timediff,fhour_first_obs,dhour_first_obs]))
                                    #print grid_init[yloc_l][xloc_l]        
                                    #print('Model Init mapped to '+str([yloc_l,xloc_l])+ 'with values of '+str([ydiff,xdiff,intdiff,areadiff,angdiff,timediff]))
                                        
                        #4) RECORD ALL INSTANCES OF MOD/OBS DISSIPATION AND CALCULATE DIFFERENCES.
                        #DISREGARD ALL INSTANCES WHERE OBJ EXISTED AT FINAL TIME
                        
                        #Final time of obj must be before last time period considered, remove all others
                        if tloc_final_obs != len(fcst_hrs_all)-1 and tloc_final_mod != len(fcst_hrs_all)-1:
        
                            #Latitude model displacement (model south is negative)
                            if lat_final_mod > lat_final_obs:
                                ysign = 1
                            else:
                                ysign = -1
                            
                            #longitude model displacement (model west is negative)
                            if lon_final_mod > lon_final_obs:
                                xsign = 1
                            else:
                                xsign = -1
                                
                            #Calculate y and x distance with x and y, respectively, constant between mod/obs object
                            ydiff = ysign * (haversine.distance((lat_final_mod, lon_final_mod),(lat_final_obs, lon_final_mod)))
                            xdiff = xsign * (haversine.distance((lat_final_mod, lon_final_mod),(lat_final_mod, lon_final_obs)))
            
                            #Calculate intensity, area, and angle differences (model - obs)
                            intdiff_10 = int_final_mod_10 - int_final_obs_10
                            intdiff_50 = int_final_mod_50 - int_final_obs_50
                            intdiff_90 = int_final_mod_90 - int_final_obs_90
                            areadiff   = area_final_mod   - area_final_obs
                            angdiff    = ang_final_mod    - ang_final_obs
                            timediff   = tloc_final_mod   - tloc_final_obs
                            
                            #Define search radius on aggregate grid, considering grid domains
                            xsearch = np.arange(xloc_final_obs-search_radius,xloc_final_obs+search_radius+1,1)
                            xsearch = xsearch[(xsearch >= 0) & (xsearch < lon_nat.shape[1])]
                            xsearch = xsearch.astype(int)
                            ysearch = np.arange(yloc_final_obs-search_radius,yloc_final_obs+search_radius+1,1)
                            ysearch = ysearch[(ysearch >= 0) & (ysearch < lat_nat.shape[0])]
                            ysearch = ysearch.astype(int)
  
                            #Aggregate statistics to native grid using aggregate grid search radius            
                            for xloc_l in xsearch: #through xloc points
                                for yloc_l in ysearch: #through yloc points    
   
                                    #Append data to disp attribute list mapped to obs location [ydiff,xdiff,intdiff_10,intdiff_50,intdiff_90,areadiff,angdiff,timediff,fhour_final_obs,dhour_final_obs]
                                    if len(grid_disp[yloc_l][xloc_l]) == 0:
                                        grid_disp[yloc_l][xloc_l] = [[ydiff,xdiff,intdiff_10,intdiff_50,intdiff_90,areadiff,angdiff,timediff,fhour_final_obs,dhour_final_obs]]
                                    else:
                                        grid_disp[yloc_l][xloc_l] = np.vstack((grid_disp[yloc_l][xloc_l], \
                                            [ydiff,xdiff,intdiff_10,intdiff_50,intdiff_90,areadiff,angdiff,timediff,fhour_final_obs,dhour_final_obs]))
                                    
                            #print('Model Disp. mapped to '+str([yloc_final_obs,xloc_final_obs,tloc_final_obs])+ 'with values of '+str([ydiff,xdiff,intdiff,areadiff,angdiff,timediff]))
                
                    #END through objects in one run 
                    pair_prop_count += 1   
                #END loop through members        
            #END check for data in paired object matrix    
        #END check for data in paired object matrix
    
    return(grid_pair, grid_init, grid_disp, pair_prop_count, data_exist_sum)
      
##################################################################################
#THIS FUNCTION LOADS THE SIMPLE OBJECTS CREATED RETROSPECTIVELY USING 
#'mtd_retroruns_save.py.' ALL OF THE DATES ARE LOADED INSIDE OF THIS FUNCTION
#AND THE STATISTICS ARE AGGREGATED SPATIALLY. THERE IS A FILTERING OPTION BY 
#FORECAST HOUR, DIURNAL HOUR, MULTIPLE MEMBERS, AND SPATIALLY AGGREGATED DATA.
#THIS NEW VERSION ALLOWS FOR SPATIAL AGGREGATION OF DATA ON A DIFFERENT DOMAIN 
#RESOLUTION THAN THE NATIVE DOMAIN.
#
#Created: 20171101-20171120. MJE.
#Updated: 20171205 to subset by forecast hour and fix bugs
#Updated: New features added to load and aggregate multiple members (this won't work for different model types). MJE. 20190927.
#Updated: Correct minor bugs and adapted to merge both subhourly and hourly input files. MJE. 20191106.
#Updated: Add forecast/diurnal hour information to output and remove option to subset hours. MJE 20200106.
#Updated: Add 10,50,90th percentile outputs. MJE. 20200128.
#Updated: Fixed bug for computing spatially aggregated data. MJE. 20200204.
#Updated: Option for spatial aggregation of data on a different resolution than native domain. MJE 20200305.
#Updated: Fixed bug for aggregation option. MJE. 20200319
#Updated: Adjusted code for a list of days to allow for nonconsecutive days, rather than start/end date. MJE. 20210324.
#
#####################INPUT FILES FOR load_simp_prop################################
#TRACK_PATH        = path to track data
#GRIB_PATH_DES     = unique string ID for MET run
#load_model        = a string list of model data to be loaded
#list_date         = list of dates (datetime element)
#start_hrs         = start hour for MTD run (usually zero)
#total_fcst_hrs    = total forecast hours
#pre_acc           = precipitation accumulation interval
#thres             = thrshold for precipitation data
#lat_nat           = latitude native grid
#lon_nat           = longitude native grid
#grid_res_agg      = grid resolution to aggregate statistics (e.g. search radius)
####################OUTPUT FILES FOR load_simp_prop################################
#grid_obs_sing     = observation grid of simple object attributes
#grid_mod_sing     = model grid of simple object attributes
#simp_prop_count   = total sample size of data
#data_exist_sum    = total sample size of data by grid point
###################################################################################

def load_simp_prop(TRACK_PATH,GRIB_PATH_DES,load_model,list_date,start_hrs,total_fcst_hrs,pre_acc,thres,lat_nat,lon_nat,grid_res_agg):

    #Calculate native grid resolution
    grid_res_nat = np.unique(np.round(np.diff(lon_nat),1))
    
    #Calculate search radius out for aggregate statistics in grid points
    if grid_res_agg == []:
        search_radius = 0
    else:
        search_radius = np.floor(grid_res_agg / grid_res_nat ) - 1
    
    #Initialize the paired attributes matrices and other temporary variables
    grid_obs_sing   = [[[] for i in range(0,lat_nat.shape[1])] for j in range(0,lat_nat.shape[0])]  
    grid_mod_sing   = [[[] for i in range(0,lat_nat.shape[1])] for j in range(0,lat_nat.shape[0])]  
    data_sum_count  = 0
    simp_prop_count = 0
   
    #Determine if there is one or several datetime elements
    try: 
        temps = list_date.shape
    except AttributeError:
        list_date = [list_date]

    #Loop through and aggregate data
    for datetime_curdate in list_date: #through the dates

            print(datetime_curdate)
 
            for model in load_model: #through the members

                #Load the simple and paired model/obs track files here
                try:
    
                    #Isolate member number if there are multiple members
                    if 'mem' in model:
                        mem = model[model.find('mem')+3:model.find('mem')+5]
                
                        filename_load = TRACK_PATH+GRIB_PATH_DES+'_m'+mem+'_'+'{:04d}'.format(datetime_curdate.year)+ \
                            '{:02d}'.format(datetime_curdate.month)+'{:02d}'.format(datetime_curdate.day)+'{:02d}'.format(datetime_curdate.hour)+\
                            '_simp_prop'+'_s'+str(int(start_hrs))+'_e'+str(int(start_hrs+total_fcst_hrs))+'_h'+'{0:.2f}'.format(pre_acc)+'_t'+str(thres)+'.npz'
                    else:
                        filename_load = TRACK_PATH+GRIB_PATH_DES+'_'+'{:04d}'.format(datetime_curdate.year)+ \
                            '{:02d}'.format(datetime_curdate.month)+'{:02d}'.format(datetime_curdate.day)+'{:02d}'.format(datetime_curdate.hour)+\
                            '_simp_prop'+'_s'+str(int(start_hrs))+'_e'+str(int(start_hrs+total_fcst_hrs))+'_h'+'{0:.2f}'.format(pre_acc)+'_t'+str(thres)+'.npz'

                    #Unzip the file, load the data, and rezip the original file
                    output = os.system('gunzip '+filename_load+'.gz')
                    data   = np.load(filename_load)
                    output = os.system('gzip '+filename_load)
                        
                    #Initialize grid to sum total number of missing points
                    if data_sum_count == 0:
                        data_exist_sum = np.zeros((data['data_exist'].shape))
                        data_sum_count += 1
                    
                    #Archive the data    
                    simp_prop_k     = data['simp_prop_k']
                    data_exist_sum  = data_exist_sum + data['data_exist']
                    
                except IOError:
                    simp_prop_k = np.nan
                    print(filename_load+' Not Found')
                                
                ##LOOP THROUGH simp_prop_k, GATHERING DATA THAT CONTAINS INTENSITY, AREA, ANGLE AND COUNT
                ##FOR UNMATCHED MODEL AND OBSERVATION TRACK POINTS.
        
                if np.mean(np.isnan(simp_prop_k)) < 1 and np.mean(simp_prop_k) == 0:
                    simp_prop_count += 1
                    
                elif np.mean(np.isnan(simp_prop_k)) < 1 and np.mean(simp_prop_k) != 0:    
                    for track in range(0,len(simp_prop_k[0])):
                        
                        #Check that values are within domain boundaries
                        if not (simp_prop_k[4][track] < np.nanmin(lat_nat) or simp_prop_k[4][track] > np.nanmax(lat_nat) or \
                            simp_prop_k[5][track] < np.nanmin(lon_nat) or simp_prop_k[5][track] > np.nanmax(lon_nat)):

                            #Find location of object on interpolation grid (maps to most southeast point on the grid)
                            yloc  = int(np.argmax(np.diff([lat_nat[:,1]>simp_prop_k[4][track]]))+1)
                            xloc  = int(np.argmax(np.diff([lon_nat[1,:]<simp_prop_k[5][track]]))+1)

                            #Gather data to save
                            inten10 = simp_prop_k[7][track]                                        #10th percentile of ntensity
                            inten50 = simp_prop_k[8][track]                                        #intensity
                            inten90 = simp_prop_k[9][track]                                        #intensity
                            area    = simp_prop_k[3][track]                                        #area
                            ang     = simp_prop_k[6][track]                                        #axis angle
                            fhour   = (simp_prop_k[2][track] + 1) * pre_acc                        #forecast hour increment
                            dhour   = (((simp_prop_k[2][track]+ 1) * pre_acc) + datetime_curdate.hour) - \
                                24 * ((((simp_prop_k[2][track] + 1) * pre_acc) + datetime_curdate.hour) >= 24) * 1 #diurnal hour increment
                            
                            #Define search radius on aggregate grid, considering grid domains
                            xsearch = np.arange(xloc-search_radius,xloc+search_radius+1,1)
                            xsearch = xsearch[(xsearch >= 0) & (xsearch < lon_nat.shape[1])]
                            xsearch = xsearch.astype(int)
                            ysearch = np.arange(yloc-search_radius,yloc+search_radius+1,1)
                            ysearch = ysearch[(ysearch >= 0) & (ysearch < lat_nat.shape[0])]
                            ysearch = ysearch.astype(int)

                            #Aggregate statistics to native grid using aggregate grid search radius            
                            for xloc_l in xsearch: #through xloc points
                                for yloc_l in ysearch: #through yloc points    

                                    #Separate into model or observation
                                    if simp_prop_k[0][track] < 0: #Observation within time specifications
                
                                        if len(grid_obs_sing[yloc_l][xloc_l]) == 0:
                                            grid_obs_sing[yloc_l][xloc_l] = [[inten10,inten50,inten90,area,ang,fhour,dhour]]
                                        else:
                                            grid_obs_sing[yloc_l][xloc_l] = np.vstack((grid_obs_sing[yloc_l][xloc_l],[inten10,inten50,inten90,area,ang,fhour,dhour]))
                                            
                                    elif simp_prop_k[0][track] > 0: #Model within time specfications
                
                                        if len(grid_mod_sing[yloc_l][xloc_l]) == 0:
                                            grid_mod_sing[yloc_l][xloc_l] = [[inten10,inten50,inten90,area,ang,fhour,dhour]]

                                        else:
                                            grid_mod_sing[yloc_l][xloc_l] = np.vstack((grid_mod_sing[yloc_l][xloc_l],[inten10,inten50,inten90,area,ang,fhour,dhour]))
                    #END through objects in one run    
                    simp_prop_count += 1  
            
                #END check for data in simple object matrix  
            #END loop through members    
        #END loop through inithr
    #END loop through date 
    
    return(grid_obs_sing, grid_mod_sing,simp_prop_count,data_exist_sum) 

###############################################################################################
#THIS FUNCTION LOADS THE AVERAGE PROBABILITY OF OBSERVED OBJECTS EXISTING (PROB OBS YES OR POY)
#GIVEN THE SIMPLE MODEL OBJECT EXISTS (PROB MODEL YES OR PMY). THIS FUNCTION NEEDS ONLY 'simp_prop'
#AND COMPARES THE SIMPLE TO CLUSTER OBJECTS WITHIN THE 2D TEXT OUTPUT FILES FROM MTD.
#
#NOTE: THESE STATISTICS ARE GATHERED FOR EACH UNIQUE TRACK, NOT FOR EACH TIME STAMP WITHIN EACH TRACK.
#NOTE: SPATIALLY AGGREGATED STATISTICS ARE MAPPED TO THE MODEL GRID, NOT THE OBSERVATION GRID. THIS IS 
#DIFFERENT FROM load_pair_prop* WHICH GATHERS MODEL DIFFERENCES ON THE OBSERVATION GRID.
#20210127-0202 MJE.
#
#Updated: Adjusted code for a list of days to allow for nonconsecutive days, rather than start/end date. MJE. 20210324.
#
#####################INPUT FILES FOR load_pair_POYgPMY#########################################
#TRACK_PATH        = path to track data
#GRIB_PATH_DES     = unique string ID for MET run
#load_model        = a string list of model data to be loaded
#list_date         = list of dates (datetime element)
#start_hrs         = start hour for MTD run (usually zero)
#total_fcst_hrs    = total forecast hours
#pre_acc           = precipitation accumulation interval
#thres             = thrshold for precipitation data
#lat_nat           = latitude native grid
#lon_nat           = longitude native grid
#grid_res_agg      = grid resolution to aggregate statistics (e.g. search radius)
####################OUTPUT FILES FOR load_pair_POYgPMY################################
#grid_POYgPMY      = grid of probability of observation existing given model exists 
#simp_prop_count   = total sample size of data (e.g. files, with or without data)
#data_exist_sum    = total sample size of data by grid point
###################################################################################

def load_pair_POYgPMY(TRACK_PATH,GRIB_PATH_DES,load_model,list_date,start_hrs,total_fcst_hrs,pre_acc,thres,lat_nat,lon_nat,grid_res_agg):

    #Calculate native grid resolution
    grid_res_nat = np.unique(np.round(np.diff(lon_nat),1))

    #Calculate search radius out for aggregate statistics in grid points
    if grid_res_agg == []:
        search_radius = 0
    else:
        search_radius = np.floor(grid_res_agg / grid_res_nat ) - 1

    #Initialize the paired attributes matrices and other temporary variables
    grid_mod_yes   = np.zeros((lat_nat.shape[0],lat_nat.shape[1])) #Grid of yes model instances
    grid_mod_tot   = np.zeros((lat_nat.shape[0],lat_nat.shape[1])) #Grid of total model instances
    grid_POYgPMY   = np.zeros((lat_nat.shape[0],lat_nat.shape[1])) #Grid of probability of observation yes given model yes
    data_sum_count  = 0
    simp_prop_count = 0

    #Determine if there is one or several datetime elements
    try:
        temps = list_date.shape
    except AttributeError:
        list_date = [list_date]

    #Loop through and aggregate data
    for datetime_curdate in list_date: #through the dates

            print(datetime_curdate)

            for model in load_model: #through the members

                #Load the simple and paired model/obs track files here
                try:
                    #Isolate member number if there are multiple members
                    if 'mem' in model:
                        mem = '_m'+model[model.find('mem')+3:model.find('mem')+5]+'_'
                    else:
                        mem = '_'

                    filename_load_simp = TRACK_PATH+GRIB_PATH_DES+mem+'{:04d}'.format(datetime_curdate.year)+ \
                        '{:02d}'.format(datetime_curdate.month)+'{:02d}'.format(datetime_curdate.day)+'{:02d}'.format(datetime_curdate.hour)+\
                        '_simp_prop'+'_s'+str(int(start_hrs))+'_e'+str(int(start_hrs+total_fcst_hrs))+'_h'+'{0:.2f}'.format(pre_acc)+'_t'+str(thres)+'.npz'

                    #Unzip the file, load the data, and rezip the original file
                    output    = os.system('gunzip '+filename_load_simp+'.gz')
                    data_simp = np.load(filename_load_simp)
                    output    = os.system('gzip '+filename_load_simp)

                    #Initialize grid to sum total number of missing points
                    if data_sum_count == 0:
                        data_exist_sum = np.zeros((data_simp['data_exist'].shape))
                        data_sum_count += 1

                    #Archive the data
                    simp_prop_k     = data_simp['simp_prop_k']

                    data_exist_sum  = data_exist_sum + data_simp['data_exist']

                except IOError:
                    simp_prop_k = np.nan
                    print(filename_load_simp+' and '+filename_load_simp+' Not Found')

                ##Loop through each unique track, gathering information of whether the simple model has a cluster component.

                if np.mean(np.isnan(simp_prop_k)) < 1 and np.mean(simp_prop_k) == 0: #Model exists, but with no data
                    simp_prop_count += 1

                elif np.mean(np.isnan(simp_prop_k)) < 1 and np.mean(simp_prop_k) != 0: #Model exists with data

                    for mod_num in np.unique(simp_prop_k[0][simp_prop_k[0]>0]): #Through each model unique track
 
                        mod_use = np.where(simp_prop_k[0] == mod_num)[0]

                        #Check to see if the average value of the entire track length is within the domain
                        if not (np.nanmean(simp_prop_k[4][mod_use]) < np.nanmin(lat_nat) or np.nanmean(simp_prop_k[4][mod_use]) > np.nanmax(lat_nat) or \
                            np.nanmean(simp_prop_k[5][mod_use]) < np.nanmin(lon_nat) or np.nanmean(simp_prop_k[5][mod_use]) > np.nanmax(lon_nat)):

                            #Find average location of object on interpolation grid (maps to most southeast point on the grid)
                            yloc  = int(np.argmax(np.diff([lat_nat[:,1]>np.nanmean(simp_prop_k[4][mod_use])]))+1)
                            xloc  = int(np.argmax(np.diff([lon_nat[1,:]<np.nanmean(simp_prop_k[5][mod_use])]))+1)

                            #Define search radius on aggregate grid, considering grid domains
                            xsearch = np.arange(xloc-search_radius,xloc+search_radius+1,1)
                            xsearch = xsearch[(xsearch >= 0) & (xsearch < lon_nat.shape[1])]
                            xsearch = xsearch.astype(int)
                            ysearch = np.arange(yloc-search_radius,yloc+search_radius+1,1)
                            ysearch = ysearch[(ysearch >= 0) & (ysearch < lat_nat.shape[0])]
                            ysearch = ysearch.astype(int)

                            #Aggregate statistics to native grid using aggregate grid search radius
                            for xloc_l in xsearch: #through xloc points
                                for yloc_l in ysearch: #through yloc points

                                    #If simple object is paired, then it's observational component exists
                                    if np.nanmean(simp_prop_k[1][mod_use]) > 0:
                                        grid_mod_yes[yloc_l,xloc_l] += 1
                            
                                    #Regardless of whether model object is paired, count the total number of simple model instances
                                    grid_mod_tot[yloc_l,xloc_l] += 1

                            #END search through grid
                    simp_prop_count += 1 
                    #END through model track 
            #END through the members
        #END loop through inithr
    #END loop through date

    #Calculate POYgPMY by looping through 'grid_mod_yes' and 'grid_mod_tot'
    for xloc_l in range(grid_mod_yes.shape[1]):
        for yloc_l in range(grid_mod_yes.shape[0]):
            grid_POYgPMY[yloc_l,xloc_l] = (grid_mod_yes[yloc_l,xloc_l] / grid_mod_tot[yloc_l][xloc_l] ) *100

    return(grid_POYgPMY,simp_prop_count,data_exist_sum)

