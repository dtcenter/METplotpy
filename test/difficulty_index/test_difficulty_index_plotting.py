#!/usr/bin/env conda run -n blenny_363 python

from  import CBL_compute as cc
from metcalcpy.compare_images import CompareImages

def test_difficulty_index_plot():
    """
    Compare the expected image (diff_index_expected.png) to the latest
    one generated.  Invoke the plot_difficulty_index.py
    script to generate the difficulty_index.png
    """
    file1 = '../../metplotpy/blocking_S2S/Z500dayDJF.nc'
                                            cc.main(file1)
                                                comparison = CompareImages('../data/CBL/CBL_DJF_expected.png', 'CBL_DJF.png')
                                                    assert comparison.mssim == 1

