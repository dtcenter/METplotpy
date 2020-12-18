# !!!IMPORTANT!!!
# activate conda environment in the testing subshell
# Replace blenny_363 with your METplus Python 3.6.3
# conda environment name
# !!!!!!!!

# !/usr/bin/env conda run -n blenny_363 python

import pytest
import os
from metplotpy.plots.roc_diagram import roc_diagram as roc
from metcalcpy.compare_images import CompareImages


@pytest.fixture
def setup():
    # Cleanup the plotfile and point1 output file from any previous run
    cleanup()
    # Set up the METPLOTPY_BASE so that met_plot.py will correctly find
    # the config directory containing all the default config files.
    os.environ['METPLOTPY_BASE'] = "../../metplotpy"
    custom_config_filename = "./test_roc_diagram.yaml"

    # Invoke the command to generate a Performance Diagram based on
    # the custom_performance_diagram.yaml custom config file.
    roc.main(custom_config_filename)

def cleanup():
    # remove the performance_diagram_expected.png and plot_20200317_151252.points1 files
    # from any previous runs
    try:
        path = os.getcwd()
        plot_file = 'roc_diagram_actual.png'
        points_file = 'plot_20200507_074426.points1'
        html_file = '.html'
        os.remove(os.path.join(path, plot_file))
        os.remove(os.path.join(path, points_file))
        os.remove(os.path.join(path, html_file))
    except OSError as e:
        # Typically when files have already been removed or
        # don't exist.  Ignore.
        pass

def test_first(setup):
    assert True

@pytest.mark.parametrize("test_input,expected_boolean",(["./roc_diagram_expected.png", True], ["./plot_20200507_074426.points1", True]))
def test_files_exist(setup, test_input, expected_boolean):
    '''
        Checking that the plot and data files are getting created
    '''
    assert os.path.isfile(test_input) == expected_boolean
    cleanup()


def test_images_match(setup):
    '''
        Compare an expected plot with the
        newly created plot to verify that the plot hasn't
        changed in appearance.
    '''
    path = os.getcwd()
    plot_file = './roc_diagram_actual.png'
    actual_file = os.path.join(path, plot_file)
    comparison = CompareImages('./roc_diagram_expected.png',actual_file)
    assert comparison.mssim == 1
    cleanup()
