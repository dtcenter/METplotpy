import os
import sys
import argparse
import logging
import numpy as np
import matplotlib.pyplot as plt
from netCDF4 import Dataset

def read_tcrmw(filename):

    try:
        file_id = Dataset(filename, 'r')
        logging.info('reading ' + filename)
    except IOError:
        logging.error('failed to open ' + filename)
        sys.exit()

    lat_grid = file_id.variables['lat'][:]
    lon_grid = file_id.variables['lon'][:]

    logging.debug('lat_grid.shape=' + str(lat_grid.shape))
    logging.debug('lon_grid.shape=' + str(lon_grid.shape))

    file_id.close()

    return lat_grid, lon_grid

def plot_tracks(datadir, plotdir, filename):

    logging.info(datadir)
    logging.info(plotdir)

    lat_grid, lon_grid = \
        read_tcrmw(os.path.join(datadir, filename))

if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        description='Cyclone Track Plots')
    parser.add_argument(
        '--datadir', type=str, dest='datadir', required=True)
    parser.add_argument(
        '--plotdir', type=str, dest='plotdir', required=True)
    parser.add_argument(
        '--filename', type=str, dest='filename', required=True)

    args = parser.parse_args()

    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

    plot_tracks(args.datadir,
                args.plotdir,
                args.filename)
