"""
Plotting for Stratosphere diagnostics
 """
__author__ = 'Zach D. Lawrence (CIRES/CU, NOAA/PSL), modified by Minna Win (NCAR)'

import xarray as xr
import numpy as np
from matplotlib import pyplot as plt
from metcalcpy.pre_processing.directional_means import meridional_mean
from metcalcpy.pre_processing.directional_means import zonal_mean
import yaml
from metplotpy.plots import util

def main(config_filename=None):
    # Retrieve the contents of the custom config file to over-ride
    # or augment settings defined by the default config file.
    if not config_filename:
        config_file = util.read_config_from_command_line()
    else:
        config_file = config_filename
    with open(config_file, 'r') as stream:
        try:
            docs = yaml.load(stream, Loader=yaml.FullLoader)
        except yaml.YAMLError as exc:
            print(exc)

    try:
        pass
    except ValueError as val_er:
        print(val_er)


if __name__ == "__main__":
    main()