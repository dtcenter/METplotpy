"""Common functions for fv3_physics_tend"""

import argparse
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
from typing import Tuple, Dict, Any


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


def get_da2plot(config: Dict[str, Any], ds: xarray.Dataset) -> Tuple[xarray.DataArray, str]:
    """
    Processes a dataset to extract and compute tendencies for a given state variable.

    Args:
        config (Dict[str, Any]: Configuration dictionary containing keys such as:
            - "twindow" (int): Time window in hours.
            - "validtime" (str or None): Validation time.
            - "statevarname" (str): Name of state variable
            - "tendency_varnames" (Dict[str, list]): Mapping of state variables to tendencies.
            - "tendencies_were_zeroed_and_averaged_after_every_output" (bool): Flag for processing logic.
        ds (xarray.Dataset): The dataset containing state variables and their tendencies.

    Returns:
        Tuple[xrray.DataArray, str]:
            - DataArray containing processed tendencies.
            - string of time window
    """
    # Assert validtime and twindow match between config and Dataset
    twindow = datetime.timedelta(hours=config["twindow"])
    twindow_quantity = twindow.total_seconds() * units.seconds
    validtime = config["validtime"]
    if not validtime:
        logging.info(
            "validtime not configured. Use last time %s.",
            validtime,
        )
        validtime = ds.time.values[-1]

    validtime = pd.to_datetime(validtime)
    
    if "validtime" in ds.attrs:
        assert pd.to_datetime(ds.attrs["validtime"]) == validtime, (
            f"config validtime {validtime} != Dataset validtime {ds.attrs['validtime']}" 
        )
    if "twindow" in ds.attrs:
        assert datetime.timedelta(hours=ds.attrs["twindow"]) == twindow, (
            f"config twindow {twindow} != Dataset twindow {ds.attrs['twindow']}" 
        )

    logging.debug(f"twindow {twindow} validtime {validtime}")

    twindow_start = validtime - twindow
    logging.debug(f"twindow_start {twindow_start}")
    twindow_title = f'{twindow_start}-{validtime} ({twindow_quantity.to("hours"):~} time window)'

    # list of tendency variable names for requested state variable
    statevarname = config["statevarname"]
    tendency_vars = config["tendency_varnames"][statevarname]
    logging.debug(f"tendency_vars {tendency_vars}")
    tendencies = ds[tendency_vars]  # subset of original Dataset
    tendencies = tendencies.load()
    # convert DataArrays to Quantities to protect units. DataArray.mean drops units attribute.
    tendencies = tendencies.metpy.quantify()
    logging.info(tendencies.max())

    if config["tendencies_were_zeroed_and_averaged_after_every_output"]:
        logging.warning("assume tendencies_were_zeroed_and_averaged_after_every_output")
        assert twindow_start in ds.time, (
            f"twindow_start {twindow_start} not in history file. Closest is "
            f"{ds.time.sel(time=twindow_start, method='nearest').time.data}"
        )
        # Define time slice starting with the first time after twindow_start and ending with validtime.
        # We use the time *after* twindow_start because the time range corresponding to the tendency
        # output is the period immediately prior to the tendency timestamp.
        # That way, slice(time_after_twindow_start, validtime) has a time range of [twindow_start,validtime].
        idx_first_time_after_twindow_start = (ds.time > twindow_start).argmax()
        time_after_twindow_start = ds.time[idx_first_time_after_twindow_start].data
        tindex = {"time": slice(time_after_twindow_start, validtime)}
        logging.debug("Time-weighted mean tendencies for time index slice %s", tindex)
        timeweights = ds.time.diff("time").sel(tindex)
        time_weighted_tendencies = tendencies.sel(tindex) * timeweights
        tendencies_avg = time_weighted_tendencies.sum(dim="time") / timeweights.sum(
            dim="time"
        )
        tendencies = tendencies_avg

    # Make list of long_names before .to_array() loses them.
    long_names = [ds[da].attrs["long_name"] for da in tendencies]
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
    state_variable = ds[statevarname].metpy.quantify()
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
        [tendencies, all_tendencies, actual_tendency, resid], dim=tendency_dim
    )


    return da2plot, twindow_title


def get_datetimeindex(datetimeindex):
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
    if hasattr(datetimeindex, "to_datetimeindex"):
        # Convert from CFTime to pandas datetime or get warning
        # CFTimeIndex from non-standard calendar 'julian'.
        # Maybe history file should be saved with standard calendar.
        # To turn off warning, set unsafe=True.
        logging.debug(f"convert {datetimeindex} to datetimeindex")
        datetimeindex = datetimeindex.to_datetimeindex(unsafe=True, time_unit="ns")
        logging.debug(f"converted to {datetimeindex}")
    ragged_times = datetimeindex != datetimeindex.round("1ms")
    if any(ragged_times):
        logging.info(
            f"round times to nearest millisec. before: {datetimeindex[ragged_times].values}"
        )
        datetimeindex = datetimeindex.round("1ms")
        logging.info(f"after: {datetimeindex[ragged_times].values}")
    return datetimeindex


def get_fv3ds(config: dict, historyfile: xarray.Dataset, **kwargs) -> xarray.Dataset:
    """
    Retrieve and process FV3 model data from a given history file.
    Works with UFS runs for cutoff low study.
    2-D variables on a single pressure level are stacked along 'pfull' vertical dimension.

    Parameters:
    fv3 (dict): Configuration dictionary containing FV3 model parameters.
    historyfile (str): Path to the history file to be opened.
    **kwargs: Additional keyword arguments to override the configuration dictionary.

    Returns:
    xarray.Dataset: Processed dataset with concatenated state variables and change in tendencies.

    Raises:
    ValueError: If no stack variables match the specified prefix and suffix or state variable pattern.

    Notes:
    - The function updates the FV3 configuration with any additional keyword arguments.
    - It subtracts the tendencies across a time window.
    - The units of the tendencies are adjusted to cancel the extra "per second" in the tendency units.
    - Concatenates 2-D variables along the 'pfull' vertical dimension.
    - State variables are not subtracted across the time window. All times are returned.
    - The dataset is returned dequantified.
    """
    # Override config file with keyword args
    config.update(kwargs)
    logging.info(historyfile)
    ds = xarray.open_dataset(historyfile, chunks={})
    ds.attrs.update(config)
    twindow = datetime.timedelta(hours=config["twindow"])
    twindow_quantity = twindow.total_seconds() * units.seconds
    validtime = config["validtime"]

    ds["time"] = get_datetimeindex(ds.indexes["time"])

    if not validtime:
        validtime = ds.time.data[-1]  # last time
        logging.info(
            "null validtime. Using last time in history %s.",
            validtime,
        )
    validtime = pd.to_datetime(validtime)
    logging.debug(f"twindow {twindow} validtime {validtime}")
    twindow_start = validtime - twindow
    logging.debug(f"twindow_start {twindow_start}")

    # Loop through all state vars in the tendency_varnames dictionary.
    # Considered restricting to statevarname if statevarname is specified, but
    # doing all of them is fast enough.
    statevarnames = config["tendency_varnames"]
    for statevarname in statevarnames:
        for tendvarname in config["tendency_varnames"][statevarname]:
            # tendvarname is something like 'du3dt150_nonphys'
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
            # Cancel the extra "per second" in tendency units.
            ds[tendvarname] = ds[tendvarname] * units.s
            logging.debug(
                f"divide {tendvarname} by twindow_quantity {twindow_quantity}"
            )
            ds[tendvarname] = (
                ds[tendvarname].sel(time=validtime) - ds[tendvarname].sel(time=twindow_start)
            ) / twindow_quantity
            logging.debug(f"{tendvarname} units {ds[tendvarname].metpy.units}")

            ds[tendvarname].attrs["long_name"] = tendvarname
            ds[tendvarname].attrs["twindow"] = twindow
            ds[tendvarname].attrs["twindow_start"] = twindow_start
            ds[tendvarname].attrs["twindow_end"] = validtime

            ds = ds.drop_vars(stack_vars)
            logging.debug(tendvarname)

        # Pre-compile regex for matching statevar variables
        statevar_pattern = re.compile(f"^{statevarname}\\d+$")
        stack_vars = [var for var in ds.variables if statevar_pattern.match(var)]
        if not stack_vars:
            raise ValueError(f"No stack_vars match pattern for {statevarname}")

        plevs = [int(var[len(statevarname) :]) for var in stack_vars]

        # Concatenate along 'pfull' dimension
        ds[statevarname] = (
            ds[stack_vars]
            .metpy.quantify()  # don't lose units
            .to_dataarray(dim="pfull")
            .assign_coords(pfull=plevs)
        )
        ds[statevarname].attrs["long_name"] = statevarname
        ds = ds.drop_vars(stack_vars)

        ds["pfull"].attrs["units"] = "hPa"
        ds["pfull"].attrs["positive"] = "down"
        logging.info(statevarname)

    ds = ds.sortby("pfull")  # monotonic for .sel method=nearest later
    return ds.metpy.dequantify()


def parse_args():
    """
    parse command line arguments
    """

    # =============Arguments===================
    parser = argparse.ArgumentParser(
        description="Plot FV3 diagnostic tendencies",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    # ==========Mandatory Arguments===================
    parser.add_argument("config", help="yaml configuration file")
    parser.add_argument("historyfile", help="FV3 history file")
    parser.add_argument("gridfile", help="FV3 grid spec file")
    parser.add_argument("--out_dir", help="name of directory to write output image file")
    parser.add_argument("--debug", action="store_true", help="more log messages")

    args = parser.parse_args()
    return args


def prepare_ds(config: dict, historyfile: Path, gridfile: Path) -> xarray.Dataset:
    """
    Open (and maybe preprocess) historyfile

    Assign lat and lon from gridfile.
    """

    # Open input file
    pattern = r".*tile\d.nc$"
    if re.match(pattern, str(historyfile)):  # str handles pathlib.Path
        logging.warning("cubed-sphere historyfile")
        ds = get_fv3ds(config, historyfile)
    else:
        logging.debug("open %s", historyfile)
        ds = xarray.open_dataset(historyfile)
        ds["time"] = get_datetimeindex(ds.indexes["time"])

    ds = assign_latlon(config, ds, gridfile)
    return ds


def assign_latlon(config: dict, ds: xarray.Dataset, gridfile: Path) -> xarray.Dataset:
    """
    Assign T-cell lat and lon coords to history Dataset
    """
    # Read lat/lon from gfile
    logging.debug(f"read lat/lon from {gridfile}")
    gds = xarray.open_dataset(gridfile)
    lont = gds[config["lon_name"]]
    latt = gds[config["lat_name"]]
    assert ds.grid_xt.equals(
        gds.grid_xt
    ), f"history grid_xt {ds.grid_xt.size} no match {gridfile}"
    assert ds.grid_yt.equals(
        gds.grid_yt
    ), f"history grid_yt {ds.grid_yt.size} no match {gridfile}"

    # lont and latt used by pcolorfill()
    ds = ds.assign_coords(lont=lont, latt=latt)

    ds["area"] = gds["area"]

    return ds


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
