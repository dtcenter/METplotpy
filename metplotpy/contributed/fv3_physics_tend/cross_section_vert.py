""" vertcal cross section of tendencies """

import argparse
import datetime
import logging
import os

import cartopy
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray
import yaml
from matplotlib.ticker import MultipleLocator
from metpy.interpolate import cross_section
from metpy.units import units

from metplotpy.contributed.fv3_physics_tend import physics_tend


def parse_args():
    """
    parse command line arguments
    """

    # =============Arguments===================
    parser = argparse.ArgumentParser(
        description="Vertical cross section of FV3 diagnostic tendencies",
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
    Vertical cross section view of tendencies of t, q, u, or v from physics parameterizations,
    dynamics (non-physics), the combination of all tendencies (physics and non-physics),
    the actual tendency, and the residual. Residual is the sum of all tendencies minus the
    actual tendency.
    """
    args = parse_args()
    gridfile = args.gridfile
    historyfile = args.historyfile
    config = yaml.load(open(args.config, encoding="utf8"), Loader=yaml.FullLoader)

    ds = physics_tend.prepare_ds(config, historyfile, gridfile)

    pcm = cross_section_vert(config, ds)

    startpt = config["startpt"]
    endpt = config["endpt"]
    ofile = (
        physics_tend.TMPDIR
        / f"{config['statevarname']}_{startpt[0]}N{startpt[1]}E-{endpt[0]}N{endpt[1]}E.png"
    )
    pcm.fig.savefig(ofile, dpi=config["dpi"])
    logging.info("created %s", os.path.realpath(ofile))


# Don't name `cross_section` metpy already has this method.
def cross_section_vert(config, fv3ds, **kwargs):
    # Override config file with keyword args
    config.update(kwargs)
    fineprint = config["fineprint"]
    ncols = config["ncols"]
    startpt = config["startpt"]
    endpt = config["endpt"]
    robust = config["robust"]
    statevarname = config["statevarname"]
    twindow = datetime.timedelta(hours=config["twindow"])
    twindow_quantity = twindow.total_seconds() * units.seconds
    validtime = config["validtime"]
    vmin = config["vmin"]
    vmax = config["vmax"]

    level = logging.INFO
    if config["debug"]:
        level = logging.DEBUG
    # prepend log message with time
    logging.basicConfig(format="%(asctime)s - %(message)s", level=level)

    if not validtime:
        validtime = fv3ds.time.values[-1]
        logging.info(
            "validtime not configured. Using last time in history %s.",
            validtime,
        )
    validtime = pd.to_datetime(validtime)
    if "validtime" in fv3ds.attrs:
        assert pd.to_datetime(fv3ds.attrs["validtime"]) == validtime, (
            f"config validtime {validtime} != Dataset validtime {fv3ds.attrs['validtime']}" 
        )
    if "twindow" in fv3ds.attrs:
        assert datetime.timedelta(hours=fv3ds.attrs["twindow"]) == twindow, (
            f"config twindow {twindow} != Dataset twindow {fv3ds.attrs['twindow']}" 
        )
    logging.debug(f"twindow {twindow} validtime {validtime}")
    twindow_start = validtime - twindow
    logging.debug(f"twindow_start {twindow_start}")

    # list of tendency variable names for requested state variable
    tendency_vars = config["tendency_varnames"][statevarname]
    logging.debug(f"tendency_vars {tendency_vars}")
    tendencies = fv3ds[tendency_vars]  # subset of original Dataset
    tendencies = tendencies.load()
    # convert DataArrays to Quantities to protect units. DataArray.mean drops units attribute.
    tendencies = tendencies.metpy.quantify()
    logging.info(tendencies.max())

    if config["tendencies_were_zeroed_and_averaged_after_every_output"]:
        logging.warning("assume tendencies_were_zeroed_and_averaged_after_every_output")
        assert twindow_start in fv3ds.time, (
            f"twindow_start {twindow_start} not in history file. Closest is "
            f"{fv3ds.time.sel(time=twindow_start, method='nearest').time.data}"
        )
        # Define time slice starting with the first time after twindow_start and ending with validtime.
        # We use the time *after* twindow_start because the time range corresponding to the tendency
        # output is the period immediately prior to the tendency timestamp.
        # That way, slice(time_after_twindow_start, validtime) has a time range of [twindow_start,validtime].
        idx_first_time_after_twindow_start = (fv3ds.time > twindow_start).argmax()
        time_after_twindow_start = fv3ds.time[idx_first_time_after_twindow_start].data
        tindex = {"time": slice(time_after_twindow_start, validtime)}
        logging.debug("Time-weighted mean tendencies for time index slice %s", tindex)
        timeweights = fv3ds.time.diff("time").sel(tindex)
        time_weighted_tendencies = tendencies.sel(tindex) * timeweights
        tendencies_avg = time_weighted_tendencies.sum(dim="time") / timeweights.sum(
            dim="time"
        )
        tendencies = tendencies_avg

    # Make list of long_names before .to_array() loses them.
    long_names = [fv3ds[da].attrs["long_name"] for da in tendencies]
    print(long_names)

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
    logging.info(f"from {twindow_start} to {validtime}")
    actual_change = state_variable.sel(time=validtime) - state_variable.sel(
        time=twindow_start, method="nearest", tolerance=datetime.timedelta(milliseconds=1)
    )
    actual_change = actual_change.assign_coords(time=validtime)
    actual_change.attrs["long_name"] = (
        f"actual change in {state_variable.attrs['long_name']}"
    )

    # Sum all tendencies (physics and non-physics)
    all_tendencies = tendencies.sum(dim=tendency_dim)

    # Subtract physics tendency variable if it was in tendency_vars. Don't want to double-count.
    phys_var = any(x.endswith("_phys") for x in tendency_vars)
    if phys_var:
        logging.info(
            "subtract 'phys' tendency variable from "
            "all_tendencies to avoid double-counting"
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

    if da2plot.metpy.vertical.attrs["units"] == "mb":
        # For MetPy. Otherwise, mb is interpreted as millibarn.
        da2plot.metpy.vertical.attrs["units"] = "hPa"

    # Make default dimensions of Facetgrid kind of square.
    if not ncols:
        # Default # of cols is square root of # of panels
        ncols = int(np.ceil(np.sqrt(len(da2plot))))

    # Kludgy steps to prepare metadata for metpy cross section
    # grid_yt and grid_xt confuse metpy
    da2plot = da2plot.drop_vars(["grid_yt", "grid_xt", "long_name"]).rename(
        {"grid_yt": "y", "grid_xt": "x"}
    )
    # fv3 uses Extended Schmidt Gnomomic grid for regional applications. This is not in cartopy.
    # Found similar Lambert Conformal projection by trial and error.
    crs = dict(
        grid_mapping_name="lambert_conformal_conic",
        standard_parallel=config["standard_parallel"],
        longitude_of_central_meridian=-97.5,
        latitude_of_projection_origin=config["standard_parallel"],
    )
    if config["crs"]:
        logging.warning(f"use crs from config {crs}")
        crs = config["crs"]
    da2plot = da2plot.metpy.assign_crs(crs).metpy.assign_y_x(
        force=True, tolerance=5e7 * units.m
    )

    # dequantify moves units from DataArray to attributes. Now they show up in colorbar.
    # and avoid NotImplementedError: Don't yet support nd fancy indexing from cross_section()
    da2plot = da2plot.metpy.dequantify()

    logging.info("Define cross section.")
    cross = cross_section(da2plot, startpt, endpt)

    logging.debug("plot pcolormesh")
    if robust:
        logging.debug("compute colormap range with 2nd and 98th percentiles")
    # normalized width and height of inset. Shrink colorbar to provide space.
    wid_inset, hgt_inset = 0.18, 0.18
    pcm = cross.squeeze().plot.pcolormesh(
        x="lont",
        y="pfull",
        yincrease=False,
        col=col,
        col_wrap=ncols,
        robust=robust,
        infer_intervals=True,
        vmin=vmin,
        vmax=vmax,
        cmap=config["cmap"],
        cbar_kwargs={"shrink": 1 - hgt_inset, "anchor": (0, 0.25 - hgt_inset)},
    )

    for ax in pcm.axs.flat:
        ax.grid(visible=True, color="grey", alpha=0.5, lw=0.5)
        ax.yaxis.set_major_locator(MultipleLocator(100))
        ax.yaxis.set_minor_locator(MultipleLocator(25))
        ax.grid(which="minor", alpha=0.3, lw=0.4)

    # Add time to title
    title = f'{twindow_start}-{validtime} ({twindow_quantity.to("hours"):~} time window)'
    plt.suptitle(title, wrap=True)
    # pad top and bottom for title and fineprint.
    # Unfortunately, you must redefine right pad, as xarray no longer controls it.
    plt.subplots_adjust(top=0.9, right=0.8, bottom=0.1)

    # Locate cross section on conus map background. Put in inset.
    data_crs = da2plot.metpy.cartopy_crs
    ax_inset = plt.gcf().add_axes(
        [0.995 - wid_inset, 0.999 - hgt_inset, wid_inset, hgt_inset],
        projection=data_crs,
    )
    # Plot the endpoints of the cross section (make sure they match path)
    endpoints = data_crs.transform_points(
        cartopy.crs.Geodetic(), *np.vstack([startpt, endpt]).transpose()[::-1]
    )
    bb = ax_inset.scatter(endpoints[:, 0], endpoints[:, 1], c="k", zorder=2)
    ax_inset.scatter(
        cross["x"],
        cross["y"],
        s=3.4,
        c="white",
        linewidths=0.2,
        edgecolors="k",
        zorder=bb.get_zorder() + 1,
    )
    # Plot the path of the cross section
    ax_inset.plot(cross["x"], cross["y"], c="k", zorder=2)
    physics_tend.add_conus_features(ax_inset)
    extent = config["extent"]
    ax_inset.set_extent(extent)

    # Annotate figure with timestamp
    fineprint_str = f"created {datetime.datetime.now(tz=None)}"
    if fineprint:
        logging.debug("add fineprint to image")
        plt.figtext(0, 0, fineprint_str, fontsize="xx-small", va="bottom", wrap=True)
    else:
        logging.debug(fineprint_str)

    return pcm


if __name__ == "__main__":
    main()
