"""Common functions for fv3_physics_tend"""
import logging
import os
import cartopy.io.shapereader as shpreader
import cartopy.feature as cfeature
import matplotlib.path
import numpy as np
from shapely.geometry import multipolygon
# from tqdm import tqdm # progress bar
import xarray


def add_conus_features(ax):
    """ add borders """
    ax.add_feature(cfeature.COASTLINE.with_scale('50m'), linewidth=0.3)
    ax.add_feature(cfeature.BORDERS.with_scale('50m'), linewidth=0.3)
    ax.add_feature(cfeature.STATES.with_scale('50m'), linewidth=0.1)
    ax.add_feature(cfeature.LAKES.with_scale(
        '50m'), edgecolor='k', linewidth=0.25, facecolor='k', alpha=0.1)
    return ax


def add_time0(ds, variable, fv3, interval=np.timedelta64(1, 'h')):
    """
    Return new Dataset with time0 (initialization time)
    Assume initialization time is "interval" before first time
    in ds. Interval is 1 hour by default, but can be changed.
    """
    tendency_varnames = fv3["tendency_varnames"]
    time0_varname = fv3["time0_varname"]
    # This takes a while so only keep requested state variable and
    # its tendency_varnames.
    tokeep = tendency_varnames[variable].copy()
    tokeep.append(time0_varname[variable])
    tokeep.append(variable)
    ds = ds[tokeep]

    # Return new Dataset with time0 (initialization time)
    # Assume initialization time is an interval before first time
    # in ds. Interval is 1 hour by default, but can be changed.
    time0 = ds.time.values[0] - interval
    times = np.insert(ds.time.values, 0, time0)  # new time array
    # Allocate new Dataset with additional time at time0
    # extract ds.coords as dictionary so it can be changed.
    coords = dict(ds.coords)
    coords.update({"time":times})
    data_vars = {}
    dims = ds[variable].dims
    # state variable at time0 and other times
    vari = ds[time0_varname[variable]]
    data = np.insert(ds[variable].data, 0, vari.data, axis=0)
    data_vars[variable] = (dims, data)
    # tendency=0 at time0
    logging.info(f"Adding time0 to {variable}. This could take a while...")
    # for tendency in tqdm(tendency_varnames[variable]):
    for tendency in tendency_varnames[variable]:
        logging.debug(tendency)
        dims = ds[tendency].dims
        data = ds[tendency].data
        data = np.insert(data, 0, np.zeros_like(data[0]), axis=0)
        data_vars[tendency] = (dims, data)
    ds0 = xarray.Dataset(data_vars=data_vars, coords=coords)
    ds0.attrs = ds.attrs
    for da in ds0:
        ds0[da].attrs = ds[da].attrs
    return ds0


def pts_in_shp(lats, lons, shp):
    # Map longitude to -180 to +180 range
    lons = np.where(lons > 180, lons-360, lons)
    # If shp is a directory, point to .shp file of same name in it.
    shp = shp.rstrip("/")
    if os.path.isdir(shp):
        shp = shp + "/" + os.path.basename(shp) + ".shp"
    shape = shpreader.Reader(shp)
    ll_array = np.hstack(
        (lons.flatten()[:, np.newaxis], lats.flatten()[:, np.newaxis]))
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
        assert not g.has_z, (f"Uh oh. shape geometry has z-coordinate in {shp}"
                "I don't know how to process 3-D polygons (i.e. POLYGON Z).")
        if isinstance(g, multipolygon.MultiPolygon):
            for mp in g.geoms:
                mask = mask | matplotlib.path.Path(
                    mp.exterior.coords).contains_points(ll_array)
        else:
            mask = mask | matplotlib.path.Path(
                g.exterior.coords).contains_points(ll_array)
        logging.debug("pts_in_shp: %s points", mask.sum())
    shape.close()
    return np.reshape(mask, lats.shape)
