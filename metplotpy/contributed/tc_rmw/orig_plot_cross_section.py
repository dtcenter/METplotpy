# ============================*
 # ** Copyright UCAR (c) 2020
 # ** University Corporation for Atmospheric Research (UCAR)
 # ** National Center for Atmospheric Research (NCAR)
 # ** Research Applications Lab (RAL)
 # ** P.O.Box 3000, Boulder, Colorado, 80307-3000, USA
 # ============================*
 
 
 
import os
import sys
import argparse
import logging
import numpy as np
import matplotlib
import yaml
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from tc_utils import read_tcrmw, format_valid_time, \
    radial_tangential_winds, height_from_pressure

def plot_cross_section(config, plotdir,
    valid_time, range_grid, pressure_grid,
    wind_data, scalar_data,
    field='TMP', track_index=0):
    """
       Generate the cross-section plot of the tangential and radial wind
    """

    # Retrieve vertical level information: coordinate input type, dimension name, and vertical levels
    vert_coord_input_type = config['vertical_coord_type_in']
    vert_dimension_name = config['vertical_dim_name']
    vert_levels = config['vertical_levels']
    y_tick_step = config['vertical_level_stepsize'][0]
    if vert_dimension_name == "pressure":
        by_pressure_lvl = True
        levels = np.array(vert_levels)
        # determine the starting and ending PRESSURE levels
        start_level = np.amax(levels)
        end_level = np.amin(levels)
    else:
        by_pressure_lvl = False
        levels = np.array(vert_levels)
        # determine the starting and ending HEIGHT levels
        start_level = np.amax(levels)
        end_level = np.amin(levels)

    # azimuthal mean
    wind_radial = np.mean(wind_data['radial'], axis=1)
    wind_tangential = np.mean(wind_data['tangential'], axis=1)
    scalar_field = np.mean(scalar_data[field], axis=1)
    logging.debug(wind_radial.shape)
    logging.debug(wind_tangential.shape)
    logging.debug(scalar_field.shape)

    # Generate two plots, one for tangential cross-section and the other
    # for radial cross-section winds
    wind_types = ['tangential', 'radial']
    for wt in wind_types:
        fig, ax = plt.subplots(figsize=(8., 4.5))
        ax.plot([1, 1], [1000, 50], color='lightgrey')

        plt.title(
            format_valid_time(int(valid_time[track_index])))

        if wt == 'tangential':
            #
            # Tangential wind
            #

            # read in the config options for tangential_contour_level_start, tangential_contour_level_end, and
            # tangential_contour_level_stepsize
            start = config['tangential_contour_level_start']
            end = config['tangential_contour_level_end']
            step = config['tangential_contour_level_stepsize']
            wind_contour = ax.contour(range_grid, pressure_grid,
                                      wind_tangential[:, :, track_index].transpose(),
                                      levels=np.arange(start, end, step), colors='darkgreen', linewidths=1)
            ax.clabel(wind_contour, colors='darkgreen', fmt='%1.0f')


            scalar_contour = ax.contour(range_grid, pressure_grid,
                                        scalar_field[:, :, track_index].transpose(),
                                        levels=np.arange(250, 300, 10), colors='darkblue',
                                        linewidths=1)

            ax.clabel(scalar_contour, colors='darkblue', fmt='%1.0f')

            ax.annotate('Tangential Wind (m s-1)', xy=(14, 350), color='darkgreen')
            ax.annotate('Temperature (K)', xy=(14, 370), color='darkblue')

            ax.set_xlabel(
                'Range (RMW = %4.1f km)' % track_data['RMW'][track_index])
            ax.set_xticks(np.arange(1, 20))

            ax.set_yscale('symlog')

            # provide support for wind data in pressure or height
            min_y_tick = config['vertical_levels'][0]
            num_vert_levels = len(config['vertical_levels']) -1
            max_y_tick = config['vertical_levels'][num_vert_levels]

            if by_pressure_lvl:
                ax.set_ylabel('Pressure (mb)')
                ax.set_ylim(start_level, end_level)
                ax.set_yticks(np.arange(start_level, end_level, y_tick_step))
                ax.set_yticklabels(np.arange(start_level, end_level, y_tick_step))
            else:
                ax.set_ylabel('Height (m)')
                ax.set_ylim(start_level, end_level)
                ax.set_yticks(np.arange(start_level, end_level, y_tick_step))
                ax.set_yticklabels(np.arange(start_level, end_level, y_tick_step))

            tang_outfile = os.path.join(plotdir,
                                        'tangential_cross_section_' + str(valid_time[track_index]))

            fig.savefig(tang_outfile + '.png', dpi=300)
            fig.savefig(tang_outfile + '.pdf')
        else:
            #
            # Radial wind
            #

            # read in the config options for radial_contour_level_start, radial_contour_level_end, and
            # radial_contour_level_stepsize
            start = config['radial_contour_level_start']
            end = config['radial_contour_level_end']
            step = config['radial_contour_level_stepsize']
            wind_contour = ax.contour(range_grid, pressure_grid,
                                      wind_radial[:, :, track_index].transpose(),
                                      levels=np.arange(start,end,step), colors='darkgreen', linewidths=1)
            ax.clabel(wind_contour, colors='darkgreen', fmt='%1.0f')


            scalar_contour = ax.contour(range_grid, pressure_grid,
                                        scalar_field[:, :, track_index].transpose(),
                                        levels=np.arange(250, 300, 10), colors='darkblue',
                                        linewidths=1)

            ax.clabel(scalar_contour, colors='darkblue', fmt='%1.0f')

            ax.annotate('Radial Wind (m s-1)', xy=(14, 350), color='darkgreen')
            ax.annotate('Temperature (K)', xy=(14, 370), color='darkblue')

            ax.set_xlabel(
                'Range (RMW = %4.1f km)' % track_data['RMW'][track_index])
            ax.set_xticks(np.arange(1, 20))

            ax.set_yscale('symlog')

            # provide support for wind data in pressure or height
            if by_pressure_lvl:
                ax.set_ylabel('Pressure (mb)')
                # ax.set_ylim(1000, 250)
                # ax.set_yticks(np.arange(1000, 250, -100))
                # ax.set_yticklabels(np.arange(1000, 250, -100))
                ax.set_ylim(start_level, end_level)
                ax.set_yticks(np.arange(start_level, end_level, y_tick_step))
                ax.set_yticklabels(np.arange(start_level, end_level, y_tick_step))
            else:
                ax.set_ylabel('Height (m)')
                # ax.set_ylim(110, 10359)
                # ax.set_yticks(np.arange(110, 10359, 1000))
                # ax.set_yticklabels(np.arange(110, 10359, 1000))
                ax.set_ylim(start_level, end_level)
                ax.set_yticks(np.arange(start_level, end_level, y_tick_step))
                ax.set_yticklabels(np.arange(start_level, end_level, y_tick_step))

            rad_outfile = os.path.join(plotdir,
                                       'radial_cross_section_' + str(valid_time[track_index]))

            fig.savefig(rad_outfile + '.png', dpi=300)
            fig.savefig(rad_outfile + '.pdf')


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
    logging.info(config)

    logging.basicConfig(stream=sys.stdout,
        level=logging.DEBUG)


    valid_time, lat_grid, lon_grid, \
        range_grid, azimuth_grid, pressure_grid, \
        track_data, wind_data, scalar_data \
        = read_tcrmw(os.path.join(args.datadir, args.filename))

    logging.debug(track_data.keys())
    logging.debug(wind_data.keys())
    logging.debug(scalar_data.keys())

    radial_tangential_wind_data = radial_tangential_winds(
        valid_time, range_grid, azimuth_grid, pressure_grid, wind_data)

    # logging.debug(wind_data.keys())
    logging.debug(radial_tangential_wind_data.keys())

    plot_cross_section(config, args.plotdir, valid_time, range_grid, pressure_grid,
                       radial_tangential_wind_data, scalar_data)
