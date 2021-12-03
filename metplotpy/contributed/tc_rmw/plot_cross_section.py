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


def plot_cross_section(config, ds, args, itime=0):

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
                                field_azi_mean.transpose(),
                                levels=np.arange(config['contour_level_start'], config['contour_level_end'], config['contour_level_stepsize']),
                                colors=config['contour_line_colors'], linewidths=(config['line_width'])
                                )
    plt.title(config['plot_title'])
    ax.clabel(scalar_contour, colors=config['contour_label_color'],fmt=config['contour_label_fmt'])

    ax.set_xlabel(config['x_label'])
    ax.set_ylabel(config['y_label'])
    ax.set_xticks(np.arange(config['x_tick_start'], config['x_tick_end']))
    ax.set_yticks(np.arange(config['y_tick_start'], config['y_tick_end'], config['y_tick_stepsize']))
    ax.set_yscale(config['y_scale'])
    ax.set_ylim(config['y_lim_start'], config['y_lim_end'])
    plot_outdir = args.plotdir
    fig.savefig(os.path.join(plot_outdir,config['plot_filename'] + '.png'), dpi=config['plot_res'])
    fig.savefig(os.path.join(plot_outdir,config['plot_filename'] + '.pdf'))


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

    plot_cross_section(config, ds, args)
