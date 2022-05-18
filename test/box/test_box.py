# !!!IMPORTANT!!!
# activate conda environment in the testing subshell
# Replace blenny_363 with your METplus Python 3.6.3
# conda environment name
# !!!!!!!!

# !/usr/bin/env conda run -n blenny_363 python

import pytest
import os
from metplotpy.plots.box import box
from metcalcpy.compare_images import CompareImages


@pytest.fixture
def setup():
    # Cleanup the plotfile and point1 output file from any previous run
    cleanup()
    # Set up the METPLOTPY_BASE so that met_plot.py will correctly find
    # the config directory containing all the default config files.
    #os.environ['METPLOTPY_BASE'] = "../../metplotpy"
    os.environ['METPLOTPY_BASE'] = "../../"
    custom_config_filename = "custom_box.yaml"

    # Invoke the command to generate a Performance Diagram based on
    # the test_custom_performance_diagram.yaml custom config file.
    box.main(custom_config_filename)


def cleanup():
    # remove the box.png and .points files
    # from any previous runs
    try:
        path = os.getcwd()
        plot_file = 'box.png'
        points_file_1 = 'box.points1'
        os.remove(os.path.join(path, points_file_1))
        os.remove(os.path.join(path, plot_file))

    except OSError as e:
        # Typically when files have already been removed or
        # don't exist.  Ignore.
        pass


@pytest.mark.parametrize("test_input, expected",
                         (["./box.png", True],["./box.points1", True]))
def test_files_exist(setup, test_input, expected):
    """
        Checking that the plot and data files are getting created
    """
    assert os.path.isfile(test_input) == expected
    cleanup()

@pytest.mark.skip("fails on linux hosts")
def test_images_match(setup):
    """
        Compare an expected plot with the
        newly created plot to verify that the plot hasn't
        changed in appearance.
    """
    comparison = CompareImages('./box_expected.png', './box.png')
    assert comparison.mssim == 1
    cleanup()


@pytest.mark.parametrize("test_input, expected",
                         (["./box_expected.png", True],["./box_points1.png", True],["./intermed_files/box.points1", True]))
def test_points1_file_exist(test_input, expected):
    """
        Checking that the plot is created and points1 output files is created
        where specified in the custom_box_points1.yaml file
    """
    os.environ['METPLOTPY_BASE'] = "../../"
    custom_config_filename = "custom_box_points1.yaml"
    try:
       os.mkdir(os.path.join(os.getcwd(), './intermed_files'))
    except FileExistsError as e:
        pass

    # Invoke the command to generate a box plot based on
    # the custom_box_points1.yaml custom config file.
    box.main(custom_config_filename)
    assert os.path.isfile(test_input) == expected
    try:
        path = os.getcwd()
        plot_file = 'box_points1.png'
        points_file_1 = 'box.points1'
        subdir = os.path.join(path, './intermed_files')
        os.remove(os.path.join(path, plot_file))
        os.remove(os.path.join(subdir, points_file_1))
        os.rmdir(subdir)
    except OSError as e:
        # Typically when files have already been removed or
        # don't exist.  Ignore.
        pass


@pytest.mark.parametrize("test_input, expected",
                         (["./box_defaultpoints1.png", True],["./box.points1", True]))
def test_defaultpoints1_file_exist(test_input, expected):
    """
        Checking that the plot is created and points1 output files is created
        in the default location (i.e. the current working dir, where the box.data file resides)
    """
    os.environ['METPLOTPY_BASE'] = "../../"
    custom_config_filename = "custom_box_defaultpoints1.yaml"

    # Invoke the command to generate a box plot based on
    # the custom_box_defaultpoints1.yaml custom config file.
    box.main(custom_config_filename)
    assert os.path.isfile(test_input) == expected

    # remove the created plot and intermediate .points1 file
    try:
        path = os.getcwd()
        plot_file = 'box_defaultpoints1.png'
        points_file_1 = 'box.points1'
        os.remove(os.path.join(path, points_file_1))
        os.remove(os.path.join(path, plot_file))

    except OSError as e:
        # Typically when files have already been removed or
        # don't exist.  Ignore.
        pass


def test_no_nans_in_points_file(setup):
    """
        Checking that the points1 file does not contain NaN's
    """
    os.environ['METPLOTPY_BASE'] = "../../"
    custom_config_filename = "custom_box_defaultpoints1.yaml"

    # Invoke the command to generate a box plot based on
    # the custom_box_defaultpoints1.yaml custom config file.
    box.main(custom_config_filename)

    # Check for NaN's in the intermediate files, line.points1 and line.points2
    # Fail if there are any NaN's-this indicates something went wrong with the
    # line_series.py module's  _create_series_points() method.
    nans_found = False
    with open("./box.points1", "r") as f:
        data = f.read()
        if "NaN" in data:
            nans_found = True

    assert nans_found == False
    cleanup()

    # Verify that the nan.points1 file does indeed trigger a "nans_found"
    with open("./nan.points1", "r") as f:
        data = f.read()
        if "NaN" in data:
            nans_found = True

    # assert
    assert nans_found == True

    # remove the created plot and intermediate .points1 file
    try:
        path = os.getcwd()
        plot_file = 'box_defaultpoints1.png'
        points_file_1 = 'box.points1'
        os.remove(os.path.join(path, points_file_1))
        os.remove(os.path.join(path, plot_file))

    except OSError as e:
        # Typically when files have already been removed or
        # don't exist.  Ignore.
        pass

