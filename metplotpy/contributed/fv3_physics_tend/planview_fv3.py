import argparse
import cartopy
import datetime
import logging
import matplotlib.pyplot as plt
from metpy.units import units
import numpy as np
import os
import pandas as pd
import pdb
import physics_tend
import sys
import xarray
import yaml

"""
Plan view of tendencies of t, q, u, or v from physics parameterizations, dynamics (non-physics), their total, and residual.
Total change is the actual change in state variable from first time to last time. Total change differs from cumulative change
attributed to physics and non-physics tendencies when residual is not zero.
"""

# List of tendency variable names for each state variable, names of lat and lon variables in grid file, graphics parameters
fv3 = yaml.load(open("fv3_physics_tend_defaults.yaml"), Loader=yaml.FullLoader)
state_variables = fv3["tendency_varnames"].keys()

def parse_args():
    # Populate list of choices for contour fill variable argument.
    fill_choices = []
    for state_variable in state_variables: # tendencies for each state variable
        fill_choices.extend(fv3["tendency_varnames"][state_variable])
    # Remove characters up to and including 1st underscore (e.g. du3dt_). 
    # for example dt3dt_pbl -> pbl
    fill_choices = ["_".join(x.split("_")[1:]) for x in fill_choices] # Just the physics/parameterization string after the "_"
    for state_variable in state_variables:
        fill_choices.append(f"d{state_variable}") # total change in state variable
    fill_choices.append("resid") # residual tendency
    fill_choices = set(fill_choices) # no repeats (same physics/parameterization used for multiple state variables). 

    # =============Arguments===================
    parser = argparse.ArgumentParser(description = "Plan view of FV3 diagnostic tendency", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    # ==========Mandatory Arguments===================
    parser.add_argument("historyfile", type=argparse.FileType("r"), help="FV3 history file")
    parser.add_argument("gridfile", type=argparse.FileType("r"), help="FV3 grid spec file")
    parser.add_argument("statevariable", type=str, choices=state_variables, default="tmp", help="state variable")
    parser.add_argument("fill", type=str, choices = fill_choices, help='type of tendency. ignored if pfull is a single level')
    # ==========Optional Arguments===================
    parser.add_argument("-d", "--debug", action='store_true')
    parser.add_argument("--method", type=str, choices=["nearest", "linear","loglinear"], default="nearest", help="vertical interpolation method")
    parser.add_argument("--ncols", type=int, default=None, help="number of columns")
    parser.add_argument("--nofineprint", action='store_true', help="Don't add metadata and created by date (for comparing images)")
    parser.add_argument("-o", "--ofile", type=str, help="name of output image file")
    parser.add_argument("-p", "--pfull", nargs='+', type=float, default=[1000,925,850,700,500,300,200,100,0], help="pressure level(s) in hPa to plot. If only one pressure level is provided, the type-of-tendency argument will be ignored and all tendencies will be plotted.")
    parser.add_argument("-s", "--shp", type=str, default=None, help="shape file directory for mask")
    parser.add_argument("--subtract", type=argparse.FileType("r"), help="FV3 history file to subtract")
    parser.add_argument("-t", "--twindow", type=int, default=3, help="time window in hours")
    parser.add_argument("-v", "--validtime", type=lambda x:pd.to_datetime(x), help="valid time")

    args = parser.parse_args()
    return args

def main():
    args = parse_args()
    gfile      = args.gridfile
    ifile      = args.historyfile
    variable   = args.statevariable
    fill       = args.fill
    debug      = args.debug
    method     = args.method
    ncols      = args.ncols
    nofineprint= args.nofineprint
    ofile      = args.ofile
    pfull      = args.pfull * units.hPa
    shp        = args.shp
    subtract   = args.subtract
    twindow    = datetime.timedelta(hours = args.twindow)
    validtime  = args.validtime

    level = logging.INFO
    if debug: level = logging.DEBUG
    logging.basicConfig(format='%(asctime)s - %(message)s', level=level) # prepend log message with time
    logging.debug(args)

    # Output filename.
    if ofile is None:
        if len(pfull) == 1:
            pfull_str = f"{pfull[0]:~.0f}".replace(" ","")
            ofile = f"{variable}_{pfull_str}.png"
        else:
            ofile = f"{variable}_{fill}.png"
    else:
        ofile = args.ofile
    logging.info(f"output filename={ofile}")


    # Read lat/lon/area from gfile
    logging.debug(f"read lat/lon/area from {gfile}")
    gds  = xarray.open_dataset(gfile.name)
    lont = gds[fv3["lon_name"]]
    latt = gds[fv3["lat_name"]]
    area = gds["area"]

    # Open input file
    logging.debug(f"About to open {ifile}")
    fv3ds = xarray.open_dataset(ifile.name)
    datetimeindex = fv3ds.indexes['time']
    if hasattr(datetimeindex, "to_datetimeindex"):
        # Convert from CFTime to pandas datetime. I get a warning CFTimeIndex from non-standard calendar 'julian'. Maybe history file should be saved with standard calendar.
        # To turn off warning, set unsafe=True.
        datetimeindex = datetimeindex.to_datetimeindex(unsafe=True)
    fv3ds['time'] = datetimeindex
    if subtract:
        logging.debug(f"subtracting {subtract.name}")
        with xarray.set_options(keep_attrs=True):
            fv3ds -= xarray.open_dataset(subtract.name)

    fv3ds = fv3ds.assign_coords(lont=lont, latt=latt) # lont and latt used by pcolorfill()
    tendency_vars = fv3["tendency_varnames"][variable] # list of tendency variable names for requested state variable
    fv3ds = physics_tend.add_time0(fv3ds, variable)
    tendencies = fv3ds[tendency_vars] # subset of original Dataset

    if validtime is None:
        logging.debug("validtime not provided on command line, so use latest time in history file.")
        validtime = fv3ds.time.values[-1]
        validtime = pd.to_datetime(validtime)
    time0 = validtime - twindow
    time1 = time0 + datetime.timedelta(hours=1)
    logging.info(f"Sum tendencies {time1}-{validtime}")
    tindex = dict(time=slice(time1, validtime)) # slice of time from hour after time0 through validtime
    tendencies_avg = tendencies.sel(tindex).mean(dim="time") # average tendencies in time 

    # Dynamics (nophys) tendency is not reset every hour. Just calculate change from time0 to validtime.
    nophys_var = [x for x in tendency_vars if x.endswith("_nophys")]
    assert len(nophys_var) == 1
    nophys_var = nophys_var[0] # we don't want a 1-element list; we want a string. So that tendencies[nophys_var] is a DataArray, not a Dataset.
    logging.info(f"Subtract nophys tendency at {time0} from {validtime}")
    nophys_delta = tendencies[nophys_var].sel(time=validtime) - tendencies[nophys_var].sel(time=time0)
    tendencies_avg[nophys_var] = nophys_delta / args.twindow 


    # Restore units after .mean() removed them. Copy units from 1st tendency variable.
    tendency_units = units.parse_expression(fv3ds[tendency_vars[0]].units)
    logging.debug(f"restoring {tendency_units} units after .mean() method removed them.")
    tendencies_avg *= tendency_units
    for da in tendencies_avg:
        tendencies_avg[da] = tendencies_avg[da].metpy.convert_units("K/hour")
    long_names = [fv3ds[da].attrs["long_name"] for da in tendencies_avg] # Make list of long_names before .to_array() loses them.

    # Remove characters up to and including 1st underscore (e.g. du3dt_) in DataArray name.
    # for example dt3dt_pbl -> pbl
    name_dict = {da : "_".join(da.split("_")[1:]) for da in tendencies_avg.data_vars} 
    tendencies_avg = tendencies_avg.rename(name_dict)

    # Stack variables along new tendency dimension of new DataArray.
    tendency_dim = f"{variable} tendency"
    tendencies_avg = tendencies_avg.to_array(dim=tendency_dim)
    # Assign long_names to a new DataArray coordinate. It will have the same shape as tendency dimension. 
    tendencies_avg = tendencies_avg.assign_coords({"long_name":(tendency_dim,long_names)})

    logging.info(f"calculate actual change in {variable}")
    state_variable = fv3ds[variable].metpy.quantify() # Tried metpy.quantify() with open_dataset, but pint.errors.UndefinedUnitError: 'dBz' is not defined in the unit registry
    dstate_variable = state_variable.sel(time = validtime) - state_variable.sel(time = time0)
    dstate_variable = dstate_variable.assign_coords(time=validtime)
    dstate_variable.attrs["long_name"] = f"actual change in {state_variable.attrs['long_name']}"

    # Add all tendencies together and subtract actual rate of change in state variable.
    # This is residual.
    total = tendencies_avg.sum(dim=tendency_dim)
    twindow_quantity = twindow.total_seconds() * units.seconds 
    resid = total - dstate_variable/twindow_quantity


    logging.info("Define DataArray to plot (da2plot).")
    if len(pfull) == 1:
        # If only 1 pressure level was requested, plot all tendencies.
        da2plot = tendencies_avg
        # Add total and resid DataArrays to tendency_dim.
        total = total.expand_dims({tendency_dim:["total"]}).assign_coords(long_name="sum of tendencies")
        resid = resid.expand_dims({tendency_dim:["resid"]}).assign_coords(long_name=f"sum of tendencies - actual rate of change of {variable} (residual)")
        da2plot = xarray.concat([da2plot, total, resid], dim=tendency_dim)
        col = tendency_dim
    else:
        # otherwise pick a DataArray (resid, state_variable, dstate_variable, tendency) 
        col = "pfull"
        if fill == 'resid': # residual
            da2plot = resid
        elif fill == "": # plain-old state variable
            da2plot = state_variable.sel(time=validtime)
        elif fill == "d"+variable: # actual change in state variable
            da2plot = dstate_variable
        else: # expected change in state variable from tendencies
            da2plot = tendencies_avg.sel({tendency_dim:fill}) 

    if da2plot.metpy.vertical.attrs["units"] == "mb":
        da2plot.metpy.vertical.attrs["units"] = "hPa" # For MetPy. Otherwise, mb is interpreted as millibarn.

    # dequantify moves units from DataArray to Attributes. Now they show up in colorbar. And they aren't lost in xarray.DataArray.interp.
    da2plot = da2plot.metpy.dequantify()

    # Select vertical levels.
    if method == "nearest":
        da2plot = da2plot.metpy.sel(vertical=pfull, method=method, tolerance=10.*units.hPa)
    elif method == "linear":
        da2plot = da2plot.interp(coords={"pfull":pfull}, method=method)
    elif method == "loglinear": # interpolate in log10(pressure)
        da2plot["pfull"] = np.log10(da2plot.pfull) 
        da2plot = da2plot.interp(coords={"pfull":np.log10(pfull.m)}, method="linear")
        da2plot["pfull"] = 10**da2plot.pfull


    # Mask points outside shape.
    if shp:
        shp = shp.rstrip("/")
        # Add shapefile name to output filename
        shapename = os.path.basename(shp)
        root, ext = os.path.splitext(ofile)
        ofile = root + f".{shapename}" + ext

        # mask points outside shape
        mask = physics_tend.pts_in_shp(latt.values, lont.values, shp, debug=debug) # Use .values to avoid AttributeError: 'DataArray' object has no attribute 'flatten'
        mask = xarray.DataArray(mask, coords=[da2plot.grid_yt, da2plot.grid_xt])
        da2plot = da2plot.where(mask, drop=True)
        area     = area.where(mask).fillna(0)

    totalarea = area.metpy.convert_units("km**2").sum()

    # Make default dimensions of facetgrid kind of square.
    if not ncols:
        # Default # of cols is square root of # of panels
        ncols = int(np.ceil(np.sqrt(len(da2plot))))

    nrows = int(np.ceil(len(da2plot)/ncols))


    if da2plot["pfull"].size == 1:
        # Avoid ValueError: ('grid_yt', 'grid_xt') must be a permuted list of ('pfull', 'grid_yt', 'grid_xt'), unless `...` is included
        # Error occurs in pcolormesh().
        da2plot=da2plot.squeeze()


    # central lon/lat from https://github.com/NOAA-EMC/regional_workflow/blob/release/public-v1/ush/Python/plot_allvars.py
    subplot_kws = dict(projection=cartopy.crs.LambertConformal(central_longitude=-97.6, central_latitude=35.4, standard_parallels=None))


    logging.info("plot pcolormesh")
    pc = da2plot.plot.pcolormesh(x="lont", y="latt", col=col, col_wrap=ncols, robust=True, infer_intervals=True,
            transform=cartopy.crs.PlateCarree(),
            cmap=fv3["cmap"], cbar_kwargs={'shrink':0.8}, subplot_kws=subplot_kws) # robust (bool, optional) – If True and vmin or vmax are absent, the colormap range is computed with 2nd and 98th percentiles instead of the extreme values
    for ax in pc.axes.flat:
        ax.set_extent(fv3["extent"]) # Why needed only when col=tendency_dim? With col="pfull" it shrinks to unmasked size.
        physics_tend.add_conus_features(ax)

    # Add time to title and output filename
    root, ext = os.path.splitext(ofile)
    ofile = root + f".{time0.strftime('%Y%m%d_%H%M%S')}-{validtime.strftime('%Y%m%d_%H%M%S')}" + ext
    title = f'{time0}-{validtime} ({twindow_quantity.to("hours"):~} time window)'
    if col == tendency_dim:
        title = f'pfull={pfull[0]:~.0f} {title}'
    elif 'long_name' in da2plot.coords:
        title = f'{da2plot.coords["long_name"].data} {title}'
    plt.suptitle(title, wrap=True)

    # Annotate figure with details about figure creation. 
    fineprint  = f"history: {os.path.realpath(ifile.name)}"
    if subtract:
        fineprint  += f"\nsubtract: {os.path.realpath(subtract.name)}"
    fineprint += f"\ngrid_spec: {os.path.realpath(gfile.name)}"
    if shp: fineprint += f"\nmask: {shp}"
    fineprint += f"\ntotal area: {totalarea.data:~.0f}"
    fineprint += f"\nvertical interpolation method: {method}  requested levels: {pfull}"
    fineprint += f"\ncreated {datetime.datetime.now(tz=None)}"
    if nofineprint:
        logging.info(fineprint)
    else:
        fineprint_obj = plt.annotate(text=fineprint, xy=(1,1), xycoords='figure pixels', fontsize=5)


    plt.savefig(ofile, dpi=fv3["dpi"])
    logging.info(f'created {os.path.realpath(ofile)}')

if __name__ == "__main__":
    main()
