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
import sys
import argparse
import datetime
import yaml
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr

matplotlib.use('Agg')
from metplotpy.plots import util

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

    # Use default log level of INFO if unspecified
    if args.loglevel is not None:
        log_level = args.loglevel
    else:
        log_level = "INFO"

    plot_outdir = args.plotdir
    start = datetime.datetime.now()
    # Create the log file using the same name as the plot name with '_log' and in the
    # same location.
    try:
       os.makedirs(plot_outdir, exist_ok=True)
    except FileExistsError:
        pass
    log_filename = os.path.join(plot_outdir, config['plot_filename'] + '_log' + '.txt')
    logger = util.get_common_logger(log_level, log_filename)

    logger.info("Begin plotting the cross-section")
    plot_width = config['plot_size_width']
    plot_height = config['plot_size_height']
    fig, ax = plt.subplots(figsize=(plot_width, plot_height))

    field = data_set[config['field']]
    itime = config['index_time_slice']

    # originally, axis=1 but the order of dimensions was modified
    # (Github issue:https://github.com/dtcenter/METcalcpy/issues/308)
    field_azi_mean = np.mean(field, axis=0)[:, :, itime]

    # originally, the transpose of the field_azi_mean was used, but this is no
    # longer necessary.  If the transpose is used, the dimensions are incorrect
    # and a TypeError will be raised by the contour plot.
    scalar_contour = ax.contour(data_set['range'],
                                data_set[config['vertical_coord_name']],
                                field_azi_mean,
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

    logger.info("Saving cross-section plot")
    fig.savefig(os.path.join(plot_outdir, config['plot_filename'] + '.png'), dpi=config['plot_res'])
    fig.savefig(os.path.join(plot_outdir, config['plot_filename'] + '.pdf'))

    logger.info(f"Finished generating cross-section plot in {datetime.datetime.now() - start} seconds")


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
    parser.add_argument('--loglevel', type=str,
                        required=False)

    input_args = parser.parse_args()

    """
    Read YAML configuration file
    """
    try:
        plotting_config = yaml.load(
            open(input_args.config), Loader=yaml.FullLoader)
    except yaml.YAMLError as exc:
        sys.exit(1)

    """
    Read dataset and call for plotting
    """
    try:
        input_data = xr.open_dataset(os.path.join(input_args.datadir, input_args.filename))
    except (ValueError, FileNotFoundError, PermissionError):
        sys.exit(1)
    plot_cross_section(plotting_config, input_data, input_args)

