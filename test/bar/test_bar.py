import os

import pytest

from metplotpy.plots.bar import bar
# from metcalcpy.compare_images import CompareImages

cwd = os.path.dirname(__file__)
CLEANUP_FILES = ['bar.png', 'bar.points1']


@pytest.fixture
def setup(remove_files, setup_env):
    # Cleanup the plotfile and point1 output file from any previous run
    remove_files(cwd, CLEANUP_FILES)
    setup_env(cwd)
    custom_config_filename = f"{cwd}/custom_bar.yaml"

    # Invoke the command to generate a Bar plot based on
    # the custom_bar.yaml custom config file.
    bar.main(custom_config_filename)


@pytest.fixture
def setup_nones(remove_files, setup_env):
    # Cleanup the plotfile and point1 output file from any previous run
    remove_files(cwd, CLEANUP_FILES)
    setup_env(cwd)
    custom_config_filename = f"{cwd}/bar_with_nones.yaml"

    # Invoke the command to generate a Bar plot based on
    # the custom_bar.yaml custom config file.
    bar.main(custom_config_filename)


@pytest.mark.parametrize("test_input, expected",
                         (["bar_expected.png", True],
                          ["bar.png", True],
                          ["bar.points1", True]))
def test_files_exist(setup, test_input, expected, remove_files):
    """
        Checking that the plot and data files are getting created
    """
    assert os.path.isfile(f"{cwd}/{test_input}") == expected
    remove_files(cwd, CLEANUP_FILES)


def test_no_nans_in_points_file(setup, remove_files):
    """
        Checking that the points1 intermediate file does not
        have any NaN's.  This is indicative of a problem with the _create_series_points() method.
    """

    # Check for NaN's in the intermediate files, line.points1 and line.points2
    # Fail if there are any NaN's-this indicates something went wrong with the
    # line_series.py module's  _create_series_points() method.
    nans_found = False
    with open(f"{cwd}/bar.points1", "r") as f:
        data = f.read()
        if "NaN" in data:
            nans_found = True

    assert not nans_found

    # Verify that the nan.points1 file does indeed trigger a "nans_found"
    with open(f"{cwd}/nan.points1", "r") as f:
        data = f.read()
        if "NaN" in data:
            nans_found = True

    assert nans_found
    remove_files(cwd, CLEANUP_FILES)


@pytest.mark.skip("fails on linux host machines")
def test_images_match(setup, remove_files):
    """
        Compare an expected plot with the
        newly created plot to verify that the plot hasn't
        changed in appearance.
    """
    comparison = CompareImages(f'{cwd}/bar_expected.png', f'{cwd}/bar.png')
    assert comparison.mssim == 1
    remove_files(cwd, CLEANUP_FILES)


@pytest.mark.skip("fails on linux host machines")
def test_none_data_images_match(setup_nones):
    """
        Compare an expected plot with the
        newly created plot to verify that the plot hasn't
        changed in appearance.
    """
    comparison = CompareImages(f'{cwd}/expected_with_nones.png', f'{cwd}/bar_with_nones.png')
    assert comparison.mssim == 1

    try:
        plot_file = f'{cwd}/bar_with_nones.png'
        os.remove(plot_file)
    except OSError:
        pass


@pytest.mark.parametrize("test_input, expected",
                         (["bar_points1.png", True],
                          ["intermed_files/bar.points1", True]))
def test_point_and_plot_files_exist(setup_env, test_input, expected, remove_files):
    """
        Checking that the plot and (specified location) intermediate file are getting created
    """
    setup_env(cwd)
    custom_config_filename = f"{cwd}/custom_points1_bar.yaml"
    intermed_dir = os.path.join(cwd, 'intermed_files')
    try:
        os.mkdir(intermed_dir)
    except FileExistsError:
        pass

    # Invoke the command to generate a Bar plot based on
    # the custom_bar.yaml custom config file.
    bar.main(custom_config_filename)

    assert os.path.isfile(f"{cwd}/{test_input}") == expected
    remove_files(cwd, ['bar_points1.png'])


@pytest.mark.parametrize("test_input, expected",
                         (["bar_defaultpoints1.png", True], ["bar.points1", True]))
def test_point_and_plot_files_exist(setup_env, test_input, expected, remove_files):
    """
        Checking that the plot and (specified location) intermediate file are getting created
    """
    setup_env(cwd)
    custom_config_filename = f"{cwd}/custom_defaultpoints1_bar.yaml"

    # Invoke the command to generate a Bar plot based on
    # the custom_bar.yaml custom config file.
    bar.main(custom_config_filename)

    assert os.path.isfile(f"{cwd}/{test_input}") == expected

    # remove the .png and .points files
    remove_files(cwd, ['bar_defaultpoints1.png', 'bar.points1'])


@pytest.mark.skip("fails on linux host machines")
def test_threshold_plotting(setup_env, remove_files):
    """
      Verify that the bar plot using data with thresholds is correct.

    """
    # Cleanup the plotfile and point1 output file from any previous run
    remove_files(cwd, CLEANUP_FILES)
    setup_env(cwd)
    custom_config_filename = f"{cwd}/threshold_bar.yaml"

    # Invoke the command to generate a Bar plot based on
    # the custom_bar.yaml custom config file.
    bar.main(custom_config_filename)

    comparison = CompareImages(f'{cwd}/expected_threshold.png', f'{cwd}/threshold_bar.png')
    assert comparison.mssim == 1
    remove_files(cwd, ['threshold_bar.png'])
