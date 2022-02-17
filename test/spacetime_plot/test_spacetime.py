import sys
import numpy as np
import xarray as xr
import pytest
sys.path.append("../../")
# import metplotpy.contributed.spacetime_plot.spacetime_plot as stp
import yaml_environment_util as util


# Use the logic in the spectra_plot_power script to
# compute the input parameters for the spacetime_plot script.
def get_powerplot_parameters(config):
    '''

    :param config: The configuration dictionary from parsing the YAML config
    :return:
    '''

    # get the path to input data
    pathdata = config['plotdata']

    # store all in a powerplot dict
    power_plot_params = {}

    # plot layout parameters
    flim = power_plot_params['flim'] = 0.5  # maximum frequency in cpd for plotting
    nWavePlt = power_plot_params['nWavePlt'] = 15  # maximum wavenumber for plotting
    power_plot_params['contourmin'] = -10  # contour minimum
    power_plot_params['contourmax'] = -8.  # contour maximum
    power_plot_params['contourspace'] = 0.2  # contour spacing
    power_plot_params['wave_modes'] = [1, 2]  # wave modes for plotting (N in spectra_plot_power.py)
    power_plot_params['source'] = "ERAI"
    power_plot_params['var1'] = "precip"


    symmetry = ("symm", "asymm", "latband")
    nplot = len(symmetry)
    pp = 0

    while pp < nplot:

        # read data from file
        # fin = xr.open_dataset(pathdata + 'SpaceTimeSpectra_' + filenames[pp] + '.nc')
        fin = xr.open_dataset(pathdata + 'SpaceTimeSpectra_' + str(pp) + '.nc')
        STC = fin['STC'][:, :, :]
        wnum = fin['wnum']
        freq = fin['freq']

        ifreq = np.where((freq[:] >= 0) & (freq[:] <= flim))
        iwave = np.where(abs(wnum[:]) <= nWavePlt)

        STC[:, freq[:] == 0, :] = 0.
        STC = STC.sel(wnum=slice(-nWavePlt, nWavePlt))
        STC = STC.sel(freq=slice(0, flim))
        pow1 = np.squeeze(STC[0, :, :])
        pow2 = np.squeeze(STC[1, :, :])
        pow1.where(pow1 <= 0, drop=True)
        pow2.where(pow2 <= 0, drop=True)

        if pp == 0:
            Pow1 = np.empty([nplot, len(freq[ifreq]), len(wnum[iwave])])
            Pow2 = np.empty([nplot, len(freq[ifreq]), len(wnum[iwave])])

        Pow1[pp, :, :] = np.log10(pow1)
        Pow2[pp, :, :] = np.log10(pow2)

        pp += 1

    power_plot_params['pow1'] = Pow1
    return power_plot_params

@pytest.mark.skip("code to test is incomplete")
def test_spectra_power_plot_exists():
    '''
        Verify that output spectra power plots are generated

    '''

    config = util.parse_config("./spacetime.yaml")
    plotpath = config['plotpath']
    print('output_path:' , plotpath)
    plot_params = get_powerplot_parameters(config)
    pow1 = plot_params['pow1']
    symmetry = plot_params['symmetry']
    source = plot_params['source']
    var1 = plot_params['var1']
    flim = plot_params['flim']
    nwave_plt = plot_params['nWavePlt']
    contour_min = plot_params['contourmin']
    contour_max = plot_params['contourmax']
    contour_space = plot_params['contourspace']
    nplot = plot_params['nplot']
    wave_modes = plot_params['wave_modes']
    # stp.plot_power(pow1, symmetry, source, var1, plotpath, flim, nwave_plt, contour_min, contour_max, contour_space, nplot,
    #                wave_modes)


@pytest.mark.skip()
def test_coh_resources():
    ''' Make sure that the coh_resources returns a resource'''
    # use these values
    cmin = 0.05
    cmax = 0.55
    cspac = 0.05
    FillMode = "Fill"
    flim = 0.8
    nwaveplt = 20
    res = stp.coh_resources(cmin, cmax, cspac, FillMode, flim, nwaveplt)
    assert res


@pytest.mark.skip()
def test_coh_resources_mixed_values():
    ''' Make sure that the coh_resources returns a resource'''
    # use these values
    cmin = 0.
    cmax = 0.55
    cspac = 0.05
    FillMode = "Fill"
    flim = 0.8
    # omit the nwaveplt value (last value)
    res = stp.coh_resources(cmin, cmax, cspac, FillMode, flim)

    assert res


@pytest.mark.skip()
def test_coh_resources_default():
    '''
        Make sure that default values are applied when no
        values are provided.
    '''
    res = stp.coh_resources()
    assert res


@pytest.mark.skip()
def test_phase_resources():
    '''
       Verify that a resource is created using default
       values when no args are provided.
    '''
    res = stp.phase_resources()
    assert res


