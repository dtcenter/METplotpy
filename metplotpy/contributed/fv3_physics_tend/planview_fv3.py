""" Plan view of tendencies """

import argparse
import datetime
import logging
import os
import re

import cartopy
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray
import yaml
from metpy.units import units

from metplotpy.contributed.fv3_physics_tend import physics_tend


def parse_args():
    """
    parse command line arguments
    """

    # =============Arguments===================
    parser = argparse.ArgumentParser(
        description="Plan view of FV3 diagnostic tendencies",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    # ==========Mandatory Arguments===================
    parser.add_argument("config", help="yaml configuration file")
    parser.add_argument("historyfile", help="FV3 history file")
    parser.add_argument("gridfile", help="FV3 grid spec file")

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
    gridfile = args.gridfile
    historyfile = args.historyfile
    config = args.config
    fv3 = yaml.load(open(config, encoding="utf8"), Loader=yaml.FullLoader)

    ds = physics_tend.prepare_ds(fv3, historyfile, gridfile)

    pcm = planview(fv3, ds)

    ofile = default_ofile(fv3)
    pcm.fig.savefig(ofile, dpi=fv3["dpi"])
    logging.info("created %s", os.path.realpath(ofile))


def planview(fv3, fv3ds, **kwargs):
    # Override config file with keyword args
    fv3.update(kwargs)
    fineprint = fv3["fineprint"]
    ncols = fv3["ncols"]
    pfull = fv3["pfull"] * units.hPa
    robust = fv3["robust"]
    sel_method = fv3["sel_method"]
    shp = fv3["shp"]
    statevarname = fv3["statevarname"]
    tendencytype = fv3["tendencytype"]
    twindow = datetime.timedelta(hours=fv3["twindow"])
    twindow_quantity = twindow.total_seconds() * units.seconds
    validtime = fv3["validtime"]
    vmin = fv3["vmin"]
    vmax = fv3["vmax"]

    level = logging.INFO
    if fv3["debug"]:
        level = logging.DEBUG
    # prepend log message with time
    logging.basicConfig(format="%(asctime)s - %(message)s", level=level)

    if not validtime:
        validtime = fv3ds.time.values[-1]
        logging.info(
            "validtime not configured. Using last time in history %s.",
            validtime,
        )
    logging.debug(type(validtime))
    validtime = pd.to_datetime(validtime)
    logging.debug(f"twindow {twindow} validtime {validtime}")
    time0 = validtime - twindow
    logging.debug(f"time0 {time0}")

    # list of tendency variable names for requested state variable
    tendency_vars = fv3["tendency_varnames"][statevarname]
    logging.debug(f"tendency_vars {tendency_vars}")
    tendencies = fv3ds[tendency_vars]  # subset of original Dataset
    tendencies = tendencies.load()
    # convert DataArrays to Quantities to protect units. DataArray.mean drops units attribute.
    tendencies = tendencies.metpy.quantify()
    logging.info(tendencies.max())

    if fv3["tendencies_were_zeroed_and_averaged_after_every_output"]:
        logging.warning("assume tendencies_were_zeroed_and_averaged_after_every_output")
        assert time0 in fv3ds.time, (
            f"time0 {time0} not in history file. Closest is "
            f"{fv3ds.time.sel(time=time0, method='nearest').time.data}"
        )
        # Define time slice starting with time-after-time0 and ending with validtime.
        # We use the time *after* time0 because the time range corresponding to the tendency
        # output is the period immediately prior to the tendency timestamp.
        # That way, slice(time_after_time0, validtime) has a time range of [time0,validtime].
        idx_first_time_after_time0 = (fv3ds.time > time0).argmax()
        time_after_time0 = fv3ds.time[idx_first_time_after_time0]
        tindex = {"time": slice(time_after_time0, validtime)}
        logging.debug("Time-weighted mean tendencies for time index slice %s", tindex)
        timeweights = fv3ds.time.diff("time").sel(tindex)
        time_weighted_tendencies = tendencies.sel(tindex) * timeweights
        tendencies_avg = time_weighted_tendencies.sum(dim="time") / timeweights.sum(
            dim="time"
        )
        tendencies = tendencies_avg

    # Make list of long_names before .to_array() loses them.
    long_names = [fv3ds[da].attrs["long_name"] for da in tendencies]

    # Keep characters after final underscore. The first part is redundant.
    # for example dtend_u_pbl -> pbl
    name_dict = {da: "_".join(da.split("_")[-1:]) for da in tendencies.data_vars}
    logging.debug("rename %s", name_dict)
    tendencies = tendencies.rename(name_dict)

    # Stack variables along new tendency dimension of new DataArray.
    tendency_dim = f"{statevarname} tendency"
    tendencies = tendencies.to_array(dim=tendency_dim, name=tendency_dim)
    # Assign long_names to a new DataArray coordinate.
    # It will have the same shape as tendency dimension.
    tendencies = tendencies.assign_coords({"long_name": (tendency_dim, long_names)})

    logging.info("calculate actual change in %s", statevarname)
    # Tried metpy.quantify() with open_dataset, but
    # pint.errors.UndefinedUnitError: 'dBz' is not defined in the unit registry
    state_variable = fv3ds[statevarname].metpy.quantify()
    actual_change = state_variable.sel(time=validtime) - state_variable.sel(
        time=time0, method="nearest", tolerance=datetime.timedelta(milliseconds=1)
    )
    actual_change = actual_change.assign_coords(time=validtime)
    actual_change.attrs["long_name"] = (
        f"actual change in {state_variable.attrs['long_name']}"
    )

    # Sum all tendencies (physics and non-physics)
    all_tendencies = tendencies.sum(dim=tendency_dim)

    # Subtract physics tendency variable if it was in tendency_vars. Don't want to double-count.
    phys_var = [x for x in tendency_vars if x.endswith("_phys")]
    if phys_var:
        logging.info(
            "subtracting 'phys' tendency variable "
            "from all_tendencies to avoid double-counting"
        )
        # use .data to avoid re-introducing tendency coordinate
        all_tendencies = all_tendencies - tendencies.sel({tendency_dim: "phys"}).data

    # Calculate actual tendency of state variable.
    actual_tendency = actual_change / twindow_quantity
    logging.info("subtract actual tendency from all_tendencies to get residual")
    resid = all_tendencies - actual_tendency

    # Concatenate all_tendencies, actual_tendency, and resid DataArrays.
    # Give them a name and long_name along tendency_dim.
    all_tendencies = all_tendencies.expand_dims({tendency_dim: ["all"]}).assign_coords(
        long_name="sum of tendencies"
    )
    actual_tendency = actual_tendency.expand_dims(
        {tendency_dim: ["actual"]}
    ).assign_coords(long_name=f"actual rate of change of {statevarname}")
    resid = resid.expand_dims({tendency_dim: ["resid"]}).assign_coords(
        long_name=f"sum of tendencies - actual rate of change of {statevarname} (residual)"
    )
    da2plot = xarray.concat(
        [tendencies, all_tendencies, actual_tendency, resid], dim=tendency_dim
    )

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

    logging.info(f"Select vertical levels with '{sel_method}' method")
    if sel_method == "nearest":
        da2plot = da2plot.metpy.sel(
            vertical=pfull, method=sel_method, tolerance=10.0 * units.hPa
        )
    elif sel_method == "linear":
        da2plot = da2plot.interp(coords={"pfull": pfull}, method=sel_method)
    elif sel_method == "loglinear":  # interpolate in log10(pressure)
        da2plot["pfull"] = np.log10(da2plot.pfull)
        da2plot = da2plot.interp(coords={"pfull": np.log10(pfull.m)}, method="linear")
        da2plot["pfull"] = 10**da2plot.pfull

    # Mask points outside shape.
    if shp:
        # Use .values to avoid AttributeError: 'DataArray' object has no attribute 'flatten'
        mask = physics_tend.pts_in_shp(latt.values, lont.values, shp)
        mask = xarray.DataArray(mask, coords=[da2plot.grid_yt, da2plot.grid_xt])
        da2plot = da2plot.where(mask)

    # Make default dimensions of Facetgrid kind of square.
    if not ncols:
        # Default # of cols is square root of # of panels
        ncols = int(np.ceil(np.sqrt(len(da2plot))))

    da2plot = (
        da2plot.load()
    )  # avoid multiple UserWarning: Sending large graph of size 324.02 MiB.
    # pfull is size-1 or ValueError: cannot select a dimension to squeeze out which has length greater than one
    if da2plot.pfull.size == 1:
        da2plot = da2plot.squeeze(dim="pfull")  # Avoid ValueError in pcolormesh().

    # central lon/lat from https://github.com/NOAA-EMC/regional_workflow/blob/
    # release/public-v1/ush/Python/plot_allvars.py
    # switching from central_latitude=35.4 to central_latitude=fv3["standard_parallel"]
    # (38.139 as of Aug 22, 2023) did not change plot appearance.
    subplot_kws = {
        "projection": cartopy.crs.LambertConformal(
            central_longitude=-97.6, central_latitude=35.4
        )
    }

    logging.debug("plot pcolormesh")
    if robust:
        logging.warning("compute colormap range with 2nd and 98th percentiles")
    pcm = da2plot.plot.pcolormesh(
        x="lont",
        y="latt",
        col=col,
        col_wrap=ncols,
        robust=robust,
        infer_intervals=True,
        transform=cartopy.crs.PlateCarree(),
        vmin=vmin,
        vmax=vmax,
        cmap=fv3["cmap"],
        cbar_kwargs={"shrink": 0.8},
        subplot_kws=subplot_kws,
    )
    for ax in pcm.axs.flat:
        # Why needed only when col=tendency_dim? With col="pfull" it shrinks to unmasked size.
        ax.set_extent(fv3["extent"])
        physics_tend.add_conus_features(ax)

    # Add time to title
    title = f'{time0}-{validtime} ({twindow_quantity.to("hours"):~} time window)'
    if col == tendency_dim:
        title = f"pfull={da2plot.pfull.metpy.quantify().data:~.1f} {title}"
    elif "long_name" in da2plot.coords:
        title = f'{da2plot.coords["long_name"].data} {title}'
    plt.suptitle(title, wrap=True)

    # Annotate figure with timestamp
    fineprint_str = f"created {datetime.datetime.now(tz=None)}"
    if fineprint:
        logging.debug("add fineprint to image")
        plt.figtext(0, 0, fineprint_str, fontsize="xx-small", va="bottom", wrap=True)
    else:
        logging.debug(fineprint_str)

    return pcm


def default_ofile(fv3):
    """
    Return default output filename.
    """
    pfull = fv3["pfull"] * units.hPa
    if len(pfull) == 1:
        pfull_str = f"{pfull[0]:~.0f}".replace(" ", "")
        ofile = f"{fv3["statevarname"]}_{pfull_str}.png"
    else:
        ofile = f"{fv3["statevarname"]}_{fv3["tendencytype"]}.png"
    if fv3["shp"]:
        shp = fv3["shp"].rstrip("/")
        # Add shapefile name to output filename
        shapename = os.path.basename(shp)
        root, ext = os.path.splitext(ofile)
        ofile = root + f".{shapename}" + ext
    ofile = physics_tend.TMPDIR / ofile
    return ofile


if __name__ == "__main__":
    main()
