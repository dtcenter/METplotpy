# ============================*
 # ** Copyright UCAR (c) 2020
 # ** University Corporation for Atmospheric Research (UCAR)
 # ** National Center for Atmospheric Research (NCAR)
 # ** Research Applications Lab (RAL)
 # ** P.O.Box 3000, Boulder, Colorado, 80307-3000, USA
 # ============================*
 
 
 
import os
import sys
import logging
import numpy as np
import xarray as xr

def read_gfs_times(datadir, filelist):
    """
    Read times from a list of GFS grib files.
    """
    lead_times = []
    valid_times = []
    for filename in filelist:
        filename = os.path.join(datadir, filename.rstrip())
        try:
            ds = xr.open_dataset(filename, engine='cfgrib',
                backend_kwargs={
                'filter_by_keys' : {'typeOfLevel' : 'sigma'}})
            logging.info('reading ' + filename)
        except IOError:
            logging.error('failed to open ' + filename)
            sys.exit()

        logging.info(ds)
        lead_times.append(ds['time'].values)
        valid_times.append(ds['valid_time'].values)

    return lead_times, valid_times

def read_gfs_winds(datadir, filename):
    """
    Read wind fields from a GFS grib file.
    """
    filename = os.path.join(datadir, filename.rstrip())
    try:
        logging.info('reading ' + filename)
        ds = xr.open_dataset(filename, engine='cfgrib',
            backend_kwargs={
            'filter_by_keys' :
            {'typeOfLevel' : 'isobaricInhPa', 'shortName' : 'u'}})
        logging.info(ds)
        UGRD = ds['u'].values
        ds = xr.open_dataset(filename, engine='cfgrib',
            backend_kwargs={
            'filter_by_keys' :
            {'typeOfLevel' : 'isobaricInhPa', 'shortName' : 'v'}})
        logging.info(ds)
        VGRD = ds['v'].values
    except IOError:
        logging.error('failed to open ' + filename)
        sys.exit()

    return UGRD, VGRD
