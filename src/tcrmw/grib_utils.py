import os
import sys
import logging
import numpy as np
import pygrib

def read_grib_times(datadir, filelist):
    """
    Read times from a list of grib files.
    """
    for filename in filelist:
        filename = os.path.join(datadir, filename)
        try:
            file_id = pygrib.open(filename)
            logging.info('reading ' + filename)
        except IOError:
            logging.error('failed to open ' + filename)
            sys.exit()
