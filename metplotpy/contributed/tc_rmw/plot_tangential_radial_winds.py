# ============================*
# ** Copyright UCAR (c) 2020
# ** University Corporation for Atmospheric Research (UCAR)
# ** National Center for Atmospheric Research (NCAR)
# ** Research Applications Lab (RAL)
# ** P.O.Box 3000, Boulder, Colorado, 80307-3000, USA
# ============================*

__author__ = 'David Fillmore'

"""
plot_cross_section for tangential and radial winds

"""

import os
import sys
import argparse
import logging
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr
import metcalcpy.process_tcrmw as pt


def plot_pressure_lev(arg, ds, track_index=0):
    # Plot setup
    textcolor = (175 / 255, 177 / 255, 179 / 255)
    plt.rcParams['figure.dpi'] = 300
    plt.rcParams['text.color'] = textcolor
    plt.rcParams['axes.edgecolor'] = textcolor
    plt.rcParams['axes.labelcolor'] = textcolor
    plt.rcParams['xtick.color'] = textcolor
    plt.rcParams['ytick.color'] = textcolor
    fig = plt.figure(figsize=(10, 5))
    ax = fig.add_subplot()
    ax.annotate('Tangential Wind (m s-1)', xy=(14, 350), color='darkgreen')
    ax.annotate('Temperature (K)', xy=(14, 370), color='darkblue')
    # nautical miles to kilometers conversion factor
    nm_to_km = 1.852
    ax.set_xlabel(
        'Range (RMW = %4.1f km)' % (nm_to_km * ds['RMW'][track_index]))
    ax.set_xticks(np.arange(1, 20))
    ax.set_ylabel('Pressure (mb)')
    ax.set_yscale('symlog')
    ax.set_ylim(1000, 250)
    ax.set_yticks(np.arange(1000, 250, -100))
    ax.set_yticklabels(np.arange(1000, 250, -100))

    # Azimuthal averages
    u_radial_azi_mean = np.mean(ds['u_radial'].values, axis=1)
    u_tangential_azi_mean = np.mean(ds['u_tangential'].values, axis=1)
    T_azi_mean = np.mean(ds[arg.T].values, axis=1)

    # Contour plots
    u_contour = ax.contour(ds['range'].values, ds['pressure'].values,
        u_tangential_azi_mean[:, :, track_index].transpose(),
        levels=np.arange(5, 40, 5), colors='darkgreen', linewidths=1)
    ax.clabel(u_contour, colors='darkgreen', fmt='%1.0f')
    T_contour = ax.contour(ds['range'].values, ds['pressure'].values,
        T_azi_mean[:, :, track_index].transpose(),
        levels=np.arange(250, 300, 10), colors='darkblue', linewidths=1)
    ax.clabel(T_contour, colors='darkblue', fmt='%1.0f')

    # plt.savefig(os.path.join(args.datadir, 'test.pdf'))
    output_plot = args.output + ".png"
    plt.savefig(os.path.join(args.outputdir, output_plot), dpi=300)
    #plt.show()


if __name__ == '__main__':


    """
    Parse command line arguments
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--datadir', type=str,
                        default=os.getenv('DATA_DIR'),
                        help='top-level data directory (default $DATA_DIR)')
    parser.add_argument('--input', type=str,
                        required=True,
                        help='input file name')
    parser.add_argument('--outputdir', type=str,
                        default=os.getenv('OUTPUT_DIR'),
                        help='top-level output directory (default $OUTPUT_DIR)')
    parser.add_argument('--output', type=str,
                        required=True,
                        help='output file name')
    parser.add_argument('--plottype', type=str,
                        default='tangential',
                        help='choices: tangential or radial')
    parser.add_argument('--logfile', type=str,
                        default=sys.stdout,
                        help='log file (default stdout)')
    parser.add_argument('--debug', action='store_true',
                        help='set logging level to debug')
    parser.add_argument('--u', type=str,
                        help='zonal wind field',
                        default='UGRD')
    parser.add_argument('--v', type=str,
                        help='meridional wind field',
                        default='VGRD')
    parser.add_argument('--T', type=str,
                        help='temperature field',
                        default='TMP')
    parser.add_argument('--RH', type=str,
                        help='relative humidity field',
                        default='RH')
    parser.add_argument('--vars', type=str,
                        help='additional variables to process',
                        default=',')
    parser.add_argument('--levels', type=str,
                        help='vertical height levels',
                        default='100,200,500,1000,1500,2000,3000,4000,5000')

    args = parser.parse_args()


    """
    Setup logging
    """
    logging_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(stream=args.logfile, level=logging_level)


    """
    Construct input and output filenames
    """
    if os.path.isdir(args.datadir):
        logging.info(args.datadir)
    else:
        logging.error(args.datadir + ' datadir not found')
        sys.exit(1)
    filename_in = os.path.join(args.datadir, args.input)

    if os.path.isdir(args.outputdir):
        logging.info(args.outputdir)
    else:
        logging.error(args.outputdir + ' outputdir not found')
        sys.exit(1)
    filename_out = os.path.join(args.outputdir, args.output)

    """
    Height levels
    """
    levels = np.array([float(lev) for lev in args.levels.split(',')])
    logging.info(('levels', levels))

    """
    Variable list
    """
    var_list = args.vars.split(',')
    logging.info(('vars', var_list))

    """
    Open dataset
    """
    ds = pt.read_tcrmw(filename_in)

    """
    Compute interpolation weights
    """
    pt.compute_interpolation_weights(args, ds)

    """
    Compute tangential and radial wind components
    """
    u_radial, u_tangential = pt.compute_wind_components(args, ds)

    """
    Write dataset
    """
    ds['u_radial'] = xr.DataArray(u_radial, coords=ds[args.T].coords)
    ds['u_tangential'] = xr.DataArray(u_tangential, coords=ds[args.T].coords)
    ds.to_netcdf(filename_out + ".nc")

    """
    Make plots
    """
    plot_pressure_lev(args, ds)
