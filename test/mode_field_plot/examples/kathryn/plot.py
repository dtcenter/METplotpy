import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import netCDF4 as nc

# Load the NetCDF file
ds = nc.Dataset('mode_KWBC_APCP_24_vs_IMERG_APCP_24_240000L_20240204_000000V_240000A_R1_T2_obj.nc')

# Load variables
data = ds.variables['fcst_raw'][:]
lat = ds.variables['lat'][:]
lon = ds.variables['lon'][:]

# Mask near-zero values
data_masked = np.ma.masked_less_equal(data, 0.0)

# Convert longitudes from 0-360 to -180 to 180
lon = np.where(lon > 180, lon - 360, lon)

# Sort by longitude to ensure correct ordering
sort_idx = np.argsort(lon)
lon = lon[sort_idx]
data_masked = data_masked[:, sort_idx]

# Set colormap - use set_under for values below vmin (white for zero values)
cmap = plt.cm.jet.copy()
cmap.set_under('white')

# Set up the plot
fig, ax = plt.subplots(figsize=(14, 4),
                        subplot_kw={'projection': ccrs.PlateCarree()})

# Set ocean background to white
ax.set_facecolor('white')

# Plot the data
mesh = ax.pcolormesh(lon, lat, data_masked,
                     cmap=cmap,
                     vmin=0.01,
                     vmax=25,
                     transform=ccrs.PlateCarree())

# Limit to tropical band
ax.set_extent([-180, 180, -20, 20], crs=ccrs.PlateCarree())

# Add land feature in grey
ax.add_feature(cfeature.LAND, facecolor='lightgrey', zorder=0)

# Colorbar
plt.colorbar(mesh, ax=ax, label='APCP_24 (mm)',
             shrink=0.5,
             aspect=20,
             pad=0.05)

# Add coastlines and borders
ax.add_feature(cfeature.COASTLINE, linewidth=0.5, zorder=2)
ax.add_feature(cfeature.BORDERS, linewidth=0.5, zorder=2)

# Add gridlines - labels on left and bottom only
gl = ax.gridlines(draw_labels=True, linewidth=0.5, color='gray', alpha=0.5)
gl.top_labels = False    # remove top labels
gl.right_labels = False  # remove right labels

plt.title('APCP_24')
plt.tight_layout()
plt.savefig('apcp_mask_noaa.png', dpi=300, bbox_inches='tight')
plt.show()
