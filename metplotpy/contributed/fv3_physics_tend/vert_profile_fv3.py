""" Vertical profile of tendencies """
import argparse
import datetime
import logging
import os
import cartopy
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
from metpy.units import units
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
        description="Vertical profile of FV3 diagnostic tendencies",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    # ==========Mandatory Arguments===================
    parser.add_argument("config", help="yaml configuration file")
    parser.add_argument("historyfile", help="FV3 history file")
    parser.add_argument("gridfile", help="FV3 grid spec file")
    parser.add_argument(
        "statevariable", help="moisture, temperature, or wind component variable name")
    # ==========Optional Arguments===================
    parser.add_argument("-d", "--debug", action='store_true')
    parser.add_argument("--nofineprint", action='store_true',
                        help="Don't add metadata and created by date (for comparing images)")
    parser.add_argument("-o", "--ofile", help="name of output image file")
    parser.add_argument("--resid", action="store_true",
                        help="calculate residual")
    parser.add_argument("-s", "--shp", help="shape file directory for mask")
    parser.add_argument("--subtract", help="FV3 history file to subtract")
    parser.add_argument("-t", "--twindow", type=float,
                        default=3, help="time window in hours")
    parser.add_argument("-v", "--validtime", help="valid time")
    parser.add_argument("--xmin", type=float, help="x-axis minimum")
    parser.add_argument("--xmax", type=float, help="x-axis maximum")

    args = parser.parse_args()
    return args

def main():
    """
    Vertical profile of tendencies of t, q, u, or v from physics parameterizations,
    dynamics (non-physics), the combination of all tendencies (physics and non-physics),
    the actual tendency, and the residual. Residual is the sum of all tendencies minus the
    actual tendency.
    """
    args = parse_args()
    gfile = args.gridfile
    ifile = args.historyfile
    variable = args.statevariable
    config = args.config
    nofineprint = args.nofineprint
    ofile = args.ofile
    shp = args.shp
    subtract = args.subtract
    twindow = datetime.timedelta(hours=args.twindow)
    twindow_quantity = twindow.total_seconds() * units.seconds
    validtime = pd.to_datetime(args.validtime)
    xmin = args.xmin
    xmax = args.xmax

    level = logging.INFO
    if args.debug:
        level = logging.DEBUG
    # prepend log message with time
    logging.basicConfig(format='%(asctime)s - %(message)s', level=level)
    logging.debug(args)

    # Output filename.
    if ofile is None:
        ofile = f"{variable}.vert_profile.png"
        if shp:
            shp = shp.rstrip("/")
            # Add shapefile name to output filename
            shapename = os.path.basename(shp)
            root, ext = os.path.splitext(ofile)
            ofile = root + f".{shapename}" + ext
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

    da2plot = tendencies_avg
    if args.resid:
        # Concatenate all_tendencies, actual_tendency, and resid DataArrays.
        # Give them a name and long_name along tendency_dim.
        all_tendencies = all_tendencies.expand_dims({tendency_dim: ["all"]}).assign_coords(
            long_name="sum of tendencies")
        actual_tendency = actual_tendency.expand_dims({tendency_dim: ["actual"]}).assign_coords(
            long_name=f"actual rate of change of {variable}")
        resid = resid.expand_dims({tendency_dim: ["resid"]}).assign_coords(
            long_name=f"sum of tendencies - actual rate of change of {variable} (residual)")
        da2plot = xarray.concat(
            [da2plot, all_tendencies, actual_tendency, resid], dim=tendency_dim)


    # Mask points outside shape.
    if shp is not None:
        # Use .values to avoid AttributeError: 'DataArray' object has no attribute 'flatten'
        mask = physics_tend.pts_in_shp(
            latt.values, lont.values, shp)
        mask = xarray.DataArray(
            mask, coords=[da2plot.grid_yt, da2plot.grid_xt])
        da2plot = da2plot.where(mask)

    logging.info("area-weighted spatial average")
    da2plot = da2plot.weighted(area).mean(area.dims)
    # Put units in attributes so they show up in xlabel.
    # dequantify after area-weighted mean to preserve units.
    da2plot = da2plot.metpy.dequantify()

    logging.info("creating figure")
    _, ax = plt.subplots()
    plt.subplots_adjust(bottom=0.18)  # add space at bottom for fine print
    ax.invert_yaxis()  # pressure increases from top to bottom
    ax.grid(visible=True, color="grey", alpha=0.5, lw=0.5)
    ax.yaxis.set_major_locator(MultipleLocator(100))
    ax.yaxis.set_minor_locator(MultipleLocator(25))
    ax.grid(which='minor', alpha=0.3, lw=0.4)

    logging.info("plot area-weighted spatial average...")
    lines = da2plot.plot.line(
        y="pfull", ax=ax, xlim=(xmin, xmax), hue=tendency_dim)

    if args.resid:
        # Add special marker to actual_change and residual lines.
        # DataArray plot legend handles differ from the plot lines, for some reason. So if you
        # change the style of a line later, it is not automatically changed in the legend.
        # zip d{variable}, resid line and their respective legend handles together and change
        # their style together.
        # [-2:] means take last two elements of da2plot.
        special_lines = list(zip(lines, ax.get_legend().legendHandles))[-2:]
        special_marker = 'o'
        special_marker_size = 3
        for line, leghandle in special_lines:
            line.set_marker(special_marker)
            line.set_markersize(special_marker_size)
            leghandle.set_marker(special_marker)
            leghandle.set_markersize(special_marker_size)

    # Add time to title
    title = f'{time0}-{validtime} ({twindow_quantity.to("hours"):~} time window)'
    ax.set_title(title, wrap=True)

    if shp is not None:
        # Locate region of interest on conus map background. Put in inset.
        projection = cartopy.crs.LambertConformal(
            central_longitude=-97.5, central_latitude=fv3["standard_parallel"])
        ax_inset = plt.gcf().add_axes(
            [.7, .001, .19, .13], projection=projection)
        # astype(int) to avoid TypeError: numpy boolean subtract
        cbar_kwargs = {"ticks":[0.25, 0.75], "shrink":0.6}
        pcm = mask.assign_coords(lont=lont, latt=latt).astype(int).plot.pcolormesh(
            ax=ax_inset, x="lont", y="latt", infer_intervals=True,
            transform=cartopy.crs.PlateCarree(), cmap=plt.cm.get_cmap('cool', 2),
            add_labels=False, cbar_kwargs=cbar_kwargs)
        pcm.colorbar.ax.set_yticklabels(
            ["masked", "valid"], fontsize='xx-small')
        pcm.colorbar.outline.set_visible(False)
        physics_tend.add_conus_features(ax_inset)
        extent = fv3["extent"]
        ax_inset.set_extent(extent)

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


if __name__ == "__main__":
    main()
