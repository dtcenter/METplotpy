# !!!IMPORTANT!!!
# activate conda environment in the testing subshell
# Replace blenny_363 with your METplus Python 3.6.3
# conda environment name
# !!!!!!!!

# !/usr/bin/env conda run -n blenny_363 python

import pytest
import os
from metplotpy.plots.equivalence_testing_bounds import equivalence_testing_bounds as etb
from metcalcpy.compare_images import CompareImages


@pytest.fixture
def setup():
    # Cleanup the plotfile and point1 output file from any previous run
    cleanup()
    # Set up the METPLOTPY_BASE so that met_plot.py will correctly find
    # the config directory containing all the default config files.
    os.environ['METPLOTPY_BASE'] = "../../.."
    custom_config_filename = "./custom_equivalence_testing_bounds.yaml"

    # Invoke the command to generate an equivalence testing boundary plot based on
    # the custom config file.
    etb.main(custom_config_filename)


def cleanup():
    # remove the line.png and .points1 file
    # from any previous runs
    try:
        path = os.getcwd()
        plot_file = 'equivalence_testing_bounds.png'
        points_file_1 = 'equivalence_testing_bounds.points1'
        os.remove(os.path.join(path, plot_file))
        os.remove(os.path.join(path, points_file_1))
    except OSError as e:
        # Typically when files have already been removed or
        # don't exist.  Ignore.
        pass


@pytest.mark.parametrize("test_input,expected",
                         (["./equivalence_testing_bounds.png", True],
                          ["./equivalence_testing_bounds.points1", True]))
def test_files_exist(setup, test_input, expected):
    '''
        Checking that the plot and data files are getting created
    '''
    assert os.path.isfile(test_input) == expected
    cleanup()


def test_images_match(setup):
    '''
        Compare an expected plot with the
        newly created plot to verify that the plot hasn't
        changed in appearance.
    '''
    path = os.getcwd()
    plot_file = './equivalence_testing_bounds.png'
    actual_file = os.path.join(path, plot_file)
    comparison = CompareImages('./equivalence_testing_bounds_expected.png', actual_file)
    assert comparison.mssim == 1
    cleanup()


@pytest.mark.parametrize("test_input,expected",
                         (["./intermed_files/equivalence_testing_bounds.png", True],
                          ["./intermed_files/equivalence_testing_bounds.points1", True]))
def test_files_exist(test_input, expected):
    '''
        Checking that the plot and data files are getting created
    '''

    intermed_dir = os.path.join(os.getcwd(), 'intermed_files')
    try:
        os.mkdir(intermed_dir)
    except FileExistsError as e:
        pass

    os.environ['METPLOTPY_BASE'] = "../../.."
    custom_config_filename = "./custom_equivalence_testing_bounds2.yaml"

    # Invoke the command to generate an equivalence testing boundary plot based on
    # the custom config file.
    etb.main(custom_config_filename)

    assert os.path.isfile(test_input) == expected
    try:
        path = os.getcwd()
        plot_file = 'equivalence_testing_bounds.png'
        points_file_1 = 'equivalence_testing_bounds.points1'
        subdir = os.path.join(path, 'intermed_files')
        os.remove(os.path.join(subdir, plot_file))
        os.remove(os.path.join(subdir, points_file_1))
        os.rmdir(intermed_dir)
    except OSError as e:
        # Typically when files have already been removed or
        # don't exist.  Ignore.
        pass
