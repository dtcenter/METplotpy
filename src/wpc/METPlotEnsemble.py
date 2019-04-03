#!/usr/bin/python

################################################################################################
#SEIRES OF FUNCTIONS TO CREATE A VARIETY OF PLOTS FROM MET GENERATED DATA. MJE. 20161213
#UPDATE: ADD ADDITIONAL FUNCTIONS AND STREAMLINE. 20170510. MJE.
#UPDATE: ADDED DYNAMIC LEGEND GENERATION BASED ON USER SPECIFIED MODELS. 201700608. MJE.
################################################################################################

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
import warnings
from matplotlib.mlab import griddata
from scipy import ndimage

###################################################################################
#MODEPlotAllFcst creates a plot of forecast ensemble object probability (shading) and 
#object centroid location/magnitude/model type (marker). This code does not plot the ST4
#QPE, and is useful when making forecasts in realtime.
#
#Created by MJE. 20161213.
#####################INPUT FILES FOR MODEPlotAll####################################
#GRIB_PATH_DES   = unique identifier assigned to figure name
#FIG_PATH_s      = path where figures are to be saved
#latlon_dims     = latitude/longitude dimensions for plotting [WLON,SLAT,ELON,NLAT]
#pre_acc         = accumulation interval
#fcst_hr         = forecast hour
#start_hrs       = skip ahead specified hours before running MET
#raw_thres       = raw threshold for MODE
#curdate         = datetime attribute
#data_success    = record of which data were succesfully loaded
#load_data_nc    = gridded variable data
#lat             = gridded latitude data
#lon             = gridded longitude data
#clus_bin        = gridded cluster data
#simp_prop       = simple cluster centroid info of lat,lon,max
####################OUTPUT FILES FOR MODEPlotAllFcst####################################
#Note: "Simple" means unmerged while "cluster" refers to merged
#"Single" refers to unmatched objects while "pair" refers to matched objects.
#
###################################################################################
def MODEPlotAllFcst(GRIB_PATH_DES,FIG_PATH_s,latlon_dims,pre_acc,fcst_hr,start_hrs,raw_thres,curdate,data_success,load_data_nc,lat,lon,clus_bin,simp_prop):
          
    #data_success=data_success[fcst_hr_count,:,thres_count]
    #clus_bin=clus_bin[:,:,:,fcst_hr_count]
    #simp_prop=simp_prop[fcst_hr_count]
     
    #Remove ST4 data since ST4 objects are not plotted here
    remove_st4=[]
    for i in range(0,len(load_data_nc),1):
        if 'ST4' in load_data_nc[i]:
            remove_st4 = np.append(remove_st4,False)
        else:
            remove_st4 = np.append(remove_st4,True)
            
    remove_st4       = remove_st4 == 1
    load_data_nc     = [load_data_nc[i] for i in range(0,len(load_data_nc),1) if remove_st4[i]]
    data_success     = data_success[remove_st4]
    clus_bin         = clus_bin[:,:,remove_st4]
    simp_prop        = [simp_prop[i] for i in range(0,len(simp_prop),1) if remove_st4[i]]

    #Remove any missing models
    clus_bin = clus_bin[:,:,data_success==0]
    
    #Compute raw ensemble mean probability, set 100% to 99% to preserve colorbar
    ens_mean = np.nanmean(clus_bin, axis = 2)
    ens_mean[ens_mean > 0.95] = 0.95
    
    #Compute the proper forecast hour strings
    curdate_currn = curdate + datetime.timedelta(hours=0)
    curdate_start = curdate + datetime.timedelta(hours=fcst_hr-pre_acc)
    curdate_stop  = curdate + datetime.timedelta(hours=fcst_hr)
            
    #Plotting information; define a legend symbol based on the model
    legend_symbol=['o','d','*','^','<','>','s']
    legend_name=['NAM-NEST','HIRESW','HRRR','NSSL-OP','NSSL-ARW','NSSL-NMB','HRAM']
    
    #Establish a smoothing kernel to smooth ensemble probaiblities
    kern=np.hanning(50)
    kern /= kern.sum() 
    
    #Create first colorlist
    colorlist = ["#ffffff", "#02fd02", "#01c501", "#228b22", "#9acd32", "#fdf802", "#f8d826", "#e5bc00", "#fd9500", "#fd0000", "#bc0000"]
    my_cmap1 = mpl.colors.ListedColormap(colorlist)
    
    #Create second colorlist, replace first element with white
    my_cmap2 = mpl.cm.get_cmap('cool')
    my_cmap2.set_under('white')
    
    #Create range of values to plot
    values = np.linspace(0,1,11)
    fig = plt.figure(figsize=(8,8))
    ax = fig.add_axes([0.1,0.1,0.8,0.8])
    #Create polar stereographic Basemap instance.
    m = Basemap(llcrnrlon=latlon_dims[0], llcrnrlat=latlon_dims[1], urcrnrlon=latlon_dims[2],urcrnrlat=latlon_dims[3],resolution='i',projection='merc')
    #Draw coastlines, state and country boundaries, edge of map.
    m.drawcoastlines(linewidth=0.5)
    m.drawstates(linewidth=0.5)
    m.drawcountries(linewidth=0.5)
    #Draw parallels and meridians
    m.drawparallels(np.arange(0,90,5),labels=[1,0,0,0],fontsize=12,linewidth=0.5) #labels=[left,right,top,bottom]
    m.drawmeridians(np.arange(-180,0,10),labels=[0,0,0,1],fontsize=12,linewidth=0.5) #labels=[left,right,top,bottom]
    props = dict(boxstyle='round', facecolor='wheat', alpha=1)
    ax.text(0.5, 0.03, str(int(np.sum(data_success==0)))+' Members Found', 
        transform=ax.transAxes, fontsize=12,verticalalignment='bottom', horizontalalignment='center', bbox=props)
    ax.text(0.5, 0.97, "Valid Time: "+curdate_start.strftime('%Y%m%d%H')+" - "+curdate_stop.strftime('%Y%m%d%H'),
        transform=ax.transAxes, fontsize=12,verticalalignment='top', horizontalalignment='center', bbox=props)
    norm = mpl.colors.BoundaryNorm(values, len(colorlist))
    
    cs = m.contourf(lon, lat, ndimage.filters.gaussian_filter(ens_mean, 2), latlon=True, levels=values, extend='min', cmap=my_cmap2, antialiased=False, markerstyle='o', vmin=np.spacing(0.0),vmax=1)
    cb = m.colorbar(cs,"right", ticks=values, size="5%", pad="2%", extend='min')
    
    #Scatter plot includes intensity (color) and member (symbol)
    for model in range(len(load_data_nc)):
        if 'NAM' in load_data_nc[model]:       #NAMNEST and NAMNESTp
            marker=legend_symbol[0]
        elif 'HIRESW' in load_data_nc[model]:  #HIRESARW/HIRESNMB
            marker=legend_symbol[1]
        elif 'HRRR' in load_data_nc[model]:    #HRRRv2 and HRRRv3
            marker=legend_symbol[2]
        elif 'NSSL-OP' in load_data_nc[model]: #NSSL OP
            marker=legend_symbol[3]
        elif 'NSSL-ARW' in load_data_nc[model]:#NSSL ARW
            marker=legend_symbol[4]
        elif 'NSSL-NMB' in load_data_nc[model]:#NSSL NMB
            marker=legend_symbol[5]
        elif 'HRAM' in load_data_nc[model]:    #HRAM3e and HRAM3g
            marker=legend_symbol[6]
        else:
            marker=None
        
        #Separate centroid data, only plot model
        if np.mean(np.isnan(simp_prop[model])) != 1:
            if marker and len(simp_prop[model]) > 0:
                lon_pt=simp_prop[model][2,simp_prop[model][0,:]>0]
                lat_pt=simp_prop[model][1,simp_prop[model][0,:]>0]
                max_pt=simp_prop[model][3,simp_prop[model][0,:]>0]/25.4

                cs2 = m.scatter(np.concatenate((lon_pt,lon_pt,lon_pt)), np.concatenate((lat_pt,lat_pt,lat_pt)), c=np.concatenate((max_pt,max_pt,max_pt)), marker=marker, \
                    vmin=0, vmax=10, s=30, linewidth=0.5, cmap=my_cmap1, latlon=True)
    #END through model to create scatterplot
    
    #Pass line instances to a legend to create centroid maximum legend by color
    classes = ['>='+str(x)+"\"" for x in np.round(np.linspace(0,10,len(colorlist)),2)]
    line_label=[]
    line_str=[];
    for x in range(len(colorlist)):
        line_label = np.hstack((line_label, mpl.lines.Line2D(range(1), range(1), color=colorlist[x], linestyle='None', marker='o', markersize=7)))
        line_str   = np.hstack((line_str, classes[x]))
    first_legend=plt.legend(line_label, line_str, fontsize=7, numpoints=1, loc=3, framealpha=1)
    ax2 = plt.gca().add_artist(first_legend)
    
    #Pass line instances to a legend denoting member-type by markersize
    classes = ['>='+str(x)+"\"" for x in np.round(np.linspace(0,10,len(colorlist)),2)]
    line_label=[]
    line_str=[];
    for x in range(len(legend_symbol)):
        line_label = np.hstack((line_label, mpl.lines.Line2D(range(1), range(1), color='k', linestyle='None', marker=legend_symbol[x], markersize=7)))
        line_str   = np.hstack((line_str, legend_name[x]))
    plt.legend(line_label, line_str, fontsize=7, numpoints=1, loc=4, framealpha=1)
    
    ax.set_title("Ensemble Object Probabilities - "+"Precip. >= "+str(raw_thres)+"\" \n "+'{:02d}'.format(int(pre_acc))+ \
        " Hour Acc. Precip. - Initialized "+curdate.strftime('%Y%m%d%H'),fontsize=13)
    #Show and save the plot
    #plt.hold(True)
    plt.show()
    plt.savefig(FIG_PATH_s+'/'+GRIB_PATH_DES+'_TOTENS_objprob_'+curdate_currn.strftime('%Y%m%d%H')+'_f'+'{:02d}'.format(fcst_hr)+'_p'+'{:02d}'.format(int(pre_acc))+ \
        '_t'+str(raw_thres)+'.png', bbox_inches='tight',dpi=150)
    plt.close()
      
###################################################################################
#MODEPlotTLEFcst creates a plot of model only time-lagged objects, including centroid 
#location and intensity. The code will search for and group time lagged ensembles (TLE).
#Note this code can handle a maximum of two unique models for a maximum of three lags, 
#as specified in the variable name section in this function. If more than two unique 
#models or three lags are input, then the user is warned, the first two time-lagged 
#models are used, and the most recent lags are used. The user can change this by modifying
#the variables and the colorlists in this function. This code does not plot ST4 QPE.
#
#Created by MJE. 20161215-20161222.
#####################INPUT FILES FOR MODEPlotTLEFcst####################################
#GRIB_PATH_DES   = unique identifier assigned to figure name
#FIG_PATH_s      = path where figures are to be saved
#latlon_dims     = latitude/longitude dimensions for plotting [WLON,SLAT,ELON,NLAT]
#pre_acc         = accumulation interval
#fcst_hr         = forecast hour
#start_hrs       = skip ahead specified hours before running MET
#raw_thres       = raw threshold for MODE
#curdate         = datetime attribute
#data_success    = record of which data were succesfully loaded
#load_data_nc    = gridded variable data
#lat             = gridded latitude data
#lon             = gridded longitude data
#clus_bin        = gridded cluster data
#simp_prop       = simple cluster centroid info of lat,lon,max
####################OUTPUT FILES FOR MODEPlotTLEobj####################################
#Note: "Simple" means unmerged while "cluster" refers to merged
#"Single" refers to unmatched objects while "pair" refers to matched objects.
#
###################################################################################
def MODEPlotTLEFcst(GRIB_PATH_DES,FIG_PATH_s,latlon_dims,pre_acc,fcst_hr,start_hrs,raw_thres,curdate,data_success,load_data_nc,lat,lon,clus_bin,simp_prop):

    #fcst_hr_count=0
    #data_success=data_success[fcst_hr_count,:]
    #clus_bin=clus_bin[:,:,:,fcst_hr_count]
    #simp_prop=simp_prop[fcst_hr_count]
    
    ###################Function variables###################################################
    unique_models = 2       #Maximum umber of unique models to plot
    unique_lags   = 3       #Maximum size of the time lagged ensemble for each unique model
    ###################Function variables###################################################

    #Remove ST4 data since ST4 objects are not plotted here
    remove_st4=[]
    for i in range(0,len(load_data_nc),1):
        if 'ST4' in load_data_nc[i]:
            remove_st4 = np.append(remove_st4,False)
        else:
            remove_st4 = np.append(remove_st4,True)
            
    remove_st4       = remove_st4 == 1
    load_data_nc     = [load_data_nc[i] for i in range(0,len(load_data_nc),1) if remove_st4[i]]
    data_success     = data_success[remove_st4]
    clus_bin         = clus_bin[:,:,remove_st4]
    simp_prop        = [simp_prop[i] for i in range(0,len(simp_prop),1) if remove_st4[i]]
    #simp_prop = [simp_prop[i] for i in range(0,len(simp_prop),1) if remove_st4[i]]
    
    #Find unique models with different lags
    load_data_short = [load_data_nc[i][:-9] for i in range(0,len(load_data_nc))]
    load_data = [load_data_nc[i][:-3] for i in range(0,len(load_data_nc))]
    lag = np.array([long(load_data[i][load_data[i].index("lag")+3::]) for i in range(0,len(load_data))])
    [u, indices] = np.unique(load_data_short, return_inverse=True)
    
    #Initialize variables
    data_success_k     = []
    load_data_nc_k     = []
    finalcolor_k       = []
    clus_bin_k         = np.empty((clus_bin.shape[0],clus_bin.shape[1],0))
    simp_prop_k        = [[] for i in range(0,6,1)]
    ind_count          = 0
    
    #Loop through the unique models, find 2 or less sets of time-lagged models and archive
    count_elem = 0 
    for ind in range(0,len(u),1):
        if (sum(indices==ind) > 1 and ind_count < unique_models): #check for TLE, but not more than 2 TLEs
      
            #Consider the current TLE and subset data
            current_ind        = indices == ind
            data_success_p     = data_success[current_ind]
            load_data_nc_p     = [load_data_nc[i] for i in range(0,int(len(current_ind))) if current_ind[i] == True]
            clus_bin_p         = clus_bin[:,:,current_ind]
            simp_prop_p        = [simp_prop[i] for i in range(0,int(len(current_ind))) if current_ind[i] == True]
            lag_p              = lag[current_ind]
            
            #Sort the current TLE from newest to oldest           
            old2new = np.argsort(lag_p)
            
            if len(old2new) > unique_lags:   #Restrict each TLE to 3 members
                old2new = old2new[0:3]
            
            #Cat all TLEs by model
            data_success_k     = np.concatenate((data_success_k,data_success_p[old2new[::-1]]))
            load_data_nc_k     = np.concatenate((load_data_nc_k,[load_data_nc_p[old2new[i]] for i in range(int(len(old2new))-1,-1,-1)]))
            clus_bin_k         = np.concatenate((clus_bin_k, np.squeeze(clus_bin_p[:,:,old2new[::-1]])),axis=2)      
            
            for model in range(int(len(old2new))-1,-1,-1):
                if np.mean(np.isnan(simp_prop_p[old2new[model]])) != 1:
                    simp_prop_k[count_elem] = simp_prop_p[old2new[model]][:,simp_prop_p[old2new[model]][0,:]>0]
                else:
                    simp_prop_k[count_elem] = np.nan
                    
                count_elem += 1

            #Set colorlist depending on whats available
            if ind_count == 0:
                finalcolor = ["#9999ff", "#1a1aff", "#000080"]
            elif ind_count == 1:
                finalcolor = ["#bf80ff", "#9933ff", "#5900b3"]
                
            finalcolor_k = np.append(finalcolor_k,finalcolor[-sum(indices==ind):])
            ind_count += 1
    
    #Create range of values to plot and colorbar
    values = np.linspace(0,1,2)
    
    #Compute the proper forecast hour strings
    curdate_currn = curdate + datetime.timedelta(hours=0)
    curdate_start = curdate + datetime.timedelta(hours=fcst_hr-pre_acc)
    curdate_stop  = curdate + datetime.timedelta(hours=fcst_hr)
    
    fig = plt.figure(figsize=(8,8))
    ax = fig.add_axes([0.1,0.1,0.8,0.8])
    # create polar stereographic Basemap instance.
    m = Basemap(llcrnrlon=latlon_dims[0], llcrnrlat=latlon_dims[1], urcrnrlon=latlon_dims[2],urcrnrlat=latlon_dims[3],resolution='i',projection='merc')
    # draw coastlines, state and country boundaries, edge of map.
    m.drawcoastlines(linewidth=0.5)
    m.drawstates(linewidth=0.5)
    m.drawcountries(linewidth=0.5)
    # draw parallels and meridians
    m.drawparallels(np.arange(0,90,5),labels=[1,0,0,0],fontsize=12,linewidth=0.5) #labels=[left,right,top,bottom]
    m.drawmeridians(np.arange(-180,0,10),labels=[0,0,0,1],fontsize=12,linewidth=0.5) #labels=[left,right,top,bottom]
    props = dict(boxstyle='round', facecolor='wheat', alpha=1)
    ax.text(0.5, 0.03, str(int(np.sum(data_success_k==0)))+' Members Found', 
        transform=ax.transAxes, fontsize=12,verticalalignment='bottom', horizontalalignment='center', bbox=props)
    ax.text(0.5, 0.97, "Valid Time: "+curdate_start.strftime('%Y%m%d%H')+" - "+curdate_stop.strftime('%Y%m%d%H'),
        transform=ax.transAxes, fontsize=12,verticalalignment='top', horizontalalignment='center', bbox=props)
    norm = mpl.colors.BoundaryNorm(values, len(finalcolor_k))
    
    #Plot the raw TLE objects
    line_label=[]
    line_str=[]
    for model in range(len(load_data_nc_k)):
    
        #Create colorlist for each TLE
        colorlist = [finalcolor_k[model]]
        my_cmap3 = mpl.colors.ListedColormap(colorlist)
        
        tempdata=clus_bin_k[:,:,model]
        #cs = m.contourf(lon, lat, tempdata, latlon=True, levels=values, extend='min', cmap=my_cmap3, antialiased=False, markerstyle='o', vmin=np.spacing(0.0), vmax=1, alpha = 0.5)
        cs = m.contour(lon, lat, tempdata>0, latlon=True, levels=values, cmap=my_cmap3, linewidths=1, zorder=1)
        #plt.hold(True)
        
        #Create legend attributes
        line_label = np.hstack((line_label, mpl.lines.Line2D(range(1), range(1), color=finalcolor_k[model], linestyle='None', marker='o', markersize=5)))
        line_str   = np.hstack((line_str, load_data_nc_k[model]))
    #END loop through TLE runs only 
    
    #Create the legend for the object colors
    first_legend = plt.legend(line_label, line_str, fontsize=7, numpoints=1, loc=4, framealpha=1)        
    ax2 = plt.gca().add_artist(first_legend)
    
    #Redefine colorlist to show QPF value
    colorlist = ["#98fb98", "#02fd02", "#01c501", "#228b22", "#9acd32", "#fdf802", "#f8d826", "#e5bc00", "#fd9500", "#fd0000", "#bc0000"]
    my_cmap1 = mpl.colors.ListedColormap(colorlist)
    
    #Scatter plot includes intensity (color) and member (symbol)
    for model in range(len(load_data_nc_k)):
        if np.mean(np.isnan(simp_prop_k[model])) != 1:
            if np.sum(simp_prop_k[model][2,:]) != 0:
                cs2 = m.scatter(np.concatenate((simp_prop_k[model][2,:],simp_prop_k[model][2,:],simp_prop_k[model][2,:])), \
                    np.concatenate((simp_prop_k[model][1,:],simp_prop_k[model][1,:],simp_prop_k[model][1,:])), \
                    c=np.concatenate((simp_prop_k[model][3,:]/25.4,simp_prop_k[model][3,:]/25.4,simp_prop_k[model][3,:]/25.4)), \
                    marker='x', vmin=0, vmax=10, s=30, linewidth=0.5, cmap=my_cmap1, latlon=True, zorder=2)
    #END through model to create scatterplot
        
    #Pass line instances to a legend to create centroid maximum legend by color
    classes = ['>='+str(x)+"\"" for x in np.round(np.linspace(0,10,len(colorlist)),2)]
    line_label=[]
    line_str=[];
    for x in range(len(colorlist)):
        line_label = np.hstack((line_label, mpl.lines.Line2D(range(1), range(1), color=colorlist[x], linestyle='None', marker='x', markersize=5)))
        line_str   = np.hstack((line_str, classes[x]))
    second_legend = plt.legend(line_label, line_str, fontsize=7, numpoints=1, loc=3, framealpha=1)
    
    ax.set_title("Objects/Max. Locations - "+"Precip. >= "+str(raw_thres)+"\" \n "+'{:02d}'.format(int(pre_acc))+ \
        " Hour Acc. Precip. - Initialized "+curdate.strftime('%Y%m%d%H'),fontsize=13)
    #plt.hold(True)
    plt.show()
    plt.savefig(FIG_PATH_s+'/'+GRIB_PATH_DES+'_TLE_obj_'+curdate_currn.strftime('%Y%m%d%H')+'_f'+'{:02d}'.format(fcst_hr)+'_p'+'{:02d}'.format(int(pre_acc))+ \
    '_t'+str(raw_thres)+'.png', bbox_inches='tight',dpi=150)
    plt.close()
    
########################################################################################
#MODEPlotFcstObjObsObj creates a plot, for each model, of the forecast simple object
#(outline) and observed simple object (shaded), along with the interest value for each 
#matched forecast/observation object and the domain averaged interest value.
#
#Created by MJE. 20170103.
#####################INPUT FILES FOR MODEPlotTLEFcst####################################
#GRIB_PATH_DES   = unique identifier assigned to figure name
#FIG_PATH_s      = path where figures are to be saved
#latlon_dims     = latitude/longitude dimensions for plotting [WLON,SLAT,ELON,NLAT]
#pre_acc         = accumulation interval
#fcst_hr         = forecast hour
#start_hrs       = skip ahead specified hours before running MET
#raw_thres       = raw threshold for MODE
#curdate         = datetime attribute
#data_success    = record of which data were succesfully loaded
#load_data_nc    = gridded variable data
#lat             = gridded latitude data
#lon             = gridded longitude data
#simp_bin        = gridded simple object data
#simp_prop       = simple cluster centroid info of lat,lon,max
#clus_prop       = cluster cluster info of comp_obs_id,comp_mod_id,comp_cent_dist,
#                    comp_bound_dist,comp_convex_hull_dist,comp_angle_diff,
#                    comp_area_ratio,comp_inter_area,comp_union_area,comp_symm_diff,
#                    comp_inter_over_area,comp_complex_ratio comp_pctle_inten_ratio,
#                    comp_interest. Format clus_prop[model][attributes]
####################OUTPUT FILES FOR MODEPlotFcstObjObsObj####################################
#Note: "Simple" means unmerged while "cluster" refers to merged
#"Single" refers to unmatched objects while "pair" refers to matched objects.
#
###################################################################################
def MODEPlotFcstObjObsObj(GRIB_PATH_DES,FIG_PATH_s,latlon_dims,pre_acc,fcst_hr,start_hrs,raw_thres,curdate,data_success,load_data_nc,lat,lon,simp_bin,simp_prop,clus_prop):

    #data_success=data_success[fcst_hr_count,:,thres_count]
    #simp_bin=simp_bin[:,:,:,fcst_hr_count,thres_count]
    #simp_prop=simp_prop[thres_count][fcst_hr_count]
    #clus_prop=clus_prop[thres_count][fcst_hr_count]

    #Find ST4 data and create a logical matrix
    st4_loc_t=[]
    for i in range(0,len(load_data_nc),1):
        if 'ST4' in load_data_nc[i]:
            st4_loc_t = np.append(st4_loc_t,True)
        else:
            st4_loc_t = np.append(st4_loc_t,False)  
    st4_loc_t = st4_loc_t == 1
    #Find model locations in data string matrix
    mod_loc = [i for i in range(0,len(st4_loc_t)) if st4_loc_t[i] == False]
    #Find st4 locations in data string matrix
    st4_loc = [i for i in range(0,len(st4_loc_t)) if st4_loc_t[i] == True]
    
    #Check to see if 'ST4' exists, return if it does not
    if not st4_loc:
        return
    
    #Create range of values to plot and colorbar
    values = np.linspace(0,1,2)
    
    #Compute the proper forecast hour strings
    curdate_currn = curdate + datetime.timedelta(hours=0)
    curdate_start = curdate + datetime.timedelta(hours=fcst_hr-pre_acc)
    curdate_stop  = curdate + datetime.timedelta(hours=fcst_hr)
    
    #Set colorlist red for model and green for observation
    cmap_model = mpl.colors.ListedColormap(["#ff0000"])
    cmap_obs   = mpl.colors.ListedColormap(['#ffffff',"#00ff00"])
        
    #Loop through each model and create a forecast VS observation object figure
    for model in mod_loc:
  
        fig = plt.figure(figsize=(8,8))
        ax = fig.add_axes([0.1,0.1,0.8,0.8])
        # create polar stereographic Basemap instance.
        m = Basemap(llcrnrlon=latlon_dims[0], llcrnrlat=latlon_dims[1], urcrnrlon=latlon_dims[2],urcrnrlat=latlon_dims[3],resolution='i',projection='merc')
        # draw coastlines, state and country boundaries, edge of map.
        m.drawcoastlines(linewidth=0.5)
        m.drawstates(linewidth=0.5)
        m.drawcountries(linewidth=0.5)
        # draw parallels and meridians
        m.drawparallels(np.arange(0,90,5),labels=[1,0,0,0],fontsize=12,linewidth=0.5) #labels=[left,right,top,bottom]
        m.drawmeridians(np.arange(-180,0,10),labels=[0,0,0,1],fontsize=12,linewidth=0.5) #labels=[left,right,top,bottom]
        props = dict(boxstyle='round', facecolor='wheat', alpha=1)

        #Plot model outline
        cs1 = m.contour(lon, lat, simp_bin[:,:,model]>0, latlon=True, levels=values, cmap=cmap_model, linewidths=2)
        cs2 = m.contourf(lon, lat, simp_bin[:,:,st4_loc[0]]>0, latlon=True, levels=values, extend='min', cmap=cmap_obs, antialiased=False, markerstyle='o', vmin=np.spacing(0.0), vmax=1, alpha = 0.5)
        #plt.hold(True)

        #Plot model/obs simple centroid ID number
        for pts in range(0,len(simp_prop[model][0])):
            if simp_prop[model][0,pts] >= 0: #If model
                x, y = m(simp_prop[model][2,pts], simp_prop[model][1,pts]+0.5)
                x2, y2 = m(simp_prop[model][2,pts], simp_prop[model][1,pts])
                plt.text(x, y, int(simp_prop[model][0,pts]), fontsize=12, ha='center', va='center', color='#8b0000')
                plt.text(x2, y2, '.', fontsize=18, ha='center', va='center', color='#8b0000')
            elif simp_prop[model][0,pts] < 0: #If obs
                x, y = m(simp_prop[model][2,pts], simp_prop[model][1,pts]+0.5)
                x2, y2 = m(simp_prop[model][2,pts], simp_prop[model][1,pts])
                plt.text(x, y, int(np.abs(simp_prop[model][0,pts])), fontsize=12, ha='center', va='center', color='#003518')
                plt.text(x2, y2, '.', fontsize=18, ha='center', va='center', color='#003518')

        #Plot model/obs cluster (grouped) centroid statistics
        for pts in range(0,len(clus_prop[model][0])):

            #Try relating simple and cluster object to plot interest (compos) and location (simple)
            f_index = np.flatnonzero(clus_prop[model][0][pts]==simp_prop[model][0])
            x, y = m(simp_prop[model][2][f_index],simp_prop[model][1][f_index]+(latlon_dims[3]-latlon_dims[1])*0.07)
            plot_string = 'I = '+ \
                    str(np.round(clus_prop[model][-1][pts],2))#+' \n'   
                    
            try:
                t = ax.text(x,y,plot_string,va='top',ha='center',fontsize=4,bbox={'facecolor':'white', 'alpha':0.75})
                #t.set_bbox(dict(color='white', edgecolor='none', alpha=0.5))
            except UnboundLocalError:
                t = ax.text(x,y,'Error',va='top',ha='center',fontsize=4,facecolor='k')
                #t.set_bbox(dict(color='white', edgecolor='none', alpha=0.5))
            
            if pts == len(clus_prop[model][0])-1: #Create total interest 
                plot_string = 'Domain Average Interest - '+ \
                    str(np.round(np.nanmean(clus_prop[model][-1,:]),2))#+' \n'   
                            
        x,y = m(np.mean([latlon_dims[0],latlon_dims[2]]),latlon_dims[3]-((latlon_dims[3]-latlon_dims[1])*0.03))    
        try:
            ax.text(x,y,plot_string,va='center',ha='center',fontsize=12,color='k',bbox=props)
        except UnboundLocalError:
            ax.text(x,y,'Error in Computing Domain Average Interest',va='center',ha='center',fontsize=12,color='k',backgroundcolor='w')
            
        plt.show()
        
        #Set up the legend and display
        line_label=[]
        line_str=[]
        for elements in range(0,2): #through one model and obs
            if elements == 0:     
                line_label = np.hstack((line_label, mpl.lines.Line2D(range(1), range(1), color=cmap_obs.colors[-1], linestyle='None', marker='o', markersize=5)))
                line_str   = np.hstack((line_str, load_data_nc[st4_loc[0]][0:-9]))
            else:
                line_label = np.hstack((line_label, mpl.lines.Line2D(range(1), range(1), color=cmap_model.colors[-1], linestyle='None', marker='o', markersize=5)))
                line_str   = np.hstack((line_str, load_data_nc[model][0:-9]))
    
        #Create the legend for the object colors
        legend1 = plt.legend(line_label, line_str, fontsize=8, numpoints=1, loc=4, bbox_to_anchor=(1, 0.06), framealpha=1)        
        ax1 = plt.gca().add_artist(legend1)
        
        ax.text(0.5, 0.06, "Valid Time: "+curdate_start.strftime('%Y%m%d%H')+" - "+curdate_stop.strftime('%Y%m%d%H'),
            transform=ax.transAxes, fontsize=12,verticalalignment='top', horizontalalignment='center', bbox=props)
        ax.set_title(load_data_nc[model][0:-9]+" Vs Stage IV Objects >= "+str(raw_thres)+"\" \n "+'{:02d}'.format(int(pre_acc))+ \
            " Hour Acc. Precip. - Initialized "+curdate.strftime('%Y%m%d%H'),fontsize=12)
        #plt.hold(True)
        plt.show()
        plt.savefig(FIG_PATH_s+'/'+GRIB_PATH_DES+'_'+load_data_nc[model][0:-9]+'vsOBS_obj'+curdate_currn.strftime('%Y%m%d%H')+'_f'+'{:02d}'.format(fcst_hr)+'_p'+'{:02d}'.format(int(pre_acc))+ \
            '_t'+str(raw_thres)+'.png', bbox_inches='tight',dpi=150)
        plt.close() 
               
###################################################################################
#MTDPlotAllFcst creates three plots: 1) forecast ensemble object probability (shading) and 
#object centroid location/magnitude/model type (marker). If observation exists then the
#observed object is plotted (black outline) in addition to centroid location/magnitude.
#2) forecast ensemble object probability (shading) and object centroid location/forecast 
#hour/model type (marker). If observation exists, observed object is plotted (black outline)
#in addition to centroid location/magnitude. 3) An hourly animation of figure 1) is created
#to better convey temporal details of the objects.
#
#Created by MJE. 20170327-20170420
#####################INPUT FILES FOR MODEPlotAll####################################
#GRIB_PATH_DES   = unique identifier assigned to figure name
#FIG_PATH_s      = path where figures are to be saved
#latlon_dims     = latitude/longitude dimensions for plotting [WLON,SLAT,ELON,NLAT]
#pre_acc         = accumulation interval
#hrs             = array of forecast hours
#raw_thres       = raw threshold for MODE
#curdate         = datetime attribute
#data_success    = record of which data were succesfully loaded
#load_data_nc    = gridded variable data
#lat             = gridded latitude data
#lon             = gridded longitude data
#simp_bin        = gridded simple data
#simp_prop       = simple cluster centroid info of lat,lon,max. Takes the form of [model][attributes]
####################OUTPUT FILES FOR MODEPlotAllFcst####################################
#Note: "Simple" means unmerged while "cluster" refers to merged
#"Single" refers to unmatched objects while "pair" refers to matched objects.
#
###################################################################################
def MTDPlotAllFcst(GRIB_PATH_DES,FIG_PATH_s,latlon_dims,pre_acc,hrs,raw_thres,curdate,data_success,load_data_nc,lat,lon,simp_bin,simp_prop):
          
    #data_success  = data_success_new[:,:,thres_count]
    #simp_bin      = simp_bin[:,:,:,:,thres_count]
    #simp_prop     = simp_prop[thres_count]
    #latlon_dims   = latlon_sub[subsets]
    #GRIB_PATH_DES = GRIB_PATH_DES+domain_sub[subsets]
    #raw_thres     = raw_thres[0]

    #Find and isolate ST4 data
    isolate_st4=[]
    for i in range(0,len(load_data_nc),1):
        if 'ST4' in load_data_nc[i]:
            isolate_st4 = np.append(isolate_st4,False)
        else:
            isolate_st4 = np.append(isolate_st4,True)
    isolate_st4       = isolate_st4 == 1

    #Currently this function only requires a logical matrix
    simp_bin = simp_bin > 0
    
    #Add NaNs to missing data in binary matrix. Convert to float
    simp_bin=simp_bin.astype(float)
    NaN_loc = (data_success == 1).astype(float)
    NaN_loc[NaN_loc == 1] = np.NaN
    
    for j in range(simp_bin.shape[0]):
        for i in range(simp_bin.shape[1]):
            simp_bin[j,i,:,:] = simp_bin[j,i,:,:] + NaN_loc
            
    #Compute raw ensemble mean probability, set 100% to 99% to preserve colorbar
    ens_mean = np.nanmax(np.nanmean(simp_bin[:,:,:,isolate_st4], axis = 3) , axis = 2)
    ens_mean[ens_mean > 0.95] = 0.95
    
    #Compute the proper forecast hour strings
    curdate_currn = curdate + datetime.timedelta(hours=0)
    curdate_start = curdate + datetime.timedelta(hours=hrs[0])
    curdate_stop  = curdate + datetime.timedelta(hours=hrs[-1])
    
    #Establish a smoothing kernel to smooth ensemble probaiblities
    kern=np.hanning(50)
    kern /= kern.sum() 
    
    #Create first colorlist
    colorlist = ["#ffffff", "#02fd02", "#01c501", "#228b22", "#9acd32", "#fdf802", "#f8d826", "#e5bc00", "#fd9500", "#fd0000", "#bc0000"]
    my_cmap1 = mpl.colors.ListedColormap(colorlist)

    #Given a default model name list, build a list based on user specified models
    leg_nam_bymod_default = ['ST4'  ,'HIRESNAM','HIRESW','HRRR','NSSL-OP','NSSL-ARW','NSSL-NMB','HRAM']
    leg_sym_bymod_default = ['s','d','*','^','<','>','v','o']
    
    if len(load_data_nc) <= 8: #If list is small enough, specific markers for individual models
        leg_nam_bymod  = load_data_nc
        leg_sym_bymod  = leg_sym_bymod_default[0:len(load_data_nc)]
    else:                      #Create markers by model type
        leg_nam_bymod = []
        leg_sym_bymod = []
        for bymod in range(0,len(leg_nam_bymod_default)):
            if np.sum([leg_nam_bymod_default[bymod] in i for i in load_data_nc]) > 0:
                leg_nam_bymod = np.append(leg_nam_bymod,leg_nam_bymod_default[bymod])
                leg_sym_bymod = np.append(leg_sym_bymod,leg_sym_bymod_default[bymod])
    
    leg_nam_byint  = ['>='+str(x)+"\"" for x in np.round(np.linspace(0,np.array(raw_thres)*10,len(colorlist)),2)]
    leg_nam_bytime = ['Hours '+str(i)+' - '+str(i+int(round(len(hrs)/len(colorlist)))) \
        for i in range(0,len(hrs),int(round(len(hrs)/len(colorlist))+1))]
    
    #Shorten initial colorlist for bytime plots
    my_cmap1_short = mpl.colors.ListedColormap(colorlist[0:len(leg_nam_bytime)])
       
    #Create second colorlist, replace first element with white
    my_cmap2 = mpl.cm.get_cmap('cool')
    my_cmap2.set_under('white')
     
    ##########################################################################################
    ###PLOT OF OBJ PROB. (SHADED), MODEL TYPE (MARKERTYPE), AND OBJ. INTENSITY (MARKER COLOR)#
    ##########################################################################################
    
    #Create range of values to plot
    values = np.linspace(0,1,11)
    fig = plt.figure(figsize=(8,8))
    ax = fig.add_axes([0.1,0.1,0.8,0.8])
    #Create polar stereographic Basemap instance.
    m = Basemap(llcrnrlon=latlon_dims[0], llcrnrlat=latlon_dims[1], urcrnrlon=latlon_dims[2],urcrnrlat=latlon_dims[3],resolution='i',projection='merc')
    #Draw coastlines, state and country boundaries, edge of map.
    m.drawcoastlines(linewidth=0.5)
    m.drawstates(linewidth=0.5)
    m.drawcountries(linewidth=0.5)
    #Draw parallels and meridians
    m.drawparallels(np.arange(0,90,5),labels=[1,0,0,0],fontsize=12,linewidth=0.5) #labels=[left,right,top,bottom]
    m.drawmeridians(np.arange(-180,0,10),labels=[0,0,0,1],fontsize=12,linewidth=0.5) #labels=[left,right,top,bottom]
    props  = dict(boxstyle='round', facecolor='wheat', alpha=1)
    props2 = dict(boxstyle='round', facecolor='tan', alpha=1)
    if '_ALL' not in GRIB_PATH_DES: #Simplify 'ALL' plot of CONUS
        ax.text(0.5, 0.03, str(int(np.sum(np.mean(data_success[:,isolate_st4],axis=0)<1)))+' Members Found', 
            transform=ax.transAxes, fontsize=12,verticalalignment='bottom', horizontalalignment='center', bbox=props)
        ax.text(0.5, 0.97, "Valid Time: "+curdate_start.strftime('%Y%m%d%H')+" - "+curdate_stop.strftime('%Y%m%d%H'),
            transform=ax.transAxes, fontsize=12,verticalalignment='top', horizontalalignment='center', bbox=props)
    cs = m.contourf(lon, lat, ndimage.filters.gaussian_filter(ens_mean, 2), latlon=True, levels=values, extend='min', cmap=my_cmap2, antialiased=False, markerstyle='o', vmin=np.spacing(0.0),vmax=1)
    cb = m.colorbar(cs,"right", ticks=values, size="5%", pad="2%", extend='min') 
    
    #Outline the observation if it exists
    str_inc = [i for i in range(len(isolate_st4)) if isolate_st4[i] == 0]
    if sum(isolate_st4 == 0) > 0:
        m.contour(lon, lat, np.squeeze(np.mean(simp_bin[:,:,:,str_inc],axis=2)) > 0, latlon=True, levels=values, cmap=mpl.colors.ListedColormap(["#000000"]), linewidths=2)
        
    #Scatter plot includes intensity (color) and member (symbol)
    for model in range(len(load_data_nc)):
        
        #Specify marker properly 
        if len(load_data_nc) == len(leg_nam_bymod):
            marker = leg_sym_bymod[model]    
        else:
            for bymod in range(0,len(leg_nam_bymod)):
                if leg_nam_bymod[bymod] in load_data_nc[model]:
                    marker=leg_sym_bymod[bymod]

        #Find modeled/observed objects in metadata
        if np.mean(np.isnan(simp_prop[model])) != 1:
            elements = np.unique(simp_prop[model][0])
            
            #Separate model and observations and set plotting properties
            if isolate_st4[model] == 0:
                elements   = elements[elements < 0]
                linecolor  = 'b'
                linewidth  = 1.5
                markersize = 50
                zorder     = 3
            else:
                elements = elements[elements > 0]
                linecolor  = 'k'
                linewidth  = 0.5
                markersize = 25
                zorder     = 2
    
            for tot_obj in elements: #Through each track
                ind = simp_prop[model][0] == tot_obj
  
                if len(simp_prop[model][4][ind]) > 2:
                    cs2= m.plot(simp_prop[model][5][ind], simp_prop[model][4][ind], color=linecolor, linewidth=linewidth, zorder=zorder, latlon=True)
                    cs = m.scatter(simp_prop[model][5][ind], simp_prop[model][4][ind], c = simp_prop[model][7][ind], \
                        marker=marker, vmin=0, vmax=np.array(raw_thres)*10, s=markersize, linewidth=0.25, cmap=my_cmap1, zorder=zorder, alpha=1, latlon=True)  
                else:
                    cs2= m.plot(simp_prop[model][5][ind][0], simp_prop[model][4][ind][0], color=linecolor, linewidth=linewidth, zorder=zorder, latlon=True)
                    cs = m.scatter(simp_prop[model][5][ind][0], simp_prop[model][4][ind][0], c = simp_prop[model][7][ind][0], \
                        marker=marker, vmin=0, vmax=np.array(raw_thres)*10, s=markersize, linewidth=0.25, cmap=my_cmap1, zorder=zorder, alpha=0.8, latlon=True)
                        
            #END model VS obs check
        #END through each track
    #END through the models
         
    if '_ALL' not in GRIB_PATH_DES: #Simplify 'ALL' plot of CONUS
        #Pass line instances to a legend to create centroid maximum legend by color
        line_label=[]
        line_str=[];
        for x in range(len(colorlist)):
            line_label = np.hstack((line_label, mpl.lines.Line2D(range(1), range(1), color=colorlist[x], linestyle='None', marker='o', markersize=7)))
            line_str   = np.hstack((line_str, leg_nam_byint[x]))
        first_legend=plt.legend(line_label, line_str, fontsize=7, numpoints=1, loc=3, framealpha=1)
        ax2 = plt.gca().add_artist(first_legend)
        
        #Pass line instances to a legend denoting member-type by markersize
        line_label=[]
        line_str=[];
        for x in range(len(leg_sym_bymod)):
            line_label = np.hstack((line_label, mpl.lines.Line2D(range(1), range(1), color='k', linestyle='None', marker=leg_sym_bymod[x], markersize=7)))
            line_str   = np.hstack((line_str, leg_nam_bymod[x]))
        plt.legend(line_label, line_str, fontsize=7, numpoints=1, loc=4, framealpha=1)
    
    #Create the title
    ax.set_title("Ensemble Object Probabilities - "+"Precip. >= "+str(raw_thres)+"\" \n "+'{:02d}'.format(int(pre_acc))+ \
        " Hour Acc. Precip. - Initialized "+curdate.strftime('%Y%m%d%H'),fontsize=13)
        
    #Special condition, when plotting 'ALL' of CONUS, draw lines to show distinct regions
    if '_ALL' in GRIB_PATH_DES:
        m.plot(np.array([-110,-110,-110]), np.array([20,36,52]),color='k',linewidth=3,zorder=3,alpha=0.5,latlon=True)
        m.plot(np.array([-85,-85,-85]), np.array([20,36,52]),color='k',linewidth=3,zorder=3,alpha=0.5,latlon=True)
        m.plot(np.array([-130,-97,-64]), np.array([38,38,38]),color='k',linewidth=3,zorder=3,alpha=0.5,latlon=True)

        ax.text((1.0/6.0)-0.02, 0.95, 'North West Domain \n Click to Zoom in',
            transform=ax.transAxes, fontsize=11,verticalalignment='top',zorder=5,horizontalalignment='center',bbox=props2)
        ax.text(0.5, 0.95, 'North Central Domain \n Click to Zoom in', 
            transform=ax.transAxes, fontsize=11,verticalalignment='top',zorder=5,horizontalalignment='center',bbox=props2)
        ax.text((5.0/6.0)+0.02, 0.95, 'North East Domain \n Click to Zoom in', 
            transform=ax.transAxes, fontsize=11,verticalalignment='top',zorder=5,horizontalalignment='center',bbox=props2)
                    
        ax.text((1.0/6.0)-0.02, 0.1, 'South West Domain \n Click to Zoom in',
            transform=ax.transAxes, fontsize=11,verticalalignment='top',zorder=5,horizontalalignment='center',bbox=props2)
        ax.text(0.5, 0.1, 'South Central Domain \n Click to Zoom in', 
            transform=ax.transAxes, fontsize=11,verticalalignment='top',zorder=5,horizontalalignment='center',bbox=props2)
        ax.text((5.0/6.0)+0.02, 0.1, 'South East Domain \n Click to Zoom in', 
            transform=ax.transAxes, fontsize=11,verticalalignment='top',zorder=5,horizontalalignment='center',bbox=props2)
            
    #Show and save the plot
    #plt.hold(True)
    plt.show()
    plt.savefig(FIG_PATH_s+'/'+GRIB_PATH_DES+'_TOTENS_objprob_bymodel_'+curdate_currn.strftime('%Y%m%d%H')+'_p'+'{:02d}'.format(int(pre_acc))+ \
        '_t'+str(raw_thres)+'.png', bbox_inches='tight',dpi=150)
    plt.close()
    
    ##########################################################################################
    ###PLOT OF OBJ PROB. (SHADED), MODEL TYPE (MARKERTYPE), AND OBJ. FCST HR (MARKER COLOR)#
    ##########################################################################################
    
    #Create range of values to plot
    values = np.linspace(0,1,11)
    fig = plt.figure(figsize=(8,8))
    ax = fig.add_axes([0.1,0.1,0.8,0.8])
    #Create polar stereographic Basemap instance.
    m = Basemap(llcrnrlon=latlon_dims[0], llcrnrlat=latlon_dims[1], urcrnrlon=latlon_dims[2],urcrnrlat=latlon_dims[3],resolution='i',projection='merc')
    #Draw coastlines, state and country boundaries, edge of map.
    m.drawcoastlines(linewidth=0.5)
    m.drawstates(linewidth=0.5)
    m.drawcountries(linewidth=0.5)
    #Draw parallels and meridians
    m.drawparallels(np.arange(0,90,5),labels=[1,0,0,0],fontsize=12,linewidth=0.5) #labels=[left,right,top,bottom]
    m.drawmeridians(np.arange(-180,0,10),labels=[0,0,0,1],fontsize=12,linewidth=0.5) #labels=[left,right,top,bottom]
    props = dict(boxstyle='round', facecolor='wheat', alpha=1)
    ax.text(0.5, 0.03, str(int(np.sum(np.mean(data_success[:,isolate_st4],axis=0)<1)))+' Members Found', 
        transform=ax.transAxes, fontsize=12,verticalalignment='bottom', horizontalalignment='center', bbox=props)
    ax.text(0.5, 0.97, "Valid Time: "+curdate_start.strftime('%Y%m%d%H')+" - "+curdate_stop.strftime('%Y%m%d%H'),
        transform=ax.transAxes, fontsize=12,verticalalignment='top', horizontalalignment='center', bbox=props)
    cs = m.contourf(lon, lat, ndimage.filters.gaussian_filter(ens_mean, 2), latlon=True, levels=values, extend='min', cmap=my_cmap2, antialiased=False, markerstyle='o', vmin=np.spacing(0.0),vmax=1)
    cb = m.colorbar(cs,"right", ticks=values, size="5%", pad="2%", extend='min') 
        
    #Outline the observation if it exists
    str_inc = [i for i in range(len(isolate_st4)) if isolate_st4[i] == 0]
    if sum(isolate_st4 == 0) > 0:
        m.contour(lon, lat, np.squeeze(np.mean(simp_bin[:,:,:,str_inc],axis=2)) > 0, latlon=True, levels=values, cmap=mpl.colors.ListedColormap(["#000000"]), linewidths=2)
        
    #Scatter plot includes intensity (color) and member (symbol)
    for model in range(len(load_data_nc)):

        #Specify marker properly 
        if len(load_data_nc) == len(leg_nam_bymod):
            marker = leg_sym_bymod[model]    
        else:
            for bymod in range(0,len(leg_nam_bymod)):
                if leg_nam_bymod[bymod] in load_data_nc[model]:
                    marker=leg_sym_bymod[bymod]
        
        #Find modeled objects in metadata
        if np.mean(np.isnan(simp_prop[model])) != 1:
            
            elements = np.unique(simp_prop[model][0])
            #Separate model and observations and set plotting properties
            if isolate_st4[model] == 0:
                elements   = elements[elements < 0]
                linecolor  = 'b'
                linewidth  = 1.5
                markersize = 50
                zorder     = 3
            else:
                elements = elements[elements > 0]
                linecolor  = 'k'
                linewidth  = 0.5
                markersize = 25
                zorder     = 2
    
            for tot_obj in elements: #Through each track
                ind = simp_prop[model][0] == tot_obj
                
                if len(simp_prop[model][5][ind]) > 2:
                    cs2= m.plot(simp_prop[model][5][ind], simp_prop[model][4][ind], color='k', linewidth=linewidth, zorder=zorder, latlon=True)
                    cs = m.scatter(simp_prop[model][5][ind], simp_prop[model][4][ind], c = simp_prop[model][2][ind]+1, \
                        marker=marker, vmin=0, vmax=hrs[-1], s=markersize, linewidth=0.25, cmap=my_cmap1_short, zorder=zorder, alpha=2, latlon=True)  
                else:
                    cs2= m.plot(simp_prop[model][5][ind][0], simp_prop[model][4][ind][0], color='k', linewidth=linewidth, zorder=zorder, latlon=True)
                    cs = m.scatter(simp_prop[model][5][ind][0], simp_prop[model][4][ind][0], c = simp_prop[model][2][ind][0]+1, \
                        marker=marker, vmin=0, vmax=hrs[-1], s=markersize, linewidth=0.25, cmap=my_cmap1_short, zorder=zorder, alpha=2, latlon=True)
        #END through each track
    #END through the models

    #Pass line instances to a legend to create centroid forecast hour legend by color
    line_label=[]
    line_str=[];
    for x in range(0,len(leg_nam_bytime)):
        line_label = np.hstack((line_label, mpl.lines.Line2D(range(1), range(1), color=colorlist[x], linestyle='None', marker='o', markersize=7)))
        line_str   = np.hstack((line_str, leg_nam_bytime[x]))
    first_legend=plt.legend(line_label, line_str, fontsize=7, numpoints=1, loc=3, framealpha=1)
    ax2 = plt.gca().add_artist(first_legend)
    
    #Pass line instances to a legend denoting member-type by markersize
    line_label=[]
    line_str=[];
    for x in range(len(leg_sym_bymod)):
        line_label = np.hstack((line_label, mpl.lines.Line2D(range(1), range(1), color='k', linestyle='None', marker=leg_sym_bymod[x], markersize=7)))
        line_str   = np.hstack((line_str, leg_nam_bymod[x]))
    plt.legend(line_label, line_str, fontsize=7, numpoints=1, loc=4, framealpha=1)
    
    #Create the title
    ax.set_title("Ensemble Object Probabilities - "+"Precip. >= "+str(raw_thres)+"\" \n "+'{:02d}'.format(int(pre_acc))+ \
        " Hour Acc. Precip. - Initialized "+curdate.strftime('%Y%m%d%H'),fontsize=13)
        
    #Show and save the plot
    #plt.hold(True)
    plt.show()
    plt.savefig(FIG_PATH_s+'/'+GRIB_PATH_DES+'_TOTENS_objprob_bytime_'+curdate_currn.strftime('%Y%m%d%H')+'_p'+'{:02d}'.format(int(pre_acc))+ \
        '_t'+str(raw_thres)+'.png', bbox_inches='tight',dpi=150)
    plt.close()

    #############################################################################################
    #ANIMATION OF OBJ PROB. (SHADED), MODEL TYPE (MARKERTYPE), AND OBJ. INTENSITY (MARKER COLOR)#
    #############################################################################################
    fig_name=[];
    
    for hr_inc in range(len(hrs)):
        
        #Determine time stamp for hour
        curdate_curr = curdate_currn + datetime.timedelta(hours=hr_inc+1)
        
        #Determine hour matrix that isolates models existing for that hour
        isolate_hr = np.array(isolate_st4 == 1) & np.array(data_success[hr_inc,:] == 0)
        
        #Determine hourly object probabilities
        ens_mean = np.nanmean(simp_bin[:,:,hr_inc,isolate_hr == 1], axis = 2)
        ens_mean[ens_mean > 0.95] = 0.95
        
        #Create range of values to plot
        values = np.linspace(0,1,11)
        fig = plt.figure(figsize=(8,8))
        ax = fig.add_axes([0.1,0.1,0.8,0.8])
        #Create polar stereographic Basemap instance.
        m = Basemap(llcrnrlon=latlon_dims[0], llcrnrlat=latlon_dims[1], urcrnrlon=latlon_dims[2],urcrnrlat=latlon_dims[3],resolution='i',projection='merc')
        #Draw coastlines, state and country boundaries, edge of map.
        m.drawcoastlines(linewidth=0.5)
        m.drawstates(linewidth=0.5)
        m.drawcountries(linewidth=0.5)
        #Draw parallels and meridians
        m.drawparallels(np.arange(0,90,5),labels=[1,0,0,0],fontsize=12,linewidth=0.5) #labels=[left,right,top,bottom]
        m.drawmeridians(np.arange(-180,0,10),labels=[0,0,0,1],fontsize=12,linewidth=0.5) #labels=[left,right,top,bottom]
        props = dict(boxstyle='round', facecolor='wheat', alpha=1)
        ax.text(0.5, 0.03, str(int(np.sum(isolate_hr == 1)))+' Members Found', 
            transform=ax.transAxes, fontsize=12,verticalalignment='bottom', horizontalalignment='center', bbox=props)
        ax.text(0.5, 0.97, "Valid Time: "+curdate_curr.strftime('%Y%m%d%H')+" - "+str(int(pre_acc))+' Hour Accumulation ',
            transform=ax.transAxes, fontsize=12,verticalalignment='top', horizontalalignment='center', bbox=props)
        cs = m.contourf(lon, lat, ndimage.filters.gaussian_filter(ens_mean, 2), latlon=True, levels=values, extend='min', cmap=my_cmap2, antialiased=False, markerstyle='o', vmin=np.spacing(0.0),vmax=1)
        cb = m.colorbar(cs,"right", ticks=values, size="5%", pad="2%", extend='min') 
        
        #Outline the observation if it exists
        str_inc = [i for i in range(len(isolate_st4)) if isolate_st4[i] == 0]
        if sum(isolate_st4 == 0) > 0:
            m.contour(lon, lat, np.squeeze(simp_bin[:,:,hr_inc,str_inc],axis=2) > 0, latlon=True, levels=values, cmap=mpl.colors.ListedColormap(["#000000"]), linewidths=2)
            
        #Create two plots: 1) includes intensity (color) and member (symbol) at time of concern
        #                  2) total track of object throughout time
        for model in range(len(load_data_nc)):
      
            #Specify marker properly 
            if len(load_data_nc) == len(leg_nam_bymod):
                marker = leg_sym_bymod[model]    
            else:
                for bymod in range(0,len(leg_nam_bymod)):
                    if leg_nam_bymod[bymod] in load_data_nc[model]:
                        marker=leg_sym_bymod[bymod]
                
            #Find modeled/observed objects in metadata
            if np.mean(np.isnan(simp_prop[model])) != 1:
                
                #Isolate/identify specific hour object attributes
                hr_loc = simp_prop[model][2] == hr_inc
                
                #If data exists for that hour, isolate and plot
                if len(hr_loc) > 0:
                    elements = np.unique(simp_prop[model][0][hr_loc])
                    
                    #Separate model and observations and set plotting properties
                    if isolate_st4[model] == 0:
                        elements   = elements[elements < 0]
                        linecolor  = 'b'
                        linewidth  = 1.5
                        markersize = 50
                        zorder     = 3
                    else:
                        elements = elements[elements > 0]
                        linecolor  = 'k'
                        linewidth  = 0.5
                        markersize = 25
                        zorder     = 2
            
                    for tot_obj in elements: #Through each track
                        #Tracks for instantaneous time and total time
                        ind_snap = np.asarray(simp_prop[model][0] == tot_obj) & np.asarray(simp_prop[model][2] == hr_inc)
                        ind_all  = np.asarray(simp_prop[model][0] == tot_obj)
                        
                        if len(simp_prop[model][5][ind_snap]) > 2:
                            m.plot(simp_prop[model][5][ind_snap], simp_prop[model][4][ind_snap], color=linecolor, linewidth=linewidth, zorder=zorder, latlon=True)
                            m.scatter(simp_prop[model][5][ind_snap], simp_prop[model][4][ind_snap], c = simp_prop[model][7][ind_snap], \
                                marker=marker, vmin=0, vmax=np.array(raw_thres)*10, s=markersize, linewidth=0.25, cmap=my_cmap1, zorder=zorder, alpha=1, latlon=True)  
                        else:
                            m.plot(simp_prop[model][5][ind_snap][0], simp_prop[model][4][ind_snap][0], color=linecolor, linewidth=linewidth, zorder=zorder, latlon=True)
                            m.scatter(simp_prop[model][5][ind_snap][0], simp_prop[model][4][ind_snap][0], c = simp_prop[model][7][ind_snap][0], \
                                marker=marker, vmin=0, vmax=np.array(raw_thres)*10, s=markersize, linewidth=0.25, cmap=my_cmap1, zorder=zorder, alpha=0.8, latlon=True)
                                
                        if len(simp_prop[model][5][ind_all]) > 2:
                            m.plot(simp_prop[model][5][ind_all], simp_prop[model][4][ind_all], color=linecolor, linewidth=linewidth-0.25, zorder=zorder, latlon=True) 
                        else:
                            m.plot(simp_prop[model][5][ind_all][0], simp_prop[model][4][ind_all][0], color=linecolor, linewidth=linewidth-0.25, zorder=zorder, latlon=True)
                                            
                    #END check for hourly data existing
                #END model VS obs check
            #END through each track
        #END through the models
    
        #Pass line instances to a legend to create centroid maximum legend by color
        line_label=[]
        line_str=[];
        for x in range(len(colorlist)):
            line_label = np.hstack((line_label, mpl.lines.Line2D(range(1), range(1), color=colorlist[x], linestyle='None', marker='o', markersize=7)))
            line_str   = np.hstack((line_str, leg_nam_byint[x]))
        first_legend=plt.legend(line_label, line_str, fontsize=7, numpoints=1, loc=3, framealpha=1)
        ax2 = plt.gca().add_artist(first_legend)
        
        #Pass line instances to a legend denoting member-type by markersize
        line_label=[]
        line_str=[];
        for x in range(len(leg_sym_bymod)):
            line_label = np.hstack((line_label, mpl.lines.Line2D(range(1), range(1), color='k', linestyle='None', marker=leg_sym_bymod[x], markersize=7)))
            line_str   = np.hstack((line_str, leg_nam_bymod[x]))
        plt.legend(line_label, line_str, fontsize=7, numpoints=1, loc=4, framealpha=1)
        
        #Create the title
        ax.set_title("Ensemble Object Probabilities - "+"Precip. >= "+str(raw_thres)+"\" \n "+'{:02d}'.format(int(pre_acc))+ \
            " Hour Acc. Precip. - Initialized "+curdate.strftime('%Y%m%d%H'),fontsize=13)
            
        #Show and save the plot
        #plt.hold(True)
        plt.show()
        plt.savefig(FIG_PATH_s+'/'+GRIB_PATH_DES+'_TOTENS_objprob_byhour_'+curdate_currn.strftime('%Y%m%d%H')+'_p'+'{:02d}'.format(int(pre_acc))+ \
            '_t'+str(raw_thres)+'_f'+str(int(hr_inc+1))+'.png', bbox_inches='tight',dpi=150)
        plt.close()
        
        #Update figure names to create animated figure
        fig_name=np.append(fig_name,FIG_PATH_s+'/'+GRIB_PATH_DES+'_TOTENS_objprob_byhour_'+curdate_currn.strftime('%Y%m%d%H')+'_p'+'{:02d}'.format(int(pre_acc))+ \
            '_t'+str(raw_thres)+'_f'+str(int(hr_inc+1))+'.png')
    
    #Create an animation from the figures previously saved
    subprocess.call('convert -delay 100 '+' '.join(fig_name)+' -loop 0 '+FIG_PATH_s+'/'+GRIB_PATH_DES+'_TOTENS_objprob_byhour_'+ \
        curdate_currn.strftime('%Y%m%d%H')+'_p'+'{:02d}'.format(int(pre_acc))+'_t'+str(raw_thres)+'.gif', \
        stdout=open(os.devnull, 'wb'), stderr=open(os.devnull, 'wb'), shell=True) 

###################################################################################
#MTDPlotTLEFcst identifies any time lagged ensembles and plots each one separately
#with color/location representing centroid location/magnitude, and marker type representing
#each member in the TLE. This code will plot an unlimited number of TLE's with up to 9 
#members within each TLE (restricted by marker type legend). The goal is to assess any 
#potential trends in the plots. QPE is also plotted if requested with object shape in 
#black outline and color/location representing centroid location/magnitude.
#
#Created by MJE. 20170328-20170420
#
#####################INPUT FILES FOR MODEPlotAll####################################
#GRIB_PATH_DES   = unique identifier assigned to figure name
#FIG_PATH_s      = path where figures are to be saved
#latlon_dims     = latitude/longitude dimensions for plotting [WLON,SLAT,ELON,NLAT]
#pre_acc         = accumulation interval
#hrs             = array of forecast hours
#raw_thres       = raw threshold for MODE
#curdate         = datetime attribute
#data_success    = record of which data were succesfully loaded
#load_data_nc    = gridded variable data
#lat             = gridded latitude data
#lon             = gridded longitude data
#simp_bin        = gridded simple data
#simp_prop       = simple cluster centroid info of lat,lon,max. Takes the form of [model][attributes]
####################OUTPUT FILES FOR MODEPlotAllFcst####################################
#Note: "Simple" means unmerged while "cluster" refers to merged
#"Single" refers to unmatched objects while "pair" refers to matched objects.
#
###################################################################################
def MTDPlotTLEFcst(GRIB_PATH_DES,FIG_PATH_s,latlon_dims,pre_acc,hrs,raw_thres,curdate,data_success,load_data_nc,lat,lon,simp_bin,simp_prop):
    
    #data_success=data_success[:,:,thres_count]
    #simp_bin=simp_bin[:,:,:,:,thres_count]
    #simp_prop=simp_prop[thres_count]
    
    #Remove ST4 data since ST4 objects are not plotted here
    isolate_st4=[]
    for i in range(0,len(load_data_nc),1):
        if 'ST4' in load_data_nc[i]:
            isolate_st4 = np.append(isolate_st4,False)
        else:
            isolate_st4 = np.append(isolate_st4,True)
            
    isolate_st4      = isolate_st4 == 1
    isolate_st4      = np.array(isolate_st4 == 1)
            
    #Currently this function only requires a logical matrix
    simp_bin = simp_bin > 0
    
    #Add NaNs to missing data in binary matrix. Convert to float
    simp_bin=simp_bin.astype(float)
    NaN_loc = (data_success == 1).astype(float)
    NaN_loc[NaN_loc == 1] = np.NaN
    
    for j in range(simp_bin.shape[0]):
        for i in range(simp_bin.shape[1]):
            simp_bin[j,i,:,:] = simp_bin[j,i,:,:] + NaN_loc
            
    #Compute the proper forecast hour strings
    curdate_currn = curdate + datetime.timedelta(hours=0)
    curdate_start = curdate + datetime.timedelta(hours=hrs[0])
    curdate_stop  = curdate + datetime.timedelta(hours=hrs[-1])
    
    #Establish a smoothing kernel to smooth ensemble probaiblities
    kern=np.hanning(50)
    kern /= kern.sum() 
    
    #Create colorlist attributes and legend information if possible
    colorlist = ["#ffffff", "#02fd02", "#01c501", "#228b22", "#9acd32", "#fdf802", "#f8d826", "#e5bc00", "#fd9500", "#fd0000", "#bc0000"]
    my_cmap1 = mpl.colors.ListedColormap(colorlist)
    my_cmap2 = mpl.cm.get_cmap('cool')
    my_cmap2.set_under('white')
    leg_nam_byint  = ['>='+str(x)+"\"" for x in np.round(np.linspace(0,np.array(raw_thres)*10,len(colorlist)),2)]
    if sum(isolate_st4 == 0) > 0: #If obs exists, change legend
        leg_sym_bymem  = ['s','d','o','*','^','1','2','3','4']
        mod_inc = 1 #When plotting marker, add 1 for models if st4 exists
    else:
        leg_sym_bymem  = ['d','o','*','^','1','2','3','4']
        mod_inc = 0 #If ST4 does not exist, no offset needed
        
    #Find unique models with different lags
    load_data_short = [load_data_nc[i][:-9] for i in range(0,len(load_data_nc))]
    load_data = [load_data_nc[i][:-3] for i in range(0,len(load_data_nc))]
    lag = np.array([long(load_data[i][load_data[i].index("lag")+3::]) for i in range(0,len(load_data))])
    [u, indices] = np.unique(load_data_short, return_inverse=True)

    #Loop through each unique model grouping. Create a separate plot for each TLE
    ind_count = 0
    for ind in range(0,len(u),1):
        
        #Initialize variables
        simp_prop_k        = [[] for i in range(0,20,1)]
        leg_sym_use        = []
        
        #Consider the current TLE and subset data
        current_ind        = indices == ind
        data_success_p     = data_success[:,current_ind]
        load_data_nc_p     = [load_data_nc[i] for i in range(0,int(len(current_ind))) if current_ind[i] == True]
        simp_bin_p         = simp_bin[:,:,:,current_ind]
        simp_prop_p        = [simp_prop[i] for i in range(0,int(len(current_ind))) if current_ind[i] == True]
        lag_p              = lag[current_ind]
        
        if sum(indices==ind) > 1 and np.mean(data_success_p) != 1: #check to see if a TLE exists with data

            #Sort the current TLE from newest to oldest           
            old2new = np.argsort(lag_p)
            
            #Cat all TLEs by model
            data_success_k     = data_success_p[:,old2new[::-1]]
            load_data_nc_k     = [load_data_nc_p[old2new[i]] for i in range(int(len(old2new))-1,-1,-1)]
            #simp_bin_k         = np.squeeze(simp_bin_p[:,:,:,old2new[::-1]])
            count_elem         = 0 
            
            for model in range(int(len(old2new))-1,-1,-1):
                if np.mean(np.isnan(simp_prop_p[old2new[model]])) != 1:
                    simp_prop_k[count_elem] = simp_prop_p[old2new[model]][:,simp_prop_p[old2new[model]][0,:]>0]
                else:
                    simp_prop_k[count_elem] = np.nan
                    
                count_elem += 1

            #Compute raw ensemble mean probability, set 100% to 95% to preserve colorbar
            ens_mean = np.nanmax(np.nanmean(simp_bin_p, axis = 3) , axis = 2)
            ens_mean[ens_mean > 0.95] = 0.95

            #Legend information for time lagged ensembles
            if sum(isolate_st4 == 0) > 0:
                leg_nam_bymem = np.append('ST4',[str(i)+' Hours Lag' for i in lag_p])
            else:
                leg_nam_bymem = np.array([str(i)+' Hours Lag' for i in lag_p])

            #Create range of values to plot and colorbar
            values = np.linspace(0,1,11)
            
            fig = plt.figure(figsize=(8,8))
            ax = fig.add_axes([0.1,0.1,0.8,0.8])
            # create polar stereographic Basemap instance.
            m = Basemap(llcrnrlon=latlon_dims[0], llcrnrlat=latlon_dims[1], urcrnrlon=latlon_dims[2],urcrnrlat=latlon_dims[3],resolution='i',projection='merc')
            # draw coastlines, state and country boundaries, edge of map.
            m.drawcoastlines(linewidth=0.5)
            m.drawstates(linewidth=0.5)
            m.drawcountries(linewidth=0.5)
            # draw parallels and meridians
            m.drawparallels(np.arange(0,90,5),labels=[1,0,0,0],fontsize=12,linewidth=0.5) #labels=[left,right,top,bottom]
            m.drawmeridians(np.arange(-180,0,10),labels=[0,0,0,1],fontsize=12,linewidth=0.5) #labels=[left,right,top,bottom]
            props = dict(boxstyle='round', facecolor='wheat', alpha=1)
            ax.text(0.5, 0.03, load_data_nc_k[0][:-9]+' - '+str(int(np.sum(np.mean(data_success_k==0,axis=0)>0)))+' Members Found', 
                transform=ax.transAxes, fontsize=12,verticalalignment='bottom', horizontalalignment='center', bbox=props)
            ax.text(0.5, 0.97, "Valid Time: "+curdate_start.strftime('%Y%m%d%H')+" - "+curdate_stop.strftime('%Y%m%d%H'),
                transform=ax.transAxes, fontsize=12,verticalalignment='top', horizontalalignment='center', bbox=props)
            norm = mpl.colors.BoundaryNorm(values, 0)

            cs = m.contourf(lon, lat, ndimage.filters.gaussian_filter(ens_mean, 2), latlon=True, \
                levels=values, extend='min', cmap=my_cmap2, antialiased=False, markerstyle='o', vmin=np.spacing(0.0),vmax=1)
            cb = m.colorbar(cs,"right", ticks=values, size="5%", pad="2%", extend='min')
            
            #If observation exists, plot outline
            if sum(isolate_st4 == 0) > 0:
                m.contour(lon, lat, np.squeeze(np.mean(simp_bin[:,:,:,isolate_st4 == 0],axis=2)) > 0, latlon=True, levels=values, cmap=mpl.colors.ListedColormap(["#000000"]), linewidths=2)

            #Plot the raw TLE objects
            line_label=[]
            line_str=[]
            
            #Array to properly index marker legend
            marker_inc = range(int(len(old2new))-1,-1,-1)
            
            #Scatter plot the observation if it exists
            if sum(isolate_st4 == 0) > 0:
                
                #Element location for observation
                obs_inc = [int(i) for i in range(len(isolate_st4)) if isolate_st4[i] == 0]
                obs_inc = obs_inc[0]
                
                #Find observed objects in metadata
                if np.mean(np.isnan(simp_prop[obs_inc])) != 1:
                    
                    elements = np.unique(simp_prop[obs_inc][0])
                    elements = elements[elements < 0]
            
                    for tot_obj in elements: #Through each track
                        obj = simp_prop[obs_inc][0] == tot_obj
                        
                        if len(simp_prop[obs_inc][5][obj]) > 2:
                            m.plot(simp_prop[obs_inc][5][obj], simp_prop[obs_inc][4][obj], color='b', linewidth=1.5, zorder = 3, latlon=True)
                            m.scatter(simp_prop[obs_inc][5][obj], simp_prop[obs_inc][4][obj], c = simp_prop[obs_inc][7][obj], \
                                marker=leg_sym_bymem[obs_inc], vmin=0, vmax=np.array(raw_thres)*10, s=50, linewidth=0.25, cmap=my_cmap1, zorder = 3, alpha = 0.8, latlon=True)  
                        else:
                            m.plot(simp_prop[obs_inc][5][obj][0], simp_prop[obs_inc][4][obj][0], color='b', linewidth=1.5, zorder = 3, latlon=True)
                            m.scatter(simp_prop[obs_inc][5][obj][0], simp_prop[obs_inc][4][obj][0], c = simp_prop[obs_inc][7][obj][0], \
                                marker=leg_sym_bymem[obs_inc], vmin=0, vmax=np.array(raw_thres)*10, s=50, linewidth=0.25, cmap=my_cmap1, zorder = 3, alpha = 0.8, latlon=True)
                    leg_sym_use = np.append(leg_sym_use,leg_sym_bymem[obs_inc])  

            #Scatter plot includes intensity (color) and member (symbol)
            for model in range(len(load_data_nc_k)):
             
                #Find modeled objects in metadata
                if np.mean(np.isnan(simp_prop_k[model])) != 1:
                    
                    elements = np.unique(simp_prop_k[model][0])
                    elements = elements[elements >= 0]
            
                    for tot_obj in elements: #Through each track
                        obj = simp_prop_k[model][0] == tot_obj
                        
                        if len(simp_prop_k[model][5][obj]) > 2:
                            m.plot(simp_prop_k[model][5][obj], simp_prop_k[model][4][obj], color='k', linewidth=0.5, zorder = 2, latlon=True)
                            m.scatter(simp_prop_k[model][5][obj], simp_prop_k[model][4][obj], c = simp_prop_k[model][7][obj], \
                                marker=leg_sym_bymem[marker_inc[model]+mod_inc], vmin=0, vmax=np.array(raw_thres)*10, s=25, linewidth=0.25, cmap=my_cmap1, zorder = 2, alpha = 0.8, latlon=True)  
                        else:
                            m.plot(simp_prop_k[model][5][obj][0], simp_prop_k[model][4][obj][0], color='k', linewidth=0.5, zorder = 2, latlon=True)
                            m.scatter(simp_prop_k[model][5][obj][0], simp_prop_k[model][4][obj][0], c = simp_prop_k[model][7][obj][0], \
                                marker=leg_sym_bymem[marker_inc[model]+mod_inc], vmin=0, vmax=np.array(raw_thres)*10, s=25, linewidth=0.25, cmap=my_cmap1, zorder = 2, alpha = 0.8, latlon=True)
                leg_sym_use = np.append(leg_sym_use,leg_sym_bymem[marker_inc[model]+mod_inc])
            #END through model to create scatterplot
            #plt.hold(True)
                                                                                                                                                                                                                                                                                                                                                                                                                                             
            #Pass line instances to a legend to create centroid maximum legend by color
            line_label = []
            line_str   = []
            for x in range(len(colorlist)):
                line_label = np.hstack((line_label, mpl.lines.Line2D(range(1), range(1), color=colorlist[x], linestyle='None', marker='o', markersize=5)))
                line_str   = np.hstack((line_str, leg_nam_byint[x]))
            first_legend  = plt.legend(line_label, line_str, fontsize=7, numpoints=1, loc=3, framealpha=1)
            plt.gca().add_artist(first_legend)
            
            #Create legend of markertype by member
            line_label = []
            line_str   = []
            leg_count  = 0
            for x in range(np.sum(np.mean(data_success_k,axis=0) < 1) + mod_inc):
                line_label = np.hstack((line_label, mpl.lines.Line2D(range(1), range(1), color='k', linestyle='None', marker=leg_sym_use[x], markersize=5)))
                line_str   = np.hstack((line_str, leg_nam_bymem[x]))
                leg_count += 1
            second_legend = plt.legend(line_label, line_str, fontsize=7, numpoints=1, loc=4, framealpha=1)
            plt.gca().add_artist(second_legend)
            
            ax.set_title("Objects/Max. Locations - "+"Precip. >= "+str(raw_thres)+"\" \n "+'{:02d}'.format(int(pre_acc))+ \
                " Hour Acc. Precip. - Initialized "+curdate.strftime('%Y%m%d%H'),fontsize=13)
            #plt.hold(True)
            plt.show()
            plt.savefig(FIG_PATH_s+'/'+GRIB_PATH_DES+'_TLE_obj_'+curdate_currn.strftime('%Y%m%d%H')+'_p'+'{:02d}'.format(int(pre_acc))+ \
            '_t'+str(raw_thres)+'_group'+str(ind_count)+'.png', bbox_inches='tight',dpi=150)
            plt.close()
            
            ind_count += 1
         
###################################################################################
#MTDPlotAllSnowFcst creates three plots: 1) forecast ensemble object probability (shading) and 
#object centroid location/magnitude/model type (marker). If observation exists then the
#observed object is plotted (black outline) in addition to centroid location/magnitude.
#2) forecast ensemble object probability (shading) and object centroid location/forecast 
#hour/model type (marker). If observation exists, observed object is plotted (black outline)
#in addition to centroid location/magnitude. 3) An hourly animation of figure 1) is created
#to better convey temporal details of the objects.
#
#Created by MJE. 20170327-20170420
#####################INPUT FILES FOR MTDPlotAllSnowFcst####################################
#GRIB_PATH_DES   = unique identifier assigned to figure name
#FIG_PATH_s      = path where figures are to be saved
#latlon_dims     = latitude/longitude dimensions for plotting [WLON,SLAT,ELON,NLAT]
#pre_acc         = accumulation interval
#hrs             = array of forecast hours
#raw_thres       = raw threshold for MODE
#curdate         = datetime attribute
#data_success    = record of which data were succesfully loaded
#load_data_nc    = gridded variable data
#lat             = gridded latitude data
#lon             = gridded longitude data
#simp_bin        = gridded simple data
#simp_prop       = simple cluster centroid info of lat,lon,max. Takes the form of [model][attributes]
####################OUTPUT FILES FOR MODEPlotAllFcst####################################
#Note: "Simple" means unmerged while "cluster" refers to merged
#"Single" refers to unmatched objects while "pair" refers to matched objects.
#
###################################################################################
def MTDPlotAllSnowFcst(GRIB_PATH_DES,FIG_PATH_s,latlon_dims,pre_acc,hrs,raw_thres,curdate,data_success,load_data_nc,lat,lon,simp_bin,simp_prop):
          
    #data_success  = data_success_new[:,:,thres_count]
    #simp_bin      = simp_bin[:,:,:,:,thres_count]
    #simp_prop     = simp_prop[thres_count]
    #latlon_dims   = latlon_sub[subsets]
    #GRIB_PATH_DES = GRIB_PATH_DES+domain_sub[subsets]
    #raw_thres     = raw_thres[0]
    
    #Find and isolate ST4 data
    isolate_st4=[]
    for i in range(0,len(load_data_nc),1):
        if 'ST4' in load_data_nc[i]:
            isolate_st4 = np.append(isolate_st4,False)
        else:
            isolate_st4 = np.append(isolate_st4,True)
    isolate_st4       = isolate_st4 == 1

    #Add NaNs to missing data in binary matrix. Convert to float
    simp_bin=simp_bin.astype(float)
    NaN_loc = (data_success == 1).astype(float)
    NaN_loc[NaN_loc == 1] = np.NaN
    
    for j in range(simp_bin.shape[0]):
        for i in range(simp_bin.shape[1]):
            simp_bin[j,i,:,:] = simp_bin[j,i,:,:] + NaN_loc
            
    #Isolate model only to plot outline of all objects
    simp_bin_mod = simp_bin[:,:,:,isolate_st4]
    
    #Compute the proper forecast hour strings
    curdate_currn = curdate + datetime.timedelta(hours=0)
    
    #Establish a smoothing kernel to smooth ensemble probaiblities
    kern=np.hanning(50)
    kern /= kern.sum() 
    
    #Create first colorlist
    colorlist = ["#ffffff", "#02fd02", "#01c501", "#228b22", "#9acd32", "#fdf802", "#f8d826", "#e5bc00", "#fd9500", "#fd0000", "#bc0000"]
    my_cmap1 = mpl.colors.ListedColormap(colorlist)

    #Given a default model name list, build a list based on user specified models
    leg_nam_bymod_default = ['ST4'  ,'HIRESNAM','HIRESW','HRRR','NSSL-OP','NSSL-ARW','NSSL-NMB','HRAM']
    leg_sym_bymod_default = ['s','d','*','^','<','>','v','o']
    
    if len(load_data_nc) <= 8: #If list is small enough, specific markers for individual models
        leg_nam_bymod  = load_data_nc
        leg_sym_bymod  = leg_sym_bymod_default[0:len(load_data_nc)]
    else:                      #Create markers by model type
        leg_nam_bymod = []
        leg_sym_bymod = []
        for bymod in range(0,len(leg_nam_bymod_default)):
            if np.sum([leg_nam_bymod_default[bymod] in i for i in load_data_nc]) > 0:
                leg_nam_bymod = np.append(leg_nam_bymod,leg_nam_bymod_default[bymod])
                leg_sym_bymod = np.append(leg_sym_bymod,leg_sym_bymod_default[bymod])
    
    leg_nam_byint  = ['>='+str(x)+"\"" for x in np.round(np.linspace(0,np.array(raw_thres)*10,len(colorlist)),2)]
    leg_nam_bytime = ['Hours '+str(i)+' - '+str(i+int(round(len(hrs)/len(colorlist)))) \
        for i in range(0,len(hrs),int(round(len(hrs)/len(colorlist))+1))]
    
    #Shorten initial colorlist for bytime plots
    my_cmap1_short = mpl.colors.ListedColormap(colorlist[0:len(leg_nam_bytime)])
       
    #Create second colorlist, replace first element with white
    my_cmap2 = mpl.cm.get_cmap('cool')
    my_cmap2.set_under('white')
     
    ##########################################################################################
    ########################CREATE HOURLY PLOTS OF SNOWBAND OBJECTS###########################
    ##########################################################################################
    #['OBJ_ID','CLUS_ID','TIME_INDEX','AREA','CENTROID_LAT','CENTROID_LON','AXIS_ANG','INTENSITY_90'] 
    
    for hr_inc in range(len(hrs)):

        #Create datestring for forecast hour
        curdate_cur = curdate + datetime.timedelta(hours=hr_inc+1)
        
        #Create range of values to plot
        values = np.linspace(0,1,11)
        fig = plt.figure(figsize=(8,8))
        ax = fig.add_axes([0.1,0.1,0.8,0.8])
        #Create polar stereographic Basemap instance.
        m = Basemap(llcrnrlon=latlon_dims[0], llcrnrlat=latlon_dims[1], urcrnrlon=latlon_dims[2],urcrnrlat=latlon_dims[3],resolution='i',projection='merc')
        #Draw coastlines, state and country boundaries, edge of map.
        m.drawcoastlines(linewidth=0.5)
        m.drawstates(linewidth=0.5)
        m.drawcountries(linewidth=0.5)
        #Draw parallels and meridians
        m.drawparallels(np.arange(0,90,5),labels=[1,0,0,0],fontsize=12,linewidth=0.5) #labels=[left,right,top,bottom]
        m.drawmeridians(np.arange(-180,0,10),labels=[0,0,0,1],fontsize=12,linewidth=0.5) #labels=[left,right,top,bottom]
        props  = dict(boxstyle='round', facecolor='wheat', alpha=1)
        props2 = dict(boxstyle='round', facecolor='tan', alpha=1)
        ax.text(0.5, 0.03, str(int(np.sum((data_success[hr_inc,isolate_st4]==0)*1,axis=0)))+' Members Found', 
            transform=ax.transAxes, fontsize=12,verticalalignment='bottom', horizontalalignment='center', bbox=props)
        ax.text(0.5, 0.97, "Valid Time: "+curdate_cur.strftime('%Y%m%d%H'),
            transform=ax.transAxes, fontsize=12,verticalalignment='top', horizontalalignment='center', bbox=props)
       
        for model in range(0,simp_bin_mod.shape[3]):
            
            if np.sum(simp_bin_mod[:,:,hr_inc,model]) == 0: #If no data, insert single value point
                simp_bin_mod[0,0,hr_inc,model] = 1
                    
            #Capture 90th percentile of object intensity through time matching
            try:
                inten  = simp_prop[model][7][simp_prop[model][2] == hr_inc]
                obj_id = np.unique(simp_bin_mod[:,:,hr_inc,model])
                
            except TypeError:
                inten  = [0]
                obj_id = [0,0]
            
            if len(inten) == 0:
                inten  = [0]
                obj_id = [0,0]
            
            #Loop through the objects
            obj_count = 1
            for obj in inten:
   
                colorlist = ["#ffffff", "#02fd02", "#01c501", "#228b22", "#9acd32", "#fdf802", "#f8d826", "#e5bc00", "#fd9500", "#fd0000", "#bc0000"]

                if obj == 0:
                    c_outline = "#ffffff"
                elif obj >  0.0 and obj < 0.1:
                    c_outline = "#02fd02"
                elif obj >= 0.1 and obj < 0.2:
                    c_outline = "#01c501"
                elif obj >= 0.2 and obj < 0.3:
                    c_outline = "#228b22"
                elif obj >= 0.3 and obj < 0.4:
                    c_outline = "#9acd32"
                elif obj >  0.4 and obj < 0.5:
                    c_outline = "#fdf802"
                elif obj >= 0.5 and obj < 0.6:
                    c_outline = "#f8d826"
                elif obj >= 0.6 and obj < 0.7:
                    c_outline = "#e5bc00"
                elif obj >= 0.7 and obj < 0.8:
                    c_outline = "#fd9500"
                elif obj >= 0.8 and obj < 0.9:
                    c_outline = "#fd0000"
                elif obj >= 0.9 and obj < 1:
                    c_outline = "#bc0000"
                       
                try: #Catch error if plotting objects outside of regional subset
                    #Contour creates bad legends, so use contour plot outline but contourf attributes for legend
                    cs1 = m.contourf(lon, lat, (simp_bin_mod[:,:,hr_inc,model]==obj_id[obj_count]*1)*0, latlon=True, levels=values,  cmap=my_cmap1, \
                        antialiased=False, vmin=np.spacing(0.0),vmax=1)
                    cb = m.colorbar(cs1,"right", ticks=values, size="5%", pad="5%", filled=True, extend='min') 
                    
                    cs2 = m.contour(lon, lat, (simp_bin_mod[:,:,hr_inc,model]==obj_id[obj_count]*1), latlon=True, antialiased=False, colors=c_outline,linewidths=0.8)
                except:
                    pass
                    
                obj_count += 1

        #Create the title
        ax.set_title("All Snow Precip. Objects >= "+str(raw_thres)+"\" \n "+'{:02d}'.format(int(pre_acc))+ \
            " Hour Acc. Precip. at Hour "+'{:02d}'.format(int(hrs[hr_inc]))+" - Initialized "+curdate.strftime('%Y%m%d%H'),fontsize=13)
            
        #Show and save the plot
        #plt.hold(True)
        plt.show()
        plt.savefig(FIG_PATH_s+'/'+GRIB_PATH_DES+'_snowobj_byhour_'+curdate_currn.strftime('%Y%m%d%H')+'_p'+'{:02d}'.format(int(pre_acc))+ \
            '_t'+str(raw_thres)+'_h'+'{:02d}'.format(int(hrs[hr_inc]))+'.png', bbox_inches='tight',dpi=150)
        plt.close()

###################################################################################
#THIS FUNCTION IS DESGINED TO LOAD AND PLOT ALL PAIRED MODEL/OBS FUNCTION ATTRIBUTES 
#AND PRECIPITATION BY MODEL INITIALIZATION FOR JUST A SINGLE SPECIFIED RUN. IT IS 
#DESIGNED TO COMPARE INTUITIVE "BY EYE" RESULTS TO THE TRACKER SO THE TRACKER CAN 
#BE TUNED AND ADJUSTED AS NEEDED. THIS FUNCTION LOADS THE RETROSPECTIVE DATA FORMAT ONLY.
#
#Created by MJE. 20171205.
#####################INPUT FILES FOR MTDPlotRetro####################################
#GRIB_PATH_DES   = unique identifier assigned to figure name
#FIG_PATH_s      = path where figures are to be saved
#latlon_dims     = latitude/longitude dimensions for plotting [WLON,SLAT,ELON,NLAT]
#pre_acc         = accumulation interval
#hrs             = array of forecast hours
#raw_thres       = raw threshold for MODE
#curdate         = datetime attribute
#data_success    = record of which data were succesfully loaded
#load_data_nc    = gridded variable data
#lat             = gridded latitude data
#lon             = gridded longitude data
#fcst            = raw forecast field
#obs             = raw observation field
#clus_bin        = gridded cluster data
#pair_prop       = paired cluster centroid info of lat,lon,max. Takes the form of [model][attributes]
####################OUTPUT FILES FOR MTDPlotRetro####################################
#Note: "Simple" means unmerged while "cluster" refers to merged
#"Single" refers to unmatched objects while "pair" refers to matched objects.
#
###################################################################################
def MTDPlotRetro(GRIB_PATH_DES,FIG_PATH_s,latlon_dims,pre_acc,hrs,raw_thres,curdate,data_success,load_data_nc,lat,lon,fcst,obs,clus_bin,pair_prop):
                               
    #fcst       = fcst_p
    #obs        = obs_p
    #hrs        = hrs_all
    #raw_thres  = thres
    #FIG_PATH_s = FIG_PATH
    #latlon_dims = [lonmin,latmin,lonmax,latmax]
    
    #Find and isolate ST4 data
    isolate_analy=[]
    for i in range(0,len(load_data_nc),1):
        if 'ST4' in load_data_nc[i] or 'MRMS' in load_data_nc[i]:
            isolate_analy = np.append(isolate_analy,False)
        else:
            isolate_analy = np.append(isolate_analy,True)
    isolate_analy       = isolate_analy == 1

    #Currently this function only requires a logical matrix
    clus_bin = clus_bin > 0
    
    #Add NaNs to missing data in binary matrix. Convert to float
    clus_bin=clus_bin.astype(float)
    NaN_loc = (np.mean(data_success,axis=1)>0)*1.0
    NaN_loc[NaN_loc == 1] = np.NaN
    
    for j in range(clus_bin.shape[0]):
        for i in range(clus_bin.shape[1]):
            for m in range(clus_bin.shape[3]):
                clus_bin[j,i,:,m] = clus_bin[j,i,:,m] + NaN_loc

    #Compute the proper forecast hour strings
    curdate_currn = curdate + datetime.timedelta(hours=0)
    
    #Establish a smoothing kernel to smooth ensemble probaiblities
    kern=np.hanning(50)
    kern /= kern.sum() 
    
    #Create first colorlist
    colorlist = ["#ffffff", "#02fd02", "#01c501", "#228b22", "#9acd32", "#fdf802", "#f8d826", "#e5bc00", "#fd9500", "#fd0000", "#bc0000"]
    my_cmap1 = mpl.colors.ListedColormap(colorlist)

    #Given a default model name list, build a list based on user specified models
    leg_nam_bymod_default = ['ST4'  'MRMS','HIRESNAM','HIRESW','HRRR','NSSL-OP','NSSL-ARW','NSSL-NMB','HRAM','NEWSe']
    leg_sym_bymod_default = ['s','d','*','^','<','>','v','o']
    
    if len(load_data_nc) <= 8: #If list is small enough, specific markers for individual models
        leg_nam_bymod  = load_data_nc
        leg_sym_bymod  = leg_sym_bymod_default[0:len(load_data_nc)]
    else:                      #Create markers by model type
        leg_nam_bymod = []
        leg_sym_bymod = []
        for bymod in range(0,len(leg_nam_bymod_default)):
            if np.sum([leg_nam_bymod_default[bymod] in i for i in load_data_nc]) > 0:
                leg_nam_bymod = np.append(leg_nam_bymod,leg_nam_bymod_default[bymod])
                leg_sym_bymod = np.append(leg_sym_bymod,leg_sym_bymod_default[bymod])
    
    leg_nam_byint  = ['>='+str(x)+"\"" for x in np.round(np.linspace(0,np.array(raw_thres)*10,len(colorlist)),2)]

    #Create second colorlist, replace first element with white
    my_cmap2 = mpl.cm.get_cmap('cool')
    my_cmap2.set_under('white')
     
    #############################################################################################
    #ANIMATION OF OBJ OUTLINE, INTENSITY, TYPE FOR MODEL AND OBSERVATION#########################
    #############################################################################################
    fig_name=[];
    
    hr_count = 0
    for hr_inc in hrs:
        
        if np.isnan(NaN_loc[hr_count]) != 1:

            #Determine time stamp for hour
            curdate_curr = curdate_currn + datetime.timedelta(hours=hr_inc)
        
            #Create range of values to plot
            values = np.linspace(0,1,11)
            fig = plt.figure(figsize=(8,8))
            ax = fig.add_axes([0.1,0.1,0.8,0.8])
            #Create polar stereographic Basemap instance.
            m = Basemap(llcrnrlon=latlon_dims[0], llcrnrlat=latlon_dims[1], urcrnrlon=latlon_dims[2],urcrnrlat=latlon_dims[3],resolution='i',projection='merc')
            #Draw coastlines, state and country boundaries, edge of map.
            m.drawcoastlines(linewidth=0.5)
            m.drawstates(linewidth=0.5)
            m.drawcountries(linewidth=0.5)
            #Draw parallels and meridians
            m.drawparallels(np.arange(0,90,5),labels=[1,0,0,0],fontsize=12,linewidth=0.5) #labels=[left,right,top,bottom]
            m.drawmeridians(np.arange(-180,0,10),labels=[0,0,0,1],fontsize=12,linewidth=0.5) #labels=[left,right,top,bottom]
            props = dict(boxstyle='round', facecolor='wheat', alpha=1)
            ax.text(0.5, 0.97, "Valid Time: "+curdate_curr.strftime('%Y%m%d%H%M')+" - "+str(pre_acc)+' Hour Accumulation ',
                transform=ax.transAxes, fontsize=12,verticalalignment='top', horizontalalignment='center', bbox=props)
            #Plot the model object outline in grey
            print clus_bin.shape
            print isolate_analy.shape
            if np.sum(clus_bin[:,:,hr_count,isolate_analy==1]) > 0:
                try:
                    cs = m.contour(lon, lat, np.squeeze(np.round(clus_bin[:,:,hr_count,isolate_analy==1],2)), latlon=True, colors='grey', linewidths=1, zorder=1)
                except ValueError:
                    pass
            #Plot the observation object outline in black
            if np.sum(clus_bin[:,:,hr_count,isolate_analy==0]) > 0:
                try:
                    cs = m.contour(lon, lat, np.squeeze(np.round(clus_bin[:,:,hr_count,isolate_analy==0],2)), latlon=True, colors='black', linewidths=1, zorder=1)
                except ValueError:
                    pass
                    
        #Plot object attributes
        for model in range(len(load_data_nc)):
      
            #Specify marker properly 
            if len(load_data_nc) == len(leg_nam_bymod):
                marker = leg_sym_bymod[model]    
            else:
                for bymod in range(0,len(leg_nam_bymod)):
                    if leg_nam_bymod[bymod] in load_data_nc[model]:
                        marker=leg_sym_bymod[bymod]
                
            #Find modeled/observed objects in metadata
            if np.mean(np.isnan(pair_prop[model])) != 1:
                
                #Isolate/identify specific hour object attributes
                hr_loc = pair_prop[model][2] == hr_count
                
                #If data exists for that hour, isolate and plot
                if len(hr_loc) > 0:
                    elements = np.unique(pair_prop[model][0][hr_loc])
                    
                    #Separate model and observations and set plotting properties
                    if isolate_analy[model] == 0:
                        elements   = elements[elements < 0]
                        linecolor  = 'b'
                        linewidth  = 1.5
                        markersize = 50
                        zorder     = 3
                    else:
                        elements = elements[elements > 0]
                        linecolor  = 'k'
                        linewidth  = 0.5
                        markersize = 25
                        zorder     = 2
            
                    for tot_obj in elements: #Through each track
                        #Tracks for instantaneous time and total time
                        ind_snap = np.asarray(pair_prop[model][0] == tot_obj) & np.asarray(pair_prop[model][2] == hr_count)
                        ind_all  = np.asarray(pair_prop[model][0] == tot_obj)
                        
                        if len(pair_prop[model][5][ind_snap]) > 2:
                            m.plot(pair_prop[model][5][ind_snap], pair_prop[model][4][ind_snap], c = linecolor, linewidth=linewidth, zorder=zorder, latlon=True)
                            m.scatter(pair_prop[model][5][ind_snap], pair_prop[model][4][ind_snap], c = pair_prop[model][9][ind_snap], \
                                marker=marker, vmin=0, vmax=np.array(raw_thres)*10, s=markersize, linewidth=0.25, cmap=my_cmap1, zorder=zorder, alpha=1, latlon=True)  
                        else:
                            m.plot(pair_prop[model][5][ind_snap][0], pair_prop[model][4][ind_snap][0], c = linecolor, linewidth=linewidth, zorder=zorder, latlon=True)
                            m.scatter(pair_prop[model][5][ind_snap][0], pair_prop[model][4][ind_snap][0], c = pair_prop[model][9][ind_snap][0], \
                                marker=marker, vmin=0, vmax=np.array(raw_thres)*10, s=markersize, linewidth=0.25, cmap=my_cmap1, zorder=zorder, alpha=0.8, latlon=True)
                                
                        if len(pair_prop[model][5][ind_all]) > 2:
                            m.plot(pair_prop[model][5][ind_all], pair_prop[model][4][ind_all], color=linecolor, linewidth=linewidth-0.25, zorder=zorder, latlon=True) 
                        else:
                            m.plot(pair_prop[model][5][ind_all][0], pair_prop[model][4][ind_all][0], color=linecolor, linewidth=linewidth-0.25, zorder=zorder, latlon=True)
                                            
                    #END check for hourly data existing
                #END model VS obs check
            #END through each track
        #END through the models
    
        #Pass line instances to a legend to create centroid maximum legend by color
        line_label=[]
        line_str=[];
        for x in range(len(colorlist)):
            line_label = np.hstack((line_label, mpl.lines.Line2D(range(1), range(1), color=colorlist[x], linestyle='None', marker='o', markersize=7)))
            line_str   = np.hstack((line_str, leg_nam_byint[x]))
        first_legend=plt.legend(line_label, line_str, fontsize=7, numpoints=1, loc=3, framealpha=1)
        ax2 = plt.gca().add_artist(first_legend)
        
        #Pass line instances to a legend denoting member-type by markersize
        line_label=[]
        line_str=[];
        for x in range(len(leg_sym_bymod)):
            line_label = np.hstack((line_label, mpl.lines.Line2D(range(1), range(1), color='k', linestyle='None', marker=leg_sym_bymod[x], markersize=7)))
            line_str   = np.hstack((line_str, leg_nam_bymod[x]))
        plt.legend(line_label, line_str, fontsize=7, numpoints=1, loc=4, framealpha=1)
        
        #Create the title
        ax.set_title("Ensemble Object Probabilities - "+"Precip. >= "+str(raw_thres)+"\" \n "+str(pre_acc)+ \
            " Hour Acc. Precip. - Initialized "+curdate.strftime('%Y%m%d%H%M'),fontsize=13)
            
        #Show and save the plot
        #plt.hold(True)
        plt.show()
        plt.savefig(FIG_PATH_s+'/'+curdate_currn.strftime('%Y%m%d%H')+'/'+GRIB_PATH_DES+'_TOTENS_objshape_byhour_'+curdate_currn.strftime('%Y%m%d%H%M')+ \
            '_p'+str(pre_acc)+'_t'+str(raw_thres)+'_f'+str(hr_inc)+'.png', bbox_inches='tight',dpi=150)
        plt.close()
        
        #Update figure names to create animated figure
        fig_name=np.append(fig_name,FIG_PATH_s+'/'+curdate_currn.strftime('%Y%m%d%H')+'/'+GRIB_PATH_DES+'_TOTENS_objshape_byhour_'+ \
            curdate_currn.strftime('%Y%m%d%H%M')+'_p'+str(pre_acc)+'_t'+str(raw_thres)+'_f'+str(hr_inc)+'.png')
            
        hr_count += 1

    #Create an animation from the figures previously saved
    subprocess.call('convert -delay 100 '+' '.join(fig_name)+' -loop 0 '+FIG_PATH_s+'/'+curdate_currn.strftime('%Y%m%d%H')+'/'+ \
        GRIB_PATH_DES+'_TOTENS_objshape_byhour_'+curdate_currn.strftime('%Y%m%d%H%M')+'_p'+str(pre_acc)+'_t'+str(raw_thres)+'.gif', \
        stdout=open(os.devnull, 'wb'), stderr=open(os.devnull, 'wb'), shell=True) 
  
    #############################################################################################
    ####ANIMATION OF RAW FORECAST PRECIPITATION WITH OBJECT ATTRIBUTE OVERLAY####################
    #############################################################################################

    fig_name=[];
    
    hr_count = 0
    for hr_inc in hrs:
        
        if np.isnan(NaN_loc[hr_count]) != 1:

            #Determine time stamp for hour
            curdate_curr = curdate_currn + datetime.timedelta(hours=hr_inc)
        
            #Create range of values to plot
            values = np.linspace(0,1,11)
            fig = plt.figure(figsize=(8,8))
            ax = fig.add_axes([0.1,0.1,0.8,0.8])
            #Create polar stereographic Basemap instance.
            m = Basemap(llcrnrlon=latlon_dims[0], llcrnrlat=latlon_dims[1], urcrnrlon=latlon_dims[2],urcrnrlat=latlon_dims[3],resolution='i',projection='merc')
            #Draw coastlines, state and country boundaries, edge of map.
            m.drawcoastlines(linewidth=0.5)
            m.drawstates(linewidth=0.5)
            m.drawcountries(linewidth=0.5)
            #Draw parallels and meridians
            m.drawparallels(np.arange(0,90,5),labels=[1,0,0,0],fontsize=12,linewidth=0.5) #labels=[left,right,top,bottom]
            m.drawmeridians(np.arange(-180,0,10),labels=[0,0,0,1],fontsize=12,linewidth=0.5) #labels=[left,right,top,bottom]
            props = dict(boxstyle='round', facecolor='wheat', alpha=1)
            ax.text(0.5, 0.97, "Valid Time: "+curdate_curr.strftime('%Y%m%d%H%M')+" - "+str(pre_acc)+' Hour Accumulation ',
                transform=ax.transAxes, fontsize=12,verticalalignment='top', horizontalalignment='center', bbox=props)
            #Plot the model object outline in grey
            if np.nansum(fcst[:,:,hr_count]) > 0:
                cs = m.contourf(lon, lat, np.round(fcst[:,:,hr_count],2), latlon=True, levels=values, extend='min', cmap=my_cmap2, antialiased=False, markerstyle='o', vmin=raw_thres,vmax=1)
            cb = m.colorbar(cs,"right", ticks=values, size="5%", pad="2%", extend='min')
                
        #Plot forecast object attributes
        fcst_loc = np.where(isolate_analy==1)[0][0]
        
        #Specify marker properly 
        if len(load_data_nc) == len(leg_nam_bymod):
            marker = leg_sym_bymod[fcst_loc]    
        else:
            for bymod in range(0,len(leg_nam_bymod)):
                if leg_nam_bymod[bymod] in load_data_nc[fcst_loc]:
                    marker=leg_sym_bymod[bymod]
            
        #Find modeled/observed objects in metadata
        if np.mean(np.isnan(pair_prop[fcst_loc])) != 1:
            
            #Isolate/identify specific hour object attributes
            hr_loc = pair_prop[fcst_loc][2] == hr_count
            
            #If data exists for that hour, isolate and plot
            if len(hr_loc) > 0:
                elements = np.unique(pair_prop[fcst_loc][0][hr_loc])
                
                #Separate model and observations and set plotting properties

                elements   = elements[elements > 0]
                linecolor  = 'b'
                linewidth  = 1.5
                markersize = 50
                zorder     = 3

                for tot_obj in elements: #Through each track
                    #Tracks for instantaneous time and total time
                    ind_snap = np.asarray(pair_prop[fcst_loc][0] == tot_obj) & np.asarray(pair_prop[fcst_loc][2] == hr_count)
                    ind_all  = np.asarray(pair_prop[fcst_loc][0] == tot_obj)
                    
                    if len(pair_prop[fcst_loc][5][ind_snap]) > 2:
                        m.plot(pair_prop[fcst_loc][5][ind_snap], pair_prop[fcst_loc][4][ind_snap], c = linecolor, linewidth=linewidth, zorder=zorder, latlon=True)
                        m.scatter(pair_prop[fcst_loc][5][ind_snap], pair_prop[fcst_loc][4][ind_snap], c = pair_prop[fcst_loc][9][ind_snap], \
                            marker=marker, vmin=0, vmax=np.array(raw_thres)*10, s=markersize, linewidth=0.25, cmap=my_cmap1, zorder=zorder, alpha=1, latlon=True)  
                    else:
                        m.plot(pair_prop[fcst_loc][5][ind_snap][0], pair_prop[fcst_loc][4][ind_snap][0], c = linecolor, linewidth=linewidth, zorder=zorder, latlon=True)
                        m.scatter(pair_prop[fcst_loc][5][ind_snap][0], pair_prop[fcst_loc][4][ind_snap][0], c = pair_prop[fcst_loc][9][ind_snap][0], \
                            marker=marker, vmin=0, vmax=np.array(raw_thres)*10, s=markersize, linewidth=0.25, cmap=my_cmap1, zorder=zorder, alpha=0.8, latlon=True)
                            
                    if len(pair_prop[fcst_loc][5][ind_all]) > 2:
                        m.plot(pair_prop[fcst_loc][5][ind_all], pair_prop[fcst_loc][4][ind_all], color=linecolor, linewidth=linewidth-0.25, zorder=zorder, latlon=True) 
                    else:
                        m.plot(pair_prop[fcst_loc][5][ind_all][0], pair_prop[fcst_loc][4][ind_all][0], color=linecolor, linewidth=linewidth-0.25, zorder=zorder, latlon=True)
                                        
                #END check for hourly data existing
            #END model VS obs check
        #END through each track
    
        #Pass line instances to a legend to create centroid maximum legend by color
        line_label=[]
        line_str=[];
        for x in range(len(colorlist)):
            line_label = np.hstack((line_label, mpl.lines.Line2D(range(1), range(1), color=colorlist[x], linestyle='None', marker='o', markersize=7)))
            line_str   = np.hstack((line_str, leg_nam_byint[x]))
        first_legend=plt.legend(line_label, line_str, fontsize=7, numpoints=1, loc=3, framealpha=1)
        ax2 = plt.gca().add_artist(first_legend)
        
        #Pass line instances to a legend denoting member-type by markersize
        line_label=[]
        line_str=[];
        for x in range(len(leg_sym_bymod)):
            line_label = np.hstack((line_label, mpl.lines.Line2D(range(1), range(1), color='k', linestyle='None', marker=leg_sym_bymod[x], markersize=7)))
            line_str   = np.hstack((line_str, leg_nam_bymod[x]))
        plt.legend(line_label, line_str, fontsize=7, numpoints=1, loc=4, framealpha=1)
        
        #Create the title
        ax.set_title("Model Object and Raw Precipitation - "+"Precip. >= "+str(raw_thres)+"\" \n "+str(pre_acc)+ \
            " Hour Acc. Precip. - Initialized "+curdate.strftime('%Y%m%d%H%M'),fontsize=13)
            
        #Show and save the plot
        #plt.hold(True)
        plt.show()
        plt.savefig(FIG_PATH_s+'/'+curdate_currn.strftime('%Y%m%d%H')+'/'+GRIB_PATH_DES+'_fcst_precipAobjs_byhour_'+curdate_currn.strftime('%Y%m%d%H%M')+'_p'+str(pre_acc)+ \
            '_t'+str(raw_thres)+'_f'+str(hr_inc)+'.png', bbox_inches='tight',dpi=150)
        plt.close()
        
        #Update figure names to create animated figure
        fig_name=np.append(fig_name,FIG_PATH_s+'/'+curdate_currn.strftime('%Y%m%d%H')+'/'+GRIB_PATH_DES+'_fcst_precipAobjs_byhour_'+curdate_currn.strftime('%Y%m%d%H%M')+'_p'+str(pre_acc)+ \
            '_t'+str(raw_thres)+'_f'+str(hr_inc)+'.png')

        hr_count += 1
    #Create an animation from the figures previously saved
    subprocess.call('convert -delay 50 '+' '.join(fig_name)+' -loop 0 '+FIG_PATH_s+'/'+curdate_currn.strftime('%Y%m%d%H')+'/'+ \
        GRIB_PATH_DES+'_fcst_precipAobjs_byhour_'+curdate_currn.strftime('%Y%m%d%H%M')+'_p'+str(pre_acc)+'_t'+str(raw_thres)+'.gif', \
        stdout=open(os.devnull, 'wb'), stderr=open(os.devnull, 'wb'), shell=True) 
        
    #############################################################################################
    ####ANIMATION OF RAW OBSERVATION PRECIPITATION WITH OBJECT ATTRIBUTE OVERLAY#################
    #############################################################################################

    fig_name=[];
    hr_count = 0
    
    for hr_inc in hrs:
        
        if np.isnan(NaN_loc[hr_count]) != 1:

            #Determine time stamp for hour
            curdate_curr = curdate_currn + datetime.timedelta(hours=hr_inc)
        
            #Create range of values to plot
            values = np.linspace(0,1,11)
            fig = plt.figure(figsize=(8,8))
            ax = fig.add_axes([0.1,0.1,0.8,0.8])
            #Create polar stereographic Basemap instance.
            m = Basemap(llcrnrlon=latlon_dims[0], llcrnrlat=latlon_dims[1], urcrnrlon=latlon_dims[2],urcrnrlat=latlon_dims[3],resolution='i',projection='merc')
            #Draw coastlines, state and country boundaries, edge of map.
            m.drawcoastlines(linewidth=0.5)
            m.drawstates(linewidth=0.5)
            m.drawcountries(linewidth=0.5)
            #Draw parallels and meridians
            m.drawparallels(np.arange(0,90,5),labels=[1,0,0,0],fontsize=12,linewidth=0.5) #labels=[left,right,top,bottom]
            m.drawmeridians(np.arange(-180,0,10),labels=[0,0,0,1],fontsize=12,linewidth=0.5) #labels=[left,right,top,bottom]
            props = dict(boxstyle='round', facecolor='wheat', alpha=1)
            ax.text(0.5, 0.97, "Valid Time: "+curdate_curr.strftime('%Y%m%d%H%M')+" - "+str(pre_acc)+' Hour Accumulation ',
                transform=ax.transAxes, fontsize=12,verticalalignment='top', horizontalalignment='center', bbox=props)
            #Plot the obs object outline in grey
            if np.nansum(obs[:,:,hr_count]) > 0:
                cs = m.contourf(lon, lat, np.round(obs[:,:,hr_count],2), latlon=True, levels=values, extend='min', cmap=my_cmap2, antialiased=False, markerstyle='o', vmin=raw_thres,vmax=1)
            cb = m.colorbar(cs,"right", ticks=values, size="5%", pad="2%", extend='min')
                                                                                                                                                                                                                                             
        #Plot observation object attributes
        obs_loc = np.where(isolate_analy==0)[0][0]
        
        #Specify marker properly 
        if len(load_data_nc) == len(leg_nam_bymod):
            marker = leg_sym_bymod[obs_loc]    
        else:
            for bymod in range(0,len(leg_nam_bymod)):
                if leg_nam_bymod[bymod] in load_data_nc[obs_loc]:
                    marker=leg_sym_bymod[bymod]
            
        #Find modeled/observed objects in metadata
        if np.mean(np.isnan(pair_prop[obs_loc])) != 1:
            
            #Isolate/identify specific hour object attributes
            hr_loc = pair_prop[obs_loc][2] == hr_count
            
            #If data exists for that hour, isolate and plot
            if len(hr_loc) > 0:
                elements = np.unique(pair_prop[obs_loc][0][hr_loc])
                
                #Separate model and observations and set plotting properties

                elements   = elements[elements < 0]
                linecolor  = 'b'
                linewidth  = 1.5
                markersize = 50
                zorder     = 3

                for tot_obj in elements: #Through each track
                    #Tracks for instantaneous time and total time
                    ind_snap = np.asarray(pair_prop[obs_loc][0] == tot_obj) & np.asarray(pair_prop[obs_loc][2] == hr_count)
                    ind_all  = np.asarray(pair_prop[obs_loc][0] == tot_obj)
                    
                    if len(pair_prop[obs_loc][5][ind_snap]) > 2:
                        m.plot(pair_prop[obs_loc][5][ind_snap], pair_prop[obs_loc][4][ind_snap], c = linecolor, linewidth=linewidth, zorder=zorder, latlon=True)
                        m.scatter(pair_prop[obs_loc][5][ind_snap], pair_prop[obs_loc][4][ind_snap], c = pair_prop[obs_loc][9][ind_snap], \
                            marker=marker, vmin=0, vmax=np.array(raw_thres)*10, s=markersize, linewidth=0.25, cmap=my_cmap1, zorder=zorder, alpha=1, latlon=True)  
                    else:
                        m.plot(pair_prop[obs_loc][5][ind_snap][0], pair_prop[obs_loc][4][ind_snap][0], c = linecolor, linewidth=linewidth, zorder=zorder, latlon=True)
                        m.scatter(pair_prop[obs_loc][5][ind_snap][0], pair_prop[obs_loc][4][ind_snap][0], c = pair_prop[obs_loc][9][ind_snap][0], \
                            marker=marker, vmin=0, vmax=np.array(raw_thres)*10, s=markersize, linewidth=0.25, cmap=my_cmap1, zorder=zorder, alpha=0.8, latlon=True)
                            
                    if len(pair_prop[obs_loc][5][ind_all]) > 2:
                        m.plot(pair_prop[obs_loc][5][ind_all], pair_prop[obs_loc][4][ind_all], color=linecolor, linewidth=linewidth-0.25, zorder=zorder, latlon=True) 
                    else:
                        m.plot(pair_prop[obs_loc][5][ind_all][0], pair_prop[obs_loc][4][ind_all][0], color=linecolor, linewidth=linewidth-0.25, zorder=zorder, latlon=True)
                                        
                #END check for hourly data existing
            #END model VS obs check
        #END through each track
    
        #Pass line instances to a legend to create centroid maximum legend by color
        line_label=[]
        line_str=[];
        for x in range(len(colorlist)):
            line_label = np.hstack((line_label, mpl.lines.Line2D(range(1), range(1), color=colorlist[x], linestyle='None', marker='o', markersize=7)))
            line_str   = np.hstack((line_str, leg_nam_byint[x]))
        first_legend=plt.legend(line_label, line_str, fontsize=7, numpoints=1, loc=3, framealpha=1)
        ax2 = plt.gca().add_artist(first_legend)
        
        #Pass line instances to a legend denoting member-type by markersize
        line_label=[]
        line_str=[];
        for x in range(len(leg_sym_bymod)):
            line_label = np.hstack((line_label, mpl.lines.Line2D(range(1), range(1), color='k', linestyle='None', marker=leg_sym_bymod[x], markersize=7)))
            line_str   = np.hstack((line_str, leg_nam_bymod[x]))
        plt.legend(line_label, line_str, fontsize=7, numpoints=1, loc=4, framealpha=1)
        
        #Create the title
        ax.set_title("Observed Object and Raw Precipitation - "+"Precip. >= "+str(raw_thres)+"\" \n "+str(pre_acc)+ \
            " Hour Acc. Precip. - Initialized "+curdate.strftime('%Y%m%d%H%M'),fontsize=13)
            
        #Show and save the plot
        #plt.hold(True)
        plt.show()
        plt.savefig(FIG_PATH_s+'/'+curdate_currn.strftime('%Y%m%d%H')+'/'+GRIB_PATH_DES+'_obs_precipAobjs_byhour_'+curdate_currn.strftime('%Y%m%d%H%M')+ \
            '_p'+str(pre_acc)+'_t'+str(raw_thres)+'_f'+str(hr_inc)+'.png', bbox_inches='tight',dpi=150)
        plt.close()
        
        #Update figure names to create animated figure
        fig_name=np.append(fig_name,FIG_PATH_s+'/'+curdate_currn.strftime('%Y%m%d%H')+'/'+GRIB_PATH_DES+'_obs_precipAobjs_byhour_'+ \
            curdate_currn.strftime('%Y%m%d%H%M')+'_p'+str(pre_acc)+'_t'+str(raw_thres)+'_f'+str(hr_inc)+'.png')

        hr_count += 1
    #Create an animation from the figures previously saved
    subprocess.call('convert -delay 50 '+' '.join(fig_name)+' -loop 0 '+FIG_PATH_s+'/'+curdate_currn.strftime('%Y%m%d%H')+'/'+ \
        GRIB_PATH_DES+'_obs_precipAobjs_byhour_'+curdate_currn.strftime('%Y%m%d%H%M')+'_p'+str(pre_acc)+'_t'+str(raw_thres)+'.gif', \
        stdout=open(os.devnull, 'wb'), stderr=open(os.devnull, 'wb'), shell=True) 
     
###################################################################################
#THIS FUNCTION IS DESGINED TO LOAD AND PLOT ALL PAIRED MODEL/OBS PRECIPITATION BY MODEL 
#INITIALIZATION FOR JUST A SINGLE SPECIFIED RUN. THIS VERSION ONLY PLOTS PRECIPITATION 
#SO THAT THESE FIGURES CAN BE PRINTED OUT AND SUBJECTIVELY EVALUATED.
#
#Created by MJE. 20180227.
#####################INPUT FILES FOR MTDPlotRetroJustPrecip####################################
#GRIB_PATH_DES   = unique identifier assigned to figure name
#FIG_PATH_s      = path where figures are to be saved
#latlon_dims     = latitude/longitude dimensions for plotting [WLON,SLAT,ELON,NLAT]
#pre_acc         = accumulation interval
#hrs             = array of forecast hours
#raw_thres       = raw threshold for MODE
#curdate         = datetime attribute
#data_success    = record of which data were succesfully loaded
#load_data_nc    = gridded variable data
#lat             = gridded latitude data
#lon             = gridded longitude data
#fcst            = raw forecast field
#obs             = raw observation field
#clus_bin        = gridded cluster data
#pair_prop       = paired cluster centroid info of lat,lon,max. Takes the form of [model][attributes]
####################OUTPUT FILES FOR MTDPlotRetroJustPrecip####################################
#Note: "Simple" means unmerged while "cluster" refers to merged
#"Single" refers to unmatched objects while "pair" refers to matched objects.
#
###################################################################################
def MTDPlotRetroJustPrecip(GRIB_PATH_DES,FIG_PATH_s,latlon_dims,pre_acc,hrs,raw_thres,curdate,data_success,load_data_nc,lat,lon,fcst,obs,clus_bin,pair_prop):
    
    #fcst = fcst_p
    #obs  = obs_p
    #raw_thres = thres
    #FIG_PATH = FIG_PATH_s
    
    #Find and isolate ST4 data
    isolate_st4=[]
    for i in range(0,len(load_data_nc),1):
        if 'ST4' in load_data_nc[i]:
            isolate_st4 = np.append(isolate_st4,False)
        else:
            isolate_st4 = np.append(isolate_st4,True)
    isolate_st4       = isolate_st4 == 1

    #Currently this function only requires a logical matrix
    clus_bin = clus_bin > 0
    
    #Add NaNs to missing data in binary matrix. Convert to float
    clus_bin=clus_bin.astype(float)
    NaN_loc = (np.mean(data_success,axis=1)>0)*1.0
    NaN_loc[NaN_loc == 1] = np.NaN
    
    for j in range(clus_bin.shape[0]):
        for i in range(clus_bin.shape[1]):
            for m in range(clus_bin.shape[3]):
                clus_bin[j,i,:,m] = clus_bin[j,i,:,m] + NaN_loc

    #Compute the proper forecast hour strings
    curdate_currn = curdate + datetime.timedelta(hours=0)
    
    #Establish a smoothing kernel to smooth ensemble probaiblities
    kern=np.hanning(50)
    kern /= kern.sum() 

    #Create second colorlist, replace first element with white
    my_cmap2 = mpl.cm.get_cmap('cool')
    my_cmap2.set_under('white')
  
    #############################################################################################
    ####ANIMATION OF RAW FORECAST PRECIPITATION WITH OBJECT ATTRIBUTE OVERLAY####################
    #############################################################################################

    fig_name=[];
    hr_count = 0
        
    for hr_inc in hrs:
        
        if np.isnan(NaN_loc[hr_count]) != 1:

            #Determine time stamp for hour
            curdate_curr = curdate_currn + datetime.timedelta(hours=hr_inc)
            
            #Create range of values to plot
            values = np.linspace(0,1,11)
            fig = plt.figure(figsize=(8,8))
            ax = fig.add_axes([0.1,0.1,0.8,0.8])
            #Create polar stereographic Basemap instance.
            m = Basemap(llcrnrlon=latlon_dims[0], llcrnrlat=latlon_dims[1], urcrnrlon=latlon_dims[2],urcrnrlat=latlon_dims[3],resolution='i',projection='merc')
            #Draw coastlines, state and country boundaries, edge of map.
            m.drawcoastlines(linewidth=0.5)
            m.drawstates(linewidth=0.5)
            m.drawcountries(linewidth=0.5)
            #Draw parallels and meridians
            m.drawparallels(np.arange(0,90,0.5),labels=[1,0,0,0],fontsize=12,linewidth=0.5) #labels=[left,right,top,bottom]
            m.drawmeridians(np.arange(-180,0,0.5),labels=[0,0,0,1],fontsize=12,linewidth=0.5) #labels=[left,right,top,bottom]
            props = dict(boxstyle='round', facecolor='wheat', alpha=1)
            ax.text(0.5, 0.97, "Valid Time: "+curdate_curr.strftime('%Y%m%d%H%M')+" - "+str(int(pre_acc))+' Hour Accumulation ',
                transform=ax.transAxes, fontsize=12,verticalalignment='top', horizontalalignment='center', bbox=props)
            #Plot the model object outline in grey
            if np.nansum(fcst[:,:,hr_count]) > 0:
                cs = m.contourf(lon, lat, np.round(fcst[:,:,hr_count],2), latlon=True, levels=values, extend='min', cmap=my_cmap2, antialiased=False, markerstyle='o', vmin=raw_thres,vmax=1)
            cb = m.colorbar(cs,"right", ticks=values, size="5%", pad="2%", extend='min')
                
        #Create the title
        ax.set_title("Model Object and Raw Precipitation - "+"Precip. >= "+str(raw_thres)+"\" \n "+'{:02d}'.format(int(pre_acc))+ \
            " Hour Acc. Precip. - Initialized "+curdate.strftime('%Y%m%d%H%M'),fontsize=13)
            
        #Show and save the plot
        #plt.hold(True)
        plt.show()
        plt.savefig(FIG_PATH_s+'/'+curdate_currn.strftime('%Y%m%d%H')+'/'+GRIB_PATH_DES+'_fcst_precipAobjs_byhour_'+curdate_currn.strftime('%Y%m%d%H%M')+'_p'+'{:02d}'.format(int(pre_acc))+ \
            '_t'+str(raw_thres)+'_f'+str(hr_inc)+'_PRECIPONLY.png', bbox_inches='tight',dpi=150)
        plt.close()
 
        #Update figure names to create animated figure
        fig_name=np.append(fig_name,FIG_PATH_s+'/'+curdate_currn.strftime('%Y%m%d%H')+'/'+GRIB_PATH_DES+'_fcst_precipAobjs_byhour_'+curdate_currn.strftime('%Y%m%d%H%M')+'_p'+'{:02d}'.format(int(pre_acc))+ \
            '_t'+str(raw_thres)+'_f'+str(hr_inc)+'_PRECIPONLY.png')
            
        hr_count += 1
    #Create an animation from the figures previously saved
    subprocess.call('convert -delay 50 '+' '.join(fig_name)+' -loop 0 '+FIG_PATH_s+'/'+curdate_currn.strftime('%Y%m%d%H')+'/'+ \
        GRIB_PATH_DES+'_fcst_precipAobjs_byhour_'+curdate_currn.strftime('%Y%m%d%H%M')+'_p'+'{:02d}'.format(int(pre_acc))+'_t'+str(raw_thres)+'_PRECIPONLY.gif', \
        stdout=open(os.devnull, 'wb'), stderr=open(os.devnull, 'wb'), shell=True) 
        
    #############################################################################################
    ####ANIMATION OF RAW OBSERVATION PRECIPITATION WITH OBJECT ATTRIBUTE OVERLAY#################
    #############################################################################################

    fig_name=[];
    hr_count = 0
        
    for hr_inc in hrs:
        
        if np.isnan(NaN_loc[hr_count]) != 1:

            #Determine time stamp for hour
            curdate_curr = curdate_currn + datetime.timedelta(hours=hr_inc)
        
            #Create range of values to plot
            values = np.linspace(0,1,11)
            fig = plt.figure(figsize=(8,8))
            ax = fig.add_axes([0.1,0.1,0.8,0.8])
            #Create polar stereographic Basemap instance.
            m = Basemap(llcrnrlon=latlon_dims[0], llcrnrlat=latlon_dims[1], urcrnrlon=latlon_dims[2],urcrnrlat=latlon_dims[3],resolution='i',projection='merc')
            #Draw coastlines, state and country boundaries, edge of map.
            m.drawcoastlines(linewidth=0.5)
            m.drawstates(linewidth=0.5)
            m.drawcountries(linewidth=0.5)
            #Draw parallels and meridians
            m.drawparallels(np.arange(0,90,0.5),labels=[1,0,0,0],fontsize=12,linewidth=0.5) #labels=[left,right,top,bottom]
            m.drawmeridians(np.arange(-180,0,0.5),labels=[0,0,0,1],fontsize=12,linewidth=0.5) #labels=[left,right,top,bottom]
            props = dict(boxstyle='round', facecolor='wheat', alpha=1)
            ax.text(0.5, 0.97, "Valid Time: "+curdate_curr.strftime('%Y%m%d%H%M')+" - "+str(int(pre_acc))+' Hour Accumulation ',
                transform=ax.transAxes, fontsize=12,verticalalignment='top', horizontalalignment='center', bbox=props)
            #Plot the obs object outline in grey
            if np.nansum(obs[:,:,hr_count]) > 0:
                cs = m.contourf(lon, lat, np.round(obs[:,:,hr_count],2), latlon=True, levels=values, extend='min', cmap=my_cmap2, antialiased=False, markerstyle='o', vmin=raw_thres,vmax=1)
            cb = m.colorbar(cs,"right", ticks=values, size="5%", pad="2%", extend='min')

        #Create the title
        ax.set_title("Observed Object and Raw Precipitation - "+"Precip. >= "+str(raw_thres)+"\" \n "+'{:02d}'.format(int(pre_acc))+ \
            " Hour Acc. Precip. - Initialized "+curdate.strftime('%Y%m%d%H%M'),fontsize=13)
            
        #Show and save the plot
        #plt.hold(True)
        plt.show()
        plt.savefig(FIG_PATH_s+'/'+curdate_currn.strftime('%Y%m%d%H')+'/'+GRIB_PATH_DES+'_obs_precipAobjs_byhour_'+curdate_currn.strftime('%Y%m%d%H%M')+ \
            '_p'+'{:02d}'.format(int(pre_acc))+'_t'+str(raw_thres)+'_f'+str(hr_inc)+'_PRECIPONLY.png', bbox_inches='tight',dpi=150)
        plt.close()
        
        #Update figure names to create animated figure
        fig_name=np.append(fig_name,FIG_PATH_s+'/'+curdate_currn.strftime('%Y%m%d%H')+'/'+GRIB_PATH_DES+'_obs_precipAobjs_byhour_'+ \
            curdate_currn.strftime('%Y%m%d%H%M')+'_p'+'{:02d}'.format(int(pre_acc))+'_t'+str(raw_thres)+'_f'+str(hr_inc)+'_PRECIPONLY.png')

        hr_count += 1
    #Create an animation from the figures previously saved
    subprocess.call('convert -delay 50 '+' '.join(fig_name)+' -loop 0 '+FIG_PATH_s+'/'+curdate_currn.strftime('%Y%m%d%H')+'/'+ \
        GRIB_PATH_DES+'_obs_precipAobjs_byhour_'+curdate_currn.strftime('%Y%m%d%H%M')+'_p'+'{:02d}'.format(int(pre_acc))+'_t'+str(raw_thres)+'_PRECIPONLY.gif', \
        stdout=open(os.devnull, 'wb'), stderr=open(os.devnull, 'wb'), shell=True) 