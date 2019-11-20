import os
import sys
import argparse
import logging
import numpy as np
import matplotlib
# matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from tc_utils import read_tcrmw, radial_tangential_winds

def plot_cross_section(plotdir):
    pass

if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        description='Plot Tropical Cyclone Cross Section')

    parser.add_argument(
        '--datadir', type=str, dest='datadir',
        required=True)
    parser.add_argument(
        '--plotdir', type=str, dest='plotdir',
        required=True)
    parser.add_argument(
        '--filename', type=str, dest='filename',
        required=True)

    args = parser.parse_args()

    logging.basicConfig(stream=sys.stdout,
        level=logging.DEBUG)

    valid_time, lat_grid, lon_grid, \
        range_grid, azimuth_grid, pressure_grid, \
        track_data, wind_data, scalar_data \
        = read_tcrmw(os.path.join(args.datadir, args.filename))

    logging.debug(track_data.keys())
    logging.debug(wind_data.keys())
    logging.debug(scalar_data.keys())

    radial_tangential_winds(
        valid_time, range_grid, azimuth_grid, pressure_grid, wind_data)

    logging.debug(wind_data.keys())

    plot_cross_section(args.plotdir)
