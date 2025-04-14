""" vertcal cross section of tendencies """

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


def main():
    """
    Vertical cross section view of tendencies of t, q, u, or v from physics parameterizations,
    dynamics (non-physics), the combination of all tendencies (physics and non-physics),
    the actual tendency, and the residual. Residual is the sum of all tendencies minus the
    actual tendency.
    """
    args = physics_tend.parse_args()
    gridfile = args.gridfile
    historyfile = args.historyfile
    config = yaml.load(open(args.config, encoding="utf8"), Loader=yaml.FullLoader)

    ds = physics_tend.prepare_ds(config, historyfile, gridfile)

    pcm = cross_section_vert(config, ds)

    startpt = config["startpt"]
    endpt = config["endpt"]

    ofile = f"{config['statevarname']}_{startpt[0]}N{startpt[1]}E-{endpt[0]}N{endpt[1]}E.png"
    if args.out_dir:
        ofile = os.path.join(args.out_dir, ofile)
        os.makedirs(os.path.dirname(ofile), exist_ok=True)

    pcm.fig.savefig(ofile, dpi=config["dpi"])
    logging.info("created %s", os.path.realpath(ofile))


# Don't name `cross_section` metpy already has this method.
def cross_section_vert(config, fv3ds, **kwargs):
    # Override config file with keyword args
    config.update(kwargs)
    ncols = config["ncols"]
    startpt = config["startpt"]
    endpt = config["endpt"]

    level = logging.INFO
    if config["debug"]:
        level = logging.DEBUG
    # prepend log message with time
    logging.basicConfig(format="%(asctime)s - %(message)s", level=level, force=True)

    da2plot, title = physics_tend.get_da2plot(config, fv3ds)
    tendency_dim = f"{config['statevarname']} tendency"
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
    # normalized width and height of inset. Shrink colorbar to provide space.
    wid_inset, hgt_inset = 0.18, 0.18
    pcm = cross.squeeze().plot.pcolormesh(
        x="lont",
        y="pfull",
        yincrease=False,
        col=col,
        col_wrap=ncols,
        robust=config["robust"],
        infer_intervals=True,
        vmin=config["vmin"],
        vmax=config["vmax"],
        cmap=config["cmap"],
        cbar_kwargs={"shrink": 1 - hgt_inset, "anchor": (0, 0.25 - hgt_inset)},
    )

    for ax in pcm.axs.flat:
        ax.grid(visible=True, color="grey", alpha=0.5, lw=0.5)
        ax.yaxis.set_major_locator(MultipleLocator(100))
        ax.yaxis.set_minor_locator(MultipleLocator(25))
        ax.grid(which="minor", alpha=0.3, lw=0.4)

    # Add title
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
    if config["fineprint"]:
        logging.debug("add fineprint to image")
        plt.figtext(0, 0, fineprint_str, fontsize="xx-small", va="bottom", wrap=True)
    logging.debug(fineprint_str)

    return pcm


if __name__ == "__main__":
    main()
