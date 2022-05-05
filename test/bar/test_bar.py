# !!!IMPORTANT!!!
# activate conda environment in the testing subshell
# Replace blenny_363 with your METplus Python 3.6.3
# conda environment name
# !!!!!!!!

# !/usr/bin/env conda run -n blenny_363 python

import pytest
import os
from metplotpy.plots.bar import bar
from metcalcpy.compare_images import CompareImages


@pytest.fixture
def setup():
    # Cleanup the plotfile and point1 output file from any previous run
    cleanup()
    # Set up the METPLOTPY_BASE so that met_plot.py will correctly find
    # the config directory containing all the default config files.
    os.environ['METPLOTPY_BASE'] = "../../"
    custom_config_filename = "custom_bar.yaml"

    # Invoke the command to generate a Bar plot based on
    # the custom_bar.yaml custom config file.
    bar.main(custom_config_filename)


def cleanup():
    # remove the bbar.png and .points files
    # from any previous runs
    try:
        path = os.getcwd()
        plot_file = 'bar.png'
        points_file_1 = 'bar.points1'
        os.remove(os.path.join(path, plot_file))
        os.remove(os.path.join(path, points_file_1))
    except OSError as e:
        # Typically when files have already been removed or
        # don't exist.  Ignore.
        pass


@pytest.mark.parametrize("test_input, expected",
                         (["./bar_expected.png", True],["./bar.png", True],["./bar.points1", True]))
def test_files_exist( setup, test_input, expected):
    """
        Checking that the plot and data files are getting created
    """
    assert os.path.isfile(test_input) == expected
    cleanup()

def test_no_nans_in_points_file(setup):
    """
        Checking that the points1 intermediate file does not
        have any NaN's.  This is indicative of a problem with the _create_series_points() method.
    """

    # Check for NaN's in the intermediate files, line.points1 and line.points2
    # Fail if there are any NaN's-this indicates something went wrong with the
    # line_series.py module's  _create_series_points() method.
    nans_found = False
    with open("./bar.points1", "r") as f:
        data = f.read()
        if "NaN" in data:
            nans_found = True

    assert nans_found == False
    cleanup()

    # Verify that the nan.points1 file does indeed trigger a "nans_found"
    with open("./intermed_files/nan.points1", "r") as f:
        data = f.read()
        if "NaN" in data:
            nans_found = True

    # assert
    assert nans_found == True


@pytest.mark.skip("fails on linux host machines")
def test_images_match(setup):
    """
        Compare an expected plot with the
        newly created plot to verify that the plot hasn't
        changed in appearance.
    """
    comparison = CompareImages('./bar_expected.png', './bar.png')
    assert comparison.mssim == 1
    cleanup()


@pytest.mark.parametrize("test_input, expected",
                         (["./bar_points1.png", True],["./intermed_files/bar.points1", True]))
def test_point_and_plot_files_exist( test_input, expected):
    """
        Checking that the plot and (specified location) intermediate file are getting created
    """
    os.environ['METPLOTPY_BASE'] = "../../"
    custom_config_filename = "custom_points1_bar.yaml"
    intermed_dir = os.path.join(os.getcwd(), 'intermed_files')
    try:
        os.mkdir(intermed_dir)
    except FileExistsError as e:
        pass

    # Invoke the command to generate a Bar plot based on
    # the custom_bar.yaml custom config file.
    bar.main(custom_config_filename)


    assert os.path.isfile(test_input) == expected
    # remove the .png and .points files
    try:
        path = os.getcwd()
        plot_file = 'bar_points1.png'
        points_file_1 = 'bar.points1'
        subdir = os.path.join(path, 'intermed_files')
        os.remove(os.path.join(path, plot_file))
        os.remove(os.path.join(subdir, points_file_1))
        os.rmdir(intermed_dir)
    except OSError as e:
        # Typically when files have already been removed or
        # don't exist.  Ignore.
        pass

@pytest.mark.parametrize("test_input, expected",
                         (["./bar_defaultpoints1.png", True],["./bar.points1", True]))
def test_point_and_plot_files_exist( test_input, expected):
    """
        Checking that the plot and (specified location) intermediate file are getting created
    """
    os.environ['METPLOTPY_BASE'] = "../../"
    custom_config_filename = "custom_defaultpoints1_bar.yaml"

    # Invoke the command to generate a Bar plot based on
    # the custom_bar.yaml custom config file.
    bar.main(custom_config_filename)

    assert os.path.isfile(test_input) == expected

    # remove the .png and .points files
    try:
        path = os.getcwd()
        plot_file = 'bar_defaultpoints1.png'
        points_file_1 = 'bar.points1'
        os.remove(os.path.join(path, plot_file))
        os.remove(os.path.join(path, points_file_1))
    except OSError as e:
        # Typically when files have already been removed or
        # don't exist.  Ignore.
        pass

