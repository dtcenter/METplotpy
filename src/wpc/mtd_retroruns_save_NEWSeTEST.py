#!/usr/bin/python

################################################################################################
#USED TO RUN MTD IN RETROSPECTIVE MODE FOR ONLY ONE MODEL AT A TIME AND SAVE THE DATA. 
#THIS SCRIPT IS THE MOST TIME CONSUMING OF THE RETROSPECTIVE SINCE IT INVOKES MTD.
#IF NAMELIST SETTINGS AREN'T CHANGED, THIS PORTION ONLY HAS TO BE RUN ONCE. 
#USE 'mtd_retroruns_plot' TO LOAD THE OUTPUT FROM THIS SCRIPT, AGGREGATE, ANALYZE, AND PLOT THE OUTPUT FROM
#THIS SCRIPT. MJE. 201708-20171214.

#Some specifics, 1) This code considers accumulation intervals with a resolution of one minute. 
#                2) This code considers model initializations with a resolution of one hour.
################################################################################################

import pygrib
import subprocess
import os
import numpy as np
import datetime
from mpl_toolkits.basemap import Basemap, cm
import matplotlib as mpl
mpl.use('Agg') #So plots can be saved in cron
import matplotlib.pyplot as plt
from matplotlib.mlab import griddata
from scipy.io import netcdf
from netCDF4 import Dataset
from scipy import ndimage

#Load predefined functions
import METConFigGen_NEW
import METLoadEnsemble_NEW
import METPlotEnsemble
reload(METConFigGen_NEW)
reload(METLoadEnsemble_NEW)
reload(METPlotEnsemble)

################################################################################
#########################1)MATRIX OF VARIABLES#################################
################################################################################
MET_PATH       = '/opt/MET7/bin'                                        #Location of MET software
CON_PATH       = '/usr1/wpc_cpgffh/METv6.0/'                            #Location of MET config files
GRIB_PATH      = '/usr1/wpc_cpgffh/gribs/'                              #Location of model GRIB files
FIG_PATH       = '/usr1/wpc_cpgffh/figures/MET/RETRO/'                  #Location for figure generation
TRACK_PATH     = '/usr1/wpc_cpgffh/tracks/'                             #Location for saving track files
snow_mask      = 'FALSE'                                                #Keep only regions that are snow 'TRUE' or no masking 'FALSE'
beg_date       = datetime.datetime(2018,7,18,18,0,0)                    #Beginning time of retrospective runs (datetime element)
end_date       = datetime.datetime(2018,7,18,18,0,0)                    #Ending time of retrospective runs (datetime element)
latlon_dims    = [-126,23,-65,50]                                       #Latitude/longitude dimensions for plotting [WLON,SLAT,ELON,NLAT]
pre_acc        = 1.0/4.0                                                #Precipitation accumulation total
total_fcst_hrs = 6.0                                                    #Last forecast hour to be considered
start_hrs      = 0.0                                                    #Skip hours ahead before running MET                                                                                                                             
thres          = 0.2                                                   #Precip. threshold for defining objects (inches) (specifiy single value)
conv_radius    = 2                                                      #Radius of the smoothing (grid squares)
min_volume     = 20                                                     #Area threshold (grid squares) to keep an object
ti_thresh      = 0.7                                                    #Total interest threshold for determining matches   
#load_model     = ['NEWSe60min_mem01_lag00','NEWSe60min_mem02_lag00','NEWSe60min_mem03_lag00','NEWSe60min_mem04_lag00','NEWSe60min_mem05_lag00','NEWSe60min_mem06_lag00','NEWSe60min_mem07_lag00','NEWSe60min_mem08_lag00','NEWSe60min_mem09_lag00'] #['NEWSe5min_mem02_lag00']                             #Choose the model to load (NOTE: NEWS-E DOES NOT WORK FOR ANYTHING OTHER THAN LAG = 00)
load_model     = ['NEWSe5min_mem02_lag00'] 
load_qpe       = ['MRMS15min_lag00']                                    #'ST4','MRMS',or 'NONE' (NOTE: NEWS-E DOES NOT WORK FOR ANYTHING OTHER THAN LAG = 00)
plot_allhours  = 'TRUE'                                                #Plot every track figure hour-by-hour (good for comparing tracker to eye)     
GRIB_PATH_DES  = 'MTD_RETRO_NEWSe15min_t'+str(thres)                    #An appended string label for the temporary directory name            

################################################################################

#If using NEWSe/MRMS, only load 1 hour increment or less
if ('NEWSe' in ''.join(load_model) or 'MRMS' in load_qpe) and pre_acc > 1:
    raise ValueError('NEWSe or MRMS data can only Have a precipitation accumulation interval of 1 hour or less')
    
#Determine if models are being compared to QPE, or if the models are solo
if load_qpe[0] is not 'None':
    load_data = np.insert(load_model,0,load_qpe[0])
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
      
#Create log file for writting
log_file = '/export/hpc-lw-dtbdev5/merickson/log/'+GRIB_PATH_DES+'_s'+snow_mask+'_f'+ \
    str(int(total_fcst_hrs))+'_p'+str(int(pre_acc))+'_t'+str(thres)+'.log'
target = open(log_file,'w')
target.close()

#Set environment for MET properly
os.environ["LD_LIBRARY_PATH"] = '/lib:/usr/lib:/lib:/opt/MET7/external_libs/lib:'+ \
    '/export/hpc-lw-dtbdev5/merickson/Canopy/appdata/canopy-1.7.2.3327.rh5-x86_64/lib'
os.environ["LIBS"] = '/opt/MET7/external_libs'

################################################################################
##########3) LOAD MODEL DATA, RUN MTD###########################################
################################################################################

beg_date_jul = pygrib.datetime_to_julian(beg_date)
end_date_jul = pygrib.datetime_to_julian(end_date)

for dates in range(int(round(beg_date_jul)),int(round(end_date_jul))+1): #through the dates

    #Create datetime element for day being loaded
    datetime_curdate = pygrib.julian_to_datetime(dates)

    #If first or last date, load starting/end forecast hour
    if dates == int(round(beg_date_jul)) and dates == int(round(end_date_jul)):
        init_hrs = range(beg_date.hour,end_date.hour+1)
    elif dates == int(round(beg_date_jul)) and dates != int(round(end_date_jul)):
        init_hrs = range(beg_date.hour,24)
    elif dates == int(round(end_date_jul)) and dates != int(round(beg_date_jul)):
        init_hrs = range(0,end_date.hour+1)
    else:
        init_hrs = range(0,24)

    for inits in init_hrs: #through the model initializations
        
        #Edit datetime element to reflect proper hour
        datetime_curdate = datetime_curdate.replace(hour = inits)
        
        print datetime_curdate
        
        #Given the variables, create metadata for loading models and lots of things under the hood
        (GRIB_PATH_TEMP,FIG_PATH_s,curdate,init_yrmondayhr,hrs,offset_fcsthr,load_data_nc,acc_int,lat,lon) = \
            METLoadEnsemble_NEW.setupData(GRIB_PATH,FIG_PATH,GRIB_PATH_DES,load_data,pre_acc,total_fcst_hrs,latlon_dims,datetime_curdate)

        #Remove data in 'GRIB_PATH_TEMP'
        output = subprocess.call("rm -rf "+GRIB_PATH_TEMP+"/*", stdout=open(os.devnull, 'wb'), stderr=open(os.devnull, 'wb'), shell=True)
        
        #Initialize variables determining successfully downloaded models
        MTDfile_old        = [[]  for j in range(0,len(load_data))]
        MTDfile_new        = [[]  for j in range(0,len(load_data))]   
        
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
            hrstr_beg    = '{:02d}'.format(int(time_inc_beg.seconds/(60*60)))
            hrstr_end    = '{:02d}'.format(int(time_inc_end.seconds/(60*60)))
            minstr_beg   = '{:02d}'.format(int((time_inc_beg.seconds-(60*60*(time_inc_beg.seconds>=60*60)))/60))
            minstr_end   = '{:02d}'.format(int((time_inc_end.seconds-(60*60*(time_inc_end.seconds>=60*60)))/60))
            APCP_str_beg = 'A'+hrstr_beg+minstr_beg+'00'
            APCP_str_end = 'A'+hrstr_end+minstr_end+'00'

            
            #Given the variables, create proper config files
            config_name = METConFigGen_NEW.set_MTDConfig_NEWSe(CON_PATH,'MTDConfig_USE_SAMP',thres,conv_radius,min_volume,total_fcst_hrs,ti_thresh,APCP_str_end)
            
            #Isolate member number if there are multiple members
            if 'mem' in load_data_nc[model]:
                mem = np.append(mem,'_m'+load_data_nc[model][load_data_nc[model].find('mem')+3:load_data_nc[model].find('mem')+5])
            else:
                mem = np.append(mem,'')
                
            #Determine lag from string specification
            mod_lag = int(load_data[model][load_data[model].find('lag')+3:load_data[model].find('lag')+5])
            
            fcst_hr_count = 0
            data_name_grib        = []
            data_name_nc          = []
            data_name_nc_lagQPE   = []
            
            #NEWSe 60min files only store accumulated precip. Must load previous hour in instances of lag
            if 'NEWSe60min' in load_data[model] and mod_lag > 0:
                hrs_all = np.arange(hrs[0]-1,hrs[-1]+pre_acc,pre_acc)
                data_success       = np.concatenate((data_success,np.ones([1, len(load_data)])),axis = 0)
            else: 
                hrs_all = np.arange(hrs[0],hrs[-1]+pre_acc,pre_acc)

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
                    data_name_temp = np.append(data_name_temp,METLoadEnsemble_NEW.loadDataStr(GRIB_PATH, load_data[model], init_yrmondayhr[model], acc_int[model], fcst_hr_str, fcst_min_str))

                    #Find location of last slash to isolate file name from absolute path
                    for i in range(0,len(data_name_temp[sum_hr_count])):
                        if '/' in data_name_temp[sum_hr_count][i]:
                            str_search = i + 1
                    data_name_temp_part = np.append(data_name_temp_part, data_name_temp[sum_hr_count][str_search::])

                    #Copy the needed files to a temp directory and note successes
                    output=subprocess.call("cp "+data_name_temp[sum_hr_count]+".gz "+GRIB_PATH_TEMP, stdout=open(os.devnull, 'wb'), stderr=open(os.devnull, 'wb'), shell=True)
                    sum_hr_count += 1
                #END loop through accumulated precipitation
                
                #Create the string for the time increment ahead
                yrmonday_ahead = str(curdate_ahead.year)+'{:02d}'.format(int(curdate_ahead.month))+'{:02d}'.format(int(curdate_ahead.day))
                hrmin_ahead = '{:02d}'.format(int(curdate_ahead.hour))+'{:02d}'.format(int(curdate_ahead.minute))

                #Gunzip the file 
                output = subprocess.call("gunzip "+GRIB_PATH_TEMP+"/*.gz", stdout=open(os.devnull, 'wb'), stderr=open(os.devnull, 'wb'), shell=True)
                
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
 
                print pcp_combine_str_beg
                print pcp_combine_str_end
                
                os.chdir(GRIB_PATH_TEMP)
                
                #Use MET pcp_combine to sum, except for 1 hr acc from NAM, which contains either 1, 2, 3 hr acc. precip
                if 'HIRESNAM' in load_data[model] and pre_acc == 1:
                    if ((fcst_hr - 1) % 3) == 0:   #Every 3rd hour contains 1 hr acc. precip
                        output = subprocess.call(MET_PATH+"/pcp_combine -sum "+pcp_combine_str+" "+str(int(acc_int[model]))+" "+ \
                            yrmonday_ahead+"_"+hours_ahead_str+"0000 "+'{:02d}'.format(int(pre_acc))+" "+GRIB_PATH_TEMP+"/"+ \
                            load_data_nc[model]+" -pcpdir "+GRIB_PATH_TEMP+"/",stdout=open(os.devnull, 'wb'), stderr=open(os.devnull, 'wb'),shell=True)
                    elif ((fcst_hr - 2) % 3) == 0: #2nd file contains 2 hr  acc. precip
                        output = subprocess.call(MET_PATH+"/pcp_combine -subtract "+GRIB_PATH_TEMP+"/"+data_name_grib[fcst_hr_count]+" 02 "+ \
                            GRIB_PATH_TEMP+"/"+data_name_grib[fcst_hr_count-1]+" 01 "+GRIB_PATH_TEMP+"/"+load_data_nc[model], stdout=open(os.devnull, 'wb'), \
                            stderr=open(os.devnull, 'wb'), shell=True)
                    elif ((fcst_hr - 3) % 3) == 0: #3rd file contains 3 hr  acc. precip
                        output = subprocess.call(MET_PATH+"/pcp_combine -subtract "+GRIB_PATH_TEMP+"/"+data_name_grib[fcst_hr_count]+" 03 "+ \
                            GRIB_PATH_TEMP+"/"+data_name_grib[fcst_hr_count-1]+" 02 "+GRIB_PATH_TEMP+"/"+load_data_nc[model], \
                            stdout=open(os.devnull, 'wb'), stderr=open(os.devnull, 'wb'),shell=True)
                elif 'HIRESNAM' in load_data[model] and pre_acc % 3 == 0: #NAM sum 3 hour increments
                    output = subprocess.call(MET_PATH+"/pcp_combine -sum "+pcp_combine_str+" 3 "+ \
                        yrmonday_ahead+"_"+hours_ahead_str+"0000 "+'{:02d}'.format(int(pre_acc))+" "+GRIB_PATH_TEMP+"/"+ \
                        load_data_nc[model]+" -pcpdir "+GRIB_PATH_TEMP+"/",stdout=open(os.devnull, 'wb'), stderr=open(os.devnull, 'wb'),shell=True)
                elif 'HIRESNAM' in load_data[model] and pre_acc % 3 == 1: #Error if desired interval is not 1 or divisible by 3
                    raise ValueError('NAM pre_acc variable can only be 1 or divisible by 3')
                elif 'NEWSe60min' in load_data[model]:
                    if fcst_hr_load == 1: #If using fcst hour 1, no need to subtract data
                        output = subprocess.call(MET_PATH+'/pcp_combine -sum '+pcp_combine_str_beg+' '+APCP_str_beg[1::]+' '+pcp_combine_str_end+' '+ \
                            APCP_str_end[1::]+' '+GRIB_PATH_TEMP+'/'+load_data_nc[model]+' -name "'+APCP_str_end+'"',shell=True)
                    elif fcst_hr_load > 1: #If not first hour, subtract current from previous hour
                        output = subprocess.call(MET_PATH+"/pcp_combine -subtract "+GRIB_PATH_TEMP+"/"+data_name_grib[fcst_hr_count]+" "+last_fcst_hr_str+" "+ \
                            GRIB_PATH_TEMP+"/"+data_name_grib[fcst_hr_count-1]+" "+'{:02d}'.format(int(last_fcst_hr_str)-1)+" "+GRIB_PATH_TEMP+"/"+ \
                            load_data_nc[model]+' -name "'+APCP_str_end+'"',shell=True)
                elif 'NEWSe5min' in load_data[model]:
                    output = subprocess.call(MET_PATH+'/pcp_combine -sum  '+pcp_combine_str_beg+' '+APCP_str_beg[1::]+' '+pcp_combine_str_end+' '+ \
                        APCP_str_end[1::]+' '+GRIB_PATH_TEMP+'/'+load_data_nc[model]+' -field \'name="'+APCP_str_beg+'"; level="Surface";\''+ \
                        ' -name "'+APCP_str_end+'"',shell=True)
                elif 'MRMS15min' in load_data[model]:
                    call_str = [data_name_grib[i]+' \'name="'+APCP_str_beg+'" ; level="(*,*)" ; \'' for i in range(int((fcst_hr_count)*(pre_acc/acc_int[model])),int((fcst_hr_count+1)*(pre_acc/acc_int[model])))]
                    output = subprocess.call(MET_PATH+'/pcp_combine -add  '+' '.join(call_str)+' '+ \
                        GRIB_PATH_TEMP+'/'+load_data_nc[model]+' -name "'+APCP_str_end+'"',shell=True)
                else:
                    output = subprocess.call(MET_PATH+'/pcp_combine -sum  '+pcp_combine_str_beg+' '+APCP_str_beg[1::]+' '+pcp_combine_str_end+' '+ \
                        APCP_str_end[1::]+' '+GRIB_PATH_TEMP+'/'+load_data_nc[model]+' -name "'+APCP_str_end+'"',shell=True)
                
                ##Use MET regrid_data_plane to regrid data a default grid
                #if 'NEWSe60min' in load_data[model]:
                #    data_success[fcst_hr_count,model] = subprocess.call(MET_PATH+"/regrid_data_plane "+GRIB_PATH_TEMP+"/"+ \
                #        load_data_nc[model]+" "+GRIB_PATH+"/temp/ensmean_sample_NODELETE "+GRIB_PATH_TEMP+"/"+load_data_nc[model]+"2 "+ \
                #        "-field 'name=\"APCP_"+last_fcst_hr_str+"\"; level=\"A"+last_fcst_hr_str+ \
                #        "\";'", shell=True)
                #else:
                data_success[fcst_hr_count,model] = subprocess.call(MET_PATH+"/regrid_data_plane "+GRIB_PATH_TEMP+"/"+ \
                    load_data_nc[model]+" "+GRIB_PATH+"/temp/ensmean_sample_NODELETE "+GRIB_PATH_TEMP+"/"+load_data_nc[model]+"2 "+ \
                    "-field 'name=\""+APCP_str_end+"\"; level=\""+APCP_str_end+ \
                    "\";' -name "+APCP_str_end, shell=True)
                
                #Remove original netcdf files
                output=subprocess.call("rm -rf "+GRIB_PATH_TEMP+"/"+load_data_nc[model], shell=True)

                #Rename netcdf file
                data_name_nc = np.append(data_name_nc,GRIB_PATH_TEMP+"/"+load_data_nc[model][0:-3]+"_f"+fcst_hr_str+fcst_min_str+".nc")
                output=subprocess.call("mv "+GRIB_PATH_TEMP+"/"+load_data_nc[model]+"2 "+data_name_nc[fcst_hr_count], \
                    shell=True)
                    
                #Construct an array of lagged OBS files corresponding to the lagged model
                if (load_qpe[0] != 'None') and (load_qpe[0] not in load_data[model]):
                    data_name_nc_lagQPE = np.append(data_name_nc_lagQPE,GRIB_PATH_TEMP+"/"+load_data[0]+"_f"+fcst_hr_str+fcst_min_str+".nc")
                elif (load_qpe[0] != 'None') and (load_qpe[0] in load_data[model]):
                    data_name_nc_lagQPE = np.append(data_name_nc_lagQPE,'null')
                
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
                    subprocess.call(MET_PATH+"/regrid_data_plane "+mask_file_in+" "+GRIB_PATH+"/temp/ensmean_sample_NODELETE "+ \
                        mask_file_ou+" "+ "-field 'name=\"CSNOW"+"\"; level=\"L0"+"\";'",stdout=open(os.devnull, 'wb'), \
                        stderr=open(os.devnull, 'wb'),shell=True)

                    #If considering WEASD, must subtract current hour from previous hour (if it exists)
                    if masking_str == 'WEASD' and fcst_hr_count > 0:
                        mask_file_ou_prev = GRIB_PATH_TEMP+'/'+data_name_grib[fcst_hr_count-1]+'.nc'
                        
                        output = subprocess.call(MET_PATH+"/pcp_combine -subtract "+mask_file_ou+" 'name=\"WEASD_L0\"; level=\"L0\";' "+" "+ \
                            mask_file_ou_prev+" 'name=\"WEASD_L0\"; level=\"L0\";' "+mask_file_ou+"2", stdout=open(os.devnull, 'wb'), \
                            stderr=open(os.devnull, 'wb'),shell=True)
                            
                        #Mask out all non-snow data
                        subprocess.call(MET_PATH+"/gen_vx_mask "+data_name_nc[fcst_hr_count]+" "+mask_file_ou+"2 "+data_name_nc[fcst_hr_count]+ \
                            "_2 -type data -input_field 'name=\"APCP_"+'{:02d}'.format(int(pre_acc))+"_A"+'{:01d}'.format(int(pre_acc))+ \
                            "\"; level=\"A"+'{:01d}'.format(int(pre_acc))+"\";' -mask_field 'name=\""+masking_str+"_01\"; level=\"A1\";' -thresh le0 -value 0 -name APCP_"+ \
                            '{:02d}'.format(int(pre_acc))+"_A"+'{:01d}'.format(int(pre_acc)),stdout=open(os.devnull, 'wb'), stderr=open(os.devnull, 'wb'),shell=True)
                    else:
                        output = subprocess.call("cp "+mask_file_ou+' '+mask_file_ou+'2',stdout=open(os.devnull, 'wb'), stderr=open(os.devnull, 'wb'),shell=True)
                        
                        #Mask out all non-snow data
                        subprocess.call(MET_PATH+"/gen_vx_mask "+data_name_nc[fcst_hr_count]+" "+mask_file_ou+"2 "+data_name_nc[fcst_hr_count]+ \
                            "_2 -type data -input_field 'name=\"APCP_"+'{:02d}'.format(int(pre_acc))+"_A"+'{:01d}'.format(int(pre_acc))+ \
                            "\"; level=\"A"+'{:01d}'.format(int(pre_acc))+"\";' -mask_field 'name=\""+masking_str+"_L0\"; level=\"L0\";' -thresh le0 -value 0 -name APCP_"+ \
                            '{:02d}'.format(int(pre_acc))+"_A"+'{:01d}'.format(int(pre_acc)),stdout=open(os.devnull, 'wb'), stderr=open(os.devnull, 'wb'),shell=True)
                     
                    #Replace old file with properly masked file
                    subprocess.call("mv "+data_name_nc[fcst_hr_count]+"_2 "+data_name_nc[fcst_hr_count], stdout=open(os.devnull, 'wb'), \
                        stderr=open(os.devnull, 'wb'), shell=True)
                                    
                    ##Remove actual mask
                    #subprocess.call('rm -rf '+mask_file_ou, stdout=open(os.devnull, 'wb'), stderr=open(os.devnull, 'wb'), shell=True)

                #END snow mask check
                
                #Check to make sure that missing data in observation is reflected in model
                
                if (load_qpe[0] != 'None') and (load_qpe[0] not in load_data[model]):
                    subprocess.call(MET_PATH+'/gen_vx_mask '+data_name_nc_lagQPE[fcst_hr_count]+' '+data_name_nc[fcst_hr_count]+' '+data_name_nc_lagQPE[fcst_hr_count]+'2 '+ \
                        ' -type data -input_field \'name="'+APCP_str_end+'" ; level="(*,*)" ;\' -mask_field \'name="'+APCP_str_end+ \
                        '" ; level="(*,*)" ;\' -thresh eq-9999 -value -9999 -name '+APCP_str_end,shell=True)

                    #Replace old file with properly masked file
                    subprocess.call('mv '+data_name_nc_lagQPE[fcst_hr_count]+'2 '+data_name_nc_lagQPE[fcst_hr_count], stdout=open(os.devnull, 'wb'), \
                        stderr=open(os.devnull, 'wb'), shell=True)
                    
                #Remove the netcdf files
                output=subprocess.call("rm -rf "+GRIB_PATH_TEMP+"/"+load_data_nc[model],stdout=open(os.devnull, 'wb'), \
                    stderr=open(os.devnull, 'wb'), shell=True)
                   
                print str(fcst_hr_count)     
                fcst_hr_count += 1
            #END through forecast hour

            #Remove original grib files
            for files in data_name_grib:
                output = subprocess.call('rm -rf '+GRIB_PATH_TEMP+'/'+files+'*', stdout=open(os.devnull, 'wb'), stderr=open(os.devnull, 'wb'), shell=True)
                
            #Determine which hours are successfully loaded for each model
            if (load_qpe[0] != 'None') and (load_qpe[0] not in load_data[model]):
                hour_success = data_success[:,0] + data_success[:,model] == 0
            elif (load_qpe[0] not in load_data[model]): #No OBS, compare model to itself 
                hour_success = data_success[:,model] == 0
                
            #Create variable name for default MTD file and renamed MTD file
            if (load_qpe[0] not in load_data[model]):
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
                load_data_nc[model][0:-3]+'_p'+str(pre_acc)+'_t'+str(thres)

            #Remove old MTD output files if they exist
            if os.path.isfile(GRIB_PATH_TEMP+'/'+MTDfile_new[model]): 
                os.remove(GRIB_PATH_TEMP+'/'+MTDfile_new[model])    
            
            #Run MTD: 1) if QPE exists compare model to obs, otherwise 2) run mtd in single mode
            output = []
            if (load_qpe[0] != 'None') and (load_qpe[0] not in load_data[model]):
                print MET_PATH+'/mtd -fcst '+' '.join(data_name_nc[hour_success])+ \
                    ' -obs '+' '.join(data_name_nc_lagQPE[hour_success])+' -config '+config_name+' -outdir '+GRIB_PATH_TEMP
                mtd_success = subprocess.call(MET_PATH+'/mtd -fcst '+' '.join(data_name_nc[hour_success])+ \
                    ' -obs '+' '.join(data_name_nc_lagQPE[hour_success])+' -config '+config_name+' -outdir '+GRIB_PATH_TEMP, shell=True)
            elif (load_qpe[0] not in load_data[model]): #No QPE, compare model to itself
                mtd_success = subprocess.call(MET_PATH+'/mtd -single '+' '.join(data_name_nc[hour_success])+' -config '+ \
                    config_name+' -outdir '+GRIB_PATH_TEMP, shell=True)
            #Matrix to gather all netcdf file strings
            data_name_nc_all = np.append(data_name_nc_all,data_name_nc)
            
            #Rename cluster file and 2d text file (QPE is handled later)
            if load_qpe[0] not in load_data[model]:
                output = subprocess.call('mv '+GRIB_PATH_TEMP+'/'+MTDfile_old[model]+'_obj.nc '+ GRIB_PATH_TEMP+'/'+MTDfile_new[model]+ \
                    '_obj.nc ',stdout=open(os.devnull, 'wb'), stderr=open(os.devnull, 'wb'), shell=True)
                output = subprocess.call('mv '+GRIB_PATH_TEMP+'/'+MTDfile_old[model]+'_2d.txt '+ GRIB_PATH_TEMP+'/'+MTDfile_new[model]+ \
                    '_2d.txt ',stdout=open(os.devnull, 'wb'), stderr=open(os.devnull, 'wb'), shell=True)
                output = subprocess.call('rm -rf '+GRIB_PATH_TEMP+'/'+MTDfile_old[model]+'_3d_ss.txt', \
                    stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'),shell=True)
                output = subprocess.call('rm -rf '+GRIB_PATH_TEMP+'/'+MTDfile_old[model]+'_3d_sc.txt', \
                    stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'),shell=True)
                output = subprocess.call('rm -rf '+GRIB_PATH_TEMP+'/'+MTDfile_old[model]+'_3d_ps.txt', \
                    stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'),shell=True)
                output = subprocess.call('rm -rf '+GRIB_PATH_TEMP+'/'+MTDfile_old[model]+'_3d_pc.txt', \
                    stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'),shell=True)

            #Log outcome of MTD
            target = open(log_file,'a')
            if np.nanmean(data_success[:,model],axis = 0) < 1: #Successful
                target.write(load_data_nc[model]+' MTD Data Processed For '+str(np.sum(data_success[:,model]==0)*pre_acc)+ \
                    ' Hours; Threshold - '+str(thres)+'\n')
                print load_data_nc[model]+' MTD Data Processed For '+str(np.sum(data_success[:,model]==0)*pre_acc)+' Hours; Threshold - '+str(thres)
            else:
                target.write(load_data_nc[model]+' MTD Data Not Found; Threshold - '+str(thres)+'\n')
                print load_data_nc[model]+' MTD Data Not Found; Threshold - '+str(thres)
            target.close()
            
        #END through model

        #Remove the netcdf files
        for files in data_name_nc_all:
            output=subprocess.call("rm -rf "+files,stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'), shell=True)
     
################################################################################
#########4 LOAD MTD DATA IN PROPER FORMAT TO BE SAVED###########################
################################################################################

        #Find model index location to load MTD data
        mod_loc = [i for i in range(0,len(MTDfile_new)) if load_model[0] in MTDfile_new[i]][0]
        
        #Function to read in MTD data
        for model in range(len(load_data)): #Through the 1 model and observation
            (lat_t, lon_t, fcst_p, obs_p, simp_bin_p, clus_bin_p, simp_prop_k, pair_prop_k, data_success_p) = \
                METLoadEnsemble_NEW.loadDataMTD(GRIB_PATH_TEMP, MTDfile_new[1], ismodel[model], latlon_dims)
             
            if model == 1:
                print simp_prop_k[4] 
                print pair_prop_k[4]
                
            simp_prop[model]       = simp_prop_k
            pair_prop[model]       = pair_prop_k
        
            #Determine length of hours, place into matrices properly time-matched
            if (load_qpe[0] != 'None') and (load_qpe[0] not in load_data[model]):
                hour_success = data_success[:,0] + data_success[:,model] == 0
            elif (load_qpe[0] not in load_data[model]): #No OBS, compare model to itself 
                hour_success = data_success[:,model] == 0
                
            hours_true = np.where(hour_success == 1)[0]
            
            if np.mean(np.isnan(simp_bin_p)) != 1:
                simp_bin[:,:,hours_true,model] = simp_bin_p
            if np.mean(np.isnan(clus_bin_p)) != 1:
                clus_bin[:,:,hours_true,model] = clus_bin_p
            
            #Create binomial grid where = 1 if model and obs exist
            if np.mean(np.isnan(obs_p)) == 1 or  np.mean(np.isnan(fcst_p)) == 1:
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

                METPlotEnsemble.MTDPlotRetro(GRIB_PATH_DES,FIG_PATH,[lonmin,latmin,lonmax,latmax],pre_acc,hrs_all,thres,curdate, \
                    data_success,load_data_nc,lat,lon,fcst_p,obs_p,clus_bin,pair_prop)
                    
            #Save the simple and paired model/obs track files specifying simp/pair, start/end time, hour acc. interval, and threshold
            if (np.sum(hour_success) > 0) and (load_qpe[0] != 'None') and (load_qpe[0] not in load_data[model]):
                np.savez(TRACK_PATH+GRIB_PATH_DES+mem[model]+'_'+'{:04d}'.format(datetime_curdate.year)+'{:02d}'.format(datetime_curdate.month)+ \
                    '{:02d}'.format(datetime_curdate.day)+'{:02d}'.format(datetime_curdate.hour)+'_simp_prop'+'_s'+str(int(start_hrs))+\
                    '_e'+str(int(start_hrs+total_fcst_hrs))+'_h'+str(pre_acc)+'_t'+str(thres),simp_prop_k = simp_prop_k,data_exist = data_exist)
                np.savez(TRACK_PATH+GRIB_PATH_DES+mem[model]+'_'+'{:04d}'.format(datetime_curdate.year)+'{:02d}'.format(datetime_curdate.month)+ \
                    '{:02d}'.format(datetime_curdate.day)+'{:02d}'.format(datetime_curdate.hour)+'_pair_prop'+'_s'+str(int(start_hrs))+\
                    '_e'+str(int(start_hrs+total_fcst_hrs))+'_h'+str(pre_acc)+'_t'+str(thres),pair_prop_k = pair_prop_k,data_exist = data_exist)
                
                #Remove old files
                output = subprocess.call('rm -rf '+TRACK_PATH+GRIB_PATH_DES+mem[model]+'_'+'{:04d}'.format(datetime_curdate.year)+'{:02d}'.format(datetime_curdate.month)+ \
                    '{:02d}'.format(datetime_curdate.day)+'{:02d}'.format(datetime_curdate.hour)+'_simp_prop'+'_s'+str(int(start_hrs))+\
                    '_e'+str(int(start_hrs+total_fcst_hrs))+'_h'+str(pre_acc)+'_t'+str(thres)+'.npz.gz',stdout=open(os.devnull, 'wb'),\
                    stderr=open(os.devnull, 'wb'), shell=True)
                output = subprocess.call('rm -rf '+TRACK_PATH+GRIB_PATH_DES+mem[model]+'_'+'{:04d}'.format(datetime_curdate.year)+'{:02d}'.format(datetime_curdate.month)+ \
                    '{:02d}'.format(datetime_curdate.day)+'{:02d}'.format(datetime_curdate.hour)+'_pair_prop'+'_s'+str(int(start_hrs))+\
                    '_e'+str(int(start_hrs+total_fcst_hrs))+'_h'+str(pre_acc)+'_t'+str(thres)+'.npz.gz',stdout=open(os.devnull, 'wb'),\
                    stderr=open(os.devnull, 'wb'), shell=True)
                    
                #Gunzip the files
                output = subprocess.call('gzip '+TRACK_PATH+GRIB_PATH_DES+mem[model]+'_'+'{:04d}'.format(datetime_curdate.year)+'{:02d}'.format(datetime_curdate.month)+ \
                    '{:02d}'.format(datetime_curdate.day)+'{:02d}'.format(datetime_curdate.hour)+'_simp_prop'+'_s'+str(int(start_hrs))+\
                    '_e'+str(int(start_hrs+total_fcst_hrs))+'_h'+str(pre_acc)+'_t'+str(thres)+'.npz',stdout=open(os.devnull, 'wb'),\
                    stderr=open(os.devnull, 'wb'), shell=True)
                output = subprocess.call('gzip '+TRACK_PATH+GRIB_PATH_DES+mem[model]+'_'+'{:04d}'.format(datetime_curdate.year)+'{:02d}'.format(datetime_curdate.month)+ \
                    '{:02d}'.format(datetime_curdate.day)+'{:02d}'.format(datetime_curdate.hour)+'_pair_prop'+'_s'+str(int(start_hrs))+\
                    '_e'+str(int(start_hrs+total_fcst_hrs))+'_h'+str(pre_acc)+'_t'+str(thres)+'.npz',stdout=open(os.devnull, 'wb'),\
                    stderr=open(os.devnull, 'wb'), shell=True)

        #Delete the source files to save hard drive space
        output=subprocess.call('rm -rf '+GRIB_PATH_TEMP,stdout=open(os.devnull, 'wb'), stderr=open(os.devnull, 'wb'), shell=True)
   
        #Fix an issue by deleting a folder created in METLoadEnsemble_NEW.setupData if no plotting is requested
        if plot_allhours == 'FALSE':
            subprocess.call("rm -rf "+FIG_PATH+"/"+'{:04d}'.format(datetime_curdate.year)+'{:02d}'.format(datetime_curdate.month)+ \
                '{:02d}'.format(datetime_curdate.day)+'{:02d}'.format(datetime_curdate.hour), stdout=open(os.devnull, 'wb'), \
                stderr=open(os.devnull, 'wb'), shell=True)


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