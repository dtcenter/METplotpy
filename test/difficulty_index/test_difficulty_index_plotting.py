import example_difficulty_index as edi  
from metcalcpy.compare_images import CompareImages
import pytest
import warnings

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
    assert comparison.mssim == 1

