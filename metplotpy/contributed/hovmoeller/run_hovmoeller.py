import numpy as np
import xarray as xr
import sys

sys.path.append('../../')
"""
local scripts, if loading from a different directory include that with a '.' between
directory name and script name
"""
from metplotpy.contributed.hovmoeller.hovmoeller_calc import lat_avg
from metplotpy.contributed.hovmoeller.hovmoeller_plotly import hovmoeller
plotpath = '../plots/hovmoeller/'

"""
Parameters to set for the Hovmoeller diagrams.
"""
datestrt = '2016-01-01'  # plot start date, format: yyyy-mm-dd
datelast = '2016-03-31'  # plot end date, format: yyyy-mm-dd
latMax = 5.  # maximum latitude for the average
latMin = -5.  # minimum latitude for the average

print("reading data from file:")

ds = xr.open_dataset('/data/mgehne/ERAI/MetricsObs/precip.erai.sfc.1p5.2x.1979-2016.nc')
A = ds.precip
lonA = ds.lon
print("extracting time period:")
A = A.sel(time=slice(datestrt, datelast))
timeA = ds.time.sel(time=slice(datestrt, datelast))
ds.close()

print("average over latitude band:")
A = A * 1000 / 4
A.attrs['units'] = 'mm/day'
A = lat_avg(A, latmin=latMin, latmax=latMax)

print("plot hovmoeller diagram:")
spd = 2  # number of obs per day
source = "ERAI"  # data source
var = "precip"  # variable to plot
lev = ""   # level
# plot using user set contour levels
contourmin = 0.2  # contour minimum
contourmax = 1.2  # contour maximum
contourspace = 0.2  # contour spacing
hovmoeller(A, lonA, timeA, datestrt, datelast, plotpath, latMin, latMax, spd, source, var, lev,
           contourmin, contourmax, contourspace)
# plot using default contour levels for this variable
# hovmoeller(A, lonA, timeA, datestrt, datelast, plotpath, latMin, latMax, spd, source, var, lev)

