import os
import sys
import argparse
import logging
import numpy as np
from gfs_utils import read_gfs_times, read_gfs_winds

def tc_winds(datadir, filelist):

    logging.info(datadir)

    # lead_times, valid_times = read_gfs_times(datadir, filelist)

    # for t in range(len(lead_times)):
    #     logging.info(lead_times[t])
    #     logging.info(valid_times[t])

    for filename in filelist:
        u, v = read_gfs_winds(datadir, filename)
        logging.debug((u.shape, v.shape))

if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        description='Tropical Cyclone Data')
    parser.add_argument(
        '--datadir', type=str, dest='datadir', required=True)
    parser.add_argument(
        '--filelist', type=str, dest='filelist', required=True)

    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

    args = parser.parse_args()

    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

    f = open(args.filelist)
    filelist = f.readlines()

    tc_winds(args.datadir, filelist)
