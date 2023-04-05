import pandas as pd

import metplotpy.plots.util as util


def test_is_threshold():
    """
        Verify that threshold values are getting correctly identified.

    """
    not_thresholds = [1.0, 11, 77]
    mixed_thresholds = ['==0.0', '>11', 21]

    if util.is_threshold_value(not_thresholds):
        assert True

    if util.is_threshold_value(mixed_thresholds):
        assert True

    series_not_thresholds = pd.Series(not_thresholds, range(len(not_thresholds)))
    series_mixed_thresholds = pd.Series(mixed_thresholds, range(len(mixed_thresholds)))
    if util.is_threshold_value(series_not_thresholds):
        assert True

    if util.is_threshold_value(series_mixed_thresholds):
        assert True


def test_sort_threshold_values():
    """
       Verify that sorting of threshold values is correct.

    """

    threshold_list = ['>0', '<0', '==11', '<11']
    expected_list = ['<0', '>0', '<11', '==11']

    sorted_list = util.sort_threshold_values(threshold_list)

    for idx, sorted in enumerate(sorted_list):
        if sorted != expected_list[idx]:
            assert False
