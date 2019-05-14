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
import METLoadEnsemble_NEW
import METPlotEnsemble

def generate_plot():

    # Set some values that we need to invoke the plotting functions, specifically METPlotEnsemble.MTDPlotRetro()
    thres = 0.2
    MET_PATH = 'MTD_RETRO_NEWSe15min_' + str(thres)
    GRIB_PATH_DES = 'MTD_RETRO_NEWSe15min_t'+str(thres)
    FIG_PATH = '/d1/minnawin/wpc/figures/MET/RETRO'
    pre_acc = 1.0/4.0
    load_qpe = 'MRMS15min_lag00'
    load_model = 'NEWSe5min_mem02_lag00'
    plot_allhours = 'TRUE'
    total_fcst_hrs = 6.0
    hrs = np.arange(0.0, total_fcst_hrs + 1, pre_acc)
    hrs_all = np.arange(hrs[0] - 1, hrs[1] + pre_acc, pre_acc)

    # Beginning time of retrospective runs (datetime element)
    # based on the MTD ascii files provided to us.
    beg_date = datetime.datetime(2019, 4, 9, 12, 0, 0)
    end_date = datetime.datetime(2019, 4, 9, 12, 0, 0)
    curdate = get_curdate(beg_date, end_date)

    # this is input to the METLoadEnsemble_NEW.loadDataMTD() function to
    # retrieve the lon_t, lat_t, fcst_p and obs_p needed by the MTDRetro plotting function
    GRIB_PATH_TEMP = '/d1/minnawin/METplotpy/data/20190409'
    MTDfile_new = 'mtd_20190409_h12_f48_HIRESWARW_lag12_p1_t0.1'
    ismodel = 1
    latlon_dims = [-126, 23, -65, 50]
    latmax = 50
    latmin = 23
    lonmax = -65
    lonmin = -126

    (lat_t, lon_t, fcst_p, obs_p, simp_bin_p, clus_bin_p, simp_prop_k, pair_prop_k, data_success_p) = \
        METLoadEnsemble_NEW.loadDataMTD(GRIB_PATH_TEMP, MTDfile_new, ismodel, latlon_dims)

    #latmin = np.nanmin(lat_t[fcst_p[:, :, 0].data > 0])
    print("lat_t: {}".format(lat_t))
    print("lon_t: {}".format(lon_t))
    print("fcst_p: {}".format(fcst_p))
    print("obs_p: {}".format(obs_p))
    print("simp_bin_p: {}".format(simp_bin_p))
    print("pair_prop_k: {}".format(pair_prop_k))
    latmax = np.nanmax(lat_t[fcst_p[:, :, 0].data > 0])
    lonmin = np.nanmin(lon_t[fcst_p[:, :, 0].data > 0])
    lonmin = np.nanmin(lon_t[fcst_p[:, :, 0].data > 0])
    lonmax = np.nanmax(lon_t[fcst_p[:, :, 0].data > 0])
    # lonmax = -65
    # lonmin = -126
    print("latmax: ", latmax)
    print("latmin: ", latmin)
    print("lonmax: ", lonmax)
    print("lonmin: ", lonmin)

    # Get remaining input variables from METLoadEnsembleNEW.setupData, such as load_data_nc

    # invoke the MTDRetro plotting function
    #METPlotEnsemble.MTDPlotRetro(GRIB_PATH_DES,FIG_PATH,latlon_dims, pre_acc, hrs_all, thres, curdate, data_success_p,)


def get_curdate(beg_date, end_date):
    beg_dat_jul = pygrib.datetime_to_julian(beg_date)
    end_date_jul = pygrib.datetime_to_julian(end_date)

    # Typically do this for the range of beg_dat_jul and end_date_jul, but these are the same date so
    # we can omit looping over the range of julian dates.
    datetime_curtime = pygrib.julian_to_datetime(beg_dat_jul)



    return datetime_curtime

if __name__ == "__main__":
    generate_plot()