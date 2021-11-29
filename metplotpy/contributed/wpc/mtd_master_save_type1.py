#!/usr/bin/python

################################################################################################
#MASTER MTD SCRIPT TO BE RUN IN OPERATIONAL OR RETROSPECTIVE MODE. HAS MULTIPLE MODEL/ENSEMBLE
#OPTIONS. CAN ONLY SPECIFY ONE THRESHOLD AT A TIME. WHEN RUN IN RETROSPECTIVE MODE, CAN ONLY
#USE ONE MODEL/MEMBER AT A TIME. THIS SCRIPT IS TYPE ONE OF THE CODE AND IS BEST FOR BEING
#RUN IN OPERATIONAL MODE. TYPE 2 IS BEST FOR RETROSPECTIVE RUNNING BETWEEN A START AND 
#END DATE. MJE. 201708-20190606,20210609.

#Some specifics, 1) This code considers accumulation intervals with a resolution of one minute. 
#                2) This code considers model initializations with a resolution of one hour.
#
#Update: Fixed some minor inconsisteny issues with subhourly data. MJE. 20191114.
#Update: Addition to code to allow saving of simple operational objects for bias look-up tables
#and improving functionality to the way data is loaded. MJE. 20210323.
#Update: Added seasonal subset capability to dates loaded. MJE. 20210324.
#Update: Designate this verison of the code as type 1 for saving MTD option. MJE. 20210609.
################################################################################################

import pygrib
import sys
import os
import numpy as np
import time
import datetime
import matplotlib as mpl
mpl.use('Agg') #So plots can be saved in cron
import matplotlib.pyplot as plt
from scipy.io import netcdf
from netCDF4 import Dataset
from scipy import ndimage
import importlib
#Load predefined functions
sys.path.append('/export/hpc-lw-dtbdev5/merickson/code/python/MET')
import METConFigGenV100
import METLoadEnsemble
import METPlotEnsemble
import subprocess
importlib.reload(METConFigGenV100)
importlib.reload(METLoadEnsemble)
importlib.reload(METPlotEnsemble)

print(datetime.datetime.now())

################################################################################
########################1)MATRIX OF VARIABLES###################################
################################################################################
MET_PATH       = '/opt/MET/METPlus4_0/bin/'                                    #Location of MET software
CON_PATH       = '/export/hpc-lw-dtbdev5/wpc_cpgffh/METv6.0/'          #Location of MET config files
GRIB_PATH      = '/export/hpc-lw-dtbdev5/wpc_cpgffh/gribs/'            #Location of model GRIB files
FIG_PATH       = '/export/hpc-lw-dtbdev5/wpc_cpgffh/figures/MET/'      #Location for figure generation
TRACK_PATH     = '/export/hpc-lw-dtbdev5/wpc_cpgffh/tracks/'           #Location for saving track files
beg_date       = datetime.datetime(2021,5,1,0,0,0)                    #Beginning time of retrospective runs (datetime element)
end_date       = datetime.datetime(2021,5,1,1,0,0)                     #Ending time of retrospective runs (datetime element)
init_inc       = 1                                                     #Initialization increment (hours; e.g. total hours between model init. cycles)
season_sub     = [5,6,7,8]                                             #Seasonally subset the data by month (array of months to keep)
latlon_dims    = [-126,23,-65,50]                                      #Latitude/longitude dimensions for plotting [WLON,SLAT,ELON,NLAT]
pre_acc        = 1.0                                                   #Precipitation accumulation total
total_fcst_hrs = 18.0                                                   #Last forecast hour to be considered
start_hrs      = 0.0                                                   #Skip hours ahead before running MET
thres          = 0.1                                                   #Precip. threshold for defining objects (inches) (specifiy single value)
sigma          = 2                                                     #Gaussian Filter for smoothing ensemble probabilities in some plots (grid points)
plot_allhours  = 'FALSE'                                               #Plot every track figure hour-by-hour (good for comparing tracker to eye)     
snow_mask      = 'FALSE'                                               #Keep only regions that are snow 'TRUE' or no masking 'FALSE'
mtd_mode       = 'Retro'                                               #'Operational' to run live data for plotting or 'Retro' for retroruns
ops_check      = 60*60*0                                               #If in 'Operational' mode, how many seconds to wait before exiting 
conv_radius    = 6                                                     #Radius of the smoothing (grid squares)
min_volume     = 700                                                   #Area threshold (grid squares) to keep an object
ti_thresh      = 0.7                                                   #Total interest threshold for determining matches   
load_model     = ['HRRRv4_TLE_lag00']                                  #Models to be loaded (in 'retro' can only load ensemble members)
load_qpe       = ['ST4_lag00']#['MRMS15min_lag00']                     #'ST4','MRMS',or 'NONE' (NOTE: NEWS-E and HRRRe DOES NOT WORK FOR ANYTHING OTHER THAN LAG = 00)
GRIB_PATH_DES  = 'MTD_QPF_HRRRTLE_EXT'                                 #An appended string label for the temporary directory name
domain_sub     = ['_ALL','_NW','_SW','_NC','_SC','_NE','_SE']          #Sub-domain names for plotting (Operational model only)
latlon_sub     = [[-130,20,-64,52],[-130,36,-100,52],[-128,26,-98,42],[-112,34,-82,50], \
                     [-115,24,-85,40],[-93,34,-63,50],[-100,22,-70,40]]#Sub-domain lat/lon sizes for plotting (Operational mode only)
################################################################################

#Adjust beginning and end dates to proper ranges given 'init_inc'
beg_date = beg_date + datetime.timedelta(hours = (init_inc-beg_date.hour%init_inc)*(beg_date.hour%init_inc>0))
end_date = end_date - datetime.timedelta(hours = end_date.hour%init_inc)

#Throw an error if 'end_date' is before 'beg_date'
if (end_date - beg_date).days < 0:
    raise ValueError("'end_date' is before 'beg_date'")

#If mtd_mode='Operational' then there should be no verification and only one cycle analyzed
if mtd_mode == 'Operational':
    if load_qpe[0] != 'None':
        raise ValueError('If mtd_mode = \'Operational\' then load_qpe = \'None\'')  
    if beg_date != end_date:
        raise ValueError('If mtd_mode = \'Operational\' then beg_date = end_date (e.g. Only one model cycle)')
elif mtd_mode == 'Retro':
    FIG_PATH = FIG_PATH+'RETRO/'
    if len(load_model) > 1:
        raise ValueError('If mtd_mode = \'Retro\' then only one model specification at a time')    

#NEWSe not contain snow information
if 'NEWSe' in ''.join(load_model) and snow_mask == 'TRUE':
    raise ValueError('NEWSe does not contain the appropriate snow mask information')  
    
#If using NEWSe/MRMS, only load 1 hour increment or less
if ('NEWSe' in ''.join(load_model) or 'MRMS' in load_qpe) and pre_acc > 1:
    raise ValueError('NEWSe or MRMS data can only Have a precipitation accumulation interval of 1 hour or less')
    
#Determine if models are being compared to QPE, or if the models are solo
if load_qpe[0].lower() != 'none':
    load_data = np.append(load_model,load_qpe[0])
else:
    load_data = load_model

#Set the proper forecast hours load depending on the initialization
hrs = np.arange(0.0,total_fcst_hrs+1,pre_acc)
hrs = hrs[hrs > 0]    

#Set hours to be loaded conditional on starting time
hrs = hrs + start_hrs
hrs = hrs[hrs >= start_hrs]
hrs = hrs[hrs <= total_fcst_hrs]

#Logical matrix = 1 if model and = 0 if obs
ismodel = []
for mod in load_data:
    if 'ST4' in mod or 'MRMS' in mod:
        ismodel = np.append(ismodel,0)
    else:
        ismodel = np.append(ismodel,1)
      
os.environ["LD_LIBRARY_PATH"] ='/opt/MET/METPlus4_0/external_libs/lib:/export-5/ncosrvnfs-cp/'+ \
    'nawips2/os/linux2.6.32_x86_64/lib:/lib:/usr/lib:/export-5/ncosrvnfs-cp/nawips3/'+ \
    'os/linux2.6.32_x86_64/lib:/export/hpc-lw-dtbdev5/'+ \
    'merickson/Canopy/appdata/canopy-1.7.2.3327.rh5-x86_64/lib:/usr/lib64/openmpi/lib/'
os.environ["LIBS"] = '/opt/MET/METPlus4_0/external_libs'

#Record the current date
datetime_now = datetime.datetime.now()

################################################################################
##########3) LOAD MODEL DATA, RUN MTD###########################################
################################################################################

#Create datetime list of all model initializations to be loaded
delta = end_date - beg_date
total_incs = int(((delta.days * 24) + (delta.seconds / 3600) - 1) / init_inc)
list_date = []
for i in range(total_incs+1):
    if (beg_date + datetime.timedelta(hours = i * init_inc)).month in season_sub:
        list_date = np.append(list_date,beg_date + datetime.timedelta(hours = i * init_inc))

for datetime_curdate in list_date: #through the dates

        #Given the variables, create metadata for loading models and lots of things under the hood
        (GRIB_PATH_TEMP,FIG_PATH_s,curdate,init_yrmondayhr,hrs,offset_fcsthr,load_data_nc,acc_int,lat,lon) = \
            METLoadEnsemble.setupData(GRIB_PATH,FIG_PATH,GRIB_PATH_DES,load_data,pre_acc,total_fcst_hrs,latlon_dims,datetime_curdate,thres)

        #Remove data in 'GRIB_PATH_TEMP'
        output = os.system("rm -rf "+GRIB_PATH_TEMP+"/*")
        
        #Initialize variables determining successfully downloaded models
        MTDfile_old        = ['dummyname'  for j in range(0,len(load_data))]
        MTDfile_new        = ['dummyname'  for j in range(0,len(load_data))]
        simp_bin           = np.zeros((lat.shape[0], lat.shape[1], len(hrs), len(load_data)),dtype=np.int8)
        clus_bin           = np.zeros((lat.shape[0], lat.shape[1], len(hrs), len(load_data)),dtype=np.int8)
        simp_prop          = [[] for i in range(0,len(load_data))]
        pair_prop          = [[] for i in range(0,len(load_data))]
        data_success       = np.ones([len(hrs), len(load_data)])
        mem                = []
        
        data_name_nc_all = []
        
        for model in range(len(load_data)): #Through the 1 model and observation
            
            #Create APCP string (e.g. pre_acc = 1, APCP_str_beg = 'A010000'; pre_acc = 0.25, APCP_str_beg = 'A001500')
            time_inc_beg = datetime.timedelta(hours=acc_int[model])
            time_inc_end = datetime.timedelta(hours=pre_acc)
            APCP_str_beg = 'A'+'{:02d}'.format(int(time_inc_beg.seconds/(3600)))+'{:02d}'.format(int(((time_inc_beg.seconds \
                 % 3600)/60 * (time_inc_beg.seconds >= 3600)) + ((time_inc_beg.seconds < 3600)*(time_inc_beg.seconds / 60))))+'00'
            APCP_str_end = 'A'+'{:02d}'.format(int(time_inc_end.seconds/(3600)))+'{:02d}'.format(int(((time_inc_end.seconds \
                 % 3600)/60 * (time_inc_end.seconds >= 3600)) + ((time_inc_end.seconds < 3600)*(time_inc_end.seconds / 60))))+'00'

            #Given the variables, create proper config files
            if 'NEWSe' in ''.join(load_model):
                config_name = METConFigGenV100.set_MTDConfig_NEWSe(CON_PATH,'MTDConfig_USE_SAMP',thres,conv_radius,min_volume,total_fcst_hrs,ti_thresh,APCP_str_end)
            else:
                config_name = METConFigGenV100.set_MTDConfig(CON_PATH,'MTDConfig_USE_SAMP',thres,conv_radius,min_volume,total_fcst_hrs,ti_thresh,APCP_str_end)

            #Isolate member number if there are multiple members
            if 'mem' in load_data_nc[model]:
                mem = np.append(mem,'_m'+load_data_nc[model][load_data_nc[model].find('mem')+3:load_data_nc[model].find('mem')+5])
            else:
                mem = np.append(mem,'')
                
            #Determine lag from string specification
            mod_lag = int(load_data[model][load_data[model].find('lag')+3:load_data[model].find('lag')+5])

            #NEWSe 60min files only store accumulated precip. Must load previous hour in instances of lag
            if 'NEWSe60min' in load_data[model] and mod_lag > 0:
                hrs_all = np.arange(hrs[0]-1,hrs[-1]+pre_acc,pre_acc)
                data_success       = np.concatenate((data_success,np.ones([1, len(load_data)])),axis = 0)
            else: 
                hrs_all = np.arange(hrs[0],hrs[-1]+pre_acc,pre_acc)

            while 1: #In operational mode, wait for a while to make sure all data comes in
                
                fcst_hr_count = 0
                data_name_grib        = []
                data_name_nc          = []
                data_name_nc_prev   = []
                for fcst_hr in hrs_all: #Through the forecast hours
    
                    #Create proper string of last hour loaded to read in MTD file
                    last_fcst_hr_str = '{:02d}'.format(int(fcst_hr+offset_fcsthr[model]))
    
                    #Sum through accumulated precipitation interval
                    sum_hr_count = 0
                    data_name_temp = []
                    data_name_temp_part = []
    
                    for sum_hr in np.arange(pre_acc-acc_int[model],-acc_int[model],-acc_int[model]):
                    
                        #range(int(pre_acc) - int(acc_int[model]),-1,int(-acc_int[model])):
                        
                        #Determine the forecast hour and min to load given current forecast hour, summing location and offset
                        fcst_hr_load = float(fcst_hr) + offset_fcsthr[model] - float(round(sum_hr,2))
                        fcst_hr_str  = '{:02d}'.format(int(fcst_hr_load))
                        fcst_min_str = '{:02d}'.format(int(round((fcst_hr_load-int(fcst_hr_load))*60)))
    
                        #Determine the end date for the summation of precipitation accumulation
                        curdate_ahead = curdate+datetime.timedelta(hours=fcst_hr_load - offset_fcsthr[model])
    
                        #Use function to load proper data filename string
                        data_name_temp = np.append(data_name_temp,METLoadEnsemble.loadDataStr(GRIB_PATH, load_data[model], init_yrmondayhr[model], acc_int[model], fcst_hr_str, fcst_min_str))
    
                        #Find location of last slash to isolate file name from absolute path
                        for i in range(0,len(data_name_temp[sum_hr_count])):
                            if '/' in data_name_temp[sum_hr_count][i]:
                                str_search = i + 1
                        data_name_temp_part = np.append(data_name_temp_part, data_name_temp[sum_hr_count][str_search::])
    
                        #Copy the needed files to a temp directory and note successes
                        output=os.system("cp "+data_name_temp[sum_hr_count]+".gz "+GRIB_PATH_TEMP)
                        sum_hr_count += 1
                    #END loop through accumulated precipitation
                    
                    #Create the string for the time increment ahead
                    yrmonday_ahead = str(curdate_ahead.year)+'{:02d}'.format(int(curdate_ahead.month))+'{:02d}'.format(int(curdate_ahead.day))
                    hrmin_ahead = '{:02d}'.format(int(curdate_ahead.hour))+'{:02d}'.format(int(curdate_ahead.minute))
    
                    #Gunzip the file 
                    output = os.system("gunzip "+GRIB_PATH_TEMP+"/*.gz")
                    
                    #Create archive of last hour grib file name within the summed increment
                    data_name_grib     = np.append(data_name_grib, data_name_temp_part)
    
                    #Create variable name for pcp_combine
                    if load_qpe[0] in load_data[model]:
                        pcp_combine_str = '00000000_000000'
                    else:
                        pcp_combine_str = init_yrmondayhr[model][:-2]+'_'+init_yrmondayhr[model][-2:]+'0000' 
    
                    #Create variables names for pcp_combine
                    if 'ST4' in load_data[model]:
                        pcp_combine_str_beg = '00000000_000000'
                    else:
                        pcp_combine_str_beg = init_yrmondayhr[model][:-2]+'_'+init_yrmondayhr[model][-2::]+'0000 '
                        
                    pcp_combine_str_end = yrmonday_ahead+'_'+hrmin_ahead+'00 '
    
                    os.chdir(GRIB_PATH_TEMP)
                    
                    ##########?) USE MET PCP_COMBINE TO CONVERT DATA TO NETCDF AND SUM PRECIPITATION WHEN APPLICABLE############

                    #Use MET pcp_combine to sum, except for 1 hr acc from NAM, which contains either 1, 2, 3 hr acc. precip
                    if 'HIRESNAM' in load_data[model] and pre_acc == 1:
                        if ((fcst_hr - 1) % 3) == 0:   #Every 3rd hour contains 1 hr acc. precip
                            output = os.system(MET_PATH+'/pcp_combine -sum '+pcp_combine_str_beg+' '+APCP_str_beg[1::]+' '+ \
                                pcp_combine_str_end+APCP_str_end[1::]+' '+GRIB_PATH_TEMP+'/'+load_data_nc[model]+' -pcpdir '+ \
                                GRIB_PATH_TEMP+'/ -name "'+APCP_str_end+'"')
                        elif ((fcst_hr - 2) % 3) == 0: #2nd file contains 2 hr  acc. precip
                            output = os.system(MET_PATH+'/pcp_combine -subtract '+GRIB_PATH_TEMP+'/'+data_name_grib[fcst_hr_count]+' 020000 '+ \
                                GRIB_PATH_TEMP+'/'+data_name_grib[fcst_hr_count-1]+' 010000 '+GRIB_PATH_TEMP+'/'+load_data_nc[model]+ \
                                ' -name "'+APCP_str_end+'"')
                        elif ((fcst_hr - 3) % 3) == 0: #3rd file contains 3 hr  acc. precip
                            output = os.system(MET_PATH+'/pcp_combine -subtract '+GRIB_PATH_TEMP+'/'+data_name_grib[fcst_hr_count]+' 030000 '+ \
                                GRIB_PATH_TEMP+'/'+data_name_grib[fcst_hr_count-1]+' 020000 '+GRIB_PATH_TEMP+'/'+load_data_nc[model]+ \
                                ' -name "'+APCP_str_end+'"')
                    elif 'HIRESNAM' in load_data[model] and pre_acc % 3 == 0: #NAM increments divisible by 3
                        
                        output = os.system(MET_PATH+'/pcp_combine -sum '+pcp_combine_str_beg+' 030000 '+ \
                            pcp_combine_str_end+' '+APCP_str_end[1::]+' '+GRIB_PATH_TEMP+'/'+ load_data_nc[model]+ \
                            ' -pcpdir '+GRIB_PATH_TEMP+'/  -name "'+APCP_str_end+'"')     
                    elif 'HIRESNAM' in load_data[model] and pre_acc % 3 == 1: #Error if desired interval is not 1 or divisible by 3
                        raise ValueError('NAM pre_acc variable can only be 1 or divisible by 3')
                    elif 'NEWSe60min' in load_data[model]:
                        if fcst_hr_load == 1: #If using fcst hour 1, no need to subtract data
                            output = os.system(MET_PATH+'/pcp_combine -sum '+pcp_combine_str_beg+' '+APCP_str_beg[1::]+' '+pcp_combine_str_end+' '+ \
                                APCP_str_end[1::]+' '+GRIB_PATH_TEMP+'/'+load_data_nc[model]+' -name "'+APCP_str_end+'"')
                        elif fcst_hr_load > 1: #If not first hour, subtract current from previous hour
                            output = os.system(MET_PATH+"/pcp_combine -subtract "+GRIB_PATH_TEMP+"/"+data_name_grib[fcst_hr_count]+" "+last_fcst_hr_str+" "+ \
                                GRIB_PATH_TEMP+"/"+data_name_grib[fcst_hr_count-1]+" "+'{:02d}'.format(int(last_fcst_hr_str)-1)+" "+GRIB_PATH_TEMP+"/"+ \
                                load_data_nc[model]+' -name "'+APCP_str_end+'"')
                    elif 'NEWSe5min' in load_data[model]:
                        output = os.system(MET_PATH+'/pcp_combine -sum  '+pcp_combine_str_beg+' '+APCP_str_beg[1::]+' '+pcp_combine_str_end+' '+ \
                            APCP_str_end[1::]+' '+GRIB_PATH_TEMP+'/'+load_data_nc[model]+' -field \'name="'+APCP_str_beg+'"; level="Surface";\''+ \
                            ' -name "'+APCP_str_end+'"')
                    elif 'MRMS15min' in load_data[model]:
                        call_str = [data_name_grib[i]+' \'name="'+APCP_str_beg+'" ; level="(*,*)" ; \'' for i in range(int((fcst_hr_count)*(pre_acc/acc_int[model])),int((fcst_hr_count+1)*(pre_acc/acc_int[model])))]
                        output = os.system(MET_PATH+'/pcp_combine -add  '+' '.join(call_str)+' '+ \
                            GRIB_PATH_TEMP+'/'+load_data_nc[model]+' -name "'+APCP_str_end+'"')
                    elif 'HRRRe' in load_data[model]:
                        
                        if pre_acc != 1:
                            raise ValueError('HRRRe pre_acc variable can only be set to 1')
                            
                        #HRRRe accumulates precip, so must subtract data from previous hour to obtain 1 hour acc. precip.
                        if fcst_hr == 1:
                            output = os.system(MET_PATH+'/pcp_combine -sum '+pcp_combine_str_beg+' '+APCP_str_beg[1::]+' '+ \
                                pcp_combine_str_end+APCP_str_end[1::]+' '+GRIB_PATH_TEMP+'/'+load_data_nc[model]+' -pcpdir '+ \
                                GRIB_PATH_TEMP+'/ -name "'+APCP_str_end+'"')
                        else:
                            output = os.system(MET_PATH+'/pcp_combine -subtract '+GRIB_PATH_TEMP+'/'+data_name_grib[fcst_hr_count]+ \
                                ' '+'{:02d}'.format(fcst_hr_count+1)+'0000 '+GRIB_PATH_TEMP+'/'+data_name_grib[fcst_hr_count-1]+' '+ \
                                '{:02d}'.format(fcst_hr_count)+'0000 '+GRIB_PATH_TEMP+'/'+load_data_nc[model]+ ' -name "'+APCP_str_end+ \
                                '"')
                                
                    else:
                        output = os.system(MET_PATH+'/pcp_combine -sum  '+pcp_combine_str_beg+' '+APCP_str_beg[1::]+' '+pcp_combine_str_end+' '+ \
                            APCP_str_end[1::]+' '+GRIB_PATH_TEMP+'/'+load_data_nc[model]+' -name "'+APCP_str_end+'"')
    
                    #For NEWSe/WoF the domain changes so determine domain here
                    if mtd_mode == 'Operational':
                        if 'NEWSe' in load_model[model] and not 'latlon_dims_keep' in locals():
                            try:
                                f = Dataset(GRIB_PATH_TEMP+"/"+load_data_nc[model], "a", format="NETCDF4")
                                latlon_sub = [[np.nanmin(np.array(f.variables['lon'][:]))-0.5,np.nanmin(np.array(f.variables['lat'][:]))-0.1,\
                                    np.nanmax(np.array(f.variables['lon'][:])),np.nanmax(np.array(f.variables['lat'][:]))+0.5]]
                                domain_sub = ['ALL']
                                f.close()
                            except:
                                pass
                    
                    #Regrid to ST4 grid using regrid_data_plane
                    data_success[fcst_hr_count,model] = subprocess.call(MET_PATH+"/regrid_data_plane "+GRIB_PATH_TEMP+"/"+ \
                        load_data_nc[model]+" "+GRIB_PATH+"/temp/ensmean_sample_NODELETE "+GRIB_PATH_TEMP+"/"+load_data_nc[model]+"2 "+ \
                        "-field 'name=\""+APCP_str_end+"\"; level=\""+APCP_str_end+ \
                        "\";' -name "+APCP_str_end,shell=True)
                    
                    #Remove original netcdf files
                    output=os.system("rm -rf "+GRIB_PATH_TEMP+"/"+load_data_nc[model])
    
                    #Rename netcdf file
                    data_name_nc = np.append(data_name_nc,GRIB_PATH_TEMP+"/"+load_data_nc[model][0:-3]+"_f"+fcst_hr_str+fcst_min_str+".nc")
                    output=os.system("mv "+GRIB_PATH_TEMP+"/"+load_data_nc[model]+"2 "+data_name_nc[fcst_hr_count])
                        
                    #Construct an array of filenames in the previous model portion of the loop when in retro mode
                    if (mtd_mode == 'Retro') and (load_model[0] not in load_data[model]):
                        data_name_nc_prev = np.append(data_name_nc_prev,GRIB_PATH_TEMP+"/"+load_data[0]+"_f"+fcst_hr_str+fcst_min_str+".nc")
                    elif (mtd_mode == 'Retro') and (load_model[0] in load_data[model]):
                        data_name_nc_prev = np.append(data_name_nc_prev,'null')
                        
                    #If csnow_mask is 'TRUE' 1) interpolate to common domain (regrid_data plane), 2) mask out non-snow data mask
                    if snow_mask == 'TRUE':

                        #Determine masking string
                        if 'NSSL' in GRIB_PATH_DES:
                            masking_str = 'WEASD'
                        else:
                            masking_str = 'CSNOW'
                                    
                        mask_file_in = GRIB_PATH_TEMP+'/'+data_name_grib[fcst_hr_count]
                        mask_file_ou = GRIB_PATH_TEMP+'/'+data_name_grib[fcst_hr_count]+'.nc'
                        
                        #Regrid the data to common grid
                        os.system(MET_PATH+'/regrid_data_plane '+mask_file_in+' '+GRIB_PATH+'/temp/ensmean_sample_NODELETE '+ \
                            mask_file_ou+' '+ '-field \'name="CSNOW"; level="L0";\' -name "'+APCP_str_end+'"')

                        #If considering WEASD, must subtract current hour from previous hour (if it exists)
                        if masking_str == 'WEASD' and fcst_hr_count > 0:
                            mask_file_ou_prev = GRIB_PATH_TEMP+'/'+data_name_grib[fcst_hr_count-1]+'.nc'
                            
                            output = os.system(MET_PATH+'/pcp_combine -subtract '+mask_file_ou+' \'name="WEASD_L0"; level="L0";\' '+ \
                                mask_file_ou_prev+' \'name="WEASD_L0"; level="L0";\' '+mask_file_ou+'2')
                                
                            #Mask out all non-snow data
                            os.system(MET_PATH+'/gen_vx_mask '+data_name_nc[fcst_hr_count]+' '+mask_file_ou+'2 '+data_name_nc[fcst_hr_count]+ \
                                '_2 -type data -input_field \'name="'+APCP_str_end+ \
                                '"; level="(*,*)";\' -mask_field \'name="'+APCP_str_end+'"; level="(*,*)";\' -thresh le0 -value 0 -name '+APCP_str_end)
                        else:
                            output = os.system("cp "+mask_file_ou+' '+mask_file_ou+'2')
                            
                            #Mask out all non-snow data
                            os.system(MET_PATH+'/gen_vx_mask '+data_name_nc[fcst_hr_count]+' '+mask_file_ou+'2 '+data_name_nc[fcst_hr_count]+ \
                                '_2 -type data -input_field \'name="'+APCP_str_end+ \
                                '"; level="(*,*)";\' -mask_field \'name="'+APCP_str_end+'"; level="(*,*)";\' -thresh le0 -value 0 -name '+APCP_str_end)
                        
                        #Replace old file with properly masked file
                        os.system("mv "+data_name_nc[fcst_hr_count]+"_2 "+data_name_nc[fcst_hr_count])
 
                    #END snow mask check
                    
    #############MTD DOES NOT ALLOW MASKING INTERNALLY SO MASK MODEL/OBS FIELD IF EITHER HAS MISSING DATA###################
                               
                    if (mtd_mode == 'Retro') and (load_qpe[0] in load_data[model]):
                        #First mask observation with model
                        os.system(MET_PATH+'/gen_vx_mask '+data_name_nc_prev[fcst_hr_count]+' '+data_name_nc[fcst_hr_count]+' '+data_name_nc_prev[fcst_hr_count]+'2 '+ \
                            ' -type data -input_field \'name="'+APCP_str_end+'" ; level="(*,*)" ;\' -mask_field \'name="'+APCP_str_end+ \
                            '" ; level="(*,*)" ;\' -thresh eq-9999 -value -9999 -name '+APCP_str_end)
                        os.system('mv '+data_name_nc_prev[fcst_hr_count]+'2 '+data_name_nc_prev[fcst_hr_count])
                        #Second mask model with observation
                        os.system(MET_PATH+'/gen_vx_mask '+data_name_nc[fcst_hr_count]+' '+data_name_nc_prev[fcst_hr_count]+' '+data_name_nc[fcst_hr_count]+'2 '+ \
                            ' -type data -input_field \'name="'+APCP_str_end+'" ; level="(*,*)" ;\' -mask_field \'name="'+APCP_str_end+ \
                            '" ; level="(*,*)" ;\' -thresh eq-9999 -value -9999 -name '+APCP_str_end)
                        os.system('mv '+data_name_nc[fcst_hr_count]+'2 '+data_name_nc[fcst_hr_count])
                            
                        #Remove the netcdf files
                        output=os.system("rm -rf "+GRIB_PATH_TEMP+"/"+load_data_nc[model])
                        
                    fcst_hr_count += 1
                #END through forecast hour

                #Remove original grib files
                for files in data_name_grib:
                    output = os.system('rm -rf '+GRIB_PATH_TEMP+'/'+files+'*')
                  
                #Determine which hours are successfully loaded for each model
                if (mtd_mode == 'Retro'):
                    hour_success = (data_success[:,[i for i in range(0,len(load_data)) if load_data[i] == load_qpe[0]][0]] + \
                        data_success[:,[i for i in range(0,len(load_data)) if load_data[i] == load_model[0]][0]]) == 0
                elif (mtd_mode == 'Operational'): #No OBS, compare model to itself 
                    hour_success = data_success[:,model] == 0
                
                #If not all of the data is in during operational mode, then pause for 2 minutes and try again. Repeat for one hour
                if np.nanmean(data_success[:,model]) != 0 and mtd_mode == 'Operational':
                    if (datetime.datetime.now() - datetime_now).seconds > ops_check:
                        print('Missing Model Data; Plotting What We Have')
                        break
                    else:
                        print('There is missing Model Data; Pausing')
                        time.sleep(120)
                elif np.nanmean(data_success[:,model]) == 0 and mtd_mode == 'Operational':
                    break
                else:
                    break 

            #END while check for all model data  
            
            #Create variable name for default MTD file and renamed MTD file
            if ((mtd_mode == 'Retro' and load_qpe[0] in load_data[model]) or (mtd_mode == 'Operational')):
                #Find first tracked forecast hour for mtd output label
                hours_MTDlabel    = (((np.argmax(hour_success == 1)+1)*pre_acc)+int(load_data[model][-2:])+int(init_yrmondayhr[model][-2:]))
                curdate_MTDlabel  = curdate + datetime.timedelta(hours = ((np.argmax(hour_success == 1)+1)*pre_acc))
                yrmonday_MTDlabel = str(curdate_MTDlabel.year)+'{:02d}'.format(int(curdate_MTDlabel.month))+'{:02d}'.format(int(curdate_MTDlabel.day))

                if hours_MTDlabel >= 24:
                    hours_MTDlabel = hours_MTDlabel - 24
                mins_MTDlabel     = '{:02d}'.format(int(((hours_MTDlabel - int(hours_MTDlabel))*60)))
                hours_MTDlabel    = '{:02d}'.format(int(hours_MTDlabel))

                MTDfile_old[model] = 'mtd_'+yrmonday_MTDlabel+'_'+hours_MTDlabel+mins_MTDlabel+'00V'
            MTDfile_new[model] = 'mtd_'+init_yrmondayhr[model][:-2]+'_h'+init_yrmondayhr[model][-2:]+'_f'+last_fcst_hr_str+'_'+ \
                load_data_nc[model][0:-3]+'_p'+'{0:.2f}'.format(pre_acc)+'_t'+str(thres)

            #Remove old MTD output files if they exist
            if os.path.isfile(GRIB_PATH_TEMP+'/'+MTDfile_new[model]): 
                os.remove(GRIB_PATH_TEMP+'/'+MTDfile_new[model])    
 
            #In retro mode, if there is no data in the model, then quit this attempt
            if mtd_mode == 'Retro' and load_data[model] != load_qpe[0] and np.nanmean(data_success[:,model]) == 1:
                print('skipped')
                break
               
            #Run MTD: 1) if QPE exists compare model to obs, otherwise 2) run mtd in single mode   
            output = []
            if mtd_mode == 'Retro' and load_qpe[0] in load_data[model]:
                print(MET_PATH+'/mtd -fcst '+' '.join(data_name_nc_prev[hour_success])+ \
                    ' -obs '+' '.join(data_name_nc[hour_success])+' -config '+config_name+' -outdir '+GRIB_PATH_TEMP)
                mtd_success = os.system(MET_PATH+'/mtd -fcst '+' '.join(data_name_nc_prev[hour_success])+ \
                    ' -obs '+' '.join(data_name_nc[hour_success])+' -config '+config_name+' -outdir '+GRIB_PATH_TEMP)
                cows
            elif mtd_mode == 'Operational' and load_qpe[0] not in load_data[model]: #No QPE, compare model to itself
                mtd_success = os.system(MET_PATH+'/mtd -single '+' '.join(data_name_nc[hour_success])+' -config '+ \
                    config_name+' -outdir '+GRIB_PATH_TEMP)
            
            #Matrix to gather all netcdf file strings
            data_name_nc_all = np.append(data_name_nc_all,data_name_nc)

            #Rename cluster file and 2d text file (QPE is handled later)
            if ((mtd_mode == 'Retro' and load_qpe[0] in load_data[model]) or (mtd_mode == 'Operational')):
                output = os.system('mv '+GRIB_PATH_TEMP+'/'+MTDfile_old[model]+'_obj.nc '+ GRIB_PATH_TEMP+'/'+MTDfile_new[model]+ \
                    '_obj.nc ')
                output = os.system('mv '+GRIB_PATH_TEMP+'/'+MTDfile_old[model]+'_2d.txt '+ GRIB_PATH_TEMP+'/'+MTDfile_new[model]+ \
                    '_2d.txt ')
                output = os.system('rm -rf '+GRIB_PATH_TEMP+'/'+MTDfile_old[model]+'_3d_ss.txt')
                output = os.system('rm -rf '+GRIB_PATH_TEMP+'/'+MTDfile_old[model]+'_3d_sc.txt')
                output = os.system('rm -rf '+GRIB_PATH_TEMP+'/'+MTDfile_old[model]+'_3d_ps.txt')
                output = os.system('rm -rf '+GRIB_PATH_TEMP+'/'+MTDfile_old[model]+'_3d_pc.txt')

        #END through model

        #Remove the netcdf files
        for files in data_name_nc_all:
            output=os.system("rm -rf "+files)
     
################################################################################
#########4 LOAD MTD DATA IN PROPER FORMAT TO BE SAVED###########################
################################################################################

        #Find model index location to load MTD data
        mod_loc = [i for i in range(0,len(MTDfile_new)) if load_model[0] in MTDfile_new[i]][0]
        
        #Function to read in MTD data
        for model in range(len(load_data)): #Through the 1 model and observation
            
            #Retro mode has one model/one obs only, but the obs are in the model data, so load model but collect obs for retro
            if mtd_mode == 'Retro':    
                (lat_t, lon_t, fcst_p, obs_p, simp_bin_p, clus_bin_p, simp_prop_k, pair_prop_k, data_success_p) = \
                    METLoadEnsemble.loadDataMTDV90(GRIB_PATH_TEMP, MTDfile_new[1], ismodel[model], latlon_dims)
            else:
                (lat_t, lon_t, fcst_p, obs_p, simp_bin_p, clus_bin_p, simp_prop_k, pair_prop_k, data_success_p) = \
                    METLoadEnsemble.loadDataMTDV90(GRIB_PATH_TEMP, MTDfile_new[model], ismodel[model], latlon_dims)
            print(pair_prop_k)
            print(simp_prop_k)

            #Determine length of hours, place into matrices properly time-matched
            if mtd_mode == 'Retro':
                hour_success = (data_success[:,[i for i in range(0,len(load_data)) if load_data[i] == load_qpe[0]][0]] + \
                    data_success[:,[i for i in range(0,len(load_data)) if load_data[i] == load_model[0]][0]]) == 0
            elif mtd_mode == 'Operational': #No OBS, compare model to itself 
                hour_success = data_success[:,model] == 0

            hours_true = np.where(hour_success == 1)[0]
            
            if not np.isnan(np.nanmean(simp_prop_k)):                
                #Add data to total matrices
                simp_prop[model]       = simp_prop_k
                pair_prop[model]       = pair_prop_k
            else:
                simp_prop[model]       = np.full((10,1),np.NaN)
                pair_prop[model]       = np.full((10,1),np.NaN)

            if np.mean(np.isnan(simp_bin_p)) != 1:
                simp_bin[:,:,hours_true,model] = simp_bin_p
            if np.mean(np.isnan(clus_bin_p)) != 1:
                clus_bin[:,:,hours_true,model] = clus_bin_p
          
            del simp_bin_p
                  
            #Create binomial grid where = 1 if model and obs exist
            if np.mean(np.isnan(obs_p)) == 1 or  np.mean(np.isnan(fcst_p)) == 1 or \
                np.isnan(np.mean(np.isnan(obs_p))) == 1 or  np.isnan(np.mean(np.isnan(fcst_p))) == 1:
                data_exist = np.zeros((lat.shape))
            else:
                data_exist = (np.isnan(obs_p[:,:,0].data)*1 + np.isnan(fcst_p[:,:,0].data)*1) == 0
            
            #If requested, plot hourly paired mod/obs objects to manually check results by-eye
            if plot_allhours == 'TRUE' and model > 0:
                #If the domain is subset, determine proper coordinates for plotting
                latmin = np.nanmin(lat_t[fcst_p[:,:,0].data>0])
                latmax = np.nanmax(lat_t[fcst_p[:,:,0].data>0])
                lonmin = np.nanmin(lon_t[fcst_p[:,:,0].data>0])
                lonmax = np.nanmax(lon_t[fcst_p[:,:,0].data>0])
                #METPlotEnsemble.MTDPlotRetroJustPrecip(GRIB_PATH_DES,FIG_PATH,[lonmin,latmin,lonmax,latmax],pre_acc,hrs_all,thres,curdate, \
                #    data_success,load_data_nc,lat,lon,fcst_p,obs_p)
                METPlotEnsemble.MTDPlotRetro(GRIB_PATH_DES,FIG_PATH,[lonmin,latmin,lonmax,latmax],pre_acc,hrs_all,thres,curdate, \
                    data_success,load_data_nc,lat,lon,fcst_p,obs_p,clus_bin,pair_prop)
            
            del clus_bin_p
            del fcst_p
            del obs_p
        
        #If running in retro mode, save the data and remove the old files        
        if mtd_mode == 'Retro':

            #Save the simple and paired model/obs track files specifying simp/pair, start/end time, hour acc. interval, and threshold
            if (np.sum(hour_success) > 0) and (mtd_mode == 'Retro') and (load_qpe[0] in load_data[model]):
                np.savez(TRACK_PATH+GRIB_PATH_DES+mem[0]+'_'+'{:04d}'.format(datetime_curdate.year)+'{:02d}'.format(datetime_curdate.month)+ \
                    '{:02d}'.format(datetime_curdate.day)+'{:02d}'.format(datetime_curdate.hour)+'_simp_prop'+'_s'+str(int(start_hrs))+\
                    '_e'+str(int(start_hrs+total_fcst_hrs))+'_h'+'{0:.2f}'.format(pre_acc)+'_t'+str(thres),simp_prop_k = simp_prop_k,data_exist = data_exist)
                np.savez(TRACK_PATH+GRIB_PATH_DES+mem[0]+'_'+'{:04d}'.format(datetime_curdate.year)+'{:02d}'.format(datetime_curdate.month)+ \
                    '{:02d}'.format(datetime_curdate.day)+'{:02d}'.format(datetime_curdate.hour)+'_pair_prop'+'_s'+str(int(start_hrs))+\
                    '_e'+str(int(start_hrs+total_fcst_hrs))+'_h'+'{0:.2f}'.format(pre_acc)+'_t'+str(thres),pair_prop_k = pair_prop_k,data_exist = data_exist)
                
                #Remove old files
                output = os.system('rm -rf '+TRACK_PATH+GRIB_PATH_DES+mem[0]+'_'+'{:04d}'.format(datetime_curdate.year)+'{:02d}'.format(datetime_curdate.month)+ \
                    '{:02d}'.format(datetime_curdate.day)+'{:02d}'.format(datetime_curdate.hour)+'_simp_prop'+'_s'+str(int(start_hrs))+\
                    '_e'+str(int(start_hrs+total_fcst_hrs))+'_h'+'{0:.2f}'.format(pre_acc)+'_t'+str(thres)+'.npz.gz')
                output = os.system('rm -rf '+TRACK_PATH+GRIB_PATH_DES+mem[0]+'_'+'{:04d}'.format(datetime_curdate.year)+'{:02d}'.format(datetime_curdate.month)+ \
                    '{:02d}'.format(datetime_curdate.day)+'{:02d}'.format(datetime_curdate.hour)+'_pair_prop'+'_s'+str(int(start_hrs))+\
                    '_e'+str(int(start_hrs+total_fcst_hrs))+'_h'+'{0:.2f}'.format(pre_acc)+'_t'+str(thres)+'.npz.gz')
                
                #Gunzip the files
                output = os.system('gzip '+TRACK_PATH+GRIB_PATH_DES+mem[0]+'_'+'{:04d}'.format(datetime_curdate.year)+'{:02d}'.format(datetime_curdate.month)+ \
                    '{:02d}'.format(datetime_curdate.day)+'{:02d}'.format(datetime_curdate.hour)+'_simp_prop'+'_s'+str(int(start_hrs))+\
                    '_e'+str(int(start_hrs+total_fcst_hrs))+'_h'+'{0:.2f}'.format(pre_acc)+'_t'+str(thres)+'.npz')
                output = os.system('gzip '+TRACK_PATH+GRIB_PATH_DES+mem[0]+'_'+'{:04d}'.format(datetime_curdate.year)+'{:02d}'.format(datetime_curdate.month)+ \
                    '{:02d}'.format(datetime_curdate.day)+'{:02d}'.format(datetime_curdate.hour)+'_pair_prop'+'_s'+str(int(start_hrs))+\
                    '_e'+str(int(start_hrs+total_fcst_hrs))+'_h'+'{0:.2f}'.format(pre_acc)+'_t'+str(thres)+'.npz')
        elif mtd_mode == 'Operational':#If in operational mode, create plots

            #Save an npz track file for the operational code (with no obs) for computation of bias look up tables
            if (np.sum(hour_success) > 0):

                #Remove old operational files of the same type, save new, and gzip
                output = os.system('rm -rf '+TRACK_PATH+GRIB_PATH_DES+mem[0]+'*_OPER*_simp_prop'+'_s*t'+str(thres)+'.npz.gz')

                np.savez(TRACK_PATH+GRIB_PATH_DES+mem[0]+'_OPER_'+'{:04d}'.format(datetime_curdate.year)+'{:02d}'.format(datetime_curdate.month)+ \
                    '{:02d}'.format(datetime_curdate.day)+'{:02d}'.format(datetime_curdate.hour)+'_simp_prop'+'_s'+str(int(start_hrs))+\
                    '_e'+str(int(start_hrs+total_fcst_hrs))+'_h'+'{0:.2f}'.format(pre_acc)+'_t'+str(thres),simp_prop_k = simp_prop_k,data_exist = data_exist)

                output = os.system('gzip '+TRACK_PATH+GRIB_PATH_DES+mem[0]+'_OPER_'+'{:04d}'.format(datetime_curdate.year)+'{:02d}'.format(datetime_curdate.month)+ \
                    '{:02d}'.format(datetime_curdate.day)+'{:02d}'.format(datetime_curdate.hour)+'_simp_prop'+'_s'+str(int(start_hrs))+\
                    '_e'+str(int(start_hrs+total_fcst_hrs))+'_h'+'{0:.2f}'.format(pre_acc)+'_t'+str(thres)+'.npz')

            if snow_mask == 'FALSE':
                #Loop through domain subset specifications to plot specific regions
                for subsets in range(0,len(domain_sub)):
                    #Plot the smoothed ensemble probabilities with object centroids
                    METPlotEnsemble.MTDPlotAllFcst(GRIB_PATH_DES+domain_sub[subsets],FIG_PATH_s,latlon_sub[subsets],pre_acc,hrs,thres,curdate, \
                        data_success,load_data_nc,lat,lon,simp_bin,simp_prop,sigma)
        
                    #Plot the objects for each TLE
                    METPlotEnsemble.MTDPlotTLEFcst(GRIB_PATH_DES+domain_sub[subsets],FIG_PATH_s,latlon_sub[subsets],pre_acc,hrs,thres,curdate, \
                        data_success,load_data_nc,lat,lon,simp_bin,simp_prop,sigma)
            elif snow_mask == 'TRUE':        
                #Loop through domain subset specifications to plot specific regions
                for subsets in range(0,len(domain_sub)):
                    #Plot the smoothed ensemble probabilities with object centroids
                    METPlotEnsemble.MTDPlotAllSnowFcst(GRIB_PATH_DES+domain_sub[subsets],FIG_PATH_s,latlon_sub[subsets],pre_acc,hrs,thres,curdate, \
                        data_success,load_data_nc,lat,lon,simp_bin,simp_prop)

        #Delete workspace variables
        del simp_prop 
        del pair_prop 
        del simp_bin
        
        #Delete the source files to save hard drive space
        output=os.system('rm -rf '+GRIB_PATH_TEMP)
   
        #Fix an issue by deleting a folder created in METLoadEnsemble.setupData if no plotting is requested
        if plot_allhours == 'FALSE' and mtd_mode == 'Retro':
            os.system("rm -rf "+FIG_PATH+"/"+'{:04d}'.format(datetime_curdate.year)+'{:02d}'.format(datetime_curdate.month)+ \
                '{:02d}'.format(datetime_curdate.day)+'{:02d}'.format(datetime_curdate.hour))
           
#Copy over relevant images to  http://origin.wpc.ncep.noaa.gov/verification/mtd/images/ for website
if mtd_mode == 'Operational':
    if snow_mask == 'FALSE':
        for subsets in range(0,len(domain_sub)):
            if 'NEWSe' in ''.join(load_data):
                hrs_count = 1
                for hours in hrs:
                    filename_o = GRIB_PATH_DES+domain_sub[subsets]+'_TOTENS_objprob_byhour_'+'{:04d}'.format(curdate.year)+ \
                        '{:02d}'.format(curdate.month)+'{:02d}'.format(curdate.day)+ '{:02d}'.format(curdate.hour)+ \
                        '_p'+'{0:.2f}'.format(pre_acc)+'_t'+str(thres)+'_f'+'{:02d}'.format(int(hrs_count))+'.png'
                    os.system('scp '+FIG_PATH_s+'/'+filename_o+' hpc@vm-lnx-rzdm05:/home/people/hpc/www/'+ \
                        'htdocs/WoF/images/'+filename_o)
                    hrs_count += 1
            elif 'HRRRv415min' in ''.join(load_data):
                hrs_count = 1
                for hours in hrs:
                    filename_o = GRIB_PATH_DES+domain_sub[subsets]+'_TOTENS_objprob_byhour_'+'{:04d}'.format(curdate.year)+ \
                        '{:02d}'.format(curdate.month)+'{:02d}'.format(curdate.day)+ '{:02d}'.format(curdate.hour)+ \
                        '_p'+'{0:.2f}'.format(pre_acc)+'_t'+str(thres)+'_f'+'{:02d}'.format(int(hrs_count))+'.png'
                    os.system('scp '+FIG_PATH_s+'/'+filename_o+' hpc@vm-lnx-rzdm05:/home/people/hpc/www/'+ \
                        'htdocs/HRRRSubHr/images/'+filename_o)
                    hrs_count += 1
            else:

                hrs_count = 1
                for hours in hrs:
                    filename_o = GRIB_PATH_DES+domain_sub[subsets]+'_TOTENS_objprob_byhour_'+'{:04d}'.format(curdate.year)+ \
                        '{:02d}'.format(curdate.month)+'{:02d}'.format(curdate.day)+ '{:02d}'.format(curdate.hour)+ \
                        '_p'+'{0:.2f}'.format(pre_acc)+'_t'+str(thres)+'_f'+'{:02d}'.format(int(hrs_count))+'.png'
                    os.system('scp '+FIG_PATH_s+'/'+filename_o+' hpc@vm-lnx-rzdm05:/home/people/hpc/www/'+ \
                        'htdocs/verification/mtd/images/'+filename_o)
                    hrs_count += 1

                filename_o = GRIB_PATH_DES+domain_sub[subsets]+'_TOTENS_objprob_bymodel_'+'{:04d}'.format(curdate.year)+ \
                    '{:02d}'.format(curdate.month)+'{:02d}'.format(curdate.day)+ '{:02d}'.format(curdate.hour)+ \
                    '_p'+'{0:.2f}'.format(pre_acc)+'_t'+str(thres)+'.png'
                filename_n = GRIB_PATH_DES+domain_sub[subsets]+'_TOTENS_objprob_bymodel_p'+ \
                    '{0:.2f}'.format(pre_acc)+'_t'+str(thres)+'.png'
                os.system('cp '+FIG_PATH_s+'/'+filename_o+' '+FIG_PATH_s+'/'+filename_n)
                os.system('scp '+FIG_PATH_s+'/'+filename_n+' hpc@vm-lnx-rzdm05:/home/people/hpc/www/'+ \
                    'htdocs/verification/mtd/images/'+filename_n)

                filename_o = GRIB_PATH_DES+domain_sub[subsets]+'_TOTENS_objprob_byhour_'+'{:04d}'.format(curdate.year)+ \
                    '{:02d}'.format(curdate.month)+'{:02d}'.format(curdate.day)+ '{:02d}'.format(curdate.hour)+ \
                    '_p'+'{0:.2f}'.format(pre_acc)+'_t'+str(thres)+'.gif'
                filename_n = GRIB_PATH_DES+domain_sub[subsets]+'_TOTENS_objprob_byhour_p'+ \
                    '{0:.2f}'.format(pre_acc)+'_t'+str(thres)+'.gif'
                os.system('cp '+FIG_PATH_s+'/'+filename_o+' '+FIG_PATH_s+'/'+filename_n)
                os.system('scp '+FIG_PATH_s+'/'+filename_n+' hpc@vm-lnx-rzdm05:/home/people/hpc/www/'+ \
                    'htdocs/verification/mtd/images/'+filename_n)
                   
        #Clear files older than two days from vm-lnx-rzdm05 to save memory
        curdate_old  = curdate - datetime.timedelta(days=2)
        yrmonday_old = '{:04d}'.format(curdate_old.year)+'{:02d}'.format(curdate_old.month)+'{:02d}'.format(curdate_old.day)
        os.system("ssh hpc@vm-lnx-rzdm05 'rm /home/people/hpc/www/htdocs/WoF/images/*"+GRIB_PATH_DES+"*"+yrmonday_old+"*png'")

        yrmonday_old = '{:04d}'.format(curdate_old.year)+'{:02d}'.format(curdate_old.month)+'{:02d}'.format(curdate_old.day)
        os.system("ssh hpc@vm-lnx-rzdm05 'rm /home/people/hpc/www/htdocs/verification/mtd/images/*"+GRIB_PATH_DES+"*"+yrmonday_old+"*png'")

        #For HRRR subhourly, remove files that are 18-24 hours old
        for hrz in range(36,48):
            curdate_old    = curdate - datetime.timedelta(hours=hrz)
            yrmondayhr_old = '{:04d}'.format(curdate_old.year)+'{:02d}'.format(curdate_old.month)+'{:02d}'.format(curdate_old.day)+'{:02d}'.format(curdate_old.hour)
            os.system("ssh hpc@vm-lnx-rzdm05 'rm /home/people/hpc/www/htdocs/HRRRSubHr/images/*"+GRIB_PATH_DES+"*"+yrmondayhr_old+"*png'")
 
    elif snow_mask == 'TRUE':  

        #Copy over relevant images to  http://origin.wpc.ncep.noaa.gov/verification/mtd/images/ for website
        for subsets in range(0,len(domain_sub)):
            for hours in hrs:
                filename_o = GRIB_PATH_DES+domain_sub[subsets]+'_snowobj_byhour_'+'{:04d}'.format(curdate.year)+ \
                    '{:02d}'.format(curdate.month)+'{:02d}'.format(curdate.day)+ '{:02d}'.format(curdate.hour)+ \
                    '_p'+'{0:.2f}'.format(pre_acc)+'_t'+str(thres)+'_h'+'{:02d}'.format(int(hours))+'.png'
                os.system('scp '+FIG_PATH_s+'/'+filename_o+' hpc@vm-lnx-rzdm05:/home/people/hpc/www/'+ \
                    'htdocs/snowbands/images/'+filename_o, \
                    shell=True)

        #Clear files older than two weeks from vm-lnx-rzdm05 to save memory
        curdate_old  = curdate - datetime.timedelta(days=7)
        yrmonday_old = '{:04d}'.format(curdate_old.year)+'{:02d}'.format(curdate_old.month)+'{:02d}'.format(curdate_old.day)
        os.system("ssh hpc@vm-lnx-rzdm05 'rm /home/people/hpc/www/htdocs/snowbands/images/*"+GRIB_PATH_DES+"*"+yrmonday_old+"*png'")
        
datetime.datetime.now()      
###SAMPLE PLOTTING SCRIPT####
#fid          = Dataset('/export/hpc-lw-dtbdev5/merickson/temp/2018071218_preacc_0.5_MTD_RETRO_NEWSe15min_t0.01/mtd_20180712_183000V_obj.nc', 'a', format='NETCDF4')
#lat          = (np.array(fid.variables['lat'][:]))*1
#lon          = (np.array(fid.variables['lon'][:]))*1
#fcst_raw     = (np.array(fid.variables['fcst_raw'][:]))*1
#obs_raw      = (np.array(fid.variables['obs_raw'][:]))*1
#
#for i in range(0,fcst_raw.shape[0]):
#    values = [0,0.05,0.10,0.20,0.50,1.0]
#    my_cmap2 = mpl.cm.get_cmap('cool')
#    my_cmap2.set_under('white')    
#    plt.figure()
#    ax = plt.gca()
#    #Create polar stereographic Basemap instance.
#    m = Basemap(llcrnrlon=-105, llcrnrlat=40, urcrnrlon=-90,urcrnrlat=48,resolution='i',projection='merc')
#    #Draw coastlines, state and country boundaries, edge of map.
#    m.drawcoastlines(linewidth=0.5)
#    m.drawstates(linewidth=0.5)
#    m.drawcountries(linewidth=0.5)
#    #Draw parallels and meridians
#    m.drawparallels(np.arange(0,90,5),labels=[1,0,0,0],fontsize=12,linewidth=0.5) #labels=[left,right,top,bottom]
#    m.drawmeridians(np.arange(-180,0,10),labels=[0,0,0,1],fontsize=12,linewidth=0.5) #labels=[left,right,top,bottom]
#    props = dict(boxstyle='round', facecolor='wheat', alpha=1)
#    cs = m.contourf(lon, lat, fcst_raw[i,:,:], latlon=True, levels=values, extend='min', cmap=my_cmap2, antialiased=False, markerstyle='o', vmin=np.min(values),vmax=np.max(values))
#    cb = m.colorbar(cs,"right", ticks=values, size="5%", pad="2%", extend='min')
#    
#for i in range(0,fcst_raw.shape[0]):
#    values = [0,0.05,0.10,0.20,0.50,1.0]
#    my_cmap2 = mpl.cm.get_cmap('cool')
#    my_cmap2.set_under('white')    
#    plt.figure()
#    ax = plt.gca()
#    #Create polar stereographic Basemap instance.
#    m = Basemap(llcrnrlon=-105, llcrnrlat=40, urcrnrlon=-90,urcrnrlat=48,resolution='i',projection='merc')
#    #Draw coastlines, state and country boundaries, edge of map.
#    m.drawcoastlines(linewidth=0.5)
#    m.drawstates(linewidth=0.5)
#    m.drawcountries(linewidth=0.5)
#    #Draw parallels and meridians
#    m.drawparallels(np.arange(0,90,5),labels=[1,0,0,0],fontsize=12,linewidth=0.5) #labels=[left,right,top,bottom]
#    m.drawmeridians(np.arange(-180,0,10),labels=[0,0,0,1],fontsize=12,linewidth=0.5) #labels=[left,right,top,bottom]
#    props = dict(boxstyle='round', facecolor='wheat', alpha=1)
#    cs = m.contourf(lon, lat, obs_raw[i,:,:], latlon=True, levels=values, extend='min', cmap=my_cmap2, antialiased=False, markerstyle='o', vmin=np.min(values),vmax=np.max(values))
#    cb = m.colorbar(cs,"right", ticks=values, size="5%", pad="2%", extend='min')
