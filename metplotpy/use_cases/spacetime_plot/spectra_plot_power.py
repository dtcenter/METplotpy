import Ngl as ngl
import numpy as np
from diagnostics import spacetime_plot as stp
import string
import sys
import xarray as xr

sys.path.append('../../')

pathdata = './'
plotpath = './'

# plot layout parameters
flim = 0.5  # maximum frequency in cpd for plotting
nWavePlt = 15  # maximum wavenumber for plotting
contourmin = -10  # contour minimum
contourmax = -8.  # contour maximum
contourspace = 0.2  # contour spacing
N = [1, 2]  # wave modes for plotting
source = "ERAI"
var1 = "precip"
spd = 2

symmetry = ("symm", "asymm", "latband")
nplot = len(symmetry)
pp = 0

while pp < nplot:

    # read data from file
    fin = xr.open_dataset(pathdata + 'SpaceTimeSpectra_' + filenames[pp] + '.nc')
    STC = fin['STC'][:, :, :]
    wnum = fin['wnum']
    freq = fin['freq']

    ifreq = np.where((freq[:] >= 0) & (freq[:] <= flim))
    iwave = np.where(abs(wnum[:]) <= nWavePlt)

    STC[:, freq[:] == 0, :] = 0.
    STC = STC.sel(wnum=slice(-nWavePlt, nWavePlt))
    STC = STC.sel(freq=slice(0, flim))
    pow1 = np.squeeze(STC[0, :, :])
    pow2 = np.squeeze(STC[1, :, :])
    pow1.where(pow1 <= 0, drop=True)
    pow2.where(pow2 <= 0, drop=True)

    if pp == 0:
        Pow1 = np.empty([nplot, len(freq[ifreq]), len(wnum[iwave])])
        Pow2 = np.empty([nplot, len(freq[ifreq]), len(wnum[iwave])])

    Pow1[pp, :, :] = np.log10(pow1)
    Pow2[pp, :, :] = np.log10(pow2)


    pp += 1

stp.plot_power(Pow1, symmetry, source, var1, plotpath, flim, nWavePlt, contourmin,contourmax,contourspace,nplot,N)
exit()
