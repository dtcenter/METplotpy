import argparse
import cartopy
import datetime
import fv3 # dictionary of tendencies for each state variable, varnames of lat and lon variables in grid file, graphics parameters
import logging
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
from metpy.interpolate import cross_section
from metpy.units import units
import numpy as np
import os
import pandas as pd
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

    # =============Arguments===================
    parser = argparse.ArgumentParser(description = "Plan view plot of FV3 diagnostic tendency", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    # ==========Mandatory Arguments===================
    parser.add_argument("historyfile", type=argparse.FileType("r"), help="FV3 history file")
    parser.add_argument("gridfile", type=argparse.FileType("r"), help="FV3 grid spec file")
    parser.add_argument("statevariable", type=str, choices=state_variables, default="tmp", help="state variable")
    # ==========Optional Arguments===================
    parser.add_argument("-d", "--debug", action='store_true')
    parser.add_argument("--dindex", type=int, default=20, help="tick and gridline interval along cross section")
    parser.add_argument("--ncols", type=int, default=None, help="number of columns")
    parser.add_argument("-o", "--ofile", type=str, help="name of output image file")
    parser.add_argument("-s", "--start", nargs=2, type=float, default=(28, -115), help="start point")
    parser.add_argument("-e", "--end", nargs=2, type=float, default=(30, -82), help="end point")
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
    dindex     = args.dindex
    ncols      = args.ncols
    ofile      = args.ofile
    startpt    = args.start
    endpt      = args.end
    subtract   = args.subtract
    twindow    = datetime.timedelta(hours = args.twindow)
    validtime  = args.validtime

    level = logging.INFO
    if debug: level = logging.DEBUG
    logging.basicConfig(format='%(asctime)s - %(message)s', level=level) # prepend log message with time
    logging.debug(args)

    # Output filename.
    if ofile is None:
        ofile = f"{variable}_{startpt[0]}N{startpt[1]}E-{endpt[0]}N{endpt[1]}E.png"
    else:
        ofile = args.ofile
    logging.info(f"output filename={ofile}")


    # Read lat/lon from gfile
    logging.debug(f"read lat/lon from {gfile}")
    gds  = xarray.open_dataset(gfile.name)
    lont = gds[fv3.lon_name]
    latt = gds[fv3.lat_name]

    # Open input file
    logging.debug(f"About to open {ifile}")
    fv3ds = xarray.open_dataset(ifile.name)
    datetimeindex = fv3ds.indexes['time']
    if hasattr(datetimeindex, "to_datetimeindex"):
        # Convert from CFTime to pandas datetime. I get a warning CFTimeIndex from non-standard calendar 'julian'. Maybe history file should be saved with standard calendar.
        datetimeindex = datetimeindex.to_datetimeindex()
    fv3ds['time'] = datetimeindex
    if subtract:
        logging.debug(f"subtracting {subtract.name}")
        with xarray.set_options(keep_attrs=True):
            fv3ds -= xarray.open_dataset(subtract.name)

    fv3ds = fv3ds.assign_coords(lont=lont, latt=latt) # lont and latt used by pcolorfill()
    tendency_vars = fv3.tendencies[variable] # list of tendency variable names for requested state variable
    fv3ds = fv3.add_time0(fv3ds, variable)
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
    # Plot all tendencies.
    da2plot = tendencies_avg
    # Add total and resid DataArrays to tendency_dim.
    total = total.expand_dims({tendency_dim:["total"]}).assign_coords(long_name="sum of tendencies")
    resid = resid.expand_dims({tendency_dim:["resid"]}).assign_coords(long_name=f"sum of tendencies - actual rate of change of {variable} (residual)")
    da2plot = xarray.concat([da2plot, total, resid], dim=tendency_dim)
    col = tendency_dim

    if da2plot.metpy.vertical.attrs["units"] == "mb":
        da2plot.metpy.vertical.attrs["units"] = "hPa" # For MetPy. Otherwise, mb is interpreted as millibarn.


    # Make default dimensions of facetgrid kind of square.
    if not ncols:
        # Default # of cols is square root of # of panels
        ncols = int(np.ceil(np.sqrt(len(da2plot))))

    nrows = int(np.ceil(len(da2plot)/ncols))

    # dequantify moves units from DataArray to Attributes. Now they show up in colorbar.
    da2plot = da2plot.metpy.dequantify()

    if da2plot["pfull"].size == 1:
        # Avoid ValueError: ('grid_yt', 'grid_xt') must be a permuted list of ('pfull', 'grid_yt', 'grid_xt'), unless `...` is included
        # Error occurs in pcolormesh().
        da2plot=da2plot.squeeze()

    # Kludgy steps to prepare metadata for metpy cross section
    da2plot = da2plot.drop_vars(['grid_yt','grid_xt','long_name']).rename(dict(grid_yt="y",grid_xt="x")) # these confuse metpy 
    # fv3 uses Extended Schmidt Gnomomic grid for regional applications. This is not in cartopy.
    # Found similar Lambert Conformal projection by trial and error.
    da2plot = da2plot.metpy.assign_crs( grid_mapping_name="lambert_conformal_conic", standard_parallel=fv3.standard_parallel, longitude_of_central_meridian=-97.5, latitude_of_projection_origin=fv3.standard_parallel).metpy.assign_y_x(force=True, tolerance=44069*units.m)
    # Define cross section. Use different variable than da2plot because da2plot is used later for inset.
    cross = cross_section(da2plot, startpt, endpt)

    logging.info("plot pcolormesh")
    w,h = 0.18, 0.18 # normalized width and height of inset. Shrink colorbar to provide space.
    pc = cross.plot.pcolormesh(x="index", y="pfull", col=col, col_wrap=ncols, robust=True, infer_intervals=True,
            cmap=fv3.cmap, cbar_kwargs={ 'shrink':1-h, 'anchor':(0,0.3-h)}) # robust (bool, optional) – If True and vmin or vmax are absent, the colormap range is computed with 2nd and 98th percentiles instead of the extreme values
    for ax in pc.axes.flat:
        ax.grid(visible=True, color="grey", alpha=0.5, lw=0.5)
        ax.xaxis.set_major_locator(MultipleLocator(dindex))
        ax.yaxis.set_major_locator(MultipleLocator(100))
        ax.yaxis.set_minor_locator(MultipleLocator(25))
        ax.grid(which="minor", alpha=0.3, lw=0.4)

    pc.axes[0,0].invert_yaxis() # tried in pc.axes loop but it didn't stick (maybe it flipped all axes back and forth with each iteration)

    # Add time to title and output filename
    root, ext = os.path.splitext(ofile)
    ofile = root + f".{time0.strftime('%Y%m%d_%H%M%S')}-{validtime.strftime('%Y%m%d_%H%M%S')}" + ext
    title = f'{time0}-{validtime} ({twindow_quantity.to("hours"):~} time window)'
    plt.suptitle(title, wrap=True)

    # Locate cross section on conus map background. Put in inset.
    data_crs = da2plot.metpy.cartopy_crs
    ax_inset = plt.gcf().add_axes([.999-w,.999-h, w, h], projection=data_crs)
    # Plot the endpoints of the cross section (make sure they match path)
    endpoints = data_crs.transform_points(cartopy.crs.Geodetic(), *np.vstack([startpt, endpt]).transpose()[::-1])
    bb = ax_inset.scatter(endpoints[:, 0], endpoints[:, 1], s=1.3, c='k', zorder=2)
    ax_inset.scatter(cross['x'][dindex::dindex], cross['y'][dindex::dindex], s=3.4, c='white', linewidths=0.2, edgecolors='k', zorder=bb.get_zorder()+1)
    # Plot the path of the cross section
    ax_inset.plot(cross['x'], cross['y'], c='k', zorder=2)
    fv3.add_conus_features(ax_inset)
    extent = fv3.extent
    ax_inset.set_extent(extent)

    # Annotate figure with details about figure creation. 
    fineprint  = f"history: {os.path.realpath(ifile.name)}"
    if subtract:
        fineprint  += f"\nsubtract: {os.path.realpath(subtract.name)}"
    fineprint += f"\ngrid_spec: {os.path.realpath(gfile.name)}"
    fineprint += f"\ncreated {datetime.datetime.now(tz=None)}"
    fineprint_obj = plt.annotate(text=fineprint, xy=(1,1), xycoords='figure pixels', fontsize=5)


    plt.savefig(ofile, dpi=fv3.dpi)
    logging.info(f'created {os.path.realpath(ofile)}')

if __name__ == "__main__":
    main()
