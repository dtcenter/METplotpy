# !!!IMPORTANT!!!
# activate conda environment in the testing subshell
# Replace blenny_363 with your METplus Python 3.6.3
# conda environment name
# !!!!!!!!

# !/usr/bin/env conda run -n blenny_363 python

import pytest
import os
from metplotpy.plots.line import line as l
from metcalcpy.compare_images import CompareImages


@pytest.fixture
def setup():
    # Cleanup the plotfile and point1 output file from any previous run
    cleanup()
    # Set up the METPLOTPY_BASE so that met_plot.py will correctly find
    # the config directory containing all the default config files.
    os.environ['METPLOTPY_BASE'] = "../../"
    custom_config_filename = "custom_line.yaml"

    # Invoke the command to generate a Performance Diagram based on
    # the test_custom_performance_diagram.yaml custom config file.
    l.main(custom_config_filename)


def cleanup():
    # remove the line.png and .points files
    # from any previous runs
    try:
        path = os.getcwd()
        plot_file = 'line.png'
        points_file_1 = 'line.points1'
        points_file_2 = 'line.points2'
        os.remove(os.path.join(path, plot_file))
        os.remove(os.path.join(path, points_file_1))
        os.remove(os.path.join(path, points_file_2))
    except OSError as e:
        # Typically when files have already been removed or
        # don't exist.  Ignore.
        pass


@pytest.mark.parametrize("test_input,expected",
                         (["./line.png", True], ["./line.points1", False], ["./line.points2", False]))
def test_files_exist(setup, test_input, expected):
    '''
        Checking that the plot file is getting created but the
        .points1 and .points2 files are NOT
    '''
    assert os.path.isfile(test_input) == expected
    cleanup()

@pytest.mark.parametrize("test_input,expected",
                         (["./line.png", True], ["./intermed_files/line.points1", True], ["./intermed_files/line.points2", True]))
def test_points_files_exist(test_input, expected):
    '''
        Checking that the plot and point data files are getting created
    '''

    # create the intermediate directory to store the .points1 and .points2 files
    try:
       os.mkdir(os.path.join(os.getcwd(), 'intermed_files'))
    except FileExistsError as e:
        pass

    os.environ['METPLOTPY_BASE'] = "../../"
    custom_config_filename = "custom_line2.yaml"
    l.main(custom_config_filename)

    # Test for expected values
    assert os.path.isfile(test_input) == expected

    # cleanup intermediate files and plot
    try:
        path = os.getcwd()
        plot_file = 'line.png'
        points_file_1 = 'line.points1'
        points_file_2 = 'line.points2'
        intermed_path = os.path.join(path, 'intermed_files')
        os.remove(os.path.join(path, plot_file))
        os.remove(os.path.join(intermed_path, points_file_1))
        os.remove(os.path.join(intermed_path, points_file_2))
    except OSError as e:
        # Typically when files have already been removed or
        # don't exist.  Ignore.
        pass

def test_no_nans_in_points_files():
    '''
        Checking that the point data files do not have any NaN's
    '''

    # create the intermediate directory to store the .points1 and .points2 files
    try:
       os.mkdir(os.path.join(os.getcwd(), 'intermed_files'))
    except FileExistsError as e:
        pass

    os.environ['METPLOTPY_BASE'] = "../../"
    custom_config_filename = "custom_line2.yaml"
    l.main(custom_config_filename)


    # Check for NaN's in the intermediate files, line.points1 and line.points2
    # Fail if there are any NaN's-this indicates something went wrong with the
    # line_series.py module's  _create_series_points() method.
    nans_found = False
    with open("./intermed_files/line.points1", "r" ) as f:
        data = f.read()
        if "NaN" in data:
            nans_found = True

    assert nans_found == False

    # Now check line.points2
    with open("./intermed_files/line.points2", "r") as f:
        data = f.read()
        if "NaN" in data:
            nans_found = True

    assert nans_found == False

    # Verify that the nan.points1 file does indeed trigger a "nans_found"
    with open("./intermed_files/nan.points1", "r") as f:
        data = f.read()
        if "NaN" in data:
            nans_found = True

    # assert
    assert nans_found == True

    # cleanup intermediate files and plot
    try:
        path = os.getcwd()
        plot_file = 'line.png'
        points_file_1 = 'line.points1'
        points_file_2 = 'line.points2'
        intermed_path = os.path.join(path, 'intermed_files')
        os.remove(os.path.join(path, plot_file))
        os.remove(os.path.join(intermed_path, points_file_1))
        os.remove(os.path.join(intermed_path, points_file_2))
    except OSError as e:
        # Typically when files have already been removed or
        # don't exist.  Ignore.
        pass


@pytest.mark.skip()
def test_images_match(setup):
    '''
        Compare an expected plot with the
                 newly created plot to verify that the plot hasn't
         changed in appearance.
     '''
    path = os.getcwd()
    plot_file = './line.png'
    actual_file = os.path.join(path, plot_file)
    comparison = CompareImages('./line_expected.png', actual_file)

    # !!!WARNING!!! SOMETIMES FILE SIZES DIFFER IN SPITE OF THE PLOTS LOOKING THE SAME
    # THIS TEST IS NOT 100% RELIABLE because of differences in machines, OS, etc.
    assert comparison.mssim == 1
    cleanup()


