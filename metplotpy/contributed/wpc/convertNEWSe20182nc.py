################################################################################################
#THIS CODE IS DESIGNED TO RENAME NEWSe 5-MINUTE DATA AND STRIP OUT ONLY THE PRECIPITATION 
#DATA FOR THE SUMMER OF 2018.
#
#3 INPUTS TO THIS FUNCTION: 1)  DIRECTORY WHERE DATA IS TO BE SAVED
#                           2) 'YYYYMMDDHR' OF DATA BEING CONSIDERED 
#                           3)  PRECIPITATION ACCUMULATION INTERVAL 'HHMMSS'
#                           
#MJE. 20190219-20190304.
################################################################################################

import pygrib
import subprocess
import sys
import os
import numpy as np
import datetime
from mpl_toolkits.basemap import Basemap, cm
import matplotlib as mpl
mpl.use('Agg') #So plots can be saved in cron
import matplotlib.pyplot as plt
from scipy.interpolate import griddata
from scipy.io import netcdf
from netCDF4 import Dataset
from scipy import ndimage
sys.path.append('/export/hpc-lw-dtbdev5/merickson/code/python/ERO')
import py2netcdf

#Static variables for MRMS grid
latlon_dims = [-130,20,-60,55]
grid_delta  = 0.01

#Pull the user input variables
GRIB_PATH = sys.argv[1]
inityear  = sys.argv[2][0:4]
initmonth = sys.argv[2][4:6]
initdays  = sys.argv[2][6:8]
inithour  = sys.argv[2][8:10]
initmins  = sys.argv[2][10:12]

fcstyear  = sys.argv[3][0:4]
fcstmonth = sys.argv[3][4:6]
fcstdays  = sys.argv[3][6:8]
fcsthour  = sys.argv[3][8:10]
fcstmins  = sys.argv[3][10:12]

pre_acc   = sys.argv[4]
count     = sys.argv[5]

#GRIB_PATH = '/usr1/wpc_cpgffh/gribs/NEWSe/NEWSe_Min/'
#inityear      = '2018'
#initmonth     = '07'
#initdays      = '12'
#inithour      = '18'
#initmins      = '00'
#fcsthour      = '18'
#fcstmins      = '10'
#pre_acc   = '000500'
#count     = '02'

#Set variable names, load original data, convert to netcdf and save
GRIB_PATH_spec = GRIB_PATH+inityear+initmonth+initdays+'/'
filename       = GRIB_PATH+inityear+initmonth+initdays+'/news-e_ENS_'+count+'_'+inityear+initmonth+initdays+'_'+inithour+initmins+'_'+fcsthour+fcstmins+'.nc'

#filename  = '/usr1/wpc_cpgffh/gribs/MRMS/20180712/20180712-181500.netcdf'
#datetime_beg = pygrib.datetime(int(inityear),int(initmonth),int(initdays),int(fcsthour),int(fcstmins)) - datetime.timedelta(minutes = int(pre_acc[2:4]))
datetime_init = pygrib.datetime(int(inityear),int(initmonth),int(initdays),int(inithour),int(initmins))
datetime_end  = pygrib.datetime(int(fcstyear),int(fcstmonth),int(fcstdays),int(fcsthour),int(fcstmins))

subprocess.call('gunzip '+filename+'.gz',stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'),shell=True)
print filename
f         = Dataset(filename, "a", format="NETCDF4")
subprocess.call('gzip '+filename,stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb'),shell=True)

#Read in data from netcdf file
lat       = (np.array(f.variables['xlat'][:]))*1
lon       = (np.array(f.variables['xlon'][:]))*1
temp      = (np.array(f.variables['rain'][:]))*1
f.close()

#Create regular dlat/dlon grid
[lon_g,lat_g] = np.meshgrid(np.arange(np.round(np.nanmin(lon)-grid_delta,2),np.round(np.nanmax(lon)+grid_delta,2),0.01), \
    np.arange(np.round(np.nanmax(lat)+grid_delta,2),np.round(np.nanmin(lat)-grid_delta,2),-0.01))

#Loop through each NEWSe model, interpolate irregular to regular grid, and save each member individually

for mem in range(0,temp.shape[0]):
    filename_newer = GRIB_PATH+inityear+initmonth+initdays+'/NEWSe_'+inityear+initmonth+initdays+'_i'+inithour+initmins+'_m'+str(mem)+'_f'+fcsthour+fcstmins+'.nc'
    temp_g = griddata((lon.flatten(),lat.flatten()),temp[mem,:,:].flatten(),(lon_g,lat_g),method='linear')*25.4

    temp_g[np.isnan(temp_g)] = -9999.0
    #Make the preexisting netcdf creation function work! Note: vhr is actually vminute!
    filename_new = py2netcdf.py2netcdf_FCST(GRIB_PATH_spec,[np.nanmin(lon_g),np.nanmin(lat_g),np.nanmax(lon_g),np.nanmax(lat_g)],grid_delta,datetime_init, \
        datetime_end,pre_acc,datetime_end.minute,lat_g[::-1,0],lon_g[0,:],temp_g[::-1,:],"A"+pre_acc,'NEWSe')
        
    #stdout=open(os.devnull, 'wb'),stderr=open(os.devnull, 'wb')                
    subprocess.call('mv '+filename_new+' '+filename_newer,shell=True)
    subprocess.call('gzip '+filename_newer,shell=True)
    
subprocess.call('rm -rf '+filename+'.gz',shell=True)
subprocess.call('rm -rf '+filename,shell=True)

#values = [0.05,0.10,0.20,0.50,1.0]  
#my_cmap2 = mpl.cm.get_cmap('cool')
#my_cmap2.set_under('white')    
#plt.figure()
#ax = plt.gca()
##Create polar stereographic Basemap instance.
#m = Basemap(llcrnrlon=latlon_dims[0], llcrnrlat=latlon_dims[1], urcrnrlon=latlon_dims[2],urcrnrlat=latlon_dims[3],resolution='i',projection='merc')
##Draw coastlines, state and country boundaries, edge of map.
#m.drawcoastlines(linewidth=0.5)
#m.drawstates(linewidth=0.5)
#m.drawcountries(linewidth=0.5)
##Draw parallels and meridians
#m.drawparallels(np.arange(0,90,5),labels=[1,0,0,0],fontsize=12,linewidth=0.5) #labels=[left,right,top,bottom]
#m.drawmeridians(np.arange(-180,0,10),labels=[0,0,0,1],fontsize=12,linewidth=0.5) #labels=[left,right,top,bottom]
#props = dict(boxstyle='round', facecolor='wheat', alpha=1)
#cs = m.contourf(lon, lat, temp[0,:,:]*20, latlon=True, levels=values, extend='min', cmap=my_cmap2, antialiased=False, markerstyle='o', vmin=np.min(values),vmax=np.max(values))
#cb = m.colorbar(cs,"right", ticks=values, size="5%", pad="2%", extend='min')
