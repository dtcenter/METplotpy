# ============================*
# ** Copyright UCAR (c) 2022
# ** University Corporation for Atmospheric Research (UCAR)
# ** National Center for Atmospheric Research (NCAR)
# ** Research Applications Lab (RAL)
# ** P.O.Box 3000, Boulder, Colorado, 80307-3000, USA
# ============================*


# !/bin/env python
"""
Ice Concentration Metrics
Version 1.0
Todd Spindler and Hank Fisher
NOAA/NWS/NCEP/EMC/NSF NCAR

"""
import logging
import warnings
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import norm
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import xarray as xr
from pyproj import Geod
import pyresample as pyr
from datetime import datetime, date
import PIL
from PIL import Image
import io
import os, sys
import yaml



# something pandas needs
from pandas.plotting import register_matplotlib_converters

import metplotpy.plots.util as util
import warnings

register_matplotlib_converters()



# -------------------------------------
# figure optimization and compression 
# -------------------------------------
def save_image(imagefile, logger,  **kwargs):
    logger.info(f"Saving image {imagefile}")
    ram = io.BytesIO()
    plt.gcf().savefig(ram, **kwargs)
    ram.seek(0)
    im = Image.open(ram)
    im.convert('RGB').convert('P', palette=Image.WEB)
    im.save(imagefile, format='PNG', optimize=True)
    ram.close()
    return 0


# -------------------------------------
def ice_area(lon1, lat1, ice1, logger):
    """
    Compute the cell side dimensions (Vincenty) and the cell surface areas.
    This assumes the ice has already been masked and subsampled as needed    
    returns ice_extent, ice_area, surface_area = ice_area(lon,lat,ice)
    surface_area is the computed grid areas in km**2)
    """

    logger.info("Computing cell side dimensions and cell surface areas...")
    lon = lon1.copy()
    lat = lat1.copy()
    ice = ice1.copy()
    g = Geod(ellps='WGS84')
    _, _, xdist = g.inv(lon, lat, np.roll(lon, -1, axis=1), np.roll(lat, -1, axis=1))
    _, _, ydist = g.inv(lon, lat, np.roll(lon, -1, axis=0), np.roll(lat, -1, axis=0))
    xdist = np.ma.array(xdist, mask=ice.mask) / 1000.
    ydist = np.ma.array(ydist, mask=ice.mask) / 1000.
    xdist = xdist[:-1, :-1]
    ydist = ydist[:-1, :-1]
    ice = ice[:-1, :-1]  # just to match the roll
    extent = xdist * ydist  # extent is surface area only
    area = xdist * ydist * ice  # ice area is actual ice cover (area * concentration)
    logger.info("Finished computing cell side dimensions and cell surface areas")
    return extent.flatten().sum(), area.flatten().sum(), extent


# --------------------------------------------------------
def make_maps(image_dir, hemisphere,
              nlon, nlat, nice, rlon, rlat, rice,
              diff, crs, fcst_area, obs_area, model_name,
              obstype_name, init_time, logger):
    cmap = 'nipy_spectral'

    # pretty pictures
    logger.info(f'Plotting ice  {obstype_name}')
    plt.figure(dpi=150)
    ax = plt.axes(projection=crs)
    plt.pcolormesh(rlon, rlat, rice, cmap=cmap,
                   transform=ccrs.PlateCarree(),
                   vmin=0, vmax=1.0)
    plt.tick_params(labelsize='x-small')
    ax.add_feature(cfeature.LAND, zorder=1)
    ax.coastlines(zorder=1)
    ax.gridlines()
    cb = plt.colorbar()
    cb.ax.tick_params(labelsize='x-small')

    plt.title(
        obstype_name + ' Global sea ice concentration ' + init_time + '\n(area=' + '%10.3e' % obs_area + ' km$^2$)',
        fontsize='small')
    logger.info(f"Plot title: {plt.title}")
    logger.info(f"Saving image to {image_dir}")
    save_image(image_dir + '/' + init_time + '_observation_ice_' + hemisphere + '.png', logger, dpi=150)
    plt.close()

    logger.info(f"Plotting ice {model_name}")
    plt.figure(dpi=150)
    ax = plt.axes(projection=crs)
    plt.pcolormesh(nlon, nlat, nice, cmap=cmap,
                   transform=ccrs.PlateCarree(),
                   vmin=0, vmax=1.0)
    plt.tick_params(labelsize='x-small')
    ax.add_feature(cfeature.LAND, zorder=1)
    ax.coastlines(zorder=1)
    ax.gridlines()
    cb = plt.colorbar()
    cb.ax.tick_params(labelsize='x-small')
    plt.title(
        model_name + ' Forecast sea ice concentration ' + init_time + '\n(area=' + '%10.3e' % fcst_area + ' km$^2$)',
        fontsize='small')
    save_image(image_dir + '/' + init_time + '_fcst_ice_' + hemisphere + '.png', logger,  dpi=150)
    plt.close()

    logger.info("Plotting difference")
    plt.figure(dpi=150)
    ax1 = plt.subplot2grid((4, 1), (0, 0), rowspan=3, projection=crs)
    plt.pcolormesh(nlon, nlat, diff, cmap='bwr', transform=ccrs.PlateCarree())
    plt.tick_params(labelsize='x-small')
    ax1.add_feature(cfeature.LAND, zorder=1)
    ax1.coastlines(zorder=1)
    ax1.gridlines()
    cb = plt.colorbar()
    cb.ax.tick_params(labelsize='x-small')
    plt.title('FCST minus OBS sea ice concentration for ' + init_time, fontsize='small')

    save_image(image_dir + '/' + init_time + '_ice_diff_' + hemisphere + '.png', logger,  dpi=150)

    return 0


# -------------------------------------------------------
def process_one_day(config, hemisphere, logger):
    logger.info(f"Processing {hemisphere}ern hemisphere")
    if hemisphere == 'north':
        crs = ccrs.NorthPolarStereo(central_longitude=-168.)
        bounding_lat = 30.98
    else:
        crs = ccrs.SouthPolarStereo(central_longitude=-60.)
        bounding_lat = -39.23

    image_dir = os.environ.get("OUTPUT_BASE", ".")
    image_dir = image_dir + "/ice_images"
    met_grid_stat_ice = os.environ.get("INPUT_FILE_NAME", "grid_stat_north_000000L_20210305_120000V_pairs.nc")
    # Add the line below so that a ~ can be used to
    # grab file in a users home directory
    input_file = os.path.expanduser(met_grid_stat_ice)

    # separate the images by date
    if not os.path.isdir(image_dir):
        logger.info(f"Making image directory {image_dir}")
        os.makedirs(image_dir)

    # load ice data and subset to hemisphere of interest and ice cover min value
    logger.info("Reading ice file ")
    if not os.path.exists(input_file):
        logger.error(f"Missing ice file {input_file}")
        return

    # The variables below are found in the default yaml file
    # they are the variable names found in the netcdf file
    # you need to place the variables your netcdf file has
    # into the yaml file you are using
    obs_netcdf_var_name = config['obs_netcdf_var_name']
    forecast_netcdf_var_name = config['forecast_netcdf_var_name']
    ice_data = xr.open_dataset(input_file, decode_times=True)
    obs_ice = ice_data[obs_netcdf_var_name][:-1, :-1, ]
    fcst_ice = ice_data[forecast_netcdf_var_name][:-1, :-1, ]
    model_name = ice_data.model
    obtype_name = ice_data.obtype
    init_time = ice_data[forecast_netcdf_var_name].init_time
    logger.info(f" Model name: {model_name} obtype name: {obtype_name} init time: {init_time}")

    # trim to polar regions
    if hemisphere == 'north':
        obs_ice = obs_ice.where((obs_ice.lat >= bounding_lat), drop=True)
        fcst_ice = fcst_ice.where((fcst_ice.lat >= bounding_lat), drop=True)
    else:
        obs_ice = obs_ice.where((obs_ice.lat <= bounding_lat), drop=True)
        fcst_ice = fcst_ice.where((fcst_ice.lat <= bounding_lat), drop=True)

    # now it's back to masked arrays
    rlon = obs_ice.lon.values % 360
    rlat = obs_ice.lat.values
    rlon, rlat = np.meshgrid(rlon, rlat)  # shift from 1-d to 2-d arrays
    rice = obs_ice.to_masked_array()

    nlon = fcst_ice.lon.values % 360.  # shift from -180 - 180 to 0-360
    nlat = fcst_ice.lat.values
    nlon, nlat = np.meshgrid(nlon, nlat)  # shift from 1-d to 2-d arrays
    nice = fcst_ice.to_masked_array()

    # mask out values below 15%
    rice.mask = np.ma.mask_or(rice.mask, rice < 0.15)
    nice.mask = np.ma.mask_or(nice.mask, nice < 0.15)

    # compute ice area on original grids
    logger.info("Computing ice area")
    _, fcst_area, _ = ice_area(nlon, nlat, nice, logger)
    _, obs_area, _ = ice_area(rlon, rlat, rice, logger)

    # interpolate obs_ice to ncep grid
    logger.info("Interpolating obs_ice to NCEP grid")

    # pyresample gausssian-weighted kd-tree interp
    rlon1 = pyr.utils.wrap_longitudes(rlon)
    rlat1 = rlat.copy()
    nlon1 = pyr.utils.wrap_longitudes(nlon)
    nlat1 = nlat.copy()
    # define the grids
    orig_def = pyr.geometry.GridDefinition(lons=rlon1, lats=rlat1)
    targ_def = pyr.geometry.GridDefinition(lons=nlon1, lats=nlat1)
    radius = 50000
    sigmas = 25000
    with warnings.catch_warnings(record=True) as w:
        rice2 = pyr.kd_tree.resample_gauss(orig_def, rice, targ_def,
                                       radius_of_influence=radius,
                                       sigmas=sigmas,
                                       nprocs=8,
                                       neighbours=8,
                                       fill_value=None)
        for warning in w:
            logger.warning(f"Warning encountered while resampling {warning}")


    logger.info("Creating combined mask")
    combined_mask = np.logical_and(nice.mask, rice2.mask)
    nice2 = nice.filled(fill_value=0.0)
    rice2 = rice2.filled(fill_value=0.0)
    nice2 = np.ma.array(nice2, mask=combined_mask)
    rice2 = np.ma.array(rice2, mask=combined_mask)

    # compute various statistics
    logger.info("Computing statistics")
    diff = nice2 - rice2

    # draw pictures
    make_maps(image_dir, hemisphere,
              nlon1, nlat1, nice2, nlon1, nlat1, rice2,
              diff, crs, fcst_area, obs_area, model_name,
              obtype_name, init_time, logger)

    return 0


# -----------------------------------------------------------------

if __name__ == '__main__':
    """

    This main function is designed to work for a specific file found
    in the METplus data repository and using the configuration defaults
    found in METplotpy/metplotpy/plots/config/polar_plot_defaults.yaml

    """

    """
    Read YAML configuration file
    """

    # YAML config file resides in the same directory as this script
    config_file_dir = os.path.dirname(os.path.realpath(__file__))
    yaml_file_name =  os.path.join (config_file_dir, "polar_ice.yaml")
    try:
        config = yaml.load(
            open(yaml_file_name), Loader=yaml.FullLoader)
    except yaml.YAMLError as exc:
        sys.exit(exc)

    polar_logger = util.get_common_logger(config['log_level'], config['log_filename'])
    start = datetime.now()
    polar_logger.info(f"Input file: {config['input_file']}")
    os.environ['INPUT_FILE_NAME'] = config['input_file']

    polar_logger.info(f'Starting Ice Concentration V&V at {datetime.now()}')
    logging.captureWarnings(True)
    process_one_day(config, "north", polar_logger)
    total_time = datetime.now() - start
    polar_logger.info(f'Completed polar ice calculations and plotting in {total_time} seconds')
