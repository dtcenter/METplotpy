import os
import sys
import argparse
import logging
import numpy as np
from grib_utils import read_grib_times

def tc_data(datadir, filelist):

    logging.info(datadir)

    lead_times, valid_times = read_grib_times(datadir, filelist)

    for t in range(len(lead_times)):
        logging.info(lead_times[t])
        logging.info(valid_times[t])

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

    tc_data(args.datadir, filelist)
