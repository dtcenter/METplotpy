import os
import sys
import logging
import numpy as np
import xarray as xr

def read_grib_times(datadir, filelist):
    """
    Read times from a list of grib files.
    """
    for filename in filelist:
        filename = os.path.join(datadir, filename.rstrip())
        try:
            ds = xr.open_dataset(filename, engine='cfgrib',
                backend_kwargs={
                'filter_by_keys' : {'typeOfLevel' : 'atmosphere'}})
            logging.info('reading ' + filename)
            logging.info(ds)
        except IOError:
            logging.error('failed to open ' + filename)
            sys.exit()
