""" Vertical profile of tendencies """

import datetime
import logging
import os

import cartopy
import matplotlib.pyplot as plt
import pandas as pd
import xarray
import yaml
from matplotlib.ticker import MultipleLocator
from metpy.units import units

from metplotpy.contributed.fv3_physics_tend import physics_tend


def main():
    """
    Vertical profile of tendencies of t, q, u, or v from physics parameterizations,
    dynamics (non-physics), the combination of all tendencies (physics and non-physics),
    the actual tendency, and the residual. Residual is the sum of all tendencies minus the
    actual tendency.
    """
    args = physics_tend.parse_args()
    gridfile = args.gridfile
    historyfile = args.historyfile
    config = yaml.load(open(args.config, encoding="utf8"), Loader=yaml.FullLoader)
    statevarname = config["statevarname"]

    ds = physics_tend.prepare_ds(config, historyfile, gridfile)

    fig = vert_profile(config, ds)

    # Output filename.
    ofile = physics_tend.TMPDIR / f"{statevarname}.vert_profile.png"
    if config["shp"]:
        shp = config["shp"].rstrip("/")
        # Add shapefile name to output filename
        shapename = os.path.basename(shp)
        root, ext = os.path.splitext(ofile)
        ofile = root + f".{shapename}" + ext
    fig.savefig(ofile, dpi=config["dpi"])
    logging.info("created %s", os.path.realpath(ofile))


def vert_profile(config, fv3ds, **kwargs):
    # Override config file with keyword args
    config.update(kwargs)
    shp = config["shp"]
    statevarname = config["statevarname"]
    twindow = datetime.timedelta(hours=config["twindow"])
    twindow_quantity = twindow.total_seconds() * units.seconds
    validtime = config["validtime"]

    level = logging.INFO
    if config["debug"]:
        level = logging.DEBUG
    # prepend log message with time
    logging.basicConfig(format="%(asctime)s - %(message)s", level=level, force=True)

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

    da2plot = tendencies
    if config["resid"]:
        # Concatenate all_tendencies, actual_tendency, and resid DataArrays.
        # Give them a name and long_name along tendency_dim.
        all_tendencies = all_tendencies.expand_dims(
            {tendency_dim: ["all"]}
        ).assign_coords(long_name="sum of tendencies")
        actual_tendency = actual_tendency.expand_dims(
            {tendency_dim: ["actual"]}
        ).assign_coords(long_name=f"actual rate of change of {statevarname}")
        resid = resid.expand_dims({tendency_dim: ["resid"]}).assign_coords(
            long_name=f"sum of tendencies - actual rate of change of {statevarname} (residual)"
        )
        da2plot = xarray.concat(
            [da2plot, all_tendencies, actual_tendency, resid], dim=tendency_dim
        )

    # Mask points outside shape.
    if shp:
        # Use .values to avoid AttributeError: 'DataArray' object has no attribute 'flatten'
        mask = physics_tend.pts_in_shp(fv3ds.latt.values, fv3ds.lont.values, shp)
        mask = xarray.DataArray(mask, coords=[da2plot.grid_yt, da2plot.grid_xt])
        da2plot = da2plot.where(mask)

    logging.info("area-weighted spatial average")
    da2plot = da2plot.weighted(fv3ds.area).mean(fv3ds.area.dims)
    # Put units in attributes so they show up in xlabel.
    # dequantify after area-weighted mean to preserve units.
    da2plot = da2plot.metpy.dequantify()

    logging.debug("creating figure")
    fig, ax = plt.subplots()
    fig.subplots_adjust(bottom=0.18)  # add space at bottom for fine print
    ax.invert_yaxis()  # pressure increases from top to bottom
    ax.grid(visible=True, color="grey", alpha=0.5, lw=0.5)
    ax.yaxis.set_major_locator(MultipleLocator(100))
    ax.yaxis.set_minor_locator(MultipleLocator(25))
    ax.grid(which="minor", alpha=0.3, lw=0.4)

    logging.info("plot area-weighted spatial average...")
    lines = da2plot.plot.line(y="pfull", ax=ax, xlim=(config["xmin"], config["xmax"]), hue=tendency_dim)

    if config["resid"]:
        # Add special marker to actual_change and residual lines.
        # DataArray plot legend handles differ from the plot lines, for some reason. So if you
        # change the style of a line later, it is not automatically changed in the legend.
        # zip d{variable}, resid line and their respective legend handles together and change
        # their style together.
        # [-2:] means take last two elements of da2plot.
        special_lines = list(zip(lines, ax.get_legend().legend_handles))[-2:]
        special_marker = "o"
        special_marker_size = 3
        for line, leghandle in special_lines:
            line.set_marker(special_marker)
            line.set_markersize(special_marker_size)
            leghandle.set_marker(special_marker)
            leghandle.set_markersize(special_marker_size)

    # Add time to title
    title = f'{twindow_start}-{validtime} ({twindow_quantity.to("hours"):~} time window)'
    ax.set_title(title, wrap=True)

    if shp:
        # Locate region of interest on conus map background. Put in inset.
        projection = cartopy.crs.LambertConformal(
            central_longitude=-97.5, central_latitude=config["standard_parallel"]
        )
        # bottom-left corner. was right side but covered power-of-ten of xaxis ticks.
        ax_inset = plt.gcf().add_axes([0.001, 0.001, 0.19, 0.13], projection=projection)
        # astype(int) to avoid TypeError: numpy boolean subtract
        cbar_kwargs = {"ticks": [0.25, 0.75], "shrink": 0.6}
        pcm = (
            mask.assign_coords(lont=fv3ds.lont, latt=fv3ds.latt)
            .astype(int)
            .plot.pcolormesh(
                ax=ax_inset,
                x="lont",
                y="latt",
                infer_intervals=True,
                transform=cartopy.crs.PlateCarree(),
                cmap=plt.colormaps["cool"],
                add_labels=False,
                cbar_kwargs=cbar_kwargs,
            )
        )
        pcm.colorbar.ax.set_yticklabels(["masked", "valid"], fontsize="xx-small")
        pcm.colorbar.outline.set_visible(False)
        physics_tend.add_conus_features(ax_inset)
        extent = config["extent"]
        ax_inset.set_extent(extent)

    # Annotate figure with timestamp
    fineprint_str = f"created {datetime.datetime.now(tz=None)}"
    if config["fineprint"]:
        logging.debug("add fineprint to image")
        plt.figtext(0, 0, fineprint_str, fontsize="xx-small", va="bottom", wrap=True)
    else:
        logging.debug(fineprint_str)

    return fig


if __name__ == "__main__":
    main()
