import argparse
import cartopy
import datetime
import logging
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
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
Vertical profile of tendencies of t, q, u, or v from physics parameterizations, dynamics (non-physics), their total, and residual.
Total change is the actual change in state variable from first time to last time. Total change differs from cumulative change
attributed to physics and non-physics tendencies when residual is not zero.
"""

# List of tendency variable names for each state variable, names of lat and lon variables in grid file, graphics parameters
fv3 = yaml.load(open("fv3_physics_tend_defaults.yaml"), Loader=yaml.FullLoader)
state_variables = fv3["tendency_varnames"].keys()

def parse_args():
    # =============Arguments===================
    parser = argparse.ArgumentParser(description = "Vertical profile of FV3 diagnostic tendencies", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    # ==========Mandatory Arguments===================
    parser.add_argument("historyfile", type=argparse.FileType("r"), help="FV3 history file")
    parser.add_argument("gridfile", type=argparse.FileType("r"), help="FV3 grid spec file")
    parser.add_argument("statevariable", type=str, choices=state_variables, default="tmp", help="state variable")
    # ==========Optional Arguments===================
    parser.add_argument("-d", "--debug", action='store_true')
    parser.add_argument("--nofineprint", action='store_true', help="Don't add metadata and created by date (for comparing images)")
    parser.add_argument("-o", "--ofile", type=str, help="name of output image file")
    parser.add_argument("--resid", action="store_true", help="calculate residual")
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
    debug      = args.debug
    resid      = args.resid
    nofineprint= args.nofineprint
    ofile      = args.ofile
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
        ofile = f"{variable}.vert_profile.png"
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

    da2plot = tendencies_avg
    if resid is not None:
        # Add total and resid DataArrays to tendency_dim.
        total = total.expand_dims({tendency_dim:["total"]}).assign_coords(long_name="sum of tendencies")
        resid = resid.expand_dims({tendency_dim:["resid"]}).assign_coords(long_name=f"sum of tendencies - actual rate of change of {variable} (residual)")
        da2plot = xarray.concat([da2plot, total, resid], dim=tendency_dim)



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


    logging.info(f"area-weighted spatial average")
    da2plot = da2plot.weighted(area).mean(area.dims)


    logging.info("creating figure")
    fig, ax = plt.subplots()
    plt.subplots_adjust(bottom=0.18) # add space at bottom for fine print
    ax.invert_yaxis() # pressure increases from top to bottom
    ax.grid(visible=True, color="grey", alpha=0.5, lw=0.5)
    ax.yaxis.set_major_locator(MultipleLocator(100))
    ax.yaxis.set_minor_locator(MultipleLocator(25))
    ax.grid(which='minor', alpha=0.3, lw=0.4)

    # Put units in attributes so they show up in xlabel.
    da2plot = da2plot.metpy.dequantify()

    logging.info("plot area-weighted spatial average...")
    lines = da2plot.plot.line(y="pfull", ax=ax, hue=tendency_dim)

    if resid is not None: # resid might have been turned from a Boolean scalar variable to a DataArray.
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

    # Add time to title and output filename
    root, ext = os.path.splitext(ofile)
    ofile = root + f".{time0.strftime('%Y%m%d_%H%M%S')}-{validtime.strftime('%Y%m%d_%H%M%S')}" + ext
    title = f'{time0}-{validtime} ({twindow_quantity.to("hours"):~} time window)'
    ax.set_title(title, wrap=True)

    if shp:
        # Locate region of interest on conus map background. Put in inset.
        projection = cartopy.crs.LambertConformal(central_longitude=-97.5, central_latitude=fv3["standard_parallel"])
        ax_inset = plt.gcf().add_axes([.7, .001, .19, .13], projection=projection)
        # astype(int) to avoid TypeError: numpy boolean subtract
        cbar_kwargs = dict(ticks=[0.25,0.75],shrink=0.6)
        pc = mask.assign_coords(lont=lont, latt=latt).astype(int).plot.pcolormesh(ax=ax_inset, x="lont", y="latt", infer_intervals=True, 
            transform=cartopy.crs.PlateCarree(), cmap=plt.cm.get_cmap('cool',2), add_labels=False, cbar_kwargs=cbar_kwargs)
        pc.colorbar.ax.set_yticklabels(["masked","valid"], fontsize='xx-small')
        pc.colorbar.outline.set_visible(False)
        physics_tend.add_conus_features(ax_inset)
        extent = fv3["extent"]
        ax_inset.set_extent(extent)

    # Annotate figure with details about figure creation. 
    fineprint  = f"history: {os.path.realpath(ifile.name)}"
    if subtract:
        fineprint  += f"\nsubtract: {os.path.realpath(subtract.name)}"
    fineprint += f"\ngrid_spec: {os.path.realpath(gfile.name)}"
    if shp: fineprint += f"\nmask: {shp}"
    fineprint += f"\ntotal area: {totalarea.data:~.0f}"
    fineprint += f"\ncreated {datetime.datetime.now(tz=None)}"
    if nofineprint:
        logging.info(fineprint)
    else:
        fineprint_obj = plt.annotate(text=fineprint, xy=(1,1), xycoords='figure pixels', fontsize=5)


    plt.savefig(ofile, dpi=fv3["dpi"])
    logging.info(f'created {os.path.realpath(ofile)}')

if __name__ == "__main__":
    main()
