#
# input file from grid diag tool
grid_diag_out = '/glade/p/ral/jntp/AF/cloud_vx/grid_diag/GridDiag/grid_diag_out_GFS_2020060800-2020061500_f09-09.nc'
file_out = 'grid_diag_out_cdf_GFS_2020060800-2020061500_f09-09.png'
model_title = 'GFS'
obs_title = 'GOES-16'
#
# Relevant modules
from netCDF4 import Dataset
import matplotlib.pyplot as plt
import numpy as np
#
print(' ')
print('Plotting CDFs for model and observational data')
#
# Get variables for CDF
fgd = Dataset(grid_diag_out, 'r', format = 'NETCDF4')
hist_model = fgd.variables['hist_SBT1613_L0'][:]
hist_obser = fgd.variables['hist_tb_g16_L0'][:]
x_model = fgd.variables['SBT1613_L0_mid'][:]
x_obser = fgd.variables['tb_g16_L0_mid'][:]
fgd.close()
#
# Convert histogram data to CDF
cdf_model = np.cumsum(hist_model / np.sum(hist_model))
cdf_obser = np.cumsum(hist_obser / np.sum(hist_obser))
#
print('Plotting results')
fig, ax = plt.subplots(figsize = (6, 4))
#
ax.plot(x_model, cdf_model, linewidth = 2, color = (0.85, 0.35, 0.35))
ax.plot(x_obser, cdf_obser, linewidth = 2, color = (0.35, 0.35, 0.85))
#
# Other plot formatting
major_ticks = np.arange(0, 1.1, 0.1)
ax.set_yticks(major_ticks)
major_ticks = np.arange(200, 310, 10)
ax.set_xticks(major_ticks)
plt.axis([190, 310, 0, 1])
ax.grid(True, axis = 'both', linestyle = ':', color = (0.7, 0.7, 0.7))
plt.xlabel('Brightness Temperature (K)', fontweight = 'bold')
plt.ylabel('Cumulative Distribution Function', fontweight = 'bold')
plt.legend((model_title, obs_title), loc = 'upper left')
fig.savefig(file_out, dpi = 300)
#
print(' ')
#
