"""Common functions for fv3_physics_tend"""

import datetime
import logging
import os
import re
from pathlib import Path

import cartopy.feature as cfeature
import cartopy.io.shapereader as shpreader
import matplotlib.path
import numpy as np
import pandas as pd
import xarray
from metpy.units import units
from shapely.geometry import multipolygon

# from tqdm import tqdm # progress bar

TMPDIR = Path(os.getenv("TMPDIR", Path(os.getenv("SCRATCH")) / "temp"))


def add_conus_features(ax):
    """add borders"""
    ax.add_feature(cfeature.COASTLINE.with_scale("50m"), linewidth=0.3)
    ax.add_feature(cfeature.BORDERS.with_scale("50m"), linewidth=0.3)
    ax.add_feature(cfeature.STATES.with_scale("50m"), linewidth=0.1)
    ax.add_feature(
        cfeature.LAKES.with_scale("50m"),
        edgecolor="k",
        linewidth=0.25,
        facecolor="k",
        alpha=0.1,
    )
    return ax


def get_datetimeindex(ds):
    """
    Convert the time index of an xarray dataset to a pandas DateTimeIndex.

    This function checks if the time index of the given xarray dataset can be
    converted to a pandas DateTimeIndex. If the time index is a CFTimeIndex
    with a non-standard calendar (e.g., 'julian'), it converts it to a pandas
    DateTimeIndex, potentially raising a warning unless `unsafe=True` is set.
    It also rounds the times to the nearest millisecond if there are any
    "ragged" times that do not align to the nearest millisecond.

    Parameters:
    ds (xarray.Dataset): The xarray dataset containing the time index to be converted.

    Returns:
    pandas.DatetimeIndex: The converted and possibly rounded pandas DateTimeIndex.
    """
    datetimeindex = ds.indexes["time"]
    if hasattr(datetimeindex, "to_datetimeindex"):
        # Convert from CFTime to pandas datetime or get warning
        # CFTimeIndex from non-standard calendar 'julian'.
        # Maybe history file should be saved with standard calendar.
        # To turn off warning, set unsafe=True.
        datetimeindex = datetimeindex.to_datetimeindex(unsafe=True)
    ragged_times = datetimeindex != datetimeindex.round("1ms")
    if any(ragged_times):
        logging.info(
            f"round times to nearest millisec. before: {datetimeindex[ragged_times].values}"
        )
        datetimeindex = datetimeindex.round("1ms")
        logging.info(f"after: {datetimeindex[ragged_times].values}")
    return datetimeindex


def get_fv3ds(historyfile, fv3):
    logging.info(f"Opening {historyfile}")
    ds = xarray.open_dataset(historyfile, chunks={})
    twindow = datetime.timedelta(hours=fv3["twindow"])
    twindow_quantity = twindow.total_seconds() * units.seconds
    validtime = fv3["validtime"]
    ds["time"] = get_datetimeindex(ds)

    if not validtime:
        validtime = ds.time.data[-1]  # last time
        logging.info(
            "validtime not configured. Using last time in history %s.",
            validtime,
        )
    validtime = pd.to_datetime(validtime)
    time0 = validtime - twindow

    STATEVARS = fv3["tendency_varnames"]

    for statevar in STATEVARS:
        for tendvarname in STATEVARS[statevar]:
            prefix, tendencytype = tendvarname.split("_")
            suffix = f"_{tendencytype}"

            # Filter variables by prefix and suffix
            stack_vars = [
                var
                for var in ds.variables
                if var.startswith(prefix) and var.endswith(suffix)
            ]
            if not stack_vars:
                raise ValueError(
                    f"No stack_vars start with {prefix} and end with {suffix}"
                )

            plevs = [int(var[len(prefix) : -len(suffix)]) for var in stack_vars]

            # Concatenate along 'pfull' dimension
            ds[tendvarname] = (
                ds[stack_vars]
                .metpy.quantify()
                .to_dataarray(dim="pfull")
                .assign_coords(pfull=plevs)
            )
            # Cancel the extra "per second" in units.
            ds[tendvarname] = ds[tendvarname] * units.s
            ds[tendvarname] = (
                ds[tendvarname].sel(time=validtime) - ds[tendvarname].sel(time=time0)
            ) / twindow_quantity
            logging.debug(f"{tendvarname} units {ds[tendvarname].metpy.units}")

            ds[tendvarname].attrs["long_name"] = tendvarname
            ds = ds.drop_vars(stack_vars)
            logging.info(tendvarname)

        # Pre-compile regex for matching statevar variables
        statevar_pattern = re.compile(f"^{statevar}\\d+$")
        stack_vars = [var for var in ds.variables if statevar_pattern.match(var)]
        if not stack_vars:
            raise ValueError(f"No stack_vars match pattern for {statevar}")

        plevs = [int(var[len(statevar) :]) for var in stack_vars]

        # Concatenate along 'pfull' dimension
        ds[statevar] = (
            ds[stack_vars]
            .metpy.quantify()  # don't lose units
            .to_dataarray(dim="pfull")
            .assign_coords(pfull=plevs)
        )
        ds[statevar].attrs["long_name"] = statevar
        ds = ds.drop_vars(stack_vars)

        ds["pfull"].attrs["units"] = "hPa"
        ds["pfull"].attrs["positive"] = "down"
        logging.info(statevar)

    return ds.metpy.dequantify()


def pts_in_shp(lats, lons, shp):
    # Map longitude to -180 to +180 range
    lons = np.where(lons > 180, lons - 360, lons)
    # If shp is a directory, construct the path to the .shp file by appending
    # the basename of the directory with a .shp extension. This ensures that
    # the correct shapefile is read even if only the directory name is provided.
    shp = shp.rstrip("/")
    if os.path.isdir(shp):
        shp = shp + "/" + os.path.basename(shp) + ".shp"
    shape = shpreader.Reader(shp)
    ll_array = np.hstack((lons.flatten()[:, np.newaxis], lats.flatten()[:, np.newaxis]))
    mask = np.full(lats.flatten().shape, False)
    # How to make shapefile for EAST_CONUS (CONUS east of 105W)
    # import shapefile
    # import geopandas
    # from shapely.geometry import Polygon
    # shape = geopandas.read_file("./CONUS/CONUS.shp")
    # bbox = Polygon([(-105,65),(-50,65),(-50,10),(-105,10)])
    # shape = shape.intersection(bbox)
    # shape.to_file("EAST_CONUS")
    # It is as simple as that.

    # This seems kind of hacky.
    # Can you recurse through a mixture of Polygons and Multipolygons more elegantly?
    # Tried geopandas read_shape . geometry but it was no more elegant.
    for g in shape.geometries():
        logging.debug(f"{__name__} pts_in_shp area {g.area}")
        # How to deal with 3-D polygons (i.e. POLYGON Z)? some shape files are 3D.
        assert not g.has_z, (
            f"Uh oh. shape geometry has z-coordinate in {shp}"
            "I don't know how to process 3-D polygons (i.e. POLYGON Z)."
        )
        if isinstance(g, multipolygon.MultiPolygon):
            for mp in g.geoms:
                mask = mask | matplotlib.path.Path(mp.exterior.coords).contains_points(
                    ll_array
                )
        else:
            mask = mask | matplotlib.path.Path(g.exterior.coords).contains_points(
                ll_array
            )
        logging.debug("pts_in_shp: %s points", mask.sum())
    shape.close()
    return np.reshape(mask, lats.shape)
