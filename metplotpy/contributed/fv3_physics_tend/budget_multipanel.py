import xarray as xr
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

import cartopy.feature as cfeature
import cartopy.crs as ccrs
import cartopy.mpl.ticker as cticker
from datetime import datetime
import cftime
from fv3_planview import desc



"""
"""

path  = '/glade/scratch/mwong/RRFS/sample_cases/CONUS_25km_GFSv15p2/2019050412/'
fname = 'fv3_history.nc'

terms = ['dt3dt_lw', 'dt3dt_sw', 'dt3dt_pbl', 'dt3dt_deepcnv', 'dt3dt_shalcnv', 'dt3dt_mp', 
         'dt3dt_orogwd','dt3dt_rdamp', 'dt3dt_congwd', 'dt3dt_nophys']


ds = xr.open_dataset(path+fname)
gr = xr.open_dataset(path+'grid_spec.nc')
min_lat = 20.# gr['grid_latt'].min()
max_lat = 55.#gr['grid_latt'].max()
min_lon = -130. #gr['grid_lont'].min()-360.
max_lon = -60. #gr['grid_lont'].max()-360.

tinterval = 3600. # diagnostic output interval (s)

lev = 40 
tstep = 13   # ending time step (where 0 is 1h) 
nh    = 3   # number of hours
nrows = 3
ncols = 4


# Load total tendency
var_init = ds['tmp_i']

if ( tstep - nh < -1 ):
    print("Average period exceeds starting time. Stop.")
    exit() 
if ( tstep - nh == -1 ):
    dtmp = ds['tmp'][tstep,lev,:,:] - var_init[lev,:,:]
else:
    dtmp = ds['tmp'][tstep,lev,:,:] - ds['tmp'][tstep-nh,lev,:,:]


# Compute (accumulated) tendencies over requested period
# - dynamics tendency: already accumulated over entire forecast integration (in units per second)
# - physics tendencies: averaged over each diagnostic output interval (in units per second)
for i, variable in enumerate(terms[:-1]):
    for t in np.arange(tstep-nh+1,tstep+1):
       data=ds[variable][t,lev,:,:]*tinterval   #get tendency over the output interval (1h)
       # accumulate physics tendencies over period of interest
       if ( t == tstep-nh+1): 
          ds['temp'] = data 
       else:
          ds['temp'] = ds['temp'] + data 
       strname = variable + "_p" # p for period  
       ds[strname] = ds['temp']

# nophys is already in accumulated form
#ds['dt3dt_nophys_p'] = (ds['dt3dt_nophys'][tstep,lev,:,:] - ds['dt3dt_nophys'][tstep-nh,lev,:,:])*tinterval
strname = terms[-1] + "_p" 
variable = terms[-1]
ds[strname] = (ds[variable][tstep,lev,:,:] - ds[variable][tstep-nh,lev,:,:])*tinterval


# summing up the tendency terms
for i, variable in enumerate(terms):
    strname = variable + "_p"
    if ( i==0):
       ds['sum_of_terms'] = ds[strname] 
    else:
       ds['sum_of_terms'] = ds['sum_of_terms'] + ds[strname]


print(f"sum_of_terms {desc(ds['sum_of_terms'])}")

# Define the contour levels to use in plt.contourf
#clevs=np.linspace(dtmp.min(), dtmp.max(), 100)
clevs=np.linspace(-2.0, 2.0, 100)

fig, axs = plt.subplots(nrows=nrows,ncols=ncols,
                        subplot_kw={'projection': ccrs.PlateCarree()},
                        figsize=(14,8.5))

# Set the axes using the specified map projection
axs=axs.flatten()

for i,variable in enumerate(terms):

    # Choose the budget term
    strname =variable + "_p"
    data=ds[strname]
    print(f"{strname} {desc(data)}")

    # Make a filled contour plot
    cs=axs[i].contourf(gr['grid_lont'], gr['grid_latt'], data, clevs,
            transform = ccrs.PlateCarree(),cmap='Spectral',extend='both')

    # Add coastlines
    axs[i].coastlines()

    # Title each subplot
    axs[i].set_title(variable)

    # Define the xticks for longitude
    if ( i >= 8):
        axs[i].set_xticks(np.arange(min_lon,max_lon,15), crs=ccrs.PlateCarree())
        lon_formatter = cticker.LongitudeFormatter()
        axs[i].xaxis.set_major_formatter(lon_formatter)

    # Define the yticks for latitude
    if ( i == 0 or i == 4 or i == 8 ):
        axs[i].set_yticks(np.arange(min_lat,max_lat,10.), crs=ccrs.PlateCarree())
        lat_formatter = cticker.LatitudeFormatter()
        axs[i].yaxis.set_major_formatter(lat_formatter)

        # Set last plot
        last_i = i

"""
 Plot total tendency
"""
i = last_i+1 
data = dtmp
print(f"dtmp {desc(data)}")
cs = axs[i].contourf(gr['grid_lont'], gr['grid_latt'], data, clevs,
                    transform = ccrs.PlateCarree(),cmap='Spectral',extend='both')
# Add coastlines
axs[i].coastlines()

# Title each subplot
axs[i].set_title("Total tendency")

# Define the yticks for latitude
axs[i].set_xticks(np.arange(min_lon,max_lon,15), crs=ccrs.PlateCarree())
lon_formatter = cticker.LongitudeFormatter()
axs[i].xaxis.set_major_formatter(lon_formatter)
last_i = i

"""
 Plot residual 
"""
i = i + 1
data = ds['sum_of_terms']
print(f"dtmp-data {desc(dtmp-data)}")
csr = axs[i].contourf(gr['grid_lont'], gr['grid_latt'], dtmp-data, 
                    transform = ccrs.PlateCarree(),cmap='Spectral',extend='both')

# Add coastlines
axs[i].coastlines()

# Title each subplot
axs[i].set_title("Residual")

# Define the yticks for latitude
axs[i].set_xticks(np.arange(min_lon,max_lon,15), crs=ccrs.PlateCarree())
lon_formatter = cticker.LongitudeFormatter()
axs[i].xaxis.set_major_formatter(lon_formatter)
last_i = i


# Get rid of any extra panels
for i in np.arange(last_i+1,nrows*ncols): 
    fig.delaxes(axs[i])


# Adjust the location of the subplots on the page to make room for the colorbar
fig.subplots_adjust(bottom=0.25, top=0.9, left=0.1, right=0.9,
                    wspace=0.02, hspace=0.02)

# Add a colorbar axis at the bottom of the graph
cbar_ax = fig.add_axes([0.2, 0.2, 0.6, 0.02])

# Draw the colorbar
cbar=fig.colorbar(cs, cax=cbar_ax,orientation='horizontal')
cb = fig.colorbar(csr,ax=axs[i])

# Add a big title at the top
plt.suptitle('Temperature tendencies (K/h) at reference pressure '+str(round(ds['pfull'][lev].item(0)))+ 'mb')

plt.show()
#plt.savefig("Temperature_budget.pdf")
