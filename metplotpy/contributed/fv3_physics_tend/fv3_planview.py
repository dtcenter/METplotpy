import argparse
import cartopy
import cartopy.feature as cfeature
import datetime
import fv3 # get dictionary of variable names for each type of tendency, string name of lat and lon variables
import logging
import matplotlib.pyplot as plt
from metpy.units import units
import numpy as np
import os
import pdb
import sys
import xarray

"""
Plan view of tendencies of t, q, u, or v from physics parameterizations, dynamics (non-physics), their total, and residual.
Total change is the actual change in state variable from first time to last time. Total change differs from cumulative change
attributed to physics and non-physics tendencies when residual is not zero.
"""

state_variables = fv3.tendencies.keys()

def parse_args():
    # Populate list of choices for contour fill variable argument.
    fill_choices = []
    for state_variable in state_variables: # tendencies for each state variable
        fill_choices.extend(fv3.tendencies[state_variable])
    # Remove characters up to and including 1st underscore (e.g. du3dt_). 
    # for example dt3dt_pbl -> pbl
    fill_choices = ["_".join(x.split("_")[1:]) for x in fill_choices] # Just the physics/parameterization string after the "_"
    for state_variable in state_variables:
        fill_choices.append(f"d{state_variable}") # total change in state variable
    fill_choices.append("resid") # residual tendency
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
    parser.add_argument("-p", "--pfull", nargs='+', type=float, default=[1000,925,850,700,500,300,200,100,0], help="pressure level(s) in hPa to plot")
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
    fill       = args.fill
    debug      = args.debug
    dt         = args.dtsec * units.seconds
    ncols      = args.ncols
    ofile      = args.ofile
    pfull      = args.pfull * units.hPa
    shp        = args.shp
    subtract   = args.subtract

    logging.debug(args)
    gds  = xarray.open_dataset(gfile.name)
    lont = gds[fv3.lon_name]
    latt = gds[fv3.lat_name]
    area = gds["area"]

    if ofile is None:
        ofile = f"{variable}_{fill}.png"
    else:
        ofile = args.ofile


    # Open input file
    if debug:
        print(f"About to open {ifile}")
    fv3ds = xarray.open_dataset(ifile.name)
    if subtract:
        logging.debug(f"subtracting {subtract.name}")
        with xarray.set_options(keep_attrs=True):
            fv3ds -= xarray.open_dataset(subtract.name)

    fv3ds = fv3ds.assign_coords(lont=lont, latt=latt) # lont and latt used by pcolorfill()


    # Convert tendency to cumulative change.
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
    long_names = [total_change[da].attrs["long_name"] for da in total_change] # Make list of long_names before .to_array() loses them.
    total_change = total_change.to_array(dim=tendency)
    # Assign long_names to a new DataArray coordinate. It will have the same shape as tendency dimension. 
    total_change = total_change.assign_coords({"long_name":(tendency,long_names)})

    logging.info(f"calculate d{variable}")
    state_variable = fv3ds[variable].metpy.quantify() # Tried metpy.quantify() with open_dataset, but pint.errors.UndefinedUnitError: 'dBz' is not defined in the unit registry
    state_variable_initial_time = fv3ds[variable+"_i"].metpy.quantify() 
    dstate_variable = state_variable.sel(time = lasttime) - state_variable_initial_time
    dstate_variable = dstate_variable.assign_coords(time=lasttime)
    dstate_variable.attrs["long_name"] = f"change in {state_variable.attrs['long_name']}"

    # Sum along tendency axis and subtract change in state variable.
    # This is residual.
    resid = total_change.sum(dim=tendency) - dstate_variable
    resid.attrs["long_name"] = f"total_change - d{variable}"


    # Assign final DataArray to plot.
    if fill == 'resid':
        da2plot = resid
    elif fill == "":
        da2plot = state_variable.sel(time=lasttime)
    elif fill == "d"+variable:
        da2plot = dstate_variable
    else:
        da2plot = total_change.sel({tendency:fill})

    # Select vertical levels.
    if da2plot.metpy.vertical.attrs["units"] == "mb":
        da2plot.metpy.vertical.attrs["units"] = "hPa" # For MetPy. Otherwise, mb is interpreted as millibarn.
    da2plot = da2plot.metpy.sel(vertical=pfull, method="nearest", tolerance=50.*units.hPa)
   

    # Mask points outside shape.
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

    # Make default dimensions of facetgrid kind of square.
    if not ncols:
        # Default # of cols is square root of # of panels
        ncols = int(np.ceil(np.sqrt(len(da2plot))))

    nrows = int(np.ceil(len(da2plot)/ncols))


    # central lon/lat from https://github.com/NOAA-EMC/regional_workflow/blob/release/public-v1/ush/Python/plot_allvars.py
    subplot_kws = dict(projection=cartopy.crs.LambertConformal(central_longitude=-97.6, central_latitude=35.4, standard_parallels=None))

    print("creating figure")
    # dequantify moves units from DataArray to Attributes. Now they show up in colorbar.
    da2plot = da2plot.metpy.dequantify()
    p = da2plot.plot.pcolormesh(x="lont", y="latt", col="pfull", col_wrap=ncols, robust=True, infer_intervals=True, transform=cartopy.crs.PlateCarree(),
            subplot_kws=subplot_kws) # robust (bool, optional) – If True and vmin or vmax are absent, the colormap range is computed with 2nd and 98th percentiles instead of the extreme values
    for ax in p.axes.flat:
        ax.add_feature(cfeature.COASTLINE.with_scale('50m'), linewidth=0.3)
        ax.add_feature(cfeature.BORDERS.with_scale('50m'), linewidth=0.3)
        ax.add_feature(cfeature.STATES.with_scale('50m'), linewidth=0.1)
        ax.add_feature(cfeature.LAKES.with_scale('50m'), edgecolor='k', linewidth=0.25, facecolor='k', alpha=0.1)

    # Add time to title and output filename
    root, ext = os.path.splitext(ofile)
    ofile = root + f".{lasttime.dt.strftime('%Y%m%d_%H%M%S').item()}" + ext
    title = f'{lasttime.item()}'
    if 'long_name' in da2plot.coords:
        title = f'{da2plot.coords["long_name"].data}  {lasttime.item()}'
    plt.suptitle(title, wrap=True)

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
