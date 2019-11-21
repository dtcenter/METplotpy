import os
import sys
import argparse
import logging
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from tc_utils import read_tcrmw, \
    radial_tangential_winds, height_from_pressure

def plot_cross_section(plotdir,
    valid_time, range_grid, pressure_grid,
    wind_data, scalar_data,
    field='TMP', track_index=0):
    """
    """

    find_height = True

    fig = plt.figure(1, figsize=(8., 4.5))
    ax = plt.axes()
    ax.plot([1, 1], [1000, 50], color='lightgrey')

    # azimuthal mean
    wind_radial = np.mean(wind_data['radial'], axis=1)
    wind_tangential = np.mean(wind_data['tangential'], axis=1)
    scalar_field = np.mean(scalar_data[field], axis=1)
    logging.debug(wind_radial.shape)
    logging.debug(wind_tangential.shape)
    logging.debug(scalar_field.shape)

    if find_height:
        mb_to_Pa = 100  # millibar to Pascal
        m_to_km = 0.001 # meter to kilometer
        temperature = np.mean(scalar_data['TMP'], axis=1)
        surface_pressure = np.mean(scalar_data['PRMSL'], axis=1)
        logging.debug(temperature.shape)
        logging.debug(surface_pressure.shape)
        height = height_from_pressure(surface_pressure[0, track_index],
            temperature[0, :, track_index], mb_to_Pa * pressure_grid) \
            * m_to_km
        logging.debug(height)

    wind_contour = ax.contour(range_grid, pressure_grid,
        wind_tangential[:,:,track_index].transpose(),
        levels=np.arange(5, 40, 5), colors='darkgreen', linewidths=1)
    ax.clabel(wind_contour, colors='darkgreen', fmt='%1.0f')

    scalar_contour = ax.contour(range_grid, pressure_grid,
        scalar_field[:,:,track_index].transpose(),
        levels=np.arange(250, 300, 10), colors='darkblue',
        linewidths=1)
    ax.clabel(scalar_contour, colors='darkblue', fmt='%1.0f')

    ax.annotate('Tangential Wind (m s-1)', xy=(6, 270), color='darkgreen')
    ax.annotate('Temperature (K)', xy=(6, 300), color='darkblue')

    ax.set_xlabel('Range (RMW)')
    ax.set_xticks(np.arange(1, 10))

    ax.set_ylabel('Pressure (hPa)')
    ax.set_yscale('symlog')
    ax.set_ylim(1000, 250)
    ax.set_yticks(np.arange(1000, 250, -100))
    ax.set_yticklabels(np.arange(1000, 250, -100))

    plt.savefig(os.path.join(plotdir, 'tc_cross_section.png'), dpi=300)
    plt.savefig(os.path.join(plotdir, 'tc_cross_section.pdf'))

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

    plot_cross_section(args.plotdir, valid_time, range_grid, pressure_grid,
        wind_data, scalar_data)
