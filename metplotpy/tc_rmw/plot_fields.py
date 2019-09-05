import os
import sys
import argparse
import logging
import numpy as np
import matplotlib
# matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import cartopy
import cartopy.crs as ccrs
import shapely.geometry as sgeom
from tc_utils import read_tcrmw

def plot_fields(datadir, plotdir, trackfile, params):
    """
    Plot TCRMW track and track centered range azimuth grids. 
    """

    logging.info(datadir)
    logging.info(plotdir)

    valid_time, lat_grid, lon_grid, wind_data, scalar_data = \
        read_tcrmw(os.path.join(datadir, trackfile),
        levels=[args.level])
    lat_track, lon_track = lat_grid[0, 0, :], lon_grid[0, 0, :]
    lat_min, lat_max = lat_track.min(), lat_track.max()
    lon_min, lon_max = lon_track.min(), lon_track.max()
    lat_mid = (lat_min + lat_max) / 2
    lon_mid = (lon_min + lon_max) / 2
    logging.info((lon_min, lon_max))
    logging.info((lat_min, lat_max))

    # define projection and map
    # proj = ccrs.Orthographic(
    #     central_latitude=lat_mid,
    #     central_longitude=lon_mid)
    proj = ccrs.LambertConformal()
    # proj = ccrs.PlateCarree()
    proj_geom = ccrs.PlateCarree()
    fig = plt.figure(figsize=(params['figsize'],params['figsize']))
    ax = plt.axes(projection=proj)
    ax.set_extent(
        [lon_min - params['buffer'],
         lon_max + params['buffer'],
         lat_min - params['buffer'],
         lat_max + params['buffer']])
    ax.add_feature(cartopy.feature.LAND)
    ax.add_feature(cartopy.feature.OCEAN)
    ax.gridlines()

    n_range, n_azimuth, n_track = lat_grid.shape

    # plot scalar field
    field = scalar_data[args.scalar_field + '_' + args.level]
    u_grid = wind_data['U']
    v_grid = wind_data['V']
    magnitude = (u_grid**2 + v_grid**2)**0.5
    for i in range(params['start'], n_track, params['step']):
        cfplot = plt.contourf(
            # lon_grid[:,:,i], lat_grid[:,:,i], field[::-1,:,i],
            lon_grid[:,:,i], lat_grid[:,:,i], field[:,:,i],
            transform=proj_geom,
            # cmap=ListedColormap(plt.cm.cividis.colors[::-1]),
            cmap=plt.cm.gist_yarg,
            alpha=0.5)
        cplot = plt.contour(
            # lon_grid[:,:,i], lat_grid[:,:,i], field[::-1,:,i],
            lon_grid[:,:,i], lat_grid[:,:,i], field[:,:,i],
            colors='k',
            transform=proj_geom)
        ax.clabel(cplot, colors='k', fmt='%1.0f')
        vplot = plt.streamplot(
            lon_grid[:,:,i], lat_grid[:,:,i],
            # u_grid[::-1,:,i], v_grid[::-1,:,i],
            u_grid[:,:,i], v_grid[:,:,i],
            # color=magnitude[::-1,:,i],
            color=magnitude[:,:,i],
            transform=proj_geom, density=6)

    # plt.colorbar(cplot, shrink=0.8)
    cbar = plt.colorbar(vplot.lines,
        orientation='vertical', pad=0.01)
    cbar.set_label('Wind Speed (m s-1)')

    # plot track
    track = sgeom.LineString(zip(lon_track, lat_track))
    ax.add_geometries([track], proj_geom,
        edgecolor='black', facecolor='none', linewidth=4)

    # plot grid
    for i in range(params['start'], n_track, params['step']):
        # scale = float(i) / n_track
        scale = 0.5
        for j in range(0, n_range, params['range_step']):
            circle = sgeom.LineString(
                zip(lon_grid[j,:,i], lat_grid[j,:,i]))
            ax.add_geometries([circle], proj_geom,
                edgecolor=(scale, scale, scale), facecolor='none')
        circle = sgeom.LineString(
            zip(lon_grid[-1,:,i], lat_grid[-1,:,i]))
        ax.add_geometries([circle], proj_geom,
            edgecolor=(scale, scale, scale), facecolor='none')
        for j in range(0, n_azimuth, params['azimuth_step']):
            line = sgeom.LineString(
                zip(lon_grid[:,j,i], lat_grid[:,j,i]))
            ax.add_geometries([line], proj_geom,
                edgecolor=(scale, scale, scale), facecolor='none')

    plt.title('FV3GFS Hurricane Matthew 2016 Sep 28 - Oct 9')

    fig.canvas.draw()
    plt.tight_layout()
    # save figure
    plt.savefig(os.path.join(plotdir,
        trackfile.replace('.nc', '.png')), dpi=300)
    plt.savefig(os.path.join(plotdir,
        trackfile.replace('.nc', '.pdf')))
    # display
    plt.show()

if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        description='Cyclone Track Plot')
    parser.add_argument(
        '--datadir', type=str, dest='datadir', required=True)
    parser.add_argument(
        '--plotdir', type=str, dest='plotdir', required=True)
    parser.add_argument(
        '--trackfile', type=str, dest='trackfile', required=True)
    parser.add_argument(
        '--start', type=int, dest='start', required=False,
        default=0)
    parser.add_argument(
        '--step', type=int, dest='step', required=False,
        default=1)
    parser.add_argument(
        '--range_step', type=int, dest='range_step', required=False,
        default=10)
    parser.add_argument(
        '--azimuth_step', type=int, dest='azimuth_step', required=False,
        default=15)
    parser.add_argument(
        '--buffer', type=int, dest='buffer', required=False,
        default=10)
    parser.add_argument(
        '--figsize', type=int, dest='figsize', required=False,
        default=15)
    parser.add_argument(
        '--scalar_field', type=str, dest='scalar_field', required=False,
        default='T')
    parser.add_argument(
        '--level', type=str, dest='level', required=False,
        default='L0')

    args = parser.parse_args()

    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

    params = {'start' : args.start,
              'step' : args.step,
              'range_step' : args.range_step,
              'azimuth_step' : args.azimuth_step,
              'buffer' : args.buffer,
              'figsize' : args.figsize,
              'scalar_field' : args.scalar_field}

    plot_fields(args.datadir,
                args.plotdir,
                args.trackfile,
                params)
