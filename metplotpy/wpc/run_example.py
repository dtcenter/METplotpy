import pygrib
import subprocess
import os
import numpy as np
import datetime
from mpl_toolkits.basemap import Basemap, cm
import matplotlib as mpl
mpl.use('Agg') #So plots can be saved in cron
import matplotlib.pyplot as plt
from matplotlib.mlab import griddata
from scipy.io import netcdf
from netCDF4 import Dataset

from scipy import ndimage
import METLoadEnsemble
import METPlotEnsemble

def generate_plot():

    # Set some values that we need to invoke the plotting functions, specifically METPlotEnsemble.MTDPlotRetro()
    thres = 0.2
    MET_PATH = 'MTD_RETRO_NEWSe15min_' + str(thres)
    GRIB_PATH_DES = 'MTD_RETRO_NEWSe15min_t'+str(thres)
    # No grib files because we only received the MTD output, use placeholder directory for now
    GRIB_PATH = '/d1/minnawin/METplotpy/data/'
    FIG_PATH = '/d1/minnawin/wpc/figures/MET/RETRO'
    pre_acc = 1.0/4.0
    load_qpe = ['HIRESNAM_lag06']
    load_data = load_model = ['HIRESWARW_lag12']
    plot_allhours = 'TRUE'
    total_fcst_hrs = 6.0
    start_hrs = 0.0
    # Set the proper forecast hours load depending on the initialization
    hrs = np.arange(0.0, total_fcst_hrs + 1, pre_acc)
    hrs = hrs[hrs > 0]
    data_success = np.ones([len(hrs), len(load_data)])

    # Set hours to be loaded conditional on starting time
    hrs = hrs + start_hrs
    hrs = hrs[hrs >= start_hrs]
    hrs = hrs[hrs <= total_fcst_hrs]

    hrs_all = np.arange(hrs[0] - 1, hrs[1] + pre_acc, pre_acc)

    # Beginning time of retrospective runs (datetime element)
    # based on the MTD ascii files provided to us.
    beg_date = datetime.datetime(2019, 4, 9, 12, 0, 0)
    end_date = datetime.datetime(2019, 4, 9, 12, 0, 0)
    curdate =datetime_curdate = get_curdate(beg_date, end_date)

    # this is input to the METLoadEnsemble_NEW.loadDataMTD() function to
    # retrieve the lon_t, lat_t, fcst_p and obs_p needed by the MTDRetro 
    # plotting function. The MTD output files in netcdf and text are located 
    # in the GRIB_PATH_TEMP directory.
    GRIB_PATH_TEMP = '/d1/minnawin/METplotpy/data/netcdf/20190409'
    MTDfile_new = 'mtd_20190409_h12_f48_HIRESWARW_lag12_p1_t0.1'
    
    # hard code this to 1, to for the MTD output using WRF data, as verified
    # via ncdump on the MTD netCDF output file.
    ismodel = 1
    latlon_dims = [-126, 23, -65, 50]

    (lat_t, lon_t, fcst_p, obs_p, simp_bin_p, clus_bin_p, simp_prop_k, pair_prop_k, data_success_p) = \
        METLoadEnsemble.loadDataMTD(GRIB_PATH_TEMP, MTDfile_new, ismodel, latlon_dims)

    print("lat_t: {}".format(lat_t))
    print("lon_t: {}".format(lon_t))
    print("fcst_p: {}".format(fcst_p))
    print("obs_p: {}".format(obs_p))
    print("simp_bin_p: {}".format(simp_bin_p))
    print("pair_prop_k: {}".format(pair_prop_k))
    print("latmax: ", lat_t)
    print("lonmax: ", lon_t)
    print("grib path temp: ", GRIB_PATH_TEMP)
    print("mtd file: ", MTDfile_new)
    
    # print('lat_t[fcst_p]: ', np.nanmax(lat_t[fcst_p[:,:,0].data]))

    # errors when checking for data > 0
    # we are looking for min/max value in lon_t and lat_t matrix, ignoring np.nan values...
    latmin = np.nanmin(lat_t[fcst_p[:, :, 0].data > 0])
    latmax = np.nanmax(lat_t[fcst_p[:, :, 0 ].data > 0])
    lonmin = np.nanmin(lon_t[fcst_p[:, :, 0].data > 0])
    lonmax = np.nanmax(lon_t[fcst_p[:, :, 0].data > 0])
    print('latmin: {}'.format(latmin))
    print('latmax: {}'.format(latmax))
    print('lonmin: {}'.format(lonmin))
    print('lonmin: {}'.format(lonmax))
    # Assign the min/max lat/lon to the appropriate value in the latlon_dims list/array:
    # [WLON, SLAT, ELON, NLAT]
    latlon_dims = [lonmin, latmin,lonmin, latmax]


    # set hrs_all to this, the other option is
    # hrs_all = np.arange(hrs[0] - 1, hrs[-1] + pre_acc, pre_acc)
    # data_success = np.concatenate((data_success, np.ones([1, len(load_data)])), axis=0) for the condition:
    # if 'NEWSe60min' in load_data[model] and mod_lag > 0
    hrs_all = np.arange(hrs[0], hrs[-1] + pre_acc, pre_acc)

    # Get remaining input variables from METLoadEnsembleNEW.setupData, such as load_data_nc, from
    #METLoadEnsemble_NEW.setupData()

    #First, print out all the input variables to setupData()
    print("data_success: {}".format(data_success))
    print("GRIB_PATH: {}".format(GRIB_PATH))
    print("FIG_PATH: {}".format(FIG_PATH))
    print("GRIB_PATH_DES: {}".format(GRIB_PATH_DES))
    print("load_data: {}".format(load_data))
    print("pre_acc: {}".format(pre_acc))
    print("total_fcst_hrs: {} ".format(total_fcst_hrs))
    print("latlon_dims: {}".format(latlon_dims))
    print("datetime_curdate: {}".format(datetime_curdate))

    (GRIB_PATH_TEMP, FIG_PATH_S, curdate, init_yrmondayhr, hrs, offset_fcsthr, load_data_nc, acc_int, lat,lon) = \
    METLoadEnsemble.setupData(GRIB_PATH, FIG_PATH, GRIB_PATH_DES, load_data, pre_acc, total_fcst_hrs, latlon_dims,
                                  datetime_curdate, thres)

    # print the output values returned from setupData
    print("======Values returned from setupData=======")
    print("GRIB_PATH_TEMP: ", GRIB_PATH_TEMP)
    print("FIG_PATH_S", FIG_PATH_S)
    print("curdate: ", curdate)
    print("init_yrmondayhr: ", init_yrmondayhr)
    print('hrs: ', hrs)
    print("offset_fcsthr: ", offset_fcsthr)
    print("load_data_nc: ", load_data_nc )
    print("acc_int: ", acc_int)
    print("lat: ", lat, "  lon: ", lon)

    # invoke the MTDRetro plotting function
    # METPlotEnsemble.MTDPlotRetro(GRIB_PATH_DES,FIG_PATH,latlon_dims, pre_acc, hrs_all, thres, curdate, data_success, load_data_nc, lat_t, lon_t, fcst_p, obs_p, clus_bin_p, pair_prop_k)
    METPlotEnsemble.MTDPlotRetroJustPrecip(GRIB_PATH_DES,FIG_PATH,latlon_dims, pre_acc, hrs_all, thres, curdate, data_success, load_data_nc, lat_t, lon_t, fcst_p, obs_p, clus_bin_p, pair_prop_k)



def get_curdate(beg_date, end_date):

    beg_date_jul = pygrib.datetime_to_julian(beg_date)
    end_date_jul = pygrib.datetime_to_julian(end_date)

    # Typically do this for the range of beg_dat_jul and end_date_jul, but these are the same date so
    # we can omit looping over the range of julian dates.
    dates = range(int(round(beg_date_jul)), int(round(end_date_jul)) + 1)
    # since the beg_date_jul = end_date_jul, pass in only the beg_date_jul, instead of dates
    datetime_curtime = pygrib.julian_to_datetime(beg_date_jul)



    return datetime_curtime

if __name__ == "__main__":
    generate_plot()