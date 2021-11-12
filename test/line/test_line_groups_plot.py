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
    os.environ['METPLOTPY_BASE'] = "../../metplotpy"
    custom_config_filename = "./custom_line_groups.yaml"

    # Invoke the command to generate a Performance Diagram based on
    # the custom_performance_diagram.yaml custom config file.
    l.main(custom_config_filename)


def cleanup():
    # remove the line.png and .points files
    # from any previous runs
    try:
        path = os.getcwd()
        plot_file = 'line_groups.png'
        points_file_1 = 'line_groups.points1'
        points_file_2 = 'line_groups.points2'
        html_file = 'line_groups.html'
        os.remove(os.path.join(path, plot_file))
        os.remove(os.path.join(path, points_file_1))
        os.remove(os.path.join(path, points_file_2))
        os.remove(os.path.join(path, html_file))
    except OSError as e:
        # Typically when files have already been removed or
        # don't exist.  Ignore.
        pass


@pytest.mark.parametrize("test_input,expected",
                         (["./line_groups.png", True], ["./line_groups.points1", True]))
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
    plot_file = 'line_groups.png'
    actual_file = os.path.join(path, plot_file)
    comparison = CompareImages('./line_groups_expected.png', actual_file)
    assert comparison.mssim == 1
    cleanup()

@pytest.mark.parametrize("test_input,expected",
                         (["./intermed_files/line_groups.png", True], ["./intermed_files/line_groups.points1", True]))
def test_files_exist(setup, test_input, expected):
    '''
        Checking that the plot and data files are getting created
    '''
    intermed_dir = './intermed_files'
    try:
        os.mkdir(intermed_dir)
    except FileExistsError as e:
        pass

    os.environ['METPLOTPY_BASE'] = "../../metplotpy"
    custom_config_filename = "./custom_line_groups2.yaml"

    # Invoke the command to generate a Performance Diagram based on
    # the custom_performance_diagram.yaml custom config file.
    l.main(custom_config_filename)
    assert os.path.isfile(test_input) == expected
    cleanup()

    # remove the subdirectory that was created
    try:
        path = os.getcwd()
        subdir = os.path.join(path, intermed_dir)
        plot_file = 'line_groups.png'
        points_file_1 = 'line_groups.points1'
        points_file_2 = 'line_groups.points2'
        html_file = 'line_groups.html'
        os.remove(os.path.join(subdir, plot_file))
        os.remove(os.path.join(subdir, points_file_1))
        os.remove(os.path.join(subdir, points_file_2))
        os.remove(os.path.join(subdir, html_file))
        os.rmdir(intermed_dir)
    except OSError as e:
        # Typically when files have already been removed or
        # don't exist.  Ignore.
        pass