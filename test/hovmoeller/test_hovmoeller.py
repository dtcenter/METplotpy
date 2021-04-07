import os, sys
import xarray as xr
import pytest
import yaml
sys.path.append("../..")
from metplotpy.contributed.hovmoeller.hovmoeller_calc import lat_avg
import metplotpy.contributed.hovmoeller.hovmoeller_plotly as hov

def get_config():
    config_file = "./hovmoeller.yaml"

    with open(config_file, 'r') as stream:
        try:
            config = yaml.load(stream, Loader=yaml.FullLoader)
            return config
        except yaml.YAMLError as exc:
            print(exc)

@pytest.mark.skip()
def test_get_timestr():
    """ Tests that the function get_timestr (in hovmoeller_plotly.py) returns a list
        of timestrings (i.e. a non-zero length list).
    """

    config = get_config()

    input_data = config['input_data']
    date_strt = config['date_start']
    date_last = config['date_last']

    # open the sample data into an Xarray arrsy
    ds = xr.open_dataset(input_data)
    A = ds.precip
    A = A.sel(time=slice(date_strt, date_last))
    timeA = ds.time.sel(time=slice(date_strt, date_last))
    ds.close()
    actual_timestr = hov.get_timestr(timeA)

    assert (len(actual_timestr) > 0)



def test_output_plot_created():

    """ Check for the presence of the expected plot
    """
    config = get_config()
    input_data = config['input_data']
    plotpath = config['output_plot_path']
    datestrt = config['date_start']
    datelast = config['date_last']

    #Copy the rest from METplotpy/metplotpy/contribs/hovmoeller/test_hovemoeller.py (the code that
    #invokes the plotting)
    latMax = 5.  # maximum latitude for the average
    latMin = -5.  # minimum latitude for the average

    ds = xr.open_dataset(input_data)
    A = ds.precip
    lonA = ds.lon
    print("extracting time period:")
    A = A.sel(time=slice(datestrt, datelast))
    timeA = ds.time.sel(time=slice(datestrt, datelast))
    ds.close()

    print("average over latitude band:")
    A = A * 1000 / 4
    A.attrs['units'] = 'mm/day'
    A = lat_avg(A, latmin=latMin, latmax=latMax)

    print("plot hovmoeller diagram:")
    spd = 2  # number of obs per day
    source = "ERAI"  # data source
    var = "precip"  # variable to plot
    lev = ""  # level
    # plot using user set contour levels
    contourmin = 0.2  # contour minimum
    contourmax = 1.2  # contour maximum
    contourspace = 0.2  # contour spacing
    hov.hovmoeller(A, lonA, timeA, datestrt, datelast, plotpath, latMin, latMax, spd, source, var, lev,
               contourmin, contourmax, contourspace)

    plttype = "png"
    plotname = plotpath + "Hovmoeller_" + source + var + lev + "_" + str(datestrt) + "-" + str(
        datelast) + "." + plttype

    # check if the output plot was generated
    if os.path.isfile(plotname):
        assert True
    else:
        assert False

