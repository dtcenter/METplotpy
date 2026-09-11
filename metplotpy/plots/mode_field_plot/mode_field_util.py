# ============================*
# ** Copyright UCAR (c) 2026
# ** University Corporation for Atmospheric Research (UCAR)
# ** National Science Foundation National Center for Atmospheric Research (NSF NCAR)
# ** Research Applications Lab (RAL)
# ** P.O.Box 3000, Boulder, Colorado, 80307-3000, USA
# ============================*


"""
    mode_field_util contains utility methods that can be reused by
    any other mode plotting applications
"""

__author__ = 'Michelle Harrold'

import datetime
import numpy as np


def roll_to_pm180(lon, *fields):
    """Roll a 0-360 lon axis (and matching 2D fields) to -180..180."""
    lon = np.asarray(lon)
    lon_adj = np.where(lon > 180, lon - 360, lon)
    order = np.argsort(lon_adj)
    lon_out = lon_adj[order]
    fields_out = [f[:, order] for f in fields]
    return lon_out, fields_out


def get_extent(lat, lon, *id_fields, pad=5.0):
    """Bounding box (lon-lat) covering all non-missing object pixels, padded."""
    mask = np.zeros(id_fields[0].shape, dtype=bool)
    for f in id_fields:
        mask |= ~np.ma.getmaskarray(f)
    rows = np.where(mask.any(axis=1))[0]
    cols = np.where(mask.any(axis=0))[0]
    lat_min, lat_max = lat[rows.min()], lat[rows.max()]
    lon_min, lon_max = lon[cols.min()], lon[cols.max()]
    return [
        max(lon_min - pad, -180),
        min(lon_max + pad, 180),
        max(lat_min - pad, -90),
        min(lat_max + pad, 90),
    ]



