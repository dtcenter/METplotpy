import argparse
import cartopy
import datetime
import fv3
import matplotlib.pyplot as plt
from metpy.units import units
import numpy as np
import os
import pdb
import sys
import xarray

"""
Plot tendencies of t, q, u, or v from physics parameterizations, dynamics (non-physics), their total, and residual.
Total change is difference between state variable at t = 12 and t = 1, where t is the output timestep.
"""

state_variables = ["tmp", "ugrd", "vgrd", "spfh"]

# =============Arguments===================
parser = argparse.ArgumentParser(description = "Vertical profile of FV3 diagnostic tendencies", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
# ==========Mandatory Arguments===================
parser.add_argument("ifile", type=argparse.FileType("r"), help="FV3 history file")
parser.add_argument("gfile", type=argparse.FileType("r"), help="FV3 grid spec file")
parser.add_argument("variable", type=str, choices=state_variables, default="t", help="variable")
# ==========Optional Arguments===================
parser.add_argument("-d", "--debug", action='store_true')
parser.add_argument("--dtsec", type=float, default=300, help="model time step in seconds")
parser.add_argument("-o", "--ofile", type=str, help="name of output image file")

parser.add_argument("-s", "--shp", type=str, default=None, help="shape file directory for mask")

args = parser.parse_args()
gfile      = args.gfile
ifile      = args.ifile
variable   = args.variable
debug      = args.debug
dt         = args.dtsec * units.seconds
ofile      = args.ofile
shp        = args.shp

if debug:
    print(args)

gds  = xarray.open_dataset(gfile.name)
lont = gds["grid_lont"]
latt = gds["grid_latt"]
area = gds["area"]

if ofile is None:
    ofile = f"{variable}.vert_profile.png"
else:
    ofile = args.ofile


print("creating figure")
fig, ax = plt.subplots()
plt.subplots_adjust(bottom=0.15)
ax.invert_yaxis() # pressure increases from top to bottom
gl = ax.grid(b=True, color="grey", alpha=0.5, lw=0.5)

# Open input file
if debug:
    print(f"About to open {ifile}")
fv3ds = xarray.open_dataset(ifile.name)

lasttime = fv3ds.time[-1] 
# Extract tendencies DataArrays at last time, and multiply by dt * numdt.
all_tend = fv3ds[fv3.tendencies[variable]].sel(time = lasttime).metpy.quantify()
numdt = fv3ds.time.size
# Units of tendencies are K/s averaged over number of time steps within first forecast hour.
# Multiply by time step and number of time steps
all_tend *= dt * numdt

# Stack variables along "tendency" axis of new array. Simpler code but long_name attrs are lost. # TODO preserve long_names 
all_tend = all_tend.to_array(dim="tendency")

print(f"total change in {variable}")
state_variable = fv3ds[variable].metpy.quantify() # Tried metpy.quantify() with open_dataset, but pint.errors.UndefinedUnitError: 'dBz' is not defined in the unit registry
dstate_variable = state_variable.sel(time = lasttime) - state_variable.isel(time=0)
dstate_variable = dstate_variable.assign_coords(time=lasttime)
dstate_variable.attrs["long_name"] = f"change in {state_variable.attrs['long_name']}"

# Sum along "tendency" axis.
resid = all_tend.sum(dim="tendency") - dstate_variable
resid.attrs["long_name"] = f"all_tend - d{variable}"

# Expand "tendency" axis with dstate_variable and resid.
dstate_variable = dstate_variable.expand_dims(dim={"tendency":[f"d{variable}"]})
resid = resid.expand_dims(dim={"tendency":["resid"]})

# Concatentate DataArrays along "tendency" axis.
all_tend = xarray.concat([all_tend,dstate_variable,resid], "tendency")

if shp:
    shp = shp.rstrip("/")
    # Add shapefile name to output filename
    shapename = os.path.basename(shp)
    root, ext = os.path.splitext(ofile)
    ofile = root + f".{shapename}" + ext

    # mask points outside shape
    mask = fv3.pts_in_shp(latt.values, lont.values, shp, debug=debug) # Use .values to avoid AttributeError: 'DataArray' object has no attribute 'flatten'
    mask = xarray.DataArray(mask, coords=[all_tend.grid_yt, all_tend.grid_xt])
    all_tend = all_tend.where(mask)
    area     = area.where(mask).fillna(0)

totalarea = area.metpy.convert_units("km**2").sum()

# append time to output filename
root, ext = os.path.splitext(ofile)
ofile = root + f".{lasttime.dt.strftime('%Y%m%d_%H%M%S').item()}" + ext

# area-weighted spatial average
all_tend = all_tend.weighted(area).mean(area.dims)

print("plot area-weighted spatial average...")
lines = all_tend.plot.line(y="pfull", ax=ax, hue="tendency")
#TODO: get markers in legend entries automatically
for line in lines[-2:]:
    line.set_marker('o')

fineprint  = os.path.realpath(ifile.name)
if shp:
    fineprint += f"\nmask: {shp}"
fineprint += f"\narea: {totalarea.values} {totalarea.metpy.units}"
fineprint += "\ncreated "+str(datetime.datetime.now(tz=None)).split('.')[0]
fineprint_obj = plt.annotate(text=fineprint, xy=(0.01,0.01), xycoords='figure fraction', fontsize=6)


plt.savefig(ofile, dpi=150)
print('created ' + os.path.realpath(ofile))
