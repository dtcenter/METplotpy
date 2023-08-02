""" vertcal cross section of tendencies """
import argparse
import datetime
import logging
import os
import cartopy
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
from metpy.interpolate import cross_section
from metpy.units import units
import numpy as np
import pandas as pd
import xarray
import yaml
import physics_tend


def parse_args():
    """
    parse command line arguments
    """

    # =============Arguments===================
    parser = argparse.ArgumentParser(
            description = "Vertical cross section of FV3 diagnostic tendency",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    # ==========Mandatory Arguments===================
    parser.add_argument("config", help="yaml configuration file")
    parser.add_argument("historyfile", help="FV3 history file")
    parser.add_argument("gridfile", help="FV3 grid spec file")
    parser.add_argument("statevariable", help="moisture, temperature, or wind component variable name")
    # ==========Optional Arguments===================
    parser.add_argument("-d", "--debug", action='store_true')
    parser.add_argument("--dindex", type=int, default=20, help="tick and gridline interval along cross section")
    parser.add_argument("--ncols", type=int, default=None, help="number of columns")
    parser.add_argument("--nofineprint", action='store_true',
            help="Don't add metadata and created by date (for comparing images)")
    parser.add_argument("--norobust", action='store_true',
            help="compute colormap range with extremes, not 2nd and 98th percentiles")
    parser.add_argument("-o", "--ofile", help="name of output image file")
    parser.add_argument("-s", "--start", nargs=2, type=float, default=(28, -115), help="start point")
    parser.add_argument("-e", "--end", nargs=2, type=float, default=(30, -82), help="end point")
    parser.add_argument("--subtract", help="FV3 history file to subtract")
    parser.add_argument("-t", "--twindow", type=float, default=3, help="time window in hours")
    parser.add_argument("-v", "--validtime", help="valid time")

    args = parser.parse_args()
    return args

def main():
    """
    Plan view of tendencies of t, q, u, or v from physics parameterizations, dynamics (non-physics), their total, and residual.
    Total change is the actual change in state variable from first time to last time. Total change differs from cumulative change
    attributed to physics and non-physics tendencies when residual is not zero.
    """
    args = parse_args()
    gfile      = args.gridfile
    ifile      = args.historyfile
    variable   = args.statevariable
    config     = args.config
    debug      = args.debug
    dindex     = args.dindex
    ncols      = args.ncols
    nofineprint= args.nofineprint
    ofile      = args.ofile
    startpt    = args.start
    endpt      = args.end
    subtract   = args.subtract
    twindow    = datetime.timedelta(hours = args.twindow)
    twindow_quantity = twindow.total_seconds() * units.seconds
    validtime  = pd.to_datetime(args.validtime)

    level = logging.INFO
    if debug:
        level = logging.DEBUG
    # prepend log message with time
    logging.basicConfig(format='%(asctime)s - %(message)s', level=level)
    logging.debug(args)

    # Output filename.
    if ofile is None:
        ofile = f"{variable}_{startpt[0]}N{startpt[1]}E-{endpt[0]}N{endpt[1]}E.png"
    else:
        ofile = os.path.realpath(args.ofile)
        odir = os.path.dirname(ofile)
        if not os.path.exists(odir):
            logging.info(f"output directory {odir} does not exist. Creating it")
            os.mkdir(odir)
    logging.info("output filename=%s", ofile)


    # Reload fv3 in case user specifies a custom --config file
    fv3 = yaml.load(open(config, encoding="utf8"), Loader=yaml.FullLoader)

    # Read lat/lon from gfile
    logging.debug(f"read lat/lon from {gfile}")
    gds  = xarray.open_dataset(gfile)
    lont = gds[fv3["lon_name"]]
    latt = gds[fv3["lat_name"]]

    # Open input file
    logging.debug("open %s", ifile)
    fv3ds = xarray.open_dataset(ifile)
    datetimeindex = fv3ds.indexes['time']
    if hasattr(datetimeindex, "to_datetimeindex"):
        # Convert from CFTime to pandas datetime or get warning
        # CFTimeIndex from non-standard calendar 'julian'.
        # Maybe history file should be saved with standard calendar.
        # To turn off warning, set unsafe=True.
        datetimeindex = datetimeindex.to_datetimeindex(unsafe=True)
    ragged_times = datetimeindex != datetimeindex.round('1ms')
    if any(ragged_times):
        logging.info(f"round times to nearest millisecond. before: {datetimeindex[ragged_times].values}")
        datetimeindex = datetimeindex.round('1ms')
        logging.info(f"after: {datetimeindex[ragged_times].values}")
    fv3ds['time'] = datetimeindex
    if subtract:
        logging.info("subtracting %s", subtract)
        with xarray.set_options(keep_attrs=True):
            fv3ds -= xarray.open_dataset(subtract)

    fv3ds = fv3ds.assign_coords(lont=lont, latt=latt) # lont and latt used by pcolorfill()

    if validtime is None:
        validtime = fv3ds.time.values[-1]
        validtime = pd.to_datetime(validtime)
        logging.info(
                "validtime not provided on command line. Using last time in history file %s.",
                validtime)
    time0 = validtime - twindow
    if time0 not in fv3ds.time:
        logging.info("time0 %s not in history file. add it.", time0)
        fv3ds = physics_tend.add_time0(fv3ds, variable, fv3)

    # list of tendency variable names for requested state variable
    tendency_vars = fv3["tendency_varnames"][variable]
    tendencies = fv3ds[tendency_vars] # subset of original Dataset
    # convert DataArrays to Quantities to protect units. DataArray.mean drops units attribute.
    tendencies = tendencies.metpy.quantify()

    # Define time slice starting with time-after-time0 and ending with validtime.
    # We use the time *after* time0 because the time range of the tendency field is the period
    # immediately prior to the tendency timestamp.
    # That way, slice(time_after_time0, validtime) has a time range of [time0,validtime].
    idx_first_time_after_time0 = (fv3ds.time > time0).argmax()
    time_after_time0 = fv3ds.time[idx_first_time_after_time0]
    tindex = {"time":slice(time_after_time0, validtime)}
    logging.debug("Time-weighted mean tendencies for time index slice %s", tindex)
    timeweights = fv3ds.time.diff("time").sel(tindex)
    time_weighted_tendencies = tendencies.sel(tindex) * timeweights
    tendencies_avg = time_weighted_tendencies.sum(dim="time") / timeweights.sum(dim="time")

    # Make list of long_names before .to_array() loses them.
    long_names = [fv3ds[da].attrs["long_name"] for da in tendencies_avg]

    # Keep characters after final underscore. The first part is redundant.
    # for example dtend_u_pbl -> pbl
    name_dict = {da : "_".join(da.split("_")[-1:]) for da in tendencies_avg.data_vars}
    logging.info("rename %s", name_dict)
    tendencies_avg = tendencies_avg.rename(name_dict)


    # Stack variables along new tendency dimension of new DataArray.
    tendency_dim = f"{variable} tendency"
    tendencies_avg = tendencies_avg.to_array(dim=tendency_dim)
    # Assign long_names to a new DataArray coordinate.
    # It will have the same shape as tendency dimension.
    tendencies_avg = tendencies_avg.assign_coords({"long_name":(tendency_dim,long_names)})

    logging.info("calculate actual change in %s", variable)
    # Tried metpy.quantify() with open_dataset, but
    # pint.errors.UndefinedUnitError: 'dBz' is not defined in the unit registry
    state_variable = fv3ds[variable].metpy.quantify()
    actual_change = state_variable.sel(time = validtime) - state_variable.sel(
            time=time0, method="nearest", tolerance=datetime.timedelta(milliseconds=1))
    actual_change = actual_change.assign_coords(time=validtime)
    actual_change.attrs["long_name"] = f"actual change in {state_variable.attrs['long_name']}"


    # Sum all tendencies (physics and non-physics)
    all_tendencies = tendencies_avg.sum(dim=tendency_dim)

    # Subtract physics tendency variable if it was in tendency_vars. Don't want to double-count.
    phys_var = [x for x in tendency_vars if x.endswith("_phys")]
    if phys_var:
        logging.info("subtracting 'phys' tendency variable "
                     "from all_tendencies to avoid double-counting")
        # use .data to avoid re-introducing tendency coordinate
        all_tendencies = all_tendencies - tendencies_avg.sel({tendency_dim:"phys"}).data

    # Calculate actual tendency of state variable.
    actual_tendency = actual_change / twindow_quantity
    logging.info("subtract actual tendency from all_tendencies to get residual")
    resid = all_tendencies - actual_tendency


    logging.debug("Define DataArray to plot (da2plot).")
    # Plot all tendencies.
    da2plot = tendencies_avg
    # Concatenate all_tendencies, actual_tendency, and resid DataArrays.
    # Give them a name and long_name along tendency_dim.
    all_tendencies = all_tendencies.expand_dims({tendency_dim:["all"]}).assign_coords(
            long_name="sum of tendencies")
    actual_tendency = actual_tendency.expand_dims({tendency_dim:["actual"]}).assign_coords(
            long_name=f"actual rate of change of {variable}")
    resid = resid.expand_dims({tendency_dim:["resid"]}).assign_coords(
            long_name=f"sum of tendencies - actual rate of change of {variable} (residual)")
    da2plot = xarray.concat([da2plot, all_tendencies, actual_tendency, resid], dim=tendency_dim)
    col = tendency_dim

    if da2plot.metpy.vertical.attrs["units"] == "mb":
        da2plot.metpy.vertical.attrs["units"] = "hPa" # For MetPy. Otherwise, mb is interpreted as millibarn.

    # dequantify moves units from DataArray to attributes. Now they show up in colorbar.
    # And they aren't lost in xarray.DataArray.interp.
    da2plot = da2plot.metpy.dequantify()


    # Make default dimensions of facetgrid kind of square.
    if not ncols:
        # Default # of cols is square root of # of panels
        ncols = int(np.ceil(np.sqrt(len(da2plot))))

    if da2plot["pfull"].size == 1:
        # Avoid ValueError: ('grid_yt', 'grid_xt') must be a
        # permuted list of ('pfull', 'grid_yt', 'grid_xt'), unless `...` is included
        # Error occurs in pcolormesh().
        da2plot=da2plot.squeeze()

    # Kludgy steps to prepare metadata for metpy cross section
    da2plot = da2plot.drop_vars(['grid_yt','grid_xt','long_name']).rename(dict(grid_yt="y",grid_xt="x")) # these confuse metpy 
    # fv3 uses Extended Schmidt Gnomomic grid for regional applications. This is not in cartopy.
    # Found similar Lambert Conformal projection by trial and error.
    da2plot = da2plot.metpy.assign_crs( grid_mapping_name="lambert_conformal_conic", standard_parallel=fv3["standard_parallel"], longitude_of_central_meridian=-97.5, latitude_of_projection_origin=fv3["standard_parallel"]).metpy.assign_y_x(force=True, tolerance=44069*units.m)
    # Define cross section. Use different variable than da2plot because da2plot is used later for inset.
    # upgraded xarray to 0.21.1 to avoid FutureWarning: Passing method to Float64Index.get_loc is deprecated
    cross = cross_section(da2plot, startpt, endpt)


    logging.info("plot pcolormesh")
    w,h = 0.18, 0.18 # normalized width and height of inset. Shrink colorbar to provide space.
    pc = cross.plot.pcolormesh(x="index", y="pfull", yincrease=False, col=col, col_wrap=ncols, robust=True, infer_intervals=True,
            cmap=fv3["cmap"], cbar_kwargs={'shrink':1-h, 'anchor':(0,0.25-h)}) # robust (bool, optional) – If True and vmin or vmax are absent, the colormap range is computed with 2nd and 98th percentiles instead of the extreme values
    for ax in pc.axes.flat:
        ax.grid(visible=True, color="grey", alpha=0.5, lw=0.5)
        ax.xaxis.set_major_locator(MultipleLocator(dindex))
        ax.yaxis.set_major_locator(MultipleLocator(100))
        ax.yaxis.set_minor_locator(MultipleLocator(25))
        ax.grid(which="minor", alpha=0.3, lw=0.4)

    # Add time to title
    title = f'{time0}-{validtime} ({twindow_quantity.to("hours"):~} time window)'
    plt.suptitle(title, wrap=True)
    # pad top and bottom for title and fineprint. Unfortunately, you must redefine right pad, as xarray no longer controls it. 
    plt.subplots_adjust(top=0.9,right=0.8,bottom=0.1)

    # Locate cross section on conus map background. Put in inset.
    data_crs = da2plot.metpy.cartopy_crs
    ax_inset = plt.gcf().add_axes([.999-w,.999-h, w, h], projection=data_crs)
    # Plot the endpoints of the cross section (make sure they match path)
    endpoints = data_crs.transform_points(cartopy.crs.Geodetic(), *np.vstack([startpt, endpt]).transpose()[::-1])
    bb = ax_inset.scatter(endpoints[:, 0], endpoints[:, 1], s=1.3, c='k', zorder=2)
    ax_inset.scatter(cross['x'][dindex::dindex], cross['y'][dindex::dindex], s=3.4, c='white', linewidths=0.2, edgecolors='k', zorder=bb.get_zorder()+1)
    # Plot the path of the cross section
    ax_inset.plot(cross['x'], cross['y'], c='k', zorder=2)
    physics_tend.add_conus_features(ax_inset)
    extent = fv3["extent"]
    ax_inset.set_extent(extent)

    # Annotate figure with args namespace and timestamp
    fineprint  = f"{args} "
    fineprint += f", created {datetime.datetime.now(tz=None)}"
    if nofineprint:
        logging.debug(fineprint)
    else:
        logging.debug("add fineprint to image")
        plt.figtext(0, 0, fineprint, fontsize='xx-small', va="bottom", wrap=True)


    plt.savefig(ofile, dpi=fv3["dpi"])
    logging.info('created %s',os.path.realpath(ofile))

if __name__ == "__main__":
    main()
