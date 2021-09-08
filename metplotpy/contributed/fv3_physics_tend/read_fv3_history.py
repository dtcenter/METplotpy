import argparse
import cartopy
import cartopy.feature as cfeature
import datetime
import matplotlib.pyplot as plt
from metpy.units import units
import numpy as np
import os
import pdb
import st4
import sys
import xarray

"""
Plot physics tendencies:
dt3dt_cnvgwd dt3dt_deepcnv dt3dt_lw dt3dt_mp dt3dt_orogwd dt3dt_pbl dt3dt_rdamp dt3dt_shalcnv dt3dt_sw

The non-physics tendencies:
'dt3dt_nophys'

The temperature state to get the total tendency change (difference between t = 12 and t = 1, where t is the output timestep):
’tmp’

"""


tmp_tendencies = ['dt3dt_cnvgwd','dt3dt_deepcnv','dt3dt_lw','dt3dt_mp','dt3dt_orogwd','dt3dt_pbl','dt3dt_rdamp','dt3dt_shalcnv','dt3dt_sw']
q_tendencies = ['dq3dt_deepcnv','dq3dt_mp','dq3dt_pbl','dq3dt_shalcnv']
u_tendencies = ['du3dt_cnvgwd','du3dt_deepcnv','du3dt_orogwd','du3dt_pbl','du3dt_rdamp','du3dt_shalcnv']
v_tendencies = ['dv3dt_cnvgwd','dv3dt_deepcnv','dv3dt_orogwd','dv3dt_pbl','dv3dt_rdamp','dv3dt_shalcnv']
physics_tendencies = q_tendencies
nonphysics_tendencies = [f'd{var}3dt_nophys' for var in ["t","q","u","v"]]


# =============Arguments===================
parser = argparse.ArgumentParser(description = "Horizontal plot of FV3 diagnostic tendency", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
# ==========Mandatory Arguments===================
parser.add_argument("ifile", type=argparse.FileType("r"), help="FV3 history file")
parser.add_argument("gfile", type=argparse.FileType("r"), help="FV3 grid spec file")
parser.add_argument("fill", type=str, choices = tmp_tendencies + q_tendencies + u_tendencies + v_tendencies + nonphysics_tendencies + ["dtmp","tmp", "resid"], help='filled contour variable with 2 spatial dims and optional time and vertical dims.')
# ==========Optional Arguments===================
parser.add_argument("-c", "--contourf", action='store_true', help="use contourf (bilinear interp) instead of pcolormesh (blocky-looking, but fast)")
parser.add_argument("-d", "--debug", action='store_true')
parser.add_argument("--dtsec", type=float, default=300, help="model time step in seconds")
parser.add_argument("-e", "--extent", nargs=4, type=float, default=None, help="minlon maxlon minlat maxlat")
parser.add_argument("-l", "--levels", type=float, nargs="+", help="filled contour levels", default=None)
parser.add_argument("--ncols", type=int, default=None, help="number of columns")
parser.add_argument("-o", "--ofile", type=str, help="name of output image file")
parser.add_argument("-p", "--pfull", nargs='*', type=float, default=None, help="pressure level(s) to plot")
parser.add_argument("-s", "--shp", type=argparse.FileType("r"), default=None, help="subdomain shape file")

args = parser.parse_args()
gfile      = args.gfile
ifile      = args.ifile
fill       = args.fill
contourf   = args.contourf
debug      = args.debug
dt         = args.dtsec * units.seconds
extent     = args.extent
levels     = args.levels
ncols      = args.ncols
ofile      = args.ofile
pfull      = args.pfull
shp        = args.shp

if debug:
    print(args)

gds  = xarray.open_dataset(gfile.name)
lon  = gds["grid_lont"]
lat  = gds["grid_latt"]
area = gds["area"]
# Derive SW corner of cell from cell centers
# pcolormesh expects this.
dlat = lat - np.roll(lat, 1, axis=0)
if (dlat.ndim == 1):
    dlat[0] = dlat[1] # Replace element 0 deltas that wrapped domain with element 1.
if (dlat.ndim == 2):
    dlat[0,:] = dlat[1,:] # Replace row 0 deltas that wrapped domain with row 1.
dlon = lon - np.roll(lon, 1, axis=lon.ndim-1)
if (lon.ndim == 1):
    dlon[0] = dlon[1] # Replace element 0 deltas that wrapped domain with element 1.
if (lon.ndim == 2):
    dlon[:,0] = dlon[:,1] # Replace column 0 deltas that wrapped domain with column 1.
if debug:
    print(dlat)
    print(dlon)
SWlat = lat - dlat/2
SWlon = lon - dlon/2

if ofile is None:
    ofile = f"{fill}.png"
else:
    ofile = args.ofile


print("creating figure")
fig = plt.figure()

# Open input file
if debug:
    print(f"About to open {ifile}")
fv3xr = xarray.open_dataset(ifile.name)
if fill not in fv3xr.variables and fill not in ["dtmp","resid"]:
    print("variable "+ fill + " not found")
    print("choices:", fv3xr.variables.keys())
    sys.exit(1)

if shp:
    # Add shapefile name to output filename
    shapename, ext = os.path.splitext(os.path.basename(shp.name))
    root, ext = os.path.splitext(ofile)
    ofile = root + f".{shapename}" + ext

# Position color bar
cax = fig.add_axes([0.3333, 0.065, 0.33333, 0.02])

stride = 1 # set higher for debugging. it is faster.
title_fontsize="x-small"

tmp = fv3xr["tmp"].metpy.quantify()
lasttime = tmp.time[-1] # last time used to slice tendency Dataset

# Grab Dataset with physics and non-physics tendencies at last time
#all_tend = fv3xr[tmp_tendencies + nonphysics_tendencies].sel(time = lasttime)
all_tend = fv3xr[tmp_tendencies].sel(time = lasttime)
# Stack variables along "tendency" axis of new array
all_tend = all_tend.to_array(dim="tendency")
# Units of tendencies are K/s averaged over number of time steps within first forecast hour.
all_tend *= units["K/s"] # to_array() got rid of units. restore them.
numdt = tmp.time.size
# Multiply by time step and number of time steps
all_tend *= dt * numdt
# Sum along new axis.
all_tend_sum = all_tend.sum(dim="tendency")

print(f"change in temperature")
dtmp = tmp.sel(time = lasttime) - tmp.isel(time=0)
dtmp.attrs["long_name"] = f"change in {tmp.attrs['long_name']}"
resid = all_tend_sum - dtmp
resid.attrs["long_name"] = "residual"

if fill == "dtmp":
    dafill = dtmp
elif fill == "resid":
    dafill = resid
else:
    print(f"reading {fill}")
    dafill = fv3xr[fill]
    print(f"grabbing last time")
    dafill = dafill.isel(time = -1)

if shp:
    # mask points outside shape
    mask = st4.pts_in_shp(lat.values, lon.values, shp.name, debug=debug)
    dafill = dafill.where(mask)

# append time to title and output filename
title = f'{dafill.attrs["long_name"]} ({fill})  {lasttime.item()}'
root, ext = os.path.splitext(ofile)
ofile = root + f".{lasttime.dt.strftime('%Y%m%d_%H%M%S').item()}" + ext

# static parts of title and output file name
plt.suptitle(title, wrap=True)
root, ext = os.path.splitext(ofile)

myslices = dafill.sel(pfull=pfull, method="nearest", tolerance=50.)
# Use percentiles so color scale isn't affected by one or two extreme values.
vmin,vmax = myslices.metpy.dequantify().quantile([0.001, 0.999], skipna=True)

if not ncols:
    # Default # of cols is square root of # of panels
    ncols = int(np.ceil(np.sqrt(len(myslices))))

nrows = int(np.ceil(len(myslices)/ncols))
for n, myslice in enumerate(myslices):
    print(f"creating GeoAxes {nrows} {ncols} {n+1}")
    # central lon/lat from https://github.com/NOAA-EMC/regional_workflow/blob/release/public-v1/ush/Python/plot_allvars.py
    ax = plt.subplot(nrows, ncols, n+1, projection=cartopy.crs.LambertConformal(central_longitude=-97.6, central_latitude=35.4, standard_parallels=None))
    ax.add_feature(cfeature.COASTLINE.with_scale('50m'), linewidth=0.3)
    ax.add_feature(cfeature.BORDERS.with_scale('50m'), linewidth=0.3)
    ax.add_feature(cfeature.STATES.with_scale('50m'), linewidth=0.1)
    ax.add_feature(cfeature.LAKES.with_scale('50m'), edgecolor='k', linewidth=0.25, facecolor='k', alpha=0.1)

    # Append vertical level to title 
    title = f' {myslice.pfull.item():.0f} {myslice.pfull.attrs["units"]}'
    ax.set_title(title, fontsize=title_fontsize)

    if contourf: 
        cfill   = ax.contourf(lon[::stride,::stride], lat[::stride,::stride], myslice[::stride,::stride], 
                transform=cartopy.crs.PlateCarree(), vmin=vmin, vmax=vmax )
    else:
        cfill   = ax.pcolormesh(SWlon[::stride,::stride], SWlat[::stride,::stride], myslice[::stride,::stride], 
                transform=cartopy.crs.PlateCarree(), vmin=vmin, vmax=vmax )

    if extent:
        if debug: print("use requested extent", extent)
        ax.set_extent(extent)

# add colorbar
cb = plt.colorbar(mappable=cfill, cax=cax, orientation='horizontal')
cb.set_label(dafill.metpy.units, fontsize=6)
cb.outline.set_linewidth(0.5)
cb.ax.tick_params(labelsize=4.5)
cb.ax.xaxis.get_offset_text().set(size=5)

fineprint  = os.path.realpath(ifile.name)
if shp:
    fineprint += f"\nshape {shp.name}"
fineprint += f"\nextent {extent}"
fineprint += "\ncreated "+str(datetime.datetime.now(tz=None)).split('.')[0]
fineprint_obj = plt.annotate(s=fineprint, xy=(5,5), xycoords='figure pixels', fontsize=4)

plt.savefig(ofile, dpi=150)
print('created ' + os.path.realpath(ofile))
