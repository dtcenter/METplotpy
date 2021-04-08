import sys
import pytest
sys.path.append("../../")
import metplotpy.contributed.spacetime_plot.spacetime_plot as stp


def parse_config(config):
    '''
       Parse the yaml config file to
       retrieve ENV vars and other settings
       that are used in some of these tests.
    '''
    return None


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

def test_coh_resources_default():
    '''
        Make sure that default values are applied when no
        values are provided.
    '''
    res = stp.coh_resources()
    assert res

def test_phase_resources():
    '''
       Verify that a resource is created using default
       values when no args are provided.
    '''
    res = stp.phase_resources()
    assert res
