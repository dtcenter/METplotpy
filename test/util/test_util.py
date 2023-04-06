import pandas as pd

import metplotpy.plots.util as util


def test_is_threshold():
    """
        Verify that threshold values are getting correctly identified.

    """

    # test lists
    not_thresholds = [1.0, 11, 77]
    mixed_thresholds = ['==0.0', '> 11', 21, '>= .5', '== 3']

    if not util.is_threshold_value(not_thresholds):
        assert True

    if util.is_threshold_value(mixed_thresholds):
        assert True

    # test series
    series_not_thresholds = pd.Series(not_thresholds, range(len(not_thresholds)))
    series_mixed_thresholds = pd.Series(mixed_thresholds, range(len(mixed_thresholds)))
    if not util.is_threshold_value(series_not_thresholds):
        assert True

    if util.is_threshold_value(series_mixed_thresholds):
        assert True


def test_sort_threshold_values():
    """
       Verify that sorting of threshold values is correct.

    """

    threshold_list = ['>0', 100, '<  19.8', '<0', '== 11']
    expected_list = ['<0', '>0', '== 11', '<  19.8', 100]

    sorted_list = util.sort_threshold_values(threshold_list)

    for idx, sorted in enumerate(sorted_list):
        if sorted != expected_list[idx]:
            assert False


def test_sort_threshold_values_whitespace():
    """
       Verify that sorting of threshold values is correct.

    """

    threshold_list = ['>0', '<0', '==11', '< 11']
    expected_list = ['<0', '>0', '< 11', '==11']

    sorted_list = util.sort_threshold_values(threshold_list)

    for idx, sorted in enumerate(sorted_list):
        if sorted != expected_list[idx]:
            assert False


def test_sort_threshold_values_floats():
    """
       Verify that sorting of threshold values is correct.

    """

    threshold_list = ['>1.1', '<0.80', '<0', '==11', '< 11']
    expected_list = ['<0', '<0.80', '>1.1', '< 11', '==11']

    sorted_list = util.sort_threshold_values(threshold_list)

    for idx, sorted in enumerate(sorted_list):
        if sorted != expected_list[idx]:
            assert False
