import argparse
import cartopy
import cartopy.feature as cfeature
import datetime
import fv3 # get expected variable names for each type of tendency
import matplotlib.pyplot as plt
from metpy.units import units
import numpy as np
import os
import pdb
import sys
import xarray

"""
Plan view of tendencies of t, q, u, or v from physics parameterizations, dynamics (non-physics), their total, and residual.
Total change is difference between state variable at t = 12 and t = 1, where t is the output timestep.
"""

state_variables = fv3.tendencies.keys()

def parse_args():
    # Populate list of choices for contour fill argument.
    fill_choices = ["resid"] # residual tendency
    for state_variable in state_variables: # tendencies for each state variable
        fill_choices.extend(fv3.tendencies[state_variable])
    fill_choices = ["_".join(x.split("_")[1:]) for x in fill_choices] # Just the physics/parameterization string after the "_"
    for state_variable in state_variables:
        fill_choices.append(f"d{state_variable}") # total change in state variable
    fill_choices = set(fill_choices) # no repeats (same physics/parameterization used for multiple state variables). 

    # =============Arguments===================
    parser = argparse.ArgumentParser(description = "Plan view plot of FV3 diagnostic tendency", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    # ==========Mandatory Arguments===================
    parser.add_argument("historyfile", type=argparse.FileType("r"), help="FV3 history file")
    parser.add_argument("gridfile", type=argparse.FileType("r"), help="FV3 grid spec file")
    parser.add_argument("statevariable", type=str, choices=state_variables, default="tmp", help="state variable")
    parser.add_argument("fill", type=str, choices = fill_choices, help='filled contour variable with 2 spatial dims and optional time and vertical dims.')
    # ==========Optional Arguments===================
    parser.add_argument("-d", "--debug", action='store_true')
    parser.add_argument("--dtsec", type=float, default=300, help="model time step in seconds")
    parser.add_argument("--ncols", type=int, default=None, help="number of columns")
    parser.add_argument("-o", "--ofile", type=str, help="name of output image file")
    parser.add_argument("-p", "--pfull", nargs='+', type=float, default=[1000,925,850,700,500,300,200,100,0], help="pressure level(s) to plot")
    parser.add_argument("-s", "--shp", type=str, default=None, help="shape file directory for mask")

    args = parser.parse_args()
    return args

def main():
    args = parse_args()
    gfile      = args.gridfile
    ifile      = args.historyfile
    variable   = args.statevariable
    fill       = args.fill
    debug      = args.debug
    dt         = args.dtsec * units.seconds
    ncols      = args.ncols
    ofile      = args.ofile
    pfull      = args.pfull
    shp        = args.shp

    if debug:
        print(args)
    gds  = xarray.open_dataset(gfile.name)
    lont = gds["grid_lont"]
    latt = gds["grid_latt"]
    area = gds["area"]

    if ofile is None:
        ofile = f"{variable}.png"
        if fill:
            ofile = f"{variable}_{fill}.png"

    else:
        ofile = args.ofile


    # Open input file
    if debug:
        print(f"About to open {ifile}")
    fv3ds = xarray.open_dataset(ifile.name)

    fv3ds = fv3ds.assign_coords(lont=lont, latt=latt) # lont and latt used by pcolorfill()
    lasttime = fv3ds.time[-1] 
    # Extract tendencies DataArrays at last time, and multiply by dt * numdt.
    all_tend = fv3ds[fv3.tendencies[variable]].sel(time = lasttime).metpy.quantify()
    numdt = fv3ds.time.size
    # Units of tendencies are K/s averaged over number of time steps within first forecast hour.
    # Multiply by time step and number of time steps
    all_tend *= dt * numdt
    # Reassign original long_name attributes but replace "tendency" with "change".
    # long_name was correctly removed after multiplying by dt * numdt.
    for varname, da in all_tend.data_vars.items():
        da.attrs["long_name"] = fv3ds[varname].attrs["long_name"].replace("tendency", "change")
    # Remove characters up to and including 1st underscore (e.g. du3dt_) in DataArray name.
    name_dict = {da : "_".join(da.split("_")[1:]) for da in all_tend.data_vars} 
    all_tend = all_tend.rename(name_dict)

    # Stack variables along new tendency axis of new DataArray.
    tendency = f"{variable} tendency"
    all_tend = all_tend.to_array(dim=tendency)

    print(f"calculate d{variable}")
    state_variable = fv3ds[variable].metpy.quantify() # Tried metpy.quantify() with open_dataset, but pint.errors.UndefinedUnitError: 'dBz' is not defined in the unit registry
    dstate_variable = state_variable.sel(time = lasttime) - state_variable.isel(time=0)
    dstate_variable = dstate_variable.assign_coords(time=lasttime)
    dstate_variable.attrs["long_name"] = f"change in {state_variable.attrs['long_name']}"

    # Sum along tendency axis.
    resid = all_tend.sum(dim=tendency) - dstate_variable
    resid.attrs["long_name"] = f"all_tend - d{variable}"

    if fill == 'resid':
        all_tend = resid
    elif fill == "":
        all_tend = state_variable.sel(time=lasttime)
    elif fill == "d"+variable:
        all_tend = dstate_variable
    else:
        all_tend = all_tend.sel({tendency:fill})

    all_tend = all_tend.sel(pfull=pfull, method="nearest", tolerance=50.)

    if shp:
        shp = shp.rstrip("/")
        # Add shapefile name to output filename
        shapename = os.path.basename(shp)
        root, ext = os.path.splitext(ofile)
        ofile = root + f".{shapename}" + ext

        # mask points outside shape
        mask = fv3.pts_in_shp(latt.values, lont.values, shp, debug=debug) # Use .values to avoid AttributeError: 'DataArray' object has no attribute 'flatten'
        mask = xarray.DataArray(mask, coords=[all_tend.grid_yt, all_tend.grid_xt])
        all_tend = all_tend.where(mask, drop=True)
        area     = area.where(mask).fillna(0)

    totalarea = area.metpy.convert_units("km**2").sum()

    if not ncols:
        # Default # of cols is square root of # of panels
        ncols = int(np.ceil(np.sqrt(len(all_tend))))

    nrows = int(np.ceil(len(all_tend)/ncols))


    # central lon/lat from https://github.com/NOAA-EMC/regional_workflow/blob/release/public-v1/ush/Python/plot_allvars.py
    subplot_kws = dict(projection=cartopy.crs.LambertConformal(central_longitude=-97.6, central_latitude=35.4, standard_parallels=None))

    print("creating figure")
    # dequantify moves units from DataArray to Attributes. Now they show up in colorbar.
    all_tend = all_tend.metpy.dequantify()
    p = all_tend.plot.pcolormesh(x="lont", y="latt", col="pfull", col_wrap=ncols, robust=True, infer_intervals=True, transform=cartopy.crs.PlateCarree(),
            subplot_kws=subplot_kws) # robust (bool, optional) – If True and vmin or vmax are absent, the colormap range is computed with 2nd and 98th percentiles instead of the extreme values
    for ax in p.axes.flat:
        ax.add_feature(cfeature.COASTLINE.with_scale('50m'), linewidth=0.3)
        ax.add_feature(cfeature.BORDERS.with_scale('50m'), linewidth=0.3)
        ax.add_feature(cfeature.STATES.with_scale('50m'), linewidth=0.1)
        ax.add_feature(cfeature.LAKES.with_scale('50m'), edgecolor='k', linewidth=0.25, facecolor='k', alpha=0.1)

    # add time to title and output filename
    root, ext = os.path.splitext(ofile)
    ofile = root + f".{lasttime.dt.strftime('%Y%m%d_%H%M%S').item()}" + ext
    title = lasttime.item()
    if "long_name" in all_tend.attrs:
        title = f'{all_tend.attrs["long_name"]} ({fill})  {lasttime.item()}'
    plt.suptitle(title, wrap=True)

    fineprint  = f"history: {os.path.realpath(ifile.name)}"
    fineprint += f"\ngrid_spec: {os.path.realpath(gfile.name)}"
    if shp: fineprint += f"\nmask: {shp}"
    fineprint += f"\ntotal area: {totalarea.data:~.0f}"
    fineprint += f"\ncreated {datetime.datetime.now(tz=None)}"
    fineprint_obj = plt.annotate(text=fineprint, xy=(1,1), xycoords='figure pixels', fontsize=5)


    plt.savefig(ofile, dpi=150)
    print('created ' + os.path.realpath(ofile))

if __name__ == "__main__":
    main()
