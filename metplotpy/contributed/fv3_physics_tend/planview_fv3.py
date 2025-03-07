""" Plan view of tendencies """

import datetime
import logging
import os

import cartopy
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray
import yaml
from metpy.units import units

from metplotpy.contributed.fv3_physics_tend import physics_tend


def main():
    """
    Plan view of tendencies of t, q, u, or v from physics parameterizations,
    dynamics (non-physics), the combination of all tendencies (physics and non-physics),
    the actual tendency, and the residual. Residual is the sum of all tendencies minus the
    actual tendency.
    """
    args = physics_tend.parse_args()
    gridfile = args.gridfile
    historyfile = args.historyfile
    config = yaml.load(open(args.config, encoding="utf8"), Loader=yaml.FullLoader)

    ds = physics_tend.prepare_ds(config, historyfile, gridfile)

    pcm = planview(config, ds)

    ofile = default_ofile(config)
    pcm.fig.savefig(ofile, dpi=config["dpi"])
    logging.info("created %s", os.path.realpath(ofile))


def planview(config, fv3ds, **kwargs):
    # Override config file with keyword args
    config.update(kwargs)
    ncols = config["ncols"]
    pfull = config["pfull"] * units.hPa
    sel_method = config["sel_method"]
    statevarname = config["statevarname"]
    tendencytype = config["tendencytype"]

    level = logging.INFO
    if config["debug"]:
        level = logging.DEBUG
    # prepend log message with time
    logging.basicConfig(format="%(asctime)s - %(message)s", level=level, force=True)

    twindow, twindow_quantity, validtime = physics_tend.assert_times(config, fv3ds)
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

    logging.debug(f"Select {len(pfull)} vertical levels with '{sel_method}' method")
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
    if config["shp"]:
        # Use .values to avoid AttributeError: 'DataArray' object has no attribute 'flatten'
        mask = physics_tend.pts_in_shp(fv3ds.latt.values, fv3ds.lont.values, config["shp"])
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
    pcm = da2plot.plot.pcolormesh(
        x="lont",
        y="latt",
        col=col,
        col_wrap=ncols,
        robust=config["robust"],
        infer_intervals=True,
        transform=cartopy.crs.PlateCarree(),
        vmin=config["vmin"],
        vmax=config["vmax"],
        cmap=config["cmap"],
        cbar_kwargs={"shrink": 0.8},
        subplot_kws=subplot_kws,
    )
    for ax in pcm.axs.flat:
        # Why needed only when col=tendency_dim? With col="pfull" it shrinks to unmasked size.
        ax.set_extent(config["extent"])
        physics_tend.add_conus_features(ax)

    # Add time to title
    title = f'{twindow_start}-{validtime} ({twindow_quantity.to("hours"):~} time window)'
    if col == tendency_dim:
        title = f"pfull={da2plot.pfull.metpy.quantify().data:~.1f} {title}"
    elif "long_name" in da2plot.coords:
        title = f'{da2plot.coords["long_name"].data} {title}'
    plt.suptitle(title, wrap=True)

    # Annotate figure with timestamp
    fineprint_str = f"created {datetime.datetime.now(tz=None)}"
    if config["fineprint"]:
        logging.debug("add fineprint to image")
        plt.figtext(0, 0, fineprint_str, fontsize="xx-small", va="bottom", wrap=True)
    logging.debug(fineprint_str)

    return pcm


def default_ofile(config):
    """
    Return default output filename.
    """
    pfull = config["pfull"] * units.hPa
    if len(pfull) == 1:
        pfull_str = f"{pfull[0]:~.0f}".replace(" ", "")
        ofile = f"{config['statevarname']}_{pfull_str}.png"
    else:
        ofile = f"{config['statevarname']}_{config['tendencytype']}.png"
    if config["shp"]:
        shp = config["shp"].rstrip("/")
        # Add shapefile name to output filename
        shapename = os.path.basename(shp)
        root, ext = os.path.splitext(ofile)
        ofile = root + f".{shapename}" + ext
    return ofile


if __name__ == "__main__":
    main()
