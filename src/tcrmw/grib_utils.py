import os
import sys
import logging
import numpy as np
import xarray as xr

def read_grib_times(datadir, filelist):
    """
    Read times from a list of grib files.
    """
    lead_times = []
    valid_times = []
    for filename in filelist:
        filename = os.path.join(datadir, filename.rstrip())
        try:
            ds = xr.open_dataset(filename, engine='cfgrib',
                backend_kwargs={
                'filter_by_keys' : {'typeOfLevel' : 'atmosphere'}})
            logging.info('reading ' + filename)
        except IOError:
            logging.error('failed to open ' + filename)
            sys.exit()

        logging.info(ds)
        lead_times.append(ds['time'].values)
        valid_times.append(ds['valid_time'].values)

    return lead_times, valid_times
