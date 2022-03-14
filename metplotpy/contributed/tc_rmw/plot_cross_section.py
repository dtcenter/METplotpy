# ============================*
 # ** Copyright UCAR (c) 2020
 # ** University Corporation for Atmospheric Research (UCAR)
 # ** National Center for Atmospheric Research (NCAR)
 # ** Research Applications Lab (RAL)
 # ** P.O.Box 3000, Boulder, Colorado, 80307-3000, USA
 # ============================*
 
 
 
"""
plot_cross_section
"""
__author__ = 'David Fillmore'

import os
import argparse
import yaml
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr

matplotlib.use('Agg')


def plot_cross_section(config, data_set, args):
    """
        Generate the cross-section plot of the field specified in the YAML config file
        (e.g. plot_cross_section.yaml)

       Args:
          @param config: The config object of items in the YAML configuration file (used to
                         customize the appearance of the plot).
          @param data_set: The xarray dataset (gridded data, either netCDF or grib2).
          @param args: The command line arguments indicating the location of input and output dirs, etc.

       Returns:
       None, generates output files: .png and .pdf versions of the cross-section plot.

    """

    # pylint raises issues with the use of 'ax' for matplotlib calls,
    # Keep the use of 'ax' as this is commonly used
    # pylint: disable=invalid-name


    plot_width = config['plot_size_width']
    plot_height = config['plot_size_height']
    fig, ax = plt.subplots(figsize=(plot_width, plot_height))

    field = data_set[config['field']]
    itime = config['index_time_slice']
    field_azi_mean = np.mean(field, axis=1)[:, :, itime]

    scalar_contour = ax.contour(data_set['range'],
                                data_set[config['vertical_coord_name']],
                                field_azi_mean.transpose(),
                                levels=np.arange(config['contour_level_start'],
                                                 config['contour_level_end'],
                                                 config['contour_level_stepsize']),
                                                 colors=config['contour_line_colors'],
                                                 linewidths=(config['line_width'])
                                )
    plt.title(config['plot_title'])
    ax.clabel(scalar_contour, colors=config['contour_label_color'], fmt=config['contour_label_fmt'])
    ax.set_xlabel(config['x_label'])
    ax.set_ylabel(config['y_label'])
    ax.set_xticks(np.arange(config['x_tick_start'], config['x_tick_end']))
    ax.set_yticks(np.arange(config['y_tick_start'],
                            config['y_tick_end'],
                            config['y_tick_stepsize']))
    ax.set_yscale(config['y_scale'])
    ax.set_ylim(config['y_lim_start'], config['y_lim_end'])
    plot_outdir = args.plotdir
    fig.savefig(os.path.join(plot_outdir, config['plot_filename'] + '.png'), dpi=config['plot_res'])
    fig.savefig(os.path.join(plot_outdir, config['plot_filename'] + '.pdf'))


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

    input_args = parser.parse_args()

    """
    Read YAML configuration file
    """
    plotting_config = yaml.load(
        open(input_args.config), Loader=yaml.FullLoader)

    """
    Read dataset and call for plotting
    """
    input_data = xr.open_dataset(os.path.join(input_args.datadir, input_args.filename))
    plot_cross_section(plotting_config, input_data, input_args)
