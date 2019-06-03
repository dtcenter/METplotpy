import os
import sys
import argparse
import logging
import numpy as np
import matplotlib.pyplot as plt
import cartopy
import cartopy.crs as ccrs
import shapely.geometry as sgeom
from netCDF4 import Dataset

def read_tcrmw(filename):
    """
    Read netcdf file generated by the tc_rmw tool.
    """

    try:
        file_id = Dataset(filename, 'r')
        logging.info('reading ' + filename)
    except IOError:
        logging.error('failed to open ' + filename)
        sys.exit()

    lat_grid = file_id.variables['lat'][:]
    lon_grid = file_id.variables['lon'][:]

    logging.debug('lat_grid.shape=' + str(lat_grid.shape))
    logging.debug('lon_grid.shape=' + str(lon_grid.shape))

    file_id.close()

    return lat_grid, lon_grid

def plot_tracks(datadir, plotdir, filename):

    logging.info(datadir)
    logging.info(plotdir)

    lat_grid, lon_grid = \
        read_tcrmw(os.path.join(datadir, filename))
    lat_track, lon_track = lat_grid[0, 0, :], lon_grid[0, 0, :]
    lat_min, lat_max = lat_track.min(), lat_track.max()
    lon_min, lon_max = lon_track.min(), lon_track.max()
    lat_mid = (lat_min + lat_max) / 2
    lon_mid = (lon_min + lon_max) / 2

    # define projection and map
    # proj = ccrs.Orthographic(
    #     central_latitude=lat_mid,
    #     central_longitude=lon_mid)
    proj = ccrs.LambertConformal()
    # proj = ccrs.PlateCarree()
    plt.figure(figsize=(15,15))
    ax = plt.axes(projection=proj)
    ax.set_extent(
        [lon_min - 10, lon_max + 10, lat_min - 10, lat_max + 10])
    ax.add_feature(cartopy.feature.LAND)
    ax.add_feature(cartopy.feature.OCEAN)
    ax.gridlines()

    n_range, n_azimuth, n_track = lat_grid.shape

    # plot track
    track = sgeom.LineString(zip(lon_track, lat_track))
    ax.add_geometries([track], ccrs.PlateCarree(),
        edgecolor='black', facecolor='none', linewidth=4)

    # plot grid
    for i in range(0, n_track, 20):
        scale = float(i) / n_track
        for j in range(0, n_range, 10):
            circle = sgeom.LineString(
                zip(lon_grid[j,:,i], lat_grid[j,:,i]))
            ax.add_geometries([circle], ccrs.PlateCarree(),
                edgecolor=(0, scale**2, scale), facecolor='none')
        circle = sgeom.LineString(
            zip(lon_grid[-1,:,i], lat_grid[-1,:,i]))
        ax.add_geometries([circle], ccrs.PlateCarree(),
            edgecolor=(0, scale**2, scale), facecolor='none')
        for j in range(0, n_azimuth, 15):
            line = sgeom.LineString(
                zip(lon_grid[:,j,i], lat_grid[:,j,i]))
            ax.add_geometries([line], ccrs.PlateCarree(),
                edgecolor=(0, scale**2, scale), facecolor='none')

    # display
    plt.tight_layout()
    plt.show()

if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        description='Cyclone Track Plots')
    parser.add_argument(
        '--datadir', type=str, dest='datadir', required=True)
    parser.add_argument(
        '--plotdir', type=str, dest='plotdir', required=True)
    parser.add_argument(
        '--filename', type=str, dest='filename', required=True)

    args = parser.parse_args()

    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

    plot_tracks(args.datadir,
                args.plotdir,
                args.filename)
