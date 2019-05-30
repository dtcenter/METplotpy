import os
import sys
import argparse
import logging
import numpy as np
import matplotlib.pyplot as plt
from netCDF4 import Dataset

def plot_tracks(datadir, plotdir, filename):

    logging.info(datadir)
    logging.info(plotdir)
    logging.info(filename)

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
