#!/usr/bin/env conda run -n blenny_363 python

from blocking_s2s import CBL_compute as cc
from metcalcpy.compare_images import CompareImages

def test_create_cbl_plot():
    """
        Compare the expected image (CBL_DJF_expected.png to the latest
        one generated.  Invoke the CBL_compute.py
        script to generate the latest CBL_DJF.png
    """
    file1 = '../../metplotpy/blocking_S2S/Z500dayDJF.nc'
    cc.main(file1)
    comparison = CompareImages('../data/CBL/CBL_DJF_expected.png', 'CBL_DJF.png')
    assert comparison.mssim == 1
    # assert True

