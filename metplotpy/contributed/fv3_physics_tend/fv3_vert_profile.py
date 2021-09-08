import argparse
import cartopy
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
parser = argparse.ArgumentParser(description = "Vertical profile of FV3 diagnostic tendencies", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
# ==========Mandatory Arguments===================
parser.add_argument("ifile", type=argparse.FileType("r"), help="FV3 history file")
parser.add_argument("gfile", type=argparse.FileType("r"), help="FV3 grid spec file")
# ==========Optional Arguments===================
parser.add_argument("-d", "--debug", action='store_true')
parser.add_argument("--dtsec", type=float, default=300, help="model time step in seconds")
parser.add_argument("-e", "--extent", nargs=4, type=float, default=None, help="minlon maxlon minlat maxlat")
parser.add_argument("-o", "--ofile", type=str, help="name of output image file")

parser.add_argument("-s", "--shp", type=argparse.FileType("r"), default=None, help="subdomain shape file")

args = parser.parse_args()
gfile      = args.gfile
ifile      = args.ifile
debug      = args.debug
dt         = args.dtsec * units.seconds
extent     = args.extent
ofile      = args.ofile
shp        = args.shp

if debug:
    print(args)

gds  = xarray.open_dataset(gfile.name)
lon  = gds["grid_lont"]
lat  = gds["grid_latt"]
area = gds["area"]

if ofile is None:
    ofile = f"vert_profile.png"
else:
    ofile = args.ofile


print("creating figure")
fig, ax = plt.subplots()
ax.invert_yaxis()
gl = ax.grid(b=True, color="grey", alpha=0.5, lw=0.5)

# Open input file
if debug:
    print(f"About to open {ifile}")
fv3xr = xarray.open_dataset(ifile.name)

if shp:
    # Add shapefile name to output filename
    shapename, ext = os.path.splitext(os.path.basename(shp.name))
    root, ext = os.path.splitext(ofile)
    ofile = root + f".{shapename}" + ext
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

if shp:
    # mask points outside shape
    mask = st4.pts_in_shp(lat.values, lon.values, shp.name, debug=debug)
    all_tend = all_tend.where(mask)
    dtmp = dtmp.where(mask)
    resid = resid.where(mask)

# append time to title and output filename
title = lasttime.item()
root, ext = os.path.splitext(ofile)
ofile = root + f".{lasttime.dt.strftime('%Y%m%d_%H%M%S').item()}" + ext

# area-weighted spatial average
print("plot area-weighted spatial average...")
# Tried using xarray.DataArray.plot.line method but the legend didn't include additional lines dtmp and resid.
for tend in all_tend:
    ax.plot(tend.weighted(area).mean(area.dims), tmp.pfull, label=tend.tendency.values)
ax.plot(dtmp.weighted(area).mean(area.dims), tmp.pfull, linestyle="dashed", label="dtmp")
ax.plot(resid.weighted(area).mean(area.dims), tmp.pfull, linestyle="dotted", label="resid")
ax.set_title(title)
ax.set_xlabel(tmp.metpy.units)
ax.set_ylabel(tmp.pfull.units)
leg = plt.legend()

fineprint  = os.path.realpath(ifile.name)
if shp:
    fineprint += f"\nshape {shp.name}"
fineprint += f"\nextent {extent}"
fineprint += "\ncreated "+str(datetime.datetime.now(tz=None)).split('.')[0]
fineprint_obj = plt.annotate(s=fineprint, xy=(5,5), xycoords='figure pixels', fontsize=4)

plt.savefig(ofile, dpi=150)
print('created ' + os.path.realpath(ofile))
