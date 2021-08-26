import os
import sys
import argparse
import logging
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from tc_utils import read_tcrmw, format_valid_time, \
    radial_tangential_winds, height_from_pressure

def plot_cross_section(plotdir,
    valid_time, range_grid, pressure_grid,
    wind_data, scalar_data, by_pressure_lvl,
    field='TMP', track_index=0):
    """
       Generate the cross-section plot of the tangential and radial wind
    """

    wind_types = ['tangential', 'radial']
    for wt in wind_types:
        fig, ax = plt.subplots(figsize=(8., 4.5))
        ax.plot([1, 1], [1000, 50], color='lightgrey')

        plt.title(
            format_valid_time(int(valid_time[track_index])))

        # azimuthal mean
        wind_radial = np.mean(wind_data['radial'], axis=1)
        wind_tangential = np.mean(wind_data['tangential'], axis=1)
        scalar_field = np.mean(scalar_data[field], axis=1)
        logging.debug(wind_radial.shape)
        logging.debug(wind_tangential.shape)
        logging.debug(scalar_field.shape)

        if wt == 'tangential':
            wind_contour = ax.contour(range_grid, pressure_grid,
                                      wind_tangential[:, :, track_index].transpose(),
                                      levels=np.arange(5, 40, 5), colors='darkgreen', linewidths=1)
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

            if by_pressure_lvl:
                ax.set_ylabel('Pressure (mb)')
                ax.set_ylim(1000, 250)
                ax.set_yticks(np.arange(1000, 250, -100))
                ax.set_yticklabels(np.arange(1000, 250, -100))
            else:
                ax.set_ylabel('Height (m)')
                ax.set_ylim(110, 10359)
                ax.set_yticks(np.arange(110, 10359, 1000))
                ax.set_yticklabels(np.arange(110, 10359, 1000))

            tang_outfile = os.path.join(plotdir,
                                        'tangential_cross_section_' + str(valid_time[track_index]))
            # plt.savefig(os.path.join(plotdir, 'tc_cross_section.png'), dpi=300)
            # plt.savefig(os.path.join(plotdir, 'tc_cross_section.pdf'))

            fig.savefig(tang_outfile + '.png', dpi=300)
            fig.savefig(tang_outfile + '.pdf')
        else:
            wind_contour = ax.contour(range_grid, pressure_grid,
                                      wind_radial[:, :, track_index].transpose(),
                                      levels=np.arange(5, 40, 5), colors='darkgreen', linewidths=1)
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

            if by_pressure_lvl:
                ax.set_ylabel('Pressure (mb)')
                ax.set_ylim(1000, 250)
                ax.set_yticks(np.arange(1000, 250, -100))
                ax.set_yticklabels(np.arange(1000, 250, -100))
            else:
                ax.set_ylabel('Height (m)')
                ax.set_ylim(110, 10359)
                ax.set_yticks(np.arange(110, 10359, 1000))
                ax.set_yticklabels(np.arange(110, 10359, 1000))

            rad_outfile = os.path.join(plotdir,
                                       'radial_cross_section_' + str(valid_time[track_index]))
            # plt.savefig(os.path.join(plotdir, 'tc_cross_section.png'), dpi=300)
            # plt.savefig(os.path.join(plotdir, 'tc_cross_section.pdf'))

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
    parser.add_argument(
        '--by_pressure_lvl', type=str, dest='by_pressure_lvl',
        required=True)


    args = parser.parse_args()

    logging.basicConfig(stream=sys.stdout,
        level=logging.INFO)

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
        wind_data, scalar_data, args.by_pressure_lvl)
