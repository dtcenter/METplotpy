tendencies = dict(
tmp = ['dt3dt_cnvgwd','dt3dt_deepcnv','dt3dt_lw','dt3dt_mp','dt3dt_orogwd','dt3dt_pbl','dt3dt_rdamp','dt3dt_shalcnv','dt3dt_sw','dt3dt_nophys'],
spfh= ['dq3dt_deepcnv','dq3dt_mp','dq3dt_pbl','dq3dt_shalcnv','dq3dt_nophys'],
ugrd= ['du3dt_cnvgwd','du3dt_deepcnv','du3dt_orogwd','du3dt_pbl','du3dt_rdamp','du3dt_shalcnv','du3dt_nophys'],
vgrd= ['dv3dt_cnvgwd','dv3dt_deepcnv','dv3dt_orogwd','dv3dt_pbl','dv3dt_rdamp','dv3dt_shalcnv','dv3dt_nophys']
)
import cartopy.io.shapereader as shpreader
import datetime
import matplotlib.path
import numpy as np
import os
import pandas as pd
import pdb
from shapely.geometry import Point, multipolygon

def pts_in_shp(lats, lons, shp, debug=False):
    # Map longitude to -180 to +180 range
    lons = np.where(lons > 180, lons-360, lons)
    # If shp is a directory, point to .shp file of same name in it.
    shp = shp.rstrip("/")
    if os.path.isdir(shp):
        shp = shp + "/" + os.path.basename(shp) + ".shp"
    shape = shpreader.Reader(shp)
    ll_array = np.hstack((lons.flatten()[:,np.newaxis],lats.flatten()[:,np.newaxis]))
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

    # This seems kind of hacky. Can you recurse through a mixture of Polygons and Multipolygons more elegantly?
    # Tried geopandas read_shape . geometry but it was no more elegant.
    for g in shape.geometries():
        if debug:
            print(__name__, "pts_in_shp area", g.area)
        # How to deal with 3-D polygons (i.e. POLYGON Z)? some shape files are 3D.
        if g.has_z:
            print("Uh oh. shape geometry has z-coordinate in",shp)
            print("I don't know how to process 3-D polygons (i.e. POLYGON Z).")
            sys.exit(1)
        if isinstance(g, multipolygon.MultiPolygon):
            for mp in g.geoms:
                mask = mask | matplotlib.path.Path(mp.exterior.coords).contains_points(ll_array)
        else:
            mask = mask | matplotlib.path.Path(g.exterior.coords).contains_points(ll_array)
        if debug:
            print("pts_in_shp:", mask.sum(), "points")
    shape.close()
    return np.reshape(mask, lats.shape)
