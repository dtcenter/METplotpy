import os
import sys
import argparse
import yaml

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap

import numpy as np
import xarray as xr

matplotlib.use('Agg')


def plot_cross_section(config, ds, itime=0):

    fig, ax = plt.subplots(figsize=(8., 4.5))

    """
    (range, azimuth, lev, track_point)
    """
    field = ds[config['field']]
    print(field.shape)
    field_azi_mean = np.mean(field, axis=1)[:,:,itime]
    print(field_azi_mean.shape)

    scalar_contour = ax.contour(ds['range'],
                                ds[config['vertical_coord_name']],
                                field_azi_mean.transpose())

    fig.savefig('test.png', dpi=300)
    fig.savefig('test.pdf')

    """
                                levels=, colors='darkblue',
                                linewidths=1)
    """

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
    parser.add_argument('--config', type=str,
                        required=True,
                        help='configuration file')

    args = parser.parse_args()

    """
    Read YAML configuration file
    """
    config = yaml.load(
        open(args.config), Loader=yaml.FullLoader)

    """
    Read dataset
    """
    ds = xr.open_dataset(os.path.join(args.datadir, args.filename))

    plot_cross_section(config, ds)
