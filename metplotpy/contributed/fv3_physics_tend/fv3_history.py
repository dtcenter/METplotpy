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
parser.add_argument("-d", "--debug", action='store_true')
parser.add_argument("--dtsec", type=float, default=300, help="model time step in seconds")
parser.add_argument("-e", "--extent", nargs=4, type=float, default=None, help="minlon maxlon minlat maxlat")
parser.add_argument("-l", "--levels", type=float, nargs="+", help="filled contour levels", default=None)
parser.add_argument("--ncols", type=int, default=None, help="number of columns")
parser.add_argument("-o", "--ofile", type=str, help="name of output image file")
parser.add_argument("-p", "--pfull", nargs='+', type=float, default=[500], help="pressure level(s) to plot")
parser.add_argument("-s", "--shp", type=str, default=None, help="shape file directory for mask")

args = parser.parse_args()
gfile      = args.gfile
ifile      = args.ifile
fill       = args.fill
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
lont  = gds["grid_lont"]
latt  = gds["grid_latt"]
area = gds["area"]

if ofile is None:
    ofile = f"{fill}.png"
else:
    ofile = args.ofile


# Open input file
if debug:
    print(f"About to open {ifile}")
fv3ds = xarray.open_dataset(ifile.name)
if fill not in fv3ds.variables and fill not in ["dtmp","resid"]:
    print("variable "+ fill + " not found")
    print("choices:", fv3ds.variables.keys())
    sys.exit(1)

fv3ds = fv3ds.assign_coords(lont = lont, latt=latt)

tmp = fv3ds["tmp"].metpy.quantify()
lasttime = tmp.time[-1] # last time used to slice tendency Dataset

# Grab Dataset with physics and non-physics tendencies at last time
#all_tend = fv3ds[tmp_tendencies + nonphysics_tendencies].sel(time = lasttime)
all_tend = fv3ds[tmp_tendencies].sel(time = lasttime)
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
    dafill = fv3ds[fill]
    print(f"grabbing last time")
    dafill = dafill.isel(time = -1)

if shp:
    # Add shapefile name to output filename
    shapename = os.path.basename(shp)
    root, ext = os.path.splitext(ofile)
    ofile = root + f".{shapename}" + ext

    # mask points outside shape
    mask = st4.pts_in_shp(latt.values, lont.values, shp, debug=debug)
    mask = xarray.DataArray(mask, coords=[dafill.grid_yt, dafill.grid_xt])
    dafill = dafill.where(mask, drop=True)

dafill = dafill.sel(pfull=pfull, method="nearest", tolerance=50.)
if not ncols:
    # Default # of cols is square root of # of panels
    ncols = int(np.ceil(np.sqrt(len(dafill))))

nrows = int(np.ceil(len(dafill)/ncols))


# TODO: get LambertConformal to show any data (it is just a white screen)
# central lon/lat from https://github.com/NOAA-EMC/regional_workflow/blob/release/public-v1/ush/Python/plot_allvars.py
subplot_kws = dict(projection=cartopy.crs.LambertConformal(central_longitude=-97.6, central_latitude=35.4, standard_parallels=None))
subplot_kws = dict(projection=cartopy.crs.PlateCarree())

print("creating figure")
p = dafill.plot.pcolormesh(x="lont", y="latt", col="pfull", col_wrap=ncols, robust=True, infer_intervals=True, subplot_kws=subplot_kws) # robust (bool, optional) – If True and vmin or vmax are absent, the colormap range is computed with 2nd and 98th percentiles instead of the extreme values
for ax in p.axes.flat:
    ax.add_feature(cfeature.COASTLINE.with_scale('50m'), linewidth=0.3)
    ax.add_feature(cfeature.BORDERS.with_scale('50m'), linewidth=0.3)
    ax.add_feature(cfeature.STATES.with_scale('50m'), linewidth=0.1)
    ax.add_feature(cfeature.LAKES.with_scale('50m'), edgecolor='k', linewidth=0.25, facecolor='k', alpha=0.1)
    if extent:
        if debug: print("requested extent", extent)
        ax.set_extent(extent)
    else:
        # If extent is not provided, use extent of unmasked data.
        ax.set_extent([dafill.lont.min(), dafill.lont.max(), dafill.latt.min(), dafill.latt.max()])

# append time to title and output filename
title = f'{dafill.attrs["long_name"]} ({fill})  {lasttime.item()}'
root, ext = os.path.splitext(ofile)
ofile = root + f".{lasttime.dt.strftime('%Y%m%d_%H%M%S').item()}" + ext

# static parts of title and output file name
plt.suptitle(title, wrap=True)


# TODO get fineprint to show again (with FacetGrid)
fineprint  = os.path.realpath(ifile.name)
if shp:
    fineprint += f"\nmask: {shp}"
fineprint += f"\nextent: {extent}"
fineprint += "\ncreated "+str(datetime.datetime.now(tz=None)).split('.')[0]
fineprint_obj = plt.annotate(text=fineprint, xy=(0.01,0.01), xycoords='figure fraction', fontsize=10)


plt.savefig(ofile, dpi=150)
print('created ' + os.path.realpath(ofile))
