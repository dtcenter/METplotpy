import argparse
import cartopy
import datetime
import fv3 # get dictionary of variable names for each type of tendency, string name of lat and lon variables
import logging
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
from metpy.units import units
import numpy as np
import os
import pdb
import sys
import xarray

"""
Vertical profile of tendencies of t, q, u, or v from physics parameterizations, dynamics (non-physics), their total, and residual.
Total change is the actual change in state variable from first time to last time. Total change differs from cumulative change
attributed to physics and non-physics tendencies when residual is not zero.
"""

state_variables = fv3.tendencies.keys()

def parse_args():
    # =============Arguments===================
    parser = argparse.ArgumentParser(description = "Vertical profile of FV3 diagnostic tendencies", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    # ==========Mandatory Arguments==================
    parser.add_argument("historyfile", type=argparse.FileType("r"), help="FV3 history file")
    parser.add_argument("gridfile", type=argparse.FileType("r"), help="FV3 grid spec file")
    parser.add_argument("statevariable", type=str, choices=state_variables, default="tmp", help="state variable")
    # ==========Optional Arguments===================
    parser.add_argument("-d", "--debug", action='store_true')
    parser.add_argument("--resid", action="store_true", help="calculate residual")
    parser.add_argument("--dtsec", type=float, default=300, help="model time step in seconds")
    parser.add_argument("-o", "--ofile", type=str, help="name of output image file")

    parser.add_argument("-s", "--shp", type=str, default=None, help="shape file directory for mask")
    parser.add_argument("--subtract", type=argparse.FileType("r"), help="FV3 history file to subtract")

    args = parser.parse_args()
    return args

logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)
def main():
    args = parse_args()
    gfile      = args.gridfile
    ifile      = args.historyfile
    variable   = args.statevariable
    debug      = args.debug
    resid      = args.resid
    dt         = args.dtsec * units.seconds
    ofile      = args.ofile
    shp        = args.shp
    subtract   = args.subtract

    logging.debug(args)
    gds  = xarray.open_dataset(gfile.name)
    lont = gds[fv3.lon_name]
    latt = gds[fv3.lat_name]
    area = gds["area"]

    if ofile is None:
        ofile = f"{variable}.vert_profile.png"
    else:
        ofile = args.ofile


    print("creating figure")
    fig, ax = plt.subplots()
    plt.subplots_adjust(bottom=0.18) # add space at bottom for fine print
    ax.invert_yaxis() # pressure increases from top to bottom
    ax.grid(visible=True, color="grey", alpha=0.5, lw=0.5)
    ax.yaxis.set_major_locator(MultipleLocator(100))
    ax.yaxis.set_minor_locator(MultipleLocator(25))
    ax.grid(which='minor', alpha=0.3, lw=0.4)

    # Open input file
    if debug:
        print(f"About to open {ifile}")
    fv3ds = xarray.open_dataset(ifile.name)
    if subtract:
        logging.debug(f"subtracting {subtract.name}")
        with xarray.set_options(keep_attrs=True):
            fv3ds -= xarray.open_dataset(subtract.name)

    lasttime = fv3ds.time[-1] 
    # Extract tendencies DataArrays at last time, and multiply by dt * numdt.
    all_tend = fv3ds[fv3.tendencies[variable]].sel(time = lasttime).metpy.quantify()
    numdt = fv3ds.time.size
    # Units of tendencies are K/s averaged over number of time steps within first forecast hour.
    # Multiply by time step and number of time steps
    total_change = all_tend * dt * numdt
    # Reassign original long_name attributes but replace "tendency" with "change".
    # long_name was correctly removed after multiplying by dt * numdt.
    for varname, da in total_change.data_vars.items():
        da.attrs["long_name"] = fv3ds[varname].attrs["long_name"].replace("tendency", "change")


    # Remove characters up to and including 1st underscore (e.g. du3dt_) in DataArray name.
    # for example dt3dt_pbl -> pbl
    name_dict = {da : "_".join(da.split("_")[1:]) for da in total_change.data_vars} 
    total_change = total_change.rename(name_dict)


    # Stack variables along new tendency axis of new DataArray.
    tendency = f"{variable} tendency"
    # In fv3_planview.py we keep track of long_names, but this causes trouble in 
    # fv3_vert_profile if resid=True and we add dstate_variable and resid.
    # Those DataArrays won't have a long_name coordinate.
    total_change = total_change.to_array(dim=tendency)

    print(f"calculate d{variable}")
    state_variable = fv3ds[variable].metpy.quantify() # Tried metpy.quantify() with open_dataset, but pint.errors.UndefinedUnitError: 'dBz' is not defined in the unit registry
    state_variable_initial_time = fv3ds[variable+"_i"] 
    dstate_variable = state_variable.sel(time = lasttime) - state_variable_initial_time
    dstate_variable = dstate_variable.assign_coords(time=lasttime)
    dstate_variable.attrs["long_name"] = f"change in {state_variable.attrs['long_name']}"

    # Sum along tendency axis and subtract change in state variable.
    # This is residual.
    resid = total_change.sum(dim=tendency) - dstate_variable
    resid.attrs["long_name"] = f"total_change - d{variable}"

    if resid is not None:
        # Expand tendency axis with dstate_variable and resid.
        dstate_variable = dstate_variable.expand_dims(dim={tendency:[f"d{variable}"]})
        resid = resid.expand_dims(dim={tendency:["resid"]})

        # Add dstate_variable and resid DataArrays to tendency axis.
        total_change = xarray.concat([total_change,dstate_variable,resid], tendency)


    da2plot = total_change
    if shp:
        shp = shp.rstrip("/")
        # Add shapefile name to output filename
        shapename = os.path.basename(shp)
        root, ext = os.path.splitext(ofile)
        ofile = root + f".{shapename}" + ext

        # mask points outside shape
        mask = fv3.pts_in_shp(latt.values, lont.values, shp, debug=debug) # Use .values to avoid AttributeError: 'DataArray' object has no attribute 'flatten'
        mask = xarray.DataArray(mask, coords=[da2plot.grid_yt, da2plot.grid_xt])
        da2plot = da2plot.where(mask, drop=True)
        area     = area.where(mask).fillna(0)

    totalarea = area.metpy.convert_units("km**2").sum()

    # Append time to output filename
    root, ext = os.path.splitext(ofile)
    ofile = root + f".{lasttime.dt.strftime('%Y%m%d_%H%M%S').item()}" + ext

    # area-weighted spatial average
    da2plot = da2plot.weighted(area).mean(area.dims)

    # Put units in attributes so they show up in xlabel.
    da2plot = da2plot.metpy.dequantify()

    print("plot area-weighted spatial average...")
    lines = da2plot.metpy.dequantify().plot.line(y="pfull", ax=ax, hue=tendency)

    if resid is not None: # resid might have been turned from a Boolean to a DataArray.
        # Add special marker to dstate_variable and residual lines.
        # DataArray plot legend handles differ from the plot lines, for some reason. So if you 
        # change the style of a line later, it is not automatically changed in the legend.
        # zip d{variable}, resid line and their respective legend handles together and change their style together.
        # [-2:] means take last two elements of da2plot.
        special_lines = list(zip(lines, ax.get_legend().legendHandles))[-2:]
        special_marker = 'o'
        special_marker_size = 3
        for line, leghandle in special_lines:
            line.set_marker(special_marker)
            line.set_markersize(special_marker_size)
            leghandle.set_marker(special_marker)
            leghandle.set_markersize(special_marker_size)

    # Annotate figure with details about figure creation. 
    fineprint  = f"history: {os.path.realpath(ifile.name)}"
    if subtract:
        fineprint  += f"\nsubtract: {os.path.realpath(subtract.name)}"
    fineprint += f"\ngrid_spec: {os.path.realpath(gfile.name)}"
    if shp: fineprint += f"\nmask: {shp}"
    fineprint += f"\ntotal area: {totalarea.data:~.0f}"
    fineprint += f"\ncreated {datetime.datetime.now(tz=None)}"
    fineprint_obj = plt.annotate(text=fineprint, xy=(1,1), xycoords='figure pixels', fontsize=5)


    plt.savefig(ofile, dpi=150)
    print('created ' + os.path.realpath(ofile))

if __name__ == "__main__":
    main()
