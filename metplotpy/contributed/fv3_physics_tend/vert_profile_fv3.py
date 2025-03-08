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
    ofile = f"{statevarname}.vert_profile.png"
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

    level = logging.INFO
    if config["debug"]:
        level = logging.DEBUG
    # prepend log message with time
    logging.basicConfig(format="%(asctime)s - %(message)s", level=level, force=True)

    da2plot, title = physics_tend.get_da2plot(config, fv3ds)
    tendency_dim = f"{config['statevarname']} tendency"
    # Mask points outside shape.
    if shp:
        # Use .values to avoid AttributeError: 'DataArray' object has no attribute 'flatten'
        mask = physics_tend.pts_in_shp(fv3ds["latt"].values, fv3ds["lont"].values, shp)
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

    # Add title
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
            mask.assign_coords(lont=fv3ds["lont"], latt=fv3ds["latt"])
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
    logging.debug(fineprint_str)

    return fig


if __name__ == "__main__":
    main()
