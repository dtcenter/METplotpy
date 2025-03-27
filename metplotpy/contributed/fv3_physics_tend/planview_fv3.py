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
    if args.out_dir:
        ofile = os.path.join(args.out_dir, ofile)
        os.makedirs(os.path.dirname(ofile), exist_ok=True)

    pcm.fig.savefig(ofile, dpi=config["dpi"])
    logging.info("created %s", os.path.realpath(ofile))


def planview(config, fv3ds, **kwargs):
    # Override config file with keyword args
    config.update(kwargs)
    ncols = config["ncols"]
    pfull = config["pfull"] * units.hPa
    sel_method = config["sel_method"]
    tendencytype = config["tendencytype"]

    level = logging.INFO
    if config["debug"]:
        level = logging.DEBUG
    # prepend log message with time
    logging.basicConfig(format="%(asctime)s - %(message)s", level=level, force=True)

    da2plot, title = physics_tend.get_da2plot(config, fv3ds)
    tendency_dim = f"{config['statevarname']} tendency"
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
        mask = physics_tend.pts_in_shp(fv3ds["latt"].values, fv3ds["lont"].values, config["shp"])
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

    # Add title
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
