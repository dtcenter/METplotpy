import sys
sys.path.append("../..")
import example_difficulty_index as edi
import math
import pytest
import warnings

def test_difficulty_index_plot():
    """
    Compare difficulty index values to ensure correctness.
    """
    
    file1 = 'swh_North_Pacific_5dy_ensemble.npz'
    lats, lons, fieldijn = edi.load_data(file1)
    muij, sigmaij = edi.compute_stats(fieldijn)

    assert 6.988188171386719 == muij[0][10]

    assert 6.3287403106689455 == muij[18][65]

    assert 9.475065612792969 == muij[25][100]

if __name__ == "__main__":
            test_difficulty_index_plot()
