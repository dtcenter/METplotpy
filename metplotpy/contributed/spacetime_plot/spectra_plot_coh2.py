# ============================*
 # ** Copyright UCAR (c) 2020
 # ** University Corporation for Atmospheric Research (UCAR)
 # ** National Center for Atmospheric Research (NCAR)
 # ** Research Applications Lab (RAL)
 # ** P.O.Box 3000, Boulder, Colorado, 80307-3000, USA
 # ============================*
 
 
 
import numpy as np
from netCDF4 import Dataset
import xarray as xr
import sys, os
import yaml
import metcalcpy.util.read_env_vars_in_config as readconfig

sys.path.append('../../')
import spacetime_plot as stp
"""
This routine reads spectra computed using mjo_cross in spacetime routines.

The output from mjo_cross includes:
STC = [8,nfreq,nwave]
STC[0,:,:] : Power spectrum of x
STC[1,:,:] : Power spectrum of y
STC[2,:,:] : Co-spectrum of x and y
STC[3,:,:] : Quadrature-spectrum of x and y
STC[4,:,:] : Coherence-squared spectrum of x and y
STC[5,:,:] : Phase spectrum of x and y
STC[6,:,:] : Phase angle v1
STC[7,:,:] : Phase angle v2
freq 
wave
number_of_segments
dof
prob
prob_coh2

The output is saved to a netcdf file with save_Spectra and this is what is read in below.
"""


# Read in the YAML config file
# user can use their own, if none specified at the command line,
# use the "default" example YAML config file, spectra_plot_coh2.py
# Using a custom YAML reader so we can use environment variables
config_file = './spectra_plot_coh2.yaml'
#with open(config_file, 'r') as stream:
#    try:
#        config = yaml.load(stream, Loader=yaml.FullLoader)
#    except yaml.YAMLError as exc:
#        print(exc)

config_dict = readconfig.parse_config(config_file)

# Retrieve settings from config file
pathdata = config_dict['pathdata'][0]
plotpath = config_dict['plotpath'][0]


# plot layout parameters
flim = 0.5  # maximum frequency in cpd for plotting
nWavePlt = 20  # maximum wavenumber for plotting
contourmin = 0.1  # contour minimum
contourmax = 0.8  # contour maximum
contourspace = 0.1  # contour spacing
N = [1, 2]  # wave modes for plotting
source = ""

symmetry = "symm"      #("symm", "asymm", "latband")
# filenames = ['ERAI_TRMM_P_symm_1spd', 'FV3_TRMM_P_symm_1spd_fhr00', 'FV3_TRMM_P_symm_1spd_fhr24',
#              'ERAI_P_D850_symm_1spd', 'FV3_P_D850_symm_1spd_fhr00', 'FV3_P_D850_symm_1spd_fhr24',
#              'ERAI_P_D200_symm_1spd', 'FV3_P_D200_symm_1spd_fhr00', 'FV3_P_D200_symm_1spd_fhr24']
filenames = ['ERAI_TRMM_P_symm_2spd',
             'ERAI_P_D850_symm_2spd',
             'ERAI_P_D200_symm_2spd']
# vars1 = ['ERAI P', 'ERAI P', 'FV3 P FH00', 'FV3 P FH24', 'ERAI P', 'FV3 P FH00', 'FV3 P FH24']
vars1 = ['ERAI', 'ERAI P', 'ERAI P']
# vars2 = ['TRMM', 'TRMM', 'TRMM', 'ERAI D850', 'FV3 D850 FH00', 'FV3 D850 FH24', 'ERAI D200', 'FV3 D200 FH00', 'FV3 D200 FH24']
vars2 = ['TRMM', 'D850', 'D200']
nplot = len(vars1)

pp = 0

while pp < nplot:

    # read data from file
    var1 = vars1[pp]
    var2 = vars2[pp]
    input_fname = 'SpaceTimeSpectra_' + filenames[pp] + '.nc'
    full_input_file = os.path.join(pathdata, input_fname)
    # fin = xr.open_dataset(pathdata + 'SpaceTimeSpectra_' + filenames[pp] + '.nc')
    fin = xr.open_dataset(full_input_file)
    STC = fin['STC'][:, :, :]
    wnum = fin['wnum']
    freq = fin['freq']

    ifreq = np.where((freq[:] >= 0) & (freq[:] <= flim))
    iwave = np.where(abs(wnum[:]) <= nWavePlt)

    STC[:, freq[:] == 0, :] = 0.
    STC = STC.sel(wnum=slice(-nWavePlt, nWavePlt))
    STC = STC.sel(freq=slice(0, flim))
    coh2 = np.squeeze(STC[4, :, :])
    phs1 = np.squeeze(STC[6, :, :])
    phs2 = np.squeeze(STC[7, :, :])
    phs1.where(coh2 <= contourmin, drop=True)
    phs2.where(coh2 <= contourmin, drop=True)
    pow1 = np.squeeze(STC[0, :, :])
    pow2 = np.squeeze(STC[1, :, :])
    pow1.where(pow1 <= 0, drop=True)
    pow2.where(pow2 <= 0, drop=True)

    if pp == 0:
        Coh2 = np.empty([nplot, len(freq[ifreq]), len(wnum[iwave])])
        Phs1 = np.empty([nplot, len(freq[ifreq]), len(wnum[iwave])])
        Phs2 = np.empty([nplot, len(freq[ifreq]), len(wnum[iwave])])
        Pow1 = np.empty([nplot, len(freq[ifreq]), len(wnum[iwave])])
        Pow2 = np.empty([nplot, len(freq[ifreq]), len(wnum[iwave])])
        k = wnum[iwave]
        w = freq[ifreq]

    Coh2[pp, :, :] = coh2
    Phs1[pp, :, :] = phs1
    Phs2[pp, :, :] = phs2
    Pow1[pp, :, :] = np.log10(pow1)
    Pow2[pp, :, :] = np.log10(pow2)

    phstmp = Phs1
    phstmp = np.square(Phs1) + np.square(Phs2)
    phstmp = np.where(phstmp == 0, np.nan, phstmp)
    scl_one = np.sqrt(1 / phstmp)
    Phs1 = scl_one * Phs1
    Phs2 = scl_one * Phs2

    pp += 1



# plot coherence
print("plotpath ",plotpath)
stp.plot_coherence(Coh2, Phs1, Phs2, symmetry, source, vars1, vars2, plotpath, flim, 20, contourmin, contourmax,
                   contourspace, nplot, N)

exit()
