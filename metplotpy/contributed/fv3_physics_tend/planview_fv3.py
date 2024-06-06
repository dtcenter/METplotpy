""" Plan view of tendencies """
import argparse
import datetime
import logging
import os
import cartopy
import matplotlib.pyplot as plt
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
        description="Plan view of FV3 diagnostic tendencies",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    # ==========Mandatory Arguments===================
    parser.add_argument("config", help="yaml configuration file")
    parser.add_argument("historyfile", help="FV3 history file")
    parser.add_argument("gridfile", help="FV3 grid spec file")
    parser.add_argument(
        "statevariable", help="moisture, temperature, or wind component variable name")
    parser.add_argument(
        "tendencytype", help='type of tendency. ignored if pfull is a single level')
    # ==========Optional Arguments===================
    parser.add_argument("-d", "--debug", action='store_true')
    parser.add_argument("--method", choices=["nearest", "linear", "loglinear"], default="nearest",
                        help="vertical interpolation method")
    parser.add_argument("--ncols", type=int, default=None,
                        help="number of columns")
    parser.add_argument("--nofineprint", action='store_true',
                        help="Don't add metadata and created by date (for comparing images)")
    parser.add_argument("--norobust", action='store_true',
                        help="compute colormap range with extremes, not 2nd and 98th percentiles")
    parser.add_argument("-o", "--ofile", help="name of output image file")
    parser.add_argument("-p", "--pfull", nargs='+', type=float,
                        default=[1000, 925, 850, 700, 500, 300, 200, 100, 0],
                        help=("pressure level(s) in hPa to plot. "
                              "If only one pressure level is provided, the type-of-tendency "
                              "argument will be ignored and all tendencies will be plotted.")
                        )
    parser.add_argument("-s", "--shp", help="shape file directory for mask")
    parser.add_argument("--subtract", help="FV3 history file to subtract")
    parser.add_argument("-t", "--twindow", type=float,
                        default=3, help="time window in hours")
    parser.add_argument("-v", "--validtime", help="valid time")
    parser.add_argument("--vmin", type=float,
                        help="color bar minimum (overrides robust=True)")
    parser.add_argument("--vmax", type=float,
                        help="color bar maximum (overrides robust=True)")

    args = parser.parse_args()
    return args

def main():
    """
    Plan view of tendencies of t, q, u, or v from physics parameterizations,
    dynamics (non-physics), the combination of all tendencies (physics and non-physics),
    the actual tendency, and the residual. Residual is the sum of all tendencies minus the
    actual tendency.
    """
    args = parse_args()
    gfile = args.gridfile
    ifile = args.historyfile
    variable = args.statevariable
    tendencytype = args.tendencytype
    config = args.config
    method = args.method
    ncols = args.ncols
    nofineprint = args.nofineprint
    ofile = args.ofile
    pfull = args.pfull * units.hPa
    robust = not args.norobust
    shp = args.shp
    subtract = args.subtract
    twindow = datetime.timedelta(hours=args.twindow)
    twindow_quantity = twindow.total_seconds() * units.seconds
    validtime = pd.to_datetime(args.validtime)
    vmin = args.vmin
    vmax = args.vmax

    level = logging.INFO
    if args.debug:
        level = logging.DEBUG
    # prepend log message with time
    logging.basicConfig(format='%(asctime)s - %(message)s', level=level)
    logging.debug(args)

    # Output filename.
    if ofile is None:
        ofile = default_ofile(args)
    else:
        ofile = os.path.realpath(args.ofile)
        odir = os.path.dirname(ofile)
        if not os.path.exists(odir):
            logging.info(
                f"output directory {odir} does not exist. Creating it")
            os.mkdir(odir)
    logging.debug("output filename=%s", ofile)

    # Reload fv3 in case user specifies a custom --config file
    fv3 = yaml.load(open(config, encoding="utf8"), Loader=yaml.FullLoader)

    # Read lat/lon/area from gfile
    logging.debug(f"read lat/lon/area from {gfile}")
    gds = xarray.open_dataset(gfile)
    lont = gds[fv3["lon_name"]]
    latt = gds[fv3["lat_name"]]
    area = gds["area"]

    # Open input file
    logging.debug("open %s", ifile)
    fv3ds = xarray.open_dataset(ifile)

    if subtract:
        logging.info("subtracting %s", subtract)
        with xarray.set_options(keep_attrs=True):
            fv3ds -= xarray.open_dataset(subtract)

    datetimeindex = fv3ds.indexes['time']
    if hasattr(datetimeindex, "to_datetimeindex"):
        # Convert from CFTime to pandas datetime or get warning
        # CFTimeIndex from non-standard calendar 'julian'.
        # Maybe history file should be saved with standard calendar.
        # To turn off warning, set unsafe=True.
        datetimeindex = datetimeindex.to_datetimeindex(unsafe=True)
    ragged_times = datetimeindex != datetimeindex.round('1ms')
    if any(ragged_times):
        logging.info(
            f"round times to nearest millisec. before: {datetimeindex[ragged_times].values}")
        datetimeindex = datetimeindex.round('1ms')
        logging.info(f"after: {datetimeindex[ragged_times].values}")
    fv3ds['time'] = datetimeindex

    # lont and latt used by pcolorfill()
    fv3ds = fv3ds.assign_coords(lont=lont, latt=latt)

    if validtime is None:
        validtime = fv3ds.time.values[-1]
        validtime = pd.to_datetime(validtime)
        logging.info(
            "validtime not provided on command line. Using last time in history file %s.",
            validtime)
    time0 = validtime - twindow
    assert time0 in fv3ds.time, (f"time0 {time0} not in history file. Closest is "
                                 f"{fv3ds.time.sel(time=time0, method='nearest').time.data}")

    # list of tendency variable names for requested state variable
    tendency_vars = fv3["tendency_varnames"][variable]
    tendencies = fv3ds[tendency_vars]  # subset of original Dataset
    # convert DataArrays to Quantities to protect units. DataArray.mean drops units attribute.
    tendencies = tendencies.metpy.quantify()

    # Define time slice starting with time-after-time0 and ending with validtime.
    # We use the time *after* time0 because the time range corresponding to the tendency
    # output is the period immediately prior to the tendency timestamp.
    # That way, slice(time_after_time0, validtime) has a time range of [time0,validtime].
    idx_first_time_after_time0 = (fv3ds.time > time0).argmax()
    time_after_time0 = fv3ds.time[idx_first_time_after_time0]
    tindex = {"time": slice(time_after_time0, validtime)}
    logging.debug(
        "Time-weighted mean tendencies for time index slice %s", tindex)
    timeweights = fv3ds.time.diff("time").sel(tindex)
    time_weighted_tendencies = tendencies.sel(tindex) * timeweights
    tendencies_avg = time_weighted_tendencies.sum(
        dim="time") / timeweights.sum(dim="time")

    # Make list of long_names before .to_array() loses them.
    long_names = [fv3ds[da].attrs["long_name"] for da in tendencies_avg]

    # Keep characters after final underscore. The first part is redundant.
    # for example dtend_u_pbl -> pbl
    name_dict = {da: "_".join(da.split("_")[-1:])
                 for da in tendencies_avg.data_vars}
    logging.debug("rename %s", name_dict)
    tendencies_avg = tendencies_avg.rename(name_dict)

    # Stack variables along new tendency dimension of new DataArray.
    tendency_dim = f"{variable} tendency"
    tendencies_avg = tendencies_avg.to_array(dim=tendency_dim, name=tendency_dim)
    # Assign long_names to a new DataArray coordinate.
    # It will have the same shape as tendency dimension.
    tendencies_avg = tendencies_avg.assign_coords(
        {"long_name": (tendency_dim, long_names)})

    logging.info("calculate actual change in %s", variable)
    # Tried metpy.quantify() with open_dataset, but
    # pint.errors.UndefinedUnitError: 'dBz' is not defined in the unit registry
    state_variable = fv3ds[variable].metpy.quantify()
    actual_change = state_variable.sel(time=validtime) - state_variable.sel(
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
        all_tendencies = all_tendencies - \
            tendencies_avg.sel({tendency_dim: "phys"}).data

    # Calculate actual tendency of state variable.
    actual_tendency = actual_change / twindow_quantity
    logging.info(
        "subtract actual tendency from all_tendencies to get residual")
    resid = all_tendencies - actual_tendency

    # Concatenate all_tendencies, actual_tendency, and resid DataArrays.
    # Give them a name and long_name along tendency_dim.
    all_tendencies = all_tendencies.expand_dims({tendency_dim: ["all"]}).assign_coords(
        long_name="sum of tendencies")
    actual_tendency = actual_tendency.expand_dims({tendency_dim: ["actual"]}).assign_coords(
        long_name=f"actual rate of change of {variable}")
    resid = resid.expand_dims({tendency_dim: ["resid"]}).assign_coords(
        long_name=f"sum of tendencies - actual rate of change of {variable} (residual)")
    da2plot = xarray.concat(
        [tendencies_avg, all_tendencies, actual_tendency, resid], dim=tendency_dim)
    col = tendency_dim

    if len(pfull) > 1:
        # If more than one pressure level was specified
        col = "pfull"
        # just select one type of tendency
        da2plot = da2plot.sel({tendency_dim: tendencytype})

    if da2plot.metpy.vertical.attrs["units"] == "mb":
        # For MetPy. Otherwise, mb is interpreted as millibarn.
        da2plot.metpy.vertical.attrs["units"] = "hPa"

    # dequantify moves units from DataArray to attributes. Now they show up in colorbar.
    # And they aren't lost in xarray.DataArray.interp.
    da2plot = da2plot.metpy.dequantify()

    logging.info(f"Select vertical levels with '{method}' method")
    if method == "nearest":
        da2plot = da2plot.metpy.sel(
            vertical=pfull, method=method, tolerance=10.*units.hPa)
    elif method == "linear":
        da2plot = da2plot.interp(coords={"pfull": pfull}, method=method)
    elif method == "loglinear":  # interpolate in log10(pressure)
        da2plot["pfull"] = np.log10(da2plot.pfull)
        da2plot = da2plot.interp(
            coords={"pfull": np.log10(pfull.m)}, method="linear")
        da2plot["pfull"] = 10**da2plot.pfull

    # Mask points outside shape.
    if shp is not None:
        # Use .values to avoid AttributeError: 'DataArray' object has no attribute 'flatten'
        mask = physics_tend.pts_in_shp(
            latt.values, lont.values, shp)
        mask = xarray.DataArray(
            mask, coords=[da2plot.grid_yt, da2plot.grid_xt])
        da2plot = da2plot.where(mask)


    # Make default dimensions of facetgrid kind of square.
    if not ncols:
        # Default # of cols is square root of # of panels
        ncols = int(np.ceil(np.sqrt(len(da2plot))))

    if da2plot["pfull"].size == 1:
        # Avoid ValueError in pcolormesh().
        da2plot = da2plot.squeeze()

    # central lon/lat from https://github.com/NOAA-EMC/regional_workflow/blob/
    # release/public-v1/ush/Python/plot_allvars.py
    # switching from central_latitude=35.4 to central_latitude=fv3["standard_parallel"]
    # (38.139 as of Aug 22, 2023) did not change plot appearance.
    subplot_kws = {
        "projection": cartopy.crs.LambertConformal(
            central_longitude=-97.6, central_latitude=35.4)}

    logging.debug("plot pcolormesh")
    if robust:
        logging.warning("compute colormap range with 2nd and 98th percentiles")
    pcm = da2plot.plot.pcolormesh(x="lont", y="latt", col=col, col_wrap=ncols, robust=robust,
                                  infer_intervals=True, transform=cartopy.crs.PlateCarree(),
                                  vmin=vmin, vmax=vmax, cmap=fv3["cmap"],
                                  cbar_kwargs={'shrink': 0.8}, subplot_kws=subplot_kws)
    for ax in pcm.axs.flat:
        # Why needed only when col=tendency_dim? With col="pfull" it shrinks to unmasked size.
        ax.set_extent(fv3["extent"])
        physics_tend.add_conus_features(ax)

    # Add time to title
    title = f'{time0}-{validtime} ({twindow_quantity.to("hours"):~} time window)'
    if col == tendency_dim:
        title = f'pfull={da2plot.pfull.metpy.quantify().data:~.1f} {title}'
    elif 'long_name' in da2plot.coords:
        title = f'{da2plot.coords["long_name"].data} {title}'
    plt.suptitle(title, wrap=True)

    # Annotate figure with args namespace and timestamp
    fineprint = f"{args} "
    fineprint += f"created {datetime.datetime.now(tz=None)}"
    if nofineprint:
        logging.debug(fineprint)
    else:
        logging.debug("add fineprint to image")
        plt.figtext(0, 0, fineprint, fontsize='xx-small',
                    va="bottom", wrap=True)

    plt.savefig(ofile, dpi=fv3["dpi"])
    logging.info('created %s', os.path.realpath(ofile))


def default_ofile(args):
    """
    Return default output filename.
    """
    pfull = args.pfull * units.hPa
    if len(pfull) == 1:
        pfull_str = f"{pfull[0]:~.0f}".replace(" ", "")
        ofile = f"{args.statevariable}_{pfull_str}.png"
    else:
        ofile = f"{args.statevariable}_{args.tendencytype}.png"
    if args.shp is not None:
        shp = shp.rstrip("/")
        # Add shapefile name to output filename
        shapename = os.path.basename(shp)
        root, ext = os.path.splitext(ofile)
        ofile = root + f".{shapename}" + ext
    return ofile


if __name__ == "__main__":
    main()
