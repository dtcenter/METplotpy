import sys
sys.path.append("../..")
import example_difficulty_index as edi
# from difficulty_index import example_difficulty_index as edi
import math
from metcalcpy.compare_images import CompareImages
import pytest
import warnings


# skip this test in automated/CI environments. This is brittle
# and can fail due to differences in matplotlib bugfix versions.
@pytest.mark.skip('ad-hoc test that can fail even when content is correct but '
             'labels and titles move by one pixel. Not a reliable test in an'
             'automated application.')
def test_difficulty_index_plot():
    """
    Compare the expected image (diff_index_expected.png) to the latest
    one generated.  Invoke the plot_difficulty_index.py
    script to generate the difficulty_index.png
    """
    
    warnings.filterwarnings("ignore", category=DeprecationWarning)

    file1 = 'swh_North_Pacific_5dy_ensemble.npz'
    edi.main()
    comparison = CompareImages('diff_index_expected.png', 'swh_North_Pacific_difficulty_index_9_00_feet.png')
    # Allow small changes in the title font size, which
    # result in comparison = 0.9926 and not the expected value of 1.
    # Accepting 99% match between the expected and actual results in a change
    # of the original assertion.
    # assert (0.99 < comparison.mssim)
    assert comparison.mssim == 1

