import os
import numpy as np
from netCDF4 import Dataset

import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm
## Added for logarithmic color scale
import matplotlib.colors as colors

#grid_diag_out = '/glade/p/ral/jntp/AF/cloud_vx/grid_diag/GridDiag/grid_diag_out_GFS_20200608-15_f00-21.nc'
#grid_diag_out = '/glade/p/ral/jntp/AF/cloud_vx/grid_diag/GridDiag/grid_diag_out_GFS_20200608-15_f24-45.nc'
#grid_diag_out = '/glade/p/ral/jntp/AF/cloud_vx/grid_diag/GridDiag/grid_diag_out_GFS_20200608-15_f48-69.nc'
#grid_diag_out = '/glade/p/ral/jntp/AF/cloud_vx/grid_diag/GridDiag/grid_diag_out_GFS_20200608-15_f00-21_600bins.nc'
#grid_diag_out = '/glade/p/ral/jntp/AF/cloud_vx/grid_diag/GridDiag/grid_diag_out_GFS_20200608-15_f00-21_50bins.nc'
grid_diag_out = '/glade/p/ral/jntp/AF/cloud_vx/grid_diag/GridDiag/grid_diag_out_GFS_2020060800-2020061500_f03-24_50bins.nc'

file_id = Dataset(grid_diag_out, 'r')
hist_gfs_obs = file_id.variables['hist_SBT1613_L0_tb_g16_L0'][:]
gfs_ctr = file_id.variables['SBT1613_L0_mid'][:]
obs_ctr = file_id.variables['tb_g16_L0_mid'][:]
file_id.close()

n_total = np.sum(hist_gfs_obs)

obs_mesh, gfs_mesh = np.meshgrid(obs_ctr, gfs_ctr)

gfs_count = np.sum(hist_gfs_obs, axis=0)
gfs_mean = np.sum(
    gfs_mesh * hist_gfs_obs, axis=0) \
    / gfs_count

# plot
#data_max=100000
data_max=750000
#data_max=25000
cmap = plt.get_cmap('gist_ncar')
levels = np.linspace(0.0, data_max, 51)
norm = BoundaryNorm(levels, ncolors=cmap.N, clip=True)
##hist = plt.pcolormesh(obs_mesh, gfs_mesh,
##    hist_gfs_obs,
##    cmap=cmap, norm=norm)
hist_gfs_obs_norm = 100*hist_gfs_obs / np.sum(np.sum(hist_gfs_obs))
hist = plt.pcolormesh(obs_mesh, gfs_mesh,
    hist_gfs_obs_norm,
    cmap = cmap, norm = colors.LogNorm(vmin = 0.00001, vmax = 0.5))
##
# hist_gfs_obs / n_total
ax = plt.gca()

## Increased linewidth from 1 to 2
ax.plot(obs_ctr, gfs_mean, linewidth=2)
## Add grid lines 
ax.grid(True, which = 'major', axis = 'both', linestyle = '--', 
        color = (0.5, 0.5, 0.5))
##
ax.set_xlabel('Obs Tb (K)')
ax.set_ylabel('GFS Tb (K)')
plt.xlim(195, 305) ## Switched to 195-305 from 170-320
plt.ylim(195, 305) ## Switched to 195-305 from 170-320
plt.title('MET GridDiag 2D Histogram')
##cbar = plt.colorbar(
##    hist, ticks = np.linspace(0.0, data_max, 11))
cbar = plt.colorbar()
cbar.ax.set_ylabel('Probability (%)')
##
#plt.savefig('grid_diag_out_GFS_20200608-15_f00-21.png', dpi=300)
#plt.savefig('grid_diag_out_GFS_20200608-15_f24-45.png', dpi=300)
#plt.savefig('grid_diag_out_GFS_20200608-15_f48-69.png', dpi=300)
#plt.savefig('grid_diag_out_GFS_20200608-15_f00-21_600bins.png', dpi=300)
plt.savefig('grid_diag_out_2dhist_GFS_2020060800-2020061500_f03-24_50bins.png', dpi=300)
