import pandas as pd

import metplotpy.plots.util as util
import gc


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

def test_is_thresh():
    """ Verify that the regular expression used to test
        for column labels that are threshold-types (i.e. fcst_thresh, obs_thresh,
        cov_thresh).

    """
    no_thresh_cols = ['fcst_lead', 'vx_mask', 'fcst_init_beg']
    thresh_cols = ['fcst_thresh', 'obs_thresh', 'cov_thresh', 'xyz_thresh_abc']
    mixed_cols = ['fcst_lead', 'obtype', 'obs_thresh', 'vx_mask', 'fcst_thresh']

    counter = 0
    expected_none = len(no_thresh_cols)
    for cur_col in no_thresh_cols:
       if not util.is_thresh_column(cur_col):
           counter += 1

    if counter == expected_none:
        assert True

    counter = 0
    expected_all = len(thresh_cols)
    for cur_col in thresh_cols:
        if util.is_thresh_column(cur_col):
            counter +=1
    if counter == expected_all:
        assert True
    else:
        assert False

    expected_found = 2
    counter = 0
    for cur_col in mixed_cols:
        if util.is_thresh_column(cur_col):
            counter +=1

    if counter == expected_found:
        assert True
    else:
        assert False


def test_filter_by_fixed_vars():
    """
       Verify that the expected query string is generated and the query
       results are what are expected.


    """

    settings_dict = {'fcst_thresh': ['NA', '>0.0', '>=0.254'], 'obtype': ['CCPA'],
                 'vx_mask': ['CONUS'], 'fcst_init_beg': ['2023-06-24 12:00:00']}

    expected_query_list = ["fcst_thresh.isnull() | fcst_thresh in ( '>0.0', "
                           "'>=0.254') ",
                  "obtype in ('CCPA') ",
                  "vx_mask in ('CONUS')",
                  "fcst_init_beg in ('2023-06-24 12:00:00')"]

    input_df = pd.read_csv("./full_thresh_data.txt", sep='\t')
    filtered_df = util.filter_by_fixed_vars(input_df, settings_dict)
    expected_df = input_df.copy(deep=True)

    for qry in expected_query_list:
        intermed_df = expected_df.query(qry)
        expected_df = intermed_df.copy(deep=True)

    # Verify that the expected and filtered dataframes have the same dimensions
    assert filtered_df.shape == expected_df.shape


    filtered_list = filtered_df['fcst_thresh'].to_list()
    expected_list = expected_df['fcst_thresh'].to_list()

    for filtered in filtered_list:
       assert filtered in expected_list


    # Clean up previous dataframes
    del intermed_df
    del expected_df
    gc.collect()


    # Now test when there is only one value in fcst_thresh and it is NA
    settings_dict2 = {'fcst_thresh': ['NA'], 'obtype': ['CCPA'],
                 'vx_mask': ['CONUS'], 'fcst_init_beg': ['2023-06-24 12:00:00']}

    expected_query_list2 = ["fcst_thresh.isnull() ",
                  "obtype in ('CCPA') ",
                  "vx_mask in ('CONUS')",
                  "fcst_init_beg in ('2023-06-24 12:00:00')"]

    filtered_df = util.filter_by_fixed_vars(input_df, settings_dict2)
    expected_df = input_df.copy(deep=True)

    for qry in expected_query_list2:
        intermed_df = expected_df.query(qry)
        expected_df = intermed_df.copy(deep=True)

    assert filtered_df.shape == expected_df.shape


    filtered_list = filtered_df['fcst_thresh'].to_list()
    expected_list = expected_df['fcst_thresh'].to_list()

    for filtered in filtered_list:
       assert filtered in expected_list
