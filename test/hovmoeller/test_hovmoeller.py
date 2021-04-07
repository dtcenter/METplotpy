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


def test_get_latstring():
    '''
       Verify that the lat string created is expected
    :return:
    '''

    # Try a few lats and latn values to make sure we are covering
    # all possibilities

    latstr = hov.get_latstring(-90, 90)
    expected_str = '90S - 90N'
    assert latstr == expected_str


    latstr = hov.get_latstring(0, -5)
    expected_str = '0N - 5S'
    assert latstr == expected_str

def test_get_clevels():
   '''
      test that the get_clevels() function is behaving correctly
   '''
   pltvarname = ['precip', 'uwnd', 'vwnd', 'div', 'olr']
   # order in list: cmin, cmax, cspc
   expected = {'precip':[0.2, 1.6, 0.2], 'div':[-0.000011,0.000011,0.000002],
               'uwnd':[-21.,21.,2.],'vwnd':[-21.,21.,2.] , 'olr':[160.,240.,20.]}
   for var in pltvarname:
       cmin, cmax, cspac = hov.get_clevels(var)
       assert expected[var][0] == cmin
       assert expected[var][1] == cmax
       assert expected[var][2] == cspac


def test_get_clevels_bogus_var():
   '''
      test that the get_clevels() function is behaving correctly
      when an unexpected variable is input
   '''

   # When an unexpected variable is encountered, a default tuple for
   # cmin, cmax and cspac is returned, with a printed error message.
   # We can't capture the output, but we can check for these default values.
   default = [-21.,21.,2.]
   cmin, cmax, cspac = hov.get_clevels("bogus")

   assert cmin == default[0]
   assert cmax == default[1]
   assert cspac == default[2]