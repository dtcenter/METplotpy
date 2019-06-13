import os
import sys
import logging
import numpy as np
import pygrib

def read_grib_times(filelist):
    """
    Read times from a list of grib files.
    """
    for filename in filelist:
        try:
            file_id = pygrib.open()
            logging.info('reading ' + filename)
        except IOError:
            logging.error('failed to open ' + trackfile)
            sys.exit()
